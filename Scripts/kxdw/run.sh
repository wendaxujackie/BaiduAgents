#!/bin/bash
# 自动运行脚本 - 检查并激活虚拟环境

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境已创建"
fi

# 激活虚拟环境
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    
    # 检查依赖是否已安装
    if ! python -c "import pychrome" 2>/dev/null; then
        echo "📦 正在安装依赖包..."
        pip install -r requirements.txt -q
        echo "✅ 依赖包安装完成"
    fi
    
    # 运行脚本
    echo "🚀 运行爬虫脚本..."
    python3 kxdw_crawler.py "$@"
    
    # 退出虚拟环境
    deactivate
else
    echo "❌ 无法找到虚拟环境激活脚本"
    exit 1
fi

