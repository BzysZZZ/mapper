import os

from PIL import Image
import numpy as np
import rasterio
from rasterio import CRS
from rasterio.transform import from_origin
import matplotlib.pyplot as plt
from rasterio.windows import Window
from rasterio.enums import Resampling
from rasterio.transform import Affine
import cv2
import threading

# bands = [
#    'AOT', 'B01', 'B02', 'B03', 'B04',
#    'B05', 'B06', 'B07', 'B8A', 'B11',
#    'B12', 'SCL', 'TCI', 'WVP'
# ]

# B02 B03 B04分别是蓝绿红
bands = [
    'B01', 'B02', 'B03', 'B04', 'B05',
    'B06', 'B07', 'B8A', 'B11', 'B12'
]

base_path = ('../loc3/sentinel2/S2A_MSIL2A_20230829T192911_N0509_R142_T10VFL_20230830T011205.SAFE/GRANULE'
             '/L2A_T10VFL_A042753_20230829T193052/IMG_DATA/R20m/')
mask_path = '../loc3output/2023-08-29/0829mask.tif'


def merge_bands(path: str = '', param1: str = '', param2: str = ''):    # 10波段版
    """
    param1和param2是文件夹前缀，自动处理
    path=root_path
    """
    band_arrays = []
    meta = None
    for i, band in enumerate(bands):
        file_path = f'{path}{param1}_{param2}_{band}_20m.jp2'
        with rasterio.open(file_path) as src:
            band_data = src.read(1)
            band_arrays.append(band_data)
            # 读取第一个影像的元数据
            if i == 0:
                meta = src.meta.copy()

    # 堆叠波段，形成形状 (num_bands, height, width)
    multi_spectral_image = np.stack(band_arrays)
    multi_spectral_image = np.expand_dims(multi_spectral_image, axis=0)  # 扩展维度以符合神经网络输入要求

    # 使用更高精度的浮点数类型进行归一化处理
    multi_spectral_image = multi_spectral_image.astype(np.float32) / 65535.0  # 假设数据为16位

    return multi_spectral_image, meta


def save_multi_image(multi_spectral_image: np.ndarray, save_dir: str, meta: dict = None):
    """
    保存所有波段影像为单一图像文件，带详细错误提示，并动态获取元数据
    """
    try:
        # 检查multi_spectral_image的格式
        if len(multi_spectral_image.shape) != 4:
            raise ValueError("multi_spectral_image 应为四维 (batch_size, num_bands, height, width)")

        # 处理图像数据
        multi_spectral_image = multi_spectral_image.squeeze(0)
        height, width = multi_spectral_image.shape[1], multi_spectral_image.shape[2]

        # 检查波段数量
        band_count = multi_spectral_image.shape[0]
        if band_count == 0:
            raise ValueError("multi_spectral_image 不包含任何波段")

        # 将数据归一化为 uint16 (范围: [0, 65535])
        img_uint16 = np.clip(multi_spectral_image * 65535, 0, 65535).astype(np.uint16)

        # 更新元数据
        meta.update({
            'driver': 'JP2OpenJPEG',
            'count': band_count,
            'dtype': 'uint16',
            'width': width,
            'height': height,
        })

        # 检查目录并创建
        os.makedirs(os.path.dirname(save_dir), exist_ok=True)

        # 保存图像文件
        with rasterio.open(save_dir, 'w', **meta) as dst:
            for i in range(band_count):
                try:
                    dst.write(img_uint16[i, :, :], i + 1)
                except Exception as e:
                    raise IOError(f"写入波段 {i + 1} 失败: {e}")

        print(f"图像成功保存到 {save_dir}")

    except rasterio.errors.RasterioIOError as rio_err:
        print(f"Rasterio IO 错误: {rio_err}")
    except ValueError as val_err:
        print(f"值错误: {val_err}")
    except IOError as io_err:
        print(f"I/O 错误: {io_err}")
    except Exception as e:
        print(f"发生未知错误: {e}")


def check_meta_data(band: str):
    """查看元数据
    band='TCI'
    """
    file_path = f'{base_path}T10VFL_20230829T192911_{band}_20m.jp2'
    with rasterio.open(file_path) as src:
        print(src.meta)
    print(src.shape)


