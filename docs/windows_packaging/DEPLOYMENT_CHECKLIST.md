# Windows 打包部署检查清单

## 📋 构建前检查

- [ ] Python 版本 3.10 或 3.11（运行 `python --version` 验证）
- [ ] 已安装 Conda（运行 `conda --version` 验证）
- [ ] 创建了专用的 conda 环境（运行 `conda env list` 验证）
- [ ] 已激活 conda 环境
- [ ] 已安装所有依赖：
  - [ ] `conda install -c conda-forge geopandas rasterio fiona pyogrio`
  - [ ] `pip install -r requirements.txt`
  - [ ] `pip install pyinstaller`
- [ ] 验证导入成功：
  ```bash
  python -c "import ultralytics; import rasterio; import geopandas; import torch; print('✓ 所有模块就绪')"
  ```

## 📦 项目文件检查

- [ ] `main.py` 存在且可运行（测试：`python main.py`）
- [ ] `models/` 文件夹存在且包含模型：
  - [ ] `yolov8n.pt`
  - [ ] `yolov8x.pt`
  - [ ] `yolov8n-obb.pt`
  - [ ] `yolov8x-obb.pt`
- [ ] `requirements.txt` 包含所有依赖
- [ ] `AI_GIS_Pro_Windows.spec` 存在
- [ ] `build_windows.bat` 或 `build_windows.ps1` 存在

## 🛠️ 构建执行

- [ ] 清理旧版本：删除 `build/` 和 `dist/` 文件夹
- [ ] 运行构建脚本：
  - [ ] 批处理版本：`build_windows.bat`
  - [ ] PowerShell 版本：`build_windows.ps1`
  - [ ] Python 版本：`python scripts/build_app.py`
- [ ] 构建完成无错误
- [ ] 构建输出在 `dist/AI_GIS_Pro/` 中

## ✅ 可执行文件验证

- [ ] `dist/AI_GIS_Pro/AI_GIS_Pro.exe` 存在
- [ ] `dist/AI_GIS_Pro/_internal/` 文件夹存在
- [ ] `dist/AI_GIS_Pro/models/` 文件夹存在且有模型文件
- [ ] 文件夹大小约 1-1.5 GB（正常范围）

## 🧪 功能测试

1. **基础启动**
   - [ ] 双击 `AI_GIS_Pro.exe` 应用启动
   - [ ] UI 显示正确（按钮、菜单等）
   - [ ] 没有缺少模块或依赖的错误

2. **图像加载**
   - [ ] 能加载 GeoTIFF 文件
   - [ ] 图像显示在画布上
   - [ ] 放大/缩小功能正常

3. **对象检测**
   - [ ] 可以选择模型（HBB 或 OBB）
   - [ ] 可以运行检测
   - [ ] 检测完成后显示结果
   - [ ] 性能可接受

4. **GIS 工具**
   - [ ] 测量工具正常
   - [ ] 面积计算正常
   - [ ] 坐标转换正确

5. **导出功能**
   - [ ] 可以导出为 Shapefile
   - [ ] 可以导出为 GeoJSON
   - [ ] 导出文件可在 QGIS 中打开

6. **性能检查**
   - [ ] 启动时间 < 30 秒
   - [ ] 内存使用正常（< 2GB 闲置）
   - [ ] 检测时不会冻结 UI
   - [ ] 关闭应用正常退出

## 📦 分发准备

### 打包为 ZIP

```bash
# 在 dist 文件夹中
tar -czf AI_GIS_Pro-Windows-v1.0.0.zip AI_GIS_Pro/

# 或使用 7-Zip/WinRAR
# 右键 AI_GIS_Pro → 压缩为 ZIP
```

- [ ] ZIP 文件创建成功
- [ ] ZIP 大小约 1-1.5 GB
- [ ] ZIP 可以正常解压

### 文档准备

- [ ] [README.md](README.md) 已更新
- [ ] [WINDOWS_QUICK_START.md](WINDOWS_QUICK_START.md) 已审阅
- [ ] [BUILD_WINDOWS.md](BUILD_WINDOWS.md) 已审阅
- [ ] 包含系统需求信息
- [ ] 包含快速开始说明
- [ ] 包含故障排除指南

### 发布说明

- [ ] 准备发布说明文档，包括：
  - 版本号（例如：v1.0.0）
  - 发布日期
  - 新增功能列表
  - 已修复的 Bug
  - 已知问题
  - 系统需求

示例格式：
```markdown
# AI GIS Pro v1.0.0 - Windows 版本发布

## 发布日期
2024年12月28日

## 系统需求
- Windows 10 或更高版本
- 4GB RAM（推荐 8GB）
- 2GB 可用磁盘空间
- NVIDIA GPU（可选，用于加速）

## 安装步骤
1. 下载 AI_GIS_Pro-Windows-v1.0.0.zip
2. 解压到任意位置
3. 双击 AI_GIS_Pro.exe 运行

## 新增功能
- 支持 OBB 目标检测
- 改进的 GIS 工具
- 更快的处理速度

## 已知问题
- 某些旧的 GeoTIFF 可能无法加载
- 大型影像（>10GB）可能需要更多内存
```

## 🔐 质量保证

- [ ] 在不同的 Windows 版本上测试（Windows 10, Windows 11）
- [ ] 在没有 Python 安装的新计算机上测试
- [ ] 测试从 ZIP 解压后直接运行
- [ ] 检查没有临时文件或调试信息泄露
- [ ] 验证所有模型文件都被正确打包
- [ ] 检查没有硬编码的本地路径

## 📊 最终清单

- [ ] 构建成功且无错误
- [ ] 所有功能都能工作
- [ ] 文档完整且准确
- [ ] 性能满足预期
- [ ] 可以安全分发给用户
- [ ] 有故障排除指南可供用户参考

## 🚀 上线前最后检查

- [ ] 最终在目标 Windows 系统上进行完整测试
- [ ] 确认没有启动错误或崩溃
- [ ] 验证与不同硬件配置的兼容性
- [ ] 获取用户反馈（如果可能）
- [ ] 准备技术支持材料

---

**检查完成？准备分发！** ✅

如果所有项目都打钩，您的 Windows 可执行程序已准备好分发。

**常用命令：**
```bash
# 快速验证
dist\AI_GIS_Pro\AI_GIS_Pro.exe

# 查看文件夹大小
dir /s dist\AI_GIS_Pro | find "free"

# 创建校验和（用于完整性验证）
certutil -hashfile dist\AI_GIS_Pro\AI_GIS_Pro.exe SHA256
```
