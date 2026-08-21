import asyncio
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Set
from fastapi import WebSocket
from sqlalchemy import select
from backend.app.config import settings
from backend.app.database import AsyncSessionLocal
from backend.app.models.token_price import TokenInfo, TokenPriceRecord, KlineData
from backend.app.schemas.token_schema import TokenPriceSummary, KlinePoint, DepthLevel, OrderBookDepth

class PriceFetcherService:
    def __init__(self):
        self.active_websockets: Set[WebSocket] = set()
        self.prices_cache: Dict[str, dict] = {}
        self.history_sparkline: Dict[str, List[float]] = {}
        self.is_running = False
        self._task = None

    async def initialize(self):
        """初始化默认 Token 数据与基础价格"""
        async with AsyncSessionLocal() as session:
            for item in settings.DEFAULT_TOKENS:
                stmt = select(TokenInfo).where(TokenInfo.symbol == item["symbol"])
                result = await session.execute(stmt)
                token = result.scalar_one_or_none()
                if not token:
                    new_token = TokenInfo(
                        symbol=item["symbol"],
                        name=item["name"],
                        is_active=True,
                        is_favorite=item["symbol"] == "WELL"
                    )
                    session.add(new_token)
            await session.commit()

        # 初始化内存价格缓存
        now = datetime.utcnow()
        for item in settings.DEFAULT_TOKENS:
            sym = item["symbol"]
            base = item["base_price"]
            self.prices_cache[sym] = {
                "symbol": sym,
                "name": item["name"],
                "price": base,
                "change_24h": round(random.uniform(-3.5, 7.8), 2),
                "high_24h": round(base * 1.05, 4),
                "low_24h": round(base * 0.95, 4),
                "volume_24h": round(base * random.uniform(50000, 500000), 2),
                "market_cap": round(base * 10000000, 2),
                "timestamp": now,
                "volatility": item["volatility"]
            }
            # 生成 30 个初始 sparkline 点
            spk = []
            curr = base * 0.98
            for _ in range(30):
                curr += curr * random.uniform(-0.01, 0.012)
                spk.append(round(curr, 4))
            self.history_sparkline[sym] = spk

    async def start_loop(self):
        """启动后台行情更新与数据推送循环"""
        self.is_running = True
        self._task = asyncio.create_task(self._fetch_loop())

    async def stop_loop(self):
        """停止后台循环"""
        self.is_running = False
        if self._task:
            self._task.cancel()

    async def _fetch_loop(self):
        while self.is_running:
            try:
                await self._update_prices()
                await self._broadcast_websocket()
                await asyncio.sleep(settings.PRICE_FETCH_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[PriceFetcherService] Update error: {e}")
                await asyncio.sleep(settings.PRICE_FETCH_INTERVAL)

    async def _update_prices(self):
        """模拟/拉取最新价格并更新 SQLite 记录"""
        now = datetime.utcnow()
        records_to_insert = []
        
        for sym, data in self.prices_cache.items():
            vol = data["volatility"]
            drift = random.uniform(-vol, vol * 1.05)
            new_price = round(data["price"] * (1 + drift), 4 if data["price"] < 10 else 2)
            
            data["price"] = new_price
            data["timestamp"] = now
            if new_price > data["high_24h"]:
                data["high_24h"] = new_price
            if new_price < data["low_24h"]:
                data["low_24h"] = new_price
            data["volume_24h"] += round(new_price * random.uniform(10, 100), 2)
            
            # 更新 sparkline
            if sym in self.history_sparkline:
                self.history_sparkline[sym].append(new_price)
                if len(self.history_sparkline[sym]) > 40:
                    self.history_sparkline[sym].pop(0)

            records_to_insert.append(
                TokenPriceRecord(
                    symbol=sym,
                    price=new_price,
                    change_24h=data["change_24h"],
                    high_24h=data["high_24h"],
                    low_24h=data["low_24h"],
                    volume_24h=data["volume_24h"],
                    market_cap=data["market_cap"],
                    timestamp=now
                )
            )

        # 写入数据库 (每若干次或每次批量写入)
        try:
            async with AsyncSessionLocal() as session:
                session.add_all(records_to_insert)
                await session.commit()
        except Exception as e:
            print(f"[Database write error]: {e}")

    async def get_all_summaries(self) -> List[TokenPriceSummary]:
        summaries = []
        for sym, d in self.prices_cache.items():
            summaries.append(
                TokenPriceSummary(
                    symbol=d["symbol"],
                    name=d["name"],
                    price=d["price"],
                    change_24h=d["change_24h"],
                    high_24h=d["high_24h"],
                    low_24h=d["low_24h"],
                    volume_24h=d["volume_24h"],
                    market_cap=d["market_cap"],
                    timestamp=d["timestamp"],
                    sparkline=self.history_sparkline.get(sym, [])
                )
            )
        return summaries

    async def get_kline_data(self, symbol: str, timeframe: str = "1m", limit: int = 100) -> List[KlinePoint]:
        symbol = symbol.upper()
        current_data = self.prices_cache.get(symbol)
        base = current_data["price"] if current_data else 100.0
        
        # 依据当前价格与周期生成平滑逼真的 K 线图数据
        points: List[KlinePoint] = []
        now_ts = int(time.time() * 1000)
        interval_ms = 60 * 1000 if timeframe == "1m" else (300 * 1000 if timeframe == "5m" else 3600 * 1000)
        
        curr = base * 0.92
        for i in range(limit, 0, -1):
            ts = now_ts - (i * interval_ms)
            step_change = curr * random.uniform(-0.015, 0.018)
            open_p = curr
            close_p = round(curr + step_change, 2 if base > 10 else 4)
            high_p = round(max(open_p, close_p) + abs(step_change) * random.uniform(0.1, 0.6), 2 if base > 10 else 4)
            low_p = round(min(open_p, close_p) - abs(step_change) * random.uniform(0.1, 0.6), 2 if base > 10 else 4)
            vol = round(random.uniform(500, 8000) * base, 2)
            
            points.append(KlinePoint(
                timestamp=ts,
                open=open_p,
                high=high_p,
                low=low_p,
                close=close_p,
                volume=vol
            ))
            curr = close_p

        # 确保最后一个点与当前实时价格对齐
        if points and current_data:
            points[-1].close = current_data["price"]
            points[-1].high = max(points[-1].high, current_data["price"])
            points[-1].low = min(points[-1].low, current_data["price"])

        return points

    async def get_order_book_depth(self, symbol: str, depth_levels: int = 15) -> OrderBookDepth:
        symbol = symbol.upper()
        current_data = self.prices_cache.get(symbol)
        curr_price = current_data["price"] if current_data else 100.0
        
        bids: List[DepthLevel] = []
        asks: List[DepthLevel] = []
        
        # 买单（从当前价格向下）
        bid_total = 0.0
        for i in range(1, depth_levels + 1):
            p = round(curr_price * (1 - 0.0015 * i), 2 if curr_price > 10 else 4)
            amt = round(random.uniform(5, 50) * (depth_levels - i + 1), 2)
            bid_total += amt
            bids.append(DepthLevel(price=p, amount=amt, total=round(bid_total, 2)))
            
        # 卖单（从当前价格向上）
        ask_total = 0.0
        for i in range(1, depth_levels + 1):
            p = round(curr_price * (1 + 0.0015 * i), 2 if curr_price > 10 else 4)
            amt = round(random.uniform(5, 50) * (depth_levels - i + 1), 2)
            ask_total += amt
            asks.append(DepthLevel(price=p, amount=amt, total=round(ask_total, 2)))
            
        return OrderBookDepth(
            symbol=symbol,
            timestamp=int(time.time() * 1000),
            bids=bids,
            asks=asks
        )

    # WebSocket 管理
    async def connect_ws(self, websocket: WebSocket):
        await websocket.accept()
        self.active_websockets.add(websocket)

    def disconnect_ws(self, websocket: WebSocket):
        self.active_websockets.discard(websocket)

    async def _broadcast_websocket(self):
        if not self.active_websockets:
            return
        
        summaries = [s.model_dump(mode="json") for s in await self.get_all_summaries()]
        payload = {
            "type": "price_update",
            "timestamp": int(time.time() * 1000),
            "data": summaries
        }
        
        disconnected = set()
        for ws in self.active_websockets:
            try:
                await ws.send_json(payload)
            except Exception:
                disconnected.add(ws)
                
        for ws in disconnected:
            self.disconnect_ws(ws)

price_service = PriceFetcherService()
