#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描CSV文件，检查已下载文件的大小
如果文件大小小于详情页的文件大小，删除文件夹并更新CSV
"""

import csv
import re
import sys
import time
from pathlib import Path
from typing import Optional, Dict

try:
    import requests
except ImportError:
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# 导入百度建议词功能
try:
    baidu_suggestion_path = Path(__file__).parent.parent / 'web_download_for_duduo' / 'baidu_suggestion.py'
    if baidu_suggestion_path.exists():
        sys.path.insert(0, str(baidu_suggestion_path.parent))
        from baidu_suggestion import get_baidu_suggestions
    else:
        from baidu_suggestion import get_baidu_suggestions
except ImportError:
    print("⚠️  无法导入 baidu_suggestion，将使用游戏名称作为文件夹名")
    get_baidu_suggestions = None


def get_folder_name(game_name: str) -> str:
    """使用百度建议词获取文件夹名"""
    if get_baidu_suggestions:
        try:
            suggestions = get_baidu_suggestions(game_name)
            if suggestions:
                folder_name = suggestions[0]
                folder_name = re.sub(r'[<>:"/\\|?*]', '_', folder_name)
                return folder_name
        except Exception as e:
            print(f"⚠️  获取建议词失败: {e}，使用游戏名称")
    
    # 如果没有建议词，使用游戏名称
    folder_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)
    return folder_name


def parse_size_to_mb(size_str: str) -> float:
    """将大小字符串转换为MB数值"""
    if not size_str:
        return 0.0
    
    size_str = size_str.strip().upper()
    
    # 匹配数字和单位
    match = re.match(r'(\d+\.?\d*)\s*([MG]B?)', size_str)
    if not match:
        return 0.0
    
    value = float(match.group(1))
    unit = match.group(2) or 'M'
    
    # 转换为MB
    if 'G' in unit:
        value = value * 1024
    
    return value


def get_file_size_from_page(page_url: str) -> Optional[float]:
    """从详情页的 ul.azgm_txtList 中解析文件大小"""
    if not requests:
        print("   ⚠️  requests未安装，无法解析详情页")
        return None
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://www.kxdw.com/'
        }
        
        response = requests.get(page_url, headers=headers, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        html = response.text
        
        # 使用BeautifulSoup解析（如果可用）
        if BeautifulSoup:
            soup = BeautifulSoup(html, 'html.parser')
            ul = soup.find('ul', class_='azgm_txtList')
            if ul:
                lis = ul.find_all('li')
                for li in lis:
                    text = li.get_text(strip=True)
                    # 查找包含大小信息的li（通常包含"MB"或"GB"）
                    if 'MB' in text.upper() or 'GB' in text.upper():
                        # 提取大小信息
                        size_match = re.search(r'(\d+\.?\d*)\s*([MG]B)', text, re.IGNORECASE)
                        if size_match:
                            value = float(size_match.group(1))
                            unit = size_match.group(2).upper()
                            if 'G' in unit:
                                value = value * 1024
                            return value
        
        # 如果BeautifulSoup不可用，使用正则表达式
        # 查找 ul class="azgm_txtList" 及其内容
        ul_pattern = r'<ul[^>]*class=["\']azgm_txtList["\'][^>]*>(.*?)</ul>'
        ul_match = re.search(ul_pattern, html, re.DOTALL | re.IGNORECASE)
        if ul_match:
            ul_content = ul_match.group(1)
            # 查找所有li标签
            li_pattern = r'<li[^>]*>(.*?)</li>'
            li_matches = re.findall(li_pattern, ul_content, re.DOTALL | re.IGNORECASE)
            for li_content in li_matches:
                # 移除HTML标签，只保留文本
                text = re.sub(r'<[^>]+>', '', li_content).strip()
                # 查找包含大小信息的文本
                if 'MB' in text.upper() or 'GB' in text.upper():
                    size_match = re.search(r'(\d+\.?\d*)\s*([MG]B)', text, re.IGNORECASE)
                    if size_match:
                        value = float(size_match.group(1))
                        unit = size_match.group(2).upper()
                        if 'G' in unit:
                            value = value * 1024
                        return value
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  解析详情页失败: {e}")
        return None


def check_and_cleanup_files(csv_file: str, download_dir: str = "./downloads", 
                            start: int = 0, limit: int = None):
    """扫描CSV文件，检查文件大小并清理不完整的文件
    
    Args:
        csv_file: CSV文件路径
        download_dir: 下载目录
        start: 从第几条开始（从0开始）
        limit: 检查的数量限制（None表示检查所有）
    """
    csv_path = Path(csv_file)
    download_path = Path(download_dir)
    
    if not csv_path.exists():
        print(f"❌ CSV文件不存在: {csv_file}")
        return
    
    if not download_path.exists():
        print(f"❌ 下载目录不存在: {download_dir}")
        return
    
    # 读取CSV文件
    all_games = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_games.append(row)
    
    total_count = len(all_games)
    print(f"📋 共 {total_count} 条记录")
    
    # 应用start和limit参数
    if start < 0:
        start = 0
    if start >= total_count:
        print(f"❌ start参数 ({start}) 超出总记录数 ({total_count})")
        return
    
    games = all_games[start:]
    if limit is not None and limit > 0:
        games = games[:limit]
    
    end_index = start + len(games) - 1
    print(f"📋 将检查第 {start + 1} 到 {end_index + 1} 条记录（共 {len(games)} 条）")
    print(f"{'='*60}")
    
    updated_count = 0
    deleted_count = 0
    skipped_count = 0
    
    for i, game in enumerate(games):
        # 计算实际索引（从1开始，考虑start偏移）
        actual_index = start + i + 1
        total_to_check = len(games)
        
        game_name = game.get('游戏名称', '').strip()
        page_url = game.get('详情页链接', '').strip()
        
        if not game_name or not page_url:
            print(f"\n[{actual_index}/{total_count}] ⚠️  跳过：游戏名称或详情页链接为空")
            skipped_count += 1
            continue
        
        print(f"\n[{actual_index}/{total_count}] 🔍 检查: {game_name}")
        
        # 1. 获取文件夹名
        folder_name = get_folder_name(game_name)
        folder_path = download_path / folder_name
        
        # 2. 检查文件夹是否存在
        if not folder_path.exists() or not folder_path.is_dir():
            print(f"   ⏭️  文件夹不存在: {folder_name}，跳过")
            skipped_count += 1
            continue
        
        # 3. 解析详情页获取文件大小（从 ul.azgm_txtList 中提取）
        print(f"   📄 解析详情页: {page_url}")
        expected_size_mb = get_file_size_from_page(page_url)
        
        if expected_size_mb is None or expected_size_mb == 0:
            print(f"   ⚠️  无法从详情页获取文件大小，跳过")
            skipped_count += 1
            continue
        
        print(f"   📊 详情页文件大小: {expected_size_mb:.2f}MB")
        
        # 4. 检查文件夹中的文件
        files = [f for f in folder_path.iterdir() if f.is_file()]
        if not files:
            print(f"   ⚠️  文件夹为空，跳过")
            skipped_count += 1
            continue
        
        # 查找最大的文件（通常是APK文件）
        largest_file = max(files, key=lambda f: f.stat().st_size)
        existing_file_size_bytes = largest_file.stat().st_size
        existing_file_size_mb = existing_file_size_bytes / 1024 / 1024
        
        print(f"   📄 找到文件: {largest_file.name} ({existing_file_size_mb:.2f}MB)")
        
        # 5. 比较文件大小
        # 使用5%的容差（考虑浮点数精度和文件系统差异）
        # 只要文件大小 >= 详情页大小 * 0.95，就认为文件完整
        min_acceptable_size = expected_size_mb * 0.95
        if existing_file_size_mb >= min_acceptable_size:
            print(f"   ✅ 文件大小完整: {existing_file_size_mb:.2f}MB >= {min_acceptable_size:.2f}MB (详情页: {expected_size_mb:.2f}MB, 容差5%)")
        else:
            size_diff = existing_file_size_mb - expected_size_mb
            print(f"   ⚠️  文件大小不完整: {existing_file_size_mb:.2f}MB < {min_acceptable_size:.2f}MB (详情页: {expected_size_mb:.2f}MB, 差异: {size_diff:.2f}MB)")
            print(f"   🗑️  删除文件夹下的所有文件...")
            
            # 删除文件夹下的所有文件
            try:
                for file in files:
                    try:
                        file.unlink()
                        print(f"      ✅ 已删除: {file.name}")
                    except Exception as e:
                        print(f"      ⚠️  删除失败 {file.name}: {e}")
                
                # 更新CSV
                game['是否已下载'] = '否'
                updated_count += 1
                deleted_count += 1
                print(f"   ✅ 已更新CSV: 是否已下载 = 否")
            except Exception as e:
                print(f"   ❌ 删除文件时出错: {e}")
    
    # 保存CSV文件（需要更新原始CSV文件）
    if updated_count > 0:
        print(f"\n{'='*60}")
        print(f"💾 保存CSV文件...")
        # 更新all_games中对应的记录
        for i, game in enumerate(games):
            original_index = start + i
            if original_index < len(all_games):
                all_games[original_index] = game
        
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            if all_games:
                fieldnames = list(all_games[0].keys())
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_games)
        print(f"✅ CSV文件已保存")
    
    # 输出统计信息
    print(f"\n{'='*60}")
    print(f"📊 统计信息:")
    print(f"   总记录数: {total_count}")
    print(f"   检查范围: 第 {start + 1} 到 {end_index + 1} 条（共 {len(games)} 条）")
    print(f"   已更新: {updated_count}")
    print(f"   已删除文件夹: {deleted_count}")
    print(f"   跳过: {skipped_count}")
    print(f"{'='*60}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='扫描CSV文件，检查已下载文件的大小')
    parser.add_argument('csv_file', help='CSV文件路径')
    parser.add_argument('--download-dir', default='./downloads', help='下载目录（默认: ./downloads）')
    parser.add_argument('--start', type=int, default=0, help='从第几条开始（从0开始，默认: 0）')
    parser.add_argument('--limit', type=int, default=None, help='检查的数量限制（默认: 检查所有）')
    
    args = parser.parse_args()
    
    check_and_cleanup_files(
        csv_file=args.csv_file,
        download_dir=args.download_dir,
        start=args.start,
        limit=args.limit
    )

