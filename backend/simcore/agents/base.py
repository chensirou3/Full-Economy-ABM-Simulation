"""
代理基类
定义所有经济主体的通用接口和行为
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import numpy as np
from mesa import Agent

from ..telemetry import Event, EventType
from ..rng import get_agent_stream


class AgentType(Enum):
    """代理类型枚举"""
    PERSON = "person"
    HOUSEHOLD = "household"
    FIRM = "firm"
    BANK = "bank"
    CENTRAL_BANK = "central_bank"
    GOVERNMENT = "government"


class AgentStatus(Enum):
    """代理状态枚举"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANKRUPT = "bankrupt"
    DECEASED = "deceased"


@dataclass
class Position:
    """位置信息"""
    x: float
    y: float
    
    def distance_to(self, other: "Position") -> float:
        """计算到另一个位置的距离"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)


@dataclass
class BalanceSheet:
    """资产负债表"""
    assets: Dict[str, float]
    liabilities: Dict[str, float]
    
    def __post_init__(self):
        if not self.assets:
            self.assets = {}
        if not self.liabilities:
            self.liabilities = {}
    
    @property
    def total_assets(self) -> float:
        """总资产"""
        return sum(self.assets.values())
    
    @property
    def total_liabilities(self) -> float:
        """总负债"""
        return sum(self.liabilities.values())
    
    @property
    def net_worth(self) -> float:
        """净资产"""
        return self.total_assets - self.total_liabilities
    
    def add_asset(self, asset_type: str, amount: float) -> None:
        """增加资产"""
        self.assets[asset_type] = self.assets.get(asset_type, 0) + amount
    
    def add_liability(self, liability_type: str, amount: float) -> None:
        """增加负债"""
        self.liabilities[liability_type] = self.liabilities.get(liability_type, 0) + amount
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "assets": self.assets,
            "liabilities": self.liabilities,
            "total_assets": self.total_assets,
            "total_liabilities": self.total_liabilities,
            "net_worth": self.net_worth,
        }


class BaseAgent(Agent, ABC):
    """
    经济主体基类
    继承自 Mesa 的 Agent 类，添加经济模拟特有功能
    """
    
    def __init__(self, unique_id: int, model, agent_type: AgentType):
        super().__init__(model)
        self.unique_id = unique_id
        self.agent_type = agent_type
        self.status = AgentStatus.ACTIVE
        self.position = Position(0.0, 0.0)
        self.balance_sheet = BalanceSheet({}, {})
        
        # 随机数生成器
        self._agent_rng = get_agent_stream(unique_id, agent_type.value)
        
        # 历史记录
        self.history: List[Dict[str, Any]] = []
        self.max_history_length = 100
        
        # 关系网络
        self.connections: Dict[str, List[int]] = {}  # 连接类型 -> 代理ID列表
        
        # 事件队列
        self.pending_events: List[Event] = []
    
    @abstractmethod
    def tick(self) -> None:
        """
        每个时间步的主要逻辑
        子类必须实现此方法
        """
        pass
    
    def step(self) -> None:
        """
        Mesa 框架调用的步骤方法
        处理事件队列，然后调用 tick()
        """
        # 处理待处理的事件
        self._process_pending_events()
        
        # 执行主要逻辑
        self.tick()
        
        # 记录历史状态
        self._record_history()
    
    def _process_pending_events(self) -> None:
        """处理待处理的事件"""
        for event in self.pending_events:
            self.on_event(event)
        self.pending_events.clear()
    
    def on_event(self, event: Event) -> None:
        """
        事件处理器
        子类可以重写此方法来处理特定事件
        """
        pass
    
    def add_event(self, event: Event) -> None:
        """添加事件到队列"""
        self.pending_events.append(event)
    
    def _record_history(self) -> None:
        """记录历史状态"""
        state = self.serialize_state()
        self.history.append(state)
        
        # 限制历史长度
        if len(self.history) > self.max_history_length:
            self.history.pop(0)
    
    def serialize_state(self) -> Dict[str, Any]:
        """
        序列化当前状态
        用于历史记录和快照
        """
        return {
            "timestamp": self.model.current_time if hasattr(self.model, 'current_time') else 0,
            "agent_id": self.unique_id,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
            "position": {"x": self.position.x, "y": self.position.y},
            "balance_sheet": self.balance_sheet.to_dict(),
            "connections": self.connections,
        }
    
    def serialize_delta(self, previous_state: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        序列化状态变化（增量更新）
        用于高效的前端更新
        """
        current_state = self.serialize_state()
        
        if previous_state is None:
            return current_state
        
        # 计算变化的字段
        delta = {}
        for key, value in current_state.items():
            if key not in previous_state or previous_state[key] != value:
                delta[key] = value
        
        return delta if delta else None
    
    def move_to(self, x: float, y: float) -> None:
        """移动到指定位置"""
        old_pos = self.position
        self.position = Position(x, y)
        
        # 如果位置发生变化，触发移动事件
        if old_pos.x != x or old_pos.y != y:
            self._emit_event(EventType.AGENT_MIGRATION, {
                "old_position": {"x": old_pos.x, "y": old_pos.y},
                "new_position": {"x": x, "y": y},
            })
    
    def add_connection(self, connection_type: str, other_agent_id: int) -> None:
        """添加与其他代理的连接"""
        if connection_type not in self.connections:
            self.connections[connection_type] = []
        
        if other_agent_id not in self.connections[connection_type]:
            self.connections[connection_type].append(other_agent_id)
    
    def remove_connection(self, connection_type: str, other_agent_id: int) -> None:
        """移除与其他代理的连接"""
        if connection_type in self.connections:
            if other_agent_id in self.connections[connection_type]:
                self.connections[connection_type].remove(other_agent_id)
    
    def get_connections(self, connection_type: str) -> List[int]:
        """获取指定类型的连接"""
        return self.connections.get(connection_type, [])
    
    def _emit_event(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """发射事件（同步）"""
        if hasattr(self.model, 'telemetry'):
            self.model.telemetry.emit_event_sync(
                event_type=event_type,
                actor_id=self.unique_id,
                payload=payload,
            )
    
    def is_bankrupt(self) -> bool:
        """检查是否破产"""
        return self.balance_sheet.net_worth < 0
    
    def declare_bankruptcy(self) -> None:
        """宣布破产"""
        if self.status != AgentStatus.BANKRUPT:
            self.status = AgentStatus.BANKRUPT
            self._emit_event(EventType.FIRM_BANKRUPTCY, {
                "net_worth": self.balance_sheet.net_worth,
                "total_assets": self.balance_sheet.total_assets,
                "total_liabilities": self.balance_sheet.total_liabilities,
            })
    
    def get_neighbors(self, radius: float) -> List["BaseAgent"]:
        """获取指定半径内的邻居代理"""
        neighbors = []
        for agent in self.model.schedule.agents:
            if agent != self and hasattr(agent, 'position'):
                distance = self.position.distance_to(agent.position)
                if distance <= radius:
                    neighbors.append(agent)
        return neighbors
    
    def random_choice(self, choices: List[Any], probabilities: Optional[List[float]] = None) -> Any:
        """使用代理专用随机数生成器进行选择"""
        if probabilities is None:
            return self._agent_rng.choice(choices)
        else:
            return self._agent_rng.choice(choices, p=probabilities)
    
    def random_normal(self, mean: float = 0.0, std: float = 1.0, size: Optional[int] = None) -> Union[float, np.ndarray]:
        """生成正态分布随机数"""
        if size is None:
            return self._agent_rng.normal(mean, std)
        else:
            return self._agent_rng.normal(mean, std, size)
    
    def random_uniform(self, low: float = 0.0, high: float = 1.0, size: Optional[int] = None) -> Union[float, np.ndarray]:
        """生成均匀分布随机数"""
        if size is None:
            return self._agent_rng.uniform(low, high)
        else:
            return self._agent_rng.uniform(low, high, size)


# 代理工厂函数
def create_agent(agent_type: AgentType, unique_id: int, model, **kwargs) -> BaseAgent:
    """
    代理工厂函数
    根据类型创建相应的代理实例
    """
    from .person import Person
    from .household import Household
    from .firm import Firm
    from .bank import Bank
    from .central_bank import CentralBank
    
    agent_classes = {
        AgentType.PERSON: Person,
        AgentType.HOUSEHOLD: Household,
        AgentType.FIRM: Firm,
        AgentType.BANK: Bank,
        AgentType.CENTRAL_BANK: CentralBank,
    }
    
    agent_class = agent_classes.get(agent_type)
    if agent_class is None:
        raise ValueError(f"未知的代理类型: {agent_type}")
    
    return agent_class(unique_id, model, **kwargs)


# W3-W4 扩展点预留：
# - 代理生命周期管理（生老病死）
# - 复杂社交网络建模
# - 学习和适应机制
# - 多层次决策模型（认知偏差）
# - 空间移动和迁移模型
