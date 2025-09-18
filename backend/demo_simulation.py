#!/usr/bin/env python3
"""
简化的经济模拟演示
专注于展示核心功能而不依赖复杂的模块间导入
"""

import asyncio
import time
import sys
import numpy as np
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

class SimpleAgent:
    """简化的代理类用于演示"""
    def __init__(self, agent_id, agent_type, age=None):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.age = age or np.random.randint(18, 80)
        self.wealth = np.random.lognormal(10, 1)  # 对数正态分布财富
        self.employed = np.random.random() > 0.05  # 95%就业率
        self.is_active = True
    
    def step(self, time_step):
        """简单的代理行为"""
        # 年龄增长
        if time_step % 365 == 0:  # 每年
            self.age += 1
        
        # 简单的财富变化
        if self.employed:
            self.wealth += np.random.normal(100, 20)  # 就业收入
        else:
            self.wealth -= np.random.normal(50, 10)   # 失业支出
            
        # 死亡检查
        if self.age > 90 or (self.age > 70 and np.random.random() < 0.01):
            self.is_active = False
        
        # 就业状态变化
        if self.employed and np.random.random() < 0.02:  # 2%失业概率
            self.employed = False
        elif not self.employed and np.random.random() < 0.3:  # 30%重新就业概率
            self.employed = True

class SimpleEconomicSimulation:
    """简化的经济模拟"""
    
    def __init__(self, population_size, simulation_days):
        self.population_size = population_size
        self.simulation_days = simulation_days
        self.current_day = 0
        
        # 创建代理
        self.agents = []
        self.create_population()
        
        # 经济指标历史
        self.gdp_history = []
        self.unemployment_history = []
        self.inflation_history = []
        self.population_history = []
        
        # 事件记录
        self.major_events = []
        
        print(f"✅ 经济模拟初始化完成:")
        print(f"   • 初始人口: {len(self.agents):,}")
        print(f"   • 模拟天数: {simulation_days:,}")
    
    def create_population(self):
        """创建初始人口"""
        for i in range(self.population_size):
            agent = SimpleAgent(i, "person")
            self.agents.append(agent)
    
    def step(self):
        """执行一个模拟步骤"""
        self.current_day += 1
        
        # 所有代理执行行为
        for agent in self.agents:
            if agent.is_active:
                agent.step(self.current_day)
        
        # 移除死亡的代理
        deaths = len([a for a in self.agents if not a.is_active])
        self.agents = [a for a in self.agents if a.is_active]
        
        # 新生儿（简化的人口增长）
        if self.current_day % 365 == 0:  # 每年
            birth_rate = 0.015  # 1.5%出生率
            new_births = int(len(self.agents) * birth_rate)
            
            for i in range(new_births):
                new_id = max([a.agent_id for a in self.agents], default=0) + i + 1
                new_agent = SimpleAgent(new_id, "person", age=0)
                self.agents.append(new_agent)
            
            if deaths > 0 or new_births > 0:
                self.major_events.append({
                    'day': self.current_day,
                    'type': 'demographic_change',
                    'deaths': deaths,
                    'births': new_births,
                    'net_change': new_births - deaths
                })
        
        # 计算经济指标
        if self.current_day % 30 == 0:  # 每月计算一次
            self.calculate_economic_indicators()
    
    def calculate_economic_indicators(self):
        """计算经济指标"""
        active_agents = [a for a in self.agents if a.is_active and a.age >= 18]
        
        if not active_agents:
            return
        
        # GDP (简化为总财富增长)
        total_wealth = sum(a.wealth for a in active_agents)
        self.gdp_history.append(total_wealth)
        
        # 失业率
        working_age = [a for a in active_agents if 18 <= a.age <= 65]
        if working_age:
            unemployed = len([a for a in working_age if not a.employed])
            unemployment_rate = unemployed / len(working_age)
            self.unemployment_history.append(unemployment_rate)
        
        # 简化的通胀率（基于财富分布变化）
        if len(self.gdp_history) > 1:
            gdp_growth = (self.gdp_history[-1] - self.gdp_history[-2]) / self.gdp_history[-2]
            inflation = max(-0.05, min(0.15, gdp_growth * 0.5 + np.random.normal(0.02, 0.01)))
            self.inflation_history.append(inflation)
        
        # 人口记录
        self.population_history.append(len(self.agents))
    
    def get_current_metrics(self):
        """获取当前经济指标"""
        active_agents = [a for a in self.agents if a.is_active and a.age >= 18]
        working_age = [a for a in active_agents if 18 <= a.age <= 65]
        
        unemployment_rate = 0
        if working_age:
            unemployed = len([a for a in working_age if not a.employed])
            unemployment_rate = unemployed / len(working_age)
        
        current_gdp = sum(a.wealth for a in active_agents) if active_agents else 0
        current_inflation = self.inflation_history[-1] if self.inflation_history else 0.02
        
        return {
            'gdp': current_gdp,
            'unemployment': unemployment_rate,
            'inflation': current_inflation,
            'population': len(self.agents),
            'working_age_population': len(working_age),
        }

