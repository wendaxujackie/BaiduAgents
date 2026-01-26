import os
import shutil
import random
import argparse

def generate_apk_copies(source_dir, target_folder_name="2026发发发", copy_count_per_file=4):
    # 1. 路径处理
    source_dir = os.path.abspath(source_dir)
    target_folder = os.path.join(source_dir, target_folder_name)
    
    # 2. 关键词库（保留原有的并增加热词）
    base_keywords = [
        "官方版", "手机版", "最新版", "中文版", 
        "汉化版", "官方正版", "安卓版", "手机版下载",
    ]
    
    # 增加的热词（结合游戏分发场景）
    trending_keywords = [
        "破解版", "无限资源", "免登录", "高帧率版", "联机版",
        "内测版", "国际服", "模拟器版", "极速版", "全解锁版",
        "2026最新版", "高清重制版", "怀旧版", "直装版", "变态版", "MOD版"
    ]
    
    all_keywords = list(set(base_keywords + trending_keywords))
    
    # 3. 创建目标文件夹
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        print(f"创建目标文件夹: {target_folder}")
    else:
        print(f"目标文件夹已存在: {target_folder}")

    # 4. 获取指定目录下的所有 APK/XAPK/ZIP 文件
    try:
        files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.apk', '.xapk', '.zip'))]
    except Exception as e:
        print(f"无法读取目录 {source_dir}: {e}")
        return
    
    if not files:
        print(f"错误：在目录 {source_dir} 中没有找到 APK、XAPK 或 ZIP 文件！")
        return

    print(f"源目录: {source_dir}")
    print(f"发现 {len(files)} 个文件，准备为每个文件创建 {copy_count_per_file} 个随机副本...\n")

    total_copies = 0
    processed_count = 0
    
    for filename in files:
        full_path = os.path.join(source_dir, filename)
        name_part, ext_part = os.path.splitext(filename)
        print(f"正在处理: {filename}")
        
        # 随机抽取关键词
        selected_keywords = random.sample(all_keywords, min(copy_count_per_file, len(all_keywords)))
        
        for kw in selected_keywords:
            new_name = f"{name_part}{kw}{ext_part}"
            target_path = os.path.join(target_folder, new_name)
            
            # 复制文件
            try:
                shutil.copy2(full_path, target_path)
                total_copies += 1
                print(f"  -> 已生成副本: {new_name}")
            except Exception as e:
                print(f"  ! 生成失败 {new_name}: {e}")
        
        # 移动原始文件到目标文件夹
        try:
            shutil.move(full_path, os.path.join(target_folder, filename))
            processed_count += 1
            print(f"  [OK] 原始文件已移至目标文件夹\n")
        except Exception as e:
            print(f"  [!] 移动原始文件失败: {e}\n")

    print("=" * 40)
    print(f"处理完成！")
    print(f"总计处理原始文件: {processed_count} 个")
    print(f"总计创建副本: {total_copies} 个")
    print(f"所有文件已保存至: {target_folder}")
    print("=" * 40)

if __name__ == "__main__":
    # 使用 argparse 来支持命令行指定目录
    parser = argparse.ArgumentParser(description="APK/ZIP 随机关键词副本生成工具")
    parser.add_argument("directory", nargs="?", default=".", help="指定要处理的 APK/ZIP 文件目录 (默认为当前目录)")
    
    args = parser.parse_args()
    
    # 如果用户没有通过命令行传参，也可以手动输入
    target_dir = args.directory
    if target_dir == ".":
        input_dir = input("请输入要处理的 APK/ZIP 文件夹路径 (直接回车表示当前目录): ").strip()
        if input_dir:
            target_dir = input_dir

    generate_apk_copies(target_dir)
