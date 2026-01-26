#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试下载完成判断逻辑
特别测试进度100%时的完成判断
"""

import sys
import time
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from kxdw_downloader import KXDWDownloader

def test_download_completion():
    """测试下载完成判断逻辑"""
    # 创建一个临时的CSV文件，使用一个较小的游戏进行测试
    csv_file = Path(__file__).parent / "test_download_completion.csv"
    
    # 选择一个较小的游戏进行测试（文件大小约87MB）
    test_data = """游戏名称,详情页链接,是否已下载,是否有安卓下载链接
刺客信条阿泰尔编年史汉化版下载 v1.0.2 安卓版,https://www.kxdw.com/android/165708.html,否,否
"""
    
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write(test_data)
    
    print("="*60)
    print("测试下载完成判断逻辑")
    print("="*60)
    print(f"测试游戏: 刺客信条阿泰尔编年史汉化版下载 v1.0.2 安卓版")
    print(f"详情页: https://www.kxdw.com/android/165708.html")
    print(f"预期文件大小: 约87.52MB")
    print("="*60)
    print()
    
    # 检查Chrome是否已启动（使用简单的socket检查）
    print("检查Chrome调试端口...")
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 9222))
        sock.close()
        if result == 0:
            print("✅ Chrome调试端口已开启")
        else:
            print("❌ Chrome调试端口未响应")
            print("💡 请先启动Chrome调试模式:")
            print("   ./start_chrome_debug.sh")
            return
    except Exception as e:
        print(f"❌ 无法连接到Chrome调试端口: {e}")
        print("💡 请先启动Chrome调试模式:")
        print("   ./start_chrome_debug.sh")
        return
    
    print()
    print("开始测试下载...")
    print("="*60)
    print()
    
    try:
        # 创建下载器（使用Chrome模式，不使用代理）
        downloader = KXDWDownloader(
            str(csv_file),
            download_base_dir="./test_downloads",
            use_chrome=True,
            chrome_debug_url="http://127.0.0.1:9222"
        )
        
        if not downloader.use_chrome:
            print("❌ Chrome模式未启用，无法测试")
            return
        
        print("✅ 已创建下载器（Chrome模式）")
        print()
        
        # 处理第一个游戏
        if downloader.games:
            game = downloader.games[0]
            start_time = time.time()
            
            print(f"开始下载: {game.get('游戏名称', '')}")
            print(f"详情页: {game.get('详情页链接', '')}")
            print()
            
            success = downloader.process_game(game, 0)
            
            elapsed_time = time.time() - start_time
            
            print()
            print("="*60)
            if success:
                print(f"✅ 下载成功！")
                print(f"   耗时: {elapsed_time:.1f}秒")
            else:
                print(f"❌ 下载失败")
                print(f"   耗时: {elapsed_time:.1f}秒")
            print("="*60)
            
            # 检查下载的文件
            folder_name = downloader._get_folder_name(game.get('游戏名称', ''))
            folder_path = Path("./test_downloads") / folder_name
            if folder_path.exists():
                files = list(folder_path.glob('*'))
                print(f"\n下载的文件:")
                for file in files:
                    if file.is_file():
                        size_mb = file.stat().st_size / 1024 / 1024
                        print(f"  - {file.name}: {size_mb:.2f}MB")
        else:
            print("❌ 没有游戏数据")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理测试文件
        if csv_file.exists():
            csv_file.unlink()
            print(f"\n已清理测试文件: {csv_file.name}")

if __name__ == "__main__":
    test_download_completion()

