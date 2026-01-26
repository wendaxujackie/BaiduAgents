#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量下载工具
从CSV文件读取游戏列表，使用百度建议词创建文件夹，下载文件并更新CSV

用法:
    python3 batch_downloader.py games_list_all.csv
    python3 batch_downloader.py games_list_all.csv --start 10  # 从第10行开始
    python3 batch_downloader.py games_list_all.csv --limit 5   # 只处理5个
"""

import csv
import os
import re
import time
import argparse
import subprocess
import platform
import signal
import atexit
from pathlib import Path
from urllib.parse import urlparse, unquote
import requests
from typing import Optional

# 导入百度建议词功能
try:
    from baidu_suggestion import get_baidu_suggestions
except ImportError:
    print("❌ 无法导入 baidu_suggestion，请确保 baidu_suggestion.py 在同一目录")
    exit(1)

# 导入Chrome DevTools Protocol支持
try:
    import pychrome
except ImportError:
    pychrome = None


class BatchDownloader:
    """批量下载工具"""
    
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
        self.chrome_process = None  # 存储自动启动的Chrome进程
        self.chrome_user_data_dir = Path.home() / "chrome-debug-profile"
        
        # 代理相关
        self.proxies = []
        self.current_proxy_index = 0
        self._load_proxies(proxy_file, proxy)
        
        if self.use_chrome:
            self._connect_chrome()
        
        # 读取CSV数据
        self.games = []
        self._load_csv()
    
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
    
    def _get_next_proxy(self) -> Optional[str]:
        """获取下一个代理（轮换）"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    def _format_proxy_for_requests(self, proxy: str) -> dict:
        """格式化代理为requests格式"""
        if not proxy:
            return {}
        
        # 支持格式: http://user:pass@host:port 或 http://host:port
        if '://' not in proxy:
            proxy = f"http://{proxy}"
        
        return {
            'http': proxy,
            'https': proxy
        }
    
    def _find_chrome_executable(self) -> Optional[str]:
        """查找Chrome可执行文件路径"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        elif system == "Windows":
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
            ]
        else:  # Linux
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
            ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _start_chrome(self) -> bool:
        """自动启动Chrome调试模式"""
        chrome_path = self._find_chrome_executable()
        if not chrome_path:
            print("❌ 未找到Chrome可执行文件")
            return False
        
        # 创建用户数据目录
        self.chrome_user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # 解析端口
        port = 9222
        if ":" in self.chrome_debug_url:
            try:
                port = int(self.chrome_debug_url.split(":")[-1])
            except:
                pass
        
        # 构建启动命令
        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={self.chrome_user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
        
        # 如果有代理，添加代理参数
        if self.proxies:
            proxy = self._get_next_proxy()
            # 提取代理地址（去掉协议前缀）
            proxy_url = proxy.replace("http://", "").replace("https://", "").replace("socks5://", "")
            cmd.append(f"--proxy-server={proxy_url}")
        
        try:
            print(f"🚀 正在自动启动Chrome调试模式...")
            print(f"   路径: {chrome_path}")
            print(f"   端口: {port}")
            print(f"   数据目录: {self.chrome_user_data_dir}")
            
            # 启动Chrome（后台运行）
            if platform.system() == "Windows":
                # Windows需要特殊处理
                self.chrome_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                self.chrome_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                )
            
            # 等待Chrome启动
            print(f"   ⏳ 等待Chrome启动（最多10秒）...")
            for i in range(20):  # 最多等待10秒
                time.sleep(0.5)
                try:
                    # 尝试连接
                    test_browser = pychrome.Browser(url=self.chrome_debug_url)
                    test_browser.close()
                    print(f"   ✅ Chrome已成功启动！")
                    return True
                except:
                    continue
            
            print(f"   ⚠️  Chrome启动超时，但可能仍在启动中...")
            return True  # 即使超时也返回True，让后续连接尝试
            
        except Exception as e:
            print(f"   ❌ 启动Chrome失败: {e}")
            return False
    
    def _stop_chrome(self):
        """停止自动启动的Chrome进程"""
        if self.chrome_process:
            try:
                if platform.system() == "Windows":
                    self.chrome_process.terminate()
                else:
                    os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGTERM)
                self.chrome_process.wait(timeout=5)
                print("✅ 已关闭自动启动的Chrome进程")
            except:
                try:
                    if platform.system() == "Windows":
                        self.chrome_process.kill()
                    else:
                        os.killpg(os.getpgid(self.chrome_process.pid), signal.SIGKILL)
                except:
                    pass
            finally:
                self.chrome_process = None
    
    def _connect_chrome(self):
        """连接到Chrome调试端口，如果连接失败则自动启动Chrome"""
        if not pychrome:
            print("⚠️  pychrome未安装，将使用requests方式")
            self.use_chrome = False
            return False
        
        # 首先尝试连接
        try:
            self.browser = pychrome.Browser(url=self.chrome_debug_url)
            print(f"✅ 已连接到 Chrome: {self.chrome_debug_url}")
            
            # 如果有代理，设置Chrome代理
            if self.proxies:
                proxy = self._get_next_proxy()
                print(f"🌐 使用代理: {proxy}")
                print("   提示: Chrome代理需要在启动时设置，如果连接失败，脚本会自动启动带代理的Chrome")
            
            # 注册退出时清理
            atexit.register(self._stop_chrome)
            return True
        except Exception as e:
            print(f"⚠️  无法连接到 Chrome 调试端口: {self.chrome_debug_url}")
            print(f"   尝试自动启动Chrome...")
            
            # 自动启动Chrome
            if self._start_chrome():
                # 等待一下让Chrome完全启动
                time.sleep(2)
                
                # 再次尝试连接
                try:
                    self.browser = pychrome.Browser(url=self.chrome_debug_url)
                    print(f"✅ 已连接到自动启动的 Chrome: {self.chrome_debug_url}")
                    
                    # 注册退出时清理
                    atexit.register(self._stop_chrome)
                    return True
                except Exception as e2:
                    print(f"❌ 自动启动Chrome后仍无法连接: {e2}")
                    print(f"   将使用requests方式（可能被拦截）")
                    self.use_chrome = False
                    return False
            else:
                print(f"❌ 自动启动Chrome失败")
                print(f"   将使用requests方式（可能被拦截）")
                print(f"\n💡 如果希望手动启动Chrome，可以使用以下命令:")
                print(f"   Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222 --user-data-dir=~/chrome-debug-profile")
                print(f"   Windows: chrome.exe --remote-debugging-port=9222 --user-data-dir=%USERPROFILE%\\chrome-debug-profile")
                print(f"   Linux: google-chrome --remote-debugging-port=9222 --user-data-dir=~/chrome-debug-profile")
                self.use_chrome = False
                return False
    
    def _get_chrome_tab(self):
        """获取或创建Chrome标签页"""
        if not self.use_chrome or not self.browser:
            return None
        
        try:
            # 如果已有标签页且已启动，直接返回
            if self.tab:
                try:
                    # 检查标签页是否仍然有效
                    self.tab.Runtime.evaluate(expression="1")
                    return self.tab
                except:
                    # 标签页已失效，重新创建
                    self.tab = None
            
            # 获取或创建标签页
            tabs = self.browser.list_tab()
            if tabs:
                self.tab = tabs[0]
            else:
                self.tab = self.browser.new_tab()
            
            # 启动并启用必要的域
            self.tab.start()
            self.tab.Network.enable()
            self.tab.Page.enable()
            self.tab.Runtime.enable()
            
            return self.tab
        except Exception as e:
            error_msg = str(e)
            if "HTTPConnectionPool" in error_msg or "Connection refused" in error_msg or "无法连接" in error_msg:
                print(f"\n{'='*60}")
                print(f"❌ 获取Chrome标签页失败: Chrome调试端口未启动")
                print(f"{'='*60}")
                print(f"\n错误详情: {e}")
                print(f"\n💡 请先启动Chrome调试模式（必须指定独立的数据目录）:")
                print(f"   Mac:")
                print(f"     mkdir -p ~/chrome-debug-profile")
                print(f"     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
                print(f"       --remote-debugging-port=9222 \\")
                print(f"       --user-data-dir=~/chrome-debug-profile")
                print(f"   Windows:")
                print(f"     mkdir %USERPROFILE%\\chrome-debug-profile")
                print(f"     chrome.exe --remote-debugging-port=9222 --user-data-dir=%USERPROFILE%\\chrome-debug-profile")
                print(f"   Linux:")
                print(f"     mkdir -p ~/chrome-debug-profile")
                print(f"     google-chrome --remote-debugging-port=9222 --user-data-dir=~/chrome-debug-profile")
                print(f"\n⚠️  如果Chrome已在运行，请先关闭所有Chrome窗口再启动")
                print(f"{'='*60}\n")
            else:
                print(f"⚠️  获取Chrome标签页失败: {e}")
            return None
    
    def _load_csv(self):
        """加载CSV文件"""
        if not self.csv_file.exists():
            raise FileNotFoundError(f"CSV文件不存在: {self.csv_file}")
        
        with open(self.csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.games.append(row)
        
        print(f"✅ 已加载 {len(self.games)} 个游戏")
    
    def _save_csv(self):
        """保存CSV文件"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            if not self.games:
                return
            
            fieldnames = ['游戏名称', '游戏大小(MB)', '网址链接', '是否已下载']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.games)
    
    def _get_folder_name(self, game_name: str) -> str:
        """使用百度建议词获取文件夹名"""
        try:
            suggestions = get_baidu_suggestions(game_name)
            if suggestions:
                folder_name = suggestions[0]
                # 清理文件夹名（移除非法字符）
                folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
                return folder_name
            else:
                # 如果没有建议词，使用游戏名称
                folder_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)
                return folder_name
        except Exception as e:
            print(f"⚠️  获取建议词失败: {e}，使用游戏名称")
            folder_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)
            return folder_name
    
    def _simulate_human_operation(self, page_url: str) -> Optional[str]:
        """使用Chrome模拟真实的人类操作来获取下载链接"""
        import random
        
        tab = self._get_chrome_tab()
        if not tab:
            return None
        
        try:
            print(f"   使用Chrome模拟人类操作...")
            
            # 1. 导航到页面
            print(f"   📍 访问页面...")
            tab.Page.navigate(url=page_url)
            
            # 2. 等待页面加载（模拟网络延迟）
            wait_time = random.uniform(2, 4)
            print(f"   ⏳ 等待页面加载 ({wait_time:.1f}秒)...")
            time.sleep(wait_time)
            
            # 3. 等待页面完全加载
            try:
                tab.Page.loadEventFired()
                time.sleep(1)
            except:
                pass
            
            # 4. 模拟滚动页面（人类会滚动查看内容）
            print(f"   📜 模拟滚动页面...")
            scroll_js = """
            (function() {
                window.scrollTo(0, document.body.scrollHeight / 3);
                return true;
            })();
            """
            tab.Runtime.evaluate(expression=scroll_js)
            time.sleep(random.uniform(0.5, 1.5))
            
            scroll_js2 = """
            (function() {
                window.scrollTo(0, document.body.scrollHeight / 2);
                return true;
            })();
            """
            tab.Runtime.evaluate(expression=scroll_js2)
            time.sleep(random.uniform(0.5, 1.5))
            
            # 5. 滚动回顶部（找到下载按钮）
            scroll_js3 = """
            (function() {
                window.scrollTo({top: 0, behavior: 'smooth'});
                return true;
            })();
            """
            tab.Runtime.evaluate(expression=scroll_js3)
            time.sleep(random.uniform(1, 2))
            
            # 6. 查找下载按钮并点击
            print(f"   🔍 查找下载按钮...")
            find_and_click_js = """
            (function() {
                // 查找各种可能的下载按钮
                const selectors = [
                    'a[href*="api.ddooo.com/down/"]',
                    'a:contains("下载")',
                    'a:contains("立即下载")',
                    'a:contains("高速下载")',
                    '.download-btn',
                    '.btn-download',
                    '[class*="download"]',
                    'a[onclick*="download"]'
                ];
                
                for (let selector of selectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (let el of elements) {
                            const text = el.textContent || el.innerText || '';
                            const href = el.href || '';
                            if (href.includes('api.ddooo.com/down/') || 
                                text.includes('下载') || 
                                text.includes('Download')) {
                                // 模拟鼠标移动到元素上
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                return href || el.getAttribute('onclick') || '';
                            }
                        }
                    } catch(e) {}
                }
                
                // 如果没找到，尝试查找所有链接
                const allLinks = document.querySelectorAll('a[href]');
                for (let link of allLinks) {
                    const href = link.href || '';
                    if (href.includes('api.ddooo.com/down/')) {
                        link.scrollIntoView({behavior: 'smooth', block: 'center'});
                        return href;
                    }
                }
                
                return null;
            })();
            """
            
            result = tab.Runtime.evaluate(expression=find_and_click_js, returnByValue=True)
            found_url = result.get("result", {}).get("value")
            
            if found_url and 'api.ddooo.com/down/' in found_url:
                print(f"   ✅ 找到下载链接")
                if not found_url.startswith('http'):
                    found_url = 'https://' + found_url
                return found_url
            
            # 7. 如果没找到，尝试点击下载按钮触发下载
            print(f"   🖱️  尝试点击下载按钮...")
            click_download_js = """
            (function() {
                const buttons = document.querySelectorAll('a, button, [onclick]');
                for (let btn of buttons) {
                    const text = (btn.textContent || btn.innerText || '').toLowerCase();
                    const href = btn.href || '';
                    const onclick = btn.getAttribute('onclick') || '';
                    
                    if (text.includes('安卓版下载') || 
                        text.includes('download') ||
                        href.includes('api.ddooo.com/down/') ||
                        onclick.includes('download')) {
                        btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        // 模拟鼠标悬停
                        const event = new MouseEvent('mouseover', {bubbles: true});
                        btn.dispatchEvent(event);
                        return true;
                    }
                }
                return false;
            })();
            """
            
            tab.Runtime.evaluate(expression=click_download_js)
            time.sleep(random.uniform(1, 2))
            
            # 8. 尝试点击下载按钮
            print(f"   🖱️  尝试点击下载按钮...")
            click_js = """
            (function() {
                // 查找所有可能的下载链接
                const selectors = [
                    'a[href*="api.ddooo.com/down/"]',
                    'a[href*="/down/"]',
                    'a:contains("安卓版下载")',
                    'a:contains("立即下载")',
                    'button:contains("下载")'
                ];
                
                for (let selector of selectors) {
                    try {
                        const elements = document.querySelectorAll(selector);
                        for (let el of elements) {
                            const href = el.href || el.getAttribute('href') || '';
                            const text = (el.textContent || el.innerText || '').toLowerCase();
                            if (href.includes('api.ddooo.com/down/') || 
                                (text.includes('下载') && href)) {
                                el.scrollIntoView({behavior: 'smooth', block: 'center'});
                                // 模拟鼠标事件
                                const mouseOver = new MouseEvent('mouseover', {bubbles: true, cancelable: true});
                                el.dispatchEvent(mouseOver);
                                return href;
                            }
                        }
                    } catch(e) {}
                }
                
                // 查找所有链接
                const allLinks = document.querySelectorAll('a[href]');
                for (let link of allLinks) {
                    const href = link.href || '';
                    if (href.includes('api.ddooo.com/down/')) {
                        link.scrollIntoView({behavior: 'smooth', block: 'center'});
                        return href;
                    }
                }
                
                return null;
            })();
            """
            
            result = tab.Runtime.evaluate(expression=click_js, returnByValue=True)
            clicked_url = result.get("result", {}).get("value")
            
            if clicked_url and 'api.ddooo.com/down/' in clicked_url:
                if not clicked_url.startswith('http'):
                    clicked_url = 'https://' + clicked_url
                return clicked_url
            
            time.sleep(random.uniform(1, 2))
            
            # 10. 最后尝试从页面HTML中提取
            print(f"   📄 从页面提取下载链接...")
            html_result = tab.Runtime.evaluate(expression="document.documentElement.outerHTML")
            html = html_result.get("result", {}).get("value", "")
            
            patterns = [
                r'https?://api\.ddooo\.com/down/\d+',
                r'api\.ddooo\.com/down/\d+',
                r'href=["\']([^"\']*api\.ddooo\.com/down/\d+[^"\']*)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    url = matches[0] if isinstance(matches[0], str) else matches[0]
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
            
            return None
            
        except Exception as e:
            print(f"   ❌ 模拟操作出错: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_size_to_mb(self, size_str: str) -> float:
        """将大小字符串转换为MB数值"""
        if not size_str:
            return 0.0
        
        size_str = size_str.strip().upper().replace('MB', '').replace('M', '')
        
        # 提取数字
        match = re.match(r'(\d+\.?\d*)', size_str)
        if match:
            value = float(match.group(1))
            # 如果原始字符串包含G，转换为MB
            if 'G' in size_str.upper():
                value = value * 1024
            return value
        
        return 0.0
    
    def _get_download_url(self, page_url: str) -> Optional[str]:
        """从页面URL获取真实下载链接"""
        # 优先使用Chrome模拟人类操作（避免验证码）
        if self.use_chrome:
            try:
                print(f"   🌐 使用Chrome模式模拟人类操作...")
                download_url = self._simulate_human_operation(page_url)
                if download_url:
                    print(f"   ✅ Chrome模式成功获取下载链接")
                    return download_url
                else:
                    print(f"   ⚠️  Chrome模式未找到下载链接，尝试备用方法...")
            except Exception as e:
                print(f"   ⚠️  Chrome模拟操作失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 如果Chrome模式失败或未启用，尝试从URL推断下载链接
        # 例如: https://www.ddooo.com/softdown/237605.htm -> https://api.ddooo.com/down/237605
        match = re.search(r'/softdown/(\d+)\.htm', page_url)
        game_id = None
        if match:
            game_id = match.group(1)
            # 尝试构造下载链接
            download_url = f"https://api.ddooo.com/down/{game_id}"
            # 验证链接是否有效（发送HEAD请求）
            try:
                print(f"   🔍 尝试直接推断下载链接...")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Referer': 'https://www.ddooo.com/'
                }
                proxies = self._format_proxy_for_requests(self._get_next_proxy()) if self.proxies else {}
                response = requests.head(download_url, headers=headers, proxies=proxies, timeout=10, allow_redirects=True)
                if response.status_code == 200:
                    print(f"   ✅ 直接推断成功")
                    return download_url
            except Exception as e:
                print(f"   ⚠️  直接推断失败: {e}")
        
        # 如果Chrome失败或未启用，使用requests方式
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.ddooo.com/'
            }
            
            proxies = self._format_proxy_for_requests(self._get_next_proxy()) if self.proxies else {}
            if proxies:
                print(f"   使用代理访问: {list(proxies.values())[0]}")
            
            response = requests.get(page_url, headers=headers, proxies=proxies, timeout=30)
            response.raise_for_status()
            
            # 查找下载链接
            patterns = [
                r'https?://api\.ddooo\.com/down/\d+',
                r'api\.ddooo\.com/down/\d+',
                r'href=["\']([^"\']*api\.ddooo\.com/down/\d+[^"\']*)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    url = matches[0] if isinstance(matches[0], str) else matches[0]
                    if not url.startswith('http'):
                        url = 'https://' + url
                    return url
        except Exception as e:
            print(f"⚠️  从页面提取下载链接失败: {e}")
        
        # 如果还是没找到，返回推断的链接（即使验证失败也尝试）
        if game_id:
            return f"https://api.ddooo.com/down/{game_id}"
        
        return None
    
    def _download_file(self, download_url: str, save_path: Path) -> bool:
        """下载文件"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.ddooo.com/'
            }
            
            proxies = self._format_proxy_for_requests(self._get_next_proxy()) if self.proxies else {}
            if proxies:
                print(f"   使用代理下载: {list(proxies.values())[0]}")
            
            response = requests.get(download_url, headers=headers, proxies=proxies, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(save_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size:
                            percent = (downloaded / total_size) * 100
                            print(f"\r   下载进度: {percent:.1f}%", end="", flush=True)
            
            print(f"\n✅ 下载完成: {save_path.name}")
            return True
            
        except Exception as e:
            print(f"\n❌ 下载失败: {e}")
            return False
    
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
        size_str = game.get('游戏大小(MB)', '')
        page_url = game.get('网址链接', '')
        downloaded = game.get('是否已下载', '否')
        
        # 如果已下载，跳过
        if downloaded == '是':
            return True
        
        print(f"\n{'='*60}")
        print(f"[{index}/{len(self.games)}] 处理: {game_name}")
        print(f"{'='*60}")
        
        # 检查文件大小（超过1G跳过）
        size_mb = self._parse_size_to_mb(size_str)
        if size_mb > 1024:
            print(f"⏭️  文件大小 {size_mb:.2f}MB ({size_mb/1024:.2f}G) 超过1G，跳过")
            return False
        
        # 获取文件夹名
        print(f"🔍 获取文件夹名...")
        folder_name = self._get_folder_name(game_name)
        print(f"📁 文件夹名: {folder_name}")
        
        # 创建文件夹
        folder_path = self.download_base_dir / folder_name
        folder_path.mkdir(parents=True, exist_ok=True)
        
        # 获取下载链接
        print(f"🔗 获取下载链接...")
        download_url = self._get_download_url(page_url)
        
        if not download_url:
            print(f"❌ 无法获取下载链接，跳过")
            return False
        
        print(f"📥 下载链接: {download_url[:80]}...")
        
        # 确定文件名（从URL提取或使用建议词名）
        file_ext = os.path.splitext(urlparse(download_url).path)[1]
        if not file_ext:
            # 根据URL判断
            if 'apk' in download_url.lower():
                file_ext = '.apk'
            elif 'exe' in download_url.lower():
                file_ext = '.exe'
            else:
                file_ext = '.apk'  # 默认
        
        file_name = f"{folder_name}{file_ext}"
        save_path = folder_path / file_name
        
        # 如果文件已存在，跳过
        if save_path.exists():
            print(f"⏭️  文件已存在，跳过下载")
        else:
            # 下载文件
            print(f"⬇️  开始下载: {file_name}")
            if not self._download_file(download_url, save_path):
                return False
        
        # 创建信息文件
        print(f"📝 创建信息文件...")
        self._create_info_files(folder_path)
        
        # 更新CSV
        game['是否已下载'] = '是'
        self._save_csv()
        
        print(f"✅ 完成!")
        return True
    
    def run(self, start_index: int = 0, limit: Optional[int] = None):
        """运行批量下载"""
        print(f"\n{'='*60}")
        print(f"🚀 开始批量下载")
        print(f"{'='*60}")
        
        # 检查Chrome模式
        if not self.use_chrome:
            print(f"⚠️  警告: 未启用Chrome模式！")
            print(f"   建议使用 --chrome 参数来模拟人类操作，避免被拦截")
            print(f"   当前将使用requests方式，可能被网站拦截")
            print(f"{'='*60}\n")
        else:
            print(f"✅ Chrome模式已启用 - 将模拟人类操作")
            if self.proxies:
                print(f"✅ 代理已配置 - 共 {len(self.proxies)} 个代理")
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
                
                # 避免请求过快（使用Chrome时可以稍短一些）
                wait_time = 3 if self.use_chrome else 2
                time.sleep(wait_time)
                
            except KeyboardInterrupt:
                print(f"\n\n⚠️  用户中断")
                break
            except Exception as e:
                print(f"\n❌ 处理失败: {e}")
                fail_count += 1
                continue
        
        # 清理Chrome资源
        if self.tab:
            try:
                self.tab.stop()
                if self.browser:
                    self.browser.close_tab(self.tab)
            except:
                pass
        
        # 清理自动启动的Chrome进程（如果存在）
        # 注意：如果用户希望保留Chrome窗口，可以注释掉下面这行
        # self._stop_chrome()
        
        print(f"\n{'='*60}")
        print(f"📊 处理完成统计")
        print(f"{'='*60}")
        print(f"成功: {success_count}")
        print(f"跳过: {skip_count}")
        print(f"失败: {fail_count}")
        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="批量下载工具 - 从CSV读取游戏列表并下载（必须使用Chrome模式模拟人类操作）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
⚠️  重要提示：必须使用 --chrome 参数！脚本会模拟真实的人类操作来避免被拦截。

示例:
  # 基本用法（必须使用Chrome模式）
  python3 batch_downloader.py games_list_all.csv --chrome
  
  # 指定Chrome端口
  python3 batch_downloader.py games_list_all.csv --chrome -p 9222
  
  # 使用代理（推荐，进一步降低被拦截风险）
  python3 batch_downloader.py games_list_all.csv --chrome --proxy-file proxies.txt
  
  # 其他参数
  python3 batch_downloader.py games_list_all.csv --chrome --start 10 --limit 5

✨ Chrome模式会自动启动（无需手动启动）:
  - 脚本会自动检测Chrome是否已运行
  - 如果未运行，会自动启动Chrome调试模式
  - 数据目录: ~/chrome-debug-profile（自动创建）
  - 如果自动启动失败，可以手动启动（见下方命令）

手动启动Chrome（仅在自动启动失败时使用）:
  Mac:
    /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\
      --remote-debugging-port=9222 \\
      --user-data-dir=~/chrome-debug-profile
  
  Windows:
    chrome.exe --remote-debugging-port=9222 --user-data-dir=%USERPROFILE%\\chrome-debug-profile
  
  Linux:
    google-chrome --remote-debugging-port=9222 --user-data-dir=~/chrome-debug-profile

Chrome模式会模拟以下人类操作：
  - 访问页面并等待加载
  - 模拟滚动页面
  - 查找并点击下载按钮
  - 等待下载链接出现
  - 获取真实的下载地址

代理文件格式（proxies.txt）:
  http://127.0.0.1:7890
  http://user:pass@proxy.example.com:8080
  socks5://127.0.0.1:1080
        """
    )
    
    parser.add_argument("csv_file", help="CSV文件路径")
    parser.add_argument("-d", "--dir", default="./downloads", help="下载保存目录（默认: ./downloads）")
    parser.add_argument("--start", type=int, default=0, help="起始行号（从0开始，默认0）")
    parser.add_argument("--limit", type=int, help="处理数量限制（默认处理全部）")
    parser.add_argument("--chrome", action="store_true", help="使用Chrome DevTools Protocol（避免验证码）")
    parser.add_argument("-p", "--port", default="9222", help="Chrome调试端口（默认9222）")
    parser.add_argument("--proxy", help="单个代理地址（格式: http://user:pass@host:port 或 http://host:port）")
    parser.add_argument("--proxy-file", help="代理列表文件路径（每行一个代理地址）")
    
    args = parser.parse_args()
    
    try:
        downloader = BatchDownloader(
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
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())

