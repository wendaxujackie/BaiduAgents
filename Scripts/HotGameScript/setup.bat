@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================
REM 快手游戏APK自动化采集工具 - 一键安装脚本 (Windows)
REM ============================================

title 快手游戏APK自动化采集工具 - 环境配置
color 0A

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║   快手游戏APK自动化采集工具 - 环境配置脚本               ║
echo ║   支持: Windows 10/11                                    ║
echo ║   版本: 1.0.0                                            ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM ========================================
REM 步骤1: 检查Python
REM ========================================
echo ========================================
echo ^>^>^> 步骤1: 检查Python环境
echo ========================================
echo.

set "PYTHON_CMD="

REM 尝试python命令
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PY_VERSION=%%i"
    echo [INFO] 找到Python: !PY_VERSION!
    set "PYTHON_CMD=python"
    goto :python_found
)

REM 尝试python3命令
where python3 >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set "PY_VERSION=%%i"
    echo [INFO] 找到Python: !PY_VERSION!
    set "PYTHON_CMD=python3"
    goto :python_found
)

REM 尝试py命令 (Windows Python Launcher)
where py >nul 2>&1
if %errorlevel% equ 0 (
    for /f "tokens=2" %%i in ('py --version 2^>^&1') do set "PY_VERSION=%%i"
    echo [INFO] 找到Python: !PY_VERSION!
    set "PYTHON_CMD=py"
    goto :python_found
)

echo [ERROR] 未找到Python，请先安装Python 3.8+
echo.
echo 下载地址: https://www.python.org/downloads/
echo 安装时请勾选 "Add Python to PATH"
echo.
pause
exit /b 1

:python_found
echo [SUCCESS] Python检查通过
echo.

REM ========================================
REM 步骤2: 创建虚拟环境
REM ========================================
echo ========================================
echo ^>^>^> 步骤2: 创建Python虚拟环境
echo ========================================
echo.

set "VENV_DIR=%SCRIPT_DIR%venv"

if exist "%VENV_DIR%" (
    echo [WARNING] 虚拟环境已存在: %VENV_DIR%
    set /p RECREATE="是否删除并重新创建? (y/N): "
    if /i "!RECREATE!"=="y" (
        echo [INFO] 删除旧虚拟环境...
        rmdir /s /q "%VENV_DIR%"
    ) else (
        echo [INFO] 跳过虚拟环境创建
        goto :activate_venv
    )
)

echo [INFO] 创建虚拟环境...
%PYTHON_CMD% -m venv "%VENV_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] 创建虚拟环境失败
    pause
    exit /b 1
)
echo [SUCCESS] 虚拟环境创建成功
echo.

:activate_venv

REM ========================================
REM 步骤3: 激活虚拟环境
REM ========================================
echo ========================================
echo ^>^>^> 步骤3: 激活虚拟环境
echo ========================================
echo.

if exist "%VENV_DIR%\Scripts\activate.bat" (
    call "%VENV_DIR%\Scripts\activate.bat"
    echo [SUCCESS] 虚拟环境已激活
) else (
    echo [ERROR] 虚拟环境激活脚本不存在
    pause
    exit /b 1
)
echo.

REM ========================================
REM 步骤4: 升级pip
REM ========================================
echo ========================================
echo ^>^>^> 步骤4: 升级pip
echo ========================================
echo.

python -m pip install --upgrade pip -q
echo [SUCCESS] pip已升级
echo.

REM ========================================
REM 步骤5: 安装Python依赖
REM ========================================
echo ========================================
echo ^>^>^> 步骤5: 安装Python依赖
echo ========================================
echo.

if not exist "requirements.txt" (
    echo [ERROR] requirements.txt 不存在
    pause
    exit /b 1
)

echo [INFO] 正在安装依赖，这可能需要几分钟...
echo.

REM 安装基础依赖
pip install wheel setuptools -q

REM 安装主要依赖
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo [WARNING] 部分依赖可能安装失败，请检查错误信息
) else (
    echo [SUCCESS] Python依赖安装完成
)
echo.

REM ========================================
REM 步骤6: 安装PaddleOCR (可选)
REM ========================================
echo ========================================
echo ^>^>^> 步骤6: 安装PaddleOCR (OCR引擎)
echo ========================================
echo.

set /p INSTALL_PADDLE="是否安装PaddleOCR? (推荐，用于游戏名称识别) (Y/n): "
if /i not "!INSTALL_PADDLE!"=="n" (
    echo [INFO] 正在安装PaddlePaddle (CPU版本)...
    pip install paddlepaddle -q
    
    echo [INFO] 正在安装PaddleOCR...
    pip install paddleocr -q
    
    echo [SUCCESS] PaddleOCR安装完成
) else (
    echo [WARNING] 跳过PaddleOCR安装
)
echo.

