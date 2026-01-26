#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简单的测试：只测试返回关注列表功能
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def test_simple():
    """最简单的测试"""
    logger.info("=" * 60)
    logger.info("简单测试：返回关注列表")
    logger.info("=" * 60)
    
    automation = None
    try:
        automation = KuaishouiOS()
        
        if not automation.connect():
            logger.error("❌ 连接失败")
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
            logger.error("❌ 打开APP失败")
            return False
        
        # 导航到我的页面
        if not automation.navigate_to_me():
            logger.error("❌ 导航失败")
            return False
        
        # 点击关注
        if not automation.click_follow():
            logger.error("❌ 点击关注失败")
            return False
        
        # 获取关注列表
        follow_list = automation.get_follow_list()
        if len(follow_list) < 2:
            logger.error(f"❌ 关注列表用户太少: {len(follow_list)}")
            return False
        
        logger.info(f"✅ 获取到 {len(follow_list)} 个用户")
        logger.info(f"   用户1: {follow_list[0].get('name')}")
        logger.info(f"   用户2: {follow_list[1].get('name')}")
        
        # 测试1: 进入第一个用户
        logger.info("\n测试1: 进入第一个用户...")
        if not automation.enter_user_profile(follow_list[0]):
            logger.error("❌ 进入用户1失败")
            return False
        logger.success("✅ 已进入用户1主页")
        time.sleep(2)
        
        # 测试2: 返回关注列表
        logger.info("\n测试2: 返回关注列表...")
        if not automation.ensure_back_to_follow_list():
            logger.error("❌ 返回关注列表失败")
            return False
        logger.success("✅ 已返回关注列表")
        time.sleep(2)
        
        # 测试3: 重新获取列表，检查是否能找到用户2
        logger.info("\n测试3: 重新获取关注列表...")
        current_list = automation.get_follow_list()
        logger.info(f"   当前列表有 {len(current_list)} 个用户")
        
        user2_name = follow_list[1].get('name')
        found = False
        for u in current_list:
            if u.get('name') == user2_name:
                found = True
                logger.success(f"✅ 找到用户2: {user2_name}")
                break
        
        if not found:
            logger.warning(f"⚠️  未找到用户2: {user2_name}")
            logger.info("   当前列表中的用户:")
            for i, u in enumerate(current_list[:5]):
                logger.info(f"     {i+1}. {u.get('name')}")
        
        # 测试4: 尝试进入用户2
        if found:
            logger.info("\n测试4: 进入用户2...")
            for u in current_list:
                if u.get('name') == user2_name:
                    if automation.enter_user_profile(u):
                        logger.success("✅ 成功进入用户2主页")
                        break
        
        logger.success("\n✅ 测试完成")
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
    test_simple()
