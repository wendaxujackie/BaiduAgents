# -*- coding: utf-8 -*-
"""
快手Android自动化模块
实现Android平台上的快手APP自动化操作
"""
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import (
    APPIUM_CONFIG, 
    KUAISHOU_ELEMENTS, 
    LIMITS,
    SCREENSHOTS_DIR
)
from .base_automation import BaseAutomation


class KuaishouAndroid(BaseAutomation):
    """快手Android自动化类"""
    
    def __init__(self, custom_capabilities: Dict[str, Any] = None):
        """
        初始化快手Android自动化
        
        Args:
            custom_capabilities: 自定义设备能力配置
        """
        config = APPIUM_CONFIG["android"]
        capabilities = config["capabilities"].copy()
        
        if custom_capabilities:
            capabilities.update(custom_capabilities)
        
        super().__init__(
            platform="android",
            server_url=config["server_url"],
            capabilities=capabilities
        )
        
        self.elements = KUAISHOU_ELEMENTS["android"]
        self.processed_users = set()  # 已处理的用户
        self.processed_videos = set()  # 已处理的视频
        
    def open_app(self) -> bool:
        """打开快手APP"""
        if not self.driver:
            if not self.connect():
                return False
        
        logger.info("正在打开快手APP...")
        
        try:
            # 检查APP是否已启动
            current_activity = self.driver.current_activity
            if "HomeActivity" in current_activity or "MainActivity" in current_activity:
                logger.info("快手APP已在前台运行")
                return True
            
            # 启动APP
            self.driver.activate_app(self.capabilities.get("appPackage", "com.smile.gifmaker"))
            time.sleep(3)  # 等待APP启动
            
            logger.success("快手APP启动成功")
            return True
            
        except Exception as e:
            logger.error(f"打开快手APP失败: {e}")
            return False
    
    def navigate_to_me(self) -> bool:
        """导航到'我的'页面"""
        logger.info("正在导航到'我的'页面...")
        
        # 尝试多种方式定位'我'标签
        me_locators = [
            self.elements["tab_me"],
            {"type": "xpath", "value": "//*[contains(@text,'我')]"},
            {"type": "xpath", "value": "//android.widget.TextView[@text='我的']"},
            {"type": "android_uiautomator", "value": 'new UiSelector().text("我")'},
        ]
        
        for locator in me_locators:
            if self.click_element(locator, timeout=5):
                time.sleep(2)
                logger.success("成功导航到'我的'页面")
                return True
        
        logger.error("无法找到'我的'标签")
        return False
    
    def click_follow(self) -> bool:
        """点击关注按钮进入关注列表"""
        logger.info("正在点击关注按钮...")
        
        # 尝试多种方式定位关注按钮
        follow_locators = [
            self.elements["follow_button"],
            {"type": "xpath", "value": "//*[contains(@text,'关注')]"},
            {"type": "xpath", "value": "//android.widget.TextView[contains(@text,'关注') and contains(@resource-id,'follow')]"},
            {"type": "android_uiautomator", "value": 'new UiSelector().textContains("关注")'},
        ]
        
        for locator in follow_locators:
            if self.click_element(locator, timeout=5):
                time.sleep(2)
                logger.success("成功进入关注列表")
                return True
        
        logger.error("无法找到关注按钮")
        return False
    
    def get_follow_list(self) -> List[Dict[str, Any]]:
        """
        获取关注列表
        
        Returns:
            关注用户信息列表
        """
        logger.info("正在获取关注列表...")
        follow_users = []
        scroll_count = 0
        max_scrolls = 10  # 最大滚动次数
        
        while len(follow_users) < LIMITS["max_follow_users"] and scroll_count < max_scrolls:
            # 查找列表项
            items = self.find_elements(self.elements["follow_list_item"], timeout=5)
            
            if not items:
                # 尝试备用定位方式
                items = self.find_elements({
                    "type": "xpath",
                    "value": "//androidx.recyclerview.widget.RecyclerView//*[@clickable='true']"
                }, timeout=5)
            
            for item in items:
                try:
                    # 尝试获取用户名
                    user_name_element = item.find_element(
                        "xpath", 
                        ".//*[contains(@resource-id,'user_name') or contains(@resource-id,'name')]"
                    )
                    user_name = user_name_element.text if user_name_element else ""
                    
                    if user_name and user_name not in self.processed_users:
                        user_info = {
                            "name": user_name,
                            "element": item,
                            "index": len(follow_users)
                        }
                        follow_users.append(user_info)
                        self.processed_users.add(user_name)
                        logger.info(f"发现关注用户: {user_name}")
                        
                except Exception as e:
                    logger.debug(f"处理列表项时出错: {e}")
                    continue
            
            # 如果没有找到新用户，滚动页面
            prev_count = len(follow_users)
            self.swipe_up(ratio=0.6)
            scroll_count += 1
            
            if len(follow_users) == prev_count:
                # 如果滚动后没有新用户，可能已到列表末尾
                logger.info("已到达关注列表末尾")
                break
        
        logger.info(f"共获取 {len(follow_users)} 个关注用户")
        return follow_users
    
    def enter_user_profile(self, user_info: Dict[str, Any]) -> bool:
        """
        进入用户主页
        
        Args:
            user_info: 用户信息字典
            
        Returns:
            是否成功进入
        """
        user_name = user_info.get("name", "未知用户")
        logger.info(f"正在进入用户 [{user_name}] 的主页...")
        
        try:
            element = user_info.get("element")
            if element:
                element.click()
                time.sleep(2)
                logger.success(f"成功进入用户 [{user_name}] 的主页")
                return True
        except Exception as e:
            logger.error(f"进入用户主页失败: {e}")
        
        # 如果直接点击失败，尝试通过用户名查找
        user_locator = {
            "type": "xpath",
            "value": f"//*[contains(@text,'{user_name}')]"
        }
        
        if self.click_element(user_locator, timeout=5):
            time.sleep(2)
            return True
        
        return False
    
    def get_user_videos(self) -> List[Dict[str, Any]]:
        """
        获取用户发布的视频列表
        
        Returns:
            视频信息列表
        """
        logger.info("正在获取用户视频列表...")
        videos = []
        scroll_count = 0
        max_scrolls = 5
        
        # 先点击'作品'标签确保在作品列表
        works_locators = [
            self.elements["works_tab"],
            {"type": "xpath", "value": "//*[contains(@text,'作品')]"},
            {"type": "android_uiautomator", "value": 'new UiSelector().textContains("作品")'},
        ]
        
        for locator in works_locators:
            if self.click_element(locator, timeout=3):
                time.sleep(1)
                break
        
        while len(videos) < LIMITS["max_videos_per_user"] and scroll_count < max_scrolls:
            # 查找视频项
            video_items = self.find_elements(self.elements["video_item"], timeout=5)
            
            if not video_items:
                video_items = self.find_elements({
                    "type": "xpath",
                    "value": "//androidx.recyclerview.widget.RecyclerView//android.widget.ImageView[@clickable='true']"
                }, timeout=5)
            
            for idx, item in enumerate(video_items):
                try:
                    # 生成唯一标识
                    video_id = f"video_{len(videos)}_{int(time.time())}"
                    
                    if video_id not in self.processed_videos:
                        video_info = {
                            "id": video_id,
                            "element": item,
                            "index": len(videos)
                        }
                        videos.append(video_info)
                        self.processed_videos.add(video_id)
                        
                except Exception as e:
                    logger.debug(f"处理视频项时出错: {e}")
                    continue
            
            if len(videos) >= LIMITS["max_videos_per_user"]:
                break
                
            prev_count = len(videos)
            self.swipe_up(ratio=0.4)
            scroll_count += 1
            
            if len(videos) == prev_count:
                break
        
        logger.info(f"共获取 {len(videos)} 个视频")
        return videos
    
    def enter_video_detail(self, video_info: Dict[str, Any]) -> bool:
        """
        进入视频详情页
        
        Args:
            video_info: 视频信息字典
            
        Returns:
            是否成功进入
        """
        video_id = video_info.get("id", "未知视频")
        logger.info(f"正在进入视频 [{video_id}] 详情页...")
        
        try:
            element = video_info.get("element")
            if element:
                element.click()
                time.sleep(2)
                logger.success(f"成功进入视频详情页")
                return True
        except Exception as e:
            logger.error(f"进入视频详情页失败: {e}")
        
        return False
    
    def screenshot_and_analyze(self, prefix: str = "") -> Optional[Path]:
        """
        截图并保存用于后续分析
        
        Args:
            prefix: 文件名前缀
            
        Returns:
            截图文件路径
        """
        timestamp = int(time.time() * 1000)
        filename = f"{prefix}_{timestamp}.png" if prefix else f"screenshot_{timestamp}.png"
        return self.take_screenshot(filename)
    
    def process_all_follows(self, on_screenshot_callback=None):
        """
        处理所有关注用户
        
        Args:
            on_screenshot_callback: 截图后的回调函数，用于OCR处理
            
        Returns:
            所有截图路径列表
        """
        screenshots = []
        
        # 1. 打开APP
        if not self.open_app():
            logger.error("无法打开快手APP")
            return screenshots
        
        # 2. 导航到'我的'页面
        if not self.navigate_to_me():
            logger.error("无法导航到'我的'页面")
            return screenshots
        
        # 3. 点击关注
        if not self.click_follow():
            logger.error("无法进入关注列表")
            return screenshots
        
        # 4. 获取关注列表
        follow_list = self.get_follow_list()
        
        if not follow_list:
            logger.warning("关注列表为空")
            return screenshots
        
        # 5. 遍历每个关注用户
        for user_idx, user_info in enumerate(follow_list):
            user_name = user_info.get("name", f"用户{user_idx}")
            logger.info(f"正在处理用户 {user_idx + 1}/{len(follow_list)}: {user_name}")
            
            # 重新获取关注列表中的元素（因为页面可能已刷新）
            if user_idx > 0:
                # 返回到关注列表
                self.go_back()
                time.sleep(1)
                
                # 重新定位用户
                current_follows = self.get_follow_list()
                matching_user = None
                for u in current_follows:
                    if u.get("name") == user_name:
                        matching_user = u
                        break
                
                if not matching_user:
                    logger.warning(f"无法重新定位用户: {user_name}")
                    continue
                    
                user_info = matching_user
            
            # 进入用户主页
            if not self.enter_user_profile(user_info):
                continue
            
            # 获取用户视频
            videos = self.get_user_videos()
            
            # 遍历每个视频
            for video_idx, video_info in enumerate(videos):
                logger.info(f"  处理视频 {video_idx + 1}/{len(videos)}")
                
                # 重新获取视频列表（如果不是第一个视频）
                if video_idx > 0:
                    self.go_back()
                    time.sleep(1)
                    current_videos = self.get_user_videos()
                    if video_idx < len(current_videos):
                        video_info = current_videos[video_idx]
                    else:
                        continue
                
                # 进入视频详情
                if not self.enter_video_detail(video_info):
                    continue
                
                # 等待视频加载
                time.sleep(2)
                
                # 截图
                screenshot_path = self.screenshot_and_analyze(
                    prefix=f"user{user_idx}_video{video_idx}"
                )
                
                if screenshot_path:
                    screenshots.append(screenshot_path)
                    
                    # 调用OCR回调
                    if on_screenshot_callback:
                        try:
                            on_screenshot_callback(screenshot_path)
                        except Exception as e:
                            logger.error(f"OCR回调处理失败: {e}")
                
                # 返回视频列表
                self.go_back()
                time.sleep(1)
            
            # 返回关注列表
            self.go_back()
            time.sleep(1)
        
        logger.success(f"处理完成，共截取 {len(screenshots)} 张截图")
        return screenshots
    
    def close(self):
        """关闭自动化连接"""
        self.disconnect()
