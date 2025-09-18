"""
时间控制 API 路由
提供 Play/Pause/Step/Speed/Jump/Rewind 功能
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
import structlog

from ..dependencies import get_simulation_scheduler
from ...simcore.scheduler import SimulationScheduler


logger = structlog.get_logger()
router = APIRouter()


class PlayRequest(BaseModel):
    """开始播放请求"""
    speed: Optional[float] = 1.0


class SpeedRequest(BaseModel):
    """调整速度请求"""
    speed: float


class StepRequest(BaseModel):
    """单步执行请求"""
    steps: int = 1


class JumpRequest(BaseModel):
    """时间跳转请求"""
    target_time: int
    

class RewindRequest(BaseModel):
    """倒带请求"""
    target_time: int


@router.post("/play")
async def play_simulation(
    request: PlayRequest,
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """开始/恢复模拟"""
    try:
        await scheduler.play(speed=request.speed)
        logger.info("模拟开始播放", speed=request.speed)
        
        return {
            "status": "success",
            "message": "模拟已开始播放",
            "speed": request.speed,
            "current_time": scheduler.current_time,
        }
    except Exception as e:
        logger.error("启动模拟失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"启动模拟失败: {str(e)}")


@router.post("/pause")
async def pause_simulation(
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """暂停模拟"""
    try:
        await scheduler.pause()
        logger.info("模拟已暂停")
        
        return {
            "status": "success",
            "message": "模拟已暂停",
            "current_time": scheduler.current_time,
        }
    except Exception as e:
        logger.error("暂停模拟失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"暂停模拟失败: {str(e)}")


@router.post("/step")
async def step_simulation(
    request: StepRequest,
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """单步执行模拟"""
    try:
        final_time = await scheduler.step(steps=request.steps)
        logger.info("模拟单步执行", steps=request.steps, final_time=final_time)
        
        return {
            "status": "success",
            "message": f"执行了 {request.steps} 步",
            "steps_executed": request.steps,
            "current_time": final_time,
        }
    except Exception as e:
        logger.error("单步执行失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"单步执行失败: {str(e)}")


@router.post("/speed")
async def set_simulation_speed(
    request: SpeedRequest,
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """调整模拟速度"""
    try:
        if request.speed <= 0:
            raise HTTPException(status_code=400, detail="速度必须大于0")
        
        await scheduler.set_speed(request.speed)
        logger.info("模拟速度已调整", speed=request.speed)
        
        return {
            "status": "success",
            "message": f"模拟速度已调整为 {request.speed}x",
            "speed": request.speed,
            "current_time": scheduler.current_time,
        }
    except Exception as e:
        logger.error("调整速度失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"调整速度失败: {str(e)}")


@router.post("/jump")
async def jump_to_time(
    request: JumpRequest,
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """跳转到指定时间"""
    try:
        if request.target_time < 0:
            raise HTTPException(status_code=400, detail="目标时间不能为负数")
        
        if request.target_time < scheduler.current_time:
            raise HTTPException(
                status_code=400, 
                detail="不能跳转到过去的时间，请使用 rewind 功能"
            )
        
        final_time = await scheduler.jump_to(request.target_time)
        logger.info("时间跳转完成", target_time=request.target_time, final_time=final_time)
        
        return {
            "status": "success",
            "message": f"已跳转到时间 {final_time}",
            "target_time": request.target_time,
            "current_time": final_time,
        }
    except Exception as e:
        logger.error("时间跳转失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"时间跳转失败: {str(e)}")


@router.post("/rewind")
async def rewind_simulation(
    request: RewindRequest,
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """倒带到指定时间"""
    try:
        if request.target_time < 0:
            raise HTTPException(status_code=400, detail="目标时间不能为负数")
        
        if request.target_time >= scheduler.current_time:
            raise HTTPException(
                status_code=400, 
                detail="不能倒带到未来的时间，请使用 jump 功能"
            )
        
        final_time = await scheduler.rewind_to(request.target_time)
        logger.info("倒带完成", target_time=request.target_time, final_time=final_time)
        
        return {
            "status": "success",
            "message": f"已倒带到时间 {final_time}",
            "target_time": request.target_time,
            "current_time": final_time,
        }
    except Exception as e:
        logger.error("倒带失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"倒带失败: {str(e)}")


@router.get("/status")
async def get_simulation_status(
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """获取模拟状态"""
    try:
        status = scheduler.get_status()
        
        return {
            "status": "success",
            "data": status,
        }
    except Exception as e:
        logger.error("获取模拟状态失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@router.post("/reset")
async def reset_simulation(
    scheduler: SimulationScheduler = Depends(get_simulation_scheduler)
):
    """重置模拟"""
    try:
        await scheduler.reset()
        logger.info("模拟已重置")
        
        return {
            "status": "success",
            "message": "模拟已重置",
            "current_time": 0,
        }
    except Exception as e:
        logger.error("重置模拟失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"重置模拟失败: {str(e)}")
