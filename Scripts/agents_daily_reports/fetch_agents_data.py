#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取百度灵境 Agent 数据并生成报表
"""

import requests
import json
import csv
import time
import re
import argparse
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random


class AgentsDataFetcher:
    @staticmethod
    def parse_curl_command(curl_cmd: str) -> tuple:
        """解析 curl 命令，提取 cookies 和 headers
        
        Args:
            curl_cmd: curl 命令字符串
            
        Returns:
            (cookies_dict, headers_dict) 元组
        """
        cookies = {}
        headers = {}
        
        # 提取 cookie (从 -b 或 --cookie 参数)
        # 匹配 -b '...' 或 -b "..." 或 --cookie '...' 或 --cookie "..."
        cookie_patterns = [
            r"-[bB]\s+['\"]([^'\"]+)['\"]",  # -b '...' 或 -b "..."
            r"--cookie\s+['\"]([^'\"]+)['\"]",  # --cookie '...' 或 --cookie "..."
        ]
        
        cookie_str = None
        for pattern in cookie_patterns:
            match = re.search(pattern, curl_cmd)
            if match:
                cookie_str = match.group(1)
                break
        
        # 解析 cookie 字符串
        if cookie_str:
            # 处理可能包含引号的情况
            cookie_str = cookie_str.strip("'\"")
            for item in cookie_str.split(';'):
                item = item.strip()
                if '=' in item:
                    key, value = item.split('=', 1)
                    # 移除值两端的引号（如果有）
                    value = value.strip("'\"")
                    cookies[key.strip()] = value
        
        # 提取 headers (从 -H 参数)
        # 匹配 -H 'Header-Name: value' 或 -H "Header-Name: value"
        header_pattern = r"-H\s+['\"]([^:]+):\s*([^'\"]*)['\"]"
        for match in re.finditer(header_pattern, curl_cmd):
            header_name = match.group(1).strip()
            header_value = match.group(2).strip()
            headers[header_name] = header_value
        
        return cookies, headers
    
    def __init__(self, curl_cmd: Optional[str] = None, curl_file: Optional[str] = None):
        """初始化
        
        Args:
            curl_cmd: curl 命令字符串，如果提供则解析它
            curl_file: curl 命令文件路径，如果提供则从文件读取
        """
        # 如果提供了 curl 命令或文件，解析它们
        if curl_file:
            if os.path.exists(curl_file):
                with open(curl_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 只提取 curl 命令部分（到第一个空行或 JSON 开始处）
                    lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        # 如果遇到空行或 JSON 开始，停止读取
                        if not line or line.startswith('{'):
                            break
                        lines.append(line)
                    curl_cmd = ' '.join(lines).strip()
                    # 移除行尾的反斜杠并合并
                    curl_cmd = re.sub(r'\\\s+', ' ', curl_cmd)
            else:
                print(f"警告: curl 文件 {curl_file} 不存在，使用默认配置")
                curl_cmd = None
        
        if curl_cmd:
            # 解析 curl 命令
            self.cookies, self.headers = self.parse_curl_command(curl_cmd)
            print(f"已从 curl 命令解析出 {len(self.cookies)} 个 cookies 和 {len(self.headers)} 个 headers")
        else:
            # 使用默认配置（保留原有配置作为后备）
            self.cookies = {
            'PSTM': '1739107486',
            'BIDUPSID': '4513CC59BFFB710D15E33F2DC6BD27F3',
            'MAWEBCUID': 'web_GhmazbhOuVenghmCcrZjOHgsPmZuOaTQgGTnmkCOohMwOJExOi',
            'H_WISE_SIDS_BFESS': '110085_651903_652164_654812_655050_655722_656054_656174_654041_656531_656548_656661_656696_656750_656755_656826_656868_654341_656985_657156_657159_657223_655417_657588_657543_8000002_8000090_8000113_8000124_8000140_8000150_8000160_8000163_8000185_8000189_8000204',
            'BAIDUID': '48DBB83E9AF4C71D168CEA1B800EC448:FG=1',
            'BAIDUID_BFESS': '48DBB83E9AF4C71D168CEA1B800EC448:FG=1',
            '__bid_n': '19b55b5af998736e9e3063',
            'Hm_lvt_9250b39ef2208a969a3c5951147e6566': '1766720682,1767092248,1767164858',
            'ZFY': 'wPsYnbFqYjXdXCq2oY3R6XQHrDbQ5lOp4Z3EfbgbGCE:C',
            'XFI': '11b77f60-e971-11f0-913a-a323dc0546ef',
            'XFCS': '6F4DBF08F8822A7A9B04477D7BE7F3421A3BC10BBAA5873B77271EBFB17A86ED',
            'XFT': 'ofM34dbUec0Qiq43su1GEKVFX2HG2EdpDj4mkPIlrLI=',
            'delPer': '0',
            'BAIDU_WISE_UID': 'wapp_1767602970756_55',
            'BDRCVFR[feWj1Vr5u3D]': 'mk3SLVN4HKm',
            'PSINO': '5',
            'H_PS_PSSID': '60276_63145_66581_66593_66685_66849_67045_67081_67109_67140_67152_67161_67179_67181_67217_67229_67240_67265_67231_67267_67244_67268_67273_67282_67251_67287',
            'BA_HECTOR': '85012g818ha401ak212g0g0181212g1km3bu027',
            'H_WISE_SIDS': '60276_63145_66581_66593_66685_66849_67045_67081_67109_67140_67152_67161_67179_67181_67217_67229_67240_67265_67231_67267_67244_67268_67273_67282_67251_67287',
            'BDORZ': 'B490B5EBF6F3CD402E515D22BCDA1598',
            'ppfuid': 'FOCoIC3q5fKa8fgJnwzbE0LGziLN3VHbX8wfShDP6RCsfXQp/69CStRUAcn/QmhIlFDxPrAc/s5tJmCocrihdwitHd04Lvs3Nfz26Zt2holplnIKVacidp8Sue4dMTyfg65BJnOFhn1HthtSiwtygiD7piS4vjG/W9dLb1VAdqPDGlvl3S9CENy8XO0gBHvcO0V6uxgO+hV7+7wZFfXG0MSpuMmh7GsZ4C7fF/kTgmv4wr7PaMlE/s6kBdsEohC5lhnnkjJxVh1I/fKNibqIaBYhlEb4xFUg1hpvItixYR81v2iwj13daM+9aWJ5GJCQM+RpBohGNhMcqCHhVhtXpVObaDCHgWJZH3ZrTGYHmi7XJB9z3y2o8Kqxep5XBCsuFKJEamDWP0B99HzIVbHvraGnwl1i7e7qceiikFe+mqIYxfzcV/H7l3Vw5Wr7n3LlnvNXIEW2pwj4BXINSNFrPGGVKiHVw+XnVp5diRSvwr8FMb7+JFWxNGoA0JNiv6hCb0gkXpkEpISi6tVHh+hsQifjACGGz0MbLI9AAutvQNmLovQE8DrrUkOPSWZkiBwIUvxonSGS2lgiNZBxgK/Nad6P3sfvyvYhyXNwxm6SzH+Oja1l6cy9uoP7y446ILa1CLEOaV1jDkGoksNhRtn7B1VPovN1TRU04qLrmECuDGMBVR4vlhy8DqZQ1/LUEQ9mjyqP/SnZsRdyLAjuA3ESTcrCSmS6iWcmxBDT8gjuTbf5rG4+h0gsZ2eMGgzIHtuSXLTZ/xR/iXiARxHnfkBQ3OuP9fq9vXd3v4lNo/GG5VCGC57WsO7eqtj/kuTYBS/b8YClTpPkuiWM0gZm41VCO+dj8pAfyVHqnsedsJI6TBFIvNOHWlA4ALxNVt7DVMwSa2bzqsCqzf6y1nB7JA6BQ/+rcAUu2n5CREV98SkmXm94nwnWYdP1IUCRyS9/5kSzUoS++JCTHJcBpLvpJhi1yR2iQk4tebY7PPyZzlVWfZoVPROmfgSyfLVF0yznUoFRJQdKps+jY88nMSivXabqVOFHtiCaV8u3uSe0kPld4zsYRDDc4ujl2xJR5AN3q8OeRvvb9Mxhxs9bjxa5KdKAwMvzbQbq/mwgjd9siXUizBEYRDDc4ujl2xJR5AN3q8Oe1WWULX5oIJzwrbxFaliZTRLbhH0MNlXHePf60sunDcFG4X+UjvIZDl0Se0IQy2dVnsoNyj9nbfWSjkXB5sG8/RTllnZC81hhWPgxy+x2ZmXayxvT1iTUpRrGE132K7Dr',
            'BDUSS': 'FNjTVdCSDA3N0taLU5DeE40VGZKYkU5WGt5NXk3WlpscHpVOXFsRGFiYlVCb3BwRVFBQUFBJCQAAAAAAAAAAAEAAACnas8nd2FrZXVwODMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANR5YmnUeWJpR',
            'BDUSS_BFESS': 'FNjTVdCSDA3N0taLU5DeE40VGZKYkU5WGt5NXk3WlpscHpVOXFsRGFiYlVCb3BwRVFBQUFBJCQAAAAAAAAAAAEAAACnas8nd2FrZXVwODMAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAANR5YmnUeWJpR',
            'STOKEN': '8482b787308aabe90ae88d80136808dfe4d5f32c25c8d6c4c36f607e493daac6',
            'ab_sr': '1.0.1_ZjdhYzk5MGVlM2QwNTZkZGExNzE1NzM0YTI0NTBkNGE2NTY0OGU3OTZlY2NmN2ZhOGM2MzA2NGNjYzQ4NGMzZDZlY2Q2NzA4OGI2YTRhOTgwOWQ3YmFmYTA5ZWFlYzA4N2EyNDE5ZTM1M2FkZGE2ZTZjZTI0MmI0ZjZhZWU0MTRlMmJiNDVlZGU2YWY0ZjQyZGVhNzFmNjdlMzY0ZjA1YjE5ZTdlNjZhMWQ4MzEyODI2ZWViMGVkZGMxMmZlYmE2',
            'RT': 'z=1&dm=baidu.com&si=5eeab8d6-5ab3-4c44-a465-419140fb81f2&ss=mk7mvxyt&sl=4m&tt=17706&bcn=https%3A%2F%2Ffclog.baidu.com%2Flog%2Fweirwood%3Ftype%3Dperf',
            'JSESSIONID': 'BDfhL2TSbggDJJ6s84vS91n0SvW2fkSSeR5Q7QNq'
        }
        
        # 请求头
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Connection': 'keep-alive',
            'Lingjing-Operation': 'unKnow',
            'Referer': 'https://agents.baidu.com/agent/list/codeless',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
            'User-Session': 'd084c340-2d46-4b2c-8cd5-22bbb24b4f89',
            'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"'
        }
        
        self.session = requests.Session()
        self.session.cookies.update(self.cookies)
        self.session.headers.update(self.headers)
    
    def get_agent_list(self) -> List[Dict]:
        """获取 Agent 列表"""
        url = 'https://agents.baidu.com/lingjing/agent/list'
        params = {
            'agentSource': 1,
            'agentType': 1,
            'pageNo': 1,
            'pageSize': 50
        }
        
        print("正在获取 Agent 列表...")
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('errno') == 0:
                agent_list = data.get('data', {}).get('agentList', [])
                print(f"成功获取 {len(agent_list)} 个 Agent")
                return agent_list
            else:
                print(f"获取 Agent 列表失败: {data.get('msg', '未知错误')}")
                return []
        except Exception as e:
            print(f"获取 Agent 列表时发生错误: {e}")
            return []
    
    def save_agent_list_to_csv(self, agent_list: List[Dict], filename: str = 'agent_list.csv'):
        """将 Agent 列表保存为 CSV 文件"""
        if not agent_list:
            print("Agent 列表为空，无法保存")
            return
        
        # 获取所有可能的字段（展平嵌套结构）
        all_fields = set()
        for agent in agent_list:
            all_fields.update(agent.keys())
        
        # 排序字段，将常用字段放在前面
        priority_fields = ['appId', 'name', 'agentType', 'agentSource', 'description', 
                          'logoUrl', 'status', 'onlineTime', 'permission']
        fields = priority_fields + sorted([f for f in all_fields if f not in priority_fields])
        
        print(f"正在保存 Agent 列表到 {filename}...")
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            
            for agent in agent_list:
                # 处理嵌套字段和 None 值
                row = {}
                for field in fields:
                    value = agent.get(field)
                    if value is None:
                        row[field] = ''
                    elif isinstance(value, (list, dict)):
                        row[field] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[field] = value
                writer.writerow(row)
        
        print(f"Agent 列表已保存到 {filename}")
    
    def get_last_7_days_timestamps(self) -> tuple:
        """获取最近7天的时间戳（startTime 和 endTime）"""
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)
        
        start_of_period = seven_days_ago.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_period = today.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        start_time = int(start_of_period.timestamp())
        end_time = int(end_of_period.timestamp())
        
        return start_time, end_time
    
    def get_last_7_days_dates(self) -> List[str]:
        """获取最近7天的日期字符串列表，格式：['2025/12/28', '2025/12/29', ...]"""
        dates = []
        for i in range(7, 0, -1):  # 从7天前到今天
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime('%Y/%m/%d'))
        return dates
    
    def get_agent_statistics(self, app_id: str, start_time: int, end_time: int) -> Optional[Dict]:
        """获取单个 Agent 的统计数据"""
        url = 'https://agents.baidu.com/lingjing/agent/statistics/all/detail'
        params = {
            'pageNo': 1,
            'pageSize': 20,  # 增加到20，确保能获取7天的数据
            'appId': app_id,
            'startTime': start_time,
            'endTime': end_time
        }
        
        # 使用不同的 User-Session 和 Referer 来避免被封
        headers = self.headers.copy()
        headers['Lingjing-Operation'] = 'editAgent'
        headers['Referer'] = f'https://agents.baidu.com/agent/prompt/edit?appId={app_id}&activeTab=analysis'
        headers['User-Session'] = f'{random.randint(10000000, 99999999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100000000000, 999999999999)}'
        
        try:
            # 添加随机延迟，避免被封
            time.sleep(random.uniform(1, 3))
            
            response = self.session.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if data.get('errno') == 0:
                return data.get('data', {})
            else:
                print(f"获取 Agent {app_id} 统计数据失败: {data.get('msg', '未知错误')}")
                return None
        except Exception as e:
            print(f"获取 Agent {app_id} 统计数据时发生错误: {e}")
            return None
    
    def extract_last_7_days_rounds(self, data_list: List[Dict], dates: List[str]) -> Dict[str, int]:
        """从数据列表中提取最近7天的 rounds，返回日期到rounds的字典"""
        rounds_dict = {}
        # 先初始化所有日期为0
        for date in dates:
            rounds_dict[date] = 0
        
        # 从返回的数据中提取
        for item in data_list:
            date = item.get('date')
            if date in rounds_dict:
                rounds_dict[date] = item.get('rounds', 0)
        
        return rounds_dict
    
    def process_all_agents(self, agent_list: List[Dict]) -> List[Dict]:
        """处理所有 Agent，获取最近7天的 rounds 数据"""
        start_time, end_time = self.get_last_7_days_timestamps()
        dates = self.get_last_7_days_dates()
        
        print(f"\n开始处理 {len(agent_list)} 个 Agent，查询最近7天数据")
        print(f"日期范围: {dates[0]} 至 {dates[-1]}")
        print(f"时间戳范围: {start_time} - {end_time}\n")
        
        results = []
        daily_totals = {date: 0 for date in dates}  # 每天的总计
        
        for idx, agent in enumerate(agent_list, 1):
            app_id = agent.get('appId')
            name = agent.get('name', '未知')
            
            print(f"[{idx}/{len(agent_list)}] 正在处理: {name} ({app_id})")
            
            stats_data = self.get_agent_statistics(app_id, start_time, end_time)
            
            if stats_data:
                data_list = stats_data.get('dataList', [])
                rounds_dict = self.extract_last_7_days_rounds(data_list, dates)
                
                # 计算7天总计
                total_rounds = sum(rounds_dict.values())
                
                # 更新每天的总计
                for date, rounds in rounds_dict.items():
                    daily_totals[date] += rounds
                
                result = {
                    'appId': app_id,
                    'name': name,
                    **rounds_dict,  # 展开每天的rounds数据
                    'total_7days': total_rounds
                }
                results.append(result)
                print(f"  ✓ 获取成功: 7天总计 rounds = {total_rounds}")
            else:
                # 如果获取失败，所有日期都设为0
                result = {
                    'appId': app_id,
                    'name': name,
                    **{date: 0 for date in dates},
                    'total_7days': 0
                }
                results.append(result)
                print(f"  ✗ 获取失败，设置为 0")
        
        print(f"\n所有 Agent 处理完成！")
        print(f"最近7天每日总计:")
        for date in dates:
            print(f"  {date}: {daily_totals[date]} rounds")
        print(f"7天总 rounds: {sum(daily_totals.values())}")
        
        return results, daily_totals
    
    def save_rounds_summary_to_csv(self, results: List[Dict], daily_totals: Dict[str, int], 
                                   filename: str = 'last_7_days_rounds_summary.csv'):
        """保存最近7天的 rounds 汇总数据到 CSV"""
        print(f"\n正在保存汇总数据到 {filename}...")
        
        if not results:
            print("没有数据可保存")
            return
        
        # 获取所有日期字段（除了appId, name, total_7days）
        dates = sorted([k for k in results[0].keys() if k not in ['appId', 'name', 'total_7days']])
        fieldnames = ['appId', 'name'] + dates + ['total_7days']
        
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            # 写入每个Agent的数据
            for result in results:
                writer.writerow(result)
            
            # 添加汇总行
            summary_row = {
                'appId': '总计',
                'name': '所有 Agent',
                **{date: daily_totals.get(date, 0) for date in dates},
                'total_7days': sum(daily_totals.values())
            }
            writer.writerow(summary_row)
        
        print(f"汇总数据已保存到 {filename}")
    
    @staticmethod
    def find_low_performance_agents(
        agent_list_file: str = 'agent_list.csv',
        rounds_summary_file: str = 'last_7_days_rounds_summary.csv',
        days_threshold: int = 10,
        rounds_threshold: int = 20
    ) -> List[Dict]:
        """查找 onlineTime 大于指定天数且对话数少于指定阈值的 Agent
        
        Args:
            agent_list_file: Agent 列表 CSV 文件路径
            rounds_summary_file: Rounds 汇总 CSV 文件路径
            days_threshold: onlineTime 天数阈值（默认10天）
            rounds_threshold: 对话数阈值（默认20）
            
        Returns:
            符合条件的 Agent 列表
        """
        if not os.path.exists(agent_list_file):
            print(f"错误: 文件 {agent_list_file} 不存在")
            return []
        
        if not os.path.exists(rounds_summary_file):
            print(f"错误: 文件 {rounds_summary_file} 不存在")
            return []
        
        # 读取 Agent 列表
        agents = {}
        with open(agent_list_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                app_id = row.get('appId')
                if app_id:
                    agents[app_id] = row
        
        # 读取 Rounds 汇总数据
        rounds_data = {}
        with open(rounds_summary_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                app_id = row.get('appId')
                if app_id and app_id != '总计':  # 跳过总计行
                    total_rounds = row.get('total_7days', '0')
                    try:
                        rounds_data[app_id] = int(total_rounds)
                    except ValueError:
                        rounds_data[app_id] = 0
        
        # 计算10天前的时间戳（毫秒）
        ten_days_ago = datetime.now() - timedelta(days=days_threshold)
        ten_days_ago_timestamp = int(ten_days_ago.timestamp() * 1000)
        
        # 筛选符合条件的 Agent
        low_performance_agents = []
        
        for app_id, agent in agents.items():
            # 获取 onlineTime
            online_time_str = agent.get('onlineTime', '0')
            try:
                online_time = int(online_time_str) if online_time_str else 0
            except ValueError:
                online_time = 0
            
            # 获取对话数（如果没有数据，默认为0）
            total_rounds = rounds_data.get(app_id, 0)
            
            # 判断条件：onlineTime > 10天前 且 total_7days < 20
            if online_time > 0 and online_time < ten_days_ago_timestamp and total_rounds < rounds_threshold:
                # 计算上线天数
                online_datetime = datetime.fromtimestamp(online_time / 1000)
                days_online = (datetime.now() - online_datetime).days
                
                low_performance_agents.append({
                    'appId': app_id,
                    'name': agent.get('name', '未知'),
                    'onlineTime': online_time,
                    'onlineDate': online_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'daysOnline': days_online,
                    'totalRounds': total_rounds
                })
        
        # 按上线时间排序（最早的在前面）
        low_performance_agents.sort(key=lambda x: x['onlineTime'])
        
        return low_performance_agents
    
    @staticmethod
    def print_low_performance_agents(agents: List[Dict], output_file: Optional[str] = None):
        """打印或保存低性能 Agent 列表
        
        Args:
            agents: Agent 列表
            output_file: 可选，输出文件路径（CSV格式）
        """
        if not agents:
            print("\n未找到符合条件的 Agent")
            return
        
        print(f"\n找到 {len(agents)} 个符合条件的 Agent（上线超过10天且最近7天对话数少于20）:")
        print("=" * 100)
        print(f"{'序号':<6} {'App ID':<35} {'名称':<30} {'上线日期':<20} {'上线天数':<10} {'7天对话数':<10}")
        print("-" * 100)
        
        for idx, agent in enumerate(agents, 1):
            print(f"{idx:<6} {agent['appId']:<35} {agent['name']:<30} {agent['onlineDate']:<20} "
                  f"{agent['daysOnline']:<10} {agent['totalRounds']:<10}")
        
        print("=" * 100)
        print(f"\n总计: {len(agents)} 个 Agent")
        
        # 如果指定了输出文件，保存为 CSV
        if output_file:
            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                fieldnames = ['appId', 'name', 'onlineTime', 'onlineDate', 'daysOnline', 'totalRounds']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(agents)
            print(f"\n结果已保存到: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='获取百度灵境 Agent 数据并生成报表',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用示例:
  # 从文件读取 curl 命令
  python fetch_agents_data.py --curl-file curl.txt
  
  # 直接传入 curl 命令（需要加引号）
  python fetch_agents_data.py --curl "curl 'https://...' -H '...'"
  
  # 自定义 CSV 文件名
  python fetch_agents_data.py --agent-list-csv my_agents.csv --rounds-summary-csv my_summary.csv
  
  # 查找低性能 Agent（上线超过10天且对话数少于20）
  python fetch_agents_data.py --find-low-performance
  
  # 查找低性能 Agent 并保存到文件
  python fetch_agents_data.py --find-low-performance --output-low-performance low_performance_agents.csv
  
  # 自定义筛选条件（上线超过15天且对话数少于10）
  python fetch_agents_data.py --find-low-performance --days-threshold 15 --rounds-threshold 10
  
  # 使用默认配置
  python fetch_agents_data.py
        '''
    )
    parser.add_argument(
        '--curl',
        type=str,
        help='curl 命令字符串'
    )
    parser.add_argument(
        '--curl-file',
        type=str,
        default='curl.txt',
        help='包含 curl 命令的文件路径（默认: curl.txt）'
    )
    parser.add_argument(
        '--agent-list-csv',
        type=str,
        default='agent_list.csv',
        help='Agent 列表 CSV 文件名（默认: agent_list.csv）'
    )
    parser.add_argument(
        '--rounds-summary-csv',
        type=str,
        default='last_7_days_rounds_summary.csv',
        help='最近7天 rounds 汇总 CSV 文件名（默认: last_7_days_rounds_summary.csv）'
    )
    parser.add_argument(
        '--find-low-performance',
        action='store_true',
        help='查找 onlineTime 大于10天且对话数少于20的 Agent'
    )
    parser.add_argument(
        '--days-threshold',
        type=int,
        default=10,
        help='onlineTime 天数阈值（默认: 10天）'
    )
    parser.add_argument(
        '--rounds-threshold',
        type=int,
        default=20,
        help='对话数阈值（默认: 20）'
    )
    parser.add_argument(
        '--output-low-performance',
        type=str,
        help='低性能 Agent 列表输出文件路径（CSV格式）'
    )
    
    args = parser.parse_args()
    
    # 如果指定了查找低性能 Agent，只执行筛选功能
    if args.find_low_performance:
        print(f"正在查找符合条件的 Agent（上线超过{args.days_threshold}天且最近7天对话数少于{args.rounds_threshold}）...")
        low_performance_agents = AgentsDataFetcher.find_low_performance_agents(
            agent_list_file=args.agent_list_csv,
            rounds_summary_file=args.rounds_summary_csv,
            days_threshold=args.days_threshold,
            rounds_threshold=args.rounds_threshold
        )
        AgentsDataFetcher.print_low_performance_agents(
            low_performance_agents,
            output_file=args.output_low_performance
        )
        return
    
    # 确定使用哪种方式初始化
    curl_cmd = None
    curl_file = None
    
    if args.curl:
        curl_cmd = args.curl
        print("使用命令行传入的 curl 命令")
    elif args.curl_file and os.path.exists(args.curl_file):
        curl_file = args.curl_file
        print(f"从文件 {curl_file} 读取 curl 命令")
    else:
        if args.curl_file:
            print(f"警告: 文件 {args.curl_file} 不存在，使用默认配置")
        else:
            print("使用默认配置")
    
    # 初始化 fetcher
    fetcher = AgentsDataFetcher(curl_cmd=curl_cmd, curl_file=curl_file)
    
    # 1. 获取 Agent 列表
    agent_list = fetcher.get_agent_list()
    
    if not agent_list:
        print("无法获取 Agent 列表，程序退出")
        return
    
    # 2. 保存 Agent 列表到 CSV
    fetcher.save_agent_list_to_csv(agent_list, args.agent_list_csv)
    
    # 3. 处理所有 Agent，获取最近7天的 rounds 数据
    results, daily_totals = fetcher.process_all_agents(agent_list)
    
    # 4. 保存汇总数据到 CSV
    fetcher.save_rounds_summary_to_csv(results, daily_totals, args.rounds_summary_csv)
    
    print("\n所有任务完成！")


if __name__ == '__main__':
    main()

