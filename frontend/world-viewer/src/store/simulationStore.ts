/**
 * 模拟状态管理
 * 使用 Zustand 管理全局状态
 */

import { create } from 'zustand'
import { subscribeWithSelector } from 'zustand/middleware'

export interface Agent {
  agent_id: number
  agent_type: string
  status: string
  position: {
    x: number
    y: number
  }
  balance_sheet: {
    total_assets: number
    total_liabilities: number
    net_worth: number
  }
  // 代理特定属性
  [key: string]: any
}

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
}

export interface SimulationState {
  // 连接状态
  isConnected: boolean
  connectionError: string | null
  
  // 模拟状态
  simulationStatus: {
    state: 'stopped' | 'running' | 'paused' | 'stepping' | 'rewinding'
    current_time: number
    speed: number
    total_agents: number
    steps_per_second: number
  } | null
  
  // 数据
  agents: Agent[]
  metrics: MetricsData | null
  events: any[]
  
  // UI 状态
  selectedAgent: Agent | null
  showLayers: {
    agents: boolean
    unemployment: boolean
    population: boolean
    firms: boolean
    banks: boolean
  }
  
  // 相机状态
  camera: {
    x: number
    y: number
    zoom: number
  }
}

export interface SimulationActions {
  // 连接管理
  setConnected: (connected: boolean) => void
  setConnectionError: (error: string | null) => void
  
  // 数据更新
  updateSimulationStatus: (status: SimulationState['simulationStatus']) => void
  updateAgents: (agents: Agent[]) => void
  updateMetrics: (metrics: MetricsData) => void
  addEvent: (event: any) => void
  
  // UI 交互
  selectAgent: (agent: Agent | null) => void
  toggleLayer: (layer: keyof SimulationState['showLayers']) => void
  updateCamera: (camera: Partial<SimulationState['camera']>) => void
  
  // 重置
  reset: () => void
}

const initialState: SimulationState = {
  isConnected: false,
  connectionError: null,
  simulationStatus: null,
  agents: [],
  metrics: null,
  events: [],
  selectedAgent: null,
  showLayers: {
    agents: true,
    unemployment: false,
    population: true,
    firms: true,
    banks: true,
  },
  camera: {
    x: 0,
    y: 0,
    zoom: 1,
  },
}

export const useSimulationStore = create<SimulationState & SimulationActions>()(
  subscribeWithSelector((set, get) => ({
    ...initialState,
    
    // 连接管理
    setConnected: (connected) => set({ isConnected: connected }),
    setConnectionError: (error) => set({ connectionError: error }),
    
    // 数据更新
    updateSimulationStatus: (status) => set({ simulationStatus: status }),
    
    updateAgents: (agents) => {
      set({ agents })
      
      // 如果选中的代理已更新，更新选中状态
      const { selectedAgent } = get()
      if (selectedAgent) {
        const updatedAgent = agents.find(a => a.agent_id === selectedAgent.agent_id)
        if (updatedAgent) {
          set({ selectedAgent: updatedAgent })
        }
      }
    },
    
    updateMetrics: (metrics) => set({ metrics }),
    
    addEvent: (event) => set((state) => ({
      events: [...state.events.slice(-999), event] // 保持最新1000个事件
    })),
    
    // UI 交互
    selectAgent: (agent) => set({ selectedAgent: agent }),
    
    toggleLayer: (layer) => set((state) => ({
      showLayers: {
        ...state.showLayers,
        [layer]: !state.showLayers[layer],
      },
    })),
    
    updateCamera: (camera) => set((state) => ({
      camera: { ...state.camera, ...camera },
    })),
    
    // 重置
    reset: () => set(initialState),
  }))
)

// 选择器 hooks
export const useAgents = () => useSimulationStore((state) => state.agents)
export const useMetrics = () => useSimulationStore((state) => state.metrics)
export const useSimulationStatus = () => useSimulationStore((state) => state.simulationStatus)
export const useSelectedAgent = () => useSimulationStore((state) => state.selectedAgent)
export const useShowLayers = () => useSimulationStore((state) => state.showLayers)
export const useCamera = () => useSimulationStore((state) => state.camera)

// 派生状态选择器
export const useAgentsByType = (agentType?: string) => 
  useSimulationStore((state) => 
    agentType 
      ? state.agents.filter(agent => agent.agent_type === agentType)
      : state.agents
  )

export const useAgentCounts = () => 
  useSimulationStore((state) => {
    const counts = state.agents.reduce((acc, agent) => {
      acc[agent.agent_type] = (acc[agent.agent_type] || 0) + 1
      return acc
    }, {} as Record<string, number>)
    
    return {
      total: state.agents.length,
      ...counts,
    }
  })
