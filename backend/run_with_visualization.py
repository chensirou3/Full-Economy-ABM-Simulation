#!/usr/bin/env python3
"""
带可视化的模拟演示
启动后端API服务器，提供可视化数据
"""

import asyncio
import sys
import time
from pathlib import Path
import json

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

async def run_visualization_demo():
    """运行可视化演示"""
    print("🎨 ABM 经济体模拟系统 - 可视化演示")
    print("=" * 50)
    
    try:
        # 1. 加载配置
        from simcore.config import load_scenario_config
        
        config = load_scenario_config("../scenarios/long_term_20k.yml")
        print(f"✅ 场景配置: {config.population.N:,} 人口")
        
        # 2. 创建简化的可视化数据生成器
        print("\n🎮 创建可视化数据生成器...")
        
        viz_data = create_visualization_data(config)
        
        # 3. 生成模拟数据用于可视化
        print("\n📊 生成可视化数据...")
        
        # 代理位置数据
        agents_data = generate_agents_visualization_data(config)
        print(f"✅ 生成了 {len(agents_data)} 个代理的可视化数据")
        
        # 经济指标数据
        metrics_data = generate_metrics_visualization_data()
        print(f"✅ 生成了 {len(metrics_data)} 个时间点的指标数据")
        
        # 事件数据
        events_data = generate_events_visualization_data()
        print(f"✅ 生成了 {len(events_data)} 个事件用于可视化")
        
        # 4. 保存可视化数据为JSON (供前端使用)
        print("\n💾 保存可视化数据...")
        
        visualization_package = {
            "metadata": {
                "population": config.population.N,
                "simulation_days": config.runtime.T_end_days,
                "grid_size": [config.world.grid.rows, config.world.grid.cols],
                "generated_at": time.time(),
            },
            "agents": agents_data[:1000],  # 限制数量避免文件过大
            "metrics": metrics_data,
            "events": events_data,
            "world_state": {
                "current_time": 0,
                "tiles": generate_tile_data(config),
            }
        }
        
        # 保存到文件
        viz_file = Path("visualization_data.json")
        with open(viz_file, 'w', encoding='utf-8') as f:
            json.dump(visualization_package, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 可视化数据已保存到: {viz_file}")
        print(f"   文件大小: {viz_file.stat().st_size / 1024:.1f} KB")
        
        # 5. 展示可视化数据结构
        print("\n🔍 可视化数据结构预览:")
        print("📍 代理数据示例:")
        for i, agent in enumerate(agents_data[:3]):
            print(f"   {i+1}. ID:{agent['agent_id']} 类型:{agent['agent_type']} "
                  f"位置:({agent['position']['x']:.1f},{agent['position']['y']:.1f}) "
                  f"状态:{agent['status']}")
        
        print("\n📊 指标数据示例:")
        for i, metric in enumerate(metrics_data[:3]):
            print(f"   时间{metric['timestamp']}: GDP:{metric['kpis']['gdp']:.0f} "
                  f"失业率:{metric['kpis']['unemployment']:.1%} "
                  f"通胀:{metric['kpis']['inflation']:.1%}")
        
        print("\n📢 事件数据示例:")
        for i, event in enumerate(events_data[:3]):
            print(f"   {event['timestamp']}: {event['event_type']} - {event['payload']}")
        
        # 6. 启动简化的API服务器
        print(f"\n🌐 启动可视化API服务器...")
        await start_visualization_server(visualization_package)
        
    except Exception as e:
        print(f"❌ 可视化演示失败: {e}")
        import traceback
        traceback.print_exc()

def create_visualization_data(config):
    """创建可视化数据生成器"""
    import numpy as np
    
    # 设置随机种子确保可复现
    np.random.seed(config.world.seed)
    
    return {
        "config": config,
        "rng": np.random.RandomState(config.world.seed)
    }

def generate_agents_visualization_data(config):
    """生成代理可视化数据"""
    import numpy as np
    
    agents = []
    
    # 生成个人代理
    for i in range(config.population.N):
        agent = {
            "agent_id": 100000 + i,
            "agent_type": "person",
            "status": "active",
            "position": {
                "x": np.random.uniform(0, config.world.grid.cols),
                "y": np.random.uniform(0, config.world.grid.rows)
            },
            "balance_sheet": {
                "total_assets": np.random.lognormal(9, 1),
                "total_liabilities": np.random.lognormal(8, 1),
                "net_worth": 0  # 会在后面计算
            },
            # 个人特定属性
            "age": int(np.random.beta(2, 5) * 100),
            "employment_status": np.random.choice(["employed", "unemployed"], p=[0.95, 0.05]),
            "wage": np.random.lognormal(10.5, 0.5) if np.random.random() > 0.05 else 0,
        }
        agent["balance_sheet"]["net_worth"] = agent["balance_sheet"]["total_assets"] - agent["balance_sheet"]["total_liabilities"]
        agents.append(agent)
    
    # 生成企业代理
    num_firms = config.population.N // 100  # 每100人一个企业
    for i in range(num_firms):
        agent = {
            "agent_id": 10000 + i,
            "agent_type": "firm",
            "status": "active",
            "position": {
                "x": np.random.uniform(0, config.world.grid.cols),
                "y": np.random.uniform(0, config.world.grid.rows)
            },
            "balance_sheet": {
                "total_assets": np.random.lognormal(12, 1),
                "total_liabilities": np.random.lognormal(11, 1),
                "net_worth": 0
            },
            # 企业特定属性
            "sector": np.random.choice(config.firms.sectors),
            "num_employees": int(np.random.pareto(1.16) + 1),
            "current_output": np.random.lognormal(8, 1),
            "price": np.random.normal(100, 20),
        }
        agent["balance_sheet"]["net_worth"] = agent["balance_sheet"]["total_assets"] - agent["balance_sheet"]["total_liabilities"]
        agents.append(agent)
    
    # 生成银行代理
    num_banks = max(3, config.population.N // 5000)  # 每5000人一个银行
    for i in range(num_banks):
        agent = {
            "agent_id": 1000 + i,
            "agent_type": "bank",
            "status": "active",
            "position": {
                "x": np.random.uniform(0, config.world.grid.cols),
                "y": np.random.uniform(0, config.world.grid.rows)
            },
            "balance_sheet": {
                "total_assets": np.random.lognormal(15, 0.5),
                "total_liabilities": np.random.lognormal(14.8, 0.5),
                "net_worth": 0
            },
            # 银行特定属性
            "capital_ratio": np.random.normal(0.12, 0.02),
            "total_loans": np.random.randint(50, 500),
            "total_deposits": np.random.lognormal(14.5, 0.5),
        }
        agent["balance_sheet"]["net_worth"] = agent["balance_sheet"]["total_assets"] - agent["balance_sheet"]["total_liabilities"]
        agents.append(agent)
    
    # 生成央行
    agents.append({
        "agent_id": 0,
        "agent_type": "central_bank",
        "status": "active",
        "position": {
            "x": config.world.grid.cols / 2,
            "y": config.world.grid.rows / 2
        },
        "balance_sheet": {
            "total_assets": 1000000000,  # 10亿
            "total_liabilities": 950000000,  # 9.5亿
            "net_worth": 50000000  # 5000万
        },
        "policy_rate": config.policy.r_star,
        "inflation_target": config.policy.pi_star,
    })
    
    return agents

def generate_metrics_visualization_data():
    """生成指标可视化数据"""
    import numpy as np
    
    # 模拟30年的月度数据
    months = 30 * 12  # 360个月
    metrics_data = []
    
    # 初始值
    gdp = 1000000
    unemployment = 0.05
    inflation = 0.02
    policy_rate = 0.025
    
    for month in range(months):
        # 模拟经济周期
        cycle_phase = month / 120  # 10年周期
        
        # GDP 增长（带周期性）
        gdp_growth = 0.003 + 0.002 * np.sin(cycle_phase * 2 * np.pi) + np.random.normal(0, 0.001)
        gdp *= (1 + gdp_growth)
        
        # 失业率（反周期）
        unemployment_change = -0.5 * gdp_growth + np.random.normal(0, 0.002)
        unemployment = max(0.01, min(0.15, unemployment + unemployment_change))
        
        # 通胀率（带趋势和噪声）
        inflation_target = 0.02
        inflation += 0.1 * (inflation_target - inflation) + np.random.normal(0, 0.003)
        inflation = max(-0.02, min(0.08, inflation))
        
        # 政策利率（Taylor规则简化版）
        taylor_rate = 0.025 + 1.5 * (inflation - 0.02) + 0.5 * (unemployment - 0.05)
        policy_rate += 0.1 * (taylor_rate - policy_rate) + np.random.normal(0, 0.001)
        policy_rate = max(0, min(0.10, policy_rate))
        
        metrics_data.append({
            "timestamp": month * 30,  # 转换为天
            "kpis": {
                "gdp": gdp,
                "unemployment": unemployment,
                "inflation": inflation,
                "policy_rate": policy_rate,
                "total_agents": 20000 + np.random.randint(-100, 100),
                "credit_growth": np.random.normal(0.05, 0.02),
            }
        })
    
    return metrics_data

def generate_events_visualization_data():
    """生成事件可视化数据"""
    import numpy as np
    
    events = []
    
    # 模拟30年的重要事件
    for year in range(30):
        base_time = year * 365
        
        # 每年的常规事件
        events.extend([
            {
                "timestamp": base_time + np.random.randint(0, 365),
                "event_type": "system.checkpoint_created",
                "actor_id": None,
                "payload": {"year": year + 1}
            }
        ])
        
        # 随机经济事件
        if np.random.random() < 0.3:  # 30%概率
            events.append({
                "timestamp": base_time + np.random.randint(0, 365),
                "event_type": "policy.interest_rate_change",
                "actor_id": 0,
                "payload": {
                    "old_rate": np.random.normal(0.03, 0.01),
                    "new_rate": np.random.normal(0.03, 0.01),
                    "reason": "economic_conditions"
                }
            })
        
        if np.random.random() < 0.1:  # 10%概率
            events.append({
                "timestamp": base_time + np.random.randint(0, 365),
                "event_type": "firm.bankruptcy",
                "actor_id": np.random.randint(10000, 10200),
                "payload": {
                    "sector": np.random.choice(["agri", "manu", "services"]),
                    "employees_affected": np.random.randint(10, 100)
                }
            })
        
        if np.random.random() < 0.05:  # 5%概率
            events.append({
                "timestamp": base_time + np.random.randint(0, 365),
                "event_type": "unemployment.spike",
                "actor_id": None,
                "payload": {
                    "region": f"region_{np.random.randint(1, 5)}",
                    "magnitude": np.random.uniform(0.02, 0.05)
                }
            })
    
    return sorted(events, key=lambda x: x['timestamp'])

def generate_tile_data(config):
    """生成地块可视化数据"""
    import numpy as np
    
    tiles = []
    
    # 为地图的每个格子生成基础数据
    for y in range(0, config.world.grid.rows, 5):  # 每5格采样一次
        for x in range(0, config.world.grid.cols, 5):
            tile = {
                "x": x,
                "y": y,
                "type": np.random.choice(["land", "water", "mountain", "city"], 
                                       p=[0.6, 0.2, 0.15, 0.05]),
                "properties": {
                    "population_density": np.random.exponential(100),
                    "unemployment_rate": np.random.beta(2, 20),  # 偏向低失业率
                    "average_income": np.random.lognormal(10, 0.5),
                }
            }
            tiles.append(tile)
    
    return tiles

async def start_visualization_server(data):
    """启动简化的可视化服务器"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    import json
    
    class VisualizationHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/api/visualization/data':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(data).encode())
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "healthy", "service": "visualization"}')
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            pass  # 禁用日志
    
    server = HTTPServer(('localhost', 8001), VisualizationHandler)
    
    # 在后台线程运行服务器
    def run_server():
        print("🌐 可视化API服务器启动在 http://localhost:8001")
        print("📡 可视化数据端点: http://localhost:8001/api/visualization/data")
        server.serve_forever()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待一段时间让用户查看
    print("\n💡 可视化服务器正在运行...")
    print("🔗 您可以访问以下端点获取可视化数据:")
    print("   • http://localhost:8001/health - 健康检查")
    print("   • http://localhost:8001/api/visualization/data - 完整可视化数据")
    
    print("\n📊 数据包含:")
    print(f"   • {len(data['agents'])} 个代理的位置和状态")
    print(f"   • {len(data['metrics'])} 个时间点的经济指标")
    print(f"   • {len(data['events'])} 个经济事件")
    print(f"   • {len(data['world_state']['tiles'])} 个地块信息")
    
    print("\n🎨 前端可视化组件可以使用这些数据:")
    print("   • PixiJS 渲染代理位置和移动")
    print("   • Plotly 绘制经济指标图表") 
    print("   • 实时事件流显示")
    print("   • 热力图显示地区经济状况")
    
    # 保持服务器运行30秒
    print(f"\n⏰ 服务器将运行30秒供测试...")
    await asyncio.sleep(30)
    
    server.shutdown()
    print("✅ 可视化服务器已关闭")

def main():
    """主函数"""
    try:
        asyncio.run(run_visualization_demo())
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")

if __name__ == "__main__":
    main()
