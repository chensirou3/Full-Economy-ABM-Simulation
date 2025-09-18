"""
FastAPI 主应用
提供 REST API 和 WebSocket 端点
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import asyncio
import json
import structlog
from typing import Dict, List, Any, Optional
import uvicorn

from .routes import control, scenarios, snapshots, metrics
from .websocket import WebSocketManager
from ..simcore.config import APISettings
from ..simcore.telemetry import get_telemetry
from ..simcore.scheduler import SimulationScheduler


logger = structlog.get_logger()

# 全局变量
simulation_scheduler: Optional[SimulationScheduler] = None
websocket_manager: WebSocketManager = WebSocketManager()
settings = APISettings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global simulation_scheduler
    
    # 启动时初始化
    logger.info("启动 ABM 经济体模拟 API 服务器")
    
    # 初始化遥测系统
    telemetry = get_telemetry()
    
    # 初始化模拟调度器
    simulation_scheduler = SimulationScheduler()
    
    # 连接遥测系统与WebSocket管理器
    telemetry.event_bus.websocket_clients = websocket_manager.active_connections
    
    yield
    
    # 关闭时清理
    logger.info("关闭 ABM 经济体模拟 API 服务器")
    if simulation_scheduler:
        await simulation_scheduler.stop()


# 创建 FastAPI 应用
app = FastAPI(
    title="ABM 经济体模拟 API",
    description="基于多主体建模的经济体模拟系统 REST API",
    version="0.1.0",
    lifespan=lifespan,
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "ABM Economic Simulation API",
        "version": "0.1.0",
        "simulation_running": simulation_scheduler.is_running if simulation_scheduler else False,
    }


# WebSocket 端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    await websocket_manager.connect(websocket)
    
    # 获取遥测系统并添加客户端
    telemetry = get_telemetry()
    await telemetry.event_bus.add_websocket_client(websocket)
    
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 处理客户端请求
            await handle_websocket_message(websocket, message)
            
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket)
        await telemetry.event_bus.remove_websocket_client(websocket)
        logger.info("WebSocket 客户端断开连接")
    except Exception as e:
        logger.error("WebSocket 连接错误", error=str(e))
        await websocket_manager.disconnect(websocket)
        await telemetry.event_bus.remove_websocket_client(websocket)


async def handle_websocket_message(websocket: WebSocket, message: Dict[str, Any]):
    """处理 WebSocket 消息"""
    message_type = message.get("type")
    
    if message_type == "subscribe":
        # 订阅特定主题
        topics = message.get("topics", [])
        await websocket_manager.subscribe_to_topics(websocket, topics)
        
    elif message_type == "unsubscribe":
        # 取消订阅
        topics = message.get("topics", [])
        await websocket_manager.unsubscribe_from_topics(websocket, topics)
        
    elif message_type == "ping":
        # 心跳检测
        await websocket.send_text(json.dumps({"type": "pong", "timestamp": message.get("timestamp")}))
        
    else:
        # 未知消息类型
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": f"Unknown message type: {message_type}"
        }))


# 包含路由模块
app.include_router(control.router, prefix="/control", tags=["控制"])
app.include_router(scenarios.router, prefix="/scenarios", tags=["场景"])
app.include_router(snapshots.router, prefix="/snapshots", tags=["快照"])
app.include_router(metrics.router, prefix="/metrics", tags=["指标"])


# 错误处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """通用异常处理器"""
    logger.error("未处理的异常", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "status_code": 500,
        }
    )


# 获取全局对象的辅助函数
def get_simulation_scheduler() -> SimulationScheduler:
    """获取模拟调度器"""
    if simulation_scheduler is None:
        raise HTTPException(status_code=500, detail="模拟调度器未初始化")
    return simulation_scheduler


def get_websocket_manager() -> WebSocketManager:
    """获取 WebSocket 管理器"""
    return websocket_manager


# 开发服务器入口
def main():
    """开发服务器入口点"""
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )


if __name__ == "__main__":
    main()
