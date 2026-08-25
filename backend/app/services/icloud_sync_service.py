import os
import sys
import json
import time
import asyncio
import hmac
import hashlib
import secrets
import base64
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.database import AsyncSessionLocal
from backend.app.config import settings, DATA_DIR
from backend.app.models.token_price import (
    RelaySite, SiteModelPricing, ModelMetadata,
    ChannelModelMapping, ModelAlias, SystemSetting, SpeedTestHistory
)
from backend.app.services.dashboard_service import dashboard_service
from backend.app.services.model_normalizer import model_normalizer


class SecurePayloadCipher:
    """基于标准库 PBKDF2-HMAC-SHA256 与 CTR/HMAC 认证流加密的高安全性端到端加密器"""

    @staticmethod
    def encrypt(data_str: str, password: str) -> Dict[str, str]:
        salt = secrets.token_bytes(16)
        iv = secrets.token_bytes(16)
        
        # PBKDF2 派生 64 字节密钥 (前 32 字节用于流加密，后 32 字节用于 HMAC 认证)
        derived = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations=100000,
            dklen=64
        )
        enc_key = derived[:32]
        auth_key = derived[32:]

        plaintext_bytes = data_str.encode('utf-8')
        
        # 生成 CTR 模式密钥流并与明文异或
        keystream = bytearray()
        block_count = (len(plaintext_bytes) + 31) // 32
        for counter in range(block_count):
            counter_bytes = counter.to_bytes(8, byteorder='big')
            block_seed = iv + counter_bytes
            keystream.extend(hmac.new(enc_key, block_seed, hashlib.sha256).digest())

        ciphertext = bytes([p ^ k for p, k in zip(plaintext_bytes, keystream[:len(plaintext_bytes)])])

        # 计算 HMAC 认证标签 (Salt + IV + Ciphertext)
        tag = hmac.new(auth_key, salt + iv + ciphertext, hashlib.sha256).digest()

        return {
            "algorithm": "PBKDF2-HMAC-SHA256-CTR",
            "salt": base64.b64encode(salt).decode('utf-8'),
            "iv": base64.b64encode(iv).decode('utf-8'),
            "tag": base64.b64encode(tag).decode('utf-8'),
            "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
        }

    @staticmethod
    def decrypt(cipher_data: Dict[str, str], password: str) -> str:
        try:
            salt = base64.b64decode(cipher_data["salt"])
            iv = base64.b64decode(cipher_data["iv"])
            tag = base64.b64decode(cipher_data["tag"])
            ciphertext = base64.b64decode(cipher_data["ciphertext"])
        except Exception:
            raise ValueError("密文数据结构损坏或 Base64 解码失败")

        derived = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            iterations=100000,
            dklen=64
        )
        enc_key = derived[:32]
        auth_key = derived[32:]

        # 校验 HMAC 认证标签 (防篡改与密码错误校验)
        expected_tag = hmac.new(auth_key, salt + iv + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected_tag):
            raise ValueError("解密密码错误或同步数据已被篡改")

        # 生成 CTR 模式密钥流并异或解密
        keystream = bytearray()
        block_count = (len(ciphertext) + 31) // 32
        for counter in range(block_count):
            counter_bytes = counter.to_bytes(8, byteorder='big')
            block_seed = iv + counter_bytes
            keystream.extend(hmac.new(enc_key, block_seed, hashlib.sha256).digest())

        plaintext = bytes([c ^ k for c, k in zip(ciphertext, keystream[:len(ciphertext)])])
        return plaintext.decode('utf-8')


