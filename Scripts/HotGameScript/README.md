# 快手游戏APK自动化采集工具 🎮

一个完整的自动化工具，用于从快手APP中采集游戏信息，搜索下载资源，并批量生成带热词的APK副本。

## 📋 功能概览

### 核心功能

1. **📱 移动端自动化** (Android/iOS)
   - 自动打开快手APP
   - 导航到"我的"页面
   - 进入关注列表
   - 递归访问关注用户的主页
   - 浏览用户发布的视频内容
   - 自动截图保存

2. **🔍 OCR游戏识别**
   - 使用PaddleOCR进行文字识别
   - 智能提取游戏名称
   - 支持多种文本模式匹配
   - 自动去重和评分排序

3. **🌐 网页搜索分析**
   - 支持百度/Google/Bing搜索
   - 自动分析下载链接可靠性
   - 识别可信APK下载站点
   - 链接评分排序

4. **📥 APK下载与重命名**
   - 支持直接链接下载
   - 支持页面解析下载
   - 按热词规则批量生成副本
   - 与BAT脚本规则一致

## 🛠️ 环境要求

### 系统要求
- Python 3.8+
- Node.js 14+ (用于Appium)
- Chrome浏览器

### 移动端要求

**Android:**
- Android 5.0+
- 开启USB调试
- 已安装快手APP

**iOS:**
- iOS 12.0+
- 已安装快手APP
- WebDriverAgent配置完成

## 📦 安装

### 1. 克隆项目

```bash
cd /Users/jackiexu/Desktop/Scripts/HotGameScript
```

### 2. 创建虚拟环境 (推荐)

```bash
python -m venv venv
source venv/bin/activate  # Mac/Linux
# 或
.\venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装Appium

```bash
npm install -g appium
appium driver install uiautomator2  # Android
appium driver install xcuitest      # iOS
```

### 5. 安装PaddleOCR (推荐)

```bash
pip install paddlepaddle paddleocr
```

## 🚀 使用方法

### 启动前准备

1. **启动Appium服务器**
```bash
appium
```

2. **启动Chrome调试模式**
```bash
# Windows
chrome.exe --remote-debugging-port=9222

# Mac
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

3. **连接移动设备**
```bash
# 检查Android设备
adb devices

# iOS设备确保已信任电脑
```

### 运行模式

#### 完整流程
```bash
python main.py --full --platform android
python main.py --full --platform ios
```

#### 单独模式

```bash
# 仅移动端自动化
python main.py --mode mobile --platform android

# 仅搜索游戏
python main.py --mode search
y
# 仅下载APK
python main.py --mode download

# 仅OCR识别
python main.py --mode ocr --image-dir ./screenshots
```

#### 调试模式
```bash
python main.py --full --platform android --debug
```

## 📁 项目结构

```
HotGameScript/
├── main.py                 # 主程序入口
├── config.py               # 配置文件
├── requirements.txt        # 依赖列表
├── README.md               # 说明文档
├── APK关键词生成.bat       # Windows批处理脚本
│
├── mobile_automation/      # 移动端自动化模块
│   ├── __init__.py
│   ├── base_automation.py  # 基类
│   ├── kuaishou_android.py # Android实现
│   └── kuaishou_ios.py     # iOS实现
│
├── ocr_processor/          # OCR处理模块
│   ├── __init__.py
│   └── game_recognizer.py  # 游戏名称识别
│
├── web_automation/         # 网页自动化模块
│   ├── __init__.py
│   ├── game_searcher.py    # 游戏搜索
│   └── apk_downloader.py   # APK下载
│
├── utils/                  # 工具模块
│   ├── __init__.py
│   ├── csv_handler.py      # CSV处理
│   └── file_renamer.py     # 文件重命名
│
├── screenshots/            # 截图保存目录
├── downloads/              # APK下载目录
├── data/                   # 数据目录
│   ├── games.csv           # 游戏名称CSV
│   ├── search_results.json # 搜索结果
│   └── download_report.json# 下载报告
│
├── logs/                   # 日志目录
└── 2026发发发/             # APK输出目录
```

## ⚙️ 配置说明

编辑 `config.py` 自定义配置：

### Appium配置
```python
APPIUM_CONFIG = {
    "android": {
        "server_url": "http://localhost:4723",
        "capabilities": {
            "deviceName": "Android Device",
            # ...
        }
    }
}
```

### APK热词配置
```python
APK_KEYWORDS = [
    "官方版", "手机版", "最新版", "中文版",
    "手游", "汉化版", "官方正版", "安卓版",
    "手机版下载", "安卓版下载"
]
APK_COPIES_COUNT = 7  # 每个APK生成的副本数
```

### Chrome调试配置
```python
CHROME_DEBUG_CONFIG = {
    "debug_port": 9222,
    "headless": False,
}
```

## 📊 输出示例

### games.csv
```csv
game_name,original_text,score,updated_at
王者荣耀,《王者荣耀》手游下载,3,2026-01-20 10:30:00
和平精英,和平精英最新版,2,2026-01-20 10:31:00
```

### 生成的APK文件
```
2026发发发/
├── 王者荣耀.apk           # 原始文件
├── 王者荣耀官方版.apk
├── 王者荣耀手机版.apk
├── 王者荣耀最新版.apk
├── 王者荣耀中文版.apk
├── 王者荣耀手游.apk
├── 王者荣耀汉化版.apk
├── 王者荣耀官方正版.apk
└── ...
```

## 🔧 常见问题

### Q: Appium连接失败
```
A: 1. 确保Appium服务已启动
   2. 检查设备是否已连接 (adb devices)
   3. 确认capabilities配置正确
```

### Q: Chrome调试连接失败
```
A: 1. 确保Chrome以调试模式启动
   2. 检查端口是否被占用
   3. 关闭其他Chrome实例后重试
```

### Q: OCR识别不准确
```
A: 1. 提高截图质量
   2. 调整OCR配置中的阈值
   3. 考虑使用GPU加速
```

### Q: 下载失败
```
A: 1. 检查网络连接
   2. 某些站点可能需要代理
   3. 查看logs目录下的详细日志
```

## 📝 注意事项

1. **遵守使用条款**：请确保您的使用符合快手APP和相关网站的服务条款
2. **网络请求频率**：工具已内置请求间隔，避免过于频繁的请求
3. **数据安全**：下载的APK文件请自行检查安全性
4. **设备电量**：长时间运行建议保持设备充电状态

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

本项目仅供学习和研究使用。

---

**开发者**: 自动化脚本爱好者  
**版本**: 1.0.0  
**更新日期**: 2026-01-20
