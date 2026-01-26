@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM ============================================
REM Chrome调试模式启动脚本 (Windows)
REM 用于网页自动化和APK下载功能
REM ============================================

title Chrome 调试模式启动器

REM 默认调试端口
set "DEBUG_PORT=9222"

REM 用户数据目录
set "SCRIPT_DIR=%~dp0"
set "USER_DATA_DIR=%SCRIPT_DIR%chrome_profile"

REM 解析命令行参数
:parse_args
if "%~1"=="" goto :start
if /i "%~1"=="-p" (
    set "DEBUG_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="--port" (
    set "DEBUG_PORT=%~2"
    shift
    shift
    goto :parse_args
)
if /i "%~1"=="-k" goto :kill_chrome
if /i "%~1"=="--kill" goto :kill_chrome
if /i "%~1"=="-h" goto :show_help
if /i "%~1"=="--help" goto :show_help
shift
goto :parse_args

:show_help
echo.
echo Chrome调试模式启动脚本
echo.
echo 用法: %~nx0 [选项]
echo.
echo 选项:
echo   -p, --port PORT   指定调试端口 (默认: 9222)
echo   -k, --kill        关闭运行中的Chrome调试实例
echo   -h, --help        显示此帮助信息
echo.
exit /b 0

:kill_chrome
echo.
echo [INFO] 正在关闭Chrome调试实例...

REM 查找并关闭使用调试端口的Chrome进程
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%DEBUG_PORT%"') do (
    taskkill /PID %%a /F >nul 2>&1
)

REM 关闭所有Chrome进程（可选，更彻底）
REM taskkill /IM chrome.exe /F >nul 2>&1

echo [SUCCESS] Chrome调试实例已关闭
exit /b 0

:start
cls
echo.
echo ╔══════════════════════════════════════════════════════════╗
echo ║          Chrome 调试模式启动脚本                         ║
echo ║          用于自动化网页搜索和APK下载                     ║
echo ╚══════════════════════════════════════════════════════════╝
echo.

REM ========================================
REM 查找Chrome安装路径
REM ========================================
echo [INFO] 正在查找Chrome浏览器...

set "CHROME_PATH="

REM 检查常见安装路径
set "CHROME_PATHS[0]=C:\Program Files\Google\Chrome\Application\chrome.exe"
set "CHROME_PATHS[1]=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
set "CHROME_PATHS[2]=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
set "CHROME_PATHS[3]=C:\Program Files\Google\Chrome Beta\Application\chrome.exe"
set "CHROME_PATHS[4]=C:\Program Files\Google\Chrome Dev\Application\chrome.exe"

for /L %%i in (0,1,4) do (
    if exist "!CHROME_PATHS[%%i]!" (
        set "CHROME_PATH=!CHROME_PATHS[%%i]!"
        goto :chrome_found
    )
)

REM 从注册表查找
for /f "tokens=2*" %%a in ('reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" /ve 2^>nul') do (
    set "CHROME_PATH=%%b"
    if exist "!CHROME_PATH!" goto :chrome_found
)

for /f "tokens=2*" %%a in ('reg query "HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" /ve 2^>nul') do (
    set "CHROME_PATH=%%b"
    if exist "!CHROME_PATH!" goto :chrome_found
)

REM Chrome未找到
echo.
echo [ERROR] 未找到Chrome浏览器！
echo.
echo 请从以下地址下载安装Chrome:
echo   https://www.google.com/chrome/
echo.
pause
exit /b 1

:chrome_found
echo [SUCCESS] 找到Chrome: %CHROME_PATH%
echo.

REM ========================================
REM 检查端口是否被占用
REM ========================================
echo [INFO] 检查端口 %DEBUG_PORT% 是否被占用...

set "PORT_IN_USE="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%DEBUG_PORT%"') do (
    set "PORT_IN_USE=%%a"
)

if defined PORT_IN_USE (
    echo [WARNING] 端口 %DEBUG_PORT% 已被占用 (PID: %PORT_IN_USE%)
    echo.
    set /p KILL_EXISTING="是否关闭已有的Chrome调试实例? (Y/n): "
    if /i not "!KILL_EXISTING!"=="n" (
        echo [INFO] 正在关闭进程 %PORT_IN_USE%...
        taskkill /PID %PORT_IN_USE% /F >nul 2>&1
        timeout /t 2 /nobreak >nul
        echo [SUCCESS] 已关闭旧实例
    ) else (
        echo [INFO] 使用已有的Chrome调试实例
        goto :show_info
    )
)

echo [SUCCESS] 端口 %DEBUG_PORT% 可用
echo.

REM ========================================
REM 创建用户数据目录
REM ========================================
if not exist "%USER_DATA_DIR%" (
    mkdir "%USER_DATA_DIR%"
    echo [INFO] 创建用户数据目录: %USER_DATA_DIR%
)

REM ========================================
REM 启动Chrome调试模式
REM ========================================
echo [INFO] 正在启动Chrome调试模式...
echo.

start "" "%CHROME_PATH%" ^
    --remote-debugging-port=%DEBUG_PORT% ^
    --user-data-dir="%USER_DATA_DIR%" ^
    --no-first-run ^
    --no-default-browser-check ^
    --disable-background-networking ^
    --disable-client-side-phishing-detection ^
    --disable-default-apps ^
    --disable-hang-monitor ^
    --disable-popup-blocking ^
    --disable-prompt-on-repost ^
    --disable-sync ^
    --disable-translate ^
    --metrics-recording-only ^
    --safebrowsing-disable-auto-update ^
    --window-size=1920,1080

REM 等待Chrome启动
echo [INFO] 等待Chrome启动...
timeout /t 3 /nobreak >nul

REM 验证是否启动成功
set "STARTED="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr "LISTENING" ^| findstr ":%DEBUG_PORT%"') do (
    set "STARTED=%%a"
)

if not defined STARTED (
    echo.
    echo [ERROR] Chrome启动失败！
    echo.
    echo 请尝试:
    echo   1. 手动关闭所有Chrome窗口后重试
    echo   2. 检查Chrome是否正确安装
    echo   3. 使用管理员权限运行此脚本
    echo.
    pause
    exit /b 1
)

:show_info
echo.
echo ════════════════════════════════════════════════════════════
echo   [SUCCESS] Chrome调试模式已启动！
echo ════════════════════════════════════════════════════════════
echo.
echo   调试端口: %DEBUG_PORT%
echo   连接地址: http://127.0.0.1:%DEBUG_PORT%
echo   用户数据: %USER_DATA_DIR%
echo.
echo ════════════════════════════════════════════════════════════
echo.
echo   提示:
echo   1. 保持Chrome窗口打开
echo   2. 在另一个终端运行自动化脚本:
echo      run.bat --mode search
echo      run.bat --mode download
echo.
echo   3. 查看调试页面列表:
echo      在浏览器打开: http://127.0.0.1:%DEBUG_PORT%/json
echo.
echo ════════════════════════════════════════════════════════════
echo.
echo 按任意键退出此窗口 (Chrome会继续运行)...
pause >nul
