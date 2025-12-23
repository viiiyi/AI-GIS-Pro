import numpy as np
import rasterio
from rasterio.transform import from_origin

# 1. 创建模拟数据 (RGB 3波段, 1000x1000像素)
# 我们画几个随机的亮斑，假装是目标
data = np.zeros((3, 1000, 1000), dtype='uint8')

# 背景设为灰色
data[:, :, :] = 100

# 模拟几个"目标" (画几个白色的方块)
for i in range(10):
    x = np.random.randint(0, 900)
    y = np.random.randint(0, 900)
    # 在这些位置画白框 (255,255,255)
    data[:, y:y+50, x:x+50] = 255

# 2. 定义地理坐标 (假设在经度117, 纬度34附近)
transform = from_origin(117.0, 34.0, 0.0001, 0.0001) 

# 3. 保存为 GeoTIFF
with rasterio.open('sample_image.tif', 'w', driver='GTiff',
                   height=1000, width=1000, count=3, dtype=data.dtype,
                   crs='+proj=latlong', transform=transform) as dst:
    dst.write(data)

print(">>> 成功！模拟影像 sample_image.tif 已生成。")
