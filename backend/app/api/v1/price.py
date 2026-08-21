from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/price", tags=["Market Stream & WS"])

@router.get("/summary")
async def get_price_summary():
    """获取聚合比价摘要"""
    return await dashboard_service.get_comparison_matrix()

@router.websocket("/ws")
async def websocket_market_endpoint(websocket: WebSocket):
    """全网实时行情与测速流 WebSocket 端点"""
    await dashboard_service.connect_ws(websocket)
    try:
        # 连接成功推送当前全网比价全量数据
        matrix = await dashboard_service.get_comparison_matrix()
        await websocket.send_json({
            "type": "init",
            "data": [m.model_dump(mode="json") for m in matrix]
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        dashboard_service.disconnect_ws(websocket)
    except Exception:
        dashboard_service.disconnect_ws(websocket)
