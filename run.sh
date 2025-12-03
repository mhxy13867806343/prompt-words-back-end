#!/bin/bash

echo "启动提示词管理系统..."
echo ""
echo "请确保已安装依赖："
echo "  pip install -r requirements.txt"
echo ""
echo "请确保 PostgreSQL 和 Redis 已启动"
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
