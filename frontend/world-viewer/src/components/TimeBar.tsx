/**
 * 时间控制条组件
 * 提供播放控制和时间轴显示
 */

import React, { useState } from 'react'
import { 
  Play, 
  Pause, 
  Square, 
  SkipForward, 
  RotateCcw, 
  FastForward,
  Calendar,
  Clock
} from 'lucide-react'
import { useSimulationStatus } from '../store/simulationStore'
import { useSimulationControl } from '../hooks/useSimulationControl'

export const TimeBar: React.FC = () => {
  const simulationStatus = useSimulationStatus()
  const { play, pause, step, rewind, jump, setSpeed, isLoading } = useSimulationControl()
  
  const [jumpTarget, setJumpTarget] = useState('')
  const [showJumpInput, setShowJumpInput] = useState(false)
  
  const isRunning = simulationStatus?.state === 'running'
  const isPaused = simulationStatus?.state === 'paused'
  const currentTime = simulationStatus?.current_time || 0
  
  const handleJump = () => {
    const target = parseInt(jumpTarget)
    if (!isNaN(target) && target >= 0) {
      if (target < currentTime) {
        rewind(target)
      } else {
        jump(target)
      }
      setJumpTarget('')
      setShowJumpInput(false)
    }
  }

  const speedOptions = [0.1, 0.25, 0.5, 1, 2, 5, 10]

  return (
    <div className="time-bar h-16 bg-gray-800 border-t border-gray-700 px-6 flex items-center justify-between">
      {/* 左侧：播放控制 */}
      <div className="flex items-center gap-3">
        {/* 播放/暂停 */}
        {isRunning ? (
          <button
            onClick={pause}
            disabled={isLoading}
            className="btn btn-primary flex items-center gap-2"
            title="暂停"
          >
            <Pause size={18} />
            暂停
          </button>
        ) : (
          <button
            onClick={() => play()}
            disabled={isLoading}
            className="btn btn-primary flex items-center gap-2"
            title="播放"
          >
            <Play size={18} />
            播放
          </button>
        )}

        {/* 单步 */}
        <button
          onClick={() => step(1)}
          disabled={isLoading || isRunning}
          className="btn btn-secondary"
          title="单步执行"
        >
          <SkipForward size={18} />
        </button>

        {/* 倒带 */}
        <button
          onClick={() => rewind(Math.max(0, currentTime - 100))}
          disabled={isLoading || currentTime === 0}
          className="btn btn-secondary"
          title="倒带100步"
        >
          <RotateCcw size={18} />
        </button>

        {/* 跳转 */}
        <div className="relative">
          <button
            onClick={() => setShowJumpInput(!showJumpInput)}
            disabled={isLoading}
            className="btn btn-secondary"
            title="时间跳转"
          >
            <FastForward size={18} />
          </button>
          
          {showJumpInput && (
            <div className="absolute bottom-full left-0 mb-2 p-3 bg-gray-900 border border-gray-600 rounded shadow-lg">
              <div className="flex items-center gap-2 mb-2">
                <Calendar size={16} />
                <span className="text-sm">跳转到时间:</span>
              </div>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={jumpTarget}
                  onChange={(e) => setJumpTarget(e.target.value)}
                  placeholder={currentTime.toString()}
                  className="input w-24 text-sm"
                  min="0"
                />
                <button
                  onClick={handleJump}
                  className="btn btn-sm btn-primary"
                >
                  跳转
                </button>
                <button
                  onClick={() => setShowJumpInput(false)}
                  className="btn btn-sm btn-secondary"
                >
                  取消
                </button>
              </div>
            </div>
          )}
        </div>

        {/* 速度控制 */}
        <div className="flex items-center gap-2 ml-4">
          <span className="text-sm text-gray-400">速度:</span>
          <select
            value={simulationStatus?.speed || 1}
            onChange={(e) => setSpeed(parseFloat(e.target.value))}
            disabled={isLoading}
            className="select text-sm"
          >
            {speedOptions.map(speed => (
              <option key={speed} value={speed}>
                {speed}x
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* 中间：时间显示 */}
      <div className="flex items-center gap-6">
        <div className="text-center">
          <div className="text-xs text-gray-400">当前时间</div>
          <div className="text-lg font-mono font-bold text-white">
            {currentTime.toLocaleString()}
          </div>
        </div>

        {simulationStatus && (
          <div className="text-center">
            <div className="text-xs text-gray-400">性能</div>
            <div className="text-sm font-mono text-green-400">
              {simulationStatus.steps_per_second.toFixed(1)} steps/s
            </div>
          </div>
        )}
      </div>

      {/* 右侧：状态指示 */}
      <div className="flex items-center gap-4">
        {simulationStatus && (
          <>
            <div className="text-center">
              <div className="text-xs text-gray-400">状态</div>
              <div className={`text-sm font-medium ${getStatusColor(simulationStatus.state)}`}>
                {getStatusText(simulationStatus.state)}
              </div>
            </div>

            <div className="text-center">
              <div className="text-xs text-gray-400">代理数</div>
              <div className="text-sm font-mono text-blue-400">
                {simulationStatus.total_agents.toLocaleString()}
              </div>
            </div>
          </>
        )}

        {isLoading && (
          <div className="flex items-center gap-2 text-yellow-400">
            <div className="loading-spinner"></div>
            <span className="text-sm">处理中...</span>
          </div>
        )}
      </div>
    </div>
  )
}

// 工具函数
function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    running: 'text-green-400',
    paused: 'text-yellow-400',
    stopped: 'text-red-400',
    stepping: 'text-blue-400',
    rewinding: 'text-purple-400',
  }
  return colors[status] || 'text-gray-400'
}

function getStatusText(status: string): string {
  const texts: Record<string, string> = {
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    stepping: '步进中',
    rewinding: '回放中',
  }
  return texts[status] || status
}
