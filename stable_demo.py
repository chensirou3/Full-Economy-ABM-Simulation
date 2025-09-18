#!/usr/bin/env python3
"""
稳定的ABM演示
解决您的核心问题：企业银行动态创建 + 真实地图 + 距离概念
"""

import numpy as np
import time
import os

class SimpleMap:
    """简化但功能完整的地图"""
    
    def __init__(self, width=80, height=20):
        self.width = width
        self.height = height
        
        # 地形数据
        self.terrain = {}
        self.cities = []
        self.roads = set()
        
        self.generate_map()
    
    def generate_map(self):
        """生成地图"""
        print("🗺️ 生成真实地图...")
        
        # 1. 生成地形
        for y in range(self.height):
            for x in range(self.width):
                if x < 5 or x > 75 or y < 1 or y > 18:
                    terrain = "ocean"
                elif x > 60 and y > 15:
                    terrain = "mountain"
                elif 25 <= x <= 55 and 8 <= y <= 12:
                    terrain = "river"
                else:
                    terrain = np.random.choice(["plain", "hill", "forest"], p=[0.6, 0.2, 0.2])
                
                self.terrain[(x, y)] = terrain
        
        # 2. 建立城市 (分散在地图各处)
        potential_cities = [(20, 10), (40, 8), (60, 15), (15, 5), (65, 6), (35, 14), (50, 4), (25, 16)]
        
        for x, y in potential_cities:
            if self.terrain.get((x, y)) in ["plain", "hill"]:
                self.cities.append((x, y))
                
                # 城市周边发展
                for dx in range(-2, 3):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if (nx, ny) in self.terrain:
                            self.terrain[(nx, ny)] = "city"
        
        # 3. 建设道路连接城市
        for i, city1 in enumerate(self.cities):
            for city2 in self.cities[i+1:]:
                self._build_road(city1, city2)
        
        print(f"✅ 地图完成: {len(self.cities)} 个城市, 道路网络连接")
    
    def _build_road(self, start, end):
        """建设道路"""
        x1, y1 = start
        x2, y2 = end
        
        # 简单直线道路
        steps = max(abs(x2 - x1), abs(y2 - y1))
        
        for i in range(steps + 1):
            if steps > 0:
                t = i / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                
                if self.terrain.get((x, y)) not in ["ocean", "mountain"]:
                    self.roads.add((x, y))
    
    def calculate_distance(self, pos1, pos2):
        """计算考虑地形的距离"""
        x1, y1 = pos1
        x2, y2 = pos2
        
        # 基础距离
        base_distance = np.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        
        # 地形修正
        avg_x, avg_y = int((x1 + x2) / 2), int((y1 + y2) / 2)
        terrain = self.terrain.get((avg_x, avg_y), "plain")
        
        terrain_factor = {
            "plain": 1.0, "hill": 1.5, "mountain": 3.0,
            "forest": 2.0, "ocean": 10.0, "city": 0.8, "river": 1.2
        }.get(terrain, 1.0)
        
        # 道路修正
        road_factor = 0.7 if (avg_x, avg_y) in self.roads else 1.0
        
        return base_distance * terrain_factor * road_factor * 2.0  # 2公里/格
    
    def is_suitable_for_business(self, x, y):
        """是否适合开企业"""
        terrain = self.terrain.get((int(x), int(y)), "plain")
        return terrain in ["plain", "hill", "city"] and (int(x), int(y)) not in self.roads
    
    def get_terrain_symbol(self, x, y):
        """获取地形符号"""
        terrain = self.terrain.get((x, y), "plain")
        
        if (x, y) in self.roads:
            return "="
        
        symbols = {
            "ocean": "~", "mountain": "^", "hill": "∩",
            "plain": ".", "forest": "♠", "city": "█", "river": "≈"
        }
        
        return symbols.get(terrain, ".")

