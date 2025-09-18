/**
 * World Viewer 主组件
 * 使用 PixiJS 渲染 2D 世界视图
 */

import React, { useRef, useEffect, useState } from 'react'
import { Application, Container, Graphics, Text, TextStyle } from 'pixi.js'
import { useSimulationStore, useAgents, useCamera } from '../store/simulationStore'
import { LayerToggles } from './LayerToggles'
import { MapCanvas } from './MapCanvas'

export const WorldViewer: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const appRef = useRef<Application | null>(null)
  const [isInitialized, setIsInitialized] = useState(false)
  
  const agents = useAgents()
  const camera = useCamera()
  const { selectAgent, updateCamera } = useSimulationStore()

  // 初始化 PixiJS 应用
  useEffect(() => {
    if (!canvasRef.current || appRef.current) return

    const initPixiApp = async () => {
      try {
        const app = new Application()
        
        await app.init({
          canvas: canvasRef.current!,
          width: window.innerWidth * 0.75, // 75% 宽度，留给侧边栏
          height: window.innerHeight - 120, // 减去头部和时间条高度
          backgroundColor: 0x1a1a1a,
          antialias: true,
        })

        appRef.current = app
        setIsInitialized(true)

        // 创建主容器
        const worldContainer = new Container()
        app.stage.addChild(worldContainer)

        // 添加网格背景
        const gridGraphics = new Graphics()
        drawGrid(gridGraphics, 100, 100, 20) // 100x100 网格，每格20像素
        worldContainer.addChild(gridGraphics)

        // 添加代理容器
        const agentsContainer = new Container()
        worldContainer.addChild(agentsContainer)

        // 设置相机控制
        setupCameraControls(app, worldContainer, updateCamera)

        console.log('PixiJS 应用初始化成功')
      } catch (error) {
        console.error('PixiJS 初始化失败:', error)
      }
    }

    initPixiApp()

    return () => {
      if (appRef.current) {
        appRef.current.destroy()
        appRef.current = null
      }
    }
  }, [updateCamera])

  // 渲染代理
  useEffect(() => {
    if (!appRef.current || !isInitialized) return

    const app = appRef.current
    const worldContainer = app.stage.children[0] as Container
    const agentsContainer = worldContainer.children[1] as Container

    // 清除现有代理
    agentsContainer.removeChildren()

    // 渲染新代理
    agents.forEach(agent => {
      const sprite = createAgentSprite(agent)
      if (sprite) {
        agentsContainer.addChild(sprite)
      }
    })

    console.log(`渲染了 ${agents.length} 个代理`)
  }, [agents, isInitialized])

  // 应用相机变换
  useEffect(() => {
    if (!appRef.current || !isInitialized) return

    const app = appRef.current
    const worldContainer = app.stage.children[0] as Container

    worldContainer.position.set(camera.x, camera.y)
    worldContainer.scale.set(camera.zoom)
  }, [camera, isInitialized])

  return (
    <div className="world-viewer relative w-full h-full bg-gray-900">
      {/* 图层控制 */}
      <div className="absolute top-4 left-4 z-10">
        <LayerToggles />
      </div>

      {/* PixiJS 画布 */}
      <canvas
        ref={canvasRef}
        className="absolute inset-0"
        style={{ cursor: 'grab' }}
      />

      {/* 加载状态 */}
      {!isInitialized && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <div className="text-center text-white">
            <div className="loading-spinner mb-2"></div>
            <div>正在初始化世界视图...</div>
          </div>
        </div>
      )}

      {/* 相机信息 */}
      <div className="absolute bottom-4 left-4 text-xs text-gray-400 bg-black bg-opacity-50 px-2 py-1 rounded">
        位置: ({camera.x.toFixed(0)}, {camera.y.toFixed(0)}) | 缩放: {camera.zoom.toFixed(2)}x
      </div>
    </div>
  )
}

// 绘制网格背景
function drawGrid(graphics: Graphics, rows: number, cols: number, cellSize: number) {
  graphics.clear()
  graphics.stroke({ color: 0x333333, width: 1 })

  // 绘制垂直线
  for (let i = 0; i <= cols; i++) {
    const x = i * cellSize
    graphics.moveTo(x, 0)
    graphics.lineTo(x, rows * cellSize)
  }

  // 绘制水平线
  for (let i = 0; i <= rows; i++) {
    const y = i * cellSize
    graphics.moveTo(0, y)
    graphics.lineTo(cols * cellSize, y)
  }

  graphics.stroke()
}

// 创建代理精灵
function createAgentSprite(agent: any): Graphics | null {
  const sprite = new Graphics()
  
  // 根据代理类型设置颜色和形状
  const config = getAgentVisualConfig(agent.agent_type)
  if (!config) return null

  sprite.circle(0, 0, config.radius)
  sprite.fill(config.color)
  
  // 如果有状态指示，添加边框
  if (agent.status !== 'active') {
    sprite.circle(0, 0, config.radius + 2)
    sprite.stroke({ color: getStatusColor(agent.status), width: 2 })
  }

  // 设置位置
  sprite.position.set(agent.position.x * 20, agent.position.y * 20) // 20像素每格

  // 添加交互
  sprite.eventMode = 'static'
  sprite.cursor = 'pointer'
  sprite.on('click', () => {
    console.log('选中代理:', agent.agent_id)
    // TODO: 调用选择代理的函数
  })

  return sprite
}

// 获取代理视觉配置
function getAgentVisualConfig(agentType: string) {
  const configs: Record<string, { color: number; radius: number }> = {
    person: { color: 0x4ade80, radius: 3 },      // 绿色圆点
    firm: { color: 0x3b82f6, radius: 5 },        // 蓝色方块
    bank: { color: 0xf59e0b, radius: 6 },        // 橙色菱形
    central_bank: { color: 0xef4444, radius: 8 }, // 红色星形
  }
  
  return configs[agentType] || null
}

// 获取状态颜色
function getStatusColor(status: string): number {
  const colors: Record<string, number> = {
    active: 0x10b981,
    inactive: 0x6b7280,
    bankrupt: 0xef4444,
    deceased: 0x1f2937,
  }
  
  return colors[status] || 0x6b7280
}

// 设置相机控制
function setupCameraControls(
  app: Application, 
  worldContainer: Container, 
  updateCamera: (camera: any) => void
) {
  let isDragging = false
  let dragStart = { x: 0, y: 0 }
  let lastPosition = { x: 0, y: 0 }

  // 鼠标拖拽
  app.canvas.addEventListener('mousedown', (e) => {
    isDragging = true
    dragStart = { x: e.clientX, y: e.clientY }
    lastPosition = { x: worldContainer.x, y: worldContainer.y }
    app.canvas.style.cursor = 'grabbing'
  })

  app.canvas.addEventListener('mousemove', (e) => {
    if (!isDragging) return

    const deltaX = e.clientX - dragStart.x
    const deltaY = e.clientY - dragStart.y

    const newX = lastPosition.x + deltaX
    const newY = lastPosition.y + deltaY

    updateCamera({ x: newX, y: newY })
  })

  app.canvas.addEventListener('mouseup', () => {
    isDragging = false
    app.canvas.style.cursor = 'grab'
  })

  // 鼠标滚轮缩放
  app.canvas.addEventListener('wheel', (e) => {
    e.preventDefault()
    
    const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1
    const currentZoom = worldContainer.scale.x
    const newZoom = Math.max(0.1, Math.min(5, currentZoom * zoomFactor))

    updateCamera({ zoom: newZoom })
  })
}