def open_mask(mask_path: str):
    """
    mask_path='../loc3output/2023-08-29/0829mask.tif'
    """
    with rasterio.open(mask_path) as src:
        metadata = src.meta
        for key, value in metadata.items():
            print(f"{key}:{value}")

        print("CRS:", src.crs)
        print("Transform:", src.transform)
        print("Width:", src.width)
        print("Height:", src.height)
        print("Count (number of bands):", src.count)


def show_multi_img(path: str, ch1=None, ch2=None, ch3=None):
    """显示多波段图像的RGB合成图，支持归一化为 Uint16 格式
    img_path=f'{base_path}T10VFL_20230829T192911_TCI_20m.jp2'
    """
    with rasterio.open(path) as src:
        # 确保图像至少有3个波段
        if src.count < 3:
            raise ValueError(f"图像 {path} 至少需要3 个波段来显示RGB图像，但当前只有 {src.count} 个波段。")

        if (ch1 is not None) and (ch2 is not None) and (ch3 is not None):  # rgb序号为13 14 15
            red = src.read(ch1).astype(float)
            green = src.read(ch2).astype(float)
            blue = src.read(ch3).astype(float)
        else:
            red = src.read(1).astype(float)
            green = src.read(2).astype(float)
            blue = src.read(3).astype(float)

        # 堆叠为RGB图像
        rgb = np.stack((red, green, blue), axis=-1)

        # 归一化为Uint16
        min_val = rgb.min()
        max_val = rgb.max()
        range_val = max_val - min_val

        if range_val == 0:
            print(f"图像 {path} 中的所有像素值相同，无法进行归一化。显示全零图像。")
            # 使用全零图像，或者其他替代方案
            rgb_normalized = np.zeros_like(rgb, dtype=np.uint16)
        else:
            rgb_normalized = ((rgb - min_val) / range_val * 65535).astype(np.uint16)

        # 将归一化后的图像转换为0-255的范围，并转换为无符号8位整数，用于显示
        rgb_display = (rgb_normalized / 256).astype(np.uint8)  # 显示时使用 uint8 转换（0-255）

        # 显示图像
        plt.imshow(rgb_display)
        plt.title("RGB Image from Multiband Raster")
        plt.axis('off')  # 隐藏坐标轴
        plt.show()


# 示例调用

def crop_img_to_patches(image, patch_size=512, output_dir="patches"):
    """图像切割为512*512
    img_path=f'{base_path}T10VFL_20230829T192911_TCI_20m.jp2'
    """
    os.makedirs(output_dir, exist_ok=True)
    with rasterio.open(image) as src:
        img_width = src.width
        img_height = src.height
        num_bands = src.count
        dtype = src.dtypes[0]
        crs = src.crs
        transform = src.transform

        num_patches_x = (img_width + patch_size - 1) // patch_size
        num_patches_y = (img_height + patch_size - 1) // patch_size

        print(f"Image size:{img_width}x{img_height}，Bands:{num_bands}")
        print(f"Number of patches:{num_patches_y}rows x {num_patches_x} cols")

        for i in range(num_patches_y):
            for j in range(num_patches_x):
                row_start = i * patch_size
                col_start = j * patch_size
                window = Window(col_start, row_start,
                                min(patch_size, img_width - col_start),
                                min(patch_size, img_height - row_start))
                patch_data = src.read(window=window)
                patch_transfrom = src.window_transform(window)
                patch_meta = src.meta.copy()
                patch_meta.update({
                    "driver": "JP2OpenJPEG",
                    "height": window.height,
                    "width": window.width,
                    "transform": patch_transfrom
                })
                patch_filename = os.path.join(
                    output_dir,
                    f"patch_{i}_{j}.jp2"

                )
                with rasterio.open(patch_filename, 'w', **patch_meta) as dst:
                    dst.write(patch_data)

                print(f"Saved patch:{patch_filename} with shape {patch_data.shape}")
    print("保存完成")


image_path = f'{base_path}T10VFL_20230829T192911_TCI_20m.jp2'
image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)


if __name__ == '__main__':
    pass
    # band='TCI'
    # check_meta_data(band)
    # save_multi_image(merge_multi_band())
    # open_mask()
    # patch_img = "../utils/patches/patch_0_5.jp2"
    # file = f'../loc3_merge_img/S2A_MSIL2A_20230816T191911_N0509_R099_T10VFL_20230817T022001.SAFE.jp2'
    # show_multi_img(file,13,14,15)
    # crop_img_to_patches(img_path)
