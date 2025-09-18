/**
 * WebSocket 连接 Hook
 * 处理实时数据同步
 */

import { useEffect, useRef, useState } from 'react'
import { useSimulationStore } from '../store/simulationStore'

interface WebSocketMessage {
  topic: string
  data: any
  timestamp: number
}

export const useWebSocket = (url: string) => {
  const wsRef = useRef<WebSocket | null>(null)
  const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected')
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const reconnectAttempts = useRef(0)
  const maxReconnectAttempts = 5
  const reconnectDelay = 3000

  const {
    setConnected,
    setConnectionError,
    updateSimulationStatus,
    updateAgents,
    updateMetrics,
    addEvent,
  } = useSimulationStore()

  const connect = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }

    setConnectionState('connecting')
    console.log('正在连接 WebSocket...', url)

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('WebSocket 连接已建立')
        setConnectionState('connected')
        setConnected(true)
        setConnectionError(null)
        reconnectAttempts.current = 0

        // 订阅所有主题
        const subscribeMessage = {
          type: 'subscribe',
          topics: ['metrics.update', 'world.delta', 'events.stream', 'policy.vote']
        }
        ws.send(JSON.stringify(subscribeMessage))
      }

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          handleMessage(message)
        } catch (error) {
          console.error('解析 WebSocket 消息失败:', error, event.data)
        }
      }

      ws.onclose = (event) => {
        console.log('WebSocket 连接已关闭', event.code, event.reason)
        setConnectionState('disconnected')
        setConnected(false)
        
        // 自动重连
        if (reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++
          console.log(`尝试重连 (${reconnectAttempts.current}/${maxReconnectAttempts})...`)
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, reconnectDelay)
        } else {
          setConnectionError('连接失败，已达到最大重试次数')
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket 错误:', error)
        setConnectionError('WebSocket 连接错误')
      }

    } catch (error) {
      console.error('创建 WebSocket 连接失败:', error)
      setConnectionError('无法创建 WebSocket 连接')
      setConnectionState('disconnected')
    }
  }

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    
    setConnectionState('disconnected')
    setConnected(false)
  }

  const handleMessage = (message: WebSocketMessage) => {
    console.log('收到 WebSocket 消息:', message.topic, message.data)

    switch (message.topic) {
      case 'metrics.update':
        updateMetrics(message.data)
        break

      case 'world.delta':
        // 处理世界状态增量更新
        if (message.data.actors_delta) {
          updateAgents(message.data.actors_delta)
        }
        break

      case 'events.stream':
        addEvent(message.data)
        break

      case 'policy.vote':
        // 处理央行投票事件
        addEvent({
          ...message.data,
          type: 'policy_vote'
        })
        break

      default:
        console.log('未处理的消息主题:', message.topic)
    }
  }

  const sendMessage = (message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('WebSocket 未连接，无法发送消息')
    }
  }

  // 发送心跳
  useEffect(() => {
    if (connectionState !== 'connected') return

    const heartbeatInterval = setInterval(() => {
      sendMessage({
        type: 'ping',
        timestamp: Date.now()
      })
    }, 30000) // 30秒心跳

    return () => clearInterval(heartbeatInterval)
  }, [connectionState])

  // 组件挂载时连接
  useEffect(() => {
    connect()

    return () => {
      disconnect()
    }
  }, [url])

  return {
    connectionState,
    connect,
    disconnect,
    sendMessage,
    isConnected: connectionState === 'connected',
  }
}
