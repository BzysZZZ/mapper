## 图像处理
### 1.合并波段
```python
path1="../loc1/sentinel2"
print("loc1:")
print(extract_dates(path1))
progress_file(path1,"../loc1_merge_img/")

```
### 2.分割标记 
```python
input_shp = "../loc8/DL_FIRE_J1V-C2_548064/fire_nrt_J1V-C2_548064.shp"
output_dir = "../loc8output"
separate_data_of_mask(input_shp, output_dir)
```
### 3.日期并集
查找火点和数据的并集日期
```python
base_path='../'
loc_count=8
find_common_dates(base_path,loc_count)
```
### 4.精细裁剪
默认裁剪大小为512*512,边缘重叠32px
```python 
input_dir="../loc1patch"
output_dir="../loc1patch/patch"
split_tif_with_overlap(input_dir,output_dir)
```

### 5.数据总数
参数x设定为2-x文件夹默认8,即loc2到loc8
```python
tif_count = count_tif_files_in_patch()
print(f"总和: {tif_count}")
```


***[11.10完成]***

---

合并为uint16均已实现，旧版本不再留存<br>
***[11.11完成]***<br>

---
loc1(39.274,-121.618)只有4.4一张，没有参考价值<br>
loc2(38.040,-119.922)可用[6.25,6.30,7.10]<br>
loc3可用比较多<br>
loc4未处理

## 文件结构和命名规范
```text
mapper  |--loc1
            |--sentinel2     # 各种源数据
            |--DL_FIRE_LS_539039    # 火点总数据
            |--loc1_roi_1.xml   # 该区域的roi，作为分割边缘
            |--loc1_roi_2.xml
            |...
        |--loc1_merge_img    # 合并后的10波段图像
        |--loc1output
            |--2023-04-04    # 切割后的shp文件位置
                |...
            |--2023-04-05
                |...
            |...
        |--loc1patch
            |--0404.tif     # 未切分的大patch
            |--0404.tif.enp
        ...
```

## 命名规范
```text
roi文件命名：{loc}_roi_{i}.xml<br>
大patch命名：{MMDD}_{i}.tif
```
1. cututils工具不支持写图片坐标已弃用（但是保留了其他完整功能）
2. 重新完成了对10波段的文件合并和检查
3. 完成了loc2和loc3的大tile分割

***[11.12完成]***

---
loc3_0816号图片没有下载标签

---


| 1.文件合成 | 2.火点下载 | 3.火点切分 | 4.火点裁剪 | 5.精细裁剪 | 数量   |
|--------|--------|--------|--------|--------|------|
| loc1   | ---    | ---    | ---    | ---    | 弃用   |
| loc2   | 完成     | 完成     | 完成     | 完成     | 48   |
| loc3   | 完成     | 完成     | 完成     | 完成     | 150  |
| loc4   | 完成     | 完成     | 完成     | 完成     | 125  |
| loc5   | 完成     | 完成     | 完成     | 完成     | 9    |
| loc6   | 完成     | 完成     | 完成     | 完成     | 151  |
| loc7   | 完成     | 完成     | 完成     | 完成     | 153  |
| loc8   | 完成     | 完成     | 完成     | 完成     | 443  |
| SUM    |        |        |        |        | 1079 |
***[11.23]***

## 标签处理
手动转换
