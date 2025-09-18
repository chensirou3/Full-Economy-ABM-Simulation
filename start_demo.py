#!/usr/bin/env python3
"""
ABM 经济体模拟系统完整演示启动脚本
一键启动完整系统演示
"""

import os
import sys
import time
import subprocess
import threading
import signal
from pathlib import Path


def print_banner():
    """打印启动横幅"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║        🚀 ABM 经济体模拟系统 - 完整演示启动器                    ║
    ║                                                              ║
    ║  • 后端 API 服务器    http://localhost:8000                    ║
    ║  • World Viewer      http://localhost:3000                   ║  
    ║  • Control Tower     http://localhost:3001                   ║
    ║                                                              ║
    ║  按 Ctrl+C 退出所有服务                                         ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """检查依赖"""
    print("🔍 检查系统依赖...")
    
    # 检查 Python
    if sys.version_info < (3, 11):
        print("❌ 需要 Python 3.11 或更高版本")
        return False
    
    # 检查 Node.js
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, text=True, check=True)
        node_version = result.stdout.strip()
        print(f"✅ Node.js {node_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ 需要安装 Node.js 18+")
        return False
    
    # 检查项目文件
    required_files = [
        'backend/pyproject.toml',
        'frontend/world-viewer/package.json',
        'frontend/control-tower/package.json',
        'scenarios/baseline.yml'
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"❌ 缺少必要文件: {file_path}")
            return False
    
    print("✅ 依赖检查通过")
    return True


def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖...")
    
    # 安装后端依赖
    print("  安装 Python 依赖...")
    try:
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-e', '.[dev]'
        ], cwd='backend', check=True, capture_output=True)
        print("  ✅ Python 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Python 依赖安装失败: {e}")
        return False
    
    # 安装前端依赖
    frontend_dirs = ['frontend/world-viewer', 'frontend/control-tower']
    
    for frontend_dir in frontend_dirs:
        print(f"  安装 {frontend_dir} 依赖...")
        try:
            subprocess.run(['npm', 'install'], 
                         cwd=frontend_dir, check=True, capture_output=True)
            print(f"  ✅ {frontend_dir} 依赖安装完成")
        except subprocess.CalledProcessError as e:
            print(f"  ❌ {frontend_dir} 依赖安装失败: {e}")
            return False
    
    return True


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.processes = []
        self.running = True
    
    def start_service(self, name, cmd, cwd=None, env=None):
        """启动服务"""
        print(f"🚀 启动 {name}...")
        
        try:
            # 合并环境变量
            service_env = os.environ.copy()
            if env:
                service_env.update(env)
            
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=service_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.processes.append((name, process))
            
            # 启动输出监控线程
            threading.Thread(
                target=self._monitor_output,
                args=(name, process),
                daemon=True
            ).start()
            
            return process
            
        except Exception as e:
            print(f"❌ 启动 {name} 失败: {e}")
            return None
    
    def _monitor_output(self, name, process):
        """监控服务输出"""
        while self.running and process.poll() is None:
            try:
                output = process.stdout.readline()
                if output:
                    # 过滤重要信息
                    if any(keyword in output.lower() for keyword in 
                          ['error', 'failed', 'exception', 'started', 'listening']):
                        print(f"[{name}] {output.strip()}")
                
                # 检查错误输出
                if process.stderr.readable():
                    error = process.stderr.readline()
                    if error and 'error' in error.lower():
                        print(f"[{name}] ERROR: {error.strip()}")
                        
            except Exception:
                break
    
    def stop_all(self):
        """停止所有服务"""
        print("\n🛑 正在停止所有服务...")
        self.running = False
        
        for name, process in self.processes:
            if process.poll() is None:
                print(f"  停止 {name}...")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    print(f"  停止 {name} 时出错: {e}")
        
        print("✅ 所有服务已停止")


def wait_for_service(url, timeout=60):
    """等待服务启动"""
    import requests
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(1)
    
    return False


def main():
    """主函数"""
    print_banner()
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装必要的依赖")
        sys.exit(1)
    
    # 询问是否安装依赖
    install_deps = input("\n📦 是否需要安装/更新依赖? (y/n): ").lower().strip()
    if install_deps in ['y', 'yes', '']:
        if not install_dependencies():
            print("\n❌ 依赖安装失败")
            sys.exit(1)
    
    # 创建服务管理器
    service_manager = ServiceManager()
    
    # 设置信号处理
    def signal_handler(sig, frame):
        service_manager.stop_all()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动后端服务
        backend_process = service_manager.start_service(
            "Backend API",
            [sys.executable, 'run_demo.py', 'api'],
            cwd='backend'
        )
        
        if not backend_process:
            print("❌ 后端服务启动失败")
            return
        
        print("⏳ 等待后端服务启动...")
        time.sleep(5)
        
        # 检查后端是否启动成功
        if not wait_for_service('http://localhost:8000/health', timeout=30):
            print("❌ 后端服务启动超时")
            service_manager.stop_all()
            return
        
        print("✅ 后端服务已启动: http://localhost:8000")
        
        # 启动 World Viewer
        world_viewer_process = service_manager.start_service(
            "World Viewer",
            ['npm', 'run', 'dev'],
            cwd='frontend/world-viewer'
        )
        
        # 启动 Control Tower
        control_tower_process = service_manager.start_service(
            "Control Tower",
            ['npm', 'run', 'dev'],
            cwd='frontend/control-tower'
        )
        
        # 等待前端服务启动
        print("⏳ 等待前端服务启动...")
        time.sleep(10)
        
        # 显示访问信息
        print("\n🎉 所有服务已启动！")
        print("\n📊 访问地址:")
        print("  • API 文档:      http://localhost:8000/docs")
        print("  • World Viewer:  http://localhost:3000")
        print("  • Control Tower: http://localhost:3001")
        
        print("\n💡 使用提示:")
        print("  1. 打开 Control Tower 查看实时指标和控制模拟")
        print("  2. 打开 World Viewer 查看 2D 世界地图")
        print("  3. 使用播放/暂停/步进/倒带等时间控制功能")
        print("  4. 尝试加载不同的场景配置")
        
        print("\n🔄 系统运行中... (按 Ctrl+C 退出)")
        
        # 保持运行
        while True:
            time.sleep(1)
            
            # 检查进程状态
            for name, process in service_manager.processes:
                if process.poll() is not None:
                    print(f"⚠️  {name} 意外退出")
    
    except KeyboardInterrupt:
        print("\n👋 收到退出信号")
    except Exception as e:
        print(f"\n❌ 运行时错误: {e}")
    finally:
        service_manager.stop_all()


if __name__ == "__main__":
    main()
