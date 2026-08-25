import os
import json
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from backend.app.services.icloud_sync_service import icloud_sync_service

router = APIRouter(prefix="/icloud", tags=["macOS iCloud Sync"])


class PushICloudRequest(BaseModel):
    sync_modules: Optional[Dict[str, bool]] = Field(default_factory=lambda: {
        "custom_channels": True,
        "custom_aliases": True,
        "favorites": True,
        "preferences": True,
        "speed_tests": False
    })
    include_api_keys: bool = True
    password: Optional[str] = None
    device_id: Optional[str] = None
    favorites_data: Optional[Dict[str, Any]] = None


class PullICloudRequest(BaseModel):
    password: Optional[str] = None
    from_backup_file: Optional[str] = None


class RestoreBackupRequest(BaseModel):
    backup_filename: str
    password: Optional[str] = None


class ImportBundleRequest(BaseModel):
    bundle: Dict[str, Any]
    password: Optional[str] = None


@router.get("/status")
async def get_icloud_status():
    """获取 macOS iCloud Drive 同步状态、文件指标与备份信息"""
    return icloud_sync_service.get_status()


@router.post("/push")
async def push_to_icloud(payload: PushICloudRequest):
    """将本地自定义渠道商、模型映射、别名与配置打包推送到 iCloud Drive"""
    try:
        res = await icloud_sync_service.push_to_icloud(
            sync_modules=payload.sync_modules,
            include_api_keys=payload.include_api_keys,
            password=payload.password,
            device_id=payload.device_id,
            favorites_data=payload.favorites_data
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推送到 iCloud 失败: {str(e)}")


@router.post("/pull")
async def pull_from_icloud(payload: PullICloudRequest):
    """从 iCloud Drive 读取云端配置并执行智能双向合并"""
    try:
        res = await icloud_sync_service.pull_and_merge_from_icloud(
            password=payload.password,
            from_backup_file=payload.from_backup_file
        )
        return res
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"从 iCloud 拉取合并失败: {str(e)}")


@router.get("/backups")
async def get_icloud_backups():
    """获取 iCloud 历史备份快照列表"""
    backups = icloud_sync_service.list_backups()
    return {"backups": backups, "count": len(backups)}


@router.post("/restore")
async def restore_from_backup(payload: RestoreBackupRequest):
    """从指定的 iCloud 历史快照还原数据"""
    try:
        res = await icloud_sync_service.pull_and_merge_from_icloud(
            password=payload.password,
            from_backup_file=payload.backup_filename
        )
        return {
            "status": "success",
            "message": f"成功从快照 [{payload.backup_filename}] 还原数据",
            "details": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"还原备份快照失败: {str(e)}")


@router.post("/open-finder")
async def open_icloud_in_finder():
    """在 macOS Finder 访达中打开 iCloud 同步目录"""
    success = icloud_sync_service.open_in_finder()
    if not success:
        raise HTTPException(status_code=500, detail="打开同步目录失败")
    return {
        "status": "success",
        "sync_folder": str(icloud_sync_service._sync_folder)
    }


@router.post("/export-bundle")
async def export_local_bundle(payload: PushICloudRequest):
    """直接导出数据包 JSON (用于通用本地下载保存)"""
    try:
        bundle = await icloud_sync_service.export_data_bundle(
            sync_modules=payload.sync_modules,
            include_api_keys=payload.include_api_keys,
            password=payload.password,
            device_id=payload.device_id
        )
        if payload.favorites_data:
            if not bundle.get("is_encrypted"):
                bundle["payload"]["favorites"] = payload.favorites_data
        return bundle
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打包导出失败: {str(e)}")


@router.post("/import-bundle")
async def import_local_bundle(payload: ImportBundleRequest):
    """接收上传的 JSON 数据包并合并到本地数据库 (通用跨平台导入)"""
    try:
        bundle = payload.bundle
        is_encrypted = bundle.get("is_encrypted", False)
        if is_encrypted:
            if not payload.password:
                raise HTTPException(status_code=400, detail="此配置文件已被加密，请输入解密密码")
            enc_data = bundle.get("encrypted_payload")
            from backend.app.services.icloud_sync_service import SecurePayloadCipher
            decrypted_str = SecurePayloadCipher.decrypt(enc_data, payload.password)
            data_payload = json.loads(decrypted_str)
        else:
            data_payload = bundle.get("payload", {})

        await icloud_sync_service._create_local_pre_merge_backup()
        report = await icloud_sync_service._merge_payload_to_db(data_payload)
        
        from backend.app.services.model_normalizer import model_normalizer
        from backend.app.services.dashboard_service import dashboard_service
        await model_normalizer.initialize()
        await dashboard_service.broadcast_market_update()

        return {
            "status": "success",
            "message": "本地配置数据包导入并合并成功",
            "report": report,
            "favorites": data_payload.get("favorites")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入数据包失败: {str(e)}")
