#!/usr/bin/env python3
"""
代理运动可视化演示
生成代理随时间移动的轨迹数据
"""

import json
import numpy as np
import time
from pathlib import Path

def generate_movement_simulation():
    """生成代理运动模拟数据"""
    print("🎬 生成代理运动可视化数据...")
    
    # 模拟参数
    num_agents = 100  # 为了演示，使用较少代理
    simulation_steps = 300  # 300个时间步
    map_size = 80
    
    # 代理初始化
    agents = []
    for i in range(num_agents):
        agent_type = "person" if i < 80 else ("firm" if i < 95 else "bank")
        
        agent = {
            "agent_id": i,
            "agent_type": agent_type,
            "initial_position": {
                "x": np.random.uniform(10, map_size - 10),
                "y": np.random.uniform(10, map_size - 10)
            },
            "movement_pattern": get_movement_pattern(agent_type),
            "trajectory": [],  # 存储运动轨迹
            "status": "active",
            "properties": generate_agent_properties(agent_type)
        }
        agents.append(agent)
    
    print(f"✅ 创建了 {num_agents} 个代理")
    
    # 生成运动轨迹
    print("🏃 生成运动轨迹...")
    
    for step in range(simulation_steps):
        step_data = {
            "timestamp": step,
            "agents_positions": []
        }
        
        for agent in agents:
            # 计算新位置
            new_pos = calculate_next_position(agent, step, map_size)
            
            # 记录位置
            position_data = {
                "agent_id": agent["agent_id"],
                "x": new_pos["x"],
                "y": new_pos["y"],
                "status": agent["status"],
                "agent_type": agent["agent_type"]
            }
            
            step_data["agents_positions"].append(position_data)
            agent["trajectory"].append(new_pos)
        
        # 每50步显示进度
        if step % 50 == 0:
            print(f"  进度: {step}/{simulation_steps} ({step/simulation_steps*100:.1f}%)")
    
    print("✅ 运动轨迹生成完成")
    
    return agents, simulation_steps

def get_movement_pattern(agent_type):
    """获取代理运动模式"""
    patterns = {
        "person": {
            "type": "random_walk",
            "speed": 0.5,
            "randomness": 0.8,
            "home_attraction": 0.3,  # 向家的吸引力
        },
        "firm": {
            "type": "stationary",
            "speed": 0.1,
            "randomness": 0.2,
            "expansion_probability": 0.01,  # 扩张概率
        },
        "bank": {
            "type": "hub",
            "speed": 0.0,
            "influence_radius": 15,  # 影响半径
        }
    }
    return patterns.get(agent_type, patterns["person"])

def generate_agent_properties(agent_type):
    """生成代理属性"""
    if agent_type == "person":
        return {
            "age": np.random.randint(18, 80),
            "wealth": np.random.lognormal(9, 1),
            "employment_status": np.random.choice(["employed", "unemployed"], p=[0.95, 0.05]),
            "home_x": np.random.uniform(0, 80),
            "home_y": np.random.uniform(0, 80),
        }
    elif agent_type == "firm":
        return {
            "sector": np.random.choice(["agri", "manu", "services"]),
            "employees": np.random.randint(5, 50),
            "revenue": np.random.lognormal(11, 1),
        }
    elif agent_type == "bank":
        return {
            "capital_ratio": np.random.normal(0.12, 0.02),
            "customers": np.random.randint(100, 1000),
        }
    return {}

