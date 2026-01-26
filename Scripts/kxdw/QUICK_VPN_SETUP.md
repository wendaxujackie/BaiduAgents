# VPN代理快速配置指南

## 方法1: 自动检测（推荐）

脚本会自动检测常见的VPN代理端口，无需配置！

```bash
python3 kxdw_downloader.py games_50_pages.csv --chrome
```

脚本会自动检测：
- Clash: `http://127.0.0.1:7890`
- V2Ray: `socks5://127.0.0.1:1080`
- Surge: `http://127.0.0.1:6152`

## 方法2: 手动指定代理

### 查看VPN代理端口

**Clash / ClashX:**
1. 打开Clash软件
2. 查看"端口"设置
3. 通常HTTP端口是 `7890`，SOCKS5端口是 `7891`

**V2Ray / V2RayU:**
1. 打开V2Ray软件
2. 查看"本地监听端口"
3. 通常SOCKS5端口是 `1080`

**Surge:**
1. 打开Surge
2. 查看"HTTP代理端口"和"SOCKS5代理端口"
3. 通常HTTP是 `6152`，SOCKS5是 `6153`

### 使用命令行参数

```bash
# HTTP代理（Clash默认）
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy http://127.0.0.1:7890

# SOCKS5代理（V2Ray默认）
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy socks5://127.0.0.1:1080
```

### 使用代理文件

1. 创建 `proxies.txt`:
```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw
echo "http://127.0.0.1:7890" > proxies.txt
```

2. 运行脚本:
```bash
python3 kxdw_downloader.py games_50_pages.csv --chrome --proxy-file proxies.txt
```

## 方法3: 快速检测脚本

运行检测脚本查看VPN代理端口：

```bash
cd /Users/jackie/Documents/副业/Scripts/kxdw
source venv/bin/activate
python3 check_vpn_proxy.py
```

## 常见VPN代理端口对照表

| VPN软件 | HTTP代理 | SOCKS5代理 |
|---------|----------|------------|
| Clash/ClashX | `http://127.0.0.1:7890` | `socks5://127.0.0.1:7891` |
| V2Ray/V2RayU | - | `socks5://127.0.0.1:1080` |
| Surge | `http://127.0.0.1:6152` | `socks5://127.0.0.1:6153` |
| Shadowrocket | `http://127.0.0.1:7890` | - |

## 注意事项

1. **确保VPN开启了本地代理**
   - 有些VPN只做系统级代理，需要在设置中开启"允许本地连接"

2. **SOCKS5代理需要安装pysocks**
   ```bash
   pip install pysocks
   ```

3. **如果自动检测失败**
   - 手动查看VPN软件的代理端口设置
   - 使用 `--proxy` 参数手动指定

