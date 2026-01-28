#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除重名文件工具
在指定目录中查找重名文件，保留第一个找到的文件，删除其他重复文件
"""

import os
import argparse
from pathlib import Path
from collections import defaultdict

def remove_duplicate_files(target_dir, dry_run=False):
    """
    删除指定目录中的重名文件
    
    Args:
        target_dir: 目标目录路径
        dry_run: 如果为True，只显示将要删除的文件，不实际删除
    """
    target_path = Path(target_dir).absolute()
    if not target_path.exists():
        print(f"错误：目录 {target_path} 不存在")
        return
    
    # 收集所有文件（递归查找）
    file_dict = defaultdict(list)
    
    for root, dirs, files in os.walk(target_path):
        for file in files:
            if file.lower().endswith(('.apk', '.xapk', '.zip')):
                full_path = os.path.join(root, file)
                file_dict[file].append(full_path)
    
    # 找出重名文件
    duplicates = {k: v for k, v in file_dict.items() if len(v) > 1}
    
    if not duplicates:
        print(f"在 {target_path} 中没有找到重名文件")
        return
    
    print(f"发现 {len(duplicates)} 个重名文件组：\n")
    
    total_to_delete = 0
    total_size = 0
    
    for filename, paths in duplicates.items():
        print(f"文件名: {filename}")
        print(f"  共找到 {len(paths)} 个同名文件：")
        
        # 按路径排序，保留第一个，删除其他的
        paths_sorted = sorted(paths)
        keep_file = paths_sorted[0]
        
        print(f"  [保留] {keep_file}")
        
        for dup_path in paths_sorted[1:]:
            file_size = os.path.getsize(dup_path)
            total_size += file_size
            total_to_delete += 1
            
            if dry_run:
                print(f"  [将删除] {dup_path} ({file_size / 1024 / 1024:.2f} MB)")
            else:
                try:
                    os.remove(dup_path)
                    print(f"  [已删除] {dup_path} ({file_size / 1024 / 1024:.2f} MB)")
                except Exception as e:
                    print(f"  [删除失败] {dup_path}: {e}")
        print()
    
    print("=" * 60)
    if dry_run:
        print(f"预览模式：将删除 {total_to_delete} 个重复文件，释放 {total_size / 1024 / 1024:.2f} MB 空间")
        print("提示：运行时不加 --dry-run 参数将实际执行删除操作")
    else:
        print(f"删除完成：已删除 {total_to_delete} 个重复文件，释放 {total_size / 1024 / 1024:.2f} MB 空间")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="删除重名文件工具")
    parser.add_argument("directory", nargs="?", default=None, help="指定要处理的文件夹路径")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，只显示将要删除的文件，不实际删除")
    
    args = parser.parse_args()
    
    target_directory = args.directory
    
    # 如果没有传参，则提示输入
    if not target_directory:
        print("--- 删除重名文件工具 ---")
        input_dir = input("请输入要处理的文件夹路径 (直接回车处理 'uploads/2026发发发'): ").strip()
        if input_dir:
            target_directory = input_dir
        else:
            target_directory = "uploads/2026发发发"
    
    remove_duplicate_files(target_directory, dry_run=args.dry_run)
