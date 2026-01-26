#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简短测试：验证两次返回（详情页 -> 作品列表 -> 关注列表）
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def test():
    logger.info("=" * 60)
    logger.info("测试：两次返回操作")
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
        if len(follow_list) < 1:
            logger.error("关注列表为空")
            return False
        
        user = follow_list[0]
        user_name = user.get('name')
        logger.info(f"\n测试用户: {user_name}")
        
        # 进入用户主页
        if not automation.enter_user_profile(user):
            return False
        logger.success("✅ 已进入用户主页")
        
        # 点击作品标签
        automation.click_works_tab()
        time.sleep(2)
        logger.success("✅ 已点击作品标签")
        
        # 点击第一个视频
        first_video = automation.find_first_video()
        if not first_video:
            logger.error("未找到视频")
            return False
        
        first_video.click()
        time.sleep(2)
        logger.success("✅ 已进入视频详情页")
        
        # 第一次返回：详情页 -> 作品列表
        logger.info("\n第一次返回：详情页 -> 作品列表")
        if automation.click_back_button():
            time.sleep(2)
        else:
            automation.go_back()
            time.sleep(2)
        logger.success("✅ 第一次返回成功")
        
        # 验证是否在作品列表（检查是否有作品标签或视频）
        try:
            items = automation.find_elements(automation.elements["video_item"], timeout=2)
            if items:
                logger.success("✅ 确认在作品列表（找到视频项）")
        except:
            logger.warning("⚠️  无法确认是否在作品列表")
        
        # 第二次返回：作品列表 -> 关注列表
        logger.info("\n第二次返回：作品列表 -> 关注列表")
        if automation.click_back_button():
            time.sleep(2)
        else:
            automation.go_back()
            time.sleep(2)
        logger.success("✅ 第二次返回成功")
        
        # 验证是否在关注列表
        logger.info("\n验证是否在关注列表...")
        try:
            items = automation.find_elements(automation.elements["follow_list_item"], timeout=3)
            if items and len(items) > 0:
                logger.success(f"✅ 确认在关注列表（找到 {len(items)} 个列表项）")
            else:
                logger.error("❌ 未找到关注列表项，可能不在关注列表")
                return False
        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False
        
        logger.success("\n✅ 测试完成：两次返回操作正确！")
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
