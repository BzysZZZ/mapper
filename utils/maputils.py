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


def show_multi_img(path: str):
    """显示多波段图像，自动判断单波段、三波段或多波段图像并显示。

    - 单波段：显示灰度图。
    - 三波段：默认 RGB 显示。
    - 其他波段数：要求用户输入显示的波段序号。
    """
    with rasterio.open(path) as src:
        band_count = src.count

        if band_count == 1:
            # 单波段：显示灰度图
            band = src.read(1).astype(float)
            plt.imshow(band, cmap='gray')
            plt.title("Single Band Grayscale Image")
            plt.axis('off')
            plt.show()

        elif band_count == 3:
            # 三波段：默认 RGB 显示
            red = src.read(1).astype(float)
            green = src.read(2).astype(float)
            blue = src.read(3).astype(float)
            rgb = np.stack((red, green, blue), axis=-1)
            min_val = rgb.min()
            max_val = rgb.max()
            range_val = max_val - min_val

            if range_val == 0:
                print("图像中所有像素值相同，显示全零图像。")
                rgb_normalized = np.zeros_like(rgb, dtype=np.uint16)
            else:
                rgb_normalized = ((rgb - min_val) / range_val * 65535).astype(np.uint16)

            # 转换为 0-255 范围的 uint8 类型以供显示
            rgb_display = (rgb_normalized / 256).astype(np.uint8)

            plt.imshow(rgb_display)
            plt.title("RGB Image from Multiband Raster")
            plt.axis('off')
            plt.show()

        else:
            # 多波段：要求用户输入波段序号
            while True:
                user_input = input(
                    f"图像有 {band_count} 个波段，请输入1个或3个波段序号（1 开始）进行显示：").strip().split()
                band_indices = [int(i) for i in user_input if i.isdigit()]

                if len(band_indices) == 1:
                    # 显示单波段灰度图
                    band = src.read(band_indices[0]).astype(float)
                    plt.imshow(band, cmap='gray')
                    plt.title(f"Band {band_indices[0]} Grayscale Image")
                    plt.axis('off')
                    plt.show()
                    break

                elif len(band_indices) == 3:
                    # 显示三波段 RGB 图像
                    red = src.read(band_indices[0]).astype(float)
                    green = src.read(band_indices[1]).astype(float)
                    blue = src.read(band_indices[2]).astype(float)
                    rgb = np.stack((red, green, blue), axis=-1)
                    min_val = rgb.min()
                    max_val = rgb.max()
                    range_val = max_val - min_val

                    if range_val == 0:
                        print("图像中所有像素值相同，显示全零图像。")
                        rgb_normalized = np.zeros_like(rgb, dtype=np.uint16)
                    else:
                        rgb_normalized = ((rgb - min_val) / range_val * 65535).astype(np.uint16)

                    # 转换为 0-255 范围的 uint8 类型以供显示
                    rgb_display = (rgb_normalized / 256).astype(np.uint8)

                    plt.imshow(rgb_display)
                    plt.title("RGB Image from Multiband Raster")
                    plt.axis('off')
                    plt.show()
                    break

                else:
                    print("输入不合法，请重新输入 1 个或 3 个有效的波段序号。")

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
                patch_transform = src.window_transform(window)
                patch_meta = src.meta.copy()
                patch_meta.update({
                    "driver": "JP2OpenJPEG",
                    "height": window.height,
                    "width": window.width,
                    "transform": patch_transform
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
    file = f'../loc1_merge_img/S2B_MSIL2A_20230424T184919_N0509_R113_T10SFJ_20230424T215033.SAFE.jp2'
    show_multi_img(file)
    # crop_img_to_patches(img_path)
