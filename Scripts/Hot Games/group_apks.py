import os
import shutil
import argparse
from pathlib import Path

def group_files_by_100(target_dir, group_size=100):
    target_path = Path(target_dir).absolute()
    if not target_path.exists():
        print(f"错误：目录 {target_path} 不存在")
        return

    # 获取所有 APK、XAPK 和 ZIP 文件
    files = [f for f in target_path.iterdir() if f.is_file() and f.suffix.lower() in ['.apk', '.xapk', '.zip']]
    
    if not files:
        print(f"在 {target_path} 中没有找到 APK、XAPK 或 ZIP 文件")
        return

    print(f"目标目录: {target_path}")
    print(f"发现 {len(files)} 个文件，准备每 {group_size} 个分为一组...")

    # 分组处理
    for i in range(0, len(files), group_size):
        group_num = (i // group_size) + 1
        group_folder = target_path / f"第{group_num}组"
        
        if not group_folder.exists():
            group_folder.mkdir()
            print(f"创建文件夹: {group_folder.name}")
        
        # 获取当前组的文件
        current_group = files[i:i + group_size]
        
        for file_path in current_group:
            try:
                shutil.move(str(file_path), str(group_folder / file_path.name))
            except Exception as e:
                print(f"移动文件 {file_path.name} 失败: {e}")
        
        print(f"  -> 已将 {len(current_group)} 个文件移至 {group_folder.name}")

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
