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
图像重新合并为16位
```python
# 全波段版本,归一化为8位 version=16-8

def merge_multi_band(path: str = base_path, param1: str = '', param2: str = ''):  # 全波段版
    """
    param1和param2是文件夹前缀，自动处理
    path=root_path
    """
    # 读取所有波段影像
    band_arrays = []
    for band in bands:
        if band == 'TCI':
            # file_n=f'{param1}_{param2}_TCI_20m.jp2'
            file_path = f'{path}{param1}_{param2}_{band}_20m.jp2'

            # file_path = f'{base_path}T10VFL_20230829T192911_{band}_20m.jp2'
            with rasterio.open(file_path) as src:
                tci_data = src.read()
                # 提取RGB通道
                band_arrays.append(tci_data[0])
                band_arrays.append(tci_data[1])
                band_arrays.append(tci_data[2])
        else:
            file_path = f'{base_path}T10VFL_20230829T192911_{band}_20m.jp2'
            file_path = f'{path}{param1}_{param2}_{band}_20m.jp2'
            with rasterio.open(file_path) as src:
                band_data = src.read(1)
                band_arrays.append(band_data)

    # 堆叠波段，形成形状(num_bands,height,width)
    multi_spectral_image = np.stack(band_arrays)
    # 扩展维度以符合神经网络输入要求
    multi_spectral_image = np.expand_dims(multi_spectral_image, axis=0)
    # 归一化处理
    multi_spectral_image = multi_spectral_image.astype(np.float32) / 255.0
    return multi_spectral_image
```
```python

# 对应的save
def save_multi_image(multi_spectral_image, save_dir: str):
    """保存所有波段影像为单一图像文件，带详细错误提示"""

    try:
        # 确保multi_spectral_image符合预期的三维格式
        if len(multi_spectral_image.shape) != 4:
            raise ValueError("multi_spectral_image 应为四维 (batch_size, num_bands, height, width)")

        # 处理图像数据
        multi_spectral_image = multi_spectral_image.squeeze(0)
        height, width = multi_spectral_image.shape[1], multi_spectral_image.shape[2]

        # 检查波段数量
        band_count = multi_spectral_image.shape[0]
        if band_count == 0:
            raise ValueError("multi_spectral_image 不包含任何波段")

        # 转换数据类型为uint8并检查转换
        try:
            img_uint8 = (multi_spectral_image * 255).astype(np.uint8)
        except Exception as e:
            raise ValueError(f"图像数据转换到 uint8 失败: {e}")

        # 定义元数据
        meta = {
            'driver': 'JP2OpenJPEG',
            'count': band_count,
            'dtype': 'uint8',
            'width': width,
            'height': height,
            'crs': CRS.from_epsg(32610),
            'transform': from_origin(600000.0, 6600000.0, 20.0, 20.0)
        }

        # 检查目录并创建
        os.makedirs(os.path.dirname(save_dir), exist_ok=True)

        # 保存图像文件
        with rasterio.open(save_dir, 'w', **meta) as dst:
            for i in range(band_count):
                try:
                    dst.write(img_uint8[i, :, :], i + 1)
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
```

```python
# 10波段版merge，归一化为8位 version=10-8
def merge_bands(path: str = base_path, param1: str = '', param2: str = ''): # 10波段版
    """
    param1和param2是文件夹前缀，自动处理
    path=root_path
    """
    # 读取所有波段影像
    band_arrays = []
    for band in bands:
        file_path = f'{path}{param1}_{param2}_{band}_20m.jp2'
        with rasterio.open(file_path) as src:
            band_data = src.read(1)
            band_arrays.append(band_data)

    # 堆叠波段，形成形状(num_bands,height,width)
    multi_spectral_image = np.stack(band_arrays)
    # 扩展维度以符合神经网络输入要求
    multi_spectral_image = np.expand_dims(multi_spectral_image, axis=0)
    # 归一化处理
    multi_spectral_image = multi_spectral_image.astype(np.float32) / 255.0
    return multi_spectral_image
```

```python
# 10波段通用版，归一化16位 version=10-16
def merge_bands(path: str = base_path, param1: str = '', param2: str = ''):
    """
    param1和param2是文件夹前缀，自动处理
    path=root_path
    """
    # 读取所有波段影像
    band_arrays = []
    for band in bands:
        file_path = f'{path}{param1}_{param2}_{band}_20m.jp2'
        with rasterio.open(file_path) as src:
            band_data = src.read(1)
            band_arrays.append(band_data)

    # 堆叠波段，形成形状(num_bands,height,width)
    multi_spectral_image = np.stack(band_arrays)
    # 扩展维度以符合神经网络输入要求
    multi_spectral_image = np.expand_dims(multi_spectral_image, axis=0)

    # 使用更高精度的浮点数类型进行归一化处理
    multi_spectral_image = multi_spectral_image.astype(np.float32)  # 保留更高精度
    multi_spectral_image = multi_spectral_image / 65535.0  # 将数据归一化到0-1范围，假设原始数据是16位

    return multi_spectral_image
```
