# -*- coding: utf-8 -*-
"""
移动端自动化基类
提供通用的自动化操作方法
"""
import time
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pathlib import Path

from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.common import AppiumOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException,
    StaleElementReferenceException
)
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import TIMEOUTS, LIMITS, SCREENSHOTS_DIR


class BaseAutomation(ABC):
    """移动端自动化基类"""
    
    def __init__(self, platform: str, server_url: str, capabilities: Dict[str, Any]):
        """
        初始化自动化基类
        
        Args:
            platform: 平台名称 ('android' 或 'ios')
            server_url: Appium服务器地址
            capabilities: 设备能力配置
        """
        self.platform = platform
        self.server_url = server_url
        self.capabilities = capabilities
        self.driver: Optional[webdriver.Remote] = None
        self.wait: Optional[WebDriverWait] = None
        
    def connect(self) -> bool:
        """连接到设备"""
        try:
            logger.info(f"正在连接到{self.platform}设备...")
            options = AppiumOptions()
            for key, value in self.capabilities.items():
                options.set_capability(key, value)
            
            self.driver = webdriver.Remote(
                command_executor=self.server_url,
                options=options
            )
            self.wait = WebDriverWait(self.driver, TIMEOUTS["element_wait"])
            logger.success(f"成功连接到{self.platform}设备")
            return True
        except Exception as e:
            logger.error(f"连接设备失败: {e}")
            return False
    
    def disconnect(self):
        """断开设备连接"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("已断开设备连接")
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")
            finally:
                self.driver = None
                self.wait = None
    
    def find_element(self, locator: Dict[str, str], timeout: int = None) -> Optional[Any]:
        """
        查找单个元素
        
        Args:
            locator: 元素定位器 {'type': 'xpath/id/...', 'value': '...'}
            timeout: 超时时间
            
        Returns:
            找到的元素或None
        """
        if not self.driver:
            logger.error("未连接到设备")
            return None
            
        timeout = timeout or TIMEOUTS["element_wait"]
        locator_type = self._get_locator_type(locator["type"])
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(
                EC.presence_of_element_located((locator_type, locator["value"]))
            )
            return element
        except TimeoutException:
            logger.warning(f"元素未找到: {locator}")
            return None
        except Exception as e:
            logger.error(f"查找元素时出错: {e}")
            return None
    
    def find_elements(self, locator: Dict[str, str], timeout: int = None) -> List[Any]:
        """
        查找多个元素
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            找到的元素列表
        """
        if not self.driver:
            logger.error("未连接到设备")
            return []
            
        timeout = timeout or TIMEOUTS["element_wait"]
        locator_type = self._get_locator_type(locator["type"])
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((locator_type, locator["value"])))
            elements = self.driver.find_elements(locator_type, locator["value"])
            return elements
        except TimeoutException:
            logger.warning(f"元素未找到: {locator}")
            return []
        except Exception as e:
            logger.error(f"查找元素时出错: {e}")
            return []
    
    def click_element(self, locator: Dict[str, str], timeout: int = None) -> bool:
        """
        点击元素
        
        Args:
            locator: 元素定位器
            timeout: 超时时间
            
        Returns:
            是否成功点击
        """
        element = self.find_element(locator, timeout)
        if element:
            try:
                element.click()
                time.sleep(0.5)  # 点击后短暂等待
                return True
            except Exception as e:
                logger.error(f"点击元素失败: {e}")
        return False
    
    def input_text(self, locator: Dict[str, str], text: str, clear: bool = True) -> bool:
        """
        输入文本
        
        Args:
            locator: 元素定位器
            text: 要输入的文本
            clear: 是否先清空
            
        Returns:
            是否成功输入
        """
        element = self.find_element(locator)
        if element:
            try:
                if clear:
                    element.clear()
                element.send_keys(text)
                return True
            except Exception as e:
                logger.error(f"输入文本失败: {e}")
        return False
    
    def get_text(self, locator: Dict[str, str]) -> str:
        """获取元素文本"""
        element = self.find_element(locator)
        if element:
            try:
                return element.text
            except Exception as e:
                logger.error(f"获取文本失败: {e}")
        return ""
    
    def take_screenshot(self, filename: str = None) -> Optional[Path]:
        """
        截取屏幕截图
        
        Args:
            filename: 文件名（不含路径）
            
        Returns:
            截图文件路径
        """
        if not self.driver:
            logger.error("未连接到设备")
            return None
            
        if not filename:
            filename = f"screenshot_{int(time.time() * 1000)}.png"
        
        filepath = SCREENSHOTS_DIR / filename
        
        try:
            self.driver.save_screenshot(str(filepath))
            logger.info(f"截图已保存: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    def swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: int = 500):
        """
        滑动操作
        
        Args:
            start_x: 起始X坐标
            start_y: 起始Y坐标
            end_x: 结束X坐标
            end_y: 结束Y坐标
            duration: 滑动持续时间（毫秒）
        """
        if not self.driver:
            return
        try:
            self.driver.swipe(start_x, start_y, end_x, end_y, duration)
            time.sleep(LIMITS["scroll_pause_time"])
        except Exception as e:
            logger.error(f"滑动操作失败: {e}")
    
    def swipe_up(self, ratio: float = 0.5):
        """向上滑动（向下浏览）"""
        if not self.driver:
            return
        size = self.driver.get_window_size()
        width = size['width']
        height = size['height']
        
        start_x = width // 2
        start_y = int(height * 0.8)
        end_y = int(height * (0.8 - ratio * 0.6))
        
        self.swipe(start_x, start_y, start_x, end_y)
    
    def swipe_down(self, ratio: float = 0.5):
        """向下滑动（向上浏览）"""
        if not self.driver:
            return
        size = self.driver.get_window_size()
        width = size['width']
        height = size['height']
        
        start_x = width // 2
        start_y = int(height * 0.3)
        end_y = int(height * (0.3 + ratio * 0.5))
        
        self.swipe(start_x, start_y, start_x, end_y)
    
    def go_back(self) -> bool:
        """返回上一页"""
        if not self.driver:
            return False
        try:
            self.driver.back()
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"返回操作失败: {e}")
            return False
    
    def wait_for_activity(self, activity: str, timeout: int = 10) -> bool:
        """等待指定Activity出现（仅Android）"""
        if self.platform != 'android' or not self.driver:
            return False
        try:
            return self.driver.wait_activity(activity, timeout)
        except Exception:
            return False
    
    def is_element_present(self, locator: Dict[str, str], timeout: int = 3) -> bool:
        """检查元素是否存在"""
        return self.find_element(locator, timeout) is not None
    
    def _get_locator_type(self, type_str: str):
        """转换定位器类型"""
        type_mapping = {
            "id": AppiumBy.ID,
            "xpath": AppiumBy.XPATH,
            "accessibility_id": AppiumBy.ACCESSIBILITY_ID,
            "class_name": AppiumBy.CLASS_NAME,
            "name": AppiumBy.NAME,
            "android_uiautomator": AppiumBy.ANDROID_UIAUTOMATOR,
            "ios_predicate": AppiumBy.IOS_PREDICATE,
            "ios_class_chain": AppiumBy.IOS_CLASS_CHAIN,
        }
        return type_mapping.get(type_str, AppiumBy.XPATH)
    
    @abstractmethod
    def open_app(self) -> bool:
        """打开APP"""
        pass
    
    @abstractmethod
    def navigate_to_me(self) -> bool:
        """导航到'我的'页面"""
        pass
    
    @abstractmethod
    def click_follow(self) -> bool:
        """点击关注按钮"""
        pass
    
    @abstractmethod
    def get_follow_list(self) -> List[Dict[str, Any]]:
        """获取关注列表"""
        pass
    
    @abstractmethod
    def enter_user_profile(self, user_info: Dict[str, Any]) -> bool:
        """进入用户主页"""
        pass
    
    @abstractmethod
    def get_user_videos(self) -> List[Dict[str, Any]]:
        """获取用户视频列表"""
        pass
    
    @abstractmethod
    def enter_video_detail(self, video_info: Dict[str, Any]) -> bool:
        """进入视频详情页"""
        pass
