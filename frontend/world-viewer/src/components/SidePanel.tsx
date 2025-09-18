/**
 * 侧边面板组件
 * 显示选中代理的详细信息和系统状态
 */

import React from 'react'
import { useSelectedAgent, useSimulationStatus, useAgentCounts } from '../store/simulationStore'
import { User, Building, Landmark, Activity, DollarSign, TrendingUp } from 'lucide-react'

export const SidePanel: React.FC = () => {
  const selectedAgent = useSelectedAgent()
  const simulationStatus = useSimulationStatus()
  const agentCounts = useAgentCounts()

  return (
    <div className="side-panel w-80 h-full bg-gray-900 border-l border-gray-700 overflow-y-auto">
      {/* 系统状态 */}
      <div className="panel mb-4">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Activity size={16} />
            <span>系统状态</span>
          </div>
        </div>
        
        <div className="panel-content">
          {simulationStatus ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-400">状态:</span>
                <span className={`font-medium ${getStatusColor(simulationStatus.state)}`}>
                  {getStatusText(simulationStatus.state)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">时间:</span>
                <span>{simulationStatus.current_time.toLocaleString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">速度:</span>
                <span>{simulationStatus.speed}x</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">性能:</span>
                <span>{simulationStatus.steps_per_second.toFixed(1)} steps/s</span>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-sm">未连接到模拟器</div>
          )}
        </div>
      </div>

      {/* 代理统计 */}
      <div className="panel mb-4">
        <div className="panel-header">
          <div className="flex items-center gap-2">
            <Users size={16} />
            <span>代理统计</span>
          </div>
        </div>
        
        <div className="panel-content">
          <div className="space-y-2 text-sm">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <User size={14} className="text-green-400" />
                <span className="text-gray-400">个人:</span>
              </div>
              <span>{agentCounts.person?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Building size={14} className="text-blue-400" />
                <span className="text-gray-400">企业:</span>
              </div>
              <span>{agentCounts.firm?.toLocaleString() || 0}</span>
            </div>
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Landmark size={14} className="text-yellow-400" />
                <span className="text-gray-400">银行:</span>
              </div>
              <span>{agentCounts.bank?.toLocaleString() || 0}</span>
            </div>
            <div className="pt-2 border-t border-gray-700">
              <div className="flex justify-between font-medium">
                <span className="text-gray-400">总计:</span>
                <span>{agentCounts.total.toLocaleString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 选中代理信息 */}
      {selectedAgent ? (
        <div className="panel">
          <div className="panel-header">
            <div className="flex items-center gap-2">
              {getAgentIcon(selectedAgent.agent_type)}
              <span>代理详情</span>
            </div>
          </div>
          
          <div className="panel-content">
            <AgentDetails agent={selectedAgent} />
          </div>
        </div>
      ) : (
        <div className="panel">
          <div className="panel-header">
            <span>代理详情</span>
          </div>
          <div className="panel-content">
            <div className="text-gray-500 text-sm text-center py-4">
              点击地图上的代理查看详情
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// 代理详情组件
const AgentDetails: React.FC<{ agent: any }> = ({ agent }) => {
  return (
    <div className="space-y-4">
      {/* 基本信息 */}
      <div>
        <h4 className="text-sm font-medium mb-2">基本信息</h4>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between">
            <span className="text-gray-400">ID:</span>
            <span>{agent.agent_id}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">类型:</span>
            <span>{getAgentTypeText(agent.agent_type)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">状态:</span>
            <span className={getStatusColor(agent.status)}>
              {getAgentStatusText(agent.status)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-400">位置:</span>
            <span>({agent.position.x.toFixed(1)}, {agent.position.y.toFixed(1)})</span>
          </div>
        </div>
      </div>

      {/* 资产负债表 */}
      {agent.balance_sheet && (
        <div>
          <h4 className="text-sm font-medium mb-2 flex items-center gap-2">
            <DollarSign size={14} />
            资产负债表
          </h4>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">总资产:</span>
              <span className="text-green-400">
                ${agent.balance_sheet.total_assets.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">总负债:</span>
              <span className="text-red-400">
                ${agent.balance_sheet.total_liabilities.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between font-medium pt-1 border-t border-gray-700">
              <span className="text-gray-400">净资产:</span>
              <span className={agent.balance_sheet.net_worth >= 0 ? 'text-green-400' : 'text-red-400'}>
                ${agent.balance_sheet.net_worth.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* 特定类型信息 */}
      {agent.agent_type === 'person' && (
        <PersonDetails agent={agent} />
      )}
      {agent.agent_type === 'firm' && (
        <FirmDetails agent={agent} />
      )}
      {agent.agent_type === 'bank' && (
        <BankDetails agent={agent} />
      )}
    </div>
  )
}

// 个人详情
const PersonDetails: React.FC<{ agent: any }> = ({ agent }) => (
  <div>
    <h4 className="text-sm font-medium mb-2">个人信息</h4>
    <div className="space-y-1 text-xs">
      {agent.age && (
        <div className="flex justify-between">
          <span className="text-gray-400">年龄:</span>
          <span>{agent.age} 岁</span>
        </div>
      )}
      {agent.employment_status && (
        <div className="flex justify-between">
          <span className="text-gray-400">就业状态:</span>
          <span>{getEmploymentStatusText(agent.employment_status)}</span>
        </div>
      )}
      {agent.wage && (
        <div className="flex justify-between">
          <span className="text-gray-400">工资:</span>
          <span>${agent.wage.toLocaleString()}/年</span>
        </div>
      )}
    </div>
  </div>
)

// 企业详情
const FirmDetails: React.FC<{ agent: any }> = ({ agent }) => (
  <div>
    <h4 className="text-sm font-medium mb-2">企业信息</h4>
    <div className="space-y-1 text-xs">
      {agent.sector && (
        <div className="flex justify-between">
          <span className="text-gray-400">行业:</span>
          <span>{getSectorText(agent.sector)}</span>
        </div>
      )}
      {agent.num_employees !== undefined && (
        <div className="flex justify-between">
          <span className="text-gray-400">员工数:</span>
          <span>{agent.num_employees}</span>
        </div>
      )}
      {agent.current_output && (
        <div className="flex justify-between">
          <span className="text-gray-400">产出:</span>
          <span>{agent.current_output.toFixed(1)}</span>
        </div>
      )}
      {agent.price && (
        <div className="flex justify-between">
          <span className="text-gray-400">价格:</span>
          <span>${agent.price.toFixed(2)}</span>
        </div>
      )}
    </div>
  </div>
)

// 银行详情
const BankDetails: React.FC<{ agent: any }> = ({ agent }) => (
  <div>
    <h4 className="text-sm font-medium mb-2">银行信息</h4>
    <div className="space-y-1 text-xs">
      {agent.capital_ratio && (
        <div className="flex justify-between">
          <span className="text-gray-400">资本充足率:</span>
          <span className={agent.capital_ratio >= 0.08 ? 'text-green-400' : 'text-red-400'}>
            {(agent.capital_ratio * 100).toFixed(1)}%
          </span>
        </div>
      )}
      {agent.total_loans !== undefined && (
        <div className="flex justify-between">
          <span className="text-gray-400">贷款数量:</span>
          <span>{agent.total_loans}</span>
        </div>
      )}
      {agent.total_deposits && (
        <div className="flex justify-between">
          <span className="text-gray-400">存款总额:</span>
          <span>${agent.total_deposits.toLocaleString()}</span>
        </div>
      )}
    </div>
  </div>
)

// 工具函数
function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    running: 'text-green-400',
    paused: 'text-yellow-400',
    stopped: 'text-red-400',
    active: 'text-green-400',
    inactive: 'text-gray-400',
    bankrupt: 'text-red-400',
    deceased: 'text-gray-600',
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

function getAgentStatusText(status: string): string {
  const texts: Record<string, string> = {
    active: '活跃',
    inactive: '非活跃',
    bankrupt: '破产',
    deceased: '死亡',
  }
  return texts[status] || status
}

function getAgentTypeText(type: string): string {
  const texts: Record<string, string> = {
    person: '个人',
    household: '家庭',
    firm: '企业',
    bank: '银行',
    central_bank: '央行',
  }
  return texts[type] || type
}

function getEmploymentStatusText(status: string): string {
  const texts: Record<string, string> = {
    employed: '就业',
    unemployed: '失业',
    student: '学生',
    retired: '退休',
  }
  return texts[status] || status
}

function getSectorText(sector: string): string {
  const texts: Record<string, string> = {
    agri: '农业',
    mining: '采矿',
    manu: '制造业',
    services: '服务业',
    finance: '金融业',
    construction: '建筑业',
  }
  return texts[sector] || sector
}

function getAgentIcon(type: string) {
  const icons: Record<string, React.ReactElement> = {
    person: <User size={16} className="text-green-400" />,
    household: <User size={16} className="text-green-600" />,
    firm: <Building size={16} className="text-blue-400" />,
    bank: <Landmark size={16} className="text-yellow-400" />,
    central_bank: <Landmark size={16} className="text-red-400" />,
  }
  return icons[type] || <Activity size={16} />
}
