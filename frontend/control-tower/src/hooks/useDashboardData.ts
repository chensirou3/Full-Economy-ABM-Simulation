/**
 * 仪表板数据获取 Hook
 */

import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useDashboardStore } from '../store/dashboardStore'
import { simulationApi } from '../api/simulation'

export const useDashboardData = () => {
  const {
    isConnected,
    connectionError,
    autoRefresh,
    refreshInterval,
    setConnected,
    setConnectionError,
    updateSimulationStatus,
    updateMetrics,
    addEvent,
    updateScenarios,
    updateSnapshots,
  } = useDashboardStore()

  const wsRef = useRef<WebSocket | null>(null)

  // WebSocket 连接
  useEffect(() => {
    const connectWebSocket = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return

      try {
        const ws = new WebSocket('ws://localhost:8000/ws')
        wsRef.current = ws

        ws.onopen = () => {
          console.log('仪表板 WebSocket 已连接')
          setConnected(true)
          setConnectionError(null)

          // 订阅相关主题
          ws.send(JSON.stringify({
            type: 'subscribe',
            topics: ['metrics.update', 'events.stream', 'policy.vote']
          }))
        }

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data)
            handleWebSocketMessage(message)
          } catch (error) {
            console.error('解析 WebSocket 消息失败:', error)
          }
        }

        ws.onclose = () => {
          console.log('仪表板 WebSocket 连接关闭')
          setConnected(false)
          
          // 3秒后重连
          setTimeout(connectWebSocket, 3000)
        }

        ws.onerror = (error) => {
          console.error('仪表板 WebSocket 错误:', error)
          setConnectionError('WebSocket 连接失败')
        }

      } catch (error) {
        console.error('创建 WebSocket 连接失败:', error)
        setConnectionError('无法创建 WebSocket 连接')
      }
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [setConnected, setConnectionError])

  // 处理 WebSocket 消息
  const handleWebSocketMessage = (message: any) => {
    switch (message.topic) {
      case 'metrics.update':
        updateMetrics(message.data)
        break

      case 'events.stream':
        addEvent({
          timestamp: message.data.timestamp,
          event_type: message.data.event_type,
          actor_id: message.data.actor_id,
          payload: message.data.payload,
          metadata: message.data.metadata,
        })
        break

      case 'policy.vote':
        addEvent({
          timestamp: message.data.timestamp,
          event_type: 'policy_vote',
          actor_id: message.data.member_id,
          payload: message.data,
        })
        break
    }
  }

  // 查询模拟状态
  const {
    data: simulationStatus,
    isLoading: statusLoading,
    error: statusError,
  } = useQuery({
    queryKey: ['dashboard-simulation-status'],
    queryFn: simulationApi.getStatus,
    refetchInterval: isConnected ? false : (autoRefresh ? refreshInterval : false),
    onSuccess: (data) => {
      updateSimulationStatus(data)
    },
    onError: (error: any) => {
      setConnectionError(error.message || '获取模拟状态失败')
    },
  })

  // 查询当前指标
  const {
    data: currentMetrics,
    isLoading: metricsLoading,
    error: metricsError,
  } = useQuery({
    queryKey: ['dashboard-current-metrics'],
    queryFn: simulationApi.getCurrentMetrics,
    refetchInterval: isConnected ? false : (autoRefresh ? refreshInterval : false),
    onSuccess: (data) => {
      updateMetrics(data)
    },
    onError: (error: any) => {
      setConnectionError(error.message || '获取指标数据失败')
    },
  })

  // 查询场景列表
  const {
    data: scenarios,
    isLoading: scenariosLoading,
  } = useQuery({
    queryKey: ['dashboard-scenarios'],
    queryFn: simulationApi.getScenarios,
    staleTime: 5 * 60 * 1000, // 5分钟缓存
    onSuccess: (data) => {
      updateScenarios(data)
    },
  })

  // 查询快照列表
  const {
    data: snapshots,
    isLoading: snapshotsLoading,
  } = useQuery({
    queryKey: ['dashboard-snapshots'],
    queryFn: simulationApi.getSnapshots,
    refetchInterval: 30000, // 30秒刷新
    onSuccess: (data) => {
      updateSnapshots(data)
    },
  })

  // 重写 refreshData 函数
  useEffect(() => {
    const originalRefreshData = useDashboardStore.getState().refreshData
    
    useDashboardStore.setState({
      refreshData: () => {
        // 手动触发所有查询刷新
        simulationStatus && updateSimulationStatus(simulationStatus)
        currentMetrics && updateMetrics(currentMetrics)
        scenarios && updateScenarios(scenarios)
        snapshots && updateSnapshots(snapshots)
      }
    })

    return () => {
      useDashboardStore.setState({ refreshData: originalRefreshData })
    }
  }, [simulationStatus, currentMetrics, scenarios, snapshots, updateSimulationStatus, updateMetrics, updateScenarios, updateSnapshots])

  return {
    isConnected,
    connectionError,
    isLoading: statusLoading || metricsLoading,
    hasError: !!(statusError || metricsError),
    
    // 数据
    simulationStatus,
    currentMetrics,
    scenarios,
    snapshots,
    
    // 加载状态
    statusLoading,
    metricsLoading,
    scenariosLoading,
    snapshotsLoading,
  }
}
