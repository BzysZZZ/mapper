## 图像处理
### 1.合并    (loc1 loc2 loc3 loc4 已完成)
```python
    path1="../loc1/sentinel2"
    print("loc1:")
    print(extract_dates(path1))
    progress_file(path1,"../loc1_merge_img/")

    path2="../loc2/sentinel2"
    print("loc2:")
    print(extract_dates(path2))
    progress_file(path2,"../loc2_merge_img/")

    path3="../loc3/sentinel2" 
    print("loc3:")
    print(extract_dates(path3))
    progress_file(path3,"../loc3_merge_img/")

    path4="../loc4/sentinel2"
    print("loc4:")
    print(extract_dates(path4))
    progress_file(path4,"../loc4_merge_img/")
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
cututils工具待优化<br>
修改了show_multi_img()方法