class SimpleAgent:
    """简化代理"""
    
    def __init__(self, agent_id, agent_type, x, y, world_map):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.x = x
        self.y = y
        self.world_map = world_map
        
        # 基础属性
        self.age = np.random.randint(20, 70) if agent_type == "person" else 0
        self.wealth = np.random.lognormal(9, 1)
        self.employed = np.random.random() > 0.05 if agent_type == "person" else True
        
        # 位置
        self.home_x = x + np.random.normal(0, 1) if agent_type == "person" else x
        self.home_y = y + np.random.normal(0, 1) if agent_type == "person" else y
        self.work_x = x
        self.work_y = y
        
        # 关系
        self.employer_id = None
        self.owned_businesses = []
        self.employees = [] if agent_type != "person" else None
        
        # 创业能力
        if agent_type == "person":
            self.entrepreneurship = np.random.random()
            self.business_skill = np.random.random()
        
        # 企业属性
        if agent_type == "firm":
            self.sector = self._determine_sector()
            self.employees = []
            self.founder_id = None
            self.established_year = 0
            self.revenue = 0
        
        # 银行属性
        elif agent_type == "bank":
            self.founder_id = None
            self.established_year = 0
            self.customers = []
    
    def _determine_sector(self):
        """根据位置确定企业类型"""
        terrain = self.world_map.terrain.get((int(self.x), int(self.y)), "plain")
        
        if terrain == "plain":
            return "agriculture"
        elif terrain == "mountain":
            return "mining"
        elif terrain == "city":
            return np.random.choice(["services", "retail", "technology"])
        else:
            return "manufacturing"

