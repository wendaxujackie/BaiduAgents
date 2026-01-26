# Chrome 远程调试端口开启指南

本脚本需要 Chrome 开启远程调试端口才能使用 `--chrome` 模式。默认端口为 **9222**。

## macOS 系统

### 方法 1: 命令行启动（推荐）

关闭所有正在运行的 Chrome 窗口，然后在终端执行：

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
```

### 方法 2: 使用别名（方便）

在 `~/.zshrc` 或 `~/.bash_profile` 中添加：

```bash
alias chrome-debug='/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222'
```

然后执行：
```bash
source ~/.zshrc  # 或 source ~/.bash_profile
chrome-debug
```

### 方法 3: 后台运行（不显示窗口）

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --headless --disable-gpu &
```

## Windows 系统

### 方法 1: 命令行启动

关闭所有正在运行的 Chrome 窗口，然后在命令提示符（CMD）或 PowerShell 中执行：

```cmd
chrome.exe --remote-debugging-port=9222
```

如果 Chrome 不在系统 PATH 中，使用完整路径：

```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

或

```cmd
"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
```

### 方法 2: 创建快捷方式

1. 右键点击 Chrome 快捷方式 → 属性
2. 在"目标"字段末尾添加：` --remote-debugging-port=9222`
3. 完整路径示例：
   ```
   "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
   ```

## Linux 系统

```bash
google-chrome --remote-debugging-port=9222
```

或

```bash
chromium-browser --remote-debugging-port=9222
```

## 验证调试端口是否开启

在浏览器中访问以下地址，如果能看到 JSON 数据，说明调试端口已成功开启：

```
http://127.0.0.1:9222/json
```

或

```
http://localhost:9222/json
```

## 使用自定义端口

如果 9222 端口被占用，可以使用其他端口（如 9223）：

```bash
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9223

# Windows
chrome.exe --remote-debugging-port=9223

# Linux
google-chrome --remote-debugging-port=9223
```

然后在运行脚本时指定端口：

```bash
python3 kxdw_downloader.py games_50_pages.csv --chrome -p 9223
```

## 常见问题

### 1. 端口已被占用

如果看到 "Address already in use" 错误：

- **方法 1**: 关闭所有 Chrome 进程后重新启动
- **方法 2**: 使用其他端口（如 9223、9224 等）

### 2. 无法连接到调试端口

确保：
- Chrome 已使用 `--remote-debugging-port` 参数启动
- 端口号与脚本中指定的端口一致（默认 9222）
- 防火墙没有阻止本地连接

### 3. 多个 Chrome 实例

如果同时运行多个 Chrome 实例，只有使用 `--remote-debugging-port` 启动的那个实例可以被脚本连接。

## 注意事项

⚠️ **安全提示**: 远程调试端口会暴露 Chrome 的控制接口，建议：
- 仅在本地使用（127.0.0.1）
- 不要在生产环境或公共网络中使用
- 使用完毕后关闭调试模式

