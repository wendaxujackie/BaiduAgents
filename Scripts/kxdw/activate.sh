#!/bin/bash
# 激活虚拟环境的便捷脚本

cd "$(dirname "$0")"
source venv/bin/activate
echo "✅ 虚拟环境已激活"
echo "💡 使用 'deactivate' 退出虚拟环境"