class ICloudSyncService:
    """macOS iCloud Drive 渠道与配置双向智能同步服务"""

    SYNC_DIR_NAME = "WellTokenDashboard"
    MAIN_SYNC_FILENAME = "welltoken_sync.json"
    BACKUPS_DIR_NAME = "backups"

    def __init__(self):
        self.is_macos = sys.platform == "darwin"
        self._sync_folder = self._resolve_icloud_folder()
        self._backups_folder = self._sync_folder / self.BACKUPS_DIR_NAME

    def _resolve_icloud_folder(self) -> Path:
        """解析并确保 iCloud 目录路径"""
        if self.is_macos:
            icloud_root = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
            if icloud_root.exists():
                folder = icloud_root / self.SYNC_DIR_NAME
                try:
                    folder.mkdir(parents=True, exist_ok=True)
                    (folder / self.BACKUPS_DIR_NAME).mkdir(parents=True, exist_ok=True)
                    return folder
                except Exception as e:
                    print(f"[iCloudSync] 创建 iCloud 目录失败，降级至本地目录: {e}")
        
        # 降级或非 macOS 环境备用目录
        fallback_folder = DATA_DIR / "icloud_sync" / self.SYNC_DIR_NAME
        fallback_folder.mkdir(parents=True, exist_ok=True)
        (fallback_folder / self.BACKUPS_DIR_NAME).mkdir(parents=True, exist_ok=True)
        return fallback_folder

    @property
    def sync_file_path(self) -> Path:
        return self._sync_folder / self.MAIN_SYNC_FILENAME

    @property
    def backups_dir_path(self) -> Path:
        return self._sync_folder / self.BACKUPS_DIR_NAME

    def is_icloud_available(self) -> bool:
        """检查 macOS iCloud Drive 是否可用"""
        if not self.is_macos:
            return False
        icloud_root = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
        return icloud_root.exists() and os.access(str(icloud_root), os.W_OK)

    def _resolve_active_sync_file(self) -> Path:
        """多层级自适应检索 iCloud 同步主文件 (兼容标准 iCloud 云盘、桌面文稿同步与全局 Spotlight 索引)"""
        primary = self._sync_folder / self.MAIN_SYNC_FILENAME
        if primary.exists():
            return primary
        
        primary_ph = self._sync_folder / f".{self.MAIN_SYNC_FILENAME}.icloud"
        if primary_ph.exists():
            return primary

        if self.is_macos:
            # 兼容文稿目录下的同名同步夹
            doc_sync = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Documents" / self.SYNC_DIR_NAME / self.MAIN_SYNC_FILENAME
            if doc_sync.exists() or (doc_sync.parent / f".{doc_sync.name}.icloud").exists():
                return doc_sync

            # 利用 macOS Spotlight 元数据引擎全局定位
            try:
                res = subprocess.run(["mdfind", "kMDItemFSName == *welltoken_sync.json*"], capture_output=True, text=True, timeout=2.0)
                lines = [l.strip() for l in res.stdout.strip().split("\n") if l.strip()]
                for line in lines:
                    if "com~apple~CloudDocs" in line:
                        p = Path(line)
                        if p.name == self.MAIN_SYNC_FILENAME:
                            return p
                        elif p.name == f".{self.MAIN_SYNC_FILENAME}.icloud":
                            return p.parent / self.MAIN_SYNC_FILENAME
            except Exception:
                pass

        return primary

    def _trigger_icloud_download(self, path: Path) -> bool:
        """通过 macOS 原生 JXA (JavaScript for Automation) 调度 bird 守护进程主动从 iCloud 下载文件"""
        if not self.is_macos:
            return False
        try:
            abs_path = str(path.resolve())
            js_code = f"""
            var path = ObjC.wrap("{abs_path}");
            var url = $.NSURL.fileURLWithPath(path);
            $.NSFileManager.defaultManager.startDownloadingUbiquitousItemAtURLError(url, null);
            """
            subprocess.run(["osascript", "-l", "JavaScript", "-e", js_code], capture_output=True, timeout=3.0)
            return True
        except Exception as e:
            print(f"[iCloudSync] 触发 iCloud 下载失败 ({path}): {e}")
            return False

    async def _ensure_file_downloaded_from_icloud(self, target_file: Path, wait_timeout_sec: float = 12.0) -> bool:
        """确保 iCloud 文件已从云端拉取下载至本地磁盘 (处理 Optimize Mac Storage 导致的 .icloud 占位符)"""
        if target_file.exists():
            return True

        # 无论是否存在占位符，都主动向 macOS 发出下载指令 (触发自身与父目录)
        self._trigger_icloud_download(target_file)
        self._trigger_icloud_download(target_file.parent)
        
        placeholder = target_file.parent / f".{target_file.name}.icloud"
        if placeholder.exists():
            self._trigger_icloud_download(placeholder)

        # 唤醒 iCloud 根目录
        if self.is_macos:
            icloud_root = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
            self._trigger_icloud_download(icloud_root)

        # 循环轮询等待文件落地
        start_time = time.time()
        while time.time() - start_time < wait_timeout_sec:
            if target_file.exists():
                return True
            discovered = self._resolve_active_sync_file()
            if discovered.exists():
                return True
            await asyncio.sleep(0.5)

        return target_file.exists()

    def get_status(self) -> Dict[str, Any]:
        """获取 iCloud 同步状态与统计信息"""
        self._sync_folder = self._resolve_icloud_folder()
        available = self.is_icloud_available()
        file_path = self._resolve_active_sync_file()
        exists = file_path.exists()
        
        # 若主文件不存在，检查是否有云端待下载占位符
        placeholder = file_path.parent / f".{file_path.name}.icloud"
        is_cloud_placeholder = False
        if not exists and placeholder.exists():
            is_cloud_placeholder = True
            exists = True
            # 后台静默触发下载
            self._trigger_icloud_download(file_path)
            self._trigger_icloud_download(placeholder)

        file_size_bytes = 0
        last_modified = None
        is_encrypted = False
        cloud_channels_count = 0
        cloud_mappings_count = 0
        cloud_aliases_count = 0
        schema_version = "1.0"
        exported_at = None
        device_id = None

        if file_path.exists():
            try:
                stat = file_path.stat()
                file_size_bytes = stat.st_size
                last_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                
                schema_version = raw_data.get("schema_version", "1.0")
                is_encrypted = raw_data.get("is_encrypted", False)
                exported_at = raw_data.get("exported_at")
                device_id = raw_data.get("device_id")

                if not is_encrypted and "payload" in raw_data:
                    p = raw_data["payload"]
                    cloud_channels_count = len(p.get("channels", []))
                    cloud_mappings_count = sum(len(c.get("mappings", [])) for c in p.get("channels", []))
                    cloud_aliases_count = len(p.get("aliases", []))
            except Exception as e:
                print(f"[iCloudSync] 读取云端同步文件状态失败: {e}")

        # 统计备份文件数
        backups = self.list_backups()

        return {
            "is_macos": self.is_macos,
            "icloud_available": available,
            "sync_folder_path": str(self._sync_folder),
            "sync_file_exists": exists,
            "is_cloud_placeholder": is_cloud_placeholder,
            "sync_file_size_bytes": file_size_bytes,
            "sync_file_last_modified": last_modified,
            "schema_version": schema_version,
            "exported_at": exported_at,
            "device_id": device_id,
            "is_encrypted": is_encrypted,
            "cloud_channels_count": cloud_channels_count,
            "cloud_mappings_count": cloud_mappings_count,
            "cloud_aliases_count": cloud_aliases_count,
            "backups_count": len(backups),
            "latest_backup": backups[0] if backups else None
        }

    async def export_data_bundle(
        self,
        sync_modules: Optional[Dict[str, bool]] = None,
        include_api_keys: bool = True,
        password: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """打包导出本地自定义渠道、映射、别名与偏好配置"""
        modules = {
            "custom_channels": True,
            "custom_aliases": True,
            "favorites": True,
            "preferences": True,
            "speed_tests": False,
            **(sync_modules or {})
        }

        payload: Dict[str, Any] = {}

        async with AsyncSessionLocal() as session:
            # 1. 导出自建与中转渠道 (is_official_catalog == False 或自建)
            if modules.get("custom_channels"):
                stmt = (
                    select(RelaySite)
                    .where(RelaySite.is_official_catalog == False)
                    .options(
                        selectinload(RelaySite.mappings),
                        selectinload(RelaySite.pricings)
                    )
                    .order_by(RelaySite.id.asc())
                )
                res = await session.execute(stmt)
                sites = res.scalars().all()

                channels_list = []
                for s in sites:
                    c_data = {
                        "provider_id": s.provider_id or "",
                        "name": s.name,
                        "base_url": s.base_url,
                        "api_key": s.api_key if include_api_keys else "",
                        "site_type": s.site_type,
                        "group_name": s.group_name or "",
                        "currency": s.currency or "CNY",
                        "recharge_rate": s.recharge_rate,
                        "models_endpoint": s.models_endpoint,
                        "status_endpoint": s.status_endpoint or "",
                        "website": s.website or "",
                        "doc_url": s.doc_url or "",
                        "env_vars": s.env_vars or "",
                        "notes": s.notes or "",
                        "is_active": s.is_active,
                        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
                        "mappings": [
                            {
                                "channel_model_name": m.channel_model_name,
                                "standard_model_id": m.standard_model_id,
                                "custom_ratio": m.custom_ratio,
                                "is_enabled": m.is_enabled
                            }
                            for m in s.mappings
                        ],
                        "pricings": [
                            {
                                "model_id": p.model_id,
                                "site_model_name": p.site_model_name,
                                "group_name": p.group_name,
                                "model_ratio": p.model_ratio,
                                "group_ratio": p.group_ratio,
                                "calculated_input_usd": p.calculated_input_usd,
                                "calculated_output_usd": p.calculated_output_usd,
                                "calculated_cache_usd": p.calculated_cache_usd,
                                "discount_percent": p.discount_percent,
                                "is_available": p.is_available
                            }
                            for p in s.pricings
                        ]
                    }
                    channels_list.append(c_data)
                payload["channels"] = channels_list

            # 2. 导出用户自定义别名 (is_system == False)
            if modules.get("custom_aliases"):
                a_stmt = select(ModelAlias).where(ModelAlias.is_system == False).order_by(ModelAlias.id.asc())
                a_res = await session.execute(a_stmt)
                aliases = a_res.scalars().all()
                payload["aliases"] = [
                    {
                        "raw_pattern": a.raw_pattern,
                        "standard_model_id": a.standard_model_id,
                        "notes": a.notes or "",
                        "created_at": a.created_at.strftime("%Y-%m-%d %H:%M:%S") if a.created_at else ""
                    }
                    for a in aliases
                ]

            # 3. 导出系统偏好设置 (汇率、汇率源)
            if modules.get("preferences"):
                await dashboard_service.ensure_settings_loaded()
                rate_updated = dashboard_service.exchange_rate_updated_at
                if isinstance(rate_updated, datetime):
                    rate_updated_str = rate_updated.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    rate_updated_str = str(rate_updated or "")

                payload["preferences"] = {
                    "usd_to_cny_rate": dashboard_service.usd_to_cny_rate,
                    "exchange_rate_source": dashboard_service.exchange_rate_source,
                    "exchange_rate_updated_at": rate_updated_str
                }

            # 4. 导出测速历史 (最近 100 条)
            if modules.get("speed_tests"):
                st_stmt = select(SpeedTestHistory).order_by(SpeedTestHistory.test_time.desc()).limit(100)
                st_res = await session.execute(st_stmt)
                tests = st_res.scalars().all()
                payload["speed_tests"] = [
                    {
                        "model_id": t.model_id,
                        "test_time": t.test_time.strftime("%Y-%m-%d %H:%M:%S") if t.test_time else "",
                        "ttft_ms": t.ttft_ms,
                        "avg_tps": t.avg_tps,
                        "peak_tps": t.peak_tps,
                        "total_latency_ms": t.total_latency_ms,
                        "is_success": t.is_success,
                        "score": t.score
                    }
                    for t in tests
                ]

        dev_name = device_id or f"{platform.node()}-{platform.system()}"
        bundle: Dict[str, Any] = {
            "schema_version": "1.0",
            "app_name": settings.APP_NAME,
            "exported_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "device_id": dev_name,
            "sync_modules": modules,
            "include_api_keys": include_api_keys,
            "is_encrypted": bool(password)
        }

        if password:
            json_str = json.dumps(payload, ensure_ascii=False)
            bundle["encrypted_payload"] = SecurePayloadCipher.encrypt(json_str, password)
        else:
            bundle["payload"] = payload

        return bundle

    async def push_to_icloud(
        self,
        sync_modules: Optional[Dict[str, bool]] = None,
        include_api_keys: bool = True,
        password: Optional[str] = None,
        device_id: Optional[str] = None,
        favorites_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """将本地配置打包并推送到 iCloud Drive，并生成滚动快照"""
        self._sync_folder = self._resolve_icloud_folder()
        bundle = await self.export_data_bundle(
            sync_modules=sync_modules,
            include_api_keys=include_api_keys,
            password=password,
            device_id=device_id
        )

        # 注入前端传递的收藏夹信息
        if favorites_data and (sync_modules is None or sync_modules.get("favorites", True)):
            if not bundle.get("is_encrypted"):
                bundle["payload"]["favorites"] = favorites_data
            else:
                # 重新加密以包含 favorites
                payload = json.loads(SecurePayloadCipher.decrypt(bundle["encrypted_payload"], password))
                payload["favorites"] = favorites_data
                bundle["encrypted_payload"] = SecurePayloadCipher.encrypt(json.dumps(payload, ensure_ascii=False), password)

        # 1. 写入主同步文件
        main_file = self.sync_file_path
        with open(main_file, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        # 2. 写入滚动备份快照 (保留最近 20 份)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"welltoken_sync_{timestamp}.json"
        backup_file = self._backups_folder / backup_filename
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        self._rotate_backups(max_keep=20)

        # 主动唤醒 macOS iCloud 同步上传新文件
        self._trigger_icloud_download(main_file)
        self._trigger_icloud_download(backup_file)
        self._trigger_icloud_download(self._sync_folder)

        channels_cnt = len(bundle.get("payload", {}).get("channels", [])) if not bundle.get("is_encrypted") else -1

        return {
            "status": "success",
            "message": "已成功推送到 iCloud Drive",
            "file_path": str(main_file),
            "backup_path": str(backup_file),
            "exported_at": bundle["exported_at"],
            "channels_count": channels_cnt,
            "is_encrypted": bundle["is_encrypted"]
        }

    async def pull_and_merge_from_icloud(
        self,
        password: Optional[str] = None,
        from_backup_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """从 iCloud Drive 主文件或指定历史备份中拉取并智能双向合并到本地数据库"""
        self._sync_folder = self._resolve_icloud_folder()
        
        target_file = self._resolve_active_sync_file()
        if from_backup_file:
            target_file = self._backups_folder / from_backup_file

        # 主动触发 iCloud 下载并等待占位文件转为实体文件 (应对跨设备同步延迟)
        await self._ensure_file_downloaded_from_icloud(target_file, wait_timeout_sec=12.0)

        if not target_file.exists():
            if from_backup_file:
                raise FileNotFoundError(f"未在 iCloud 备份目录中找到快照文件: {target_file.name}")
            else:
                raise FileNotFoundError(
                    "未在当前设备检测到 iCloud 同步文件 (welltoken_sync.json)。\n"
                    "• 如果您刚在另一台 Mac 上完成推送，苹果云端同步到本机通常需要 10~60 秒，请稍候片刻后再次重试；\n"
                    "• 您也可以在「系统设置」中点击「在访达中定位」检查 iCloud Drive 文件同步状态。"
                )

        with open(target_file, "r", encoding="utf-8") as f:
            raw_bundle = json.load(f)

        is_encrypted = raw_bundle.get("is_encrypted", False)
        payload: Dict[str, Any] = {}

        if is_encrypted:
            if not password:
                raise ValueError("该云端同步文件已被主密码加密，请输入密码后拉取")
            enc_data = raw_bundle.get("encrypted_payload")
            if not enc_data:
                raise ValueError("云端加密数据包损坏")
            decrypted_str = SecurePayloadCipher.decrypt(enc_data, password)
            payload = json.loads(decrypted_str)
        else:
            payload = raw_bundle.get("payload", {})

        # 合并前先创建一份本地自动备份快照
        await self._create_local_pre_merge_backup()

        # 执行数据库实体合并
        report = await self._merge_payload_to_db(payload)
        
        # 刷新全局缓存与别名库
        await model_normalizer.initialize()
        await dashboard_service.broadcast_market_update()

        return {
            "status": "success",
            "message": "从 iCloud 智能合并完成",
            "source_file": target_file.name,
            "exported_at": raw_bundle.get("exported_at"),
            "device_id": raw_bundle.get("device_id"),
            "is_encrypted": is_encrypted,
            "report": report,
            "favorites": payload.get("favorites")
        }

    async def _merge_payload_to_db(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """智能合并数据包至本地 SQLite 数据库"""
        created_channels = 0
        updated_channels = 0
        imported_mappings = 0
        imported_aliases = 0

        async with AsyncSessionLocal() as session:
            # 预加载标准模型以供价格计算
            m_res = await session.execute(select(ModelMetadata))
            standard_models = {m.model_id: m for m in m_res.scalars().all()}

            # A. 合并自定义渠道
            channels = payload.get("channels", [])
            for c in channels:
                name = c.get("name", "").strip()
                base_url = c.get("base_url", "").strip().rstrip("/")
                if not name or not base_url:
                    continue

                # 匹配本地已存在的自建渠道 (按名称或 base_url 匹配)
                stmt = select(RelaySite).where(
                    RelaySite.is_official_catalog == False,
                    (RelaySite.name == name) | (RelaySite.base_url == base_url)
                ).options(selectinload(RelaySite.mappings), selectinload(RelaySite.pricings))
                
                res = await session.execute(stmt)
                existing_site = res.scalar_one_or_none()

                if existing_site:
                    # 更新已有渠道基础属性
                    existing_site.base_url = base_url
                    existing_site.site_type = c.get("site_type", existing_site.site_type)
                    existing_site.group_name = c.get("group_name", existing_site.group_name)
                    existing_site.currency = c.get("currency", existing_site.currency)
                    existing_site.recharge_rate = c.get("recharge_rate", existing_site.recharge_rate)
                    existing_site.models_endpoint = c.get("models_endpoint", existing_site.models_endpoint)
                    existing_site.status_endpoint = c.get("status_endpoint", existing_site.status_endpoint)
                    existing_site.notes = c.get("notes", existing_site.notes)
                    if c.get("api_key"):
                        existing_site.api_key = c.get("api_key")
                    
                    target_site = existing_site
                    updated_channels += 1
                else:
                    # 创建新渠道
                    new_site = RelaySite(
                        name=name,
                        provider_id=c.get("provider_id", ""),
                        base_url=base_url,
                        api_key=c.get("api_key", ""),
                        site_type=c.get("site_type", "custom"),
                        group_name=c.get("group_name", ""),
                        currency=c.get("currency", "CNY"),
                        recharge_rate=c.get("recharge_rate", 1.0),
                        models_endpoint=c.get("models_endpoint", "/v1/models"),
                        status_endpoint=c.get("status_endpoint", ""),
                        website=c.get("website", ""),
                        doc_url=c.get("doc_url", ""),
                        env_vars=c.get("env_vars", ""),
                        notes=c.get("notes", ""),
                        is_official_catalog=False,
                        is_active=c.get("is_active", True),
                        last_latency_ms=45.0
                    )
                    session.add(new_site)
                    await session.flush()
                    target_site = new_site
                    created_channels += 1

                # 清理并重新导入该渠道的 mappings 与 pricings
                await session.execute(delete(ChannelModelMapping).where(ChannelModelMapping.site_id == target_site.id))
                await session.execute(delete(SiteModelPricing).where(SiteModelPricing.site_id == target_site.id))

                # 导入 Mappings
                for m_item in c.get("mappings", []):
                    std_id = m_item.get("standard_model_id", "").strip()
                    c_name = m_item.get("channel_model_name", "").strip()
                    if not std_id or not c_name:
                        continue

                    # 自动确保标准模型元数据骨架存在，防止 SQLite 外键约束校验失败
                    if std_id not in standard_models:
                        new_meta = ModelMetadata(
                            model_id=std_id,
                            name=std_id,
                            provider=target_site.provider_id or "custom",
                            official_input_price=0.0,
                            official_output_price=0.0,
                            official_cache_price=0.0,
                            created_at=datetime.utcnow()
                        )
                        session.add(new_meta)
                        await session.flush()
                        standard_models[std_id] = new_meta
                    
                    cm = ChannelModelMapping(
                        site_id=target_site.id,
                        channel_model_name=c_name,
                        standard_model_id=std_id,
                        custom_ratio=m_item.get("custom_ratio"),
                        is_enabled=m_item.get("is_enabled", True)
                    )
                    session.add(cm)
                    imported_mappings += 1

                    # 重新生成定价
                    std_meta = standard_models.get(std_id)
                    if std_meta:
                        ratio = m_item.get("custom_ratio") or target_site.recharge_rate
                        calc_in = round(std_meta.official_input_price * ratio * target_site.recharge_rate, 4)
                        calc_out = round(std_meta.official_output_price * ratio * target_site.recharge_rate, 4)
                        calc_cache = round(std_meta.official_cache_price * ratio * target_site.recharge_rate, 4)
                        discount = round(((calc_in - std_meta.official_input_price) / std_meta.official_input_price * 100), 1) if std_meta.official_input_price > 0 else 0.0

                        pricing = SiteModelPricing(
                            site_id=target_site.id,
                            model_id=std_id,
                            group_name=target_site.group_name or "",
                            site_model_name=c_name,
                            model_ratio=ratio,
                            group_ratio=1.0,
                            calculated_input_usd=calc_in,
                            calculated_output_usd=calc_out,
                            calculated_cache_usd=calc_cache,
                            discount_percent=discount,
                            is_available=True,
                            last_tested_tps=50.0
                        )
                        session.add(pricing)

            # B. 合并自定义模型别名
            aliases = payload.get("aliases", [])
            for a_item in aliases:
                pat = a_item.get("raw_pattern", "").strip().lower()
                std_id = a_item.get("standard_model_id", "").strip()
                if not pat or not std_id:
                    continue

                # 自动确保标准模型元数据骨架存在
                if std_id not in standard_models:
                    new_meta = ModelMetadata(
                        model_id=std_id,
                        name=std_id,
                        provider="custom",
                        official_input_price=0.0,
                        official_output_price=0.0,
                        official_cache_price=0.0,
                        created_at=datetime.utcnow()
                    )
                    session.add(new_meta)
                    await session.flush()
                    standard_models[std_id] = new_meta

                a_stmt = select(ModelAlias).where(ModelAlias.raw_pattern == pat)
                a_res = await session.execute(a_stmt)
                existing_alias = a_res.scalar_one_or_none()

                if existing_alias:
                    existing_alias.standard_model_id = std_id
                    existing_alias.notes = a_item.get("notes", existing_alias.notes)
                else:
                    new_alias = ModelAlias(
                        raw_pattern=pat,
                        standard_model_id=std_id,
                        is_system=False,
                        notes=a_item.get("notes", "通过 iCloud 同步恢复")
                    )
                    session.add(new_alias)
                imported_aliases += 1

            # C. 合并系统汇率偏好 (如有)
            pref = payload.get("preferences")
            if pref and pref.get("usd_to_cny_rate"):
                rate_val = float(pref.get("usd_to_cny_rate"))
                src_val = pref.get("exchange_rate_source") or dashboard_service.exchange_rate_source
                now_iso = datetime.utcnow().isoformat()

                s_rate = await session.get(SystemSetting, "usd_to_cny_rate")
                if not s_rate:
                    session.add(SystemSetting(key="usd_to_cny_rate", value=str(rate_val), description="USD对CNY基础换算汇率"))
                else:
                    s_rate.value = str(rate_val)

                s_src = await session.get(SystemSetting, "exchange_rate_source")
                if not s_src:
                    session.add(SystemSetting(key="exchange_rate_source", value=src_val, description="外汇汇率权威获取源网址"))
                else:
                    s_src.value = src_val

                s_upd = await session.get(SystemSetting, "exchange_rate_updated_at")
                if not s_upd:
                    session.add(SystemSetting(key="exchange_rate_updated_at", value=now_iso, description="外汇汇率最后一次更新时间"))
                else:
                    s_upd.value = now_iso

                dashboard_service.usd_to_cny_rate = rate_val
                dashboard_service.exchange_rate_source = src_val

            await session.commit()

        return {
            "created_channels": created_channels,
            "updated_channels": updated_channels,
            "imported_mappings": imported_mappings,
            "imported_aliases": imported_aliases
        }

    async def _create_local_pre_merge_backup(self):
        """合并前在备份目录自动保存本地状态快照"""
        try:
            bundle = await self.export_data_bundle(include_api_keys=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self._backups_folder / f"local_pre_merge_{timestamp}.json"
            with open(backup_file, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=2)
            self._rotate_backups(max_keep=20)
        except Exception as e:
            print(f"[iCloudSync] 创建本地合并前快照失败: {e}")

    def list_backups(self) -> List[Dict[str, Any]]:
        """获取所有历史备份快照列表"""
        self._sync_folder = self._resolve_icloud_folder()
        if not self._backups_folder.exists():
            return []

        backups = []
        # A. 正常已下载的 json 备份
        for file in self._backups_folder.glob("*.json"):
            try:
                stat = file.stat()
                created_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                backups.append({
                    "filename": file.name,
                    "filepath": str(file),
                    "size_bytes": stat.st_size,
                    "created_at": created_at,
                    "is_pre_merge": "pre_merge" in file.name,
                    "is_cloud_placeholder": False
                })
            except Exception:
                continue

        # B. 尚未下载落地的 .icloud 占位备份
        for file in self._backups_folder.glob(".*.json.icloud"):
            try:
                # 去掉开头的 . 和结尾的 .icloud
                clean_name = file.name[1:-7] if file.name.startswith(".") and file.name.endswith(".icloud") else file.name
                if not any(b["filename"] == clean_name for b in backups):
                    stat = file.stat()
                    created_at = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                    backups.append({
                        "filename": clean_name,
                        "filepath": str(file),
                        "size_bytes": 0,
                        "created_at": created_at,
                        "is_pre_merge": "pre_merge" in clean_name,
                        "is_cloud_placeholder": True
                    })
                    # 触发后台下载该快照
                    self._trigger_icloud_download(file)
            except Exception:
                continue

        backups.sort(key=lambda x: x["created_at"], reverse=True)
        return backups

    def _rotate_backups(self, max_keep: int = 20):
        """保留最近 N 份备份快照，清理过期文件"""
        backups = self.list_backups()
        if len(backups) > max_keep:
            for b in backups[max_keep:]:
                try:
                    Path(b["filepath"]).unlink(missing_ok=True)
                except Exception:
                    pass

    def open_in_finder(self) -> bool:
        """在 macOS 访达 Finder 中打开同步目录"""
        self._sync_folder = self._resolve_icloud_folder()
        try:
            if self.is_macos:
                subprocess.run(["open", str(self._sync_folder)], check=True)
                return True
            elif sys.platform == "win32":
                os.startfile(str(self._sync_folder))
                return True
            else:
                subprocess.run(["xdg-open", str(self._sync_folder)], check=True)
                return True
        except Exception as e:
            print(f"[iCloudSync] 打开文件夹失败: {e}")
            return False


icloud_sync_service = ICloudSyncService()
