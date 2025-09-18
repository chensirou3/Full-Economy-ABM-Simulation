"""
企业代理
代表经济体中的企业，具有生产、定价、雇佣等经济行为
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .base import BaseAgent, AgentType, AgentStatus
from ..telemetry import EventType


class Sector(Enum):
    """产业部门"""
    AGRICULTURE = "agriculture"
    MINING = "mining"
    MANUFACTURING = "manufacturing"
    SERVICES = "services"
    FINANCE = "finance"
    CONSTRUCTION = "construction"
    TECHNOLOGY = "technology"


class FirmSize(Enum):
    """企业规模"""
    MICRO = "micro"        # < 10 employees
    SMALL = "small"        # 10-49 employees
    MEDIUM = "medium"      # 50-249 employees
    LARGE = "large"        # 250+ employees


@dataclass
class ProductionFunction:
    """生产函数参数"""
    tfp: float = 1.0           # 全要素生产率
    alpha: float = 0.3         # 资本份额
    labor_elasticity: float = 0.7  # 劳动弹性
    capital_depreciation: float = 0.06  # 资本折旧率
    
    def produce(self, labor: float, capital: float) -> float:
        """Cobb-Douglas 生产函数"""
        return self.tfp * (labor ** self.labor_elasticity) * (capital ** self.alpha)


@dataclass
class PricingStrategy:
    """定价策略"""
    markup: float = 0.2        # 加成率
    price_stickiness: float = 0.75  # 价格粘性（Calvo 概率）
    adjustment_speed: float = 0.1   # 价格调整速度


class Firm(BaseAgent):
    """
    企业代理类
    代表经济体中的企业，具有生产、定价、雇佣等行为
    """
    
    def __init__(self, unique_id: int, model, **kwargs):
        super().__init__(unique_id, model, AgentType.FIRM)
        
        # 企业基本属性
        self.sector = kwargs.get('sector', Sector.MANUFACTURING)
        self.firm_size = kwargs.get('firm_size', FirmSize.SMALL)
        self.founding_date = kwargs.get('founding_date', 0)
        
        # 生产相关
        self.production_function = kwargs.get('production_function', ProductionFunction())
        self.current_output = 0.0
        self.target_output = 0.0
        self.capacity_utilization = 0.8
        
        # 定价策略
        self.pricing_strategy = kwargs.get('pricing_strategy', PricingStrategy())
        self.price = kwargs.get('initial_price', 100.0)
        self.marginal_cost = 0.0
        self.last_price_change = 0
        
        # 雇佣和劳动
        self.employees: List[int] = kwargs.get('employees', [])  # 员工ID列表
        self.target_employment = len(self.employees)
        self.wage_rate = kwargs.get('wage_rate', 30000.0)  # 年工资
        self.labor_demand = 0.0
        
        # 资本和投资
        self.capital_stock = kwargs.get('capital_stock', 100000.0)
        self.investment_rate = 0.1
        self.investment_plans = 0.0
        
        # 库存管理
        self.inventory = kwargs.get('inventory', 0.0)
        self.target_inventory_ratio = 0.1  # 相对于预期销售
        
        # 财务状态
        self.revenue = 0.0
        self.costs = 0.0
        self.profit = 0.0
        self.cash_flow = 0.0
        
        # 市场和竞争
        self.market_share = kwargs.get('market_share', 0.01)
        self.competitors: List[int] = []
        self.customers: List[int] = []
        self.suppliers: List[int] = []
        
        # 银行关系
        self.bank_id: Optional[int] = kwargs.get('bank_id')
        self.credit_limit = kwargs.get('credit_limit', 50000.0)
        self.debt_service_ratio = 0.0
        
        # 预期和学习
        self.demand_forecast = 1000.0
        self.price_expectations = {}
        self.learning_rate = 0.1
        
        # 初始化资产负债表
        self._initialize_balance_sheet()
    
    def _initialize_balance_sheet(self) -> None:
        """初始化企业资产负债表"""
        # 资产
        initial_cash = self.capital_stock * 0.1
        self.balance_sheet.assets = {
            'cash': initial_cash,
            'inventory': self.inventory * self.price,
            'capital': self.capital_stock,
            'accounts_receivable': 0.0,
        }
        
        # 负债
        initial_debt = self.capital_stock * 0.3  # 30%负债率
        self.balance_sheet.liabilities = {
            'bank_loans': initial_debt,
            'accounts_payable': 0.0,
            'wages_payable': 0.0,
        }
    
    def tick(self) -> None:
        """企业每个时间步的主要决策"""
        # 1. 更新预期和预测
        self._update_forecasts()
        
        # 2. 生产决策
        self._make_production_decision()
        
        # 3. 定价决策
        self._make_pricing_decision()
        
        # 4. 雇佣决策
        self._make_employment_decision()
        
        # 5. 投资决策
        self._make_investment_decision()
        
        # 6. 库存管理
        self._manage_inventory()
        
        # 7. 财务管理
        self._manage_finances()
        
        # 8. 检查破产风险
        self._check_bankruptcy_risk()
    
    def _update_forecasts(self) -> None:
        """更新需求预测和价格预期"""
        # 简化的适应性预期模型
        if hasattr(self, 'last_sales'):
            forecast_error = self.last_sales - self.demand_forecast
            self.demand_forecast += self.learning_rate * forecast_error
        
        # 更新价格预期（基于市场观察）
        self._update_price_expectations()
    
    def _update_price_expectations(self) -> None:
        """更新价格预期"""
        # W2: 从市场获取价格信息
        # 简化实现：基于历史价格趋势
        if hasattr(self.model, 'markets'):
            # 获取市场价格信息
            pass
    
    def _make_production_decision(self) -> None:
        """生产决策"""
        # 基于预期需求和当前库存确定目标产出
        expected_sales = self.demand_forecast
        current_inventory = self.inventory
        target_inventory = expected_sales * self.target_inventory_ratio
        
        self.target_output = max(0, expected_sales + target_inventory - current_inventory)
        
        # 考虑产能约束
        max_output = self._calculate_max_output()
        self.target_output = min(self.target_output, max_output)
        
        # 执行生产
        self._produce()
    
    def _calculate_max_output(self) -> float:
        """计算最大产出（产能约束）"""
        available_labor = len(self.employees)
        available_capital = self.capital_stock * self.capacity_utilization
        
        return self.production_function.produce(available_labor, available_capital)
    
    def _produce(self) -> None:
        """执行生产"""
        # 计算实际投入
        labor_input = len(self.employees)
        capital_input = self.capital_stock * self.capacity_utilization
        
        # 生产产出
        self.current_output = self.production_function.produce(labor_input, capital_input)
        
        # 更新库存
        self.inventory += self.current_output
        
        # 计算生产成本
        self._calculate_production_costs(labor_input, capital_input)
        
        # 资本折旧
        depreciation = self.capital_stock * self.production_function.capital_depreciation / 365
        self.capital_stock -= depreciation
        self.balance_sheet.assets['capital'] = self.capital_stock
    
    def _calculate_production_costs(self, labor_input: float, capital_input: float) -> None:
        """计算生产成本"""
        # 劳动成本
        daily_wage_cost = (self.wage_rate / 365) * len(self.employees)
        
        # 资本成本（折旧 + 利息）
        daily_capital_cost = (self.capital_stock * 0.05 / 365)  # 假设5%的资本成本
        
        # 其他可变成本
        variable_cost = self.current_output * 10  # 简化：每单位产出10的可变成本
        
        total_cost = daily_wage_cost + daily_capital_cost + variable_cost
        self.costs = total_cost
        
        # 计算边际成本
        if self.current_output > 0:
            self.marginal_cost = total_cost / self.current_output
        
        # 更新现金流
        self.balance_sheet.assets['cash'] -= total_cost
    
    def _make_pricing_decision(self) -> None:
        """定价决策"""
        # Calvo 价格粘性模型
        if self.rng.random() < (1 - self.pricing_strategy.price_stickiness):
            # 有机会调整价格
            optimal_price = self._calculate_optimal_price()
            
            # 渐进调整
            price_gap = optimal_price - self.price
            self.price += self.pricing_strategy.adjustment_speed * price_gap
            
            self.last_price_change = self.model.schedule.steps if hasattr(self.model, 'schedule') else 0
    
    def _calculate_optimal_price(self) -> float:
        """计算最优价格"""
        # 基于边际成本的加成定价
        if self.marginal_cost > 0:
            markup_price = self.marginal_cost * (1 + self.pricing_strategy.markup)
        else:
            markup_price = self.price  # 保持当前价格
        
        # 考虑竞争对手价格（简化）
        # W2: 实现更复杂的竞争定价模型
        
        return markup_price
    
    def _make_employment_decision(self) -> None:
        """雇佣决策"""
        # 基于产出目标计算劳动需求
        if self.target_output > 0:
            # 根据生产函数计算所需劳动
            required_labor = self._calculate_labor_demand()
            self.target_employment = max(1, int(required_labor))
        else:
            self.target_employment = max(1, len(self.employees) // 2)  # 保持最低雇佣
        
        current_employment = len(self.employees)
        
        if self.target_employment > current_employment:
            # 需要招聘
            self._hire_workers(self.target_employment - current_employment)
        elif self.target_employment < current_employment:
            # 需要裁员
            self._fire_workers(current_employment - self.target_employment)
    
    def _calculate_labor_demand(self) -> float:
        """计算劳动需求"""
        # 基于生产函数反推所需劳动
        if self.capital_stock > 0 and self.target_output > 0:
            # L = (Y / (TFP * K^α))^(1/β)
            capital_term = self.capital_stock ** self.production_function.alpha
            labor_demand = (self.target_output / (self.production_function.tfp * capital_term)) ** (1 / self.production_function.labor_elasticity)
            return max(1, labor_demand)
        return 1
    
    def _hire_workers(self, num_to_hire: int) -> None:
        """招聘工人"""
        # W2: 实现与劳动市场的交互
        # 简化实现：假设能够招聘到所需工人
        for _ in range(num_to_hire):
            # 创建虚拟员工ID（W2中会与实际Person代理匹配）
            new_employee_id = self.rng.integers(100000, 999999)
            self.employees.append(new_employee_id)
        
        self._emit_event(EventType.AGENT_JOB_CHANGE, {
            'action': 'hire',
            'count': num_to_hire,
            'total_employees': len(self.employees),
        })
    
    def _fire_workers(self, num_to_fire: int) -> None:
        """解雇工人"""
        num_to_fire = min(num_to_fire, len(self.employees) - 1)  # 保留至少1个员工
        
        for _ in range(num_to_fire):
            if self.employees:
                fired_employee = self.employees.pop()
                # W2: 通知被解雇的员工
        
        self._emit_event(EventType.UNEMPLOYMENT_SPIKE, {
            'action': 'fire',
            'count': num_to_fire,
            'total_employees': len(self.employees),
        })
    
    def _make_investment_decision(self) -> None:
        """投资决策"""
        # 简化的投资模型：基于预期收益和现金流
        if self.profit > 0 and self.balance_sheet.assets.get('cash', 0) > 10000:
            # 计算投资需求
            capacity_gap = max(0, self.target_output - self._calculate_max_output())
            
            if capacity_gap > 0:
                # 需要扩大产能
                investment_amount = capacity_gap * 1000  # 简化：每单位产能需要1000投资
                available_cash = self.balance_sheet.assets.get('cash', 0)
                
                self.investment_plans = min(investment_amount, available_cash * 0.5)
        
        # 执行投资
        if self.investment_plans > 0:
            self._execute_investment()
    
    def _execute_investment(self) -> None:
        """执行投资"""
        if self.balance_sheet.assets.get('cash', 0) >= self.investment_plans:
            # 扣除现金
            self.balance_sheet.assets['cash'] -= self.investment_plans
            
            # 增加资本存量
            capital_increase = self.investment_plans * 0.8  # 80%转化为资本
            self.capital_stock += capital_increase
            self.balance_sheet.assets['capital'] = self.capital_stock
            
            self.investment_plans = 0
    
    def _manage_inventory(self) -> None:
        """库存管理"""
        # 简化的库存管理：基于预期销售调整库存
        target_inventory = self.demand_forecast * self.target_inventory_ratio
        
        if self.inventory > target_inventory * 1.5:
            # 库存过多，降价促销或减产
            self.pricing_strategy.markup *= 0.95
        elif self.inventory < target_inventory * 0.5:
            # 库存不足，可能涨价或增产
            self.pricing_strategy.markup *= 1.02
    
    def _manage_finances(self) -> None:
        """财务管理"""
        # 计算收入（简化：基于库存销售）
        daily_sales = min(self.inventory, self.demand_forecast / 365)
        self.revenue = daily_sales * self.price
        
        # 更新现金和库存
        self.balance_sheet.assets['cash'] += self.revenue
        self.inventory -= daily_sales
        
        # 计算利润
        self.profit = self.revenue - self.costs
        self.cash_flow = self.profit
        
        # 债务服务
        self._service_debt()
        
        # 记录销售（用于下次预测）
        self.last_sales = daily_sales
    
    def _service_debt(self) -> None:
        """债务服务"""
        outstanding_debt = self.balance_sheet.liabilities.get('bank_loans', 0)
        if outstanding_debt > 0:
            # 简化的债务服务：年利率5%
            daily_interest = outstanding_debt * 0.05 / 365
            
            if self.balance_sheet.assets.get('cash', 0) >= daily_interest:
                self.balance_sheet.assets['cash'] -= daily_interest
                self.costs += daily_interest
                
                # 计算债务服务比率
                annual_debt_service = daily_interest * 365
                self.debt_service_ratio = annual_debt_service / max(1, self.revenue * 365)
    
    def _check_bankruptcy_risk(self) -> None:
        """检查破产风险"""
        # 破产条件：净资产为负或现金流持续为负
        if self.balance_sheet.net_worth < 0:
            self.declare_bankruptcy()
        elif self.balance_sheet.assets.get('cash', 0) < 0:
            # 现金不足，尝试借贷
            if not self._emergency_borrowing():
                self.declare_bankruptcy()
    
    def _emergency_borrowing(self) -> bool:
        """紧急借贷"""
        # 简化实现：如果有信贷额度且债务服务比率合理
        if self.credit_limit > 0 and self.debt_service_ratio < 0.3:
            emergency_loan = min(self.credit_limit, abs(self.balance_sheet.assets.get('cash', 0)) + 5000)
            
            self.balance_sheet.assets['cash'] += emergency_loan
            self.balance_sheet.add_liability('bank_loans', emergency_loan)
            
            return True
        return False
    
    def declare_bankruptcy(self) -> None:
        """宣布破产"""
        if self.status != AgentStatus.BANKRUPT:
            super().declare_bankruptcy()
            
            # 解雇所有员工
            fired_count = len(self.employees)
            self.employees.clear()
            
            if fired_count > 0:
                self._emit_event(EventType.UNEMPLOYMENT_SPIKE, {
                    'reason': 'bankruptcy',
                    'fired_count': fired_count,
                })
    
    def get_firm_size_category(self) -> FirmSize:
        """根据员工数量确定企业规模"""
        num_employees = len(self.employees)
        
        if num_employees < 10:
            return FirmSize.MICRO
        elif num_employees < 50:
            return FirmSize.SMALL
        elif num_employees < 250:
            return FirmSize.MEDIUM
        else:
            return FirmSize.LARGE
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化企业状态"""
        state = super().serialize_state()
        state.update({
            'sector': self.sector.value,
            'firm_size': self.get_firm_size_category().value,
            'num_employees': len(self.employees),
            'current_output': self.current_output,
            'price': self.price,
            'marginal_cost': self.marginal_cost,
            'capacity_utilization': self.capacity_utilization,
            'capital_stock': self.capital_stock,
            'inventory': self.inventory,
            'revenue': self.revenue,
            'costs': self.costs,
            'profit': self.profit,
            'market_share': self.market_share,
            'debt_service_ratio': self.debt_service_ratio,
        })
        return state


# W3-W4 扩展点预留：
# - 复杂的产业链和供应商网络
# - 技术创新和研发投资
# - 国际贸易和出口决策
# - 企业合并和收购
# - 环境影响和可持续发展
# - 数字化转型和平台经济
