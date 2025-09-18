.PHONY: dev backend-dev frontend-dev install test lint clean

# 开发环境启动
dev: install
	@echo "启动 ABM 经济体模拟系统..."
	@make -j3 backend-dev frontend-world-viewer-dev frontend-control-tower-dev

# 后端开发
backend-dev:
	@echo "启动后端 API 服务器..."
	cd backend && python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 前端开发 - World Viewer
frontend-world-viewer-dev:
	@echo "启动 World Viewer 前端..."
	cd frontend/world-viewer && npm run dev

# 前端开发 - Control Tower  
frontend-control-tower-dev:
	@echo "启动 Control Tower 前端..."
	cd frontend/control-tower && npm run dev

# 安装依赖
install: install-backend install-frontend

install-backend:
	@echo "安装后端依赖..."
	cd backend && pip install -e ".[dev]"

install-frontend:
	@echo "安装前端依赖..."
	cd frontend/world-viewer && npm install
	cd frontend/control-tower && npm install

# 测试
test: test-backend test-frontend

test-backend:
	@echo "运行后端测试..."
	cd backend && pytest tests/ -v

test-frontend:
	@echo "运行前端测试..."
	cd frontend/world-viewer && npm test
	cd frontend/control-tower && npm test

# 代码检查
lint: lint-backend lint-frontend

lint-backend:
	@echo "后端代码检查..."
	cd backend && ruff check . && black --check . && mypy .

lint-frontend:
	@echo "前端代码检查..."
	cd frontend/world-viewer && npm run lint
	cd frontend/control-tower && npm run lint

# 格式化代码
format:
	cd backend && ruff format . && black .
	cd frontend/world-viewer && npm run format
	cd frontend/control-tower && npm run format

# 构建生产版本
build:
	@echo "构建生产版本..."
	cd frontend/world-viewer && npm run build
	cd frontend/control-tower && npm run build

# 清理
clean:
	@echo "清理构建文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

# 生成类型定义
generate-types:
	@echo "生成 TypeScript 类型定义..."
	cd backend && python tools/generate_schemas.py
	cd frontend/world-viewer && npm run codegen
	cd frontend/control-tower && npm run codegen

# 创建新场景
new-scenario:
	@echo "创建新场景配置..."
	python tools/scripts/make_scenario.py

# Docker 构建
docker-build:
	docker build -t abm-sim:latest .

# Docker 运行
docker-run:
	docker run -p 8000:8000 -p 3000:3000 -p 3001:3001 abm-sim:latest
