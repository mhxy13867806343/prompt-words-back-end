#!/bin/bash

echo "=== 重启 PostgreSQL 和 Redis ==="
echo ""

# 检查是否使用 Homebrew 安装
if command -v brew &> /dev/null; then
    echo "📦 使用 Homebrew 管理服务"
    echo ""
    
    # 重启 PostgreSQL
    echo "🔄 重启 PostgreSQL..."
    brew services restart postgresql@14 || brew services restart postgresql@15 || brew services restart postgresql
    
    echo ""
    
    # 重启 Redis
    echo "🔄 重启 Redis..."
    brew services restart redis
    
    echo ""
    echo "✅ 服务重启完成"
    echo ""
    
    # 查看服务状态
    echo "📊 服务状态："
    brew services list | grep -E "postgresql|redis"
else
    echo "❌ 未检测到 Homebrew"
    echo "请手动重启服务或使用其他方式"
fi
