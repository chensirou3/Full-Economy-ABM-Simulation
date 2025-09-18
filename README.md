# ABM 经济体模拟系统

一个基于多主体建模（Agent-Based Model）的经济体模拟系统，提供实时可视化、时间控制和回放功能。

## 架构概览

- **后端**: Python + Mesa + FastAPI (REST + WebSocket)
- **前端**: React + PixiJS (World Viewer) + Plotly (Control Tower)
- **特性**: 实时可视化、时间控制、事件回放、模块化架构

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- Make 或 Just

### 运行方式

```bash
# 开发环境启动（同时启动后端和前端）
make dev

# 或分别启动
make backend-dev    # 启动后端 API 服务器
make frontend-dev   # 启动前端开发服务器
```

### 访问地址

- World Viewer: http://localhost:3000
- Control Tower: http://localhost:3001
- API 文档: http://localhost:8000/docs

## 主要功能

### 🌍 World Viewer
- 2D 瓦片地图可视化
- 代理移动和状态展示
- 多图层热力图（人口、失业率、房价等）
- 交互式侧边栏信息

### 🎛️ Control Tower
- 实时 KPI 指标监控
- 参数调节面板
- 事件流监控
- 自定义图表

### ⏰ 时间控制
- Play/Pause/Step/Speed 控制
- 时间跳转功能
- **倒带回放**（基于事件溯源）
- 快照与检查点

### 📊 经济指标
- GDP（产出法/收入法）
- 通胀指标（CPI/PCE）
- 失业率和劳动参与率
- 金融稳定指标
- 收入不平等指标

## 项目结构

```
abm-sim/
├── backend/           # Python 后端
│   ├── api/          # FastAPI 应用
│   ├── simcore/      # Mesa 模拟核心
│   └── metrics/      # 经济指标计算
├── frontend/         # 前端应用
│   ├── world-viewer/ # React + PixiJS
│   └── control-tower/ # React + Plotly
├── tools/            # 工具脚本
├── scenarios/        # 场景配置
└── schemas/          # JSON Schema 定义
```

## 场景配置

系统支持多种预设场景：

- `baseline.yml` - 基准经济场景
- `credit_boom.yml` - 信贷繁荣场景
- `supply_shock.yml` - 供给冲击场景

## 开发指南

详细的架构设计和扩展指南请参考：
- [ARCHITECTURE.md](./ARCHITECTURE.md) - 系统架构与扩展点
- [SCENARIOS.md](./SCENARIOS.md) - 场景配置指南

## 许可证

MIT License
