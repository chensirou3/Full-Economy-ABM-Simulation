# ABM 可视化系统指南

## 🎨 可视化内容来源

ABM 经济体模拟系统的可视化内容来自以下几个层面：

### 1. 📊 实时数据源

#### 后端数据生成
```
经济模拟 (EconomicSimulation)
    ↓
代理行为 (Person, Firm, Bank, CentralBank)
    ↓  
指标计算 (get_economic_metrics)
    ↓
遥测系统 (TelemetrySystem)
    ↓
WebSocket 推送 (topics: metrics.update, world.delta, events.stream)
    ↓
前端状态管理 (Zustand Store)
    ↓
可视化组件 (React + PixiJS + Plotly)
```

#### 数据流转过程
1. **代理执行**: 每个 tick，所有代理执行 `step()` 方法
2. **状态收集**: 模拟器收集代理状态变化
3. **指标计算**: 聚合计算 GDP、失业率、通胀率等
4. **事件发射**: 重要事件通过事件总线发射
5. **实时推送**: WebSocket 将数据推送到前端
6. **可视化渲染**: 前端组件实时更新显示

### 2. 🗺️ 2D 世界地图可视化

#### 数据来源
```python
# 代理位置数据
for agent in simulation.schedule.agents:
    agent_data = {
        "agent_id": agent.unique_id,
        "agent_type": agent.agent_type.value,
        "position": {"x": agent.position.x, "y": agent.position.y},
        "status": agent.status.value,
        # ... 其他属性
    }
```

#### 可视化实现 (PixiJS)
```typescript
// WorldViewer.tsx
function createAgentSprite(agent: Agent): Graphics {
    const sprite = new Graphics()
    
    // 根据代理类型设置颜色和形状
    const config = getAgentVisualConfig(agent.agent_type)
    sprite.circle(0, 0, config.radius)
    sprite.fill(config.color)
    
    // 设置位置 (地图坐标 → 屏幕像素)
    sprite.position.set(agent.position.x * 20, agent.position.y * 20)
    
    return sprite
}
```

#### 可视化内容
- **个人代理**: 绿色圆点，显示人口分布和移动
- **企业代理**: 蓝色方块，显示产业布局
- **银行代理**: 黄色菱形，显示金融网络节点
- **央行**: 红色星形，显示政策制定中心

### 3. 📈 经济指标图表

#### 数据来源
```python
# 经济指标计算
def get_economic_metrics(self) -> Dict[str, float]:
    # GDP 计算
    total_output = sum(firm.current_output for firm in self.firms)
    
    # 失业率计算
    working_age = [p for p in self.persons if 18 <= p.age <= 65]
    unemployed = [p for p in working_age if p.employment_status == "unemployed"]
    unemployment_rate = len(unemployed) / len(working_age)
    
    # 通胀率计算
    avg_price = sum(firm.price for firm in self.firms) / len(self.firms)
    inflation = (avg_price - baseline_price) / baseline_price
    
    return {
        "gdp": total_output,
        "unemployment": unemployment_rate, 
        "inflation": inflation,
        "policy_rate": self.central_bank.policy_rate,
    }
```

#### 可视化实现 (Plotly/Recharts)
```typescript
// EconomicCharts.tsx
<LineChart data={chartData}>
    <Line dataKey="gdp" stroke="#10b981" name="GDP" />
    <Line dataKey="unemployment" stroke="#ef4444" name="失业率" />
    <Line dataKey="inflation" stroke="#f59e0b" name="通胀率" />
    <Line dataKey="policy_rate" stroke="#3b82f6" name="政策利率" />
</LineChart>
```

### 4. 📢 事件流可视化

#### 数据来源
```python
# 事件发射示例
self._emit_event(EventType.FIRM_BANKRUPTCY, {
    'net_worth': self.balance_sheet.net_worth,
    'sector': self.sector.value,
    'employees_affected': len(self.employees)
})

self._emit_event(EventType.INTEREST_RATE_CHANGE, {
    'old_rate': old_rate,
    'new_rate': new_rate,
    'committee_vote': voting_results
})
```

#### 可视化实现
```typescript
// EventStream.tsx
{events.map(event => (
    <div className="event-item">
        <div className="event-type">{getEventTypeLabel(event.event_type)}</div>
        <div className="event-time">{formatEventTime(event.timestamp)}</div>
        <div className="event-details">{formatEventPayload(event.payload)}</div>
    </div>
))}
```

### 5. 🏦 代理详情可视化

