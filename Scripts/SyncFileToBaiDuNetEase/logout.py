#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登出脚本
使用 BaiduPCS-Go 命令进行登出
"""

import sys
import subprocess
import shutil


def check_baidupcs_go():
    """检查 BaiduPCS-Go 是否已安装"""
    possible_names = ['BaiduPCS-Go', 'baidupcs-go', 'baidupcs']
    
    for cmd in possible_names:
        if shutil.which(cmd):
            return cmd
    
    return None


def check_login_status(cmd):
    """
    检查当前登录状态
    
    Args:
        cmd: BaiduPCS-Go 命令
        
    Returns:
        bool: 是否已登录
    """
    try:
        result = subprocess.run(
            [cmd, 'who'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, None
    except:
        return False, None


def logout(cmd):
    """
    执行登出操作
    
    Args:
        cmd: BaiduPCS-Go 命令
        
    Returns:
        bool: 登出是否成功
    """
    try:
        result = subprocess.run(
            [cmd, 'logout'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # 输出命令执行结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        # 检查返回码
        if result.returncode == 0:
            print("\n✅ 登出成功！")
            return True
        else:
            print(f"\n❌ 登出失败，返回码: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print(f"错误：找不到命令 {cmd}！")
        print("请确保 BaiduPCS-Go 已安装并在 PATH 中")
        return False
    except Exception as e:
        print(f"错误：登出过程中出现异常: {e}")
        return False


def main():
    """主函数"""
    # 检查 BaiduPCS-Go 是否安装
    baidupcs_cmd = check_baidupcs_go()
    if not baidupcs_cmd:
        print("错误：未找到 BaiduPCS-Go 命令！")
        print("请先安装 BaiduPCS-Go 并确保它在系统 PATH 中")
        print("\n安装方法:")
        print("1. 访问 https://github.com/qjfoidnh/BaiduPCS-Go")
        print("2. 下载对应系统的版本")
        print("3. 解压并将可执行文件添加到 PATH")
        sys.exit(1)
    
    print(f"找到 BaiduPCS-Go: {baidupcs_cmd}\n")
    
    # 检查当前登录状态
    print("检查当前登录状态...")
    is_logged_in, user_info = check_login_status(baidupcs_cmd)
    
    if not is_logged_in:
        print("当前未登录，无需登出")
        return
    
    # 显示当前登录信息
    print("当前登录状态:")
    print(user_info)
    
    # 确认登出
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        # 强制登出，不询问
        print("\n执行登出...")
    else:
        response = input("\n确认要登出吗？(y/N): ")
        if response.lower() != 'y':
            print("取消登出")
            return
    
    # 执行登出
    success = logout(baidupcs_cmd)
    
    if success:
        # 再次检查登录状态确认
        print("\n验证登出状态...")
        is_logged_in, _ = check_login_status(baidupcs_cmd)
        if not is_logged_in:
            print("✅ 确认已登出")
        else:
            print("⚠️  警告：登出后仍检测到登录状态，请手动检查")
    else:
        print("\n登出失败，请检查:")
        print("1. BaiduPCS-Go 版本是否支持登出命令")
        print("2. 网络连接是否正常")
        sys.exit(1)


if __name__ == '__main__':
    main()
