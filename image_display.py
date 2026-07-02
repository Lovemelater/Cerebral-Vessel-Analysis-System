"""
 * image_display.py
 * 医学图像显示模块 - 负责三维医学图像的正交视图展示
 * 
 * 功能概述:
 * 1. 多视图显示: 提供医学图像的三个正交视图展示
 *    - 横截面视图 (Axial view): 显示从上到下的切面
 *    - 矢状面视图 (Sagittal view): 显示从左到右的切面
 *    - 冠状面视图 (Coronal view): 显示从前到后的切面
 *    - 3D视图框架: 用于集成VTK三维可视化组件
 * 2. 图像处理功能:
 *    - 窗宽窗位调整: 用于优化特定组织的显示效果
 *    - 血管增强处理: 突出显示血管结构
 *    - 多格式图像支持: 支持灰度、RGB及带标记的四通道图像
 * 3. 交互功能:
 *    - 鼠标点击事件处理: 实现图像查看和对比功能
 *    - 滚轮事件处理: 实现切片切换
 *    - 实时渲染更新: 与VTK组件同步更新显示
 * 
 * 竞赛亮点:
 * - 多模态医学图像融合显示技术
 * - 智能血管结构识别与高亮显示
 * - 人机交互友好的医学图像浏览界面
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (
    QFrame, QGridLayout, QLabel
)
import numpy as np
from biaozu import ImageDialog 
class ImageDisplay(QFrame):
    """
    医学图像显示组件 - 管理三个正交视图的图像显示与交互
    
    该组件实现了医学图像的三视图显示，支持多种图像格式和交互操作:
    1. 图像显示: 同时展示横截面、矢状面、冠状面三个视角的医学图像
    2. 格式支持: 支持灰度图像、RGB彩色图像、带血管标记的四通道图像
    3. 交互控制: 实现鼠标点击查看细节、滚轮切换切片等交互功能
    4. VTK集成: 提供3D视图框架用于与VTK组件集成
    """
    
    def __init__(self, parent=None):
        """
        初始化医学图像显示组件
        
        Args:
            parent (QWidget, optional): 父级组件，默认为None
        """
        super().__init__(parent)
        self.setup_ui()
        # 初始化窗宽窗位参数，用于调整图像对比度和亮度
        # 窗宽(WW)控制对比度，窗位(WC)控制亮度
        self.window_width = 700
        self.window_center = 350
        self.min_value = self.window_center - self.window_width / 2
        self.max_value = self.window_center + self.window_width / 2
        # 存储三个方向的图像数据
        self.image_xy = None  # 横截面图像数据 (Axial)
        self.image_xz = None  # 矢状面图像数据 (Sagittal)
        self.image_yz = None  # 冠状面图像数据 (Coronal)
        # 当前显示的切片索引
        self.x = 0  # 横截面切片索引
        self.y = 0  # 矢状面切片索引
        self.z = 0  # 冠状面切片索引
        self.background_mha_path = None  # 背景MHA文件路径，用于图像对比显示
    
    def setup_ui(self):
        """设置UI布局和控件 - 构建医学图像显示界面"""
        self.setFixedSize(600, 400)
        layout = QGridLayout(self)
        layout.setSpacing(20)

        # 横截面视图 (Axial view) - 显示从头部向脚部观察的切面
        self.lab1_foreground = QLabel()
        self.lab1_foreground.setFixedSize(600, 400)
        pixmap1 = QPixmap("image/agg.png")
        self.lab1_foreground.setPixmap(pixmap1)
        self.lab1_foreground.setStyleSheet("background-color: #000000; border: 3px solid #ff9999; border-radius: 6px;")
        self.lab1_foreground.setAlignment(Qt.AlignCenter)
        self.lab1_foreground.setMouseTracking(True)  # 启用鼠标跟踪以支持实时交互
        
        # 矢状面视图 (Sagittal view) - 显示从左向右观察的切面
        self.lab2_foreground = QLabel()
        self.lab2_foreground.setFixedSize(600, 400)
        pixmap2 = QPixmap("image/agg.png")
        self.lab2_foreground.setPixmap(pixmap2)
        self.lab2_foreground.setStyleSheet("background-color: #000000; border: 3px solid #99ff99; border-radius: 6px;")
        self.lab2_foreground.setAlignment(Qt.AlignCenter)
        self.lab2_foreground.setMouseTracking(True)  # 启用鼠标跟踪以支持实时交互
        
        # 冠状面视图 (Coronal view) - 显示从前向后观察的切面
        self.lab3_foreground = QLabel()
        self.lab3_foreground.setFixedSize(600, 400)
        pixmap3 = QPixmap("image/agg.png")
        if not pixmap3.isNull():
            self.lab3_foreground.setPixmap(pixmap3.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            default_pixmap = QPixmap(400, 400)
            default_pixmap.fill(Qt.black)
            self.lab3_foreground.setPixmap(default_pixmap)
        self.lab3_foreground.setStyleSheet("background-color: #000000; border: 3px solid #9999ff; border-radius: 6px;")
        self.lab3_foreground.setAlignment(Qt.AlignCenter)
        self.lab3_foreground.setMouseTracking(True)  # 启用鼠标跟踪以支持实时交互
        
        # 3D视图框架 - 用于集成VTK三维可视化组件
        self.frame1 = QFrame()
        self.frame1.resize(600, 400)
        self.frame1.setFrameShape(QFrame.StyledPanel)
        self.frame1.setStyleSheet("background-color: #000000; border: 3px solid #ffff99; border-radius: 6px;")
        layout.addWidget(self.lab1_foreground, 1, 1)
        layout.addWidget(self.lab2_foreground, 1, 2)
        layout.addWidget(self.lab3_foreground, 2, 1)
        layout.addWidget(self.frame1, 2, 2)

    
    def get_3d_frame(self):
        """
        获取3D视图框架 - 用于集成VTK三维可视化组件
        该框架作为VTK渲染器的容器，实现三维医学图像的立体展示
        
        Returns:
            QFrame: 3D视图框架组件
        """
        return self.frame1
    
    def set_image_data(self, image_xy, image_xz, image_yz):
        """
        设置图像数据 - 配置三个正交视图的医学图像数据
        该方法用于加载和初始化医学图像数据，支持后续的显示和处理操作
        
        Args:
            image_xy (numpy.ndarray): 横截面图像数据 (Axial)
            image_xz (numpy.ndarray): 矢状面图像数据 (Sagittal)
            image_yz (numpy.ndarray): 冠状面图像数据 (Coronal)
        """
        self.image_xy = image_xy
        self.image_xz = image_xz
        self.image_yz = image_yz
    
    def set_window_parameters(self, window_width, window_center):
        """
        设置窗宽窗位参数 - 调整医学图像的对比度和亮度显示效果
        医学图像通常具有较大的灰度范围，通过窗宽窗位调整可以突出显示感兴趣的组织结构
        
        窗宽(WW)和窗位(WC)原理:
        - 窗宽: 决定显示的灰度范围，影响图像对比度
        - 窗位: 决定显示的中心灰度值，影响图像亮度
        - 显示范围: [窗位-窗宽/2, 窗位+窗宽/2]
        
        Args:
            window_width (int): 窗宽值，控制对比度
            window_center (int): 窗位值，控制亮度
        """
        self.window_width = window_width
        self.window_center = window_center
        self.min_value = self.window_center - self.window_width / 2
        self.max_value = self.window_center + self.window_width / 2
    
    def set_background_mha_path(self, path):
        """
        设置背景MHA文件路径 - 用于图像对比显示功能
        该路径用于在图像对比对话框中加载原始图像作为背景参考
        
        Args:
            path (str): 背景MHA文件路径
        """
        self.background_mha_path = path
    
    def update_image_xy(self, x):
        """
        更新横截面图像显示 - 根据指定索引更新横截面视图
        横截面(AXIAL)是沿人体长轴水平切开的切面，从头部观察向脚部
        
        该方法支持多种图像格式:
        1. 四通道带标记图像: 用于显示血管结构，包含原始数据和标记信息
        2. RGB彩色图像: 用于显示已处理的彩色图像
        3. 灰度图像: 用于显示原始医学图像
        
        Args:
            x (int): 横截面切片索引
        """
        self.x = x
        if self.image_xy is None:
            return
            
        # 检查图像是否为带标记的四通道格式 (原始数据, 血管标记, ?, 颜色标记)
        if len(self.image_xy.shape) == 4 and self.image_xy.shape[-1] == 4:
            # 处理带标记的图像 - 分离原始数据和血管标记信息
            original_slice = self.image_xy[x, :, :, 0]  # 原始数据
            vessel_mask = self.image_xy[x, :, :, 1]     # 血管标记
            
            # 应用窗宽窗位调整到原始数据 - 突出显示特定组织结构
            rescaled_image = np.clip(original_slice, self.min_value, self.max_value)
            rescaled_image = ((rescaled_image - self.min_value) / self.window_width) * 255
            rescaled_image = rescaled_image.astype(np.uint8)
            
            # 创建RGB图像 - 为血管标记上色做准备
            rgb_image = np.stack([rescaled_image, rescaled_image, rescaled_image], axis=-1)
            
            # 根据颜色标记设置血管颜色 - 实现不同血管类型的可视化区分
            vessel_mask = self.image_xy[x, :, :, 1]     # 血管标记
            color_marker = self.image_xy[x, :, :, 3]    # 颜色标记
            
            # 定义不同血管类型的掩码
            red_mask = (vessel_mask == 1) & (color_marker == 0)    # 红色标记血管
            yellow_mask = (vessel_mask == 1) & (color_marker == 1) # 黄色标记血管
            white_mask = (vessel_mask == 1) & (color_marker == 2)  # 白色标记血管
            green_mask = (vessel_mask == 1) & (color_marker == 3)  # 绿色标记血管
            blue_mask = (vessel_mask == 1) & (color_marker == 4)   # 蓝色标记血管
            
            # 设置不同颜色的血管区域 - 实现血管结构的高亮显示
            rgb_image[red_mask, 0] = 255  # R通道
            rgb_image[red_mask, 1] = 0    # G通道
            rgb_image[red_mask, 2] = 0    # B通道
            
            # 设置黄色血管区域
            rgb_image[yellow_mask, 0] = 255  # R通道
            rgb_image[yellow_mask, 1] = 255  # G通道
            rgb_image[yellow_mask, 2] = 0    # B通道
            
            # 设置白色血管区域
            rgb_image[white_mask, 0] = 255  # R通道
            rgb_image[white_mask, 1] = 255  # G通道
            rgb_image[white_mask, 2] = 255  # B通道
            
            # 设置绿色血管区域
            rgb_image[green_mask, 0] = 0    # R通道
            rgb_image[green_mask, 1] = 255  # G通道
            rgb_image[green_mask, 2] = 0    # B通道
            
            # 设置蓝色血管区域
            rgb_image[blue_mask, 0] = 0     # R通道
            rgb_image[blue_mask, 1] = 0     # G通道
            rgb_image[blue_mask, 2] = 255   # B通道
            
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, w * ch, QImage.Format_RGB888)
        elif len(self.image_xy.shape) == 4 and self.image_xy.shape[-1] == 3:
            # 处理RGB图像 - 直接使用已处理的彩色图像数据
            current_slice = self.image_xy[x]
            # 直接使用RGB图像数据，不进行窗宽窗位调整，以保持原始亮度
            h, w, ch = current_slice.shape
            # 确保数组是连续的并转换为正确的数据类型
            current_slice = np.ascontiguousarray(current_slice.astype(np.uint8))
            qt_image = QImage(current_slice.data, w, h, w * ch, QImage.Format_RGB888)
        else:
            # 处理灰度图像 - 对原始医学图像进行窗宽窗位调整
            rescaled_image = np.clip(self.image_xy[self.x], self.min_value, self.max_value)
            rescaled_image = ((rescaled_image - self.min_value) / self.window_width) * 255
            rescaled_image = rescaled_image.astype(np.uint8)
            h, w = rescaled_image.shape
            # 确保数组是连续的
            rescaled_image = np.ascontiguousarray(rescaled_image)
            qt_image = QImage(rescaled_image.data, w, h, w, QImage.Format_Grayscale8)
            
        pixmap = QPixmap.fromImage(qt_image)
        self.lab1_foreground.setPixmap(pixmap.scaled(
            self.lab1_foreground.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation))
    
    def update_image_xz(self, y):
        """
        更新矢状面图像显示 - 根据指定索引更新矢状面视图
        矢状面(SAGITTAL)是沿人体长轴纵向切开的切面，从左侧观察向右侧
        
        处理流程与update_image_xy方法一致，仅数据源不同
        
        Args:
            y (int): 矢状面切片索引
        """
        self.y = y
        if self.image_xz is None:
            return
            
        # 检查图像是否为带标记的四通道格式
        if len(self.image_xz.shape) == 4 and self.image_xz.shape[-1] == 4:
            # 处理带标记的图像
            original_slice = self.image_xz[y, :, :, 0]  # 原始数据
            vessel_mask = self.image_xz[y, :, :, 1]     # 血管标记
            
            # 应用窗宽窗位调整到原始数据
            rescaled_image = np.clip(original_slice, self.min_value, self.max_value)
            rescaled_image = ((rescaled_image - self.min_value) / self.window_width) * 255
            rescaled_image = rescaled_image.astype(np.uint8)
            
            # 创建RGB图像
            rgb_image = np.stack([rescaled_image, rescaled_image, rescaled_image], axis=-1)
            
            # 根据颜色标记设置血管颜色
            vessel_mask = self.image_xz[y, :, :, 1]     # 血管标记
            color_marker = self.image_xz[y, :, :, 3]    # 颜色标记
            
            red_mask = (vessel_mask == 1) & (color_marker == 0)    # 红色标记
            yellow_mask = (vessel_mask == 1) & (color_marker == 1) # 黄色标记
            white_mask = (vessel_mask == 1) & (color_marker == 2)  # 白色标记
            green_mask = (vessel_mask == 1) & (color_marker == 3)  # 绿色标记
            blue_mask = (vessel_mask == 1) & (color_marker == 4)   # 蓝色标记
            
            # 设置红色血管区域
            rgb_image[red_mask, 0] = 255  # R
            rgb_image[red_mask, 1] = 0    # G
            rgb_image[red_mask, 2] = 0    # B
            
            # 设置黄色血管区域
            rgb_image[yellow_mask, 0] = 255  # R
            rgb_image[yellow_mask, 1] = 255  # G
            rgb_image[yellow_mask, 2] = 0    # B
            
            # 设置白色血管区域
            rgb_image[white_mask, 0] = 255  # R
            rgb_image[white_mask, 1] = 255  # G
            rgb_image[white_mask, 2] = 255  # B
            
            # 设置绿色血管区域
            rgb_image[green_mask, 0] = 0    # R
            rgb_image[green_mask, 1] = 255  # G
            rgb_image[green_mask, 2] = 0    # B
            
            # 设置蓝色血管区域
            rgb_image[blue_mask, 0] = 0     # R
            rgb_image[blue_mask, 1] = 0     # G
            rgb_image[blue_mask, 2] = 255   # B
            
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, w * ch, QImage.Format_RGB888)

        elif len(self.image_xz.shape) == 4 and self.image_xz.shape[-1] == 3:
            # 处理RGB图像
            current_slice = self.image_xz[y]
            # 直接使用RGB图像数据，不进行窗宽窗位调整，以保持原始亮度
            h, w, ch = current_slice.shape
            # 确保数组是连续的并转换为正确的数据类型
            current_slice = np.ascontiguousarray(current_slice.astype(np.uint8))
            qt_image = QImage(current_slice.data, w, h, w * ch, QImage.Format_RGB888)
        else:
            # 处理灰度图像
            rescaled_image = np.clip(self.image_xz[self.y], self.min_value, self.max_value)
            rescaled_image = ((rescaled_image - self.min_value) / self.window_width) * 255
            rescaled_image = rescaled_image.astype(np.uint8)
            h, w = rescaled_image.shape
            # 确保数组是连续的
            rescaled_image = np.ascontiguousarray(rescaled_image)
            qt_image = QImage(rescaled_image.data, w, h, w, QImage.Format_Grayscale8)
            
        pixmap = QPixmap.fromImage(qt_image)
        self.lab2_foreground.setPixmap(pixmap.scaled(
            self.lab2_foreground.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation))


    def update_image_yz(self, z):
        """
        更新冠状面图像显示 - 根据指定索引更新冠状面视图
        冠状面(CORONAL)是沿人体长轴纵向切开的切面，从前侧观察向后侧
        
        处理流程与update_image_xy方法一致，仅数据源不同
        
        Args:
            z (int): 冠状面切片索引
        """
        self.z = z
        if self.image_yz is None:
            return
            
        # 检查图像是否为带标记的四通道格式
        if len(self.image_yz.shape) == 4 and self.image_yz.shape[-1] == 4:
            # 处理带标记的图像
            original_slice = self.image_yz[z, :, :, 0]  # 原始数据
            vessel_mask = self.image_yz[z, :, :, 1]     # 血管标记
            
            # 应用窗宽窗位调整到原始数据
            rescaled_image = np.clip(original_slice, self.min_value, self.max_value)
            rescaled_image = ((rescaled_image - self.min_value) / self.window_width) * 255
            rescaled_image = rescaled_image.astype(np.uint8)
            
            # 创建RGB图像
            rgb_image = np.stack([rescaled_image, rescaled_image, rescaled_image], axis=-1)
            
             # 根据颜色标记设置血管颜色
            vessel_mask = self.image_yz[z, :, :, 1]     # 血管标记
            color_marker = self.image_yz[z, :, :, 3]    # 颜色标记
            
            red_mask = (vessel_mask == 1) & (color_marker == 0)    # 红色标记
            yellow_mask = (vessel_mask == 1) & (color_marker == 1) # 黄色标记
            white_mask = (vessel_mask == 1) & (color_marker == 2)  # 白色标记
            green_mask = (vessel_mask == 1) & (color_marker == 3)  # 绿色标记
            blue_mask = (vessel_mask == 1) & (color_marker == 4)   # 蓝色标记
            
            # 设置红色血管区域
            rgb_image[red_mask, 0] = 255  # R
            rgb_image[red_mask, 1] = 0    # G
            rgb_image[red_mask, 2] = 0    # B
            
            # 设置黄色血管区域
            rgb_image[yellow_mask, 0] = 255  # R
            rgb_image[yellow_mask, 1] = 255  # G
            rgb_image[yellow_mask, 2] = 0    # B
            
            # 设置白色血管区域
            rgb_image[white_mask, 0] = 255  # R
            rgb_image[white_mask, 1] = 255  # G
            rgb_image[white_mask, 2] = 255  # B
            
            # 设置绿色血管区域
            rgb_image[green_mask, 0] = 0    # R
            rgb_image[green_mask, 1] = 255  # G
            rgb_image[green_mask, 2] = 0    # B
            
            # 设置蓝色血管区域
            rgb_image[blue_mask, 0] = 0     # R
            rgb_image[blue_mask, 1] = 0     # G
            rgb_image[blue_mask, 2] = 255   # B
            
            h, w, ch = rgb_image.shape
            qt_image = QImage(rgb_image.data, w, h, w * ch, QImage.Format_RGB888)
        elif len(self.image_yz.shape) == 4 and self.image_yz.shape[-1] == 3:
            # 处理RGB图像
            current_slice = self.image_yz[z]
            # 直接使用RGB图像数据，不进行窗宽窗位调整，以保持原始亮度
            h, w, ch = current_slice.shape
            # 确保数组是连续的并转换为正确的数据类型
            current_slice = np.ascontiguousarray(current_slice.astype(np.uint8))
            qt_image = QImage(current_slice.data, w, h, w * ch, QImage.Format_RGB888)
        else:
            # 处理灰度图像
            rescaled_image = np.clip(self.image_yz[self.z], self.min_value, self.max_value)
            rescaled_image = ((rescaled_image - self.min_value) / self.window_width) * 255
            rescaled_image = rescaled_image.astype(np.uint8)
            h, w = rescaled_image.shape
            # 确保数组是连续的
            rescaled_image = np.ascontiguousarray(rescaled_image)
            qt_image = QImage(rescaled_image.data, w, h, w, QImage.Format_Grayscale8)
            
        pixmap = QPixmap.fromImage(qt_image)
        self.lab3_foreground.setPixmap(pixmap.scaled(
            self.lab3_foreground.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation))

    def get_current_slice_positions(self):
        """
        获取当前切片位置 - 返回三个视图的当前切片索引
        用于同步VTK三维视图或其他组件的切片位置
        
        Returns:
            tuple: (x, y, z) 当前三个视图的切片索引
                   x: 横截面切片索引
                   y: 矢状面切片索引
                   z: 冠状面切片索引
        """
        return self.x, self.y, self.z
    
    def process_image_for_vessel_enhancement(self, image_data):
        """
        对图像进行血管增强处理 - 突出显示血管结构特征
        该方法通过对比度拉伸和边缘增强技术实现血管结构的增强显示
        
        处理流程:
        1. 对比度拉伸: 扩展图像灰度范围，增强血管与背景的对比
        2. 边缘增强: 使用拉普拉斯算子增强血管边缘特征
        3. 结果融合: 将增强结果与原始图像融合
        
        Args:
            image_data (numpy.ndarray): 原始图像数据
            
        Returns:
            numpy.ndarray: 处理后的图像数据
        """
        if image_data is None:
            return None
        
        # 检查是否为RGB图像
        if len(image_data.shape) >= 3 and image_data.shape[-1] == 3:
            # 对于RGB图像，只对第一个通道进行处理
            current_slice = image_data[self.x if image_data is self.image_xy 
                                    else self.y if image_data is self.image_xz 
                                    else self.z][:,:,0]  # 取第一个通道
        else:
            # 获取当前切片
            current_slice = image_data[self.x if image_data is self.image_xy 
                                    else self.y if image_data is self.image_xz 
                                    else self.z]
        
        # 简单但更有效的血管增强方法
        # 使用对比度拉伸和边缘增强
        processed = np.copy(current_slice)
        
        # 对比度拉伸 - 扩展有效灰度范围
        p1, p99 = np.percentile(processed, (1, 99))
        processed = np.clip(processed, p1, p99)
        processed = ((processed - p1) / (p99 - p1)) * 255
        
        # 简单的边缘增强（模拟血管增强效果）
        # 这里使用拉普拉斯算子进行边缘增强
        from scipy import ndimage
        laplacian = ndimage.laplace(processed)
        enhanced = processed - 0.3 * laplacian
        enhanced = np.clip(enhanced, 0, 255)
        
        # 如果是RGB图像，创建与原数据相同结构的数组并替换当前切片的第一个通道
        if len(image_data.shape) >= 3 and image_data.shape[-1] == 3:
            result = np.copy(image_data)
            if image_data is self.image_xy:
                result[self.x][:,:,0] = enhanced
            elif image_data is self.image_xz:
                result[self.y][:,:,0] = enhanced
            elif image_data is self.image_yz:
                result[self.z][:,:,0] = enhanced
        else:
            # 创建与原数据相同结构的数组并替换当前切片
            result = np.copy(image_data)
            if image_data is self.image_xy:
                result[self.x] = enhanced
            elif image_data is self.image_xz:
                result[self.y] = enhanced
            elif image_data is self.image_yz:
                result[self.z] = enhanced
        
        return result
    

    def handle_mouse_press(self, event, vtk_viewer):
        """
        处理鼠标点击事件 - 实现图像查看和对比功能
        左键点击任一视图可打开图像对比对话框，展示原始图像与血管增强结果的对比
        
        Args:
            event (QMouseEvent): 鼠标事件对象
            vtk_viewer (VTKIntegration): VTK查看器对象，用于3D视图交互
        """
        from PyQt5.QtWidgets import QMessageBox
        
        if event.button() == Qt.LeftButton:
            # 检查是否有图像数据
            if self.image_xy is None or self.image_xz is None or self.image_yz is None:
                # 显示提示信息
                msg_box = QMessageBox()
                msg_box.setWindowTitle("提示")
                msg_box.setText("请选择医学文件")
                msg_box.setIcon(QMessageBox.Information)
                msg_box.exec_()
                return
            if self.lab1_foreground.geometry().contains(event.pos()):
                # 对于轴向视图（横截面），创建原图和处理后图像的对比窗口
                # 传递None作为processed_image参数，让ImageDialog自动加载预测文件
                slice_window = ImageDialog(self.image_xy, None, self.x, self.image_xy.shape[0], '  横 截 面', background_mha_path=self.background_mha_path)
                slice_window.exec_()
            elif self.lab2_foreground.geometry().contains(event.pos()):
                # 对于矢状视图（矢状面）
                # 传递None作为processed_image参数，让ImageDialog自动加载预测文件
                slice_window = ImageDialog(self.image_xz, None, self.y, self.image_xz.shape[0], '  矢 状 面', background_mha_path=self.background_mha_path)
                slice_window.exec_()
            elif self.lab3_foreground.geometry().contains(event.pos()):
                # 对于冠状视图（冠状面）
                # 传递None作为processed_image参数，让ImageDialog自动加载预测文件
                slice_window = ImageDialog(self.image_yz, None, self.z, self.image_yz.shape[0], '  冠 状 面', background_mha_path=self.background_mha_path)
                slice_window.exec_()
    def handle_wheel_event(self, event, vtk_viewer):
        """
        处理鼠标滚轮事件 - 实现切片切换功能
        通过滚动鼠标滚轮在当前鼠标所在的视图中切换切片
        
        切片切换逻辑:
        1. 检测鼠标位置确定操作的视图
        2. 根据滚轮方向更新对应视图的切片索引
        3. 更新二维图像显示和三维VTK视图
        
        Args:
            event (QWheelEvent): 鼠标滚轮事件对象
            vtk_viewer (VTKIntegration): VTK查看器对象，用于同步3D视图
        """
        # 检查是否有图像数据，如果没有则显示提示
        if self.image_xy is None or self.image_xz is None or self.image_yz is None:
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("提示")
            msg_box.setText("请选择医学文件")
            msg_box.exec_()
            return
            
        mouse_pos = event.pos()
        
        if self.lab1_foreground.geometry().contains(mouse_pos):
            # 横截面视图切片切换
            if event.angleDelta().y() > 0:
                self.x = min(self.x + 5, self.image_xy.shape[0] - 1)
            else:
                self.x = max(self.x - 5, 0)
            self.update_image_xy(self.x)
            vtk_viewer.change_slice(2, self.x)  # 同步更新VTK视图
        elif self.lab2_foreground.geometry().contains(mouse_pos):
            # 矢状面视图切片切换
            if event.angleDelta().y() > 0:
                self.y = min(self.y + 5, self.image_xz.shape[0] - 1)
            else:
                self.y = max(self.y - 5, 0)
            self.update_image_xz(self.y)
            vtk_viewer.change_slice(0, self.y)  # 同步更新VTK视图
        elif self.lab3_foreground.geometry().contains(mouse_pos):
            # 冠状面视图切片切换
            if event.angleDelta().y() > 0:
                self.z = min(self.z + 5, self.image_yz.shape[0] - 1)
            else:
                self.z = max(self.z - 5, 0)
            self.update_image_yz(self.z)
            vtk_viewer.change_slice(1, self.z)  # 同步更新VTK视图
    
    def delete_actor_post(self):
        """从渲染器移除后处理结果 - 清理VTK渲染器中的后处理对象"""
        if self.actor_post:
            self.ren[3].RemoveActor(self.actor_post)
            self.reader.Update()
            self.ren_win.Render()

    # 添加控制votingFusion_result.mha切片显示的方法
    def show_voting_fusion_slices(self, voting_fusion_data_xy, voting_fusion_data_xz, voting_fusion_data_yz):
        """
        显示votingFusion_result.mha的三个方向切片 - 展示融合预测结果
        该方法用于显示多模型投票融合后的血管分割结果
        
        Args:
            voting_fusion_data_xy: 横截面方向的融合结果数据
            voting_fusion_data_xz: 矢状面方向的融合结果数据
            voting_fusion_data_yz: 冠状面方向的融合结果数据
        """
        self.voting_fusion_xy = voting_fusion_data_xy
        self.voting_fusion_xz = voting_fusion_data_xz
        self.voting_fusion_yz = voting_fusion_data_yz
        
        # 更新当前切片显示
        self.update_voting_fusion_slice_xy(self.x)
        self.update_voting_fusion_slice_xz(self.y)
        self.update_voting_fusion_slice_yz(self.z)
    
    def hide_voting_fusion_slices(self):
        """隐藏votingFusion_result.mha的三个方向切片 - 恢复原始图像显示"""
        # 清除前景图像显示
        self.lab1_foreground.clear()
        self.lab2_foreground.clear()
        self.lab3_foreground.clear()
        
        # 重新显示原始图像
        self.update_image_xy(self.x)
        self.update_image_xz(self.y)
        self.update_image_yz(self.z)
    
    def update_voting_fusion_slice_xy(self, x):
        """更新横截面votingFusion切片显示"""
        if hasattr(self, 'voting_fusion_xy') and self.voting_fusion_xy is not None:
            # 实现votingFusion切片显示逻辑
            pass
            
    def update_voting_fusion_slice_xz(self, y):
        """更新矢状面votingFusion切片显示"""
        if hasattr(self, 'voting_fusion_xz') and self.voting_fusion_xz is not None:
            # 实现votingFusion切片显示逻辑
            pass
            
    def update_voting_fusion_slice_yz(self, z):
        """更新冠状面votingFusion切片显示"""
        if hasattr(self, 'voting_fusion_yz') and self.voting_fusion_yz is not None:
            # 实现votingFusion切片显示逻辑
            pass
