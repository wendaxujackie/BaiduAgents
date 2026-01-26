@echo off
REM Windows 环境设置脚本

echo ==========================================
echo 百度网盘同步工具 - 环境设置
echo ==========================================

REM 检查 Python 版本
echo 检查 Python 版本...
python --version

if %errorlevel% neq 0 (
    echo 错误：未找到 Python！
    echo 请先安装 Python 3.7 或更高版本
    exit /b 1
)

REM 创建虚拟环境
echo.
echo 创建虚拟环境...
python -m venv venv

if %errorlevel% neq 0 (
    echo 错误：创建虚拟环境失败！
    exit /b 1
)

REM 激活虚拟环境
echo.
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级 pip
echo.
echo 升级 pip...
python -m pip install --upgrade pip

REM 安装依赖（如果有的话）
echo.
echo 检查依赖...
if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo 未找到 requirements.txt，跳过依赖安装
)

REM 检查 BaiduPCS-Go
echo.
echo ==========================================
echo 检查 BaiduPCS-Go
echo ==========================================

where BaiduPCS-Go >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ BaiduPCS-Go 已安装
    BaiduPCS-Go --version
) else (
    where baidupcs-go >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ BaiduPCS-Go 已安装
        baidupcs-go --version
    ) else (
        where baidupcs >nul 2>&1
        if %errorlevel% equ 0 (
            echo ✅ BaiduPCS-Go 已安装
            baidupcs --version
        ) else (
            echo ⚠️  BaiduPCS-Go 未安装
            echo.
            echo 尝试使用 Chocolatey 安装...
            where choco >nul 2>&1
            if %errorlevel% equ 0 (
                choco install baidupcs-go -y
                if %errorlevel% equ 0 (
                    echo ✅ BaiduPCS-Go 安装成功！
                ) else (
                    echo ⚠️  Chocolatey 安装失败，请手动安装
                    echo.
                    echo 安装方法：
                    echo   1. 使用 Chocolatey: choco install baidupcs-go
                    echo   2. 从 GitHub 下载: https://github.com/qjfoidnh/BaiduPCS-Go/releases
                )
            ) else (
                echo ⚠️  未找到 Chocolatey
                echo.
                echo 安装方法：
                echo   1. 安装 Chocolatey 后运行: choco install baidupcs-go
                echo   2. 从 GitHub 下载: https://github.com/qjfoidnh/BaiduPCS-Go/releases
                echo.
                echo 详细安装说明: https://github.com/qjfoidnh/BaiduPCS-Go
            )
        )
    )
)

echo.
echo ==========================================
echo 环境设置完成！
echo ==========================================
echo.
echo 要使用虚拟环境，请运行：
echo   venv\Scripts\activate.bat
echo.
echo 退出虚拟环境：
echo   deactivate
echo.

pause
