@echo off
REM AI GIS Pro - Windows 自动构建脚本
REM 使用: 在命令提示符中运行此脚本

echo.
echo ============================================
echo AI GIS Pro - Windows 构建脚本
echo ============================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 Python。请确保 Python 已安装且在 PATH 中。
    pause
    exit /b 1
)

echo ✓ Python 已找到
python --version

REM 检查是否在 conda 环境中
echo.
echo 🔍 检查 Conda 环境...
conda info --envs >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  警告: 未检测到 Conda。强烈建议使用 Conda 环境！
    echo.
    echo 对于 Windows，推荐的环境设置:
    echo   conda create -n ai_gis_win python=3.11
    echo   conda activate ai_gis_win
    echo   conda install -c conda-forge geopandas rasterio fiona pyogrio
    echo   pip install -r requirements.txt
    echo.
    choice /C YN /M "继续构建（可能失败）?"
    if errorlevel 2 exit /b 1
)

REM 检查依赖
echo.
echo 📦 检查依赖...
pip list | findstr PyInstaller >nul
if %errorlevel% neq 0 (
    echo 📥 安装 PyInstaller...
    pip install pyinstaller
)

pip list | findstr ultralytics >nul
if %errorlevel% neq 0 (
    echo ❌ 错误: ultralytics 未安装。请先运行:
    echo    pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✓ 所有依赖已就绪

REM 清理旧构建
echo.
echo 🧹 清理旧构建文件...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo ✓ 清理完成

REM 开始构建
echo.
echo 🚀 开始构建 AI GIS Pro (Windows 64-bit)...
echo 这可能需要 5-15 分钟，请耐心等待...
echo.

pyinstaller AI_GIS_Pro_Windows.spec --distpath dist --buildpath build

if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败！
    echo 请检查上面的错误信息。
    pause
    exit /b 1
)

echo.
echo ============================================
echo ✅ 构建成功！
echo ============================================
echo.
echo 📍 可执行文件位置: dist\AI_GIS_Pro\
echo 📌 主程序文件: dist\AI_GIS_Pro\AI_GIS_Pro.exe
echo.
echo 💡 下一步:
echo    1. 测试程序: 双击 dist\AI_GIS_Pro\AI_GIS_Pro.exe
echo    2. 分发: 将 dist\AI_GIS_Pro 文件夹压缩为 ZIP
echo.
echo 📚 有问题? 查看 BUILD_WINDOWS.md 了解详细信息。
echo.
pause
