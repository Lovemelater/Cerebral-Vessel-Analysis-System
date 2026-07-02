import sys
import os
import vtk
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider, QSpinBox, QPushButton, QFileDialog, QDialog, QRadioButton, QDialogButtonBox, QButtonGroup, QCheckBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage,QColor
from basicfunction import load_mha
import numpy as np
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class MIPViewer(QWidget):
    def __init__(self, background_mha_path=None, slice_index=0, slice_orientation=''):
        super().__init__()
        
        self.background_mha_path = background_mha_path
        self.foreground_mha_path = None  # 前景文件1路径
        self.foreground2_mha_path = None  # 前景文件2路径
        self.slice_index = slice_index
        self.slice_orientation = slice_orientation
        
        # 前景文件显示控制
        self.show_foreground1 = True  # 控制前景文件1显示
        self.show_foreground2 = True  # 控制前景文件2显示
        
        # 初始化窗宽窗位参数
        self.window_width = 700
        self.window_center = 350
        
        # 初始化切片参数（切片数量）
        self.qie_pian_value = 0
        
        # 初始化TS参数（最大密度投影范围）
        self.ts_value = 0
        
        # 初始化标注透明度参数
        self.overlay_alpha = 1.0  # 默认完全不透明
        # 加载数据
        if self.background_mha_path and os.path.exists(self.background_mha_path):
            self.data, self.origin, self.spacing = load_mha(self.background_mha_path)
        else:
            # 创建测试数据
            # 修改前: self.data = np.random.randint(0, 1000, (100, 100, 100), dtype=np.uint16)
            self.data = np.zeros((100, 100, 100), dtype=np.uint16)
            self.origin = (0, 0, 0)
            self.spacing = (1, 1, 1)
        
        # 加载前景数据（血管标注）
        self.foreground_data = None
        self.foreground2_data = None
        if self.foreground_mha_path and os.path.exists(self.foreground_mha_path):
            self.foreground_data, _, _ = load_mha(self.foreground_mha_path)
            # 确保前景和背景图像尺寸一致
            if self.foreground_data.shape != self.data.shape:
                raise ValueError("前景和背景MHA文件的尺寸不一致")
                
        if self.foreground2_mha_path and os.path.exists(self.foreground2_mha_path):
            self.foreground2_data, _, _ = load_mha(self.foreground2_mha_path)
            # 确保前景2和背景图像尺寸一致
            if self.foreground2_data.shape != self.data.shape:
                raise ValueError("前景文件2和背景MHA文件的尺寸不一致")
        
        # 根据方向确定切片数量
        if self.slice_orientation == 'axial':
            self.max_slices = self.data.shape[0]
        elif self.slice_orientation == 'coronal':
            self.max_slices = self.data.shape[1]
        elif self.slice_orientation == 'sagittal':
            self.max_slices = self.data.shape[2]
        else:
            self.max_slices = self.data.shape[0]
        
        self.qie_pian_value = min(max(0, self.slice_index), max(0, self.max_slices - 1))
        
        self.setup_ui()
        self.render_mip()

    def setup_ui(self):
        """设置UI布局"""
        self.setWindowTitle("脑血管MRA分割与可视化系统 - 最大密度投影")
        self.resize(1000, 600)
        self.setStyleSheet("background-color: #121212;")
        
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 左侧控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_panel.setFixedWidth(400)
        control_panel.setStyleSheet("background-color: #000000; border-radius: 8px;")
        
        # 添加标题
        title_label = QLabel("最大密度投影")
        title_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFixedHeight(40)
        control_layout.addWidget(title_label)
        control_layout.addSpacing(10)

        # 创建一个水平布局用于放置"背景文件"和"切面方向选择"按钮
        top_buttons_layout = QHBoxLayout()
        top_buttons_layout.setSpacing(10)
        
        # 添加背景文件选择按钮
        self.background_button = QPushButton("背景文件")
        self.background_button.setFixedHeight(30)
        self.background_button.setFixedWidth(165)  # 调整宽度以适应同行布局
        self.background_button.setStyleSheet("""
            QPushButton {
                background-color: #3daee9; 
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF8E8E;
            }
            QPushButton:pressed {
                background-color: #CC5555;
            }
        """)
        top_buttons_layout.addWidget(self.background_button)
        self.background_button.clicked.connect(self.select_background_file)
        
        # 添加切面方向选择按钮
        self.orientation_button = QPushButton("切面方向选择")
        self.orientation_button.setFixedHeight(30)
        self.orientation_button.setFixedWidth(165)  # 调整宽度以适应同行布局
        self.orientation_button.setStyleSheet("""
            QPushButton {
                background-color:#3daee9; 
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFE194;
            }
            QPushButton:pressed {
                background-color: #CCB152;
            }
        """)
        top_buttons_layout.addWidget(self.orientation_button)
        self.orientation_button.clicked.connect(self.select_orientation)
        
        # 将水平布局添加到控制面板布局中
        control_layout.addLayout(top_buttons_layout)
        
        # 在"背景文件"和"切片方向选择"按钮布局与前景文件按钮布局之间添加垂直间距
        control_layout.addSpacing(8)
        
        # 创建一个水平布局用于放置前景文件按钮
        foreground_buttons_layout = QHBoxLayout()
        foreground_buttons_layout.setSpacing(10)
        
        # 添加前景文件1选择按钮
        self.foreground_button = QPushButton("前景文件1")
        self.foreground_button.setFixedHeight(30)
        self.foreground_button.setFixedWidth(165)
        self.foreground_button.setStyleSheet("""
            QPushButton {
                background-color:#3daee9; 
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7EDDD6;
            }
            QPushButton:pressed {
                background-color: #3BA8A0;
            }
        """)
        foreground_buttons_layout.addWidget(self.foreground_button)
        self.foreground_button.clicked.connect(self.select_foreground_file)
        
        # 添加前景文件2选择按钮
        self.foreground2_button = QPushButton("前景文件2")
        self.foreground2_button.setFixedHeight(30)
        self.foreground2_button.setFixedWidth(165)
        self.foreground2_button.setStyleSheet("""
            QPushButton {
                background-color:#3daee9; 
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FFE666;
            }
            QPushButton:pressed {
                background-color: #CCAF31;
            }
        """)
        foreground_buttons_layout.addWidget(self.foreground2_button)
        self.foreground2_button.clicked.connect(self.select_foreground2_file)
        
        # 将前景文件按钮布局添加到控制面板布局中
        control_layout.addLayout(foreground_buttons_layout)
        
        # 在前景文件按钮布局和前景文件复选框布局之间添加垂直间距
        control_layout.addSpacing(15)

        # 添加前景文件显示控制的复选框
        self.foreground1_checkbox = QCheckBox("前景文件1")
        self.foreground1_checkbox.setChecked(True)  # 默认选中
        self.foreground1_checkbox.setStyleSheet("""
            QCheckBox {
                color: #4ECDC4;
                font-weight: bold;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555;
                background-color: #222;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #4ECDC4;
                background-color: #4ECDC4;
            }
        """)
        self.foreground1_checkbox.stateChanged.connect(self.on_foreground1_visibility_changed)
        
        self.foreground2_checkbox = QCheckBox("前景文件2")
        self.foreground2_checkbox.setChecked(True)  # 默认选中
        self.foreground2_checkbox.setStyleSheet("""
            QCheckBox {
                color: #FFD93D;
                font-weight: bold;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #555;
                background-color: #222;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #FFD93D;
                background-color: #FFD93D;
            }
        """)
        self.foreground2_checkbox.stateChanged.connect(self.on_foreground2_visibility_changed)
        
        # 创建水平布局放置两个复选框，并居中对齐
        checkbox_layout = QHBoxLayout()
        checkbox_layout.setSpacing(20)
        checkbox_layout.addStretch()  # 添加左侧弹性空间
        checkbox_layout.addWidget(self.foreground1_checkbox)
        checkbox_layout.addWidget(self.foreground2_checkbox)
        checkbox_layout.addStretch()  # 添加右侧弹性空间
        
        # 将复选框布局添加到控制面板布局中
        control_layout.addLayout(checkbox_layout)

        # 增加间距
        control_layout.addSpacing(20)
        
        # 窗宽控制
        window_width_layout = QHBoxLayout()
        window_width_layout.setSpacing(20)
        window_width_layout.setContentsMargins(20, 0, 15, 0)
        self.window_width_label = QLabel(" 窗宽")
        self.window_width_label.setFixedSize(61, 20)
        self.window_width_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        window_width_layout.addWidget(self.window_width_label)
        
        self.window_width_slider = QSlider(Qt.Horizontal)
        self.window_width_slider.setFixedSize(150, 20)
        self.window_width_slider.setMinimum(1)
        self.window_width_slider.setMaximum(4096)
        self.window_width_slider.setValue(self.window_width)
        self.window_width_slider.setStyleSheet("""
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
        window_width_layout.addWidget(self.window_width_slider)
        
        self.window_width_spinbox = QSpinBox()
        self.window_width_spinbox.setMinimum(1)
        self.window_width_spinbox.setMaximum(4096)
        self.window_width_spinbox.setValue(self.window_width)
        self.window_width_spinbox.setFixedSize(50, 25)
        self.window_width_spinbox.setStyleSheet("""
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
        window_width_layout.addWidget(self.window_width_spinbox)
        
        control_layout.addLayout(window_width_layout)
        
        # 窗位控制
        window_center_layout = QHBoxLayout()
        window_center_layout.setSpacing(20)
        window_center_layout.setContentsMargins(20, 0, 15, 0)
        self.window_center_label = QLabel(" 窗位")
        self.window_center_label.setFixedSize(61, 20)
        self.window_center_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        window_center_layout.addWidget(self.window_center_label)
        
        self.window_center_slider = QSlider(Qt.Horizontal)
        self.window_center_slider.setFixedSize(150, 20)
        self.window_center_slider.setMinimum(-2048)
        self.window_center_slider.setMaximum(2047)
        self.window_center_slider.setValue(self.window_center)
        self.window_center_slider.setStyleSheet("""
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
        window_center_layout.addWidget(self.window_center_slider)
        
        self.window_center_spinbox = QSpinBox()
        self.window_center_spinbox.setMinimum(-2048)
        self.window_center_spinbox.setMaximum(2047)
        self.window_center_spinbox.setValue(self.window_center)
        self.window_center_spinbox.setFixedSize(50, 25)
        self.window_center_spinbox.setStyleSheet("""
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
        window_center_layout.addWidget(self.window_center_spinbox)
        
        control_layout.addLayout(window_center_layout)
        
        # 切片控制（切片索引）
        qie_pian_layout = QHBoxLayout()
        qie_pian_layout.setSpacing(20)
        qie_pian_layout.setContentsMargins(20, 0, 15, 0)
        
        self.qie_pian_label = QLabel(" 切片")
        self.qie_pian_label.setFixedSize(61, 20)
        self.qie_pian_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        qie_pian_layout.addWidget(self.qie_pian_label)
        
        self.qie_pian_slider = QSlider(Qt.Horizontal)
        self.qie_pian_slider.setFixedSize(150, 20)
        self.qie_pian_slider.setMinimum(0)
        self.qie_pian_slider.setMaximum(max(0, self.max_slices - 1))
        self.qie_pian_slider.setValue(self.qie_pian_value)
        self.qie_pian_slider.setStyleSheet("""
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
        qie_pian_layout.addWidget(self.qie_pian_slider)
        
        self.qie_pian_spinbox = QSpinBox()
        self.qie_pian_spinbox.setMinimum(0)
        self.qie_pian_spinbox.setMaximum(max(0, self.max_slices - 1))
        self.qie_pian_spinbox.setValue(self.qie_pian_value)
        self.qie_pian_spinbox.setFixedSize(50, 25)
        self.qie_pian_spinbox.setStyleSheet("""
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
        qie_pian_layout.addWidget(self.qie_pian_spinbox)
        
        control_layout.addLayout(qie_pian_layout)
        
        # TS控制（最大密度投影范围）
        ts_layout = QHBoxLayout()
        ts_layout.setSpacing(20)
        ts_layout.setContentsMargins(20, 0, 15, 0)
        
        self.ts_label = QLabel("  TS")
        self.ts_label.setFixedSize(61, 20)
        self.ts_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        ts_layout.addWidget(self.ts_label)
        
        self.ts_slider = QSlider(Qt.Horizontal)
        self.ts_slider.setFixedSize(150, 20)
        self.ts_slider.setMinimum(0)
        self.ts_slider.setMaximum(max(0, self.max_slices - 1))
        self.ts_slider.setValue(self.ts_value)
        self.ts_slider.setStyleSheet("""
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
        ts_layout.addWidget(self.ts_slider)
        
        self.ts_spinbox = QSpinBox()
        self.ts_spinbox.setMinimum(0)
        self.ts_spinbox.setMaximum(max(0, self.max_slices - 1))
        self.ts_spinbox.setValue(self.ts_value)
        self.ts_spinbox.setFixedSize(50, 25)
        self.ts_spinbox.setStyleSheet("""
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
        ts_layout.addWidget(self.ts_spinbox)
        
        control_layout.addLayout(ts_layout)
        
        # 标注透明度控制
        overlay_layout = QHBoxLayout()
        overlay_layout.setSpacing(20)
        overlay_layout.setContentsMargins(20, 0, 15, 0)
        
        self.overlay_label = QLabel("透明度")
        self.overlay_label.setFixedSize(61, 20)
        self.overlay_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        overlay_layout.addWidget(self.overlay_label)
        
        self.overlay_slider = QSlider(Qt.Horizontal)
        self.overlay_slider.setFixedSize(150, 20)
        self.overlay_slider.setMinimum(0)
        self.overlay_slider.setMaximum(100)
        self.overlay_slider.setValue(100)
        self.overlay_slider.setStyleSheet("""
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
        overlay_layout.addWidget(self.overlay_slider)
        
        self.overlay_spinbox = QSpinBox()
        self.overlay_spinbox.setMinimum(0)
        self.overlay_spinbox.setMaximum(100)
        self.overlay_spinbox.setValue(100)
        self.overlay_spinbox.setFixedSize(50, 25)
        self.overlay_spinbox.setStyleSheet("""
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
        overlay_layout.addWidget(self.overlay_spinbox)
        
        control_layout.addLayout(overlay_layout)
        
        # 添加弹性空间
        control_layout.addStretch()
        
        # 右侧图像显示区域
        self.image_label = QLabel()
        self.image_label.setStyleSheet("background-color: #000000; border: 1px solid #2979ff; border-radius: 6px;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumSize(512, 512)
        
        # 添加控件到主布局
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.image_label, 1)
        
        # 连接信号
        self.window_width_slider.valueChanged.connect(self.window_width_spinbox.setValue)
        self.window_width_spinbox.valueChanged.connect(self.window_width_slider.setValue)
        self.window_width_slider.valueChanged.connect(self.on_window_width_changed)
        
        self.window_center_slider.valueChanged.connect(self.window_center_spinbox.setValue)
        self.window_center_spinbox.valueChanged.connect(self.window_center_slider.setValue)
        self.window_center_slider.valueChanged.connect(self.on_window_center_changed)
        
        self.qie_pian_slider.valueChanged.connect(self.qie_pian_spinbox.setValue)
        self.qie_pian_spinbox.valueChanged.connect(self.qie_pian_slider.setValue)
        self.qie_pian_slider.valueChanged.connect(self.on_qie_pian_changed)
        
        self.ts_slider.valueChanged.connect(self.ts_spinbox.setValue)
        self.ts_spinbox.valueChanged.connect(self.ts_slider.setValue)
        self.ts_slider.valueChanged.connect(self.on_ts_changed)
        
        # 连接标注透明度信号
        self.overlay_slider.valueChanged.connect(self.overlay_spinbox.setValue)
        self.overlay_spinbox.valueChanged.connect(self.overlay_slider.setValue)
        self.overlay_slider.valueChanged.connect(self.on_overlay_changed)

    def array_to_pixmap(self, array):
        """将numpy数组转换为QPixmap"""
        # 应用窗宽窗位
        min_val = self.window_center - self.window_width / 2
        max_val = self.window_center + self.window_width / 2
        
        # 应用窗宽窗位调整
        rescaled = np.clip(array, min_val, max_val)
        rescaled = ((rescaled - min_val) / (max_val - min_val)) * 255
        rescaled = rescaled.astype(np.uint8)
        
        height, width = rescaled.shape
        qt_image = QImage(rescaled.data, width, height, width, QImage.Format_Grayscale8)
            
        return QPixmap.fromImage(qt_image)

    def setup_vtk_image_data(self):
        """设置图像数据"""
        # 确保qie_pian_value在有效范围内
        self.qie_pian_value = max(0, min(self.qie_pian_value, self.max_slices - 1))
        
        # 处理背景数据
        if self.slice_orientation == 'axial':
            # 在轴向上进行最大密度投影
            start_slice = max(0, self.qie_pian_value - self.ts_value)
            end_slice = min(self.data.shape[0], self.qie_pian_value + self.ts_value + 1)
            background_slice = np.max(self.data[start_slice:end_slice, :, :], axis=0)
                
        elif self.slice_orientation == 'coronal':
            # 在冠状面上进行最大密度投影
            start_slice = max(0, self.qie_pian_value - self.ts_value)
            end_slice = min(self.data.shape[1], self.qie_pian_value + self.ts_value + 1)
            # 与xiu_biaozu.py保持一致的处理方式
            transposed_data = np.flip(np.transpose(self.data, (1, 0, 2)), axis=(1, 0))
            background_slice = np.max(transposed_data[start_slice:end_slice, :, :], axis=0)
                
        elif self.slice_orientation == 'sagittal':
            # 在矢状面上进行最大密度投影
            start_slice = max(0, self.qie_pian_value - self.ts_value)
            end_slice = min(self.data.shape[2], self.qie_pian_value + self.ts_value + 1)
            # 与xiu_biaozu.py保持一致的处理方式
            transposed_data = np.transpose(self.data, (2, 0, 1))
            flipped_data = np.flip(transposed_data, axis=(0, 1))
            background_slice = np.max(flipped_data[start_slice:end_slice, :, :], axis=0)
        else:
            # 默认在轴向上进行最大密度投影
            start_slice = max(0, self.qie_pian_value - self.ts_value)
            end_slice = min(self.data.shape[0], self.qie_pian_value + self.ts_value + 1)
            background_slice = np.max(self.data[start_slice:end_slice, :, :], axis=0)
        
        # 创建RGB图像
        rgb_image = np.zeros((background_slice.shape[0], background_slice.shape[1], 3), dtype=np.uint8)
        
        # 应用窗宽窗位到背景数据
        min_val = self.window_center - self.window_width / 2
        max_val = self.window_center + self.window_width / 2
        adjusted_background = np.clip(background_slice, min_val, max_val)
        adjusted_background = ((adjusted_background - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        
        # 设置RGB通道
        rgb_image[:, :, 0] = adjusted_background  # 红色通道
        rgb_image[:, :, 1] = adjusted_background  # 绿色通道
        rgb_image[:, :, 2] = adjusted_background  # 蓝色通道
        
        # 如果有前景数据1，且前景文件1显示复选框被选中，则处理前景数据1
        if self.foreground_data is not None and self.show_foreground1:
            if self.slice_orientation == 'axial':
                # 在轴向上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground_data.shape[0], self.qie_pian_value + self.ts_value + 1)
                foreground_slice = np.max(self.foreground_data[start_slice:end_slice, :, :], axis=0)
                    
            elif self.slice_orientation == 'coronal':
                # 在冠状面上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground_data.shape[1], self.qie_pian_value + self.ts_value + 1)
                # 与xiu_biaozu.py保持一致的处理方式
                transposed_data = np.flip(np.transpose(self.foreground_data, (1, 0, 2)), axis=(1, 0))
                foreground_slice = np.max(transposed_data[start_slice:end_slice, :, :], axis=0)
                    
            elif self.slice_orientation == 'sagittal':
                # 在矢状面上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground_data.shape[2], self.qie_pian_value + self.ts_value + 1)
                # 与xiu_biaozu.py保持一致的处理方式
                transposed_data = np.transpose(self.foreground_data, (2, 0, 1))
                flipped_data = np.flip(transposed_data, axis=(0, 1))
                foreground_slice = np.max(flipped_data[start_slice:end_slice, :, :], axis=0)
            else:
                # 默认在轴向上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground_data.shape[0], self.qie_pian_value + self.ts_value + 1)
                foreground_slice = np.max(self.foreground_data[start_slice:end_slice, :, :], axis=0)
            
            # 将前景数据1叠加到背景数据上（根据透明度显示前景）
            # 将前景区域标记为红色，并应用透明度
            foreground_mask = foreground_slice > 0
            if self.overlay_alpha > 0:
                # 蓝色和绿色通道：背景 * (1 - alpha)
                rgb_image[foreground_mask, 1] = (
                    rgb_image[foreground_mask, 0] * (1 - self.overlay_alpha)
                ).astype(np.uint8)
                rgb_image[foreground_mask, 2] = (
                    rgb_image[foreground_mask, 1] * (1 - self.overlay_alpha)
                ).astype(np.uint8)
                
                # 红色通道：背景 * (1 - alpha) + 255 * alpha
                rgb_image[foreground_mask, 0] = (
                    rgb_image[foreground_mask, 2] * (1 - self.overlay_alpha) + 
                    255 * self.overlay_alpha
                ).astype(np.uint8)
        
        # 如果有前景数据2，且前景文件2显示复选框被选中，则处理前景数据2
        if self.foreground2_data is not None and self.show_foreground2:
            if self.slice_orientation == 'axial':
                # 在轴向上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground2_data.shape[0], self.qie_pian_value + self.ts_value + 1)
                foreground2_slice = np.max(self.foreground2_data[start_slice:end_slice, :, :], axis=0)
                    
            elif self.slice_orientation == 'coronal':
                # 在冠状面上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground2_data.shape[1], self.qie_pian_value + self.ts_value + 1)
                # 与xiu_biaozu.py保持一致的处理方式
                transposed_data = np.flip(np.transpose(self.foreground2_data, (1, 0, 2)), axis=(1, 0))
                foreground2_slice = np.max(transposed_data[start_slice:end_slice, :, :], axis=0)
                    
            elif self.slice_orientation == 'sagittal':
                # 在矢状面上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground2_data.shape[2], self.qie_pian_value + self.ts_value + 1)
                # 与xiu_biaozu.py保持一致的处理方式
                transposed_data = np.transpose(self.foreground2_data, (2, 0, 1))
                flipped_data = np.flip(transposed_data, axis=(0, 1))
                foreground2_slice = np.max(flipped_data[start_slice:end_slice, :, :], axis=0)
            else:
                # 默认在轴向上进行最大密度投影
                start_slice = max(0, self.qie_pian_value - self.ts_value)
                end_slice = min(self.foreground2_data.shape[0], self.qie_pian_value + self.ts_value + 1)
                foreground2_slice = np.max(self.foreground2_data[start_slice:end_slice, :, :], axis=0)
            
            # 将前景数据2叠加到背景数据上（根据透明度显示前景）
            # 将前景2区域标记为蓝色，并应用透明度
            foreground2_mask = foreground2_slice > 0
            if self.overlay_alpha > 0:
                # 红色和绿色通道：背景 * (1 - alpha)
                rgb_image[foreground2_mask, 0] = (
                    rgb_image[foreground2_mask, 0] * (1 - self.overlay_alpha)
                ).astype(np.uint8)
                rgb_image[foreground2_mask, 1] = (
                    rgb_image[foreground2_mask, 1] * (1 - self.overlay_alpha)
                ).astype(np.uint8)
                
                # 蓝色通道：背景 * (1 - alpha) + 255 * alpha
                rgb_image[foreground2_mask, 2] = (
                    rgb_image[foreground2_mask, 2] * (1 - self.overlay_alpha) + 
                    255 * self.overlay_alpha
                ).astype(np.uint8)
        
        return rgb_image
    
    def select_background_file(self):
        """选择背景文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择背景文件", 
            "", 
            "MHA Files (*.mha);;All Files (*)"
        )
        
        if file_path:
            self.background_mha_path = file_path
            # 重新加载数据
            if os.path.exists(self.background_mha_path):
                self.data, self.origin, self.spacing = load_mha(self.background_mha_path)
                # 根据方向重新确定切片数量
                if self.slice_orientation == 'axial':
                    self.max_slices = self.data.shape[0]
                elif self.slice_orientation == 'coronal':
                    self.max_slices = self.data.shape[1]
                elif self.slice_orientation == 'sagittal':
                    self.max_slices = self.data.shape[2]
                else:
                    self.max_slices = self.data.shape[0]
                
                # 更新滑块范围
                self.qie_pian_slider.setMaximum(max(0, self.max_slices - 1))
                self.qie_pian_spinbox.setMaximum(max(0, self.max_slices - 1))
                self.ts_slider.setMaximum(max(0, self.max_slices - 1))
                self.ts_spinbox.setMaximum(max(0, self.max_slices - 1))
                
                # 重新渲染
                self.render_mip()

    def select_orientation(self):
        """选择切面方向"""
        dialog = OrientationDialog(self.slice_orientation, self)
        if dialog.exec_() == QDialog.Accepted:
            selected_orientation = dialog.get_selected_orientation()
            if selected_orientation != self.slice_orientation:
                self.slice_orientation = selected_orientation
                # 重新计算切片数量
                if self.slice_orientation == 'axial':
                    self.max_slices = self.data.shape[0]
                elif self.slice_orientation == 'coronal':
                    self.max_slices = self.data.shape[1]
                elif self.slice_orientation == 'sagittal':
                    self.max_slices = self.data.shape[2]
                else:
                    self.max_slices = self.data.shape[0]
                
                # 更新滑块范围
                self.qie_pian_slider.setMaximum(max(0, self.max_slices - 1))
                self.qie_pian_spinbox.setMaximum(max(0, self.max_slices - 1))
                self.ts_slider.setMaximum(max(0, self.max_slices - 1))
                self.ts_spinbox.setMaximum(max(0, self.max_slices - 1))
                
                # 重新渲染
                self.render_mip()

    def select_foreground_file(self):
        """选择前景文件1"""
        # 检查是否已选择背景文件
        if not self.background_mha_path:
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请先选择背景文件")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #121212;
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #2979ff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00c6ff;
                }
            """)
            msg_box.exec_()
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择前景文件1", 
            "", 
            "MHA Files (*.mha);;All Files (*)"
        )
        
        if file_path:
            self.foreground_mha_path = file_path
            # 重新加载前景数据
            if os.path.exists(self.foreground_mha_path):
                self.foreground_data, _, _ = load_mha(self.foreground_mha_path)
                # 确保前景和背景图像尺寸一致
                if self.foreground_data.shape != self.data.shape:
                    raise ValueError("前景和背景MHA文件的尺寸不一致")
                
                # 勾选前景文件1复选框
                self.foreground1_checkbox.setChecked(True)
                
                # 重新渲染
                self.render_mip()

    def select_foreground2_file(self):
        """选择前景文件2"""
        # 检查是否已选择背景文件和前景文件1
        if not self.background_mha_path:
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请先选择背景文件")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #121212;
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #2979ff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00c6ff;
                }
            """)
            msg_box.exec_()
            return
            
        if not self.foreground_mha_path:
            from PyQt5.QtWidgets import QMessageBox
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("警告")
            msg_box.setText("请先选择前景文件1")
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #121212;
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 14px;
                }
                QPushButton {
                    background-color: #2979ff;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 6px 12px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #00c6ff;
                }
            """)
            msg_box.exec_()
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择前景文件2", 
            "", 
            "MHA Files (*.mha);;All Files (*)"
        )
        
        if file_path:
            self.foreground2_mha_path = file_path
            # 重新加载前景数据2
            if os.path.exists(self.foreground2_mha_path):
                self.foreground2_data, _, _ = load_mha(self.foreground2_mha_path)
                # 确保前景2和背景图像尺寸一致
                if self.foreground2_data.shape != self.data.shape:
                    raise ValueError("前景文件2和背景MHA文件的尺寸不一致")
                
                # 勾选前景文件2复选框
                self.foreground2_checkbox.setChecked(True)
                
                # 重新渲染
                self.render_mip()

    def on_foreground1_visibility_changed(self, state):
        """前景文件1显示/隐藏切换"""
        self.show_foreground1 = (state == Qt.Checked)
        self.render_mip()

    def on_foreground2_visibility_changed(self, state):
        """前景文件2显示/隐藏切换"""
        self.show_foreground2 = (state == Qt.Checked)
        self.render_mip()

    def render_mip(self):
        """渲染MIP"""
        # 获取处理后的图像数据
        image_data = self.setup_vtk_image_data()
        
        # 转换为QPixmap并显示
        if len(image_data.shape) == 3:  # RGB图像
            height, width, channels = image_data.shape
            qt_image = QImage(image_data.data, width, height, width * channels, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image)
        else:  # 灰度图像
            pixmap = self.array_to_pixmap(image_data)
        
        # 根据切面方向调整图像显示比例
        if self.slice_orientation == 'axial':
            # 横断面: spacing[1] (y) 和 spacing[2] (z)
            pixmap = self.scale_with_aspect(pixmap, self.spacing[2] / self.spacing[1])
        elif self.slice_orientation == 'coronal':
            # 冠状面: spacing[0] (x) 和 spacing[2] (z)
            pixmap = self.scale_with_aspect(pixmap, self.spacing[2] / self.spacing[0])
        elif self.slice_orientation == 'sagittal':
            # 矢状面: spacing[0] (x) 和 spacing[1] (y)
            pixmap = self.scale_with_aspect(pixmap, self.spacing[1] / self.spacing[0])
        
        self.image_label.setPixmap(pixmap)
        
        # 调整标签大小以适应图像
        self.image_label.setScaledContents(False)

    def scale_with_aspect(self, pixmap, aspect_ratio):
        """
        根据给定的宽高比缩放图像
        """
        label_width = self.image_label.width()
        label_height = self.image_label.height()
        
        # 计算保持比例的尺寸
        if label_width / label_height > aspect_ratio:
            # 控件更宽，以高度为准
            new_height = label_height
            new_width = int(label_height * aspect_ratio)
        else:
            # 控件更高，以宽度为准
            new_width = label_width
            new_height = int(label_width / aspect_ratio)
            
        return pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def on_window_width_changed(self, val):
        """窗宽变化回调"""
        try:
            self.window_width = val
            self.render_mip()
        except Exception as e:
            print(f"窗宽变化处理出错: {e}")

    def on_window_center_changed(self, val):
        """窗位变化回调"""
        try:
            self.window_center = val
            self.render_mip()
        except Exception as e:
            print(f"窗位变化处理出错: {e}")

    def on_qie_pian_changed(self, val):
        """切片变化回调"""
        try:
            self.qie_pian_value = max(0, min(val, self.max_slices - 1))
            self.render_mip()
        except Exception as e:
            print(f"切片变化处理出错: {e}")

    def on_ts_changed(self, val):
        """TS变化回调"""
        try:
            self.ts_value = max(0, min(val, self.max_slices - 1))
            self.render_mip()
        except Exception as e:
            print(f"TS变化处理出错: {e}")

    def on_overlay_changed(self, val):
        """标注透明度变化回调"""
        try:
            # 将0-100的值转换为0-1范围
            self.overlay_alpha = val / 100.0
            self.render_mip()
        except Exception as e:
            print(f"标注透明度变化处理出错: {e}")

    def resizeEvent(self, event):
        """窗口大小调整事件"""
        super().resizeEvent(event)
        # 当窗口大小改变时重新渲染
        self.render_mip()



class OrientationDialog(QDialog):
    """切面方向选择对话框"""
    def __init__(self, current_orientation, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择切面方向")
        self.setModal(True)
        self.setFixedSize(200, 150)
        self.setStyleSheet("""
            QDialog {
                background-color: #121212;
            }
            QRadioButton {
                color: #e1e1e1;
                font-size: 14px;
            }
            QDialogButtonBox QPushButton {
                background-color: #2979ff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 15px;
                font-weight: bold;
            }
            QDialogButtonBox QPushButton:hover {
                background-color: #00c6ff;
            }
        """)
        
        layout = QVBoxLayout()
        
        # 创建单选按钮
        self.axial_radio = QRadioButton("axial (横断面)")
        self.coronal_radio = QRadioButton("coronal (冠状面)")
        self.sagittal_radio = QRadioButton("sagittal (矢状面)")
        
        # 创建按钮组
        self.button_group = QButtonGroup()
        self.button_group.addButton(self.axial_radio, 0)
        self.button_group.addButton(self.coronal_radio, 1)
        self.button_group.addButton(self.sagittal_radio, 2)
        
        # 设置默认选中项
        if current_orientation == 'axial':
            self.axial_radio.setChecked(True)
        elif current_orientation == 'coronal':
            self.coronal_radio.setChecked(True)
        elif current_orientation == 'sagittal':
            self.sagittal_radio.setChecked(True)
        else:
            self.axial_radio.setChecked(True)
        
        # 添加控件到布局
        layout.addWidget(self.axial_radio)
        layout.addWidget(self.coronal_radio)
        layout.addWidget(self.sagittal_radio)
        
        # 添加确定和取消按钮
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def get_selected_orientation(self):
        """获取选中的方向"""
        if self.axial_radio.isChecked():
            return 'axial'
        elif self.coronal_radio.isChecked():
            return 'coronal'
        elif self.sagittal_radio.isChecked():
            return 'sagittal'
        return 'axial'
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 示例用法
    viewer = MIPViewer(
        slice_index=50,
        slice_orientation='axial'
    )
    viewer.show()
    exit_code = app.exec_()
    sys.exit(exit_code)