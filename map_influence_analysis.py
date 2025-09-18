#!/usr/bin/env python3
"""
地图系统对人物影响的详细分析
展示地形、距离、基础设施如何影响代理行为
"""

import numpy as np
import time
import os

class DetailedMapTile:
    """详细的地图瓦片"""
    
    def __init__(self, x, y, terrain):
        self.x = x
        self.y = y
        self.terrain = terrain
        
        # 地形属性
        self.elevation = self._calculate_elevation()
        self.fertility = self._calculate_fertility()
        self.water_access = self._calculate_water_access()
        
        # 基础设施
        self.road_quality = 0.0
        self.utilities = 0.0
        self.amenities = 0.0
        
        # 经济属性
        self.land_price = self._calculate_base_land_price()
        self.population_density = 0.0
        self.commercial_attractiveness = 0.0
        
        # 环境因素
        self.pollution_level = 0.0
        self.crime_rate = 0.0
        self.noise_level = 0.0
    
    def _calculate_elevation(self):
        """计算海拔"""
        elevation_map = {
            "ocean": 0.0,
            "plain": 0.3,
            "hill": 0.6,
            "mountain": 0.9,
            "forest": 0.4,
            "city": 0.3,
            "river": 0.2
        }
        return elevation_map.get(self.terrain, 0.3) + np.random.normal(0, 0.1)
    
    def _calculate_fertility(self):
        """计算土壤肥力"""
        fertility_map = {
            "ocean": 0.0,
            "plain": 0.8,
            "hill": 0.6,
            "mountain": 0.2,
            "forest": 0.4,
            "city": 0.1,
            "river": 1.0
        }
        return max(0, fertility_map.get(self.terrain, 0.5) + np.random.normal(0, 0.2))
    
    def _calculate_water_access(self):
        """计算水资源获取"""
        if self.terrain == "river":
            return 1.0
        elif self.terrain == "ocean":
            return 0.0  # 海水不能直接使用
        else:
            # 距离河流的远近影响水资源获取
            return np.random.uniform(0.2, 0.8)
    
    def _calculate_base_land_price(self):
        """计算基础土地价格"""
        price_map = {
            "ocean": 0,
            "plain": 100,
            "hill": 80,
            "mountain": 30,
            "forest": 60,
            "city": 500,
            "river": 150
        }
        return price_map.get(self.terrain, 100)
    
    def get_movement_speed_factor(self):
        """获取移动速度因子"""
        # 地形对移动速度的影响
        speed_factors = {
            "ocean": 0.0,      # 无法通过
            "plain": 1.0,      # 标准速度
            "hill": 0.7,       # 较慢
            "mountain": 0.3,   # 很慢
            "forest": 0.6,     # 中等
            "city": 1.2,       # 较快 (基础设施好)
            "river": 0.8       # 需要绕行或过桥
        }
        
        base_factor = speed_factors.get(self.terrain, 0.5)
        
        # 道路质量加成
        road_bonus = 1 + self.road_quality * 0.5
        
        return base_factor * road_bonus
    
    def get_living_attractiveness(self):
        """居住吸引力"""
        # 影响人们选择居住地的因素
        attractiveness = 0.0
        
        # 地形偏好
        terrain_preference = {
            "ocean": 0.0,
            "plain": 0.8,
            "hill": 0.6,
            "mountain": 0.2,
            "forest": 0.5,
            "city": 0.9,
            "river": 0.7
        }.get(self.terrain, 0.5)
        
        attractiveness += terrain_preference * 0.3
        
        # 基础设施
        attractiveness += self.utilities * 0.2
        attractiveness += self.amenities * 0.2
        
        # 环境质量
        attractiveness += (1 - self.pollution_level) * 0.15
        attractiveness += (1 - self.crime_rate) * 0.1
        
        # 价格因素 (负面)
        price_penalty = min(0.3, self.land_price / 1000)
        attractiveness -= price_penalty * 0.05
        
        return max(0, attractiveness)
    
    def get_business_attractiveness(self):
        """商业吸引力"""
        # 影响企业选址的因素
        attractiveness = 0.0
        
        # 人口密度 (客户基础)
        attractiveness += min(1.0, self.population_density / 100) * 0.4
        
        # 交通便利性
        attractiveness += self.road_quality * 0.25
        
        # 基础设施
        attractiveness += self.utilities * 0.2
        
        # 地形适宜性
        terrain_suitability = {
            "ocean": 0.0,
            "plain": 0.8,
            "hill": 0.6,
            "mountain": 0.2,
            "forest": 0.4,
            "city": 1.0,
            "river": 0.3
        }.get(self.terrain, 0.5)
        
        attractiveness += terrain_suitability * 0.15
        
        return max(0, attractiveness)

