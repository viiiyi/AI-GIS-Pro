import os
import urllib.request
import ssl

# 绕过 SSL 验证（解决你的网络问题）
ssl._create_default_https_context = ssl._create_unverified_context

# 这是一个开源的航拍车辆数据集样张 (约 18MB)
url = "https://huggingface.co/datasets/giswqs/geospatial/resolve/main/cars_7cm.tif"
filename = "real_cars.tif"

print(f"开始下载真实航拍影像: {filename} ...")
print("文件大约 18MB，请耐心等待...")

try:
    urllib.request.urlretrieve(url, filename)
    print(f"✅ 下载成功！文件已保存在: {os.path.abspath(filename)}")
except Exception as e:
    print(f"❌ 下载失败: {e}")
