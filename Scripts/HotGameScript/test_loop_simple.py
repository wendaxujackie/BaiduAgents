#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简短循环测试：验证完整的递归流程
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def test():
    logger.info("=" * 60)
    logger.info("简短循环测试：完整递归流程")
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
            logger.error("关注列表用户少于2个")
            return False
        
        logger.info(f"获取到 {len(follow_list)} 个用户")
        
        # ========== 循环处理前2个用户 ==========
        for i in range(2):
            user = follow_list[i]
            user_name = user.get('name', f'用户{i}')
            logger.info(f"\n{'='*60}")
            logger.info(f"处理用户 {i+1}/2: {user_name}")
            logger.info(f"{'='*60}")
            
            # 如果不是第一个用户，需要先返回到关注列表
            if i > 0:
                logger.info("返回到关注列表...")
                # 滚动到顶部
                for _ in range(3):
                    automation.swipe_down(ratio=0.3)
                    time.sleep(0.5)
                time.sleep(1)
                
                # 使用索引位置定位用户
                saved_index = user.get("index", i)
                logger.info(f"使用索引位置 {saved_index} 重新定位用户...")
                current_follows = automation.get_follow_list()
                
                if saved_index < len(current_follows):
                    matching_user = current_follows[saved_index]
                    if matching_user.get("name") == user_name:
                        user = matching_user
                        logger.success(f"✅ 通过索引成功定位用户: {user_name}")
                    else:
                        logger.warning("索引位置用户不匹配，尝试按名称查找...")
                        for u in current_follows:
                            if u.get("name") == user_name:
                                user = u
                                logger.success(f"✅ 通过名称成功定位用户: {user_name}")
                                break
                else:
                    logger.error(f"索引超出范围: {saved_index}")
                    continue
            
            # 进入用户主页
            logger.info("进入用户主页...")
            if not automation.enter_user_profile(user):
                logger.error("进入用户主页失败")
                continue
            logger.success("✅ 已进入用户主页")
            
            # 点击作品标签
            automation.click_works_tab()
            time.sleep(2)
            logger.success("✅ 已点击作品标签")
            
            # 点击第一个视频
            first_video = automation.find_first_video()
            if not first_video:
                logger.warning("未找到视频，跳过")
                # 返回关注列表
                automation.go_back()
                time.sleep(1)
                automation.go_back()
                time.sleep(1)
                continue
            
            first_video.click()
            time.sleep(2)
            logger.success("✅ 已进入视频详情页")
            
            # 第一次返回：详情页 -> 作品列表
            logger.info("第一次返回：详情页 -> 作品列表")
            if automation.click_back_button():
                time.sleep(2)
            else:
                automation.go_back()
                time.sleep(2)
            logger.success("✅ 第一次返回成功")
            
            # 第二次返回：作品列表 -> 关注列表
            logger.info("第二次返回：作品列表 -> 关注列表")
            if automation.click_back_button():
                time.sleep(2)
            else:
                automation.go_back()
                time.sleep(2)
            logger.success("✅ 第二次返回成功")
            
            # 验证是否在关注列表
            try:
                items = automation.find_elements(automation.elements["follow_list_item"], timeout=3)
                if items and len(items) > 0:
                    logger.success(f"✅ 确认在关注列表（找到 {len(items)} 个列表项）")
                else:
                    logger.error("❌ 未找到关注列表项")
                    break
            except:
                logger.warning("⚠️  无法验证是否在关注列表，继续...")
        
        logger.success("\n✅ 循环测试完成！")
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
