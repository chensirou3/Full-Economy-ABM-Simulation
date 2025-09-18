#!/usr/bin/env python3
"""
大规模ABM模拟：100万人 × 300年
优化性能，完整指标记录
"""

import numpy as np
import time
import json
import os
import gc
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict
import sqlite3
from pathlib import Path

@dataclass
class PopulationStats:
    """人口统计"""
    total_population: int
    working_age_population: int
    employed: int
    unemployed: int
    retired: int
    average_age: float
    birth_rate: float
    death_rate: float

@dataclass
class EconomicMetrics:
    """经济指标"""
    gdp: float
    gdp_per_capita: float
    unemployment_rate: float
    inflation_rate: float
    policy_rate: float
    total_firms: int
    total_banks: int
    average_firm_size: float
    total_wealth: float
    gini_coefficient: float

@dataclass
class GeographicStats:
    """地理统计"""
    urban_population: int
    rural_population: int
    population_density_by_region: Dict[str, float]
    firm_distribution: Dict[str, int]
    migration_flows: Dict[str, int]

class MassiveSimulation:
    """大规模模拟系统"""
    
    def __init__(self, population_size: int = 1000000, simulation_years: int = 300):
        self.population_size = population_size
        self.simulation_years = simulation_years
        self.total_days = simulation_years * 365
        self.current_day = 0
        
        # 地图系统 (扩大规模)
        self.map_width = 200  # 扩大地图
        self.map_height = 200
        self.cell_km = 1.0    # 每格1公里
        
        # 分区系统 (性能优化)
        self.regions = {}
        self.region_size = 20  # 20x20的区域
        
        # 代理统计 (不存储所有代理，只存储统计数据)
        self.population_stats = PopulationStats(0, 0, 0, 0, 0, 0.0, 0.0, 0.0)
        self.firm_stats = defaultdict(int)  # 按行业统计
        self.bank_stats = defaultdict(int)  # 按地区统计
        
        # 地理分布 (网格统计)
        self.population_grid = np.zeros((self.map_height, self.map_width))
        self.firm_grid = np.zeros((self.map_height, self.map_width))
        self.bank_grid = np.zeros((self.map_height, self.map_width))
        
        # 地图属性
        self.terrain_map = np.zeros((self.map_height, self.map_width), dtype=int)
        self.elevation_map = np.zeros((self.map_height, self.map_width))
        self.infrastructure_map = np.zeros((self.map_height, self.map_width))
        
        # 历史数据存储
        self.setup_data_storage()
        
        # 性能监控
        self.performance_stats = {
            'steps_per_second': 0,
            'memory_usage_mb': 0,
            'processing_time_per_day': 0
        }
        
        print(f"🎮 大规模模拟系统初始化:")
        print(f"   • 人口规模: {population_size:,}")
        print(f"   • 模拟年数: {simulation_years}")
        print(f"   • 地图大小: {self.map_width}×{self.map_height}")
        print(f"   • 总模拟天数: {self.total_days:,}")
    
    def setup_data_storage(self):
        """设置数据存储"""
        print("💾 设置数据存储系统...")
        
        # 创建SQLite数据库存储历史数据
        self.db_path = Path("massive_simulation.db")
        self.conn = sqlite3.connect(str(self.db_path))
        
        # 创建表结构
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS daily_metrics (
                day INTEGER PRIMARY KEY,
                year REAL,
                population INTEGER,
                firms INTEGER,
                banks INTEGER,
                gdp REAL,
                unemployment_rate REAL,
                inflation_rate REAL,
                policy_rate REAL,
                average_age REAL,
                gini_coefficient REAL,
                urban_population INTEGER,
                rural_population INTEGER
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS major_events (
                day INTEGER,
                event_type TEXT,
                region_x INTEGER,
                region_y INTEGER,
                magnitude REAL,
                description TEXT
            )
        ''')
        
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS regional_stats (
                day INTEGER,
                region_x INTEGER,
                region_y INTEGER,
                population INTEGER,
                firms INTEGER,
                banks INTEGER,
                avg_wealth REAL,
                unemployment_rate REAL
            )
        ''')
        
        self.conn.commit()
        print("✅ 数据库初始化完成")
    
    def initialize_massive_population(self):
        """初始化大规模人口"""
        print(f"👥 初始化 {self.population_size:,} 人口...")
        
        # 1. 生成地图
        self.generate_large_scale_map()
        
        # 2. 分布人口 (使用统计方法，不存储每个个体)
        self.distribute_population_statistically()
        
        # 3. 初始化企业和银行分布
        self.initialize_institutions()
        
        print("✅ 大规模人口初始化完成")
    
    def generate_large_scale_map(self):
        """生成大规模地图"""
        print("🗺️ 生成200×200大规模地图...")
        
        # 使用分形噪声生成地形
        for y in range(self.map_height):
            for x in range(self.map_width):
                # 简化的地形生成
                if x < 10 or x > 190 or y < 10 or y > 190:
                    terrain = 0  # 海洋
                    elevation = 0.0
                elif (x - 100)**2 + (y - 100)**2 > 80**2:
                    terrain = 0  # 外围海洋
                    elevation = 0.0
                else:
                    # 内陆地形
                    distance_from_center = np.sqrt((x - 100)**2 + (y - 100)**2)
                    elevation = max(0, 1 - distance_from_center / 80) + np.random.normal(0, 0.2)
                    elevation = max(0, elevation)  # 确保非负
                    
                    if elevation > 0.8:
                        terrain = 3  # 山脉
                    elif elevation > 0.6:
                        terrain = 2  # 丘陵
                    elif elevation > 0.3:
                        terrain = 1  # 平原
                    else:
                        terrain = 4  # 河流/湖泊
                
                self.terrain_map[y, x] = terrain
                self.elevation_map[y, x] = elevation
        
        # 建立城市网络 (50个主要城市)
        self.establish_city_network()
        
        # 建设基础设施
        self.build_infrastructure_network()
        
        print("✅ 大规模地图生成完成")
    
    def establish_city_network(self):
        """建立城市网络"""
        print("🏙️ 建立城市网络...")
        
        self.cities = []
        
        # 使用网格分布确保城市合理分布
        grid_size = 40  # 每40×40区域一个主要城市
        
        for grid_x in range(0, self.map_width, grid_size):
            for grid_y in range(0, self.map_height, grid_size):
                # 在网格中心附近寻找合适位置
                center_x = grid_x + grid_size // 2
                center_y = grid_y + grid_size // 2
                
                # 确保在地图范围内且是陆地
                if (20 <= center_x <= 180 and 20 <= center_y <= 180 and
                    self.terrain_map[center_y, center_x] in [1, 2]):  # 平原或丘陵
                    
                    city = {
                        'x': center_x,
                        'y': center_y,
                        'size': np.random.randint(50000, 200000),  # 城市规模
                        'specialization': np.random.choice(['trade', 'industry', 'services', 'agriculture'])
                    }
                    
                    self.cities.append(city)
                    
                    # 标记为城市地形
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            cx, cy = center_x + dx, center_y + dy
                            if 0 <= cx < self.map_width and 0 <= cy < self.map_height:
                                self.terrain_map[cy, cx] = 5  # 城市地形
        
        print(f"✅ 建立了 {len(self.cities)} 个城市")
    
    def build_infrastructure_network(self):
        """建设基础设施网络"""
        print("🛣️ 建设基础设施...")
        
        # 连接主要城市的道路网络
        for i, city1 in enumerate(self.cities):
            for city2 in self.cities[i+1:]:
                distance = np.sqrt((city1['x'] - city2['x'])**2 + (city1['y'] - city2['y'])**2)
                
                # 只连接相对较近的城市
                if distance < 80:
                    self._build_road_between_cities(city1, city2)
        
        # 计算每个位置的基础设施水平
        for y in range(self.map_height):
            for x in range(self.map_width):
                # 基于到最近城市的距离计算基础设施
                min_city_distance = float('inf')
                for city in self.cities:
                    distance = np.sqrt((x - city['x'])**2 + (y - city['y'])**2)
                    min_city_distance = min(min_city_distance, distance)
                
                # 基础设施随距离衰减
                if min_city_distance < float('inf'):
                    infrastructure_level = max(0, 1.0 - min_city_distance / 100)
                    self.infrastructure_map[y, x] = infrastructure_level
        
        print("✅ 基础设施网络建设完成")
    
    def _build_road_between_cities(self, city1, city2):
        """在城市间建设道路"""
        x1, y1 = city1['x'], city1['y']
        x2, y2 = city2['x'], city2['y']
        
        # 简化的直线道路
        steps = max(abs(x2 - x1), abs(y2 - y1))
        
        for i in range(steps + 1):
            if steps > 0:
                t = i / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                
                if 0 <= x < self.map_width and 0 <= y < self.map_height:
                    # 提升基础设施水平
                    self.infrastructure_map[y, x] = max(self.infrastructure_map[y, x], 0.7)
    
    def distribute_population_statistically(self):
        """统计方式分布人口"""
        print("📊 统计分布人口...")
        
        # 基于城市吸引力分布人口
        total_attractiveness = 0
        city_attractiveness = []
        
        for city in self.cities:
            # 城市吸引力基于规模和基础设施
            attractiveness = city['size'] * (1 + self.infrastructure_map[city['y'], city['x']])
            city_attractiveness.append(attractiveness)
            total_attractiveness += attractiveness
        
        # 分配人口到城市
        remaining_population = self.population_size
        
        for i, city in enumerate(self.cities):
            if i == len(self.cities) - 1:
                # 最后一个城市获得剩余人口
                city_population = remaining_population
            else:
                # 按吸引力比例分配
                proportion = city_attractiveness[i] / total_attractiveness
                city_population = int(self.population_size * proportion)
                remaining_population -= city_population
            
            # 在城市周围分布人口
            self._distribute_city_population(city, city_population)
        
        # 初始化人口统计
        self.update_population_statistics()
        
        print(f"✅ {self.population_size:,} 人口分布完成")
    
    def _distribute_city_population(self, city, population):
        """在城市周围分布人口"""
        center_x, center_y = city['x'], city['y']
        
        # 使用正态分布在城市周围分布人口
        radius = max(10, int(np.sqrt(population / 1000)))  # 根据人口规模确定分布半径
        
        for _ in range(100):  # 采样100个位置
            # 正态分布采样
            x = int(center_x + np.random.normal(0, radius / 2))
            y = int(center_y + np.random.normal(0, radius / 2))
            
            x = np.clip(x, 0, self.map_width - 1)
            y = np.clip(y, 0, self.map_height - 1)
            
            # 检查地形是否适宜居住
            terrain = self.terrain_map[y, x]
            if terrain in [1, 2, 5]:  # 平原、丘陵、城市
                # 分配人口到这个格子
                grid_population = population // 100
                self.population_grid[y, x] += grid_population
    
    def initialize_institutions(self):
        """初始化机构分布"""
        print("🏢 初始化机构分布...")
        
        # 基于人口分布初始化企业
        total_firms = 0
        total_banks = 0
        
        for y in range(self.map_height):
            for x in range(self.map_width):
                local_population = self.population_grid[y, x]
                
                if local_population > 100:  # 有足够人口基础
                    # 企业数量基于人口 (每100人1个企业)
                    num_firms = max(0, int(local_population / 100 + np.random.normal(0, 0.5)))
                    self.firm_grid[y, x] = num_firms
                    total_firms += num_firms
                    
                    # 银行数量 (每5000人1个银行)
                    if local_population > 5000:
                        num_banks = max(0, int(local_population / 5000))
                        self.bank_grid[y, x] = num_banks
                        total_banks += num_banks
        
        print(f"✅ 初始机构: {total_firms:,} 企业, {total_banks:,} 银行")
    
    def step_massive_simulation(self):
        """执行大规模模拟步骤"""
        step_start_time = time.time()
        
        self.current_day += 1
        current_year = self.current_day / 365
        
        # 1. 人口动态 (生老病死)
        self.update_population_dynamics()
        
        # 2. 经济活动 (就业、生产、消费)
        self.update_economic_activities()
        
        # 3. 机构动态 (创建、运营、倒闭)
        self.update_institution_dynamics()
        
        # 4. 地理流动 (迁移、通勤)
        self.update_geographic_flows()
        
        # 5. 计算指标
        metrics = self.calculate_comprehensive_metrics()
        
        # 6. 记录数据
        if self.current_day % 30 == 0:  # 每月记录
            self.record_metrics_to_db(metrics)
        
        if self.current_day % 365 == 0:  # 每年记录详细数据
            self.record_annual_snapshot(metrics)
        
        # 性能监控
        step_time = time.time() - step_start_time
        self.performance_stats['processing_time_per_day'] = step_time
        self.performance_stats['steps_per_second'] = 1.0 / step_time if step_time > 0 else 0
        
        return metrics
    
    def update_population_dynamics(self):
        """更新人口动态"""
        # 年度人口变化
        if self.current_day % 365 == 0:
            current_year = self.current_day // 365
            
            # 出生率 (随时间下降)
            base_birth_rate = 0.02  # 2%基础出生率
            birth_rate = base_birth_rate * (1 - current_year * 0.001)  # 每年下降0.1%
            
            # 死亡率 (随人口老龄化上升)
            base_death_rate = 0.01
            aging_factor = 1 + current_year * 0.0005  # 老龄化效应
            death_rate = base_death_rate * aging_factor
            
            # 净人口变化
            births = int(self.population_size * birth_rate)
            deaths = int(self.population_size * death_rate)
            net_change = births - deaths
            
            self.population_size += net_change
            
            # 更新人口统计
            self.population_stats.birth_rate = birth_rate
            self.population_stats.death_rate = death_rate
            self.population_stats.total_population = self.population_size
            
            if net_change != 0:
                print(f"👶 第{current_year:.0f}年人口变化: +{births:,} -{deaths:,} = {net_change:+,} (总人口: {self.population_size:,})")
    
    def update_economic_activities(self):
        """更新经济活动"""
        # 就业动态
        working_age_population = int(self.population_size * 0.65)  # 65%工作年龄
        
        # 基于经济周期的就业率
        current_year = self.current_day / 365
        business_cycle = np.sin(current_year * 2 * np.pi / 12)  # 12年经济周期
        
        base_employment_rate = 0.95
        cyclical_adjustment = business_cycle * 0.05
        employment_rate = max(0.85, min(0.98, base_employment_rate + cyclical_adjustment))
        
        employed_population = int(working_age_population * employment_rate)
        unemployed_population = working_age_population - employed_population
        
        # 更新统计
        self.population_stats.working_age_population = working_age_population
        self.population_stats.employed = employed_population
        self.population_stats.unemployed = unemployed_population
        
        # 平均年龄变化 (人口老龄化)
        base_age = 35
        aging_trend = current_year * 0.05  # 每年增长0.05岁
        self.population_stats.average_age = base_age + aging_trend
    
    def update_institution_dynamics(self):
        """更新机构动态"""
        # 企业动态
        self.update_firm_dynamics()
        
        # 银行动态
        self.update_bank_dynamics()
    
    def update_firm_dynamics(self):
        """更新企业动态"""
        current_year = self.current_day / 365
        
        # 企业创建率 (基于经济增长和人口)
        base_creation_rate = 0.001  # 每天0.1%的概率
        
        # 经济增长期创业更活跃
        gdp_growth_rate = 0.03 + 0.02 * np.sin(current_year * 2 * np.pi / 12)
        creation_multiplier = 1 + gdp_growth_rate * 5
        
        daily_creation_rate = base_creation_rate * creation_multiplier
        
        # 计算新企业数量
        expected_new_firms = self.population_size * daily_creation_rate / 100  # 每100人的创业率
        new_firms = np.random.poisson(expected_new_firms)
        
        # 企业倒闭率
        total_firms = np.sum(self.firm_grid)
        base_closure_rate = 0.0005  # 每天0.05%倒闭率
        
        # 经济衰退期倒闭率更高
        recession_factor = max(1, 1 - gdp_growth_rate * 10)
        closure_rate = base_closure_rate * recession_factor
        
        expected_closures = total_firms * closure_rate
        firm_closures = np.random.poisson(expected_closures)
        
        # 在地图上分布新企业和倒闭
        self._distribute_firm_changes(new_firms, firm_closures)
        
        # 记录重要事件
        if new_firms > 100 or firm_closures > 100:
            self.record_major_event(
                'massive_business_change',
                f"企业大变动: +{new_firms} -{firm_closures}"
            )
    
    def _distribute_firm_changes(self, new_firms, closures):
        """分布企业变化"""
        # 新企业倾向于在人口密集区创建
        for _ in range(new_firms):
            # 基于人口密度的概率分布
            population_weights = self.population_grid.flatten()
            population_weights = population_weights / (population_weights.sum() + 1e-10)
            
            # 选择位置
            flat_index = np.random.choice(len(population_weights), p=population_weights)
            y, x = divmod(flat_index, self.map_width)
            
            self.firm_grid[y, x] += 1
        
        # 企业倒闭随机分布
        for _ in range(closures):
            # 找到有企业的位置
            firm_positions = np.where(self.firm_grid > 0)
            
            if len(firm_positions[0]) > 0:
                idx = np.random.randint(len(firm_positions[0]))
                y, x = firm_positions[0][idx], firm_positions[1][idx]
                self.firm_grid[y, x] = max(0, self.firm_grid[y, x] - 1)
    
    def update_bank_dynamics(self):
        """更新银行动态"""
        # 银行变化较少，主要在大城市
        total_population = np.sum(self.population_grid)
        needed_banks = max(10, int(total_population / 50000))  # 每5万人1个银行
        current_banks = int(np.sum(self.bank_grid))
        
        if current_banks < needed_banks:
            # 需要新银行
            new_banks = min(5, needed_banks - current_banks)
            
            for _ in range(new_banks):
                # 在大城市建银行
                large_cities = [city for city in self.cities if city['size'] > 100000]
                
                if large_cities:
                    city = np.random.choice(large_cities)
                    x, y = city['x'], city['y']
                    
                    # 检查是否已有银行
                    if self.bank_grid[y, x] < 2:  # 每个城市最多2个银行
                        self.bank_grid[y, x] += 1
    
    def update_geographic_flows(self):
        """更新地理流动"""
        # 简化的人口迁移模型
        if self.current_day % 365 == 0:  # 年度迁移
            # 从低吸引力地区向高吸引力地区迁移
            migration_rate = 0.02  # 2%年迁移率
            
            migrants = int(self.population_size * migration_rate)
            
            # 计算各地区吸引力
            for y in range(0, self.map_height, 10):
                for x in range(0, self.map_width, 10):
                    # 区域吸引力基于就业机会和生活质量
                    local_firms = np.sum(self.firm_grid[y:y+10, x:x+10])
                    local_population = np.sum(self.population_grid[y:y+10, x:x+10])
                    local_infrastructure = np.mean(self.infrastructure_map[y:y+10, x:x+10])
                    
                    # 计算就业机会密度
                    if local_population > 0:
                        job_density = local_firms / local_population
                        region_attractiveness = job_density * 0.6 + local_infrastructure * 0.4
                        
                        # 简化的迁移逻辑
                        if region_attractiveness > 0.05:
                            # 吸引人口流入
                            immigration = int(migrants * region_attractiveness / 10)
                            self.population_grid[y:y+10, x:x+10] += immigration / 100
                        elif region_attractiveness < 0.02:
                            # 人口流出
                            emigration = int(local_population * 0.01)
                            self.population_grid[y:y+10, x:x+10] = np.maximum(
                                0, self.population_grid[y:y+10, x:x+10] - emigration / 100
                            )
    
    def calculate_comprehensive_metrics(self):
        """计算综合指标"""
        current_year = self.current_day / 365
        
        # 基础经济指标
        total_firms = int(np.sum(self.firm_grid))
        total_banks = int(np.sum(self.bank_grid))
        
        # GDP计算 (基于企业数量和人口)
        gdp_per_firm = 50000 + current_year * 1000  # 企业生产力增长
        total_gdp = total_firms * gdp_per_firm
        gdp_per_capita = total_gdp / self.population_size if self.population_size > 0 else 0
        
        # 失业率 (基于经济周期)
        business_cycle = np.sin(current_year * 2 * np.pi / 12)
        base_unemployment = 0.05
        cyclical_unemployment = -business_cycle * 0.03  # 经济好时失业率低
        unemployment_rate = max(0.01, min(0.15, base_unemployment + cyclical_unemployment))
        
        # 通胀率 (基于经济增长和货币政策)
        base_inflation = 0.02
        growth_inflation = max(0, (total_gdp / (self.population_size * 30000) - 1) * 0.5)  # 过热通胀
        inflation_rate = base_inflation + growth_inflation + np.random.normal(0, 0.003)
        inflation_rate = max(-0.02, min(0.08, inflation_rate))
        
        # 政策利率 (Taylor规则)
        policy_rate = 0.025 + 1.5 * (inflation_rate - 0.02) + 0.5 * (unemployment_rate - 0.05)
        policy_rate = max(0, min(0.12, policy_rate))
        
        # 财富分布 (基尼系数简化计算)
        # 假设对数正态分布
        gini_coefficient = 0.3 + current_year * 0.001  # 不平等随时间增加
        
        # 地理统计
        urban_population = int(np.sum(self.population_grid[self.terrain_map == 5]))  # 城市人口
        rural_population = self.population_size - urban_population
        
        metrics = {
            'day': self.current_day,
            'year': current_year,
            'population': self.population_size,
            'firms': total_firms,
            'banks': total_banks,
            'gdp': total_gdp,
            'gdp_per_capita': gdp_per_capita,
            'unemployment_rate': unemployment_rate,
            'inflation_rate': inflation_rate,
            'policy_rate': policy_rate,
            'average_age': self.population_stats.average_age,
            'gini_coefficient': gini_coefficient,
            'urban_population': urban_population,
            'rural_population': rural_population,
            'urbanization_rate': urban_population / self.population_size if self.population_size > 0 else 0
        }
        
        return metrics
    
    def update_population_statistics(self):
        """更新人口统计"""
        # 基于年龄分布估算
        working_age_ratio = max(0.5, 0.7 - (self.current_day / 365) * 0.002)  # 老龄化
        employment_rate = 0.95 - (self.current_day / 365) * 0.001  # 就业率略降
        
        self.population_stats.working_age_population = int(self.population_size * working_age_ratio)
        self.population_stats.employed = int(self.population_stats.working_age_population * employment_rate)
        self.population_stats.unemployed = self.population_stats.working_age_population - self.population_stats.employed
        self.population_stats.retired = self.population_size - self.population_stats.working_age_population
    
    def record_metrics_to_db(self, metrics):
        """记录指标到数据库"""
        self.conn.execute('''
            INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics['day'], metrics['year'], metrics['population'],
            metrics['firms'], metrics['banks'], metrics['gdp'],
            metrics['unemployment_rate'], metrics['inflation_rate'],
            metrics['policy_rate'], metrics['average_age'],
            metrics['gini_coefficient'], metrics['urban_population'],
            metrics['rural_population']
        ))
        
        self.conn.commit()
    
    def record_annual_snapshot(self, metrics):
        """记录年度快照"""
        year = int(metrics['year'])
        
        # 记录区域统计
        for y in range(0, self.map_height, 20):
            for x in range(0, self.map_width, 20):
                region_pop = np.sum(self.population_grid[y:y+20, x:x+20])
                region_firms = np.sum(self.firm_grid[y:y+20, x:x+20])
                region_banks = np.sum(self.bank_grid[y:y+20, x:x+20])
                
                if region_pop > 0:
                    # 估算区域失业率
                    region_unemployment = metrics['unemployment_rate'] + np.random.normal(0, 0.01)
                    region_avg_wealth = 30000 * (1 + year * 0.02) + np.random.normal(0, 5000)
                    
                    self.conn.execute('''
                        INSERT INTO regional_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        metrics['day'], x//20, y//20, int(region_pop),
                        int(region_firms), int(region_banks),
                        region_avg_wealth, region_unemployment
                    ))
        
        self.conn.commit()
        
        # 内存清理
        if year % 10 == 0:
            gc.collect()
    
    def record_major_event(self, event_type, description):
        """记录重大事件"""
        self.conn.execute('''
            INSERT INTO major_events VALUES (?, ?, ?, ?, ?, ?)
        ''', (self.current_day, event_type, 0, 0, 1.0, description))
        
        self.conn.commit()
    
    def run_massive_simulation(self):
        """运行大规模模拟"""
        print(f"\n🚀 启动100万人300年大规模模拟!")
        print(f"📊 预计数据量:")
        print(f"   • 每日指标: {self.simulation_years * 12:,} 条记录 (月度)")
        print(f"   • 年度快照: {self.simulation_years:,} 条记录")
        print(f"   • 区域统计: {self.simulation_years * 100:,} 条记录")
        print(f"   • 预计数据库大小: ~{self.simulation_years * 0.1:.0f} MB")
        
        input("\n按回车开始大规模模拟...")
        
        start_time = time.time()
        last_report_time = start_time
        
        try:
            while self.current_day < self.total_days:
                # 执行模拟步骤
                metrics = self.step_massive_simulation()
                
                # 每10年显示详细报告
                if self.current_day % (365 * 10) == 0:
                    self.display_decade_report(metrics)
                
                # 每年显示进度
                elif self.current_day % 365 == 0:
                    elapsed = time.time() - start_time
                    progress = self.current_day / self.total_days
                    eta = elapsed / progress * (1 - progress) if progress > 0 else 0
                    
                    year = int(metrics['year'])
                    print(f"📅 第{year:3d}年 | 进度:{progress:6.1%} | "
                          f"人口:{metrics['population']:,} | "
                          f"企业:{metrics['firms']:,} | "
                          f"银行:{metrics['banks']:,} | "
                          f"用时:{elapsed:6.1f}s | "
                          f"ETA:{eta/60:4.1f}min")
                
                # 性能监控
                current_time = time.time()
                if current_time - last_report_time > 60:  # 每分钟报告性能
                    self.report_performance()
                    last_report_time = current_time
        
        except KeyboardInterrupt:
            print(f"\n👋 模拟被中断在第{self.current_day//365}年")
        
        # 最终报告
        self.generate_final_report()
    
    def display_decade_report(self, metrics):
        """显示十年报告"""
        year = int(metrics['year'])
        
        print(f"\n" + "="*60)
        print(f"📊 第{year}年十年报告")
        print(f"   人口: {metrics['population']:,} (+{metrics['population']-1000000:+,})")
        print(f"   城市化率: {metrics['urbanization_rate']:.1%}")
        print(f"   平均年龄: {metrics['average_age']:.1f}岁")
        print(f"   企业总数: {metrics['firms']:,}")
        print(f"   银行总数: {metrics['banks']:,}")
        print(f"   GDP: ${metrics['gdp']/1e12:.1f}T")
        print(f"   人均GDP: ${metrics['gdp_per_capita']:,.0f}")
        print(f"   失业率: {metrics['unemployment_rate']:.1%}")
        print(f"   通胀率: {metrics['inflation_rate']:.1%}")
        print(f"   政策利率: {metrics['policy_rate']:.1%}")
        print(f"   基尼系数: {metrics['gini_coefficient']:.3f}")
        
        # 地理分布统计
        print(f"   地理分布:")
        print(f"     城市人口: {metrics['urban_population']:,}")
        print(f"     农村人口: {metrics['rural_population']:,}")
        
        input("按回车继续...")
    
    def report_performance(self):
        """报告性能"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        self.performance_stats['memory_usage_mb'] = memory_mb
        
        print(f"⚡ 性能报告: "
              f"速度:{self.performance_stats['steps_per_second']:.1f} days/s | "
              f"内存:{memory_mb:.1f}MB | "
              f"处理时间:{self.performance_stats['processing_time_per_day']*1000:.1f}ms/day")
    
    def generate_final_report(self):
        """生成最终报告"""
        total_time = time.time() - self.start_time if hasattr(self, 'start_time') else 0
        
        print(f"\n" + "="*70)
        print(f"🎉 大规模模拟完成!")
        print(f"⏰ 总用时: {total_time/3600:.1f} 小时")
        print(f"🏃 平均速度: {self.current_day / total_time:.0f} 天/秒")
        
        # 查询最终统计
        cursor = self.conn.execute('''
            SELECT year, population, firms, banks, gdp, unemployment_rate 
            FROM daily_metrics 
            WHERE day % 3650 = 0  -- 每10年
            ORDER BY day
        ''')
        
        decade_data = cursor.fetchall()
        
        print(f"\n📈 300年长期趋势:")
        print(f"{'年份':>6} {'人口':>10} {'企业':>8} {'银行':>6} {'GDP(T)':>8} {'失业率':>8}")
        print("-" * 50)
        
        for row in decade_data[-10:]:  # 显示最后100年
            year, pop, firms, banks, gdp, unemployment = row
            print(f"{year:6.0f} {pop:10,} {firms:8,} {banks:6} {gdp/1e12:8.1f} {unemployment:7.1%}")
        
        # 数据库统计
        total_records = self.conn.execute('SELECT COUNT(*) FROM daily_metrics').fetchone()[0]
        db_size = os.path.getsize(self.db_path) / 1024 / 1024
        
        print(f"\n💾 数据存储统计:")
        print(f"   • 数据库大小: {db_size:.1f} MB")
        print(f"   • 指标记录: {total_records:,} 条")
        print(f"   • 存储效率: {db_size*1024/total_records:.1f} KB/记录")
        
        # 生成数据导出
        self.export_key_metrics()
    
    def export_key_metrics(self):
        """导出关键指标"""
        print(f"\n📤 导出关键指标...")
        
        # 导出年度数据
        cursor = self.conn.execute('''
            SELECT * FROM daily_metrics 
            WHERE day % 365 = 0  -- 年度数据
            ORDER BY day
        ''')
        
        annual_data = cursor.fetchall()
        
        # 转换为JSON格式
        export_data = {
            'metadata': {
                'simulation_type': '100万人300年大规模模拟',
                'population_size': 1000000,
                'simulation_years': 300,
                'map_size': [self.map_width, self.map_height],
                'total_records': len(annual_data),
                'generated_at': time.time()
            },
            'annual_metrics': [
                {
                    'year': int(row[1]),
                    'population': row[2],
                    'firms': row[3], 
                    'banks': row[4],
                    'gdp': row[5],
                    'gdp_per_capita': row[5] / row[2] if row[2] > 0 else 0,
                    'unemployment_rate': row[6],
                    'inflation_rate': row[7],
                    'policy_rate': row[8],
                    'average_age': row[9],
                    'gini_coefficient': row[10],
                    'urbanization_rate': row[11] / row[2] if row[2] > 0 else 0
                }
                for row in annual_data
            ],
            'final_stats': {
                'final_population': annual_data[-1][2] if annual_data else 0,
                'total_firms_created': int(np.sum(self.firm_grid)),
                'total_banks_created': int(np.sum(self.bank_grid)),
                'population_growth_rate': ((annual_data[-1][2] / annual_data[0][2] - 1) * 100) if len(annual_data) >= 2 else 0,
                'gdp_growth_rate': ((annual_data[-1][5] / annual_data[0][5] - 1) * 100) if len(annual_data) >= 2 else 0
            }
        }
        
        # 保存导出数据
        with open('massive_simulation_results.json', 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2)
        
        file_size = os.path.getsize('massive_simulation_results.json') / 1024
        print(f"✅ 关键指标已导出: massive_simulation_results.json ({file_size:.1f} KB)")
        
        # 创建可视化报告
        self.create_visualization_report()
    
    def create_visualization_report(self):
        """创建可视化报告"""
        print("📊 创建可视化报告...")
        
        # 读取年度数据
        cursor = self.conn.execute('''
            SELECT year, population, gdp, unemployment_rate, inflation_rate, 
                   firms, banks, urbanization_rate
            FROM daily_metrics 
            WHERE day % 365 = 0
            ORDER BY year
        ''')
        
        data = cursor.fetchall()
        
        html_report = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>100万人300年模拟报告</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; background: #1a1a1a; color: white; margin: 0; padding: 20px; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ text-align: center; padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; margin-bottom: 30px; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: #2d2d2d; padding: 20px; border-radius: 10px; text-align: center; }}
        .stat-value {{ font-size: 28px; font-weight: bold; color: #4ade80; }}
        .stat-label {{ color: #9ca3af; margin-top: 8px; }}
        .chart-container {{ background: #2d2d2d; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
        .chart {{ height: 400px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ABM大规模模拟报告</h1>
            <p>100万人口 × 300年 × 完整经济演化</p>
            <p>模拟完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{len(data)}</div>
                <div class="stat-label">模拟年数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data[-1][1]:,}</div>
                <div class="stat-label">最终人口</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data[-1][5]:,}</div>
                <div class="stat-label">最终企业数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data[-1][6]}</div>
                <div class="stat-label">最终银行数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${data[-1][2]/1e12:.1f}T</div>
                <div class="stat-label">最终GDP</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{data[-1][7]:.1%}</div>
                <div class="stat-label">最终城市化率</div>
            </div>
        </div>
        
        <div class="chart-container">
            <h3>📈 300年人口演化</h3>
            <div id="populationChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <h3>💰 300年经济增长</h3>
            <div id="gdpChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <h3>🏢 机构发展</h3>
            <div id="institutionsChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <h3>📊 宏观经济指标</h3>
            <div id="macroChart" class="chart"></div>
        </div>
    </div>
    
    <script>
        const data = {json.dumps([list(row) for row in data])};
        
        // 人口图表
        Plotly.newPlot('populationChart', [{{
            x: data.map(d => d[0]),
            y: data.map(d => d[1]),
            type: 'scatter',
            mode: 'lines',
            name: '总人口',
            line: {{color: '#4ade80'}}
        }}], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff'}},
            xaxis: {{title: '年份', color: '#9ca3af'}},
            yaxis: {{title: '人口', color: '#9ca3af'}}
        }});
        
        // GDP图表
        Plotly.newPlot('gdpChart', [{{
            x: data.map(d => d[0]),
            y: data.map(d => d[2] / 1e12),
            type: 'scatter',
            mode: 'lines',
            name: 'GDP (万亿)',
            line: {{color: '#3b82f6'}}
        }}], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff'}},
            xaxis: {{title: '年份', color: '#9ca3af'}},
            yaxis: {{title: 'GDP (万亿美元)', color: '#9ca3af'}}
        }});
        
        // 机构图表
        Plotly.newPlot('institutionsChart', [
            {{
                x: data.map(d => d[0]),
                y: data.map(d => d[5]),
                type: 'scatter',
                mode: 'lines',
                name: '企业数量',
                line: {{color: '#f59e0b'}}
            }},
            {{
                x: data.map(d => d[0]),
                y: data.map(d => d[6]),
                type: 'scatter',
                mode: 'lines',
                name: '银行数量',
                yaxis: 'y2',
                line: {{color: '#ef4444'}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff'}},
            xaxis: {{title: '年份', color: '#9ca3af'}},
            yaxis: {{title: '企业数量', color: '#9ca3af'}},
            yaxis2: {{title: '银行数量', overlaying: 'y', side: 'right', color: '#9ca3af'}}
        }});
        
        // 宏观指标图表
        Plotly.newPlot('macroChart', [
            {{
                x: data.map(d => d[0]),
                y: data.map(d => d[3] * 100),
                type: 'scatter',
                mode: 'lines',
                name: '失业率 (%)',
                line: {{color: '#ef4444'}}
            }},
            {{
                x: data.map(d => d[0]),
                y: data.map(d => d[4] * 100),
                type: 'scatter',
                mode: 'lines',
                name: '通胀率 (%)',
                line: {{color: '#f59e0b'}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff'}},
            xaxis: {{title: '年份', color: '#9ca3af'}},
            yaxis: {{title: '百分比 (%)', color: '#9ca3af'}}
        }});
    </script>
</body>
</html>'''
        
        with open('massive_simulation_report.html', 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        print("✅ 可视化报告已创建: massive_simulation_report.html")

def main():
    """主函数"""
    print("🚀 ABM 大规模模拟系统")
    print("=" * 50)
    print("🎯 模拟规模:")
    print("   • 人口: 1,000,000")
    print("   • 时间: 300年 (109,500天)")
    print("   • 地图: 200×200 (40,000平方公里)")
    print("   • 预计数据: ~100MB")
    
    print(f"\n⚠️ 注意事项:")
    print(f"   • 这是一个大规模模拟，可能需要数小时完成")
    print(f"   • 建议在性能较好的机器上运行")
    print(f"   • 所有指标将完整记录到数据库")
    print(f"   • 可以随时中断并查看已有结果")
    
    confirm = input(f"\n🤔 确认开始100万人300年模拟? (y/n): ").lower().strip()
    
    if confirm in ['y', 'yes', '是']:
        sim = MassiveSimulation(population_size=1000000, simulation_years=300)
        sim.start_time = time.time()
        
        # 初始化
        sim.initialize_massive_population()
        
        # 运行模拟
        sim.run_massive_simulation()
        
        print(f"\n🎊 大规模模拟系统验证完成!")
        print(f"📁 生成文件:")
        print(f"   • massive_simulation.db - 完整历史数据")
        print(f"   • massive_simulation_results.json - 关键指标")
        print(f"   • massive_simulation_report.html - 可视化报告")
        
    else:
        print(f"👋 模拟已取消")
        
        # 创建演示版本
        print(f"\n💡 创建小规模演示版本...")
        demo_sim = MassiveSimulation(population_size=100000, simulation_years=30)  # 10万人30年
        demo_sim.start_time = time.time()
        demo_sim.initialize_massive_population()
        
        print(f"🎮 运行演示模拟...")
        
        for year in range(0, 31, 5):  # 每5年一个检查点
            target_day = year * 365
            
            while demo_sim.current_day < target_day:
                demo_sim.step_massive_simulation()
            
            if year > 0:
                metrics = demo_sim.calculate_comprehensive_metrics()
                print(f"📅 第{year}年: 人口{metrics['population']:,}, 企业{metrics['firms']:,}, GDP${metrics['gdp']/1e9:.1f}B")
        
        demo_sim.generate_final_report()
        print(f"✅ 演示版本完成，可查看 massive_simulation_report.html")

if __name__ == "__main__":
    main()
