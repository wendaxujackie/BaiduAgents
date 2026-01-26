#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试递归点击用户功能
"""
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def test_recursive_users():
    """测试递归点击用户功能"""
    logger.info("=" * 60)
    logger.info("测试递归点击用户功能")
    logger.info("=" * 60)
    
    automation = None
    try:
        # 初始化自动化
        logger.info("\n1. 初始化自动化连接...")
        automation = KuaishouiOS()
        
        # 连接设备
        if not automation.connect():
            logger.error("❌ 连接设备失败")
            return False
        
        # 关闭APP（如果正在运行）
        logger.info("\n2. 关闭APP（如果正在运行）...")
        try:
            bundle_id = automation.capabilities.get("bundleId", "com.jiangjia.gif")
            automation.driver.terminate_app(bundle_id)
            time.sleep(2)
            logger.success("✅ 已关闭APP")
        except Exception as e:
            logger.debug(f"   关闭APP失败（可能未运行）: {e}")
        
        # 打开APP
        logger.info("\n3. 打开APP...")
        if not automation.open_app():
            logger.error("❌ 打开APP失败")
            return False
        logger.success("✅ 打开APP成功")
        
        # 导航到"我的"页面
        logger.info("\n4. 导航到'我的'页面...")
        if not automation.navigate_to_me():
            logger.error("❌ 导航到'我的'页面失败")
            return False
        logger.success("✅ 导航到'我的'页面成功")
        
        # 点击关注按钮
        logger.info("\n5. 点击关注按钮...")
        if not automation.click_follow():
            logger.error("❌ 点击关注按钮失败")
            return False
        logger.success("✅ 点击关注按钮成功，已进入关注列表")
        
        # 获取关注列表
        logger.info("\n6. 获取关注列表...")
        follow_list = automation.get_follow_list()
        if not follow_list:
            logger.warning("⚠️  关注列表为空")
            return False
        
        logger.success(f"✅ 成功获取关注列表，共 {len(follow_list)} 个用户")
        for i, user in enumerate(follow_list[:10]):  # 显示前10个
            logger.info(f"   {i+1}. {user.get('name', '未知用户')}")
        
        if len(follow_list) > 10:
            logger.info(f"   ... 还有 {len(follow_list) - 10} 个用户")
        
        # 测试递归点击用户（测试前3个用户）
        logger.info("\n7. 测试递归点击用户（测试前3个用户）...")
        test_users = follow_list[:3] if len(follow_list) >= 3 else follow_list
        
        for user_idx, user_info in enumerate(test_users):
            user_name = user_info.get("name", f"用户{user_idx}")
            logger.info("")
            logger.info(f"{'='*60}")
            logger.info(f"处理用户 {user_idx + 1}/{len(test_users)}: {user_name}")
            logger.info(f"{'='*60}")
            
            # 如果不是第一个用户，先返回关注列表
            if user_idx > 0:
                logger.info("返回到关注列表...")
                if not automation.ensure_back_to_follow_list():
                    logger.error("❌ 无法返回到关注列表")
                    break
                logger.success("✅ 已返回到关注列表")
                
                # 重新定位用户
                logger.info("重新定位用户...")
                current_follows = automation.get_follow_list()
                matching_user = None
                
                # 尝试找到匹配的用户
                for u in current_follows:
                    if u.get("name") == user_name:
                        matching_user = u
                        break
                
                if not matching_user:
                    logger.warning(f"⚠️  无法重新定位用户: {user_name}，尝试滚动查找...")
                    # 尝试向下滚动查找用户
                    scroll_attempts = 0
                    while scroll_attempts < 3 and not matching_user:
                        automation.swipe_up(ratio=0.3)
                        time.sleep(1)
                        current_follows = automation.get_follow_list()
                        for u in current_follows:
                            if u.get("name") == user_name:
                                matching_user = u
                                break
                        scroll_attempts += 1
                
                if not matching_user:
                    logger.warning(f"❌ 无法重新定位用户: {user_name}，跳过")
                    continue
                    
                user_info = matching_user
                logger.success(f"✅ 成功定位用户: {user_name}")
            
            # 进入用户主页
            logger.info("进入用户主页...")
            if not automation.enter_user_profile(user_info):
                logger.error("❌ 无法进入用户主页")
                continue
            logger.success("✅ 成功进入用户主页")
            
            # 测试点击作品标签
            logger.info("点击作品标签...")
            if automation.click_works_tab():
                logger.success("✅ 成功点击作品标签")
                time.sleep(1)
                
                # 返回用户主页
                automation.go_back()
                time.sleep(1)
            else:
                logger.warning("⚠️  无法点击作品标签")
            
            # 返回关注列表
            logger.info("返回到关注列表...")
            if automation.ensure_back_to_follow_list():
                logger.success("✅ 成功返回到关注列表，准备处理下一个用户")
            else:
                logger.error("❌ 无法返回到关注列表")
                break
        
        logger.success("\n" + "=" * 60)
        logger.success("✅ 递归用户测试完成！")
        logger.success("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试过程中出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        if automation:
            logger.info("\n关闭自动化连接...")
            automation.close()

if __name__ == "__main__":
    test_recursive_users()
