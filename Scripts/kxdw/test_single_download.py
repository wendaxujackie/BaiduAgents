#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试单个游戏下载
"""

import sys
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from kxdw_downloader import KXDWDownloader

def test_single_game():
    """测试单个游戏下载"""
    # 创建一个临时的CSV文件
    csv_file = Path(__file__).parent / "test_game.csv"
    
    # 创建测试数据
    test_data = """游戏名称,详情页链接,是否已下载,是否有安卓下载链接
无烦恼厨房游戏正版,https://www.kxdw.com/android/101820.html,否,否
"""
    
    with open(csv_file, 'w', encoding='utf-8-sig') as f:
        f.write(test_data)
    
    print("="*60)
    print("测试单个游戏下载")
    print("="*60)
    print(f"游戏: 无烦恼厨房游戏正版")
    print(f"详情页: https://www.kxdw.com/android/101820.html")
    print("="*60)
    print()
    
    # 创建下载器（使用Chrome模式）
    print("使用Chrome模式测试...")
    print("提示: 请确保Chrome已启动并开启远程调试端口9222")
    print("启动命令: /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome --remote-debugging-port=9222")
    print()
    
    try:
        downloader = KXDWDownloader(
            str(csv_file),
            download_base_dir="./test_downloads",
            use_chrome=True,
            proxy="http://127.0.0.1:1082"  # 使用Shadowrocket代理
        )
        print(f"✅ 已配置代理: http://127.0.0.1:1082")
    except Exception as e:
        print(f"❌ Chrome连接失败: {e}")
        print("切换到requests模式...")
        downloader = KXDWDownloader(
            str(csv_file),
            download_base_dir="./test_downloads",
            use_chrome=False,
            proxy="http://127.0.0.1:1082"  # 使用Shadowrocket代理
        )
        print(f"✅ 已配置代理: http://127.0.0.1:1082")
    
    # 处理第一个游戏
    if downloader.games:
        game = downloader.games[0]
        result = downloader.process_game(game, 1)
        
        if result:
            print("\n✅ 测试成功！")
        else:
            print("\n❌ 测试失败")
    
    # 清理临时文件
    if csv_file.exists():
        csv_file.unlink()

if __name__ == "__main__":
    test_single_game()

