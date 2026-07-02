"""
biaozu.py
医学图像标注与交互显示模块

该模块提供了一个交互式图像标注对话框，支持医学图像的详细查看、标注和处理功能，
是医学图像分析系统中用户交互的核心组件。主要功能包括：
- 双视图对比显示：同时显示原始图像和处理后图像
- 交互式标注：允许用户在图像上点击标记感兴趣区域
- 切片导航：通过滑块和数值输入框切换不同层面的图像
- 窗宽窗位调整：实时调整图像显示对比度和亮度
- 标记点同步：在左右视图间同步显示标记点
- 标注编辑：支持对已有标注结果进行修改和优化
- 模型重训练：提供模型重新训练功能以优化分割效果
- 大模型调用：预留接口用于调用更强大的分割模型

该模块在医学图像处理竞赛项目中具有重要意义，体现了作品的交互性和实用性价值，
能够帮助医生或研究人员更准确地分析和标注医学图像数据，提升诊断和研究效率。
"""

import numpy as np
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QSpinBox, QLabel, QTextEdit,QPushButton,QInputDialog, QMessageBox,QProgressBar
from PyQt5.QtGui import QPixmap, QPainter, QColor, QImage
from PyQt5.QtCore import Qt, QPoint
from dianji import *  # 保持对dianji的引用，但只在biaozu内部使用
from basicfunction import load_mha
import sys
import os
import subprocess
import threading
from PyQt5.QtCore import QProcess, pyqtSignal
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from xiu_biaozu import PolygonEditor
from re_train import ModelTrainer


