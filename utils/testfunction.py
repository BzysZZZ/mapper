# 各种测试函数
import os
import re

import rasterio

from utils.fileutils import return_suffix, root_suffix1, root_path, root_suffix2
from utils.maputils import merge_bands, save_multi_image

import matplotlib.pyplot as plt
import numpy as np
def _test_show_band_grayscale(multi_spectral_image: np.ndarray, band_index: int):
    """
    展示合并后的多波段图像中的单个波段的灰度影像。
    :param multi_spectral_image: 合并后的多波段图像，形状为(1, num_bands, height, width)。
    :param band_index: 需要展示的波段索引。
    """
    # 检查波段索引是否在范围内
    if band_index < 0 or band_index >= multi_spectral_image.shape[1]:
        raise ValueError("波段索引超出范围")

    # 提取指定波段的图像数据
    band = multi_spectral_image[0, band_index]  # 选择第一个维度中的 band_index 波段

    # 显示灰度影像
    plt.imshow(band, cmap='gray')
    plt.colorbar()
    plt.title(f'Band {band_index + 1} Grayscale Image')
    plt.show()


def _test_progress_file(path: str = root_path, save_path: str = "../loc3_merge_img/"):
    """
    根据文件夹的文件名拼接出完整路径并合并所有波段
    :param path: root_path
    :param save_path: "../loc3_merge_img/"

    """
    file_list = []  # 要处理的文件夹列表
    dir_pattern2 = re.compile(r'.*MSIL2A_(\d{8}.*)')  # 匹配文件夹名
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            match2 = dir_pattern2.search(dir_name)
            if match2:
                file_list.append(match2.group())  # 按日期匹配文件夹

    """对文件夹列表的数据分别拼接路径并合并输出"""
    for dir_n in file_list:
        match1 = re.search(r'(\d{8}T\d{6}).*?(T10VFL|T10SGH|T10SFJ)', dir_n)  # 获得param1和param2参数
        param1 = match1.group(1)  # 日期
        param2 = match1.group(2)  # T10VFL
        full_name = os.path.join(path, dir_n, root_suffix1)  # 合并前缀
        suffix = return_suffix(full_name)  # 前缀2
        # print(full_name,",",suffix,",",root_suffix2)

        full_name = os.path.join(full_name, suffix, root_suffix2)  # 合并前缀2，前缀3
        full_name = full_name.replace("\\", '/')  # 符号统一
        # 拼接好的路径用来进行合成
        # merge_img = merge_bands(full_name, param2, param1)
        merge_img,meta = merge_bands(full_name, param2, param1)
        # 保存图像
        save_file = f'{save_path}{dir_n}.jp2'
        save_multi_image(merge_img,save_file,meta)

        print(f"{dir_n}处理完成")


if __name__ == '__main__':
    img="../loc1/sentinel2/S2A_MSIL2A_20230409T184921_N0509_R113_T10SFJ_20230409T233253.SAFE/GRANULE/L2A_T10SFJ_A040722_20230409T190314/IMG_DATA/R20m/T10SFJ_20230409T184921_AOT_20m.jp2"
    img1="../loc1_merge_img/S2A_MSIL2A_20230409T184921_N0509_R113_T10SFJ_20230409T233253.SAFE.jp2"
    with rasterio.open(img)as src:
        print(src.transform)
        print(src.crs)
    with rasterio.open(img1)as src:
        print(src.transform)
        print(src.crs)
