/**
 * 应用头部组件
 */

import React from 'react'
import { Play, Pause, Square, SkipForward, RotateCcw, Settings } from 'lucide-react'
import { useSimulationStore } from '../store/simulationStore'
import { useSimulationControl } from '../hooks/useSimulationControl'

export const Header: React.FC = () => {
  const { simulationStatus, metrics } = useSimulationStore()
  const { play, pause, step, rewind, setSpeed, isLoading } = useSimulationControl()
  
  const [speedInput, setSpeedInput] = React.useState('1.0')
  
  const handleSpeedChange = (e: React.FormEvent) => {
    e.preventDefault()
    const speed = parseFloat(speedInput)
    if (speed > 0) {
      setSpeed(speed)
    }
  }
  
  const isRunning = simulationStatus?.state === 'running'
  const isPaused = simulationStatus?.state === 'paused'
  
  return (
    <header className="h-16 bg-gray-900 border-b border-gray-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-bold text-white">ABM 经济体模拟</h1>
        
        {simulationStatus && (
          <div className="flex items-center gap-2 text-sm text-gray-300">
            <span>时间: {simulationStatus.current_time.toLocaleString()}</span>
            <span>•</span>
            <span>代理: {simulationStatus.total_agents.toLocaleString()}</span>
            <span>•</span>
            <span>速度: {simulationStatus.speed}x</span>
          </div>
        )}
      </div>
      
      <div className="flex items-center gap-4">
        {/* 核心指标 */}
        {metrics && (
          <div className="flex items-center gap-4 text-sm">
            <div className="text-center">
              <div className="text-gray-400">GDP</div>
              <div className="font-mono">{metrics.kpis.gdp.toFixed(1)}B</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400">失业率</div>
              <div className="font-mono">{(metrics.kpis.unemployment * 100).toFixed(1)}%</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400">通胀</div>
              <div className="font-mono">{(metrics.kpis.inflation * 100).toFixed(1)}%</div>
            </div>
            <div className="text-center">
              <div className="text-gray-400">政策利率</div>
              <div className="font-mono">{(metrics.kpis.policy_rate * 100).toFixed(1)}%</div>
            </div>
          </div>
        )}
        
        <div className="h-8 w-px bg-gray-600" />
        
        {/* 控制按钮 */}
        <div className="flex items-center gap-2">
          {isRunning ? (
            <button
              onClick={pause}
              disabled={isLoading}
              className="btn btn-secondary flex items-center gap-2"
            >
              <Pause size={16} />
              暂停
            </button>
          ) : (
            <button
              onClick={play}
              disabled={isLoading}
              className="btn btn-primary flex items-center gap-2"
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
          
          <button
            onClick={() => rewind(Math.max(0, (simulationStatus?.current_time || 0) - 100))}
            disabled={isLoading || !simulationStatus || simulationStatus.current_time === 0}
            className="btn btn-secondary"
            title="倒带100步"
          >
            <RotateCcw size={16} />
          </button>
        </div>
        
        {/* 速度控制 */}
        <form onSubmit={handleSpeedChange} className="flex items-center gap-2">
          <label className="text-sm text-gray-400">速度:</label>
          <input
            type="number"
            value={speedInput}
            onChange={(e) => setSpeedInput(e.target.value)}
            min="0.1"
            max="10"
            step="0.1"
            className="input w-16 text-center"
          />
          <button type="submit" className="btn btn-sm btn-secondary">设置</button>
        </form>
        
        <button className="btn btn-secondary" title="设置">
          <Settings size={16} />
        </button>
      </div>
    </header>
  )
}
