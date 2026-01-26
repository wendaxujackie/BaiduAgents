#!/bin/bash
# -*- coding: utf-8 -*-
# iOS自动化一键启动脚本
# 使用方法: ./start_ios_automation.sh

set -e

# 加载 nvm 并切换到正确的 Node.js 版本
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20.19.0 >/dev/null 2>&1 || nvm use default >/dev/null 2>&1

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
UDID="00008101-000835600E78001E"
WDA_PORT=8100
APPIUM_PORT=4723
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}  iOS快手自动化 - 一键启动${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# 函数：检查端口是否被占用
check_port() {
    lsof -i :$1 > /dev/null 2>&1
    return $?
}

# 函数：等待服务就绪
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 1
        attempt=$((attempt + 1))
    done
    return 1
}

# 步骤1: 检查并启动iproxy
echo -e "${YELLOW}[1/4] 检查iproxy端口转发...${NC}"
pkill -f "iproxy $WDA_PORT" 2>/dev/null || true
sleep 1

iproxy $WDA_PORT $WDA_PORT -u $UDID > /tmp/iproxy.log 2>&1 &
IPROXY_PID=$!
sleep 2

if ps -p $IPROXY_PID > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ iproxy已启动 (PID: $IPROXY_PID)${NC}"
else
    echo -e "${RED}   ❌ iproxy启动失败，请检查设备连接${NC}"
    exit 1
fi

# 步骤2: 检查并启动Appium
echo -e "${YELLOW}[2/4] 检查Appium服务器...${NC}"
if check_port $APPIUM_PORT; then
    echo -e "${GREEN}   ✅ Appium已在运行${NC}"
else
    echo -e "${BLUE}   正在启动Appium...${NC}"
    pkill -f "appium" 2>/dev/null || true
    sleep 1
    # 确保使用正确的 Node.js 版本启动 Appium
    source ~/.nvm/nvm.sh 2>/dev/null || true
    nvm use 20.19.0 >/dev/null 2>&1 || true
    nohup appium --relaxed-security > /tmp/appium.log 2>&1 &
    sleep 3
    
    if wait_for_service "http://127.0.0.1:$APPIUM_PORT/status" "Appium"; then
        echo -e "${GREEN}   ✅ Appium启动成功${NC}"
    else
        echo -e "${RED}   ❌ Appium启动失败${NC}"
        exit 1
    fi
fi

# 步骤3: 检查WDA
echo -e "${YELLOW}[3/4] 检查WebDriverAgent...${NC}"
if curl -s "http://127.0.0.1:$WDA_PORT/status" 2>/dev/null | grep -q "ready"; then
    echo -e "${GREEN}   ✅ WDA已就绪${NC}"
else
    echo -e "${RED}   ⚠️  WDA未运行！${NC}"
    echo ""
    echo -e "${YELLOW}   请在Xcode中手动启动WDA：${NC}"
    echo -e "   1. 打开Xcode中的WebDriverAgent项目"
    echo -e "   2. 选择 WebDriverAgentRunner scheme"
    echo -e "   3. 选择你的iPhone设备"
    echo -e "   4. 按 ${GREEN}Cmd + U${NC} 运行测试"
    echo -e "   5. 等待看到 ServerURLHere->http://... 输出"
    echo ""
    
    # 打开WDA项目 - 尝试多个可能的路径
    echo -e "${BLUE}   正在查找WDA项目...${NC}"
    
    # 可能的WDA路径列表
    WDA_PATHS=(
        "$HOME/.appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj"
        "$(npm root -g)/appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj"
        "$(npm root -g)/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj"
        "$HOME/.nvm/versions/node/$(node -v | sed 's/v//')/lib/node_modules/appium/node_modules/appium-xcuitest-driver/node_modules/appium-webdriveragent/WebDriverAgent.xcodeproj"
    )
    
    WDA_FOUND=false
    for wda_path in "${WDA_PATHS[@]}"; do
        if [ -d "$wda_path" ]; then
            echo -e "${GREEN}   找到WDA项目: $wda_path${NC}"
            open "$wda_path" 2>/dev/null && WDA_FOUND=true && break
        fi
    done
    
    if [ "$WDA_FOUND" = false ]; then
        echo -e "${YELLOW}   ⚠️  未找到WDA项目，请手动安装：${NC}"
        echo -e "   1. 运行: ${BLUE}appium driver install xcuitest${NC}"
        echo -e "   2. 或者从GitHub克隆: ${BLUE}git clone https://github.com/appium/WebDriverAgent.git${NC}"
        echo -e "   3. 然后在Xcode中打开 WebDriverAgent.xcodeproj"
    fi
    
    echo -e "${YELLOW}   按回车键继续（确保WDA已运行）...${NC}"
    read -r
    
    # 再次检查
    if curl -s "http://127.0.0.1:$WDA_PORT/status" 2>/dev/null | grep -q "ready"; then
        echo -e "${GREEN}   ✅ WDA已就绪${NC}"
    else
        echo -e "${RED}   ❌ WDA仍未运行，请检查Xcode${NC}"
        exit 1
    fi
fi

# 步骤4: 运行自动化脚本
echo -e "${YELLOW}[4/4] 启动自动化脚本...${NC}"
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  所有服务已就绪，开始自动化！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

cd "$SCRIPT_DIR"
source venv/bin/activate
python3 main.py --mode mobile --platform ios

# 清理
echo ""
echo -e "${BLUE}自动化完成！${NC}"
