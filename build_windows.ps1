# AI GIS Pro - Windows PowerShell 构建脚本
# 使用: powershell -ExecutionPolicy Bypass -File build_windows.ps1

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "AI GIS Pro - Windows 构建脚本 (PowerShell)" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Python
Write-Host "🔍 检查 Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python 已找到: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ 错误: 未找到 Python。请确保 Python 已安装且在 PATH 中。" -ForegroundColor Red
    pause
    exit 1
}

# 检查 Conda
Write-Host "🔍 检查 Conda 环境..." -ForegroundColor Yellow
$condaCheck = conda info --envs 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  警告: 未检测到 Conda。" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "强烈建议使用 Conda 环境！推荐步骤:" -ForegroundColor Yellow
    Write-Host "  conda create -n ai_gis_win python=3.11" -ForegroundColor Gray
    Write-Host "  conda activate ai_gis_win" -ForegroundColor Gray
    Write-Host "  conda install -c conda-forge geopandas rasterio fiona pyogrio" -ForegroundColor Gray
    Write-Host "  pip install -r requirements.txt" -ForegroundColor Gray
    Write-Host ""
    $response = Read-Host "继续构建？(y/n)"
    if ($response -ne "y") {
        exit 1
    }
} else {
    Write-Host "✓ Conda 已找到" -ForegroundColor Green
}

# 检查依赖
Write-Host ""
Write-Host "📦 检查依赖..." -ForegroundColor Yellow
$deps = @("PyInstaller", "ultralytics", "torch", "torchvision", "PyQt6", "rasterio", "geopandas")
$missing = @()

foreach ($dep in $deps) {
    $check = pip list 2>&1 | Select-String $dep
    if (-not $check) {
        $missing += $dep
    }
}

if ($missing.Count -gt 0) {
    Write-Host "❌ 缺少依赖: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "请运行: pip install -r requirements.txt" -ForegroundColor Yellow
    pause
    exit 1
}
Write-Host "✓ 所有依赖已就绪" -ForegroundColor Green

# 清理旧构建
Write-Host ""
Write-Host "🧹 清理旧构建文件..." -ForegroundColor Yellow
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
}
if (Test-Path "dist") {
    Remove-Item -Recurse -Force "dist" -ErrorAction SilentlyContinue
}
Write-Host "✓ 清理完成" -ForegroundColor Green

# 开始构建
Write-Host ""
Write-Host "🚀 开始构建 AI GIS Pro (Windows 64-bit)..." -ForegroundColor Cyan
Write-Host "这可能需要 5-15 分钟，请耐心等待..." -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date
$buildLog = "build_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

pyinstaller AI_GIS_Pro_Windows.spec --distpath dist --buildpath build | Tee-Object -FilePath $buildLog

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ 构建失败！" -ForegroundColor Red
    Write-Host "构建日志已保存到: $buildLog" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "请检查错误信息。常见问题:" -ForegroundColor Yellow
    Write-Host "  1. GDAL/Rasterio 二进制不兼容 -> 使用 conda 安装" -ForegroundColor Gray
    Write-Host "  2. 模块未找到 -> 检查 spec 文件中的 hiddenimports" -ForegroundColor Gray
    Write-Host "  3. 内存不足 -> 关闭其他应用后重试" -ForegroundColor Gray
    pause
    exit 1
}

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalMinutes

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "✅ 构建成功！构耗时: $([math]::Round($duration, 2)) 分钟" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 可执行文件位置: dist\AI_GIS_Pro\" -ForegroundColor Cyan
Write-Host "📌 主程序文件: dist\AI_GIS_Pro\AI_GIS_Pro.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 下一步:" -ForegroundColor Yellow
Write-Host "   1. 测试程序: .\dist\AI_GIS_Pro\AI_GIS_Pro.exe" -ForegroundColor Gray
Write-Host "   2. 分发: 将 dist\AI_GIS_Pro 文件夹压缩为 ZIP" -ForegroundColor Gray
Write-Host ""
Write-Host "📚 有问题? 查看 BUILD_WINDOWS.md 了解详细信息。" -ForegroundColor Yellow
Write-Host ""

# 提示打开文件夹
$openFolder = Read-Host "是否打开输出文件夹? (y/n)"
if ($openFolder -eq "y") {
    explorer.exe "dist"
}

pause