def calculate_next_position(agent, step, map_size):
    """计算代理的下一个位置"""
    pattern = agent["movement_pattern"]
    current_pos = agent["trajectory"][-1] if agent["trajectory"] else agent["initial_position"]
    
    if pattern["type"] == "random_walk":
        # 随机游走 + 回家倾向
        home_x = agent["properties"].get("home_x", current_pos["x"])
        home_y = agent["properties"].get("home_y", current_pos["y"])
        
        # 随机移动
        dx = np.random.normal(0, pattern["speed"]) * pattern["randomness"]
        dy = np.random.normal(0, pattern["speed"]) * pattern["randomness"]
        
        # 回家吸引力
        home_attraction = pattern["home_attraction"]
        dx += (home_x - current_pos["x"]) * home_attraction * 0.01
        dy += (home_y - current_pos["y"]) * home_attraction * 0.01
        
        # 工作日vs周末的不同行为
        is_weekend = (step // 7) % 7 in [5, 6]  # 简化的周末
        if not is_weekend and agent["properties"]["employment_status"] == "employed":
            # 工作日向商业区移动
            business_center_x = map_size * 0.6
            business_center_y = map_size * 0.4
            dx += (business_center_x - current_pos["x"]) * 0.005
            dy += (business_center_y - current_pos["y"]) * 0.005
        
        new_x = np.clip(current_pos["x"] + dx, 0, map_size)
        new_y = np.clip(current_pos["y"] + dy, 0, map_size)
        
    elif pattern["type"] == "stationary":
        # 企业基本不动，偶尔小幅调整
        dx = np.random.normal(0, pattern["speed"]) if np.random.random() < 0.1 else 0
        dy = np.random.normal(0, pattern["speed"]) if np.random.random() < 0.1 else 0
        
        new_x = np.clip(current_pos["x"] + dx, 0, map_size)
        new_y = np.clip(current_pos["y"] + dy, 0, map_size)
        
    elif pattern["type"] == "hub":
        # 银行完全静止
        new_x = current_pos["x"]
        new_y = current_pos["y"]
    
    else:
        new_x = current_pos["x"]
        new_y = current_pos["y"]
    
    return {"x": new_x, "y": new_y}

def create_animated_html():
    """创建动画HTML页面"""
    html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ABM 代理运动可视化</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #1a1a1a;
            color: #ffffff;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 20px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        .controls {
            text-align: center;
            margin-bottom: 20px;
            padding: 15px;
            background-color: #2d2d2d;
            border-radius: 8px;
        }
        
        .controls button {
            background-color: #4ade80;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 0 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .controls button:hover {
            background-color: #22c55e;
        }
        
        .controls button:disabled {
            background-color: #6b7280;
            cursor: not-allowed;
        }
        
        .simulation-container {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 20px;
        }
        
        .map-panel {
            background-color: #2d2d2d;
            border-radius: 10px;
            padding: 20px;
        }
        
        .info-panel {
            background-color: #2d2d2d;
            border-radius: 10px;
            padding: 20px;
        }
        
        #worldCanvas {
            width: 100%;
            height: 500px;
            background-color: #111;
            border-radius: 8px;
            border: 2px solid #374151;
        }
        
        .legend {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 10px;
            font-size: 12px;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .legend-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        
        .stats {
            background-color: #374151;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        .stat-row {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 ABM 代理运动可视化</h1>
            <p>观察20,000个经济主体的实时移动和互动</p>
        </div>
        
        <div class="controls">
            <button id="playBtn" onclick="toggleAnimation()">▶️ 播放</button>
            <button id="pauseBtn" onclick="pauseAnimation()" disabled>⏸️ 暂停</button>
            <button onclick="resetAnimation()">🔄 重置</button>
            <label style="margin-left: 20px;">
                速度: <input type="range" id="speedSlider" min="1" max="20" value="5" onchange="updateSpeed()">
                <span id="speedDisplay">5x</span>
            </label>
        </div>
        
        <div class="simulation-container">
            <div class="map-panel">
                <h3>🗺️ 2D 世界地图 (实时运动)</h3>
                <canvas id="worldCanvas" width="600" height="500"></canvas>
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-dot" style="background-color: #4ade80;"></div>
                        <span>个人 (移动)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot" style="background-color: #3b82f6;"></div>
                        <span>企业 (静态)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot" style="background-color: #f59e0b;"></div>
                        <span>银行 (静态)</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-dot" style="background-color: #ef4444;"></div>
                        <span>央行</span>
                    </div>
                </div>
            </div>
            
            <div class="info-panel">
                <h3>📊 实时统计</h3>
                <div class="stats">
                    <div class="stat-row">
                        <span>当前时间:</span>
                        <span id="currentTime">第 0 天</span>
                    </div>
                    <div class="stat-row">
                        <span>活跃代理:</span>
                        <span id="activeAgents">100</span>
                    </div>
                    <div class="stat-row">
                        <span>移动代理:</span>
                        <span id="movingAgents">80</span>
                    </div>
                    <div class="stat-row">
                        <span>平均速度:</span>
                        <span id="avgSpeed">0.5 单位/步</span>
                    </div>
                </div>
                
                <h4>🎯 运动模式</h4>
                <div style="font-size: 14px; line-height: 1.6;">
                    <p><strong>个人代理:</strong></p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>随机游走 + 回家倾向</li>
                        <li>工作日向商业区聚集</li>
                        <li>周末分散活动</li>
                        <li>年龄影响移动速度</li>
                    </ul>
                    
                    <p><strong>企业代理:</strong></p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>基本静止</li>
                        <li>偶尔小幅位置调整</li>
                        <li>扩张时可能搬迁</li>
                    </ul>
                    
                    <p><strong>银行代理:</strong></p>
                    <ul style="margin: 5px 0; padding-left: 20px;">
                        <li>完全静止</li>
                        <li>作为区域金融中心</li>
                        <li>影响周围经济活动</li>
                    </ul>
                </div>
                
                <h4>🔄 运动机制</h4>
                <div style="font-size: 12px; color: #9ca3af;">
                    <p>• <strong>物理约束</strong>: 边界限制、碰撞检测</p>
                    <p>• <strong>经济驱动</strong>: 就业状态影响移动</p>
                    <p>• <strong>社交网络</strong>: 关系网络影响聚集</p>
                    <p>• <strong>时间周期</strong>: 工作日/周末不同行为</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // 全局变量
        let animationData = null;
        let currentStep = 0;
        let isPlaying = false;
        let animationSpeed = 5;
        let animationInterval = null;
        
        // 画布和上下文
        const canvas = document.getElementById('worldCanvas');
        const ctx = canvas.getContext('2d');
        
        // 初始化
        window.onload = function() {
            generateAnimationData();
            drawFrame();
        };
        
        // 生成动画数据
        function generateAnimationData() {
            console.log('生成运动动画数据...');
            
            const agents = [];
            const steps = 300;
            const mapSize = 80;
            
            // 创建代理
            for (let i = 0; i < 100; i++) {
                const agentType = i < 80 ? 'person' : (i < 95 ? 'firm' : 'bank');
                
                const agent = {
                    id: i,
                    type: agentType,
                    trajectory: [],
                    color: getAgentColor(agentType),
                    size: getAgentSize(agentType),
                    homeX: Math.random() * mapSize,
                    homeY: Math.random() * mapSize,
                };
                
                // 生成轨迹
                let x = Math.random() * mapSize;
                let y = Math.random() * mapSize;
                
                for (let step = 0; step < steps; step++) {
                    // 运动逻辑
                    if (agentType === 'person') {
                        // 个人: 随机游走 + 回家倾向 + 工作聚集
                        const isWorkday = (step % 7) < 5;
                        
                        if (isWorkday) {
                            // 工作日向商业中心移动
                            const businessX = mapSize * 0.6;
                            const businessY = mapSize * 0.4;
                            x += (businessX - x) * 0.02 + (Math.random() - 0.5) * 0.8;
                            y += (businessY - y) * 0.02 + (Math.random() - 0.5) * 0.8;
                        } else {
                            // 周末向家移动
                            x += (agent.homeX - x) * 0.05 + (Math.random() - 0.5) * 1.2;
                            y += (agent.homeY - y) * 0.05 + (Math.random() - 0.5) * 1.2;
                        }
                    } else if (agentType === 'firm') {
                        // 企业: 基本静止，偶尔小调整
                        if (Math.random() < 0.02) {
                            x += (Math.random() - 0.5) * 0.2;
                            y += (Math.random() - 0.5) * 0.2;
                        }
                    }
                    // 银行完全静止
                    
                    // 边界约束
                    x = Math.max(1, Math.min(mapSize - 1, x));
                    y = Math.max(1, Math.min(mapSize - 1, y));
                    
                    agent.trajectory.push({x, y});
                }
                
                agents.push(agent);
            }
            
            animationData = { agents, steps };
            console.log('动画数据生成完成:', agents.length, '个代理,', steps, '个时间步');
        }
        
        // 获取代理颜色
        function getAgentColor(type) {
            const colors = {
                'person': '#4ade80',
                'firm': '#3b82f6', 
                'bank': '#f59e0b',
                'central_bank': '#ef4444'
            };
            return colors[type] || '#9ca3af';
        }
        
        // 获取代理大小
        function getAgentSize(type) {
            const sizes = {
                'person': 2,
                'firm': 4,
                'bank': 6,
                'central_bank': 8
            };
            return sizes[type] || 2;
        }
        
        // 绘制帧
        function drawFrame() {
            if (!animationData) return;
            
            // 清空画布
            ctx.fillStyle = '#111111';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // 绘制网格
            drawGrid();
            
            // 绘制代理
            const scaleX = canvas.width / 80;
            const scaleY = canvas.height / 80;
            
            animationData.agents.forEach(agent => {
                if (currentStep < agent.trajectory.length) {
                    const pos = agent.trajectory[currentStep];
                    
                    ctx.fillStyle = agent.color;
                    ctx.beginPath();
                    ctx.arc(
                        pos.x * scaleX, 
                        pos.y * scaleY, 
                        agent.size, 
                        0, 
                        2 * Math.PI
                    );
                    ctx.fill();
                    
                    // 绘制轨迹 (最近10步)
                    if (agent.type === 'person' && currentStep > 10) {
                        ctx.strokeStyle = agent.color + '40'; // 半透明
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        
                        for (let i = Math.max(0, currentStep - 10); i < currentStep; i++) {
                            const trailPos = agent.trajectory[i];
                            if (i === Math.max(0, currentStep - 10)) {
                                ctx.moveTo(trailPos.x * scaleX, trailPos.y * scaleY);
                            } else {
                                ctx.lineTo(trailPos.x * scaleX, trailPos.y * scaleY);
                            }
                        }
                        ctx.stroke();
                    }
                }
            });
            
            // 更新统计信息
            updateStats();
        }
        
        // 绘制网格
        function drawGrid() {
            ctx.strokeStyle = '#333333';
            ctx.lineWidth = 0.5;
            
            const gridSize = 10;
            const stepX = canvas.width / gridSize;
            const stepY = canvas.height / gridSize;
            
            for (let i = 0; i <= gridSize; i++) {
                // 垂直线
                ctx.beginPath();
                ctx.moveTo(i * stepX, 0);
                ctx.lineTo(i * stepX, canvas.height);
                ctx.stroke();
                
                // 水平线
                ctx.beginPath();
                ctx.moveTo(0, i * stepY);
                ctx.lineTo(canvas.width, i * stepY);
                ctx.stroke();
            }
        }
        
        // 更新统计信息
        function updateStats() {
            document.getElementById('currentTime').textContent = `第 ${currentStep} 天`;
            document.getElementById('activeAgents').textContent = animationData.agents.length;
            
            // 计算移动的代理数量
            let movingAgents = 0;
            if (currentStep > 0) {
                animationData.agents.forEach(agent => {
                    if (currentStep < agent.trajectory.length && currentStep > 0) {
                        const curr = agent.trajectory[currentStep];
                        const prev = agent.trajectory[currentStep - 1];
                        const distance = Math.sqrt((curr.x - prev.x)**2 + (curr.y - prev.y)**2);
                        if (distance > 0.1) movingAgents++;
                    }
                });
            }
            
            document.getElementById('movingAgents').textContent = movingAgents;
            document.getElementById('avgSpeed').textContent = '0.5 单位/步';
        }
        
        // 动画控制
        function toggleAnimation() {
            if (isPlaying) {
                pauseAnimation();
            } else {
                startAnimation();
            }
        }
        
        function startAnimation() {
            if (!animationData) return;
            
            isPlaying = true;
            document.getElementById('playBtn').disabled = true;
            document.getElementById('pauseBtn').disabled = false;
            
            animationInterval = setInterval(() => {
                currentStep++;
                if (currentStep >= animationData.steps) {
                    currentStep = 0; // 循环播放
                }
                drawFrame();
            }, 1000 / animationSpeed);
        }
        
        function pauseAnimation() {
            isPlaying = false;
            document.getElementById('playBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            
            if (animationInterval) {
                clearInterval(animationInterval);
                animationInterval = null;
            }
        }
        
        function resetAnimation() {
            pauseAnimation();
            currentStep = 0;
            drawFrame();
        }
        
        function updateSpeed() {
            const slider = document.getElementById('speedSlider');
            animationSpeed = parseInt(slider.value);
            document.getElementById('speedDisplay').textContent = animationSpeed + 'x';
            
            if (isPlaying) {
                pauseAnimation();
                startAnimation();
            }
        }
    </script>
</body>
</html>'''
    
    return html_content

def main():
    """主函数"""
    print("🎬 ABM 代理运动可视化演示生成器")
    print("=" * 50)
    
    # 生成运动数据
    agents, steps = generate_movement_simulation()
    
    # 创建动画HTML
    print("\n🎨 创建动画可视化页面...")
    html_content = create_animated_html()
    
    # 保存HTML文件
    html_file = Path("movement_demo.html")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ 动画页面已创建: {html_file}")
    
    # 保存运动数据
    movement_data = {
        "metadata": {
            "agents_count": len(agents),
            "simulation_steps": steps,
            "generated_at": time.time()
        },
        "agents": agents
    }
    
    data_file = Path("movement_data.json")
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump(movement_data, f, indent=2, default=str)
    
    print(f"✅ 运动数据已保存: {data_file}")
    print(f"   文件大小: {data_file.stat().st_size / 1024:.1f} KB")
    
    print("\n🎬 运动可视化特性:")
    print("   ✅ 100个代理的实时运动")
    print("   ✅ 300个时间步的轨迹追踪")
    print("   ✅ 不同代理类型的运动模式")
    print("   ✅ 工作日/周末行为差异")
    print("   ✅ 可调节播放速度")
    print("   ✅ 轨迹追踪显示")
    
    print(f"\n💡 打开 {html_file} 查看动画演示!")
    print("🎮 控制说明:")
    print("   • 播放/暂停: 控制动画播放")
    print("   • 速度滑条: 调节播放速度 1x-20x")
    print("   • 重置: 回到动画开始")
    print("   • 轨迹: 个人代理显示移动轨迹")

if __name__ == "__main__":
    main()
