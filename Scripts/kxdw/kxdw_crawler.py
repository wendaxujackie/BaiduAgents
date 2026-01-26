#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开心电玩手游数据抓取工具
使用 Chrome DevTools Protocol 抓取手游分类下的手游资料

使用前准备:
    1. 安装依赖: pip3 install pychrome requests websocket-client
    2. 启动 Chrome (开启调试端口):
       Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
       Windows: chrome.exe --remote-debugging-port=9222
       
用法:
    python3 kxdw_crawler.py
    python3 kxdw_crawler.py -o games.csv
    python3 kxdw_crawler.py -p 9222
"""

import argparse
import csv
import re
import time
import platform
from pathlib import Path
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional

try:
    import pychrome
except ImportError:
    pychrome = None

try:
    import requests
except ImportError:
    requests = None


class KXDWCrawler:
    """开心电玩手游数据抓取工具"""
    
    def __init__(self, debug_url: str = "http://127.0.0.1:9222"):
        self.debug_url = debug_url
        self.browser = None
        self.tab = None
        self.base_url = "https://www.kxdw.com"
        self.target_url = "https://www.kxdw.com/android/gf.html"
        self.games = []
        
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
        
        if url:
            self.navigate(url)
    
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
    
    def get_game_list(self, max_pages: int = 100) -> List[Dict]:
        """获取游戏列表"""
        print("\n" + "=" * 60)
        print("📋 获取游戏列表")
        print("=" * 60)
        
        # 滚动页面以加载更多内容
        print("📜 滚动页面加载所有游戏...")
        self._scroll_to_load_all()
        
        # 获取当前页面URL，提取分页模式
        current_url_result = self.tab.Runtime.evaluate(expression="window.location.href")
        current_url = current_url_result.get("result", {}).get("value", "")
        
        # 从当前URL提取基础路径
        url_parts = current_url.rsplit('/', 1)
        base_path = url_parts[0] if len(url_parts) == 2 else current_url.rsplit('/', 2)[0]
        
        # 检测分页模式：gf.html, gf_2.html, gf_3.html 或 azyx_60.html 等
        url_prefix = None
        start_page_num = 1
        page_file_pattern = None
        
        # 优先检测 gf_数字.html 格式（如 gf_6.html）
        page_match = re.search(r'gf_(\d+)\.html', current_url)
        if page_match:
            start_page_num = int(page_match.group(1))  # 6
            url_prefix = "gf"
            page_file_pattern = "gf_{page_num}.html"
            print(f"   📄 检测到分页模式: gf_数字.html，当前页: {start_page_num}")
        else:
            # 检测 gf.html（第一页）
            if 'gf.html' in current_url and '_' not in current_url:
                start_page_num = 1
                url_prefix = "gf"
                page_file_pattern = "gf_{page_num}.html"
                print(f"   📄 检测到分页模式: gf.html（第一页），将使用 gf_2.html, gf_3.html...")
            else:
                # 检测其他格式（如 azyx_60.html）
                page_match = re.search(r'([a-z]+)_(\d+)\.html', current_url)
                if page_match:
                    url_prefix = page_match.group(1)  # azyx
                    start_page_num = int(page_match.group(2))  # 60
                    page_file_pattern = f"{url_prefix}_{{page_num}}.html"
                    print(f"   📄 检测到分页模式: {url_prefix}_数字.html，当前页: {start_page_num}")
                else:
                    # 默认使用 gf.html 格式
                    url_prefix = "gf"
                    start_page_num = 1
                    page_file_pattern = "gf_{page_num}.html"
                    print(f"   📄 使用默认分页模式: gf.html, gf_2.html, gf_3.html...")
        
        # 处理分页（如果有）
        all_games = []
        # 始终从第1页开始抓取（gf.html）
        current_page_num = 1
        target_start_page = 1
        
        # 如果当前不在第1页，先导航到第1页
        if start_page_num > 1 or ('gf.html' not in current_url and 'gf_' not in current_url):
            print(f"   📍 导航到第1页 (gf.html)...")
            first_page_url = f"{base_path}/gf.html"
            self.navigate(first_page_url, wait_time=2)
            time.sleep(1)
            # 滚动加载第一页内容
            self._scroll_to_load_all()
        
        while current_page_num <= target_start_page + max_pages - 1:
            print(f"\n📄 处理第 {current_page_num} 页...")
            
            # 提取当前页的游戏链接
            extract_games_js = """
            (function() {
                const games = [];
                const seenUrls = new Set();
                
                // 查找所有游戏链接
                const allLinks = document.querySelectorAll('a[href]');
                
                for (let link of allLinks) {
                    let href = link.href || link.getAttribute('href') || '';
                    const text = (link.textContent || link.innerText || '').trim();
                    
                    // 转换为完整URL
                    if (href && !href.startsWith('http')) {
                        if (href.startsWith('/')) {
                            href = window.location.origin + href;
                        } else {
                            href = window.location.origin + '/' + href;
                        }
                    }
                    
                    // 过滤掉无效链接
                    if (!href || href === '#' || href === 'javascript:void(0)') continue;
                    if (href.includes('gf.html')) continue;  // 排除列表页本身
                    if (seenUrls.has(href)) continue;
                    
                    // 检查是否是游戏详情页链接
                    // 格式: https://www.kxdw.com/android/xxxxx.html
                    if (href.includes('/android/') && 
                        href.endsWith('.html') && 
                        !href.includes('gf.html') &&
                        !href.includes('index.html')) {
                        seenUrls.add(href);
                        games.push({
                            name: text || '未知游戏',
                            url: href
                        });
                    }
                }
                
                return games;
            })();
            """
            
            result = self.tab.Runtime.evaluate(expression=extract_games_js, returnByValue=True)
            page_games = result.get("result", {}).get("value", [])
            
            if not page_games:
                print(f"   ⚠️  第 {current_page_num} 页没有找到游戏，可能已到最后一页")
                break
            
            # 去重（与已有游戏比较）
            new_games = []
            existing_urls = {g['url'] for g in all_games}
            for game in page_games:
                if game['url'] not in existing_urls:
                    new_games.append(game)
                    all_games.append(game)
            
            print(f"   ✅ 第 {current_page_num} 页找到 {len(page_games)} 个游戏（新增 {len(new_games)} 个）")
            
            # 准备下一页
            current_page_num += 1
            
            # 检查是否达到最大页数
            if current_page_num > target_start_page + max_pages:
                print(f"   ✅ 已达到最大页数限制 ({max_pages} 页)")
                break
            
            # 构造下一页文件名
            # 第一页是 gf.html，从第二页开始是 gf_2.html, gf_3.html 等
            if current_page_num == 1:
                next_page_file = "gf.html"
            else:
                # 从第二页开始使用 gf_2.html, gf_3.html 等格式
                if url_prefix:
                    next_page_file = f"{url_prefix}_{current_page_num}.html"
                else:
                    next_page_file = f"gf_{current_page_num}.html"
            
            # 构造完整URL
            next_url = f"{base_path}/{next_page_file}"
            
            print(f"   ⏭️  导航到第 {current_page_num} 页: {next_page_file}")
            self.navigate(next_url, wait_time=2)
            time.sleep(1)  # 等待页面加载
        
        print(f"\n✅ 共找到 {len(all_games)} 个游戏")
        
        # 显示前几个作为预览
        if all_games:
            print("\n📋 前5个游戏预览:")
            for i, game in enumerate(all_games[:5], 1):
                print(f"   {i}. {game.get('name', '未知')} - {game.get('url', '')[:60]}...")
        
        return all_games
    
    def _scroll_to_load_all(self):
        """滚动页面以加载所有内容"""
        scroll_js = """
        (function() {
            let lastHeight = 0;
            let currentHeight = document.body.scrollHeight;
            let scrollCount = 0;
            const maxScrolls = 50; // 最多滚动50次
            
            while (currentHeight !== lastHeight && scrollCount < maxScrolls) {
                lastHeight = currentHeight;
                window.scrollTo(0, document.body.scrollHeight);
                // 等待内容加载
                setTimeout(() => {}, 500);
                currentHeight = document.body.scrollHeight;
                scrollCount++;
            }
            
            return {scrollCount: scrollCount, finalHeight: currentHeight};
        })();
        """
        
        # 分步滚动
        for i in range(10):  # 滚动10次
            self.tab.Runtime.evaluate(expression=f"window.scrollTo(0, {i * 500})")
            time.sleep(0.5)
        
        # 滚动到底部
        self.tab.Runtime.evaluate(expression="window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        # 滚动回顶部
        self.tab.Runtime.evaluate(expression="window.scrollTo(0, 0)")
        time.sleep(1)
    
    def parse_game_detail(self, game_url: str) -> Optional[Dict]:
        """解析游戏详情页，提取名称、大小、下载地址"""
        try:
            print(f"   🔍 解析: {game_url[:60]}...")
            
            # 导航到详情页
            self.tab.Page.navigate(url=game_url)
            time.sleep(2)
            
            # 等待页面加载
            try:
                self.tab.wait(timeout=5)
            except:
                pass
            
            # 提取游戏信息
            extract_info_js = """
            (function() {
                const info = {
                    name: '',
                    size: '',
                    download_url: ''
                };
                
                // 提取游戏名称
                const nameSelectors = [
                    'h1',
                    '.game-title',
                    '.title',
                    '[class*="title"]',
                    'h2'
                ];
                
                for (let selector of nameSelectors) {
                    const el = document.querySelector(selector);
                    if (el) {
                        const text = (el.textContent || el.innerText || '').trim();
                        if (text && text.length > 0 && text.length < 100) {
                            info.name = text;
                            break;
                        }
                    }
                }
                
                // 提取文件大小
                const sizePatterns = [
                    /(\\d+\\.?\\d*)\\s*([MG]B)/i,
                    /大小[：:]\\s*(\\d+\\.?\\d*)\\s*([MG]B)/i,
                    /文件大小[：:]\\s*(\\d+\\.?\\d*)\\s*([MG]B)/i
                ];
                
                const allText = document.body.innerText || document.body.textContent || '';
                for (let pattern of sizePatterns) {
                    const match = allText.match(pattern);
                    if (match) {
                        info.size = match[0];
                        break;
                    }
                }
                
                // 如果没找到，尝试查找包含"MB"或"GB"的元素
                if (!info.size) {
                    const sizeElements = document.querySelectorAll('*');
                    for (let el of sizeElements) {
                        const text = (el.textContent || el.innerText || '').trim();
                        if (/\\d+\\.?\\d*\\s*[MG]B/i.test(text)) {
                            const match = text.match(/(\\d+\\.?\\d*\\s*[MG]B)/i);
                            if (match) {
                                info.size = match[1];
                                break;
                            }
                        }
                    }
                }
                
                // 提取下载地址
                const allLinks = document.querySelectorAll('a[href]');
                const downloadKeywords = ['下载', 'download', '立即下载', '安卓版下载', '高速下载'];
                
                for (let link of allLinks) {
                    let href = link.href || link.getAttribute('href') || '';
                    const text = (link.textContent || link.innerText || '').trim().toLowerCase();
                    
                    // 转换为完整URL
                    if (href && !href.startsWith('http')) {
                        if (href.startsWith('/')) {
                            href = window.location.origin + href;
                        } else {
                            href = window.location.origin + '/' + href;
                        }
                    }
                    
                    // 检查是否是下载链接
                    const isDownloadLink = 
                        href.includes('.apk') ||
                        href.includes('download') ||
                        href.includes('down') ||
                        (downloadKeywords.some(kw => text.includes(kw)) && href && !href.includes('#'));
                    
                    if (isDownloadLink && !href.includes('javascript:')) {
                        info.download_url = href;
                        break;
                    }
                }
                
                // 如果还没找到，尝试从页面HTML中提取
                if (!info.download_url) {
                    const html = document.documentElement.outerHTML;
                    const apkPattern = /(https?:\\/\\/[^\\s"']+\\.apk)/i;
                    const match = html.match(apkPattern);
                    if (match) {
                        info.download_url = match[1];
                    }
                }
                
                return info;
            })();
            """
            
            result = self.tab.Runtime.evaluate(expression=extract_info_js, returnByValue=True)
            info = result.get("result", {}).get("value", {})
            
            # 如果名称为空，使用URL中的信息
            if not info.get('name') or info.get('name') == '未知游戏':
                # 尝试从页面标题获取
                title_result = self.tab.Runtime.evaluate(expression="document.title")
                title = title_result.get("result", {}).get("value", "")
                if title:
                    info['name'] = title.split('_')[0].split('-')[0].strip()
            
            return info
            
        except Exception as e:
            print(f"   ❌ 解析失败: {e}")
            return None
    
    def convert_size_to_mb(self, size_str: str) -> float:
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
    
    def crawl_all_games(self, max_pages: int = 100) -> List[Dict]:
        """抓取所有游戏数据"""
        print("\n" + "=" * 60)
        print("🚀 开始抓取游戏数据")
        print("=" * 60)
        print(f"📄 最大页数限制: {max_pages} 页")
        
        # 1. 访问目标页面
        self.navigate(self.target_url, wait_time=3)
        
        # 2. 获取游戏列表
        game_list = self.get_game_list(max_pages=max_pages)
        
        if not game_list:
            print("❌ 未找到任何游戏")
            return []
        
        # 3. 整理游戏数据（不需要解析详情页）
        print("\n" + "=" * 60)
        print("📋 整理游戏数据")
        print("=" * 60)
        
        all_games = []
        total = len(game_list)
        
        for i, game in enumerate(game_list, 1):
            game_url = game.get('url', '')
            game_name = game.get('name', '未知游戏')
            
            if not game_url:
                continue
            
            game_data = {
                'name': game_name,
                'detail_url': game_url,
                'downloaded': '否'
            }
            
            all_games.append(game_data)
            
            if i % 50 == 0:
                print(f"   已处理 {i}/{total} 个游戏...")
        
        print(f"\n✅ 共抓取 {len(all_games)} 个游戏")
        
        return all_games
    
    def save_to_csv(self, games: List[Dict], output_file: str = "kxdw_games.csv"):
        """保存到CSV文件"""
        if not games:
            print("❌ 没有游戏数据可保存")
            return
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # 写入表头：游戏名称、详情页链接、是否已下载
                writer.writerow(['游戏名称', '详情页链接', '是否已下载'])
                
                # 写入数据
                for game in games:
                    writer.writerow([
                        game.get('name', ''),
                        game.get('detail_url', ''),
                        game.get('downloaded', '否')
                    ])
            
            print(f"\n✅ 数据已保存到: {output_path}")
            print(f"   共 {len(games)} 条记录")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None
    
    def close(self):
        """关闭标签页"""
        if self.tab:
            try:
                self.tab.stop()
                if self.browser:
                    self.browser.close_tab(self.tab)
            except:
                pass


def main():
    parser = argparse.ArgumentParser(
        description="开心电玩手游数据抓取工具 - 使用 Chrome DevTools Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用前准备:
  1. pip3 install pychrome requests websocket-client
  2. 启动 Chrome (Mac):
     /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222

示例:
  python3 kxdw_crawler.py
  python3 kxdw_crawler.py -o games.csv
  python3 kxdw_crawler.py -p 9222
        """
    )
    
    parser.add_argument("-o", "--output", default="kxdw_games.csv", help="CSV输出文件路径（默认: kxdw_games.csv）")
    parser.add_argument("-p", "--port", default="9222", help="Chrome 调试端口 (默认 9222)")
    parser.add_argument("--max-pages", type=int, default=100, help="最大处理页数 (默认 100)")
    
    args = parser.parse_args()
    
    if not pychrome:
        print("❌ 请先安装依赖")
        print("\n💡 推荐使用虚拟环境:")
        print("   1. 激活虚拟环境:")
        print("      source venv/bin/activate  # Mac/Linux")
        print("      或")
        print("      ./activate.sh  # 使用便捷脚本")
        print("   2. 如果依赖未安装，运行:")
        print("      pip install -r requirements.txt")
        print("\n或者直接安装到系统:")
        print("   pip3 install pychrome requests websocket-client")
        return 1
    
    debug_url = f"http://127.0.0.1:{args.port}"
    crawler = KXDWCrawler(debug_url=debug_url)
    
    if not crawler.connect():
        return 1
    
    try:
        crawler.new_tab()
        
        # 抓取所有游戏
        games = crawler.crawl_all_games(max_pages=args.max_pages)
        
        # 保存到CSV
        if games:
            crawler.save_to_csv(games, args.output)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.close()
    
    return 0


if __name__ == "__main__":
    exit(main())

