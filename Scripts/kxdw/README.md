# 开心电玩手游数据抓取工具

使用 Chrome DevTools Protocol 抓取开心电玩网站的手游数据。

## 环境设置

### 1. 激活虚拟环境

**Mac/Linux（推荐使用便捷脚本）:**
```bash
./activate.sh
```

**或手动激活:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 2. 安装依赖（首次使用）

如果虚拟环境已创建但依赖未安装，运行：
```bash
pip install -r requirements.txt
```

**注意：** 依赖包已经预装在虚拟环境中，通常无需再次安装。

### 3. 启动 Chrome 调试模式

**Mac:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

**Windows:**
```bash
chrome.exe --remote-debugging-port=9222
```

**Linux:**
```bash
google-chrome --remote-debugging-port=9222
```

## 使用方法

### 方法一：使用便捷运行脚本（推荐）

```bash
./run.sh
```

**指定输出文件：**
```bash
./run.sh -o games.csv
```

**指定 Chrome 调试端口：**
```bash
./run.sh -p 9222
```

**指定最大处理页数（默认100页）：**
```bash
./run.sh --max-pages 200
```

### 方法二：手动激活虚拟环境

**1. 激活虚拟环境：**
```bash
source venv/bin/activate
# 或使用便捷脚本
./activate.sh
```

**2. 运行脚本：**
```bash
python3 kxdw_crawler.py
```

**3. 退出虚拟环境：**
```bash
deactivate
```

## 功能说明

- 自动访问 https://www.kxdw.com/android/gf.html
- 自动处理分页（支持 gf.html 格式，默认最多100页，可通过参数调整）
- 提取游戏名称和详情页链接
- 导出为CSV文件，包含：游戏名称、详情页链接、是否已下载

## 输出格式

CSV文件包含以下列：
- 游戏名称
- 详情页链接
- 是否已下载

## 下载游戏

使用 `kxdw_downloader.py` 脚本根据CSV文件下载游戏：

### 基本用法

```bash
# 使用Chrome模式（推荐）
python3 kxdw_downloader.py games_50_pages.csv --chrome

# 使用requests模式
python3 kxdw_downloader.py games_50_pages.csv
```

### 参数说明

- `--chrome`: 使用Chrome DevTools Protocol（推荐，避免被拦截）
- `-p, --port`: Chrome调试端口（默认9222）
- `-d, --dir`: 下载保存目录（默认./downloads）
- `--start`: 起始行号（从0开始）
- `--limit`: 处理数量限制

### 功能说明

- 自动读取CSV文件中的游戏列表
- 访问每个游戏的详情页
- 如果APK大小大于1G，自动跳过并标记为已下载
- 如果小于1G，解析下载地址并下载
- 使用百度建议词作为文件夹名
- 自动创建信息文件
- 自动更新CSV文件中的"是否已下载"状态

### 示例

```bash
# 下载前10个游戏
python3 kxdw_downloader.py games_50_pages.csv --chrome --limit 10

# 从第100个游戏开始下载
python3 kxdw_downloader.py games_50_pages.csv --chrome --start 100

# 指定下载目录
python3 kxdw_downloader.py games_50_pages.csv --chrome -d ./my_downloads
```

