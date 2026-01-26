#!/bin/bash
# 启动Chrome调试模式

PORT=9222

# 检测操作系统
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME_PATH=$(which google-chrome || which chromium-browser || which chromium)
fi

if [ -z "$CHROME_PATH" ] || [ ! -f "$CHROME_PATH" ]; then
    echo "未找到Chrome浏览器"
    exit 1
fi

echo "启动Chrome调试模式 (端口: $PORT)..."
"$CHROME_PATH" --remote-debugging-port=$PORT &

echo "Chrome调试模式已启动"
echo "请在另一个终端运行自动化脚本"
