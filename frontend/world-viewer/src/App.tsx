import React, { useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { WorldViewer } from './components/WorldViewer'
import { useSimulationStore } from './store/simulationStore'
import { useSimulationData } from './hooks/useSimulationData'
import { Header } from './components/Header'
import { SidePanel } from './components/SidePanel'
import { TimeBar } from './components/TimeBar'
import './App.css'

function App() {
  const { isConnected, connectionError } = useSimulationStore()
  
  // 启动数据同步
  const {
    isLoading,
    hasError,
    simulationStatus,
    currentMetrics,
  } = useSimulationData()

  // 在应用启动时显示加载状态
  if (isLoading && !simulationStatus && !currentMetrics) {
    return (
      <div className="app">
        <div className="flex items-center justify-center h-full">
          <div className="text-center text-white">
            <div className="loading-spinner mb-4 mx-auto"></div>
            <h2 className="text-xl font-semibold mb-2">正在连接模拟器...</h2>
            <p className="text-gray-400">请确保后端服务器正在运行</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="app">
        <Header />
        
        {connectionError && (
          <div className="error-banner">
            <span>连接错误: {connectionError}</span>
            <button 
              onClick={() => window.location.reload()} 
              className="ml-4 px-2 py-1 bg-red-700 rounded text-xs hover:bg-red-600"
            >
              重新连接
            </button>
          </div>
        )}
        
        {hasError && !isConnected && (
          <div className="error-banner">
            <span>⚠️ 无法连接到模拟器，请检查后端服务器是否正在运行</span>
            <a 
              href="http://localhost:8000/docs" 
              target="_blank" 
              rel="noopener noreferrer"
              className="ml-4 px-2 py-1 bg-blue-700 rounded text-xs hover:bg-blue-600"
            >
              查看 API 文档
            </a>
          </div>
        )}
        
        <div className="main-content">
          <div className="world-container">
            <Routes>
              <Route path="/" element={<WorldViewer />} />
            </Routes>
            <TimeBar />
          </div>
          
          <SidePanel />
        </div>
        
        <div className="status-bar">
          <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            {isConnected ? '已连接' : '未连接'}
          </span>
          
          {simulationStatus && (
            <>
              <span className="mx-2">•</span>
              <span className="text-xs">
                内存: {simulationStatus.memory_usage_mb.toFixed(1)} MB
              </span>
            </>
          )}
          
          {currentMetrics && (
            <>
              <span className="mx-2">•</span>
              <span className="text-xs">
                最后更新: {new Date(currentMetrics.timestamp * 1000).toLocaleTimeString()}
              </span>
            </>
          )}
        </div>
      </div>
    </Router>
  )
}

export default App