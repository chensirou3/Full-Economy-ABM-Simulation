"""
家庭代理
代表经济体中的家庭单位，聚合个人的经济行为
W3-W4 扩展：亲子关系、家庭决策、房产投资等
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from .base import BaseAgent, AgentType, AgentStatus
from .person import Person
from ..telemetry import EventType


class HouseholdType(Enum):
    """家庭类型"""
    SINGLE = "single"           # 单人家庭
    COUPLE = "couple"           # 夫妇
    NUCLEAR = "nuclear"         # 核心家庭（父母+子女）
    EXTENDED = "extended"       # 大家庭


@dataclass
class HouseholdBudget:
    """家庭预算"""
    total_income: float = 0.0
    total_expenses: float = 0.0
    savings: float = 0.0
    debt_service: float = 0.0
    
    # 支出分类
    food_expenses: float = 0.0
    housing_expenses: float = 0.0
    transportation_expenses: float = 0.0
    healthcare_expenses: float = 0.0
    education_expenses: float = 0.0
    other_expenses: float = 0.0


class Household(BaseAgent):
    """
    家庭代理类
    W1-W2: 基础实现，聚合个人行为
    W3-W4: 扩展复杂家庭决策和生命周期
    """
    
    def __init__(self, unique_id: int, model, **kwargs):
        super().__init__(unique_id, model, AgentType.HOUSEHOLD)
        
        # 家庭成员
        self.members: List[int] = kwargs.get('members', [])  # Person ID列表
        self.head_of_household: Optional[int] = kwargs.get('head_of_household')
        self.household_type = kwargs.get('household_type', HouseholdType.SINGLE)
        
        # 家庭经济
        self.budget = HouseholdBudget()
        self.joint_accounts = True  # 是否有共同账户
        
        # 住房
        self.housing_status = kwargs.get('housing_status', 'rent')  # rent/own
        self.housing_value = kwargs.get('housing_value', 0.0)
        self.mortgage_balance = kwargs.get('mortgage_balance', 0.0)
        
        # W3-W4 扩展点预留
        self.children_count = 0
        self.elderly_dependents = 0
        
        # 初始化资产负债表
        self._initialize_balance_sheet()
    
    def _initialize_balance_sheet(self) -> None:
        """初始化家庭资产负债表"""
        # 简化实现：聚合成员的资产负债
        total_cash = 0.0
        total_debt = 0.0
        
        # W2: 实际聚合成员资产
        self.balance_sheet.assets = {
            'cash': total_cash,
            'housing': self.housing_value,
            'investments': 0.0,
        }
        
        self.balance_sheet.liabilities = {
            'mortgage': self.mortgage_balance,
            'consumer_debt': total_debt,
        }
    
    def tick(self) -> None:
        """家庭每个时间步的决策"""
        # 1. 聚合成员收入和支出
        self._aggregate_member_finances()
        
        # 2. 家庭预算决策
        self._make_budget_decisions()
        
        # 3. 住房决策
        self._make_housing_decisions()
        
        # 4. 储蓄和投资决策
        self._make_investment_decisions()
        
        # W3-W4: 生育、教育、照护等决策
    
    def _aggregate_member_finances(self) -> None:
        """聚合成员财务状况"""
        # W2: 实现与Person代理的交互
        # 简化实现
        self.budget.total_income = len(self.members) * 30000 / 365  # 简化日收入
        self.budget.total_expenses = self.budget.total_income * 0.8
        self.budget.savings = self.budget.total_income - self.budget.total_expenses
    
    def _make_budget_decisions(self) -> None:
        """家庭预算决策"""
        # 简化的预算分配
        total_expenses = self.budget.total_expenses
        
        self.budget.food_expenses = total_expenses * 0.25
        self.budget.housing_expenses = total_expenses * 0.35
        self.budget.transportation_expenses = total_expenses * 0.15
        self.budget.other_expenses = total_expenses * 0.25
    
    def _make_housing_decisions(self) -> None:
        """住房决策"""
        # W3-W4: 实现复杂的购房/租房决策
        pass
    
    def _make_investment_decisions(self) -> None:
        """投资决策"""
        # W3-W4: 实现家庭投资组合管理
        pass
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化家庭状态"""
        state = super().serialize_state()
        state.update({
            'members_count': len(self.members),
            'household_type': self.household_type.value,
            'housing_status': self.housing_status,
            'total_income': self.budget.total_income,
            'total_expenses': self.budget.total_expenses,
            'savings': self.budget.savings,
        })
        return state


# W3-W4 扩展点预留：
# - 复杂的家庭生命周期模型
# - 家庭内部资源分配和决策
# - 住房市场参与和房产投资
# - 子女教育投资决策
# - 老年照护和代际转移
