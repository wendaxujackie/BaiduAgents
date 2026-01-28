#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
整理指定文件夹中的文件：
1. 按照文件名创建文件夹
2. 将文件移动到对应文件夹
3. 创建与文件名同名的真实 ZIP 压缩包
4. 创建提示txt文件
"""

import os
import shutil
import zipfile
import argparse
from pathlib import Path

# 要创建的txt文件
txt_files = [
    "不定时更新最新版本.txt",
    "先保存再下载，否则资源会损坏.txt"
]

def get_folder_name(file_name):
    """根据文件名获取文件夹名（去掉扩展名）"""
    extensions = ['.apk', '.xapk', '.ipa', '.zip', '.rar', '.7z']
    for ext in extensions:
        if file_name.lower().endswith(ext):
            return file_name[:-len(ext)]
    # 没有识别到扩展名，返回原文件名
    return file_name

def organize_files(target_dir):
    # 设置工作文件夹路径
    uploads_dir = Path(target_dir).absolute()
    
    if not uploads_dir.exists():
        print(f"错误：目录 {uploads_dir} 不存在")
        return

    # 获取所有文件（不包括子目录）
    files = [f for f in uploads_dir.iterdir() if f.is_file()]
    
    if not files:
        print(f"📂 {uploads_dir} 文件夹中没有待整理的文件")
        return
    
    print(f"📦 目标目录: {uploads_dir}")
    print(f"📦 找到 {len(files)} 个文件需要整理\n")
    
    processed = 0
    for file_path in files:
        file_name = file_path.name
        folder_name = get_folder_name(file_name)
        
        # 创建新文件夹路径
        new_folder = uploads_dir / folder_name
        
        # 如果文件名和文件夹名相同（无扩展名文件），需要特殊处理
        if folder_name == file_name:
            # 先创建临时文件夹
            temp_folder = uploads_dir / f"{folder_name}_temp"
            temp_folder.mkdir(parents=True, exist_ok=True)
            
            # 移动文件到临时文件夹
            new_file_path = temp_folder / file_name
            shutil.move(str(file_path), str(new_file_path))
            
            # 重命名临时文件夹为正式文件夹
            temp_folder.rename(new_folder)
            print(f"✓ 创建文件夹并移动: {folder_name}")
        else:
            # 正常情况：创建文件夹并移动文件
            if not new_folder.exists():
                new_folder.mkdir(parents=True)
                print(f"✓ 创建文件夹: {folder_name}")
            
            new_file_path = new_folder / file_name
            if not new_file_path.exists():
                shutil.move(str(file_path), str(new_file_path))
                print(f"  → 移动文件: {file_name}")
        
        # 创建与文件名同名的真正 zip 压缩包（如果原文件不是 zip 文件）
        if file_name.lower().endswith('.zip'):
            print(f"  ⏭️  原文件已是 ZIP 格式，跳过压缩步骤")
        else:
            zip_name = f"{folder_name}.zip"
            zip_path = new_folder / zip_name
            if not zip_path.exists():
                print(f"  ⚡ 正在将文件压缩为 ZIP...")
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(new_file_path, arcname=file_name)
                print(f"  + 压缩完成: {zip_name}")

        # 创建txt文件
        for txt_name in txt_files:
            txt_path = new_folder / txt_name
            if not txt_path.exists():
                txt_path.touch()
        
        print(f"  + 创建提示文件\n")
        processed += 1
    
    print("=" * 50)
    print(f"✅ 整理完成！共处理 {processed} 个文件")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="文件整理工具")
    parser.add_argument("directory", nargs="?", default=None, help="指定要整理的文件夹路径")
    
    args = parser.parse_args()
    
    target_directory = args.directory
    
    # 如果没有传参，则提示输入
    if not target_directory:
        print("--- 文件整理工具 ---")
        input_dir = input("请输入要整理的文件夹路径 (直接回车处理默认 uploads 目录): ").strip()
        if input_dir:
            target_directory = input_dir
        else:
            target_directory = "/Users/jackie/Documents/副业/Scripts/Hot Games/uploads"

    organize_files(target_directory)