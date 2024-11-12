## 图像处理
### 1.合并    (loc1 loc2 loc3 loc4 已完成)
```python
    path1="../loc1/sentinel2"
    print("loc1:")
    print(extract_dates(path1))
    progress_file(path1,"../loc1_merge_img/")

```
### 2.分割标记 (均完成)
```python
    input_shp = "../loc1/DL_FIRE_LS_539039/fire_nrt_LS_539039.shp"
    output_dir = "../../loc1output"
    separate_data_of_mask(output_dir, input_shp)
```
### 3.日期并集
```python
    base_path='../'
    loc_count=4
    find_common_dates(base_path,loc_count)
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
3. 完成了loc2和loc3的大patch分割

***[11.12完成]***

---
loc3_0816号图片没有下载标签