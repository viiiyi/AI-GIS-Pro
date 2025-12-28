# Windows 可执行程序构建指南

## 📋 前置要求

### 1. Python 环境（在 Windows 上）
- **Python 版本**: 3.10 或 3.11（推荐）
- **注意**: 使用 conda 环境非常重要，以避免 GDAL/Rasterio 的二进制兼容性问题

### 2. 创建 Conda 环境
```bash
# 使用 conda 创建新环境
conda create -n ai_gis_win python=3.11 -y

# 激活环境
conda activate ai_gis_win

# 安装 GIS 依赖（关键步骤！）
conda install -c conda-forge geopandas rasterio fiona pyogrio -y

# 安装其他依赖
pip install -r requirements.txt
```

### 3. 安装 PyInstaller
```bash
pip install pyinstaller
```

## 🚀 构建可执行文件

### 方法 1：使用自动化脚本（推荐）
```bash
# 在项目根目录
cd AI_GIS_Project
python scripts/build_app.py
```

输出文件在 `dist/AI_GIS_Pro/` 文件夹中。

### 方法 2：使用 spec 文件
```bash
# 在项目根目录
pyinstaller AI_GIS_Pro_Windows.spec
```

## 📦 输出结构

构建完成后，您会得到：
```
dist/AI_GIS_Pro/
├── AI_GIS_Pro.exe          # 主程序
├── _internal/              # 所有依赖库和资源
├── models/                 # YOLO 模型文件
└── 其他支持文件
```

## 🔧 发布和分发

### 选项 1：直接分享文件夹
将整个 `dist/AI_GIS_Pro` 文件夹压缩为 ZIP，用户解压后直接双击 `AI_GIS_Pro.exe` 运行。

### 选项 2：创建便携式 ZIP（推荐）
```bash
# 在 dist 目录
cd dist
tar -czf AI_GIS_Pro-Windows.zip AI_GIS_Pro/
# 或使用 7-Zip/WinRAR
```

### 选项 3：创建 MSI 安装程序（高级）
安装 WiX Toolset，然后使用 PyInstaller 生成的文件创建 MSI。

## ⚠️ 常见问题

### 1. "DLL load failed" 错误
**原因**: GDAL/Rasterio 二进制兼容性问题
**解决方案**: 确保使用 conda 安装 geopandas 和 rasterio

### 2. 可执行文件太大（>1GB）
**原因**: PyTorch 和 GDAL 库很大
**解决方案**: 这是正常的，可以考虑使用 UPX 压缩或分离模型文件

### 3. 缺少 GDAL 数据文件
**原因**: GDAL 数据文件没有被正确打包
**解决方案**: 在 spec 文件中添加 GDAL_DATA 路径

### 4. 模型文件未找到
**确保**: `models/` 文件夹与 `main.py` 在同一目录，构建脚本会自动打包

## 🧪 测试可执行文件

1. 解压 `dist/AI_GIS_Pro`
2. 双击 `AI_GIS_Pro.exe`
3. 应用应该在几秒内启动
4. 加载一个 GeoTIFF 文件进行测试

## 📝 优化建议

1. **减小文件大小**:
   - 移除不需要的模型（只保留必需的 `.pt` 文件）
   - 使用量化模型（yolov8n 而不是 yolov8x）

2. **改进启动速度**:
   - 使用 `--onedir` 而不是 `--onefile`
   - 启用 UPX 压缩

3. **改进用户体验**:
   - 添加自定义启动画面
   - 创建快捷方式到桌面
   - 添加应用图标和版本信息

## 🔗 相关资源

- [PyInstaller 官方文档](https://pyinstaller.org/)
- [Rasterio Windows 指南](https://rasterio.readthedocs.io/)
- [Geopandas 安装指南](https://geopandas.org/en/latest/getting_started/install.html)
