# 环境配置状态

## ✅ 已完成的配置

### 1. Node.js 环境
- **当前版本**: v20.19.0 (满足 Appium 3.1.2 的要求: ^20.19.0 || ^22.12.0 || >=24.0.0)
- **默认版本**: 已设置为 20.19.0
- **npm 版本**: 10.8.2

### 2. Appium 服务
- **版本**: 3.1.2
- **状态**: ✅ 已安装并可以正常运行
- **uuid 依赖**: ✅ 已修复（降级到 8.3.2 以兼容 CommonJS）

### 3. Appium 驱动
- **uiautomator2 (Android)**: ✅ 已安装 (版本 6.7.10)
- **xcuitest (iOS)**: ⚠️ 部分安装（可能需要手动安装）

### 4. Android 开发工具
- **ADB**: ✅ 已安装
  - 版本: 1.0.41 (35.0.2-12147458)
  - 路径: /opt/homebrew/bin/adb
- **设备连接**: 当前未检测到 Android 设备（需要连接手机并启用 USB 调试）

### 5. iOS 开发工具
- **libimobiledevice**: ✅ 已安装
- **设备检测**: ✅ 检测到 iOS 设备
  - 设备ID: 00008101-000835600E78001E

## 📝 使用说明

### 启动 Appium 服务
```bash
./start_appium.sh
```

或者手动启动：
```bash
source ~/.nvm/nvm.sh
nvm use 20.19.0
appium --address 127.0.0.1 --port 4723 --relaxed-security
```

### 连接 Android 设备
1. 在手机上启用"开发者选项"
2. 启用"USB 调试"
3. 使用 USB 线连接手机到电脑
4. 运行 `adb devices` 检查连接

### 连接 iOS 设备
1. 使用 USB 线连接 iPhone 到电脑
2. 在 iPhone 上信任此电脑
3. 运行 `idevice_id -l` 检查连接

## ⚠️ 注意事项

1. **Node.js 版本**: 确保使用 Node.js 20.19.0 或更高版本
   ```bash
   source ~/.nvm/nvm.sh
   nvm use 20.19.0
   ```

2. **驱动注册**: 如果驱动显示未安装，但实际上已经安装，可以尝试：
   ```bash
   appium driver list --installed
   ```

3. **端口占用**: Appium 默认使用 4723 端口，如果被占用需要先关闭

## 🔧 故障排除

### Appium 启动失败
- 检查 Node.js 版本: `node --version` (应该是 20.19.0+)
- 检查 uuid 依赖: 如果出现 ES Module 错误，运行修复脚本

### 设备无法连接
- Android: 检查 USB 调试是否启用，运行 `adb devices`
- iOS: 检查是否信任电脑，运行 `idevice_id -l`

### 驱动问题
- 驱动已安装但未显示：这可能是正常的，Appium 3.x 会自动检测已安装的驱动

## 📅 最后更新
2026-01-20
