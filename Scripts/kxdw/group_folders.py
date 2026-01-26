#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将指定文件夹下的子文件夹按每100个一组，移动到新的文件夹中。
"""

import os
import shutil
from pathlib import Path

def group_folders(target_dir, batch_size=100):
    # 转换为 Path 对象
    target_path = Path(target_dir).resolve()
    
    if not target_path.exists() or not target_path.is_dir():
        print(f"❌ 错误: 目录不存在 - {target_path}")
        return

    # 获取所有子文件夹（排除隐藏文件夹）
    subdirs = [d for d in target_path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    # 按名称排序，保证稳定性
    subdirs.sort(key=lambda x: x.name)
    
    total_folders = len(subdirs)
    if total_folders == 0:
        print(f"⚠️  在 {target_path} 下没有找到子文件夹。")
        return

    print(f"📋 找到 {total_folders} 个子文件夹，将按每 {batch_size} 个一组进行处理...")

    # 分组处理
    for i in range(0, total_folders, batch_size):
        batch = subdirs[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        # 创建新的目标文件夹名，例如 download_3568_batch_1
        new_folder_name = f"{target_path.name}_batch_{batch_num}"
        new_folder_path = target_path.parent / new_folder_name
        
        # 创建文件夹
        if not new_folder_path.exists():
            new_folder_path.mkdir(parents=True)
            print(f"📁 创建文件夹: {new_folder_name}")
        
        # 移动子文件夹
        print(f"🚚 正在移动第 {batch_num} 组 ({len(batch)} 个文件夹)...")
        for folder in batch:
            try:
                # 使用 shutil.move 移动文件夹
                shutil.move(str(folder), str(new_folder_path / folder.name))
            except Exception as e:
                print(f"  ❌ 移动 {folder.name} 失败: {e}")

    print(f"\n✅ 处理完成！共分成了 { (total_folders + batch_size - 1) // batch_size } 个文件夹。")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='将指定文件夹下的子文件夹按数量分组移动到新文件夹中')
    parser.add_argument('target_dir', nargs='?', help='需要分组处理的目标文件夹路径')
    parser.add_argument('--target_dir', dest='target_dir_opt', help='需要分组处理的目标文件夹路径（可选参数）')
    parser.add_argument('--size', type=int, default=100, help='每组包含的文件夹数量 (默认: 100)')
    
    args = parser.parse_args()
    
    target_dir = args.target_dir_opt or args.target_dir
    if not target_dir:
        parser.error("请提供目标文件夹路径，例如：group_folders.py download_4000 或 --target_dir download_4000")
    
    group_folders(target_dir, batch_size=args.size)