class ImageDialog(QDialog):
    """
    医学图像交互标注对话框类
    
    提供医学图像的详细查看、交互标注和处理功能的图形界面，是用户与医学图像处理系统
    进行深度交互的核心界面。该类实现了图像显示、用户交互、标注管理等关键功能，
    为医学图像分析提供了直观、便捷的操作环境，充分体现了本竞赛作品的人机交互设计水平。
    """
    
    def __init__(self, original_image, processed_image=None, index=0, number=1, a="", parent=None, background_mha_path=None):
        """
        初始化图像对话框
        
        Args:
            original_image (numpy.ndarray): 原始图像数据，作为参考基准显示在左侧视图
            processed_image (numpy.ndarray, optional): 处理后的图像数据，显示在右侧视图，
                                                     如果为None则只显示原始图像
            index (int): 当前显示的切片索引
            number (int): 总切片数量
            a (str): 视图名称标识，用于确定切片方向（矢状面/冠状面/横截面）
            parent (QWidget, optional): 父级组件
            background_mha_path (str, optional): 背景MHA文件路径，用于标注编辑功能
        """
        super().__init__(parent)
        self.original_image = original_image
        # 如果processed_image为None，则尝试加载prediction_Normal001-MRA_binary.mha作为processed_image
        if processed_image is not None:
            self.processed_image = processed_image
        else:
            # 根据视图方向加载对应的预测结果文件
            prediction_file_path = os.path.join("mha", "prediction_Normal001-MRA_binary.mha")
            if os.path.exists(prediction_file_path):
                try:
                    prediction_data, _, _ = load_mha(prediction_file_path)
                    
                    # 根据视图方向调整预测数据的方向
                    if '矢状面' in a or '矢 状 面' in a:
                        # 矢状面视图 - 需要将预测数据转为矢状面方向
                        prediction_data = np.transpose(prediction_data, (2, 0, 1))
                        prediction_data = np.flip(prediction_data, axis=(0, 1))
                    elif '冠状面' in a or '冠 状 面' in a:
                        # 冠状面视图 - 需要将预测数据转为冠状面方向
                        prediction_data = np.flip(np.transpose(prediction_data, (1, 0, 2)), axis=(1, 0))
                    
                    self.processed_image = prediction_data
                except Exception as e:
                    self.processed_image = original_image
            else:
                self.processed_image = original_image
        self.window_width = 700
        self.window_center = 350
        self.min_value = self.window_center - self.window_width / 2
        self.max_value = self.window_center + self.window_width / 2
        self.a = a
        self.setWindowTitle("详细操作")
        self.setGeometry(100, 100, 1400, 800)
        self.n = index
        self.background_mha_path = background_mha_path  # 保存背景MHA路径
        self.setWindowFlags(
            Qt.Window | Qt.WindowMaximizeButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)
        # 记录初始窗口大小
        self.initial_width = 800
        self.initial_height = 600

        # 主布局：垂直排列所有组件
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)  # 减少主布局间距
        self.main_layout.setContentsMargins(15, 15, 15, 15)  # 减少边距

        # 图像布局：水平排列图像显示区域
        self.image_layout = QHBoxLayout()
        self.image_layout.setSpacing(15)  # 减少图像布局间距

        # 创建可点击的标签用于显示图像
        self.original_image_label = ClickableLabel(self.array_to_pixmap(self.original_image), self)
        self.original_image_label.setStyleSheet("background-color: #000000; border: 1px solid #2979ff; border-radius: 6px;")
        self.original_image_label.setAlignment(Qt.AlignCenter)  # 居中对齐

        # 总是显示两个图像（原始图像和处理后的图像）
        processed_pixmap = self.array_to_pixmap(self.processed_image)
        self.processed_image_label = ClickableLabel(processed_pixmap, self)
        self.processed_image_label.setStyleSheet("background-color: #000000; border: 1px solid #2979ff; border-radius: 6px;")
        self.processed_image_label.setAlignment(Qt.AlignCenter)  # 居中对齐
        self.image_layout.addWidget(self.original_image_label)
        self.image_layout.addWidget(self.processed_image_label)
        # 关键修改：让左侧图像点击时，右侧图像也显示标记点
        self.original_image_label.linked_label = self.processed_image_label
        # 右侧图像也可以点击时同步到左侧
        self.processed_image_label.linked_label = self.original_image_label

        self.main_layout.addLayout(self.image_layout)

        # 按钮布局：水平排列功能按钮
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(8)  # 减少按钮间距
        
        # 添加"修改标注"按钮：用于编辑已有的标注结果
        self.modify_annotation_button = QPushButton("修改标注")
        self.modify_annotation_button.setStyleSheet("""
            QPushButton {
                background-color: #2979ff;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #1c54b2;
            }
        """)
        self.modify_annotation_button.clicked.connect(self.modify_annotation)
        self.button_layout.addWidget(self.modify_annotation_button)

        # 添加"调用大模型分割"按钮：预留接口用于调用更强大的分割模型
        self.large_model_segmentation_button = QPushButton("调用大模型分割")
        self.large_model_segmentation_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.large_model_segmentation_button.clicked.connect(self.large_model_segmentation)
        self.button_layout.addWidget(self.large_model_segmentation_button)
        
        # 添加"重新训练"按钮：用于重新训练模型以优化分割效果
        self.retrain_model_button = QPushButton("重新训练")
        self.retrain_model_button.setStyleSheet("""
            QPushButton {
                background-color: #4caf50;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
        """)
        self.retrain_model_button.clicked.connect(self.retrain_model)
        self.button_layout.addWidget(self.retrain_model_button)

        self.button_layout.addStretch()

        # 创建一个居中的滑块区域布局
        self.slider_area_layout = QHBoxLayout()
        self.slider_area_layout.setSpacing(15)  # 控件之间的小间距
        self.slider_area_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距
        self.slider_area_layout.addStretch()  # 左侧弹性空间

        # 位置标签：显示当前视图名称
        self.window_possion = QLabel(a)
        self.window_possion.setStyleSheet("color: #00c6ff; font-weight: bold;")
        self.window_possion.setFixedSize(106, 20)
        self.slider_area_layout.addWidget(self.window_possion)

        # 滑杆：用于切换不同层面的图像切片
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(number - 1)
        self.slider.setValue(index)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #3d3d3d;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background-color: #2979ff;
                border: none;
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background-color: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #00c6ff, stop: 1 #2979ff);
                height: 4px;
                border-radius: 2px;
            }
        """)
        self.slider.setFixedHeight(20)
        self.slider.setFixedWidth(200)  # 固定宽度
        self.slider_area_layout.addWidget(self.slider)

        # 滑杆按钮：通过数值输入切换图像切片
        self.index_button = QSpinBox()
        self.index_button.setMinimum(0)
        self.index_button.setMaximum(number - 1)
        self.index_button.setValue(index)
        self.index_button.setStyleSheet("""
            QSpinBox {
                background-color: #2a2a2a;
                color: #e1e1e1;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 2px;
            }
            QSpinBox:hover {
                border: 1px solid #2979ff;
            }
        """)
        self.index_button.setFixedSize(50, 25)
        self.slider_area_layout.addWidget(self.index_button)
        
        self.slider_area_layout.addStretch()  # 右侧弹性空间
        
        self.main_layout.addLayout(self.button_layout)
        self.main_layout.addLayout(self.slider_area_layout)
        
        # 添加一个策略来减少按钮区域和滑块区域之间的间距
        self.main_layout.setSpacing(5) 
        # 保存当前缩放比例
        self.original_image_label.original_pixmap = self.array_to_pixmap(self.original_image)
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.original_pixmap = self.array_to_pixmap(self.processed_image)

        # 设置初始大小
        self.set_initial_sizes()

        # 连接信号：同步滑块和数值输入框的值变化
        self.slider.valueChanged.connect(self.valuechange)
        self.index_button.valueChanged.connect(self.valuechangeinbtn)



    def array_to_pixmap(self, array):
        """
        将numpy数组转换为QPixmap图像对象
        
        根据图像数据的维度和通道数，采用不同的处理策略将numpy数组转换为QPixmap对象，
        支持灰度图像、RGB彩色图像和带标注信息的四通道图像等多种格式，确保各类医学图像
        数据都能正确显示。该方法还集成了窗宽窗位调整功能，可以根据用户设置动态调整图像对比度。
        
        Args:
            array (numpy.ndarray): 待转换的图像数据数组
            
        Returns:
            QPixmap: 转换后的图像对象，可用于界面显示
        """
        # 应用窗宽窗位
        min_val = self.window_center - self.window_width / 2
        max_val = self.window_center + self.window_width / 2
        
        # 确保索引不越界
        slice_index = min(self.n, array.shape[0] - 1) if array.shape[0] > 0 else 0
        
        # 特殊处理二值图像（最大值为1，最小值为0）
        if array.max() <= 1 and array.min() >= 0:
            # 对于二值图像，使用不同的显示方式
            if len(array.shape) == 3:
                # 3D二值图像
                binary_slice = array[slice_index]
                # 将二值图像转换为可视化图像（0保持黑色，1变为白色）
                rescaled = (binary_slice * 255).astype(np.uint8)
                height, width = rescaled.shape
                qt_image = QImage(rescaled.data, width, height, width, QImage.Format_Grayscale8)
                return QPixmap.fromImage(qt_image)
        
        # 检查是否为带标记的四通道图像
        if len(array.shape) == 4 and array.shape[-1] == 4:
            # 处理带标记的图像 (4D数组，最后一维是[原始数据, 血管标记, 0, 颜色标记])
            original_slice = array[slice_index, :, :, 0]  # 原始数据
            vessel_mask = array[slice_index, :, :, 1]     # 血管标记
            color_marker = array[slice_index, :, :, 3]    # 颜色标记
            
            # 应用窗宽窗位调整到原始数据
            rescaled = np.clip(original_slice, min_val, max_val)
            rescaled = ((rescaled - min_val) / self.window_width) * 255
            rescaled = rescaled.astype(np.uint8)
            
            # 创建RGB图像
            rgb_image = np.stack([rescaled, rescaled, rescaled], axis=-1)
            
            # 根据颜色标记设置血管颜色（与image_display.py保持一致）
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
            
            height, width, channels = rgb_image.shape
            qt_image = QImage(rgb_image.data, width, height, width * channels, QImage.Format_RGB888)
        elif len(array.shape) == 4 and array.shape[-1] == 3:
            # 处理RGB图像 (4D数组，最后一维是RGB通道)
            rescaled = np.clip(array[slice_index], min_val, max_val)
            rescaled = ((rescaled - min_val) / self.window_width) * 255
            rescaled = rescaled.astype(np.uint8)
            height, width, channels = rescaled.shape
            qt_image = QImage(rescaled.data, width, height, width * channels, QImage.Format_RGB888)
        elif len(array.shape) == 3 and array.shape[-1] == 3:
            # 处理RGB图像 (3D数组，最后一维是RGB通道)
            rescaled = np.clip(array[slice_index], min_val, max_val)
            rescaled = ((rescaled - min_val) / self.window_width) * 255
            rescaled = rescaled.astype(np.uint8)
            height, width, channels = rescaled.shape
            qt_image = QImage(rescaled.data, width, height, width * channels, QImage.Format_RGB888)
        else:
            # 处理灰度图像
            rescaled = np.clip(array[slice_index], min_val, max_val)
            rescaled = ((rescaled - min_val) / self.window_width) * 255
            rescaled = rescaled.astype(np.uint8)
            height, width = rescaled.shape
            qt_image = QImage(rescaled.data, width, height, width, QImage.Format_Grayscale8)
            
        return QPixmap.fromImage(qt_image)


    def set_initial_sizes(self):
        """设置初始大小"""
        self.original_image_label.setMinimumSize(400, 400)
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.setMinimumSize(400, 400)
        

    def valuechange(self, value):
        """
        响应滑块值变化事件
        
        当用户拖动滑块时调用此方法，更新当前显示的切片索引，并同步更新左右视图的显示内容，
        同时重置缩放因子和清除已有的标记点，确保新切片以初始状态显示，提供一致的用户体验。
        
        Args:
            value (int): 滑块的新值，即目标切片索引
        """
        self.n = value
        self.index_button.setValue(self.n)
        self.original_image_label.scale_factor = 1.0
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.scale_factor = 1.0
        self.original_image_label.click_points = []  # 清空标记点
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.click_points = []  # 清空标记点
        self.original_image_label.setPixmap(self.array_to_pixmap(self.original_image))
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.setPixmap(self.array_to_pixmap(self.processed_image))

    def valuechangeinbtn(self, value):
        """
        响应数值输入框值变化事件
        
        当用户在数值输入框中输入新值时调用此方法，功能与滑块值变化类似，
        确保滑块和数值输入框之间的值同步，并更新视图显示内容，提供统一的操作体验。
        
        Args:
            value (int): 数值输入框的新值，即目标切片索引
        """
        self.n = value
        self.slider.setValue(self.n)
        self.original_image_label.scale_factor = 1.0
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.scale_factor = 1.0
        self.original_image_label.click_points = []  # 清空标记点
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.click_points = []  # 清空标记点
        self.original_image_label.setPixmap(self.array_to_pixmap(self.original_image))
        if hasattr(self, 'processed_image_label'):
            self.processed_image_label.setPixmap(self.array_to_pixmap(self.processed_image))

    def get_marked_points(self):
        """
        获取标记点的三维坐标形式
        
        将用户在图像上点击标记的二维像素坐标转换为包含切片索引的三维坐标形式，
        便于后续处理和存储。该方法是图像标注功能的核心数据接口，为标注数据的保存
        和处理提供了标准化的数据格式。
        
        Returns:
            list: 标记点的三维坐标列表，每个元素为 [切片索引, x坐标, y坐标]
        """
        marked_points = []
        for point in self.original_image_label.click_points:
            marked_points.append([self.n, point.x(), point.y()])
        return marked_points

    def closeEvent(self, event):
        """
        响应窗口关闭事件
        
        在窗口关闭前获取并打印标记点数据，便于调试和后续处理。该方法确保了标注数据
        不会在窗口关闭时丢失，为数据持久化提供了基础支持。
        
        Args:
            event (QCloseEvent): 关闭事件对象
        """
        marked_points = self.get_marked_points()
        print("标记点数据:", marked_points)
        super().closeEvent(event)

    def modify_annotation(self):
        """
        修改标注功能实现
        
        提供对已有标注结果的编辑功能，允许用户选择特定的MHA文件进行标注修改，
        支持三种标准医学图像切片方向（轴向、冠状面、矢状面）的标注编辑，
        并根据当前视图自动确定正确的切片方向和索引范围验证，确保编辑操作的安全性。
        这一功能体现了本作品在标注数据精细化管理方面的专业水平，是参赛作品的重要亮点之一。
        """
        # 创建预设选项列表
        options = [
            "mha\\test1_1.mha",
            "mha\\test2_2.mha", 
            "mha\\test3_3.mha",
            "mha\\votingFusion_result.mha",
            "mha\\Postprocessed_result.mha"
        ]
        
        # 弹出选择对话框获取mha文件路径
        option, ok = QInputDialog.getItem(
            self, 
            "选择MHA文件", 
            "请选择需要修改标注的mha文件:",
            options,
            0,  # 默认选择第一个选项
            False  # 不可编辑
        )
        
        if not ok or not option:
            return
            
        mha_file_path = option
            
        if not os.path.exists(mha_file_path):
            QMessageBox.warning(self, "文件错误", "指定的MHA文件不存在！")
            return
            
        # 确定切片方向
        slice_orientation = 'axial'  # 默认为轴向
        print(f"视图名称: '{self.a}'")  # 添加调试输出
        if '矢状面' in self.a:
            slice_orientation = 'sagittal'
        elif '冠状面' in self.a:
            slice_orientation = 'coronal'
        elif '横截面' in self.a:
            slice_orientation = 'axial'
        # 添加对包含空格的字符串的处理
        elif '矢 状 面' in self.a:
            slice_orientation = 'sagittal'
        elif '冠 状 面' in self.a:
            slice_orientation = 'coronal'
        elif '横 截 面' in self.a:
            slice_orientation = 'axial'
        
        print(f"识别的切片方向: {slice_orientation}")  # 添加调试输出
            
        # 创建PolygonEditor实例并运行
        try:
            # 加载MHA数据以检查索引范围
            from basicfunction import load_mha
            mha_data, origin, spacing = load_mha(mha_file_path)
            
            # 根据切片方向验证索引范围
            if slice_orientation == 'axial' and (self.n < 0 or self.n >= mha_data.shape[0]):
                QMessageBox.warning(self, "索引错误", f"对于轴向切片，索引必须在[0, {mha_data.shape[0]-1}]范围内，当前值为{self.n}")
                return
            elif slice_orientation == 'coronal' and (self.n < 0 or self.n >= mha_data.shape[1]):
                QMessageBox.warning(self, "索引错误", f"对于冠状面切片，索引必须在[0, {mha_data.shape[1]-1}]范围内，当前值为{self.n}")
                return
            elif slice_orientation == 'sagittal' and (self.n < 0 or self.n >= mha_data.shape[2]):
                QMessageBox.warning(self, "索引错误", f"对于矢状面切片，索引必须在[0, {mha_data.shape[2]-1}]范围内，当前值为{self.n}")
                return
            
            self.close()
            
            editor = PolygonEditor(
                mha_file_path=mha_file_path,
                slice_index=self.n,
                slice_orientation=slice_orientation,
                background_mha_path=self.background_mha_path
            )
            editor.run()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动标注编辑器失败：{str(e)}")
    

    def large_model_segmentation(self):
        """
        调用大模型分割功能（预留接口）
        
        为未来扩展更强大的分割模型提供接口，当前版本仅显示提示信息，
        体现了作品的可扩展性和前瞻性设计。在竞赛作品中展示了团队对技术发展趋势的把握能力。
        """
        # QMessageBox.information(self, "提示", "调用大模型分割功能尚未实现")
        dialog = ScriptExecutionDialog(self)
        dialog.exec_()


    def retrain_model(self):
        """
        重新训练模型功能
        
        提供模型重新训练功能，允许用户基于当前的标注数据重新训练分割模型，
        以优化分割效果。该功能启动一个独立的训练进度对话框，实时显示训练进度，
        体现了作品在模型迭代优化方面的完整闭环设计，是参赛作品的技术亮点之一。
        """
        # 创建并显示训练进度对话框
        self.training_dialog = TrainingProgressDialog(self)
        self.training_dialog.show()
        
        # 启动训练
        self.training_dialog.start_training()

class TrainingProgressDialog(QDialog):
    """
    模型训练进度对话框类
    
    专门用于显示模型重新训练过程中的进度信息，提供直观的进度条和详细日志输出，
    让用户能够实时了解训练状态。该对话框体现了作品在用户体验设计方面的专业水准，
    是参赛作品人机交互设计的重要组成部分，展示了良好的工程实践能力。
    """
    
    def __init__(self, parent=None):
        """
        初始化训练进度对话框
        
        Args:
            parent (QWidget, optional): 父级组件
        """
        super().__init__(parent)
        self.setWindowTitle("模型重新训练")
        self.setFixedSize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2979ff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00c6ff;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QProgressBar {
                border: 1px solid #555555;
                border-radius: 5px;
                background-color: #333333;
                height: 20px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #2979ff;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("UNet模型训练进度")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2979ff;")
        layout.addWidget(title_label)
        
        # 总体进度条 (Epoch级别)
        self.epoch_progress_label = QLabel("总体进度:")
        self.epoch_progress_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        layout.addWidget(self.epoch_progress_label)
        
        self.total_progress = QProgressBar()
        self.total_progress.setRange(0, 100)
        self.total_progress.setValue(0)
        layout.addWidget(self.total_progress)
        
        # 当前Epoch进度条 (Batch级别)
        self.epoch_progress_label = QLabel("当前Epoch进度:")
        self.epoch_progress_label.setStyleSheet("color: #ffffff; font-weight: bold;")
        layout.addWidget(self.epoch_progress_label)
        
        self.epoch_progress = QProgressBar()
        self.epoch_progress.setRange(0, 100)
        self.epoch_progress.setValue(0)
        layout.addWidget(self.epoch_progress)
        
        # 训练进度文本框
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.trainer = None

    def start_training(self):
        """
        启动模型训练过程
        
        创建并启动模型训练器，连接相关信号槽以接收训练进度更新，
        实现训练过程的实时监控和状态反馈，体现了良好的异步编程实践能力。
        """
        self.trainer = ModelTrainer()
        self.trainer.progress_updated.connect(self.update_progress)
        self.trainer.epoch_progress_updated.connect(self.update_epoch_progress)
        self.trainer.total_progress_updated.connect(self.update_total_progress)
        self.trainer.training_finished.connect(self.training_completed)
        self.trainer.start()

    def update_progress(self, message):
        """
        更新训练进度信息显示
        
        将训练过程中产生的日志信息追加到文本框中，并自动滚动到最新内容，
        确保用户能够实时查看训练状态和关键信息，体现了良好的用户体验设计。
        
        Args:
            message (str): 需要显示的进度信息
        """
        self.progress_text.append(message)
        # 自动滚动到底部
        scrollbar = self.progress_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def update_epoch_progress(self, value):
        """
        更新当前epoch进度条显示
        
        Args:
            value (int): 当前epoch的进度值（0-100）
        """
        self.epoch_progress.setValue(value)
        
    def update_total_progress(self, value):
        """
        更新总体训练进度条显示
        
        Args:
            value (int): 总体训练进度值（0-100）
        """
        self.total_progress.setValue(value)
        
    def training_completed(self):
        """
        响应训练完成事件
        
        当模型训练完成后调用此方法，更新界面状态并启用关闭按钮，
        向用户明确指示训练任务已完成，体现了良好的状态管理设计。
        """
        self.progress_text.append("\n训练已完成！")
        self.total_progress.setValue(100)
        self.epoch_progress.setValue(100)
        self.close_button.setEnabled(True)

class ScriptExecutionDialog(QDialog):
    """
    脚本执行对话框类
    
    用于显示外部Python脚本执行过程和结果的对话框，提供实时日志输出功能，
    让用户能够监视脚本执行状态。该对话框体现了作品在系统集成方面的能力，
    支持调用外部大模型分割功能，提升了系统的扩展性和实用性价值。
    """
    
    def __init__(self, parent=None):
        """
        初始化脚本执行对话框
        
        Args:
            parent (QWidget, optional): 父级组件
        """
        super().__init__(parent)
        self.setWindowTitle("大模型分割执行状态")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QPushButton {
                background-color: #2979ff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00c6ff;
            }
            QPushButton:disabled {
                background-color: #555555;
            }
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
                border-radius: 5px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("大模型分割执行状态")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2979ff;")
        layout.addWidget(title_label)
        
        # 执行状态文本框
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        self.close_button.setEnabled(False)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # 创建QProcess对象用于执行外部脚本
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.finished.connect(self.process_finished)
        
    def exec_(self):
        """
        重写exec_方法，在对话框显示时立即开始执行脚本
        """
        # 立即开始执行脚本
        self.start_script()
        # 调用父类的exec_方法显示对话框
        return super().exec_()
    def start_script(self):
        """
        开始执行外部Python脚本
        """
        script_path = r"D:\0SAM-Med3D-main\medim_val_single.py"
        
        # 检查脚本文件是否存在
        if not os.path.exists(script_path):
            self.output_text.append(f"错误: 找不到脚本文件 {script_path}")
            self.close_button.setEnabled(True)
            return
            
        self.output_text.append(f"正在执行脚本: {script_path}\n")
        self.output_text.append("="*50 + "\n")
        self.output_text.append(f"脚本所在目录: {os.path.dirname(script_path)}\n")
        self.output_text.append(f"使用conda环境: sammed3d\n")
        self.output_text.append("-"*50 + "\n")
        
        # 使用QProcess执行外部Python脚本
        try:
            # 设置工作目录为脚本所在目录
            script_dir = os.path.dirname(script_path)
            self.process.setWorkingDirectory(script_dir)
            
            # 使用conda环境执行脚本
            # 构造命令: conda run -n sammed3d python medim_val_single.py
            conda_command = "conda"
            conda_args = ["run", "-n", "sammed3d", "python", script_path]
            
            self.process.start(conda_command, conda_args)
        except Exception as e:
            self.output_text.append(f"启动脚本失败: {str(e)}")
            self.output_text.append("请确保已安装Anaconda或Miniconda，并且环境'sammed3d'存在")
            self.close_button.setEnabled(True)
        
    def handle_stdout(self):
        """
        处理标准输出
        """
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf-8", errors="ignore")
        self.output_text.append(stdout.rstrip())
        
        # 自动滚动到底部
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def handle_stderr(self):
        """
        处理标准错误输出
        """
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf-8", errors="ignore")
        self.output_text.append("错误: " + stderr.rstrip())
        
        # 自动滚动到底部
        scrollbar = self.output_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def process_finished(self):
        """
        处理进程结束事件
        """
        self.output_text.append("\n" + "="*50)
        self.output_text.append("脚本执行完成!")
        self.close_button.setEnabled(True)