"""
快照管理 API 路由
"""

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import structlog

from ..dependencies import get_simulation_scheduler
from ...simcore.scheduler import SimulationScheduler


logger = structlog.get_logger()
router = APIRouter()


class SnapshotInfo(BaseModel):
    """快照信息"""
    timestamp: int
    file_size: int
    file_path: str


@router.get("/", response_model=List[SnapshotInfo])
async def list_snapshots(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """列出所有快照"""
    try:
        snapshots_data = scheduler.snapshot_manager.list_snapshots()
        
        snapshots = [
            SnapshotInfo(
                timestamp=snap["timestamp"],
                file_size=snap["file_size"],
                file_path=snap["file_path"],
            )
            for snap in snapshots_data
        ]
        
        return snapshots
        
    except Exception as e:
        logger.error("列出快照失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"列出快照失败: {str(e)}")


@router.get("/latest")
async def get_latest_snapshot(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取最新快照信息"""
    try:
        snapshots = scheduler.snapshot_manager.list_snapshots()
        
        if not snapshots:
            raise HTTPException(status_code=404, detail="没有可用的快照")
        
        latest = max(snapshots, key=lambda x: x["timestamp"])
        
        return {
            "status": "success",
            "data": latest,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取最新快照失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取最新快照失败: {str(e)}")


@router.get("/{timestamp}")
async def get_snapshot(
    timestamp: int,
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取指定时间戳的快照信息"""
    try:
        snapshot = await scheduler.snapshot_manager.load_snapshot(timestamp)
        
        if snapshot is None:
            raise HTTPException(status_code=404, detail="快照不存在")
        
        return {
            "status": "success",
            "data": {
                "timestamp": snapshot.timestamp,
                "state_hash": snapshot.state_hash,
                "metadata": snapshot.metadata,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("获取快照失败", timestamp=timestamp, error=str(e))
        raise HTTPException(status_code=500, detail=f"获取快照失败: {str(e)}")


@router.get("/{timestamp}/download")
async def download_snapshot(
    timestamp: int,
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """下载快照文件"""
    try:
        snapshots = scheduler.snapshot_manager.list_snapshots()
        snapshot_info = next((s for s in snapshots if s["timestamp"] == timestamp), None)
        
        if snapshot_info is None:
            raise HTTPException(status_code=404, detail="快照不存在")
        
        file_path = snapshot_info["file_path"]
        
        return FileResponse(
            path=file_path,
            filename=f"snapshot_{timestamp}.zst",
            media_type="application/octet-stream",
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("下载快照失败", timestamp=timestamp, error=str(e))
        raise HTTPException(status_code=500, detail=f"下载快照失败: {str(e)}")


@router.post("/create")
async def create_snapshot(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """手动创建快照"""
    try:
        if scheduler.simulation is None:
            raise HTTPException(status_code=400, detail="模拟未初始化")
        
        # 创建快照
        snapshot = await scheduler.snapshot_manager.create_snapshot(
            timestamp=scheduler.current_time,
            state=scheduler.simulation.get_state(),
            metadata={
                "manual": True,
                "description": "手动创建的快照",
            }
        )
        
        logger.info("手动快照已创建", timestamp=snapshot.timestamp)
        
        return {
            "status": "success",
            "message": "快照已创建",
            "data": {
                "timestamp": snapshot.timestamp,
                "state_hash": snapshot.state_hash,
                "metadata": snapshot.metadata,
            },
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("创建快照失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"创建快照失败: {str(e)}")


@router.delete("/{timestamp}")
async def delete_snapshot(
    timestamp: int,
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """删除指定快照"""
    try:
        snapshots = scheduler.snapshot_manager.list_snapshots()
        snapshot_info = next((s for s in snapshots if s["timestamp"] == timestamp), None)
        
        if snapshot_info is None:
            raise HTTPException(status_code=404, detail="快照不存在")
        
        # 删除文件
        import os
        os.remove(snapshot_info["file_path"])
        
        # 更新索引
        if timestamp in scheduler.snapshot_manager.snapshot_index:
            del scheduler.snapshot_manager.snapshot_index[timestamp]
            scheduler.snapshot_manager._save_index()
        
        logger.info("快照已删除", timestamp=timestamp)
        
        return {
            "status": "success",
            "message": f"快照 {timestamp} 已删除",
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("删除快照失败", timestamp=timestamp, error=str(e))
        raise HTTPException(status_code=500, detail=f"删除快照失败: {str(e)}")


@router.post("/cleanup")
async def cleanup_old_snapshots(
    keep_count: int = 10,
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """清理旧快照"""
    try:
        scheduler.snapshot_manager.cleanup_old_snapshots(keep_count=keep_count)
        
        remaining_snapshots = len(scheduler.snapshot_manager.list_snapshots())
        
        return {
            "status": "success",
            "message": f"旧快照清理完成，保留 {remaining_snapshots} 个快照",
            "remaining_count": remaining_snapshots,
        }
        
    except Exception as e:
        logger.error("清理快照失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"清理快照失败: {str(e)}")


@router.get("/stats/storage")
async def get_storage_stats(
    scheduler: SimulationScheduler = get_simulation_scheduler()
):
    """获取存储统计信息"""
    try:
        stats = scheduler.snapshot_manager.get_storage_stats()
        
        return {
            "status": "success",
            "data": stats,
        }
        
    except Exception as e:
        logger.error("获取存储统计失败", error=str(e))
        raise HTTPException(status_code=500, detail=f"获取存储统计失败: {str(e)}")