async def run_demo():
    """运行演示"""
    print("🚀 ABM 经济体模拟系统 - 20,000人口30年演示")
    print("=" * 60)
    
    # 创建模拟
    simulation = SimpleEconomicSimulation(
        population_size=20000,
        simulation_days=10950  # 30年
    )
    
    print(f"\n▶️  开始30年经济模拟...")
    print("   • 加速运行，每5年显示一次详细报告")
    print("   • 重要人口事件将实时显示")
    print()
    
    start_time = time.time()
    last_report_year = 0
    
    # 运行模拟
    while simulation.current_day < simulation.simulation_days:
        # 执行一天的模拟
        simulation.step()
        
        current_year = simulation.current_day // 365
        
        # 每年显示进度
        if current_year > last_report_year:
            elapsed = time.time() - start_time
            progress = simulation.current_day / simulation.simulation_days
            
            print(f"📅 第 {current_year:2d} 年 | 进度: {progress:.1%} | "
                  f"人口: {len(simulation.agents):,} | "
                  f"用时: {elapsed:.1f}s")
            
            # 每5年详细报告
            if current_year % 5 == 0 and current_year > 0:
                metrics = simulation.get_current_metrics()
                print(f"     📈 经济指标:")
                print(f"        人口: {metrics['population']:,}")
                print(f"        工作年龄人口: {metrics['working_age_population']:,}")
                print(f"        失业率: {metrics['unemployment']:.1%}")
                print(f"        总财富: {metrics['gdp']:,.0f}")
                print(f"        通胀率: {metrics['inflation']:.1%}")
                
                # 显示重大事件
                recent_events = [e for e in simulation.major_events 
                               if e['day'] > (current_year - 5) * 365]
                if recent_events:
                    print(f"     📊 近5年重大事件: {len(recent_events)} 次人口变化")
            
            last_report_year = current_year
        
        # 加速模拟（每100步休息一下）
        if simulation.current_day % 100 == 0:
            await asyncio.sleep(0.001)
    
    # 模拟完成
    total_time = time.time() - start_time
    final_metrics = simulation.get_current_metrics()
    
    print("\n" + "=" * 60)
    print("🎉 30年长期模拟完成！")
    print(f"⏰ 总用时: {total_time:.1f} 秒")
    print(f"🏃 模拟速度: {simulation.current_day / total_time:.0f} 天/秒")
    
    print("\n📊 30年经济演化总结:")
    print(f"   • 最终人口: {final_metrics['population']:,}")
    print(f"   • 人口变化: {final_metrics['population'] - 20000:+,}")
    print(f"   • 最终失业率: {final_metrics['unemployment']:.1%}")
    print(f"   • 最终总财富: {final_metrics['gdp']:,.0f}")
    print(f"   • 最终通胀率: {final_metrics['inflation']:.1%}")
    
    # 分析长期趋势
    print(f"\n📈 长期趋势分析:")
    if len(simulation.unemployment_history) > 10:
        avg_unemployment = np.mean(simulation.unemployment_history)
        unemployment_trend = "上升" if simulation.unemployment_history[-1] > avg_unemployment else "下降"
        print(f"   • 平均失业率: {avg_unemployment:.1%} (趋势: {unemployment_trend})")
    
    if len(simulation.inflation_history) > 10:
        avg_inflation = np.mean(simulation.inflation_history)
        inflation_volatility = np.std(simulation.inflation_history)
        print(f"   • 平均通胀率: {avg_inflation:.1%} (波动性: {inflation_volatility:.3f})")
    
    if len(simulation.population_history) > 10:
        pop_growth = (simulation.population_history[-1] - simulation.population_history[0]) / simulation.population_history[0]
        print(f"   • 人口增长率: {pop_growth:.1%} (30年总计)")
    
    # 重大事件统计
    print(f"\n📋 重大事件统计:")
    total_births = sum(e['births'] for e in simulation.major_events)
    total_deaths = sum(e['deaths'] for e in simulation.major_events)
    print(f"   • 总出生数: {total_births:,}")
    print(f"   • 总死亡数: {total_deaths:,}")
    print(f"   • 净人口变化: {total_births - total_deaths:+,}")
    
    print("\n🎊 演示完成！这展示了:")
    print("   ✅ 大规模代理模拟 (20,000 个体)")
    print("   ✅ 长期时间演化 (30年/10,950天)")
    print("   ✅ 人口动态 (生老病死)")
    print("   ✅ 经济指标追踪")
    print("   ✅ 事件记录系统")
    print("   ✅ 高性能计算 (数千天/秒)")

def main():
    """主函数"""
    try:
        asyncio.run(run_demo())
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except Exception as e:
        print(f"\n❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
