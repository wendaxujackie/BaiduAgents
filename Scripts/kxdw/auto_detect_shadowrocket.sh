#!/bin/bash
# 自动检测并配置Shadowrocket代理

echo "============================================================"
echo "自动检测Shadowrocket本地代理端口"
echo "============================================================"
echo ""

# 常见Shadowrocket端口
ports=(7890 8080 8888 1080 6152 6153)

found_proxy=""

for port in "${ports[@]}"; do
    echo -n "🔍 测试端口 $port... "
    
    # 先检查端口是否开放
    if ! lsof -i :$port > /dev/null 2>&1; then
        echo "❌ 端口未开放"
        continue
    fi
    
    # 测试HTTP代理
    response=$(curl -x http://127.0.0.1:$port -s --max-time 3 https://httpbin.org/ip 2>/dev/null)
    if [ $? -eq 0 ] && echo "$response" | grep -q "origin"; then
        ip=$(echo "$response" | grep -o '"origin":"[^"]*"' | cut -d'"' -f4)
        echo "✅ HTTP代理可用! 当前IP: $ip"
        found_proxy="http://127.0.0.1:$port"
        break
    fi
    
    # 测试SOCKS5代理
    response=$(curl --socks5 127.0.0.1:$port -s --max-time 3 https://httpbin.org/ip 2>/dev/null)
    if [ $? -eq 0 ] && echo "$response" | grep -q "origin"; then
        ip=$(echo "$response" | grep -o '"origin":"[^"]*"' | cut -d'"' -f4)
        echo "✅ SOCKS5代理可用! 当前IP: $ip"
        found_proxy="socks5://127.0.0.1:$port"
        break
    fi
    
    echo "⚠️  端口开放但代理不可用"
done

echo ""
echo "============================================================"

if [ -n "$found_proxy" ]; then
    echo "✅ 找到可用代理: $found_proxy"
    echo ""
    
    # 创建proxies.txt
    echo "$found_proxy" > proxies.txt
    echo "✅ 已自动创建 proxies.txt 文件"
    echo ""
    echo "📋 使用方法:"
    echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt"
    echo ""
    echo "   或者直接使用:"
    echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy $found_proxy"
else
    echo "❌ 未找到可用的Shadowrocket代理"
    echo ""
    echo "💡 请手动查看Shadowrocket设置:"
    echo "   1. 打开Shadowrocket应用"
    echo "   2. 点击右下角'设置'图标（齿轮）"
    echo "   3. 找到'本地代理'或'HTTP代理'选项"
    echo "   4. 查看并记录端口号"
    echo ""
    echo "   然后使用命令:"
    echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:端口号"
fi

echo "============================================================"