class EnhancedSimulation:
    """增强模拟系统"""
    
    def __init__(self):
        self.current_day = 0
        self.current_year = 0
        self.total_days = 10950  # 30年
        
        # 创建真实地图
        self.world_map = SimpleMap()
        
        # 代理集合
        self.persons = []
        self.firms = []
        self.banks = []
        
        # 统计数据
        self.stats = {
            'firms_created_by_persons': 0,
            'banks_created_by_persons': 0,
            'firms_closed': 0,
            'banks_closed': 0,
            'total_movements': 0,
        }
        
        # 历史数据
        self.metrics_history = []
        self.snapshots = {}
        
        self.initialize_population()
    
    def initialize_population(self):
        """初始化人口"""
        print("👥 在真实地图上分布20,000人口...")
        
        # 找到适宜居住的位置
        habitable_locations = []
        for (x, y), terrain in self.world_map.terrain.items():
            if terrain in ["plain", "hill", "city", "forest"]:
                habitable_locations.append((x, y))
        
        print(f"✅ 找到 {len(habitable_locations)} 个适宜居住位置")
        
        # 创建100个代理代表20,000人
        for i in range(100):
            # 70%在城市附近，30%在乡村
            if np.random.random() < 0.7 and self.world_map.cities:
                # 城市附近
                city_x, city_y = self.world_map.cities[np.random.randint(len(self.world_map.cities))]
                x = city_x + np.random.normal(0, 3)
                y = city_y + np.random.normal(0, 2)
            else:
                # 随机位置
                loc_idx = np.random.randint(len(habitable_locations))
                x, y = habitable_locations[loc_idx]
            
            x = np.clip(x, 0, 79)
            y = np.clip(y, 0, 19)
            
            person = SimpleAgent(100000 + i, "person", x, y, self.world_map)
            self.persons.append(person)
        
        print(f"✅ 人口分布完成: {len(self.persons)} 个代理代表 20,000 人")
        print("💡 企业和银行将由个人根据市场需求动态创建")
    
    def step(self):
        """执行一步模拟"""
        self.current_day += 1
        self.current_year = self.current_day // 365
        
        # 1. 更新个人 (关键：创业决策)
        new_institutions = self._update_persons()
        
        # 2. 更新企业 (可能倒闭)
        closed_firms = self._update_firms()
        
        # 3. 更新银行
        self._update_banks()
        
        # 4. 计算指标
        metrics = self._calculate_metrics()
        
        # 5. 年度快照
        if self.current_day % 365 == 0:
            self._create_snapshot()
        
        return metrics, new_institutions, closed_firms
    
    def _update_persons(self):
        """更新个人行为"""
        new_firms = 0
        new_banks = 0
        
        for person in self.persons:
            # 年龄增长
            if self.current_day % 365 == 0:
                person.age += 1
                if person.age >= 65:
                    person.employed = False
            
            # 创业决策 - 核心新功能！
            if self._should_person_start_business(person):
                if person.wealth > 300000 and len(self.banks) < 8:
                    # 创建银行
                    if self._create_bank_from_person(person):
                        new_banks += 1
                else:
                    # 创建企业
                    if self._create_firm_from_person(person):
                        new_firms += 1
            
            # 移动 (考虑地形和距离)
            self._move_person(person)
            
            # 财富变化
            if person.employed:
                person.wealth += np.random.normal(100, 20)
            else:
                person.wealth -= np.random.normal(30, 10)
                person.wealth = max(100, person.wealth)
                
                # 求职
                if np.random.random() < 0.1:
                    self._find_job(person)
        
        return {'firms': new_firms, 'banks': new_banks}
    
    def _should_person_start_business(self, person):
        """个人是否应该创业"""
        # 创业条件
        if (person.age < 25 or person.age > 55 or 
            person.wealth < 15000 or 
            person.owned_businesses):
            return False
        
        # 创业能力
        if person.entrepreneurship < 0.6 or person.business_skill < 0.5:
            return False
        
        # 市场机会 - 检查附近是否需要企业
        nearby_population = self._count_nearby_population(person, radius=15)
        nearby_firms = len([f for f in self.firms 
                           if self.world_map.calculate_distance((person.x, person.y), (f.x, f.y)) <= 15])
        
        # 如果人口多但企业少，创业机会大
        if nearby_population > 10 and nearby_firms < nearby_population / 10:
            return np.random.random() < 0.005  # 0.5%日概率
        
        return False
    
    def _create_firm_from_person(self, person):
        """个人创建企业"""
        # 寻找合适位置
        best_location = self._find_business_location(person)
        
        if best_location is None:
            return False
        
        # 创建企业
        firm_id = 10000 + len(self.firms)
        firm = SimpleAgent(firm_id, "firm", best_location[0], best_location[1], self.world_map)
        firm.founder_id = person.agent_id
        firm.established_year = self.current_year
        
        # 投资
        investment = min(person.wealth * 0.5, 30000)
        person.wealth -= investment
        firm.wealth = investment
        
        # 建立关系
        person.owned_businesses.append(firm_id)
        person.employed = True
        person.employer_id = firm_id
        person.work_x = firm.x
        person.work_y = firm.y
        firm.employees.append(person.agent_id)
        
        self.firms.append(firm)
        self.stats['firms_created_by_persons'] += 1
        
        print(f"🏢 第{self.current_year}年: 个人{person.agent_id}在({firm.x:.0f},{firm.y:.0f})创建{firm.sector}企业{firm_id}")
        
        return True
    
    def _create_bank_from_person(self, person):
        """个人创建银行"""
        # 银行偏好城市位置
        if not self.world_map.cities:
            return False
        
        # 选择最佳城市位置
        best_city = None
        best_score = 0
        
        for city_x, city_y in self.world_map.cities:
            # 检查是否已有银行
            has_bank = any(self.world_map.calculate_distance((bank.x, bank.y), (city_x, city_y)) < 5 
                          for bank in self.banks)
            
            if not has_bank:
                # 计算人口服务潜力
                nearby_pop = self._count_nearby_population_at(city_x, city_y, radius=20)
                if nearby_pop > best_score:
                    best_score = nearby_pop
                    best_city = (city_x, city_y)
        
        if best_city is None:
            return False
        
        # 创建银行
        bank_id = 1000 + len(self.banks)
        bank = SimpleAgent(bank_id, "bank", best_city[0], best_city[1], self.world_map)
        bank.founder_id = person.agent_id
        bank.established_year = self.current_year
        
        # 资本投入
        capital = min(person.wealth * 0.7, 500000)
        person.wealth -= capital
        bank.wealth = capital
        
        person.owned_businesses.append(bank_id)
        
        self.banks.append(bank)
        self.stats['banks_created_by_persons'] += 1
        
        print(f"🏦 第{self.current_year}年: 个人{person.agent_id}在({bank.x:.0f},{bank.y:.0f})创建银行{bank_id}")
        
        return True
    
    def _find_business_location(self, person):
        """寻找企业位置"""
        # 在附近寻找合适位置
        candidates = []
        
        for dx in range(-20, 21):
            for dy in range(-10, 11):
                x = person.x + dx
                y = person.y + dy
                
                if (0 <= x < 80 and 0 <= y < 20 and 
                    self.world_map.is_suitable_for_business(x, y)):
                    
                    # 计算位置评分
                    nearby_pop = self._count_nearby_population_at(x, y, radius=8)
                    distance_from_person = abs(dx) + abs(dy)
                    
                    score = nearby_pop / (1 + distance_from_person / 5)
                    candidates.append((x, y, score))
        
        if candidates:
            # 选择最佳位置
            candidates.sort(key=lambda x: x[2], reverse=True)
            return (candidates[0][0], candidates[0][1])
        
        return None
    
    def _count_nearby_population(self, person, radius):
        """统计附近人口"""
        count = 0
        for p in self.persons:
            distance = self.world_map.calculate_distance((person.x, person.y), (p.x, p.y))
            if distance <= radius:
                count += 1
        return count * 200  # 按比例放大
    
    def _count_nearby_population_at(self, x, y, radius):
        """统计指定位置附近人口"""
        count = 0
        for p in self.persons:
            distance = self.world_map.calculate_distance((x, y), (p.x, p.y))
            if distance <= radius:
                count += 1
        return count * 200  # 按比例放大
    
    def _move_person(self, person):
        """移动个人 (考虑地形)"""
        current_hour = (self.current_day * 24) % 24
        is_workday = (self.current_day % 7) < 5
        
        # 目标位置
        if person.employed and person.employer_id and is_workday and 8 <= current_hour <= 17:
            target_x, target_y = person.work_x, person.work_y
        elif 18 <= current_hour <= 22:
            # 去最近的城市
            if self.world_map.cities:
                nearest_city = min(self.world_map.cities, 
                                 key=lambda c: abs(c[0] - person.x) + abs(c[1] - person.y))
                target_x, target_y = nearest_city[0] + np.random.normal(0, 1), nearest_city[1] + np.random.normal(0, 1)
            else:
                target_x, target_y = person.home_x, person.home_y
        else:
            target_x, target_y = person.home_x, person.home_y
        
        # 执行移动 (考虑地形阻力)
        self._execute_movement(person, target_x, target_y)
    
    def _execute_movement(self, person, target_x, target_y):
        """执行移动"""
        dx = target_x - person.x
        dy = target_y - person.y
        distance = np.sqrt(dx*dx + dy*dy)
        
        if distance < 0.1:
            return
        
        # 地形影响移动速度
        terrain = self.world_map.terrain.get((int(person.x), int(person.y)), "plain")
        
        speed_factor = {
            "plain": 1.0, "hill": 0.7, "mountain": 0.3,
            "forest": 0.6, "city": 1.2, "ocean": 0.0
        }.get(terrain, 0.5)
        
        # 道路加成
        if (int(person.x), int(person.y)) in self.world_map.roads:
            speed_factor *= 1.5
        
        # 年龄影响
        age_factor = 1.0 if person.age < 50 else max(0.5, 1.0 - (person.age - 50) * 0.01)
        
        base_speed = 0.3 * speed_factor * age_factor
        move_distance = min(base_speed, distance)
        
        person.x += (dx / distance) * move_distance
        person.y += (dy / distance) * move_distance
        
        person.x = np.clip(person.x, 0, 79)
        person.y = np.clip(person.y, 0, 19)
        
        self.stats['total_movements'] += 1
    
    def _update_firms(self):
        """更新企业"""
        closed = 0
        firms_to_remove = []
        
        for firm in self.firms:
            # 企业运营
            num_employees = len(firm.employees)
            firm.revenue = max(0, num_employees * np.random.normal(150, 30))
            costs = num_employees * np.random.normal(120, 20) + 50  # 固定成本
            
            profit = firm.revenue - costs
            firm.wealth += profit
            
            # 倒闭检查
            if firm.wealth < -10000 or (num_employees == 0 and self.current_year - firm.established_year > 5):
                self._close_firm(firm)
                firms_to_remove.append(firm)
                closed += 1
        
        for firm in firms_to_remove:
            self.firms.remove(firm)
        
        return closed
    
    def _close_firm(self, firm):
        """关闭企业"""
        # 解雇员工
        for person in self.persons:
            if person.employer_id == firm.agent_id:
                person.employed = False
                person.employer_id = None
        
        # 通知创始人
        founder = next((p for p in self.persons if p.agent_id == firm.founder_id), None)
        if founder and firm.agent_id in founder.owned_businesses:
            founder.owned_businesses.remove(firm.agent_id)
        
        self.stats['firms_closed'] += 1
        print(f"💥 企业{firm.agent_id}倒闭 (存续{self.current_year - firm.established_year}年)")
    
    def _update_banks(self):
        """更新银行"""
        for bank in self.banks:
            # 银行稳定运营
            bank.wealth *= (1 + np.random.normal(0.0003, 0.0001))
    
    def _find_job(self, person):
        """寻找工作"""
        # 寻找附近企业
        nearby_firms = []
        for firm in self.firms:
            distance = self.world_map.calculate_distance((person.x, person.y), (firm.x, firm.y))
            if distance <= 30:  # 30公里通勤范围
                nearby_firms.append((firm, distance))
        
        if nearby_firms:
            # 距离越近越容易就业
            nearby_firms.sort(key=lambda x: x[1])
            firm, distance = nearby_firms[0]
            
            if np.random.random() < 0.2 / (1 + distance / 10):
                person.employed = True
                person.employer_id = firm.agent_id
                person.work_x = firm.x
                person.work_y = firm.y
                firm.employees.append(person.agent_id)
    
    def _calculate_metrics(self):
        """计算指标"""
        working_age = [p for p in self.persons if 18 <= p.age <= 65]
        employed = [p for p in working_age if p.employed]
        
        unemployment_rate = 1 - (len(employed) / len(working_age)) if working_age else 0
        total_wealth = sum(p.wealth for p in self.persons) * 200  # 按比例放大
        
        # 经济周期
        year = self.current_day / 365
        inflation = 0.02 + 0.01 * np.sin(year * 2 * np.pi / 8) + np.random.normal(0, 0.003)
        policy_rate = max(0, min(0.08, 0.025 + 1.5 * (inflation - 0.02)))
        
        metrics = {
            'year': year,
            'population': 20000,
            'firms': len(self.firms),
            'banks': len(self.banks),
            'gdp': total_wealth,
            'unemployment': unemployment_rate,
            'inflation': inflation,
            'policy_rate': policy_rate,
        }
        
        self.metrics_history.append(metrics)
        return metrics
    
    def _create_snapshot(self):
        """创建年度快照"""
        self.snapshots[self.current_year] = {
            'year': self.current_year,
            'firms': len(self.firms),
            'banks': len(self.banks),
            'stats': self.stats.copy()
        }
    
    def display_state(self):
        """显示当前状态"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("🎬 增强ABM模拟 - 解决所有核心问题")
        print("=" * 70)
        print(f"📅 第{self.current_year:2d}年第{self.current_day%365:3d}天")
        
        # 机构统计 - 展示动态创建
        print(f"🏢 动态机构创建 (由个人决策驱动):")
        print(f"   企业: {len(self.firms)} 个 (个人创建: {self.stats['firms_created_by_persons']}, 倒闭: {self.stats['firms_closed']})")
        print(f"   银行: {len(self.banks)} 个 (个人创建: {self.stats['banks_created_by_persons']})")
        
        # 经济指标
        if self.metrics_history:
            latest = self.metrics_history[-1]
            print(f"📊 经济指标:")
            print(f"   GDP: {latest['gdp']/1e9:.1f}B | 失业率: {latest['unemployment']:5.1%}")
            print(f"   通胀: {latest['inflation']:5.1%} | 政策利率: {latest['policy_rate']:5.1%}")
        
        # 地图显示 - 展示真实地形和分散的机构
        print(f"\n🗺️ 真实地图 (企业银行分布各地):")
        self._render_map()
        
        print(f"\n✅ 解决的问题:")
        print(f"   • 企业/银行由个人根据市场需求创建，不再固定位置")
        print(f"   • 真实地形系统：海洋、山脉、河流、城市、道路")
        print(f"   • 距离概念：地形影响移动速度，距离影响通勤和商业")
        print(f"   • 机构生命周期：创建→运营→可能倒闭")
    
    def _render_map(self):
        """渲染地图"""
        width, height = 80, 20
        map_display = [['.' for _ in range(width)] for _ in range(height)]
        
        # 1. 绘制地形
        for y in range(height):
            for x in range(width):
                map_display[y][x] = self.world_map.get_terrain_symbol(x, y)
        
        # 2. 绘制代理 (注意企业和银行现在分布各地!)
        for person in self.persons:
            x, y = int(person.x), int(person.y)
            if 0 <= x < width and 0 <= y < height:
                map_display[y][x] = '●'
        
        for firm in self.firms:
            x, y = int(firm.x), int(firm.y)
            if 0 <= x < width and 0 <= y < height:
                map_display[y][x] = '■'  # 企业现在分布在地图各处!
        
        for bank in self.banks:
            x, y = int(bank.x), int(bank.y)
            if 0 <= x < width and 0 <= y < height:
                map_display[y][x] = '♦'  # 银行也分布在不同城市!
        
        # 输出地图
        for row in map_display:
            print(''.join(row))
        
        print("🎨 图例: ● 个人 ■ 企业(各地分布) ♦ 银行(各地分布)")
        print("🌍 地形: ~ 海洋 ^ 山脉 ≈ 河流 █ 城市 = 道路 . 平原 ∩ 丘陵 ♠ 森林")
    
    def run_30_year_simulation(self):
        """运行30年模拟"""
        print("\n🚀 开始30年模拟...")
        
        key_years = [1, 5, 10, 15, 20, 25, 30]
        
        for target_year in key_years:
            # 快进到目标年份
            while self.current_year < target_year:
                self.step()
            
            print(f"\n⏭️ 第{target_year}年状态:")
            self.display_state()
            
            if target_year < 30:
                input("\n按回车继续到下一个关键年份...")
        
        # 最终总结
        print(f"\n🎉 30年模拟完成!")
        print(f"📊 最终统计:")
        print(f"   • 企业创建: {self.stats['firms_created_by_persons']} (全部由个人创建)")
        print(f"   • 银行创建: {self.stats['banks_created_by_persons']} (全部由个人创建)")
        print(f"   • 企业倒闭: {self.stats['firms_closed']}")
        print(f"   • 总移动次数: {self.stats['total_movements']:,}")
        
        if self.metrics_history:
            initial = self.metrics_history[0]
            final = self.metrics_history[-1]
            print(f"   • GDP增长: {((final['gdp']/initial['gdp']-1)*100):+.1f}%")
            print(f"   • 失业率变化: {initial['unemployment']:.1%} → {final['unemployment']:.1%}")

def main():
    """主函数"""
    print("🎯 ABM模拟系统 - 完全解决您的问题")
    print("=" * 50)
    print("🔧 修复的核心问题:")
    print("   1. ✅ 企业/银行由个人决策创建，分布地图各处")
    print("   2. ✅ 真实地图系统：地形、河流、道路、城市")
    print("   3. ✅ 距离概念：影响移动、通勤、商业选择")
    print("   4. ✅ 机构生命周期：动态创建和倒闭")
    
    sim = EnhancedSimulation()
    
    input("\n按回车开始30年演示...")
    
    sim.run_30_year_simulation()

if __name__ == "__main__":
    main()
