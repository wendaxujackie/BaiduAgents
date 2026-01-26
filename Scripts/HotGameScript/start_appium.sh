#!/bin/bash
# -*- coding: utf-8 -*-
# ============================================
# Appium服务启动脚本 (Mac/Linux)
# 用于移动端自动化
# ============================================

# 加载 nvm 并切换到正确的 Node.js 版本
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20.19.0 >/dev/null 2>&1 || nvm use default >/dev/null 2>&1

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              Appium 服务启动脚本                         ║"
echo "║              用于iOS/Android自动化                       ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查Appium是否安装
if ! command -v appium &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} Appium未安装！"
    echo ""
    echo "请先安装Appium:"
    echo "  1. 安装Node.js: brew install node"
    echo "  2. 安装Appium: npm install -g appium"
    echo "  3. 安装驱动:"
    echo "     - Android: appium driver install uiautomator2"
    echo "     - iOS: appium driver install xcuitest"
    echo ""
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Appium版本: $(appium --version)"
echo ""

# 检查端口是否被占用
PORT=4723
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}[WARNING]${NC} 端口 $PORT 已被占用"
    PID=$(lsof -ti :$PORT)
    echo -e "${YELLOW}[WARNING]${NC} 进程ID: $PID"
    echo ""
    read -p "是否关闭已有的Appium实例? (Y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        kill -9 $PID 2>/dev/null
        sleep 2
        echo -e "${GREEN}[SUCCESS]${NC} 已关闭旧实例"
    else
        echo -e "${BLUE}[INFO]${NC} 使用已有的Appium实例"
        exit 0
    fi
fi

# 检查已安装的驱动
echo -e "${BLUE}[INFO]${NC} 已安装的驱动:"
appium driver list --installed 2>/dev/null || echo "  (无法获取驱动列表)"
echo ""

# 检查设备连接
echo -e "${BLUE}[INFO]${NC} 检查设备连接..."

# 检查Android设备
if command -v adb &> /dev/null; then
    ANDROID_DEVICES=$(adb devices 2>/dev/null | grep -v "List" | grep "device$" | wc -l | tr -d ' ')
    if [ "$ANDROID_DEVICES" -gt 0 ]; then
        echo -e "${GREEN}[SUCCESS]${NC} 检测到 $ANDROID_DEVICES 个Android设备"
        adb devices 2>/dev/null | grep "device$"
    else
        echo -e "${YELLOW}[WARNING]${NC} 未检测到Android设备"
    fi
else
    echo -e "${YELLOW}[WARNING]${NC} adb未安装，无法检测Android设备"
fi

# 检查iOS设备 (需要libimobiledevice)
if command -v idevice_id &> /dev/null; then
    IOS_DEVICES=$(idevice_id -l 2>/dev/null | wc -l | tr -d ' ')
    if [ "$IOS_DEVICES" -gt 0 ]; then
        echo -e "${GREEN}[SUCCESS]${NC} 检测到 $IOS_DEVICES 个iOS设备"
    else
        echo -e "${YELLOW}[WARNING]${NC} 未检测到iOS设备"
    fi
else
    echo -e "${YELLOW}[WARNING]${NC} libimobiledevice未安装，无法检测iOS设备"
    echo "  安装方法: brew install libimobiledevice"
fi

echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}[INFO]${NC} 正在启动Appium服务..."
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "  服务地址: http://localhost:4723"
echo "  按 Ctrl+C 停止服务"
echo ""
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# 启动Appium
appium --address 127.0.0.1 --port 4723 --relaxed-security
