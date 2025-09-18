/**
 * KPI 卡片组件
 * 显示核心经济指标
 */

import React from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  DollarSign, 
  Percent, 
  Building,
  ArrowUp,
  ArrowDown,
  Minus
} from 'lucide-react'
import { useDashboardStore } from '../store/dashboardStore'

export const KPICards: React.FC = () => {
  const { currentMetrics, metricsHistory } = useDashboardStore()

  if (!currentMetrics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="kpi-card animate-pulse">
            <div className="h-4 bg-slate-700 rounded mb-2"></div>
            <div className="h-8 bg-slate-700 rounded mb-2"></div>
            <div className="h-3 bg-slate-700 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    )
  }

  const kpis = [
    {
      key: 'gdp',
      label: 'GDP',
      value: currentMetrics.kpis.gdp,
      format: (v: number) => `$${(v / 1000000).toFixed(1)}M`,
      icon: DollarSign,
      color: 'text-green-400',
    },
    {
      key: 'unemployment',
      label: '失业率',
      value: currentMetrics.kpis.unemployment,
      format: (v: number) => `${(v * 100).toFixed(1)}%`,
      icon: Users,
      color: 'text-red-400',
      inverse: true, // 失业率低更好
    },
    {
      key: 'inflation',
      label: '通胀率',
      value: currentMetrics.kpis.inflation,
      format: (v: number) => `${(v * 100).toFixed(1)}%`,
      icon: Percent,
      color: 'text-yellow-400',
    },
    {
      key: 'policy_rate',
      label: '政策利率',
      value: currentMetrics.kpis.policy_rate,
      format: (v: number) => `${(v * 100).toFixed(2)}%`,
      icon: TrendingUp,
      color: 'text-blue-400',
    },
    {
      key: 'total_agents',
      label: '代理总数',
      value: currentMetrics.kpis.total_agents,
      format: (v: number) => v.toLocaleString(),
      icon: Building,
      color: 'text-purple-400',
    },
    {
      key: 'credit_growth',
      label: '信贷增长',
      value: currentMetrics.kpis.credit_growth || 0,
      format: (v: number) => `${(v * 100).toFixed(1)}%`,
      icon: TrendingUp,
      color: 'text-indigo-400',
    },
  ]

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {kpis.map((kpi) => {
        const Icon = kpi.icon
        const change = calculateChange(kpi.key, currentMetrics, metricsHistory)
        
        return (
          <div key={kpi.key} className="kpi-card">
            <div className="flex items-center justify-between mb-2">
              <Icon className={`${kpi.color} opacity-80`} size={20} />
              {change !== null && (
                <ChangeIndicator 
                  change={change} 
                  inverse={kpi.inverse}
                />
              )}
            </div>
            
            <div className="kpi-value">
              {kpi.format(kpi.value)}
            </div>
            
            <div className="kpi-label">
              {kpi.label}
            </div>
            
            {change !== null && (
              <div className={`kpi-change ${getChangeClass(change, kpi.inverse)}`}>
                {change > 0 ? '+' : ''}{change.toFixed(2)}%
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// 变化指示器组件
const ChangeIndicator: React.FC<{ change: number; inverse?: boolean }> = ({ 
  change, 
  inverse = false 
}) => {
  if (Math.abs(change) < 0.01) {
    return <Minus className="text-slate-400" size={14} />
  }
  
  const isPositive = inverse ? change < 0 : change > 0
  const Icon = change > 0 ? ArrowUp : ArrowDown
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400'
  
  return <Icon className={colorClass} size={14} />
}

// 计算变化百分比
function calculateChange(
  key: string, 
  current: any, 
  history: any[]
): number | null {
  if (!history || history.length < 2) return null
  
  const previous = history[history.length - 2]
  if (!previous || !previous.kpis[key]) return null
  
  const currentValue = current.kpis[key]
  const previousValue = previous.kpis[key]
  
  if (previousValue === 0) return null
  
  return ((currentValue - previousValue) / previousValue) * 100
}

// 获取变化样式类
function getChangeClass(change: number, inverse: boolean = false): string {
  if (Math.abs(change) < 0.01) return 'neutral'
  
  const isPositive = inverse ? change < 0 : change > 0
  return isPositive ? 'positive' : 'negative'
}
