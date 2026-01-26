#!/bin/bash
# Shadowrocket快速配置脚本

echo "============================================================"
echo "Shadowrocket 代理快速配置"
echo "============================================================"
echo ""

# 提示用户输入端口号
read -p "请输入Shadowrocket的HTTP代理端口（默认7890）: " port
port=${port:-7890}

echo ""
echo "✅ 配置完成！"
echo ""
echo "代理地址: http://127.0.0.1:$port"
echo ""

# 创建proxies.txt
echo "http://127.0.0.1:$port" > proxies.txt
echo "✅ 已创建 proxies.txt 文件"
echo ""

echo "📋 使用方法:"
echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt"
echo ""
echo "   或者直接使用:"
echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:$port"
echo ""
