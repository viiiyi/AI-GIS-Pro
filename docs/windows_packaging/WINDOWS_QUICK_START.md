# 🪟 Windows 可执行程序快速开始指南

## 快速开始（3 步）

### 第 1 步：准备环境（在 Windows 上）

1. **安装 Conda**（如果还没有）：
   - 下载：https://www.anaconda.com/download/success
   - 选择 Windows 版本并完成安装

2. **打开 Anaconda Prompt（或 PowerShell）并创建环境**：
   ```bash
   conda create -n ai_gis_win python=3.11 -y
   conda activate ai_gis_win
   ```

3. **安装依赖**：
   ```bash
   # 进入项目目录
   cd path\to\AI_GIS_Project
   
   # 安装 GIS 库（必须用 conda）
   conda install -c conda-forge geopandas rasterio fiona pyogrio -y
   
   # 安装其他依赖
   pip install -r requirements.txt
   ```

### 第 2 步：构建可执行文件

**选择其中一种方式：**

#### 方式 A：使用批处理脚本（推荐新手）
```bash
# 在项目根目录双击运行
build_windows.bat
```

#### 方式 B：使用 PowerShell（推荐现代用户）
```powershell
powershell -ExecutionPolicy Bypass -File build_windows.ps1
```

#### 方式 C：手动运行 Python
```bash
conda activate ai_gis_win
python scripts/build_app.py
```

> ⏱️ **等待时间**：首次构建需要 5-15 分钟（取决于网络和硬件）

### 第 3 步：验证和分发

**测试可执行文件**：
```bash
# 打开文件浏览器，导航到
dist\AI_GIS_Pro\

# 双击 AI_GIS_Pro.exe 运行
```

**分发给用户**：
```bash
# 将整个 dist\AI_GIS_Pro 文件夹压缩
dist\AI_GIS_Pro → AI_GIS_Pro-Windows.zip

# 用户只需解压并双击 AI_GIS_Pro.exe
```

---

## 📁 构建输出说明

```
dist/
└── AI_GIS_Pro/                 # 主应用文件夹
    ├── AI_GIS_Pro.exe          # ⭐ 主程序（启动点）
    ├── _internal/              # 所有 Python 依赖和库
    │   ├── PyQt6/              # PyQt6 UI 框架
    │   ├── ultralytics/        # YOLOv8 AI 模型库
    │   ├── rasterio/           # 地理栅格数据处理
    │   ├── geopandas/          # 地理向量数据处理
    │   ├── torch/              # PyTorch 深度学习框架
    │   ├── cv2/                # OpenCV 计算机视觉
    │   └── ...其他库
    └── models/                 # YOLO 权重文件
        ├── yolov8n.pt          # 小模型
        ├── yolov8x.pt          # 大模型
        ├── yolov8n-obb.pt      # 小 OBB 模型
        └── yolov8x-obb.pt      # 大 OBB 模型
```

---

## ❓ 常见问题

### Q1: 为什么要用 Conda？
**A**: 
- `rasterio` 和 `geopandas` 依赖复杂的二进制库（GDAL）
- pip 安装在 Windows 上常出现兼容性问题
- Conda 预编译了这些二进制文件，避免编译错误

### Q2: 为什么文件这么大？（>1GB）
**A**: 
- PyTorch: ~500 MB（深度学习框架）
- GDAL/Rasterio: ~200 MB（GIS 库）
- YOLOv8 模型: ~100-400 MB（取决于型号）
- 其他依赖: ~300 MB

这是**正常的**。如果要减小：
- 只保留需要的模型（删除 `models/` 中不用的 `.pt` 文件）
- 使用轻量模型（`yolov8n` 而不是 `yolov8x`）

### Q3: 程序启动很慢
**A**: 首次启动会加载 PyTorch 和模型，可能需要 10-30 秒。
- 这是**正常的**
- 后续启动会快一些
- 加载完成后应用会非常响应灵敏

### Q4: "DLL 加载失败" 错误
**A**: 这是二进制兼容性问题
- 确保使用 `conda install -c conda-forge geopandas rasterio`
- 删除 `build/` 和 `dist/` 文件夹后重新构建
- 检查 Python 版本是否为 3.10 或 3.11

### Q5: 怎样创建快捷方式给用户？
**A**: 
```bash
# 创建快捷方式到桌面
右键点击 AI_GIS_Pro.exe → 发送到 → 桌面（创建快捷方式）
```

### Q6: 能否创建安装程序？
**A**: 可以，但需要额外工具：
- **NSIS**（免费）：https://nsis.sourceforge.io/
- **WiX**（Microsoft）：https://wixtoolset.org/
- 我们可以提供这些工具的集成

---

## 🔧 高级选项

### 自定义应用图标
1. 准备一个 256×256 像素的 `.ico` 文件
2. 放在项目根目录，命名为 `icon.ico`
3. 修改 `AI_GIS_Pro_Windows.spec` 文件中：
   ```python
   exe = EXE(
       ...,
       icon='icon.ico',  # 添加这行
       ...
   )
   ```
4. 重新构建

### 关闭控制台窗口（已默认）
已在 `.spec` 文件中配置：
```python
console=False,  # 隐藏控制台
```

### 启用代码签名（企业级）
如果要分发到企业环境：
```python
codesign_identity='Your Cert',  # Windows 代码签名证书
```

---

## 📊 构建统计信息

| 指标 | 值 |
|------|-----|
| 可执行文件大小 | ~1.5 GB |
| 启动时间 | 10-30 秒（首次），2-5 秒（后续）|
| 支持的 Python 版本 | 3.10, 3.11 |
| 支持的 Windows 版本 | Windows 10+, Windows 11 |
| 硬件需求（最小） | 2GB RAM, 2GB 磁盘空间 |
| 硬件需求（推荐） | 8GB RAM, 4GB 磁盘空间 |

---

## 🚀 自动化部署（CI/CD）

如果要在 GitHub Actions 上自动构建 Windows 版本：

```yaml
name: Build Windows Executable

on: [push]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Miniconda
        uses: conda-incubator/setup-miniconda@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: |
          conda install -c conda-forge geopandas rasterio fiona pyogrio
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build
        run: python scripts/build_app.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: AI_GIS_Pro-Windows
          path: dist/AI_GIS_Pro/
```

---

## 📞 故障排除

如果遇到问题：

1. **查看构建日志**：
   ```bash
   # 脚本会自动生成日志
   build_YYYYMMDD_HHMMSS.log
   ```

2. **重新清理构建**：
   ```bash
   rmdir /s build dist __pycache__
   pip cache purge
   # 然后重新构建
   ```

3. **更新依赖**：
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **使用详细模式**：
   ```bash
   pyinstaller AI_GIS_Pro_Windows.spec -v
   ```

---

## 📚 相关文档

- [BUILD_WINDOWS.md](BUILD_WINDOWS.md) - 详细构建指南
- [README.md](README.md) - 项目概述
- [PyInstaller 官方文档](https://pyinstaller.org/)
- [GDAL/Rasterio Windows 指南](https://rasterio.readthedocs.io/)

---

**成功构建？🎉**

如果一切正常，您应该看到：
```
✅ 构建成功！
📍 可执行文件位置: dist\AI_GIS_Pro\
📌 主程序文件: dist\AI_GIS_Pro\AI_GIS_Pro.exe
```

现在可以：
1. ✓ 本地测试应用
2. ✓ 将整个 `dist\AI_GIS_Pro` 文件夹压缩为 ZIP
3. ✓ 分发给 Windows 用户
