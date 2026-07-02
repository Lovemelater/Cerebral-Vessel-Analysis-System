"""
医学图像交互式标注组件

该组件实现了医学图像可视化和交互标注功能，支持以下特性：
医学图像显示：高质量渲染医学图像数据
交互式标注：通过鼠标点击进行病灶区域标记
坐标系统管理：处理原始图像坐标与显示坐标间的映射关系
多视图同步：实现多个视图间标注点的实时同步
图像缩放控制：通过鼠标滚轮实现图像无级缩放
可视化反馈：提供清晰的标注点视觉反馈

该组件是医学图像分析系统中用户交互的核心模块，
支持医生或研究人员进行精确的图像标注和分析工作，
为后续的图像处理和机器学习任务提供高质量的标注数据支撑。
"""

from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import  QPainter, QPen, QBrush
from PyQt5.QtCore import Qt, QPoint

class ClickableLabel(QLabel):
    """
    可交互的医学图像显示标签
    
    该类扩展了QLabel功能，提供了专业的医学图像交互能力：
    1. 高精度坐标映射：确保标注点在不同缩放级别下的准确性
    2. 多视图联动：支持正交视图间的标注同步
    3. 实时渲染：流畅的图像缩放和标注点绘制
    4. 用户友好：直观的交互反馈和视觉提示
    """
    
    def __init__(self, pixmap, parent=None):
        """
        初始化可交互图像标签
        
        Args:
            pixmap (QPixmap): 要显示的图像数据
            parent (QWidget, optional): 父级组件
        """
        super().__init__(parent)
        self.original_pixmap = pixmap  # 保存原始图像用于缩放计算，确保坐标映射精度
        self.displayed_pixmap = pixmap  # 当前显示的图像，用于屏幕渲染
        self.setStyleSheet("background-color: #000000;")  # 设置黑色背景以增强医学图像对比度
        self.click_points = []  # 存储点击的点（原始坐标），保持与图像数据坐标系一致
        self.linked_label = None  # 关联的另一个标签，用于实现多视图同步标注
        self.scale_factor = 1.0  # 当前缩放比例，1.0表示原始大小
        self.offset = QPoint(0, 0)  # 当前图像偏移量，用于居中显示
        
        # 初始设置图像显示
        self.update_displayed_pixmap()
        super().setPixmap(self.displayed_pixmap)

    def mousePressEvent(self, event):
        """
        处理鼠标按下事件，实现交互式标注功能
        
        该方法实现了精确的坐标映射机制，将屏幕坐标转换为图像原始坐标，
        确保在不同缩放级别下标注点位置的准确性，并支持多视图同步标注。
        """
        if event.button() == Qt.LeftButton:
            # 将屏幕坐标转换为原始图像坐标，消除缩放和偏移影响
            x = (event.pos().x() - self.offset.x()) / self.scale_factor
            y = (event.pos().y() - self.offset.y()) / self.scale_factor
            self.click_points.append(QPoint(int(x), int(y)))  # 存储原始坐标以保持精度

            # 如果存在关联标签，则同步标注点到其他视图
            if self.linked_label is not None:
                self.linked_label.click_points.append(QPoint(int(x), int(y)))

            print(f"点击坐标: ({x}, {y})")
            self.update()  # 更新标签以重绘标注点

            # 更新关联标签以同步显示标注点
            if self.linked_label:
                self.linked_label.update()  # 更新关联的标签以重绘

    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件实现图像无级缩放
        
        通过指数级缩放因子提供流畅的缩放体验，
        同时限制缩放范围以防止图像失真或性能问题
        """
        # 获取滚轮滚动的角度，正值表示向上滚动（放大）
        angle = event.angleDelta().y()
        
        # 根据滚轮方向调整缩放因子，1.1倍率提供平滑的缩放体验
        if angle > 0:
            self.scale_factor *= 1.1  # 放大图像
        else:
            self.scale_factor /= 1.1  # 缩小图像
            
        # 限制缩放范围在0.1倍到10倍之间，平衡显示效果和性能
        self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
        
        # 更新显示的图像和标注点位置
        self.update_displayed_pixmap()
        
        # 触发重绘以更新显示
        self.update()
        if self.linked_label:
            self.linked_label.update()

    def update_displayed_pixmap(self):
        """
        根据当前缩放因子更新显示图像
        
        该方法确保图像在不同缩放级别下保持高质量显示，
        并正确计算图像在标签中的居中位置
        """
        if self.original_pixmap.isNull():
            return
            
        # 计算新的尺寸，保持宽高比避免图像变形
        original_size = self.original_pixmap.size()
        new_width = int(original_size.width() * self.scale_factor)
        new_height = int(original_size.height() * self.scale_factor)
        
        # 使用平滑插值算法缩放图像，确保医学图像细节清晰
        scaled_pixmap = self.original_pixmap.scaled(
            new_width, new_height, 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        )
        
        # 更新显示的图像
        self.displayed_pixmap = scaled_pixmap
        
        # 计算居中偏移量，确保图像在标签中居中显示
        self.offset.setX((self.width() - new_width) // 2)
        self.offset.setY((self.height() - new_height) // 2)
        
        # 更新标签的 pixmap
        super().setPixmap(self.displayed_pixmap)

    def resizeEvent(self, event):
        """处理标签大小调整事件，确保图像始终正确居中显示"""
        super().resizeEvent(event)
        # 当标签大小改变时，重新计算图像位置以保持居中
        self.update_displayed_pixmap()

    def paintEvent(self, event):
        """
        处理绘制事件，实现标注点的实时渲染
        
        该方法在图像渲染完成后叠加绘制标注点，
        通过坐标变换确保标注点在不同缩放级别下的准确显示
        """
        super().paintEvent(event)  # 绘制原图像

        painter = QPainter(self)
        pen = QPen(Qt.red)  # 设置红色画笔以提供高对比度视觉反馈
        pen.setStyle(Qt.SolidLine)  # 设置为实线确保清晰显示
        brush = QBrush(Qt.red)  # 设置红色画刷用于填充标注点
        painter.setPen(pen)
        painter.setBrush(brush)

        # 绘制已存储的点击点（根据缩放比例和偏移量调整位置）
        # 实现从原始图像坐标到屏幕显示坐标的精确映射
        for point in self.click_points:
            display_x = int(point.x() * self.scale_factor + self.offset.x())
            display_y = int(point.y() * self.scale_factor + self.offset.y())
            painter.drawEllipse(QPoint(display_x, display_y), 3, 3)  # 绘制半径为3的红点，提供清晰可见的标注反馈
            
    def setPixmap(self, pixmap):
        """
        重写setPixmap方法以确保图像居中显示并重置缩放状态
        
        该方法在设置新图像时自动重置视图状态，
        确保用户获得一致的交互体验
        """
        self.original_pixmap = pixmap
        self.scale_factor = 1.0  # 重置缩放因子以显示完整图像
        self.update_displayed_pixmap()  # 更新显示的图像
        self.setAlignment(Qt.AlignCenter)  # 设置图像居中对齐