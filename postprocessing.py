"""
医学图像后处理模块
提供针对脑血管分割结果的形态学后处理功能，包括小连通区域去除和结果可视化叠加

主要功能:
- 移除分割结果中的小噪声区域，提高结果质量
- 将后处理结果与原始图像叠加，用于三维可视化显示
- 处理投票融合后的分割结果，生成最终输出

该模块利用连通组件分析技术，有效去除误分割的小区域，保留具有临床意义的血管结构
"""

import numpy as np
import SimpleITK as sitk
from basicfunction import load_mha, save_mha
import os

def postprocessing(filename, output_filename=None, min_voxel_num=100):
    """
    连通区域过滤后处理函数
    
    通过连通组件分析识别并移除体素数小于阈值的区域，有效去除分割噪声和误检的小区域
    主要应用于脑血管分割结果的优化，保留具有足够大小的血管结构
    
    技术原理:
    1. 使用SimpleITK进行连通组件标记
    2. 统计每个连通区域的体素数量
    3. 移除体素数小于阈值的区域
    
    Args:
        filename (str): 输入的MHA格式分割结果文件路径
        output_filename (str, optional): 输出文件路径，默认为None
        min_voxel_num (int): 最小连通区域体素数阈值，默认100
        
    Returns:
        str: 成功时返回保存路径，失败时返回None
    """
    try:
        # 加载分割结果数据
        data, origin, spacing = load_mha(filename)
        print(f"加载数据形状: {data.shape}")
        
        # 转换为SimpleITK图像格式以支持连通组件分析
        itkimage = sitk.GetImageFromArray(data, isVector=False)
        
        # 执行连通组件分析，标记所有独立的连通区域
        connect_map = sitk.ConnectedComponent(itkimage, True)
        connect_map = sitk.GetArrayFromImage(connect_map)
        
        # 获取连通区域总数（不包括背景）
        number = np.max(connect_map)
        print(f"发现 {number} 个连通区域")
        
        # 遍历所有连通区域，移除体素数小于阈值的区域
        removed_count = 0
        for i in range(1, number + 1):  # 从1开始，假设0是背景
            voxel_num = np.sum(connect_map == i)
            # 如果当前区域体素数小于阈值，则将其从结果中移除
            if voxel_num < min_voxel_num:
                data[connect_map == i] = 0
                removed_count += 1
                print(f"移除区域 {i}，体素数: {voxel_num}")
        
        print(f"共移除 {removed_count} 个小区域")
        
        
        save_path = f'mha/Postprocessed_result.mha'
            
        # 确保输出目录存在，避免保存时出错
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # 保存后处理结果
        save_mha(data, save_path, origin, spacing)
        print(f"后处理完成，结果保存至 {save_path}")
        
        return save_path
        
    except Exception as e:
        print(f"后处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def overlay_postprocessing_on_original(original_data, postprocessed_data):
    """
    将后处理结果叠加到原始图像数据上，生成用于三维可视化的四通道图像
    
    该函数为与votingFusion模块保持一致性，生成包含原始数据和分割标记的多通道图像
    用于在三个正交视图(XY、XZ、YZ)中同时显示原始图像和血管分割结果
    
    数据通道说明:
    - 通道0: 原始图像数据，用于窗宽窗位调整显示
    - 通道1: 血管分割标记，标识血管位置
    - 通道2: 占位符，保留用于扩展功能
    - 通道3: 颜色标记，0表示红色标记血管
    
    Args:
        original_data (numpy.ndarray): 原始MRA图像数据，形状为(Z, Y, X)
        postprocessed_data (numpy.ndarray): 后处理后的分割结果数据，形状为(Z, Y, X)
        
    Returns:
        tuple: (overlay_xy, overlay_xz, overlay_yz) 三个方向的四通道叠加数据数组
              每个数组形状为(?, ?, ?, 4)，分别对应不同视角的可视化数据
    """
    try:
        print(f"原始数据形状: {original_data.shape}")
        print(f"后处理数据形状: {postprocessed_data.shape}")
        print(f"后处理数据值范围: {postprocessed_data.min()} - {postprocessed_data.max()}")
        print(f"后处理数据唯一值: {np.unique(postprocessed_data)}")
        
        # 确保原始数据和后处理数据的空间维度一致
        if original_data.shape != postprocessed_data.shape:
            raise ValueError(f"原始数据和后处理数据形状不匹配: {original_data.shape} vs {postprocessed_data.shape}")
        
        # 将后处理数据二值化，确保血管标记仅为0(背景)和1(血管)
        post_binary = (postprocessed_data > 0).astype(np.uint8)
        print(f"二值化后处理数据值范围: {post_binary.min()} - {post_binary.max()}")
        
        # XY平面（轴向视图）- 沿着Z轴切片，对应image_xy显示
        # 构造四通道图像：[原始数据, 血管标记, 占位符, 颜色标记]
        overlay_data_xy = np.stack([
            original_data,                    # 原始数据用于窗宽窗位调整
            post_binary,                      # XY平面血管标记
            np.zeros_like(original_data),     # 占位符，保留用于扩展功能
            np.zeros_like(original_data)      # 颜色标记（0表示红色）
        ], axis=-1)
        
        # XZ平面（冠状视图）- 沿着Y轴切片，对应image_xz显示
        # 需要重新排列轴顺序以匹配视图方向，并进行翻转以保证正确显示
        overlay_data_xz = np.stack([
            np.transpose(original_data, (2, 0, 1)),     # XZ平面原始数据
            np.transpose(post_binary, (2, 0, 1)),       # XZ平面血管标记
            np.zeros_like(np.transpose(original_data, (2, 0, 1))),  # 占位符
            np.zeros_like(np.transpose(original_data, (2, 0, 1)))   # 颜色标记（0表示红色）
        ], axis=-1)
        overlay_data_xz = np.flip(overlay_data_xz, axis=(0, 1))  # 翻转以匹配坐标系
        
        # YZ平面（矢状视图）- 沿着X轴切片，对应image_yz显示
        # 需要重新排列轴顺序并对特定轴进行翻转以保证正确显示
        overlay_data_yz = np.stack([
            np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0)),  # YZ平面原始数据
            np.flip(np.transpose(post_binary, (1, 0, 2)), axis=(1, 0)),    # YZ平面血管标记
            np.zeros_like(np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0))),  # 占位符
            np.zeros_like(np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0)))   # 颜色标记（0表示红色）
        ], axis=-1)
        
        return overlay_data_xy, overlay_data_xz, overlay_data_yz
                
    except Exception as e:
        print(f"叠加后处理结果到原始图像时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None

def postprocessing_voting_result(subject_id=1):
    """
    对投票融合分割结果进行标准化后处理
    
    专门用于处理由多个模型投票融合产生的分割结果，执行噪声去除和结果优化
    该函数封装了标准的后处理流程，简化外部调用
    
    工作流程:
    1. 读取投票融合结果文件
    2. 应用连通区域过滤
    3. 保存标准化后处理结果
    
    Args:
        subject_id (int): 受试者编号 (1-25)，用于标识不同的数据集
        
    Returns:
        str: 成功时返回后处理结果保存路径，失败时返回None
    """
    try:
        # 定义输入文件路径（投票融合结果）
        input_path = f'mha/votingFusion_result.mha'
        
        # 定义输出文件路径（后处理结果）
        output_path = f'mha/postprocessed.mha'
        
        # 执行标准化后处理流程
        result_path = postprocessing(input_path, output_path)
        
        return result_path
        
    except Exception as e:
        print(f"投票结果后处理错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None