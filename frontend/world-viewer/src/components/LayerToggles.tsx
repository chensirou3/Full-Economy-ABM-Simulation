/**
 * 图层切换控制组件
 */

import React from 'react'
import { Eye, EyeOff, Users, Building, Landmark, TrendingDown, MapPin } from 'lucide-react'
import { useShowLayers, useSimulationStore } from '../store/simulationStore'

export const LayerToggles: React.FC = () => {
  const showLayers = useShowLayers()
  const { toggleLayer } = useSimulationStore()

  const layers = [
    {
      key: 'agents' as const,
      label: '所有代理',
      icon: Users,
      description: '显示/隐藏所有经济主体',
    },
    {
      key: 'population' as const,
      label: '人口',
      icon: Users,
      description: '显示/隐藏个人代理',
    },
    {
      key: 'firms' as const,
      label: '企业',
      icon: Building,
      description: '显示/隐藏企业代理',
    },
    {
      key: 'banks' as const,
      label: '银行',
      icon: Landmark,
      description: '显示/隐藏银行代理',
    },
    {
      key: 'unemployment' as const,
      label: '失业热力图',
      icon: TrendingDown,
      description: '显示失业率热力图',
    },
  ]

  return (
    <div className="panel w-64">
      <div className="panel-header">
        <div className="flex items-center gap-2">
          <MapPin size={16} />
          <span>图层控制</span>
        </div>
      </div>
      
      <div className="panel-content space-y-2">
        {layers.map((layer) => {
          const Icon = layer.icon
          const isVisible = showLayers[layer.key]
          
          return (
            <div
              key={layer.key}
              className="flex items-center justify-between p-2 rounded hover:bg-gray-800 cursor-pointer"
              onClick={() => toggleLayer(layer.key)}
              title={layer.description}
            >
              <div className="flex items-center gap-2">
                <Icon size={16} className="text-gray-400" />
                <span className="text-sm">{layer.label}</span>
              </div>
              
              <button className="text-gray-400 hover:text-white">
                {isVisible ? <Eye size={16} /> : <EyeOff size={16} />}
              </button>
            </div>
          )
        })}
        
        {/* 图例 */}
        <div className="mt-4 pt-4 border-t border-gray-700">
          <div className="text-xs text-gray-400 mb-2">图例</div>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span>个人</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-blue-400"></div>
              <span>企业</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-yellow-400"></div>
              <span>银行</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-red-400"></div>
              <span>央行</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
