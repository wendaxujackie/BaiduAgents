import os
import shutil
import argparse
from pathlib import Path

def group_files_by_100(target_dir, group_size=100):
    target_path = Path(target_dir).absolute()
    if not target_path.exists():
        print(f"错误：目录 {target_path} 不存在")
        return

    # 获取所有 APK、XAPK 和 ZIP 文件（只获取直接子文件，排除子目录）
    # 同时排除已经存在的组文件夹中的文件
    files = []
    existing_group_files = set()
    
    # 先收集所有组文件夹中已有的文件名，避免重复移动
    for item in target_path.iterdir():
        if item.is_dir() and item.name.startswith("第") and item.name.endswith("组"):
            for group_file in item.iterdir():
                if group_file.is_file() and group_file.suffix.lower() in ['.apk', '.xapk', '.zip']:
                    existing_group_files.add(group_file.name)
    
    # 获取需要处理的文件（只处理直接子文件，且不在组文件夹中）
    for item in target_path.iterdir():
        if item.is_file() and item.suffix.lower() in ['.apk', '.xapk', '.zip']:
            # 检查文件是否已经在组文件夹中
            if item.name not in existing_group_files:
                files.append(item)
    
    if not files:
        print(f"在 {target_path} 中没有找到需要处理的 APK、XAPK 或 ZIP 文件")
        if existing_group_files:
            print(f"注意：已发现 {len(existing_group_files)} 个文件已在组文件夹中")
        return

    print(f"目标目录: {target_path}")
    print(f"发现 {len(files)} 个文件需要分组，准备每 {group_size} 个分为一组...")
    if existing_group_files:
        print(f"注意：已跳过 {len(existing_group_files)} 个已在组文件夹中的文件")

    # 分组处理
    for i in range(0, len(files), group_size):
        group_num = (i // group_size) + 1
        group_folder = target_path / f"第{group_num}组"
        
        if not group_folder.exists():
            group_folder.mkdir()
            print(f"创建文件夹: {group_folder.name}")
        
        # 获取当前组的文件
        current_group = files[i:i + group_size]
        moved_count = 0
        
        for file_path in current_group:
            try:
                # 再次检查目标文件是否已存在（防止重复）
                target_file = group_folder / file_path.name
                if target_file.exists():
                    print(f"  警告：文件 {file_path.name} 在 {group_folder.name} 中已存在，跳过")
                    continue
                shutil.move(str(file_path), str(target_file))
                moved_count += 1
            except Exception as e:
                print(f"移动文件 {file_path.name} 失败: {e}")
        
        print(f"  -> 已将 {moved_count} 个文件移至 {group_folder.name}")

    print("\n整理完成！")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APK/ZIP 分组工具")
    parser.add_argument("directory", nargs="?", default=None, help="指定要处理的文件夹路径")
    
    args = parser.parse_args()
    
    target_directory = args.directory
    
    # 如果没有传参，则提示输入
    if not target_directory:
        print("--- APK/ZIP 分组工具 ---")
        input_dir = input("请输入要分组的文件夹路径 (直接回车处理 'uploads/2026发发发'): ").strip()
        if input_dir:
            target_directory = input_dir
        else:
            target_directory = "/Users/jackie/Documents/副业/Scripts/Hot Games/uploads/2026发发发"

    group_files_by_100(target_directory)
