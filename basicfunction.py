"""
basicfunction.py
基础功能模块，提供医学图像处理的核心工具函数

该模块包含医学图像处理应用中最基础和关键的功能函数，
为整个系统提供数据加载、保存和预处理等核心服务。
主要功能包括：
- 医学图像文件的读取和保存（MHA格式）
- 图像数据归一化处理
- 多通道标签数据合成
"""

import os
import SimpleITK as sitk
import numpy as np


def load_mha(filename):
    """
    加载MHA格式的医学图像文件
    
    该函数使用SimpleITK库读取MHA格式的医学图像文件，提取图像数据、
    原点坐标和像素间距信息。这是医学图像处理流程的起点，为后续所有
    图像处理操作提供原始数据支持。
    
    Args:
        filename (str): MHA文件的完整路径
        
    Returns:
        tuple: 包含以下三个元素的元组：
            - numpy.ndarray: 图像数据数组
            - tuple: 图像原点坐标 (x, y, z)
            - tuple: 像素间距 (spacing_x, spacing_y, spacing_z)
            
    Raises:
        FileNotFoundError: 当指定的文件不存在时抛出异常
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"文件不存在: {filename}")
    print(f"正在加载文件: {filename}")  # 调试：打印当前路径
    itkimage = sitk.ReadImage(filename)
    return sitk.GetArrayFromImage(itkimage), itkimage.GetOrigin(), itkimage.GetSpacing()


def save_mha(image, filename, origin, spacing):
    """
    保存图像数据为MHA格式文件
    
    将处理后的图像数据保存为MHA格式文件，保留医学图像的元数据信息，
    包括图像原点坐标和像素间距。这是医学图像处理流程的重要输出环节，
    确保处理结果可以被其他医学软件正确读取和使用。
    
    Args:
        image (numpy.ndarray): 待保存的图像数据数组
        filename (str): 保存文件的完整路径
        origin (tuple): 图像原点坐标 (x, y, z)
        spacing (tuple): 像素间距 (spacing_x, spacing_y, spacing_z)
    """
    itkimage = sitk.GetImageFromArray(image)
    itkimage.SetSpacing(spacing)
    itkimage.SetOrigin(origin)
    sitk.WriteImage(itkimage, filename, True)


def NormalizeImageData(image):
    """
    对图像数据进行归一化处理
    
    将图像数据线性映射到[0, 1]区间，这是医学图像处理中的标准预处理步骤。
    归一化可以消除不同扫描设备和参数带来的数值差异，为后续处理提供统一的数据范围。
    特别处理了全黑图像（最大值等于最小值）的情况，避免除零错误。
    
    Args:
        image (numpy.ndarray): 输入的图像数据数组
        
    Returns:
        numpy.ndarray: 归一化后的图像数据，数值范围在[0, 1]之间
    """
    maxValue = np.max(image)
    minVale = np.min(image)
    if maxValue == minVale:
        return np.zeros_like(image)  # 全黑图像返回零矩阵
    return (image - minVale) / (maxValue - minVale)


def ComposeBinaryLabelData(inputMultiChanelLabel):
    """
    合成二值化标签数据
    
    将多通道的标签数据转换为二值化的单一标签图像。该函数处理两种输入格式：
    1) 四维数组，最后一维为单一通道
    2) 三维数组，直接作为输出
    
    处理后的标签数据只有0和1两个值，1表示目标区域（如血管），0表示背景区域，
    为后续的分割评估和可视化提供标准格式的标签数据。
    
    Args:
        inputMultiChanelLabel (numpy.ndarray): 输入的多通道标签数据
        
    Returns:
        numpy.ndarray: 二值化的标签数据，只包含0和1两个值
    """
    outputMutliLabel = np.zeros(
        (inputMultiChanelLabel.shape[0], inputMultiChanelLabel.shape[1], inputMultiChanelLabel.shape[2]))

    if inputMultiChanelLabel.ndim > 3 and inputMultiChanelLabel.shape[-1] == 1:
        outputMutliLabel = np.squeeze(inputMultiChanelLabel, axis=-1)
    else:
        outputMutliLabel = inputMultiChanelLabel
        
    outputMutliLabel[outputMutliLabel > 0.5] = 1

    outputMutliLabel[outputMutliLabel <= 0.5] = 0

    return outputMutliLabel