"""
FastAPI 依赖注入
"""

from fastapi import HTTPException
from ..simcore.scheduler import SimulationScheduler
from .main import simulation_scheduler, websocket_manager
from .websocket import WebSocketManager


def get_simulation_scheduler() -> SimulationScheduler:
    """获取模拟调度器依赖"""
    if simulation_scheduler is None:
        raise HTTPException(status_code=500, detail="模拟调度器未初始化")
    return simulation_scheduler


def get_websocket_manager() -> WebSocketManager:
    """获取 WebSocket 管理器依赖"""
    return websocket_manager
