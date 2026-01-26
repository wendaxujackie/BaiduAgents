#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测VPN代理端口
"""

import requests
import socket

def check_common_proxy_ports():
    """检测常见的VPN代理端口"""
    print("="*60)
    print("🔍 检测VPN代理端口")
    print("="*60)
    print()
    
    # 常见VPN代理端口（扩展更多端口）
    common_ports = [
        # Clash
        (7890, 'http', 'Clash HTTP'),
        (7891, 'socks5', 'Clash SOCKS5'),
        # V2Ray / Shadowsocks
        (1080, 'socks5', 'V2Ray/Shadowsocks SOCKS5'),
        (10808, 'socks5', 'V2Ray SOCKS5 (备用)'),
        # Surge
        (6152, 'http', 'Surge HTTP'),
        (6153, 'socks5', 'Surge SOCKS5'),
        # Shadowrocket
        (7890, 'http', 'Shadowrocket HTTP'),
        # 其他常见端口
        (8080, 'http', '通用HTTP代理'),
        (8888, 'http', '通用HTTP代理'),
        (8118, 'http', 'Privoxy'),
        (9050, 'socks5', 'Tor SOCKS5'),
        (1080, 'http', '通用SOCKS5转HTTP'),
    ]
    
    found_proxies = []
    
    for port, protocol, name in common_ports:
        proxy_url = f"{protocol}://127.0.0.1:{port}"
        print(f"🔍 检测 {name} ({proxy_url})...", end=" ")
        
        # 先检测端口是否开放
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        
        if result == 0:
            # 端口开放，测试代理是否可用
            try:
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                test_response = requests.get(
                    'https://httpbin.org/ip',
                    proxies=proxies,
                    timeout=5
                )
                if test_response.status_code == 200:
                    ip_info = test_response.json()
                    print(f"✅ 可用! 当前IP: {ip_info.get('origin', 'N/A')}")
                    found_proxies.append((proxy_url, name))
                else:
                    print("⚠️  端口开放但代理不可用")
            except Exception as e:
                print(f"⚠️  端口开放但测试失败: {str(e)[:30]}")
        else:
            print("❌ 端口未开放")
    
    print()
    print("="*60)
    if found_proxies:
        print(f"✅ 找到 {len(found_proxies)} 个可用代理:")
        for proxy_url, name in found_proxies:
            print(f"   - {name}: {proxy_url}")
        print()
        print("📋 使用方法:")
        print(f"   # 方法1: 使用命令行参数")
        print(f"   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy {found_proxies[0][0]}")
        print()
        print(f"   # 方法2: 创建proxies.txt文件")
        print(f"   echo '{found_proxies[0][0]}' > proxies.txt")
        print(f"   python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt")
    else:
        print("❌ 未找到可用的VPN代理")
        print()
        print("💡 提示:")
        print("   1. 确保VPN已启动")
        print("   2. 检查VPN设置中的代理端口")
        print("   3. 常见端口:")
        print("      - Clash: http://127.0.0.1:7890")
        print("      - V2Ray: socks5://127.0.0.1:1080")
        print("      - Surge: http://127.0.0.1:6152")
    print("="*60)

if __name__ == "__main__":
    try:
        check_common_proxy_ports()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

