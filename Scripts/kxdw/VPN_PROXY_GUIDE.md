# VPN代理配置指南

## 快速检测VPN代理端口

运行检测脚本：
```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw
source venv/bin/activate
python3 check_vpn_proxy.py
```

## 常见VPN代理端口

### Clash / ClashX
- HTTP代理: `http://127.0.0.1:7890`
- SOCKS5代理: `socks5://127.0.0.1:7891`

### V2Ray / V2RayU
- SOCKS5代理: `socks5://127.0.0.1:1080`

### Surge
- HTTP代理: `http://127.0.0.1:6152`
- SOCKS5代理: `socks5://127.0.0.1:6153`

### Shadowrocket (iOS/Mac)
- HTTP代理: `http://127.0.0.1:7890`

## 如何查看VPN代理端口

### 方法1: 查看VPN软件设置
1. 打开你的VPN软件
2. 找到"代理设置"或"本地代理"选项
3. 查看HTTP代理端口和SOCKS5代理端口

### 方法2: 查看系统代理设置 (Mac)
```bash
# 查看系统HTTP代理
networksetup -getwebproxy "Wi-Fi"
networksetup -getsecurewebproxy "Wi-Fi"

# 查看系统SOCKS代理
networksetup -getsocksfirewallproxy "Wi-Fi"
```

### 方法3: 查看VPN配置文件
- Clash: 查看配置文件中的 `port` 和 `socks-port`
- V2Ray: 查看配置文件中的 `inbounds` 部分

## 配置方法

### 方法1: 使用命令行参数（推荐）

```bash
# 使用HTTP代理
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:7890

# 使用SOCKS5代理
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy socks5://127.0.0.1:1080
```

### 方法2: 使用代理文件

1. 创建 `proxies.txt` 文件：
```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw
cat > proxies.txt << EOF
http://127.0.0.1:7890
EOF
```

2. 运行脚本：
```bash
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt
```

### 方法3: 编辑现有代理文件

如果已经有 `proxies.txt`，直接编辑添加：
```
http://127.0.0.1:7890
socks5://127.0.0.1:1080
```

## 注意事项

1. **确保VPN开启了本地代理**
   - 有些VPN只做系统级代理，不提供本地代理端口
   - 需要在VPN设置中开启"允许本地连接"或"本地代理"

2. **SOCKS5代理需要安装pysocks**
   ```bash
   pip install pysocks
   ```

3. **测试代理是否可用**
   ```bash
   # 测试HTTP代理
   curl -x http://127.0.0.1:7890 https://httpbin.org/ip
   
   # 测试SOCKS5代理
   curl --socks5 127.0.0.1:1080 https://httpbin.org/ip
   ```

4. **如果VPN没有本地代理端口**
   - 可以使用系统代理（但脚本可能无法直接使用）
   - 或者使用VPN提供的API/转发功能
   - 或者使用第三方代理转发工具

