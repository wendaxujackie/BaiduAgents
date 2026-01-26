#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快手游戏APK自动化采集工具 - 主程序入口

功能流程：
1. 打开快手APP
2. 跳转到"我的"页面
3. 点击关注，查看关注列表
4. 递归访问关注用户，截取视频截图
5. 使用OCR识别游戏名称，保存到CSV
6. 使用Chrome搜索游戏，分析下载链接
7. 下载APK并按热词规则重命名

使用方法：
    python main.py --platform android  # Android端执行
    python main.py --platform ios      # iOS端执行
    python main.py --mode search       # 仅搜索模式
    python main.py --mode download     # 仅下载模式
"""
import argparse
import sys
import subprocess
import time
from pathlib import Path
from typing import Optional

from loguru import logger

# 配置日志
from config import LOG_CONFIG, BASE_DIR, GAMES_CSV_PATH

# 配置loguru
logger.remove()
logger.add(
    sys.stdout,
    format=LOG_CONFIG["format"],
    level=LOG_CONFIG["level"]
)
logger.add(
    BASE_DIR / "logs" / "app.log",
    format=LOG_CONFIG["format"],
    level=LOG_CONFIG["level"],
    rotation=LOG_CONFIG["rotation"],
    retention=LOG_CONFIG["retention"]
)


def cleanup_processes(platform: str = "android"):
    """清理之前的进程和会话，并关闭APP"""
    logger.info("🧹 清理之前的进程和会话...")
    
    # 1. 先尝试连接设备并关闭APP
    try:
        if platform == "android":
            from mobile_automation import KuaishouAndroid as TempApp
        else:
            from mobile_automation import KuaishouiOS as TempApp
        
        temp_app = TempApp()
        if temp_app.connect():
            logger.info("   正在关闭APP...")
            try:
                if platform == "ios":
                    bundle_id = temp_app.capabilities.get("bundleId", "com.jiangjia.gif")
                    temp_app.driver.terminate_app(bundle_id)
                else:
                    package_name = temp_app.capabilities.get("appPackage", "com.smile.gifmaker")
                    temp_app.driver.terminate_app(package_name)
                time.sleep(1)
                logger.success("   ✅ 已关闭APP")
            except Exception as e:
                logger.debug(f"   关闭APP失败（可能未运行）: {e}")
            finally:
                temp_app.disconnect()
    except Exception as e:
        logger.debug(f"   无法连接设备关闭APP: {e}")
    
    # 2. 杀掉所有 Appium 会话（通过 Appium 的 API）
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
                    logger.debug("   没有活跃的会话")
        except requests.exceptions.RequestException as e:
            logger.debug(f"   无法连接到 Appium API: {e}")
    except ImportError:
        logger.debug("   requests 未安装，跳过API清理")
    
    # 3. 等待会话关闭
    time.sleep(2)
    
    logger.success("✅ 清理完成，准备开始新的自动化流程")


def run_mobile_automation(platform: str = "android") -> bool:
    """
    运行移动端自动化流程
    
    Args:
        platform: 平台 ('android' 或 'ios')
        
    Returns:
        是否成功
    """
    logger.info(f"===== 开始{platform.upper()}端自动化流程 =====")
    
    # 先清理之前的进程和会话，并关闭APP
    cleanup_processes(platform)
    
    # 导入相应的自动化类
    if platform == "android":
        from mobile_automation import KuaishouAndroid as KuaishouApp
    else:
        from mobile_automation import KuaishouiOS as KuaishouApp
    
    # 导入OCR模块
    from ocr_processor import GameRecognizer
    
    # 初始化
    app = KuaishouApp()
    recognizer = GameRecognizer()
    
    # 收集所有截图的处理结果
    all_results = []
    
    # OCR回调函数
    def on_screenshot(screenshot_path: Path):
        """截图后的回调函数"""
        result = recognizer.process_screenshot(screenshot_path)
        all_results.append(result)
        # 实时保存（每次处理后都保存，防止数据丢失）
        recognizer.save_to_csv(all_results)
    
    try:
        # 执行自动化流程
        screenshots = app.process_all_follows(on_screenshot_callback=on_screenshot)
        
        logger.success(f"移动端自动化完成，共处理 {len(screenshots)} 张截图")
        
        # 保存最终结果（包含所有OCR原始文本）
        if all_results:
            recognizer.save_to_csv(all_results)
            logger.info(f"CSV已保存 {len(all_results)} 条记录，每条包含原始OCR文本分列")
        
        return True
        
    except Exception as e:
        logger.error(f"移动端自动化失败: {e}")
        return False
        
    finally:
        app.close()


def run_search_mode() -> bool:
    """
    运行搜索模式
    从CSV读取游戏名称并搜索下载链接
    
    Returns:
        是否成功
    """
    logger.info("===== 开始游戏搜索流程 =====")
    
    from utils import CSVHandler
    from web_automation import GameSearcher
    
    # 读取游戏名称
    csv_handler = CSVHandler()
    game_names = csv_handler.read_game_names()
    
    if not game_names:
        logger.warning("没有找到游戏数据，请先运行移动端自动化流程")
        return False
    
    logger.info(f"从CSV读取到 {len(game_names)} 个游戏")
    
    # 初始化搜索器
    searcher = GameSearcher(use_debug_mode=True)
    
    try:
        # 连接Chrome
        if not searcher.connect():
            logger.error("请先启动Chrome调试模式")
            logger.info("启动命令示例:")
            logger.info("  Windows: chrome.exe --remote-debugging-port=9222")
            logger.info("  Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
            return False
        
        # 搜索每个游戏
        all_results = {}
        
        for game_name in game_names:
            logger.info(f"搜索游戏: {game_name}")
            results = searcher.get_best_download_links(game_name)
            
            if results:
                all_results[game_name] = results
                
                # 显示搜索结果
                for idx, result in enumerate(results[:3], 1):
                    logger.info(f"  [{idx}] {result['title'][:50]}...")
                    logger.info(f"      URL: {result['url'][:80]}...")
                    logger.info(f"      评分: {result.get('download_score', 0)}")
        
        # 保存搜索结果
        import json
        results_path = BASE_DIR / "data" / "search_results.json"
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        logger.success(f"搜索结果已保存到: {results_path}")
        return True
        
    except Exception as e:
        logger.error(f"搜索流程失败: {e}")
        return False
        
    finally:
        searcher.disconnect()


def run_download_mode() -> bool:
    """
    运行下载模式
    从搜索结果中下载APK并生成热词副本
    
    Returns:
        是否成功
    """
    logger.info("===== 开始APK下载流程 =====")
    
    import json
    from web_automation import APKDownloader
    
    # 读取搜索结果
    results_path = BASE_DIR / "data" / "search_results.json"
    
    if not results_path.exists():
        logger.error("搜索结果文件不存在，请先运行搜索模式")
        return False
    
    try:
        with open(results_path, 'r', encoding='utf-8') as f:
            search_results = json.load(f)
    except Exception as e:
        logger.error(f"读取搜索结果失败: {e}")
        return False
    
    if not search_results:
        logger.warning("搜索结果为空")
        return False
    
    logger.info(f"准备下载 {len(search_results)} 个游戏")
    
    # 初始化下载器
    downloader = APKDownloader()
    
    try:
        # 处理下载
        results = downloader.process_multiple_games(search_results)
        
        # 显示汇总
        summary = downloader.get_summary(results)
        
        logger.info("===== 下载汇总 =====")
        logger.info(f"总游戏数: {summary['total_games']}")
        logger.info(f"成功: {summary['success_count']}")
        logger.info(f"失败: {summary['failed_count']}")
        logger.info(f"生成副本总数: {summary['total_copies']}")
        logger.info(f"目标文件夹: {summary['target_folder']}")
        
        # 保存下载报告
        report_path = BASE_DIR / "data" / "download_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.success(f"下载报告已保存到: {report_path}")
        return True
        
    except Exception as e:
        logger.error(f"下载流程失败: {e}")
        return False


def run_full_pipeline(platform: str = "android") -> bool:
    """
    运行完整流程
    
    Args:
        platform: 移动端平台
        
    Returns:
        是否成功
    """
    logger.info("===== 开始完整自动化流程 =====")
    
    # 步骤1: 移动端自动化
    logger.info(">>> 步骤1: 移动端自动化（快手APP）")
    if not run_mobile_automation(platform):
        logger.warning("移动端自动化未完全成功，继续后续流程...")
    
    # 步骤2: 游戏搜索
    logger.info(">>> 步骤2: 游戏搜索")
    if not run_search_mode():
        logger.warning("游戏搜索未完全成功，继续后续流程...")
    
    # 步骤3: APK下载
    logger.info(">>> 步骤3: APK下载与重命名")
    if not run_download_mode():
        logger.warning("APK下载未完全成功")
    
    logger.success("===== 完整流程执行完毕 =====")
    return True


def run_ocr_only(image_dir: str = None) -> bool:
    """
    仅运行OCR识别模式
    
    Args:
        image_dir: 图片目录
        
    Returns:
        是否成功
    """
    logger.info("===== 开始OCR识别流程 =====")
    
    from ocr_processor import GameRecognizer
    from config import SCREENSHOTS_DIR
    
    # 确定图片目录
    if image_dir:
        screenshots_path = Path(image_dir)
    else:
        screenshots_path = SCREENSHOTS_DIR
    
    if not screenshots_path.exists():
        logger.error(f"图片目录不存在: {screenshots_path}")
        return False
    
    # 获取所有图片
    image_files = list(screenshots_path.glob("*.png")) + list(screenshots_path.glob("*.jpg"))
    
    if not image_files:
        logger.warning(f"目录中没有图片文件: {screenshots_path}")
        return False
    
    logger.info(f"发现 {len(image_files)} 张图片")
    
    # 初始化识别器
    recognizer = GameRecognizer()
    
    # 处理所有图片
    all_games = recognizer.process_multiple_screenshots(image_files)
    
    # 保存结果
    recognizer.save_to_csv(all_games)
    
    logger.success(f"OCR识别完成，共识别出 {len(all_games)} 个游戏")
    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="快手游戏APK自动化采集工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py --full --platform android     # 运行完整流程（Android）
  python main.py --full --platform ios         # 运行完整流程（iOS）
  python main.py --mode mobile --platform android  # 仅运行移动端自动化
  python main.py --mode search                 # 仅搜索游戏
  python main.py --mode download               # 仅下载APK
  python main.py --mode ocr --image-dir ./screenshots  # 仅OCR识别

环境准备:
  1. 安装依赖: pip install -r requirements.txt
  2. 启动Appium服务器: appium
  3. 启动Chrome调试模式: 
     - Windows: chrome.exe --remote-debugging-port=9222
     - Mac: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222
        """
    )
    
    parser.add_argument(
        "--full",
        action="store_true",
        help="运行完整流程"
    )
    
    parser.add_argument(
        "--mode",
        choices=["mobile", "search", "download", "ocr"],
        help="运行模式: mobile(移动端), search(搜索), download(下载), ocr(识别)"
    )
    
    parser.add_argument(
        "--platform",
        choices=["android", "ios"],
        default="android",
        help="移动端平台 (默认: android)"
    )
    
    parser.add_argument(
        "--image-dir",
        help="OCR模式的图片目录"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.debug:
        logger.remove()
        logger.add(sys.stdout, format=LOG_CONFIG["format"], level="DEBUG")
    
    # 执行对应模式
    try:
        if args.full:
            success = run_full_pipeline(args.platform)
        elif args.mode == "mobile":
            success = run_mobile_automation(args.platform)
        elif args.mode == "search":
            success = run_search_mode()
        elif args.mode == "download":
            success = run_download_mode()
        elif args.mode == "ocr":
            success = run_ocr_only(args.image_dir)
        else:
            # 默认显示帮助
            parser.print_help()
            return
        
        if success:
            logger.success("任务完成！")
        else:
            logger.error("任务执行过程中出现错误")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"发生未处理的异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
