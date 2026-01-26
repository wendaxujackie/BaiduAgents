#!/bin/bash
# Linux/macOS 环境设置脚本

echo "=========================================="
echo "百度网盘同步工具 - 环境设置"
echo "=========================================="

# 检查 Python 版本
echo "检查 Python 版本..."
python3 --version

if [ $? -ne 0 ]; then
    echo "错误：未找到 Python3！"
    echo "请先安装 Python 3.7 或更高版本"
    exit 1
fi

# 创建虚拟环境
echo ""
echo "创建虚拟环境..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "错误：创建虚拟环境失败！"
    exit 1
fi

# 激活虚拟环境
echo ""
echo "激活虚拟环境..."
source venv/bin/activate

# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖（如果有的话）
echo ""
echo "检查依赖..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "未找到 requirements.txt，跳过依赖安装"
fi

# 检查 BaiduPCS-Go
echo ""
echo "=========================================="
echo "检查 BaiduPCS-Go"
echo "=========================================="

if command -v BaiduPCS-Go &> /dev/null || command -v baidupcs-go &> /dev/null || command -v baidupcs &> /dev/null; then
    echo "✅ BaiduPCS-Go 已安装"
    if command -v BaiduPCS-Go &> /dev/null; then
        BaiduPCS-Go --version | head -1
    elif command -v baidupcs-go &> /dev/null; then
        baidupcs-go --version | head -1
    else
        baidupcs --version | head -1
    fi
else
    echo "⚠️  BaiduPCS-Go 未安装"
    echo ""
    echo "尝试使用 Homebrew 安装..."
    if command -v brew &> /dev/null; then
        if brew install baidupcs-go; then
            echo "✅ BaiduPCS-Go 安装成功！"
        else
            echo "⚠️  Homebrew 安装失败，请手动安装"
            echo ""
            echo "安装方法："
            echo "  1. 使用 Homebrew: brew install baidupcs-go"
            echo "  2. 从 GitHub 下载: https://github.com/qjfoidnh/BaiduPCS-Go/releases"
        fi
    else
        echo "⚠️  未找到 Homebrew"
        echo ""
        echo "安装方法："
        echo "  1. 安装 Homebrew 后运行: brew install baidupcs-go"
        echo "  2. 从 GitHub 下载: https://github.com/qjfoidnh/BaiduPCS-Go/releases"
        echo ""
        echo "详细安装说明: https://github.com/qjfoidnh/BaiduPCS-Go"
    fi
fi

echo ""
echo "=========================================="
echo "环境设置完成！"
echo "=========================================="
echo ""
echo "要使用虚拟环境，请运行："
echo "  source venv/bin/activate"
echo ""
echo "退出虚拟环境："
echo "  deactivate"
echo ""