#### 数据来源
```python
# 代理状态序列化
def serialize_state(self) -> Dict[str, Any]:
    return {
        "agent_id": self.unique_id,
        "agent_type": self.agent_type.value,
        "balance_sheet": self.balance_sheet.to_dict(),
        "position": {"x": self.position.x, "y": self.position.y},
        # 代理特定属性...
    }
```

#### 可视化实现
```typescript
// SidePanel.tsx
const AgentDetails = ({ agent }) => (
    <div>
        <h4>资产负债表</h4>
        <div>总资产: ${agent.balance_sheet.total_assets.toLocaleString()}</div>
        <div>总负债: ${agent.balance_sheet.total_liabilities.toLocaleString()}</div>
        <div>净资产: ${agent.balance_sheet.net_worth.toLocaleString()}</div>
    </div>
)
```

## 🔄 实时数据同步

### WebSocket 主题系统
```python
# 后端推送
await event_bus._broadcast_to_websockets("metrics.update", {
    "timestamp": current_time,
    "kpis": {"gdp": 1000000, "unemployment": 0.05, ...}
})

await event_bus._broadcast_to_websockets("world.delta", {
    "timestamp": current_time,
    "actors_delta": [updated_agents...],
    "tiles_delta": [updated_tiles...]
})
```

### 前端订阅
```typescript
// useWebSocket.ts
ws.onmessage = (event) => {
    const message = JSON.parse(event.data)
    
    switch (message.topic) {
        case 'metrics.update':
            updateMetrics(message.data)
            break
        case 'world.delta':
            updateAgents(message.data.actors_delta)
            break
        case 'events.stream':
            addEvent(message.data)
            break
    }
}
```

## 🎯 可视化数据示例

### 当前生成的可视化数据包含：

1. **20,205 个代理** (20,000人 + 200企业 + 4银行 + 1央行)
   ```json
   {
     "agent_id": 100000,
     "agent_type": "person", 
     "position": {"x": 47.0, "y": 55.9},
     "age": 29,
     "employment_status": "employed",
     "wage": 45706
   }
   ```

2. **360 个时间点的经济指标** (30年月度数据)
   ```json
   {
     "timestamp": 0,
     "kpis": {
       "gdp": 1002510,
       "unemployment": 0.042,
       "inflation": 0.016,
       "policy_rate": 0.025
     }
   }
   ```

3. **49 个重要经济事件**
   ```json
   {
     "timestamp": 81,
     "event_type": "policy.interest_rate_change",
     "payload": {
       "old_rate": 0.041,
       "new_rate": 0.039,
       "reason": "economic_conditions"
     }
   }
   ```

4. **256 个地块信息** (地理热力图)
   ```json
   {
     "x": 0, "y": 0,
     "type": "city",
     "properties": {
       "population_density": 150.2,
       "unemployment_rate": 0.045,
       "average_income": 52000
     }
   }
   ```

## 🖥️ 查看可视化演示

### 方法1：HTML演示页面
```bash
# 在项目根目录打开
start visualization_demo.html
# 或在浏览器中打开 file:///path/to/visualization_demo.html
```

### 方法2：启动完整前端 (推荐)
```bash
# 安装前端依赖
cd frontend/world-viewer
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
```

### 方法3：Control Tower 仪表板
```bash
cd frontend/control-tower
npm install
npm run dev

# 访问 http://localhost:3001
```

## 🎮 交互式功能

### World Viewer 交互
- **缩放**: 鼠标滚轮放大缩小
- **平移**: 鼠标拖拽移动视角
- **选择**: 点击代理查看详情
- **图层**: 切换不同数据层显示
- **跟随**: 锁定特定代理视角

### Control Tower 功能
- **实时监控**: KPI 卡片实时更新
- **历史图表**: 经济指标时间序列
- **事件流**: 重要事件实时滚动
- **参数控制**: 场景切换和参数调节
- **时间控制**: Play/Pause/Step/Rewind

## 📱 可视化技术栈

### 前端渲染
- **PixiJS**: WebGL 2D 渲染引擎，高性能代理可视化
- **Plotly.js**: 交互式图表库，经济指标可视化
- **React**: 组件化UI框架
- **Canvas**: 热力图和自定义可视化

### 数据传输
- **WebSocket**: 实时数据流
- **JSON**: 结构化数据格式
- **增量更新**: 只传输变化的数据

### 性能优化
- **视口裁剪**: 只渲染可见区域
- **LOD**: 距离相关细节层次
- **批量更新**: 合并多个更新请求
- **缓存策略**: 智能数据缓存

---

**🎨 可视化内容完全来自于经济模拟的真实数据，通过多层次的数据处理和渲染管道，为用户提供直观、实时、交互式的经济系统观察体验！**
