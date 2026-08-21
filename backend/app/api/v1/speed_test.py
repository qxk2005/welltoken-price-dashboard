from fastapi import APIRouter, Query, BackgroundTasks
from typing import List, Dict, Any
from backend.app.schemas.token_schema import SpeedTestRequest, SpeedTestResultSchema
from backend.app.services.speed_tester import speed_tester
from backend.app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/speed-test", tags=["Speed Tester"])

@router.post("/run", response_model=List[SpeedTestResultSchema])
async def execute_speed_test(payload: SpeedTestRequest):
    """启动一次单渠道或批量多渠道并发性能实测任务"""
    # 定义实时流式广播回调
    async def ws_callback(event: Dict[str, Any]):
        await dashboard_service.broadcast({
            "type": "speed_test_event",
            "data": event
        })

    results = await speed_tester.run_speed_test_task(
        site_ids=payload.site_ids,
        model_id=payload.model_id,
        prompt_type=payload.prompt_type,
        rounds=payload.rounds,
        event_callback=ws_callback
    )
    return results

@router.get("/history", response_model=List[SpeedTestResultSchema])
async def get_speed_test_history(
    limit: int = Query(30, ge=5, le=100, description="历史记录条数")
):
    """获取渠道性能实测历史记录与质量评级排行榜"""
    return await speed_tester.get_recent_history(limit=limit)
