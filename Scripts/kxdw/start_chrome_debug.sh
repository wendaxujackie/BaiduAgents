#!/bin/bash
# Chrome 调试模式启动脚本（使用空配置文件）

PORT=${1:-9222}
PROFILE_DIR="/tmp/chrome-debug-profile-${PORT}"

echo "🚀 启动 Chrome 调试模式..."
echo "   端口: ${PORT}"
echo "   配置文件目录: ${PROFILE_DIR}"

# 关闭可能存在的旧实例
echo "   正在关闭旧的 Chrome 调试实例..."
pkill -f "Google Chrome.*remote-debugging-port=${PORT}" 2>/dev/null || true
sleep 1

# 创建临时配置文件目录
mkdir -p "${PROFILE_DIR}"

# 启动 Chrome（后台运行，禁用代理）
echo "   正在启动 Chrome（禁用代理）..."
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
    --remote-debugging-port=${PORT} \
    --user-data-dir="${PROFILE_DIR}" \
    --no-proxy-server \
    > /dev/null 2>&1 &

# 等待 Chrome 启动
sleep 2

# 验证是否成功
if curl -s "http://127.0.0.1:${PORT}/json" > /dev/null 2>&1; then
    echo "✅ Chrome 调试模式已成功启动！"
    echo "   调试地址: http://127.0.0.1:${PORT}/json"
    echo ""
    echo "💡 提示:"
    echo "   - 配置文件保存在: ${PROFILE_DIR}"
    echo "   - 关闭 Chrome 后，配置文件会被保留"
    echo "   - 如需清理配置文件，执行: rm -rf ${PROFILE_DIR}"
    echo ""
    echo "🔍 验证连接:"
    echo "   curl http://127.0.0.1:${PORT}/json | head -20"
else
    echo "❌ Chrome 调试模式启动失败，请检查："
    echo "   1. Chrome 是否已安装"
    echo "   2. 端口 ${PORT} 是否被占用"
    echo "   3. 是否有权限访问 Chrome"
fi

