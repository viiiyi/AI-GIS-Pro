import geopandas as gpd
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import os

def view_results(image_path, shapefile_path):
    if not os.path.exists(image_path):
        print(f"错误: 找不到影像文件 {image_path}")
        return
    if not os.path.exists(shapefile_path):
        print(f"错误: 找不到结果文件 {shapefile_path}")
        return

    print(f"正在加载影像: {image_path}")
    print(f"正在加载结果: {shapefile_path}")

    # 读取 Shapefile
    gdf = gpd.read_file(shapefile_path)
    print(f"检测到 {len(gdf)} 个目标")
    print(gdf.head())

    # 设置绘图
    fig, ax = plt.subplots(figsize=(12, 12))

    # 读取并显示影像
    with rasterio.open(image_path) as src:
        show(src, ax=ax, title="AI 检测结果可视化")

    # 显示检测框
    if len(gdf) > 0:
        gdf.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=2)
        
        # 可选：显示类别标签
        for idx, row in gdf.iterrows():
            # 获取几何中心
            centroid = row.geometry.centroid
            ax.text(centroid.x, centroid.y, f"{row['Class']}:{row['Score']:.2f}", 
                    fontsize=8, color='yellow', ha='center')

    plt.show()

if __name__ == "__main__":
    # 默认文件名，您可以根据实际情况修改
    img_file = "real_cars.tif"  # 或者 "sample_image.tif"
    shp_file = "result_fixed.shp"
    
    # 如果默认影像不存在，尝试找一下 sample_image.tif
    if not os.path.exists(img_file) and os.path.exists("sample_image.tif"):
        img_file = "sample_image.tif"

    view_results(img_file, shp_file)
