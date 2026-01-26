# -*- coding: utf-8 -*-
"""
游戏名称识别模块
使用OCR和自然语言处理从截图中提取游戏名称
支持网络搜索验证游戏名称
"""
import re
import time
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from urllib.parse import quote

from loguru import logger
import jieba
import jieba.analyse
import requests

# 尝试导入PaddleOCR（推荐）
try:
    from paddleocr import PaddleOCR
    HAS_PADDLE_OCR = True
except ImportError:
    HAS_PADDLE_OCR = False
    logger.warning("PaddleOCR未安装，将尝试使用其他OCR方案")

# 尝试导入Tesseract
try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

# 尝试导入Mac Vision框架（macOS原生OCR）
HAS_VISION = False
try:
    import platform
    if platform.system() == 'Darwin':  # macOS
        import Vision
        import Quartz
        from Foundation import NSURL
        HAS_VISION = True
        logger.info("✅ Mac Vision OCR 可用")
except ImportError:
    pass

import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import OCR_CONFIG, GAME_KEYWORDS, EXCLUDE_KEYWORDS, GAMES_CSV_PATH


class GameRecognizer:
    """游戏名称识别器"""
    
    def __init__(self, use_paddle: bool = True):
        """
        初始化游戏名称识别器
        
        Args:
            use_paddle: 是否优先使用PaddleOCR
        """
        self.ocr_engine = None
        self.use_paddle = use_paddle and HAS_PADDLE_OCR
        
        # 已识别的游戏名称缓存
        self.recognized_games: Set[str] = set()
        
        # 初始化OCR引擎
        self._init_ocr()
        
        # 加载已有的游戏数据
        self._load_existing_games()
    
    def _init_ocr(self):
        """初始化OCR引擎"""
        if self.use_paddle:
            try:
                # 使用最简参数初始化（兼容所有版本）
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                )
                logger.info("PaddleOCR引擎初始化成功")
            except Exception as e:
                logger.error(f"PaddleOCR初始化失败: {e}")
                self.use_paddle = False
        
        if not self.use_paddle and HAS_TESSERACT:
            logger.info("使用Tesseract作为OCR引擎")
        elif not self.use_paddle and not HAS_TESSERACT:
            logger.warning("没有可用的OCR引擎，OCR功能将被禁用")
    
    def _load_existing_games(self):
        """从CSV文件加载已有的游戏名称"""
        try:
            if GAMES_CSV_PATH.exists():
                import pandas as pd
                df = pd.read_csv(GAMES_CSV_PATH)
                if 'game_name' in df.columns:
                    self.recognized_games = set(df['game_name'].dropna().tolist())
                    logger.info(f"从CSV加载了 {len(self.recognized_games)} 个已识别的游戏")
        except Exception as e:
            logger.warning(f"加载已有游戏数据时出错: {e}")
    
    def ocr_with_mac_vision(self, image_path: Path) -> List[str]:
        """
        使用Mac原生Vision框架进行OCR（效果更好，文字更连贯）
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别出的文本列表
        """
        if not HAS_VISION:
            return []
        
        texts = []
        try:
            # 加载图片
            image_url = NSURL.fileURLWithPath_(str(image_path))
            ci_image = Quartz.CIImage.imageWithContentsOfURL_(image_url)
            
            if ci_image is None:
                logger.warning(f"Vision无法加载图片: {image_path}")
                return []
            
            # 创建文字识别请求
            request = Vision.VNRecognizeTextRequest.alloc().init()
            request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
            request.setRecognitionLanguages_(['zh-Hans', 'zh-Hant', 'en'])  # 简体中文、繁体中文、英文
            request.setUsesLanguageCorrection_(True)
            
            # 创建处理器并执行
            handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(ci_image, None)
            success = handler.performRequests_error_([request], None)
            
            if success and request.results():
                for observation in request.results():
                    # 获取识别的文本（置信度最高的候选）
                    if observation.topCandidates_(1):
                        text = observation.topCandidates_(1)[0].string()
                        confidence = observation.confidence()
                        if text and confidence > 0.5:
                            texts.append(text.strip())
                
                if texts:
                    logger.info(f"🍎 Mac Vision识别出 {len(texts)} 条文本:")
                    for t in texts:
                        logger.info(f"  📝 {t}")
            
        except Exception as e:
            logger.warning(f"Mac Vision OCR失败: {e}")
        
        return texts
    
    def ocr_image(self, image_path: Path) -> List[str]:
        """
        对图片进行OCR识别（合并Mac Vision和PaddleOCR的结果）
        
        Args:
            image_path: 图片路径
            
        Returns:
            识别出的文本列表
        """
        if not image_path.exists():
            logger.error(f"图片不存在: {image_path}")
            return []
        
        all_texts = []
        
        # 方法1: Mac Vision OCR（对带特效文字效果不好，暂时禁用）
        # if HAS_VISION:
        #     vision_texts = self.ocr_with_mac_vision(image_path)
        #     if vision_texts:
        #         all_texts.extend(vision_texts)
        
        texts = []
        
        # 方法2: PaddleOCR（识别率更高）
        if self.use_paddle and self.ocr_engine:
            try:
                result = self.ocr_engine.ocr(str(image_path))
                if result:
                    for page in result:
                        # 新版PaddleOCR返回字典格式
                        if isinstance(page, dict):
                            rec_texts = page.get('rec_texts', [])
                            rec_scores = page.get('rec_scores', [])
                            for i, text in enumerate(rec_texts):
                                score = rec_scores[i] if i < len(rec_scores) else 1.0
                                if score > 0.5 and text.strip():
                                    texts.append(text.strip())
                        # 旧版PaddleOCR返回列表格式
                        elif isinstance(page, list):
                            for line in page:
                                try:
                                    if isinstance(line, list) and len(line) >= 2:
                                        text_info = line[1]
                                        if isinstance(text_info, (tuple, list)):
                                            text = str(text_info[0])
                                            confidence = float(text_info[1]) if len(text_info) > 1 else 1.0
                                        else:
                                            text = str(text_info)
                                            confidence = 1.0
                                        if confidence > 0.5 and text.strip():
                                            texts.append(text.strip())
                                except Exception:
                                    continue
                
                # 过滤掉无用文本（教程类）
                filter_keywords = ['教程', '安装教程', '机版安装', '攻略', '礼包码']
                filtered_texts = []
                for t in texts:
                    if not any(kw in t for kw in filter_keywords):
                        filtered_texts.append(t)
                    else:
                        logger.debug(f"  🚫 过滤掉: {t}")
                texts = filtered_texts
                
                # 输出识别结果到日志
                if texts:
                    logger.info(f"OCR识别出 {len(texts)} 条有效文本:")
                    for t in texts:
                        logger.info(f"  📝 {t}")
                else:
                    logger.debug("OCR未识别出有效文本")
                    
            except Exception as e:
                logger.error(f"PaddleOCR识别失败: {e}")
        
        elif HAS_TESSERACT:
            try:
                image = Image.open(image_path)
                text = pytesseract.image_to_string(image, lang='chi_sim+eng')
                texts = [line.strip() for line in text.split('\n') if line.strip()]
                logger.debug(f"Tesseract识别出 {len(texts)} 条文本")
            except Exception as e:
                logger.error(f"Tesseract识别失败: {e}")
        
        # 合并所有OCR结果并去重
        all_texts.extend(texts)
        
        # 智能合并：如果有连续的文字（如"红楼梦galgame"），优先保留
        merged_texts = self._merge_ocr_texts(all_texts)
        
        return merged_texts
    
    def _merge_ocr_texts(self, texts: List[str]) -> List[str]:
        """
        智能合并OCR结果，处理分散的文字
        例如：['红楼梦', 'galgame'] -> ['红楼梦galgame']
        """
        if not texts:
            return []
        
        # 去重
        unique_texts = list(dict.fromkeys(texts))
        
        # 过滤无用文本
        filter_keywords = ['教程', '安装教程', '机版安装', '攻略', '礼包码']
        filtered = [t for t in unique_texts if not any(kw in t for kw in filter_keywords)]
        
        # 尝试合并相邻的中英文（如"红楼梦" + "galgame"）
        merged = []
        skip_next = set()
        
        for i, text in enumerate(filtered):
            if i in skip_next:
                continue
            
            # 检查是否可以和下一个文本合并
            if i + 1 < len(filtered):
                next_text = filtered[i + 1]
                
                # 如果当前是中文，下一个是英文，可能需要合并
                if self._is_chinese(text) and self._is_english(next_text):
                    merged.append(text + next_text)
                    skip_next.add(i + 1)
                    continue
                
                # 如果当前是英文，下一个是中文
                if self._is_english(text) and self._is_chinese(next_text):
                    merged.append(text + next_text)
                    skip_next.add(i + 1)
                    continue
            
            merged.append(text)
        
        return merged
    
    def _is_chinese(self, text: str) -> bool:
        """判断文本是否主要是中文"""
        chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return chinese_count > len(text) * 0.5
    
    def _is_english(self, text: str) -> bool:
        """判断文本是否主要是英文"""
        english_count = sum(1 for c in text if c.isascii() and c.isalpha())
        return english_count > len(text) * 0.5
    
    def extract_hashtags(self, texts: List[str]) -> List[str]:
        """
        从OCR文本中提取所有带#的标签
        
        Args:
            texts: OCR识别出的文本列表
            
        Returns:
            提取出的标签列表（不含#符号）
        """
        hashtags = []
        full_text = ' '.join(texts)
        
        # 方法1: 正则匹配 #标签
        # 匹配 #后面跟着的中英文字符
        pattern = r'#([^\s#@，。！？、：；""''【】《》\[\]]+)'
        matches = re.findall(pattern, full_text)
        
        for tag in matches:
            tag = tag.strip()
            if tag and len(tag) >= 2:
                hashtags.append(tag)
        
        # 方法2: 如果没找到#，尝试用空格分割找带#的部分
        if not hashtags:
            for text in texts:
                if '#' in text:
                    # 按#分割
                    parts = text.split('#')
                    for part in parts:
                        part = part.strip()
                        # 进一步按空格分割，取第一个词
                        if part:
                            word = part.split()[0] if ' ' in part else part
                            word = word.strip('，。！？、：；')
                            if word and len(word) >= 2:
                                hashtags.append(word)
        
        # 去重
        unique_hashtags = list(dict.fromkeys(hashtags))
        
        if unique_hashtags:
            logger.info(f"🏷️ 提取到 {len(unique_hashtags)} 个标签:")
            for tag in unique_hashtags:
                logger.info(f"  #{tag}")
        
        return unique_hashtags
    
    def extract_game_from_hashtags(self, hashtags: List[str]) -> Optional[str]:
        """
        从标签列表中提取游戏名称
        规则：去掉"下载"、"安装"、"攻略"等后缀，找到最短的基础名称
        
        Args:
            hashtags: 标签列表
            
        Returns:
            游戏名称
        """
        if not hashtags:
            return None
        
        # 后缀清理列表（按长度排序，先匹配长的）
        suffixes = [
            '怎么下载', '安卓下载', '苹果下载', 'ios下载',
            '手机版下载', '电脑版下载', '最新版下载',
            '下载安装', '安装教程', '下载教程',
            '下载', '安装', '攻略', '礼包', '礼包码',
            '手机版', '电脑版', '安卓版', 'ios版',
            '官方版', '正版', '破解版', '汉化版',
            '最新版', '老版本', '新版本',
        ]
        
        # 清理每个标签，提取基础名称
        base_names = []
        for tag in hashtags:
            name = tag
            for suffix in suffixes:
                if name.endswith(suffix):
                    name = name[:-len(suffix)]
                    break
            
            name = name.strip()
            if name and len(name) >= 2:
                base_names.append(name)
        
        if not base_names:
            return None
        
        # 找出现次数最多的基础名称
        from collections import Counter
        name_counts = Counter(base_names)
        most_common = name_counts.most_common(1)
        
        if most_common:
            game_name = most_common[0][0]
            logger.info(f"🎮 识别游戏名称: {game_name}")
            return game_name
        
        # 如果都只出现一次，返回最短的
        return min(base_names, key=len)
    
    def extract_game_names(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        从OCR文本中提取游戏名称
        新策略：只提取带#的标签，从标签中识别游戏名
        
        Args:
            texts: OCR识别出的文本列表
            
        Returns:
            提取出的游戏信息列表
        """
        games = []
        
        # 第一步：提取所有#标签
        hashtags = self.extract_hashtags(texts)
        
        if not hashtags:
            logger.warning("未找到任何#标签")
            return games
        
        # 第二步：从标签中提取游戏名
        game_name = self.extract_game_from_hashtags(hashtags)
        
        if game_name:
            games.append({
                "name": game_name,
                "original_text": ' '.join([f'#{t}' for t in hashtags]),
                "hashtags": hashtags,
                "score": len(hashtags),  # 标签越多，置信度越高
                "matched_keywords": ["hashtag_extract"]
            })
        
        return games
    
    def _extract_game_name_from_text(self, text: str) -> Optional[str]:
        """从文本中提取游戏名称"""
        # 移除常见后缀
        suffixes_to_remove = [
            '官方版', '正版', '手游', '手机版', '最新版', '中文版',
            '汉化版', '安卓版', '下载', '安装包', 'apk', 'APK',
            '破解版', '无限', '免费', '礼包码', '攻略',
        ]
        
        result = text
        for suffix in suffixes_to_remove:
            if result.endswith(suffix):
                result = result[:-len(suffix)]
        
        # 移除常见前缀
        prefixes_to_remove = ['下载', '推荐', '热门', '最新', '免费']
        for prefix in prefixes_to_remove:
            if result.startswith(prefix):
                result = result[len(prefix):]
        
        result = result.strip()
        
        # 验证结果
        if len(result) >= 2 and len(result) <= 20:
            return result
        
        return None
    
    def _clean_game_name(self, name: str) -> str:
        """清理游戏名称"""
        # 移除特殊字符
        name = re.sub(r'[^\w\u4e00-\u9fff\-]', '', name)
        return name.strip()
    
    def _is_likely_game_name(self, keyword: str, context: str) -> bool:
        """判断关键词是否可能是游戏名"""
        # 游戏名通常包含以下特征
        game_indicators = [
            '传奇', '仙侠', '武侠', '三国', '西游', '修仙', '奇迹',
            '战争', '策略', '卡牌', '冒险', '魔幻', '神话', '征途',
            '王者', '部落', '帝国', '世界', '大陆', '王国', '传说',
        ]
        
        # 检查是否包含游戏指示词
        if any(indicator in keyword for indicator in game_indicators):
            return True
        
        # 检查上下文中是否有游戏相关词
        context_lower = context.lower()
        if any(kw in context_lower for kw in ['游戏', '下载', 'game', 'apk', '手游']):
            if keyword in context:
                return True
        
        return False
    
    def verify_game_by_search(self, text: str) -> Dict[str, Any]:
        """
        通过网络搜索验证文本是否为游戏名称
        
        Args:
            text: 待验证的文本
            
        Returns:
            验证结果字典，包含 is_game, confidence, game_name 等
        """
        result = {
            "text": text,
            "is_game": False,
            "confidence": 0.0,
            "game_name": None,
            "search_hints": []
        }
        
        if not text or len(text) < 2:
            return result
        
        # 先清理文本，移除常见后缀
        clean_text = text
        suffixes = ['老版本', '新版本', '安装教程', '教程', '攻略', '下载', '安装包', '手机版', '电脑版', '安卓版']
        for suffix in suffixes:
            if clean_text.endswith(suffix):
                clean_text = clean_text[:-len(suffix)]
        
        # 排除明显不是游戏名的
        not_game_patterns = ['教程', '版本', '安装', '下载', '攻略', '礼包', '加面', '机版']
        if any(p in clean_text for p in not_game_patterns) or len(clean_text) < 2:
            return result
        
        # 使用清理后的文本搜索
        text = clean_text if len(clean_text) >= 2 else text
        
        try:
            # 搜索 "xxx 游戏下载"
            search_query = f"{text} 游戏下载"
            url = f"https://www.baidu.com/s?wd={quote(search_query)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.encoding = 'utf-8'
            html = response.text.lower()
            
            # 分析搜索结果中的关键词
            game_indicators = [
                ('taptap', 3),        # TapTap是专业游戏平台
                ('4399', 2),          # 4399游戏平台
                ('九游', 2),           # 九游游戏平台
                ('好游快爆', 2),        # 游戏资讯平台
                ('手游', 1),
                ('手机游戏', 1),
                ('安卓游戏', 1),
                ('ios游戏', 1),
                ('游戏下载', 1),
                ('apk下载', 1),
                ('游戏攻略', 1),
                ('游戏礼包', 1),
            ]
            
            score = 0
            hints = []
            
            for indicator, weight in game_indicators:
                if indicator in html:
                    score += weight
                    hints.append(indicator)
            
            # 检查是否在搜索结果中有明确的游戏相关描述
            if f'{text.lower()}是一款' in html or f'《{text.lower()}》' in html:
                score += 2
                hints.append('游戏介绍')
            
            # 计算置信度
            confidence = min(score / 10.0, 1.0)
            
            result["confidence"] = confidence
            result["search_hints"] = hints
            
            # 置信度阈值设为0.5，确保准确性
            if confidence >= 0.5:
                result["is_game"] = True
                result["game_name"] = clean_text if len(clean_text) >= 2 else text
                logger.info(f"🎮 网络验证: '{result['game_name']}' 确认为游戏 (置信度: {confidence:.2f}, 依据: {hints})")
            else:
                logger.debug(f"❓ 网络验证: '{text}' 可能不是游戏 (置信度: {confidence:.2f})")
            
            # 避免请求过快
            time.sleep(0.5)
            
        except Exception as e:
            logger.warning(f"网络搜索验证失败: {e}")
        
        return result
    
    def verify_texts_as_games(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        批量验证文本列表中哪些是游戏名称
        
        Args:
            texts: 待验证的文本列表
            
        Returns:
            验证结果列表
        """
        results = []
        verified_games = []
        
        for text in texts:
            # 先用本地规则快速过滤
            text = text.strip()
            if not text or len(text) < 2 or len(text) > 20:
                continue
            
            # 排除明显不是游戏名的
            if any(kw in text for kw in EXCLUDE_KEYWORDS):
                continue
            
            # 排除纯数字、纯英文等
            if text.isdigit() or (text.isascii() and len(text) < 4):
                continue
            
            # 网络搜索验证
            result = self.verify_game_by_search(text)
            results.append(result)
            
            if result["is_game"]:
                verified_games.append(result)
        
        logger.info(f"🔍 网络验证完成: {len(texts)} 个文本中有 {len(verified_games)} 个确认为游戏")
        return results
    
    def process_screenshot(self, image_path: Path, use_web_verify: bool = False) -> Dict[str, Any]:
        """
        处理单张截图，从#标签中提取游戏名称
        
        Args:
            image_path: 截图路径
            use_web_verify: 是否使用网络搜索验证游戏名称（默认关闭，因为标签已经很准确）
            
        Returns:
            包含标签和识别游戏的字典
        """
        logger.info(f"📸 处理截图: {image_path.name}")
        
        result = {
            "screenshot": image_path.name,
            "ocr_texts": [],       # 所有OCR原始文本
            "hashtags": [],        # 提取的#标签
            "game_name": None      # 识别的游戏名称
        }
        
        # OCR识别
        texts = self.ocr_image(image_path)
        result["ocr_texts"] = texts
        
        if not texts:
            logger.warning(f"截图 {image_path.name} 未识别出文本")
            return result
        
        # 从OCR结果中提取#标签
        hashtags = self.extract_hashtags(texts)
        result["hashtags"] = hashtags
        
        if not hashtags:
            logger.warning(f"截图 {image_path.name} 未找到#标签")
            return result
        
        # 从标签中提取游戏名
        game_name = self.extract_game_from_hashtags(hashtags)
        result["game_name"] = game_name
        
        # 网络验证（可选）
        if use_web_verify and game_name:
            verify_result = self.verify_game_by_search(game_name)
            if verify_result["is_game"]:
                result["verified"] = True
                result["confidence"] = verify_result["confidence"]
        
        # 更新已识别游戏集合
        if game_name:
            self.recognized_games.add(game_name)
            logger.success(f"✅ 识别游戏: {game_name} (来自标签: {hashtags})")
        
        return result
    
    def process_multiple_screenshots(self, image_paths: List[Path]) -> List[Dict[str, Any]]:
        """
        处理多张截图
        
        Args:
            image_paths: 截图路径列表
            
        Returns:
            所有截图的处理结果列表
        """
        all_results = []
        
        for path in image_paths:
            result = self.process_screenshot(path)
            all_results.append(result)
        
        return all_results
    
    def save_to_csv(self, results: List[Dict[str, Any]] = None):
        """
        保存识别结果到CSV文件
        只保存截图名、游戏名和标签
        
        Args:
            results: process_screenshot返回的结果列表
        """
        import pandas as pd
        from datetime import datetime
        
        if results is None:
            # 兼容旧模式
            results = [{"game_name": name} for name in self.recognized_games]
        
        if not results:
            logger.warning("没有数据可保存")
            return
        
        # 转换为DataFrame格式
        rows = []
        max_hashtags = 0
        
        for result in results:
            if isinstance(result, dict):
                hashtags = result.get('hashtags', [])
                max_hashtags = max(max_hashtags, len(hashtags))
                
                row = {
                    'screenshot': result.get('screenshot', ''),
                    'game_name': result.get('game_name', ''),
                    'hashtags': '|'.join(hashtags) if hashtags else '',
                    'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                }
                
                # 将标签分列存储
                for i, tag in enumerate(hashtags):
                    row[f'tag_{i+1}'] = tag
                
                rows.append(row)
        
        if not rows:
            logger.warning("没有有效数据可保存")
            return
        
        df = pd.DataFrame(rows)
        
        # 重新排列列顺序
        cols = ['screenshot', 'game_name', 'hashtags', 'created_at']
        tag_cols = [c for c in df.columns if c.startswith('tag_')]
        tag_cols.sort(key=lambda x: int(x.split('_')[-1]))
        final_cols = [c for c in cols if c in df.columns] + tag_cols
        df = df[final_cols]
        
        # 如果文件已存在，合并数据
        if GAMES_CSV_PATH.exists():
            try:
                existing_df = pd.read_csv(GAMES_CSV_PATH)
                df = pd.concat([existing_df, df], ignore_index=True)
                # 按screenshot去重，保留最新的
                df = df.drop_duplicates(subset=['screenshot'], keep='last')
            except Exception as e:
                logger.warning(f"读取现有CSV时出错: {e}")
        
        # 确保目录存在
        GAMES_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存到CSV
        df.to_csv(GAMES_CSV_PATH, index=False, encoding='utf-8-sig')
        logger.success(f"游戏数据已保存到: {GAMES_CSV_PATH}")
        logger.info(f"共保存 {len(df)} 条记录")
    
    def get_all_games(self) -> List[str]:
        """获取所有已识别的游戏名称"""
        return list(self.recognized_games)
