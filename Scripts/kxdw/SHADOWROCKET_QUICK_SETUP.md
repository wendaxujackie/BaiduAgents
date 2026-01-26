# Shadowrocket 快速配置指南

## 步骤1: 查看Shadowrocket代理端口

### 在Shadowrocket中查看：

1. **打开Shadowrocket应用**
2. **点击右下角"设置"图标（齿轮）**
3. **找到"本地代理"或"HTTP代理"选项**
4. **查看端口号**（通常是 `7890`）

### 或者查看配置文件：

Shadowrocket的配置文件通常在：
- Mac: `~/Library/Application Support/Shadowrocket/`
- 查看配置文件中的 `localPort` 或 `httpPort`

## 步骤2: 配置代理

### 方法1: 使用命令行参数（最简单）

假设你的Shadowrocket HTTP代理端口是 `7890`：

```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:7890
```

### 方法2: 创建proxies.txt文件

```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw

# 创建代理文件（假设端口是7890）
echo "http://127.0.0.1:7890" > proxies.txt

# 运行脚本
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt
```

### 方法3: 如果端口不是7890

如果Shadowrocket使用的是其他端口（比如 `8080`、`8888`等），修改端口号：

```bash
# 例如端口是8080
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:8080
```

## 常见Shadowrocket端口

- **HTTP代理**: `http://127.0.0.1:7890` （最常见）
- **SOCKS5代理**: `socks5://127.0.0.1:1080` （如果开启了SOCKS5）

## 注意事项

1. **确保Shadowrocket已启动并连接**
2. **确保开启了"允许本地连接"或"本地代理"**
3. **如果使用SOCKS5，需要安装pysocks**:
   ```bash
   pip install pysocks
   ```

## 快速测试

运行检测脚本查看端口：

```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw
source venv/bin/activate
python3 check_vpn_proxy.py
```

或者直接测试代理：

```bash
# 测试HTTP代理（假设端口7890）
curl -x http://127.0.0.1:7890 https://httpbin.org/ip

# 如果成功，会显示你的代理IP地址
```

