# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('models', 'models')],
    hiddenimports=['rasterio._features', 'rasterio._shim', 'rasterio.sample', 'rasterio.vrt', 'rasterio._io', 'fiona', 'fiona.ogrext', 'fiona._shim', 'fiona.schema', 'pyogrio', 'pyogrio._geometry', 'pyogrio._io', 'pyogrio._err', 'shapely', 'shapely.geometry', 'ultralytics'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'ipython', 'notebook'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
app = BUNDLE(
    coll,
    name='AI_GIS_Pro.app',
    icon=None,
    bundle_identifier=None,
)
