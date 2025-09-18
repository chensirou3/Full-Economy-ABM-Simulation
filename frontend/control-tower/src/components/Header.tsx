/**
 * 控制塔头部组件
 */

import React from 'react'
import { 
  BarChart3, 
  Settings, 
  RefreshCw, 
  ExternalLink,
  Activity,
  Zap
} from 'lucide-react'
import { useDashboardStore } from '../store/dashboardStore'

export const Header: React.FC = () => {
  const { 
    isConnected, 
    simulationStatus, 
    lastUpdateTime,
    refreshData 
  } = useDashboardStore()

  const handleRefresh = () => {
    refreshData()
  }

  const openWorldViewer = () => {
    window.open('http://localhost:3000', '_blank')
  }

  return (
    <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* 左侧：标题和状态 */}
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-3">
            <BarChart3 className="text-blue-400" size={24} />
            <h1 className="text-xl font-bold text-white">ABM 控制塔</h1>
          </div>
          
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                isConnected ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <span className="text-slate-300">
                {isConnected ? '已连接' : '未连接'}
              </span>
            </div>
            
            {simulationStatus && (
              <>
                <div className="text-slate-500">•</div>
                <div className="flex items-center gap-2">
                  <Activity size={14} className="text-slate-400" />
                  <span className="text-slate-300">
                    {getStatusText(simulationStatus.state)}
                  </span>
                </div>
                
                <div className="text-slate-500">•</div>
                <div className="flex items-center gap-2">
                  <Zap size={14} className="text-slate-400" />
                  <span className="text-slate-300">
                    {simulationStatus.speed}x 速度
                  </span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* 右侧：操作按钮 */}
        <div className="flex items-center gap-3">
          {lastUpdateTime && (
            <span className="text-xs text-slate-400">
              更新于 {new Date(lastUpdateTime).toLocaleTimeString()}
            </span>
          )}
          
          <button
            onClick={handleRefresh}
            className="btn btn-secondary btn-sm flex items-center gap-2"
            title="刷新数据"
          >
            <RefreshCw size={14} />
            刷新
          </button>
          
          <button
            onClick={openWorldViewer}
            className="btn btn-primary btn-sm flex items-center gap-2"
            title="打开世界视图"
          >
            <ExternalLink size={14} />
            世界视图
          </button>
          
          <button
            className="btn btn-secondary btn-sm"
            title="设置"
          >
            <Settings size={14} />
          </button>
        </div>
      </div>
    </header>
  )
}

function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    stepping: '步进中',
    rewinding: '回放中',
  }
  return statusMap[status] || status
}
