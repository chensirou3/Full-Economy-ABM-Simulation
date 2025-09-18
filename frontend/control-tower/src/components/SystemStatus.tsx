/**
 * 系统状态组件
 * 显示模拟器运行状态和控制按钮
 */

import React from 'react'
import { 
  Play, 
  Pause, 
  Square, 
  SkipForward, 
  RotateCcw, 
  FastForward,
  Activity,
  Clock,
  Cpu,
  HardDrive
} from 'lucide-react'
import { useDashboardStore } from '../store/dashboardStore'
import { useSimulationControl } from '../hooks/useSimulationControl'

export const SystemStatus: React.FC = () => {
  const { simulationStatus, isConnected } = useDashboardStore()
  const { play, pause, step, rewind, jump, setSpeed, isLoading } = useSimulationControl()

  if (!simulationStatus) {
    return (
      <div className="dashboard-card">
        <div className="dashboard-card-header">
          <h3 className="dashboard-card-title flex items-center gap-2">
            <Activity size={20} />
            系统状态
          </h3>
        </div>
        <div className="dashboard-card-content">
          <div className="text-center py-8 text-slate-400">
            {isConnected ? '正在加载系统状态...' : '未连接到模拟器'}
          </div>
        </div>
      </div>
    )
  }

  const isRunning = simulationStatus.state === 'running'
  const isPaused = simulationStatus.state === 'paused'

  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title flex items-center gap-2">
          <Activity size={20} />
          系统状态与控制
        </h3>
        <div className={`status-indicator ${simulationStatus.state}`}>
          {getStatusText(simulationStatus.state)}
        </div>
      </div>
      
      <div className="dashboard-card-content">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 状态指标 */}
          <div className="space-y-4">
            <h4 className="font-medium text-slate-200 mb-3">运行指标</h4>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400">
                  <Clock size={16} />
                  <span>模拟时间:</span>
                </div>
                <span className="font-mono text-slate-200">
                  {simulationStatus.current_time.toLocaleString()}
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400">
                  <FastForward size={16} />
                  <span>运行速度:</span>
                </div>
                <span className="font-mono text-slate-200">
                  {simulationStatus.speed}x
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400">
                  <Cpu size={16} />
                  <span>性能:</span>
                </div>
                <span className="font-mono text-green-400">
                  {simulationStatus.steps_per_second.toFixed(1)} steps/s
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400">
                  <HardDrive size={16} />
                  <span>内存使用:</span>
                </div>
                <span className="font-mono text-blue-400">
                  {simulationStatus.memory_usage_mb.toFixed(1)} MB
                </span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-slate-400">
                  <Activity size={16} />
                  <span>代理总数:</span>
                </div>
                <span className="font-mono text-purple-400">
                  {simulationStatus.total_agents.toLocaleString()}
                </span>
              </div>
            </div>
          </div>

          {/* 控制面板 */}
          <div className="space-y-4">
            <h4 className="font-medium text-slate-200 mb-3">模拟控制</h4>
            
            {/* 主控制按钮 */}
            <div className="flex gap-2">
              {isRunning ? (
                <button
                  onClick={pause}
                  disabled={isLoading}
                  className="btn btn-warning flex items-center gap-2 flex-1"
                >
                  <Pause size={16} />
                  暂停
                </button>
              ) : (
                <button
                  onClick={() => play()}
                  disabled={isLoading}
                  className="btn btn-success flex items-center gap-2 flex-1"
                >
                  <Play size={16} />
                  播放
                </button>
              )}
              
              <button
                onClick={() => step(1)}
                disabled={isLoading || isRunning}
                className="btn btn-secondary"
                title="单步执行"
              >
                <SkipForward size={16} />
              </button>
            </div>

            {/* 时间控制 */}
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-slate-400 mb-1">
                  播放速度
                </label>
                <select
                  value={simulationStatus.speed}
                  onChange={(e) => setSpeed(parseFloat(e.target.value))}
                  disabled={isLoading}
                  className="select w-full"
                >
                  <option value={0.1}>0.1x</option>
                  <option value={0.25}>0.25x</option>
                  <option value={0.5}>0.5x</option>
                  <option value={1}>1x</option>
                  <option value={2}>2x</option>
                  <option value={5}>5x</option>
                  <option value={10}>10x</option>
                </select>
              </div>

              <TimeJumpControl 
                currentTime={simulationStatus.current_time}
                onJump={jump}
                onRewind={rewind}
                disabled={isLoading}
              />
            </div>

            {/* 状态信息 */}
            {isLoading && (
              <div className="flex items-center gap-2 text-yellow-400 text-sm">
                <div className="loading-spinner"></div>
                <span>处理中...</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// 时间跳转控制组件
const TimeJumpControl: React.FC<{
  currentTime: number
  onJump: (time: number) => void
  onRewind: (time: number) => void
  disabled: boolean
}> = ({ currentTime, onJump, onRewind, disabled }) => {
  const [jumpTarget, setJumpTarget] = React.useState('')
  const [showJumpInput, setShowJumpInput] = React.useState(false)

  const handleJump = () => {
    const target = parseInt(jumpTarget)
    if (!isNaN(target) && target >= 0) {
      if (target < currentTime) {
        onRewind(target)
      } else {
        onJump(target)
      }
      setJumpTarget('')
      setShowJumpInput(false)
    }
  }

  const quickRewind = (steps: number) => {
    const target = Math.max(0, currentTime - steps)
    onRewind(target)
  }

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <button
          onClick={() => quickRewind(100)}
          disabled={disabled || currentTime < 100}
          className="btn btn-secondary btn-sm flex items-center gap-1 flex-1"
          title="倒带100步"
        >
          <RotateCcw size={14} />
          -100
        </button>
        
        <button
          onClick={() => quickRewind(1000)}
          disabled={disabled || currentTime < 1000}
          className="btn btn-secondary btn-sm flex items-center gap-1 flex-1"
          title="倒带1000步"
        >
          <RotateCcw size={14} />
          -1K
        </button>
        
        <button
          onClick={() => setShowJumpInput(!showJumpInput)}
          disabled={disabled}
          className="btn btn-secondary btn-sm"
          title="精确跳转"
        >
          <FastForward size={14} />
        </button>
      </div>

      {showJumpInput && (
        <div className="flex gap-2">
          <input
            type="number"
            value={jumpTarget}
            onChange={(e) => setJumpTarget(e.target.value)}
            placeholder={currentTime.toString()}
            className="input flex-1 text-sm"
            min="0"
          />
          <button
            onClick={handleJump}
            className="btn btn-primary btn-sm"
          >
            跳转
          </button>
        </div>
      )}
    </div>
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
