# -*- coding: utf-8 -*-
"""
配置文件 - 自动化脚本全局配置
"""
import os
from pathlib import Path

# ==================== 路径配置 ====================
BASE_DIR = Path(__file__).parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
DOWNLOADS_DIR = BASE_DIR / "downloads"
DATA_DIR = BASE_DIR / "data"
GAMES_CSV_PATH = DATA_DIR / "games.csv"

# 确保目录存在
for dir_path in [SCREENSHOTS_DIR, DOWNLOADS_DIR, DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==================== Appium配置 ====================
# 
# 【重要】iOS真机配置说明：
# 1. 连接iPhone到Mac，在iPhone上点击"信任此电脑"
# 2. 获取设备UDID: 
#    - 方法1: 打开Finder，点击左侧iPhone，点击设备名下方的信息，会显示UDID
#    - 方法2: 运行命令 xcrun xctrace list devices
#    - 方法3: 运行命令 idevice_id -l (需要安装 libimobiledevice)
# 3. 将下方 "udid" 的值改为你的设备UDID
#
# 【Android真机配置说明】:
# 1. 在手机上开启"开发者选项"和"USB调试"
# 2. 运行 adb devices 获取设备ID
# 3. 将下方 "deviceName" 改为你的设备ID

APPIUM_CONFIG = {
    "android": {
        "server_url": "http://localhost:4723",
        "capabilities": {
            "platformName": "Android",
            "automationName": "UiAutomator2",
            "deviceName": "Android Device",  # 改为你的设备ID，如 "emulator-5554" 或 "XXXXXXXX"
            "appPackage": "com.smile.gifmaker",  # 快手包名
            "appActivity": "com.yxcorp.gifshow.HomeActivity",  # 快手主Activity
            "noReset": True,
            "unicodeKeyboard": True,
            "resetKeyboard": True,
            "newCommandTimeout": 600,
        }
    },
    "ios": {
        "server_url": "http://localhost:4723",
        "capabilities": {
            "platformName": "iOS",
            "automationName": "XCUITest",
            "deviceName": "iPhone",
            "udid": "00008101-000835600E78001E",
            "bundleId": "com.jiangjia.gif",  # 快手iOS国内版 Bundle ID
            "noReset": True,
            # 关键配置：使用已运行的WDA（通过iproxy端口转发）
            "appium:webDriverAgentUrl": "http://127.0.0.1:8100",
        }
    }
}

# ==================== 快手APP元素定位 ====================
KUAISHOU_ELEMENTS = {
    "android": {
        # 底部导航栏
        "tab_me": {
            "type": "xpath",
            "value": "//android.widget.TextView[@text='我']"
        },
        "tab_home": {
            "type": "xpath", 
            "value": "//android.widget.TextView[@text='首页']"
        },
        # 我的页面
        "follow_button": {
            "type": "xpath",
            "value": "//android.widget.TextView[@text='关注']"
        },
        "follow_count": {
            "type": "id",
            "value": "com.smile.gifmaker:id/follow_count"
        },
        # 关注列表
        "follow_list_item": {
            "type": "xpath",
            "value": "//androidx.recyclerview.widget.RecyclerView//android.widget.LinearLayout"
        },
        "user_avatar": {
            "type": "id",
            "value": "com.smile.gifmaker:id/avatar"
        },
        "user_name": {
            "type": "id",
            "value": "com.smile.gifmaker:id/user_name"
        },
        # 用户主页
        "works_tab": {
            "type": "xpath",
            "value": "//android.widget.TextView[@text='作品']"
        },
        "video_item": {
            "type": "xpath",
            "value": "//androidx.recyclerview.widget.RecyclerView//android.widget.FrameLayout[@clickable='true']"
        },
        # 返回按钮
        "back_button": {
            "type": "id",
            "value": "com.smile.gifmaker:id/left_btn"
        },
        # 视频详情页
        "video_title": {
            "type": "id",
            "value": "com.smile.gifmaker:id/caption"
        },
    },
    "ios": {
        # 底部导航栏
        "tab_me": {
            "type": "accessibility_id",
            "value": "我"
        },
        "tab_home": {
            "type": "accessibility_id",
            "value": "首页"
        },
        # 我的页面
        "follow_button": {
            "type": "accessibility_id",
            "value": "关注"
        },
        # 关注列表
        "follow_list_item": {
            "type": "xpath",
            "value": "//XCUIElementTypeCell"
        },
        # 用户主页
        "works_tab": {
            "type": "ios_predicate",
            "value": "name BEGINSWITH '作品'"  # 实际name是"作品,148"这样的格式
        },
        "video_item": {
            "type": "ios_predicate",
            "value": "name CONTAINS '作品点赞数'"  # 视频项目name是"置顶作品点赞数X"
        },
        # 返回按钮
        "back_button": {
            "type": "accessibility_id",
            "value": "返回"
        },
    }
}

# ==================== OCR配置 ====================
OCR_CONFIG = {
    "use_gpu": False,
    "lang": "ch",  # 中文
    "det_db_thresh": 0.3,
    "det_db_box_thresh": 0.5,
}

# ==================== 游戏识别关键词 ====================
GAME_KEYWORDS = [
    "游戏", "手游", "网游", "端游", "页游",
    "下载", "安装", "试玩", "开服", "公测", "内测",
    "角色扮演", "RPG", "MMORPG", "策略", "卡牌", "射击", "FPS",
    "传奇", "仙侠", "武侠", "三国", "西游", "修仙",
    "官方", "正版", "破解", "变态", "BT", "私服",
    "礼包", "福利", "首充", "VIP",
]

# 排除关键词（用于过滤非游戏内容）
EXCLUDE_KEYWORDS = [
    "直播", "主播", "带货", "推荐", "关注", "粉丝",
    "抖音", "快手", "微信", "QQ", "淘宝", "京东",
]

# ==================== APK热词配置（与bat文件保持一致）====================
APK_KEYWORDS = [
    "官方版",
    "手机版", 
    "最新版",
    "中文版",
    "手游",
    "汉化版",
    "官方正版",
    "安卓版",
    "手机版下载",
    "安卓版下载",
]

# 每个APK生成的副本数量
APK_COPIES_COUNT = 7

# APK下载目标文件夹
APK_TARGET_FOLDER = "2026发发发"

# ==================== Chrome调试配置 ====================
CHROME_DEBUG_CONFIG = {
    "debug_port": 9222,
    "user_data_dir": str(BASE_DIR / "chrome_profile"),
    "headless": False,  # 是否无头模式
}

# ==================== 搜索引擎配置 ====================
SEARCH_ENGINES = {
    "baidu": "https://www.baidu.com/s?wd={}",
    "google": "https://www.google.com/search?q={}",
    "bing": "https://www.bing.com/search?q={}",
}

# APK下载站点（白名单）
APK_DOWNLOAD_SITES = [
    "apkpure.com",
    "apkmirror.com",
    "taptap.cn",
    "taptap.io",
    "wandoujia.com",
    "coolapk.com",
    "shouji.baidu.com",
    "app.mi.com",
    "anzhi.com",
    "mumayi.com",
    "liqucn.com",
    "pc6.com",
    "downza.cn",
    "onlinedown.net",
]

# ==================== 日志配置 ====================
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    "rotation": "10 MB",
    "retention": "7 days",
}

# ==================== 超时配置 ====================
TIMEOUTS = {
    "element_wait": 10,  # 元素等待超时（秒）
    "page_load": 30,     # 页面加载超时（秒）
    "download": 300,     # 下载超时（秒）
    "screenshot": 5,     # 截图超时（秒）
}

# ==================== 限制配置 ====================
LIMITS = {
    "max_follow_users": 50,      # 最大处理关注用户数
    "max_videos_per_user": 9999, # 每个用户最大处理视频数（设大点，让它滚动到底部）
    "max_retries": 3,            # 最大重试次数
    "scroll_pause_time": 1.5,    # 滚动暂停时间（秒）
}
