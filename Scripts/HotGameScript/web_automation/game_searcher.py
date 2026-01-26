# -*- coding: utf-8 -*-
"""
游戏搜索模块
使用Chrome DevTools Protocol搜索游戏并分析下载资源
"""
import time
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from loguru import logger
import requests
from bs4 import BeautifulSoup

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    CHROME_DEBUG_CONFIG,
    SEARCH_ENGINES,
    APK_DOWNLOAD_SITES,
    TIMEOUTS
)


class GameSearcher:
    """游戏搜索器"""
    
    def __init__(self, use_debug_mode: bool = True):
        """
        初始化游戏搜索器
        
        Args:
            use_debug_mode: 是否使用Chrome调试模式
        """
        self.driver: Optional[webdriver.Chrome] = None
        self.use_debug_mode = use_debug_mode
        self.search_results_cache: Dict[str, List[Dict]] = {}
        
    def connect(self, debug_port: int = None) -> bool:
        """
        连接到Chrome浏览器
        
        Args:
            debug_port: 调试端口号
            
        Returns:
            是否成功连接
        """
        debug_port = debug_port or CHROME_DEBUG_CONFIG.get("debug_port", 9222)
        
        try:
            options = Options()
            
            if self.use_debug_mode:
                # 连接到已运行的Chrome调试实例
                options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
                logger.info(f"正在连接到Chrome调试端口: {debug_port}")
            else:
                # 启动新的Chrome实例
                options.add_argument("--start-maximized")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                
                if CHROME_DEBUG_CONFIG.get("headless", False):
                    options.add_argument("--headless")
                
            self.driver = webdriver.Chrome(options=options)
            logger.success("成功连接到Chrome浏览器")
            return True
            
        except Exception as e:
            logger.error(f"连接Chrome失败: {e}")
            logger.info("请确保已启动Chrome调试模式:")
            logger.info(f'  Windows: chrome.exe --remote-debugging-port={debug_port}')
            logger.info(f'  Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port={debug_port}')
            return False
    
    def disconnect(self):
        """断开Chrome连接"""
        if self.driver:
            try:
                # 如果是调试模式，不关闭浏览器
                if not self.use_debug_mode:
                    self.driver.quit()
                else:
                    self.driver = None
                logger.info("已断开Chrome连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")
    
    def search_game(self, game_name: str, search_engine: str = "baidu") -> List[Dict[str, Any]]:
        """
        搜索游戏
        
        Args:
            game_name: 游戏名称
            search_engine: 搜索引擎 (baidu, google, bing)
            
        Returns:
            搜索结果列表
        """
        # 检查缓存
        cache_key = f"{game_name}_{search_engine}"
        if cache_key in self.search_results_cache:
            logger.info(f"使用缓存的搜索结果: {game_name}")
            return self.search_results_cache[cache_key]
        
        if not self.driver:
            if not self.connect():
                return []
        
        # 构建搜索关键词
        search_query = f"{game_name} APK下载 安卓"
        
        # 获取搜索URL
        search_url_template = SEARCH_ENGINES.get(search_engine, SEARCH_ENGINES["baidu"])
        search_url = search_url_template.format(quote(search_query))
        
        logger.info(f"正在搜索: {search_query}")
        
        results = []
        
        try:
            self.driver.get(search_url)
            time.sleep(2)  # 等待页面加载
            
            # 根据不同搜索引擎解析结果
            if search_engine == "baidu":
                results = self._parse_baidu_results()
            elif search_engine == "google":
                results = self._parse_google_results()
            elif search_engine == "bing":
                results = self._parse_bing_results()
            
            # 分析结果，标记可下载的链接
            results = self._analyze_download_links(results, game_name)
            
            # 缓存结果
            self.search_results_cache[cache_key] = results
            
            logger.info(f"搜索到 {len(results)} 条结果")
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
        
        return results
    
    def _parse_baidu_results(self) -> List[Dict[str, Any]]:
        """解析百度搜索结果"""
        results = []
        
        try:
            # 等待搜索结果加载
            WebDriverWait(self.driver, TIMEOUTS["page_load"]).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#content_left"))
            )
            
            # 获取搜索结果项
            items = self.driver.find_elements(By.CSS_SELECTOR, "#content_left .result")
            
            if not items:
                items = self.driver.find_elements(By.CSS_SELECTOR, "#content_left .c-container")
            
            for item in items[:20]:  # 只取前20条
                try:
                    # 获取标题和链接
                    title_elem = item.find_element(By.CSS_SELECTOR, "h3 a")
                    title = title_elem.text
                    url = title_elem.get_attribute("href")
                    
                    # 获取描述
                    try:
                        desc_elem = item.find_element(By.CSS_SELECTOR, ".c-abstract, .content-right_8Zs40")
                        description = desc_elem.text
                    except:
                        description = ""
                    
                    # 获取来源
                    try:
                        source_elem = item.find_element(By.CSS_SELECTOR, ".c-showurl, .source_1Vdff")
                        source = source_elem.text
                    except:
                        source = urlparse(url).netloc if url else ""
                    
                    if title and url:
                        results.append({
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": source,
                            "search_engine": "baidu"
                        })
                        
                except Exception as e:
                    logger.debug(f"解析单条结果时出错: {e}")
                    continue
                    
        except TimeoutException:
            logger.warning("百度搜索结果加载超时")
        except Exception as e:
            logger.error(f"解析百度结果失败: {e}")
        
        return results
    
    def _parse_google_results(self) -> List[Dict[str, Any]]:
        """解析Google搜索结果"""
        results = []
        
        try:
            WebDriverWait(self.driver, TIMEOUTS["page_load"]).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#search"))
            )
            
            items = self.driver.find_elements(By.CSS_SELECTOR, "#search .g")
            
            for item in items[:20]:
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, "h3")
                    link_elem = item.find_element(By.CSS_SELECTOR, "a")
                    
                    title = title_elem.text
                    url = link_elem.get_attribute("href")
                    
                    try:
                        desc_elem = item.find_element(By.CSS_SELECTOR, ".VwiC3b")
                        description = desc_elem.text
                    except:
                        description = ""
                    
                    if title and url:
                        results.append({
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": urlparse(url).netloc,
                            "search_engine": "google"
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"解析Google结果失败: {e}")
        
        return results
    
    def _parse_bing_results(self) -> List[Dict[str, Any]]:
        """解析Bing搜索结果"""
        results = []
        
        try:
            WebDriverWait(self.driver, TIMEOUTS["page_load"]).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#b_results"))
            )
            
            items = self.driver.find_elements(By.CSS_SELECTOR, "#b_results .b_algo")
            
            for item in items[:20]:
                try:
                    title_elem = item.find_element(By.CSS_SELECTOR, "h2 a")
                    title = title_elem.text
                    url = title_elem.get_attribute("href")
                    
                    try:
                        desc_elem = item.find_element(By.CSS_SELECTOR, ".b_caption p")
                        description = desc_elem.text
                    except:
                        description = ""
                    
                    if title and url:
                        results.append({
                            "title": title,
                            "url": url,
                            "description": description,
                            "source": urlparse(url).netloc,
                            "search_engine": "bing"
                        })
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"解析Bing结果失败: {e}")
        
        return results
    
    def _analyze_download_links(self, results: List[Dict], game_name: str) -> List[Dict]:
        """
        分析搜索结果，标记可下载的链接
        
        Args:
            results: 搜索结果列表
            game_name: 游戏名称
            
        Returns:
            带有分析结果的搜索结果列表
        """
        for result in results:
            url = result.get("url", "")
            title = result.get("title", "")
            description = result.get("description", "")
            
            # 检查是否为可信下载站点
            is_trusted_site = False
            matched_site = ""
            
            for site in APK_DOWNLOAD_SITES:
                if site in url.lower():
                    is_trusted_site = True
                    matched_site = site
                    break
            
            # 检查是否包含下载关键词
            download_keywords = ["下载", "download", "apk", "安装包", "安卓版"]
            has_download_keyword = any(
                kw in (title + description).lower() 
                for kw in download_keywords
            )
            
            # 检查是否包含游戏名
            has_game_name = game_name.lower() in (title + description).lower()
            
            # 计算可下载性评分
            download_score = 0
            if is_trusted_site:
                download_score += 50
            if has_download_keyword:
                download_score += 30
            if has_game_name:
                download_score += 20
            
            result["is_trusted_site"] = is_trusted_site
            result["matched_site"] = matched_site
            result["has_download_keyword"] = has_download_keyword
            result["has_game_name"] = has_game_name
            result["download_score"] = download_score
            result["is_downloadable"] = download_score >= 50
        
        # 按评分排序
        results.sort(key=lambda x: x.get("download_score", 0), reverse=True)
        
        return results
    
    def get_best_download_links(self, game_name: str, limit: int = 5) -> List[Dict]:
        """
        获取最佳下载链接
        
        Args:
            game_name: 游戏名称
            limit: 返回数量限制
            
        Returns:
            最佳下载链接列表
        """
        results = self.search_game(game_name)
        
        # 筛选可下载的链接
        downloadable = [r for r in results if r.get("is_downloadable", False)]
        
        if not downloadable:
            logger.warning(f"未找到 {game_name} 的可下载链接")
            # 返回评分最高的结果
            return results[:limit]
        
        return downloadable[:limit]
    
    def search_multiple_games(self, game_names: List[str]) -> Dict[str, List[Dict]]:
        """
        搜索多个游戏
        
        Args:
            game_names: 游戏名称列表
            
        Returns:
            每个游戏的搜索结果字典
        """
        all_results = {}
        
        for game_name in game_names:
            logger.info(f"正在搜索游戏: {game_name}")
            results = self.search_game(game_name)
            all_results[game_name] = results
            time.sleep(2)  # 避免请求过快
        
        return all_results
    
    def verify_download_page(self, url: str) -> Dict[str, Any]:
        """
        验证下载页面是否真的包含APK下载
        
        Args:
            url: 页面URL
            
        Returns:
            验证结果
        """
        result = {
            "url": url,
            "is_valid": False,
            "apk_links": [],
            "page_title": "",
            "error": None
        }
        
        if not self.driver:
            if not self.connect():
                result["error"] = "无法连接到浏览器"
                return result
        
        try:
            self.driver.get(url)
            time.sleep(3)  # 等待页面加载
            
            result["page_title"] = self.driver.title
            
            # 查找APK下载链接
            apk_patterns = [
                "a[href*='.apk']",
                "a[href*='download']",
                "a[download]",
                ".download-btn",
                ".apk-download",
                "[class*='download']"
            ]
            
            for pattern in apk_patterns:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, pattern)
                    for elem in elements:
                        href = elem.get_attribute("href")
                        text = elem.text
                        if href:
                            result["apk_links"].append({
                                "url": href,
                                "text": text,
                                "is_direct_apk": href.lower().endswith('.apk')
                            })
                except:
                    continue
            
            result["is_valid"] = len(result["apk_links"]) > 0
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"验证下载页面失败: {e}")
        
        return result
