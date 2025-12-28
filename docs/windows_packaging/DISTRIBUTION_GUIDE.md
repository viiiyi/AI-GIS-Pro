# 分发包创建指南

## 📦 为 Windows 用户创建分发包

### 方法 1：简单 ZIP 打包（推荐）

#### 步骤 1：准备文件
```bash
# 确保已构建完成
# 在项目根目录运行
build_windows.bat  # 或 build_windows.ps1
```

#### 步骤 2：创建 ZIP 包
**使用 7-Zip 或 WinRAR（推荐）：**
1. 打开文件管理器，导航到 `dist/` 文件夹
2. 右键点击 `AI_GIS_Pro` 文件夹
3. 选择"7-Zip" → "添加到压缩包..."
4. 设置压缩格式为 `.zip`
5. 命名为 `AI_GIS_Pro-v1.0.0-Windows.zip`
6. 点击"确定"

**使用 PowerShell 脚本：**
```powershell
# 在项目根目录运行
Compress-Archive -Path "dist\AI_GIS_Pro" -DestinationPath "AI_GIS_Pro-v1.0.0-Windows.zip"
```

**使用命令行：**
```bash
# Windows 10 内置
cd dist
tar -czf ..\AI_GIS_Pro-v1.0.0-Windows.zip AI_GIS_Pro
```

#### 步骤 3：验证 ZIP 包
```powershell
# 检查 ZIP 文件大小（应该是 1-1.5 GB）
Get-Item "AI_GIS_Pro-v1.0.0-Windows.zip" | Format-List Length

# 测试解压
Expand-Archive -Path "AI_GIS_Pro-v1.0.0-Windows.zip" -DestinationPath "test_extract"

# 验证可执行文件
test_extract\AI_GIS_Pro\AI_GIS_Pro.exe --version  # 如果支持
```

---

### 方法 2：创建安装程序（高级）

#### 使用 NSIS 创建 EXE 安装程序

1. **安装 NSIS**：
   - 下载：https://nsis.sourceforge.io/
   - 完成安装

2. **创建 NSIS 脚本** (`installer.nsi`)：

```nsis
; AI GIS Pro Windows Installer
; 使用 NSIS 3.x

Name "AI GIS Pro"
OutFile "AI_GIS_Pro-v1.0.0-Installer.exe"
InstallDir "$PROGRAMFILES\AI GIS Pro"

; 页面配置
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

; 安装部分
Section "安装"
  SetOutPath "$INSTDIR"
  
  ; 复制主文件夹
  File /r "dist\AI_GIS_Pro\*.*"
  
  ; 创建开始菜单快捷方式
  CreateDirectory "$SMPROGRAMS\AI GIS Pro"
  CreateShortcut "$SMPROGRAMS\AI GIS Pro\AI GIS Pro.lnk" "$INSTDIR\AI_GIS_Pro.exe"
  CreateShortcut "$SMPROGRAMS\AI GIS Pro\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; 创建桌面快捷方式
  CreateShortcut "$DESKTOP\AI GIS Pro.lnk" "$INSTDIR\AI_GIS_Pro.exe"
  
  ; 创建卸载程序
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; 卸载部分
Section "Uninstall"
  Delete "$INSTDIR\*.*"
  RMDir /r "$INSTDIR"
  Delete "$SMPROGRAMS\AI GIS Pro\*.*"
  RMDir "$SMPROGRAMS\AI GIS Pro"
  Delete "$DESKTOP\AI GIS Pro.lnk"
SectionEnd
```

3. **编译安装程序**：
```bash
# 在 NSIS 安装目录中
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
```

输出文件：`AI_GIS_Pro-v1.0.0-Installer.exe`

---

### 方法 3：Portable 版本（绿色版）

#### 创建完全便携式版本

```powershell
# 创建便携式启动脚本
$script = @"
@echo off
REM AI GIS Pro - 绿色版启动脚本

REM 获取当前目录
set SCRIPT_DIR=%~dp0

REM 切换到应用目录
cd /d "%SCRIPT_DIR%AI_GIS_Pro"

REM 启动应用
start AI_GIS_Pro.exe

REM 清理
exit /b 0
"@

# 保存为批处理文件
$script | Out-File -Encoding ASCII "run.bat"

# 创建说明文件
@"
AI GIS Pro 绿色版使用说明

1. 解压此 ZIP 文件到任意位置
2. 双击 run.bat 启动应用
3. 不需要安装，无需管理员权限
4. 卸载只需删除整个文件夹

系统要求：
- Windows 10 或更高版本
- 4GB+ RAM
- 2GB+ 可用磁盘空间

注意：首次运行可能需要 10-30 秒
"@ | Out-File -Encoding UTF8 "README_CN.txt"

# 创建英文说明
@"
AI GIS Pro Portable Edition

1. Extract this ZIP file to any location
2. Double-click run.bat to start the application
3. No installation required, no admin rights needed
4. To uninstall, simply delete the folder

System Requirements:
- Windows 10 or later
- 4GB+ RAM
- 2GB+ free disk space

Note: First launch may take 10-30 seconds
"@ | Out-File -Encoding UTF8 "README_EN.txt"
```

---

## 📋 分发包文件清单

