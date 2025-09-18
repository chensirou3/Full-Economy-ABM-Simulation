"""
个人代理
代表经济体中的个体人员，具有年龄、技能、就业状态等属性
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .base import BaseAgent, AgentType, AgentStatus, Position
from ..telemetry import EventType


class EmploymentStatus(Enum):
    """就业状态"""
    EMPLOYED = "employed"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"
    DISABLED = "disabled"


class EducationLevel(Enum):
    """教育水平"""
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"
    POSTGRADUATE = "postgraduate"


@dataclass
class Skills:
    """技能集合"""
    cognitive: float  # 认知技能
    manual: float     # 手工技能
    social: float     # 社交技能
    technical: float  # 技术技能
    
    def __post_init__(self):
        # 确保技能值在 [0, 1] 范围内
        for field in ['cognitive', 'manual', 'social', 'technical']:
            value = getattr(self, field)
            setattr(self, field, max(0.0, min(1.0, value)))
    
    def total_skill_level(self) -> float:
        """总技能水平"""
        return (self.cognitive + self.manual + self.social + self.technical) / 4
    
    def to_dict(self) -> Dict[str, float]:
        """转换为字典"""
        return {
            "cognitive": self.cognitive,
            "manual": self.manual,
            "social": self.social,
            "technical": self.technical,
            "total": self.total_skill_level(),
        }


class Person(BaseAgent):
    """
    个人代理类
    代表经济体中的个体，具有人口统计学特征和经济行为
    """
    
    def __init__(self, unique_id: int, model, **kwargs):
        super().__init__(unique_id, model, AgentType.PERSON)
        
        # 人口统计学特征
        self.age = kwargs.get('age', self._generate_age())
        self.gender = kwargs.get('gender', self._generate_gender())
        self.education = kwargs.get('education', self._generate_education())
        
        # 技能
        self.skills = kwargs.get('skills', self._generate_skills())
        
        # 就业相关
        self.employment_status = kwargs.get('employment_status', EmploymentStatus.UNEMPLOYED)
        self.employer_id: Optional[int] = kwargs.get('employer_id')
        self.wage = kwargs.get('wage', 0.0)
        self.job_search_intensity = 0.5  # 求职强度
        
        # 家庭关系
        self.household_id: Optional[int] = kwargs.get('household_id')
        self.spouse_id: Optional[int] = kwargs.get('spouse_id')
        self.children_ids: List[int] = kwargs.get('children_ids', [])
        self.parent_ids: List[int] = kwargs.get('parent_ids', [])
        
        # 经济行为参数
        self.discount_factor = kwargs.get('discount_factor', 0.96)
        self.risk_aversion = kwargs.get('risk_aversion', 0.7)
        self.consumption_preference = self._generate_consumption_preference()
        
        # 健康状态
        self.health = kwargs.get('health', 1.0)  # [0, 1]
        self.life_expectancy = kwargs.get('life_expectancy', 75.0)
        
        # 位置和移动
        if 'position' in kwargs:
            self.position = kwargs['position']
        else:
            self._initialize_position()
        
        # 初始化资产负债表
        self._initialize_balance_sheet()
    
    def _generate_age(self) -> int:
        """生成年龄"""
        # 简化的年龄分布：偏向年轻人口
        return int(self._agent_rng.beta(2, 5) * 100)
    
    def _generate_gender(self) -> str:
        """生成性别"""
        return self._agent_rng.choice(['male', 'female'])
    
    def _generate_education(self) -> EducationLevel:
        """生成教育水平"""
        # 基于年龄和随机性确定教育水平
        if self.age < 18:
            return EducationLevel.PRIMARY
        elif self.age < 25:
            return self._agent_rng.choice([
                EducationLevel.SECONDARY, 
                EducationLevel.TERTIARY
            ], p=[0.6, 0.4])
        else:
            return self._agent_rng.choice([
                EducationLevel.SECONDARY,
                EducationLevel.TERTIARY,
                EducationLevel.POSTGRADUATE
            ], p=[0.4, 0.5, 0.1])
    
    def _generate_skills(self) -> Skills:
        """生成技能"""
        # 技能与教育水平和年龄相关
        education_bonus = {
            EducationLevel.PRIMARY: 0.0,
            EducationLevel.SECONDARY: 0.1,
            EducationLevel.TERTIARY: 0.2,
            EducationLevel.POSTGRADUATE: 0.3,
        }[self.education]
        
        experience_bonus = min(0.3, (self.age - 18) * 0.01)  # 工作经验加成
        
        base_skill = 0.3 + education_bonus + experience_bonus
        noise = self._agent_rng.normal(0, 0.1, 4)  # 个体差异
        
        return Skills(
            cognitive=max(0, min(1, base_skill + noise[0])),
            manual=max(0, min(1, base_skill + noise[1])),
            social=max(0, min(1, base_skill + noise[2])),
            technical=max(0, min(1, base_skill + noise[3])),
        )
    
    def _generate_consumption_preference(self) -> Dict[str, float]:
        """生成消费偏好"""
        # 简化的消费偏好：食品、住房、其他
        base_prefs = {'food': 0.3, 'housing': 0.3, 'other': 0.4}
        
        # 根据收入水平调整偏好
        if self.wage > 0:
            income_factor = min(2.0, self.wage / 30000)  # 标准化收入
            base_prefs['food'] *= (1 / income_factor)  # 恩格尔系数
            base_prefs['other'] *= income_factor
        
        # 归一化
        total = sum(base_prefs.values())
        return {k: v/total for k, v in base_prefs.items()}
    
    def _initialize_position(self) -> None:
        """初始化位置"""
        # 随机分布在地图上
        if hasattr(self.model, 'world') and hasattr(self.model.world, 'grid'):
            rows, cols = self.model.world.grid.height, self.model.world.grid.width
            self.position = Position(
                x=self._agent_rng.uniform(0, cols),
                y=self._agent_rng.uniform(0, rows)
            )
    
    def _initialize_balance_sheet(self) -> None:
        """初始化资产负债表"""
        # 初始现金根据年龄和教育水平确定
        initial_cash = self._calculate_initial_wealth()
        
        self.balance_sheet.assets = {
            'cash': initial_cash,
            'savings': 0.0,
            'investments': 0.0,
        }
        
        self.balance_sheet.liabilities = {
            'consumer_debt': 0.0,
            'mortgage': 0.0,
        }
    
    def _calculate_initial_wealth(self) -> float:
        """计算初始财富"""
        # 基于年龄和教育的简单财富模型
        age_factor = max(0, (self.age - 18) / 47)  # 18-65岁工作期间
        education_factor = {
            EducationLevel.PRIMARY: 0.5,
            EducationLevel.SECONDARY: 1.0,
            EducationLevel.TERTIARY: 1.5,
            EducationLevel.POSTGRADUATE: 2.0,
        }[self.education]
        
        base_wealth = 5000 * age_factor * education_factor
        return max(100, base_wealth + self._agent_rng.normal(0, base_wealth * 0.3))
    
    def tick(self) -> None:
        """每个时间步的主要逻辑"""
        # 年龄增长（简化：每个 tick 代表一定时间）
        self._age_tick()
        
        # 就业相关行为
        if self.employment_status == EmploymentStatus.UNEMPLOYED:
            self._job_search()
        elif self.employment_status == EmploymentStatus.EMPLOYED:
            self._work()
        
        # 消费决策
        self._consume()
        
        # 储蓄和投资决策
        self._save_and_invest()
        
        # 健康更新
        self._update_health()
        
        # 社交互动
        self._social_interaction()
    
    def _age_tick(self) -> None:
        """年龄相关更新"""
        # 简化：假设每1000个tick代表1岁
        if self.model.schedule.steps % 1000 == 0:
            self.age += 1
            
            # 检查退休
            if self.age >= 65 and self.employment_status == EmploymentStatus.EMPLOYED:
                self._retire()
            
            # 检查死亡（简化的死亡率模型）
            death_probability = self._calculate_death_probability()
            if self._agent_rng.random() < death_probability:
                self._die()
    
    def _calculate_death_probability(self) -> float:
        """计算死亡概率"""
        # 简化的死亡率模型
        if self.age < 50:
            return 0.001
        elif self.age < 70:
            return 0.01
        else:
            return 0.05 * (1 - self.health)
    
    def _die(self) -> None:
        """死亡处理"""
        self.status = AgentStatus.DECEASED
        self._emit_event(EventType.AGENT_DEATH, {
            'age': self.age,
            'net_worth': self.balance_sheet.net_worth,
        })
    
    def _job_search(self) -> None:
        """求职行为"""
        if self._agent_rng.random() < self.job_search_intensity * 0.1:  # 每个tick有一定概率找到工作
            # 简化的求职成功率模型
            success_probability = self._calculate_job_finding_probability()
            if self._agent_rng.random() < success_probability:
                self._find_job()
    
    def _calculate_job_finding_probability(self) -> float:
        """计算找工作的概率"""
        # 基于技能、教育和市场条件
        skill_factor = self.skills.total_skill_level()
        education_factor = {
            EducationLevel.PRIMARY: 0.1,
            EducationLevel.SECONDARY: 0.2,
            EducationLevel.TERTIARY: 0.3,
            EducationLevel.POSTGRADUATE: 0.4,
        }[self.education]
        
        # 市场条件（简化：基于失业率）
        market_factor = 0.5  # W2: 从模型中获取实际失业率
        
        return skill_factor * education_factor * market_factor
    
    def _find_job(self) -> None:
        """找到工作"""
        # 简化：随机分配雇主和工资
        # W2: 实现更复杂的匹配机制
        self.employment_status = EmploymentStatus.EMPLOYED
        self.wage = self._calculate_wage()
        
        self._emit_event(EventType.AGENT_JOB_CHANGE, {
            'new_status': self.employment_status.value,
            'wage': self.wage,
        })
    
    def _calculate_wage(self) -> float:
        """计算工资"""
        # 基于技能和教育的工资模型
        skill_premium = self.skills.total_skill_level()
        education_premium = {
            EducationLevel.PRIMARY: 1.0,
            EducationLevel.SECONDARY: 1.3,
            EducationLevel.TERTIARY: 1.8,
            EducationLevel.POSTGRADUATE: 2.5,
        }[self.education]
        
        base_wage = 30000  # 年收入基准
        return base_wage * skill_premium * education_premium * (1 + self._agent_rng.normal(0, 0.2))
    
    def _work(self) -> None:
        """工作行为"""
        # 获得工资收入（简化：每个tick获得日工资）
        daily_wage = self.wage / 365
        self.balance_sheet.add_asset('cash', daily_wage)
        
        # 技能增长（工作经验）
        self._update_skills()
    
    def _update_skills(self) -> None:
        """更新技能（通过工作经验）"""
        growth_rate = 0.0001  # 每个工作日的技能增长
        
        self.skills.cognitive += growth_rate * self._agent_rng.normal(1, 0.1)
        self.skills.technical += growth_rate * self._agent_rng.normal(1, 0.1)
        
        # 确保技能不超过上限
        for field in ['cognitive', 'manual', 'social', 'technical']:
            value = getattr(self.skills, field)
            setattr(self.skills, field, min(1.0, value))
    
    def _retire(self) -> None:
        """退休"""
        self.employment_status = EmploymentStatus.RETIRED
        self.employer_id = None
        self.wage = 0.0
        
        # 获得退休金（简化）
        pension = self._calculate_pension()
        self.balance_sheet.add_asset('pension_wealth', pension)
    
    def _calculate_pension(self) -> float:
        """计算退休金"""
        # 简化的退休金计算
        working_years = max(0, self.age - 18)
        return working_years * 1000  # 每工作一年获得1000的退休金
    
    def _consume(self) -> None:
        """消费决策"""
        available_cash = self.balance_sheet.assets.get('cash', 0)
        
        if available_cash > 0:
            # 计算消费金额
            consumption_amount = self._calculate_consumption(available_cash)
            
            if consumption_amount > 0:
                self.balance_sheet.assets['cash'] -= consumption_amount
                
                # 记录消费（W2: 详细的消费品类）
                self._record_consumption(consumption_amount)
    
    def _calculate_consumption(self, available_cash: float) -> float:
        """计算消费金额"""
        # 简化的消费函数：基于收入和财富
        if self.employment_status == EmploymentStatus.EMPLOYED:
            target_consumption = self.wage / 365 * 0.8  # 消费80%的日收入
        else:
            target_consumption = available_cash * 0.05  # 失业时消费5%的现金
        
        # 最低生存消费
        min_consumption = 20.0  # 每日最低消费
        
        return max(min_consumption, min(target_consumption, available_cash))
    
    def _record_consumption(self, amount: float) -> None:
        """记录消费"""
        # W2: 实现详细的消费记录和市场交易
        pass
    
    def _save_and_invest(self) -> None:
        """储蓄和投资决策"""
        available_cash = self.balance_sheet.assets.get('cash', 0)
        
        # 保留一定的现金缓冲
        cash_buffer = self.wage / 12 if self.wage > 0 else 1000
        excess_cash = max(0, available_cash - cash_buffer)
        
        if excess_cash > 100:  # 最低投资门槛
            # 简化的投资决策
            savings_rate = self._calculate_savings_rate()
            savings_amount = excess_cash * savings_rate
            
            self.balance_sheet.assets['cash'] -= savings_amount
            self.balance_sheet.add_asset('savings', savings_amount)
    
    def _calculate_savings_rate(self) -> float:
        """计算储蓄率"""
        # 基于年龄和收入的储蓄率
        age_factor = 0.5 if self.age < 30 else (0.8 if self.age < 50 else 1.0)
        income_factor = min(1.0, self.wage / 50000) if self.wage > 0 else 0.1
        
        return 0.2 * age_factor * income_factor
    
    def _update_health(self) -> None:
        """更新健康状态"""
        # 简化的健康衰减模型
        age_decay = 0.0001 if self.age > 40 else 0
        random_shock = self._agent_rng.normal(0, 0.001)
        
        self.health = max(0, min(1, self.health - age_decay + random_shock))
    
    def _social_interaction(self) -> None:
        """社交互动"""
        # W3-W4: 实现复杂的社交网络和信息传播
        pass
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化状态"""
        state = super().serialize_state()
        state.update({
            'age': self.age,
            'gender': self.gender,
            'education': self.education.value,
            'skills': self.skills.to_dict(),
            'employment_status': self.employment_status.value,
            'employer_id': self.employer_id,
            'wage': self.wage,
            'household_id': self.household_id,
            'health': self.health,
        })
        return state


# W3-W4 扩展点预留：
# - 复杂的生命周期模型（结婚、生育、离婚）
# - 教育投资和人力资本积累
# - 详细的消费品类和效用函数
# - 社交网络和信息传播
# - 迁移决策和地理流动性
# - 政治偏好和投票行为
