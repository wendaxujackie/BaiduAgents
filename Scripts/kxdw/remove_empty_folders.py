#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除downloads文件夹下的空文件夹
"""

import argparse
from pathlib import Path


def remove_empty_folders(download_dir: str = "./downloads", dry_run: bool = False):
    """删除指定目录下的所有空文件夹
    
    Args:
        download_dir: 下载目录路径
        dry_run: 如果为True，只显示将要删除的文件夹，不实际删除
    """
    download_path = Path(download_dir)
    
    if not download_path.exists():
        print(f"❌ 目录不存在: {download_dir}")
        return
    
    if not download_path.is_dir():
        print(f"❌ 不是目录: {download_dir}")
        return
    
    print(f"🔍 扫描目录: {download_path.absolute()}")
    print(f"{'='*60}")
    
    # 收集所有空文件夹（从最深层的开始）
    empty_folders = []
    
    # 递归遍历所有子目录
    for folder in sorted(download_path.rglob('*'), reverse=True):
        if folder.is_dir():
            # 检查文件夹是否为空（不包含任何文件或子文件夹）
            try:
                items = list(folder.iterdir())
                if len(items) == 0:
                    empty_folders.append(folder)
            except PermissionError:
                print(f"⚠️  无权限访问: {folder}")
            except Exception as e:
                print(f"⚠️  检查文件夹时出错 {folder}: {e}")
    
    if not empty_folders:
        print(f"✅ 没有找到空文件夹")
        return
    
    print(f"📋 找到 {len(empty_folders)} 个空文件夹")
    print(f"{'='*60}")
    
    if dry_run:
        print(f"🔍 预览模式（不会实际删除）:")
        for folder in empty_folders:
            print(f"   📁 {folder.relative_to(download_path)}")
        print(f"\n💡 使用 --delete 参数来实际删除这些文件夹")
    else:
        deleted_count = 0
        failed_count = 0
        
        for folder in empty_folders:
            try:
                folder.rmdir()
                print(f"   ✅ 已删除: {folder.relative_to(download_path)}")
                deleted_count += 1
            except OSError as e:
                print(f"   ⚠️  删除失败 {folder.relative_to(download_path)}: {e}")
                failed_count += 1
            except Exception as e:
                print(f"   ❌ 删除时出错 {folder.relative_to(download_path)}: {e}")
                failed_count += 1
        
        print(f"\n{'='*60}")
        print(f"📊 统计信息:")
        print(f"   找到空文件夹: {len(empty_folders)}")
        print(f"   成功删除: {deleted_count}")
        print(f"   删除失败: {failed_count}")
        print(f"{'='*60}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='删除downloads文件夹下的空文件夹')
    parser.add_argument('--download-dir', default='./downloads', help='下载目录（默认: ./downloads）')
    parser.add_argument('--delete', action='store_true', help='实际删除空文件夹（默认只预览）')
    parser.add_argument('--dry-run', action='store_true', help='预览模式，不实际删除（默认行为）')
    
    args = parser.parse_args()
    
    # 如果指定了--delete，则实际删除；否则只预览
    dry_run = not args.delete
    
    remove_empty_folders(
        download_dir=args.download_dir,
        dry_run=dry_run
    )

