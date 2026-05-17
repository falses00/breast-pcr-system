#!/bin/bash
# Render 部署构建脚本

set -e

echo "=== 开始构建前端 ==="
cd frontend
npm install
npm run build
cd ..

echo "=== 开始安装后端依赖 ==="
cd backend
pip install -r requirements.txt
cd ..

echo "=== 构建完成 ==="
