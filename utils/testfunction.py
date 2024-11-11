#各种测试函数
import os
import re

from utils.fileutils import return_suffix, root_suffix1, root_path,root_suffix2
from utils.maputils import merge_bands, show_band_grayscale


def progress_file_test(path: str = root_path, save_path: str = "../loc3_merge_img/"):
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
        #print(full_name,",",suffix,",",root_suffix2)


        full_name = os.path.join(full_name, suffix, root_suffix2)  # 合并前缀2，前缀3
        full_name = full_name.replace("\\", '/')  # 符号统一
        # 拼接好的路径用来进行合成
        #merge_img = merge_bands(full_name, param2, param1)
        merge_img= merge_bands(full_name,param2,param1)
        # 保存图像
        # save_file = f'{save_path}{dir_n}.jp2'
        # save_multi_image(merge_img, save_file)
        show_band_grayscale(merge_img,0)
        break

        print(f"{dir_n}处理完成")

if __name__ == '__main__':
    path=f"../loc1/sentinel2"
    save_path=f"../loc6_merge_img"
    progress_file_test(path,save_path)