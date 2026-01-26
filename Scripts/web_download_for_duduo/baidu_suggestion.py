#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
百度搜索建议词抓取工具
抓取在百度搜索框输入关键词时显示的下拉提示词

用法:
    python3 baidu_suggestion.py 关键词
    python3 baidu_suggestion.py 关键词1 关键词2 关键词3
    python3 baidu_suggestion.py -m 关键词          # 使用移动端
    python3 baidu_suggestion.py -o output.txt 关键词  # 保存到文件
"""

import requests
import json
import argparse
from typing import List, Optional


def get_baidu_suggestions(keyword: str) -> List[str]:
    """
    获取百度搜索建议词
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        提示词列表
    """
    # 百度搜索建议API接口
    url = "https://www.baidu.com/sugrec"
    
    params = {
        "pre": 1,
        "p": 3,
        "ie": "utf-8",
        "json": 1,
        "prod": "pc",
        "from": "pc_web",
        "wd": keyword,
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Referer": "https://www.baidu.com/",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # 提取建议词
        suggestions = []
        if "g" in data:
            for item in data["g"]:
                if "q" in item:
                    suggestions.append(item["q"])
        
        return suggestions
        
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return []


def get_baidu_suggestions_mobile(keyword: str) -> List[str]:
    """
    获取百度移动端搜索建议词
    
    Args:
        keyword: 搜索关键词
        
    Returns:
        提示词列表
    """
    url = "https://m.baidu.com/sugrec"
    
    params = {
        "ie": "utf-8",
        "json": 1,
        "prod": "wise",
        "wd": keyword,
    }
    
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://m.baidu.com/",
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        suggestions = []
        if "g" in data:
            for item in data["g"]:
                if "q" in item:
                    suggestions.append(item["q"])
        
        return suggestions
        
    except requests.RequestException as e:
        print(f"请求错误: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        return []


def batch_get_suggestions(keywords: List[str], source: str = "pc") -> dict:
    """
    批量获取多个关键词的搜索建议
    
    Args:
        keywords: 关键词列表
        source: 来源，"pc" 或 "mobile"
        
    Returns:
        字典，key为关键词，value为对应的建议词列表
    """
    results = {}
    
    get_func = get_baidu_suggestions if source == "pc" else get_baidu_suggestions_mobile
    
    for keyword in keywords:
        suggestions = get_func(keyword)
        results[keyword] = suggestions
        print(f"✓ 已获取 '{keyword}' 的 {len(suggestions)} 条建议词")
    
    return results


def main():
    """主函数 - 支持命令行参数"""
    parser = argparse.ArgumentParser(
        description="百度搜索建议词抓取工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 baidu_suggestion.py Python
  python3 baidu_suggestion.py 人工智能 机器学习 深度学习
  python3 baidu_suggestion.py -m 人工智能
  python3 baidu_suggestion.py -o result.txt Python
        """
    )
    
    parser.add_argument(
        "keywords",
        nargs="+",
        help="要查询的搜索关键词（支持多个）"
    )
    
    parser.add_argument(
        "-m", "--mobile",
        action="store_true",
        help="使用移动端搜索建议（默认PC端）"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="将结果保存到文件"
    )
    
    parser.add_argument(
        "-n", "--num",
        type=int,
        default=1,
        help="显示建议词的数量（默认1个）"
    )
    
    args = parser.parse_args()
    
    # 选择获取函数
    get_func = get_baidu_suggestions_mobile if args.mobile else get_baidu_suggestions
    source_name = "📱 移动端" if args.mobile else "🖥️  PC端"
    
    print("=" * 50)
    print(f"百度搜索建议词抓取工具 ({source_name})")
    print("=" * 50)
    
    all_results = []
    
    for keyword in args.keywords:
        print(f"\n📌 关键词: {keyword}")
        print("-" * 30)
        
        suggestions = get_func(keyword)
        
        if suggestions:
            # 只取前 n 个建议词
            suggestions = suggestions[:args.num]
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")
            all_results.append({
                "keyword": keyword,
                "suggestions": suggestions
            })
        else:
            print("  未获取到建议词")
    
    # 保存到文件
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for result in all_results:
                f.write(f"【{result['keyword']}】\n")
                for s in result["suggestions"]:
                    f.write(f"  {s}\n")
                f.write("\n")
        print(f"\n✅ 结果已保存到: {args.output}")
    
    print(f"\n✅ 共查询 {len(args.keywords)} 个关键词")


if __name__ == "__main__":
    main()

