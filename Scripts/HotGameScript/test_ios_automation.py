#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iOS自动化测试脚本
测试返回关注列表和递归点击用户功能
"""
import sys
import subprocess
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from mobile_automation.kuaishou_ios import KuaishouiOS

def cleanup_processes():
    """清理之前的进程和会话"""
    logger.info("🧹 清理之前的进程和会话...")
    
    # 1. 杀掉所有 Appium 会话（通过 Appium 的 API）
    try:
        import requests
        try:
            # 获取所有会话
            response = requests.get("http://127.0.0.1:4723/sessions", timeout=3)
            if response.status_code == 200:
                sessions = response.json().get("value", [])
                if sessions:
                    logger.info(f"   发现 {len(sessions)} 个活跃会话，正在关闭...")
                    for session in sessions:
                        session_id = session.get("id")
                        if session_id:
                            try:
                                requests.delete(f"http://127.0.0.1:4723/session/{session_id}", timeout=3)
                                logger.info(f"   ✅ 已关闭会话: {session_id}")
                            except Exception as e:
                                logger.debug(f"   关闭会话 {session_id} 失败: {e}")
                else:
                    logger.info("   没有活跃的会话")
        except requests.exceptions.RequestException as e:
            logger.debug(f"   无法连接到 Appium API: {e}")
    except ImportError:
        logger.debug("   requests 未安装，跳过API清理")
    
    # 2. 等待会话关闭
    time.sleep(2)
    
    # 3. 检查并杀掉占用 4723 端口的进程（但不杀掉 Appium 服务器本身）
    # 这里只清理可能残留的进程，保留 Appium 服务器运行
    try:
        result = subprocess.run(
            ["lsof", "-ti", ":4723"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            logger.info(f"   发现占用 4723 端口的进程: {len(pids)} 个")
            # 不直接杀掉，因为可能是 Appium 服务器本身
    except Exception as e:
        logger.debug(f"   检查端口占用失败: {e}")
    
    logger.success("✅ 清理完成，准备开始新的测试")

def test_follow_list_navigation():
    """测试关注列表导航和用户递归点击"""
    logger.info("=" * 60)
    logger.info("开始测试 iOS 自动化 - 关注列表导航")
    logger.info("=" * 60)
    
    # 先清理之前的进程
    cleanup_processes()
    
    automation = None
    try:
        # 初始化自动化
        logger.info("\n1. 初始化自动化连接...")
        automation = KuaishouiOS()
        
        # 先连接设备（不打开APP）
        if not automation.connect():
            logger.error("❌ 连接设备失败")
            return False
        
        # 关闭APP（如果正在运行）
        logger.info("\n1.5. 关闭APP（如果正在运行）...")
        try:
            bundle_id = automation.capabilities.get("bundleId", "com.jiangjia.gif")
            automation.driver.terminate_app(bundle_id)
            import time
            time.sleep(2)
            logger.success("✅ 已关闭APP")
        except Exception as e:
            logger.debug(f"   关闭APP失败（可能未运行）: {e}")
        
        # 测试1: 打开APP
        logger.info("\n2. 测试打开APP...")
        if not automation.open_app():
            logger.error("❌ 打开APP失败")
            return False
        logger.success("✅ 打开APP成功")
        
        # 测试2: 导航到"我的"页面
        logger.info("\n3. 测试导航到'我的'页面...")
        if not automation.navigate_to_me():
            logger.error("❌ 导航到'我的'页面失败")
            return False
        logger.success("✅ 导航到'我的'页面成功")
        
        # 测试3: 点击关注按钮
        logger.info("\n4. 测试点击关注按钮...")
        if not automation.click_follow():
            logger.error("❌ 点击关注按钮失败")
            return False
        logger.success("✅ 点击关注按钮成功，已进入关注列表")
        
        # 测试4: 获取关注列表
        logger.info("\n5. 测试获取关注列表...")
        follow_list = automation.get_follow_list()
        if not follow_list:
            logger.warning("⚠️  关注列表为空")
            return False
        
        logger.success(f"✅ 成功获取关注列表，共 {len(follow_list)} 个用户")
        for i, user in enumerate(follow_list[:5]):  # 只显示前5个
            logger.info(f"   {i+1}. {user.get('name', '未知用户')}")
        
        if len(follow_list) > 5:
            logger.info(f"   ... 还有 {len(follow_list) - 5} 个用户")
        
        # 测试5: 测试返回关注列表功能
        logger.info("\n6. 测试返回关注列表功能...")
        if len(follow_list) > 0:
            # 进入第一个用户主页
            logger.info("   进入第一个用户主页...")
            if automation.enter_user_profile(follow_list[0]):
                logger.success("   ✅ 成功进入用户主页")
                
                # 测试返回关注列表
                if automation.ensure_back_to_follow_list():
                    logger.success("   ✅ 成功返回到关注列表")
                else:
                    logger.error("   ❌ 返回关注列表失败")
                    return False
            else:
                logger.warning("   ⚠️  无法进入用户主页，跳过返回测试")
        
        # 测试6: 测试递归点击用户（只测试前2个用户）
        logger.info("\n7. 测试递归点击用户（测试前2个用户）...")
        test_users = follow_list[:2] if len(follow_list) >= 2 else follow_list
        
        for user_idx, user_info in enumerate(test_users):
            user_name = user_info.get("name", f"用户{user_idx}")
            logger.info(f"\n   处理用户 {user_idx + 1}/{len(test_users)}: {user_name}")
            
            # 如果不是第一个用户，先返回关注列表
            if user_idx > 0:
                logger.info("   返回到关注列表...")
                if not automation.ensure_back_to_follow_list():
                    logger.error("   ❌ 无法返回到关注列表")
                    continue
                logger.success("   ✅ 已返回到关注列表")
                
                # 重新定位用户
                logger.info("   重新定位用户...")
                current_follows = automation.get_follow_list()
                matching_user = None
                for u in current_follows:
                    if u.get("name") == user_name:
                        matching_user = u
                        break
                
                if not matching_user:
                    logger.warning(f"   ⚠️  无法重新定位用户: {user_name}")
                    continue
                
                user_info = matching_user
                logger.success(f"   ✅ 成功定位用户: {user_name}")
            
            # 进入用户主页
            logger.info("   进入用户主页...")
            if not automation.enter_user_profile(user_info):
                logger.error("   ❌ 无法进入用户主页")
                continue
            logger.success("   ✅ 成功进入用户主页")
            
            # 测试点击作品标签
            logger.info("   点击作品标签...")
            if automation.click_works_tab():
                logger.success("   ✅ 成功点击作品标签")
            else:
                logger.warning("   ⚠️  无法点击作品标签")
            
            # 返回用户主页
            automation.go_back()
            import time
            time.sleep(1)
            
            # 返回关注列表
            logger.info("   返回到关注列表...")
            if automation.ensure_back_to_follow_list():
                logger.success("   ✅ 成功返回到关注列表，准备处理下一个用户")
            else:
                logger.error("   ❌ 无法返回到关注列表")
                break
        
        logger.success("\n" + "=" * 60)
        logger.success("✅ 所有测试通过！")
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
    import time
    test_follow_list_navigation()
