# -*- coding: utf-8 -*-
"""
CSV处理模块
负责游戏数据的读写操作
"""
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

import pandas as pd
from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import GAMES_CSV_PATH, DATA_DIR


class CSVHandler:
    """CSV文件处理器"""
    
    def __init__(self, csv_path: Path = None):
        """
        初始化CSV处理器
        
        Args:
            csv_path: CSV文件路径
        """
        self.csv_path = csv_path or GAMES_CSV_PATH
        
        # 确保目录存在
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    def read_games(self) -> List[Dict[str, Any]]:
        """
        读取游戏数据
        
        Returns:
            游戏数据列表
        """
        if not self.csv_path.exists():
            logger.warning(f"CSV文件不存在: {self.csv_path}")
            return []
        
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            games = df.to_dict('records')
            logger.info(f"从CSV读取了 {len(games)} 条游戏记录")
            return games
        except Exception as e:
            logger.error(f"读取CSV失败: {e}")
            return []
    
    def read_game_names(self) -> List[str]:
        """
        只读取游戏名称列表
        
        Returns:
            游戏名称列表
        """
        games = self.read_games()
        names = []
        
        for game in games:
            name = game.get('game_name') or game.get('name')
            if name:
                names.append(str(name).strip())
        
        # 去重
        names = list(dict.fromkeys(names))
        logger.info(f"获取到 {len(names)} 个唯一游戏名称")
        return names
    
    def write_games(self, games: List[Dict[str, Any]], append: bool = True):
        """
        写入游戏数据
        
        Args:
            games: 游戏数据列表
            append: 是否追加模式
        """
        if not games:
            logger.warning("没有数据可写入")
            return
        
        try:
            # 确保每条记录都有game_name字段
            for game in games:
                if 'name' in game and 'game_name' not in game:
                    game['game_name'] = game['name']
            
            df_new = pd.DataFrame(games)
            
            if append and self.csv_path.exists():
                # 读取现有数据
                df_existing = pd.read_csv(self.csv_path, encoding='utf-8-sig')
                
                # 合并数据
                df = pd.concat([df_existing, df_new], ignore_index=True)
                
                # 去重
                if 'game_name' in df.columns:
                    df = df.drop_duplicates(subset=['game_name'], keep='last')
            else:
                df = df_new
            
            # 添加更新时间
            df['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 保存
            df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
            logger.success(f"保存了 {len(df)} 条游戏记录到: {self.csv_path}")
            
        except Exception as e:
            logger.error(f"写入CSV失败: {e}")
    
    def add_game(self, game_name: str, **extra_fields):
        """
        添加单个游戏
        
        Args:
            game_name: 游戏名称
            **extra_fields: 额外字段
        """
        game_data = {
            "game_name": game_name,
            **extra_fields
        }
        self.write_games([game_data], append=True)
    
    def remove_game(self, game_name: str) -> bool:
        """
        删除游戏记录
        
        Args:
            game_name: 游戏名称
            
        Returns:
            是否成功删除
        """
        if not self.csv_path.exists():
            return False
        
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            
            if 'game_name' not in df.columns:
                return False
            
            original_count = len(df)
            df = df[df['game_name'] != game_name]
            
            if len(df) < original_count:
                df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
                logger.info(f"已删除游戏: {game_name}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除游戏失败: {e}")
            return False
    
    def search_games(self, keyword: str) -> List[Dict[str, Any]]:
        """
        搜索游戏
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的游戏列表
        """
        games = self.read_games()
        keyword_lower = keyword.lower()
        
        matched = []
        for game in games:
            name = str(game.get('game_name', '')).lower()
            if keyword_lower in name:
                matched.append(game)
        
        return matched
    
    def update_game(self, game_name: str, **fields):
        """
        更新游戏记录
        
        Args:
            game_name: 游戏名称
            **fields: 要更新的字段
        """
        if not self.csv_path.exists():
            return
        
        try:
            df = pd.read_csv(self.csv_path, encoding='utf-8-sig')
            
            if 'game_name' not in df.columns:
                return
            
            mask = df['game_name'] == game_name
            
            if mask.any():
                for field, value in fields.items():
                    df.loc[mask, field] = value
                
                df.to_csv(self.csv_path, index=False, encoding='utf-8-sig')
                logger.info(f"已更新游戏: {game_name}")
                
        except Exception as e:
            logger.error(f"更新游戏失败: {e}")
    
    def export_to_txt(self, output_path: Path = None) -> Path:
        """
        导出游戏名称到TXT文件
        
        Args:
            output_path: 输出路径
            
        Returns:
            导出的文件路径
        """
        output_path = output_path or DATA_DIR / "game_names.txt"
        
        names = self.read_game_names()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for name in names:
                    f.write(f"{name}\n")
            
            logger.success(f"导出了 {len(names)} 个游戏名称到: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        games = self.read_games()
        
        stats = {
            "total_games": len(games),
            "csv_path": str(self.csv_path),
            "file_exists": self.csv_path.exists(),
        }
        
        if games:
            # 统计各字段的填充率
            df = pd.DataFrame(games)
            for col in df.columns:
                non_null = df[col].notna().sum()
                stats[f"{col}_fill_rate"] = f"{non_null}/{len(df)}"
        
        return stats
