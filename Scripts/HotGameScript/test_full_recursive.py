#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整递归流程测试：详情 -> 作品列表 -> 关注列表 -> 下一个用户 -> 详情
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def test():
    logger.info("=" * 60)
    logger.info("完整递归流程测试")
    logger.info("=" * 60)
    
    automation = None
    try:
        automation = KuaishouiOS()
        
        if not automation.connect():
            return False
        
        # 关闭APP
        try:
            bundle_id = automation.capabilities.get("bundleId", "com.jiangjia.gif")
            automation.driver.terminate_app(bundle_id)
            time.sleep(2)
        except:
            pass
        
        # 打开APP
        if not automation.open_app():
            return False
        
        # 导航到我的页面
        if not automation.navigate_to_me():
            return False
        
        # 点击关注
        if not automation.click_follow():
            return False
        
        # 获取关注列表
        follow_list = automation.get_follow_list()
        if len(follow_list) < 2:
            logger.error("关注列表用户少于2个，无法测试")
            return False
        
        logger.info(f"获取到 {len(follow_list)} 个用户")
        logger.info(f"用户1: {follow_list[0].get('name')}")
        logger.info(f"用户2: {follow_list[1].get('name')}")
        
        # ========== 处理第一个用户 ==========
        user1 = follow_list[0]
        user1_name = user1.get('name')
        logger.info(f"\n{'='*60}")
        logger.info(f"处理用户1: {user1_name}")
        logger.info(f"{'='*60}")
        
        # 进入用户1主页
        if not automation.enter_user_profile(user1):
            return False
        logger.success("✅ 已进入用户1主页")
        
        # 点击作品标签
        automation.click_works_tab()
        time.sleep(2)
        logger.success("✅ 已点击作品标签")
        
        # 点击第一个视频进入详情页
        first_video = automation.find_first_video()
        if not first_video:
            logger.error("未找到视频")
            return False
        
        first_video.click()
        time.sleep(2)
        logger.success("✅ 已进入用户1的视频详情页")
        
        # 第一次返回：详情页 -> 作品列表
        logger.info("\n第一次返回：详情页 -> 作品列表")
        if automation.click_back_button():
            time.sleep(2)
        else:
            automation.go_back()
            time.sleep(2)
        logger.success("✅ 已返回到作品列表")
        
        # 第二次返回：作品列表 -> 关注列表
        logger.info("第二次返回：作品列表 -> 关注列表")
        if automation.click_back_button():
            time.sleep(2)
        else:
            automation.go_back()
            time.sleep(2)
        logger.success("✅ 已返回到关注列表")
        
        # 验证是否在关注列表
        try:
            items = automation.find_elements(automation.elements["follow_list_item"], timeout=3)
            if items and len(items) > 0:
                logger.success(f"✅ 确认在关注列表（找到 {len(items)} 个列表项）")
            else:
                logger.error("❌ 未找到关注列表项")
                return False
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False
        
        # ========== 处理第二个用户 ==========
        user2 = follow_list[1]
        user2_name = user2.get('name')
        logger.info(f"\n{'='*60}")
        logger.info(f"处理用户2: {user2_name}")
        logger.info(f"{'='*60}")
        
        # 重新获取关注列表并定位用户2
        logger.info("重新定位用户2...")
        current_follows = automation.get_follow_list()
        matching_user = None
        
        for u in current_follows:
            if u.get("name") == user2_name:
                matching_user = u
                break
        
        if not matching_user:
            logger.warning("无法找到用户2，尝试滚动查找...")
            scroll_attempts = 0
            while scroll_attempts < 3 and not matching_user:
                automation.swipe_up(ratio=0.3)
                time.sleep(1)
                current_follows = automation.get_follow_list()
                for u in current_follows:
                    if u.get("name") == user2_name:
                        matching_user = u
                        break
                scroll_attempts += 1
        
        if not matching_user:
            logger.error(f"❌ 无法找到用户2: {user2_name}")
            return False
        
        logger.success(f"✅ 成功定位用户2: {user2_name}")
        
        # 进入用户2主页
        if not automation.enter_user_profile(matching_user):
            return False
        logger.success("✅ 已进入用户2主页")
        
        # 点击作品标签
        automation.click_works_tab()
        time.sleep(2)
        logger.success("✅ 已点击作品标签")
        
        # 点击第一个视频进入详情页
        first_video = automation.find_first_video()
        if not first_video:
            logger.error("未找到视频")
            return False
        
        first_video.click()
        time.sleep(2)
        logger.success("✅ 已进入用户2的视频详情页")
        
        logger.success("\n✅ 完整递归流程测试成功！")
        logger.success("   - 用户1：详情页 -> 作品列表 -> 关注列表")
        logger.success("   - 用户2：关注列表 -> 用户主页 -> 作品列表 -> 详情页")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        if automation:
            automation.close()

if __name__ == "__main__":
    test()
