#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页自动下载工具 - 基于 Chrome DevTools Protocol (CDP)
直接使用 Chrome 调试协议控制浏览器，解析网页并自动下载文件

使用前准备:
    1. 安装依赖: pip3 install pychrome requests websocket-client
    2. 启动 Chrome (开启调试端口):
       Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
       Windows: chrome.exe --remote-debugging-port=9222
       
用法:
    python3 auto_downloader.py <网页URL>
    python3 auto_downloader.py https://www.ddooo.com/softdown/12345.html
    python3 auto_downloader.py -a https://www.ddooo.com/  # 仅分析页面
"""

import argparse
import json
import os
import re
import time
import base64
import subprocess
import platform
import csv
from pathlib import Path
from urllib.parse import urlparse, unquote, urljoin

try:
    import pychrome
except ImportError:
    pychrome = None

try:
    import requests
except ImportError:
    requests = None


class CDPDownloader:
    """基于 Chrome DevTools Protocol 的网页下载工具"""
    
    def __init__(self, debug_url: str = "http://127.0.0.1:9222", download_dir: str = "./downloads"):
        self.debug_url = debug_url
        self.download_dir = Path(download_dir).absolute()
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.browser = None
        self.tab = None
        self.downloaded_files = []
        self.download_urls = []  # 收集到的下载链接
        
    def connect(self) -> bool:
        """连接到 Chrome 调试端口"""
        if not pychrome:
            print("❌ 请先安装 pychrome: pip3 install pychrome")
            return False
            
        try:
            self.browser = pychrome.Browser(url=self.debug_url)
            print(f"✅ 已连接到 Chrome: {self.debug_url}")
            return True
        except Exception as e:
            print(f"❌ 无法连接到 Chrome 调试端口: {e}")
            print("\n请先启动 Chrome 并开启调试端口:")
            self._print_chrome_launch_command()
            return False
    
    def _print_chrome_launch_command(self):
        """打印启动 Chrome 的命令"""
        system = platform.system()
        if system == "Darwin":  # macOS
            print('   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222')
        elif system == "Windows":
            print('   chrome.exe --remote-debugging-port=9222')
        else:  # Linux
            print('   google-chrome --remote-debugging-port=9222')
    
    def new_tab(self, url: str = None):
        """创建或获取标签页"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # 尝试获取现有标签页，如果没有则创建新的
                tabs = self.browser.list_tab()
                if tabs:
                    self.tab = tabs[0]
                    print(f"📑 使用现有标签页")
                else:
                    self.tab = self.browser.new_tab()
                    print(f"📑 创建新标签页")
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"⏳ 重试连接... ({attempt + 1}/{max_retries})")
                    time.sleep(2)
                else:
                    raise e
        
        # 启用必要的域
        self.tab.start()
        self.tab.Network.enable()
        self.tab.Page.enable()
        self.tab.DOM.enable()
        self.tab.Runtime.enable()
        
        # 设置下载行为
        try:
            self.tab.Page.setDownloadBehavior(
                behavior="allow",
                downloadPath=str(self.download_dir)
            )
        except Exception as e:
            print(f"⚠️  设置下载行为失败: {e}")
        
        # 监听网络请求
        self.tab.Network.responseReceived = self._on_response_received
        self.tab.Network.requestWillBeSent = self._on_request_will_be_sent
        self.tab.Page.downloadWillBegin = self._on_download_will_begin
        self.tab.Page.downloadProgress = self._on_download_progress
        
        if url:
            self.navigate(url)
    
    def _on_request_will_be_sent(self, **kwargs):
        """监听请求发送事件"""
        request = kwargs.get("request", {})
        url = request.get("url", "")
        
        # 检测下载链接
        if self._is_download_url(url):
            self.download_urls.append(url)
    
    def _on_response_received(self, **kwargs):
        """监听响应接收事件"""
        response = kwargs.get("response", {})
        url = response.get("url", "")
        headers = response.get("headers", {})
        
        # 检查 Content-Disposition 头（表明是下载）
        content_disposition = headers.get("Content-Disposition", "")
        if "attachment" in content_disposition.lower():
            print(f"📥 检测到下载: {url}")
            self.download_urls.append(url)
    
    def _on_download_will_begin(self, **kwargs):
        """下载开始事件"""
        url = kwargs.get("url", "")
        suggested_filename = kwargs.get("suggestedFilename", "")
        print(f"⬇️  开始下载: {suggested_filename}")
        print(f"   URL: {url[:80]}...")
    
    def _on_download_progress(self, **kwargs):
        """下载进度事件"""
        state = kwargs.get("state", "")
        guid = kwargs.get("guid", "")
        
        if state == "completed":
            print(f"✅ 下载完成!")
            self.downloaded_files.append(guid)
        elif state == "canceled":
            print(f"❌ 下载取消")
    
    def _is_download_url(self, url: str) -> bool:
        """判断是否为下载链接"""
        url_lower = url.lower()
        
        # 排除的URL模式（统计、广告等）
        exclude_patterns = [
            r'cnzz\.com', r'baidu\.com/s\?', r'stat\.', r'analytics',
            r'google-analytics', r'\.js$', r'\.css$', r'\.png$', r'\.jpg$',
            r'\.gif$', r'qrcode', r'favicon'
        ]
        if any(re.search(p, url_lower) for p in exclude_patterns):
            return False
        
        # 真实下载链接模式
        download_patterns = [
            r'\.exe$', r'\.zip$', r'\.rar$', r'\.7z$',
            r'\.dmg$', r'\.pkg$', r'\.apk$', r'\.msi$',
            r'\.tar\.gz$', r'\.deb$', r'\.rpm$',
            r'api\.ddooo\.com/down/',  # 多多软件站的真实下载链接
            r'/down/\d+',  # 通用下载链接格式
            r'downfile',
        ]
        return any(re.search(p, url_lower) for p in download_patterns)
    
    def navigate(self, url: str, wait_time: float = 3.0):
        """导航到指定URL"""
        print(f"🌐 正在访问: {url}")
        self.tab.Page.navigate(url=url)
        
        # 等待页面加载
        time.sleep(wait_time)
        
        # 等待 load 事件
        try:
            self.tab.wait(timeout=10)
        except:
            pass
    
    def get_page_info(self) -> dict:
        """获取页面基本信息"""
        # 获取标题
        title_result = self.tab.Runtime.evaluate(expression="document.title")
        title = title_result.get("result", {}).get("value", "")
        
        # 获取URL
        url_result = self.tab.Runtime.evaluate(expression="window.location.href")
        current_url = url_result.get("result", {}).get("value", "")
        
        return {
            "title": title,
            "url": current_url
        }
    
    def find_download_links(self) -> list:
        """查找页面中的所有下载链接"""
        # JavaScript 代码：查找所有可能的下载链接
        js_code = """
        (function() {
            const links = [];
            const allLinks = document.querySelectorAll('a');
            
            // 排除的链接模式
            const excludePatterns = [
                /cnzz\\.com/i, /baidu\\.com\\/s\\?/i, /stat\\./i, 
                /analytics/i, /\\.js$/i, /\\.css$/i, /qrcode/i
            ];
            
            // 排除的文字（导航链接）
            const excludeTexts = ['MAC下载', '苹果下载', '安卓下载', 'iPhone', 'iPad', '下载帮助'];
            
            allLinks.forEach(link => {
                const href = link.href || '';
                const text = (link.innerText || link.textContent || '').trim();
                const className = link.className || '';
                
                // 排除导航链接和统计链接
                if (excludePatterns.some(p => p.test(href))) return;
                if (excludeTexts.some(t => text === t || text === t + '/')) return;
                
                // 检查是否为真实下载链接
                const isRealDownload = 
                    href.match(/\\.(exe|zip|rar|7z|dmg|pkg|apk|msi)$/i) ||
                    href.match(/api\\.ddooo\\.com\\/down\\//i) ||
                    href.match(/\\/down\\/\\d+/i) ||
                    href.includes('downfile') ||
                    (text.includes('下载') && href.match(/down/i) && !href.match(/softdown\\.htm/i));
                
                if (isRealDownload && href) {
                    links.push({
                        href: href,
                        text: text.substring(0, 50),
                        className: className,
                        priority: href.match(/api\\.ddooo\\.com\\/down\\//i) ? 1 : 
                                  href.match(/\\.(exe|zip|rar|apk)$/i) ? 2 : 3
                    });
                }
            });
            
            // 按优先级排序
            links.sort((a, b) => a.priority - b.priority);
            
            return links;
        })();
        """
        
        result = self.tab.Runtime.evaluate(expression=js_code, returnByValue=True)
        links = result.get("result", {}).get("value", [])
        
        return links
    
    def find_software_info(self) -> dict:
        """提取软件信息（针对软件下载站）"""
        js_code = """
        (function() {
            const info = {};
            
            // 尝试获取软件名称
            const h1 = document.querySelector('h1');
            if (h1) info.name = h1.innerText.trim();
            
            // 尝试获取版本
            const versionEl = document.querySelector('[class*="version"], .ver, .soft-version');
            if (versionEl) info.version = versionEl.innerText.trim();
            
            // 尝试获取文件大小
            const sizeEl = document.querySelector('[class*="size"], .filesize');
            if (sizeEl) info.size = sizeEl.innerText.trim();
            
            // 尝试获取更新时间
            const dateEl = document.querySelector('[class*="date"], [class*="time"], .update-time');
            if (dateEl) info.date = dateEl.innerText.trim();
            
            return info;
        })();
        """
        
        result = self.tab.Runtime.evaluate(expression=js_code, returnByValue=True)
        info = result.get("result", {}).get("value", {})
        
        return info
    
    def click_element(self, selector: str):
        """点击指定元素"""
        js_code = f"""
        (function() {{
            const el = document.querySelector('{selector}');
            if (el) {{
                el.click();
                return true;
            }}
            return false;
        }})();
        """
        
        result = self.tab.Runtime.evaluate(expression=js_code)
        return result.get("result", {}).get("value", False)
    
    def click_first_download_button(self) -> bool:
        """点击第一个下载按钮"""
        # 常见的下载按钮选择器
        selectors = [
            'a[href*="download"]',
            '.download-btn',
            '.down-btn',
            '.downurllist a',
            'a.btn-download',
            'a[class*="download"]',
            'a:contains("下载")',
        ]
        
        # 使用 JavaScript 查找并点击
        js_code = """
        (function() {
            // 查找包含"下载"文字的链接
            const links = document.querySelectorAll('a');
            for (const link of links) {
                const text = link.innerText || '';
                const href = link.href || '';
                if ((text.includes('下载') || text.includes('Download')) && 
                    !text.includes('手机') && !text.includes('安卓')) {
                    link.click();
                    return {success: true, text: text.trim(), href: href};
                }
            }
            
            // 查找下载按钮类
            const downloadBtns = document.querySelectorAll('.download-btn, .down-btn, [class*="download"] a');
            if (downloadBtns.length > 0) {
                downloadBtns[0].click();
                return {success: true, text: downloadBtns[0].innerText, href: downloadBtns[0].href};
            }
            
            return {success: false};
        })();
        """
        
        result = self.tab.Runtime.evaluate(expression=js_code, returnByValue=True)
        click_result = result.get("result", {}).get("value", {})
        
        if click_result.get("success"):
            print(f"🖱️  点击下载按钮: {click_result.get('text', '')}")
            return True
        return False
    
    def download_file(self, url: str, filename: str = None):
        """直接下载文件"""
        if not requests:
            print("❌ 请安装 requests: pip3 install requests")
            return None
        
        if not filename:
            # 从URL提取文件名
            parsed = urlparse(url)
            filename = unquote(os.path.basename(parsed.path))
            if not filename:
                filename = "download_file"
        
        save_path = self.download_dir / filename
        
        print(f"⬇️  下载文件: {filename}")
        print(f"   URL: {url[:80]}...")
        
        try:
            # 获取 cookies
            cookies_result = self.tab.Network.getCookies()
            cookies = {c['name']: c['value'] for c in cookies_result.get('cookies', [])}
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Referer': self.tab.Runtime.evaluate(expression="window.location.href").get("result", {}).get("value", ""),
            }
            
            response = requests.get(url, headers=headers, cookies=cookies, stream=True, timeout=60)
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
                            print(f"\r   进度: {percent:.1f}%", end="", flush=True)
            
            print(f"\n✅ 下载完成: {save_path}")
            self.downloaded_files.append(str(save_path))
            return str(save_path)
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return None
    
    def analyze_page(self, url: str):
        """分析页面结构"""
        if not self.connect():
            return
        
        self.new_tab(url)
        
        print("\n" + "=" * 50)
        print("📊 页面分析结果")
        print("=" * 50)
        
        # 页面信息
        page_info = self.get_page_info()
        print(f"\n📄 标题: {page_info['title']}")
        print(f"🔗 URL: {page_info['url']}")
        
        # 软件信息
        soft_info = self.find_software_info()
        if soft_info:
            print(f"\n📦 软件信息:")
            for key, value in soft_info.items():
                print(f"   {key}: {value}")
        
        # 下载链接
        links = self.find_download_links()
        print(f"\n🔍 找到 {len(links)} 个下载链接:")
        for i, link in enumerate(links[:10], 1):
            print(f"   {i}. [{link['text']}]")
            print(f"      -> {link['href'][:80]}...")
        
        # 网络请求中检测到的下载
        if self.download_urls:
            print(f"\n📡 网络请求中检测到的下载链接:")
            for url in self.download_urls[:5]:
                print(f"   • {url[:80]}...")
        
        self.close()
    
    def auto_download(self, url: str):
        """自动下载"""
        if not self.connect():
            return
        
        self.new_tab(url)
        
        print("\n" + "=" * 50)
        print("🚀 开始自动下载")
        print("=" * 50)
        
        # 获取页面信息
        page_info = self.get_page_info()
        soft_info = self.find_software_info()
        
        print(f"\n📄 页面: {page_info['title']}")
        if soft_info.get('name'):
            print(f"📦 软件: {soft_info['name']}")
        
        # 查找下载链接
        links = self.find_download_links()
        print(f"\n🔍 找到 {len(links)} 个下载链接")
        
        if links:
            # 显示找到的下载链接
            for i, link in enumerate(links[:3], 1):
                print(f"   {i}. [{link['text']}] -> {link['href'][:60]}...")
            
            # 选择第一个下载链接（已按优先级排序）
            best_link = links[0]
            href = best_link['href']
            
            # 生成文件名
            filename = None
            if soft_info.get('name'):
                # 从URL推断扩展名
                ext = os.path.splitext(urlparse(href).path)[1]
                if not ext:
                    # 根据链接文字推断
                    text = best_link.get('text', '').lower()
                    if 'apk' in text or '安卓' in text:
                        ext = '.apk'
                    elif 'exe' in text or 'windows' in text:
                        ext = '.exe'
                    elif 'dmg' in text or 'mac' in text:
                        ext = '.dmg'
                    else:
                        ext = '.apk'  # 默认
                
                safe_name = re.sub(r'[<>:"/\\|?*]', '_', soft_info['name'])
                filename = f"{safe_name}{ext}"
            
            print(f"\n📥 准备下载: {best_link['text']}")
            self.download_file(href, filename)
        else:
            # 没有找到下载链接，尝试点击下载按钮
            print("\n🖱️  尝试点击下载按钮...")
            if self.click_first_download_button():
                time.sleep(3)  # 等待下载开始或页面跳转
                
                # 检查是否有新的下载链接
                if self.download_urls:
                    # 过滤掉统计链接
                    valid_urls = [u for u in self.download_urls if self._is_download_url(u)]
                    if valid_urls:
                        self.download_file(valid_urls[-1])
                    else:
                        print("❌ 未找到有效的下载链接")
            else:
                print("❌ 未找到下载链接")
        
        print(f"\n✅ 完成! 下载目录: {self.download_dir}")
        self.close()
    
    def parse_game_list_from_api(self, key: str = "4_14_1", type_param: int = 3) -> list:
        """通过API接口解析游戏列表，提取游戏名称、大小和链接"""
        if not requests:
            print("❌ 请安装 requests: pip3 install requests")
            return []
        
        print("\n" + "=" * 50)
        print("📋 通过API解析游戏列表")
        print("=" * 50)
        
        api_url = "https://api.ddooo.com/api/sort.html"
        headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Origin': 'https://www.ddooo.com',
            'Referer': 'https://www.ddooo.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15'
        }
        
        all_games = []
        # 从第2页开始（第1页通常无数据）
        page = 2
        start_page = 2
        max_pages = 500  # 防止无限循环，15082个游戏大约需要378页（每页40个）
        
        print(f"🔍 开始获取数据 (key={key}, type={type_param})...")
        
        while page < max_pages:
            params = {
                'p': page,
                'key': key,
                'type': type_param
            }
            
            try:
                response = requests.get(api_url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                
                # 解析JSON（自动处理unicode编码）
                data = response.json()
                
                code = data.get('code')
                msg = data.get('msg', '')
                
                # 如果返回错误或"无数据"
                if code != 200:
                    if msg == '无数据':
                        print(f"✅ 第 {page} 页无数据，已获取全部")
                        break
                    else:
                        print(f"⚠️  第 {page} 页返回错误: {msg}")
                        break
                
                games_data = data.get('data', [])
                
                if not games_data or len(games_data) == 0:
                    print(f"✅ 第 {page} 页无数据，已获取全部")
                    break
                
                # 处理每页的游戏数据
                for game in games_data:
                    game_name = game.get('name', '')
                    game_size = game.get('size', '')
                    game_url = game.get('url', '')
                    
                    # 转换为完整URL
                    if game_url and not game_url.startswith('http'):
                        if game_url.startswith('/'):
                            full_url = f"https://www.ddooo.com{game_url}"
                        else:
                            full_url = f"https://www.ddooo.com/{game_url}"
                    else:
                        full_url = game_url
                    
                    all_games.append({
                        'name': game_name,
                        'size': game_size,
                        'url': full_url,
                        'id': game.get('id', '')
                    })
                
                print(f"📄 第 {page} 页: 获取到 {len(games_data)} 个游戏 (累计: {len(all_games)})")
                page += 1
                
                # 避免请求过快
                time.sleep(0.5)
                
            except requests.RequestException as e:
                print(f"❌ 第 {page} 页请求失败: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"❌ 第 {page} 页JSON解析失败: {e}")
                break
            except Exception as e:
                print(f"❌ 第 {page} 页处理失败: {e}")
                break
        
        print(f"\n✅ 共获取 {len(all_games)} 个游戏")
        
        # 显示前几个游戏作为预览
        if all_games:
            print("\n📋 前5个游戏预览:")
            for i, game in enumerate(all_games[:5], 1):
                print(f"   {i}. {game['name']} - {game['size']}")
        
        return all_games
    
    def parse_game_list(self, url: str = None, key: str = None, type_param: int = 3) -> list:
        """解析游戏列表（兼容旧接口，优先使用API）"""
        # 如果提供了URL，尝试从URL中提取key
        if url and not key:
            # 从URL中提取分类ID和子分类，例如:
            # https://www.ddooo.com/az/14_1_1.htm -> 4_14_1 (安卓单机)
            # https://www.ddooo.com/az/14_2_1.htm -> 4_14_2 (安卓网游)
            match = re.search(r'/az/(\d+)_(\d+)_', url)
            if match:
                category_id = match.group(1)
                sub_category = match.group(2)
                key = f"4_{category_id}_{sub_category}"
                print(f"🔍 从URL提取到 key: {key}")
            else:
                # 尝试只提取第一个数字（兼容旧格式）
                match = re.search(r'/az/(\d+)_', url)
                if match:
                    category_id = match.group(1)
                    key = f"4_{category_id}_1"
                    print(f"🔍 从URL提取到 key: {key}")
                else:
                    # 默认使用安卓单机列表
                    key = "4_14_1"
                    print(f"⚠️  无法从URL提取key，使用默认值: {key}")
        elif not key:
            # 默认使用安卓单机列表
            key = "4_14_1"
        
        # 使用API接口获取数据
        return self.parse_game_list_from_api(key=key, type_param=type_param)
    
    def check_downloaded(self, game_url: str) -> bool:
        """检查游戏是否已下载"""
        if not game_url:
            return False
        
        # 从URL中提取游戏ID
        match = re.search(r'/softdown/(\d+)\.htm', game_url)
        if not match:
            return False
        
        game_id = match.group(1)
        
        # 检查downloads目录中是否有对应的文件
        # 可能的文件名格式：游戏名称.apk, 游戏名称.exe, 或包含游戏ID的文件
        download_dir = Path(self.download_dir)
        if not download_dir.exists():
            return False
        
        # 查找包含游戏ID的文件
        for file_path in download_dir.iterdir():
            if file_path.is_file():
                # 检查文件名中是否包含游戏ID
                if game_id in file_path.name:
                    return True
        
        return False
    
    def export_game_list_to_csv(self, games: list, output_file: str = None):
        """将游戏列表导出为CSV文件，包含是否已下载列"""
        if not games:
            print("❌ 没有游戏数据可导出")
            return
        
        if not output_file:
            # 生成默认文件名
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = self.download_dir / f"game_list_{timestamp}.csv"
        else:
            output_file = Path(output_file)
        
        # 确保输出目录存在
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换大小为MB格式
        def convert_to_mb(size_str: str) -> str:
            """将大小字符串转换为MB格式"""
            if not size_str:
                return ""
            
            # 移除空格和单位，提取数字
            size_str = size_str.strip().upper()
            
            # 匹配数字和单位
            match = re.match(r'(\d+\.?\d*)\s*([MG]B?)?', size_str)
            if not match:
                return size_str
            
            value = float(match.group(1))
            unit = match.group(2) or 'M'
            
            # 转换为MB
            if 'G' in unit:
                value = value * 1024
            
            return f"{value:.2f}MB"
        
        # 检查下载状态
        print("\n🔍 检查下载状态...")
        downloaded_count = 0
        for i, game in enumerate(games, 1):
            if self.check_downloaded(game.get('url', '')):
                game['downloaded'] = '是'
                downloaded_count += 1
            else:
                game['downloaded'] = '否'
            
            if i % 100 == 0:
                print(f"   已检查 {i}/{len(games)} 个游戏...")
        
        print(f"✅ 检查完成: {downloaded_count} 个已下载")
        
        # 写入CSV文件
        try:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow(['游戏名称', '游戏大小(MB)', '网址链接', '是否已下载'])
                
                # 写入数据
                for game in games:
                    size_mb = convert_to_mb(game.get('size', ''))
                    writer.writerow([
                        game.get('name', ''),
                        size_mb,
                        game.get('url', ''),
                        game.get('downloaded', '否')
                    ])
            
            print(f"\n✅ 数据已导出到: {output_file}")
            print(f"   共 {len(games)} 条记录")
            print(f"   已下载: {downloaded_count} 个")
            return str(output_file)
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return None
    
    def close(self):
        """关闭标签页"""
        if self.tab:
            try:
                self.tab.stop()
                self.browser.close_tab(self.tab)
            except:
                pass


def launch_chrome_with_debugging():
    """启动带调试端口的 Chrome"""
    import tempfile
    
    system = platform.system()
    
    if system == "Darwin":  # macOS
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif system == "Windows":
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    else:  # Linux
        chrome_path = "google-chrome"
    
    # 使用临时目录作为用户数据目录（远程调试需要）
    user_data_dir = "/tmp/chrome-debug-profile"
    os.makedirs(user_data_dir, exist_ok=True)
    
    cmd = [
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run"
    ]
    
    print(f"🚀 启动 Chrome...")
    
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("⏳ 等待 Chrome 启动...")
        time.sleep(5)  # 等待 Chrome 启动
        return True
    except Exception as e:
        print(f"❌ 启动 Chrome 失败: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="网页自动下载工具 - 基于 Chrome DevTools Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用前准备:
  1. pip3 install pychrome requests websocket-client
  2. 启动 Chrome (Mac):
     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222

示例:
  python3 auto_downloader.py https://www.ddooo.com/softdown/12345.html
  python3 auto_downloader.py -a https://www.ddooo.com/  # 仅分析页面
  python3 auto_downloader.py -l https://www.ddooo.com/az/14_1_1.htm  # 解析游戏列表（从URL提取key）
  python3 auto_downloader.py -l -k 4_14_1 -o games.csv  # 直接指定key解析游戏列表
  python3 auto_downloader.py -l -o games.csv https://www.ddooo.com/az/14_1_1.htm  # 指定输出文件
  python3 auto_downloader.py -d ./my_downloads https://example.com
  python3 auto_downloader.py --launch https://example.com  # 自动启动Chrome
        """
    )
    
    parser.add_argument("url", nargs='?', help="要解析的网页URL（列表模式下可选）")
    parser.add_argument("-d", "--dir", default="./downloads", help="下载保存目录")
    parser.add_argument("-a", "--analyze", action="store_true", help="仅分析页面，不下载")
    parser.add_argument("-l", "--list", action="store_true", help="解析游戏列表并导出CSV（使用API接口）")
    parser.add_argument("-o", "--output", help="CSV输出文件路径（用于列表模式）")
    parser.add_argument("-k", "--key", help="API key参数（例如：4_14_1，默认从URL提取）")
    parser.add_argument("-t", "--type", type=int, default=3, help="API type参数（默认3）")
    parser.add_argument("-p", "--port", default="9222", help="Chrome 调试端口 (默认 9222)")
    parser.add_argument("--launch", action="store_true", help="自动启动 Chrome")
    
    args = parser.parse_args()
    
    # 列表模式不需要Chrome，只需要requests
    if args.list:
        if not requests:
            print("❌ 请先安装依赖:")
            print("   pip3 install requests")
            return
        
        downloader = CDPDownloader(download_dir=args.dir)
        games = downloader.parse_game_list(url=args.url, key=args.key, type_param=args.type)
        if games:
            downloader.export_game_list_to_csv(games, args.output)
        return
    
    # 其他模式需要pychrome
    if not pychrome:
        print("❌ 请先安装依赖:")
        print("   pip3 install pychrome requests websocket-client")
        return
    
    if not args.url:
        parser.error("URL参数是必需的（列表模式除外）")
    
    # 自动启动 Chrome
    if args.launch:
        launch_chrome_with_debugging()
    
    debug_url = f"http://127.0.0.1:{args.port}"
    downloader = CDPDownloader(debug_url=debug_url, download_dir=args.dir)
    
    if args.analyze:
        downloader.analyze_page(args.url)
    else:
        downloader.auto_download(args.url)


if __name__ == "__main__":
    main()
