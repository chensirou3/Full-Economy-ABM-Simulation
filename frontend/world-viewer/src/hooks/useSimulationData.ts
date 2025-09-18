/**
 * 模拟数据获取 Hook
 * 使用 React Query 管理数据获取和缓存
 */

import { useQuery } from '@tanstack/react-query'
import { simulationApi } from '../api/simulation'
import { useSimulationStore } from '../store/simulationStore'
import { useWebSocket } from './useWebSocket'

export const useSimulationData = () => {
  const { updateSimulationStatus, updateMetrics } = useSimulationStore()
  
  // WebSocket 连接
  const websocketUrl = `ws://localhost:8000/ws`
  const { isConnected } = useWebSocket(websocketUrl)

  // 查询模拟状态
  const {
    data: simulationStatus,
    isLoading: statusLoading,
    error: statusError,
  } = useQuery({
    queryKey: ['simulation-status'],
    queryFn: simulationApi.getStatus,
    refetchInterval: isConnected ? false : 2000, // WebSocket 连接时停止轮询
    onSuccess: (data) => {
      updateSimulationStatus(data)
    },
  })

  // 查询当前指标
  const {
    data: currentMetrics,
    isLoading: metricsLoading,
    error: metricsError,
  } = useQuery({
    queryKey: ['current-metrics'],
    queryFn: simulationApi.getCurrentMetrics,
    refetchInterval: isConnected ? false : 1000, // WebSocket 连接时停止轮询
    onSuccess: (data) => {
      updateMetrics(data)
    },
  })

  // 查询代理数据
  const {
    data: agentsData,
    isLoading: agentsLoading,
    error: agentsError,
  } = useQuery({
    queryKey: ['agent-metrics'],
    queryFn: () => simulationApi.getAgentMetrics(undefined, 1000), // 获取1000个代理
    refetchInterval: isConnected ? false : 5000, // WebSocket 连接时停止轮询
    onSuccess: (data) => {
      // 更新代理数据
      // updateAgents(data) // 这个会通过 WebSocket 实时更新
    },
  })

  // 查询场景列表
  const {
    data: scenarios,
    isLoading: scenariosLoading,
    error: scenariosError,
  } = useQuery({
    queryKey: ['scenarios'],
    queryFn: simulationApi.getScenarios,
    staleTime: 5 * 60 * 1000, // 5分钟内不重新获取
  })

  // 查询快照列表
  const {
    data: snapshots,
    isLoading: snapshotsLoading,
    error: snapshotsError,
  } = useQuery({
    queryKey: ['snapshots'],
    queryFn: simulationApi.getSnapshots,
    refetchInterval: 10000, // 10秒刷新
  })

  return {
    // 连接状态
    isConnected,
    
    // 模拟状态
    simulationStatus,
    statusLoading,
    statusError,
    
    // 指标数据
    currentMetrics,
    metricsLoading,
    metricsError,
    
    // 代理数据
    agentsData,
    agentsLoading,
    agentsError,
    
    // 场景数据
    scenarios,
    scenariosLoading,
    scenariosError,
    
    // 快照数据
    snapshots,
    snapshotsLoading,
    snapshotsError,
    
    // 整体加载状态
    isLoading: statusLoading || metricsLoading || agentsLoading,
    hasError: !!(statusError || metricsError || agentsError),
  }
}
