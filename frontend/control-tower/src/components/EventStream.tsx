/**
 * 事件流组件
 */

import React from 'react'
import { Activity, Filter, X } from 'lucide-react'
import { useRecentEvents } from '../store/dashboardStore'

export const EventStream: React.FC = () => {
  const events = useRecentEvents(100)
  const [filter, setFilter] = React.useState('')
  const [selectedTypes, setSelectedTypes] = React.useState<string[]>([])

  // 获取事件类型列表
  const eventTypes = React.useMemo(() => {
    const types = new Set(events.map(e => e.event_type))
    return Array.from(types).sort()
  }, [events])

  // 过滤事件
  const filteredEvents = React.useMemo(() => {
    return events.filter(event => {
      // 文本过滤
      if (filter && !event.event_type.toLowerCase().includes(filter.toLowerCase())) {
        return false
      }
      
      // 类型过滤
      if (selectedTypes.length > 0 && !selectedTypes.includes(event.event_type)) {
        return false
      }
      
      return true
    })
  }, [events, filter, selectedTypes])

  const toggleEventType = (type: string) => {
    setSelectedTypes(prev => 
      prev.includes(type) 
        ? prev.filter(t => t !== type)
        : [...prev, type]
    )
  }

  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title flex items-center gap-2">
          <Activity size={20} />
          事件流
        </h3>
        <div className="text-sm text-slate-400">
          {filteredEvents.length} / {events.length}
        </div>
      </div>
      
      <div className="dashboard-card-content">
        {/* 过滤控件 */}
        <div className="space-y-3 mb-4">
          <div className="relative">
            <input
              type="text"
              placeholder="搜索事件..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input w-full pr-8"
            />
            {filter && (
              <button
                onClick={() => setFilter('')}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* 事件类型过滤 */}
          {eventTypes.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Filter size={14} className="text-slate-400" />
                <span className="text-sm text-slate-400">事件类型:</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {eventTypes.slice(0, 6).map(type => (
                  <button
                    key={type}
                    onClick={() => toggleEventType(type)}
                    className={`px-2 py-1 rounded text-xs transition-colors ${
                      selectedTypes.includes(type)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {getEventTypeLabel(type)}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* 事件列表 */}
        <div className="event-stream">
          {filteredEvents.length === 0 ? (
            <div className="text-center py-8 text-slate-400">
              {events.length === 0 ? '暂无事件' : '没有匹配的事件'}
            </div>
          ) : (
            <div className="space-y-1">
              {filteredEvents.map((event, index) => (
                <EventItem key={`${event.timestamp}-${index}`} event={event} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 事件项组件
const EventItem: React.FC<{ event: any }> = ({ event }) => {
  const eventTypeColor = getEventTypeColor(event.event_type)
  
  return (
    <div className="event-item">
      <div className="flex items-start gap-2">
        <div className={`w-2 h-2 rounded-full mt-1.5 ${eventTypeColor}`}></div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="event-type text-sm font-medium">
              {getEventTypeLabel(event.event_type)}
            </span>
            <span className="event-time">
              {formatEventTime(event.timestamp)}
            </span>
          </div>
          
          {event.actor_id && (
            <div className="text-xs text-slate-400 mt-1">
              代理: {event.actor_id}
            </div>
          )}
          
          {event.payload && Object.keys(event.payload).length > 0 && (
            <div className="event-description">
              {formatEventPayload(event.payload)}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// 工具函数
function getEventTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    'firm.bankruptcy': '企业破产',
    'bank.failure': '银行倒闭',
    'market.crash': '市场崩溃',
    'unemployment.spike': '失业激增',
    'inflation.shock': '通胀冲击',
    'policy.interest_rate_change': '利率调整',
    'policy.central_bank_vote': '央行投票',
    'system.simulation_start': '模拟开始',
    'system.simulation_pause': '模拟暂停',
    'system.checkpoint_created': '快照创建',
    'agent.birth': '代理出生',
    'agent.death': '代理死亡',
    'agent.migration': '代理迁移',
    'agent.job_change': '工作变更',
    'market.clearing': '市场清算',
    'policy_vote': '政策投票',
  }
  return labels[type] || type
}

function getEventTypeColor(type: string): string {
  const colors: Record<string, string> = {
    'firm.bankruptcy': 'bg-red-400',
    'bank.failure': 'bg-red-500',
    'market.crash': 'bg-red-600',
    'unemployment.spike': 'bg-orange-400',
    'inflation.shock': 'bg-yellow-400',
    'policy.interest_rate_change': 'bg-blue-400',
    'policy.central_bank_vote': 'bg-purple-400',
    'system.simulation_start': 'bg-green-400',
    'system.simulation_pause': 'bg-yellow-500',
    'system.checkpoint_created': 'bg-indigo-400',
    'agent.birth': 'bg-green-300',
    'agent.death': 'bg-gray-400',
    'agent.migration': 'bg-cyan-400',
    'agent.job_change': 'bg-teal-400',
    'market.clearing': 'bg-blue-300',
    'policy_vote': 'bg-purple-300',
  }
  return colors[type] || 'bg-slate-400'
}

function formatEventTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString('zh-CN', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatEventPayload(payload: any): string {
  if (!payload || typeof payload !== 'object') return ''
  
  const keys = Object.keys(payload)
  if (keys.length === 0) return ''
  
  // 显示前几个关键字段
  const importantKeys = keys.slice(0, 3)
  const parts = importantKeys.map(key => {
    const value = payload[key]
    if (typeof value === 'number') {
      return `${key}: ${value.toLocaleString()}`
    }
    return `${key}: ${String(value).slice(0, 20)}`
  })
  
  return parts.join(', ')
}
