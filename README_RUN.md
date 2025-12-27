# AI GIS 遥感智能解译系统 - 运行指南

## 1. 环境配置 (Windows/macOS)

本项目依赖于 GIS 相关的库 (`geopandas`, `rasterio`)，这些库在 Windows 上直接通过 pip 安装可能会遇到编译错误。因此，**强烈建议使用 Conda** 来管理环境。

### 推荐方式：使用 Conda (最稳妥)

如果您已经安装了 Anaconda 或 Miniconda，请按照以下步骤操作：

1.  **创建新环境** (建议使用 Python 3.9 或 3.10)：
    ```bash
    conda create -n ai_gis python=3.9
    conda activate ai_gis
    ```

2.  **优先安装 GIS 核心库** (这一步非常关键，Conda 会自动处理二进制依赖)：
    ```bash
    conda install -c conda-forge geopandas rasterio
    ```

3.  **安装其他依赖**：
    ```bash
    pip install -r requirements.txt
    ```
    *注意：如果 `requirements.txt` 安装过程中提示 `geopandas` 或 `rasterio` 版本冲突，可以忽略，因为第2步已经安装好了这两个最难装的库。*

---

### 备选方式：使用 Pip (仅限 macOS/Linux 或 高级 Windows 用户)

如果您坚持不使用 Conda：

*   **macOS/Linux**: 直接运行 `pip install -r requirements.txt` 通常可以成功。
*   **Windows**: 您可能需要手动下载 `GDAL`, `Rasterio`, `Fiona`, `Shapely` 的 `.whl` 文件进行安装，否则 `pip install` 可能会报错。

---

## 2. 运行项目

1.  确保环境已激活 (`conda activate ai_gis`)。
2.  在项目根目录下运行：
    ```bash
    python main.py
    ```

## 3. 功能说明

*   **模型选择**：左侧面板可以选择不同的 YOLOv8 模型（支持 OBB 旋转框和 HBB 水平框）。
*   **影像导入**：点击工具栏的“打开影像”按钮，支持 `.tif`, `.png`, `.jpg` 等格式。
*   **开始检测**：导入影像后，点击“开始检测”，程序会自动进行切片分析。
*   **结果导出**：检测完成后，结果会自动保存为 Shapefile (`.shp`) 文件在输出目录中。

## 4. 常见问题

*   **Q: 运行速度慢？**
    *   A: 程序会自动检测 GPU。如果是 Windows + NVIDIA 显卡，请确保安装了 CUDA 版本的 PyTorch。如果是 macOS，程序会自动调用 MPS (Metal) 加速。
*   **Q: 报错 `ImportError: DLL load failed` (Windows)?**
    *   A: 这通常是因为 GIS 库冲突。请尝试删除环境，严格按照“推荐方式”重新安装，务必先用 conda 安装 geopandas。
