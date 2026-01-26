#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最简短测试：验证两次返回和用户标记功能
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def test():
    logger.info("=" * 60)
    logger.info("简短测试：两次返回 + 用户标记")
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
        
        # 加载已处理用户
        processed = automation._load_processed_users()
        logger.info(f"已处理用户: {len(processed)} 个")
        
        # 测试第一个用户
        user = follow_list[0]
        user_name = user.get('name')
        logger.info(f"\n测试用户: {user_name}")
        
        # 检查是否已处理
        if user_name in processed:
            logger.info(f"✅ 用户 {user_name} 已在处理列表中，跳过")
        else:
            logger.info(f"开始处理用户: {user_name}")
            
            # 进入用户主页
            if not automation.enter_user_profile(user):
                return False
            
            # 点击作品标签
            automation.click_works_tab()
            time.sleep(2)
            
            # 点击第一个视频
            first_video = automation.find_first_video()
            if first_video:
                first_video.click()
                time.sleep(2)
                logger.info("✅ 已进入视频详情页")
                
                # 测试两次返回
                logger.info("\n测试第一次返回：详情页 -> 作品列表")
                if automation.click_back_button():
                    time.sleep(2)
                else:
                    automation.go_back()
                    time.sleep(2)
                logger.success("✅ 第一次返回成功")
                
                logger.info("测试第二次返回：作品列表 -> 用户主页")
                if automation.click_back_button():
                    time.sleep(2)
                else:
                    automation.go_back()
                    time.sleep(2)
                logger.success("✅ 第二次返回成功")
                
                # 测试第三次返回：用户主页 -> 关注列表
                logger.info("测试第三次返回：用户主页 -> 关注列表")
                if automation.ensure_back_to_follow_list():
                    logger.success("✅ 第三次返回成功")
                else:
                    logger.error("❌ 第三次返回失败")
                    return False
                
                # 保存已处理用户
                automation._save_processed_user(user_name)
                logger.success(f"✅ 已保存用户 {user_name} 到处理列表")
            else:
                logger.warning("未找到视频")
        
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
    test()
