/**
 * 主仪表板组件
 */

import React from 'react'
import { KPICards } from './KPICards'
import { EconomicCharts } from './Charts/EconomicCharts'
import { EventStream } from './EventStream'
import { ParamPanel } from './ParamPanel'
import { SystemStatus } from './SystemStatus'

export const Dashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      {/* 系统状态和参数控制 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <SystemStatus />
        </div>
        <div>
          <ParamPanel />
        </div>
      </div>

      {/* KPI 卡片 */}
      <KPICards />

      {/* 图表和事件流 */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2">
          <EconomicCharts />
        </div>
        <div>
          <EventStream />
        </div>
      </div>
    </div>
  )
}
