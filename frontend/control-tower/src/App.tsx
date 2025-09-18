import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { Dashboard } from './components/Dashboard'
import { Header } from './components/Header'
import { useDashboardData } from './hooks/useDashboardData'

function App() {
  const { isLoading, hasError, connectionError } = useDashboardData()

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="loading-spinner mb-4 mx-auto w-8 h-8"></div>
          <h2 className="text-xl font-semibold mb-2">正在加载控制塔...</h2>
          <p className="text-slate-400">连接到模拟器中</p>
        </div>
      </div>
    )
  }

  return (
    <Router>
      <div className="min-h-screen bg-slate-900">
        <Header />
        
        {connectionError && (
          <div className="bg-red-600 text-white px-4 py-2 text-sm">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <span>⚠️ 连接错误: {connectionError}</span>
              <button 
                onClick={() => window.location.reload()}
                className="px-3 py-1 bg-red-700 hover:bg-red-800 rounded text-xs transition-colors"
              >
                重新连接
              </button>
            </div>
          </div>
        )}
        
        {hasError && (
          <div className="bg-yellow-600 text-white px-4 py-2 text-sm">
            <div className="max-w-7xl mx-auto">
              <span>⚠️ 无法连接到模拟器，某些功能可能不可用</span>
            </div>
          </div>
        )}

        <main className="max-w-7xl mx-auto px-4 py-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
          </Routes>
        </main>
      </div>
    </Router>
  )
}

export default App