### 标准分发包结构

```
AI_GIS_Pro-v1.0.0-Windows/
├── AI_GIS_Pro/                    # 应用文件夹
│   ├── AI_GIS_Pro.exe            # 主程序
│   ├── _internal/                # 依赖库
│   └── models/                   # YOLO 模型
├── README_CN.txt                 # 中文说明
├── README_EN.txt                 # 英文说明
├── QUICKSTART.txt                # 快速开始
├── SYSTEM_REQUIREMENTS.txt       # 系统需求
└── TROUBLESHOOTING.txt           # 故障排除
```

### 最小化分发包

如果要减小文件大小：
- 删除不需要的模型（`models/` 中的 `.pt` 文件）
- 只保留 `yolov8n.pt` 和 `yolov8n-obb.pt`（各 ~25-50 MB）
- 这样可以减小约 300-400 MB

```bash
# 移除大型模型（可选）
cd dist\AI_GIS_Pro\models
del yolov8x.pt yolov8x-obb.pt

# 现在可以重新压缩
```

---

## 📥 用户安装指南（包含在分发包中）

创建 `INSTALL.txt` 文件：

```
=== AI GIS Pro for Windows ===
安装和使用指南

【系统要求】
- Windows 10 或 Windows 11
- 4 GB RAM（推荐 8 GB）
- 2 GB 可用磁盘空间
- NVIDIA GPU（可选，用于加速）

【安装步骤】
1. 从 https://github.com/yourname/AI_GIS_Pro 下载最新版本
2. 解压 ZIP 文件到任意位置（例如：C:\Program Files\AI GIS Pro）
3. 双击 AI_GIS_Pro.exe 启动应用
4. 首次启动需要加载模型（10-30 秒），请耐心等待

【快速开始】
1. 打开菜单 → "文件" → "打开图像"
2. 选择一个 GeoTIFF 文件
3. 选择检测模型（HBB 或 OBB）
4. 点击"开始检测"
5. 等待完成后查看结果

【功能说明】
- 图像加载：支持 GeoTIFF 格式，保留地理信息
- 对象检测：使用 YOLOv8 进行 HBB/OBB 检测
- 地理工具：测距、测面积、坐标转换
- 数据导出：支持 Shapefile、GeoJSON、KML 格式

【故障排除】
Q: 程序启动后立即崩溃
A: 检查系统要求，尝试更新显卡驱动

Q: 检测速度很慢
A: 使用 yolov8n 模型（更快），或检查 GPU 是否正常

Q: 无法打开某些 GeoTIFF 文件
A: 尝试用 QGIS 或其他工具验证文件完整性

Q: 如何获得帮助？
A: 访问项目 GitHub 或查看文档

【卸载】
直接删除整个 AI GIS Pro 文件夹即可

【联系方式】
项目主页：https://github.com/yourname/AI_GIS_Project
```

---

## 🔒 分发前清单

- [ ] ZIP 文件可以正常解压
- [ ] 解压后的文件夹大小正确（~1-1.5 GB）
- [ ] AI_GIS_Pro.exe 存在且没有损坏
- [ ] models/ 文件夹包含所有需要的模型
- [ ] 在干净的 Windows 系统上测试过
- [ ] 所有说明文档都包含了
- [ ] 没有临时文件或调试信息
- [ ] 文件名正确（包含版本号）
- [ ] 准备了 MD5/SHA256 校验和

---

## 📊 分发包大小参考

| 配置 | 大小 | 说明 |
|------|------|------|
| 完整版（所有模型） | ~1.3-1.5 GB | 包含所有 YOLOv8 模型 |
| 标准版（n 和 x） | ~1.0-1.2 GB | 包含小和大模型 |
| 轻量版（仅 n） | ~0.8-1.0 GB | 仅包含最小模型 |
| 最小版（无模型） | ~0.5-0.7 GB | 用户需要自行下载模型 |

---

## 🎯 分发渠道

### 推荐渠道

1. **GitHub Releases**（最佳）
   ```
   https://github.com/yourname/AI_GIS_Project/releases
   ```
   - 优点：免费、版本控制、文件完整性验证
   - 步骤：
     1. 创建 GitHub Release
     2. 上传 ZIP 文件和校验和
     3. 写发布说明

2. **百度网盘/OneDrive**
   - 上传 ZIP 文件
   - 生成分享链接
   - 适合国内用户

3. **自托管网站**
   - 上传到自己的服务器
   - 完全控制下载体验
   - 需要配置 HTTPS

---

## 🔐 文件完整性验证

为确保用户下载的文件完整，提供校验和：

```powershell
# 生成 SHA256 校验和
$file = "AI_GIS_Pro-v1.0.0-Windows.zip"
$hash = (Get-FileHash $file -Algorithm SHA256).Hash
Write-Host "SHA256: $hash"

# 用户可以验证：
# certutil -hashfile AI_GIS_Pro-v1.0.0-Windows.zip SHA256
```

在发布说明中包含校验和：
```
文件: AI_GIS_Pro-v1.0.0-Windows.zip
大小: 1.2 GB
SHA256: abc123...
MD5: def456...
```

---

**准备完毕，可以分发！** 🚀
