#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开心电玩游戏下载工具
根据CSV文件下载游戏APK

用法:
    python3 kxdw_downloader.py games_50_pages.csv
    python3 kxdw_downloader.py games_50_pages.csv --start 10 --limit 5
    python3 kxdw_downloader.py games_50_pages.csv --chrome
"""

import argparse
import csv
import os
import zipfile
import re
import time
import random
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Dict, List, Tuple
from datetime import datetime

# 尝试导入urllib3的IncompleteRead异常（如果可用）
try:
    from urllib3.exceptions import IncompleteRead
except ImportError:
    # 如果urllib3不可用，创建一个占位符类
    class IncompleteRead(Exception):
        pass

# 设置线程异常处理，忽略pychrome后台线程的JSON解析错误
def handle_thread_exception(args):
    """处理线程异常，忽略pychrome后台线程的JSON解析错误"""
    exc_type = args.exc_type
    exc_value = args.exc_value
    exc_traceback = args.exc_traceback
    
    # 如果是pychrome的JSON解析错误，忽略它（这是后台线程的错误，不影响主程序）
    if exc_type:
        exc_type_name = exc_type.__name__ if hasattr(exc_type, '__name__') else str(exc_type)
        if 'JSONDecodeError' in exc_type_name or 'JSON' in exc_type_name:
            return  # 忽略JSON解析错误
    
    if exc_value:
        exc_value_str = str(exc_value)
        if 'JSON' in exc_value_str or 'Expecting value' in exc_value_str or 'json.decoder' in exc_value_str:
            return  # 忽略JSON相关错误
    
    # 检查是否来自pychrome的_recv_loop线程
    if exc_traceback:
        import traceback
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        if '_recv_loop' in tb_str and 'json.loads' in tb_str:
            return  # 忽略pychrome接收循环的JSON错误
    
    # 其他错误正常显示
    if exc_type and exc_value and exc_traceback:
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

# 设置全局线程异常处理（Python 3.8+）
if hasattr(threading, 'excepthook'):
    threading.excepthook = handle_thread_exception

try:
    import pychrome
except ImportError:
    pychrome = None

try:
    import requests
except ImportError:
    requests = None

# 导入百度建议词功能
try:
    import sys
    # 尝试从相对路径导入
    baidu_suggestion_path = Path(__file__).parent.parent / 'web_download_for_duduo' / 'baidu_suggestion.py'
    if baidu_suggestion_path.exists():
        sys.path.insert(0, str(baidu_suggestion_path.parent))
        from baidu_suggestion import get_baidu_suggestions
    else:
        # 如果找不到，尝试直接导入（如果已安装）
        from baidu_suggestion import get_baidu_suggestions
except ImportError:
    print("⚠️  无法导入 baidu_suggestion，将使用游戏名称作为文件夹名")
    get_baidu_suggestions = None


class KXDWDownloader:
    """开心电玩游戏下载工具"""
    
    # 常用User-Agent列表，模拟不同浏览器和操作系统
    USER_AGENTS = [
        # Chrome on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        # Chrome on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        # Chrome on Linux
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        # Firefox on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        # Firefox on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
        # Safari on macOS
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
        # Edge on Windows
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
    ]
    
    def __init__(self, csv_file: str, download_base_dir: str = "./downloads", 
                 use_chrome: bool = False, chrome_debug_url: str = "http://127.0.0.1:9222",
                 proxy_file: str = None, proxy: str = None):
        self.csv_file = Path(csv_file)
        self.download_base_dir = Path(download_base_dir)
        self.download_base_dir.mkdir(parents=True, exist_ok=True)
        
        # Chrome相关
        self.use_chrome = use_chrome and pychrome is not None
        self.chrome_debug_url = chrome_debug_url
        self.browser = None
        self.tab = None
        self._last_real_download_url = None  # 保存最后获取的真实下载地址，供requests下载使用
        
        # 代理相关
        self.proxies = []
        self.current_proxy_index = 0
        self._load_proxies(proxy_file, proxy)
        
        # 反检测相关：记录上次请求时间，用于控制请求频率
        self.last_request_time = 0
        self.request_count = 0
        
        # 读取CSV数据
        self.games = []
        self._load_csv()
        
        if self.use_chrome:
            self._connect_chrome()
    
    def _connect_chrome(self):
        """连接到Chrome调试端口"""
        if not pychrome:
            print("⚠️  pychrome未安装，将使用requests方式")
            self.use_chrome = False
            return False
        
        try:
            # Chrome本地连接不使用代理（临时取消代理环境变量）
            import os
            old_proxy_env = {}
            proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_env_vars:
                if var in os.environ:
                    old_proxy_env[var] = os.environ[var]
                    del os.environ[var]
            
            try:
                self.browser = pychrome.Browser(url=self.chrome_debug_url)
                print(f"✅ 已连接到 Chrome: {self.chrome_debug_url}")
                return True
            finally:
                # 恢复代理环境变量
                for var, value in old_proxy_env.items():
                    os.environ[var] = value
        except Exception as e:
            print(f"⚠️  无法连接到 Chrome 调试端口: {self.chrome_debug_url}")
            print(f"   将使用requests方式（可能被拦截）")
            self.use_chrome = False
            return False
    
    def _get_chrome_tab(self):
        """获取或创建Chrome标签页"""
        if not self.use_chrome or not self.browser:
            return None
        
        # 临时取消代理环境变量（Chrome本地连接不使用代理）
        import os
        old_proxy_env = {}
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_env_vars:
            if var in os.environ:
                old_proxy_env[var] = os.environ[var]
                del os.environ[var]
        
        # 设置NO_PROXY，排除本地地址
        old_no_proxy = os.environ.get('NO_PROXY', '')
        os.environ['NO_PROXY'] = '127.0.0.1,localhost,0.0.0.0'
        
        try:
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if self.tab:
                        try:
                            # 测试标签页是否仍然有效
                            self.tab.Runtime.evaluate(expression="1")
                            return self.tab
                        except Exception as e:
                            # 标签页已失效，重置
                            self.tab = None
                            if attempt < max_retries - 1:
                                print(f"   ⚠️  标签页连接断开，重新连接... ({attempt + 1}/{max_retries})")
                                time.sleep(1)
                    
                    # 重新获取或创建标签页
                    tabs = self.browser.list_tab()
                    if tabs:
                        self.tab = tabs[0]
                    else:
                        self.tab = self.browser.new_tab()
                    
                    self.tab.start()
                    self.tab.Network.enable()
                    self.tab.Page.enable()
                    self.tab.Runtime.evaluate(expression="1")  # 测试连接
                    
                    return self.tab
                except Exception as e:
                    error_msg = str(e)
                    if "websocket" in error_msg.lower() or "connection" in error_msg.lower():
                        if attempt < max_retries - 1:
                            print(f"   ⚠️  WebSocket连接异常，重试... ({attempt + 1}/{max_retries})")
                            # 重置标签页和浏览器连接
                            self.tab = None
                            time.sleep(2 + attempt)  # 递增等待时间：2秒、3秒、4秒
                            # 尝试重新连接浏览器（代理环境变量已取消）
                            try:
                                self.browser = pychrome.Browser(url=self.chrome_debug_url)
                            except Exception as browser_error:
                                print(f"   ⚠️  重新连接浏览器失败: {browser_error}")
                                # 如果浏览器连接失败，可能是Chrome没有运行
                                if attempt == max_retries - 2:  # 最后一次重试前
                                    print(f"   💡 提示: 请确保Chrome已启动并启用远程调试端口 {self.chrome_debug_url}")
                            continue
                    print(f"⚠️  获取Chrome标签页失败: {e}")
                    if attempt == max_retries - 1:
                        return None
            
            return None
        finally:
            # 恢复代理环境变量
            for var, value in old_proxy_env.items():
                os.environ[var] = value
            # 恢复NO_PROXY
            if old_no_proxy:
                os.environ['NO_PROXY'] = old_no_proxy
            elif 'NO_PROXY' in os.environ:
                del os.environ['NO_PROXY']
    
    def _load_csv(self):
        """加载CSV文件"""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV文件不存在: {self.csv_file}")
        
        with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 如果新列不存在，添加默认值"否"
                if '是否有安卓下载链接' not in row:
                    row['是否有安卓下载链接'] = '否'
                self.games.append(row)
        
        print(f"✅ 已加载 {len(self.games)} 个游戏")
    
    def _load_proxies(self, proxy_file: str = None, proxy: str = None):
        """加载代理列表"""
        # 如果指定了单个代理
        if proxy:
            self.proxies.append(proxy)
            print(f"✅ 已加载代理: {proxy}")
            return
        
        # 如果指定了代理文件
        if proxy_file:
            proxy_path = Path(proxy_file)
            if proxy_path.exists():
                with open(proxy_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            self.proxies.append(line)
                print(f"✅ 已从文件加载 {len(self.proxies)} 个代理")
            else:
                print(f"⚠️  代理文件不存在: {proxy_file}")
                return
        
        # 如果没有指定代理，先尝试检测本地VPN代理
        if not self.proxies:
            print(f"🔍 未指定代理，先检测本地VPN代理（Shadowrocket/Clash等）...")
            local_proxies = self._detect_local_vpn_proxy()
            if local_proxies:
                self.proxies = local_proxies
                print(f"✅ 检测到本地VPN代理: {self.proxies[0]}")
            else:
                print(f"⚠️  未检测到本地VPN代理")
                print(f"")
                print(f"💡 Shadowrocket用户请手动配置:")
                print(f"   1. 查看Shadowrocket设置中的HTTP代理端口（通常是7890）")
                print(f"   2. 使用命令: --proxy http://127.0.0.1:7890")
                print(f"   3. 或创建proxies.txt文件: echo 'http://127.0.0.1:7890' > proxies.txt")
                print(f"")
                print(f"⚠️  跳过免费代理获取（可用性较低），将不使用代理")
                print(f"   如果遇到IP限制，请手动配置VPN代理")
    
    def _detect_local_vpn_proxy(self) -> List[str]:
        """检测本地VPN代理端口"""
        if not requests:
            return []
        
        # 常见VPN代理端口（优先HTTP，因为不需要额外依赖）
        common_proxies = [
            # Shadowrocket / Clash HTTP（最常见）
            ('http://127.0.0.1:7890', 'Shadowrocket/Clash HTTP'),
            ('http://127.0.0.1:1082', 'Shadowrocket HTTP (1082)'),
            ('http://127.0.0.1:8080', '通用HTTP代理'),
            ('http://127.0.0.1:8888', '通用HTTP代理'),
            ('http://127.0.0.1:6152', 'Surge HTTP'),
            # SOCKS5（需要pysocks）
            ('socks5://127.0.0.1:1080', 'V2Ray/Shadowsocks SOCKS5'),
            ('socks5://127.0.0.1:7891', 'Clash SOCKS5'),
            ('socks5://127.0.0.1:6153', 'Surge SOCKS5'),
        ]
        
        for proxy_url, name in common_proxies:
            try:
                # 先检查端口是否开放（快速检测）
                import socket
                port = int(proxy_url.split(':')[-1].split('/')[0])
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                
                if result != 0:
                    continue  # 端口未开放，跳过
                
                # 端口开放，测试代理是否可用
                proxy_dict = self._format_proxy_for_requests(proxy_url)
                if not proxy_dict:
                    continue
                
                # 快速测试（使用简单的测试URL）
                test_response = requests.get(
                    'https://httpbin.org/ip',
                    proxies=proxy_dict,
                    timeout=3
                )
                if test_response.status_code == 200:
                    ip_info = test_response.json()
                    print(f"   ✅ 检测到 {name}: {proxy_url}")
                    print(f"      当前IP: {ip_info.get('origin', 'N/A')}")
                    return [proxy_url]
            except Exception as e:
                continue
        
        return []
    
    def _fetch_free_proxies(self) -> List[str]:
        """自动获取免费代理列表"""
        if not requests:
            return []
        
        proxies = []
        
        # 从免费代理API获取
        print(f"   📡 从免费代理服务获取代理列表...")
        
        # 尝试多个免费代理API源
        proxy_sources = [
            # ProxyScrape API (返回 ip:port 格式)
            ("https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all", "ip:port"),
            # GitHub代理列表
            ("https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt", "ip:port"),
            ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt", "ip:port"),
            ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt", "ip:port"),
        ]
        
        for source_url, format_type in proxy_sources:
            try:
                print(f"   🔍 尝试从代理源获取...")
                response = requests.get(source_url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                })
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    for line in lines:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            # 格式化为 http://ip:port
                            if not line.startswith('http'):
                                proxy = f"http://{line}"
                            else:
                                proxy = line
                            # 去重
                            if proxy not in proxies:
                                proxies.append(proxy)
                    
                    if proxies:
                        print(f"   ✅ 获取到 {len(proxies)} 个代理候选")
                        break
            except Exception as e:
                continue
        
        # 测试代理可用性（快速测试，找到3-5个可用即可）
        if proxies:
            print(f"   🧪 快速测试代理可用性（测试前50个，找到3个即停止）...")
            tested_proxies = []
            # 使用简单的测试URL
            test_url = "https://httpbin.org/ip"
            
            for i, proxy in enumerate(proxies[:50], 1):  # 只测试前50个
                if len(tested_proxies) >= 3:  # 找到3个可用代理就够了
                    print(f"   ✅ 已找到足够的可用代理，停止测试")
                    break
                
                try:
                    proxy_dict = self._format_proxy_for_requests(proxy)
                    if not proxy_dict:
                        continue
                    
                    # 快速测试（超时时间短）
                    test_response = requests.get(
                        test_url, 
                        proxies=proxy_dict, 
                        timeout=3,  # 缩短超时时间
                        headers={
                            'User-Agent': 'Mozilla/5.0'
                        }
                    )
                    if test_response.status_code == 200:
                        tested_proxies.append(proxy)
                        ip_info = test_response.json()
                        print(f"   ✅ [{i}] 代理可用: {proxy} (IP: {ip_info.get('origin', 'N/A')[:20]})")
                    
                except:
                    # 静默失败，继续测试下一个
                    continue
            
            if tested_proxies:
                print(f"   ✅ 总共找到 {len(tested_proxies)} 个可用代理")
                return tested_proxies
            else:
                print(f"   ⚠️  测试了50个代理，都不可用")
                print(f"   💡 提示: 免费代理可用性较低")
                print(f"   💡 建议: 使用VPN代理或付费代理服务")
        else:
            print(f"   ⚠️  未能从代理源获取到代理列表")
        
        return []
    
    def _get_next_proxy(self) -> Optional[str]:
        """获取下一个代理（轮换）"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _get_random_user_agent(self) -> str:
        """随机获取一个User-Agent"""
        return random.choice(self.USER_AGENTS)
    
    def _get_browser_headers(self, referer: str = None, is_download: bool = False) -> dict:
        """生成完整的浏览器请求头，模拟真实浏览器"""
        user_agent = self._get_random_user_agent()
        
        # 根据User-Agent判断操作系统，设置相应的Accept-Language
        if 'Windows' in user_agent:
            accept_language = random.choice([
                'zh-CN,zh;q=0.9,en;q=0.8',
                'zh-CN,zh;q=0.9',
                'en-US,en;q=0.9,zh-CN;q=0.8'
            ])
        elif 'Macintosh' in user_agent:
            accept_language = random.choice([
                'zh-CN,zh;q=0.9,en;q=0.8',
                'zh-CN,zh;q=0.9',
                'en-US,en;q=0.9,zh-CN;q=0.8'
            ])
        else:
            accept_language = 'zh-CN,zh;q=0.9,en;q=0.8'
        
        # 基础请求头
        headers = {
            'User-Agent': user_agent,
            'Accept-Language': accept_language,
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': random.choice(['max-age=0', 'no-cache', 'no-store']),
        }
        
        # 根据请求类型设置不同的Accept头
        if is_download:
            headers['Accept'] = '*/*'
        else:
            headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7'
        
        # 添加Sec-Fetch-* 头（现代浏览器的特征）
        if not is_download:
            headers['Sec-Fetch-Dest'] = 'document'
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-Site'] = random.choice(['none', 'same-origin', 'same-site'])
            headers['Sec-Fetch-User'] = '?1'
        else:
            headers['Sec-Fetch-Dest'] = 'empty'
            headers['Sec-Fetch-Mode'] = 'no-cors'
            headers['Sec-Fetch-Site'] = random.choice(['same-origin', 'cross-site'])
        
        # 添加Referer
        if referer:
            headers['Referer'] = referer
        elif not is_download:
            headers['Referer'] = 'https://www.kxdw.com/'
        
        # 随机添加一些额外的浏览器特征头
        if random.random() > 0.5:  # 50%概率添加
            headers['DNT'] = random.choice(['1', '0'])  # Do Not Track
        
        return headers
    
    def _random_delay(self, min_seconds: float = 0.5, max_seconds: float = 2.0):
        """随机延迟，模拟人类行为，并控制请求频率"""
        # 计算距离上次请求的时间
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # 如果距离上次请求时间太短，增加延迟
        min_interval = random.uniform(1.0, 3.0)  # 最小请求间隔1-3秒
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last + random.uniform(min_seconds, max_seconds)
        else:
            wait_time = random.uniform(min_seconds, max_seconds)
        
        if wait_time > 0:
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
        self.request_count += 1
    
    def _format_proxy_for_requests(self, proxy: Optional[str]) -> dict:
        """将代理字符串格式化为requests库需要的格式"""
        if not proxy:
            return {}
        
        # 支持 http, https, socks5
        if proxy.startswith('http://') or proxy.startswith('https://'):
            return {
                'http': proxy,
                'https': proxy
            }
        elif proxy.startswith('socks5://'):
            # 需要安装 requests[socks] 或 PySocks
            try:
                import socks
                return {
                    'http': proxy,
                    'https': proxy
                }
            except ImportError:
                print(f"   ⚠️  使用SOCKS5代理需要安装PySocks: pip install pysocks")
                return {}
        else:
            # 默认当作HTTP代理
            if not proxy.startswith('http://'):
                proxy = 'http://' + proxy
            return {
                'http': proxy,
                'https': proxy
            }
    
    def _save_csv(self):
        """保存CSV文件"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            if not self.games:
                return
            
            fieldnames = ['游戏名称', '详情页链接', '是否已下载', '是否有安卓下载链接']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.games)
    
    def _calculate_similarity(self, query: str, suggestion: str) -> float:
        """计算查询词与建议词之间的相似度（0-1之间）
        
        采用多种策略计算相似度：
        1. 完全匹配得分最高
        2. 包含关系得分次高
        3. 公共字符比例作为基础得分
        """
        # 标准化：转小写，移除空格和常见标点
        def normalize(s):
            s = s.lower()
            # 移除空格、括号、冒号等常见符号
            s = re.sub(r'[\s\(\)\[\]【】（）:：\-_]', '', s)
            return s
        
        query_norm = normalize(query)
        suggestion_norm = normalize(suggestion)
        
        if not query_norm or not suggestion_norm:
            return 0.0
        
        # 完全匹配
        if query_norm == suggestion_norm:
            return 1.0
        
        # 包含关系（查询词包含在建议词中）
        if query_norm in suggestion_norm:
            # 查询词越长占建议词比例越大，得分越高
            return 0.85 + 0.15 * (len(query_norm) / len(suggestion_norm))
        
        # 包含关系（建议词包含在查询词中）
        if suggestion_norm in query_norm:
            return 0.75 + 0.15 * (len(suggestion_norm) / len(query_norm))
        
        # 计算最长公共子串比例
        def longest_common_substring(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            max_len = 0
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                        max_len = max(max_len, dp[i][j])
            return max_len
        
        lcs_len = longest_common_substring(query_norm, suggestion_norm)
        lcs_ratio = lcs_len / max(len(query_norm), len(suggestion_norm))
        
        # 计算公共字符比例（Jaccard相似度）
        query_chars = set(query_norm)
        suggestion_chars = set(suggestion_norm)
        common_chars = query_chars & suggestion_chars
        jaccard = len(common_chars) / len(query_chars | suggestion_chars) if (query_chars | suggestion_chars) else 0
        
        # 综合得分：最长公共子串比例权重0.6，Jaccard相似度权重0.4
        similarity = lcs_ratio * 0.6 + jaccard * 0.4
        
        return similarity
    
    def _get_folder_name(self, game_name: str) -> str:
        """使用百度建议词获取文件夹名，选择关联性最大的建议词
        
        策略：
        1. 获取所有百度建议词
        2. 计算每个建议词与游戏名的相似度
        3. 选择相似度最高且超过阈值的建议词
        4. 如果没有满足条件的建议词，使用原始游戏名
        """
        if get_baidu_suggestions:
            try:
                suggestions = get_baidu_suggestions(game_name)
                if suggestions:
                    # 计算每个建议词与游戏名的相似度
                    best_suggestion = None
                    best_similarity = 0.0
                    min_similarity_threshold = 0.3  # 最小相似度阈值
                    
                    print(f"   📋 百度建议词列表:")
                    for i, suggestion in enumerate(suggestions[:5], 1):  # 只显示前5个
                        similarity = self._calculate_similarity(game_name, suggestion)
                        print(f"      {i}. {suggestion} (相似度: {similarity:.2f})")
                        if similarity > best_similarity:
                            best_similarity = similarity
                            best_suggestion = suggestion
                    
                    # 如果最佳相似度高于阈值，使用建议词；否则使用原始游戏名
                    if best_suggestion and best_similarity >= min_similarity_threshold:
                        folder_name = best_suggestion
                        print(f"   ✅ 选择建议词: {folder_name} (相似度: {best_similarity:.2f})")
                    else:
                        folder_name = game_name
                        print(f"   ⚠️  未找到高相似度建议词 (最高: {best_similarity:.2f} < {min_similarity_threshold})")
                        print(f"   📁 使用原始名称: {folder_name}")
                    
                    folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
                    return folder_name
            except Exception as e:
                print(f"⚠️  获取建议词失败: {e}，使用游戏名称")
        
        # 如果没有建议词，使用游戏名称
        folder_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)
        return folder_name
    
    def _parse_size_to_mb(self, size_str: str) -> float:
        """将大小字符串转换为MB数值"""
        if not size_str:
            return 0.0
        
        size_str = size_str.strip().upper()
        
        # 匹配数字和单位
        match = re.match(r'(\d+\.?\d*)\s*([MG]B?)', size_str)
        if not match:
            return 0.0
        
        value = float(match.group(1))
        unit = match.group(2) or 'M'
        
        # 转换为MB
        if 'G' in unit:
            value = value * 1024
        
        return value
    
    def _parse_game_detail(self, page_url: str) -> Optional[Dict]:
        """解析游戏详情页，提取文件大小和下载地址"""
        if self.use_chrome:
            return self._parse_with_chrome(page_url)
        else:
            print(f"   ⚠️  使用requests模式，可能被服务器检测")
            print(f"   💡 如果遇到问题，建议使用Chrome模式: --chrome")
            return self._parse_with_requests(page_url)
    
    def _parse_with_chrome(self, page_url: str) -> Optional[Dict]:
        """使用Chrome解析详情页"""
        tab = self._get_chrome_tab()
        if not tab:
            return self._parse_with_requests(page_url)
        
        try:
            print(f"   🌐 使用Chrome访问详情页...")
            
            # 使用重试机制处理 websocket 异常
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    tab.Page.navigate(url=page_url)
                    break
                except Exception as e:
                    error_msg = str(e)
                    if "websocket" in error_msg.lower() and attempt < max_retries - 1:
                        print(f"   ⚠️  WebSocket异常，重新获取标签页... ({attempt + 1}/{max_retries})")
                        time.sleep(1)
                        # 重新获取标签页
                        tab = self._get_chrome_tab()
                        if not tab:
                            return self._parse_with_requests(page_url)
                        continue
                    else:
                        raise e
            
            # 等待页面加载
            wait_time = random.uniform(2, 4)
            time.sleep(wait_time)
            
            try:
                tab.Page.loadEventFired()
                time.sleep(1)
            except:
                pass
            
            # 滚动到页面底部，确保"本地下载地址"节点加载出来
            print(f"   📜 滚动到页面底部...")
            # 渐进式滚动，确保所有内容都加载，每次滚动后随机停留
            scroll_to_bottom_js = """
            (function() {
                let lastHeight = 0;
                let currentHeight = document.body.scrollHeight;
                let scrollCount = 0;
                const maxScrolls = 20; // 最多滚动20次
                
                // 渐进式滚动到底部
                while (currentHeight !== lastHeight && scrollCount < maxScrolls) {
                    lastHeight = currentHeight;
                    window.scrollTo(0, currentHeight);
                    // 随机等待时间（500-2000ms），模拟人类行为
                    const waitTime = Math.floor(Math.random() * 1500) + 500;
                    const startTime = Date.now();
                    while (Date.now() - startTime < waitTime) {
                        // 等待
                    }
                    currentHeight = document.body.scrollHeight;
                    scrollCount++;
                }
                
                // 最后再滚动一次确保到底
                window.scrollTo(0, document.body.scrollHeight);
                
                return {
                    finalHeight: document.body.scrollHeight,
                    scrollCount: scrollCount
                };
            })();
            """
            
            # 使用重试机制处理滚动操作
            try:
                scroll_result = tab.Runtime.evaluate(expression=scroll_to_bottom_js, returnByValue=True)
                scroll_info = scroll_result.get("result", {}).get("value", {})
                print(f"   ✅ 滚动完成，页面高度: {scroll_info.get('finalHeight', 0)}px，滚动次数: {scroll_info.get('scrollCount', 0)}")
            except Exception as e:
                error_msg = str(e)
                if "websocket" in error_msg.lower():
                    print(f"   ⚠️  滚动时WebSocket异常，切换到requests模式")
                    return self._parse_with_requests(page_url)
                raise e
            
            # 滚动完成后随机停留（1-3秒），模拟人类阅读行为
            wait_after_scroll = random.uniform(1.0, 3.0)
            print(f"   ⏳ 滚动后随机停留 {wait_after_scroll:.1f} 秒...")
            time.sleep(wait_after_scroll)
            
            # 再次检查并滚动，确保"本地下载地址"节点已加载
            try:
                check_and_scroll_js = """
                (function() {
                    const hasLocalDownload = document.body.innerText.includes('本地下载地址');
                    if (!hasLocalDownload) {
                        // 如果还没找到，再滚动一次
                        window.scrollTo(0, document.body.scrollHeight);
                        // 随机等待时间（800-1500ms），模拟人类行为
                        const waitTime = Math.floor(Math.random() * 700) + 800;
                        const startTime = Date.now();
                        while (Date.now() - startTime < waitTime) {
                            // 等待
                        }
                        return false;
                    }
                    return true;
                })();
                """
                check_result = tab.Runtime.evaluate(expression=check_and_scroll_js, returnByValue=True)
                if not check_result.get("result", {}).get("value", True):
                    print(f"   ⏳ 等待'本地下载地址'节点加载...")
                    # 随机等待时间（1.5-3秒），模拟人类阅读行为
                    wait_time = random.uniform(1.5, 3.0)
                    print(f"   ⏳ 随机停留 {wait_time:.1f} 秒...")
                    time.sleep(wait_time)
            except Exception as e:
                error_msg = str(e)
                if "websocket" in error_msg.lower():
                    print(f"   ⚠️  检查时WebSocket异常，继续尝试解析")
                else:
                    pass  # 忽略其他异常，继续执行
            
            # 提取游戏信息
            extract_info_js = """
            (function() {
                const info = {
                    size: '',
                    download_url: ''
                };
                
                // 提取文件大小 - 专门从 ul.azgm_txtList 的 li 标签中提取
                const ul = document.querySelector('ul.azgm_txtList');
                if (ul) {
                    const lis = ul.querySelectorAll('li');
                    for (let li of lis) {
                        const text = (li.textContent || li.innerText || '').trim();
                        // 查找包含大小信息的li（通常包含"MB"或"GB"）
                        if (text.includes('MB') || text.includes('GB') || text.includes('Mb') || text.includes('Gb')) {
                            // 提取大小信息（匹配 "大小：87.52M" 或 "87.52MB" 等格式）
                            const sizeMatch = text.match(/(?:大小[：:]?\\s*)?(\\d+\\.?\\d*)\\s*([MG]B?)/i);
                            if (sizeMatch) {
                                info.size = sizeMatch[1] + sizeMatch[2].toUpperCase();
                                if (!info.size.includes('B')) {
                                    info.size += 'B';  // 如果只有M或G，添加B
                                }
                                break;
                            }
                        }
                    }
                }
                
                // 如果没找到，尝试在整个页面中查找（备选方案）
                if (!info.size) {
                    const sizePatterns = [
                        /大小[：:]\\s*(\\d+\\.?\\d*)\\s*([MG]B?)/i,
                        /文件大小[：:]\\s*(\\d+\\.?\\d*)\\s*([MG]B?)/i,
                        /(\\d+\\.?\\d*)\\s*([MG]B)/i
                    ];
                    
                    const allText = document.body.innerText || document.body.textContent || '';
                    for (let pattern of sizePatterns) {
                        const match = allText.match(pattern);
                        if (match) {
                            info.size = match[1] + (match[2] || 'MB').toUpperCase();
                            if (!info.size.includes('B')) {
                                info.size += 'B';
                            }
                            break;
                        }
                    }
                }
                
                // 提取下载地址 - 专门查找dt标签（包含"本地下载地址"）下的a标签
                function findDownloadLink() {
                    const debug = {
                        dtTagsFound: 0,
                        matchingDtTags: [],
                        linksFound: [],
                        rejectedLinks: []
                    };
                    
                    // 方法1: 查找所有dt标签，找到包含"本地下载地址"的dt标签
                    const allDtTags = document.querySelectorAll('dt');
                    debug.dtTagsFound = allDtTags.length;
                    
                    for (let dt of allDtTags) {
                        const text = dt.textContent || dt.innerText || '';
                        if (text.includes('本地下载地址：') || text.includes('本地下载地址')) {
                            debug.matchingDtTags.push({
                                text: text.trim().substring(0, 50),
                                hasNextSibling: !!dt.nextElementSibling,
                                nextSiblingTag: dt.nextElementSibling ? dt.nextElementSibling.tagName : null
                            });
                            
                            // 查找dt标签的下一个兄弟节点（通常是dd标签）
                            let nextSibling = dt.nextElementSibling;
                            if (nextSibling) {
                                // 在dd标签中查找a标签
                                const links = nextSibling.querySelectorAll('a[href]');
                                for (let link of links) {
                                    let href = link.href || link.getAttribute('href') || '';
                                    const linkText = (link.textContent || link.innerText || '').trim();
                                    
                                    if (href) {
                                        // 转换为完整URL
                                        if (!href.startsWith('http')) {
                                            if (href.startsWith('/')) {
                                                href = window.location.origin + href;
                                            } else {
                                                href = window.location.origin + '/' + href;
                                            }
                                        }
                                        
                                        // 判断是否为HTML页面
                                        const isHtml = href.endsWith('.html') || 
                                                      href.endsWith('.htm') || 
                                                      href.includes('kxdw.com/android/') ||
                                                      href.includes('javascript:') ||
                                                      href.includes('#');
                                        
                                        if (isHtml) {
                                            debug.rejectedLinks.push({
                                                href: href.substring(0, 100),
                                                reason: href.endsWith('.html') ? '以.html结尾' :
                                                        href.endsWith('.htm') ? '以.htm结尾' :
                                                        href.includes('kxdw.com/android/') ? '包含详情页路径' :
                                                        href.includes('javascript:') ? 'javascript链接' : '包含#锚点'
                                            });
                                            continue;
                                        }
                                        
                                        debug.linksFound.push({
                                            href: href.substring(0, 100),
                                            text: linkText.substring(0, 30),
                                            source: 'dt标签的dd兄弟节点'
                                        });
                                        
                                        if (!href.includes('javascript:') && !href.includes('#')) {
                                            return {url: href, debug: debug};
                                        }
                                    }
                                }
                            }
                            
                            // 如果dd标签中没有找到，在dt标签的父元素中查找
                            let parent = dt.parentElement;
                            if (parent) {
                                const links = parent.querySelectorAll('a[href]');
                                for (let link of links) {
                                    let href = link.href || link.getAttribute('href') || '';
                                    const linkText = (link.textContent || link.innerText || '').trim();
                                    
                                    if (href) {
                                        if (!href.startsWith('http')) {
                                            if (href.startsWith('/')) {
                                                href = window.location.origin + href;
                                            } else {
                                                href = window.location.origin + '/' + href;
                                            }
                                        }
                                        
                                        // 判断是否为HTML页面
                                        const isHtml = href.endsWith('.html') || 
                                                      href.endsWith('.htm') || 
                                                      href.includes('kxdw.com/android/') ||
                                                      href.includes('javascript:') ||
                                                      href.includes('#');
                                        
                                        if (isHtml) {
                                            debug.rejectedLinks.push({
                                                href: href.substring(0, 100),
                                                reason: href.endsWith('.html') ? '以.html结尾' :
                                                        href.endsWith('.htm') ? '以.htm结尾' :
                                                        href.includes('kxdw.com/android/') ? '包含详情页路径' :
                                                        href.includes('javascript:') ? 'javascript链接' : '包含#锚点'
                                            });
                                            continue;
                                        }
                                        
                                        debug.linksFound.push({
                                            href: href.substring(0, 100),
                                            text: linkText.substring(0, 30),
                                            source: 'dt标签的父元素'
                                        });
                                        
                                        if (!href.includes('javascript:') && !href.includes('#')) {
                                            return {url: href, debug: debug};
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    // 方法2: 如果没找到dt标签，使用通用方法查找
                    const allElements = document.querySelectorAll('*');
                    for (let el of allElements) {
                        const text = el.textContent || el.innerText || '';
                        if (text.includes('本地下载地址')) {
                            // 查找下一个兄弟节点
                            let nextSibling = el.nextElementSibling;
                            if (nextSibling) {
                                const links = nextSibling.querySelectorAll('a[href]');
                                for (let link of links) {
                                    let href = link.href || link.getAttribute('href') || '';
                                    const linkText = (link.textContent || link.innerText || '').trim();
                                    
                                    if (href) {
                                        if (!href.startsWith('http')) {
                                            if (href.startsWith('/')) {
                                                href = window.location.origin + href;
                                            } else {
                                                href = window.location.origin + '/' + href;
                                            }
                                        }
                                        
                                        // 判断是否为HTML页面
                                        const isHtml = href.endsWith('.html') || 
                                                      href.endsWith('.htm') || 
                                                      href.includes('kxdw.com/android/') ||
                                                      href.includes('javascript:') ||
                                                      href.includes('#');
                                        
                                        if (isHtml) {
                                            debug.rejectedLinks.push({
                                                href: href.substring(0, 100),
                                                reason: href.endsWith('.html') ? '以.html结尾' :
                                                        href.endsWith('.htm') ? '以.htm结尾' :
                                                        href.includes('kxdw.com/android/') ? '包含详情页路径' :
                                                        href.includes('javascript:') ? 'javascript链接' : '包含#锚点'
                                            });
                                            continue;
                                        }
                                        
                                        debug.linksFound.push({
                                            href: href.substring(0, 100),
                                            text: linkText.substring(0, 30),
                                            source: '通用方法-兄弟节点'
                                        });
                                        
                                        if (!href.includes('javascript:') && !href.includes('#')) {
                                            return {url: href, debug: debug};
                                        }
                                    }
                                }
                            }
                            
                            // 在父元素中查找
                            let parent = el.parentElement;
                            if (parent) {
                                const links = parent.querySelectorAll('a[href]');
                                for (let link of links) {
                                    let href = link.href || link.getAttribute('href') || '';
                                    const linkText = (link.textContent || link.innerText || '').trim();
                                    
                                    if (href) {
                                        if (!href.startsWith('http')) {
                                            if (href.startsWith('/')) {
                                                href = window.location.origin + href;
                                            } else {
                                                href = window.location.origin + '/' + href;
                                            }
                                        }
                                        
                                        // 判断是否为HTML页面
                                        const isHtml = href.endsWith('.html') || 
                                                      href.endsWith('.htm') || 
                                                      href.includes('kxdw.com/android/') ||
                                                      href.includes('javascript:') ||
                                                      href.includes('#');
                                        
                                        if (isHtml) {
                                            debug.rejectedLinks.push({
                                                href: href.substring(0, 100),
                                                reason: href.endsWith('.html') ? '以.html结尾' :
                                                        href.endsWith('.htm') ? '以.htm结尾' :
                                                        href.includes('kxdw.com/android/') ? '包含详情页路径' :
                                                        href.includes('javascript:') ? 'javascript链接' : '包含#锚点'
                                            });
                                            continue;
                                        }
                                        
                                        debug.linksFound.push({
                                            href: href.substring(0, 100),
                                            text: linkText.substring(0, 30),
                                            source: '通用方法-父元素'
                                        });
                                        
                                        if (!href.includes('javascript:') && !href.includes('#')) {
                                            return {url: href, debug: debug};
                                        }
                                    }
                                }
                            }
                        }
                    }
                    
                    return {url: null, debug: debug};
                }
                
                const result = findDownloadLink();
                if (result && result.url) {
                    info.download_url = result.url;
                    info.debug = result.debug;
                } else if (result && result.debug) {
                    info.debug = result.debug;
                }
                
                // 3. 如果没找到，尝试查找包含下载相关关键词的链接（备用方案）
                if (!info.download_url) {
                    const allLinks = document.querySelectorAll('a[href]');
                    const downloadKeywords = ['下载', 'download', 'down', 'apk'];
                    for (let link of allLinks) {
                        let href = link.href || link.getAttribute('href') || '';
                        const text = (link.textContent || link.innerText || '').toLowerCase();
                        
                        if (href && !href.startsWith('http')) {
                            if (href.startsWith('/')) {
                                href = window.location.origin + href;
                            } else {
                                href = window.location.origin + '/' + href;
                            }
                        }
                        
                        // 检查链接或文本中是否包含下载相关关键词，且不是HTML页面
                        const hasKeyword = downloadKeywords.some(kw => 
                            href.toLowerCase().includes(kw) || text.includes(kw)
                        );
                        
                        if (href && hasKeyword && !href.includes('javascript:') && 
                            !href.endsWith('.html') && !href.endsWith('.htm') &&
                            !href.includes('kxdw.com/android/')) {
                            info.download_url = href;
                            break;
                        }
                    }
                }
                
                return info;
            })();
            """
            
            # 使用重试机制处理解析操作
            try:
                result = tab.Runtime.evaluate(expression=extract_info_js, returnByValue=True)
                info = result.get("result", {}).get("value", {})
            except Exception as e:
                error_msg = str(e)
                if "websocket" in error_msg.lower():
                    print(f"   ⚠️  解析时WebSocket异常，切换到requests模式")
                    return self._parse_with_requests(page_url)
                raise e
            
            # 输出调试信息
            debug_info = info.get('debug', {})
            if debug_info:
                print(f"   📊 调试信息:")
                print(f"      - 找到 {debug_info.get('dtTagsFound', 0)} 个dt标签")
                print(f"      - 匹配的dt标签: {len(debug_info.get('matchingDtTags', []))} 个")
                if debug_info.get('matchingDtTags'):
                    for i, dt in enumerate(debug_info['matchingDtTags'], 1):
                        print(f"        {i}. 文本: {dt.get('text', '')}")
                        print(f"           下一个兄弟节点: {dt.get('nextSiblingTag', '无')}")
                print(f"      - 找到的候选链接: {len(debug_info.get('linksFound', []))} 个")
                if debug_info.get('linksFound'):
                    for i, link in enumerate(debug_info['linksFound'], 1):
                        print(f"        {i}. {link.get('href', '')[:80]}...")
                        print(f"           来源: {link.get('source', '')}, 文本: {link.get('text', '')}")
                print(f"      - 被拒绝的链接: {len(debug_info.get('rejectedLinks', []))} 个")
                if debug_info.get('rejectedLinks'):
                    for i, link in enumerate(debug_info['rejectedLinks'], 1):
                        print(f"        {i}. {link.get('href', '')[:80]}...")
                        print(f"           原因: {link.get('reason', '未知')}")
            
            # 调试信息：如果没找到下载链接，输出调试信息
            if not info.get('download_url'):
                debug_js = """
                (function() {
                    const debug = {
                        foundLocalDownloadText: false,
                        foundLinks: []
                    };
                    
                    // 检查是否找到"本地下载地址"文本
                    const allText = document.body.innerText || document.body.textContent || '';
                    debug.foundLocalDownloadText = allText.includes('本地下载地址');
                    
                    // 查找所有包含"本地下载地址"的元素
                    const allElements = document.querySelectorAll('*');
                    for (let el of allElements) {
                        const text = el.textContent || el.innerText || '';
                        if (text.includes('本地下载地址')) {
                            const links = el.querySelectorAll('a[href]');
                            debug.foundLinks.push({
                                element: el.tagName,
                                className: el.className,
                                linksCount: links.length,
                                links: Array.from(links).map(l => l.href || l.getAttribute('href')).slice(0, 3)
                            });
                        }
                    }
                    
                    return debug;
                })();
                """
                try:
                    debug_result = tab.Runtime.evaluate(expression=debug_js, returnByValue=True)
                    debug_info = debug_result.get("result", {}).get("value", {})
                    if debug_info.get('foundLocalDownloadText'):
                        print(f"   ⚠️  找到'本地下载地址'文本，但未找到下载链接")
                        if debug_info.get('foundLinks'):
                            print(f"   📋 找到 {len(debug_info['foundLinks'])} 个包含该文本的元素")
                    else:
                        print(f"   ⚠️  未找到'本地下载地址'文本")
                except:
                    pass  # 忽略调试信息的异常
            
            return info
            
        except Exception as e:
            error_msg = str(e)
            if "websocket" in error_msg.lower():
                print(f"   ⚠️  Chrome WebSocket异常: {e}，切换到requests模式")
            else:
                print(f"   ⚠️  Chrome解析失败: {e}，尝试使用requests")
            return self._parse_with_requests(page_url)
    
    def _parse_with_requests(self, page_url: str) -> Optional[Dict]:
        """使用requests解析详情页"""
        if not requests:
            return None
        
        try:
            # 使用Session保持Cookie和连接
            session = requests.Session()
            
            # 获取代理
            proxy = self._get_next_proxy()
            proxies = self._format_proxy_for_requests(proxy)
            if proxies:
                print(f"   🌐 使用代理: {list(proxies.values())[0]}")
            
            # 反检测措施：先访问首页获取Cookie，模拟真实用户行为
            print(f"   🔍 先访问首页获取Cookie（反检测措施）...")
            try:
                # 使用随机User-Agent和完整请求头
                home_headers = self._get_browser_headers()
                home_response = session.get('https://www.kxdw.com/', headers=home_headers, proxies=proxies, timeout=15, allow_redirects=True)
                # 随机延迟，模拟人类行为
                self._random_delay(1.0, 3.0)
            except Exception as e:
                print(f"   ⚠️  访问首页失败: {e}，继续尝试访问详情页")
            
            # 随机延迟，模拟人类浏览行为
            self._random_delay(0.5, 1.5)
            
            # 使用新的随机User-Agent和完整请求头访问详情页
            headers = self._get_browser_headers(referer='https://www.kxdw.com/')
            response = session.get(page_url, headers=headers, proxies=proxies, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # 检查是否被重定向到127.0.0.1或localhost
            final_url = response.url
            if '127.0.0.1' in final_url or 'localhost' in final_url:
                print(f"   ❌ 检测到重定向到本地地址: {final_url}")
                print(f"   ⚠️  网站检测到爬虫行为，requests模式无法绕过")
                print(f"   💡 强烈建议使用Chrome模式: python3 kxdw_downloader.py games_50_pages.csv --chrome")
                return None
            
            # 检查响应内容是否包含错误信息
            if len(response.text) < 100:
                print(f"   ⚠️  响应内容过短，可能是错误页面")
                print(f"   响应内容: {response.text[:200]}")
                return None
            
            # 检查响应内容是否为"error"（IP限制的情况）
            if response.text.strip().lower() == 'error' or response.text.strip().startswith('error'):
                print(f"   ❌ 服务器返回'error'，可能是IP地址被限制")
                print(f"   💡 解决方案:")
                print(f"      1. 切换网络（如使用5G/移动网络）")
                print(f"      2. 使用VPN或代理服务器")
                print(f"      3. 更换网络环境后重试")
                return None
            
            # 检查响应内容是否包含反爬虫提示
            if '127.0.0.1' in response.text or 'localhost' in response.text or 'access denied' in response.text.lower():
                print(f"   ❌ 响应内容包含反爬虫提示")
                print(f"   💡 建议使用Chrome模式: python3 kxdw_downloader.py games_50_pages.csv --chrome")
                return None
            
            info = {
                'size': '',
                'download_url': '',
                'debug': {
                    'dtTagsFound': 0,
                    'linksFound': [],
                    'rejectedLinks': []
                }
            }
            
            # 提取文件大小 - 专门从 ul.azgm_txtList 的 li 标签中提取
            # 首先查找 ul class="azgm_txtList"
            ul_pattern = r'<ul[^>]*class=["\']azgm_txtList["\'][^>]*>(.*?)</ul>'
            ul_match = re.search(ul_pattern, response.text, re.DOTALL | re.IGNORECASE)
            if ul_match:
                ul_content = ul_match.group(1)
                # 查找所有li标签
                li_pattern = r'<li[^>]*>(.*?)</li>'
                li_matches = re.findall(li_pattern, ul_content, re.DOTALL | re.IGNORECASE)
                for li_content in li_matches:
                    # 移除HTML标签，只保留文本
                    text = re.sub(r'<[^>]+>', '', li_content).strip()
                    # 查找包含大小信息的文本（匹配 "大小：87.52M" 或 "87.52MB" 等格式）
                    if 'MB' in text.upper() or 'GB' in text.upper() or 'M' in text.upper() or 'G' in text.upper():
                        # 优先匹配 "大小：87.52M" 格式
                        size_match = re.search(r'(?:大小[：:]?\s*)?(\d+\.?\d*)\s*([MG]B?)', text, re.IGNORECASE)
                        if size_match:
                            value = size_match.group(1)
                            unit = size_match.group(2).upper() if size_match.group(2) else 'MB'
                            if not unit.endswith('B'):
                                unit += 'B'
                            info['size'] = value + unit
                            break
            
            # 如果没找到，尝试在整个页面中查找（备选方案）
            if not info.get('size'):
                size_patterns = [
                    r'大小[：:]\s*(\d+\.?\d*)\s*([MG]B?)',
                    r'文件大小[：:]\s*(\d+\.?\d*)\s*([MG]B?)',
                    r'(\d+\.?\d*)\s*([MG]B)'
                ]
                
                for pattern in size_patterns:
                    match = re.search(pattern, response.text, re.IGNORECASE)
                    if match:
                        value = match.group(1)
                        unit = (match.group(2) or 'MB').upper()
                        if not unit.endswith('B'):
                            unit += 'B'
                        info['size'] = value + unit
                        break
            
            # 提取下载地址 - 专门查找dt标签（包含"本地下载地址"）下的a标签
            # 1. 查找dt标签中包含"本地下载地址"的，然后在其下一个兄弟节点（通常是dd）中查找a标签
            dt_pattern = r'<dt[^>]*>.*?本地下载地址.*?</dt>'
            dt_matches = re.findall(dt_pattern, response.text, re.IGNORECASE | re.DOTALL)
            info['debug']['dtTagsFound'] = len(dt_matches)
            
            if dt_matches:
                dt_match = re.search(dt_pattern, response.text, re.IGNORECASE | re.DOTALL)
                # 找到dt标签后，查找其后的dd标签中的a标签
                dt_end = dt_match.end()
                # 在dt标签后查找dd标签（最多500字符内）
                search_text = response.text[dt_end:dt_end + 500]
                dd_pattern = r'<dd[^>]*>.*?<a[^>]+href=["\']([^"\']+)["\']'
                dd_match = re.search(dd_pattern, search_text, re.IGNORECASE | re.DOTALL)
                if dd_match:
                    url = dd_match.group(1)
                    if not url.startswith('http'):
                        base_url = '/'.join(page_url.split('/')[:3])
                        if url.startswith('/'):
                            url = base_url + url
                        else:
                            url = base_url + '/' + url
                    
                    # 判断是否为HTML页面
                    is_html = url.endswith('.html') or url.endswith('.htm') or 'javascript:' in url
                    if is_html:
                        reason = '以.html结尾' if url.endswith('.html') else ('以.htm结尾' if url.endswith('.htm') else 'javascript链接')
                        info['debug']['rejectedLinks'].append({
                            'href': url[:100],
                            'reason': reason
                        })
                    elif url:
                        info['debug']['linksFound'].append({
                            'href': url[:100],
                            'source': 'dt标签的dd兄弟节点'
                        })
                        info['download_url'] = url
            
            # 2. 如果没找到，尝试更宽泛的匹配：查找dt标签，然后在附近查找a标签
            if not info['download_url']:
                # 查找包含"本地下载地址"的dt标签位置
                start_pos = response.text.find('本地下载地址')
                if start_pos != -1:
                    # 向前查找dt标签的开始
                    dt_start = response.text.rfind('<dt', 0, start_pos)
                    if dt_start != -1:
                        # 在dt标签后查找a标签（最多1000字符）
                        search_end = min(start_pos + 1000, len(response.text))
                        search_text = response.text[dt_start:search_end]
                        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\']'
                        link_matches = re.findall(link_pattern, search_text, re.IGNORECASE)
                        if link_matches:
                            for url in link_matches:
                                if not url.startswith('http'):
                                    base_url = '/'.join(page_url.split('/')[:3])
                                    if url.startswith('/'):
                                        url = base_url + url
                                    else:
                                        url = base_url + '/' + url
                                
                                # 判断是否为HTML页面
                                is_html = url.endswith('.html') or url.endswith('.htm') or 'javascript:' in url or 'kxdw.com/android/' in url
                                if is_html:
                                    reason = '以.html结尾' if url.endswith('.html') else ('以.htm结尾' if url.endswith('.htm') else ('包含详情页路径' if 'kxdw.com/android/' in url else 'javascript链接'))
                                    info['debug']['rejectedLinks'].append({
                                        'href': url[:100],
                                        'reason': reason
                                    })
                                    continue
                                
                                info['debug']['linksFound'].append({
                                    'href': url[:100],
                                    'source': 'dt标签附近'
                                })
                                info['download_url'] = url
                                break
            
            # 3. 如果还是没找到，尝试查找包含下载相关关键词的链接（备用方案）
            if not info['download_url']:
                # 查找包含下载、down、apk等关键词的链接
                download_link_pattern = r'<a[^>]+href=["\']([^"\']*(?:download|down|apk)[^"\']*)["\'][^>]*>'
                matches = re.findall(download_link_pattern, response.text, re.IGNORECASE)
                if matches:
                    for url in matches:
                        if not url.startswith('http'):
                            base_url = '/'.join(page_url.split('/')[:3])
                            if url.startswith('/'):
                                url = base_url + url
                            else:
                                url = base_url + '/' + url
                        
                        # 判断是否为HTML页面
                        is_html = (url.endswith('.html') or url.endswith('.htm') or 
                                  'kxdw.com/android/' in url or 'javascript:' in url)
                        if is_html:
                            reason = '以.html结尾' if url.endswith('.html') else ('以.htm结尾' if url.endswith('.htm') else ('包含详情页路径' if 'kxdw.com/android/' in url else 'javascript链接'))
                            info['debug']['rejectedLinks'].append({
                                'href': url[:100],
                                'reason': reason
                            })
                            continue
                        
                        info['debug']['linksFound'].append({
                            'href': url[:100],
                            'source': '包含下载关键词的链接'
                        })
                        info['download_url'] = url
                        break
            
            # 输出调试信息
            debug_info = info.get('debug', {})
            if debug_info:
                print(f"   📊 调试信息 (requests模式):")
                print(f"      - 找到 {debug_info.get('dtTagsFound', 0)} 个dt标签")
                print(f"      - 找到的候选链接: {len(debug_info.get('linksFound', []))} 个")
                if debug_info.get('linksFound'):
                    for i, link in enumerate(debug_info['linksFound'], 1):
                        print(f"        {i}. {link.get('href', '')[:80]}...")
                        print(f"           来源: {link.get('source', '')}")
                print(f"      - 被拒绝的链接: {len(debug_info.get('rejectedLinks', []))} 个")
                if debug_info.get('rejectedLinks'):
                    for i, link in enumerate(debug_info['rejectedLinks'], 1):
                        print(f"        {i}. {link.get('href', '')[:80]}...")
                        print(f"           原因: {link.get('reason', '未知')}")
            
            return info
            
        except Exception as e:
            print(f"   ⚠️  requests解析失败: {e}")
            return None
    
    def _download_with_chrome(self, download_url: str, save_path: Path, expected_size_mb: float = 0.0) -> bool:
        """使用Chrome直接下载文件（更稳定，避免连接中断）
        Args:
            download_url: 下载URL
            save_path: 保存路径
            expected_size_mb: 预期文件大小（MB），用于判断下载是否完成
        Returns:
            bool: 下载是否成功
        """
        if not pychrome or not self.use_chrome:
            return False
        
        # 如果是api.kxdw.com/adown/链接，先获取真实下载URL
        # 但不要取消下载，而是直接使用真实URL让Chrome下载
        real_url = None
        if 'api.kxdw.com/adown/' in download_url:
            print(f"   🔍 检测到api.kxdw.com/adown/链接，先获取真实下载地址...")
            real_url = self._get_real_download_url_with_chrome(download_url)
            if real_url:
                print(f"   ✅ 已获取真实下载地址，使用Chrome直接下载")
                download_url = real_url
                # 保存真实下载地址，供后续requests下载使用
                self._last_real_download_url = real_url
            else:
                print(f"   ⚠️  无法获取真实下载地址，使用原始URL尝试下载")
                self._last_real_download_url = None
        
        try:
            # Chrome本地连接不使用代理（临时取消代理环境变量）
            import os
            old_proxy_env = {}
            proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_env_vars:
                if var in os.environ:
                    old_proxy_env[var] = os.environ[var]
                    del os.environ[var]
            
            # 设置NO_PROXY，排除本地地址
            old_no_proxy = os.environ.get('NO_PROXY', '')
            os.environ['NO_PROXY'] = '127.0.0.1,localhost,0.0.0.0'
            
            browser = None
            tab = None
            download_start_time = time.time()
            
            try:
                browser = pychrome.Browser(url="http://127.0.0.1:9222")
                tab = browser.new_tab()
                tab.start()
                
                # 设置下载路径到目标文件夹
                download_dir = str(save_path.parent.absolute())  # 使用绝对路径
                print(f"   📁 目标下载目录: {download_dir}")
                print(f"   📁 目标文件路径: {save_path.absolute()}")
                
                # 确保目录存在
                save_path.parent.mkdir(parents=True, exist_ok=True)
                
                try:
                    tab.Browser.setDownloadBehavior(
                        behavior="allow",
                        downloadPath=download_dir
                    )
                    print(f"   ✅ 已设置Chrome下载路径: {download_dir}")
                except AttributeError:
                    # 如果Browser域不可用，尝试使用Page域
                    try:
                        tab.Page.setDownloadBehavior(
                            behavior="allow",
                            downloadPath=download_dir
                        )
                        print(f"   ✅ 已设置Chrome下载路径: {download_dir}")
                    except Exception as e:
                        print(f"   ⚠️  无法设置下载路径: {e}，将使用默认下载目录")
                        print(f"   💡 提示: Chrome可能下载到默认目录: {Path.home() / 'Downloads'}")
                
                # 监听下载事件
                download_completed = False
                download_guid = None
                downloaded_file_path = None
                
                # 辅助函数：检查是否存在.crdownload文件
                def has_crdownload_files() -> Tuple[bool, List[Path]]:
                    """检查指定目录和默认下载目录中是否存在.crdownload文件
                    Returns:
                        (has_crdownload, crdownload_files_list)
                    """
                    crdownload_files = []
                    # 检查指定目录
                    if save_path.parent.exists():
                        files = list(save_path.parent.glob('*.crdownload'))
                        if files:
                            crdownload_files.extend(files)
                            return True, crdownload_files
                    # 检查默认下载目录
                    default_download_dir = Path.home() / 'Downloads'
                    if default_download_dir.exists():
                        files = list(default_download_dir.glob('*.crdownload'))
                        if files:
                            crdownload_files.extend(files)
                            return True, crdownload_files
                    return False, []
                
                # 辅助函数：判断下载是否完成（基于文件大小和.crdownload文件）
                def check_download_complete(file_path: Path, expected_size_bytes: int = 0) -> bool:
                    """检查下载是否完成
                    Args:
                        file_path: 下载的文件路径（可能是.apk或.crdownload）
                        expected_size_bytes: 预期文件大小（字节），0表示不检查大小
                    Returns:
                        bool: 是否完成
                    """
                    if not file_path or not file_path.exists():
                        return False
                    
                    # 如果指定了预期大小，检查文件大小
                    if expected_size_bytes > 0:
                        current_size = file_path.stat().st_size
                        if current_size < expected_size_bytes:
                            return False
                    
                    # 关键：扫描目录中是否还有.crdownload文件（而不是只检查传入的file_path）
                    # 因为Chrome可能已经将file_path从.crdownload重命名为.apk
                    # 但如果还有其他.crdownload文件存在，说明下载可能还在进行中
                    has_crdownload, crdownload_files = has_crdownload_files()
                    
                    # 如果还有.crdownload文件，检查是否与当前文件相关（可能是同一个文件的不同阶段）
                    if has_crdownload:
                        # 检查是否有与file_path相关的.crdownload文件（相同文件名但后缀不同）
                        file_stem = file_path.stem  # 文件名（不含后缀）
                        file_dir = file_path.parent
                        
                        # 在当前文件所在目录查找相关的.crdownload文件
                        related_crdownload = file_dir / f"{file_stem}.crdownload"
                        if related_crdownload.exists():
                            # 如果找到相关的.crdownload文件，说明当前文件可能还在下载中
                            return False
                        
                        # 检查默认下载目录
                        default_download_dir = Path.home() / 'Downloads'
                        if default_download_dir.exists():
                            related_crdownload = default_download_dir / f"{file_stem}.crdownload"
                            if related_crdownload.exists():
                                return False
                    
                    # 没有找到相关的.crdownload文件，且文件大小满足要求，认为下载完成
                    return True
                
                def on_download_will_begin(**kwargs):
                    nonlocal download_guid
                    download_guid = kwargs.get('guid', None)
                    suggested_filename = kwargs.get('suggestedFilename', '')
                    print(f"   📥 Chrome开始下载: {suggested_filename or '文件'}...")
                
                progress_event_available = False  # 标记是否收到过进度事件
                last_progress_percent = 0.0  # 记录最后一次进度百分比
                last_progress_check_time = 0.0  # 记录最后一次检查进度的时间
                
                def on_download_progress(**kwargs):
                    """下载进度事件（如果可用）"""
                    nonlocal download_completed, downloaded_file_path, download_guid, progress_event_available, last_progress_time, last_progress_percent, last_progress_check_time
                    try:
                        # 兼容Browser域和Page域的下载进度事件（不同版本的API可能使用不同的字段名）
                        guid = kwargs.get('guid', '') or kwargs.get('downloadId', '')
                        state = kwargs.get('state', '') or kwargs.get('status', '')
                        received_bytes = kwargs.get('receivedBytes', 0) or kwargs.get('bytesReceived', 0)
                        # 修复：正确获取totalBytes（可能字段名不同，或者不存在）
                        total_bytes_from_event = kwargs.get('totalBytes', 0) or kwargs.get('totalSize', 0)
                        
                        # 只处理当前下载的事件（如果guid匹配，或者没有guid则处理所有事件）
                        if not download_guid or guid == download_guid or guid == str(download_guid):
                            progress_event_available = True  # 标记已收到进度事件
                            
                            # 更新最后收到进度的时间（用于动态延长超时时间）
                            last_progress_time = time.time()
                            last_progress_check_time = time.time()
                            
                            # 如果事件中没有提供totalBytes，使用expected_size_mb作为备选
                            if total_bytes_from_event == 0 and expected_size_mb > 0:
                                total_bytes = int(expected_size_mb * 1024 * 1024)
                                # 只在第一次使用时打印调试信息
                                if not hasattr(on_download_progress, '_debug_printed'):
                                    print(f"\n   💡 事件中未提供totalBytes，使用预期大小: {expected_size_mb:.2f}MB", flush=True)
                                    on_download_progress._debug_printed = True
                            else:
                                total_bytes = total_bytes_from_event
                            
                            # 显示下载进度（优先使用事件的进度信息）
                            # 使用sys.stderr确保进度显示不会被其他输出干扰
                            if total_bytes > 0:
                                progress = min((received_bytes / total_bytes) * 100, 100.0)  # 限制最大100%
                                # 更新最后进度百分比和时间
                                last_progress_percent = progress
                                last_progress_check_time = time.time()
                                sys.stderr.write(f"\r   下载进度:1 {progress:.1f}% ({received_bytes / 1024 / 1024:.2f}MB / {total_bytes / 1024 / 1024:.2f}MB)")
                                sys.stderr.flush()
                                
                                # Debug: 进度100%时打印
                                if progress >= 99.9 and not hasattr(on_download_progress, '_debug_100_printed'):
                                    print(f"\n   🔍 [DEBUG] 事件回调：收到进度100%事件（时间: {time.strftime('%H:%M:%S')}）")
                                    on_download_progress._debug_100_printed = True
                                
                                # 如果进度达到100%，检查是否还有.crdownload文件
                                # Chrome下载完成后会自动将.crdownload文件重命名为真实文件扩展名
                                # 如果没有.crdownload文件，说明Chrome已经完成重命名，下载完成
                                if progress >= 99.9:
                                    # 使用一个标记来记录是否已经检查过100%进度
                                    if not hasattr(on_download_progress, '_checked_100_percent'):
                                        on_download_progress._checked_100_percent = True
                                        on_download_progress._100_percent_time = time.time()
                                        print(f"\n   🔍 [DEBUG] 进度达到100%，开始检查完成状态（时间: {time.strftime('%H:%M:%S')}）")
                                    
                                    # 等待一小段时间，确保Chrome完成文件写入和重命名
                                    time_since_100 = time.time() - on_download_progress._100_percent_time
                                    if time_since_100 >= 2:  # 等待2秒后开始检查
                                        print(f"   🔍 [DEBUG] 进度100%后已等待{time_since_100:.1f}秒，开始检查.crdownload文件...")
                                        nonlocal download_completed
                                        has_crdownload, crdownload_files = has_crdownload_files()
                                        
                                        if has_crdownload:
                                            print(f"   🔍 [DEBUG] 找到.crdownload文件: {[f.name for f in crdownload_files]}")
                                        else:
                                            print(f"   🔍 [DEBUG] 无.crdownload文件")
                                        
                                        # 如果没有.crdownload文件，说明Chrome已经完成重命名，下载完成
                                        if not has_crdownload:
                                            download_completed = True
                                            print(f"   🔍 [DEBUG] 设置download_completed = True（无.crdownload文件）")
                                            sys.stderr.write(f"\n   ✅ Chrome下载完成（进度100%且无.crdownload文件，已重命名完成）\n")
                                            sys.stderr.flush()
                                        # 如果还有.crdownload文件，但已经等待超过10秒，也认为完成（可能Chrome重命名有问题）
                                        elif time_since_100 > 10:
                                            download_completed = True
                                            print(f"   🔍 [DEBUG] 设置download_completed = True（已等待{int(time_since_100)}秒，超时）")
                                            sys.stderr.write(f"\n   ✅ Chrome下载完成（进度100%且已等待{int(time_since_100)}秒，可能重命名延迟）\n")
                                            sys.stderr.flush()
                                        else:
                                            print(f"   🔍 [DEBUG] 仍有.crdownload文件，继续等待（已等待{time_since_100:.1f}秒）")
                                    else:
                                        if not hasattr(on_download_progress, '_debug_printed_100'):
                                            print(f"   🔍 [DEBUG] 进度100%，等待2秒后检查（当前等待{time_since_100:.1f}秒）")
                                            on_download_progress._debug_printed_100 = True
                            elif received_bytes > 0:
                                # 如果只有received_bytes，没有total_bytes，只显示已下载大小
                                sys.stderr.write(f"\r   下载进度:1 下载中... 已下载: {received_bytes / 1024 / 1024:.2f}MB")
                                sys.stderr.flush()
                            
                            # 【关键修改】无论进度多少，只要.crdownload文件不存在，就完成下载
                            # 因为网页详情中的APK大小可能不准确，所以不依赖进度100%
                            has_crdownload, crdownload_files = has_crdownload_files()
                            if not has_crdownload:
                                # 没有.crdownload文件，说明Chrome已经完成重命名，下载完成
                                download_completed = True
                                sys.stderr.write(f"\n   ✅ Chrome下载完成（.crdownload文件已消失，已下载: {received_bytes / 1024 / 1024:.2f}MB）\n")
                                sys.stderr.flush()
                            
                            # 下载完成（兼容不同的状态值）
                            # 这是最可靠的判断方式，优先使用
                            # 注意：即使收到completed状态，也要验证.crdownload文件是否已消失
                            if state in ['completed', 'finished', 'success']:
                                print(f"\n   🔍 [DEBUG] 事件回调：收到完成状态 '{state}'（时间: {time.strftime('%H:%M:%S')}）")
                                # 等待一小段时间，确保Chrome完成文件重命名（从.crdownload到.apk）
                                time.sleep(1)
                                
                                # 验证是否还有.crdownload文件存在
                                has_crdownload, _ = has_crdownload_files()
                                
                                # 只有在没有.crdownload文件时，才认为下载真正完成
                                if not has_crdownload:
                                    download_completed = True
                                    sys.stderr.write(f"\n   ✅ Chrome下载完成（通过事件，状态: {state}）\n")
                                    sys.stderr.flush()
                                else:
                                    # 还有.crdownload文件，说明下载可能还在进行中，继续等待
                                    sys.stderr.write(f"\n   ⏳ Chrome事件显示完成，但检测到.crdownload文件仍存在，继续等待...\n")
                                    sys.stderr.flush()
                    except Exception as e:
                        # 忽略事件处理中的异常，避免影响下载
                        pass
                
                tab.Page.downloadWillBegin = on_download_will_begin
                # 尝试监听下载进度（Browser域可能不可用，使用Page域作为备选）
                try:
                    # 尝试使用Browser域监听下载进度
                    if hasattr(tab, 'Browser') and hasattr(tab.Browser, 'downloadProgress'):
                        tab.Browser.downloadProgress = on_download_progress
                        print(f"   ✅ 已启用Browser域下载进度监听")
                    elif hasattr(tab, 'Page') and hasattr(tab.Page, 'downloadProgress'):
                        # 使用Page域监听下载进度（如果Browser域不可用）
                        tab.Page.downloadProgress = on_download_progress
                        print(f"   ✅ 已启用Page域下载进度监听")
                    else:
                        print(f"   ⚠️  无法启用下载进度监听，将只显示下载开始和完成状态")
                except Exception as e:
                    # 如果启用失败，只记录警告，不影响下载
                    print(f"   ⚠️  启用下载进度监听失败: {e}，将只显示下载开始和完成状态")
                tab.Page.enable()
                
                # 确保Chrome不使用代理（通过Network域设置）
                try:
                    if hasattr(tab, 'Network'):
                        tab.Network.enable()
                        # 注意：Chrome DevTools Protocol无法直接禁用代理
                        # 但我们已经取消了代理环境变量，Chrome应该不会使用代理
                        # 如果Chrome启动时使用了--proxy-server参数，仍会使用代理
                        # 建议启动Chrome时使用: --no-proxy-server 参数
                except Exception as e:
                    pass
                
                print(f"   🌐 使用Chrome直接下载（不使用代理，直连）...")
                print(f"   💡 提示: 如果Chrome仍使用代理，请在启动Chrome时添加 --no-proxy-server 参数")
                tab.Page.navigate(url=download_url)
                
                # 等待下载事件触发（最多30秒）
                wait_count = 0
                while wait_count < 60 and not download_guid:
                    time.sleep(0.5)
                    wait_count += 1
                
                if not download_guid:
                    print(f"   ⚠️  未检测到下载事件，Chrome下载可能失败")
                    return False
                
                # 等待下载完成（动态超时时间）
                # 优先使用downloadProgress事件判断完成，文件大小监控作为备选方案
                # 基础超时时间：10分钟
                base_timeout = 600
                # 如果检测到进度更新，动态延长超时时间
                # 根据文件大小估算：假设最小下载速度0.1MB/s
                if expected_size_mb > 0:
                    # 估算下载时间（秒）：文件大小(MB) / 最小速度(0.1MB/s) * 1.5倍安全系数
                    estimated_time = (expected_size_mb / 0.1) * 1.5
                    # 至少30分钟，最多2小时
                    max_wait_time = max(base_timeout, min(int(estimated_time), 7200))
                else:
                    # 如果没有预期大小，使用较长的超时时间（30分钟）
                    max_wait_time = 1800
                
                wait_count = 0
                last_file_size = 0
                last_progress_time = time.time()  # 记录最后一次收到进度更新的时间
                check_interval = 2  # 每2秒检查一次文件大小
                last_check_time = time.time()
                stable_size_count = 0  # 记录文件大小稳定的次数（连续5次检查大小相同，即10秒）
                
                while wait_count < max_wait_time and not download_completed:
                    # 短暂休眠，让事件回调有机会执行
                    # 如果Chrome的downloadProgress事件可用，主循环主要等待事件回调
                    time.sleep(0.5)
                    wait_count += 1
                    
                    # 每10秒打印一次debug信息（如果进度100%）
                    if wait_count % 20 == 0 and progress_event_available and last_progress_percent >= 99.9:
                        time_since_last_progress = time.time() - last_progress_check_time
                        print(f"\n   🔍 [DEBUG] 主循环：等待{wait_count * 0.5:.0f}秒，进度100%，最后进度更新{time_since_last_progress:.1f}秒前，download_completed={download_completed}")
                    
                    # 【关键修改】无论进度多少，只要.crdownload文件不存在，就完成下载
                    # 每次循环都检查，不等待进度100%
                    has_crdownload, crdownload_files = has_crdownload_files()
                    if not has_crdownload:
                        # 没有.crdownload文件，说明Chrome已经完成重命名，下载完成
                        download_completed = True
                        if progress_event_available:
                            print(f"\n   ✅ Chrome下载完成（.crdownload文件已消失，主循环检查，进度: {last_progress_percent:.1f}%）")
                        else:
                            print(f"\n   ✅ Chrome下载完成（.crdownload文件已消失，主循环检查）")
                        break
                    
                    # 如果进度事件可用且最后进度是100%，检查是否完成
                    # 这可以处理进度100%后事件回调不再触发的情况
                    if progress_event_available and last_progress_percent >= 99.9:
                        # 如果最后进度是100%且已经等待超过2秒，检查.crdownload文件
                        time_since_last_progress = time.time() - last_progress_check_time
                        if time_since_last_progress >= 2:
                            # 只在第一次检查时打印debug
                            if not hasattr(on_download_progress, '_main_loop_checked'):
                                print(f"\n   🔍 [DEBUG] 主循环检查：进度100%，最后进度更新{time_since_last_progress:.1f}秒前")
                                on_download_progress._main_loop_checked = True
                            
                            # 检查是否还有.crdownload文件（虽然上面已经检查过，但这里再次确认）
                            if has_crdownload and wait_count % 20 == 0:  # 每10秒打印一次
                                print(f"   🔍 [DEBUG] 主循环：找到.crdownload文件: {[f.name for f in crdownload_files]}")
                            
                            # 如果还有.crdownload文件但已等待超过10秒，也认为完成
                            if time_since_last_progress > 10:
                                download_completed = True
                                print(f"\n   🔍 [DEBUG] 主循环：设置download_completed = True（已等待{int(time_since_last_progress)}秒，超时）")
                                print(f"\n   ✅ Chrome下载完成（进度100%且已等待{int(time_since_last_progress)}秒，主循环检查）")
                                break
                    
                    # 每2秒检查一次文件大小，显示下载进度（作为备选方案）
                    # 如果Chrome的downloadProgress事件可用，减少文件大小检查的频率
                    current_time = time.time()
                    check_file_size = (current_time - last_check_time >= check_interval)
                    # 如果事件可用，延长检查间隔到5秒（减少干扰）
                    if progress_event_available:
                        check_file_size = (current_time - last_check_time >= 5.0)
                    
                    if check_file_size:
                        # 优先检查指定下载目录（save_path.parent）中的文件
                        # 这是Chrome应该下载到的目录
                        downloaded_file = None
                        crdownload_file = None
                        
                        # 调试信息：打印查找的目录
                        if wait_count == 1:  # 只在第一次检查时打印
                            print(f"\n   🔍 开始监听文件下载进度...")
                            print(f"   📁 指定下载目录: {save_path.parent.absolute()}")
                            print(f"   📁 目录是否存在: {save_path.parent.exists()}")
                            if save_path.parent.exists():
                                all_files = list(save_path.parent.iterdir())
                                print(f"   📄 目录中的文件: {[f.name for f in all_files]}")
                        
                        # 1. 首先检查指定目录中的.crdownload文件（下载进行中）
                        if save_path.parent.exists():
                            crdownload_files = list(save_path.parent.glob('*.crdownload'))
                            if crdownload_files:
                                crdownload_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                crdownload_file = crdownload_files[0]
                                if crdownload_file and crdownload_file.exists():
                                    downloaded_file = crdownload_file
                                    if wait_count == 1:
                                        print(f"   ✅ 找到临时文件: {crdownload_file.name}")
                        
                        # 2. 如果指定目录没有.crdownload文件，检查指定目录中的.apk文件（下载完成）
                        if not downloaded_file and save_path.parent.exists():
                            apk_files = list(save_path.parent.glob('*.apk'))
                            if apk_files:
                                apk_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                # 只选择最近修改的.apk文件，且修改时间在下载开始之后
                                for apk_file in apk_files:
                                    if apk_file.stat().st_mtime >= download_start_time - 10:  # 允许10秒误差
                                        downloaded_file = apk_file
                                        if wait_count == 1:
                                            print(f"   ✅ 找到已下载文件: {apk_file.name}")
                                        break
                        
                        # 3. 如果指定目录都没有文件，才检查默认下载目录（作为备选）
                        # 这通常发生在Chrome的setDownloadBehavior没有生效时
                        if not downloaded_file:
                            default_download_dir = Path.home() / 'Downloads'
                            if default_download_dir.exists():
                                # 先检查.crdownload文件
                                crdownload_files = list(default_download_dir.glob('*.crdownload'))
                                if crdownload_files:
                                    crdownload_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                    crdownload_file = crdownload_files[0]
                                    if crdownload_file and crdownload_file.exists():
                                        # 检查文件是否在下载开始后创建
                                        if crdownload_file.stat().st_mtime >= download_start_time - 10:
                                            downloaded_file = crdownload_file
                                            # 如果文件在默认目录，打印警告
                                            if wait_count % 20 == 0:  # 每10秒打印一次（20次 * 0.5秒）
                                                print(f"\n   ⚠️  检测到文件下载到默认目录而非指定目录")
                                                print(f"   📁 默认目录: {default_download_dir}")
                                                print(f"   📁 指定目录: {save_path.parent.absolute()}")
                                                print(f"   📄 临时文件: {crdownload_file.name}")
                                
                                # 如果还没有找到，检查.apk文件
                                if not downloaded_file:
                                    apk_files = list(default_download_dir.glob('*.apk'))
                                    if apk_files:
                                        apk_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                        for apk_file in apk_files:
                                            if apk_file.stat().st_mtime >= download_start_time - 10:
                                                downloaded_file = apk_file
                                                if wait_count % 20 == 0:
                                                    print(f"\n   ⚠️  检测到文件下载到默认目录而非指定目录")
                                                    print(f"   📁 默认目录: {default_download_dir}")
                                                    print(f"   📁 指定目录: {save_path.parent.absolute()}")
                                                    print(f"   📄 文件: {apk_file.name}")
                                                break
                        
                        # 如果仍然没有找到文件，打印调试信息
                        if not downloaded_file and wait_count % 40 == 0:  # 每20秒打印一次
                            print(f"\n   ⚠️  未找到下载文件（已等待 {wait_count * 0.5:.0f} 秒）")
                            print(f"   📁 检查的目录:")
                            print(f"      - 指定目录: {save_path.parent.absolute()} (存在: {save_path.parent.exists()})")
                            if save_path.parent.exists():
                                all_files = list(save_path.parent.iterdir())
                                print(f"        文件列表: {[f.name for f in all_files]}")
                            default_download_dir = Path.home() / 'Downloads'
                            print(f"      - 默认目录: {default_download_dir} (存在: {default_download_dir.exists()})")
                            if default_download_dir.exists():
                                crdownload_files = list(default_download_dir.glob('*.crdownload'))
                                apk_files = list(default_download_dir.glob('*.apk'))
                                print(f"        临时文件: {[f.name for f in crdownload_files[:3]]}")
                                print(f"        APK文件: {[f.name for f in apk_files[:3]]}")
                        
                        if downloaded_file and downloaded_file.exists():
                            current_file_size = downloaded_file.stat().st_size
                            current_file_size_mb = current_file_size / 1024 / 1024
                            
                            # 【关键修改】优先检查：如果.crdownload文件不存在，立即完成下载
                            # 不管进度是否100%，只要.crdownload文件不存在，就认为Chrome已经完成重命名，下载完成
                            has_crdownload, crdownload_files = has_crdownload_files()
                            if not has_crdownload:
                                # 没有.crdownload文件，说明Chrome已经完成重命名，下载完成
                                download_completed = True
                                print(f"\n   ✅ Chrome下载完成（.crdownload文件已消失，Chrome已完成重命名，文件大小: {current_file_size_mb:.2f}MB）")
                                break
                            
                            # 只有在文件大小 > 0 时，才进行进度显示和完成判断
                            # 下载刚开始时，文件可能还不存在或大小为0，这是正常状态
                            if current_file_size > 0:
                                # 更新最后收到进度的时间（文件大小在增长，说明下载在进行中）
                                if current_file_size > last_file_size:
                                    last_progress_time = time.time()
                                
                                # 显示进度（只有在Chrome的downloadProgress事件不可用时才显示文件大小监控的进度）
                                # 如果事件可用，优先使用事件的进度显示（在on_download_progress中处理）
                                if not progress_event_available:
                                    # Chrome的downloadProgress事件不可用，使用文件大小监控显示进度
                                    if expected_size_mb > 0:
                                        progress = min((current_file_size_mb / expected_size_mb) * 100, 100.0)  # 限制最大100%
                                        # 使用sys.stderr确保进度显示不会被其他输出干扰
                                        sys.stderr.write(f"\r   下载进度:2 {progress:.1f}% ({current_file_size_mb:.2f}MB / {expected_size_mb:.2f}MB)")
                                        sys.stderr.flush()
                                        
                                        # 如果进度达到100%，检查Chrome是否已完成重命名
                                        if progress >= 99.9:
                                            # 检查当前文件是否还是.crdownload文件
                                            is_crdownload = downloaded_file.suffix == '.crdownload' or str(downloaded_file).endswith('.crdownload')
                                            
                                            if is_crdownload:
                                                # 如果还是.crdownload，检查Chrome是否已经将其重命名为.apk
                                                # 查找相同文件名（不含后缀）的.apk文件
                                                file_stem = downloaded_file.stem
                                                file_dir = downloaded_file.parent
                                                
                                                # 在当前目录查找对应的.apk文件
                                                apk_file = file_dir / f"{file_stem}.apk"
                                                if apk_file.exists() and apk_file.stat().st_size >= current_file_size:
                                                    # Chrome已经完成重命名，下载完成
                                                    download_completed = True
                                                    print(f"\n   ✅ Chrome下载完成（文件已重命名为: {apk_file.name}，大小: {current_file_size_mb:.2f}MB）")
                                                    break
                                                else:
                                                    # 还在等待Chrome重命名
                                                    if wait_count % 20 == 0:  # 每10秒打印一次
                                                        print(f"\n   🔍 [DEBUG] 下载进度:2 进度100%，等待Chrome重命名.crdownload文件...")
                                            else:
                                                # 文件已经不是.crdownload了，说明Chrome已经完成重命名，下载完成
                                                download_completed = True
                                                print(f"\n   ✅ Chrome下载完成（通过文件大小监控，文件大小: {current_file_size_mb:.2f}MB >= 预期: {expected_size_mb:.2f}MB）")
                                                break
                                    else:
                                        sys.stderr.write(f"\r   下载进度:2 下载中... 当前大小: {current_file_size_mb:.2f}MB")
                                        sys.stderr.flush()
                                
                                # 判断下载是否完成（如果进度还没达到100%，继续检查）
                                # 注意：进度100%的判断已经在上面处理了，这里只处理进度未达到100%的情况
                                if expected_size_mb > 0:
                                    # 有预期大小，检查是否达到预期大小
                                    expected_size_bytes = int(expected_size_mb * 1024 * 1024)
                                    # 检查文件大小是否达到预期（必须 >= 预期大小，不允许误差）
                                    if current_file_size >= expected_size_bytes:
                                        # 文件大小已达到预期，检查是否完成
                                        if check_download_complete(downloaded_file, expected_size_bytes):
                                            # 下载完成
                                            download_completed = True
                                            print(f"\n   🔍 [DEBUG] 下载进度:2 文件大小达到预期且无.crdownload文件，直接完成")
                                            if progress_event_available:
                                                print(f"\n   ✅ Chrome下载完成（通过文件大小监控，文件大小: {current_file_size_mb:.2f}MB >= 预期: {expected_size_mb:.2f}MB）")
                                            else:
                                                print(f"\n   ✅ Chrome下载完成（文件大小: {current_file_size_mb:.2f}MB >= 预期: {expected_size_mb:.2f}MB）")
                                            break
                                        else:
                                            # 还有.crdownload文件，继续等待
                                            if wait_count % 20 == 0:  # 每10秒打印一次
                                                print(f"\n   🔍 [DEBUG] 下载进度:2 文件大小达到预期，但仍有.crdownload文件，继续等待...")
                                    else:
                                        # 文件大小还未达到预期，更新last_file_size
                                        if current_file_size > last_file_size:
                                            last_file_size = current_file_size
                                else:
                                    # 没有预期大小，使用备选方案：文件大小连续5次检查（10秒）没有变化
                                    # 且至少等待了30秒，且downloadProgress事件不可用
                                    
                                    # 检查是否为.crdownload文件
                                    is_crdownload = downloaded_file.suffix == '.crdownload' or str(downloaded_file).endswith('.crdownload')
                                    
                                    if current_file_size > last_file_size:
                                        # 文件大小在增长，重置稳定计数，更新last_file_size
                                        stable_size_count = 0
                                        last_file_size = current_file_size
                                    elif current_file_size == last_file_size and last_file_size > 0:
                                        # 文件大小没有变化，且之前已经有文件大小记录，增加稳定计数
                                        stable_size_count += 1
                                        # 如果连续5次检查（10秒）大小都没有变化，且至少等待了30秒，认为下载完成
                                        # 这是备选方案：即使downloadProgress事件可用，如果事件没有触发完成状态，也要有备选判断
                                        # 重要：必须确保没有.crdownload文件存在，才认为下载完成
                                        if stable_size_count >= 5 and wait_count > 30:
                                            # 再次检查是否完成（确保没有.crdownload文件）
                                            if check_download_complete(downloaded_file, 0):
                                                # 如果事件不可用，或者事件可用但等待超过60秒仍未完成，使用文件大小监控判断
                                                if not progress_event_available or (progress_event_available and wait_count > 60):
                                                    download_completed = True
                                                    if progress_event_available:
                                                        print(f"\n   ✅ Chrome下载完成（通过文件大小监控备选方案，当前大小: {current_file_size_mb:.2f}MB，且大小已稳定10秒）")
                                                    else:
                                                        print(f"\n   ✅ Chrome下载完成（通过文件大小监控，当前大小: {current_file_size_mb:.2f}MB，且大小已稳定10秒）")
                                                    break
                                        elif is_crdownload:
                                            # 如果还有.crdownload文件，重置稳定计数，继续等待
                                            stable_size_count = 0
                                    else:
                                        # 文件大小为0或异常，重置稳定计数，但更新last_file_size（如果文件大小 > 0）
                                        stable_size_count = 0
                                        if current_file_size > 0:
                                            last_file_size = current_file_size
                            else:
                                # 文件大小为0，说明下载还没开始或文件还不存在，重置稳定计数
                                stable_size_count = 0
                                # 不更新last_file_size，保持为0或之前的值
                        
                        last_check_time = current_time
                    
                    # 如果Chrome的downloadProgress事件可用，主循环只需要等待事件回调设置download_completed
                    # 不需要做太多处理，避免阻塞事件回调
                    
                    # 动态延长超时时间：如果检测到有进度更新，延长超时时间
                    # 检查是否有进度更新（通过事件或文件大小增长）
                    time_since_last_progress = time.time() - last_progress_time
                    if time_since_last_progress < 60:  # 如果最近60秒内有进度更新
                        # 下载在进行中，动态延长超时时间（每次延长5分钟，最多延长到2小时）
                        if wait_count >= max_wait_time - 60:  # 在超时前1分钟检查
                            old_max_wait_time = max_wait_time
                            max_wait_time = min(max_wait_time + 300, 7200)  # 延长5分钟，最多2小时
                            if max_wait_time > old_max_wait_time:
                                print(f"\n   💡 检测到下载进度（{int(time_since_last_progress)}秒前有更新），延长超时时间至 {max_wait_time // 60} 分钟", flush=True)
                
                # 如果超时仍未完成，检查是否是因为事件回调没有触发完成状态
                if not download_completed and wait_count >= max_wait_time:
                    print(f"\n   ⚠️  下载超时（等待{max_wait_time // 60}分钟）")
                    if progress_event_available:
                        time_since_last_progress = time.time() - last_progress_time
                        print(f"   💡 Chrome的downloadProgress事件可用，但未收到完成状态")
                        print(f"   💡 最后收到进度更新: {int(time_since_last_progress)}秒前")
                        if time_since_last_progress < 60:
                            print(f"   💡 下载可能仍在进行中，建议等待更长时间或检查网络连接")
                        else:
                            print(f"   💡 可能原因：下载已停止，或事件回调未正确触发")
                
                if download_completed:
                    # 等待一小段时间，确保文件已写入磁盘并完成重命名（从.crdownload到.apk）
                    time.sleep(2)
                    
                    # 再次验证：确保没有.crdownload文件存在
                    has_crdownload, crdownload_files = has_crdownload_files()
                    if has_crdownload:
                        print(f"   ⚠️  检测到.crdownload文件仍存在: {crdownload_files[0].name}，下载可能未完成")
                    
                    if has_crdownload:
                        # 如果还有.crdownload文件，说明下载未完成，返回False
                        print(f"   ❌ 下载未完成，.crdownload文件仍存在")
                        return False
                    
                    # 查找下载的文件（只查找.apk文件，不查找.crdownload）
                    downloaded_file = None
                    try:
                        # 检查目标目录（查找所有APK文件，不限制文件名）
                        if save_path.parent.exists():
                            # 查找最近120秒内修改的APK文件（增加时间窗口，确保能找到文件）
                            current_time = time.time()
                            apk_files = [
                                f for f in save_path.parent.glob('*.apk')
                                if f.exists() and (current_time - f.stat().st_mtime) < 120
                            ]
                            if apk_files:
                                # 按修改时间排序，最新的在前
                                apk_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                downloaded_file = apk_files[0]
                                print(f"   📄 在目标目录找到文件: {downloaded_file.name} ({downloaded_file.stat().st_size / 1024 / 1024:.2f}MB)")
                        
                        # 如果目标目录没找到，检查Chrome默认下载目录
                        if not downloaded_file:
                            default_download_dir = Path.home() / 'Downloads'
                            if default_download_dir.exists():
                                current_time = time.time()
                                apk_files = [
                                    f for f in default_download_dir.glob('*.apk')
                                    if f.exists() and (current_time - f.stat().st_mtime) < 120
                                ]
                                if apk_files:
                                    # 按修改时间排序，最新的在前
                                    apk_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                                    downloaded_file = apk_files[0]
                                    print(f"   📄 在默认下载目录找到文件: {downloaded_file.name} ({downloaded_file.stat().st_size / 1024 / 1024:.2f}MB)")
                        
                        # 移动文件到目标位置
                        if downloaded_file and downloaded_file.exists():
                            import shutil
                            if save_path.exists():
                                save_path.unlink()  # 删除已存在的文件
                            
                            if downloaded_file.parent == save_path.parent:
                                # 如果已经在目标目录，直接重命名
                                downloaded_file.rename(save_path)
                            else:
                                # 否则移动文件
                                shutil.move(str(downloaded_file), str(save_path))
                            
                            # 验证文件
                            file_size = save_path.stat().st_size
                            with open(save_path, 'rb') as f:
                                file_header = f.read(4)
                                if file_header[:2] == b'PK':
                                    # 计算下载耗时
                                    download_end_time = time.time()
                                    download_duration = download_end_time - download_start_time
                                    download_minutes = int(download_duration // 60)
                                    download_seconds = int(download_duration % 60)
                                    if download_minutes > 0:
                                        print(f"   ✅ Chrome下载完成: {save_path.name} ({file_size / 1024 / 1024:.2f}MB) 耗时: {download_minutes}分{download_seconds}秒")
                                    else:
                                        print(f"   ✅ Chrome下载完成: {save_path.name} ({file_size / 1024 / 1024:.2f}MB) 耗时: {download_seconds}秒")
                                    self._create_zip_for_apk(save_path)
                                    return True
                                else:
                                    print(f"   ⚠️  文件格式不正确，删除文件")
                                    save_path.unlink()
                                    return False
                        else:
                            print(f"   ⚠️  下载完成但未找到文件，Chrome下载可能失败")
                            return False
                    except Exception as e:
                        print(f"   ⚠️  处理下载文件时出错: {e}")
                        return False
                else:
                    print(f"   ⚠️  Chrome下载超时（等待{max_wait_time}秒）")
                    return False
                
            except Exception as e:
                print(f"   ⚠️  Chrome下载时出错: {e}")
                return False
            finally:
                # 确保资源被正确清理
                if tab:
                    try:
                        # 移除事件监听器
                        try:
                            tab.Page.downloadWillBegin = None
                            # 尝试移除Browser域的监听器
                            if hasattr(tab, 'Browser') and hasattr(tab.Browser, 'downloadProgress'):
                                tab.Browser.downloadProgress = None
                            # 尝试移除Page域的监听器
                            if hasattr(tab, 'Page') and hasattr(tab.Page, 'downloadProgress'):
                                tab.Page.downloadProgress = None
                        except:
                            pass
                        # 等待接收循环处理完
                        time.sleep(0.2)
                        # 停止tab
                        try:
                            tab.stop()
                        except:
                            pass
                    except:
                        pass
                
                if browser and tab:
                    try:
                        browser.close_tab(tab)
                    except:
                        pass
                
                # 恢复代理环境变量
                for var, value in old_proxy_env.items():
                    os.environ[var] = value
                # 恢复NO_PROXY
                if old_no_proxy:
                    os.environ['NO_PROXY'] = old_no_proxy
                elif 'NO_PROXY' in os.environ:
                    del os.environ['NO_PROXY']
                    
        except Exception as e:
            print(f"   ⚠️  Chrome下载失败: {e}")
            return False
    
    def _get_real_download_url_with_chrome(self, download_url: str) -> Optional[str]:
        """使用Chrome获取真实的下载URL（用于api.kxdw.com/adown/这类需要JS执行的链接）
        注意：这个方法只获取URL，不会实际下载文件
        """
        if not pychrome or 'api.kxdw.com/adown/' not in download_url:
            return None
        
        try:
            # Chrome本地连接不使用代理（临时取消代理环境变量）
            import os
            old_proxy_env = {}
            proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
            for var in proxy_env_vars:
                if var in os.environ:
                    old_proxy_env[var] = os.environ[var]
                    del os.environ[var]
            
            # 设置NO_PROXY，排除本地地址
            old_no_proxy = os.environ.get('NO_PROXY', '')
            os.environ['NO_PROXY'] = '127.0.0.1,localhost,0.0.0.0'
            
            browser = None
            tab = None
            try:
                browser = pychrome.Browser(url="http://127.0.0.1:9222")
                tab = browser.new_tab()
                tab.start()
                
                # 确保不使用代理（通过Network域）
                try:
                    if hasattr(tab, 'Network'):
                        tab.Network.enable()
                except:
                    pass
                
                # 设置下载行为为拒绝，这样Chrome不会实际下载，但我们仍能通过Page.downloadWillBegin事件监听到下载URL
                try:
                    tab.Page.setDownloadBehavior(behavior="deny")
                except:
                    pass
                
                # 监听下载事件
                real_download_url = None
                download_guid = None
                
                def on_download_will_begin(**kwargs):
                    nonlocal real_download_url, download_guid
                    real_download_url = kwargs.get('url', None)
                    download_guid = kwargs.get('guid', None)
                    print(f"   📥 检测到下载事件，获取真实下载地址...")
                
                tab.Page.downloadWillBegin = on_download_will_begin
                tab.Page.enable()
                
                print(f"   🌐 使用Chrome获取真实下载地址（不会实际下载）...")
                # 注意：Chrome会使用系统代理设置（如果Shadowrocket配置了系统代理）
                tab.Page.navigate(url=download_url)
                
                # 等待下载事件（最多10秒）
                for i in range(20):
                    time.sleep(0.5)
                    if real_download_url:
                        break
                
                # 获取到真实下载URL后，取消下载（因为这只是为了获取URL）
                if real_download_url:
                    print(f"   ✅ 已获取真实下载地址，取消临时下载任务...")
                    # 尝试取消下载任务
                    try:
                        if download_guid:
                            try:
                                tab.Browser.cancelDownload(guid=download_guid)
                            except:
                                pass
                    except:
                        pass
                    # 导航到空白页，停止当前页面的下载活动
                    try:
                        tab.Page.navigate(url="about:blank")
                        time.sleep(0.2)  # 等待导航完成
                    except:
                        pass
                
                # 在停止前，移除事件监听器，避免后台线程继续处理
                try:
                    tab.Page.downloadWillBegin = None
                except:
                    pass
                
            except Exception as e:
                print(f"   ⚠️  Chrome获取下载地址时出错: {e}")
            finally:
                # 确保资源被正确清理，避免后台线程JSON解析错误
                if tab:
                    try:
                        # 先移除所有事件监听器
                        try:
                            tab.Page.downloadWillBegin = None
                        except:
                            pass
                        # 等待一小段时间，让接收循环处理完当前消息
                        time.sleep(0.2)
                        # 停止tab（这会停止接收循环，避免后台线程继续读取导致JSON错误）
                        try:
                            tab.stop()
                        except:
                            # 如果stop失败，可能是连接已断开，忽略错误
                            pass
                    except Exception as e:
                        # 忽略停止时的错误（可能是连接已断开）
                        pass
                
                if browser and tab:
                    try:
                        # 关闭标签页
                        browser.close_tab(tab)
                    except Exception as e:
                        # 忽略关闭时的错误
                        pass
                
                # 恢复代理环境变量
                for var, value in old_proxy_env.items():
                    os.environ[var] = value
                # 恢复NO_PROXY
                if old_no_proxy:
                    os.environ['NO_PROXY'] = old_no_proxy
                elif 'NO_PROXY' in os.environ:
                    del os.environ['NO_PROXY']
            
            if real_download_url:
                print(f"   ✅ 获取到真实下载地址: {real_download_url[:100]}...")
                return real_download_url
            else:
                print(f"   ⚠️  未检测到下载事件，使用原始URL")
                return None
                
        except Exception as e:
            print(f"   ⚠️  Chrome获取下载地址失败: {e}")
            return None
    
    def _download_file(self, download_url: str, save_path: Path, use_proxy: bool = None) -> bool:
        """下载文件
        Args:
            download_url: 下载URL
            save_path: 保存路径
            use_proxy: 是否使用代理（None表示自动判断）
        """
        if not requests:
            print("❌ 请安装 requests: pip3 install requests")
            return False
        
        try:
            # 标记是否获取到真实下载地址
            has_real_url = False
            
            # 注意：如果是api.kxdw.com/adown/链接且启用了Chrome，
            # 应该在调用_download_file之前就使用_download_with_chrome下载
            # 这里只处理非Chrome模式或Chrome下载失败后的情况
            # 如果use_proxy=True，说明是重试（已经获取过真实URL），跳过获取步骤
            if use_proxy is True:
                # 如果是重试（强制使用代理），说明已经获取过真实URL
                has_real_url = True
                print(f"   🔄 使用代理重新下载（已获取真实下载地址）")
            
            # 使用随机User-Agent和完整请求头
            headers = self._get_browser_headers(referer='https://www.kxdw.com/', is_download=True)
            
            # 使用Session来跟踪重定向链
            session = requests.Session()
            session.max_redirects = 10
            
            print(f"   🔍 跟踪重定向链...")
            print(f"      初始URL: {download_url[:100]}...")
            
            # 如果获取到真实下载地址，先尝试不使用代理
            # 如果失败，再使用代理
            # 如果use_proxy参数已指定，使用指定值（用于重试时强制使用代理）
            if use_proxy is not None:
                use_proxy_for_download = use_proxy
            else:
                use_proxy_for_download = not has_real_url
            proxy = None
            proxies = {}
            
            if use_proxy_for_download:
                # 获取代理（用于解析页面或初始下载）
                proxy = self._get_next_proxy()
                proxies = self._format_proxy_for_requests(proxy)
                if proxies:
                    print(f"   🌐 使用代理: {list(proxies.values())[0]}")
            else:
                print(f"   🚀 不使用代理（已获取真实下载地址）")
            
            # 随机延迟，避免请求过于频繁
            self._random_delay(0.5, 1.5)
            
            # 先发送HEAD请求查看重定向（增加超时时间）
            head_response = session.head(download_url, headers=headers, proxies=proxies, timeout=60, allow_redirects=True)
            redirect_history = head_response.history
            final_url = head_response.url
            
            if redirect_history:
                print(f"   📋 发现 {len(redirect_history)} 次重定向:")
                for i, resp in enumerate(redirect_history, 1):
                    print(f"      {i}. {resp.status_code} -> {resp.headers.get('Location', 'N/A')[:100]}")
                print(f"      最终URL: {final_url[:100]}...")
            else:
                print(f"   ✅ 无重定向，直接访问: {final_url[:100]}...")
            
            # 获取最终URL的Content-Type
            content_type = head_response.headers.get('Content-Type', '').lower()
            content_length = head_response.headers.get('Content-Length', '')
            print(f"   📋 响应头信息:")
            print(f"      Content-Type: {content_type}")
            print(f"      Content-Length: {content_length} 字节" if content_length else "      Content-Length: 未提供")
            
            # 随机延迟，模拟人类点击下载的行为
            self._random_delay(0.3, 1.0)
            
            # 使用最终URL进行下载（使用新的随机User-Agent）
            download_start_time = time.time()  # 记录下载开始时间
            print(f"   📥 开始下载...")
            download_headers = self._get_browser_headers(referer=download_url, is_download=True)
            
            # 添加连接保活机制
            download_headers['Connection'] = 'keep-alive'
            download_headers['Keep-Alive'] = 'timeout=300, max=1000'
            
            # 先尝试通过HEAD请求获取文件大小（用于计算超时时间）
            # 如果获取到真实URL且不使用代理失败，尝试使用代理
            total_size = 0
            try:
                head_response = session.head(final_url, headers=download_headers, proxies=proxies, timeout=60, allow_redirects=True)
                total_size = int(head_response.headers.get('content-length', 0))
            except Exception as e:
                # 如果HEAD请求失败且不使用代理，尝试使用代理
                if not use_proxy_for_download:
                    print(f"   ⚠️  不使用代理访问失败: {e}，尝试使用代理...")
                    proxy = self._get_next_proxy()
                    proxies = self._format_proxy_for_requests(proxy)
                    use_proxy_for_download = True
                    if proxies:
                        print(f"   🌐 切换到代理: {list(proxies.values())[0]}")
                    try:
                        head_response = session.head(final_url, headers=download_headers, proxies=proxies, timeout=60, allow_redirects=True)
                        total_size = int(head_response.headers.get('content-length', 0))
                    except:
                        total_size = 0
                else:
                    # 如果HEAD请求失败，使用默认值，稍后从GET响应中获取
                    total_size = 0
            
            # 根据文件大小动态调整超时时间（至少600秒）
            if total_size > 0:
                estimated_time = (total_size / 1024 / 1024) / 0.1  # 假设最小速度0.1MB/s
                timeout = max(600, int(estimated_time * 1.5))  # 至少600秒，或估算时间的1.5倍
            else:
                timeout = 600  # 如果不知道文件大小，使用600秒
            
            # 尝试下载，如果获取到真实URL且不使用代理失败，尝试使用代理
            try:
                response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                response.raise_for_status()
            except Exception as e:
                # 如果下载失败且不使用代理，尝试使用代理
                if not use_proxy_for_download:
                    print(f"   ⚠️  不使用代理下载失败: {e}，切换到代理重新下载...")
                    
                    # 在切换代理之前，先删除未下载完的文件
                    if save_path.exists():
                        try:
                            file_size = save_path.stat().st_size
                            save_path.unlink()
                            print(f"   🗑️  已删除未下载完的文件: {save_path.name} ({file_size / 1024 / 1024:.2f}MB)")
                        except Exception as del_e:
                            print(f"   ⚠️  删除文件失败: {del_e}")
                    
                    # 切换到代理
                    proxy = self._get_next_proxy()
                    proxies = self._format_proxy_for_requests(proxy)
                    use_proxy_for_download = True
                    if proxies:
                        print(f"   🌐 切换到代理: {list(proxies.values())[0]}")
                    
                    # 重新获取响应（使用代理）
                    response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                    response.raise_for_status()
                else:
                    raise
            
            # 如果之前没有获取到文件大小，现在从响应头获取
            if total_size == 0:
                total_size = int(response.headers.get('content-length', 0))
            
            # 检查响应内容是否为"error"（IP限制的情况）
            # 先读取一小部分内容检查
            preview = response.raw.read(10) if hasattr(response.raw, 'read') else b''
            if preview == b'error' or (len(preview) > 0 and preview.startswith(b'error')):
                # 如果不使用代理且返回error，尝试切换到代理
                if not use_proxy_for_download:
                    print(f"\n   ⚠️  服务器返回'error'（不使用代理），切换到代理重新下载...")
                    
                    # 在切换代理之前，先删除未下载完的文件
                    if save_path.exists():
                        try:
                            file_size = save_path.stat().st_size
                            save_path.unlink()
                            print(f"   🗑️  已删除未下载完的文件: {save_path.name} ({file_size / 1024 / 1024:.2f}MB)")
                        except Exception as del_e:
                            print(f"   ⚠️  删除文件失败: {del_e}")
                    
                    # 关闭当前响应
                    try:
                        response.close()
                    except:
                        pass
                    
                    # 切换到代理
                    proxy = self._get_next_proxy()
                    proxies = self._format_proxy_for_requests(proxy)
                    use_proxy_for_download = True
                    if proxies:
                        print(f"   🌐 切换到代理: {list(proxies.values())[0]}")
                    
                    # 使用代理重新获取响应
                    response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                    response.raise_for_status()
                    
                    # 重新检查响应内容
                    preview = response.raw.read(10) if hasattr(response.raw, 'read') else b''
                    if preview == b'error' or (len(preview) > 0 and preview.startswith(b'error')):
                        print(f"\n❌ 使用代理后服务器仍返回'error'，可能是IP地址被限制")
                        print(f"   💡 解决方案:")
                        print(f"      1. 切换网络（如使用5G/移动网络）")
                        print(f"      2. 更换VPN或代理服务器")
                        print(f"      3. 更换网络环境后重试")
                        return False
                else:
                    print(f"\n❌ 服务器返回'error'，可能是IP地址被限制")
                    print(f"   💡 解决方案:")
                    print(f"      1. 切换网络（如使用5G/移动网络）")
                    print(f"      2. 使用VPN或代理服务器")
                    print(f"      3. 更换网络环境后重试")
                    return False
            
            # 如果已经读取了预览，需要重新获取响应
            if preview:
                try:
                    response.close()
                except:
                    pass
                # 使用下载headers重新获取（使用动态超时时间）
                if total_size > 0:
                    estimated_time = (total_size / 1024 / 1024) / 0.1
                    timeout = max(600, int(estimated_time * 1.5))
                else:
                    timeout = 600
                response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                response.raise_for_status()
                # 更新total_size（以防响应头中的值不同）
                total_size = int(response.headers.get('content-length', total_size))
            
            # 检查是否支持断点续传
            supports_range = 'bytes' in response.headers.get('Accept-Ranges', '')
            
            # 检查文件是否已存在（断点续传）
            resume_pos = 0
            if save_path.exists() and supports_range:
                resume_pos = save_path.stat().st_size
                if resume_pos > 0 and resume_pos < total_size:
                    print(f"   📥 检测到未完成的下载，从 {resume_pos / 1024 / 1024:.2f}MB 处继续下载...")
                    # 关闭当前响应
                    response.close()
                    # 使用Range请求继续下载（使用动态超时时间）
                    download_headers['Range'] = f'bytes={resume_pos}-'
                    if total_size > 0:
                        remaining_size = total_size - resume_pos
                        estimated_time = (remaining_size / 1024 / 1024) / 0.1
                        timeout = max(600, int(estimated_time * 1.5))
                    else:
                        timeout = 600
                    response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                    response.raise_for_status()
            
            # 最大重试次数（增加到5次，提高成功率）
            max_retries = 5
            retry_count = 0
            downloaded = resume_pos
            
            # 下载速度监控
            last_check_time = time.time()
            last_downloaded = downloaded
            min_speed_mbps = 0.1  # 最小下载速度 0.1MB/s，如果低于此速度则重试
            speed_check_interval = 30  # 每30秒检查一次速度
            
            # 速度下降检测：记录初始速度，如果速度持续下降则重新建立连接
            initial_speed = None
            speed_degradation_threshold = 0.5  # 如果速度下降到初始速度的50%以下，重新建立连接
            connection_refresh_interval = 120  # 每120秒（2分钟）重新建立连接，避免速度下降
            last_connection_time = time.time()
            consecutive_slow_checks = 0  # 连续慢速检查次数
            
            while retry_count < max_retries:
                try:
                    # 打开文件（追加模式用于断点续传）
                    mode = 'ab' if resume_pos > 0 else 'wb'
                    with open(save_path, mode) as f:
                        chunk_count = 0
                        for chunk in response.iter_content(chunk_size=8192 * 2):  # 减小chunk_size到16KB，提高稳定性
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                chunk_count += 1
                                
                                # 检查是否下载完成
                                if total_size > 0 and downloaded >= total_size:
                                    print(f"\n   🔍 [DEBUG] 下载完成：downloaded={downloaded}, total_size={total_size}")
                                    break
                                
                                # 下载速度监控
                                current_time = time.time()
                                if current_time - last_check_time >= speed_check_interval:
                                    elapsed = current_time - last_check_time
                                    downloaded_bytes = downloaded - last_downloaded
                                    speed_mbps = (downloaded_bytes / 1024 / 1024) / elapsed if elapsed > 0 else 0
                                    
                                    # 记录初始速度（前两次检查的平均值）
                                    if initial_speed is None:
                                        if speed_mbps > 0:
                                            initial_speed = speed_mbps
                                    else:
                                        # 如果速度持续下降，考虑重新建立连接
                                        if speed_mbps < initial_speed * speed_degradation_threshold:
                                            consecutive_slow_checks += 1
                                            if consecutive_slow_checks >= 2:  # 连续2次检查都慢
                                                print(f"\n   ⚠️  检测到速度持续下降（当前: {speed_mbps:.2f}MB/s，初始: {initial_speed:.2f}MB/s），重新建立连接...")
                                                # 保存当前进度
                                                current_size = save_path.stat().st_size if save_path.exists() else downloaded
                                                # 关闭当前响应
                                                try:
                                                    response.close()
                                                except:
                                                    pass
                                                # 如果支持断点续传，从当前位置继续
                                                if supports_range and current_size < total_size:
                                                    resume_pos = current_size
                                                    download_headers['Range'] = f'bytes={resume_pos}-'
                                                    print(f"   📥 从 {resume_pos / 1024 / 1024:.2f}MB 处重新连接...")
                                                    response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                                                    response.raise_for_status()
                                                    downloaded = resume_pos
                                                    last_check_time = time.time()
                                                    last_downloaded = downloaded
                                                    last_connection_time = time.time()
                                                    consecutive_slow_checks = 0
                                                    # 重置初始速度
                                                    initial_speed = None
                                                else:
                                                    # 不支持断点续传，抛出异常触发重试
                                                    raise requests.exceptions.ConnectionError("速度下降，重新建立连接")
                                        else:
                                            consecutive_slow_checks = 0  # 速度正常，重置计数器
                                    
                                    # 定期重新建立连接（每2分钟），避免长时间连接导致速度下降
                                    if current_time - last_connection_time >= connection_refresh_interval and downloaded < total_size * 0.95:
                                        print(f"\n   🔄 定期刷新连接（已连接 {int((current_time - last_connection_time) / 60)} 分钟），重新建立连接以保持速度...")
                                        current_size = save_path.stat().st_size if save_path.exists() else downloaded
                                        try:
                                            response.close()
                                        except:
                                            pass
                                        # 如果支持断点续传，从当前位置继续
                                        if supports_range and current_size < total_size:
                                            resume_pos = current_size
                                            download_headers['Range'] = f'bytes={resume_pos}-'
                                            response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                                            response.raise_for_status()
                                            downloaded = resume_pos
                                            last_connection_time = time.time()
                                            last_check_time = time.time()
                                            last_downloaded = downloaded
                                            consecutive_slow_checks = 0
                                            # 重置初始速度
                                            initial_speed = None
                                    
                                    if speed_mbps < min_speed_mbps and downloaded < total_size * 0.9:
                                        # 速度过慢，可能是连接问题，主动中断并重试
                                        print(f"\n   ⚠️  下载速度过慢 ({speed_mbps:.2f}MB/s < {min_speed_mbps}MB/s)，主动重试...")
                                        raise requests.exceptions.ConnectionError("下载速度过慢，主动重试")
                                    
                                    last_check_time = current_time
                                    last_downloaded = downloaded
                                
                                # 每100个chunk更新一次进度（减少I/O，提高性能）
                                if chunk_count % 100 == 0 or downloaded >= total_size:
                                    if total_size:
                                        percent = (downloaded / total_size) * 100
                                        # 计算速度（基于实际下载时间）
                                        elapsed_time = time.time() - download_start_time
                                        if elapsed_time > 0:
                                            speed = (downloaded - resume_pos) / elapsed_time / 1024 / 1024
                                        else:
                                            speed = 0
                                        # 使用sys.stderr确保进度显示不会被其他输出干扰
                                        sys.stderr.write(f"\r   下载进度:3 {percent:.1f}% ({downloaded / 1024 / 1024:.2f}MB / {total_size / 1024 / 1024:.2f}MB) 速度: {speed:.2f}MB/s")
                                        sys.stderr.flush()
                                        
                                        # Debug: 如果进度100%，打印debug信息
                                        if percent >= 99.9:
                                            print(f"\n   🔍 [DEBUG] requests下载：进度{percent:.1f}%，downloaded={downloaded}, total_size={total_size}, chunk_count={chunk_count}")
                                        
                                        # 如果下载完成，退出循环
                                        if downloaded >= total_size:
                                            print(f"\n   🔍 [DEBUG] requests下载完成，退出chunk循环")
                                            break
                    
                    # 下载成功，退出循环
                    break
                    
                except (requests.exceptions.ChunkedEncodingError, 
                        requests.exceptions.ConnectionError,
                        ConnectionResetError,
                        IOError,
                        IncompleteRead) as e:
                    # 检查是否是IncompleteRead错误或连接中断
                    error_str = str(e)
                    is_incomplete = isinstance(e, IncompleteRead) or 'IncompleteRead' in error_str or 'Connection broken' in error_str
                    
                    if is_incomplete:
                        retry_count += 1
                        current_size = save_path.stat().st_size if save_path.exists() else 0
                        
                        if retry_count < max_retries:
                            print(f"\n   ⚠️  下载中断（已下载 {current_size / 1024 / 1024:.2f}MB），正在重试 ({retry_count}/{max_retries})...")
                            
                            # 关闭当前响应
                            try:
                                response.close()
                            except:
                                pass
                            
                            # 指数退避策略：等待时间逐渐增加（2秒、4秒、8秒、16秒、32秒）
                            wait_time = min(2 ** retry_count, 32)
                            print(f"   ⏳ 等待 {wait_time} 秒后重试...")
                            time.sleep(wait_time)
                            
                            # 如果支持断点续传，从当前位置继续
                            if supports_range and current_size < total_size:
                                resume_pos = current_size
                                download_headers['Range'] = f'bytes={resume_pos}-'
                                print(f"   📥 从 {resume_pos / 1024 / 1024:.2f}MB 处继续下载...")
                                
                                # 增大超时时间（根据剩余大小动态调整，最少600秒）
                                remaining_size = total_size - resume_pos
                                estimated_time = (remaining_size / 1024 / 1024) / min_speed_mbps  # 根据最小速度估算时间
                                timeout = max(600, int(estimated_time * 1.5))  # 至少600秒，或估算时间的1.5倍
                                
                                response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                                response.raise_for_status()
                                downloaded = resume_pos
                                last_check_time = time.time()
                                last_downloaded = downloaded
                            else:
                                # 不支持断点续传，重新开始下载
                                print(f"   📥 服务器不支持断点续传，重新开始下载...")
                                if save_path.exists():
                                    save_path.unlink()
                                
                                # 根据文件大小动态调整超时时间
                                estimated_time = (total_size / 1024 / 1024) / min_speed_mbps
                                timeout = max(600, int(estimated_time * 1.5))
                                
                                response = session.get(final_url, headers=download_headers, proxies=proxies, stream=True, timeout=timeout)
                                response.raise_for_status()
                                downloaded = 0
                                resume_pos = 0
                                last_check_time = time.time()
                                last_downloaded = 0
                        else:
                            # 重试次数用完
                            # 如果获取到真实URL且不使用代理，尝试切换到代理
                            if has_real_url and not use_proxy_for_download:
                                print(f"\n   ⚠️  不使用代理下载失败（已重试 {max_retries} 次），切换到代理重新下载...")
                                
                                # 在切换代理之前，先删除未下载完的文件
                                if save_path.exists():
                                    try:
                                        file_size = save_path.stat().st_size
                                        save_path.unlink()
                                        print(f"   🗑️  已删除未下载完的文件: {save_path.name} ({file_size / 1024 / 1024:.2f}MB)")
                                    except Exception as del_e:
                                        print(f"   ⚠️  删除文件失败: {del_e}")
                                
                                # 切换到代理，重新尝试下载（递归调用，但强制使用代理）
                                try:
                                    print(f"   🔄 使用代理重新下载...")
                                    return self._download_file(download_url, save_path, use_proxy=True)
                                except Exception as retry_e:
                                    print(f"\n❌ 使用代理重新下载也失败: {retry_e}")
                                    return False
                            else:
                                # 重试次数用完，抛出异常
                                print(f"\n   ❌ 下载失败，已重试 {max_retries} 次")
                                raise
                    else:
                        # 其他错误
                        # 如果获取到真实URL且不使用代理，尝试切换到代理
                        if has_real_url and not use_proxy_for_download:
                            print(f"\n   ⚠️  下载出错（不使用代理），切换到代理重新下载...")
                            
                            # 在切换代理之前，先删除未下载完的文件
                            if save_path.exists():
                                try:
                                    file_size = save_path.stat().st_size
                                    save_path.unlink()
                                    print(f"   🗑️  已删除未下载完的文件: {save_path.name} ({file_size / 1024 / 1024:.2f}MB)")
                                except Exception as del_e:
                                    print(f"   ⚠️  删除文件失败: {del_e}")
                            
                            # 切换到代理，重新尝试下载（递归调用，但强制使用代理）
                            try:
                                print(f"   🔄 使用代理重新下载...")
                                return self._download_file(download_url, save_path, use_proxy=True)
                            except Exception as retry_e:
                                print(f"\n❌ 使用代理重新下载也失败: {retry_e}")
                                return False
                        else:
                            # 其他错误，直接抛出
                            raise
                finally:
                    # 确保响应被正确关闭，避免线程错误
                    try:
                        if response:
                            response.close()
                    except:
                        pass
            
            # 验证下载的文件确实是APK
            if save_path.exists():
                file_size = save_path.stat().st_size
                
                # 检查文件大小是否与预期一致
                if total_size > 0 and file_size < total_size:
                    print(f"\n⚠️  文件大小不完整: {file_size / 1024 / 1024:.2f}MB / {total_size / 1024 / 1024:.2f}MB")
                    # 如果文件大小不完整，但大于1MB，保留文件以便下次断点续传
                    if file_size > 1024 * 1024:  # 大于1MB
                        print(f"   💡 文件已部分下载，下次运行时会自动继续下载")
                        return False  # 返回False，但不删除文件
                    else:
                        # 文件太小，删除
                        save_path.unlink()
                        return False
                
                if file_size < 1024:  # 小于1KB可能是HTML错误页面
                    # 检查文件内容是否为"error"
                    try:
                        with open(save_path, 'rb') as f:
                            content = f.read(10)
                            if content == b'error' or content.startswith(b'error'):
                                print(f"\n❌ 下载的文件内容是'error'，IP地址可能被限制")
                                print(f"   💡 解决方案:")
                                print(f"      1. 切换网络（如使用5G/移动网络）")
                                print(f"      2. 使用VPN或代理服务器")
                                print(f"      3. 更换网络环境后重试")
                            else:
                                print(f"\n⚠️  下载的文件太小({file_size}字节)，可能是错误页面，删除文件")
                    except:
                        print(f"\n⚠️  下载的文件太小({file_size}字节)，可能是错误页面，删除文件")
                    save_path.unlink()
                    return False
                
                # 检查文件头是否是APK格式（APK文件以ZIP格式开头）
                try:
                    with open(save_path, 'rb') as f:
                        file_header = f.read(4)
                        # APK文件是ZIP格式，ZIP文件头是PK\x03\x04或PK\x05\x06
                        if file_header[:2] == b'PK':
                            # 计算下载耗时
                            download_end_time = time.time()
                            download_duration = download_end_time - download_start_time
                            download_minutes = int(download_duration // 60)
                            download_seconds = int(download_duration % 60)
                            if download_minutes > 0:
                                print(f"\n✅ 下载完成: {save_path.name} ({file_size / 1024 / 1024:.2f}MB) 耗时: {download_minutes}分{download_seconds}秒")
                            else:
                                print(f"\n✅ 下载完成: {save_path.name} ({file_size / 1024 / 1024:.2f}MB) 耗时: {download_seconds}秒")
                            self._create_zip_for_apk(save_path)
                            return True
                        else:
                            print(f"\n⚠️  文件格式不正确（不是APK/ZIP格式），可能是HTML页面，删除文件")
                            save_path.unlink()
                            return False
                except Exception as e:
                    print(f"\n⚠️  验证文件失败: {e}，但文件已下载")
                    self._create_zip_for_apk(save_path)
                    return True
            
            # 计算下载耗时
            download_end_time = time.time()
            download_duration = download_end_time - download_start_time
            download_minutes = int(download_duration // 60)
            download_seconds = int(download_duration % 60)
            if download_minutes > 0:
                print(f"\n✅ 下载完成: {save_path.name} 耗时: {download_minutes}分{download_seconds}秒")
            else:
                print(f"\n✅ 下载完成: {save_path.name} 耗时: {download_seconds}秒")
            self._create_zip_for_apk(save_path)
            return True
            
        except Exception as e:
            # 如果获取到真实URL且不使用代理下载失败，尝试使用代理重新下载
            if has_real_url and not use_proxy_for_download:
                print(f"\n   ⚠️  不使用代理下载失败: {e}，切换到代理重新下载...")
                
                # 在切换代理之前，先删除未下载完的文件
                if save_path.exists():
                    try:
                        file_size = save_path.stat().st_size
                        save_path.unlink()
                        print(f"   🗑️  已删除未下载完的文件: {save_path.name} ({file_size / 1024 / 1024:.2f}MB)")
                    except Exception as del_e:
                        print(f"   ⚠️  删除文件失败: {del_e}")
                
                # 切换到代理，重新尝试下载（递归调用，但强制使用代理）
                try:
                    print(f"   🔄 使用代理重新下载...")
                    return self._download_file(download_url, save_path, use_proxy=True)
                except Exception as retry_e:
                    print(f"\n❌ 使用代理重新下载也失败: {retry_e}")
                    return False
            else:
                print(f"\n❌ 下载失败: {e}")
                return False
    
    def _cleanup_folder_on_failure(self, folder_path: Path):
        """下载失败时清理文件夹"""
        try:
            if not folder_path.exists():
                return
            
            # 检查文件夹内容
            files = list(folder_path.iterdir())
            
            # 如果文件夹为空，直接删除
            if not files:
                try:
                    folder_path.rmdir()
                    print(f"   🗑️  已删除空文件夹: {folder_path.name}")
                    return
                except Exception as e:
                    print(f"   ⚠️  删除空文件夹失败: {e}")
                    return
            
            # 检查是否有有效的APK文件
            has_valid_apk = False
            for file in files:
                if file.is_file() and file.suffix.lower() == '.apk':
                    try:
                        # 检查文件头是否是APK格式
                        with open(file, 'rb') as f:
                            file_header = f.read(4)
                            if file_header[:2] == b'PK':
                                # 有有效的APK文件，不删除文件夹
                                has_valid_apk = True
                                break
                    except:
                        pass
            
            # 如果有有效的APK文件，不删除文件夹
            if has_valid_apk:
                print(f"   ℹ️  文件夹中包含有效的APK文件，保留文件夹")
                return
            
            # 删除文件夹中的所有内容
            for file in files:
                try:
                    if file.is_file():
                        file.unlink()
                        print(f"   🗑️  已删除文件: {file.name}")
                    elif file.is_dir():
                        import shutil
                        shutil.rmtree(file)
                        print(f"   🗑️  已删除子文件夹: {file.name}")
                except Exception as e:
                    print(f"   ⚠️  删除失败 {file.name}: {e}")
            
            # 删除空文件夹
            try:
                folder_path.rmdir()
                print(f"   🗑️  已删除文件夹: {folder_path.name}")
            except Exception as e:
                # 如果文件夹不为空（可能还有隐藏文件），尝试强制删除
                try:
                    import shutil
                    shutil.rmtree(folder_path)
                    print(f"   🗑️  已强制删除文件夹: {folder_path.name}")
                except Exception as e2:
                    print(f"   ⚠️  删除文件夹失败: {e2}")
        except Exception as e:
            print(f"   ⚠️  清理文件夹时出错: {e}")
    
    def _create_info_files(self, folder_path: Path):
        """创建信息文件"""
        # 创建"不定时更新最新版本.txt"
        file1 = folder_path / "不定时更新最新版本.txt"
        with open(file1, 'w', encoding='utf-8') as f:
            f.write("本文件夹内容会不定时更新最新版本，请关注。\n")
        
        # 创建"先保存再下载避免失效.txt"
        file2 = folder_path / "先保存再下载避免失效.txt"
        with open(file2, 'w', encoding='utf-8') as f:
            f.write("请先保存到自己的网盘再下载，避免链接失效。\n")
    
    def process_game(self, game: dict, index: int) -> bool:
        """处理单个游戏"""
        game_name = game.get('游戏名称', '')
        page_url = game.get('详情页链接', '')
        downloaded = game.get('是否已下载', '否')
        
        # 如果已下载，跳过
        if downloaded == '是':
            return True
        
        print(f"\n{'='*60}")
        print(f"[{index}/{len(self.games)}] 处理: {game_name}")
        print(f"{'='*60}")
        
        # 提前获取文件夹名（优化：在解析详情页之前）
        print(f"🔍 获取文件夹名...")
        folder_name = self._get_folder_name(game_name)
        print(f"📁 文件夹名: {folder_name}")
        
        # 先解析详情页获取文件大小（用于比较）
        print(f"🔍 解析详情页...")
        detail_info = self._parse_game_detail(page_url)
        
        if not detail_info:
            print(f"❌ 无法解析详情页，跳过")
            # 标记为没有下载链接
            game['是否有安卓下载链接'] = '否'
            self._save_csv()
            return False
        
        # 获取详情页的文件大小（直接使用详情页解析的大小）
        size_str = detail_info.get('size', '')
        if size_str:
            expected_size_mb = self._parse_size_to_mb(size_str)
            print(f"   📊 详情页文件大小: {size_str} ({expected_size_mb:.2f}MB)")
        else:
            expected_size_mb = 0.0
            print(f"   ⚠️  详情页未提供文件大小信息")
        
        # 检查文件夹是否已存在，并比较文件大小
        folder_path = self.download_base_dir / folder_name
        if folder_path.exists() and folder_path.is_dir():
            print(f"📂 文件夹已存在，检查文件...")
            # 检查文件夹中的文件
            files = [f for f in folder_path.iterdir() if f.is_file()]
            if files:
                # 查找最大的文件
                largest_file = max(files, key=lambda f: f.stat().st_size)
                existing_file_size_bytes = largest_file.stat().st_size
                existing_file_size_mb = existing_file_size_bytes / 1024 / 1024
                print(f"   📄 找到文件: {largest_file.name} ({existing_file_size_mb:.2f}MB)")
                
                # 如果详情页有文件大小信息，进行比较
                if expected_size_mb > 0:
                    print(f"   📊 详情页文件大小: {expected_size_mb:.2f}MB")
                    print(f"   📊 已存在文件大小: {existing_file_size_mb:.2f}MB")
                    
                    # 如果已存在文件大小 >= 详情页文件大小，认为已下载完成
                    # 允许5%的误差（因为文件大小可能有轻微差异）
                    if existing_file_size_mb >= expected_size_mb * 0.95:
                        print(f"✅ 已存在文件大小 ({existing_file_size_mb:.2f}MB) >= 详情页文件大小 ({expected_size_mb:.2f}MB)，认为已下载完成，跳过")
                        game['是否已下载'] = '是'
                        game['是否有安卓下载链接'] = '是'
                        self._save_csv()
                        return True
                    else:
                        print(f"⚠️  已存在文件大小 ({existing_file_size_mb:.2f}MB) < 详情页文件大小 ({expected_size_mb:.2f}MB)，删除旧文件并重新下载")
                        # 删除文件夹中的所有APK文件，准备重新下载
                        for file in files:
                            if file.suffix.lower() == '.apk':
                                try:
                                    file.unlink()
                                    print(f"   🗑️  已删除旧文件: {file.name}")
                                except Exception as e:
                                    print(f"   ⚠️  删除文件失败 {file.name}: {e}")
                else:
                    # 如果详情页没有文件大小信息，使用原来的逻辑（大于1M认为已下载）
                    if existing_file_size_mb > 1.0:
                        print(f"⚠️  详情页未提供文件大小，但已存在文件大于1M ({existing_file_size_mb:.2f}MB)，认为已下载完成，跳过")
                        game['是否已下载'] = '是'
                        game['是否有安卓下载链接'] = '是'
                        self._save_csv()
                        return True
                    else:
                        print(f"⚠️  文件大小 {existing_file_size_mb:.2f}MB 小于1M，可能是无效文件，继续下载")
        
        # 获取下载链接
        download_url = detail_info.get('download_url', '')
        if not download_url:
            print(f"❌ 无法获取下载链接，跳过")
            # 标记为没有下载链接
            game['是否有安卓下载链接'] = '否'
            self._save_csv()
            return False
        
        # 标记为有下载链接
        game['是否有安卓下载链接'] = '是'
        self._save_csv()
        
        # 验证下载链接（不强制要求.apk后缀，因为下载地址可能带查询参数）
        # api.kxdw.com/adown/ 这类链接是可信的下载地址，直接跳过校验
        if 'api.kxdw.com/adown/' in download_url:
            print(f"   ✅ 检测到可信下载地址 (api.kxdw.com/adown/)，跳过校验")
        else:
            # 判断是否为HTML页面的规则：
            print(f"   🔍 检查链接是否为HTML页面...")
            is_html = False
            html_reasons = []
            
            if download_url.endswith('.html'):
                is_html = True
                html_reasons.append("URL以.html结尾")
            elif download_url.endswith('.htm'):
                is_html = True
                html_reasons.append("URL以.htm结尾")
            elif 'kxdw.com/android/' in download_url:
                is_html = True
                html_reasons.append("URL包含详情页路径(kxdw.com/android/)")
            elif download_url.startswith('javascript:'):
                is_html = True
                html_reasons.append("URL是javascript链接")
            elif download_url.startswith('#'):
                is_html = True
                html_reasons.append("URL是锚点链接")
            
            if is_html:
                print(f"   ❌ 链接被判断为HTML页面，原因: {', '.join(html_reasons)}")
                print(f"   📋 链接: {download_url[:100]}...")
                # 链接无效，更新标记并返回（不会创建文件夹或下载）
                game['是否有安卓下载链接'] = '否'
                self._save_csv()
                return False
            else:
                print(f"   ✅ 链接通过初步检查（不是明显的HTML页面）")
        
        # 检查文件大小（优先使用页面解析的大小，如果无法解析则通过HEAD请求获取）
        size_mb = 0.0
        size_str = detail_info.get('size', '')
        if size_str:
            size_mb = self._parse_size_to_mb(size_str)
            if size_mb > 1024:
                print(f"⏭️  文件大小 {size_mb:.2f}MB ({size_mb/1024:.2f}G) 超过1G，跳过并标记为已下载")
                game['是否已下载'] = '是'
                self._save_csv()
                return False
        
        # 如果无法从页面解析大小，通过HEAD请求获取文件大小
        if size_mb == 0.0:
            print(f"   🔍 页面未显示文件大小，通过HEAD请求检查...")
            try:
                # 使用随机User-Agent和完整请求头
                headers = self._get_browser_headers(referer='https://www.kxdw.com/', is_download=True)
                # 获取代理
                proxy = self._get_next_proxy()
                proxies = self._format_proxy_for_requests(proxy)
                
                head_response = requests.head(download_url, headers=headers, proxies=proxies, timeout=10, allow_redirects=True)
                
                # 检查是否被重定向到本地地址
                if '127.0.0.1' in head_response.url or 'localhost' in head_response.url:
                    print(f"   ⚠️  检测到重定向到本地地址: {head_response.url}")
                    return False
                
                content_length = head_response.headers.get('Content-Length')
                if content_length:
                    size_bytes = int(content_length)
                    size_mb = size_bytes / 1024 / 1024
                    print(f"   📊 文件大小: {size_mb:.2f}MB")
                    if size_mb > 1024:
                        print(f"⏭️  文件大小 {size_mb:.2f}MB ({size_mb/1024:.2f}G) 超过1G，跳过并标记为已下载")
                        game['是否已下载'] = '是'
                        self._save_csv()
                        return False
                
                # api.kxdw.com/adown/ 这类链接是可信的，跳过Content-Type检查
                if 'api.kxdw.com/adown/' not in download_url:
                    # 同时检查Content-Type
                    content_type = head_response.headers.get('Content-Type', '').lower()
                    if 'html' in content_type or 'text/html' in content_type:
                        print(f"   ❌ 链接指向HTML页面，不是APK文件，跳过")
                        # 链接无效，更新标记并返回（不会创建文件夹或下载）
                        game['是否有安卓下载链接'] = '否'
                        self._save_csv()
                        return False
                    elif 'application/vnd.android.package-archive' in content_type or 'application/octet-stream' in content_type:
                        print(f"   ✅ 验证通过，是APK文件")
                    else:
                        print(f"   ⚠️  文件类型: {content_type}，继续尝试下载")
                else:
                    print(f"   ✅ 可信下载地址，跳过Content-Type检查")
            except Exception as e:
                print(f"   ⚠️  验证链接失败: {e}，继续尝试下载")
        else:
            # 如果已经从页面获取到大小，只验证Content-Type
            # api.kxdw.com/adown/ 这类链接是可信的，跳过Content-Type检查
            if 'api.kxdw.com/adown/' in download_url:
                print(f"   ✅ 可信下载地址，跳过Content-Type检查")
            else:
                print(f"   🔍 验证下载链接...")
                try:
                    # 使用随机User-Agent和完整请求头
                    headers = self._get_browser_headers(referer='https://www.kxdw.com/', is_download=True)
                    # 获取代理
                    proxy = self._get_next_proxy()
                    proxies = self._format_proxy_for_requests(proxy)
                    
                    head_response = requests.head(download_url, headers=headers, proxies=proxies, timeout=10, allow_redirects=True)
                    
                    # 检查是否被重定向到本地地址
                    if '127.0.0.1' in head_response.url or 'localhost' in head_response.url:
                        print(f"   ⚠️  检测到重定向到本地地址: {head_response.url}")
                        return False
                    content_type = head_response.headers.get('Content-Type', '').lower()
                    content_length = head_response.headers.get('Content-Length', '')
                    final_url = head_response.url  # 获取重定向后的最终URL
                    
                    print(f"   📋 响应头信息:")
                    print(f"      Content-Type: {content_type}")
                    print(f"      Content-Length: {content_length} 字节" if content_length else "      Content-Length: 未提供")
                    print(f"      最终URL: {final_url[:100]}...")
                    
                    # 判断是否为HTML页面
                    if 'html' in content_type or 'text/html' in content_type:
                        print(f"   ❌ 链接指向HTML页面（Content-Type: {content_type}），不是APK文件，跳过")
                        # 链接无效，更新标记并返回（不会创建文件夹或下载）
                        game['是否有安卓下载链接'] = '否'
                        self._save_csv()
                        return False
                    elif 'application/vnd.android.package-archive' in content_type:
                        print(f"   ✅ 验证通过，是APK文件（Content-Type: {content_type}）")
                    elif 'application/octet-stream' in content_type:
                        print(f"   ✅ 验证通过，是二进制文件（Content-Type: {content_type}），可能是APK")
                    else:
                        print(f"   ⚠️  文件类型: {content_type}，继续尝试下载")
                except Exception as e:
                    print(f"   ⚠️  验证链接失败: {e}，继续尝试下载")
        
        # 只有获取到有效的下载链接后，才会执行后续的创建文件夹和下载操作
        print(f"📥 下载链接: {download_url[:80]}...")
        
        # 创建文件夹（如果不存在，确保已经有有效的下载链接）
        if not folder_path.exists():
            folder_path.mkdir(parents=True, exist_ok=True)
            # 设置文件夹的创建时间为当前时间
            current_time = time.time()
            try:
                os.utime(folder_path, (current_time, current_time))
            except Exception as e:
                # 如果设置时间失败，不影响后续流程
                pass
            # 格式化时间显示
            create_time_str = datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
            print(f"📁 已创建文件夹: {folder_name} (创建时间: {create_time_str})")
        
        # 确定文件名
        # 从URL路径中提取扩展名，如果URL中有.apk（可能在查询参数前），也提取
        parsed_url = urlparse(download_url)
        file_ext = os.path.splitext(parsed_url.path)[1]
        
        # 如果路径中没有扩展名，检查URL中是否包含.apk
        if not file_ext or file_ext not in ['.apk', '.APK']:
            if '.apk' in download_url.lower():
                # URL中包含.apk，使用.apk扩展名
                file_ext = '.apk'
            else:
                # 默认使用.apk扩展名（因为这是安卓下载）
                file_ext = '.apk'
        
        file_name = f"{folder_name}{file_ext}"
        save_path = folder_path / file_name
        
        # 如果文件已存在，检查文件大小（与详情页文件大小比较）
        if save_path.exists():
            file_size_mb = save_path.stat().st_size / 1024 / 1024
            file_size_bytes = save_path.stat().st_size
            
            # 如果详情页有文件大小信息，进行比较
            if expected_size_mb > 0:
                expected_size_bytes = int(expected_size_mb * 1024 * 1024)
                # 允许5%的误差
                if file_size_bytes >= expected_size_bytes * 0.95:
                    print(f"⏭️  文件已存在且大小 ({file_size_mb:.2f}MB) >= 详情页文件大小 ({expected_size_mb:.2f}MB)，跳过下载")
                else:
                    print(f"⚠️  文件已存在但大小 ({file_size_mb:.2f}MB) < 详情页文件大小 ({expected_size_mb:.2f}MB)，删除旧文件并重新下载")
                    # 删除旧文件，重新下载
                    try:
                        save_path.unlink()
                        print(f"   🗑️  已删除旧文件: {file_name}")
                    except Exception as e:
                        print(f"   ⚠️  删除文件失败: {e}")
                    # 下载文件
                    print(f"⬇️  开始下载: {file_name}")
                    # 如果启用了Chrome，优先使用Chrome下载（更稳定，避免连接中断）
                    if self.use_chrome:
                        if not self._download_with_chrome(download_url, save_path, expected_size_mb):
                            # Chrome下载失败，回退到requests下载
                            print(f"   ⚠️  Chrome下载失败，切换到requests下载...")
                            # 如果获取到了真实下载地址，使用真实地址下载
                            final_download_url = self._last_real_download_url if self._last_real_download_url else download_url
                            if self._last_real_download_url:
                                print(f"   🔄 使用真实下载地址: {final_download_url[:80]}...")
                            if not self._download_file(final_download_url, save_path):
                                # 下载失败，删除文件夹
                                self._cleanup_folder_on_failure(folder_path)
                                return False
                    else:
                        if not self._download_file(download_url, save_path):
                            # 下载失败，删除文件夹
                            self._cleanup_folder_on_failure(folder_path)
                            return False
            else:
                # 如果详情页没有文件大小信息，使用原来的逻辑（大于1M认为已下载）
                if file_size_mb > 1.0:
                    print(f"⏭️  文件已存在且大小 {file_size_mb:.2f}MB > 1M（详情页未提供文件大小），跳过下载")
                else:
                    print(f"⚠️  文件已存在但大小 {file_size_mb:.2f}MB <= 1M，可能是无效文件，重新下载")
                    # 删除旧文件，重新下载
                    try:
                        save_path.unlink()
                        print(f"   🗑️  已删除旧文件: {file_name}")
                    except Exception as e:
                        print(f"   ⚠️  删除文件失败: {e}")
                    # 下载文件
                    print(f"⬇️  开始下载: {file_name}")
                    # 如果启用了Chrome，优先使用Chrome下载（更稳定，避免连接中断）
                    if self.use_chrome:
                        if not self._download_with_chrome(download_url, save_path, expected_size_mb):
                            # Chrome下载失败，回退到requests下载
                            print(f"   ⚠️  Chrome下载失败，切换到requests下载...")
                            # 如果获取到了真实下载地址，使用真实地址下载
                            final_download_url = self._last_real_download_url if self._last_real_download_url else download_url
                            if self._last_real_download_url:
                                print(f"   🔄 使用真实下载地址: {final_download_url[:80]}...")
                            if not self._download_file(final_download_url, save_path):
                                # 下载失败，删除文件夹
                                self._cleanup_folder_on_failure(folder_path)
                                return False
                    else:
                        if not self._download_file(download_url, save_path):
                            # 下载失败，删除文件夹
                            self._cleanup_folder_on_failure(folder_path)
                            return False
        else:
            # 下载文件
            print(f"⬇️  开始下载: {file_name}")
            # 如果启用了Chrome，优先使用Chrome下载（更稳定，避免连接中断）
            if self.use_chrome:
                if not self._download_with_chrome(download_url, save_path, expected_size_mb):
                    # Chrome下载失败，回退到requests下载
                    print(f"   ⚠️  Chrome下载失败，切换到requests下载...")
                    # 如果获取到了真实下载地址，使用真实地址下载
                    final_download_url = self._last_real_download_url if self._last_real_download_url else download_url
                    if self._last_real_download_url:
                        print(f"   🔄 使用真实下载地址: {final_download_url[:80]}...")
                    if not self._download_file(final_download_url, save_path):
                        # 下载失败，删除文件夹
                        self._cleanup_folder_on_failure(folder_path)
                        return False
            else:
                if not self._download_file(download_url, save_path):
                    # 下载失败，删除文件夹
                    self._cleanup_folder_on_failure(folder_path)
                    return False
        
        # 创建信息文件
        print(f"📝 创建信息文件...")
        self._create_info_files(folder_path)
        
        # 更新CSV
        game['是否已下载'] = '是'
        self._save_csv()
        
        print(f"✅ 完成!")
        return True

    def _create_zip_for_apk(self, apk_path: Path):
        """在APK所在目录生成同名ZIP文件"""
        try:
            if not apk_path or not apk_path.exists():
                return
            if apk_path.suffix.lower() != '.apk':
                return

            zip_path = apk_path.with_suffix('.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(apk_path, apk_path.name)
            zip_size_mb = zip_path.stat().st_size / 1024 / 1024
            print(f"   📦 已生成ZIP: {zip_path.name} ({zip_size_mb:.2f}MB)")
        except Exception as e:
            print(f"   ⚠️  生成ZIP失败: {apk_path.name if apk_path else '未知文件'} -> {e}")
            try:
                if apk_path:
                    zip_path = apk_path.with_suffix('.zip')
                    if zip_path.exists():
                        zip_path.unlink()
            except:
                pass
    
    def run(self, start_index: int = 0, limit: Optional[int] = None):
        """运行批量下载"""
        print(f"\n{'='*60}")
        print(f"🚀 开始批量下载")
        print(f"{'='*60}")
        
        if not self.use_chrome:
            print(f"⚠️  警告: 未启用Chrome模式！")
            print(f"   建议使用 --chrome 参数来模拟人类操作，避免被拦截")
            print(f"   当前将使用requests方式，可能被网站拦截")
            print(f"{'='*60}\n")
        else:
            print(f"✅ Chrome模式已启用 - 将模拟人类操作")
            print(f"{'='*60}\n")
        
        print(f"总游戏数: {len(self.games)}")
        print(f"起始位置: {start_index}")
        if limit:
            print(f"处理数量: {limit}")
        print(f"{'='*60}\n")
        
        end_index = len(self.games)
        if limit:
            end_index = min(start_index + limit, len(self.games))
        
        success_count = 0
        skip_count = 0
        fail_count = 0
        
        for i in range(start_index, end_index):
            game = self.games[i]
            
            # 如果已下载，跳过
            if game.get('是否已下载') == '是':
                skip_count += 1
                continue
            
            try:
                if self.process_game(game, i + 1):
                    success_count += 1
                else:
                    fail_count += 1
                
                # 避免请求过快
                wait_time = 3 if self.use_chrome else 2
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️  用户中断")
                break
            except Exception as e:
                print(f"\n❌ 处理失败: {e}")
                fail_count += 1
                continue
        
        # 清理Chrome资源，避免后台线程JSON解析错误
        if self.tab:
            try:
                # 先移除所有事件监听器
                try:
                    if hasattr(self.tab, 'Page'):
                        self.tab.Page.downloadWillBegin = None
                except:
                    pass
                # 等待一小段时间，让接收循环处理完当前消息
                time.sleep(0.1)
                # 停止tab（这会停止接收循环）
                self.tab.stop()
                if self.browser:
                    self.browser.close_tab(self.tab)
            except:
                pass
        
        print(f"\n{'='*60}")
        print(f"📊 处理完成统计")
        print(f"{'='*60}")
        print(f"成功: {success_count}")
        print(f"跳过: {skip_count}")
        print(f"失败: {fail_count}")
        print(f"{'='*60}\n")


def test_download_url(url: str):
    """测试下载链接，查看重定向和响应信息"""
    if not requests:
        print("❌ 请安装 requests: pip3 install requests")
        return
    
    print(f"\n{'='*60}")
    print(f"🔍 测试下载链接")
    print(f"{'='*60}")
    print(f"URL: {url}\n")
    
    try:
        # 使用随机User-Agent和完整请求头（测试函数，使用简单的headers）
        headers = {
            'User-Agent': random.choice(KXDWDownloader.USER_AGENTS),
            'Referer': 'https://www.kxdw.com/',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
        }
        
        # 使用Session来跟踪重定向链
        session = requests.Session()
        session.max_redirects = 10
        
        print("📋 步骤1: 发送HEAD请求查看重定向...")
        head_response = session.head(url, headers=headers, timeout=30, allow_redirects=True)
        
        redirect_history = head_response.history
        final_url = head_response.url
        
        print(f"   初始URL: {url}")
        if redirect_history:
            print(f"   ✅ 发现 {len(redirect_history)} 次重定向:")
            for i, resp in enumerate(redirect_history, 1):
                redirect_url = resp.headers.get('Location', 'N/A')
                print(f"      {i}. {resp.status_code} {resp.reason}")
                print(f"         -> {redirect_url[:120]}")
            print(f"   最终URL: {final_url}")
        else:
            print(f"   ℹ️  无重定向，直接访问")
        
        print(f"\n📋 步骤2: 查看响应头信息...")
        print(f"   Status Code: {head_response.status_code}")
        print(f"   Content-Type: {head_response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {head_response.headers.get('Content-Length', 'N/A')} 字节")
        print(f"   Content-Disposition: {head_response.headers.get('Content-Disposition', 'N/A')}")
        print(f"   Location: {head_response.headers.get('Location', 'N/A')}")
        
        print(f"\n📋 步骤3: 发送GET请求查看实际响应...")
        get_response = session.get(url, headers=headers, timeout=30, allow_redirects=True, stream=True)
        
        print(f"   最终URL: {get_response.url}")
        print(f"   Status Code: {get_response.status_code}")
        print(f"   Content-Type: {get_response.headers.get('Content-Type', 'N/A')}")
        print(f"   Content-Length: {get_response.headers.get('Content-Length', 'N/A')} 字节")
        print(f"   Content-Disposition: {get_response.headers.get('Content-Disposition', 'N/A')}")
        
        # 读取前几个字节查看文件头
        if get_response.status_code == 200:
            content_preview = get_response.content[:20]
            print(f"\n📋 步骤4: 查看文件头（前20字节）...")
            print(f"   十六进制: {content_preview.hex()}")
            print(f"   ASCII: {repr(content_preview)}")
            
            # 检查是否是APK/ZIP格式
            if content_preview[:2] == b'PK':
                print(f"   ✅ 文件头是PK（ZIP/APK格式）")
            elif content_preview.startswith(b'<!DOCTYPE') or content_preview.startswith(b'<html'):
                print(f"   ⚠️  文件头是HTML格式")
            else:
                print(f"   ℹ️  文件头格式: {content_preview[:4]}")
        
        # 尝试使用Chrome访问
        if pychrome:
            print(f"\n📋 步骤5: 使用Chrome模拟访问...")
            try:
                browser = pychrome.Browser(url="http://127.0.0.1:9222")
                # 创建新标签页
                tab = browser.new_tab()
                tab.start()
                
                # 监听下载事件
                download_info = {'triggered': False, 'url': None}
                
                def on_download_will_begin(**kwargs):
                    download_info['triggered'] = True
                    download_info['url'] = kwargs.get('url', 'N/A')
                    print(f"   📥 检测到下载事件!")
                    print(f"      下载URL: {kwargs.get('url', 'N/A')[:100]}")
                    print(f"      建议文件名: {kwargs.get('suggestedFilename', 'N/A')}")
                
                tab.Page.downloadWillBegin = on_download_will_begin
                
                # 启用Page域
                tab.Page.enable()
                
                print(f"   🌐 导航到: {url}")
                tab.Page.navigate(url=url)
                
                # 等待页面加载和可能的下载
                print(f"   ⏳ 等待响应（最多10秒）...")
                for i in range(20):  # 等待最多10秒
                    time.sleep(0.5)
                    if download_info['triggered']:
                        break
                    
                    # 检查当前页面状态
                    try:
                        result = tab.Runtime.evaluate(expression="""
                            (function() {
                                return {
                                    url: window.location.href,
                                    readyState: document.readyState
                                };
                            })();
                        """, returnByValue=True)
                        current_url = result.get("result", {}).get("value", {}).get("url", "")
                        if current_url and current_url != "about:blank" and url not in current_url:
                            print(f"   🔄 检测到重定向: {current_url[:100]}")
                    except:
                        pass
                
                if download_info['triggered']:
                    print(f"   ✅ 确认：Chrome会触发下载")
                else:
                    # 检查最终页面状态
                    try:
                        result = tab.Runtime.evaluate(expression="""
                            (function() {
                                return {
                                    url: window.location.href,
                                    title: document.title,
                                    bodyText: document.body ? document.body.innerText.substring(0, 200) : 'No body',
                                    hasIframe: document.querySelectorAll('iframe').length > 0
                                };
                            })();
                        """, returnByValue=True)
                        page_info = result.get("result", {}).get("value", {})
                        print(f"   最终页面URL: {page_info.get('url', 'N/A')[:100]}")
                        print(f"   页面标题: {page_info.get('title', 'N/A')}")
                        print(f"   页面内容预览: {page_info.get('bodyText', 'N/A')[:100]}")
                        if page_info.get('hasIframe'):
                            print(f"   ⚠️  页面包含iframe，可能需要JavaScript触发下载")
                    except Exception as e:
                        print(f"   ⚠️  无法获取页面信息: {e}")
                
                # 清理资源，避免后台线程JSON解析错误
                try:
                    # 移除事件监听器
                    tab.Page.downloadWillBegin = None
                except:
                    pass
                # 等待接收循环处理完
                time.sleep(0.1)
                # 停止tab
                tab.stop()
                browser.close_tab(tab)
                print(f"   ✅ Chrome测试完成")
            except Exception as e:
                print(f"   ⚠️  Chrome访问失败: {e}")
                print(f"   💡 提示: 请确保Chrome已启动并开启远程调试端口9222")
                import traceback
                traceback.print_exc()
        else:
            print(f"\n📋 步骤5: 跳过Chrome测试（未安装pychrome）")
        
        print(f"\n{'='*60}\n")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(
        description="开心电玩游戏下载工具 - 根据CSV文件下载游戏",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基本用法（推荐使用Chrome模式）
  python3 kxdw_downloader.py games_50_pages.csv --chrome
  
  # 指定Chrome端口
  python3 kxdw_downloader.py games_50_pages.csv --chrome -p 9222
  
  # 其他参数
  python3 kxdw_downloader.py games_50_pages.csv --chrome --start 10 --limit 5
  
  # 测试下载链接
  python3 kxdw_downloader.py --test-url "https://api.kxdw.com/adown/154551/"
  
  # 使用代理（从文件）
  python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt
  
  # 使用单个代理
  python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:7890
        """
    )
    
    parser.add_argument("csv_file", nargs="?", help="CSV文件路径")
    parser.add_argument("-d", "--dir", default="./downloads", help="下载保存目录（默认: ./downloads）")
    parser.add_argument("--start", type=int, default=0, help="起始行号（从0开始，默认0）")
    parser.add_argument("--limit", type=int, help="处理数量限制（默认处理全部）")
    parser.add_argument("--chrome", action="store_true", help="使用Chrome DevTools Protocol（避免验证码）")
    parser.add_argument("-p", "--port", default="9222", help="Chrome调试端口（默认9222）")
    parser.add_argument("--test-url", help="测试下载链接，查看重定向和响应信息")
    parser.add_argument("--proxy-file", help="代理文件路径（每行一个代理地址）")
    parser.add_argument("--proxy", help="单个代理地址（如: http://127.0.0.1:7890）")
    
    args = parser.parse_args()
    
    # 如果指定了--test-url，直接测试链接
    if args.test_url:
        test_download_url(args.test_url)
        return 0
    
    if not args.csv_file:
        parser.error("需要提供CSV文件路径，或使用 --test-url 测试链接")
    
    try:
        downloader = KXDWDownloader(
            args.csv_file,
            args.dir,
            use_chrome=args.chrome,
            chrome_debug_url=f"http://127.0.0.1:{args.port}",
            proxy_file=args.proxy_file,
            proxy=args.proxy
        )
        downloader.run(start_index=args.start, limit=args.limit)
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

