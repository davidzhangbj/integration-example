#!/bin/bash

echo "=== FlinkOMT Demo 启动脚本 ==="
echo ""

# 检查 Node.js
if ! command -v node &> /dev/null; then
    echo "❌ 未找到 Node.js，请先安装 Node.js 18+"
    exit 1
fi

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python，请先安装 Python 3.11+"
    exit 1
fi

echo "✅ 环境检查通过"
echo ""

# 安装前端依赖
if [ ! -d "node_modules" ]; then
    echo "📦 正在安装前端依赖..."
    npm install
fi

# 安装后端依赖
if [ ! -d "venv" ]; then
    echo "📦 正在创建 Python 虚拟环境..."
    python3 -m venv venv
fi

echo "📦 正在安装后端依赖..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "🚀 启动服务..."
echo ""

# 启动后端（后台运行）
echo "启动后端服务 (http://localhost:5000)..."
python3 backend/app.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务 (http://localhost:3000)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 服务已启动！"
echo "前端: http://localhost:3000"
echo "后端: http://localhost:5000"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待中断信号
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM

# 等待进程
wait

