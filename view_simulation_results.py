#!/usr/bin/env python3
"""
查看300年大规模模拟结果
展示完整的指标数据和趋势分析
"""

import json
import sqlite3
import numpy as np
import matplotlib.pyplot as plt
import os

def load_simulation_results():
    """加载模拟结果"""
    print("📊 加载300年模拟结果...")
    
    # 1. 加载JSON结果
    try:
        with open('massive_simulation_results.json', 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        print(f"✅ JSON数据加载成功: {len(json_data['annual_metrics'])} 年数据")
    except FileNotFoundError:
        print("❌ 未找到 massive_simulation_results.json")
        return None, None
    
    # 2. 加载数据库
    db_data = None
    try:
        if os.path.exists('massive_simulation.db'):
            conn = sqlite3.connect('massive_simulation.db')
            cursor = conn.execute('SELECT * FROM daily_metrics ORDER BY day')
            db_data = cursor.fetchall()
            conn.close()
            print(f"✅ 数据库加载成功: {len(db_data)} 条记录")
        else:
            print("⚠️ 数据库文件不存在")
    except Exception as e:
        print(f"⚠️ 数据库加载失败: {e}")
    
    return json_data, db_data

def analyze_300_year_trends(json_data):
    """分析300年趋势"""
    print(f"\n📈 300年长期趋势分析:")
    print("=" * 60)
    
    annual_data = json_data['annual_metrics']
    
    # 基础统计
    initial = annual_data[0]
    final = annual_data[-1]
    
    print(f"📊 总体变化 (第1年 → 第300年):")
    print(f"   人口: {initial['population']:,} → {final['population']:,} "
          f"({((final['population']/initial['population']-1)*100):+.1f}%)")
    
    print(f"   企业: {initial['firms']:,} → {final['firms']:,} "
          f"({((final['firms']/initial['firms']-1)*100):+.1f}%)")
    
    print(f"   银行: {initial['banks']} → {final['banks']}")
    
    print(f"   GDP: ${initial['gdp']/1e12:.2f}T → ${final['gdp']/1e12:.2f}T "
          f"({((final['gdp']/initial['gdp']-1)*100):+.1f}%)")
    
    print(f"   人均GDP: ${initial['gdp_per_capita']:,.0f} → ${final['gdp_per_capita']:,.0f} "
          f"({((final['gdp_per_capita']/initial['gdp_per_capita']-1)*100):+.1f}%)")
    
    print(f"   城市化率: {initial['urbanization_rate']:.1%} → {final['urbanization_rate']:.1%}")
    
    print(f"   平均年龄: {initial['average_age']:.1f}岁 → {final['average_age']:.1f}岁")
    
    print(f"   基尼系数: {initial['gini_coefficient']:.3f} → {final['gini_coefficient']:.3f}")
    
    # 增长率分析
    years = len(annual_data)
    population_cagr = ((final['population'] / initial['population']) ** (1/years) - 1) * 100
    gdp_cagr = ((final['gdp'] / initial['gdp']) ** (1/years) - 1) * 100
    
    print(f"\n📈 复合年增长率 (CAGR):")
    print(f"   人口增长率: {population_cagr:.2f}% /年")
    print(f"   经济增长率: {gdp_cagr:.2f}% /年")
    print(f"   人均GDP增长率: {gdp_cagr - population_cagr:.2f}% /年")
    
    # 周期性分析
    unemployment_data = [d['unemployment_rate'] for d in annual_data]
    inflation_data = [d['inflation_rate'] for d in annual_data]
    
    unemployment_volatility = np.std(unemployment_data)
    inflation_volatility = np.std(inflation_data)
    
    print(f"\n🌊 经济周期分析:")
    print(f"   失业率波动性: {unemployment_volatility:.3f}")
    print(f"   通胀率波动性: {inflation_volatility:.3f}")
    print(f"   平均失业率: {np.mean(unemployment_data):.1%}")
    print(f"   平均通胀率: {np.mean(inflation_data):.1%}")
    
    # 里程碑分析
    print(f"\n🏆 重要里程碑:")
    
    # 人口里程碑
    population_milestones = [2000000, 3000000, 4000000, 5000000, 6000000]
    for milestone in population_milestones:
        milestone_year = next((d['year'] for d in annual_data if d['population'] >= milestone), None)
        if milestone_year:
            print(f"   人口达到 {milestone/1e6:.0f}百万: 第{milestone_year:.0f}年")
    
    # 企业里程碑
    max_firms = max(d['firms'] for d in annual_data)
    max_firms_year = next(d['year'] for d in annual_data if d['firms'] == max_firms)
    print(f"   企业数量峰值: {max_firms:,} (第{max_firms_year:.0f}年)")
    
    return annual_data

def create_comprehensive_visualization(annual_data):
    """创建综合可视化"""
    print(f"\n🎨 创建综合可视化报告...")
    
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>100万人300年模拟 - 完整结果</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{ 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #0f172a; 
            color: white; 
            margin: 0; 
            padding: 20px; 
        }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        .header {{ 
            text-align: center; 
            padding: 30px; 
            background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%); 
            border-radius: 15px; 
            margin-bottom: 30px; 
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        }}
        .stats-grid {{ 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            margin-bottom: 30px; 
        }}
        .stat-card {{ 
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
            padding: 20px; 
            border-radius: 12px; 
            text-align: center; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border: 1px solid #475569;
        }}
        .stat-value {{ 
            font-size: 32px; 
            font-weight: bold; 
            background: linear-gradient(135deg, #60a5fa 0%, #34d399 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .stat-label {{ 
            color: #94a3b8; 
            font-size: 14px;
            font-weight: 500;
        }}
        .chart-container {{ 
            background: #1e293b; 
            padding: 25px; 
            border-radius: 12px; 
            margin-bottom: 25px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            border: 1px solid #334155;
        }}
        .chart-title {{ 
            color: #f1f5f9; 
            font-size: 20px; 
            font-weight: 600; 
            margin-bottom: 20px; 
            text-align: center;
        }}
        .chart {{ height: 450px; }}
        .summary {{ 
            background: #0f172a; 
            padding: 25px; 
            border-radius: 12px; 
            border: 2px solid #1e40af;
            margin-top: 30px;
        }}
        .highlight {{ 
            background: linear-gradient(135deg, #1e40af 0%, #7c3aed 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ABM大规模模拟结果</h1>
            <h2>100万人口 × 300年 × 完整经济演化</h2>
            <p>模拟完成时间: {time.strftime('%Y年%m月%d日 %H:%M:%S')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{annual_data[-1]['population']:,}</div>
                <div class="stat-label">最终人口</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{annual_data[-1]['firms']:,}</div>
                <div class="stat-label">最终企业数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{annual_data[-1]['banks']}</div>
                <div class="stat-label">最终银行数</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${annual_data[-1]['gdp']/1e12:.1f}T</div>
                <div class="stat-label">最终GDP</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${annual_data[-1]['gdp_per_capita']:,.0f}</div>
                <div class="stat-label">人均GDP</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{annual_data[-1]['urbanization_rate']:.1%}</div>
                <div class="stat-label">城市化率</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{annual_data[-1]['average_age']:.1f}岁</div>
                <div class="stat-label">平均年龄</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{annual_data[-1]['gini_coefficient']:.3f}</div>
                <div class="stat-label">基尼系数</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📈 300年人口演化</div>
            <div id="populationChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">💰 300年经济增长</div>
            <div id="gdpChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🏢 机构发展历程</div>
            <div id="institutionsChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📊 宏观经济指标</div>
            <div id="macroChart" class="chart"></div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">🏙️ 城市化进程</div>
            <div id="urbanizationChart" class="chart"></div>
        </div>
        
        <div class="summary">
            <h3 class="highlight">🎯 300年模拟核心发现</h3>
            <ul style="line-height: 1.8; font-size: 16px;">
                <li><strong>人口增长</strong>: 从100万增长到{annual_data[-1]['population']/1e6:.1f}百万 ({((annual_data[-1]['population']/annual_data[0]['population']-1)*100):+.1f}%)</li>
                <li><strong>经济发展</strong>: GDP增长{((annual_data[-1]['gdp']/annual_data[0]['gdp']-1)*100):+.0f}%，人均GDP达到${annual_data[-1]['gdp_per_capita']:,.0f}</li>
                <li><strong>机构演化</strong>: 企业从{annual_data[0]['firms']:,}个发展到{annual_data[-1]['firms']:,}个</li>
                <li><strong>城市化</strong>: 城市化率从{annual_data[0]['urbanization_rate']:.1%}提升到{annual_data[-1]['urbanization_rate']:.1%}</li>
                <li><strong>人口老龄化</strong>: 平均年龄从{annual_data[0]['average_age']:.1f}岁上升到{annual_data[-1]['average_age']:.1f}岁</li>
                <li><strong>收入不平等</strong>: 基尼系数从{annual_data[0]['gini_coefficient']:.3f}上升到{annual_data[-1]['gini_coefficient']:.3f}</li>
            </ul>
        </div>
    </div>

    <script>
        const data = {json.dumps(annual_data)};
        
        // 人口图表
        Plotly.newPlot('populationChart', [
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.population / 1e6),
                type: 'scatter',
                mode: 'lines',
                name: '总人口 (百万)',
                line: {{color: '#10b981', width: 3}}
            }},
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.urban_population / 1e6),
                type: 'scatter',
                mode: 'lines',
                name: '城市人口 (百万)',
                line: {{color: '#f59e0b', width: 2}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff', size: 12}},
            xaxis: {{title: '年份', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis: {{title: '人口 (百万)', color: '#94a3b8', gridcolor: '#334155'}},
            legend: {{bgcolor: 'rgba(30,41,59,0.8)', bordercolor: '#475569'}}
        }});
        
        // GDP图表
        Plotly.newPlot('gdpChart', [
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.gdp / 1e12),
                type: 'scatter',
                mode: 'lines',
                name: 'GDP (万亿)',
                line: {{color: '#3b82f6', width: 3}}
            }},
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.gdp_per_capita / 1000),
                type: 'scatter',
                mode: 'lines',
                name: '人均GDP (千美元)',
                yaxis: 'y2',
                line: {{color: '#8b5cf6', width: 2}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff', size: 12}},
            xaxis: {{title: '年份', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis: {{title: 'GDP (万亿美元)', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis2: {{title: '人均GDP (千美元)', overlaying: 'y', side: 'right', color: '#94a3b8'}},
            legend: {{bgcolor: 'rgba(30,41,59,0.8)', bordercolor: '#475569'}}
        }});
        
        // 机构图表
        Plotly.newPlot('institutionsChart', [
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.firms),
                type: 'scatter',
                mode: 'lines',
                name: '企业数量',
                line: {{color: '#06b6d4', width: 3}}
            }},
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.banks),
                type: 'scatter',
                mode: 'lines',
                name: '银行数量',
                yaxis: 'y2',
                line: {{color: '#ef4444', width: 3}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff', size: 12}},
            xaxis: {{title: '年份', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis: {{title: '企业数量', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis2: {{title: '银行数量', overlaying: 'y', side: 'right', color: '#94a3b8'}},
            legend: {{bgcolor: 'rgba(30,41,59,0.8)', bordercolor: '#475569'}}
        }});
        
        // 宏观指标图表
        Plotly.newPlot('macroChart', [
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.unemployment_rate * 100),
                type: 'scatter',
                mode: 'lines',
                name: '失业率 (%)',
                line: {{color: '#ef4444', width: 2}}
            }},
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.inflation_rate * 100),
                type: 'scatter',
                mode: 'lines',
                name: '通胀率 (%)',
                line: {{color: '#f59e0b', width: 2}}
            }},
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.policy_rate * 100),
                type: 'scatter',
                mode: 'lines',
                name: '政策利率 (%)',
                line: {{color: '#8b5cf6', width: 2}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff', size: 12}},
            xaxis: {{title: '年份', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis: {{title: '百分比 (%)', color: '#94a3b8', gridcolor: '#334155'}},
            legend: {{bgcolor: 'rgba(30,41,59,0.8)', bordercolor: '#475569'}}
        }});
        
        // 城市化图表
        Plotly.newPlot('urbanizationChart', [
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.urbanization_rate * 100),
                type: 'scatter',
                mode: 'lines',
                fill: 'tonexty',
                name: '城市化率 (%)',
                line: {{color: '#f59e0b', width: 3}}
            }},
            {{
                x: data.map(d => d.year),
                y: data.map(d => d.average_age),
                type: 'scatter',
                mode: 'lines',
                name: '平均年龄 (岁)',
                yaxis: 'y2',
                line: {{color: '#8b5cf6', width: 2}}
            }}
        ], {{
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {{color: '#ffffff', size: 12}},
            xaxis: {{title: '年份', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis: {{title: '城市化率 (%)', color: '#94a3b8', gridcolor: '#334155'}},
            yaxis2: {{title: '平均年龄 (岁)', overlaying: 'y', side: 'right', color: '#94a3b8'}},
            legend: {{bgcolor: 'rgba(30,41,59,0.8)', bordercolor: '#475569'}}
        }});
    </script>
</body>
</html>'''
    
    with open('simulation_300_years_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ 综合可视化报告已创建: simulation_300_years_report.html")
    return 'simulation_300_years_report.html'

def main():
    """主函数"""
    print("📊 ABM 300年模拟结果查看器")
    print("=" * 50)
    
    # 加载数据
    json_data, db_data = load_simulation_results()
    
    if json_data is None:
        print("❌ 无法加载模拟结果")
        return
    
    # 分析趋势
    annual_data = analyze_300_year_trends(json_data)
    
    # 创建可视化
    report_file = create_comprehensive_visualization(annual_data)
    
    print(f"\n📁 可视化文件位置:")
    print(f"   🎬 动画播放器: working_animation.html")
    print(f"   📊 300年报告: {report_file}")
    print(f"   💾 原始数据: massive_simulation_results.json")
    print(f"   🗄️ 数据库: massive_simulation.db")
    
    print(f"\n🎮 查看方式:")
    print(f"   1. 在浏览器中打开 {report_file}")
    print(f"   2. 或运行: start {report_file}")
    
    # 自动打开报告
    choice = input(f"\n🤔 是否自动打开可视化报告? (y/n): ").lower().strip()
    if choice in ['y', 'yes', '是', '']:
        os.system(f'start {report_file}')
        print(f"✅ 已在浏览器中打开300年模拟报告")

if __name__ == "__main__":
    import time
    main()
