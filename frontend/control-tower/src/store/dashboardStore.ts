/**
 * 仪表板状态管理
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export interface MetricsData {
  timestamp: number
  kpis: {
    gdp: number
    unemployment: number
    inflation: number
    policy_rate: number
    credit_growth?: number
    default_rate?: number
    total_agents: number
  }
  regional_data?: any
  sectoral_data?: any
}

export interface SimulationStatus {
  state: 'stopped' | 'running' | 'paused' | 'stepping' | 'rewinding'
  current_time: number
  speed: number
  total_agents: number
  elapsed_real_time: number
  steps_per_second: number
  memory_usage_mb: number
}

export interface DashboardEvent {
  timestamp: number
  event_type: string
  actor_id?: number | string
  payload: any
  metadata?: any
}

export interface DashboardState {
  // 连接状态
  isConnected: boolean
  connectionError: string | null
  lastUpdateTime: number | null
  
  // 模拟状态
  simulationStatus: SimulationStatus | null
  
  // 指标数据
  currentMetrics: MetricsData | null
  metricsHistory: MetricsData[]
  
  // 事件数据
  events: DashboardEvent[]
  
  // 场景和快照
  scenarios: any[]
  snapshots: any[]
  
  // UI 状态
  selectedScenario: string | null
  autoRefresh: boolean
  refreshInterval: number
  
  // 图表设置
  chartTimeRange: '1h' | '6h' | '24h' | '7d'
  selectedMetrics: string[]
}

export interface DashboardActions {
  // 连接管理
  setConnected: (connected: boolean) => void
  setConnectionError: (error: string | null) => void
  
  // 数据更新
  updateSimulationStatus: (status: SimulationStatus) => void
  updateMetrics: (metrics: MetricsData) => void
  addEvent: (event: DashboardEvent) => void
  updateScenarios: (scenarios: any[]) => void
  updateSnapshots: (snapshots: any[]) => void
  
  // UI 操作
  setSelectedScenario: (scenario: string | null) => void
  setAutoRefresh: (enabled: boolean) => void
  setRefreshInterval: (interval: number) => void
  setChartTimeRange: (range: DashboardState['chartTimeRange']) => void
  toggleMetric: (metric: string) => void
  
  // 操作
  refreshData: () => void
  clearEvents: () => void
  reset: () => void
}

const initialState: DashboardState = {
  isConnected: false,
  connectionError: null,
  lastUpdateTime: null,
  simulationStatus: null,
  currentMetrics: null,
  metricsHistory: [],
  events: [],
  scenarios: [],
  snapshots: [],
  selectedScenario: null,
  autoRefresh: true,
  refreshInterval: 2000,
  chartTimeRange: '1h',
  selectedMetrics: ['gdp', 'unemployment', 'inflation', 'policy_rate'],
}

export const useDashboardStore = create<DashboardState & DashboardActions>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,
    
    // 连接管理
    setConnected: (connected) => set({ isConnected: connected }),
    setConnectionError: (error) => set({ connectionError: error }),
    
    // 数据更新
    updateSimulationStatus: (status) => {
      set({ 
        simulationStatus: status,
        lastUpdateTime: Date.now(),
      })
    },
    
    updateMetrics: (metrics) => {
      set((state) => ({
        currentMetrics: metrics,
        metricsHistory: [...state.metricsHistory.slice(-99), metrics], // 保持最新100个
        lastUpdateTime: Date.now(),
      }))
    },
    
    addEvent: (event) => {
      set((state) => ({
        events: [...state.events.slice(-199), event], // 保持最新200个事件
      }))
    },
    
    updateScenarios: (scenarios) => set({ scenarios }),
    updateSnapshots: (snapshots) => set({ snapshots }),
    
    // UI 操作
    setSelectedScenario: (scenario) => set({ selectedScenario: scenario }),
    setAutoRefresh: (enabled) => set({ autoRefresh: enabled }),
    setRefreshInterval: (interval) => set({ refreshInterval: interval }),
    setChartTimeRange: (range) => set({ chartTimeRange: range }),
    
    toggleMetric: (metric) => {
      set((state) => {
        const selectedMetrics = state.selectedMetrics.includes(metric)
          ? state.selectedMetrics.filter(m => m !== metric)
          : [...state.selectedMetrics, metric]
        
        return { selectedMetrics }
      })
    },
    
    // 操作
    refreshData: () => {
      // 这个函数会被 useDashboardData hook 重写
      console.log('refreshData called')
    },
    
    clearEvents: () => set({ events: [] }),
    
    reset: () => set(initialState),
  }))
)

// 选择器 hooks
export const useMetrics = () => useDashboardStore((state) => state.currentMetrics)
export const useSimulationStatus = () => useDashboardStore((state) => state.simulationStatus)
export const useEvents = () => useDashboardStore((state) => state.events)
export const useMetricsHistory = () => useDashboardStore((state) => state.metricsHistory)

// 派生状态选择器
export const useFilteredMetricsHistory = (timeRange: string) => 
  useDashboardStore((state) => {
    const now = Date.now()
    const ranges = {
      '1h': 60 * 60 * 1000,
      '6h': 6 * 60 * 60 * 1000,
      '24h': 24 * 60 * 60 * 1000,
      '7d': 7 * 24 * 60 * 60 * 1000,
    }
    
    const cutoff = now - (ranges[timeRange as keyof typeof ranges] || ranges['1h'])
    
    return state.metricsHistory.filter(m => m.timestamp * 1000 > cutoff)
  })

export const useRecentEvents = (limit: number = 50) =>
  useDashboardStore((state) => state.events.slice(-limit).reverse())
