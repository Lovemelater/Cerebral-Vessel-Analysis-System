"""
医学图像标注工具模块
==================

该模块提供了一个双视图医学图像标注工具，用于在两个相关的医学图像序列上进行同步标注。
主要功能包括：
- 双视图同步显示医学图像切片
- 窗宽窗位调节以优化图像显示效果
- 鼠标点击标注关键点
- 滚轮缩放图像
- 切片导航控制

适用于医学图像分析、病灶标注、血管标记等场景。

作者：[作者名]
创建时间：[日期]
版本：1.0
"""

from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                             QLabel, QSlider, QSpinBox)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QBrush, QImage
from PyQt5.QtCore import Qt, QPoint
import numpy as np
import sys


class ClickableLabel(QLabel):
    """
    可点击的图像标签组件
    
    支持鼠标点击标注和图像缩放显示的 QLabel 扩展组件。
    能够在图像上绘制标记点，并支持与关联标签的同步操作。
    """
    
    def __init__(self, pixmap, parent=None):
        """
        初始化可点击标签
        
        Args:
            pixmap (QPixmap): 要显示的图像
            parent (QWidget, optional): 父级组件
        """
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.displayed_pixmap = pixmap
        self.setPixmap(self.displayed_pixmap)
        self.setStyleSheet("background-color: #000000;")
        self.click_points = []                  # 存储点击标记点的坐标列表
        self.linked_label = None                # 关联的标签组件（用于同步操作）
        self.scale_factor = 1.0                 # 图像缩放因子
        self.offset = QPoint(0, 0)              # 图像偏移量

    def mousePressEvent(self, event):
        """
        处理鼠标按下事件，在图像上添加标记点
        
        当用户左键点击图像时，计算相对于原始图像的坐标并添加到标记点列表，
        同时同步到关联标签上。
        
        Args:
            event (QMouseEvent): 鼠标事件对象
        """
        if event.button() == Qt.LeftButton:
            # 计算相对于原始图像的坐标（考虑缩放和偏移）
            x = (event.pos().x() - self.offset.x()) / self.scale_factor
            y = (event.pos().y() - self.offset.y()) / self.scale_factor
            self.click_points.append(QPoint(int(x), int(y)))

            # 如果有关联标签，同步添加标记点
            if self.linked_label:
                self.linked_label.click_points.append(QPoint(int(x), int(y)))

            print(f"标记点坐标: ({x}, {y})")
            self.update()
            # 更新关联标签显示
            if self.linked_label:
                self.linked_label.update()

    def paintEvent(self, event):
        """
        处理绘图事件，绘制图像和标记点
        
        绘制原始图像以及所有标记点，标记点会根据当前缩放因子进行位置调整。
        
        Args:
            event (QPaintEvent): 绘图事件对象
        """
        super().paintEvent(event)

        painter = QPainter(self)
        pen = QPen(Qt.red)
        brush = QBrush(Qt.red)
        painter.setPen(pen)
        painter.setBrush(brush)

        # 绘制所有标记点（考虑缩放和偏移）
        for point in self.click_points:
            display_x = int(point.x() * self.scale_factor + self.offset.x())
            display_y = int(point.y() * self.scale_factor + self.offset.y())
            painter.drawEllipse(QPoint(display_x, display_y), 5, 5)


