import geopandas as gpd
import rasterio
from rasterio.plot import show
import matplotlib.pyplot as plt
import os

def save_visualized_result(image_path, shapefile_path, output_path):
    if not os.path.exists(image_path):
        print(f"错误: 找不到影像文件 {image_path}")
        return
    if not os.path.exists(shapefile_path):
        print(f"错误: 找不到结果文件 {shapefile_path}")
        return

    print(f"正在读取影像: {image_path} ...")
    print(f"正在读取结果: {shapefile_path} ...")

    # 读取 Shapefile
    gdf = gpd.read_file(shapefile_path)
    print(f"共检测到 {len(gdf)} 个目标")

    # 创建画布
    # 注意：对于大图，dpi 设置高一些以保证清晰度
    fig, ax = plt.subplots(figsize=(15, 15))

    # 读取并绘制影像
    with rasterio.open(image_path) as src:
        # 绘制底图
        show(src, ax=ax)
        
        # 绘制检测框
        if len(gdf) > 0:
            print("正在绘制检测框...")
            gdf.plot(ax=ax, facecolor='none', edgecolor='red', linewidth=1.5)
            
            # 标注类别和分数
            for idx, row in gdf.iterrows():
                # 获取几何中心
                centroid = row.geometry.centroid
                # 简单的标签文本
                label = f"{row['Class']}"
                ax.text(centroid.x, centroid.y, label, 
                        fontsize=6, color='yellow', ha='center', va='center', fontweight='bold')

    # 去除坐标轴，使图片更干净
    ax.set_axis_off()
    
    # 保存图片
    print(f"正在保存图片到: {output_path} ...")
    plt.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print("✅ 完成！")

if __name__ == "__main__":
    # 自动查找影像文件
    img_file = "real_cars.tif"
    if not os.path.exists(img_file) and os.path.exists("sample_image.tif"):
        img_file = "sample_image.tif"
        
    shp_file = "result_fixed.shp"
    out_file = "final_result_marked.png"

    save_visualized_result(img_file, shp_file, out_file)
