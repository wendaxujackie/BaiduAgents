# 百度网盘文件同步工具

一个基于 Python 和 BaiduPCS-Go 的百度网盘文件同步工具，支持从 curl 命令解析 cookie 并自动上传文件。

## 功能特性

- ✅ 从 curl.txt 解析 Cookie 信息
- ✅ 使用 BaiduPCS-Go 自动登录
- ✅ 支持登出功能
- ✅ 支持上传单个文件或整个文件夹（递归）
- ✅ 保持本地目录结构
- ✅ 自动记录上传日志（按日期）
- ✅ 虚拟环境支持，避免版本冲突

## 快速开始

### 1. 环境要求

- Python 3.7+
- BaiduPCS-Go（需要单独安装）

### 2. 设置环境

```bash
# 使用 Python 脚本（跨平台）
python setup_env.py

# 或使用 Shell 脚本
bash setup_env.sh  # macOS/Linux
setup_env.bat      # Windows
```

### 3. 激活虚拟环境

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate.bat
```

### 4. 使用步骤

```bash
# 1. 登录（自动解析 Cookie）
python login.py

# 2. 上传文件
python upload.py --local-file /本地/文件/路径 --remote-dir /我的文件/备份
# 或使用位置参数：python upload.py /本地/文件/路径 /我的文件/备份

# 3. 登出（可选）
python logout.py
```

## 项目结构

```
SyncFileToBaiDuNetEase/
├── curl.txt              # 原始 curl 命令文件（需要自己准备）
├── parse_cookie.py       # Cookie 解析脚本
├── login.py              # 登录脚本
├── logout.py             # 登出脚本
├── upload.py             # 上传脚本
├── setup_env.py          # 环境设置脚本（Python）
├── setup_env.sh          # 环境设置脚本（macOS/Linux）
├── setup_env.bat         # 环境设置脚本（Windows）
├── requirements.txt      # Python 依赖（本项目主要使用标准库）
├── upload_logs/          # 上传记录目录
├── README.md             # 本文件
├── 使用说明.md           # 详细使用说明（面向 Python 小白）
└── 需求分析.md           # 需求分析文档
```

## 详细文档

请查看 [使用说明.md](使用说明.md) 获取详细的使用指南，包括：
- 如何获取 Cookie
- 详细的使用步骤
- 常见问题解答

## 注意事项

1. Cookie 可能会过期，如果登录失败需要重新获取
2. 同名文件会自动覆盖，请谨慎操作
3. 上传前会检查远端目录是否存在，不存在会报错
4. 上传记录按日期保存在 `upload_logs` 目录

## 许可证

本项目仅供学习和个人使用。