class ImageAnnotationDialog(QDialog):
    """
    双视图图像标注对话框
    
    提供双视图同步标注功能的主对话框组件，支持医学图像序列的浏览、
    标注和参数调节。
    """
    
    def __init__(self, image_series1, image_series2, title="图像标注工具", parent=None):
        """
        初始化图像标注对话框
        
        Args:
            image_series1 (list): 第一组医学图像序列数据
            image_series2 (list): 第二组医学图像序列数据
            title (str): 窗口标题
            parent (QWidget, optional): 父级组件
        """
        super().__init__(parent)
        self.image_series1 = image_series1      # 第一组图像序列
        self.image_series2 = image_series2      # 第二组图像序列
        self.current_index = 0                  # 当前显示的切片索引
        self.window_width = 700                 # 窗宽（Window Width）
        self.window_center = 350                # 窗位（Window Center）

        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1200, 700)
        self.setWindowFlags(Qt.Window | Qt.WindowMaximizeButtonHint |
                            Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        # 初始化用户界面
        self.init_ui()

    def init_ui(self):
        """初始化用户界面布局和控件"""
        # 主布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # 图像显示区域布局
        self.image_layout = QHBoxLayout()
        self.image_layout.setSpacing(20)

        # 创建两个可点击的标签用于显示图像
        self.image1_label = ClickableLabel(self.array_to_pixmap(self.image_series1[0]))
        self.image1_label.setStyleSheet("background-color: #000000; border: 1px solid #2979ff;")

        self.image2_label = ClickableLabel(self.array_to_pixmap(self.image_series2[0]))
        self.image2_label.setStyleSheet("background-color: #000000; border: 1px solid #2979ff;")

        # 关联两个标签，使点击一个时另一个也显示标记
        self.image1_label.linked_label = self.image2_label
        self.image2_label.linked_label = self.image1_label

        self.image_layout.addWidget(self.image1_label)
        self.image_layout.addWidget(self.image2_label)
        self.main_layout.addLayout(self.image_layout)

        # 控制区域布局
        self.control_layout = QHBoxLayout()

        # 切片导航控件
        self.slice_label = QLabel(f"切片: {self.current_index + 1}/{len(self.image_series1)}")
        self.slice_label.setStyleSheet("color: #00c6ff; font-weight: bold;")

        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(len(self.image_series1) - 1)
        self.slice_slider.setValue(0)
        self.slice_slider.setStyleSheet("""
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

        self.slice_spinbox = QSpinBox()
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(len(self.image_series1) - 1)
        self.slice_spinbox.setValue(0)
        self.slice_spinbox.setStyleSheet("""
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

        # 添加控件到控制布局
        self.control_layout.addWidget(self.slice_label)
        self.control_layout.addWidget(self.slice_slider)
        self.control_layout.addWidget(self.slice_spinbox)
        self.main_layout.addLayout(self.control_layout)

        # 连接信号与槽函数
        self.slice_slider.valueChanged.connect(self.change_slice)
        self.slice_spinbox.valueChanged.connect(self.change_slice)

    def array_to_pixmap(self, array):
        """
        将numpy数组转换为QPixmap图像对象
        
        应用窗宽窗位调节算法，将医学图像数据转换为适合显示的灰度图像。
        
        Args:
            array (numpy.ndarray): 医学图像数据数组
            
        Returns:
            QPixmap: 转换后的图像对象
        """
        # 应用窗宽窗位算法调整图像对比度和亮度
        min_val = self.window_center - self.window_width / 2
        max_val = self.window_center + self.window_width / 2
        # 裁剪像素值到窗宽窗位范围内
        rescaled = np.clip(array, min_val, max_val)
        # 线性映射到0-255灰度范围
        rescaled = ((rescaled - min_val) / self.window_width) * 255
        rescaled = rescaled.astype(np.uint8)

        height, width = rescaled.shape
        qt_image = QImage(rescaled.data, width, height, width, QImage.Format_Grayscale8)
        return QPixmap.fromImage(qt_image)

    def change_slice(self, value):
        """
        切换当前显示的图像切片
        
        当用户通过滑块或数字框切换切片时调用此方法，更新两个视图的显示内容。
        
        Args:
            value (int): 新的切片索引
        """
        self.current_index = value
        self.slice_label.setText(f"切片: {self.current_index + 1}/{len(self.image_series1)}")
        self.slice_slider.setValue(value)
        self.slice_spinbox.setValue(value)

        # 清除之前的标记点并重置缩放
        self.image1_label.click_points = []
        self.image2_label.click_points = []
        self.image1_label.scale_factor = 1.0
        self.image2_label.scale_factor = 1.0

        # 生成新切片的图像
        pixmap1 = self.array_to_pixmap(self.image_series1[self.current_index])
        pixmap2 = self.array_to_pixmap(self.image_series2[self.current_index])

        # 更新标签显示
        self.image1_label.original_pixmap = pixmap1
        self.image2_label.original_pixmap = pixmap2
        self.image1_label.setPixmap(pixmap1)
        self.image2_label.setPixmap(pixmap2)

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，实现图像缩放功能
        
        根据滚轮滚动方向对图像进行放大或缩小，并同步两个视图的缩放状态。
        
        Args:
            event (QWheelEvent): 鼠标滚轮事件对象
        """
        scale_factor = 1.1                      # 缩放因子
        delta = event.angleDelta().y()          # 获取滚轮滚动角度
        mouse_pos = event.pos()                 # 获取鼠标位置

        # 确定当前操作的标签（根据鼠标位置判断）
        active_label = None
        if self.image1_label.geometry().contains(mouse_pos):
            active_label = self.image1_label
        elif self.image2_label.geometry().contains(mouse_pos):
            active_label = self.image2_label

        if not active_label:
            return

        # 计算新的缩放因子
        current_scale = active_label.scale_factor
        new_scale = current_scale * (scale_factor if delta > 0 else 1 / scale_factor)

        # 限制缩放范围在0.1到10.0之间
        new_scale = max(0.1, min(new_scale, 10.0))

        # 应用缩放到当前标签
        self.scale_image(active_label, new_scale)

        # 同步缩放另一个图像保持视图一致性
        if active_label == self.image1_label:
            self.scale_image(self.image2_label, new_scale)
        else:
            self.scale_image(self.image1_label, new_scale)

    def scale_image(self, label, new_scale):
        """
        缩放指定标签中的图像显示
        
        根据新的缩放因子重新绘制图像，并保持图像在标签中的居中显示。
        
        Args:
            label (ClickableLabel): 需要缩放的标签组件
            new_scale (float): 新的缩放因子
        """
        if not label.original_pixmap:
            return

        label.scale_factor = new_scale

        # 计算缩放后的图像尺寸
        new_width = int(label.original_pixmap.width() * new_scale)
        new_height = int(label.original_pixmap.height() * new_scale)

        # 应用缩放变换
        scaled_pixmap = label.original_pixmap.scaled(
            new_width, new_height,
            Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        # 计算居中显示的偏移量
        new_offset_x = (label.width() - scaled_pixmap.width()) // 2
        new_offset_y = (label.height() - scaled_pixmap.height()) // 2
        label.offset = QPoint(new_offset_x, new_offset_y)

        # 创建带偏移的画布并绘制缩放后的图像
        canvas = QPixmap(label.size())
        canvas.fill(Qt.transparent)
        painter = QPainter(canvas)
        painter.drawPixmap(QPoint(new_offset_x, new_offset_y), scaled_pixmap)
        painter.end()

        label.setPixmap(canvas)
        label.update()

    def get_marked_points(self):
        """
        获取所有标记点的坐标信息
        
        返回当前视图中所有标记点的坐标，包括切片索引和像素坐标。
        
        Returns:
            list: 标记点坐标列表，格式为 [[slice_index, x, y], ...]
        """
        marked_points = []
        for point in self.image1_label.click_points:
            marked_points.append([self.current_index, point.x(), point.y()])
        return marked_points

    def closeEvent(self, event):
        """
        处理窗口关闭事件，输出标记点数据
        
        在窗口关闭前打印所有标记点信息，便于后续处理和分析。
        
        Args:
            event (QCloseEvent): 窗口关闭事件对象
        """
        print("标记点数据:", self.get_marked_points())
        super().closeEvent(event)


# 示例用法
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 创建示例数据 (随机生成一些图像)
    num_slices = 10
    image_size = 256
    series1 = [np.random.randint(0, 1000, (image_size, image_size), dtype=np.int16) for _ in range(num_slices)]
    series2 = [np.random.randint(0, 1000, (image_size, image_size), dtype=np.int16) for _ in range(num_slices)]

    dialog = ImageAnnotationDialog(series1, series2, "双图像标注工具")
    dialog.show()
    sys.exit(app.exec_())