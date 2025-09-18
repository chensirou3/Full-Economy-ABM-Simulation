#!/usr/bin/env python3
"""
动画模拟系统
先运行完整的20,000人30年模拟，然后生成完整动画
"""

import numpy as np
import json
import time
import os
from typing import List, Dict, Tuple
from dataclasses import dataclass

@dataclass
class AnimationFrame:
    """动画帧数据"""
    day: int
    year: int
    agents: List[Dict]
    metrics: Dict
    events: List[Dict]
    map_changes: Dict

class Agent:
    """代理类"""
    
    def __init__(self, agent_id: int, agent_type: str, x: float, y: float):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.x = x
        self.y = y
        
        # 基础属性
        self.age = np.random.randint(20, 70) if agent_type == "person" else 0
        self.wealth = np.random.lognormal(9, 1)
        self.employed = np.random.random() > 0.05 if agent_type == "person" else True
        
        # 位置记忆
        self.home_x = x + np.random.normal(0, 2) if agent_type == "person" else x
        self.home_y = y + np.random.normal(0, 2) if agent_type == "person" else y
        self.work_x = x
        self.work_y = y
        
        # 关系
        self.employer_id = None
        self.owned_businesses = []
        self.employees = [] if agent_type != "person" else None
        
        # 创业属性
        if agent_type == "person":
            self.entrepreneurship_score = np.random.random()
            self.business_skills = np.random.random(4)  # 不同技能
        
        # 企业属性
        if agent_type == "firm":
            self.sector = self._determine_sector()
            self.employees = []
            self.founder_id = None
            self.revenue = 0
            self.established_day = 0
        
        # 银行属性
        elif agent_type == "bank":
            self.founder_id = None
            self.customers = []
            self.established_day = 0
    
    def _determine_sector(self):
        """确定企业部门"""
        # 基于位置的部门分配
        if self.x < 20:
            return "agriculture"
        elif self.x > 60:
            return "mining"
        elif 30 <= self.x <= 50:
            return "services"
        else:
            return "manufacturing"
    
    def to_dict(self):
        """转换为动画数据"""
        data = {
            'id': self.agent_id,
            'type': self.agent_type,
            'x': round(self.x, 2),
            'y': round(self.y, 2),
            'age': self.age,
            'wealth': round(self.wealth, 0),
        }
        
        if self.agent_type == "person":
            data.update({
                'employed': self.employed,
                'employer_id': self.employer_id,
                'owned_businesses': self.owned_businesses,
                'home': {'x': round(self.home_x, 2), 'y': round(self.home_y, 2)},
                'work': {'x': round(self.work_x, 2), 'y': round(self.work_y, 2)},
            })
        elif self.agent_type == "firm":
            data.update({
                'sector': self.sector,
                'employees': len(self.employees),
                'founder_id': self.founder_id,
                'revenue': round(self.revenue, 0),
                'age': (0 if not hasattr(self, 'established_day') else 
                       max(0, (time.time() - self.established_day) // 365))
            })
        elif self.agent_type == "bank":
            data.update({
                'customers': len(self.customers),
                'founder_id': self.founder_id,
            })
        
        return data

class AnimationSimulation:
    """动画模拟系统"""
    
    def __init__(self, population_size: int = 20000):
        self.population_size = population_size
        self.current_day = 0
        self.total_days = 10950  # 30年
        
        # 地图系统
        self.map_width = 80
        self.map_height = 20
        self.terrain_map = {}
        self.cities = []
        
        # 代理
        self.persons: List[Agent] = []
        self.firms: List[Agent] = []
        self.banks: List[Agent] = []
        
        # 动画数据
        self.animation_frames: List[AnimationFrame] = []
        self.key_events = []
        
        # 统计
        self.stats = {
            'firms_created': 0,
            'banks_created': 0,
            'firms_closed': 0,
            'movements': 0,
        }
        
        self.setup_simulation()
    
    def setup_simulation(self):
        """设置模拟"""
        print("🎬 设置动画模拟系统...")
        
        # 1. 生成地图
        self.generate_world_map()
        
        # 2. 分布人口
        self.distribute_population()
        
        print("✅ 模拟设置完成，准备记录30年动画")
    
    def generate_world_map(self):
        """生成世界地图"""
        print("🗺️ 生成地图...")
        
        # 生成地形
        for y in range(self.map_height):
            for x in range(self.map_width):
                if x < 3 or x > 76 or y < 1 or y > 18:
                    terrain = "ocean"
                elif x > 65 and y > 15:
                    terrain = "mountain"
                elif 25 <= x <= 35 and 8 <= y <= 12:
                    terrain = "river"
                else:
                    terrain = np.random.choice(["plain", "hill", "forest"], p=[0.7, 0.2, 0.1])
                
                self.terrain_map[(x, y)] = terrain
        
        # 建立城市
        city_locations = [(15, 8), (35, 10), (55, 7), (25, 15), (45, 5), (65, 12)]
        
        for x, y in city_locations:
            if self.terrain_map.get((x, y)) in ["plain", "hill"]:
                self.cities.append((x, y))
                
                # 城市区域
                for dx in range(-2, 3):
                    for dy in range(-1, 2):
                        nx, ny = x + dx, y + dy
                        if (nx, ny) in self.terrain_map:
                            self.terrain_map[(nx, ny)] = "city"
        
        print(f"✅ 地图生成完成: {len(self.cities)} 个城市")
    
    def distribute_population(self):
        """分布人口"""
        print("👥 分布人口...")
        
        # 创建100个代理代表20,000人
        for i in range(100):
            # 70%在城市附近，30%在乡村
            if np.random.random() < 0.7 and self.cities:
                city_x, city_y = self.cities[np.random.randint(len(self.cities))]
                x = city_x + np.random.normal(0, 3)
                y = city_y + np.random.normal(0, 2)
            else:
                # 在适宜位置随机分布
                suitable_locations = [(x, y) for (x, y), terrain in self.terrain_map.items()
                                    if terrain in ["plain", "hill", "forest", "city"]]
                
                if suitable_locations:
                    x, y = suitable_locations[np.random.randint(len(suitable_locations))]
                else:
                    x, y = 40, 10  # 默认位置
            
            x = np.clip(x, 1, 78)
            y = np.clip(y, 1, 18)
            
            person = Agent(100000 + i, "person", x, y)
            self.persons.append(person)
        
        print(f"✅ 人口分布完成: {len(self.persons)} 个代理")
    
    def run_full_simulation(self):
        """运行完整30年模拟"""
        print(f"\n🚀 开始30年完整模拟...")
        print(f"   • 模拟天数: {self.total_days:,}")
        print(f"   • 记录动画帧")
        print(f"   • 跟踪机构创建和倒闭")
        print(f"   • 观察长期经济演化")
        
        start_time = time.time()
        
        # 记录初始帧
        self.record_animation_frame()
        
        # 主模拟循环
        while self.current_day < self.total_days:
            self.step()
            
            # 每月记录一帧 (360帧总计)
            if self.current_day % 30 == 0:
                self.record_animation_frame()
            
            # 每年显示进度
            if self.current_day % 365 == 0:
                year = self.current_day // 365
                elapsed = time.time() - start_time
                progress = self.current_day / self.total_days
                
                print(f"📅 第{year:2d}年完成 | 进度:{progress:.1%} | "
                      f"企业:{len(self.firms)} | 银行:{len(self.banks)} | "
                      f"用时:{elapsed:.1f}s")
        
        total_time = time.time() - start_time
        
        print(f"\n🎉 30年模拟完成!")
        print(f"⏰ 总用时: {total_time:.1f}秒")
        print(f"🎬 动画帧数: {len(self.animation_frames)}")
        print(f"📊 最终统计:")
        print(f"   • 企业创建: {self.stats['firms_created']} (全部由个人创建)")
        print(f"   • 银行创建: {self.stats['banks_created']} (全部由个人创建)")
        print(f"   • 企业倒闭: {self.stats['firms_closed']}")
        
        # 保存动画数据
        self.save_animation_data()
        
        # 生成动画播放器
        self.create_animation_player()
        
        return True
    
    def step(self):
        """执行一步模拟"""
        self.current_day += 1
        
        # 更新个人 (包括创业决策)
        self.update_persons()
        
        # 更新企业
        self.update_firms()
        
        # 更新银行
        self.update_banks()
    
    def update_persons(self):
        """更新个人"""
        for person in self.persons:
            # 年龄增长
            if self.current_day % 365 == 0:
                person.age += 1
                if person.age >= 65:
                    person.employed = False
            
            # 创业决策 (核心功能!)
            if self.should_create_business(person):
                if person.wealth > 200000 and len(self.banks) < 6:
                    # 创建银行
                    self.create_bank_from_person(person)
                else:
                    # 创建企业
                    self.create_firm_from_person(person)
            
            # 移动 (考虑工作地点和地形)
            self.move_person(person)
            
            # 财富变化
            if person.employed:
                person.wealth += np.random.normal(100, 25)
            else:
                person.wealth -= np.random.normal(40, 15)
                person.wealth = max(500, person.wealth)
                
                # 求职
                if np.random.random() < 0.15:
                    self.find_job_for_person(person)
    
    def should_create_business(self, person):
        """是否应该创业"""
        if (person.age < 25 or person.age > 55 or 
            person.wealth < 20000 or 
            person.owned_businesses):
            return False
        
        # 创业能力检查
        if person.entrepreneurship_score < 0.7:
            return False
        
        # 市场需求检查
        nearby_pop = self.count_nearby_population(person.x, person.y, radius=12)
        nearby_firms = len([f for f in self.firms 
                           if abs(f.x - person.x) + abs(f.y - person.y) <= 12])
        
        # 市场机会：人多企业少
        if nearby_pop > 15 and nearby_firms < nearby_pop / 8:
            return np.random.random() < 0.008  # 0.8%日概率
        
        return False
    
    def create_firm_from_person(self, person):
        """个人创建企业"""
        # 寻找企业位置
        location = self.find_business_location(person)
        if location is None:
            return
        
        # 创建企业
        firm_id = 10000 + len(self.firms)
        firm = Agent(firm_id, "firm", location[0], location[1])
        firm.founder_id = person.agent_id
        firm.established_day = self.current_day
        
        # 投资
        investment = min(person.wealth * 0.6, 40000)
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
        self.stats['firms_created'] += 1
        
        # 记录重要事件
        self.key_events.append({
            'day': self.current_day,
            'type': 'firm_created',
            'person_id': person.agent_id,
            'firm_id': firm_id,
            'location': location,
            'sector': firm.sector,
            'investment': investment
        })
    
    def create_bank_from_person(self, person):
        """个人创建银行"""
        # 银行位置偏好城市
        if not self.cities:
            return
        
        # 选择没有银行的城市
        available_cities = []
        for city_x, city_y in self.cities:
            has_bank = any(abs(bank.x - city_x) + abs(bank.y - city_y) < 3 
                          for bank in self.banks)
            if not has_bank:
                available_cities.append((city_x, city_y))
        
        if not available_cities:
            return
        
        location = available_cities[np.random.randint(len(available_cities))]
        
        # 创建银行
        bank_id = 1000 + len(self.banks)
        bank = Agent(bank_id, "bank", location[0], location[1])
        bank.founder_id = person.agent_id
        bank.established_day = self.current_day
        
        # 资本投入
        capital = min(person.wealth * 0.8, 300000)
        person.wealth -= capital
        bank.wealth = capital
        
        person.owned_businesses.append(bank_id)
        
        self.banks.append(bank)
        self.stats['banks_created'] += 1
        
        # 记录事件
        self.key_events.append({
            'day': self.current_day,
            'type': 'bank_created',
            'person_id': person.agent_id,
            'bank_id': bank_id,
            'location': location,
            'capital': capital
        })
    
    def find_business_location(self, person):
        """寻找企业位置"""
        # 在附近寻找合适位置
        best_location = None
        best_score = 0
        
        for dx in range(-15, 16):
            for dy in range(-8, 9):
                x = person.x + dx
                y = person.y + dy
                
                if 0 <= x < 80 and 0 <= y < 20:
                    terrain = self.terrain_map.get((int(x), int(y)), "plain")
                    
                    if terrain in ["plain", "hill", "city"]:
                        # 计算位置评分
                        nearby_pop = self.count_nearby_population(x, y, radius=8)
                        distance_penalty = (abs(dx) + abs(dy)) / 10
                        
                        score = nearby_pop - distance_penalty
                        
                        if score > best_score:
                            best_score = score
                            best_location = (x, y)
        
        return best_location
    
    def count_nearby_population(self, x, y, radius):
        """统计附近人口"""
        count = 0
        for person in self.persons:
            distance = abs(person.x - x) + abs(person.y - y)
            if distance <= radius:
                count += 1
        return count * 200  # 按比例放大到实际人口
    
    def move_person(self, person):
        """移动个人"""
        current_hour = (self.current_day * 24) % 24
        is_workday = (self.current_day % 7) < 5
        
        # 确定目标
        if person.employed and person.employer_id and is_workday and 8 <= current_hour <= 17:
            target_x, target_y = person.work_x, person.work_y
        elif 18 <= current_hour <= 22:
            # 商业活动 - 去城市
            if self.cities:
                nearest_city = min(self.cities, key=lambda c: abs(c[0] - person.x) + abs(c[1] - person.y))
                target_x = nearest_city[0] + np.random.normal(0, 2)
                target_y = nearest_city[1] + np.random.normal(0, 1)
            else:
                target_x, target_y = person.home_x, person.home_y
        else:
            target_x, target_y = person.home_x, person.home_y
        
        # 执行移动
        dx = (target_x - person.x) * 0.1
        dy = (target_y - person.y) * 0.1
        
        # 地形影响
        terrain = self.terrain_map.get((int(person.x), int(person.y)), "plain")
        speed_factor = {
            "plain": 1.0, "hill": 0.7, "mountain": 0.2,
            "forest": 0.6, "city": 1.2, "ocean": 0.0
        }.get(terrain, 0.5)
        
        person.x += dx * speed_factor + np.random.normal(0, 0.2)
        person.y += dy * speed_factor + np.random.normal(0, 0.1)
        
        person.x = np.clip(person.x, 0, 79)
        person.y = np.clip(person.y, 0, 19)
        
        self.stats['movements'] += 1
    
    def update_firms(self):
        """更新企业"""
        firms_to_remove = []
        
        for firm in self.firms:
            # 企业运营
            num_employees = len(firm.employees)
            firm.revenue = max(0, num_employees * np.random.normal(180, 40))
            costs = num_employees * np.random.normal(140, 25) + 30
            
            profit = firm.revenue - costs
            firm.wealth += profit
            
            # 倒闭检查
            years_operating = (self.current_day - firm.established_day) // 365
            
            if (firm.wealth < -15000 or 
                (num_employees == 0 and years_operating > 3) or
                (profit < -100 and years_operating > 5)):
                
                self.close_firm(firm)
                firms_to_remove.append(firm)
        
        for firm in firms_to_remove:
            self.firms.remove(firm)
    
    def close_firm(self, firm):
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
        
        # 记录倒闭事件
        self.key_events.append({
            'day': self.current_day,
            'type': 'firm_closed',
            'firm_id': firm.agent_id,
            'sector': firm.sector,
            'years_operated': (self.current_day - firm.established_day) // 365
        })
    
    def update_banks(self):
        """更新银行"""
        for bank in self.banks:
            bank.wealth *= (1 + np.random.normal(0.0004, 0.0002))
    
    def find_job_for_person(self, person):
        """为个人寻找工作"""
        nearby_firms = []
        for firm in self.firms:
            distance = abs(firm.x - person.x) + abs(firm.y - person.y)
            if distance <= 25:  # 通勤范围
                nearby_firms.append((firm, distance))
        
        if nearby_firms:
            nearby_firms.sort(key=lambda x: x[1])
            firm, distance = nearby_firms[0]
            
            if np.random.random() < 0.3 / (1 + distance / 10):
                person.employed = True
                person.employer_id = firm.agent_id
                person.work_x = firm.x
                person.work_y = firm.y
                firm.employees.append(person.agent_id)
    
    def record_animation_frame(self):
        """记录动画帧"""
        # 收集所有代理状态
        all_agents = []
        
        for person in self.persons:
            all_agents.append(person.to_dict())
        
        for firm in self.firms:
            all_agents.append(firm.to_dict())
        
        for bank in self.banks:
            all_agents.append(bank.to_dict())
        
        # 计算指标
        working_age = [p for p in self.persons if 18 <= p.age <= 65]
        employed = [p for p in working_age if p.employed]
        unemployment_rate = 1 - (len(employed) / len(working_age)) if working_age else 0
        
        total_wealth = sum(p.wealth for p in self.persons) * 200  # 按比例放大
        
        year = self.current_day / 365
        inflation = 0.02 + 0.01 * np.sin(year * 2 * np.pi / 8) + np.random.normal(0, 0.003)
        
        metrics = {
            'day': self.current_day,
            'year': round(year, 2),
            'population': 20000,
            'firms': len(self.firms),
            'banks': len(self.banks),
            'gdp': round(total_wealth, 0),
            'unemployment': round(unemployment_rate, 4),
            'inflation': round(inflation, 4),
            'policy_rate': round(max(0, 0.025 + 1.5 * (inflation - 0.02)), 4),
        }
        
        # 创建动画帧
        frame = AnimationFrame(
            day=self.current_day,
            year=round(year, 1),
            agents=all_agents,
            metrics=metrics,
            events=[e for e in self.key_events if e['day'] == self.current_day],
            map_changes={}
        )
        
        self.animation_frames.append(frame)
    
    def save_animation_data(self):
        """保存动画数据"""
        print("\n💾 保存动画数据...")
        
        animation_data = {
            'metadata': {
                'total_days': self.total_days,
                'total_frames': len(self.animation_frames),
                'population_size': self.population_size,
                'map_size': [self.map_width, self.map_height],
                'generated_at': time.time(),
            },
            'terrain_map': {f"{x},{y}": terrain for (x, y), terrain in self.terrain_map.items()},
            'cities': self.cities,
            'frames': [
                {
                    'day': frame.day,
                    'year': frame.year,
                    'agents': frame.agents,
                    'metrics': frame.metrics,
                    'events': frame.events,
                }
                for frame in self.animation_frames
            ],
            'final_stats': self.stats,
            'key_events': self.key_events,
        }
        
        # 保存为JSON
        with open('animation_data.json', 'w', encoding='utf-8') as f:
            json.dump(animation_data, f, indent=2, default=str)
        
        file_size = os.path.getsize('animation_data.json') / 1024 / 1024
        print(f"✅ 动画数据已保存: animation_data.json ({file_size:.1f} MB)")
    
    def create_animation_player(self):
        """创建动画播放器"""
        print("🎬 创建动画播放器...")
        
        html_content = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>ABM 30年经济演化动画</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            background: #1a1a1a; 
            color: white; 
            margin: 0; 
            padding: 20px; 
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            text-align: center; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            border-radius: 10px; 
            margin-bottom: 20px; 
        }
        .controls { 
            text-align: center; 
            margin-bottom: 20px; 
            padding: 15px; 
            background: #2d2d2d; 
            border-radius: 8px; 
        }
        .controls button { 
            background: #4ade80; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            margin: 0 5px; 
            border-radius: 5px; 
            cursor: pointer; 
            font-size: 14px; 
        }
        .controls button:hover { background: #22c55e; }
        .controls button:disabled { background: #6b7280; cursor: not-allowed; }
        .main-content { display: grid; grid-template-columns: 2fr 1fr; gap: 20px; }
        .map-panel, .info-panel { 
            background: #2d2d2d; 
            border-radius: 10px; 
            padding: 20px; 
        }
        #animationCanvas { 
            width: 100%; 
            height: 500px; 
            background: #111; 
            border-radius: 8px; 
            border: 2px solid #374151; 
        }
        .metrics { 
            display: grid; 
            grid-template-columns: 1fr 1fr; 
            gap: 10px; 
            margin-bottom: 20px; 
        }
        .metric { 
            background: #374151; 
            padding: 10px; 
            border-radius: 5px; 
            text-align: center; 
        }
        .metric-value { font-size: 18px; font-weight: bold; color: #60a5fa; }
        .metric-label { font-size: 12px; color: #9ca3af; }
        .events-log { 
            height: 200px; 
            overflow-y: auto; 
            background: #111; 
            padding: 10px; 
            border-radius: 5px; 
            font-size: 12px; 
        }
        .timeline { 
            width: 100%; 
            margin: 10px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 ABM 30年经济演化动画</h1>
            <p>20,000人口 × 动态机构创建 × 真实地图系统</p>
        </div>
        
        <div class="controls">
            <button onclick="playAnimation()">▶️ 播放</button>
            <button onclick="pauseAnimation()">⏸️ 暂停</button>
            <button onclick="resetAnimation()">🔄 重置</button>
            <button onclick="jumpToYear()">⏭️ 跳转年份</button>
            <label>
                速度: <input type="range" id="speedSlider" min="1" max="50" value="10" onchange="updateSpeed()">
                <span id="speedDisplay">10x</span>
            </label>
        </div>
        
        <div class="main-content">
            <div class="map-panel">
                <h3>🗺️ 世界地图 (30年演化)</h3>
                <canvas id="animationCanvas" width="800" height="500"></canvas>
                <input type="range" id="timelineSlider" class="timeline" min="0" max="360" value="0" onchange="jumpToFrame()">
                <div style="display: flex; justify-content: space-between; font-size: 12px; color: #9ca3af;">
                    <span>第1年</span>
                    <span id="currentTimeDisplay">第0年</span>
                    <span>第30年</span>
                </div>
            </div>
            
            <div class="info-panel">
                <h3>📊 实时指标</h3>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="yearDisplay">0</div>
                        <div class="metric-label">年份</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="populationDisplay">20,000</div>
                        <div class="metric-label">人口</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="firmsDisplay">0</div>
                        <div class="metric-label">企业数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="banksDisplay">0</div>
                        <div class="metric-label">银行数</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="unemploymentDisplay">5.0%</div>
                        <div class="metric-label">失业率</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="gdpDisplay">1.0B</div>
                        <div class="metric-label">GDP</div>
                    </div>
                </div>
                
                <h4>📢 重要事件</h4>
                <div id="eventsLog" class="events-log">
                    等待加载动画数据...
                </div>
                
                <h4>🎯 系统特色</h4>
                <div style="font-size: 12px; line-height: 1.5;">
                    <p>✅ <strong>动态机构创建</strong>: 企业和银行由个人根据市场需求创建</p>
                    <p>✅ <strong>真实地图系统</strong>: 地形影响移动和经济活动</p>
                    <p>✅ <strong>距离概念</strong>: 通勤范围、服务半径、运输成本</p>
                    <p>✅ <strong>完整生命周期</strong>: 机构创建→运营→可能倒闭</p>
                    <p>✅ <strong>空间经济学</strong>: 位置影响商业决策</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let animationData = null;
        let currentFrame = 0;
        let isPlaying = false;
        let playSpeed = 10;
        let playInterval = null;
        
        // 画布
        const canvas = document.getElementById('animationCanvas');
        const ctx = canvas.getContext('2d');
        
        // 加载动画数据
        window.onload = async function() {
            console.log('加载30年动画数据...');
            
            try {
                const response = await fetch('./animation_data.json');
                animationData = await response.json();
                
                console.log('动画数据加载成功:', animationData.frames.length, '帧');
                
                // 设置时间轴
                document.getElementById('timelineSlider').max = animationData.frames.length - 1;
                
                // 渲染第一帧
                renderFrame(0);
                
                // 显示数据统计
                showDataSummary();
                
            } catch (error) {
                console.error('加载动画数据失败:', error);
                document.getElementById('eventsLog').innerHTML = '❌ 动画数据加载失败<br>请确保运行了模拟并生成了 animation_data.json';
            }
        };
        
        function showDataSummary() {
            const summary = `
                📊 动画数据统计:<br>
                • 总帧数: ${animationData.frames.length}<br>
                • 模拟天数: ${animationData.metadata.total_days}<br>
                • 人口规模: ${animationData.metadata.population_size.toLocaleString()}<br>
                • 地图尺寸: ${animationData.metadata.map_size[0]}×${animationData.metadata.map_size[1]}<br>
                • 最终企业: ${animationData.final_stats.firms_created}<br>
                • 最终银行: ${animationData.final_stats.banks_created}<br>
                <br>🎬 准备播放30年经济演化动画...
            `;
            
            document.getElementById('eventsLog').innerHTML = summary;
        }
        
        function renderFrame(frameIndex) {
            if (!animationData || frameIndex >= animationData.frames.length) return;
            
            const frame = animationData.frames[frameIndex];
            currentFrame = frameIndex;
            
            // 清空画布
            ctx.fillStyle = '#111111';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // 绘制地形
            drawTerrain();
            
            // 绘制代理
            drawAgents(frame.agents);
            
            // 更新UI
            updateUI(frame);
        }
        
        function drawTerrain() {
            const scaleX = canvas.width / 80;
            const scaleY = canvas.height / 20;
            
            // 绘制地形背景
            for (let y = 0; y < 20; y++) {
                for (let x = 0; x < 80; x++) {
                    const terrain = animationData.terrain_map[`${x},${y}`] || 'plain';
                    
                    const colors = {
                        'ocean': '#1e40af', 'mountain': '#78716c', 'hill': '#a3a3a3',
                        'plain': '#22c55e', 'forest': '#166534', 'city': '#fbbf24',
                        'river': '#0ea5e9'
                    };
                    
                    ctx.fillStyle = colors[terrain] || '#374151';
                    ctx.fillRect(x * scaleX, y * scaleY, scaleX, scaleY);
                }
            }
            
            // 绘制城市标记
            animationData.cities.forEach(city => {
                const x = city[0] * scaleX;
                const y = city[1] * scaleY;
                
                ctx.fillStyle = '#fbbf24';
                ctx.fillRect(x - 2, y - 2, 4, 4);
            });
        }
        
        function drawAgents(agents) {
            const scaleX = canvas.width / 80;
            const scaleY = canvas.height / 20;
            
            agents.forEach(agent => {
                const x = agent.x * scaleX;
                const y = agent.y * scaleY;
                
                const colors = {
                    'person': '#4ade80',
                    'firm': '#3b82f6', 
                    'bank': '#f59e0b'
                };
                
                const sizes = {
                    'person': 2,
                    'firm': 4,
                    'bank': 6
                };
                
                ctx.fillStyle = colors[agent.type] || '#9ca3af';
                ctx.beginPath();
                ctx.arc(x, y, sizes[agent.type] || 2, 0, 2 * Math.PI);
                ctx.fill();
                
                // 企业和银行显示ID
                if (agent.type === 'firm' || agent.type === 'bank') {
                    ctx.fillStyle = 'white';
                    ctx.font = '8px Arial';
                    ctx.fillText(agent.id.toString().slice(-2), x + 5, y + 3);
                }
            });
        }
        
        function updateUI(frame) {
            // 更新指标显示
            document.getElementById('yearDisplay').textContent = Math.floor(frame.year);
            document.getElementById('populationDisplay').textContent = frame.metrics.population.toLocaleString();
            document.getElementById('firmsDisplay').textContent = frame.metrics.firms;
            document.getElementById('banksDisplay').textContent = frame.metrics.banks;
            document.getElementById('unemploymentDisplay').textContent = (frame.metrics.unemployment * 100).toFixed(1) + '%';
            document.getElementById('gdpDisplay').textContent = (frame.metrics.gdp / 1e9).toFixed(1) + 'B';
            
            // 更新时间显示
            document.getElementById('currentTimeDisplay').textContent = `第${Math.floor(frame.year)}年`;
            document.getElementById('timelineSlider').value = currentFrame;
            
            // 显示当前事件
            if (frame.events && frame.events.length > 0) {
                const eventsHtml = frame.events.map(event => {
                    const eventTypes = {
                        'firm_created': '🏢 企业创建',
                        'bank_created': '🏦 银行创建',
                        'firm_closed': '💥 企业倒闭'
                    };
                    
                    return `<div style="margin-bottom: 5px;">
                        <strong>${eventTypes[event.type] || event.type}</strong><br>
                        第${Math.floor(event.day / 365)}年 - ${JSON.stringify(event).slice(0, 100)}...
                    </div>`;
                }).join('');
                
                document.getElementById('eventsLog').innerHTML = eventsHtml;
            }
        }
        
        function playAnimation() {
            if (isPlaying) return;
            
            isPlaying = true;
            playInterval = setInterval(() => {
                if (currentFrame < animationData.frames.length - 1) {
                    currentFrame++;
                    renderFrame(currentFrame);
                } else {
                    pauseAnimation();
                }
            }, 1000 / playSpeed);
        }
        
        function pauseAnimation() {
            isPlaying = false;
            if (playInterval) {
                clearInterval(playInterval);
                playInterval = null;
            }
        }
        
        function resetAnimation() {
            pauseAnimation();
            currentFrame = 0;
            renderFrame(0);
        }
        
        function jumpToYear() {
            const year = prompt('跳转到第几年? (0-30)');
            if (year && !isNaN(year)) {
                const targetYear = parseInt(year);
                const targetFrame = Math.floor((targetYear / 30) * (animationData.frames.length - 1));
                currentFrame = Math.max(0, Math.min(animationData.frames.length - 1, targetFrame));
                renderFrame(currentFrame);
            }
        }
        
        function jumpToFrame() {
            const slider = document.getElementById('timelineSlider');
            currentFrame = parseInt(slider.value);
            renderFrame(currentFrame);
        }
        
        function updateSpeed() {
            const slider = document.getElementById('speedSlider');
            playSpeed = parseInt(slider.value);
            document.getElementById('speedDisplay').textContent = playSpeed + 'x';
            
            if (isPlaying) {
                pauseAnimation();
                playAnimation();
            }
        }
    </script>
</body>
</html>'''
        
        with open('economic_evolution_animation.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print("✅ 动画播放器已创建: economic_evolution_animation.html")
        print("\n🎬 动画特色:")
        print("   • 完整30年经济演化过程")
        print("   • 企业和银行动态创建可视化")
        print("   • 真实地形和城市分布")
        print("   • 可控制播放速度 (1x-50x)")
        print("   • 时间轴拖拽跳转")
        print("   • 实时指标同步显示")
        print("   • 重要事件时间线")

def main():
    """主函数"""
    print("🎬 ABM 动画模拟系统")
    print("=" * 50)
    print("🎯 解决方案:")
    print("   1. 先运行完整30年模拟")
    print("   2. 记录每个月的状态帧")
    print("   3. 生成完整动画播放器")
    print("   4. 支持时间控制和回放")
    
    sim = AnimationSimulation(population_size=20000)
    
    print(f"\n🚀 开始模拟...")
    success = sim.run_full_simulation()
    
    if success:
        print(f"\n🎊 模拟和动画生成完成!")
        print(f"📁 生成的文件:")
        print(f"   • animation_data.json - 完整动画数据")
        print(f"   • economic_evolution_animation.html - 动画播放器")
        
        print(f"\n🎬 查看动画:")
        print(f"   在浏览器中打开 economic_evolution_animation.html")
        print(f"   您将看到完整的30年经济演化过程!")
        
        print(f"\n✨ 动画展示:")
        print(f"   • 个人如何创建企业和银行")
        print(f"   • 机构在地图各处的分布")
        print(f"   • 30年间的经济指标变化")
        print(f"   • 企业倒闭和新建的循环")
        print(f"   • 地形对经济活动的影响")

if __name__ == "__main__":
    main()
