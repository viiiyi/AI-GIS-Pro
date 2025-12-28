# AI GIS 遥感智能解译系统 (Pro)

这是一个基于 **PyQt6** 和 **YOLOv8** 的桌面端 AI GIS 应用程序，专为遥感影像的目标检测与分析设计。

## 🚀 功能特性

- **多模型支持**：支持 YOLOv8 水平框 (HBB) 和 旋转框 (OBB) 模型，适配航拍/卫星视角。
- **大图切片检测**：内置滑动窗口 (Sliding Window) 算法，支持超大分辨率 GeoTIFF 影像的自动切片与结果合并。
- **交互式可视化**：
  - 支持缩放、平移的地图视图。
  - **热力图模式**：直观展示目标分布密度。
  - **矢量叠加**：实时绘制检测框和多边形。
- **GIS 专业工具**：
  - **📏 测距**：像素/地理距离测量。
  - **📐 测面积**：多边形区域面积计算。
- **多格式导出**：
  - 支持导出检测结果为 **Excel (.xlsx)** 统计表。
  - 支持导出 **GeoJSON** 和 **KML** 矢量文件，可直接在 QGIS/ArcGIS/Google Earth 中使用。
- **数据统计**：内置图表分析（柱状图、饼图、置信度分布）。

## 🛠️ 安装与运行

### 1. 环境要求
- Python 3.9+
- 建议使用虚拟环境

### 2. 安装依赖
```bash
pip install -r requirements.txt
```
*(注：本项目依赖 `ultralytics`, `PyQt6`, `rasterio`, `geopandas`, `shapely`, `opencv-python`, `matplotlib`, `pandas`, `openpyxl` 等库)*

### 3. 运行
```bash
python main.py
```

## � Windows 打包与分发

本项目提供了完整的 Windows 可执行程序打包方案。

- **快速开始**: 请阅读 [docs/windows_packaging/START_HERE.md](docs/windows_packaging/START_HERE.md)
- **一键构建**: 双击运行 `build_windows.bat`
- **详细指南**: 参见 [docs/windows_packaging/BUILD_WINDOWS.md](docs/windows_packaging/BUILD_WINDOWS.md)

## 📂 目录结构
```
AI_GIS_Project/
├── main.py              # 主程序入口
├── models/              # 模型权重文件
├── scripts/             # 辅助脚本
├── docs/                # 项目文档
│   └── windows_packaging/ # Windows 打包相关文档
├── build_windows.bat    # Windows 构建脚本
├── .gitignore           # Git 忽略配置
└── README.md            # 项目说明
```

## 📝 注意事项
- 大模型文件 (`yolov8x.pt`, `yolov8x-obb.pt`) 和大型测试影像 (`real_cars.tif`) 因文件过大未包含在仓库中，请自行下载或训练后放入 `models/` 目录。

## 📄 License
MIT
