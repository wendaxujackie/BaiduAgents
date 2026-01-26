# -*- coding: utf-8 -*-
"""
快手iOS自动化模块
实现iOS平台上的快手APP自动化操作
"""
import time
import subprocess
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


def get_connected_ios_devices() -> List[Dict[str, str]]:
    """
    获取已连接的iOS设备列表
    
    Returns:
        设备列表 [{"udid": "xxx", "name": "xxx"}, ...]
    """
    devices = []
    
    # 方法1: 使用 xcrun xctrace
    try:
        result = subprocess.run(
            ["xcrun", "xctrace", "list", "devices"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines:
                # 跳过模拟器和标题行
                if 'Simulator' in line or '==' in line or not line.strip():
                    continue
                # 解析真机信息，格式: "iPhone Name (iOS Version) (UDID)"
                if '(' in line and ')' in line:
                    parts = line.rsplit('(', 1)
                    if len(parts) == 2:
                        udid = parts[1].rstrip(')')
                        # 验证是否为有效UDID（40字符或更长）
                        if len(udid) >= 20 and '-' not in udid[:10]:
                            name = parts[0].strip()
                            # 提取设备名（去掉iOS版本）
                            if '(' in name:
                                name = name.rsplit('(', 1)[0].strip()
                            devices.append({"udid": udid, "name": name})
    except Exception as e:
        logger.debug(f"xcrun xctrace 检测失败: {e}")
    
    # 方法2: 使用 idevice_id (libimobiledevice)
    if not devices:
        try:
            result = subprocess.run(
                ["idevice_id", "-l"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                udids = result.stdout.strip().split('\n')
                for udid in udids:
                    if udid.strip():
                        devices.append({"udid": udid.strip(), "name": "iPhone"})
        except Exception as e:
            logger.debug(f"idevice_id 检测失败: {e}")
    
    return devices


class KuaishouiOS(BaseAutomation):
    """快手iOS自动化类"""
    
    def __init__(self, custom_capabilities: Dict[str, Any] = None):
        """
        初始化快手iOS自动化
        
        Args:
            custom_capabilities: 自定义设备能力配置
        """
        config = APPIUM_CONFIG["ios"]
        capabilities = config["capabilities"].copy()
        
        if custom_capabilities:
            capabilities.update(custom_capabilities)
        
        # 自动检测设备UDID
        if capabilities.get("udid") == "auto" or not capabilities.get("udid"):
            devices = get_connected_ios_devices()
            if devices:
                capabilities["udid"] = devices[0]["udid"]
                capabilities["deviceName"] = devices[0]["name"]
                logger.info(f"自动检测到iOS设备: {devices[0]['name']} ({devices[0]['udid'][:8]}...)")
            else:
                logger.warning("未检测到已连接的iOS真机")
                logger.info("请确保：")
                logger.info("  1. iPhone已通过USB连接到Mac")
                logger.info("  2. 已在iPhone上点击'信任此电脑'")
                logger.info("  3. iPhone已解锁")
                # 删除auto值，让Appium使用默认行为
                if "udid" in capabilities:
                    del capabilities["udid"]
        
        super().__init__(
            platform="ios",
            server_url=config["server_url"],
            capabilities=capabilities
        )
        
        self.elements = KUAISHOU_ELEMENTS["ios"]
        self.processed_users = set()
        self.processed_videos = set()
        
    def open_app(self) -> bool:
        """打开快手APP"""
        if not self.driver:
            if not self.connect():
                return False
        
        logger.info("正在打开快手APP...")
        
        try:
            bundle_id = self.capabilities.get("bundleId", "com.kuaishou.nebula")
            self.driver.activate_app(bundle_id)
            time.sleep(3)
            
            logger.success("快手APP启动成功")
            return True
            
        except Exception as e:
            logger.error(f"打开快手APP失败: {e}")
            return False
    
    def navigate_to_me(self) -> bool:
        """导航到'我的'页面"""
        logger.info("正在导航到'我的'页面...")
        
        me_locators = [
            self.elements["tab_me"],
            {"type": "accessibility_id", "value": "我的"},
            {"type": "xpath", "value": "//XCUIElementTypeButton[@name='我']"},
            {"type": "ios_predicate", "value": "label == '我' OR label == '我的'"},
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
        
        follow_locators = [
            self.elements["follow_button"],
            {"type": "accessibility_id", "value": "关注"},
            {"type": "xpath", "value": "//XCUIElementTypeStaticText[contains(@name,'关注')]"},
            {"type": "ios_predicate", "value": "label CONTAINS '关注'"},
        ]
        
        for locator in follow_locators:
            if self.click_element(locator, timeout=5):
                time.sleep(2)
                logger.success("成功进入关注列表")
                return True
        
        logger.error("无法找到关注按钮")
        return False
    
    def _is_valid_user_name(self, name: str) -> bool:
        """检查是否为有效的用户名（允许空白用户名，因为有些用户就是没有名称）"""
        if not name:
            return False
        
        name = name.strip()
        
        # 排除的关键词列表（筛选按钮、UI元素、功能按钮、状态文字等）
        invalid_keywords = [
            "我的关注",
            "关注",
            "取消关注",
            "快手平台",
            "快手官方",
            "看作品",
            "查看更多",
            "全部",
            "人）",  # "我的关注（3人）"
            "综合排序",
            "有更新",
            "有看过",
            "最新",
            "最热",
            "你可能感兴趣的人",
            "你可能错过的更新",
            "发私信",
            "进店铺",
            "已关注",
            "设置备注",
            "升级为快手号",
            "加载中",
            "批量管理",
            "好评率",
            "直播中",
            "直播",
            "看过",
            "%",
        ]
        
        for keyword in invalid_keywords:
            if keyword in name:
                logger.debug(f"过滤无效用户名(包含关键词): {name}")
                return False
        
        # 排除纯数字
        if name.isdigit():
            logger.debug(f"过滤无效用户名(纯数字): {name}")
            return False
        
        # 排除包含百分号的（如"97% 好评率"）
        if "%" in name:
            logger.debug(f"过滤无效用户名(包含百分号): {name}")
            return False
        
        # 允许空白用户名（有些用户就是没有名称）
        # 只要不是明显的UI元素关键词，就认为是有效用户
        
        return True
    
    def _is_follow_user_cell(self, cell) -> bool:
        """检查cell是否是真正的关注用户cell"""
        try:
            # 检查cell是否可点击（真正的用户cell应该是可点击的）
            if not cell.is_displayed():
                return False
            
            # 检查是否有头像元素（真正的用户cell通常有头像）
            has_image = len(cell.find_elements("xpath", ".//XCUIElementTypeImage")) > 0
            
            # 获取cell中的所有文本元素
            text_elements = cell.find_elements("xpath", ".//XCUIElementTypeStaticText")
            if len(text_elements) < 1:
                return False
            
            # 收集所有文本，找到最可能的用户名
            all_texts = []
            for elem in text_elements:
                text = elem.text
                if text and text.strip():
                    all_texts.append(text.strip())
            
            # 如果没有文本，不是用户cell
            if not all_texts:
                return False
            
            # 找到最长的有效用户名（排除状态文字、按钮文字等）
            valid_user_name = None
            max_length = 0
            
            for text in all_texts:
                if self._is_valid_user_name(text):
                    # 排除状态文字（通常很短，如"直播中"、"有看过"）
                    if len(text) <= 4 and any(keyword in text for keyword in ["中", "直播", "在线", "看过", "更新"]):
                        continue
                    # 选择最长的有效用户名
                    if len(text) > max_length:
                        valid_user_name = text
                        max_length = len(text)
            
            # 真正的用户cell应该：有头像 或者 有足够长的有效用户名（至少3个字符）
            if has_image:
                # 有头像，认为是用户cell
                return True
            elif valid_user_name and len(valid_user_name) >= 3:
                # 没有头像但用户名足够长，也可能是用户cell
                return True
            
            return False
        except:
            return False
    
    def get_follow_list(self) -> List[Dict[str, Any]]:
        """获取关注列表 - 只获取真正的关注用户cell"""
        logger.info("正在获取关注列表...")
        follow_users = []
        scroll_count = 0
        max_scrolls = 10
        seen_names = set()  # 用于去重
        
        while len(follow_users) < LIMITS["max_follow_users"] and scroll_count < max_scrolls:
            items = self.find_elements(self.elements["follow_list_item"], timeout=5)
            
            if not items:
                items = self.find_elements({
                    "type": "xpath",
                    "value": "//XCUIElementTypeTable//XCUIElementTypeCell"
                }, timeout=5)
            
            for item_idx, item in enumerate(items):
                try:
                    # 先检查是否是真正的关注用户cell
                    if not self._is_follow_user_cell(item):
                        continue
                    
                    # 获取cell中的所有文本元素
                    user_name_elements = item.find_elements(
                        "xpath",
                        ".//XCUIElementTypeStaticText"
                    )
                    
                    # 找到最长的有效用户名（通常是真正的用户名）
                    user_name = ""
                    max_length = 0
                    for elem in user_name_elements:
                        text = elem.text
                        if text and self._is_valid_user_name(text):
                            text = text.strip()
                            # 排除状态文字（通常很短）
                            if len(text) <= 3 and any(keyword in text for keyword in ["中", "直播", "在线"]):
                                continue
                            # 选择最长的有效用户名
                            if len(text) > max_length:
                                user_name = text
                                max_length = len(user_name)
                    
                    if user_name and user_name not in seen_names:
                        user_info = {
                            "name": user_name,
                            "element": item,
                            "index": len(follow_users),  # 在最终列表中的索引
                            "list_index": item_idx,  # 在当前屏幕列表中的索引
                        }
                        follow_users.append(user_info)
                        seen_names.add(user_name)
                        logger.info(f"✅ 发现有效用户: {user_name} (索引: {len(follow_users)-1})")
                        
                except Exception as e:
                    logger.debug(f"处理列表项时出错: {e}")
                    continue
            
            prev_count = len(follow_users)
            self.swipe_up(ratio=0.6)
            scroll_count += 1
            
            if len(follow_users) == prev_count:
                logger.info("已到达关注列表末尾")
                break
        
        logger.info(f"共获取 {len(follow_users)} 个有效关注用户")
        return follow_users
    
    def enter_user_profile(self, user_info: Dict[str, Any]) -> bool:
        """进入用户主页"""
        user_name = user_info.get("name", "未知用户")
        logger.info(f"正在进入用户 [{user_name}] 的主页...")
        
        # 优先尝试使用元素（如果可用且有效）
        element = user_info.get("element")
        if element:
            try:
                # 检查元素是否仍然有效
                if element.is_displayed():
                    element.click()
                    time.sleep(2)
                    logger.success(f"成功进入用户 [{user_name}] 的主页")
                    return True
            except Exception as e:
                logger.debug(f"使用保存的元素失败，将重新定位: {e}")
        
        # 如果元素不可用，重新定位用户
        user_locators = [
            {"type": "ios_predicate", "value": f"label == '{user_name}'"},
            {"type": "ios_predicate", "value": f"label CONTAINS '{user_name}'"},
            {"type": "xpath", "value": f"//XCUIElementTypeStaticText[@name='{user_name}']"},
            {"type": "xpath", "value": f"//XCUIElementTypeCell[.//XCUIElementTypeStaticText[@name='{user_name}']]"},
        ]
        
        for locator in user_locators:
            element = self.find_element(locator, timeout=3)
            if element:
                try:
                    # 如果找到的是文本元素，尝试找到其父容器（Cell）
                    if element.tag_name == "StaticText":
                        # 尝试点击父容器
                        parent = element.find_element("xpath", "..")
                        if parent:
                            parent.click()
                        else:
                            element.click()
                    else:
                        element.click()
                    time.sleep(2)
                    logger.success(f"成功进入用户 [{user_name}] 的主页")
                    return True
                except Exception as e:
                    logger.debug(f"点击元素失败: {e}")
                    continue
        
        logger.error(f"无法找到或点击用户: {user_name}")
        return False
    
    def click_works_tab(self) -> bool:
        """点击作品标签"""
        works_locators = [
            self.elements["works_tab"],
            {"type": "ios_predicate", "value": "name BEGINSWITH '作品'"},
            {"type": "ios_predicate", "value": "label BEGINSWITH '作品'"},
            {"type": "xpath", "value": "//XCUIElementTypeButton[contains(@name, '作品')]"},
        ]
        
        for locator in works_locators:
            if self.click_element(locator, timeout=3):
                time.sleep(1)
                return True
        return False
    
    def find_first_video(self):
        """找到当前屏幕上第一个可见的视频"""
        video_locators = [
            self.elements["video_item"],
            {"type": "ios_predicate", "value": "name CONTAINS '作品点赞数'"},
            {"type": "xpath", "value": "//XCUIElementTypeOther[contains(@name, '作品点赞数')]"},
        ]
        
        for locator in video_locators:
            items = self.find_elements(locator, timeout=3)
            if items:
                # 找到visible=true的元素
                for item in items:
                    try:
                        if item.is_displayed():
                            return item
                    except:
                        continue
                # 如果没有visible的，返回第一个
                return items[0]
        return None
    
    def get_user_videos(self) -> List[Dict[str, Any]]:
        """获取用户视频列表（实现抽象方法，实际使用process_user_videos）"""
        # 此方法仅为满足抽象类要求，实际逻辑在process_user_videos中
        return []
    
    def enter_video_detail(self, video_info: Dict[str, Any]) -> bool:
        """进入视频详情页（实现抽象方法，实际使用process_user_videos）"""
        # 此方法仅为满足抽象类要求，实际逻辑在process_user_videos中
        return True
    
    def _is_in_follow_list(self) -> bool:
        """检查是否在关注列表页面 - 通过实际获取列表来验证"""
        try:
            # 快速获取列表（不滚动）
            items = self.find_elements(self.elements["follow_list_item"], timeout=2)
            if not items or len(items) < 3:
                logger.debug(f"   列表项数量不足: {len(items) if items else 0}")
                return False
            
            # 检查获取到的用户是否包含有效的用户名（排除筛选按钮等）
            valid_users = []
            for item in items[:10]:  # 检查前10个
                try:
                    user_name_elements = item.find_elements("xpath", ".//XCUIElementTypeStaticText")
                    for elem in user_name_elements:
                        text = elem.text
                        if text and self._is_valid_user_name(text):
                            valid_users.append(text)
                            break
                except:
                    continue
            
            # 如果至少有3个有效用户，说明在关注列表
            if len(valid_users) >= 3:
                logger.debug(f"   检测到 {len(valid_users)} 个有效用户，在关注列表")
                return True
            else:
                logger.debug(f"   有效用户数量不足: {len(valid_users)}")
        except Exception as e:
            logger.debug(f"   检测失败: {e}")
        
        return False
    
    def click_back_button(self) -> bool:
        """点击左上角的返回按钮"""
        back_locators = [
            {"type": "accessibility_id", "value": "返回"},
            {"type": "ios_predicate", "value": "label == '返回'"},
            {"type": "ios_predicate", "value": "name == '返回'"},
            {"type": "xpath", "value": "//XCUIElementTypeButton[@name='返回']"},
            {"type": "xpath", "value": "//XCUIElementTypeNavigationBar//XCUIElementTypeButton[1]"},
            {"type": "xpath", "value": "//XCUIElementTypeButton[contains(@name,'返回') or contains(@label,'返回')]"},
            # 尝试点击导航栏最左边的按钮
            {"type": "xpath", "value": "//XCUIElementTypeNavigationBar/XCUIElementTypeButton[1]"},
        ]
        
        for locator in back_locators:
            try:
                element = self.find_element(locator, timeout=1)
                if element:
                    element.click()
                    time.sleep(1)
                    logger.debug(f"   成功点击返回按钮: {locator.get('type')}")
                    return True
            except:
                continue
        
        logger.debug("   未找到返回按钮，使用系统返回")
        return False
    
    def ensure_back_to_follow_list(self) -> bool:
        """确保返回到关注列表"""
        logger.info("正在返回到关注列表...")
        
        # 尝试点击返回按钮（通常1次就能返回）
        if self.click_back_button():
            time.sleep(2)  # 等待页面加载
            logger.success("✅ 已点击返回按钮，返回到关注列表")
            return True
        else:
            # 如果找不到返回按钮，使用系统返回
            self.go_back()
            time.sleep(2)
            logger.success("✅ 已使用系统返回，返回到关注列表")
            return True
        
        # 如果多次返回后仍不在关注列表，尝试重新进入
        logger.warning("多次返回后可能不在关注列表，尝试重新进入...")
        
        # 如果多次返回后仍不在关注列表，尝试重新进入
        logger.warning("多次返回后仍不在关注列表，尝试重新进入...")
        
        # 先尝试返回到"我的"页面（使用返回按钮）
        for back_attempt in range(5):
            if self.click_back_button():
                time.sleep(1.5)
            else:
                self.go_back()
                time.sleep(1.5)
            
            # 检查是否在"我的"页面（通过检查是否有"关注"按钮）
            if self.is_element_present(self.elements["follow_button"], timeout=2):
                logger.info(f"   已返回到'我的'页面（尝试 {back_attempt + 1} 次），重新进入关注列表...")
                if self.click_follow():
                    time.sleep(2)
                    if self._is_in_follow_list():
                        logger.success("✅ 已重新进入关注列表")
                        return True
                break
        
        # 最后尝试：完全重新导航
        logger.warning("尝试完全重新导航到关注列表...")
        if self.navigate_to_me():
            time.sleep(1)
            if self.click_follow():
                time.sleep(3)
                # 滚动到顶部
                for _ in range(3):
                    self.swipe_down(ratio=0.3)
                    time.sleep(0.5)
                if self._is_in_follow_list():
                    logger.success("✅ 已重新进入关注列表")
                    return True
        
        logger.error("❌ 无法返回到关注列表")
        return False
    
    def process_user_videos(self, on_screenshot_callback=None) -> List[Path]:
        """
        处理用户的视频：
        1. 点击作品标签
        2. 点击第一个视频进入详情页
        3. 截图底部文字描述区域
        4. 上滑到下一个视频
        5. 循环直到没有更多内容
        """
        from PIL import Image
        import io
        
        screenshots = []
        processed_count = 0
        max_videos = LIMITS["max_videos_per_user"]
        
        # 连续没有新内容的次数
        no_new_content_count = 0
        max_no_new_content = 3
        
        # 先点击作品标签
        logger.info("正在点击作品标签...")
        self.click_works_tab()
        time.sleep(2)
        
        # 点击第一个视频进入详情页
        logger.info("正在点击第一个视频...")
        first_video = self.find_first_video()
        if not first_video:
            logger.warning("没有找到视频，尝试备用定位...")
            first_video = self.find_element({
                "type": "xpath",
                "value": "//XCUIElementTypeOther[contains(@name, '作品点赞数')]"
            }, timeout=5)
        
        if not first_video:
            logger.error("无法找到任何视频")
            return screenshots
        
        try:
            first_video.click()
            logger.success("成功点击视频，进入详情页")
            time.sleep(2)  # 等待详情页加载
        except Exception as e:
            logger.error(f"点击视频失败: {e}")
            return screenshots
        
        # 获取屏幕尺寸用于计算截图区域
        window_size = self.driver.get_window_size()
        screen_width = window_size['width']
        screen_height = window_size['height']
        logger.info(f"屏幕尺寸: {screen_width}x{screen_height}")
        
        # 在详情页循环处理视频
        last_description = ""
        while processed_count < max_videos:
            try:
                logger.info(f"正在处理第 {processed_count + 1} 个视频...")
                
                # 截取全屏
                full_screenshot = self.driver.get_screenshot_as_png()
                full_image = Image.open(io.BytesIO(full_screenshot))
                img_width, img_height = full_image.size
                logger.debug(f"截图尺寸: {img_width}x{img_height}")
                
                # 计算底部文字描述区域（大约在屏幕75%-95%的位置）
                # 从用户截图来看，红框区域在底部
                scale = img_width / screen_width  # 计算实际像素比
                
                # 底部描述区域：从屏幕70%高度到90%高度（避开底部评论框）
                crop_top = int(img_height * 0.70)
                crop_bottom = int(img_height * 0.92)
                crop_left = int(img_width * 0.02)  # 左边留一点边距
                crop_right = int(img_width * 0.85)  # 右边不要包含点赞等按钮
                
                # 裁剪底部描述区域
                description_area = full_image.crop((crop_left, crop_top, crop_right, crop_bottom))
                
                # 保存截图
                timestamp = int(time.time() * 1000)
                filename = f"desc_{processed_count}_{timestamp}.png"
                filepath = SCREENSHOTS_DIR / filename
                description_area.save(filepath)
                
                logger.success(f"✅ 截取视频描述区域: {filename}")
                screenshots.append(filepath)
                
                # 回调处理OCR
                if on_screenshot_callback:
                    on_screenshot_callback(filepath)
                
                processed_count += 1
                
                # 上滑到下一个视频
                logger.info("上滑到下一个视频...")
                self.swipe_up(ratio=0.7)  # 大幅度上滑切换视频
                time.sleep(2)  # 等待视频加载
                
                # 检查是否还有新视频（通过截图对比或其他方式）
                # 简单方法：尝试获取当前视频的描述文字
                try:
                    desc_element = self.find_element({
                        "type": "xpath",
                        "value": "//XCUIElementTypeTextView | //XCUIElementTypeStaticText[string-length(@label) > 20]"
                    }, timeout=2)
                    
                    if desc_element:
                        current_desc = desc_element.get_attribute("value") or desc_element.get_attribute("label") or ""
                        if current_desc and current_desc == last_description:
                            no_new_content_count += 1
                            logger.info(f"检测到相同内容 ({no_new_content_count}/{max_no_new_content})")
                        else:
                            no_new_content_count = 0
                            last_description = current_desc
                    else:
                        no_new_content_count = 0
                except:
                    no_new_content_count = 0  # 获取失败就继续
                
                if no_new_content_count >= max_no_new_content:
                    logger.info("✅ 连续多次检测到相同内容，已到达视频列表末尾")
                    break
                    
            except Exception as e:
                logger.error(f"处理视频时出错: {e}")
                no_new_content_count += 1
                if no_new_content_count >= max_no_new_content:
                    break
                continue
        
        logger.info(f"🎉 共截取 {len(screenshots)} 个视频描述区域")
        
        # 第一次返回：从详情页返回到作品列表
        logger.info("第一次返回：从详情页返回到作品列表...")
        if self.click_back_button():
            time.sleep(2)
        else:
            self.go_back()
            time.sleep(2)
        logger.success("✅ 已返回到作品列表")
        
        # 第二次返回：从作品列表返回到关注列表（直接返回，不经过用户主页）
        logger.info("第二次返回：从作品列表返回到关注列表...")
        if self.click_back_button():
            time.sleep(2)
        else:
            self.go_back()
            time.sleep(2)
        logger.success("✅ 已返回到关注列表")
        
        return screenshots
    
    def screenshot_and_analyze(self, prefix: str = "") -> Optional[Path]:
        """截图并保存"""
        timestamp = int(time.time() * 1000)
        filename = f"{prefix}_{timestamp}.png" if prefix else f"screenshot_{timestamp}.png"
        return self.take_screenshot(filename)
    
    def _load_processed_users(self) -> set:
        """从CSV加载已处理的用户列表"""
        processed_users = set()
        try:
            import pandas as pd
            from config import DATA_DIR
            
            processed_file = DATA_DIR / "processed_users.csv"
            if processed_file.exists():
                df = pd.read_csv(processed_file)
                if 'user_name' in df.columns:
                    processed_users = set(df['user_name'].dropna().astype(str))
                    logger.info(f"从CSV加载了 {len(processed_users)} 个已处理用户")
        except Exception as e:
            logger.debug(f"加载已处理用户列表失败: {e}")
        
        return processed_users
    
    def _save_processed_user(self, user_name: str):
        """保存已处理的用户到CSV"""
        try:
            import pandas as pd
            from config import DATA_DIR
            from datetime import datetime
            
            processed_file = DATA_DIR / "processed_users.csv"
            
            new_record = {
                'user_name': user_name,
                'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if processed_file.exists():
                df = pd.read_csv(processed_file)
                # 检查是否已存在
                if user_name not in df['user_name'].values:
                    df = pd.concat([df, pd.DataFrame([new_record])], ignore_index=True)
                else:
                    # 更新处理时间
                    df.loc[df['user_name'] == user_name, 'processed_at'] = new_record['processed_at']
            else:
                df = pd.DataFrame([new_record])
            
            df.to_csv(processed_file, index=False, encoding='utf-8-sig')
            logger.debug(f"已保存用户 {user_name} 到已处理列表")
        except Exception as e:
            logger.warning(f"保存已处理用户失败: {e}")
    
    def process_all_follows(self, on_screenshot_callback=None):
        """处理所有关注用户"""
        screenshots = []
        
        if not self.open_app():
            logger.error("无法打开快手APP")
            return screenshots
        
        if not self.navigate_to_me():
            logger.error("无法导航到'我的'页面")
            return screenshots
        
        if not self.click_follow():
            logger.error("无法进入关注列表")
            return screenshots
        
        follow_list = self.get_follow_list()
        
        if not follow_list:
            logger.warning("关注列表为空")
            return screenshots
        
        # 加载已处理的用户列表
        processed_users = self._load_processed_users()
        
        # 过滤掉已处理的用户
        unprocessed_list = [u for u in follow_list if u.get('name') not in processed_users]
        
        if len(unprocessed_list) < len(follow_list):
            logger.info(f"📋 共找到 {len(follow_list)} 个关注用户，其中 {len(processed_users)} 个已处理，剩余 {len(unprocessed_list)} 个待处理")
        else:
            logger.info(f"📋 共找到 {len(follow_list)} 个关注用户，开始递归处理...")
        
        for user_idx, user_info in enumerate(unprocessed_list):
            user_name = user_info.get("name", f"用户{user_idx}")
            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"正在处理用户 {user_idx + 1}/{len(follow_list)}: {user_name}")
            logger.info(f"{'='*60}")
            
            # 如果不是第一个用户，需要先返回到关注列表
            if user_idx > 0:
                # process_user_videos 已经返回到关注列表了，只需要滚动到顶部
                logger.info("滚动到关注列表顶部...")
                for _ in range(3):
                    self.swipe_down(ratio=0.3)  # 向下滑动（向上浏览）
                    time.sleep(0.5)
                time.sleep(1)
                
                # 使用保存的索引位置直接获取用户
                saved_index = user_info.get("index", user_idx)
                logger.info(f"使用保存的索引位置 {saved_index} 重新定位用户: {user_name}")
                
                # 重新获取关注列表（从顶部开始）
                current_follows = self.get_follow_list()
                
                # 优先使用索引位置
                if saved_index < len(current_follows):
                    matching_user = current_follows[saved_index]
                    if matching_user.get("name") == user_name:
                        user_info = matching_user
                        logger.success(f"✅ 通过索引位置成功定位用户: {user_name}")
                    else:
                        # 索引位置不对，尝试按名称查找
                        logger.warning(f"索引位置用户不匹配（期望: {user_name}, 实际: {matching_user.get('name')}），尝试按名称查找...")
                        matching_user = None
                        for u in current_follows:
                            if u.get("name") == user_name:
                                matching_user = u
                                break
                        if matching_user:
                            user_info = matching_user
                            logger.success(f"✅ 通过名称成功定位用户: {user_name}")
                        else:
                            logger.warning(f"❌ 无法重新定位用户: {user_name}，跳过")
                            continue
                else:
                    # 索引超出范围，尝试按名称查找
                    logger.warning(f"索引超出范围，尝试按名称查找...")
                    matching_user = None
                    for u in current_follows:
                        if u.get("name") == user_name:
                            matching_user = u
                            break
                    if matching_user:
                        user_info = matching_user
                        logger.success(f"✅ 通过名称成功定位用户: {user_name}")
                    else:
                        logger.warning(f"❌ 无法重新定位用户: {user_name}，跳过")
                        continue
            
            # 进入用户主页
            if not self.enter_user_profile(user_info):
                logger.error(f"❌ 无法进入用户主页: {user_name}，跳过")
                continue
            
            # 处理用户视频
            logger.info(f"开始处理用户 [{user_name}] 的视频...")
            user_screenshots = self.process_user_videos(on_screenshot_callback)
            screenshots.extend(user_screenshots)
            logger.success(f"✅ 用户 [{user_name}] 处理完成，共截取 {len(user_screenshots)} 张截图")
            
            # 保存已处理的用户
            self._save_processed_user(user_name)
            
            # process_user_videos 已经返回到了关注列表，不需要再次返回
            # 只需要等待页面稳定即可
            if user_idx < len(unprocessed_list) - 1:  # 不是最后一个用户
                logger.info("")
                logger.info("准备处理下一个用户...")
                time.sleep(1)  # 等待页面稳定
        
        logger.info("")
        logger.success(f"{'='*60}")
        logger.success(f"🎉 所有用户处理完成！共截取 {len(screenshots)} 张截图")
        logger.success(f"   已处理用户数: {len(unprocessed_list)}")
        logger.success(f"   已跳过用户数: {len(processed_users)}")
        logger.success(f"{'='*60}")
        return screenshots
    
    def close(self):
        """关闭自动化连接"""
        self.disconnect()
