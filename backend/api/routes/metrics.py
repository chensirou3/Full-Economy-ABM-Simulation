"""
指标 API 路由
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import structlog

from ..dependencies import get_simulation_scheduler
from ...simcore.scheduler import SimulationScheduler


logger = structlog.get_logger()
router = APIRouter()


class MetricsResponse(BaseModel):
    """指标响应"""
    timestamp: float
    kpis: Dict[str, float]
    regional_data: Optional[Dict[str, Any]] = None
    sectoral_data: Optional[Dict[str, Any]] = None


@router.get("/current")
async def get_current_metrics(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取当前经济指标"""
    try:
        if scheduler.simulation is None:
            raise HTTPException(status_code=400, detail="模拟未初始化")
        
        # 获取当前指标
        current_metrics = scheduler.telemetry.metrics_aggregator.get_current_metrics()
        
        # 获取实时计算的指标
        live_metrics = scheduler.simulation.get_economic_metrics()
        
        # 合并指标
        all_metrics = {**current_metrics, **live_metrics}
        
        return {
            "status": "success",
            "data": {
                "timestamp": float(scheduler.current_time),
                "kpis": all_metrics,
                "current_time": scheduler.current_time,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取当前指标失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


@router.get("/history")
async def get_metrics_history(
    limit: int = Query(100, ge=1, le=10000),
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取指标历史"""
    try:
        history = scheduler.telemetry.metrics_aggregator.get_metrics_history(limit=limit)
        
        metrics_data = [
            {
                "timestamp": update.timestamp,
                "kpis": update.kpis,
                "regional_data": update.regional_data,
                "sectoral_data": update.sectoral_data,
            }
            for update in history
        ]
        
        return {
            "status": "success",
            "data": metrics_data,
            "count": len(metrics_data),
        }
        
    except Exception as e:
        logger.error("获取指标历史失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取指标历史失败: {str(e)}")


@router.get("/summary")
async def get_metrics_summary(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取指标摘要"""
    try:
        if scheduler.simulation is None:
            raise HTTPException(status_code=400, detail="模拟未初始化")
        
        # 获取当前指标
        current_metrics = scheduler.simulation.get_economic_metrics()
        
        # 获取历史数据进行统计
        history = scheduler.telemetry.metrics_aggregator.get_metrics_history(limit=1000)
        
        # 计算统计信息
        summary = {}
        if history:
            # 计算各指标的统计信息
            for key in current_metrics.keys():
                values = [update.kpis.get(key, 0) for update in history if key in update.kpis]
                if values:
                    summary[key] = {
                        "current": current_metrics[key],
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "trend": "stable",  # 简化的趋势分析
                    }
        
        return {
            "status": "success",
            "data": {
                "current_time": scheduler.current_time,
                "summary": summary,
                "data_points": len(history),
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取指标摘要失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取指标摘要失败: {str(e)}")


@router.get("/agents")
async def get_agent_metrics(
    agent_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取代理层面的指标"""
    try:
        if scheduler.simulation is None:
            raise HTTPException(status_code=400, detail="模拟未初始化")
        
        agents_data = []
        
        # 根据类型过滤代理
        agents = scheduler.simulation.schedule.agents
        if agent_type:
            agents = [agent for agent in agents if agent.agent_type.value == agent_type]
        
        # 限制返回数量
        agents = agents[:limit]
        
        for agent in agents:
            if hasattr(agent, 'serialize_state'):
                agent_data = agent.serialize_state()
                agents_data.append(agent_data)
        
        return {
            "status": "success",
            "data": agents_data,
            "count": len(agents_data),
            "total_agents": len(scheduler.simulation.schedule.agents),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取代理指标失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取代理指标失败: {str(e)}")


@router.get("/performance")
async def get_performance_metrics(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取模拟性能指标"""
    try:
        # 获取模拟状态
        status = scheduler.get_status()
        
        # 获取性能统计
        perf_stats = scheduler.get_performance_stats()
        
        return {
            "status": "success",
            "data": {
                "simulation_status": {
                    "state": status.state.value,
                    "current_time": status.current_time,
                    "speed": status.speed,
                    "total_agents": status.total_agents,
                    "elapsed_real_time": status.elapsed_real_time,
                    "steps_per_second": status.steps_per_second,
                    "memory_usage_mb": status.memory_usage_mb,
                },
                "performance_stats": perf_stats,
            },
        }
        
    except Exception as e:
        logger.error("获取性能指标失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/export")
async def export_metrics(
    format: str = Query("json", regex="^(json|csv)$"),
    start_time: Optional[int] = Query(None),
    end_time: Optional[int] = Query(None),
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """导出指标数据"""
    try:
        # 获取历史数据
        history = scheduler.telemetry.metrics_aggregator.get_metrics_history(limit=10000)
        
        # 时间范围过滤
        if start_time is not None:
            history = [h for h in history if h.timestamp >= start_time]
        if end_time is not None:
            history = [h for h in history if h.timestamp <= end_time]
        
        if format == "json":
            data = [
                {
                    "timestamp": update.timestamp,
                    "kpis": update.kpis,
                }
                for update in history
            ]
            
            return {
                "status": "success",
                "format": "json",
                "data": data,
                "count": len(data),
            }
        
        elif format == "csv":
            # CSV 格式导出
            import io
            import csv
            from fastapi.responses import StreamingResponse
            
            output = io.StringIO()
            
            if history:
                # 获取所有指标键
                all_keys = set()
                for update in history:
                    all_keys.update(update.kpis.keys())
                
                fieldnames = ["timestamp"] + sorted(all_keys)
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for update in history:
                    row = {"timestamp": update.timestamp}
                    row.update(update.kpis)
                    writer.writerow(row)
            
            output.seek(0)
            
            return StreamingResponse(
                io.BytesIO(output.getvalue().encode()),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=metrics_export.csv"}
            )
        
    except Exception as e:
        logger.error("导出指标失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"导出指标失败: {str(e)}")
