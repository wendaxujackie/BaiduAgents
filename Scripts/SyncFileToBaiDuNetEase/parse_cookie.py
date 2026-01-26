#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 解析脚本
从 curl.txt 文件中解析出 cookie 信息，提取 BDUSS 和 STOKEN 等关键字段
"""

import re
import sys
import os
from urllib.parse import unquote


def parse_curl_file(file_path):
    """
    从 curl.txt 文件中解析 cookie
    
    Args:
        file_path: curl.txt 文件路径
        
    Returns:
        dict: 包含解析出的 cookie 信息
    """
    if not os.path.exists(file_path):
        print(f"错误：文件 {file_path} 不存在！")
        sys.exit(1)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取 -b 参数后的 cookie 字符串
    # 匹配模式：-b 'cookie字符串' 或 -b "cookie字符串"
    # 注意：cookie 字符串中可能包含引号，需要正确处理
    # 由于 cookie 字符串可能很长，使用更简单的方法：逐行查找并提取
    
    lines = content.split('\n')
    cookie_string = None
    
    # 查找包含 -b 参数的行
    for i, line in enumerate(lines):
        if '-b' in line or '--cookie' in line:
            # 找到 -b 参数，提取引号内的内容
            # 先尝试单引号
            match = re.search(r"-b\s+'([^']*)'", line)
            if not match:
                # 尝试双引号
                match = re.search(r'-b\s+"([^"]*)"', line)
            
            if match:
                cookie_string = match.group(1)
                break
            else:
                # 如果引号跨行，需要合并多行
                # 找到开始引号
                start_idx = line.find("'")
                if start_idx == -1:
                    start_idx = line.find('"')
                
                if start_idx != -1:
                    quote_char = line[start_idx]
                    # 提取从引号开始的内容
                    remaining = line[start_idx+1:]
                    # 继续查找后续行，直到找到结束引号
                    for j in range(i+1, len(lines)):
                        end_idx = lines[j].find(quote_char)
                        if end_idx != -1:
                            # 找到结束引号
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
    # 处理可能包含引号的值（如 RT="..."）
    parts = re.split(r';\s*(?=\w+=)', cookie_string)
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # 分割键值对
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


def main():
    """主函数"""
    # 默认使用当前目录下的 curl.txt
    if len(sys.argv) > 1:
        curl_file = sys.argv[1]
    else:
        curl_file = 'curl.txt'
    
    print(f"正在解析文件: {curl_file}")
    
    # 解析 cookie
    cookies, cookie_string = parse_curl_file(curl_file)
    
    print(f"\n成功解析 {len(cookies)} 个 cookie 字段")
    
    # 提取关键字段
    key_cookies = extract_key_cookies(cookies)
    
    # 保存解析结果到文件
    output_file = 'cookies.json'
    import json
    result = {
        'full_cookie_string': cookie_string,
        'all_cookies': cookies,
        'key_cookies': key_cookies
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n解析结果已保存到: {output_file}")
    
    # 显示关键 cookie 信息
    print("\n关键 Cookie 信息:")
    if 'BDUSS' in key_cookies:
        bduss = key_cookies['BDUSS']
        print(f"BDUSS: {bduss[:50]}... (已截断)")
    else:
        print("警告：未找到 BDUSS！")
    
    if 'STOKEN' in key_cookies:
        stoken = key_cookies['STOKEN']
        print(f"STOKEN: {stoken}")
    else:
        print("警告：未找到 STOKEN！")
    
    # 生成登录命令提示
    print("\n登录命令提示:")
    print("优先使用完整 cookie 字符串登录（推荐，更安全）:")
    print(f"BaiduPCS-Go login -cookies=\"{cookie_string[:100]}...\" (已截断)")
    print("\n或者使用 BDUSS + STOKEN 登录:")
    if 'BDUSS' in key_cookies and 'STOKEN' in key_cookies:
        print(f"BaiduPCS-Go login -bduss={key_cookies['BDUSS']} -stoken={key_cookies['STOKEN']}")
    elif 'BDUSS' in key_cookies:
        print(f"BaiduPCS-Go login -bduss={key_cookies['BDUSS']}")
    else:
        print("（未找到 BDUSS 或 STOKEN）")


if __name__ == '__main__':
    main()
