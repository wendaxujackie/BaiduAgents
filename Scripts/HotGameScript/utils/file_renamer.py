# -*- coding: utf-8 -*-
"""
文件重命名模块
按照APK关键词规则批量重命名文件
"""
import random
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path

from loguru import logger

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import APK_KEYWORDS, APK_COPIES_COUNT, APK_TARGET_FOLDER, BASE_DIR


class FileRenamer:
    """文件重命名器"""
    
    def __init__(self, target_folder: Path = None):
        """
        初始化文件重命名器
        
        Args:
            target_folder: 目标文件夹
        """
        self.target_folder = target_folder or BASE_DIR / APK_TARGET_FOLDER
        self.target_folder.mkdir(parents=True, exist_ok=True)
        self.keywords = APK_KEYWORDS.copy()
    
    def shuffle_keywords(self) -> List[str]:
        """
        使用Fisher-Yates算法洗牌关键词
        
        Returns:
            洗牌后的关键词列表
        """
        shuffled = self.keywords.copy()
        n = len(shuffled)
        
        for i in range(n - 1, 0, -1):
            j = random.randint(0, i)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        
        return shuffled
    
    def generate_keyword_filename(self, base_name: str, keyword: str) -> str:
        """
        生成带关键词的文件名
        
        Args:
            base_name: 基础文件名（不含扩展名）
            keyword: 关键词
            
        Returns:
            新文件名
        """
        return f"{base_name}{keyword}.apk"
    
    def rename_single_file(self, source_path: Path, game_name: str) -> List[Path]:
        """
        为单个APK文件生成关键词副本
        
        Args:
            source_path: 源文件路径
            game_name: 游戏名称（用于命名）
            
        Returns:
            生成的文件路径列表
        """
        if not source_path.exists():
            logger.error(f"源文件不存在: {source_path}")
            return []
        
        if not source_path.suffix.lower() == '.apk':
            logger.warning(f"文件不是APK格式: {source_path}")
        
        created_files = []
        shuffled_keywords = self.shuffle_keywords()
        
        # 清理游戏名称
        safe_name = self._sanitize_name(game_name)
        
        logger.info(f"正在为 [{safe_name}] 生成 {APK_COPIES_COUNT} 个关键词副本...")
        
        copy_count = 0
        keyword_index = 0
        
        while copy_count < APK_COPIES_COUNT and keyword_index < len(shuffled_keywords):
            keyword = shuffled_keywords[keyword_index]
            new_name = self.generate_keyword_filename(safe_name, keyword)
            new_path = self.target_folder / new_name
            
            if new_path.exists():
                logger.info(f"跳过: {new_name} 已存在")
                keyword_index += 1
                continue
            
            try:
                shutil.copy2(str(source_path), str(new_path))
                created_files.append(new_path)
                copy_count += 1
                logger.info(f"创建副本 {copy_count}: {new_name}")
            except Exception as e:
                logger.error(f"创建副本失败: {e}")
            
            keyword_index += 1
        
        # 移动原始文件到目标文件夹
        original_dest = self.target_folder / source_path.name
        if not original_dest.exists() and source_path.exists():
            try:
                shutil.move(str(source_path), str(original_dest))
                logger.info(f"移动原始文件: {source_path.name}")
            except Exception as e:
                logger.warning(f"移动原始文件失败: {e}")
        
        logger.success(f"完成: 为 [{safe_name}] 创建了 {len(created_files)} 个副本")
        return created_files
    
    def rename_batch(self, file_mapping: Dict[Path, str]) -> Dict[str, Any]:
        """
        批量处理文件
        
        Args:
            file_mapping: 源文件路径到游戏名称的映射
            
        Returns:
            处理结果
        """
        results = {
            "total_files": len(file_mapping),
            "total_copies": 0,
            "processed_files": [],
            "errors": []
        }
        
        for source_path, game_name in file_mapping.items():
            try:
                created = self.rename_single_file(source_path, game_name)
                results["total_copies"] += len(created)
                results["processed_files"].append({
                    "source": str(source_path),
                    "game_name": game_name,
                    "copies_created": len(created)
                })
            except Exception as e:
                results["errors"].append({
                    "source": str(source_path),
                    "error": str(e)
                })
        
        return results
    
    def process_directory(self, source_dir: Path, name_extractor=None) -> Dict[str, Any]:
        """
        处理整个目录中的APK文件
        
        Args:
            source_dir: 源目录
            name_extractor: 从文件名提取游戏名的函数
            
        Returns:
            处理结果
        """
        if not source_dir.exists():
            logger.error(f"源目录不存在: {source_dir}")
            return {"error": "源目录不存在"}
        
        apk_files = list(source_dir.glob("*.apk"))
        
        if not apk_files:
            logger.warning(f"目录中没有APK文件: {source_dir}")
            return {"error": "没有找到APK文件"}
        
        logger.info(f"发现 {len(apk_files)} 个APK文件")
        
        # 创建文件映射
        file_mapping = {}
        for apk_file in apk_files:
            if name_extractor:
                game_name = name_extractor(apk_file.stem)
            else:
                game_name = apk_file.stem  # 使用文件名作为游戏名
            
            file_mapping[apk_file] = game_name
        
        return self.rename_batch(file_mapping)
    
    def _sanitize_name(self, name: str) -> str:
        """清理文件名"""
        # 移除非法字符
        illegal_chars = '<>:"/\\|?*'
        for char in illegal_chars:
            name = name.replace(char, '')
        
        # 移除前后空白
        name = name.strip()
        
        # 限制长度
        if len(name) > 100:
            name = name[:100]
        
        return name
    
    def get_folder_statistics(self) -> Dict[str, Any]:
        """
        获取目标文件夹统计信息
        
        Returns:
            统计信息
        """
        if not self.target_folder.exists():
            return {"exists": False}
        
        apk_files = list(self.target_folder.glob("*.apk"))
        
        # 按关键词分组统计
        keyword_stats = {}
        for keyword in self.keywords:
            count = sum(1 for f in apk_files if keyword in f.stem)
            keyword_stats[keyword] = count
        
        # 计算总大小
        total_size = sum(f.stat().st_size for f in apk_files)
        
        return {
            "exists": True,
            "path": str(self.target_folder),
            "total_files": len(apk_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "keyword_distribution": keyword_stats
        }
