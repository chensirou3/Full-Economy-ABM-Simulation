/**
 * 模拟 API 客户端 (Control Tower)
 */

import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface SimulationStatus {
  state: 'stopped' | 'running' | 'paused' | 'stepping' | 'rewinding'
  current_time: number
  speed: number
  total_agents: number
  elapsed_real_time: number
  steps_per_second: number
  memory_usage_mb: number
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
  regional_data?: any
  sectoral_data?: any
}

export const simulationApi = {
  // 控制 API
  async play(speed?: number) {
    const response = await api.post('/control/play', { speed })
    return response.data
  },
  
  async pause() {
    const response = await api.post('/control/pause')
    return response.data
  },
  
  async step(steps: number) {
    const response = await api.post('/control/step', { steps })
    return response.data
  },
  
  async setSpeed(speed: number) {
    const response = await api.post('/control/speed', { speed })
    return response.data
  },
  
  async jump(targetTime: number) {
    const response = await api.post('/control/jump', { target_time: targetTime })
    return response.data
  },
  
  async rewind(targetTime: number) {
    const response = await api.post('/control/rewind', { target_time: targetTime })
    return response.data
  },
  
  async reset() {
    const response = await api.post('/control/reset')
    return response.data
  },
  
  async getStatus(): Promise<SimulationStatus> {
    const response = await api.get('/control/status')
    return response.data.data
  },
  
  // 指标 API
  async getCurrentMetrics(): Promise<MetricsData> {
    const response = await api.get('/metrics/current')
    return response.data.data
  },
  
  async getMetricsHistory(limit?: number): Promise<MetricsData[]> {
    const response = await api.get('/metrics/history', { params: { limit } })
    return response.data.data
  },
  
  async getMetricsSummary() {
    const response = await api.get('/metrics/summary')
    return response.data.data
  },
  
  async exportMetrics(format: 'json' | 'csv' = 'json', startTime?: number, endTime?: number) {
    const response = await api.get('/metrics/export', {
      params: { format, start_time: startTime, end_time: endTime }
    })
    return response.data
  },
  
  // 场景 API
  async getScenarios() {
    const response = await api.get('/scenarios/')
    return response.data
  },
  
  async getScenario(scenarioName: string) {
    const response = await api.get(`/scenarios/${scenarioName}`)
    return response.data.data
  },
  
  async loadScenario(scenarioName: string) {
    const response = await api.post(`/scenarios/load/${scenarioName}`)
    return response.data
  },
  
  async validateScenario(scenarioName: string) {
    const response = await api.get(`/scenarios/validate/${scenarioName}`)
    return response.data
  },
  
  // 快照 API
  async getSnapshots() {
    const response = await api.get('/snapshots/')
    return response.data
  },
  
  async getLatestSnapshot() {
    const response = await api.get('/snapshots/latest')
    return response.data.data
  },
  
  async createSnapshot() {
    const response = await api.post('/snapshots/create')
    return response.data
  },
  
  async getStorageStats() {
    const response = await api.get('/snapshots/stats/storage')
    return response.data.data
  },
}

// 响应拦截器处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.data?.error) {
      throw new Error(error.response.data.error)
    }
    if (error.code === 'ECONNREFUSED') {
      throw new Error('无法连接到服务器，请确保后端服务正在运行')
    }
    throw error
  }
)
