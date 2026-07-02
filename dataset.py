# 完整替换dataset.py的MRADataset类
import torch
from torch.utils.data import Dataset #用于构建可迭代的数据集。
import numpy as np 
from basicfunction import load_mha, NormalizeImageData
import os

"""
这是一个用于医学图像处理的自定义 PyTorch 数据集类，专门用于处理 MRA（磁共振血管造影）数据。

"""
class MRADataset(Dataset):
    def __init__(self, data_paths, label_paths, axis=0):
        self.data_paths = data_paths #医学图像数据文件路径列表
        self.label_paths = label_paths #对应的标签文件路径列表
        self.axis = axis #切片方向轴（0、1、2 分别代表不同的切片方向）
        self.volumes = [] # 存储所有加载的医学图像数据
        self.labels = [] # 存储所有对应的标签数据
        self.valid_slices = [] # 存储有效切片的索引信息
        
        print(f"开始预加载{len(data_paths)}个数据文件...")
        
        total_valid_slices = 0
        # 单次循环完成加载和进度提示
        for i, (data_path, label_path) in enumerate(zip(data_paths, label_paths)):
            print(f"正在加载文件 {i+1}/{len(data_paths)}: {os.path.basename(data_path)}")
            data_vol, origin, spacing = load_mha(data_path)
            label_vol, _, _ = load_mha(label_path)
            """
            使用 load_mha 函数加载医学图像数据（.mha格式）
            同时加载图像和对应的标签数据
            """
            
            # 检查每个切片，过滤掉全相同切片
            volume_valid_slices = []
            for slice_idx in range(data_vol.shape[axis]):
                # 提取切片
                if self.axis == 0:
                    data_slice = data_vol[slice_idx]
                elif self.axis == 1:
                    data_slice = data_vol[:, slice_idx, :]
                elif self.axis == 2:
                    data_slice = data_vol[:, :, slice_idx]
                
                # 检查是否为全相同切片
                if not np.all(data_slice == data_slice[0]):
                    volume_valid_slices.append(slice_idx)
                else:
                    print(f"跳过全相同切片 - Volume {i}, Slice {slice_idx}")
            
            if len(volume_valid_slices) > 0:
                self.volumes.append(data_vol)
                self.labels.append(label_vol)
                self.valid_slices.append((i, volume_valid_slices, total_valid_slices))
                total_valid_slices += len(volume_valid_slices)
            else:
                print(f"警告：Volume {i} 没有有效切片，已跳过")
        
        """
        预加载所有数据：一次性将所有文件加载到内存中，提高训练时的数据读取速度
        进度提示：显示加载进度，便于监控加载过程
        累积索引：通过 np.cumsum 构建累积切片索引，便于后续快速定位
        """
        
        # 计算内存占用
        total_bytes = 0
        for arr in self.volumes + self.labels:
            total_bytes += arr.nbytes
        print(f"预加载完成，占用内存：{total_bytes / 1024 / 1024:.2f} MB")
        print(f"有效切片总数：{total_valid_slices}")

    def __len__(self):
        if not self.valid_slices:
            return 0
        last_entry = self.valid_slices[-1]
        return last_entry[2] + len(last_entry[1])

    def __getitem__(self, idx):
        # 查找该索引属于哪个volume和slice
        volume_info = None
        for i, (vol_idx, slices, start_idx) in enumerate(self.valid_slices):
            if idx >= start_idx and idx < start_idx + len(slices):
                local_slice_idx = idx - start_idx
                volume_info = (vol_idx, slices[local_slice_idx])
                break
        
        if volume_info is None:
            raise IndexError("索引超出范围")
        
        volume_idx, slice_idx = volume_info
        
        # 使用预加载的数据
        data_vol = self.volumes[volume_idx]
        label_vol = self.labels[volume_idx]
        
        # 根据指定的切片轴提取对应的二维切片。
        if self.axis == 0:
            data_slice = data_vol[slice_idx]
            label_slice = label_vol[slice_idx]
        elif self.axis == 1:
            data_slice = data_vol[:, slice_idx, :]
            label_slice = label_vol[:, slice_idx, :]
        elif self.axis == 2:
            data_slice = data_vol[:, :, slice_idx]
            label_slice = label_vol[:, :, slice_idx]
        
        # 归一化处理
        data_slice = NormalizeImageData(data_slice) #使用外部函数对图像数据进行标准化处理
        label_slice = np.where(label_slice > 0.5, 1, 0)  # 严格二值化

        if data_slice.dtype == np.uint16:
            data_slice = data_slice.astype(np.float32)
        if label_slice.dtype == np.uint16:
            label_slice = label_slice.astype(np.float32)
        return torch.FloatTensor(data_slice).unsqueeze(0), torch.FloatTensor(label_slice).unsqueeze(0)
        """
        该组件实现了完整的数据预处理流水线，包括：
        医学图像文件加载
        多方向切片提取
        数据质量检查
        图像标准化
        标签二值化
        格式转换为深度学习框架所需格式
        这些预处理步骤确保了输入数据的质量和一致性，为后续的深度学习训练做好了准备。
        """