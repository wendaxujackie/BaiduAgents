# -*- coding: utf-8 -*-
"""
APK下载模块
负责下载APK文件并按规则重命名
"""
import time
import os
import re
import random
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    DOWNLOADS_DIR,
    APK_KEYWORDS,
    APK_COPIES_COUNT,
    APK_TARGET_FOLDER,
    TIMEOUTS,
    BASE_DIR
)


class APKDownloader:
    """APK下载器"""
    
    def __init__(self):
        """初始化APK下载器"""
        self.driver: Optional[webdriver.Chrome] = None
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 确保下载目录存在
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 确保目标文件夹存在
        self.target_folder = BASE_DIR / APK_TARGET_FOLDER
        self.target_folder.mkdir(parents=True, exist_ok=True)
    
    def connect_browser(self, debug_port: int = 9222) -> bool:
        """连接到Chrome浏览器"""
        try:
            options = Options()
            options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
            
            # 设置下载目录
            prefs = {
                "download.default_directory": str(DOWNLOADS_DIR),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
            }
            options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=options)
            logger.success("成功连接到Chrome浏览器")
            return True
            
        except Exception as e:
            logger.error(f"连接Chrome失败: {e}")
            return False
    
    def download_apk(self, url: str, game_name: str) -> Optional[Path]:
        """
        下载APK文件
        
        Args:
            url: APK下载URL
            game_name: 游戏名称（用于命名）
            
        Returns:
            下载后的文件路径
        """
        logger.info(f"正在下载: {game_name}")
        logger.debug(f"下载URL: {url}")
        
        # 清理游戏名称用于文件名
        safe_name = self._sanitize_filename(game_name)
        
        # 判断是否为直接APK链接
        if url.lower().endswith('.apk'):
            return self._download_direct(url, safe_name)
        else:
            return self._download_from_page(url, safe_name)
    
    def _download_direct(self, url: str, safe_name: str) -> Optional[Path]:
        """直接下载APK文件"""
        try:
            response = self.session.get(url, stream=True, timeout=TIMEOUTS["download"])
            response.raise_for_status()
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            # 生成文件名
            filename = f"{safe_name}.apk"
            filepath = DOWNLOADS_DIR / filename
            
            # 下载文件（带进度条）
            with open(filepath, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            
            logger.success(f"下载完成: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"直接下载失败: {e}")
            return None
    
    def _download_from_page(self, url: str, safe_name: str) -> Optional[Path]:
        """从页面获取并下载APK"""
        if not self.driver:
            if not self.connect_browser():
                logger.error("无法连接到浏览器")
                return None
        
        try:
            self.driver.get(url)
            time.sleep(3)
            
            # 查找下载链接
            download_selectors = [
                "a[href$='.apk']",
                "a[download]",
                ".download-btn",
                ".apk-download",
                "a[href*='download']",
                ".btn-download",
                "#download",
                "[class*='download']"
            ]
            
            for selector in download_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        href = elem.get_attribute("href")
                        if href:
                            # 检查是否为APK链接
                            if href.lower().endswith('.apk'):
                                return self._download_direct(href, safe_name)
                            
                            # 尝试点击下载按钮
                            try:
                                elem.click()
                                time.sleep(5)  # 等待下载开始
                                
                                # 检查下载目录是否有新文件
                                downloaded_file = self._wait_for_download()
                                if downloaded_file:
                                    # 重命名文件
                                    new_path = DOWNLOADS_DIR / f"{safe_name}.apk"
                                    shutil.move(str(downloaded_file), str(new_path))
                                    logger.success(f"下载完成: {new_path}")
                                    return new_path
                            except:
                                continue
                                
                except Exception as e:
                    logger.debug(f"选择器 {selector} 未找到元素: {e}")
                    continue
            
            logger.warning(f"页面中未找到APK下载链接: {url}")
            return None
            
        except Exception as e:
            logger.error(f"从页面下载失败: {e}")
            return None
    
    def _wait_for_download(self, timeout: int = 60) -> Optional[Path]:
        """等待下载完成"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 获取下载目录中的文件
            files = list(DOWNLOADS_DIR.glob("*.apk"))
            
            for f in files:
                # 检查文件是否正在下载（.crdownload是Chrome的临时下载文件）
                if not str(f).endswith('.crdownload'):
                    return f
            
            time.sleep(1)
        
        return None
    
    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除非法字符"""
        # 移除或替换非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            name = name.replace(char, '')
        
        # 移除前后空白
        name = name.strip()
        
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        
        return name
    
    def generate_keyword_copies(self, apk_path: Path, game_name: str) -> List[Path]:
        """
        生成带关键词的APK副本（按照bat文件的规则）
        
        Args:
            apk_path: 原始APK文件路径
            game_name: 游戏名称
            
        Returns:
            生成的副本文件路径列表
        """
        if not apk_path.exists():
            logger.error(f"APK文件不存在: {apk_path}")
            return []
        
        logger.info(f"正在为 {game_name} 生成关键词副本...")
        
        copies = []
        safe_name = self._sanitize_filename(game_name)
        
        # 使用Fisher-Yates洗牌算法随机选择关键词（与bat文件逻辑一致）
        keywords = APK_KEYWORDS.copy()
        random.shuffle(keywords)
        
        # 生成指定数量的副本
        for i in range(min(APK_COPIES_COUNT, len(keywords))):
            keyword = keywords[i]
            new_name = f"{safe_name}{keyword}.apk"
            new_path = self.target_folder / new_name
            
            # 检查是否已存在
            if new_path.exists():
                logger.info(f"跳过: {new_name} 已存在")
                # 尝试使用备用关键词
                for j in range(APK_COPIES_COUNT, len(keywords)):
                    alt_keyword = keywords[j]
                    alt_name = f"{safe_name}{alt_keyword}.apk"
                    alt_path = self.target_folder / alt_name
                    if not alt_path.exists():
                        try:
                            shutil.copy2(str(apk_path), str(alt_path))
                            copies.append(alt_path)
                            logger.info(f"创建副本（备用）: {alt_name}")
                        except Exception as e:
                            logger.error(f"创建副本失败: {e}")
                        break
            else:
                try:
                    shutil.copy2(str(apk_path), str(new_path))
                    copies.append(new_path)
                    logger.info(f"创建副本 {i + 1}: {new_name}")
                except Exception as e:
                    logger.error(f"创建副本失败: {e}")
        
        # 移动原始文件到目标文件夹
        original_in_target = self.target_folder / apk_path.name
        if not original_in_target.exists():
            try:
                shutil.move(str(apk_path), str(original_in_target))
                logger.info(f"移动原始文件: {apk_path.name}")
            except Exception as e:
                logger.warning(f"移动原始文件失败: {e}")
        
        logger.success(f"为 {game_name} 生成了 {len(copies)} 个关键词副本")
        return copies
    
    def download_and_generate_copies(self, url: str, game_name: str) -> Dict[str, Any]:
        """
        下载APK并生成关键词副本
        
        Args:
            url: 下载URL
            game_name: 游戏名称
            
        Returns:
            处理结果
        """
        result = {
            "game_name": game_name,
            "url": url,
            "success": False,
            "original_file": None,
            "copies": [],
            "error": None
        }
        
        # 下载APK
        apk_path = self.download_apk(url, game_name)
        
        if not apk_path:
            result["error"] = "下载失败"
            return result
        
        result["original_file"] = str(apk_path)
        
        # 生成关键词副本
        copies = self.generate_keyword_copies(apk_path, game_name)
        result["copies"] = [str(p) for p in copies]
        result["success"] = True
        
        return result
    
    def process_multiple_games(self, download_links: Dict[str, List[Dict]]) -> List[Dict]:
        """
        处理多个游戏的下载
        
        Args:
            download_links: 游戏名称到下载链接列表的字典
            
        Returns:
            处理结果列表
        """
        results = []
        
        for game_name, links in download_links.items():
            if not links:
                logger.warning(f"游戏 {game_name} 没有可用的下载链接")
                continue
            
            # 选择评分最高的链接
            best_link = max(links, key=lambda x: x.get("download_score", 0))
            url = best_link.get("url")
            
            if url:
                logger.info(f"处理游戏: {game_name}")
                result = self.download_and_generate_copies(url, game_name)
                results.append(result)
                
                # 避免请求过快
                time.sleep(2)
        
        return results
    
    def get_summary(self, results: List[Dict]) -> Dict[str, Any]:
        """
        获取处理汇总
        
        Args:
            results: 处理结果列表
            
        Returns:
            汇总信息
        """
        total = len(results)
        success = sum(1 for r in results if r.get("success"))
        failed = total - success
        total_copies = sum(len(r.get("copies", [])) for r in results)
        
        return {
            "total_games": total,
            "success_count": success,
            "failed_count": failed,
            "total_copies": total_copies,
            "target_folder": str(self.target_folder),
            "details": results
        }
