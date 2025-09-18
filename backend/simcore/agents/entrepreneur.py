"""
创业者和机构创建机制
个人代理可以决定创建企业或银行
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .base import BaseAgent, AgentType
from .person import Person
from .firm import Firm
from .bank import Bank
from ..telemetry import EventType


class BusinessType(Enum):
    """企业类型"""
    SOLE_PROPRIETORSHIP = "sole_proprietorship"  # 个体工商户
    PARTNERSHIP = "partnership"                  # 合伙企业
    CORPORATION = "corporation"                  # 公司
    COOPERATIVE = "cooperative"                  # 合作社


class EntrepreneurialDecision:
    """创业决策模型"""
    
    def __init__(self, person: Person, world_map):
        self.person = person
        self.world_map = world_map
        
    def should_start_business(self) -> bool:
        """是否应该创业"""
        # 创业意愿因素
        factors = {
            'age': self._age_factor(),
            'wealth': self._wealth_factor(),
            'skills': self._skills_factor(),
            'market_opportunity': self._market_opportunity_factor(),
            'location': self._location_factor(),
            'risk_tolerance': self._risk_tolerance_factor(),
        }
        
        # 综合评分
        total_score = sum(factors.values()) / len(factors)
        
        # 基础创业概率 (每年约1%的人考虑创业)
        base_probability = 0.01 / 365  # 日概率
        
        # 调整概率
        adjusted_probability = base_probability * (1 + total_score)
        
        return self.person.random_uniform() < adjusted_probability
    
    def _age_factor(self) -> float:
        """年龄因素"""
        # 25-45岁创业意愿最强
        if 25 <= self.person.age <= 45:
            return 1.0
        elif 18 <= self.person.age < 25:
            return 0.5  # 年轻但经验不足
        elif 45 < self.person.age <= 60:
            return 0.3  # 年长但风险厌恶
        else:
            return 0.1  # 其他年龄段
    
    def _wealth_factor(self) -> float:
        """财富因素"""
        cash = self.person.balance_sheet.assets.get('cash', 0)
        
        # 需要一定启动资金，但过富有的人创业意愿反而低
        if cash < 10000:
            return 0.1  # 资金不足
        elif 10000 <= cash <= 100000:
            return (cash - 10000) / 90000  # 线性增长
        else:
            return 0.8  # 富有但创业意愿稍降
    
    def _skills_factor(self) -> float:
        """技能因素"""
        if hasattr(self.person, 'skills'):
            # 高技能更容易创业成功
            return self.person.skills.total_skill_level()
        return 0.5
    
    def _market_opportunity_factor(self) -> float:
        """市场机会因素"""
        # 分析当地市场饱和度
        nearby_firms = self._count_nearby_firms(radius=10)
        local_population = self._count_nearby_population(radius=10)
        
        if local_population == 0:
            return 0.1
        
        # 企业密度过高则机会较少
        firm_density = nearby_firms / local_population
        
        if firm_density < 0.01:  # 企业密度低，机会多
            return 1.0
        elif firm_density < 0.05:
            return 0.7
        else:
            return 0.3  # 市场饱和
    
    def _location_factor(self) -> float:
        """位置因素"""
        tile = self.world_map.get_tile(int(self.person.position.x), int(self.person.position.y))
        
        if tile is None:
            return 0.5
        
        # 商业吸引力
        return tile.get_commercial_attractiveness()
    
    def _risk_tolerance_factor(self) -> float:
        """风险承受能力"""
        # 基于个人风险厌恶系数
        risk_aversion = getattr(self.person, 'risk_aversion', 0.7)
        return max(0, 1 - risk_aversion)
    
    def _count_nearby_firms(self, radius: float) -> int:
        """统计附近企业数量"""
        count = 0
        for agent in self.person.model.schedule.agents:
            if isinstance(agent, Firm):
                distance = self.person.position.distance_to(agent.position)
                if distance <= radius:
                    count += 1
        return count
    
    def _count_nearby_population(self, radius: float) -> int:
        """统计附近人口"""
        count = 0
        for agent in self.person.model.schedule.agents:
            if isinstance(agent, Person):
                distance = self.person.position.distance_to(agent.position)
                if distance <= radius:
                    count += 1
        return count
    
    def determine_business_type(self) -> str:
        """确定企业类型"""
        # 基于当地资源和人口特征
        tile = self.world_map.get_tile(int(self.person.position.x), int(self.person.position.y))
        
        if tile is None:
            return "services"
        
        # 农业区
        if tile.get_agricultural_potential() > 0.6:
            return "agriculture"
        
        # 矿业区
        if tile.mineral_wealth > 0.5:
            return "mining"
        
        # 城市区域
        if tile.population_density > 50:
            return self.person.random_choice(["services", "retail", "technology"], 
                                           p=[0.5, 0.3, 0.2])
        
        # 工业区
        if tile.land_use.value == "industrial":
            return "manufacturing"
        
        # 默认服务业
        return "services"
    
    def find_optimal_location(self, business_type: str) -> Optional[Tuple[int, int]]:
        """寻找最优企业位置"""
        purpose_map = {
            "agriculture": "agricultural",
            "mining": "industrial", 
            "manufacturing": "industrial",
            "services": "commercial",
            "retail": "commercial",
            "technology": "commercial"
        }
        
        purpose = purpose_map.get(business_type, "commercial")
        return self.world_map.find_suitable_location(purpose)


class BankingDecision:
    """银行创建决策"""
    
    def __init__(self, person: Person, world_map):
        self.person = person
        self.world_map = world_map
    
    def should_start_bank(self) -> bool:
        """是否应该创建银行"""
        # 银行创建门槛更高
        if not self._meets_capital_requirements():
            return False
        
        if not self._has_banking_skills():
            return False
        
        if not self._market_needs_bank():
            return False
        
        # 基础概率很低 (银行是特殊机构)
        base_probability = 0.001 / 365  # 年概率0.1%
        
        # 调整因素
        wealth_bonus = min(2.0, self.person.balance_sheet.net_worth / 1000000)  # 百万资产加成
        location_bonus = self._location_banking_potential()
        
        adjusted_probability = base_probability * wealth_bonus * location_bonus
        
        return self.person.random_uniform() < adjusted_probability
    
    def _meets_capital_requirements(self) -> bool:
        """是否满足资本要求"""
        min_capital = 500000  # 50万最低资本
        return self.person.balance_sheet.net_worth >= min_capital
    
    def _has_banking_skills(self) -> bool:
        """是否具备银行技能"""
        if hasattr(self.person, 'skills'):
            # 需要高认知技能和社交技能
            return (self.person.skills.cognitive > 0.7 and 
                   self.person.skills.social > 0.6)
        return False
    
    def _market_needs_bank(self) -> bool:
        """市场是否需要银行"""
        # 分析服务半径内的银行密度
        service_radius = 20  # 银行服务半径
        
        nearby_banks = 0
        nearby_population = 0
        
        for agent in self.person.model.schedule.agents:
            distance = self.person.position.distance_to(agent.position)
            
            if distance <= service_radius:
                if isinstance(agent, Bank):
                    nearby_banks += 1
                elif isinstance(agent, Person):
                    nearby_population += 1
        
        # 每5000人需要1个银行
        needed_banks = max(1, nearby_population // 5000)
        
        return nearby_banks < needed_banks
    
    def _location_banking_potential(self) -> float:
        """位置银行潜力"""
        tile = self.world_map.get_tile(int(self.person.position.x), int(self.person.position.y))
        
        if tile is None:
            return 0.5
        
        # 银行偏好商业区和交通便利位置
        potential = (tile.get_commercial_attractiveness() * 0.6 + 
                    tile.road_quality * 0.4)
        
        return potential


class InstitutionLifecycle:
    """机构生命周期管理"""
    
    @staticmethod
    def create_firm_from_person(person: Person, world_map, business_type: str) -> Optional[Firm]:
        """个人创建企业"""
        # 寻找位置
        decision_maker = EntrepreneurialDecision(person, world_map)
        location = decision_maker.find_optimal_location(business_type)
        
        if location is None:
            return None
        
        # 计算初始投资
        initial_investment = min(person.balance_sheet.assets.get('cash', 0) * 0.8, 100000)
        
        if initial_investment < 5000:  # 最低投资门槛
            return None
        
        # 创建企业
        firm_id = person.model.next_unique_id()
        firm = Firm(
            unique_id=firm_id,
            model=person.model,
            sector_name=business_type,
            founder_id=person.unique_id,
            initial_capital=initial_investment,
            location=location
        )
        
        # 从个人账户转移资金
        person.balance_sheet.assets['cash'] -= initial_investment
        person.balance_sheet.add_asset('business_equity', initial_investment)
        
        # 建立关系
        person.add_connection('owned_business', firm_id)
        firm.add_connection('owner', person.unique_id)
        
        # 设置位置
        firm.move_to(location[0], location[1])
        
        # 发射创业事件
        person._emit_event(EventType.FIRM_CREATION, {
            'firm_id': firm_id,
            'business_type': business_type,
            'initial_investment': initial_investment,
            'location': location,
        })
        
        print(f"🏢 个人{person.unique_id}在({location[0]:.1f},{location[1]:.1f})创建了{business_type}企业")
        
        return firm
    
    @staticmethod
    def create_bank_from_person(person: Person, world_map) -> Optional[Bank]:
        """个人创建银行"""
        decision_maker = BankingDecision(person, world_map)
        
        # 寻找银行位置
        location = world_map.find_suitable_location("commercial")
        if location is None:
            return None
        
        # 银行初始资本
        initial_capital = min(person.balance_sheet.net_worth * 0.9, 2000000)
        
        # 创建银行
        bank_id = person.model.next_unique_id()
        bank = Bank(
            unique_id=bank_id,
            model=person.model,
            founder_id=person.unique_id,
            initial_capital=initial_capital,
            location=location
        )
        
        # 资金转移
        person.balance_sheet.assets['cash'] -= initial_capital
        person.balance_sheet.add_asset('bank_equity', initial_capital)
        
        # 建立关系
        person.add_connection('owned_bank', bank_id)
        bank.add_connection('owner', person.unique_id)
        
        # 设置位置
        bank.move_to(location[0], location[1])
        
        # 发射银行创建事件
        person._emit_event(EventType.BANK_CREATION, {
            'bank_id': bank_id,
            'initial_capital': initial_capital,
            'location': location,
        })
        
        print(f"🏦 个人{person.unique_id}在({location[0]:.1f},{location[1]:.1f})创建了银行")
        
        return bank
    
    @staticmethod
    def should_firm_close(firm: Firm) -> bool:
        """企业是否应该倒闭"""
        # 倒闭条件
        conditions = [
            firm.balance_sheet.net_worth < -firm.balance_sheet.total_assets * 0.5,  # 严重亏损
            firm.balance_sheet.assets.get('cash', 0) < 0,  # 现金流断裂
            len(firm.employees) == 0 and firm.revenue == 0,  # 无员工无收入
        ]
        
        return any(conditions)
    
    @staticmethod
    def close_firm(firm: Firm) -> Dict[str, Any]:
        """关闭企业"""
        closure_data = {
            'firm_id': firm.unique_id,
            'sector': firm.sector.value if hasattr(firm, 'sector') else 'unknown',
            'final_net_worth': firm.balance_sheet.net_worth,
            'employees_affected': len(firm.employees) if hasattr(firm, 'employees') else 0,
            'closure_reason': 'bankruptcy' if firm.balance_sheet.net_worth < 0 else 'voluntary'
        }
        
        # 解雇所有员工
        if hasattr(firm, 'employees'):
            for employee_id in firm.employees:
                employee = firm.model.schedule._agents.get(employee_id)
                if employee and isinstance(employee, Person):
                    employee.employment_status = employee.employment_status.__class__.UNEMPLOYED
                    employee.employer_id = None
        
        # 通知所有者
        if hasattr(firm, 'owner_id'):
            owner = firm.model.schedule._agents.get(firm.owner_id)
            if owner and isinstance(owner, Person):
                # 企业价值归零
                owner.balance_sheet.assets['business_equity'] = 0
        
        # 标记为破产
        firm.declare_bankruptcy()
        
        # 发射倒闭事件
        firm._emit_event(EventType.FIRM_BANKRUPTCY, closure_data)
        
        print(f"💥 企业{firm.unique_id}倒闭: {closure_data['closure_reason']}")
        
        return closure_data


# 在Person类中添加创业行为
def add_entrepreneurial_behavior_to_person():
    """为Person类添加创业行为"""
    
    def entrepreneurial_tick(self):
        """创业相关的tick行为"""
        # 只有成年且有一定财富的人才考虑创业
        if self.age < 25 or self.balance_sheet.net_worth < 10000:
            return
        
        # 如果已经是企业主，则管理企业
        if self.get_connections('owned_business'):
            self._manage_owned_businesses()
            return
        
        # 如果已经是银行家，则管理银行
        if self.get_connections('owned_bank'):
            self._manage_owned_banks()
            return
        
        # 考虑创业
        if hasattr(self.model, 'world_map'):
            decision_maker = EntrepreneurialDecision(self, self.model.world_map)
            
            if decision_maker.should_start_business():
                business_type = decision_maker.determine_business_type()
                new_firm = InstitutionLifecycle.create_firm_from_person(
                    self, self.model.world_map, business_type
                )
                
                if new_firm:
                    # 将新企业添加到模型中
                    self.model.schedule.add(new_firm)
                    if hasattr(self.model, 'firms'):
                        self.model.firms.append(new_firm)
        
        # 考虑创建银行 (概率更低)
        if hasattr(self.model, 'world_map') and not self.get_connections('owned_bank'):
            banking_decision = BankingDecision(self, self.model.world_map)
            
            if banking_decision.should_start_bank():
                new_bank = InstitutionLifecycle.create_bank_from_person(
                    self, self.model.world_map
                )
                
                if new_bank:
                    self.model.schedule.add(new_bank)
                    if hasattr(self.model, 'banks'):
                        self.model.banks.append(new_bank)
    
    def _manage_owned_businesses(self):
        """管理拥有的企业"""
        business_ids = self.get_connections('owned_business')
        
        for business_id in business_ids:
            firm = self.model.schedule._agents.get(business_id)
            if firm and isinstance(firm, Firm):
                # 检查是否需要关闭
                if InstitutionLifecycle.should_firm_close(firm):
                    closure_data = InstitutionLifecycle.close_firm(firm)
                    
                    # 从连接中移除
                    self.remove_connection('owned_business', business_id)
                    
                    # 从模型中移除
                    self.model.schedule.remove(firm)
                    if hasattr(self.model, 'firms') and firm in self.model.firms:
                        self.model.firms.remove(firm)
    
    def _manage_owned_banks(self):
        """管理拥有的银行"""
        bank_ids = self.get_connections('owned_bank')
        
        for bank_id in bank_ids:
            bank = self.model.schedule._agents.get(bank_id)
            if bank and isinstance(bank, Bank):
                # 银行风险管理
                if bank.balance_sheet.net_worth < 0:
                    # 银行倒闭处理
                    self._handle_bank_closure(bank)
    
    def _handle_bank_closure(self, bank: Bank):
        """处理银行倒闭"""
        # 银行倒闭的系统性影响
        bank.declare_bankruptcy()
        
        # 从连接中移除
        self.remove_connection('owned_bank', bank.unique_id)
        
        # 从模型中移除
        self.model.schedule.remove(bank)
        if hasattr(self.model, 'banks') and bank in self.model.banks:
            self.model.banks.remove(bank)
        
        print(f"🏦💥 银行{bank.unique_id}倒闭，造成系统性冲击")
    
    # 将这些方法添加到Person类
    Person.entrepreneurial_tick = entrepreneurial_tick
    Person._manage_owned_businesses = _manage_owned_businesses
    Person._manage_owned_banks = _manage_owned_banks
    Person._handle_bank_closure = _handle_bank_closure


# 修改Person的tick方法以包含创业行为
def enhanced_person_tick(self):
    """增强的个人tick方法"""
    # 原有行为
    self._age_tick()
    
    if self.employment_status.value == "unemployed":
        self._job_search()
    elif self.employment_status.value == "employed":
        self._work()
    
    self._consume()
    self._save_and_invest()
    self._update_health()
    self._social_interaction()
    
    # 新增：创业行为
    self.entrepreneurial_tick()


# 应用增强
add_entrepreneurial_behavior_to_person()


# W3-W4 扩展点预留：
# - 复杂的商业计划和市场分析
# - 风险投资和融资机制
# - 企业并购和重组
# - 创新和技术创业
# - 社会企业和非营利组织
# - 国际投资和跨国企业
