from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.app.database import get_db
from backend.app.models.token_price import TokenInfo
from backend.app.schemas.token_schema import (
    TokenPriceSummary,
    KlinePoint,
    OrderBookDepth,
    TokenWatchlistCreate
)
from backend.app.services.price_fetcher import price_service

router = APIRouter(prefix="/price", tags=["Price & Market"])

@router.get("/summary", response_model=List[TokenPriceSummary])
async def get_price_summary():
    """获取所有监控 Token 的最新价格概览与分时微图"""
    return await price_service.get_all_summaries()

@router.get("/kline", response_model=List[KlinePoint])
async def get_kline(
    symbol: str = Query(..., description="Token 标识，如 WELL, BTC, ETH"),
    timeframe: str = Query("1m", description="周期：1m, 5m, 1h, 1d"),
    limit: int = Query(100, ge=10, le=500)
):
    """获取指定币种的历史与实时 K 线数据柱"""
    return await price_service.get_kline_data(symbol=symbol, timeframe=timeframe, limit=limit)

@router.get("/depth", response_model=OrderBookDepth)
async def get_orderbook_depth(
    symbol: str = Query(..., description="Token 标识"),
    levels: int = Query(15, ge=5, le=50)
):
    """获取买卖盘挂单深度分布"""
    return await price_service.get_order_book_depth(symbol=symbol, depth_levels=levels)

@router.get("/watchlist")
async def get_watchlist(db: AsyncSession = Depends(get_db)):
    """获取用户配置的监控清单"""
    stmt = select(TokenInfo).order_by(TokenInfo.sort_order.asc())
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/watchlist")
async def add_to_watchlist(item: TokenWatchlistCreate, db: AsyncSession = Depends(get_db)):
    """添加或关注指定 Token"""
    symbol = item.symbol.upper()
    stmt = select(TokenInfo).where(TokenInfo.symbol == symbol)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing:
        existing.is_favorite = item.is_favorite or False
        await db.commit()
        return {"status": "updated", "symbol": symbol}
    
    new_token = TokenInfo(
        symbol=symbol,
        name=item.name,
        is_active=True,
        is_favorite=item.is_favorite or False
    )
    db.add(new_token)
    await db.commit()
    return {"status": "created", "symbol": symbol}

@router.delete("/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str, db: AsyncSession = Depends(get_db)):
    """从自选清单中移除"""
    stmt = delete(TokenInfo).where(TokenInfo.symbol == symbol.upper())
    await db.execute(stmt)
    await db.commit()
    return {"status": "deleted", "symbol": symbol.upper()}

@router.websocket("/ws")
async def websocket_price_endpoint(websocket: WebSocket):
    """WebSocket 实时推送行情数据流"""
    await price_service.connect_ws(websocket)
    try:
        # 首次连接立即推送当前全量数据
        summaries = [s.model_dump(mode="json") for s in await price_service.get_all_summaries()]
        await websocket.send_json({"type": "init", "data": summaries})
        while True:
            # 维持连接与接收客户端 Ping / 控制指令
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        price_service.disconnect_ws(websocket)
    except Exception:
        price_service.disconnect_ws(websocket)