class MapInfluenceAnalyzer:
    """地图影响分析器"""
    
    def __init__(self):
        self.width = 80
        self.height = 20
        self.tiles = {}
        self.cities = [(15, 8), (35, 10), (55, 7), (25, 15), (45, 5)]
        
        self.generate_detailed_map()
    
    def generate_detailed_map(self):
        """生成详细地图"""
        print("🗺️ 生成详细地图系统...")
        
        # 1. 生成基础地形
        for y in range(self.height):
            for x in range(self.width):
                terrain = self._determine_terrain(x, y)
                self.tiles[(x, y)] = DetailedMapTile(x, y, terrain)
        
        # 2. 发展城市区域
        self._develop_cities()
        
        # 3. 建设道路网络
        self._build_road_network()
        
        # 4. 计算衍生属性
        self._calculate_derived_properties()
        
        print("✅ 详细地图生成完成")
    
    def _determine_terrain(self, x, y):
        """确定地形类型"""
        if x < 3 or x > 76 or y < 1 or y > 18:
            return "ocean"
        elif x > 65 and y > 15:
            return "mountain"
        elif 25 <= x <= 35 and 8 <= y <= 12:
            return "river"
        elif (x, y) in self.cities:
            return "city"
        else:
            # 基于位置的地形生成
            if x < 20:  # 西部农业区
                return np.random.choice(["plain", "forest"], p=[0.8, 0.2])
            elif x > 60:  # 东部山区
                return np.random.choice(["hill", "mountain"], p=[0.7, 0.3])
            else:  # 中部混合区
                return np.random.choice(["plain", "hill", "forest"], p=[0.6, 0.3, 0.1])
    
    def _develop_cities(self):
        """发展城市"""
        for city_x, city_y in self.cities:
            # 城市中心
            if (city_x, city_y) in self.tiles:
                center_tile = self.tiles[(city_x, city_y)]
                center_tile.utilities = 0.9
                center_tile.amenities = 0.8
                center_tile.road_quality = 0.9
                center_tile.population_density = 200
                center_tile.land_price = 800
            
            # 城市周边发展
            for radius in range(1, 4):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        x, y = city_x + dx, city_y + dy
                        
                        if (x, y) in self.tiles:
                            tile = self.tiles[(x, y)]
                            distance = max(abs(dx), abs(dy))
                            
                            # 距离衰减效应
                            decay_factor = 1.0 / (1 + distance)
                            
                            tile.utilities = max(tile.utilities, 0.8 * decay_factor)
                            tile.amenities = max(tile.amenities, 0.7 * decay_factor)
                            tile.road_quality = max(tile.road_quality, 0.8 * decay_factor)
                            tile.population_density += 100 * decay_factor
                            tile.land_price *= (1 + decay_factor)
    
    def _build_road_network(self):
        """建设道路网络"""
        # 连接所有城市
        for i, city1 in enumerate(self.cities):
            for city2 in self.cities[i+1:]:
                self._build_road_between(city1, city2)
    
    def _build_road_between(self, start, end):
        """建设道路"""
        x1, y1 = start
        x2, y2 = end
        
        # 简单直线路径
        steps = max(abs(x2 - x1), abs(y2 - y1))
        
        for i in range(steps + 1):
            if steps > 0:
                t = i / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                
                if (x, y) in self.tiles:
                    self.tiles[(x, y)].road_quality = max(self.tiles[(x, y)].road_quality, 0.7)
    
    def _calculate_derived_properties(self):
        """计算衍生属性"""
        for tile in self.tiles.values():
            # 商业吸引力
            tile.commercial_attractiveness = tile.get_business_attractiveness()
            
            # 污染水平 (城市和工业区较高)
            if tile.terrain == "city":
                tile.pollution_level = 0.3 + tile.population_density / 1000
            elif tile.population_density > 50:
                tile.pollution_level = tile.population_density / 500
            else:
                tile.pollution_level = 0.1
    
    def analyze_movement_influences(self, person_x, person_y, target_x, target_y):
        """分析移动影响因素"""
        print(f"\n🔍 分析从({person_x:.1f},{person_y:.1f})到({target_x:.1f},{target_y:.1f})的移动:")
        
        # 起点分析
        start_tile = self.tiles.get((int(person_x), int(person_y)))
        end_tile = self.tiles.get((int(target_x), int(target_y)))
        
        if start_tile:
            print(f"📍 起点 ({int(person_x)},{int(person_y)}):")
            print(f"   地形: {start_tile.terrain}")
            print(f"   移动速度因子: {start_tile.get_movement_speed_factor():.2f}")
            print(f"   道路质量: {start_tile.road_quality:.2f}")
            print(f"   基础设施: {start_tile.utilities:.2f}")
        
        if end_tile:
            print(f"📍 终点 ({int(target_x)},{int(target_y)}):")
            print(f"   地形: {end_tile.terrain}")
            print(f"   居住吸引力: {end_tile.get_living_attractiveness():.2f}")
            print(f"   商业吸引力: {end_tile.get_business_attractiveness():.2f}")
        
        # 路径分析
        distance = np.sqrt((target_x - person_x)**2 + (target_y - person_y)**2)
        travel_time = self._calculate_travel_time(person_x, person_y, target_x, target_y)
        
        print(f"🛣️ 路径分析:")
        print(f"   直线距离: {distance:.1f} 格 ({distance * 2:.1f} 公里)")
        print(f"   预计旅行时间: {travel_time:.1f} 时间单位")
        print(f"   地形影响: {self._analyze_terrain_impact(person_x, person_y, target_x, target_y)}")
        
        return travel_time
    
    def _calculate_travel_time(self, x1, y1, x2, y2):
        """计算旅行时间"""
        # 简化的路径计算
        steps = max(abs(x2 - x1), abs(y2 - y1))
        total_time = 0
        
        for i in range(int(steps) + 1):
            if steps > 0:
                t = i / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                
                tile = self.tiles.get((x, y))
                if tile:
                    speed_factor = tile.get_movement_speed_factor()
                    total_time += 1.0 / max(0.1, speed_factor)
                else:
                    total_time += 2.0  # 未知地形惩罚
        
        return total_time
    
    def _analyze_terrain_impact(self, x1, y1, x2, y2):
        """分析地形影响"""
        terrains_crossed = set()
        
        steps = max(abs(x2 - x1), abs(y2 - y1))
        
        for i in range(int(steps) + 1):
            if steps > 0:
                t = i / steps
                x = int(x1 + (x2 - x1) * t)
                y = int(y1 + (y2 - y1) * t)
                
                tile = self.tiles.get((x, y))
                if tile:
                    terrains_crossed.add(tile.terrain)
        
        return f"穿越地形: {', '.join(terrains_crossed)}"
    
    def analyze_location_choice(self, person_wealth, person_age, purpose):
        """分析位置选择"""
        print(f"\n🎯 分析{purpose}位置选择 (财富:{person_wealth:.0f}, 年龄:{person_age}):")
        
        suitable_locations = []
        
        for (x, y), tile in self.tiles.items():
            score = 0
            factors = {}
            
            if purpose == "居住":
                # 居住位置选择因素
                factors['地形适宜性'] = tile.get_living_attractiveness() * 0.3
                factors['基础设施'] = tile.utilities * 0.25
                factors['环境质量'] = (1 - tile.pollution_level) * 0.2
                factors['价格因素'] = max(0, (1000 - tile.land_price) / 1000) * 0.15
                factors['便利性'] = tile.amenities * 0.1
                
                # 年龄影响偏好
                if person_age > 50:
                    factors['环境质量'] *= 1.5  # 老年人更重视环境
                    factors['便利性'] *= 1.3    # 更重视便利性
                
                # 财富影响
                if person_wealth > 50000:
                    factors['价格因素'] *= 0.5  # 富人不太在意价格
                    factors['便利性'] *= 1.2    # 更重视便利性
            
            elif purpose == "工作":
                # 工作地点选择因素
                factors['商业吸引力'] = tile.get_business_attractiveness() * 0.4
                factors['交通便利'] = tile.road_quality * 0.3
                factors['人口密度'] = min(1.0, tile.population_density / 100) * 0.2
                factors['成本考虑'] = max(0, (500 - tile.land_price) / 500) * 0.1
            
            elif purpose == "创业":
                # 创业位置选择因素
                factors['市场潜力'] = min(1.0, tile.population_density / 50) * 0.35
                factors['交通便利'] = tile.road_quality * 0.25
                factors['成本控制'] = max(0, (300 - tile.land_price) / 300) * 0.2
                factors['基础设施'] = tile.utilities * 0.15
                factors['竞争程度'] = max(0, 1 - tile.commercial_attractiveness) * 0.05
            
            total_score = sum(factors.values())
            
            if total_score > 0.5:  # 只考虑高分位置
                suitable_locations.append((x, y, total_score, factors))
        
        # 显示最佳位置
        suitable_locations.sort(key=lambda x: x[2], reverse=True)
        
        print(f"   🏆 最佳位置 TOP 3:")
        for i, (x, y, score, factors) in enumerate(suitable_locations[:3]):
            print(f"   {i+1}. ({x},{y}) 综合评分: {score:.2f}")
            for factor_name, factor_value in factors.items():
                if factor_value > 0.1:
                    print(f"      {factor_name}: {factor_value:.2f}")
        
        return suitable_locations[:5] if suitable_locations else []
    
    def simulate_daily_movement_pattern(self, person_x, person_y, person_age, employed):
        """模拟日常移动模式"""
        print(f"\n🚶 模拟个人日常移动模式:")
        print(f"   起始位置: ({person_x:.1f},{person_y:.1f})")
        print(f"   年龄: {person_age}, 就业状态: {'就业' if employed else '失业'}")
        
        daily_pattern = []
        
        for hour in range(24):
            target_x, target_y, activity = self._determine_hourly_target(
                person_x, person_y, hour, employed
            )
            
            travel_time = self._calculate_travel_time(person_x, person_y, target_x, target_y)
            
            daily_pattern.append({
                'hour': hour,
                'activity': activity,
                'target': (target_x, target_y),
                'travel_time': travel_time
            })
        
        # 显示关键时段
        key_hours = [8, 12, 18, 22]
        print(f"   📅 关键时段移动:")
        
        for hour in key_hours:
            pattern = daily_pattern[hour]
            print(f"   {hour:2d}:00 - {pattern['activity']:12s} → ({pattern['target'][0]:4.1f},{pattern['target'][1]:4.1f}) "
                  f"(旅行时间: {pattern['travel_time']:4.1f})")
        
        return daily_pattern
    
    def _determine_hourly_target(self, person_x, person_y, hour, employed):
        """确定每小时的目标位置"""
        if employed and 8 <= hour <= 17:
            # 工作时间 - 去商业区
            target_x = 55 + np.random.normal(0, 3)
            target_y = 10 + np.random.normal(0, 2)
            activity = "工作"
        
        elif 18 <= hour <= 22:
            # 下班时间 - 商业活动
            if np.random.random() < 0.4:
                # 去最近的城市
                nearest_city = min(self.cities, 
                                 key=lambda c: abs(c[0] - person_x) + abs(c[1] - person_y))
                target_x = nearest_city[0] + np.random.normal(0, 2)
                target_y = nearest_city[1] + np.random.normal(0, 1)
                activity = "购物/社交"
            else:
                target_x = person_x + np.random.normal(0, 1)
                target_y = person_y + np.random.normal(0, 1)
                activity = "在家附近"
        
        else:
            # 其他时间 - 在家
            target_x = person_x + np.random.normal(0, 0.5)
            target_y = person_y + np.random.normal(0, 0.5)
            activity = "在家"
        
        # 边界约束
        target_x = np.clip(target_x, 0, 79)
        target_y = np.clip(target_y, 0, 19)
        
        return target_x, target_y, activity
    
    def analyze_business_location_factors(self):
        """分析企业选址因素"""
        print(f"\n🏢 企业选址影响因素分析:")
        
        # 分析不同区域的商业潜力
        regions = {
            "西部农业区": [(x, y) for x in range(5, 25) for y in range(3, 17)],
            "中部城市区": [(x, y) for x in range(25, 55) for y in range(5, 15)],
            "东部山区": [(x, y) for x in range(55, 75) for y in range(3, 17)]
        }
        
        for region_name, positions in regions.items():
            region_tiles = [self.tiles.get(pos) for pos in positions if pos in self.tiles]
            region_tiles = [t for t in region_tiles if t is not None]
            
            if region_tiles:
                avg_attractiveness = np.mean([t.get_business_attractiveness() for t in region_tiles])
                avg_population = np.mean([t.population_density for t in region_tiles])
                avg_land_price = np.mean([t.land_price for t in region_tiles])
                avg_road_quality = np.mean([t.road_quality for t in region_tiles])
                
                print(f"   📊 {region_name}:")
                print(f"      商业吸引力: {avg_attractiveness:.2f}")
                print(f"      人口密度: {avg_population:.0f}")
                print(f"      土地价格: {avg_land_price:.0f}")
                print(f"      道路质量: {avg_road_quality:.2f}")
                
                # 推荐企业类型
                if avg_attractiveness > 0.7:
                    recommended = "服务业、零售业"
                elif avg_population < 20:
                    recommended = "农业、采矿业"
                else:
                    recommended = "制造业"
                
                print(f"      推荐企业: {recommended}")
    
    def demonstrate_map_influence(self):
        """演示地图影响"""
        print(f"\n🎭 地图影响演示:")
        
        # 创建示例人物
        test_persons = [
            {"name": "年轻上班族", "x": 20, "y": 8, "age": 28, "wealth": 30000, "employed": True},
            {"name": "中年企业家", "x": 40, "y": 10, "age": 45, "wealth": 200000, "employed": False},
            {"name": "退休老人", "x": 15, "y": 8, "age": 68, "wealth": 80000, "employed": False}
        ]
        
        for person in test_persons:
            print(f"\n👤 {person['name']} (年龄{person['age']}, 财富{person['wealth']:,}):")
            
            # 分析居住选择
            suitable_homes = self.analyze_location_choice(person['wealth'], person['age'], "居住")
            
            # 分析移动模式
            if person['employed']:
                self.simulate_daily_movement_pattern(person['x'], person['y'], person['age'], True)
            
            # 分析创业潜力
            if person['wealth'] > 50000 and 25 <= person['age'] <= 55:
                self.analyze_location_choice(person['wealth'], person['age'], "创业")
    
    def visualize_influence_map(self):
        """可视化影响地图"""
        print(f"\n🗺️ 地图影响可视化:")
        
        # 显示不同属性的地图
        maps_to_show = [
            ("移动速度", lambda t: t.get_movement_speed_factor()),
            ("居住吸引力", lambda t: t.get_living_attractiveness()),
            ("商业吸引力", lambda t: t.get_business_attractiveness()),
            ("土地价格", lambda t: t.land_price / 1000)
        ]
        
        for map_name, value_func in maps_to_show:
            print(f"\n📊 {map_name}地图:")
            
            # 创建可视化网格
            for y in range(0, 20, 2):  # 每2行显示一次
                line = ""
                for x in range(0, 80, 4):  # 每4列显示一次
                    tile = self.tiles.get((x, y))
                    if tile:
                        value = value_func(tile)
                        
                        # 转换为符号
                        if value > 0.8:
                            symbol = "█"
                        elif value > 0.6:
                            symbol = "▓"
                        elif value > 0.4:
                            symbol = "▒"
                        elif value > 0.2:
                            symbol = "░"
                        else:
                            symbol = "."
                        
                        line += symbol
                    else:
                        line += " "
                
                print(f"   {line}")
            
            print(f"   图例: █ 很高 ▓ 高 ▒ 中 ░ 低 . 很低")

