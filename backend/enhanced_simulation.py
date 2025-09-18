#!/usr/bin/env python3
"""
增强的经济模拟系统
包含真实地图、动态机构创建、距离概念
"""

import numpy as np
import time
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import os

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

from simcore.world.map import WorldMap, MapTile, TerrainType, LandUse
from simcore.config import WorldConfig, SimulationConfig

class EnhancedAgent:
    """增强的代理类"""
    
    def __init__(self, agent_id: int, agent_type: str, x: float, y: float):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.x = x
        self.y = y
        self.age = np.random.randint(18, 80) if agent_type == "person" else 0
        self.wealth = np.random.lognormal(9, 1)
        self.employed = np.random.random() > 0.05 if agent_type == "person" else True
        
        # 新增属性
        self.home_x = x + np.random.normal(0, 2) if agent_type == "person" else x
        self.home_y = y + np.random.normal(0, 2) if agent_type == "person" else y
        self.work_x = 0
        self.work_y = 0
        self.employer_id = None
        self.owned_businesses = []
        self.skills = np.random.random(4)  # [认知, 手工, 社交, 技术]
        
        # 企业特定属性
        if agent_type == "firm":
            self.sector = np.random.choice(["agriculture", "mining", "manufacturing", "services"])
            self.employees = []
            self.founder_id = None
            self.established_day = 0
            self.revenue = 0
            self.costs = 0
        
        # 银行特定属性
        elif agent_type == "bank":
            self.capital_ratio = np.random.normal(0.12, 0.02)
            self.customers = []
            self.founder_id = None
            self.established_day = 0
    
    def distance_to(self, other) -> float:
        """计算到另一个代理的距离"""
        return np.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def to_dict(self):
        """转换为字典"""
        base_data = {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'position': {'x': self.x, 'y': self.y},
            'age': self.age,
            'wealth': self.wealth,
        }
        
        if self.agent_type == "person":
            base_data.update({
                'employment_status': 'employed' if self.employed else 'unemployed',
                'home_position': {'x': self.home_x, 'y': self.home_y},
                'employer_id': self.employer_id,
                'owned_businesses': self.owned_businesses,
                'skills': self.skills.tolist(),
            })
        elif self.agent_type == "firm":
            base_data.update({
                'sector': self.sector,
                'employees': len(self.employees),
                'founder_id': self.founder_id,
                'revenue': self.revenue,
                'costs': self.costs,
            })
        elif self.agent_type == "bank":
            base_data.update({
                'capital_ratio': self.capital_ratio,
                'customers': len(self.customers),
                'founder_id': self.founder_id,
            })
        
        return base_data

