# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for Windows
# 用法: pyinstaller AI_GIS_Pro_Windows.spec

import os
import sys

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models', 'models'),  # 添加 YOLO 模型文件夹
    ],
    hiddenimports=[
        # Rasterio 相关
        'rasterio._features',
        'rasterio._shim',
        'rasterio.sample',
        'rasterio.vrt',
        'rasterio._io',
        # Fiona 相关
        'fiona',
        'fiona.ogrext',
        'fiona._shim',
        'fiona.schema',
        # PyOGRIO 相关
        'pyogrio',
        'pyogrio._geometry',
        'pyogrio._io',
        'pyogrio._err',
        # Shapely
        'shapely',
        'shapely.geometry',
        # Ultralytics
        'ultralytics',
        'ultralytics.models.yolo',
        'ultralytics.models.yolo.detect',
        'ultralytics.models.yolo.obb',
        # PyQt6
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        # 其他重要模块
        'numpy',
        'cv2',
        'torch',
        'torchvision',
        'pandas',
        'geopandas',
        'matplotlib',
        'matplotlib.backends.backend_qt5agg',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'ipython',
        'notebook',
        'jupyter',
        'jupyter_core',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AI_GIS_Pro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AI_GIS_Pro',
)
