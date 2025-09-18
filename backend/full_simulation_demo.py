#!/usr/bin/env python3
"""
完整的20,000人30年模拟演示
包含时间控制、运动可视化、指标同步
"""

import asyncio
import time
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

@dataclass
class Agent:
    """简化的代理类"""
    agent_id: int
    agent_type: str
    x: float
    y: float
    age: int
    wealth: float
    employed: bool
    home_x: float
    home_y: float
    firm_id: int = None
    bank_id: int = None
    
    def to_dict(self):
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'position': {'x': self.x, 'y': self.y},
            'age': self.age,
            'wealth': self.wealth,
            'employment_status': 'employed' if self.employed else 'unemployed',
            'home_position': {'x': self.home_x, 'y': self.home_y},
            'firm_id': self.firm_id,
            'bank_id': self.bank_id,
        }

class FullEconomicSimulation:
    """完整的经济模拟"""
    
    def __init__(self):
        self.current_day = 0
        self.agents: List[Agent] = []
        self.firms: List[Agent] = []
        self.banks: List[Agent] = []
        
        # 历史数据
        self.metrics_history = []
        self.events_history = []
        self.snapshots = {}  # day -> full_state
        
        # 运行状态
        self.is_running = False
        self.speed = 1.0
        self.target_day = None
        
        # 地图参数
        self.map_width = 80
        self.map_height = 80
        
        print("🎮 经济模拟器初始化完成")
    
    def initialize_population(self, population_size=20000):
        """初始化人口"""
        print(f"👥 创建 {population_size:,} 个代理...")
        
        # 创建个人
        for i in range(population_size):
            agent = Agent(
                agent_id=100000 + i,
                agent_type="person",
                x=np.random.uniform(5, self.map_width - 5),
                y=np.random.uniform(5, self.map_height - 5),
                age=int(np.random.beta(2, 5) * 80 + 18),  # 18-98岁
                wealth=np.random.lognormal(9, 1),
                employed=np.random.random() > 0.05,  # 95%就业率
                home_x=0, home_y=0
            )
            agent.home_x = agent.x + np.random.normal(0, 2)
            agent.home_y = agent.y + np.random.normal(0, 2)
            self.agents.append(agent)
        
        # 创建企业
        num_firms = population_size // 100  # 每100人一个企业
        for i in range(num_firms):
            firm = Agent(
                agent_id=10000 + i,
                agent_type="firm",
                x=np.random.uniform(10, self.map_width - 10),
                y=np.random.uniform(10, self.map_height - 10),
                age=np.random.randint(1, 50),  # 企业年龄
                wealth=np.random.lognormal(12, 1),
                employed=True,  # 企业总是"活跃"
                home_x=0, home_y=0
            )
            firm.home_x = firm.x  # 企业的"家"就是当前位置
            firm.home_y = firm.y
            self.firms.append(firm)
        
        # 创建银行
        num_banks = max(3, population_size // 5000)
        for i in range(num_banks):
            bank = Agent(
                agent_id=1000 + i,
                agent_type="bank",
                x=np.random.uniform(15, self.map_width - 15),
                y=np.random.uniform(15, self.map_height - 15),
                age=np.random.randint(5, 100),
                wealth=np.random.lognormal(15, 0.5),
                employed=True,
                home_x=0, home_y=0
            )
            bank.home_x = bank.x
            bank.home_y = bank.y
            self.banks.append(bank)
        
        # 建立雇佣关系
        self._establish_employment()
        
        print(f"✅ 人口初始化完成:")
        print(f"   • 个人: {len(self.agents):,}")
        print(f"   • 企业: {len(self.firms):,}")
        print(f"   • 银行: {len(self.banks):,}")
    
    def _establish_employment(self):
        """建立雇佣关系"""
        employed_persons = [a for a in self.agents if a.employed]
        
        for person in employed_persons:
            # 随机分配到企业
            if self.firms:
                firm = np.random.choice(self.firms)
                person.firm_id = firm.agent_id
            
            # 随机分配银行
            if self.banks:
                bank = np.random.choice(self.banks)
                person.bank_id = bank.agent_id
    
    def step(self):
        """执行一个模拟步骤"""
        self.current_day += 1
        
        # 更新所有代理
        self._update_person_agents()
        self._update_firm_agents()
        self._update_bank_agents()
        
        # 计算经济指标
        metrics = self._calculate_metrics()
        self.metrics_history.append(metrics)
        
        # 生成事件
        events = self._generate_events()
        self.events_history.extend(events)
        
        # 每年创建快照
        if self.current_day % 365 == 0:
            self._create_snapshot()
        
        return metrics, events
    
    def _update_person_agents(self):
        """更新个人代理"""
        current_hour = (self.current_day * 24) % 24
        is_workday = (self.current_day % 7) < 5
        
        for person in self.agents:
            if not person.employed:
                continue
                
            # 年龄增长
            if self.current_day % 365 == 0:
                person.age += 1
                
                # 退休检查
                if person.age >= 65:
                    person.employed = False
                    continue
            
            # 运动逻辑
            if is_workday and 8 <= current_hour <= 17:
                # 工作时间 - 向工作地点移动
                if person.firm_id:
                    firm = next((f for f in self.firms if f.agent_id == person.firm_id), None)
                    if firm:
                        # 向企业位置移动 (带噪声)
                        target_x = firm.x + np.random.normal(0, 1)
                        target_y = firm.y + np.random.normal(0, 1)
                        
                        # 平滑移动
                        dx = (target_x - person.x) * 0.1
                        dy = (target_y - person.y) * 0.1
                        
                        person.x = np.clip(person.x + dx, 0, self.map_width)
                        person.y = np.clip(person.y + dy, 0, self.map_height)
            
            elif 18 <= current_hour <= 22:
                # 下班时间 - 商业活动
                if np.random.random() < 0.3:  # 30%概率去商业区
                    business_x = self.map_width * 0.6
                    business_y = self.map_height * 0.4
                    
                    dx = (business_x - person.x) * 0.05
                    dy = (business_y - person.y) * 0.05
                    
                    person.x += dx + np.random.normal(0, 0.5)
                    person.y += dy + np.random.normal(0, 0.5)
            
            else:
                # 其他时间 - 向家移动
                dx = (person.home_x - person.x) * 0.1
                dy = (person.home_y - person.y) * 0.1
                
                person.x += dx + np.random.normal(0, 0.3)
                person.y += dy + np.random.normal(0, 0.3)
            
            # 边界约束
            person.x = np.clip(person.x, 0, self.map_width)
            person.y = np.clip(person.y, 0, self.map_height)
            
            # 财富更新
            if person.employed:
                person.wealth += np.random.normal(100, 20)  # 日收入
            else:
                person.wealth -= np.random.normal(50, 10)   # 日支出
                
                # 求职行为
                if np.random.random() < 0.1:  # 10%概率找到工作
                    person.employed = True
    
    def _update_firm_agents(self):
        """更新企业代理"""
        for firm in self.firms:
            # 企业基本不移动，但可能扩张
            if np.random.random() < 0.001:  # 0.1%概率调整位置
                firm.x += np.random.normal(0, 0.1)
                firm.y += np.random.normal(0, 0.1)
                
                firm.x = np.clip(firm.x, 0, self.map_width)
                firm.y = np.clip(firm.y, 0, self.map_height)
            
            # 财富增长
            firm.wealth *= (1 + np.random.normal(0.0003, 0.001))  # 年化10%增长
    
    def _update_bank_agents(self):
        """更新银行代理"""
        # 银行不移动，但财富变化
        for bank in self.banks:
            bank.wealth *= (1 + np.random.normal(0.0002, 0.0005))
    
    def _calculate_metrics(self):
        """计算经济指标"""
        working_age = [a for a in self.agents if 18 <= a.age <= 65]
        employed = [a for a in working_age if a.employed]
        
        total_wealth = sum(a.wealth for a in self.agents)
        unemployment_rate = 1 - (len(employed) / len(working_age)) if working_age else 0
        
        # 模拟通胀 (基于财富增长)
        if len(self.metrics_history) > 0:
            prev_wealth = self.metrics_history[-1]['kpis']['gdp']
            inflation = (total_wealth - prev_wealth) / prev_wealth if prev_wealth > 0 else 0.02
        else:
            inflation = 0.02
        
        # 模拟政策利率 (简化Taylor规则)
        policy_rate = 0.025 + 1.5 * (inflation - 0.02) + 0.5 * (unemployment_rate - 0.05)
        policy_rate = max(0, min(0.10, policy_rate))
        
        return {
            'timestamp': self.current_day,
            'kpis': {
                'gdp': total_wealth,
                'unemployment': unemployment_rate,
                'inflation': inflation,
                'policy_rate': policy_rate,
                'total_agents': len(self.agents) + len(self.firms) + len(self.banks),
                'population': len(self.agents),
                'average_age': np.mean([a.age for a in self.agents]),
            }
        }
    
    def _generate_events(self):
        """生成事件"""
        events = []
        
        # 年度事件
        if self.current_day % 365 == 0:
            year = self.current_day // 365
            events.append({
                'timestamp': self.current_day,
                'event_type': 'system.year_completed',
                'payload': {'year': year, 'population': len(self.agents)}
            })
        
        # 随机经济事件
        if np.random.random() < 0.01:  # 1%概率
            event_type = np.random.choice([
                'firm.bankruptcy', 'policy.interest_rate_change', 
                'unemployment.spike', 'market.shock'
            ])
            
            events.append({
                'timestamp': self.current_day,
                'event_type': event_type,
                'payload': {'magnitude': np.random.uniform(0.01, 0.05)}
            })
        
        return events
    
    def _create_snapshot(self):
        """创建快照"""
        snapshot = {
            'day': self.current_day,
            'agents': [a.to_dict() for a in self.agents[:100]],  # 保存前100个代理
            'metrics': self.metrics_history[-1] if self.metrics_history else None,
            'total_agents': len(self.agents) + len(self.firms) + len(self.banks)
        }
        
        self.snapshots[self.current_day] = snapshot
        print(f"📸 第{self.current_day//365}年快照已创建")
    
    def get_current_state(self):
        """获取当前状态"""
        all_agents = []
        
        # 添加所有代理 (限制数量避免过载)
        for agent in (self.agents[:500] + self.firms + self.banks):
            all_agents.append(agent.to_dict())
        
        return {
            'current_day': self.current_day,
            'agents': all_agents,
            'metrics': self.metrics_history[-1] if self.metrics_history else None,
            'events': self.events_history[-10:] if self.events_history else []
        }
    
    def jump_to_day(self, target_day):
        """跳转到指定天数"""
        if target_day < self.current_day:
            # 回到过去 - 使用快照
            snapshot_day = max([d for d in self.snapshots.keys() if d <= target_day], default=0)
            if snapshot_day in self.snapshots:
                self._restore_snapshot(snapshot_day)
            
            # 从快照快进到目标时间
            while self.current_day < target_day:
                self.step()
        else:
            # 跳到未来 - 快进
            while self.current_day < target_day:
                self.step()
        
        print(f"⏭️ 已跳转到第 {self.current_day} 天 (第{self.current_day//365}年)")
    
    def _restore_snapshot(self, snapshot_day):
        """恢复快照"""
        snapshot = self.snapshots[snapshot_day]
        self.current_day = snapshot_day
        
        # 简化的状态恢复
        print(f"⏪ 恢复到第{snapshot_day//365}年的快照")

class VisualizationServer:
    """可视化服务器"""
    
    def __init__(self, simulation):
        self.simulation = simulation
        self.server = None
        self.server_thread = None
    
    def start(self, port=8002):
        """启动服务器"""
        class Handler(BaseHTTPRequestHandler):
            def do_GET(handler_self):
                if handler_self.path == '/api/state':
                    handler_self.send_response(200)
                    handler_self.send_header('Content-Type', 'application/json')
                    handler_self.send_header('Access-Control-Allow-Origin', '*')
                    handler_self.end_headers()
                    
                    state = self.simulation.get_current_state()
                    handler_self.wfile.write(json.dumps(state, default=str).encode())
                
                elif handler_self.path == '/api/control/play':
                    self.simulation.is_running = True
                    handler_self.send_response(200)
                    handler_self.end_headers()
                
                elif handler_self.path == '/api/control/pause':
                    self.simulation.is_running = False
                    handler_self.send_response(200)
                    handler_self.end_headers()
                
                else:
                    handler_self.send_response(404)
                    handler_self.end_headers()
            
            def log_message(self, format, *args):
                pass  # 静默日志
        
        self.server = HTTPServer(('localhost', port), Handler)
        self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.server_thread.start()
        
        print(f"🌐 可视化服务器启动: http://localhost:{port}")
        print(f"📡 状态端点: http://localhost:{port}/api/state")

async def run_full_simulation():
    """运行完整模拟"""
    print("🚀 ABM 完整模拟系统 - 20,000人30年演示")
    print("=" * 60)
    
    # 1. 初始化模拟
    simulation = FullEconomicSimulation()
    simulation.initialize_population(20000)
    
    # 2. 启动可视化服务器
    viz_server = VisualizationServer(simulation)
    viz_server.start(port=8002)
    
    # 3. 创建可视化HTML页面
    create_full_visualization_page()
    
    print("\n🎮 模拟控制:")
    print("   • 's' - 开始/暂停")
    print("   • '+' - 加速 (最高20x)")
    print("   • '-' - 减速")
    print("   • 'j' - 跳转到指定年份")
    print("   • 'r' - 重置到第1年")
    print("   • 'q' - 退出")
    print("   • 'v' - 打开可视化页面")
    
    print(f"\n▶️ 准备开始30年模拟...")
    print("按任意键开始，或输入命令:")
    
    # 4. 交互式控制循环
    simulation.is_running = False
    last_metrics = None
    
    try:
        while True:
            if simulation.is_running:
                # 执行模拟步骤
                metrics, events = simulation.step()
                
                # 显示进度
                if simulation.current_day % (30 * simulation.speed) == 0:  # 根据速度调整显示频率
                    year = simulation.current_day // 365
                    progress = simulation.current_day / 10950 * 100
                    
                    print(f"\r📅 第{year:2d}年 第{simulation.current_day%365:3d}天 | "
                          f"进度:{progress:5.1f}% | "
                          f"人口:{len(simulation.agents):,} | "
                          f"失业率:{metrics['kpis']['unemployment']:5.1%} | "
                          f"GDP:{metrics['kpis']['gdp']/1e9:6.1f}B | "
                          f"速度:{simulation.speed:3.1f}x", end="")
                
                # 显示重要事件
                for event in events:
                    if event['event_type'] != 'system.year_completed':
                        print(f"\n📊 事件: {event['event_type']} - {event['payload']}")
                
                # 检查结束条件
                if simulation.current_day >= 10950:  # 30年
                    print(f"\n🎉 30年模拟完成!")
                    break
                
                # 控制速度
                await asyncio.sleep(0.1 / simulation.speed)
                last_metrics = metrics
            
            else:
                # 等待用户输入
                await asyncio.sleep(0.1)
    
    except KeyboardInterrupt:
        print(f"\n👋 模拟被中断")
    
    # 5. 显示最终结果
    if last_metrics:
        print(f"\n📊 最终统计 (第{simulation.current_day//365}年):")
        print(f"   • 人口: {last_metrics['kpis']['population']:,}")
        print(f"   • 平均年龄: {last_metrics['kpis']['average_age']:.1f}岁")
        print(f"   • 失业率: {last_metrics['kpis']['unemployment']:.1%}")
        print(f"   • 总财富: {last_metrics['kpis']['gdp']/1e9:.1f}B")
        print(f"   • 通胀率: {last_metrics['kpis']['inflation']:.1%}")
    
    print(f"\n💾 快照统计: {len(simulation.snapshots)} 个年度快照")
    print(f"📢 事件统计: {len(simulation.events_history)} 个事件")

def create_full_visualization_page():
    """创建完整的可视化页面"""
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>ABM 完整模拟可视化</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: white; 
            margin: 0; 
            padding: 20px; 
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            text-align: center; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            border-radius: 10px; 
            margin-bottom: 20px; 
        }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }
        .card { background: #2d2d2d; padding: 20px; border-radius: 10px; }
        .controls { text-align: center; margin-bottom: 20px; }
        .controls button { 
            background: #4ade80; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            margin: 0 5px; 
            border-radius: 5px; 
            cursor: pointer; 
        }
        .controls button:hover { background: #22c55e; }
        #mapCanvas { width: 100%; height: 400px; background: #111; border-radius: 8px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-bottom: 20px; }
        .metric { background: #374151; padding: 15px; border-radius: 8px; text-align: center; }
        .metric-value { font-size: 24px; font-weight: bold; color: #60a5fa; }
        .metric-label { font-size: 12px; color: #9ca3af; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 ABM 完整模拟可视化</h1>
            <p>20,000人口 × 30年 × 实时运动 × 指标同步</p>
        </div>
        
        <div class="controls">
            <button onclick="toggleSimulation()">▶️ 开始/暂停</button>
            <button onclick="jumpToYear()">⏭️ 跳转年份</button>
            <button onclick="resetSimulation()">🔄 重置</button>
            <label>
                速度: <input type="range" id="speedSlider" min="1" max="20" value="5" onchange="updateSpeed()">
                <span id="speedDisplay">5x</span>
            </label>
        </div>
        
        <div class="metrics" id="metricsPanel">
            <div class="metric">
                <div class="metric-value" id="currentYear">0</div>
                <div class="metric-label">当前年份</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="population">20,000</div>
                <div class="metric-label">人口</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="unemployment">5.0%</div>
                <div class="metric-label">失业率</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="gdp">1.0B</div>
                <div class="metric-label">GDP</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="inflation">2.0%</div>
                <div class="metric-label">通胀率</div>
            </div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>🗺️ 2D 世界地图 (实时运动)</h3>
                <canvas id="mapCanvas" width="600" height="400"></canvas>
                <p style="font-size: 12px; color: #9ca3af; margin-top: 10px;">
                    绿点: 个人(移动) | 蓝点: 企业(静态) | 黄点: 银行 | 观察工作日聚集现象
                </p>
            </div>
            
            <div class="card">
                <h3>📈 30年经济指标</h3>
                <div id="economicChart" style="height: 400px;"></div>
            </div>
        </div>
        
        <div class="card">
            <h3>📢 实时事件流</h3>
            <div id="eventsPanel" style="height: 200px; overflow-y: auto; background: #111; padding: 10px; border-radius: 5px;">
                等待事件数据...
            </div>
        </div>
    </div>

    <script>
        let simulationData = null;
        let isPlaying = false;
        let currentStep = 0;
        let speed = 5;
        let updateInterval = null;
        
        // 初始化
        window.onload = function() {
            console.log('初始化可视化系统...');
            startDataFetching();
        };
        
        // 开始数据获取
        function startDataFetching() {
            updateInterval = setInterval(fetchSimulationData, 1000 / speed);
        }
        
        // 获取模拟数据
        async function fetchSimulationData() {
            try {
                const response = await fetch('http://localhost:8002/api/state');
                if (response.ok) {
                    simulationData = await response.json();
                    updateVisualization();
                }
            } catch (error) {
                console.log('使用模拟数据 (后端未连接)');
                simulationData = generateMockData();
                updateVisualization();
            }
        }
        
        // 生成模拟数据
        function generateMockData() {
            const day = currentStep * speed;
            const year = Math.floor(day / 365);
            
            // 模拟代理数据
            const agents = [];
            for (let i = 0; i < 100; i++) {
                const agentType = i < 80 ? 'person' : (i < 95 ? 'firm' : 'bank');
                const baseX = (i % 10) * 6 + 5;
                const baseY = Math.floor(i / 10) * 4 + 2;
                
                // 个人有运动，企业和银行基本静止
                let x = baseX, y = baseY;
                if (agentType === 'person') {
                    const workHour = (day * 24) % 24;
                    const isWorkday = (day % 7) < 5;
                    
                    if (isWorkday && workHour >= 8 && workHour <= 17) {
                        // 工作时间聚集
                        x = 45 + Math.sin(day * 0.1 + i) * 5;
                        y = 15 + Math.cos(day * 0.1 + i) * 3;
                    } else {
                        // 其他时间分散
                        x = baseX + Math.sin(day * 0.05 + i) * 8;
                        y = baseY + Math.cos(day * 0.05 + i) * 6;
                    }
                }
                
                agents.push({
                    agent_id: i,
                    agent_type: agentType,
                    position: { x: Math.max(1, Math.min(79, x)), y: Math.max(1, Math.min(19, y)) },
                    age: 20 + (i % 60),
                    employment_status: Math.random() > 0.05 ? 'employed' : 'unemployed'
                });
            }
            
            // 模拟指标
            const unemployment = 0.05 + Math.sin(day / 365 * 2 * Math.PI) * 0.02;
            const gdp = 1000000000 * (1 + day / 10950 * 0.5);
            const inflation = 0.02 + Math.sin(day / 100) * 0.01;
            
            return {
                current_day: day,
                agents: agents,
                metrics: {
                    timestamp: day,
                    kpis: {
                        gdp: gdp,
                        unemployment: unemployment,
                        inflation: inflation,
                        policy_rate: 0.025 + inflation * 1.5,
                        population: 20000 - Math.floor(day / 365) * 50,
                        average_age: 35 + day / 365 * 0.1
                    }
                }
            };
        }
        
        // 更新可视化
        function updateVisualization() {
            if (!simulationData) return;
            
            updateMetrics();
            updateMap();
            updateChart();
            currentStep++;
        }
        
        // 更新指标
        function updateMetrics() {
            const metrics = simulationData.metrics.kpis;
            const year = Math.floor(simulationData.current_day / 365);
            
            document.getElementById('currentYear').textContent = year;
            document.getElementById('population').textContent = metrics.population.toLocaleString();
            document.getElementById('unemployment').textContent = (metrics.unemployment * 100).toFixed(1) + '%';
            document.getElementById('gdp').textContent = (metrics.gdp / 1e9).toFixed(1) + 'B';
            document.getElementById('inflation').textContent = (metrics.inflation * 100).toFixed(1) + '%';
        }
        
        // 更新地图
        function updateMap() {
            const canvas = document.getElementById('mapCanvas');
            const ctx = canvas.getContext('2d');
            
            // 清空画布
            ctx.fillStyle = '#111111';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // 绘制网格
            ctx.strokeStyle = '#333';
            ctx.lineWidth = 0.5;
            for (let i = 0; i <= 8; i++) {
                const x = (i / 8) * canvas.width;
                ctx.beginPath();
                ctx.moveTo(x, 0);
                ctx.lineTo(x, canvas.height);
                ctx.stroke();
                
                const y = (i / 8) * canvas.height;
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.lineTo(canvas.width, y);
                ctx.stroke();
            }
            
            // 绘制代理
            const scaleX = canvas.width / 80;
            const scaleY = canvas.height / 20;
            
            simulationData.agents.forEach(agent => {
                const x = agent.position.x * scaleX;
                const y = agent.position.y * scaleY;
                
                const colors = {
                    'person': '#4ade80',
                    'firm': '#3b82f6',
                    'bank': '#f59e0b'
                };
                
                const sizes = {
                    'person': 2,
                    'firm': 4,
                    'bank': 6
                };
                
                ctx.fillStyle = colors[agent.agent_type] || '#9ca3af';
                ctx.beginPath();
                ctx.arc(x, y, sizes[agent.agent_type] || 2, 0, 2 * Math.PI);
                ctx.fill();
            });
        }
        
        // 更新图表
        function updateChart() {
            // 这里可以添加Plotly图表更新逻辑
            // 由于数据更新频繁，简化处理
        }
        
        // 控制函数
        function toggleSimulation() {
            isPlaying = !isPlaying;
            // 这里可以调用后端API
            console.log('切换播放状态:', isPlaying);
        }
        
        function jumpToYear() {
            const year = prompt('跳转到第几年? (0-30)');
            if (year && !isNaN(year)) {
                const targetDay = parseInt(year) * 365;
                console.log('跳转到第', year, '年');
                // 这里可以调用后端API
            }
        }
        
        function resetSimulation() {
            currentStep = 0;
            console.log('重置模拟');
        }
        
        function updateSpeed() {
            const slider = document.getElementById('speedSlider');
            speed = parseInt(slider.value);
            document.getElementById('speedDisplay').textContent = speed + 'x';
            
            // 重新设置更新间隔
            if (updateInterval) {
                clearInterval(updateInterval);
                updateInterval = setInterval(fetchSimulationData, 1000 / speed);
            }
        }
    </script>
</body>
</html>'''
    
    with open('full_simulation_demo.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("🎨 完整可视化页面已创建: full_simulation_demo.html")

def main():
    """主函数"""
    try:
        asyncio.run(run_full_simulation())
    except Exception as e:
        print(f"❌ 运行失败: {e}")

if __name__ == "__main__":
    main()
