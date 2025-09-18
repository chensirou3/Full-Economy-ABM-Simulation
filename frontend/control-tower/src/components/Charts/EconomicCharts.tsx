/**
 * 经济图表组件
 */

import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { TrendingUp, BarChart3 } from 'lucide-react'
import { useMetricsHistory, useDashboardStore } from '../../store/dashboardStore'

export const EconomicCharts: React.FC = () => {
  const metricsHistory = useMetricsHistory()
  const { chartTimeRange, selectedMetrics, setChartTimeRange, toggleMetric } = useDashboardStore()

  // 准备图表数据
  const chartData = React.useMemo(() => {
    if (!metricsHistory || metricsHistory.length === 0) return []

    // 根据时间范围过滤数据
    const now = Date.now()
    const ranges = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
    }
    
    const cutoff = now - ranges[chartTimeRange]
    const filteredData = metricsHistory.filter(m => m.timestamp * 1000 > cutoff)

    return filteredData.map(m => ({
      time: new Date(m.timestamp * 1000).toLocaleTimeString('zh-CN', { 
        hour12: false,
        hour: '2-digit',
        minute: '2-digit'
      }),
      timestamp: m.timestamp,
      GDP: m.kpis.gdp / 1000000, // 转换为百万
      失业率: m.kpis.unemployment * 100,
      通胀率: m.kpis.inflation * 100,
      政策利率: m.kpis.policy_rate * 100,
      信贷增长: (m.kpis.credit_growth || 0) * 100,
      代理数: m.kpis.total_agents,
    }))
  }, [metricsHistory, chartTimeRange])

  const metrics = [
    { key: 'GDP', label: 'GDP (百万)', color: '#10b981', unit: 'M' },
    { key: '失业率', label: '失业率', color: '#ef4444', unit: '%' },
    { key: '通胀率', label: '通胀率', color: '#f59e0b', unit: '%' },
    { key: '政策利率', label: '政策利率', color: '#3b82f6', unit: '%' },
    { key: '信贷增长', label: '信贷增长', color: '#8b5cf6', unit: '%' },
    { key: '代理数', label: '代理数量', color: '#06b6d4', unit: '' },
  ]

  if (chartData.length === 0) {
    return (
      <div className="dashboard-card">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title flex items-center gap-2">
            <TrendingUp size={20} />
            经济指标图表
          </h3>
        </div>
        <div className="dashboard-card-content">
          <div className="text-center py-12 text-slate-400">
            <BarChart3 size={48} className="mx-auto mb-4 opacity-50" />
            <p>暂无历史数据</p>
            <p className="text-sm mt-1">等待模拟器运行以收集数据...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title flex items-center gap-2">
          <TrendingUp size={20} />
          经济指标图表
        </h3>
        
        {/* 时间范围选择 */}
        <div className="flex items-center gap-2">
          {(['1h', '6h', '24h', '7d'] as const).map(range => (
            <button
              key={range}
              onClick={() => setChartTimeRange(range)}
              className={`px-2 py-1 rounded text-xs transition-colors ${
                chartTimeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>
      
      <div className="dashboard-card-content">
        {/* 指标选择 */}
        <div className="mb-4">
          <div className="flex flex-wrap gap-2">
            {metrics.map(metric => (
              <button
                key={metric.key}
                onClick={() => toggleMetric(metric.key)}
                className={`px-3 py-1 rounded text-sm transition-colors flex items-center gap-2 ${
                  selectedMetrics.includes(metric.key)
                    ? 'bg-slate-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                <div 
                  className="w-3 h-3 rounded"
                  style={{ backgroundColor: metric.color }}
                ></div>
                {metric.label}
              </button>
            ))}
          </div>
        </div>

        {/* 图表 */}
        <div className="chart-container large">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="time" 
                stroke="#9ca3af"
                fontSize={12}
                interval="preserveStartEnd"
              />
              <YAxis 
                stroke="#9ca3af"
                fontSize={12}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: '#1f2937',
                  border: '1px solid #374151',
                  borderRadius: '6px',
                  color: '#f3f4f6'
                }}
                labelStyle={{ color: '#d1d5db' }}
              />
              <Legend />
              
              {metrics.map(metric => 
                selectedMetrics.includes(metric.key) ? (
                  <Line
                    key={metric.key}
                    type="monotone"
                    dataKey={metric.key}
                    stroke={metric.color}
                    strokeWidth={2}
                    dot={false}
                    name={metric.label}
                  />
                ) : null
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* 数据点信息 */}
        <div className="mt-4 text-xs text-slate-400">
          数据点: {chartData.length} | 
          时间范围: {chartTimeRange} | 
          更新时间: {chartData.length > 0 ? new Date(chartData[chartData.length - 1].timestamp * 1000).toLocaleString('zh-CN') : '无'}
        </div>
      </div>
    </div>
  )
}
