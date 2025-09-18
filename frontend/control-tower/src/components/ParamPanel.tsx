/**
 * 参数控制面板
 */

import React from 'react'
import { Settings, Upload, Download, RotateCcw } from 'lucide-react'
import { useDashboardStore } from '../store/dashboardStore'
import { simulationApi } from '../api/simulation'

export const ParamPanel: React.FC = () => {
  const { scenarios, selectedScenario, setSelectedScenario } = useDashboardStore()
  const [isLoading, setIsLoading] = React.useState(false)

  const handleScenarioChange = async (scenarioName: string) => {
    if (!scenarioName || scenarioName === selectedScenario) return

    setIsLoading(true)
    try {
      await simulationApi.loadScenario(scenarioName)
      setSelectedScenario(scenarioName)
    } catch (error) {
      console.error('加载场景失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="dashboard-card">
      <div className="dashboard-card-header">
        <h3 className="dashboard-card-title flex items-center gap-2">
          <Settings size={20} />
          参数控制
        </h3>
      </div>
      
      <div className="dashboard-card-content space-y-4">
        {/* 场景选择 */}
        <div>
          <label className="block text-sm text-slate-400 mb-2">
            场景配置
          </label>
          <select
            value={selectedScenario || ''}
            onChange={(e) => handleScenarioChange(e.target.value)}
            disabled={isLoading}
            className="select w-full"
          >
            <option value="">选择场景...</option>
            {scenarios.map((scenario: any) => (
              <option key={scenario.name} value={scenario.name}>
                {scenario.name}
              </option>
            ))}
          </select>
          {selectedScenario && (
            <p className="text-xs text-slate-500 mt-1">
              当前场景: {selectedScenario}
            </p>
          )}
        </div>

        {/* 快速操作 */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-slate-300">快速操作</h4>
          
          <div className="grid grid-cols-1 gap-2">
            <button
              onClick={() => simulationApi.createSnapshot()}
              className="btn btn-secondary btn-sm flex items-center gap-2 justify-center"
            >
              <Download size={14} />
              创建快照
            </button>
            
            <button
              onClick={() => simulationApi.reset()}
              className="btn btn-danger btn-sm flex items-center gap-2 justify-center"
            >
              <RotateCcw size={14} />
              重置模拟
            </button>
          </div>
        </div>

        {/* 系统信息 */}
        <div className="pt-4 border-t border-slate-700">
          <h4 className="text-sm font-medium text-slate-300 mb-2">系统信息</h4>
          <div className="space-y-1 text-xs text-slate-400">
            <div>场景数量: {scenarios.length}</div>
            <div>API 版本: v1.0</div>
            <div>更新频率: 2秒</div>
          </div>
        </div>

        {isLoading && (
          <div className="flex items-center gap-2 text-yellow-400 text-sm">
            <div className="loading-spinner"></div>
            <span>正在加载...</span>
          </div>
        )}
      </div>
    </div>
  )
}
