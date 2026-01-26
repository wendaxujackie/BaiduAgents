# 代理使用指南

## 快速开始

### 1. 创建代理文件

复制示例文件：
```bash
cp proxies.txt.example proxies.txt
```

### 2. 编辑代理文件

编辑 `proxies.txt`，填入你的代理地址：

```
http://127.0.0.1:7890
http://127.0.0.1:7891
socks5://127.0.0.1:1080
```

### 3. 使用代理运行脚本

```bash
# 使用代理文件
python batch_downloader.py games_list_all.csv --proxy-file proxies.txt

# 使用单个代理
python batch_downloader.py games_list_all.csv --proxy http://127.0.0.1:7890

# Chrome + 代理
python batch_downloader.py games_list_all.csv --chrome --proxy-file proxies.txt
```

## 代理格式说明

### HTTP/HTTPS 代理
```
http://host:port
http://username:password@host:port
https://host:port
```

### SOCKS5 代理
```
socks5://host:port
socks5://username:password@host:port
```

## 代理轮换机制

- 脚本会自动轮换使用代理列表中的代理
- 每次请求（访问页面、下载文件）都会切换到下一个代理
- 如果代理列表用完了，会从头开始轮换
- 这样可以有效避免被网站 block

## 常见代理服务

### 本地代理（如 Clash、V2Ray）
```
http://127.0.0.1:7890
socks5://127.0.0.1:1080
```

### 商业代理服务
根据你购买的代理服务商提供的地址格式填写

## 注意事项

1. 确保代理地址格式正确
2. 如果代理需要认证，记得包含用户名和密码
3. 代理文件中的空行和以 `#` 开头的行会被忽略
4. 如果代理连接失败，脚本会继续尝试下一个代理







