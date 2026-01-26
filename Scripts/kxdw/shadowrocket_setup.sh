#!/bin/bash
# Shadowrocket代理配置脚本

echo "============================================================"
echo "Shadowrocket 代理配置指南"
echo "============================================================"
echo ""

# 检测常见端口
echo "🔍 检测Shadowrocket代理端口..."
echo ""

# 检测7890端口（HTTP代理）
if lsof -i :7890 > /dev/null 2>&1; then
    echo "✅ 检测到端口 7890 (HTTP代理)"
    echo "   代理地址: http://127.0.0.1:7890"
    echo ""
    echo "📋 使用方法:"
    echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:7890"
    echo ""
    # 自动创建proxies.txt
    echo "http://127.0.0.1:7890" > proxies.txt
    echo "✅ 已自动创建 proxies.txt 文件"
    exit 0
fi

# 检测1080端口（SOCKS5代理）
if lsof -i :1080 > /dev/null 2>&1; then
    echo "✅ 检测到端口 1080 (SOCKS5代理)"
    echo "   代理地址: socks5://127.0.0.1:1080"
    echo ""
    echo "📋 使用方法:"
    echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy socks5://127.0.0.1:1080"
    echo ""
    # 自动创建proxies.txt
    echo "socks5://127.0.0.1:1080" > proxies.txt
    echo "✅ 已自动创建 proxies.txt 文件"
    exit 0
fi

echo "❌ 未检测到Shadowrocket代理端口"
echo ""
echo "💡 如何查看Shadowrocket代理端口:"
echo "   1. 打开Shadowrocket应用"
echo "   2. 点击右下角'设置'图标"
echo "   3. 找到'本地代理'或'HTTP代理'设置"
echo "   4. 查看端口号（通常是7890）"
echo ""
echo "📋 手动配置方法:"
echo "   1. 创建proxies.txt文件:"
echo "      echo 'http://127.0.0.1:7890' > proxies.txt"
echo ""
echo "   2. 运行脚本:"
echo "      python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt"
echo ""
echo "   或者直接使用命令行参数:"
echo "      python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:7890"
echo ""