REM ========================================
REM 步骤7: 检查Node.js和Appium
REM ========================================
echo ========================================
echo ^>^>^> 步骤7: 安装Appium (移动端自动化)
echo ========================================
echo.

set /p INSTALL_APPIUM="是否安装Appium? (用于手机自动化操作) (Y/n): "
if /i not "!INSTALL_APPIUM!"=="n" (
    where node >nul 2>&1
    if %errorlevel% neq 0 (
        echo [WARNING] 未找到Node.js
        echo.
        echo 请先安装Node.js:
        echo   下载地址: https://nodejs.org/
        echo.
        echo [WARNING] 跳过Appium安装
    ) else (
        echo [INFO] Node.js版本:
        node --version
        
        echo [INFO] 正在安装Appium...
        call npm install -g appium 2>nul
        
        echo [INFO] 安装Appium驱动...
        call appium driver install uiautomator2 2>nul
        call appium driver install xcuitest 2>nul
        
        echo [SUCCESS] Appium安装完成
    )
) else (
    echo [WARNING] 跳过Appium安装
)
echo.

REM ========================================
REM 步骤8: 创建目录
REM ========================================
echo ========================================
echo ^>^>^> 步骤8: 创建项目目录
echo ========================================
echo.

for %%d in (screenshots downloads data logs "2026发发发") do (
    if not exist "%%~d" (
        mkdir "%%~d"
        echo [INFO] 创建目录: %%~d
    )
)
echo [SUCCESS] 目录创建完成
echo.

REM ========================================
REM 步骤9: 创建启动脚本
REM ========================================
echo ========================================
echo ^>^>^> 步骤9: 创建快捷启动脚本
echo ========================================
echo.

REM 创建run.bat
(
echo @echo off
echo chcp 65001 ^>nul
echo cd /d "%%~dp0"
echo call venv\Scripts\activate.bat
echo python main.py %%*
) > run.bat
echo [SUCCESS] 创建启动脚本: run.bat

REM 创建Chrome调试启动脚本
(
echo @echo off
echo echo 启动Chrome调试模式 ^(端口: 9222^)...
echo start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
echo echo Chrome调试模式已启动
echo echo 请在另一个终端运行自动化脚本
echo pause
) > start_chrome_debug.bat
echo [SUCCESS] 创建Chrome调试脚本: start_chrome_debug.bat

REM 创建Appium启动脚本
(
echo @echo off
echo echo 启动Appium服务...
echo appium
) > start_appium.bat
echo [SUCCESS] 创建Appium启动脚本: start_appium.bat

echo.

REM ========================================
REM 步骤10: 验证安装
REM ========================================
echo ========================================
echo ^>^>^> 步骤10: 验证安装
echo ========================================
echo.

echo [INFO] 检查已安装的包...
echo.

python -c "import selenium; print('[SUCCESS] selenium ✓')" 2>nul || echo [WARNING] selenium 未安装
python -c "import requests; print('[SUCCESS] requests ✓')" 2>nul || echo [WARNING] requests 未安装
python -c "import pandas; print('[SUCCESS] pandas ✓')" 2>nul || echo [WARNING] pandas 未安装
python -c "import loguru; print('[SUCCESS] loguru ✓')" 2>nul || echo [WARNING] loguru 未安装
python -c "import PIL; print('[SUCCESS] Pillow ✓')" 2>nul || echo [WARNING] Pillow 未安装

echo.
echo [INFO] 检查OCR引擎...
python -c "from paddleocr import PaddleOCR; print('[SUCCESS] PaddleOCR ✓')" 2>nul || (
    python -c "import pytesseract; print('[SUCCESS] Tesseract ✓')" 2>nul || echo [WARNING] OCR引擎未安装
)

echo.
echo [INFO] 检查Appium...
where appium >nul 2>&1 && echo [SUCCESS] Appium ✓ || echo [WARNING] Appium未安装

echo.

REM ========================================
REM 完成
REM ========================================
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║                    安装完成！                            ║
echo ╚══════════════════════════════════════════════════════════╝
echo.
echo 使用方法:
echo.
echo   1. 运行完整流程:
echo      run.bat --full --platform android
echo.
echo   2. 单独模式:
echo      run.bat --mode mobile --platform android  (移动端自动化)
echo      run.bat --mode search                     (搜索游戏)
echo      run.bat --mode download                   (下载APK)
echo      run.bat --mode ocr                        (OCR识别)
echo.
echo   3. 启动Chrome调试模式:
echo      start_chrome_debug.bat
echo.
echo   4. 启动Appium服务:
echo      start_appium.bat
echo.
echo ============================================
echo.

pause