def run_influence_analysis():
    """运行影响分析"""
    print("🔍 ABM地图系统影响分析")
    print("=" * 50)
    
    analyzer = MapInfluenceAnalyzer()
    
    print("\n📋 分析内容:")
    print("   1. 地形对移动速度的影响")
    print("   2. 位置选择的影响因素")
    print("   3. 日常移动模式分析")
    print("   4. 企业选址因素分析")
    print("   5. 地图影响可视化")
    
    input("\n按回车开始分析...")
    
    # 1. 移动影响分析
    print(f"\n" + "="*50)
    print(f"1️⃣ 移动影响分析")
    
    # 示例移动路径
    test_routes = [
        (10, 5, 60, 10, "农村到城市通勤"),
        (35, 10, 55, 7, "城市间移动"),
        (20, 8, 25, 12, "穿越河流"),
        (70, 16, 40, 8, "山区到平原")
    ]
    
    for x1, y1, x2, y2, description in test_routes:
        print(f"\n🛣️ {description}:")
        analyzer.analyze_movement_influences(x1, y1, x2, y2)
    
    input("\n按回车继续...")
    
    # 2. 位置选择分析
    print(f"\n" + "="*50)
    print(f"2️⃣ 位置选择影响因素")
    analyzer.demonstrate_map_influence()
    
    input("\n按回车继续...")
    
    # 3. 企业选址分析
    print(f"\n" + "="*50)
    print(f"3️⃣ 企业选址分析")
    analyzer.analyze_business_location_factors()
    
    input("\n按回车继续...")
    
    # 4. 影响地图可视化
    print(f"\n" + "="*50)
    print(f"4️⃣ 地图影响可视化")
    analyzer.visualize_influence_map()
    
    print(f"\n🎯 总结 - 地图系统如何影响人物:")
    print(f"   ✅ 移动速度: 地形和道路质量直接影响移动效率")
    print(f"   ✅ 居住选择: 环境、价格、便利性影响居住地选择")
    print(f"   ✅ 工作通勤: 距离和交通条件影响就业选择")
    print(f"   ✅ 创业决策: 人口密度、成本、基础设施影响企业选址")
    print(f"   ✅ 日常活动: 不同时段有不同的目标位置偏好")
    print(f"   ✅ 生命周期: 年龄和财富影响位置偏好权重")

if __name__ == "__main__":
    run_influence_analysis()
