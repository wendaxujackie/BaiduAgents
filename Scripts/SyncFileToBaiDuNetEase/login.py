#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录脚本
从 curl.txt 解析 cookie 并使用 BaiduPCS-Go 命令进行登录
"""

import json
import sys
import subprocess
import os
import shutil
import re


def check_baidupcs_go():
    """检查 BaiduPCS-Go 是否已安装"""
    # 可能的命令名称
    possible_names = ['BaiduPCS-Go', 'baidupcs-go', 'baidupcs']
    
    for cmd in possible_names:
        if shutil.which(cmd):
            return cmd
    
    return None


def parse_curl_file(file_path):
    """
    从 curl.txt 文件中解析 cookie
    
    Args:
        file_path: curl.txt 文件路径
        
    Returns:
        tuple: (cookies字典, cookie字符串)
    """
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在！")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 -b 参数后的 cookie 字符串
    lines = content.split('\n')
    cookie_string = None
    
    # 查找包含 -b 参数的行
    for i, line in enumerate(lines):
        if '-b' in line or '--cookie' in line:
            # 找到 -b 参数，提取引号内的内容
            match = re.search(r"-b\s+'([^']*)'", line)
            if not match:
                match = re.search(r'-b\s+"([^"]*)"', line)
            
            if match:
                cookie_string = match.group(1)
                break
            else:
                # 如果引号跨行，需要合并多行
                start_idx = line.find("'")
                if start_idx == -1:
                    start_idx = line.find('"')
                
                if start_idx != -1:
                    quote_char = line[start_idx]
                    remaining = line[start_idx+1:]
                    for j in range(i+1, len(lines)):
                        end_idx = lines[j].find(quote_char)
                        if end_idx != -1:
                            remaining += '\n' + lines[j][:end_idx]
                            cookie_string = remaining
                            break
                        else:
                            remaining += '\n' + lines[j]
                    break
    
    if not cookie_string:
        print("错误：无法在文件中找到 cookie 信息（-b 参数）！")
        print("请确保 curl.txt 文件包含 -b 参数和 cookie 字符串")
        sys.exit(1)
    
    # 解析 cookie 键值对
    cookies = {}
    parts = re.split(r';\s*(?=\w+=)', cookie_string)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if '=' in part:
            key, value = part.split('=', 1)
            key = key.strip()
            value = value.strip()
            # 移除值两端的引号
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            cookies[key] = value
    
    return cookies, cookie_string


def extract_key_cookies(cookies):
    """
    提取关键的 cookie 字段（BDUSS 和 STOKEN）
    
    Args:
        cookies: cookie 字典
        
    Returns:
        dict: 包含 BDUSS 和 STOKEN 的字典
    """
    key_cookies = {}
    
    # 提取 BDUSS（优先使用 BDUSS，如果没有则使用 BDUSS_BFESS）
    if 'BDUSS' in cookies:
        key_cookies['BDUSS'] = cookies['BDUSS']
    elif 'BDUSS_BFESS' in cookies:
        key_cookies['BDUSS'] = cookies['BDUSS_BFESS']
    
    # 提取 STOKEN
    if 'STOKEN' in cookies:
        key_cookies['STOKEN'] = cookies['STOKEN']
    
    return key_cookies


def parse_and_save_cookies(curl_file='curl.txt', output_file='cookies.json'):
    """
    从 curl.txt 解析 cookie 并保存到 cookies.json
    
    Args:
        curl_file: curl.txt 文件路径
        output_file: 输出文件路径
        
    Returns:
        dict: cookie 数据字典
    """
    print(f"正在解析文件: {curl_file}")
    
    # 解析 cookie
    cookies, cookie_string = parse_curl_file(curl_file)
    
    print(f"成功解析 {len(cookies)} 个 cookie 字段")
    
    # 提取关键字段
    key_cookies = extract_key_cookies(cookies)
    
    # 保存解析结果
    result = {
        'full_cookie_string': cookie_string,
        'all_cookies': cookies,
        'key_cookies': key_cookies
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"解析结果已保存到: {output_file}\n")
    
    return result


def load_cookies(cookie_file='cookies.json'):
    """
    从 cookies.json 文件加载 cookie 信息
    
    Args:
        cookie_file: cookie 文件路径
        
    Returns:
        dict: cookie 信息
    """
    if not os.path.exists(cookie_file):
        return None
    
    with open(cookie_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def login_with_cookies(cmd, cookies_data):
    """
    使用 cookie 登录
    优先使用完整的 cookie 字符串，这种方式更安全可靠
    
    Args:
        cmd: BaiduPCS-Go 命令
        cookies_data: cookie 数据字典
        
    Returns:
        bool: 登录是否成功
    """
    # 优先使用完整 cookie 字符串登录（更安全）
    cookie_string = cookies_data.get('full_cookie_string', '')
    
    if cookie_string:
        # 使用完整 cookie 字符串
        # BaiduPCS-Go 的 -cookies 参数格式：-cookies="cookie字符串"
        # 在 subprocess 中使用列表传递时，参数值中的引号会被保留
        # 这样 BaiduPCS-Go 可以正确解析 cookie 字符串
        login_cmd = [
            cmd,
            'login',
            f'-cookies="{cookie_string}"'
        ]
    else:
        # 如果没有完整 cookie 字符串，尝试使用 BDUSS + STOKEN
        key_cookies = cookies_data.get('key_cookies', {})
        
        if 'BDUSS' in key_cookies and 'STOKEN' in key_cookies:
            login_cmd = [
                cmd,
                'login',
                f"-bduss={key_cookies['BDUSS']}",
                f"-stoken={key_cookies['STOKEN']}"
            ]
        elif 'BDUSS' in key_cookies:
            login_cmd = [
                cmd,
                'login',
                f"-bduss={key_cookies['BDUSS']}"
            ]
        else:
            print("错误：无法找到有效的登录凭证！")
            print("请确保 cookies.json 中包含 full_cookie_string 或 key_cookies")
            return False
    
    print(f"执行登录命令: {cmd} login -cookies=\"...\" (cookie 字符串已隐藏)")
    print("正在登录...")
    
    try:
        result = subprocess.run(
            login_cmd,
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
            print("\n✅ 登录成功！")
            return True
        else:
            print(f"\n❌ 登录失败，返回码: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print(f"错误：找不到命令 {cmd}！")
        print("请确保 BaiduPCS-Go 已安装并在 PATH 中")
        return False
    except Exception as e:
        print(f"错误：登录过程中出现异常: {e}")
        return False


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
            print("当前登录状态:")
            print(result.stdout)
            return True
        else:
            return False
    except:
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
    if check_login_status(baidupcs_cmd):
        response = input("\n已检测到登录状态，是否重新登录？(y/N): ")
        if response.lower() != 'y':
            print("取消登录")
            return
    
    # 确定输入文件
    cookies_data = None
    
    # 如果提供了命令行参数
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
        
        # 判断是 curl.txt 还是 cookies.json
        if input_file.endswith('.txt') or 'curl' in input_file.lower():
            # 是 curl.txt 文件，解析它
            cookies_data = parse_and_save_cookies(input_file)
        else:
            # 假设是 cookies.json
            cookies_data = load_cookies(input_file)
            if not cookies_data:
                print(f"错误：找不到文件 {input_file}！")
                sys.exit(1)
    else:
        # 没有提供参数，自动查找
        # 优先查找 curl.txt
        if os.path.exists('curl.txt'):
            print("自动检测到 curl.txt 文件，开始解析...\n")
            cookies_data = parse_and_save_cookies('curl.txt')
        elif os.path.exists('cookies.json'):
            print("自动检测到 cookies.json 文件，直接使用...\n")
            cookies_data = load_cookies('cookies.json')
        else:
            print("错误：未找到 curl.txt 或 cookies.json 文件！")
            print("\n使用方法:")
            print("  python login.py [curl.txt 或 cookies.json]")
            print("\n或者将 curl.txt 放在当前目录下")
            sys.exit(1)
    
    # 执行登录
    success = login_with_cookies(baidupcs_cmd, cookies_data)
    
    if success:
        # 再次检查登录状态
        print("\n验证登录状态...")
        check_login_status(baidupcs_cmd)
    else:
        print("\n登录失败，请检查:")
        print("1. Cookie 是否有效（可能已过期）")
        print("2. BaiduPCS-Go 版本是否支持该登录方式")
        print("3. 网络连接是否正常")
        sys.exit(1)


if __name__ == '__main__':
    main()
