import sys
import os
import time
import rasterio
import numpy as np
import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Polygon, LineString
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QMessageBox, QTextEdit, 
                             QHBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
                             QComboBox, QGraphicsRectItem, QGraphicsPolygonItem, QToolBar,
                             QStyle, QTableWidget, QTableWidgetItem, QHeaderView, QSplitter, QFrame,
                             QProgressBar, QGroupBox, QRadioButton, QButtonGroup, QListWidget,
                             QLineEdit, QStackedWidget, QSlider, QCheckBox, QMenu, QGraphicsLineItem, QGraphicsEllipseItem,
                             QTabWidget, QToolBox, QMenuBar, QDockWidget, QGraphicsItemGroup, QGraphicsTextItem)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QRectF, QPointF, QSize, QEvent, QSettings
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QWheelEvent, QPolygonF, QAction, QIcon, QFont, QBrush, QCursor
from ultralytics import YOLO
import cv2
import torch
from torchvision.ops import nms
import webbrowser
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QDateEdit, QDialog, QFormLayout, QDoubleSpinBox, QSpinBox

# Matplotlib integration
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# Optional: psutil for system monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# --- Matplotlib Widget ---
class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # Dark theme for plot
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.patch.set_facecolor('#21252b') # Match UI background
        self.axes.set_facecolor('#21252b')

