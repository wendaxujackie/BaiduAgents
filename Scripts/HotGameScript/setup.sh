#!/bin/bash
# ============================================
# 快手游戏APK自动化采集工具 - 一键安装脚本 (Mac/Linux)
# ============================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "\n${PURPLE}========================================${NC}"
    echo -e "${PURPLE}>>> $1${NC}"
    echo -e "${PURPLE}========================================${NC}\n"
}

# 显示欢迎信息
show_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║   快手游戏APK自动化采集工具 - 环境配置脚本               ║"
    echo "║   支持: macOS / Linux                                    ║"
    echo "║   版本: 1.0.0                                            ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检查Python版本
check_python() {
    print_step "检查Python环境"
    
    # 尝试不同的Python命令
    PYTHON_CMD=""
    for cmd in python3 python; do
        if command_exists "$cmd"; then
            version=$($cmd --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)
            
            if [ "$major" -ge 3 ] && [ "$minor" -ge 8 ]; then
                PYTHON_CMD="$cmd"
                print_success "找到Python: $($cmd --version)"
                break
            fi
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        print_error "未找到Python 3.8+，请先安装Python"
        echo ""
        echo "安装方法:"
        echo "  macOS: brew install python@3.11"
        echo "  Ubuntu: sudo apt install python3.11 python3.11-venv"
        echo "  或从 https://www.python.org/downloads/ 下载安装"
        exit 1
    fi
    
    export PYTHON_CMD
}

# 创建虚拟环境
create_venv() {
    print_step "创建Python虚拟环境"
    
    VENV_DIR="$SCRIPT_DIR/venv"
    
    if [ -d "$VENV_DIR" ]; then
        print_warning "虚拟环境已存在: $VENV_DIR"
        read -p "是否删除并重新创建? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            print_info "跳过虚拟环境创建"
            return
        fi
    fi
    
    print_info "创建虚拟环境..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    print_success "虚拟环境创建成功: $VENV_DIR"
}

# 激活虚拟环境
activate_venv() {
    print_step "激活虚拟环境"
    
    VENV_DIR="$SCRIPT_DIR/venv"
    
    if [ -f "$VENV_DIR/bin/activate" ]; then
        source "$VENV_DIR/bin/activate"
        print_success "虚拟环境已激活"
        print_info "Python路径: $(which python)"
    else
        print_error "虚拟环境不存在，请先创建"
        exit 1
    fi
}

# 升级pip
upgrade_pip() {
    print_step "升级pip"
    
    pip install --upgrade pip -q
    print_success "pip已升级到最新版本: $(pip --version)"
}

# 安装Python依赖
install_python_deps() {
    print_step "安装Python依赖"
    
    if [ ! -f "requirements.txt" ]; then
        print_error "requirements.txt 不存在"
        exit 1
    fi
    
    print_info "正在安装依赖，这可能需要几分钟..."
    
    # 先安装基础依赖
    print_info "安装基础依赖..."
    pip install wheel setuptools -q
    
    # 安装主要依赖
    pip install -r requirements.txt --progress-bar on
    
    print_success "Python依赖安装完成"
}

# 安装PaddleOCR（可选但推荐）
install_paddleocr() {
    print_step "安装PaddleOCR (OCR引擎)"
    
    read -p "是否安装PaddleOCR? (推荐，用于游戏名称识别) (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        print_info "正在安装PaddlePaddle..."
        
        # 检测是否有GPU
        if command_exists nvidia-smi; then
            print_info "检测到NVIDIA GPU，安装GPU版本..."
            pip install paddlepaddle-gpu -q
        else
            print_info "安装CPU版本..."
            pip install paddlepaddle -q
        fi
        
        print_info "正在安装PaddleOCR..."
        pip install paddleocr -q
        
        print_success "PaddleOCR安装完成"
    else
        print_warning "跳过PaddleOCR安装，将使用备用OCR方案"
    fi
}

# 安装Node.js和Appium（可选）
install_appium() {
    print_step "安装Appium (移动端自动化)"
    
    read -p "是否安装Appium? (用于手机自动化操作) (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        # 检查Node.js
        if ! command_exists node; then
            print_warning "未找到Node.js"
            echo ""
            echo "请先安装Node.js:"
            echo "  macOS: brew install node"
            echo "  Ubuntu: sudo apt install nodejs npm"
            echo "  或从 https://nodejs.org/ 下载安装"
            echo ""
            print_warning "跳过Appium安装"
            return
        fi
        
        print_info "Node.js版本: $(node --version)"
        
        # 检查并修复已安装的Appium的uuid依赖问题
        if command_exists appium; then
            print_info "检测到已安装的Appium，检查依赖兼容性..."
            # 尝试修复uuid依赖问题
            if npm list -g uuid 2>/dev/null | grep -q "uuid@"; then
                print_info "修复uuid依赖兼容性问题..."
                npm install -g uuid@8.3.2 --legacy-peer-deps 2>/dev/null || true
            fi
        fi
        
        # 安装Appium
        print_info "正在安装Appium..."
        # 使用 --legacy-peer-deps 来解决依赖兼容性问题
        if npm install -g appium --legacy-peer-deps 2>/dev/null; then
            print_success "Appium安装成功"
            
            # 修复uuid依赖兼容性问题
            print_info "修复uuid依赖兼容性问题..."
            APPIUM_DIR=$(npm root -g)/appium
            if [ -d "$APPIUM_DIR" ]; then
                # 修复主目录的uuid
                cd "$APPIUM_DIR" && npm install uuid@8.3.2 --save --legacy-peer-deps 2>/dev/null || true
                # 修复@appium/support的uuid
                if [ -d "$APPIUM_DIR/node_modules/@appium/support" ]; then
                    cd "$APPIUM_DIR/node_modules/@appium/support" && npm install uuid@8.3.2 --save --legacy-peer-deps 2>/dev/null || true
                fi
                cd "$SCRIPT_DIR"
            fi
        else
            print_warning "全局安装失败，将使用npx方式运行Appium"
            print_info "提示: 可以使用 'npx appium' 来运行Appium"
        fi
        
        # 安装驱动
        print_info "安装Appium驱动..."
        # 如果 appium 命令可用，尝试安装驱动
        if command_exists appium; then
        appium driver install uiautomator2 2>/dev/null || true
        appium driver install xcuitest 2>/dev/null || true
        else
            print_info "使用npx方式安装驱动..."
            npx appium driver install uiautomator2 2>/dev/null || true
            npx appium driver install xcuitest 2>/dev/null || true
        fi
        
        print_success "Appium安装完成"
    else
        print_warning "跳过Appium安装"
    fi
}

