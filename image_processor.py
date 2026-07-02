"""
image_processor.py
医学图像处理核心模块 - 负责医学图像数据的加载、预处理和管理

功能概述:
1. 医学图像加载:
   - 支持多种医学图像格式（MHA、NIfTI等）
   - 使用SimpleITK库进行高效图像读取
2. 图像预处理:
   - 三维医学图像分解为三个正交视图
   - 坐标轴转换和图像翻转以匹配显示坐标系
3. 数据管理:
   - 管理横截面、矢状面、冠状面三个视图的图像数据
   - 统计各视图的切片数量信息
4. 文件验证:
   - 验证医学图像文件的有效性和完整性
   - 提供用户友好的错误提示机制

竞赛亮点:
- 高效的医学图像加载和预处理算法
- 多视图图像数据管理机制
- 完善的异常处理和用户交互设计
"""

import numpy as np
from SimpleITK import ImageFileReader, GetArrayFromImage
from PyQt5.QtWidgets import QMessageBox
import os

class ImageProcessor:
    """
    医学图像处理器 - 封装医学图像处理的核心业务逻辑
    
    该类负责医学图像的加载、预处理和管理，是整个医学图像显示系统
    的数据处理核心。支持多种医学图像格式，能够将3D医学图像数据分解
    为三个正交视图（横截面、矢状面、冠状面）以供显示和分析。
    """
    
    def __init__(self):
        """
        初始化医学图像处理器
        创建图像处理器实例，初始化图像数据和切片计数器
        """
        # 存储三个正交视图的图像数据
        self.image_xy = None  # 横截面视图数据 (Axial view)
        self.image_xz = None  # 矢状面视图数据 (Sagittal view)
        self.image_yz = None  # 冠状面视图数据 (Coronal view)
        
        # 各视图的切片数量统计
        self.num_slices_xz = 0  # 矢状面视图切片数
        self.num_slices_yz = 0  # 冠状面视图切片数
        self.num_slices_xy = 0  # 横截面视图切片数
    
    def load_medical_image(self, file_name):
        """
        加载并预处理医学图像文件 - 核心数据处理方法
        
        该方法使用SimpleITK库加载医学图像文件，然后将3D图像数据
        分解为三个正交视图，每个视图对应不同的解剖切面方向，便于
        医生从不同角度观察病灶和解剖结构。
        
        处理流程:
        1. 使用SimpleITK读取医学图像文件
        2. 将图像数据转换为NumPy数组格式
        3. 对图像数据进行坐标轴转换和翻转操作，以匹配显示坐标系
        4. 计算并存储各视图的切片数量
        
        Args:
            file_name (str): 医学图像文件的完整路径
            
        Returns:
            tuple: (image_array, image_xy, image_xz, image_yz)
                   image_array: 原始3D图像数组
                   image_xy: 横截面视图数据 (Axial view)
                   image_xz: 矢状面视图数据 (Sagittal view)
                   image_yz: 冠状面视图数据 (Coronal view)
        """
        # 使用SimpleITK创建图像文件读取器
        reader = ImageFileReader()
        reader.SetFileName(file_name)
        image = reader.Execute()
        image_array = GetArrayFromImage(image)
        
        # 将3D图像数据分解为三个正交视图
        # 矢状面视图 (Sagittal view) - 沿X轴切片
        self.image_xz = np.transpose(image_array, (2, 0, 1))
        self.image_xz = np.flip(self.image_xz, axis=(0, 1))
        
        # 冠状面视图 (Coronal view) - 沿Y轴切片
        self.image_yz = np.flip(np.transpose(image_array, (1, 0, 2)), axis=(1, 0))
        
        # 横截面视图 (Axial view) - 沿Z轴切片
        self.image_xy = np.transpose(image_array, (0, 1, 2))
        
        # 计算各视图的切片数量
        self.num_slices_xz = self.image_xz.shape[0]
        self.num_slices_yz = self.image_yz.shape[0]
        self.num_slices_xy = self.image_xy.shape[0]
        
        return image_array, self.image_xy, self.image_xz, self.image_yz
    
    def get_slice_counts(self):
        """
        获取各视图的切片数量 - 用于界面布局和导航控制
        
        该方法返回三个正交视图的切片数量，用于初始化滑块控件的
        范围和设置切片导航的最大值，确保用户可以在有效范围内
        浏览所有图像切片。
        
        Returns:
            tuple: (num_slices_xz, num_slices_yz, num_slices_xy)
                   num_slices_xz: 矢状面视图切片数
                   num_slices_yz: 冠状面视图切片数
                   num_slices_xy: 横截面视图切片数
        """
        return self.num_slices_xz, self.num_slices_yz, self.num_slices_xy
    
    def get_image_data(self):
        """
        获取处理后的图像数据 - 为显示模块提供数据支持
        
        该方法返回已处理的三个正交视图图像数据，供图像显示模块
        使用。这些数据已经过坐标转换和翻转处理，可以直接用于
        显示而无需额外处理。
        
        Returns:
            tuple: (image_xy, image_xz, image_yz) 处理后的图像数据
                   image_xy: 横截面视图数据
                   image_xz: 矢状面视图数据
                   image_yz: 冠状面视图数据
        """
        return self.image_xy, self.image_xz, self.image_yz
    
    def validate_file(self, file_name, parent):
        """
        验证医学图像文件有效性 - 确保数据质量和用户体验
        
        该方法检查指定的医学图像文件是否存在且有效，防止程序
        因无效文件而崩溃。如果文件无效，会向用户显示友好的
        错误提示信息，引导用户选择有效的医学图像文件。
        
        Args:
            file_name (str): 待验证的文件路径
            parent (QWidget): 父级窗口对象，用于显示消息框
            
        Returns:
            bool: 文件验证结果
                  True: 文件有效
                  False: 文件无效
        """
        # 检查文件路径是否为空或文件是否存在
        if file_name is None or not os.path.exists(file_name):
            QMessageBox.warning(parent, "文件错误", "请先选择有效的医学图像文件！")
            return False
        return True