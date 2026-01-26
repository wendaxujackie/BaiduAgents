#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将指定文件夹下所有子文件夹中的 APK 文件打包成 ZIP 文件。
每个 APK 文件会在其所在目录下生成一个同名的 ZIP 压缩包。
"""

import os
import zipfile
from pathlib import Path

def pack_apk_to_zip(source_dir):
    """
    将源目录下所有子文件夹中的 APK 文件打包成 ZIP 文件
    每个 APK 文件会在其所在目录下生成一个同名的 ZIP 文件
    
    Args:
        source_dir: 源文件夹路径（包含子文件夹的目录）
    """
    source_path = Path(source_dir).resolve()
    
    if not source_path.exists() or not source_path.is_dir():
        print(f"❌ 错误: 目录不存在 - {source_path}")
        return
    
    # 获取所有子文件夹（排除隐藏文件夹）
    subdirs = [
        d for d in source_path.iterdir() 
        if d.is_dir() and not d.name.startswith('.')
    ]
    
    # 按名称排序
    subdirs.sort(key=lambda x: x.name)
    
    total_folders = len(subdirs)
    if total_folders == 0:
        print(f"⚠️  在 {source_path} 下没有找到子文件夹。")
        return
    
    print(f"📋 找到 {total_folders} 个子文件夹，开始处理...")
    print(f"📦 ZIP 文件将保存在每个 APK 文件所在的目录下")
    print(f"{'='*60}")
    
    total_apk_count = 0
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for i, subdir in enumerate(subdirs, 1):
        print(f"\n[{i}/{total_folders}] 🔍 处理: {subdir.name}")
        
        # 查找所有 APK 文件
        apk_files = list(subdir.glob("*.apk"))
        
        if not apk_files:
            print(f"   ⏭️  未找到 APK 文件，跳过")
            skip_count += 1
            continue
        
        total_apk_count += len(apk_files)
        
        # 对每个 APK 文件创建对应的 ZIP 文件
        for apk_file in apk_files:
            # ZIP 文件名使用 APK 文件名（只改变扩展名）
            zip_filename = apk_file.stem + ".zip"
            zip_path = apk_file.parent / zip_filename
            
            # 如果 ZIP 文件已存在，跳过或覆盖（这里直接覆盖）
            if zip_path.exists():
                print(f"   ⚠️  ZIP 文件已存在，将覆盖: {zip_filename}")
            
            try:
                # 创建 ZIP 文件，只包含这个 APK 文件
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(apk_file, apk_file.name)
                
                apk_size = apk_file.stat().st_size / 1024 / 1024
                zip_size = zip_path.stat().st_size / 1024 / 1024
                print(f"   ✅ {apk_file.name} -> {zip_filename} (APK: {apk_size:.2f}MB, ZIP: {zip_size:.2f}MB)")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ 创建 ZIP 失败 {apk_file.name}: {e}")
                error_count += 1
                # 如果出错，删除可能创建的不完整 ZIP 文件
                if zip_path.exists():
                    try:
                        zip_path.unlink()
                    except:
                        pass
    
    # 输出统计信息
    print(f"\n{'='*60}")
    print(f"📊 处理完成！统计信息:")
    print(f"   总文件夹数: {total_folders}")
    print(f"   找到 APK 文件: {total_apk_count}")
    print(f"   ✅ 成功创建 ZIP: {success_count}")
    print(f"   ⏭️  跳过（无APK）: {skip_count}")
    print(f"   ❌ 失败: {error_count}")
    print(f"{'='*60}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='将指定文件夹下所有子文件夹中的 APK 文件打包成 ZIP（每个 APK 在其所在目录生成同名 ZIP）')
    parser.add_argument('source_dir', help='源文件夹路径（包含子文件夹的目录）')
    
    args = parser.parse_args()
    
    pack_apk_to_zip(args.source_dir)
