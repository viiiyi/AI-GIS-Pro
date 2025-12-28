# AI GIS Project - Copilot Instructions

## 🧠 Project Overview
This is a desktop AI GIS application for remote sensing imagery analysis, built with **PyQt6** and **YOLOv8**. It performs object detection (HBB & OBB) on large GeoTIFFs and provides GIS tools (measure, area) and export capabilities.

## 🏗 Architecture & Core Components
- **Entry Point**: `main.py` contains the `AI_GIS_App` (Main Window) and `DetectionThread`.
- **UI Framework**: PyQt6. Key custom widgets:
  - `ZoomableGraphicsView`: Handles map interaction (pan, zoom, measure).
  - `MplCanvas`: Matplotlib integration for charts.
- **AI Engine**: `DetectionThread` manages YOLOv8 inference.
  - **Sliding Window**: Custom logic for images > 1000x1000px (640px slice, 500px stride).
  - **Hardware Acceleration**: Auto-detects MPS (Apple Silicon), CUDA (NVIDIA), or CPU.
- **GIS Data Flow**:
  - **Input**: `rasterio` reads GeoTIFFs (preserves CRS/Transform).
  - **Processing**: Pixel coordinates -> Geographic coordinates via `rasterio.transform.xy`.
  - **Output**: `geopandas` & `shapely` generate Shapefiles (`.shp`), GeoJSON, KML.

## 🛠 Developer Workflows
- **Environment Setup**:
  - **CRITICAL**: Use **Conda** for `geopandas` and `rasterio` to avoid binary conflicts.
  - `conda install -c conda-forge geopandas rasterio`
- **Running the App**: `python main.py`
- **Building Executable**: `python scripts/build_app.py` (Uses PyInstaller, handles hidden imports).
- **Sample Data**: Run `python scripts/download_data.py` to fetch `real_cars.tif`.

## 🧩 Patterns & Conventions
- **Threading**: NEVER run heavy tasks (inference, file I/O) on the main UI thread. Use `QThread` (e.g., `DetectionThread`) and `pyqtSignal` for communication.
- **Coordinate Systems**:
  - **Image Coords**: (x, y) pixels, used for OpenCV drawing.
  - **Scene Coords**: PyQt `QGraphicsScene` coordinates.
  - **Geo Coords**: (lon, lat) or projected, used for Shapefile export.
  - Always transform correctly between these spaces.
- **Model Handling**: Models (`.pt`) reside in `models/`. The app supports both standard YOLO (HBB) and OBB models.
- **Error Handling**: Use `try-except` blocks in threads and emit `finish_signal` with error messages to be displayed in the UI.

## ⚠️ Critical Dependencies
- **Ultralytics**: YOLOv8 implementation.
- **Rasterio/Geopandas**: GIS core. Handle with care regarding versions and binary compatibility.
- **PyQt6**: UI library. Ensure signals are connected properly.

## 📂 Key Files
- `main.py`: Core logic and UI.
- `scripts/build_app.py`: Build configuration.
- `models/`: YOLOv8 weights.
