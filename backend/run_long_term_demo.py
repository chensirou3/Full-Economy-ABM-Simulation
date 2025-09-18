#!/usr/bin/env python3
"""
长期模拟演示脚本
20,000人口，30年时间跨度
"""

import asyncio
import time
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

async def run_long_term_simulation():
    """运行长期模拟"""
    print("🚀 ABM 经济体模拟系统 - 30年长期演示")
    print("👥 人口规模: 20,000")
    print("⏰ 时间跨度: 30年 (10,950天)")
    print("=" * 60)
    
    try:
        # 1. 加载长期场景配置
        print("📋 加载长期模拟场景...")
        from simcore.config import load_scenario_config
        
        scenario_path = Path("../scenarios/long_term_20k.yml")
        if not scenario_path.exists():
            print(f"❌ 场景文件不存在: {scenario_path}")
            return
        
        config = load_scenario_config(scenario_path)
        print(f"✅ 场景加载成功:")
        print(f"   • 人口: {config.population.N:,}")
        print(f"   • 模拟天数: {config.runtime.T_end_days:,}")
        print(f"   • 地图大小: {config.world.grid.rows}x{config.world.grid.cols}")
        print(f"   • 随机种子: {config.world.seed}")
        
        # 2. 初始化模拟
        print("\n🎮 初始化模拟器...")
        from simcore.scheduler import SimulationScheduler
        from simcore.telemetry import get_telemetry, EventType
        
        scheduler = SimulationScheduler(config)
        await scheduler.initialize()
        
        print(f"✅ 模拟器初始化完成:")
        print(f"   • 代理总数: {scheduler.simulation.get_agent_count():,}")
        print(f"   • 个人: {len(scheduler.simulation.persons):,}")
        print(f"   • 企业: {len(scheduler.simulation.firms):,}")
        print(f"   • 银行: {len(scheduler.simulation.banks):,}")
        
        # 3. 设置事件监听
        telemetry = get_telemetry()
        
        milestone_events = []
        
        def track_milestone(event):
            milestone_events.append({
                'time': scheduler.current_time,
                'type': event.event_type.value,
                'data': event.payload
            })
            print(f"📊 里程碑事件 [第{scheduler.current_time}天]: {event.event_type.value}")
        
        # 监听重要事件
        important_events = [
            EventType.FIRM_BANKRUPTCY,
            EventType.BANK_FAILURE,
            EventType.INTEREST_RATE_CHANGE,
            EventType.UNEMPLOYMENT_SPIKE,
            EventType.CHECKPOINT_CREATED,
        ]
        
        for event_type in important_events:
            telemetry.event_bus.subscribe(event_type.value, track_milestone)
        
        # 4. 开始模拟
        print(f"\n▶️  开始30年经济模拟 (加速运行)...")
        print("   • 每年显示一次进度报告")
        print("   • 每5年显示详细经济指标")
        print("   • 重要事件将实时显示")
        print()
        
        await scheduler.play(speed=50.0)  # 50倍速运行
        
        # 5. 监控进度
        start_real_time = time.time()
        last_report_year = 0
        
        while scheduler.current_time < config.runtime.T_end_days and scheduler.state.value == "running":
            await asyncio.sleep(0.5)  # 每0.5秒检查一次
            
            current_year = scheduler.current_time // 365
            
            # 每年报告一次进度
            if current_year > last_report_year:
                elapsed_real = time.time() - start_real_time
                progress = scheduler.current_time / config.runtime.T_end_days
                
                print(f"📅 第 {current_year:2d} 年 | "
                      f"进度: {progress:.1%} | "
                      f"实际用时: {elapsed_real:.1f}s | "
                      f"模拟速度: {scheduler.get_status().steps_per_second:.0f} steps/s")
                
                # 每5年显示详细指标
                if current_year % 5 == 0 and current_year > 0:
                    metrics = scheduler.simulation.get_economic_metrics()
                    print(f"     📈 经济指标:")
                    print(f"        GDP: {metrics['gdp']:,.0f}")
                    print(f"        失业率: {metrics['unemployment']:.1%}")
                    print(f"        通胀率: {metrics['inflation']:.1%}")
                    print(f"        政策利率: {metrics['policy_rate']:.1%}")
                    print(f"        活跃代理: {metrics['total_agents']:,}")
                
                last_report_year = current_year
        
        # 6. 模拟完成
        await scheduler.pause()
        
        total_real_time = time.time() - start_real_time
        final_metrics = scheduler.simulation.get_economic_metrics()
        
        print("\n" + "=" * 60)
        print("🎉 30年长期模拟完成！")
        print(f"⏰ 总用时: {total_real_time:.1f} 秒")
        print(f"🏃 平均速度: {scheduler.current_time / total_real_time:.0f} 模拟天/秒")
        
        print("\n📊 最终经济指标:")
        print(f"   • GDP: {final_metrics['gdp']:,.0f}")
        print(f"   • 失业率: {final_metrics['unemployment']:.1%}")
        print(f"   • 通胀率: {final_metrics['inflation']:.1%}")
        print(f"   • 政策利率: {final_metrics['policy_rate']:.1%}")
        print(f"   • 存活代理: {final_metrics['total_agents']:,}")
        
        print(f"\n📈 重要事件统计:")
        event_counts = {}
        for event in milestone_events:
            event_type = event['type']
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        for event_type, count in event_counts.items():
            print(f"   • {event_type}: {count} 次")
        
        # 7. 快照统计
        snapshot_stats = scheduler.snapshot_manager.get_storage_stats()
        print(f"\n💾 快照统计:")
        print(f"   • 快照数量: {snapshot_stats['total_snapshots']}")
        print(f"   • 存储大小: {snapshot_stats['total_size_mb']:.1f} MB")
        
        # 8. 演示回放功能
        print(f"\n⏪ 演示回放功能...")
        print(f"   当前时间: 第 {scheduler.current_time} 天")
        
        # 回到10年前
        rewind_target = max(0, scheduler.current_time - 3650)  # 10年前
        print(f"   倒带到: 第 {rewind_target} 天")
        
        await scheduler.rewind_to(rewind_target)
        print(f"   ✅ 倒带完成，当前时间: 第 {scheduler.current_time} 天")
        
        # 显示回放后的指标
        rewind_metrics = scheduler.simulation.get_economic_metrics()
        print(f"   📊 10年前的经济指标:")
        print(f"      GDP: {rewind_metrics['gdp']:,.0f}")
        print(f"      失业率: {rewind_metrics['unemployment']:.1%}")
        
        print("\n🎊 长期模拟演示完成！")
        print("💡 这展示了系统的:")
        print("   ✅ 大规模代理处理能力")
        print("   ✅ 长期时间模拟能力") 
        print("   ✅ 实时监控和报告")
        print("   ✅ 事件记录和回放")
        print("   ✅ 快照管理和存储")
        
    except Exception as e:
        print(f"\n❌ 模拟运行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        if 'scheduler' in locals():
            await scheduler.stop()


def main():
    """主函数"""
    print("🔧 准备运行长期模拟...")
    
    # 检查 Python 版本
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 或更高版本")
        return
    
    # 运行模拟
    try:
        asyncio.run(run_long_term_simulation())
    except KeyboardInterrupt:
        print("\n👋 模拟被用户中断")
    except Exception as e:
        print(f"\n❌ 运行失败: {e}")


if __name__ == "__main__":
    main()
