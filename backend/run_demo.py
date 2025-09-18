#!/usr/bin/env python3
"""
ABM 经济体模拟系统演示脚本
快速启动和演示系统功能
"""

import asyncio
import time
import logging
from pathlib import Path

from simcore.config import load_scenario_config
from simcore.scheduler import SimulationScheduler
from simcore.telemetry import get_telemetry, EventType


# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_demo():
    """运行演示"""
    logger.info("🚀 启动 ABM 经济体模拟系统演示")
    
    # 1. 加载基准场景
    logger.info("📋 加载基准场景配置...")
    scenario_path = Path("scenarios/baseline.yml")
    if not scenario_path.exists():
        logger.error(f"场景文件不存在: {scenario_path}")
        return
    
    config = load_scenario_config(scenario_path)
    logger.info(f"✅ 场景配置加载成功: {config.population.N} 个代理")
    
    # 2. 创建调度器
    logger.info("🎮 初始化模拟调度器...")
    scheduler = SimulationScheduler(config)
    await scheduler.initialize()
    
    # 3. 设置遥测监听
    telemetry = get_telemetry()
    
    # 监听重要事件
    def on_important_event(event):
        logger.info(f"📊 重要事件: {event.event_type.value} - {event.payload}")
    
    important_events = [
        EventType.FIRM_BANKRUPTCY,
        EventType.BANK_FAILURE,
        EventType.INTEREST_RATE_CHANGE,
        EventType.CHECKPOINT_CREATED,
    ]
    
    for event_type in important_events:
        telemetry.event_bus.subscribe(event_type.value, on_important_event)
    
    # 4. 运行短期模拟
    logger.info("▶️  开始模拟运行...")
    await scheduler.play(speed=2.0)  # 2倍速
    
    # 运行一段时间
    start_time = time.time()
    target_duration = 30  # 30秒演示
    
    while time.time() - start_time < target_duration:
        await asyncio.sleep(1)
        
        status = scheduler.get_status()
        if status.simulationStatus:
            logger.info(
                f"⏰ 时间: {status.simulationStatus.current_time}, "
                f"代理: {status.simulationStatus.total_agents}, "
                f"速度: {status.steps_per_second:.1f} steps/s"
            )
        
        # 每10秒显示经济指标
        if int(time.time() - start_time) % 10 == 0:
            if scheduler.simulation:
                metrics = scheduler.simulation.get_economic_metrics()
                logger.info(
                    f"📈 经济指标 - GDP: {metrics['gdp']:.1f}, "
                    f"失业率: {metrics['unemployment']:.1%}, "
                    f"通胀: {metrics['inflation']:.1%}, "
                    f"政策利率: {metrics['policy_rate']:.1%}"
                )
    
    # 5. 演示时间控制功能
    logger.info("⏸️  暂停模拟...")
    await scheduler.pause()
    
    logger.info("👆 单步执行 5 步...")
    await scheduler.step(5)
    
    logger.info("⏪ 倒带到 100 步前...")
    current_time = scheduler.current_time
    target_time = max(0, current_time - 100)
    await scheduler.rewind_to(target_time)
    
    logger.info("⏩ 快进到原来的时间...")
    await scheduler.jump_to(current_time)
    
    # 6. 创建手动快照
    logger.info("📸 创建快照...")
    snapshot = await scheduler.snapshot_manager.create_snapshot(
        timestamp=scheduler.current_time,
        state=scheduler.simulation.get_state(),
        metadata={"demo": True, "description": "演示快照"}
    )
    logger.info(f"✅ 快照已创建: {snapshot.timestamp}")
    
    # 7. 显示统计信息
    logger.info("📊 显示系统统计...")
    perf_stats = scheduler.get_performance_stats()
    storage_stats = scheduler.snapshot_manager.get_storage_stats()
    
    logger.info(f"性能统计:")
    logger.info(f"  - 平均步骤时间: {perf_stats.get('avg_step_time', 0):.3f}s")
    logger.info(f"  - 最大步骤时间: {perf_stats.get('max_step_time', 0):.3f}s")
    
    logger.info(f"存储统计:")
    logger.info(f"  - 快照数量: {storage_stats['total_snapshots']}")
    logger.info(f"  - 存储大小: {storage_stats['total_size_mb']:.1f} MB")
    
    # 8. 停止模拟
    logger.info("🛑 停止模拟...")
    await scheduler.stop()
    
    logger.info("✨ 演示完成！")
    logger.info("💡 提示: 运行 'make dev' 启动完整的 Web 界面")


async def run_api_demo():
    """运行 API 演示"""
    logger.info("🌐 启动 API 服务器演示")
    
    try:
        import uvicorn
        from api.main import app
        
        # 启动 API 服务器
        config = uvicorn.Config(
            app, 
            host="127.0.0.1", 
            port=8000, 
            log_level="info"
        )
        server = uvicorn.Server(config)
        
        logger.info("🚀 API 服务器启动在 http://127.0.0.1:8000")
        logger.info("📚 API 文档地址: http://127.0.0.1:8000/docs")
        logger.info("🔌 WebSocket 地址: ws://127.0.0.1:8000/ws")
        
        await server.serve()
        
    except ImportError as e:
        logger.error(f"❌ 缺少依赖: {e}")
        logger.info("💡 请运行: pip install -e .")
    except Exception as e:
        logger.error(f"❌ 启动失败: {e}")


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        # 启动 API 服务器
        asyncio.run(run_api_demo())
    else:
        # 运行核心演示
        asyncio.run(run_demo())


if __name__ == "__main__":
    main()
