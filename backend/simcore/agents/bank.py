"""
银行代理
代表经济体中的银行，具有存贷款、风险管理、资本充足率等功能
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import math

from .base import BaseAgent, AgentType, AgentStatus
from ..telemetry import EventType


class BankType(Enum):
    """银行类型"""
    COMMERCIAL = "commercial"     # 商业银行
    INVESTMENT = "investment"     # 投资银行
    CENTRAL = "central"          # 中央银行
    COOPERATIVE = "cooperative"   # 合作银行


class LoanType(Enum):
    """贷款类型"""
    CONSUMER = "consumer"         # 消费贷款
    MORTGAGE = "mortgage"         # 抵押贷款
    BUSINESS = "business"         # 企业贷款
    INTERBANK = "interbank"       # 银行间贷款


class CreditRating(Enum):
    """信用评级"""
    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    D = "D"  # 违约


@dataclass
class Loan:
    """贷款数据结构"""
    loan_id: int
    borrower_id: int
    loan_type: LoanType
    principal: float
    interest_rate: float
    term_months: int
    remaining_balance: float
    monthly_payment: float
    origination_date: int
    credit_rating: CreditRating
    collateral_value: float = 0.0
    is_performing: bool = True
    days_past_due: int = 0
    
    def calculate_pd(self) -> float:
        """计算违约概率"""
        # 简化的PD模型：基于信用评级和逾期天数
        base_pd = {
            CreditRating.AAA: 0.001,
            CreditRating.AA: 0.002,
            CreditRating.A: 0.005,
            CreditRating.BBB: 0.01,
            CreditRating.BB: 0.03,
            CreditRating.B: 0.08,
            CreditRating.CCC: 0.20,
            CreditRating.D: 1.0,
        }[self.credit_rating]
        
        # 逾期调整
        if self.days_past_due > 0:
            overdue_multiplier = 1 + (self.days_past_due / 30) * 0.5
            return min(1.0, base_pd * overdue_multiplier)
        
        return base_pd
    
    def calculate_lgd(self) -> float:
        """计算违约损失率"""
        # 简化的LGD模型：基于贷款类型和抵押品
        base_lgd = {
            LoanType.CONSUMER: 0.6,
            LoanType.MORTGAGE: 0.3,
            LoanType.BUSINESS: 0.5,
            LoanType.INTERBANK: 0.4,
        }[self.loan_type]
        
        # 抵押品调整
        if self.collateral_value > 0:
            collateral_coverage = self.collateral_value / self.remaining_balance
            lgd_reduction = min(0.5, collateral_coverage * 0.3)
            return max(0.1, base_lgd - lgd_reduction)
        
        return base_lgd


@dataclass
class RiskMetrics:
    """风险指标"""
    capital_ratio: float = 0.0
    tier1_ratio: float = 0.0
    leverage_ratio: float = 0.0
    rwa: float = 0.0  # 风险加权资产
    var_1day: float = 0.0  # 1天VaR
    expected_loss: float = 0.0
    credit_concentration: float = 0.0


class Bank(BaseAgent):
    """
    银行代理类
    代表经济体中的银行，具有存贷款、风险管理等功能
    """
    
    def __init__(self, unique_id: int, model, **kwargs):
        super().__init__(unique_id, model, AgentType.BANK)
        
        # 银行基本属性
        self.bank_type = kwargs.get('bank_type', BankType.COMMERCIAL)
        self.bank_name = kwargs.get('bank_name', f"Bank_{unique_id}")
        self.founding_date = kwargs.get('founding_date', 0)
        
        # 监管参数
        self.capital_ratio_floor = kwargs.get('capital_ratio_floor', 0.08)  # 巴塞尔III
        self.tier1_ratio_floor = kwargs.get('tier1_ratio_floor', 0.06)
        self.leverage_ratio_floor = kwargs.get('leverage_ratio_floor', 0.03)
        self.lcr_floor = kwargs.get('lcr_floor', 1.0)  # 流动性覆盖率
        
        # 风险参数
        self.risk_appetite = kwargs.get('risk_appetite', 0.5)  # [0,1]
        self.default_lgd = kwargs.get('default_lgd', 0.45)
        self.credit_loss_provision_rate = 0.01
        
        # 贷款组合
        self.loan_portfolio: Dict[int, Loan] = {}
        self.next_loan_id = 1
        self.total_loans_outstanding = 0.0
        
        # 存款
        self.deposits: Dict[int, Dict[str, Any]] = {}  # 客户ID -> 存款信息
        self.total_deposits = 0.0
        self.deposit_rate = kwargs.get('deposit_rate', 0.02)
        
        # 银行间市场
        self.interbank_loans_given: Dict[int, float] = {}  # 银行ID -> 金额
        self.interbank_loans_received: Dict[int, float] = {}
        self.interbank_rate = 0.03
        
        # 央行关系
        self.central_bank_reserves = kwargs.get('reserves', 10000.0)
        self.required_reserve_ratio = 0.10
        self.discount_window_access = True
        
        # 风险指标
        self.risk_metrics = RiskMetrics()
        
        # 定价模型
        self.base_lending_rate = 0.05
        self.interest_rate_spread = 0.03
        
        # 经营指标
        self.net_interest_income = 0.0
        self.non_interest_income = 0.0
        self.operating_expenses = 0.0
        self.credit_losses = 0.0
        self.roe = 0.0  # 资产回报率
        
        # 初始化资产负债表
        self._initialize_balance_sheet()
    
    def _initialize_balance_sheet(self) -> None:
        """初始化银行资产负债表"""
        initial_capital = 50000.0
        initial_deposits = 200000.0
        
        # 资产
        self.balance_sheet.assets = {
            'cash': 20000.0,
            'central_bank_reserves': self.central_bank_reserves,
            'loans': 0.0,
            'securities': 30000.0,
            'interbank_assets': 0.0,
            'fixed_assets': 10000.0,
        }
        
        # 负债
        self.balance_sheet.liabilities = {
            'deposits': initial_deposits,
            'interbank_liabilities': 0.0,
            'bonds_issued': 0.0,
            'other_liabilities': 5000.0,
        }
        
        # 权益（隐含计算）
        self.total_deposits = initial_deposits
    
    def tick(self) -> None:
        """银行每个时间步的主要业务"""
        # 1. 处理存款和提取
        self._process_deposits_withdrawals()
        
        # 2. 放贷决策
        self._make_lending_decisions()
        
        # 3. 贷款管理和催收
        self._manage_loan_portfolio()
        
        # 4. 银行间市场操作
        self._interbank_operations()
        
        # 5. 风险管理
        self._risk_management()
        
        # 6. 计算收益和费用
        self._calculate_pnl()
        
        # 7. 监管合规检查
        self._regulatory_compliance()
    
    def _process_deposits_withdrawals(self) -> None:
        """处理存款和提取"""
        # W2: 实现与个人和企业代理的存款交互
        # 简化实现：随机存款流入流出
        
        # 存款流入
        daily_deposits = self.rng.normal(1000, 200)
        if daily_deposits > 0:
            self.total_deposits += daily_deposits
            self.balance_sheet.liabilities['deposits'] += daily_deposits
            self.balance_sheet.assets['cash'] += daily_deposits
        
        # 存款流出
        daily_withdrawals = self.rng.normal(800, 150)
        if daily_withdrawals > 0 and daily_withdrawals <= self.balance_sheet.assets['cash']:
            self.total_deposits -= daily_withdrawals
            self.balance_sheet.liabilities['deposits'] -= daily_withdrawals
            self.balance_sheet.assets['cash'] -= daily_withdrawals
    
    def _make_lending_decisions(self) -> None:
        """放贷决策"""
        available_funds = self._calculate_available_lending_capacity()
        
        if available_funds > 1000:  # 最低放贷门槛
            # W2: 实现与企业和个人的贷款申请匹配
            # 简化实现：主动寻找放贷机会
            
            target_loan_amount = min(available_funds, 10000)
            if self._should_make_loan(target_loan_amount):
                self._originate_loan(target_loan_amount)
    
    def _calculate_available_lending_capacity(self) -> float:
        """计算可放贷资金"""
        # 基于资本充足率和流动性约束
        current_capital_ratio = self._calculate_capital_ratio()
        
        if current_capital_ratio > self.capital_ratio_floor * 1.2:  # 保留缓冲
            # 可用现金减去准备金要求
            required_reserves = self.total_deposits * self.required_reserve_ratio
            available_cash = self.balance_sheet.assets['cash'] - required_reserves
            
            return max(0, available_cash * 0.8)  # 保留20%流动性缓冲
        
        return 0
    
    def _should_make_loan(self, amount: float) -> bool:
        """判断是否应该放贷"""
        # 基于风险偏好和市场条件
        current_risk_level = self._assess_portfolio_risk()
        
        if current_risk_level > self.risk_appetite:
            return False
        
        # 考虑预期收益
        expected_return = self._calculate_expected_loan_return(amount)
        risk_adjusted_return = expected_return - current_risk_level * 0.1
        
        return risk_adjusted_return > 0.02  # 最低收益要求
    
    def _originate_loan(self, amount: float) -> None:
        """发放贷款"""
        # 简化的贷款发放：创建虚拟借款人
        borrower_id = self.rng.integers(100000, 999999)
        loan_type = self.rng.choice(list(LoanType))
        
        # 根据贷款类型确定参数
        if loan_type == LoanType.MORTGAGE:
            term_months = 360  # 30年
            base_rate = 0.04
        elif loan_type == LoanType.BUSINESS:
            term_months = 60   # 5年
            base_rate = 0.06
        else:  # CONSUMER
            term_months = 36   # 3年
            base_rate = 0.08
        
        # 风险定价
        credit_rating = self._assess_borrower_credit(borrower_id)
        risk_premium = self._calculate_risk_premium(credit_rating)
        interest_rate = base_rate + risk_premium
        
        # 计算月供
        monthly_rate = interest_rate / 12
        monthly_payment = amount * (monthly_rate * (1 + monthly_rate)**term_months) / ((1 + monthly_rate)**term_months - 1)
        
        # 创建贷款记录
        loan = Loan(
            loan_id=self.next_loan_id,
            borrower_id=borrower_id,
            loan_type=loan_type,
            principal=amount,
            interest_rate=interest_rate,
            term_months=term_months,
            remaining_balance=amount,
            monthly_payment=monthly_payment,
            origination_date=self.model.schedule.steps if hasattr(self.model, 'schedule') else 0,
            credit_rating=credit_rating,
            collateral_value=amount * 0.8 if loan_type == LoanType.MORTGAGE else 0,
        )
        
        self.loan_portfolio[self.next_loan_id] = loan
        self.next_loan_id += 1
        
        # 更新资产负债表
        self.balance_sheet.assets['loans'] += amount
        self.balance_sheet.assets['cash'] -= amount
        self.total_loans_outstanding += amount
    
    def _assess_borrower_credit(self, borrower_id: int) -> CreditRating:
        """评估借款人信用"""
        # 简化的信用评级模型
        credit_score = self.rng.normal(0.6, 0.2)  # 标准化信用分数
        
        if credit_score > 0.9:
            return CreditRating.AAA
        elif credit_score > 0.8:
            return CreditRating.AA
        elif credit_score > 0.7:
            return CreditRating.A
        elif credit_score > 0.6:
            return CreditRating.BBB
        elif credit_score > 0.4:
            return CreditRating.BB
        elif credit_score > 0.2:
            return CreditRating.B
        else:
            return CreditRating.CCC
    
    def _calculate_risk_premium(self, credit_rating: CreditRating) -> float:
        """计算风险溢价"""
        risk_premiums = {
            CreditRating.AAA: 0.001,
            CreditRating.AA: 0.002,
            CreditRating.A: 0.005,
            CreditRating.BBB: 0.01,
            CreditRating.BB: 0.03,
            CreditRating.B: 0.06,
            CreditRating.CCC: 0.12,
            CreditRating.D: 0.20,
        }
        return risk_premiums[credit_rating]
    
    def _manage_loan_portfolio(self) -> None:
        """管理贷款组合"""
        total_payments_received = 0.0
        total_charge_offs = 0.0
        
        for loan_id, loan in list(self.loan_portfolio.items()):
            # 模拟还款
            if self._simulate_loan_payment(loan):
                # 正常还款
                payment = loan.monthly_payment / 30  # 日还款
                total_payments_received += payment
                
                # 更新贷款余额
                interest_portion = loan.remaining_balance * (loan.interest_rate / 365)
                principal_portion = payment - interest_portion
                
                loan.remaining_balance -= principal_portion
                
                if loan.remaining_balance <= 0:
                    # 贷款还清
                    del self.loan_portfolio[loan_id]
                    self.total_loans_outstanding -= loan.principal
            else:
                # 违约处理
                loan.days_past_due += 1
                loan.is_performing = False
                
                # 如果逾期超过90天，进行核销
                if loan.days_past_due > 90:
                    charge_off_amount = loan.remaining_balance
                    total_charge_offs += charge_off_amount
                    
                    del self.loan_portfolio[loan_id]
                    self.total_loans_outstanding -= loan.remaining_balance
        
        # 更新资产负债表
        self.balance_sheet.assets['cash'] += total_payments_received
        self.balance_sheet.assets['loans'] -= total_charge_offs
        self.credit_losses += total_charge_offs
    
    def _simulate_loan_payment(self, loan: Loan) -> bool:
        """模拟贷款还款"""
        # 基于违约概率判断是否还款
        pd = loan.calculate_pd()
        daily_default_prob = 1 - (1 - pd) ** (1/365)
        
        return self.rng.random() > daily_default_prob
    
    def _interbank_operations(self) -> None:
        """银行间市场操作"""
        # 计算流动性需求
        liquidity_need = self._assess_liquidity_need()
        
        if liquidity_need > 0:
            # 需要借入资金
            self._borrow_interbank(liquidity_need)
        elif liquidity_need < -1000:
            # 有多余流动性，可以放贷
            self._lend_interbank(abs(liquidity_need) * 0.5)
    
    def _assess_liquidity_need(self) -> float:
        """评估流动性需求"""
        # 简化的流动性管理
        required_reserves = self.total_deposits * self.required_reserve_ratio
        current_liquid_assets = self.balance_sheet.assets['cash'] + self.central_bank_reserves
        
        return required_reserves - current_liquid_assets
    
    def _borrow_interbank(self, amount: float) -> None:
        """银行间借款"""
        # W2: 实现与其他银行的交互
        # 简化实现：从央行借款
        if self.discount_window_access:
            self.balance_sheet.assets['cash'] += amount
            self.balance_sheet.liabilities['interbank_liabilities'] += amount
    
    def _lend_interbank(self, amount: float) -> None:
        """银行间放贷"""
        # W2: 实现银行间网络
        if self.balance_sheet.assets['cash'] >= amount:
            self.balance_sheet.assets['cash'] -= amount
            self.balance_sheet.assets['interbank_assets'] += amount
    
    def _risk_management(self) -> None:
        """风险管理"""
        # 更新风险指标
        self.risk_metrics.capital_ratio = self._calculate_capital_ratio()
        self.risk_metrics.tier1_ratio = self._calculate_tier1_ratio()
        self.risk_metrics.leverage_ratio = self._calculate_leverage_ratio()
        self.risk_metrics.rwa = self._calculate_rwa()
        self.risk_metrics.expected_loss = self._calculate_expected_loss()
        
        # 风险限额管理
        if self.risk_metrics.capital_ratio < self.capital_ratio_floor * 1.1:
            self._reduce_risk_exposure()
    
    def _calculate_capital_ratio(self) -> float:
        """计算资本充足率"""
        total_capital = self.balance_sheet.net_worth
        rwa = self._calculate_rwa()
        
        if rwa > 0:
            return total_capital / rwa
        return 0
    
    def _calculate_tier1_ratio(self) -> float:
        """计算一级资本充足率"""
        # 简化：假设所有资本都是一级资本
        return self._calculate_capital_ratio()
    
    def _calculate_leverage_ratio(self) -> float:
        """计算杠杆率"""
        tier1_capital = self.balance_sheet.net_worth
        total_exposure = self.balance_sheet.total_assets
        
        if total_exposure > 0:
            return tier1_capital / total_exposure
        return 0
    
    def _calculate_rwa(self) -> float:
        """计算风险加权资产"""
        # 简化的风险权重
        rwa = 0.0
        
        # 现金和央行准备金：0%权重
        rwa += 0.0
        
        # 贷款：基于信用评级的权重
        for loan in self.loan_portfolio.values():
            risk_weight = self._get_loan_risk_weight(loan)
            rwa += loan.remaining_balance * risk_weight
        
        # 银行间资产：20%权重
        rwa += self.balance_sheet.assets.get('interbank_assets', 0) * 0.2
        
        # 证券：50%权重（简化）
        rwa += self.balance_sheet.assets.get('securities', 0) * 0.5
        
        return rwa
    
    def _get_loan_risk_weight(self, loan: Loan) -> float:
        """获取贷款风险权重"""
        # 基于信用评级的风险权重
        weights = {
            CreditRating.AAA: 0.2,
            CreditRating.AA: 0.2,
            CreditRating.A: 0.5,
            CreditRating.BBB: 1.0,
            CreditRating.BB: 1.0,
            CreditRating.B: 1.5,
            CreditRating.CCC: 1.5,
            CreditRating.D: 1.5,
        }
        return weights.get(loan.credit_rating, 1.0)
    
    def _calculate_expected_loss(self) -> float:
        """计算预期损失"""
        total_el = 0.0
        
        for loan in self.loan_portfolio.values():
            pd = loan.calculate_pd()
            lgd = loan.calculate_lgd()
            ead = loan.remaining_balance  # 违约风险敞口
            
            el = pd * lgd * ead
            total_el += el
        
        return total_el
    
    def _assess_portfolio_risk(self) -> float:
        """评估组合风险"""
        if not self.loan_portfolio:
            return 0.0
        
        # 简化的组合风险度量
        avg_pd = sum(loan.calculate_pd() for loan in self.loan_portfolio.values()) / len(self.loan_portfolio)
        concentration_risk = self._calculate_concentration_risk()
        
        return avg_pd + concentration_risk
    
    def _calculate_concentration_risk(self) -> float:
        """计算集中度风险"""
        if not self.loan_portfolio:
            return 0.0
        
        # 按行业/借款人集中度（简化）
        sector_exposure = {}
        total_exposure = sum(loan.remaining_balance for loan in self.loan_portfolio.values())
        
        for loan in self.loan_portfolio.values():
            sector = loan.loan_type.value
            sector_exposure[sector] = sector_exposure.get(sector, 0) + loan.remaining_balance
        
        # 计算赫芬达尔指数
        hhi = sum((exposure / total_exposure) ** 2 for exposure in sector_exposure.values())
        
        return max(0, hhi - 0.25)  # 超过25%集中度开始有风险
    
    def _calculate_expected_loan_return(self, amount: float) -> float:
        """计算预期贷款收益"""
        # 简化的收益计算
        base_return = self.base_lending_rate
        risk_adjustment = self.risk_appetite * 0.02
        
        return base_return + risk_adjustment
    
    def _reduce_risk_exposure(self) -> None:
        """降低风险敞口"""
        # 提高放贷标准
        self.risk_appetite *= 0.95
        
        # 增加准备金
        additional_reserves = self.balance_sheet.total_assets * 0.01
        if self.balance_sheet.assets['cash'] >= additional_reserves:
            self.balance_sheet.assets['cash'] -= additional_reserves
            self.central_bank_reserves += additional_reserves
    
    def _calculate_pnl(self) -> None:
        """计算损益"""
        # 净利息收入
        interest_income = sum(
            loan.remaining_balance * loan.interest_rate / 365 
            for loan in self.loan_portfolio.values()
        )
        interest_expense = self.total_deposits * self.deposit_rate / 365
        self.net_interest_income = interest_income - interest_expense
        
        # 非利息收入（手续费等）
        self.non_interest_income = self.total_deposits * 0.001 / 365  # 0.1%年化手续费
        
        # 运营费用
        self.operating_expenses = self.balance_sheet.total_assets * 0.015 / 365  # 1.5%年化运营费用
        
        # 净利润
        net_profit = self.net_interest_income + self.non_interest_income - self.operating_expenses - self.credit_losses
        
        # 更新现金
        self.balance_sheet.assets['cash'] += net_profit
        
        # 计算ROE
        if self.balance_sheet.net_worth > 0:
            self.roe = net_profit * 365 / self.balance_sheet.net_worth
    
    def _regulatory_compliance(self) -> None:
        """监管合规检查"""
        violations = []
        
        # 资本充足率检查
        if self.risk_metrics.capital_ratio < self.capital_ratio_floor:
            violations.append("capital_ratio")
        
        # 杠杆率检查
        if self.risk_metrics.leverage_ratio < self.leverage_ratio_floor:
            violations.append("leverage_ratio")
        
        # 如果有违规，触发监管事件
        if violations:
            self._emit_event(EventType.BANK_FAILURE, {
                'violations': violations,
                'capital_ratio': self.risk_metrics.capital_ratio,
                'leverage_ratio': self.risk_metrics.leverage_ratio,
            })
            
            # 严重违规可能导致破产
            if len(violations) > 1 or self.risk_metrics.capital_ratio < 0:
                self.declare_bankruptcy()
    
    def serialize_state(self) -> Dict[str, Any]:
        """序列化银行状态"""
        state = super().serialize_state()
        state.update({
            'bank_type': self.bank_type.value,
            'total_loans': len(self.loan_portfolio),
            'total_loans_outstanding': self.total_loans_outstanding,
            'total_deposits': self.total_deposits,
            'capital_ratio': self.risk_metrics.capital_ratio,
            'leverage_ratio': self.risk_metrics.leverage_ratio,
            'net_interest_income': self.net_interest_income,
            'credit_losses': self.credit_losses,
            'roe': self.roe,
        })
        return state


# W3-W4 扩展点预留：
# - 复杂的银行间网络和系统性风险
# - 更精细的信用风险模型（机器学习）
# - 市场风险和操作风险管理
# - 监管资本工具（CoCo债券等）
# - 数字货币和央行数字货币(CBDC)
# - 绿色金融和ESG风险管理
