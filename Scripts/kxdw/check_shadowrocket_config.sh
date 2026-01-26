#!/bin/bash
echo "============================================================"
echo "检查Shadowrocket配置"
echo "============================================================"
echo ""

# 检查配置文件
config_dir="$HOME/Library/Application Support/Shadowrocket"
if [ -d "$config_dir" ]; then
    echo "✅ 找到Shadowrocket配置目录"
    echo ""
    
    # 查找配置文件
    echo "📋 查找配置文件..."
    find "$config_dir" -type f \( -name "*.conf" -o -name "*.json" -o -name "*.plist" \) 2>/dev/null | head -5 | while read file; do
        echo "   文件: $file"
        # 尝试查找端口号
        if grep -q -E "(port|Port|PORT|7890|1080|8080)" "$file" 2>/dev/null; then
            echo "   📌 可能包含端口配置:"
            grep -E "(port|Port|PORT|7890|1080|8080)" "$file" 2>/dev/null | head -3
        fi
    done
else
    echo "❌ 未找到Shadowrocket配置目录"
fi

echo ""
echo "💡 提示: Shadowrocket的本地代理端口通常在应用设置中查看"
echo "   1. 打开Shadowrocket"
echo "   2. 点击右下角'设置'图标"
echo "   3. 查找'本地代理'或'HTTP代理'选项"
echo "   4. 查看端口号（常见: 7890, 8080, 8888）"
echo ""
echo "============================================================"