# 创建必要的目录
create_directories() {
    print_step "创建项目目录"
    
    dirs=("screenshots" "downloads" "data" "logs" "2026发发发")
    
    for dir in "${dirs[@]}"; do
        mkdir -p "$SCRIPT_DIR/$dir"
        print_info "创建目录: $dir"
    done
    
    print_success "目录创建完成"
}

# 验证安装
verify_installation() {
    print_step "验证安装"
    
    echo ""
    print_info "检查已安装的包..."
    
    # 确保使用虚拟环境中的Python
    VENV_DIR="$SCRIPT_DIR/venv"
    if [ -f "$VENV_DIR/bin/python" ]; then
        PYTHON_CMD="$VENV_DIR/bin/python"
    else
        PYTHON_CMD="python"
    fi
    
    # 检查关键包
    packages=("selenium" "appium" "requests" "pandas" "loguru" "Pillow")
    
    for pkg in "${packages[@]}"; do
        # Pillow 包的导入名称是 PIL，不是 pillow
        if [ "$pkg" = "Pillow" ]; then
            import_name="PIL"
        else
            pkg_lower=$(echo "$pkg" | tr '[:upper:]' '[:lower:]')
            import_name="$pkg_lower"
        fi
        
        if $PYTHON_CMD -c "import $import_name" 2>/dev/null; then
            print_success "$pkg ✓"
        else
            print_warning "$pkg 未安装或导入失败"
        fi
    done
    
    # 检查OCR
    echo ""
    print_info "检查OCR引擎..."
    if $PYTHON_CMD -c "from paddleocr import PaddleOCR" 2>/dev/null; then
        print_success "PaddleOCR ✓"
    elif $PYTHON_CMD -c "import pytesseract" 2>/dev/null; then
        print_success "Tesseract ✓"
    else
        print_warning "OCR引擎未安装"
    fi
    
    # 检查Appium
    echo ""
    print_info "检查Appium..."
    if command_exists appium; then
        print_success "Appium ✓ ($(appium --version 2>/dev/null || echo 'unknown'))"
    else
        print_warning "Appium未安装"
    fi
}

# 创建启动脚本
create_run_script() {
    print_step "创建快捷启动脚本"
    
    cat > "$SCRIPT_DIR/run.sh" << 'EOF'
#!/bin/bash
# 快捷启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 激活虚拟环境
source venv/bin/activate

# 运行主程序
python main.py "$@"
EOF

    chmod +x "$SCRIPT_DIR/run.sh"
    print_success "创建启动脚本: run.sh"
    
    # 创建Chrome调试启动脚本
    cat > "$SCRIPT_DIR/start_chrome_debug.sh" << 'EOF'
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
EOF

    chmod +x "$SCRIPT_DIR/start_chrome_debug.sh"
    print_success "创建Chrome调试脚本: start_chrome_debug.sh"
}

# 显示完成信息
show_completion() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                    安装完成！                            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}使用方法:${NC}"
    echo ""
    echo "  1. 激活虚拟环境:"
    echo "     ${YELLOW}source venv/bin/activate${NC}"
    echo ""
    echo "  2. 运行完整流程:"
    echo "     ${YELLOW}python main.py --full --platform android${NC}"
    echo ""
    echo "  3. 或使用快捷脚本:"
    echo "     ${YELLOW}./run.sh --full --platform android${NC}"
    echo ""
    echo -e "${CYAN}可用命令:${NC}"
    echo "  ${YELLOW}./run.sh --mode mobile --platform android${NC}  # 移动端自动化"
    echo "  ${YELLOW}./run.sh --mode search${NC}                     # 搜索游戏"
    echo "  ${YELLOW}./run.sh --mode download${NC}                   # 下载APK"
    echo "  ${YELLOW}./run.sh --mode ocr${NC}                        # OCR识别"
    echo ""
    echo -e "${CYAN}启动Chrome调试模式:${NC}"
    echo "  ${YELLOW}./start_chrome_debug.sh${NC}"
    echo ""
    echo -e "${CYAN}启动Appium服务:${NC}"
    echo "  ${YELLOW}appium${NC}"
    echo ""
}

# 主函数
main() {
    show_banner
    
    check_python
    create_venv
    activate_venv
    upgrade_pip
    install_python_deps
    install_paddleocr
    install_appium
    create_directories
    create_run_script
    verify_installation
    show_completion
}

# 运行主函数
main
