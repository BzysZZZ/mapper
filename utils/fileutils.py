import os
import re
from maputils import bands, merge_multi_band
# from maputils import merge_multi_band
from maputils import merge_bands
from maputils import save_multi_image
import geopandas as gpd

root_path = f"../loc3/sentinel2"
output_img_dir = f"../loc3_merge_img/img"
output_mask_dir = f"../loc3_merge_img/mask"

root_suffix1 = f"GRANULE/"
root_suffix2 = f"IMG_DATA/R20m/"
input_shp = 'loc2/DL_FIRE_SV-C2_517560/fire_archive_SV-C2_517560.shp'


def extract_dates(path: str):
    """提取所有日期
    path=root_path
    """
    date_list = []
    date_pattern = re.compile(r'MSIL2A_(\d{8})')
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            match = date_pattern.search(dir_name)
            if match:
                date_list.append(match.group(1))
    return date_list


def progress_file(path: str = root_path, save_path: str = "../loc3_merge_img/"):
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
        merge_img= merge_multi_band(full_name,param2,param1)
        # 保存图像
        save_file = f'{save_path}{dir_n}.jp2'
        save_multi_image(merge_img, save_file)

        print(f"{dir_n}处理完成")


def return_suffix(root_path: str):
    """拼接后缀
    root_path=root_path
    """
    for root, dirs, files in os.walk(root_path):
        for dir_name in dirs:
            if dir_name.startswith('L2A'):
                return dir_name
    print("error")
    return 1


import os
import geopandas as gpd


def separate_data_of_mask(input_shp: str,output_dir: str):
    """按照日期切分标签"""
    print(f"开始读取输入 Shapefile: {input_shp}")

    # 读取输入 Shapefile
    try:
        gdf = gpd.read_file(input_shp)
        print(f"成功读取 Shapefile, 总记录数: {len(gdf)}")
    except Exception as e:
        print(f"读取 Shapefile 失败: {e}")
        return

    # 获取日期字段并检查日期字段是否存在
    date_column = 'ACQ_DATE'  # 根据实际字段名进行修改
    if date_column not in gdf.columns:
        print(f"错误: 找不到日期字段 '{date_column}'")
        return

    # 获取唯一日期
    unique_dates = gdf[date_column].unique()
    print(f"找到 {len(unique_dates)} 个唯一日期: {unique_dates}")

    # 为每个日期保存一个新的 Shapefile
    for date in unique_dates:
        # 格式化日期并创建对应的文件夹
        date_str = str(date)
        save_dir = os.path.join(output_dir, date_str)
        os.makedirs(save_dir, exist_ok=True)

        print(f"正在处理日期: {date_str}")

        # 筛选出对应日期的数据
        subset = gdf[gdf[date_column] == date].copy()  # 创建副本
        print(f"日期 {date_str} 包含 {len(subset)} 条记录")

        # 保存为新的 Shapefile
        output_shp = os.path.join(save_dir, f'{date_str}.shp')
        try:
            subset.to_file(output_shp, driver='ESRI Shapefile')
            print(f"成功保存 Shapefile: {output_shp}")
        except Exception as e:
            print(f"保存 Shapefile 失败: {e}")

    print("切分完成")


import os
import re

import os
import re
from datetime import datetime


def extract_data_dates(path: str):
    """提取每个 loc 中的数据日期，并格式化为 YYYY-MM-DD"""
    date_list = []
    date_pattern = re.compile(r'MSIL2A_(\d{8})')
    for root, dirs, files in os.walk(path):
        for dir_name in dirs:
            match = date_pattern.search(dir_name)
            if match:
                # 格式化为 YYYY-MM-DD
                date_str = datetime.strptime(match.group(1), "%Y%m%d").strftime("%Y-%m-%d")
                date_list.append(date_str)
    return sorted(date_list)


def extract_label_dates(path: str):
    """提取每个 loc 的标签日期"""
    date_list = []
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)):
            date_list.append(item)
    return sorted(date_list)


def find_common_dates(base_path: str, loc_count: int):
    """查找每个 loc 的数据日期和标签日期的交集，并保存到文件"""
    result = {}

    # 遍历每个 loc 目录
    for i in range(1, loc_count + 1):
        loc_data_path = os.path.join(base_path, f'loc{i}')
        loc_label_path = os.path.join(base_path, f'loc{i}output')

        # 提取数据日期
        data_dates = extract_data_dates(loc_data_path)
        # 提取标签日期
        label_dates = extract_label_dates(loc_label_path)

        # 计算交集
        common_dates = sorted(set(data_dates).intersection(label_dates))
        result[f'loc{i}'] = common_dates

        # 打印每个 loc 的日期信息
        print(f'loc{i} 数据日期: {data_dates}')
        print(f'loc{i} 标签日期: {label_dates}')
        print(f'loc{i} 交集日期: {common_dates}\n')

    # 将结果保存到文件中
    with open('../ava_date.txt', 'w') as file:
        for loc, dates in result.items():
            file.write(f"{loc}: {dates}\n")

    print("所有 loc 的日期交集已保存到 ../ava_date.txt")



if __name__ == '__main__':
    path1 = "../loc1/sentinel2"
    print("loc1:")
    print(extract_dates(path1))
    progress_file(path1, "../loc6_merge_img/")

