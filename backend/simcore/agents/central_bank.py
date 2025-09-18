"""
央行代理
代表经济体中的中央银行，具有货币政策制定、银行监管等功能
包含由人组成的货币政策委员会，委员投票决定政策
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from .base import BaseAgent, AgentType, AgentStatus
from ..telemetry import EventType


class PolicyTool(Enum):
    """政策工具"""
    INTEREST_RATE = "interest_rate"
    RESERVE_RATIO = "reserve_ratio"
    DISCOUNT_WINDOW = "discount_window"
    QE = "quantitative_easing"        # W3-W4 扩展
    FORWARD_GUIDANCE = "forward_guidance"  # W3-W4 扩展
    MACRO_PRUDENTIAL = "macro_prudential"  # W3-W4 扩展


class CommitteeMemberType(Enum):
    """委员类型"""
    GOVERNOR = "governor"             # 行长
    DEPUTY_GOVERNOR = "deputy_governor"  # 副行长
    BOARD_MEMBER = "board_member"     # 理事
    REGIONAL_PRESIDENT = "regional_president"  # 地区行长


@dataclass
class PolicyProposal:
    """政策提案"""
    proposal_id: int
    proposer_id: int
    tool: PolicyTool
    target_value: float
    current_value: float
    rationale: str
    urgency: float  # [0,1]
    
    def get_change_magnitude(self) -> float:
        """获取变化幅度"""
        return abs(self.target_value - self.current_value)


@dataclass
class CommitteeMember:
    """货币政策委员"""
    member_id: int
    member_type: CommitteeMemberType
    name: str
    
    # 政策偏好
    inflation_weight: float = 0.5     # 通胀目标权重
    employment_weight: float = 0.3    # 就业目标权重
    financial_stability_weight: float = 0.2  # 金融稳定权重
    
    # 个性特征
    dovishness: float = 0.5          # 鸽派程度 [0,1]
    conservatism: float = 0.5        # 保守程度 [0,1]
    data_dependency: float = 0.7     # 数据依赖程度 [0,1]
    
    # 投票历史
    vote_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.vote_history is None:
            self.vote_history = []
    
    def calculate_utility(self, proposal: PolicyProposal, economic_state: Dict[str, float]) -> float:
        """计算提案的效用"""
        # 基于个人偏好和经济状态计算效用
        inflation_gap = economic_state.get('inflation', 0.02) - economic_state.get('inflation_target', 0.02)
        unemployment_gap = economic_state.get('unemployment', 0.05) - economic_state.get('natural_unemployment', 0.05)
        financial_stress = economic_state.get('financial_stress_index', 0.0)
        
        # 计算各目标的损失
        inflation_loss = self.inflation_weight * (inflation_gap ** 2)
        employment_loss = self.employment_weight * (unemployment_gap ** 2)
        stability_loss = self.financial_stability_weight * (financial_stress ** 2)
        
        total_loss = inflation_loss + employment_loss + stability_loss
        
        # 考虑政策变化的成本（保守主义）
        change_cost = self.conservatism * (proposal.get_change_magnitude() ** 2)
        
        return -total_loss - change_cost  # 效用为负损失
    
    def vote_on_proposal(self, proposal: PolicyProposal, economic_state: Dict[str, float]) -> bool:
        """对提案进行投票"""
        utility = self.calculate_utility(proposal, economic_state)
        
        # 基于效用和随机因素决定投票
        # 效用越高，支持概率越大
        support_probability = 1 / (1 + np.exp(-utility * 10))  # Sigmoid函数
        
        # 添加随机性
        random_factor = np.random.normal(0, 0.1)
        final_probability = np.clip(support_probability + random_factor, 0, 1)
        
        vote = np.random.random() < final_probability
        
        # 记录投票历史
        self.vote_history.append({
            'proposal_id': proposal.proposal_id,
            'vote': vote,
            'utility': utility,
            'support_probability': support_probability,
        })
        
        return vote


class CentralBank(BaseAgent):
    """
    中央银行代理类
    代表经济体中的中央银行，负责货币政策和银行监管
    """
    
    def __init__(self, unique_id: int, model, **kwargs):
        super().__init__(unique_id, model, AgentType.CENTRAL_BANK)
        
        # 央行基本属性
        self.bank_name = kwargs.get('bank_name', "Central Bank")
        self.mandate = kwargs.get('mandate', "dual")  # dual, inflation_targeting, employment
        
        # 政策目标
        self.inflation_target = kwargs.get('inflation_target', 0.02)  # 2%
        self.natural_unemployment = kwargs.get('natural_unemployment', 0.05)  # 5%
        self.neutral_rate = kwargs.get('neutral_rate', 0.025)  # 2.5%
        
        # 政策工具
        self.policy_rate = kwargs.get('initial_policy_rate', 0.025)
        self.reserve_requirement = kwargs.get('reserve_requirement', 0.10)
        self.discount_rate = kwargs.get('discount_rate', 0.035)
        
        # Taylor规则参数
        self.taylor_rule_params = {
            'r_star': self.neutral_rate,
            'pi_star': self.inflation_target,
            'phi_pi': kwargs.get('phi_pi', 1.5),      # 通胀反应系数
            'phi_y': kwargs.get('phi_y', 0.5),        # 产出缺口反应系数
            'phi_f': kwargs.get('phi_f', 0.3),        # 金融稳定反应系数
            'smoothing': kwargs.get('smoothing', 0.8), # 利率平滑参数
        }
        
        # 货币政策委员会
        self.committee_size = kwargs.get('committee_size', 7)
        self.committee_members: List[CommitteeMember] = []
        self.voting_threshold = 0.5  # 简单多数
        
        # 会议和决策
        self.meeting_frequency = kwargs.get('meeting_frequency', 30)  # 30天开一次会
        self.last_meeting_date = 0
        self.next_meeting_date = self.meeting_frequency
        self.decision_history: List[Dict[str, Any]] = []
        
        # 经济数据和预测
        self.economic_indicators: Dict[str, float] = {}
        self.forecasts: Dict[str, List[float]] = {}
        self.forecast_horizon = 8  # 8个季度
        
        # 沟通和前瞻指引
        self.communication_strategy = kwargs.get('communication_strategy', 'data_dependent')
        self.forward_guidance_horizon = 4  # 4个季度
        
        # 银行监管
        self.supervised_banks: List[int] = []
        self.systemic_risk_threshold = 0.3
        
        # 初始化委员会
        self._initialize_committee()
        
        # 初始化资产负债表
        self._initialize_balance_sheet()
    
    def _initialize_committee(self) -> None:
        """初始化货币政策委员会"""
        # 创建委员会成员
        member_types = [
            CommitteeMemberType.GOVERNOR,
            CommitteeMemberType.DEPUTY_GOVERNOR,
            CommitteeMemberType.DEPUTY_GOVERNOR,
        ]
        
        # 添加理事和地区行长
        for i in range(self.committee_size - 3):
            if i % 2 == 0:
                member_types.append(CommitteeMemberType.BOARD_MEMBER)
            else:
                member_types.append(CommitteeMemberType.REGIONAL_PRESIDENT)
        
        for i, member_type in enumerate(member_types):
            member = CommitteeMember(
                member_id=i,
                member_type=member_type,
                name=f"{member_type.value}_{i}",
                
                # 随机生成偏好（有一定相关性）
                inflation_weight=self.rng.beta(2, 2) * 0.6 + 0.2,  # [0.2, 0.8]
                employment_weight=self.rng.beta(2, 2) * 0.4 + 0.1,  # [0.1, 0.5]
                financial_stability_weight=self.rng.beta(2, 2) * 0.3 + 0.1,  # [0.1, 0.4]
                
                # 行长通常更保守
                dovishness=self.rng.beta(3, 3) if member_type != CommitteeMemberType.GOVERNOR else self.rng.beta(2, 4),
                conservatism=self.rng.beta(4, 2) if member_type == CommitteeMemberType.GOVERNOR else self.rng.beta(3, 3),
                data_dependency=self.rng.beta(4, 2),  # 大多数委员都比较依赖数据
            )
            
            # 归一化权重
            total_weight = member.inflation_weight + member.employment_weight + member.financial_stability_weight
            member.inflation_weight /= total_weight
            member.employment_weight /= total_weight
            member.financial_stability_weight /= total_weight
            
            self.committee_members.append(member)
    
    def _initialize_balance_sheet(self) -> None:
        """初始化央行资产负债表"""
        # 央行资产负债表
        self.balance_sheet.assets = {
            'government_bonds': 100000.0,
            'foreign_reserves': 50000.0,
            'loans_to_banks': 0.0,
            'other_assets': 10000.0,
        }
        
        self.balance_sheet.liabilities = {
            'currency_issued': 80000.0,
            'bank_reserves': 70000.0,
            'government_deposits': 5000.0,
            'other_liabilities': 5000.0,
        }
    
    def tick(self) -> None:
        """央行每个时间步的操作"""
        current_time = self.model.schedule.steps if hasattr(self.model, 'schedule') else 0
        
        # 1. 更新经济指标
        self._update_economic_indicators()
        
        # 2. 检查是否需要开会
        if current_time >= self.next_meeting_date:
            self._hold_committee_meeting()
            self.last_meeting_date = current_time
            self.next_meeting_date = current_time + self.meeting_frequency
        
        # 3. 执行货币政策操作
        self._execute_monetary_operations()
        
        # 4. 银行监管
        self._supervise_banks()
        
        # 5. 更新预测
        self._update_forecasts()
        
        # 6. 对外沟通
        self._communicate_policy()
    
    def _update_economic_indicators(self) -> None:
        """更新经济指标"""
        # W2: 从模型中获取实际经济数据
        # 简化实现：模拟经济指标
        
        self.economic_indicators.update({
            'inflation': self.rng.normal(0.02, 0.01),
            'unemployment': self.rng.normal(0.05, 0.01),
            'gdp_growth': self.rng.normal(0.03, 0.02),
            'financial_stress_index': max(0, self.rng.normal(0.1, 0.05)),
            'credit_growth': self.rng.normal(0.05, 0.02),
            'exchange_rate_volatility': self.rng.exponential(0.1),
        })
        
        # 确保指标在合理范围内
        self.economic_indicators['inflation'] = max(-0.05, min(0.10, self.economic_indicators['inflation']))
        self.economic_indicators['unemployment'] = max(0.01, min(0.20, self.economic_indicators['unemployment']))
    
    def _hold_committee_meeting(self) -> None:
        """召开货币政策委员会会议"""
        # 1. 准备经济状态信息
        economic_state = self.economic_indicators.copy()
        economic_state.update({
            'inflation_target': self.inflation_target,
            'natural_unemployment': self.natural_unemployment,
            'current_policy_rate': self.policy_rate,
        })
        
        # 2. 生成政策提案
        proposals = self._generate_policy_proposals(economic_state)
        
        # 3. 委员会投票
        voting_results = []
        for proposal in proposals:
            votes = []
            for member in self.committee_members:
                vote = member.vote_on_proposal(proposal, economic_state)
                votes.append(vote)
            
            support_ratio = sum(votes) / len(votes)
            voting_results.append({
                'proposal': proposal,
                'votes': votes,
                'support_ratio': support_ratio,
                'passed': support_ratio > self.voting_threshold,
            })
        
        # 4. 执行通过的提案
        implemented_changes = []
        for result in voting_results:
            if result['passed']:
                proposal = result['proposal']
                self._implement_policy_change(proposal)
                implemented_changes.append(proposal)
        
        # 5. 记录决策历史
        meeting_record = {
            'date': self.model.schedule.steps if hasattr(self.model, 'schedule') else 0,
            'economic_state': economic_state,
            'proposals': proposals,
            'voting_results': voting_results,
            'implemented_changes': implemented_changes,
        }
        self.decision_history.append(meeting_record)
        
        # 6. 发布政策事件
        if implemented_changes:
            for change in implemented_changes:
                self._emit_event(EventType.INTEREST_RATE_CHANGE, {
                    'tool': change.tool.value,
                    'old_value': change.current_value,
                    'new_value': change.target_value,
                    'rationale': change.rationale,
                })
    
    def _generate_policy_proposals(self, economic_state: Dict[str, float]) -> List[PolicyProposal]:
        """生成政策提案"""
        proposals = []
        proposal_id = len(self.decision_history)
        
        # 1. 基于Taylor规则的利率提案
        taylor_rate = self._calculate_taylor_rule_rate(economic_state)
        
        if abs(taylor_rate - self.policy_rate) > 0.001:  # 至少1个基点的变化
            proposals.append(PolicyProposal(
                proposal_id=proposal_id * 10 + 1,
                proposer_id=0,  # 行长提案
                tool=PolicyTool.INTEREST_RATE,
                target_value=taylor_rate,
                current_value=self.policy_rate,
                rationale=f"Taylor rule suggests rate of {taylor_rate:.3f}",
                urgency=min(1.0, abs(taylor_rate - self.policy_rate) * 10),
            ))
        
        # 2. 基于金融稳定的准备金率提案
        if economic_state.get('financial_stress_index', 0) > self.systemic_risk_threshold:
            new_reserve_ratio = min(0.15, self.reserve_requirement + 0.01)
            proposals.append(PolicyProposal(
                proposal_id=proposal_id * 10 + 2,
                proposer_id=1,  # 副行长提案
                tool=PolicyTool.RESERVE_RATIO,
                target_value=new_reserve_ratio,
                current_value=self.reserve_requirement,
                rationale="Increase reserve ratio due to financial stress",
                urgency=economic_state.get('financial_stress_index', 0),
            ))
        
        # W3-W4: 添加QE、前瞻指引等非常规政策提案
        
        return proposals
    
    def _calculate_taylor_rule_rate(self, economic_state: Dict[str, float]) -> float:
        """计算Taylor规则建议利率"""
        # 标准Taylor规则：r = r* + π + φ_π(π - π*) + φ_y(y - y*)
        
        r_star = self.taylor_rule_params['r_star']
        pi_star = self.taylor_rule_params['pi_star']
        phi_pi = self.taylor_rule_params['phi_pi']
        phi_y = self.taylor_rule_params['phi_y']
        phi_f = self.taylor_rule_params['phi_f']
        smoothing = self.taylor_rule_params['smoothing']
        
        # 当前通胀和产出缺口
        inflation = economic_state.get('inflation', pi_star)
        inflation_gap = inflation - pi_star
        
        # 简化的产出缺口估计（基于失业率）
        unemployment = economic_state.get('unemployment', self.natural_unemployment)
        output_gap = -(unemployment - self.natural_unemployment) * 2  # Okun's law approximation
        
        # 金融稳定调整
        financial_stress = economic_state.get('financial_stress_index', 0)
        
        # Taylor规则计算
        taylor_rate = (
            r_star + inflation + 
            phi_pi * inflation_gap + 
            phi_y * output_gap +
            phi_f * financial_stress
        )
        
        # 利率平滑
        smoothed_rate = smoothing * self.policy_rate + (1 - smoothing) * taylor_rate
        
        # 确保利率在合理范围内
        return max(0.0, min(0.15, smoothed_rate))
    
    def _implement_policy_change(self, proposal: PolicyProposal) -> None:
        """实施政策变化"""
        if proposal.tool == PolicyTool.INTEREST_RATE:
            self.policy_rate = proposal.target_value
        elif proposal.tool == PolicyTool.RESERVE_RATIO:
            self.reserve_requirement = proposal.target_value
        elif proposal.tool == PolicyTool.DISCOUNT_WINDOW:
            self.discount_rate = proposal.target_value
        # W3-W4: 实施QE、前瞻指引等政策
    
    def _execute_monetary_operations(self) -> None:
        """执行货币政策操作"""
        # 1. 公开市场操作
        self._conduct_open_market_operations()
        
        # 2. 贴现窗口操作
        self._manage_discount_window()
        
        # 3. 准备金管理
        self._manage_reserve_requirements()
    
    def _conduct_open_market_operations(self) -> None:
        """公开市场操作"""
        # 简化实现：根据政策利率目标调整市场流动性
        # W2: 实现与债券市场的交互
        pass
    
    def _manage_discount_window(self) -> None:
        """管理贴现窗口"""
        # W2: 处理银行的贴现窗口申请
        pass
    
    def _manage_reserve_requirements(self) -> None:
        """管理准备金要求"""
        # W2: 与银行系统交互，执行准备金政策
        pass
    
    def _supervise_banks(self) -> None:
        """银行监管"""
        # W2: 监督银行的资本充足率、风险管理等
        # 简化实现：检查系统性风险
        
        if hasattr(self.model, 'banks'):
            # 计算银行系统风险指标
            total_bank_assets = 0
            stressed_banks = 0
            
            for bank in self.model.banks:
                total_bank_assets += bank.balance_sheet.total_assets
                if hasattr(bank, 'risk_metrics') and bank.risk_metrics.capital_ratio < 0.08:
                    stressed_banks += 1
            
            # 如果有大量银行面临压力，采取行动
            if stressed_banks > len(self.model.banks) * 0.2:  # 20%以上的银行有问题
                self._emit_event(EventType.BANK_FAILURE, {
                    'systemic_risk': True,
                    'stressed_banks_ratio': stressed_banks / len(self.model.banks),
                })
    
    def _update_forecasts(self) -> None:
        """更新经济预测"""
        # 简化的预测模型
        # W3-W4: 实现复杂的宏观经济预测模型
        
        current_inflation = self.economic_indicators.get('inflation', 0.02)
        current_unemployment = self.economic_indicators.get('unemployment', 0.05)
        
        # 简单的AR(1)预测
        inflation_forecast = []
        unemployment_forecast = []
        
        for h in range(self.forecast_horizon):
            # 通胀预测：均值回归到目标
            inflation_h = 0.7 * current_inflation + 0.3 * self.inflation_target + self.rng.normal(0, 0.005)
            inflation_forecast.append(inflation_h)
            current_inflation = inflation_h
            
            # 失业率预测
            unemployment_h = 0.8 * current_unemployment + 0.2 * self.natural_unemployment + self.rng.normal(0, 0.002)
            unemployment_forecast.append(unemployment_h)
            current_unemployment = unemployment_h
        
        self.forecasts.update({
            'inflation': inflation_forecast,
            'unemployment': unemployment_forecast,
        })
    
    def _communicate_policy(self) -> None:
        """政策沟通"""
        # W3-W4: 实现复杂的沟通策略和前瞻指引
        pass
    
    def get_policy_stance(self) -> str:
        """获取政策立场"""
        neutral_rate = self.taylor_rule_params['r_star']
        
        if self.policy_rate > neutral_rate + 0.005:
            return "tightening"
        elif self.policy_rate < neutral_rate - 0.005:
            return "accommodative"
        else:
            return "neutral"
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化央行状态"""
        state = super().serialize_state()
        state.update({
            'policy_rate': self.policy_rate,
            'reserve_requirement': self.reserve_requirement,
            'discount_rate': self.discount_rate,
            'inflation_target': self.inflation_target,
            'policy_stance': self.get_policy_stance(),
            'committee_size': len(self.committee_members),
            'last_meeting_date': self.last_meeting_date,
            'next_meeting_date': self.next_meeting_date,
            'economic_indicators': self.economic_indicators,
        })
        return state


# W3-W4 扩展点预留：
# - 非常规货币政策工具（QE/QT、负利率、收益率曲线控制）
# - 复杂的前瞻指引和沟通策略
# - 宏观审慎政策工具
# - 央行数字货币(CBDC)实施
# - 国际货币政策协调
# - 气候变化相关的央行政策
