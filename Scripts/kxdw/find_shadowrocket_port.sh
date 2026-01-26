#!/bin/bash
# 查找Shadowrocket本地代理端口

echo "============================================================"
echo "查找Shadowrocket本地代理端口"
echo "============================================================"
echo ""

# 检查常见端口
ports=(7890 1080 8080 8888 6152 6153 10808)

found=false

for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "✅ 发现端口 $port 正在监听"
        
        # 尝试测试是否是HTTP代理
        if curl -x http://127.0.0.1:$port -s --max-time 3 https://httpbin.org/ip > /dev/null 2>&1; then
            echo "   ✅ 这是HTTP代理: http://127.0.0.1:$port"
            echo ""
            echo "📋 使用方法:"
            echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:$port"
            echo ""
            # 自动创建proxies.txt
            echo "http://127.0.0.1:$port" > proxies.txt
            echo "✅ 已自动创建 proxies.txt 文件"
            found=true
            break
        fi
        
        # 尝试测试是否是SOCKS5代理
        if curl --socks5 127.0.0.1:$port -s --max-time 3 https://httpbin.org/ip > /dev/null 2>&1; then
            echo "   ✅ 这是SOCKS5代理: socks5://127.0.0.1:$port"
            echo ""
            echo "📋 使用方法:"
            echo "   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy socks5://127.0.0.1:$port"
            echo ""
            # 自动创建proxies.txt
            echo "socks5://127.0.0.1:$port" > proxies.txt
            echo "✅ 已自动创建 proxies.txt 文件"
            found=true
            break
        fi
    fi
done

if [ "$found" = false ]; then
    echo "❌ 未找到Shadowrocket本地代理端口"
    echo ""
    echo "💡 如何查看Shadowrocket本地代理端口:"
    echo "   1. 打开Shadowrocket应用"
    echo "   2. 点击右下角'设置'图标（齿轮）"
    echo "   3. 找到'本地代理'或'HTTP代理'选项"
    echo "   4. 查看端口号（通常是7890）"
    echo ""
    echo "   或者查看Shadowrocket配置文件:"
    echo "   ~/Library/Application Support/Shadowrocket/"
    echo ""
fi

echo "============================================================"