# --- 自定义可缩放视图 ---
class ZoomableGraphicsView(QGraphicsView):
    # 定义点击信号，传递场景坐标
    clicked_signal = pyqtSignal(QPointF)
    mouse_moved_signal = pyqtSignal(QPointF)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag) # 默认拖拽模式
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QColor(40, 44, 52)) # 现代深色背景
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setMouseTracking(True) # 开启鼠标追踪
        self.measure_mode = None # 'distance', 'area', None

    def wheelEvent(self, event: QWheelEvent):
        # 优化触控板体验：根据 delta 值动态调整缩放速度
        delta = event.angleDelta().y()
        factor = 1.001 ** delta
        self.scale(factor, factor)
        
    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        self.mouse_moved_signal.emit(scene_pos)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if self.measure_mode and event.button() == Qt.MouseButton.LeftButton:
            # 将视图坐标转换为场景坐标
            scene_pos = self.mapToScene(event.pos())
            self.clicked_signal.emit(scene_pos)
        else:
            super().mousePressEvent(event)

    def zoom_in(self):
        self.scale(1.2, 1.2)

    def zoom_out(self):
        self.scale(1/1.2, 1/1.2)

    def reset_zoom(self):
        self.resetTransform()
        if self.scene():
            self.fitInView(self.scene().itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

# --- 后台 AI 线程 ---
class DetectionThread(QThread):
    log_signal = pyqtSignal(str)
    finish_signal = pyqtSignal(str)
    result_signal = pyqtSignal(str, str, str, list) # original_path, vis_path, stats, detections
    progress_signal = pyqtSignal(int, str, str) # percent, eta, usage

    def __init__(self, model_path, image_paths, output_dir, conf=0.25, iou=0.45):
        super().__init__()
        self.model_path = model_path
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.conf = conf
        self.iou = iou

    def run(self):
        try:
            # 1. 硬件加速配置
            device = 'cpu'
            if torch.backends.mps.is_available():
                device = 'mps'
                self.log_signal.emit("🍎 检测到 Apple Silicon 芯片，已启用 MPS (Metal) 神经网络加速！")
            elif torch.cuda.is_available():
                device = 'cuda'
                self.log_signal.emit("🚀 检测到 NVIDIA GPU，已启用 CUDA 加速！")
            else:
                self.log_signal.emit("🐢 未检测到专用加速硬件，使用 CPU 运行...")

            self.log_signal.emit(f"正在加载模型: {os.path.basename(self.model_path)}...")
            model = YOLO(self.model_path)
            
            total_files = len(self.image_paths)
            
            for idx, image_path in enumerate(self.image_paths):
                file_start_time = time.time()
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                output_shp_path = os.path.join(self.output_dir, f"{base_name}_result.shp")
                
                self.log_signal.emit(f"[{idx+1}/{total_files}] 正在读取影像: {base_name}...")
                
                with rasterio.open(image_path) as src:
                    transform = src.transform
                    crs = src.crs
                    
                    img_data = src.read()
                    img_array = np.transpose(img_data, (1, 2, 0))
                    img_array = np.ascontiguousarray(img_array)
                    
                    h, w = img_array.shape[:2]
                    self.log_signal.emit(f"影像尺寸: {w} x {h}")

                    final_polygons = [] 
                    final_scores = []
                    final_classes = []
                    final_names = []

                    # --- 智能切片扫描逻辑 ---
                    if h > 1000 or w > 1000:
                        self.log_signal.emit("🚀 启用高精度切片扫描模式 (Sliding Window)...")
                        slice_size = 640
                        stride = 500
                        
                        total_slices = ((h // stride) + 1) * ((w // stride) + 1)
                        processed_count = 0
                        
                        for y in range(0, h, stride):
                            for x in range(0, w, stride):
                                h_slice = min(slice_size, h - y)
                                w_slice = min(slice_size, w - x)
                                crop = img_array[y:y+h_slice, x:x+w_slice]
                                
                                # 预测
                                results = model.predict(crop, save=False, conf=self.conf, iou=self.iou, augment=False, verbose=False, device=device)
                                
                                for r in results:
                                    # 处理 OBB (旋转框)
                                    if r.obb is not None and len(r.obb) > 0:
                                        for i, obb in enumerate(r.obb):
                                            points = obb.xyxyxyxy[0].cpu().numpy()
                                            points[:, 0] += x
                                            points[:, 1] += y
                                            final_polygons.append(points)
                                            final_scores.append(float(obb.conf.cpu().numpy()[0]))
                                            cls_id = int(obb.cls.cpu().numpy()[0])
                                            final_classes.append(cls_id)
                                            final_names.append(model.names[cls_id])
                                    
                                    # 处理 HBB (水平框)
                                    elif r.boxes is not None and len(r.boxes) > 0:
                                        for box_data in r.boxes:
                                            bx1, by1, bx2, by2 = box_data.xyxy[0].cpu().numpy()
                                            points = np.array([
                                                [bx1+x, by1+y], [bx2+x, by1+y], 
                                                [bx2+x, by2+y], [bx1+x, by2+y]
                                            ])
                                            final_polygons.append(points)
                                            final_scores.append(float(box_data.conf.cpu().numpy()[0]))
                                            cls_id = int(box_data.cls.cpu().numpy()[0])
                                            final_classes.append(cls_id)
                                            final_names.append(model.names[cls_id])
                                
                                processed_count += 1
                                
                                # 更新进度和 ETA
                                elapsed = time.time() - file_start_time
                                if processed_count > 0:
                                    avg_time_per_slice = elapsed / processed_count
                                    remaining_slices = total_slices - processed_count
                                    eta_seconds = remaining_slices * avg_time_per_slice
                                    eta_str = time.strftime("%M:%S", time.gmtime(eta_seconds))
                                else:
                                    eta_str = "--:--"
                                
                                # 获取系统资源
                                usage_str = "CPU: ?%"
                                if HAS_PSUTIL:
                                    cpu_p = psutil.cpu_percent()
                                    mem_p = psutil.virtual_memory().percent
                                    usage_str = f"CPU: {cpu_p}% | MEM: {mem_p}%"
                                
                                # 总体进度 = (已完成文件数 + 当前文件进度) / 总文件数
                                current_file_progress = processed_count / total_slices
                                total_progress = int(((idx + current_file_progress) / total_files) * 100)
                                
                                self.progress_signal.emit(total_progress, f"ETA: {eta_str} (File {idx+1}/{total_files})", usage_str)
                            
                    else:
                        self.log_signal.emit("影像较小，使用全图模式...")
                        results = model.predict(img_array, save=False, conf=self.conf, iou=self.iou, augment=False, device=device)
                        result = results[0]
                        
                        if result.obb is not None and len(result.obb) > 0:
                            for obb in result.obb:
                                points = obb.xyxyxyxy[0].cpu().numpy()
                                final_polygons.append(points)
                                final_scores.append(float(obb.conf.cpu().numpy()[0]))
                                cls_id = int(obb.cls.cpu().numpy()[0])
                                final_classes.append(cls_id)
                                final_names.append(result.names[cls_id])
                        elif result.boxes is not None and len(result.boxes) > 0:
                            for box_data in result.boxes:
                                x1, y1, x2, y2 = box_data.xyxy[0].cpu().numpy()
                                points = np.array([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
                                final_polygons.append(points)
                                final_scores.append(float(box_data.conf.cpu().numpy()[0]))
                                cls_id = int(box_data.cls.cpu().numpy()[0])
                                final_classes.append(cls_id)
                                final_names.append(result.names[cls_id])
                        
                        self.progress_signal.emit(int(((idx + 1) / total_files) * 100), "Done", "Processing...")

                    # --- 准备数据 ---
                    geometries = []
                    detections_list = [] 
                    
                    if len(final_polygons) > 0:
                        self.log_signal.emit(f"[{base_name}] 最终确认 {len(final_polygons)} 个目标...")
                        for i, points in enumerate(final_polygons):
                            # points shape: (4, 2)
                            # 1. 生成 Shapefile 几何 (Polygon)
                            geo_points = []
                            for px, py in points:
                                gx, gy = rasterio.transform.xy(transform, py, px, offset='center')
                                geo_points.append((gx, gy))
                            
                            geometries.append(Polygon(geo_points))
                            
                            # 2. 收集前端数据
                            min_x, min_y = np.min(points, axis=0)
                            max_x, max_y = np.max(points, axis=0)
                            
                            detections_list.append({
                                'name': final_names[i],
                                'bbox': [float(min_x), float(min_y), float(max_x), float(max_y)], 
                                'polygon': points.tolist(), 
                                'score': float(final_scores[i])
                            })
                    else:
                        self.log_signal.emit(f"[{base_name}] ⚠️ 未检测到任何目标。")

                    # 导出 Shapefile
                    if len(geometries) > 0:
                        gdf = gpd.GeoDataFrame({
                            'Class': final_names,
                            'Score': final_scores
                        }, geometry=geometries, crs=crs)
                        gdf.to_file(output_shp_path, driver='ESRI Shapefile', encoding='utf-8')
                    else:
                        gdf = gpd.GeoDataFrame({'Class': [], 'Score': []}, geometry=[], crs=crs)
                        gdf.to_file(output_shp_path, driver='ESRI Shapefile', encoding='utf-8')

                    # --- 生成可视化结果 ---
                    self.log_signal.emit(f"[{base_name}] 正在绘制可视化结果...")
                    
                    from collections import Counter
                    count_stats = Counter(final_names)
                    stats_text = f"【{base_name} 统计】\n"
                    for cls_name, count in count_stats.items():
                        stats_text += f"- {cls_name}: {count} 个\n"
                    
                    vis_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                    
                    for i, points in enumerate(final_polygons):
                        pts = points.astype(np.int32).reshape((-1, 1, 2))
                        cv2.polylines(vis_img, [pts], True, (0, 0, 255), 2)
                        
                        x1, y1 = pts[0][0]
                        label = f"{final_names[i]}"
                        (w_text, h_text), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                        cv2.rectangle(vis_img, (x1, y1 - 20), (x1 + w_text, y1), (0, 0, 255), -1)
                        cv2.putText(vis_img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    temp_vis_path = os.path.join(self.output_dir, f"{base_name}_vis.png")
                    cv2.imwrite(temp_vis_path, vis_img)
                    
                    self.result_signal.emit(image_path, temp_vis_path, stats_text, detections_list)

            self.finish_signal.emit(f"✅ 批量处理完成！共处理 {total_files} 个文件。")

        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(error_msg) 
            self.finish_signal.emit(f"❌ 出错: {str(e)}")

# --- GEE 下载对话框 ---


# --- 界面部分 ---
class AI_GIS_App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI GIS 遥感智能解译系统 (Pro)")
        self.setGeometry(100, 100, 1400, 900)
        
        # 持久化设置
        self.settings = QSettings("AI_GIS_Lab", "AI_GIS_Pro")
        
        self.img_paths = [] 
        self.results = {} 
        
        # 导航数据
        self.all_detections = []
        self.current_filtered_detections = []
        self.current_index = -1
        self.highlight_item = None 
        self.current_cv_img = None # Cache for heatmap
        self.is_heatmap = False
        self.min_conf = 0.2
        
        # 图层管理
        self.layer_groups = {
            'image': None,
            'vector': None,
            'label': None
        }
        self.layer_visibility = {
            'image': True,
            'vector': True,
            'label': True
        }
        
        # 测量相关
        self.measure_points = []
        self.measure_items = []
        self.current_transform = None # 用于像素转地理坐标
        
        self.apply_stylesheet()
        self.init_ui()
        self.create_menus()
        self.create_dock_windows()
        self.init_status_bar()
        self.load_settings()

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #282c34; color: #abb2bf; }
            QWidget { font-family: 'Arial', 'Microsoft YaHei', sans-serif; font-size: 14px; }
            QLabel { color: #abb2bf; }
            QPushButton {
                background-color: #61afef; color: #282c34; border: none; padding: 8px 16px;
                border-radius: 4px; font-weight: bold;
            }
            QPushButton:hover { background-color: #528bff; }
            QPushButton:disabled { background-color: #3e4451; color: #5c6370; }
            QTextEdit, QTableWidget, QListWidget {
                background-color: #21252b; color: #abb2bf; border: 1px solid #181a1f; border-radius: 4px;
            }
            QHeaderView::section {
                background-color: #21252b; color: #abb2bf; padding: 4px; border: 1px solid #181a1f;
            }
            QComboBox {
                background-color: #21252b; color: #abb2bf; border: 1px solid #181a1f; padding: 4px;
            }
            QToolBar { background-color: #21252b; border-bottom: 1px solid #181a1f; spacing: 10px; }
            QToolButton { background-color: transparent; border: none; padding: 4px; color: #abb2bf; } /* 修复工具栏字体颜色 */
            QToolButton:hover { background-color: #3e4451; border-radius: 4px; }
            QProgressBar {
                border: 1px solid #181a1f; border-radius: 4px; text-align: center; color: #abb2bf;
            }
            QProgressBar::chunk { background-color: #98c379; }
            QGroupBox { 
                border: 1px solid #3e4451; border-radius: 4px; margin-top: 10px; padding-top: 10px; font-weight: bold; color: #61afef; 
            }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
            QToolBox::tab {
                background: #21252b;
                color: #abb2bf;
                border-radius: 4px;
                border: 1px solid #3e4451;
            }
            QToolBox::tab:selected {
                font-weight: bold;
                color: #61afef;
            }
        """)
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # --- 左侧控制栏 (使用 QToolBox 优化布局) ---
        left_panel = QWidget()
        left_panel.setMinimumWidth(400)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        title_lbl = QLabel("<h2>🛰️ AI 遥感检测 Pro</h2>")
        title_lbl.setStyleSheet("color: #61afef; margin-bottom: 10px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title_lbl)
        
        self.toolbox = QToolBox()
        left_layout.addWidget(self.toolbox)
        
        # Page 1: 模型与配置
        page_config = QWidget()
        config_layout = QVBoxLayout(page_config)
        
        # 模型选择
        config_layout.addWidget(QLabel("选择检测模型:"))
        self.combo_model = QComboBox()
        self.combo_model.addItem("YOLOv8n-OBB (遥感/DOTA) - 旋转框", resource_path(os.path.join("models", "yolov8n-obb.pt")))
        self.combo_model.addItem("YOLOv8x-OBB (遥感/DOTA) - 高精旋转", resource_path(os.path.join("models", "yolov8x-obb.pt")))
        self.combo_model.addItem("YOLOv8n (通用/COCO) - 速度快", resource_path(os.path.join("models", "yolov8n.pt")))
        self.combo_model.addItem("YOLOv8x (通用/COCO) - 精度高", resource_path(os.path.join("models", "yolov8x.pt")))
        self.combo_model.currentIndexChanged.connect(self.on_model_changed)
        config_layout.addWidget(self.combo_model)
        
        self.lbl_model_desc = QLabel("适合航拍视角，支持旋转目标检测 (如船只、车辆)")
        self.lbl_model_desc.setWordWrap(True)
        self.lbl_model_desc.setStyleSheet("font-size: 12px; color: #98c379; margin-bottom: 10px;")
        config_layout.addWidget(self.lbl_model_desc)
        
        # 推理参数
        param_group = QGroupBox("推理参数微调")
        param_layout = QVBoxLayout(param_group)
        
        # IOU
        iou_layout = QHBoxLayout()
        iou_layout.addWidget(QLabel("NMS IOU:"))
        self.spin_iou = QSlider(Qt.Orientation.Horizontal)
        self.spin_iou.setRange(1, 100)
        self.spin_iou.setValue(45)
        iou_layout.addWidget(self.spin_iou)
        self.lbl_iou_val = QLabel("0.45")
        self.spin_iou.valueChanged.connect(lambda v: self.lbl_iou_val.setText(f"{v/100:.2f}"))
        iou_layout.addWidget(self.lbl_iou_val)
        param_layout.addLayout(iou_layout)
        
        # Conf
        conf_layout = QHBoxLayout()
        conf_layout.addWidget(QLabel("Min Conf:"))
        self.spin_conf_infer = QSlider(Qt.Orientation.Horizontal)
        self.spin_conf_infer.setRange(1, 100)
        self.spin_conf_infer.setValue(25)
        conf_layout.addWidget(self.spin_conf_infer)
        self.lbl_conf_infer_val = QLabel("0.25")
        self.spin_conf_infer.valueChanged.connect(lambda v: self.lbl_conf_infer_val.setText(f"{v/100:.2f}"))
        conf_layout.addWidget(self.lbl_conf_infer_val)
        param_layout.addLayout(conf_layout)
        
        config_layout.addWidget(param_group)
        config_layout.addStretch()
        
        self.toolbox.addItem(page_config, "🛠️ 模型与配置")
        
        # Page 2: 任务队列
        page_task = QWidget()
        task_layout = QVBoxLayout(page_task)
        
        btn_layout = QHBoxLayout()
        self.btn_img = QPushButton("➕ 影像")
        self.btn_img.clicked.connect(self.select_image)
        btn_layout.addWidget(self.btn_img)
        
        self.btn_folder = QPushButton("📂 文件夹")
        self.btn_folder.clicked.connect(self.select_folder)
        btn_layout.addWidget(self.btn_folder)
        
        self.btn_clear = QPushButton("🗑️")
        self.btn_clear.setFixedWidth(40)
        self.btn_clear.clicked.connect(self.clear_queue)
        btn_layout.addWidget(self.btn_clear)
        
        task_layout.addLayout(btn_layout)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.file_list.itemClicked.connect(self.on_file_clicked)
        task_layout.addWidget(self.file_list)
        
        # Output
        out_layout = QHBoxLayout()
        self.line_output = QLineEdit()
        self.line_output.setPlaceholderText("结果保存目录...")
        self.line_output.setReadOnly(True)
        out_layout.addWidget(self.line_output)
        self.btn_browse = QPushButton("📂")
        self.btn_browse.setFixedWidth(40)
        self.btn_browse.clicked.connect(self.select_output_dir)
        out_layout.addWidget(self.btn_browse)
        task_layout.addLayout(out_layout)
        
        self.btn_run = QPushButton("🚀 批量开始智能解译")
        self.btn_run.clicked.connect(self.start_process)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet("background-color: #98c379; color: #282c34; font-size: 16px; padding: 12px;")
        task_layout.addWidget(self.btn_run)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        task_layout.addWidget(self.progress_bar)
        
        status_layout = QHBoxLayout()
        self.lbl_eta = QLabel("ETA: --:--")
        self.lbl_usage = QLabel("CPU: --%")
        status_layout.addWidget(self.lbl_eta)
        status_layout.addStretch()
        status_layout.addWidget(self.lbl_usage)
        task_layout.addLayout(status_layout)
        
        self.toolbox.addItem(page_task, "📂 任务队列")
        self.toolbox.setCurrentIndex(1) # Default to task page
        
        # Page 3: 结果与日志
        page_res = QWidget()
        res_layout = QVBoxLayout(page_res)
        
        self.btn_export = QPushButton("💾 导出结果 (Excel/GeoJSON/KML)")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet("background-color: #d19a66; color: #282c34; font-weight: bold;")
        res_layout.addWidget(self.btn_export)
        
        res_layout.addWidget(QLabel("运行日志:"))
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        res_layout.addWidget(self.log_box)
        
        self.toolbox.addItem(page_res, "📊 结果与日志")
        
        splitter.addWidget(left_panel)

        # --- 右侧展示区 (多视图) ---
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # 0. 视图切换栏
        view_switch_bar = QFrame()
        view_switch_bar.setStyleSheet("background-color: #21252b; border-bottom: 1px solid #181a1f;")
        view_switch_layout = QHBoxLayout(view_switch_bar)
        view_switch_layout.setContentsMargins(10, 5, 10, 5)
        
        # 样式：未选中时透明背景白字，选中时蓝色背景黑字
        btn_style = """
            QPushButton {
                background-color: transparent; 
                color: #abb2bf; 
                border: 1px solid #3e4451; 
                padding: 6px 12px;
                border-radius: 4px;
            }
            QPushButton:checked {
                background-color: #61afef;
                color: #282c34;
                border: none;
            }
            QPushButton:hover:!checked {
                background-color: #3e4451;
            }
        """
        
        self.btn_view_img = QPushButton("🖼️ 影像视图")
        self.btn_view_img.setCheckable(True)
        self.btn_view_img.setChecked(True)
        self.btn_view_img.setStyleSheet(btn_style)
        self.btn_view_img.clicked.connect(lambda: self.switch_right_view(0))
        
        self.btn_view_chart = QPushButton("📊 统计图表")
        self.btn_view_chart.setCheckable(True)
        self.btn_view_chart.setStyleSheet(btn_style)
        self.btn_view_chart.clicked.connect(lambda: self.switch_right_view(1))
        
        # 互斥按钮组
        self.view_group = QButtonGroup(self)
        self.view_group.addButton(self.btn_view_img)
        self.view_group.addButton(self.btn_view_chart)
        
        view_switch_layout.addWidget(self.btn_view_img)
        view_switch_layout.addWidget(self.btn_view_chart)
        view_switch_layout.addStretch()
        
        right_layout.addWidget(view_switch_bar)

        # 1. 堆叠部件
        self.stack_right = QStackedWidget()
        right_layout.addWidget(self.stack_right)
        
        # --- Page 1: 影像视图 ---
        page_img = QWidget()
        page_img_layout = QVBoxLayout(page_img)
        page_img_layout.setContentsMargins(0,0,0,0)
        page_img_layout.setSpacing(0)
        
        # 工具栏
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        page_img_layout.addWidget(toolbar)
        
        self.add_toolbar_action(toolbar, "🔍 放大", self.action_zoom_in)
        self.add_toolbar_action(toolbar, "🔍 缩小", self.action_zoom_out)
        self.add_toolbar_action(toolbar, "🖼️ 适应窗口", self.action_fit_view)
        self.add_toolbar_action(toolbar, "📷 截图", self.action_screenshot)
        toolbar.addSeparator()
        self.add_toolbar_action(toolbar, "✋ 拖拽模式", self.action_pan_mode)
        
        # 测量工具
        toolbar.addSeparator()
        self.add_toolbar_action(toolbar, "📏 测距", self.action_measure_dist)
        self.add_toolbar_action(toolbar, "📐 测面积", self.action_measure_area)
        self.add_toolbar_action(toolbar, "❌ 清除测量", self.clear_measure)
        
        # 热力图开关
        toolbar.addSeparator()
        self.chk_heatmap = QCheckBox("🔥 热力图模式")
        self.chk_heatmap.setStyleSheet("color: #e06c75; font-weight: bold; margin-left: 10px;")
        self.chk_heatmap.stateChanged.connect(self.toggle_heatmap)
        toolbar.addWidget(self.chk_heatmap)

        # 图片视图
        self.scene = QGraphicsScene()
        self.view = ZoomableGraphicsView(self.scene)
        self.view.clicked_signal.connect(self.on_view_clicked) # 连接点击信号
        self.view.mouse_moved_signal.connect(self.on_mouse_moved)
        page_img_layout.addWidget(self.view)
        
        # 底部导航栏
        nav_bar = QFrame()
        nav_bar.setStyleSheet("background-color: #21252b; border-top: 1px solid #181a1f;")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(10, 5, 10, 5)
        
        # 1. 类别筛选
        nav_layout.addWidget(QLabel("筛选类别:"))
        self.combo_classes = QComboBox()
        self.combo_classes.setMinimumWidth(100)
        self.combo_classes.currentTextChanged.connect(self.on_class_changed)
        nav_layout.addWidget(self.combo_classes)
        
        # 2. 置信度滑块
        nav_layout.addSpacing(20)
        nav_layout.addWidget(QLabel("置信度:"))
        self.lbl_conf = QLabel("0.20")
        self.lbl_conf.setFixedWidth(40)
        nav_layout.addWidget(self.lbl_conf)
        
        self.slider_conf = QSlider(Qt.Orientation.Horizontal)
        self.slider_conf.setRange(20, 95) # 0.20 - 0.95
        self.slider_conf.setValue(20)
        self.slider_conf.setFixedWidth(120)
        self.slider_conf.valueChanged.connect(self.on_conf_changed)
        nav_layout.addWidget(self.slider_conf)
        
        nav_layout.addStretch()
        
        self.btn_prev = QPushButton("⬅️ 上一个")
        self.btn_prev.clicked.connect(self.prev_object)
        self.btn_prev.setFixedWidth(100)
        nav_layout.addWidget(self.btn_prev)
        
        self.lbl_counter = QLabel("0 / 0")
        self.lbl_counter.setFixedWidth(80)
        self.lbl_counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_counter.setStyleSheet("font-weight: bold; font-size: 16px;")
        nav_layout.addWidget(self.lbl_counter)
        
        self.btn_next = QPushButton("下一个 ➡️")
        self.btn_next.clicked.connect(self.next_object)
        self.btn_next.setFixedWidth(100)
        nav_layout.addWidget(self.btn_next)
        
        page_img_layout.addWidget(nav_bar)
        self.stack_right.addWidget(page_img)
        
        # --- Page 2: 大图表视图 ---
        page_chart = QWidget()
        page_chart_layout = QVBoxLayout(page_chart)
        
        # 图表控制栏
        chart_ctrl_layout = QHBoxLayout()
        chart_ctrl_layout.setContentsMargins(20, 20, 20, 0)
        chart_ctrl_layout.addWidget(QLabel("📊 统计图表类型:"))
        
        self.combo_chart_type = QComboBox()
        self.combo_chart_type.addItems(["柱状图 (Bar)", "饼图 (Pie)", "置信度分布 (Hist)"])
        self.combo_chart_type.setMinimumWidth(200)
        self.combo_chart_type.currentTextChanged.connect(self.update_chart)
        chart_ctrl_layout.addWidget(self.combo_chart_type)
        
        chart_ctrl_layout.addStretch()
        page_chart_layout.addLayout(chart_ctrl_layout)

        self.large_chart_canvas = MplCanvas(self, width=10, height=8, dpi=100)
        page_chart_layout.addWidget(self.large_chart_canvas)
        self.stack_right.addWidget(page_chart)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([450, 950])

    def create_menus(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: #21252b; color: #abb2bf;")
        
        # File Menu
        file_menu = menubar.addMenu("文件 (File)")
        
        action_open_img = QAction("打开影像", self)
        action_open_img.triggered.connect(self.select_image)
        file_menu.addAction(action_open_img)
        
        action_open_folder = QAction("打开文件夹", self)
        action_open_folder.triggered.connect(self.select_folder)
        file_menu.addAction(action_open_folder)
        
        file_menu.addSeparator()
        
        action_save_proj = QAction("保存项目 (Save Project)", self)
        action_save_proj.setShortcut("Ctrl+S")
        action_save_proj.triggered.connect(self.save_project)
        file_menu.addAction(action_save_proj)
        
        action_load_proj = QAction("加载项目 (Load Project)", self)
        action_load_proj.setShortcut("Ctrl+O")
        action_load_proj.triggered.connect(self.load_project)
        file_menu.addAction(action_load_proj)
        
        file_menu.addSeparator()
        
        action_exit = QAction("退出", self)
        action_exit.triggered.connect(self.close)
        file_menu.addAction(action_exit)
        
        # View Menu
        view_menu = menubar.addMenu("视图 (View)")
        self.action_toggle_layer = QAction("图层管理器", self)
        self.action_toggle_layer.setCheckable(True)
        self.action_toggle_layer.setChecked(True)
        self.action_toggle_layer.triggered.connect(lambda: self.dock_layer.setVisible(self.action_toggle_layer.isChecked()))
        view_menu.addAction(self.action_toggle_layer)

    def create_dock_windows(self):
        # Layer Manager Dock
        self.dock_layer = QDockWidget("图层管理 (Layers)", self)
        self.dock_layer.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        
        layer_widget = QWidget()
        layer_layout = QVBoxLayout(layer_widget)
        
        self.chk_layer_img = QCheckBox("显示原始影像")
        self.chk_layer_img.setChecked(True)
        self.chk_layer_img.stateChanged.connect(lambda s: self.toggle_layer('image', s))
        layer_layout.addWidget(self.chk_layer_img)
        
        self.chk_layer_vec = QCheckBox("显示检测框")
        self.chk_layer_vec.setChecked(True)
        self.chk_layer_vec.stateChanged.connect(lambda s: self.toggle_layer('vector', s))
        layer_layout.addWidget(self.chk_layer_vec)
        
        self.chk_layer_lbl = QCheckBox("显示标签文字")
        self.chk_layer_lbl.setChecked(True)
        self.chk_layer_lbl.stateChanged.connect(lambda s: self.toggle_layer('label', s))
        layer_layout.addWidget(self.chk_layer_lbl)
        
        layer_layout.addStretch()
        self.dock_layer.setWidget(layer_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_layer)

    def init_status_bar(self):
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("background-color: #21252b; color: #abb2bf;")
        
        self.lbl_coords = QLabel("Ready")
        self.lbl_coords.setStyleSheet("padding: 0 10px;")
        self.status_bar.addPermanentWidget(self.lbl_coords)

    def load_settings(self):
        # Restore geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Restore last output dir
        last_output = self.settings.value("last_output_dir")
        if last_output:
            self.line_output.setText(last_output)
            
        # Restore model selection
        last_model_idx = self.settings.value("last_model_index", type=int)
        if last_model_idx is not None:
            self.combo_model.setCurrentIndex(last_model_idx)

    def save_settings(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("last_output_dir", self.line_output.text())
        self.settings.setValue("last_model_index", self.combo_model.currentIndex())

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_project(self):
        path, _ = QFileDialog.getSaveFileName(self, "保存项目", "project.json", "JSON Files (*.json)")
        if not path: return
        
        data = {
            "img_paths": self.img_paths,
            "results": self.results, # Note: results might contain non-serializable data if not careful, but currently dicts/lists
            "output_dir": self.line_output.text()
        }
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.status_bar.showMessage(f"项目已保存: {path}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "加载项目", "", "JSON Files (*.json)")
        if not path: return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.img_paths = data.get("img_paths", [])
            self.results = data.get("results", {})
            output_dir = data.get("output_dir", "")
            
            # Restore UI
            self.file_list.clear()
            for p in self.img_paths:
                base_name = os.path.basename(p)
                item = QListWidget(self.file_list).item(0) # Dummy
                self.file_list.addItem(base_name)
                # Find the item we just added
                item = self.file_list.item(self.file_list.count() - 1)
                
                # Check if processed
                if p in self.results:
                    item.setForeground(QColor("#98c379"))
                    item.setText(f"✅ {base_name}")
                
                item.setData(Qt.ItemDataRole.UserRole, p)
                
            self.line_output.setText(output_dir)
            if self.img_paths and output_dir:
                self.btn_run.setEnabled(True)
                self.btn_export.setEnabled(bool(self.results))
                
            self.status_bar.showMessage(f"项目已加载: {path}", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")

    def toggle_layer(self, layer_name, state):
        is_visible = (state == Qt.CheckState.Checked.value)
        self.layer_visibility[layer_name] = is_visible
        
        group = self.layer_groups.get(layer_name)
        if group:
            group.setVisible(is_visible)

    def on_mouse_moved(self, pos):
        px_x, px_y = pos.x(), pos.y()
        text = f"Pixel: ({int(px_x)}, {int(px_y)})"
        
        if self.current_transform:
            # Pixel to Geo
            gx, gy = rasterio.transform.xy(self.current_transform, px_y, px_x, offset='center')
            text += f" | Geo: ({gx:.6f}, {gy:.6f})"
            
        self.lbl_coords.setText(text)

    def switch_right_view(self, index):
        self.stack_right.setCurrentIndex(index)
        if index == 0:
            self.btn_view_img.setChecked(True)
        else:
            self.btn_view_chart.setChecked(True)
            # 切换到图表时刷新一下
            self.update_chart()

    def select_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "选择结果保存目录")
        if path:
            self.line_output.setText(path)
            if self.img_paths:
                self.btn_run.setEnabled(True)

    def on_model_changed(self, index):
        data = self.combo_model.currentData()
        if "obb" in data:
            self.lbl_model_desc.setText("适合航拍视角，支持旋转目标检测 (如船只、车辆)")
        else:
            self.lbl_model_desc.setText("适合平视/街景视角，仅支持水平框检测 (如行人、普通车辆)")

    def add_toolbar_action(self, toolbar, text, callback):
        action = QAction(text, self)
        action.triggered.connect(callback)
        toolbar.addAction(action)

    # --- 工具栏回调 ---
    def action_zoom_in(self):
        self.view.zoom_in()
    
    def action_zoom_out(self):
        self.view.zoom_out()
        
    def action_fit_view(self):
        self.view.reset_zoom()
        
    def action_screenshot(self):
        # 截图当前视图
        if not self.scene.items():
            return
            
        # 弹出保存对话框
        path, _ = QFileDialog.getSaveFileName(self, "保存截图", "screenshot.png", "Images (*.png *.jpg)")
        if path:
            # 获取场景的边界矩形
            rect = self.scene.itemsBoundingRect()
            # 创建图像
            image = QImage(rect.size().toSize(), QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(image)
            self.scene.render(painter, target=QRectF(image.rect()), source=rect)
            painter.end()
            
            image.save(path)
            self.log_box.append(f"截图已保存: {path}")
        
    def action_pan_mode(self):
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.view.measure_mode = None
        self.view.setCursor(Qt.CursorShape.OpenHandCursor)

    def action_measure_dist(self):
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.measure_mode = 'distance'
        self.view.setCursor(Qt.CursorShape.CrossCursor)
        self.measure_points = []
        self.log_box.append("📏 进入测距模式：请在图上点击两点...")

    def action_measure_area(self):
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.view.measure_mode = 'area'
        self.view.setCursor(Qt.CursorShape.CrossCursor)
        self.measure_points = []
        self.log_box.append("📐 进入测面积模式：请在图上点击多点 (右键或双击结束暂不支持，请点击3个点以上自动闭合计算)...")

    def clear_measure(self):
        for item in self.measure_items:
            self.scene.removeItem(item)
        self.measure_items = []
        self.measure_points = []
        self.log_box.append("已清除测量结果。")

    def on_view_clicked(self, pos):
        if not self.view.measure_mode: return
        
        self.measure_points.append(pos)
        
        # 绘制点
        ellipse = QGraphicsEllipseItem(pos.x()-2, pos.y()-2, 4, 4)
        ellipse.setBrush(QBrush(QColor("yellow")))
        self.scene.addItem(ellipse)
        self.measure_items.append(ellipse)
        
        if self.view.measure_mode == 'distance':
            if len(self.measure_points) == 2:
                p1 = self.measure_points[0]
                p2 = self.measure_points[1]
                
                # 绘制线
                line = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
                line.setPen(QPen(QColor("yellow"), 2))
                self.scene.addItem(line)
                self.measure_items.append(line)
                
                # 计算距离
                dist_px = np.sqrt((p1.x()-p2.x())**2 + (p1.y()-p2.y())**2)
                
                # 尝试转换为地理距离
                dist_str = f"{dist_px:.2f} px"
                if self.current_transform:
                    # 简单的分辨率估算 (假设投影坐标系单位为米)
                    res_x = self.current_transform[0]
                    dist_geo = dist_px * res_x
                    dist_str = f"{dist_geo:.2f} m (Est.)"
                
                self.log_box.append(f"📏 距离: {dist_str}")
                
                # 重置
                self.measure_points = []
                
        elif self.view.measure_mode == 'area':
            if len(self.measure_points) > 1:
                # 绘制临时线
                p1 = self.measure_points[-2]
                p2 = self.measure_points[-1]
                line = QGraphicsLineItem(p1.x(), p1.y(), p2.x(), p2.y())
                line.setPen(QPen(QColor("yellow"), 2, Qt.PenStyle.DashLine))
                self.scene.addItem(line)
                self.measure_items.append(line)
            
            # 实时计算面积 (3点以上)
            if len(self.measure_points) >= 3:
                poly_points = [(p.x(), p.y()) for p in self.measure_points]
                poly = Polygon(poly_points)
                area_px = poly.area
                
                area_str = f"{area_px:.2f} px²"
                if self.current_transform:
                    res_x = self.current_transform[0]
                    area_geo = area_px * (res_x ** 2)
                    area_str = f"{area_geo:.2f} m² (Est.)"
                
                self.log_box.append(f"📐 当前面积 ({len(self.measure_points)}点): {area_str}")

    def export_results(self):
        if not self.results:
            QMessageBox.warning(self, "提示", "没有可导出的结果！")
            return
            
        # 弹出菜单选择格式
        menu = QMenu(self)
        action_excel = menu.addAction("导出为 Excel (.xlsx)")
        action_geojson = menu.addAction("导出为 GeoJSON (.json)")
        action_kml = menu.addAction("导出为 KML (.kml)")
        
        action = menu.exec(QCursor.pos())
        if not action: return
        
        save_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not save_dir: return
        
        try:
            count = 0
            for img_path, res in self.results.items():
                detections = res['detections']
                if not detections: continue
                
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                
                # 准备 DataFrame
                data = []
                geometries = []
                for d in detections:
                    data.append({
                        'Class': d['name'],
                        'Score': d['score'],
                        'Image': base_name
                    })
                    # 恢复 Polygon
                    points = d['polygon']
                    # 注意：这里的 points 是像素坐标，如果需要地理坐标需要 transform
                    # 由于我们在 DetectionThread 里已经生成了 Shapefile，这里为了简单，
                    # 我们直接用像素坐标导出 Excel，GeoJSON/KML 需要地理坐标
                    # 如果要地理坐标，需要重新读取 transform
                    
                df = pd.DataFrame(data)
                
                if action == action_excel:
                    out_path = os.path.join(save_dir, f"{base_name}_result.xlsx")
                    df.to_excel(out_path, index=False)
                    
                elif action == action_geojson or action == action_kml:
                    # 需要重新计算地理坐标
                    with rasterio.open(img_path) as src:
                        transform = src.transform
                        crs = src.crs
                    
                    geo_polys = []
                    for d in detections:
                        points = d['polygon']
                        geo_points = []
                        for px, py in points:
                            gx, gy = rasterio.transform.xy(transform, py, px, offset='center')
                            geo_points.append((gx, gy))
                        geo_polys.append(Polygon(geo_points))
                        
                    gdf = gpd.GeoDataFrame(df, geometry=geo_polys, crs=crs)
                    
                    if action == action_geojson:
                        out_path = os.path.join(save_dir, f"{base_name}_result.json")
                        gdf.to_file(out_path, driver='GeoJSON')
                    else:
                        out_path = os.path.join(save_dir, f"{base_name}_result.kml")
                        # KML driver support varies, try/except
                        try:
                            gdf.to_file(out_path, driver='KML')
                        except Exception as e:
                            self.log_box.append(f"KML 导出失败 (可能缺少驱动): {str(e)}")
                            continue
                            
                count += 1
                
            QMessageBox.information(self, "成功", f"已成功导出 {count} 个文件的结果！")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def add_image_to_list(self, path):
        if path not in self.img_paths:
            self.img_paths.append(path)
            self.file_list.addItem(os.path.basename(path))
            if self.line_output.text():
                self.btn_run.setEnabled(True)
            self.btn_clear.setEnabled(True)

    def select_image(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "选择影像 (支持多选)", "", "GeoTIFF (*.tif *.tiff)")
        if paths:
            for path in paths:
                if path not in self.img_paths:
                    self.img_paths.append(path)
                    self.file_list.addItem(os.path.basename(path))
            
            if self.img_paths:
                # 只有当选择了输出目录时才启用运行
                if self.line_output.text():
                    self.btn_run.setEnabled(True)
                self.btn_clear.setEnabled(True)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择包含影像的文件夹")
        if folder:
            # 递归查找 .tif, .tiff, .jpg, .png
            valid_exts = ('.tif', '.tiff', '.jpg', '.png', '.jpeg')
            count = 0
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.lower().endswith(valid_exts):
                        path = os.path.join(root, file)
                        if path not in self.img_paths:
                            self.img_paths.append(path)
                            self.file_list.addItem(os.path.basename(path))
                            count += 1
            
            if count > 0:
                self.log_box.append(f"已添加文件夹中的 {count} 张影像。")
                if self.line_output.text():
                    self.btn_run.setEnabled(True)
                self.btn_clear.setEnabled(True)
            else:
                QMessageBox.information(self, "提示", "该文件夹下未找到支持的影像文件。")

    def clear_queue(self):
        self.img_paths = []
        self.file_list.clear()
        self.btn_run.setEnabled(False)
        self.results = {}
        self.highlight_item = None # Reset highlight item
        self.current_cv_img = None
        self.scene.clear()
        self.log_box.clear()
        self.large_chart_canvas.axes.clear()
        self.large_chart_canvas.draw()

    def start_process(self):
        if not self.img_paths: return
        
        output_dir = self.line_output.text()
        if not output_dir:
            QMessageBox.warning(self, "提示", "请先选择结果保存目录！")
            return
            
        self.btn_run.setEnabled(False)
        self.log_box.clear()
        self.highlight_item = None # Reset highlight item
        self.current_cv_img = None
        self.scene.clear()
        self.scene.addText("正在批量处理中，请稍候...", QFont("Arial", 20)).setDefaultTextColor(QColor("white"))
        
        # 获取选中的模型路径
        model_path = self.combo_model.currentData()
        
        # 获取参数
        conf = self.spin_conf_infer.value() / 100.0
        iou = self.spin_iou.value() / 100.0
        
        self.worker = DetectionThread(model_path, self.img_paths, output_dir, conf=conf, iou=iou)
        self.worker.log_signal.connect(self.log_box.append)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.result_signal.connect(self.show_result)
        self.worker.finish_signal.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, percent, eta, usage):
        self.progress_bar.setValue(percent)
        self.lbl_eta.setText(eta)
        self.lbl_usage.setText(usage)

    def show_result(self, img_path, vis_path, stats_text, detections_list):
        # Store result
        self.results[img_path] = {
            'vis_path': vis_path,
            'stats': stats_text,
            'detections': detections_list
        }
        
        self.btn_export.setEnabled(True) # Enable export button
        
        # Update list item style
        base_name = os.path.basename(img_path)
        items = self.file_list.findItems(base_name, Qt.MatchFlag.MatchExactly)
        if items:
            item = items[0]
            item.setForeground(QColor("#98c379")) # Green text
            item.setText(f"✅ {base_name}")
            # Store full path in item data for retrieval
            item.setData(Qt.ItemDataRole.UserRole, img_path)

        # If it's the first result or currently selected, display it
        self.display_result(img_path)

    def on_file_clicked(self, item):
        img_path = item.data(Qt.ItemDataRole.UserRole)
        if not img_path:
            # Try to find by name if data not set (e.g. before processing)
            text = item.text().replace("✅ ", "")
            for p in self.img_paths:
                if os.path.basename(p) == text:
                    img_path = p
                    break
        
        if img_path:
            if img_path in self.results:
                self.display_result(img_path)
            else:
                # Show original image if not processed yet
                if os.path.exists(img_path):
                    self.highlight_item = None # Reset highlight item
                    self.current_cv_img = None
                    self.scene.clear()
                    self.scene.addPixmap(QPixmap(img_path))
                    self.view.reset_zoom()
                    self.log_box.append(f"预览: {os.path.basename(img_path)}")
                    
                    # Try to get transform for measurement
                    try:
                        with rasterio.open(img_path) as src:
                            self.current_transform = src.transform
                    except:
                        self.current_transform = None

    def display_result(self, img_path):
        if img_path not in self.results: return
        
        res = self.results[img_path]
        # vis_path = res['vis_path'] # 不再使用预渲染的图片
        detections_list = res['detections']
        
        # 显示统计信息到日志
        if 'stats' in res:
            self.log_box.append(res['stats'])
        
        self.all_detections = detections_list
        
        # 加载原始图片用于动态绘制
        if os.path.exists(img_path):
            # 缓存 OpenCV 图像用于热力图
            # 注意：rasterio 读取的可能是多波段，这里简化为读取 RGB 用于显示
            # 为了速度，我们用 cv2 读取 (假设是标准 TIFF/JPG)
            # 如果是 GeoTIFF 多波段，cv2 可能读不出来，需要用 rasterio
            # 这里为了稳健，我们还是用 rasterio 读取并转为 numpy
            try:
                with rasterio.open(img_path) as src:
                    self.current_transform = src.transform # Update transform for measurement
                    img_data = src.read()
                    # (bands, h, w) -> (h, w, bands)
                    img_array = np.transpose(img_data, (1, 2, 0))
                    
                    # Handle dimensions
                    if len(img_array.shape) == 2:
                        img_array = np.expand_dims(img_array, axis=2)

                    # 只取前3个波段
                    if img_array.shape[2] >= 3:
                        img_array = img_array[:, :, :3]
                    
                    # 转换为 uint8
                    if img_array.dtype != np.uint8:
                        # 简单的归一化
                        min_val = np.nanmin(img_array)
                        max_val = np.nanmax(img_array)
                        if max_val > min_val:
                            img_array = ((img_array - min_val) / (max_val - min_val) * 255).astype(np.uint8)
                        else:
                            img_array = np.zeros_like(img_array, dtype=np.uint8)
                    
                    if img_array.shape[2] == 1:
                        self.current_cv_img = cv2.cvtColor(img_array, cv2.COLOR_GRAY2BGR)
                    else:
                        self.current_cv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Rasterio load failed: {e}")
                # Fallback to cv2
                self.current_cv_img = cv2.imread(img_path)
            
            # 更新类别下拉框
            unique_classes = sorted(list(set([d['name'] for d in detections_list])))
            self.combo_classes.blockSignals(True)
            self.combo_classes.clear()
            self.combo_classes.addItem("全部")
            self.combo_classes.addItems(unique_classes)
            self.combo_classes.blockSignals(False)
            
            # 触发重绘
            self.refresh_scene()
        else:
            self.scene.addText("图片加载失败")

    def on_conf_changed(self, value):
        self.min_conf = value / 100.0
        self.lbl_conf.setText(f"{self.min_conf:.2f}")
        self.refresh_scene()

    def toggle_heatmap(self, state):
        self.is_heatmap = (state == Qt.CheckState.Checked.value)
        self.refresh_scene()

    def refresh_scene(self):
        if self.current_cv_img is None: return
        
        # 1. 过滤检测结果
        filtered = [d for d in self.all_detections if d['score'] >= self.min_conf]
        
        # 2. 再次根据类别过滤
        cls_text = self.combo_classes.currentText()
        if cls_text != "全部":
            filtered = [d for d in filtered if d['name'] == cls_text]
            
        self.current_filtered_detections = filtered
        self.update_chart(filtered)
        self.update_nav_ui()
        
        self.scene.clear()
        self.highlight_item = None
        
        # Create Groups
        self.layer_groups['image'] = QGraphicsItemGroup()
        self.layer_groups['vector'] = QGraphicsItemGroup()
        self.layer_groups['label'] = QGraphicsItemGroup()
        
        # 3. 绘制
        h, w = self.current_cv_img.shape[:2]
        
        if self.is_heatmap:
            # 生成热力图
            heatmap = np.zeros((h, w), dtype=np.float32)
            
            # 简单的点累加
            for d in filtered:
                bbox = d['bbox']
                cx = int((bbox[0] + bbox[2]) / 2)
                cy = int((bbox[1] + bbox[3]) / 2)
                if 0 <= cx < w and 0 <= cy < h:
                    heatmap[cy, cx] += 1
            
            # 高斯模糊
            if len(filtered) > 0:
                heatmap = cv2.GaussianBlur(heatmap, (0, 0), sigmaX=50, sigmaY=50)
                # 归一化
                cv2.normalize(heatmap, heatmap, 0, 255, cv2.NORM_MINMAX)
            
            heatmap = heatmap.astype(np.uint8)
            heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
            
            # 叠加
            # 调整权重让热力图更明显 (原图 0.4, 热力图 0.6)
            overlay = cv2.addWeighted(self.current_cv_img, 0.4, heatmap_color, 0.6, 0)
            
            # 转为 QPixmap
            overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
            h, w, ch = overlay.shape
            bytes_per_line = ch * w
            qimg = QImage(overlay.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(qimg))
            self.layer_groups['image'].addToGroup(pixmap_item)
            
        else:
            # Image Layer
            rgb_img = cv2.cvtColor(self.current_cv_img, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_img.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb_img.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap_item = QGraphicsPixmapItem(QPixmap.fromImage(qimg))
            self.layer_groups['image'].addToGroup(pixmap_item)
            
            # Vector & Label Layers
            pen = QPen(QColor(255, 0, 0)) # 红色
            pen.setWidth(2)
            
            for d in filtered:
                label_x, label_y = 0, 0
                
                if 'polygon' in d:
                    points = d['polygon']
                    qpoints = [QPointF(p[0], p[1]) for p in points]
                    poly_item = QGraphicsPolygonItem(QPolygonF(qpoints))
                    poly_item.setPen(pen)
                    self.layer_groups['vector'].addToGroup(poly_item)
                    label_x, label_y = points[0][0], points[0][1]
                else:
                    bbox = d['bbox']
                    rect_item = QGraphicsRectItem(bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1])
                    rect_item.setPen(pen)
                    self.layer_groups['vector'].addToGroup(rect_item)
                    label_x, label_y = bbox[0], bbox[1]

                # 绘制标签 (背景 + 文字)
                label_str = f"{d['name']} {d['score']:.2f}"
                
                text_item = QGraphicsTextItem(label_str)
                text_item.setDefaultTextColor(QColor("white"))
                text_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                
                br = text_item.boundingRect()
                # 调整标签位置到框的上方
                bg_rect = QGraphicsRectItem(label_x, label_y - br.height(), br.width(), br.height())
                bg_rect.setBrush(QBrush(QColor(255, 0, 0)))
                bg_rect.setPen(QPen(Qt.PenStyle.NoPen))
                
                self.layer_groups['label'].addToGroup(bg_rect)
                
                text_item.setPos(label_x, label_y - br.height())
                text_item.setZValue(1) # 确保文字在背景之上
                self.layer_groups['label'].addToGroup(text_item)

        # Add groups to scene
        self.scene.addItem(self.layer_groups['image'])
        self.scene.addItem(self.layer_groups['vector'])
        self.scene.addItem(self.layer_groups['label'])
        
        # Apply visibility
        self.layer_groups['image'].setVisible(self.layer_visibility['image'])
        self.layer_groups['vector'].setVisible(self.layer_visibility['vector'])
        self.layer_groups['label'].setVisible(self.layer_visibility['label'])

        self.view.reset_zoom()

    def update_chart(self, detections=None):
        # 修正: 信号可能会传入字符串 (combo box text)，需要忽略并使用 self.all_detections
        if detections is None or isinstance(detections, str):
            detections = self.all_detections
            
        if not detections:
            self.large_chart_canvas.axes.clear()
            self.large_chart_canvas.draw()
            return

        from collections import Counter
        
        names = []
        scores = []
        # 确保数据格式正确
        if isinstance(detections, list):
            if len(detections) > 0:
                if isinstance(detections[0], dict):
                    names = [d['name'] for d in detections]
                    scores = [d['score'] for d in detections]
                elif isinstance(detections[0], str):
                    names = detections
        
        if not names:
            return

        counts = Counter(names)
        
        labels = list(counts.keys())
        values = list(counts.values())
        
        chart_type = self.combo_chart_type.currentText()
        
        # 设置中文字体支持 (MacOS/Windows)
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Heiti TC', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False
        
        # --- 绘制大图表 ---
        canvas = self.large_chart_canvas
        canvas.axes.clear()
        
        if "Bar" in chart_type:
            canvas.axes.set_aspect('auto') # 强制重置纵横比
            bars = canvas.axes.bar(labels, values, color='#61afef')
            canvas.axes.set_title('目标数量统计 (Object Counts)', color='white', fontsize=14)
            canvas.axes.tick_params(axis='x', colors='white', rotation=30, labelsize=12)
            canvas.axes.tick_params(axis='y', colors='white', labelsize=12)
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                canvas.axes.text(bar.get_x() + bar.get_width()/2., height,
                        f'{int(height)}', ha='center', va='bottom', color='white', fontsize=12)
        elif "Pie" in chart_type:
            canvas.axes.pie(values, labels=labels, autopct='%1.1f%%', 
                                     textprops={'color':"white", 'fontsize': 12})
            canvas.axes.set_title('类别占比 (Class Distribution)', color='white', fontsize=14)
        elif "Hist" in chart_type:
            canvas.axes.set_aspect('auto') # 强制重置纵横比
            canvas.axes.hist(scores, bins=10, range=(0, 1), color='#61afef', edgecolor='white')
            canvas.axes.set_title('置信度分布 (Confidence)', color='white', fontsize=14)
            canvas.axes.set_xlabel('Score', color='white', fontsize=12)
            canvas.axes.set_ylabel('Count', color='white', fontsize=12)
            canvas.axes.tick_params(colors='white', labelsize=12)
            
        canvas.fig.tight_layout()
        canvas.draw()

    def on_class_changed(self, text):
        if text == "全部":
            self.current_filtered_detections = self.all_detections
        else:
            self.current_filtered_detections = [d for d in self.all_detections if d['name'] == text]
        
        self.current_index = -1
        self.update_nav_ui()
        
        # 如果有结果，自动跳到第一个
        if len(self.current_filtered_detections) > 0:
            self.next_object()

    def update_nav_ui(self):
        total = len(self.current_filtered_detections)
        current = self.current_index + 1 if self.current_index >= 0 else 0
        self.lbl_counter.setText(f"{current} / {total}")
        self.btn_prev.setEnabled(total > 0)
        self.btn_next.setEnabled(total > 0)

    def next_object(self):
        if not self.current_filtered_detections: return
        self.current_index = (self.current_index + 1) % len(self.current_filtered_detections)
        self.jump_to_object()

    def prev_object(self):
        if not self.current_filtered_detections: return
        self.current_index = (self.current_index - 1) % len(self.current_filtered_detections)
        self.jump_to_object()

    def jump_to_object(self):
        self.update_nav_ui()
        if not self.current_filtered_detections or self.current_index < 0: return
        
        obj = self.current_filtered_detections[self.current_index]
        
        # 移除旧的高亮框
        if self.highlight_item:
            if self.highlight_item.scene() == self.scene:
                self.scene.removeItem(self.highlight_item)
            self.highlight_item = None
            
        # 创建新高亮框 (绿色粗框)
        pen = QPen(QColor(0, 255, 0))
        pen.setWidth(4)

        if 'polygon' in obj:
            # 绘制多边形
            points = obj['polygon'] # list of [x, y]
            qpoints = [QPointF(p[0], p[1]) for p in points]
            polygon = QPolygonF(qpoints)
            self.highlight_item = QGraphicsPolygonItem(polygon)
            
            # 计算中心点用于聚焦
            bbox = obj['bbox']
            center_x = (bbox[0] + bbox[2]) / 2
            center_y = (bbox[1] + bbox[3]) / 2
            center_point = QPointF(center_x, center_y)
        else:
            # 兼容旧格式 (矩形)
            bbox = obj['bbox'] # [x1, y1, x2, y2]
            rect = QRectF(bbox[0], bbox[1], bbox[2]-bbox[0], bbox[3]-bbox[1])
            self.highlight_item = QGraphicsRectItem(rect)
            center_point = rect.center()

        self.highlight_item.setPen(pen)
        self.scene.addItem(self.highlight_item)
        
        # 聚焦视图
        self.view.centerOn(center_point)
        # 适当缩放以看清目标 (但不要缩放太大)
        # self.view.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio) # 这个会缩放得太满
        # 我们可以手动设置一个比例，或者只 centerOn
        
    def on_finished(self, msg):
        self.btn_run.setEnabled(True)
        QMessageBox.information(self, "状态", msg)

if __name__ == '__main__':
    try:
        import PyQt6
        plugin_path = os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins')
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
    except:
        pass

    app = QApplication(sys.argv)
    window = AI_GIS_App()
    window.show()
    sys.exit(app.exec())
