import PyInstaller.__main__
import os
import sys
import shutil
import platform

# 1. 清理旧构建
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('dist'):
    shutil.rmtree('dist')

# 2. 定义资源文件 (源路径, 目标路径)
# 注意: Windows上分隔符是;, Linux/Mac上是:
# 这里我们使用 --add-data 参数格式
sep = ':' if os.name == 'posix' else ';'

# 获取当前系统
system_name = platform.system()
print(f"🖥️  检测到操作系统: {system_name}")

# 确保 models 文件夹存在
if not os.path.exists('models'):
    os.makedirs('models')

# 3. PyInstaller 参数
args = [
    'main.py',                       # 主程序入口
    '--name=AI_GIS_Pro',             # 生成的可执行文件名称
    '--windowed',                    # GUI模式，不显示控制台 (Windows下有效，Mac下生成.app)
    '--onedir',                      # 生成文件夹模式 (比单文件启动快，且易于排查依赖问题)
    '--clean',                       # 清理缓存
    '--noconfirm',                   # 不确认覆盖
    
    # 添加数据文件: models 文件夹 -> models 文件夹
    f'--add-data=models{sep}models',
    
    # 排除不需要的模块 (减小体积)
    '--exclude-module=tkinter',
    '--exclude-module=ipython',
    '--exclude-module=notebook',
    
    # 收集必要的隐藏导入 (Ultralytics, Rasterio 等有时需要显式指定)
    '--hidden-import=rasterio._features',
    '--hidden-import=rasterio._shim',
    '--hidden-import=rasterio.sample',
    '--hidden-import=rasterio.vrt',
    '--hidden-import=rasterio._io',
    '--hidden-import=fiona',
    '--hidden-import=fiona.ogrext',
    '--hidden-import=fiona._shim',
    '--hidden-import=fiona.schema',
    '--hidden-import=pyogrio',
    '--hidden-import=pyogrio._geometry',
    '--hidden-import=pyogrio._io',
    '--hidden-import=pyogrio._err',
    '--hidden-import=shapely',
    '--hidden-import=shapely.geometry',
    '--hidden-import=ultralytics',
]

# Windows特定配置
if system_name == 'Windows':
    args.extend([
        '--icon=icon.ico',  # 如果有图标文件
    ])

print(f"🚀 开始打包 AI GIS Pro ({system_name})...")
PyInstaller.__main__.run(args)
print("✅ 打包完成！")

# 系统特定的信息提示
if system_name == 'Windows':
    print("\n📦 Windows 可执行文件信息:")
    print("   位置: dist/AI_GIS_Pro/")
    print("   主程序: AI_GIS_Pro.exe")
    print("   分发方式: 将整个 dist/AI_GIS_Pro 文件夹打包为 ZIP 或使用安装程序")
elif system_name == 'Darwin':
    print("\n📦 macOS 应用信息:")
    print("   位置: dist/AI_GIS_Pro.app")
    print("   可以直接双击运行")
else:
    print("\n📦 Linux 可执行文件:")
    print("   位置: dist/AI_GIS_Pro/")