class EnhancedEconomicSimulation:
    """增强的经济模拟"""
    
    def __init__(self, population_size=20000):
        self.population_size = population_size
        self.current_day = 0
        self.total_days = 10950  # 30年
        
        # 创建真实地图
        self.world_map = self._create_world_map()
        
        # 代理集合
        self.persons: List[EnhancedAgent] = []
        self.firms: List[EnhancedAgent] = []
        self.banks: List[EnhancedAgent] = []
        
        # 历史数据
        self.metrics_history = []
        self.events_history = []
        self.snapshots = {}
        
        # 机构统计
        self.institution_stats = {
            'firms_created': 0,
            'firms_closed': 0,
            'banks_created': 0,
            'banks_closed': 0
        }
        
        self.initialize()
    
    def _create_world_map(self) -> WorldMap:
        """创建世界地图"""
        print("🗺️ 创建真实世界地图...")
        
        config = WorldConfig(
            grid={'rows': 80, 'cols': 80, 'cell_km': 2.0},
            generator={
                'sea_level': 0.52,
                'mountain_ratio': 0.15,
                'city_count': 8,
                'road_density': 0.6,
                'resource_richness': 1.0
            }
        )
        
        world_map = WorldMap(config)
        world_map.generate()
        
        return world_map
    
    def initialize(self):
        """初始化模拟"""
        print(f"👥 在真实地图上分布 {self.population_size:,} 人口...")
        
        # 获取适宜居住的位置
        habitable_locations = []
        for (x, y), tile in self.world_map.tiles.items():
            if tile.is_habitable():
                # 根据城市距离和便利性加权
                weight = 1.0 + tile.amenities + tile.utilities
                habitable_locations.extend([(x, y)] * int(weight * 10))
        
        if not habitable_locations:
            print("❌ 没有找到适宜居住的位置!")
            return
        
        print(f"✅ 找到 {len(set(habitable_locations))} 个适宜居住位置")
        
        # 创建人口，按地理分布
        for i in range(self.population_size):
            # 选择居住位置 (考虑聚集效应)
            if i < 100:  # 前100个用于可视化
                location = np.random.choice(len(habitable_locations))
                x, y = habitable_locations[location]
                
                # 添加噪声避免完全重叠
                x += np.random.normal(0, 0.5)
                y += np.random.normal(0, 0.5)
                
                person = EnhancedAgent(100000 + i, "person", x, y)
                self.persons.append(person)
            
            # 每1000人显示进度
            if (i + 1) % 1000 == 0:
                print(f"  创建进度: {i+1:,}/{self.population_size:,}")
        
        print(f"✅ 人口分布完成: {len(self.persons)} 个可视化代理")
        
        # 不预先创建企业和银行 - 让个人自己决定创建！
        print("💡 企业和银行将由个人根据需求动态创建")
        
        # 计算初始指标
        self.calculate_metrics()
    
    def step(self):
        """执行一步模拟"""
        self.current_day += 1
        
        # 1. 更新所有个人 (可能创建新机构)
        new_institutions = self.update_persons()
        
        # 2. 更新企业 (可能倒闭)
        closed_firms = self.update_firms()
        
        # 3. 更新银行
        closed_banks = self.update_banks()
        
        # 4. 更新地图状态 (人口密度、土地价格等)
        self.update_map_dynamics()
        
        # 5. 计算指标
        metrics = self.calculate_metrics()
        
        # 6. 记录事件
        self.record_daily_events(new_institutions, closed_firms, closed_banks)
        
        # 7. 年度快照
        if self.current_day % 365 == 0:
            self.create_snapshot()
        
        return metrics
    
    def update_persons(self) -> Dict[str, int]:
        """更新个人代理"""
        new_firms = 0
        new_banks = 0
        
        for person in self.persons:
            # 年龄增长
            if self.current_day % 365 == 0:
                person.age += 1
                
                # 退休
                if person.age >= 65:
                    person.employed = False
                    person.employer_id = None
            
            # 创业决策 (关键新功能!)
            if person.age >= 25 and person.wealth > 20000:
                # 创业概率基于多种因素
                entrepreneurship_prob = self.calculate_entrepreneurship_probability(person)
                
                if np.random.random() < entrepreneurship_prob:
                    # 决定创建企业还是银行
                    if person.wealth > 500000 and len(self.banks) < len(self.persons) // 5000:
                        # 创建银行
                        new_bank = self.create_bank_from_person(person)
                        if new_bank:
                            self.banks.append(new_bank)
                            new_banks += 1
                    else:
                        # 创建企业
                        new_firm = self.create_firm_from_person(person)
                        if new_firm:
                            self.firms.append(new_firm)
                            new_firms += 1
            
            # 移动逻辑 (考虑地形和距离)
            self.update_person_movement(person)
            
            # 就业状态更新
            if not person.employed:
                self.job_search(person)
            
            # 财富更新
            if person.employed:
                person.wealth += np.random.normal(100, 20)
            else:
                person.wealth -= np.random.normal(50, 15)
                person.wealth = max(0, person.wealth)
        
        return {'new_firms': new_firms, 'new_banks': new_banks}
    
    def calculate_entrepreneurship_probability(self, person: EnhancedAgent) -> float:
        """计算创业概率"""
        # 基础概率
        base_prob = 0.001 / 365  # 年概率0.1%
        
        # 年龄因素 (25-45岁最高)
        age_factor = 1.0 if 25 <= person.age <= 45 else 0.5
        
        # 财富因素
        wealth_factor = min(2.0, person.wealth / 50000)
        
        # 技能因素
        skill_factor = np.mean(person.skills)
        
        # 当地市场机会
        market_factor = self.assess_local_market_opportunity(person.x, person.y)
        
        return base_prob * age_factor * wealth_factor * skill_factor * market_factor
    
    def assess_local_market_opportunity(self, x: float, y: float) -> float:
        """评估当地市场机会"""
        # 统计附近的企业和人口
        radius = 10.0
        nearby_firms = 0
        nearby_population = 0
        
        for person in self.persons:
            distance = np.sqrt((x - person.x)**2 + (y - person.y)**2)
            if distance <= radius:
                nearby_population += 1
        
        for firm in self.firms:
            distance = np.sqrt((x - firm.x)**2 + (y - firm.y)**2)
            if distance <= radius:
                nearby_firms += 1
        
        # 企业密度低 = 机会多
        if nearby_population > 0:
            firm_density = nearby_firms / nearby_population
            return max(0.1, 1.0 - firm_density * 20)  # 密度越高机会越少
        
        return 0.5
    
    def create_firm_from_person(self, person: EnhancedAgent) -> Optional[EnhancedAgent]:
        """个人创建企业"""
        # 寻找合适的企业位置
        location = self.find_business_location(person)
        if location is None:
            return None
        
        # 确定企业类型
        business_type = self.determine_business_type(location)
        
        # 创建企业
        firm_id = 10000 + len(self.firms)
        firm = EnhancedAgent(firm_id, "firm", location[0], location[1])
        firm.sector = business_type
        firm.founder_id = person.agent_id
        firm.established_day = self.current_day
        firm.employees = [person.agent_id]  # 创始人是第一个员工
        
        # 初始投资
        initial_investment = min(person.wealth * 0.6, 50000)
        person.wealth -= initial_investment
        firm.wealth = initial_investment
        
        # 建立雇佣关系
        person.employed = True
        person.employer_id = firm_id
        person.work_x = firm.x
        person.work_y = firm.y
        person.owned_businesses.append(firm_id)
        
        self.institution_stats['firms_created'] += 1
        
        print(f"🏢 第{self.current_day//365}年: 个人{person.agent_id}在({location[0]:.1f},{location[1]:.1f})创建{business_type}企业{firm_id}")
        
        return firm
    
    def create_bank_from_person(self, person: EnhancedAgent) -> Optional[EnhancedAgent]:
        """个人创建银行"""
        # 银行需要更高门槛
        if person.wealth < 500000:
            return None
        
        # 寻找商业区位置
        location = self.find_banking_location(person)
        if location is None:
            return None
        
        # 创建银行
        bank_id = 1000 + len(self.banks)
        bank = EnhancedAgent(bank_id, "bank", location[0], location[1])
        bank.founder_id = person.agent_id
        bank.established_day = self.current_day
        bank.customers = []
        
        # 初始资本
        initial_capital = min(person.wealth * 0.8, 1000000)
        person.wealth -= initial_capital
        bank.wealth = initial_capital
        
        person.owned_businesses.append(bank_id)
        
        self.institution_stats['banks_created'] += 1
        
        print(f"🏦 第{self.current_day//365}年: 个人{person.agent_id}在({location[0]:.1f},{location[1]:.1f})创建银行{bank_id}")
        
        return bank
    
    def find_business_location(self, person: EnhancedAgent) -> Optional[Tuple[float, float]]:
        """寻找企业位置"""
        # 在人员附近寻找合适位置
        search_radius = 15.0
        best_location = None
        best_score = 0
        
        # 搜索范围内的位置
        for _ in range(20):  # 随机搜索20个位置
            x = person.x + np.random.uniform(-search_radius, search_radius)
            y = person.y + np.random.uniform(-search_radius, search_radius)
            
            x = np.clip(x, 0, 79)
            y = np.clip(y, 0, 79)
            
            # 检查位置适宜性
            tile = self.world_map.get_tile(int(x), int(y))
            if tile and tile.is_buildable():
                score = tile.get_commercial_attractiveness()
                
                # 避免过度聚集
                nearby_firms = sum(1 for f in self.firms 
                                 if np.sqrt((f.x - x)**2 + (f.y - y)**2) < 5)
                if nearby_firms > 3:
                    score *= 0.5
                
                if score > best_score:
                    best_score = score
                    best_location = (x, y)
        
        return best_location
    
    def find_banking_location(self, person: EnhancedAgent) -> Optional[Tuple[float, float]]:
        """寻找银行位置"""
        # 银行偏好商业中心
        best_location = None
        best_score = 0
        
        # 寻找商业区
        for (x, y), tile in self.world_map.tiles.items():
            if tile.land_use == LandUse.COMMERCIAL and tile.is_buildable():
                # 检查是否已有银行
                nearby_banks = sum(1 for b in self.banks 
                                 if np.sqrt((b.x - x)**2 + (b.y - y)**2) < 15)
                
                if nearby_banks == 0:  # 没有竞争银行
                    score = tile.get_commercial_attractiveness()
                    
                    if score > best_score:
                        best_score = score
                        best_location = (float(x), float(y))
        
        return best_location
    
    def determine_business_type(self, location: Tuple[float, float]) -> str:
        """根据位置确定企业类型"""
        x, y = int(location[0]), int(location[1])
        tile = self.world_map.get_tile(x, y)
        
        if tile is None:
            return "services"
        
        # 基于地块特性确定类型
        if tile.get_agricultural_potential() > 0.6:
            return "agriculture"
        elif tile.mineral_wealth > 0.4:
            return "mining"
        elif tile.land_use == LandUse.INDUSTRIAL:
            return "manufacturing"
        else:
            return "services"
    
    def update_person_movement(self, person: EnhancedAgent):
        """更新个人移动 (考虑地形和距离)"""
        current_hour = (self.current_day * 24) % 24
        is_workday = (self.current_day % 7) < 5
        
        # 确定目标位置
        if person.employed and person.employer_id and is_workday and 8 <= current_hour <= 17:
            # 工作时间 - 去工作地点
            target_x, target_y = person.work_x, person.work_y
        elif 18 <= current_hour <= 22:
            # 下班时间 - 商业活动
            commercial_areas = self.find_nearby_commercial_areas(person.x, person.y)
            if commercial_areas:
                target_x, target_y = np.random.choice(commercial_areas)
            else:
                target_x, target_y = person.home_x, person.home_y
        else:
            # 其他时间 - 回家
            target_x, target_y = person.home_x, person.home_y
        
        # 计算移动 (考虑地形阻力)
        movement = self.calculate_movement_with_terrain(person, target_x, target_y)
        
        person.x = np.clip(person.x + movement[0], 0, 79)
        person.y = np.clip(person.y + movement[1], 0, 19)
    
    def calculate_movement_with_terrain(self, person: EnhancedAgent, target_x: float, target_y: float) -> Tuple[float, float]:
        """计算考虑地形的移动"""
        # 当前位置地形
        current_tile = self.world_map.get_tile(int(person.x), int(person.y))
        target_tile = self.world_map.get_tile(int(target_x), int(target_y))
        
        # 基础移动向量
        dx = target_x - person.x
        dy = target_y - person.y
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance < 0.1:
            return (0, 0)
        
        # 移动速度基于地形
        base_speed = 0.5
        
        if current_tile:
            # 道路质量影响速度
            speed_multiplier = 0.5 + current_tile.road_quality * 0.5
            
            # 地形影响
            terrain_speed = {
                TerrainType.PLAIN: 1.0,
                TerrainType.HILL: 0.7,
                TerrainType.MOUNTAIN: 0.3,
                TerrainType.FOREST: 0.6,
                TerrainType.DESERT: 0.4,
                TerrainType.OCEAN: 0.0,  # 不能通过
                TerrainType.RIVER: 0.8,
            }.get(current_tile.terrain, 0.5)
            
            actual_speed = base_speed * speed_multiplier * terrain_speed
        else:
            actual_speed = base_speed * 0.5
        
        # 年龄影响移动能力
        age_factor = 1.0 if person.age < 50 else max(0.3, 1.0 - (person.age - 50) * 0.02)
        actual_speed *= age_factor
        
        # 计算实际移动
        move_distance = min(actual_speed, distance)
        move_x = (dx / distance) * move_distance
        move_y = (dy / distance) * move_distance
        
        return (move_x, move_y)
    
    def find_nearby_commercial_areas(self, x: float, y: float) -> List[Tuple[float, float]]:
        """寻找附近商业区"""
        commercial_areas = []
        
        for (tx, ty), tile in self.world_map.tiles.items():
            if tile.land_use == LandUse.COMMERCIAL:
                distance = np.sqrt((x - tx)**2 + (y - ty)**2)
                if distance <= 20:  # 20公里范围内
                    commercial_areas.append((float(tx), float(ty)))
        
        return commercial_areas
    
    def update_firms(self) -> int:
        """更新企业 (可能倒闭)"""
        closed_count = 0
        firms_to_remove = []
        
        for firm in self.firms:
            # 企业运营
            firm.revenue = max(0, len(firm.employees) * np.random.normal(200, 50))
            firm.costs = len(firm.employees) * np.random.normal(150, 30)
            
            daily_profit = firm.revenue - firm.costs
            firm.wealth += daily_profit
            
            # 倒闭检查
            if self.should_firm_close(firm):
                self.close_firm(firm)
                firms_to_remove.append(firm)
                closed_count += 1
        
        # 移除倒闭的企业
        for firm in firms_to_remove:
            self.firms.remove(firm)
        
        return closed_count
    
    def should_firm_close(self, firm: EnhancedAgent) -> bool:
        """企业是否应该倒闭"""
        # 倒闭条件
        return (firm.wealth < -10000 or  # 严重亏损
                (len(firm.employees) == 0 and firm.revenue == 0) or  # 无员工无收入
                (self.current_day - firm.established_day) > 365 * 10 and firm.wealth < 1000)  # 长期亏损
    
    def close_firm(self, firm: EnhancedAgent):
        """关闭企业"""
        # 解雇员工
        for person in self.persons:
            if person.employer_id == firm.agent_id:
                person.employed = False
                person.employer_id = None
                print(f"  👤 员工{person.agent_id}失业")
        
        # 通知创始人
        founder = next((p for p in self.persons if p.agent_id == firm.founder_id), None)
        if founder:
            if firm.agent_id in founder.owned_businesses:
                founder.owned_businesses.remove(firm.agent_id)
        
        self.institution_stats['firms_closed'] += 1
        print(f"💥 企业{firm.agent_id}倒闭 (存续{(self.current_day - firm.established_day)//365}年)")
    
    def update_banks(self) -> int:
        """更新银行"""
        # 银行基本不会倒闭 (简化)
        for bank in self.banks:
            bank.wealth *= (1 + np.random.normal(0.0002, 0.0001))  # 稳定增长
        
        return 0
    
    def job_search(self, person: EnhancedAgent):
        """求职"""
        # 寻找附近的企业
        nearby_firms = []
        for firm in self.firms:
            distance = np.sqrt((person.x - firm.x)**2 + (person.y - firm.y)**2)
            if distance <= 30:  # 30公里通勤范围
                nearby_firms.append((firm, distance))
        
        if nearby_firms:
            # 选择最近的企业 (简化)
            nearby_firms.sort(key=lambda x: x[1])
            firm, distance = nearby_firms[0]
            
            # 就业概率与距离反相关
            employment_prob = 0.1 / (1 + distance / 10)
            
            if np.random.random() < employment_prob:
                person.employed = True
                person.employer_id = firm.agent_id
                person.work_x = firm.x
                person.work_y = firm.y
                firm.employees.append(person.agent_id)
                
                print(f"  💼 个人{person.agent_id}在企业{firm.agent_id}找到工作")
    
    def update_map_dynamics(self):
        """更新地图动态"""
        # 更新人口密度
        for tile in self.world_map.tiles.values():
            tile.population_density = 0
        
        # 统计每个地块的人口
        for person in self.persons:
            tile = self.world_map.get_tile(int(person.x), int(person.y))
            if tile:
                tile.population_density += 1
        
        # 更新土地价格 (基于需求)
        for tile in self.world_map.tiles.values():
            if tile.population_density > 0:
                # 人口密度推高土地价格
                demand_factor = 1 + tile.population_density / 100
                tile.land_price *= (1 + 0.001 * demand_factor)
    
    def calculate_metrics(self):
        """计算经济指标"""
        # 人口统计
        working_age = [p for p in self.persons if 18 <= p.age <= 65]
        employed = [p for p in working_age if p.employed]
        
        unemployment_rate = 1 - (len(employed) / len(working_age)) if working_age else 0
        avg_age = np.mean([p.age for p in self.persons]) if self.persons else 35
        
        # 经济指标
        total_wealth = sum(p.wealth for p in self.persons)
        firm_wealth = sum(f.wealth for f in self.firms)
        bank_wealth = sum(b.wealth for b in self.banks)
        
        gdp = total_wealth + firm_wealth + bank_wealth
        
        # 模拟通胀
        year = self.current_day / 365
        inflation = 0.02 + 0.01 * np.sin(year * 2 * np.pi / 8) + np.random.normal(0, 0.002)
        
        # 政策利率
        policy_rate = 0.025 + 1.5 * (inflation - 0.02) + 0.5 * (unemployment_rate - 0.05)
        policy_rate = max(0, min(0.10, policy_rate))
        
        metrics = {
            'timestamp': self.current_day,
            'year': year,
            'kpis': {
                'population': len(self.persons),
                'firms': len(self.firms),
                'banks': len(self.banks),
                'gdp': gdp,
                'unemployment': unemployment_rate,
                'inflation': inflation,
                'policy_rate': policy_rate,
                'average_age': avg_age,
                'total_wealth': total_wealth,
            },
            'institutions': {
                'firms_created': self.institution_stats['firms_created'],
                'firms_closed': self.institution_stats['firms_closed'],
                'banks_created': self.institution_stats['banks_created'],
                'net_firms': len(self.firms),
                'net_banks': len(self.banks),
            }
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def record_daily_events(self, new_institutions: Dict, closed_firms: int, closed_banks: int):
        """记录每日事件"""
        events = []
        
        if new_institutions['new_firms'] > 0:
            events.append({
                'day': self.current_day,
                'type': 'new_firms_created',
                'count': new_institutions['new_firms']
            })
        
        if new_institutions['new_banks'] > 0:
            events.append({
                'day': self.current_day,
                'type': 'new_banks_created', 
                'count': new_institutions['new_banks']
            })
        
        if closed_firms > 0:
            events.append({
                'day': self.current_day,
                'type': 'firms_closed',
                'count': closed_firms
            })
        
        self.events_history.extend(events)
    
    def create_snapshot(self):
        """创建年度快照"""
        year = self.current_day // 365
        
        snapshot = {
            'year': year,
            'day': self.current_day,
            'population': len(self.persons),
            'firms': len(self.firms),
            'banks': len(self.banks),
            'metrics': self.metrics_history[-1] if self.metrics_history else None,
            'institution_stats': self.institution_stats.copy(),
            'map_summary': self.world_map.get_map_summary(),
        }
        
        self.snapshots[year] = snapshot
        print(f"\n📸 第{year}年快照: 人口{snapshot['population']:,}, 企业{snapshot['firms']}, 银行{snapshot['banks']}")
    
    def jump_to_year(self, target_year: int):
        """跳转到指定年份"""
        target_day = target_year * 365
        current_year = self.current_day // 365
        
        if target_year < current_year:
            # 回到过去
            print(f"⏪ 从第{current_year}年回到第{target_year}年...")
            
            # 使用快照恢复 (简化实现)
            available_years = [y for y in self.snapshots.keys() if y <= target_year]
            if available_years:
                restore_year = max(available_years)
                print(f"   从第{restore_year}年快照恢复")
                self.current_day = restore_year * 365
            else:
                print("   重新初始化")
                self.current_day = 0
                self.initialize()
        
        # 快进到目标年份
        while self.current_day < target_day and self.current_day < self.total_days:
            self.step()
            
            # 每季度显示一次进度
            if self.current_day % 90 == 0:
                year = self.current_day // 365
                quarter = (self.current_day % 365) // 90 + 1
                print(f"  ⏭️ 第{year}年Q{quarter}: 人口{len(self.persons):,}, 企业{len(self.firms)}, 银行{len(self.banks)}")
    
    def display_current_state(self):
        """显示当前状态"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        year = self.current_day // 365
        day_in_year = self.current_day % 365
        progress = (self.current_day / self.total_days) * 100
        
        print("🎬 增强ABM模拟 - 真实地图 + 动态机构创建")
        print("=" * 70)
        print(f"📅 第{year:2d}年第{day_in_year:3d}天 | 进度: {progress:5.1f}%")
        
        # 机构统计
        print(f"🏢 机构动态:")
        print(f"   企业: {len(self.firms)} (创建{self.institution_stats['firms_created']}, 倒闭{self.institution_stats['firms_closed']})")
        print(f"   银行: {len(self.banks)} (创建{self.institution_stats['banks_created']}, 倒闭{self.institution_stats['banks_closed']})")
        
        # 经济指标
        if self.metrics_history:
            latest = self.metrics_history[-1]['kpis']
            print(f"📊 经济指标:")
            print(f"   人口: {latest['population']:,} | GDP: {latest['gdp']/1e9:.1f}B")
            print(f"   失业率: {latest['unemployment']:5.1%} | 通胀: {latest['inflation']:5.1%}")
        
        # 地图可视化
        print(f"\n🗺️ 地图状态 (显示前50个代理):")
        self.render_enhanced_map()
        
        print(f"\n💡 特色: 企业和银行由个人创建 | 真实地形影响移动 | 距离影响经济活动")
    
    def render_enhanced_map(self):
        """渲染增强地图"""
        width, height = 80, 20
        map_grid = [['.' for _ in range(width)] for _ in range(height)]
        
        # 绘制地形背景
        for y in range(height):
            for x in range(width):
                tile = self.world_map.get_tile(x, y)
                if tile:
                    if tile.terrain == TerrainType.OCEAN:
                        map_grid[y][x] = '~'
                    elif tile.terrain == TerrainType.MOUNTAIN:
                        map_grid[y][x] = '^'
                    elif tile.terrain == TerrainType.RIVER:
                        map_grid[y][x] = '≈'
                    elif tile.land_use == LandUse.COMMERCIAL:
                        map_grid[y][x] = '▓'
                    elif tile.land_use == LandUse.RESIDENTIAL:
                        map_grid[y][x] = '░'
                    elif tile.road_quality > 0.5:
                        map_grid[y][x] = '═'
        
        # 绘制代理 (前50个)
        display_agents = self.persons[:40] + self.firms + self.banks
        
        for agent in display_agents:
            x = int(np.clip(agent.x, 0, width-1))
            y = int(np.clip(agent.y, 0, height-1))
            
            symbols = {'person': '●', 'firm': '■', 'bank': '♦'}
            map_grid[y][x] = symbols.get(agent.agent_type, '?')
        
        # 输出地图
        for row in map_grid:
            print(''.join(row))
        
        print("🎨 图例: ● 个人 ■ 企业 ♦ 银行 | ~ 海洋 ^ 山脉 ≈ 河流 ▓ 商业区 ░ 居住区 ═ 道路")

def run_enhanced_demo():
    """运行增强演示"""
    print("🚀 启动增强ABM模拟系统")
    print("🎯 特色功能:")
    print("   ✅ 真实地图系统 (地形、河流、道路、城市)")
    print("   ✅ 动态机构创建 (个人决策驱动)")
    print("   ✅ 距离和地形影响")
    print("   ✅ 机构生命周期 (创建→运营→倒闭)")
    print()
    
    # 创建模拟
    sim = EnhancedEconomicSimulation(population_size=20000)
    
    print("\n🎮 开始30年模拟演示...")
    print("   观察企业和银行的动态创建过程")
    print("   观察地形对代理移动的影响")
    print("   观察经济指标与机构数量的关系")
    
    input("\n按回车开始...")
    
    # 演示关键年份
    key_years = [0, 1, 5, 10, 15, 20, 25, 30]
    
    for target_year in key_years:
        print(f"\n⏭️ 跳转到第{target_year}年...")
        sim.jump_to_year(target_year)
        
        sim.display_current_state()
        
        if target_year < 30:
            input(f"\n按回车继续到下一个关键年份...")
    
    # 最终总结
    print(f"\n🎉 30年模拟完成!")
    print(f"📊 机构演化统计:")
    print(f"   • 企业创建: {sim.institution_stats['firms_created']}")
    print(f"   • 企业倒闭: {sim.institution_stats['firms_closed']}")
    print(f"   • 银行创建: {sim.institution_stats['banks_created']}")
    print(f"   • 最终企业数: {len(sim.firms)}")
    print(f"   • 最终银行数: {len(sim.banks)}")
    
    print(f"\n🗺️ 地图系统验证:")
    map_summary = sim.world_map.get_map_summary()
    print(f"   • 地图尺寸: {map_summary['dimensions']}")
    print(f"   • 城市数量: {map_summary['cities']}")
    print(f"   • 道路网络: {map_summary['road_network_nodes']} 节点")
    print(f"   • 地形分布: {map_summary['terrain_distribution']}")

if __name__ == "__main__":
    run_enhanced_demo()
