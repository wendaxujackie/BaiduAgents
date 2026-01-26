#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台环境设置脚本
自动创建虚拟环境并安装依赖
"""

import os
import sys
import subprocess
import platform
import shutil


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"错误：需要 Python 3.7 或更高版本，当前版本: {version.major}.{version.minor}")
        return False
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro} ✅")
    return True


def create_venv():
    """创建虚拟环境"""
    venv_dir = 'venv'
    
    if os.path.exists(venv_dir):
        response = input(f"虚拟环境目录 {venv_dir} 已存在，是否重新创建？(y/N): ")
        if response.lower() == 'y':
            import shutil
            shutil.rmtree(venv_dir)
        else:
            print("使用现有虚拟环境")
            return True
    
    print("创建虚拟环境...")
    try:
        subprocess.run([sys.executable, '-m', 'venv', venv_dir], check=True)
        print("✅ 虚拟环境创建成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ 虚拟环境创建失败")
        return False


def get_pip_command():
    """获取 pip 命令路径"""
    system = platform.system()
    if system == 'Windows':
        pip_path = os.path.join('venv', 'Scripts', 'pip.exe')
    else:
        pip_path = os.path.join('venv', 'bin', 'pip')
    
    return pip_path if os.path.exists(pip_path) else None


def install_dependencies():
    """安装依赖"""
    pip_cmd = get_pip_command()
    if not pip_cmd:
        print("警告：未找到虚拟环境中的 pip，跳过依赖安装")
        return False
    
    print("升级 pip...")
    try:
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
    except:
        pass
    
    if os.path.exists('requirements.txt'):
        print("安装依赖...")
        try:
            subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
            print("✅ 依赖安装成功")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  依赖安装失败（可能没有需要安装的依赖）")
            return False
    else:
        print("未找到 requirements.txt，跳过依赖安装")
        return True


def check_baidupcs_go():
    """检查 BaiduPCS-Go 是否已安装"""
    possible_names = ['BaiduPCS-Go', 'baidupcs-go', 'baidupcs']
    
    for cmd in possible_names:
        if shutil.which(cmd):
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"✅ BaiduPCS-Go 已安装: {version}")
                return True
    
    return False


def install_baidupcs_go():
    """尝试安装 BaiduPCS-Go"""
    system = platform.system()
    
    print("\n" + "="*50)
    print("BaiduPCS-Go 未安装")
    print("="*50)
    
    if system == 'Darwin':  # macOS
        print("\n检测到 macOS 系统")
        print("尝试使用 Homebrew 安装...")
        try:
            # 检查是否有 brew
            if shutil.which('brew'):
                result = subprocess.run(['brew', 'install', 'baidupcs-go'],
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ BaiduPCS-Go 安装成功！")
                    return True
                else:
                    print("⚠️  Homebrew 安装失败，请手动安装")
            else:
                print("⚠️  未找到 Homebrew，请先安装 Homebrew 或手动安装 BaiduPCS-Go")
        except Exception as e:
            print(f"⚠️  安装过程出错: {e}")
    
    elif system == 'Linux':
        print("\n检测到 Linux 系统")
        print("请使用系统包管理器安装 BaiduPCS-Go")
        print("\n安装方法：")
        print("  # Arch Linux")
        print("  sudo pacman -S baidupcs-go")
        print("\n  # Ubuntu/Debian (需要添加仓库)")
        print("  或从 GitHub 下载: https://github.com/qjfoidnh/BaiduPCS-Go/releases")
    
    elif system == 'Windows':
        print("\n检测到 Windows 系统")
        print("请使用以下方法之一安装：")
        print("  1. 使用 Chocolatey: choco install baidupcs-go")
        print("  2. 从 GitHub 下载: https://github.com/qjfoidnh/BaiduPCS-Go/releases")
    
    print("\n详细安装说明请查看: https://github.com/qjfoidnh/BaiduPCS-Go")
    print("安装完成后，请确保 BaiduPCS-Go 在系统 PATH 中")
    
    return False


def print_usage():
    """打印使用说明"""
    system = platform.system()
    
    print("\n" + "="*50)
    print("环境设置完成！")
    print("="*50)
    print("\n要使用虚拟环境，请运行：")
    
    if system == 'Windows':
        print("  venv\\Scripts\\activate.bat")
    else:
        print("  source venv/bin/activate")
    
    print("\n退出虚拟环境：")
    print("  deactivate")
    print()


def main():
    """主函数"""
    print("="*50)
    print("百度网盘同步工具 - 环境设置")
    print("="*50)
    print()
    
    # 检查 Python 版本
    if not check_python_version():
        sys.exit(1)
    
    print()
    
    # 创建虚拟环境
    if not create_venv():
        sys.exit(1)
    
    print()
    
    # 安装依赖
    install_dependencies()
    
    print()
    
    # 检查 BaiduPCS-Go
    print("="*50)
    print("检查 BaiduPCS-Go")
    print("="*50)
    if not check_baidupcs_go():
        install_baidupcs_go()
    else:
        print()
    
    # 打印使用说明
    print_usage()


if __name__ == '__main__':
    main()
