"""
processing_controls.py
处理控制组件，管理医学图像处理流程的用户交互界面

功能概述：
1. 文件管理：
   - 支持多种医学图像格式（.mhd, .mha, .nii等）的文件选择
   - 文件有效性验证和错误处理机制

2. 算法处理控制：
   - 血管分割算法选择和执行
   - 多视图图像导出功能（横截面、冠状面、矢状面）

3. 处理模式管理：
   - 本地模式：直接在本地计算机执行处理算法
   - SOCKET模式：通过网络连接远程服务器进行处理

4. 结果管理：
   - 投票融合结果展示控制
   - 后处理结果展示控制
   - 多种处理结果的可视化切换

设计特点：
- 采用自定义ComboBox组件，保持界面风格统一
- 集成VTK三维可视化控制接口
- 支持动态添加和管理处理结果的显示控制
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QFileDialog, QCheckBox, QMessageBox, QStyle, QStyleOptionComboBox, QStylePainter,
    QListView
)
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt
import os

class CustomComboBox(QComboBox):
    """自定义下拉框组件，用于保持界面风格统一
       
    该组件通过重写paintEvent方法实现以下功能：
    1. 固定显示文本为"文件"并居中对齐
    2. 保持按钮样式的视觉效果
    3. 与全局CSS样式表配合使用，实现统一的UI设计
    """
    def __init__(self, parent=None):
        """初始化自定义下拉框组件"""
        super().__init__(parent)
        self.setView(QListView()) 
        # 使用QListView作为视图以支持全局CSS样式
        
    def paintEvent(self, event):
        """重写绘制事件，实现固定文本和居中显示效果
        
        Args:
            event: 绘制事件对象
        """
        painter = QStylePainter(self)
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        
        # 固定显示"文件"文本并居中对齐
        option.currentText = ""
        option.editable = False  # 设置为非可编辑模式以保持按钮外观
        
        # 绘制下拉框基础样式
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        
        # 在编辑区域绘制居中的文本
        text_rect = self.style().subControlRect(QStyle.CC_ComboBox, option, QStyle.SC_ComboBoxEditField, self)
        painter.drawText(text_rect, Qt.AlignCenter, "文件")

class ProcessingControls(QWidget):
    """医学图像处理控制面板组件
       
    该组件负责管理整个医学图像处理流程的用户交互，包括文件选择、
    算法选择、处理模式切换和结果展示控制等功能。作为系统的核心控制
    界面，它与VTK三维可视化模块和图像显示模块紧密协作，实现完整
    的医学图像处理工作流。
    """
    def __init__(self, parent=None):
        """初始化处理控制组件"""
        super().__init__(parent)
        self.setup_ui()
        
        # 初始化处理相关属性
        self.file_name1 = None                      # 当前选择的文件路径
        self.voting_fusion_result = None           # 投票融合结果路径
        self.postprocessing_result = None          # 后处理结果数据
        self.postprocessing_enabled = False        # 后处理功能启用状态
        self.one = 0                               # 模型1显示状态标志
        self.two = 0                               # 模型2显示状态标志
        self.three = 0                             # 模型3显示状态标志
        self.four = 0                              # 融合结果显示状态标志
        self.cboxself = 0                          # 原始图像显示状态标志

    def setup_ui(self):
        """设置用户界面布局和控件
        
        创建并布局所有处理控制相关的UI组件，包括文件选择、算法选择、
        模式切换和结果管理等下拉框控件。所有控件均采用统一的尺寸和
        样式设计，确保界面美观和用户体验一致性。
        """
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # 文件操作下拉框 - 模拟按钮行为但保持下拉框功能
        self.datashow = CustomComboBox()
        self.datashow.setFixedSize(105, 45)
        self.datashow.addItems(["文件", "选择文件", "清空文件","TS模式","切换模式"])
        self.datashow.setCurrentIndex(0)
        
        # 算法选择下拉框 - 提供不同的血管分割和视图导出选项
        self.suanfa = QComboBox()
        self.suanfa.setObjectName("suanfa")
        self.suanfa.setFixedSize(106, 45)
        self.suanfa.addItems(["导出血管", "导出横截面", "导出冠状面", "导出矢状面"])
        self.suanfa.setView(QListView())  # 使用QListView来支持样式
        self.suanfa.setCurrentIndex(0)
        
        # 处理模式选择下拉框 - 切换本地处理和网络处理模式
        self.sk = QComboBox()
        self.sk.setObjectName("sk")
        self.sk.setFixedSize(107, 45)
        self.sk.addItems(["本地模式", "SOCKET"])
        self.sk.setView(QListView())  # 使用QListView来支持样式
        self.sk.setCurrentIndex(0)
        
        # 后处理结果管理下拉框 - 控制最终处理结果的显示
        self.postprocessing_combo = QComboBox()
        self.postprocessing_combo.setObjectName("postprocessing_combo")
        self.postprocessing_combo.setFixedSize(105, 45)
        self.postprocessing_combo.addItems(["最终结果","投票融合", "后处理"])
        self.postprocessing_combo.setCurrentIndex(0)
        self.postprocessing_combo.setEnabled(False)  # 初始状态下禁用，直到有处理结果
        self.postprocessing_combo.setView(QListView())  # 使用QListView来支持样式
        # 移除了内联样式，使用全局CSS样式
        
        # 添加控件到布局中
        layout.addWidget(self.datashow)
        layout.addWidget(self.suanfa)
        layout.addWidget(self.sk)
        layout.addWidget(self.postprocessing_combo)
        layout.addStretch(1)


    def get_buttons(self):
        """
        获取文件操作和后处理相关的下拉框组件
        
        Returns:
            tuple: (文件操作下拉框, 后处理下拉框)
        """
        return self.datashow, self.postprocessing_combo
    
    def get_comboboxes(self):
        """
        获取所有处理控制下拉框组件
        
        Returns:
            tuple: (算法选择下拉框, 模式选择下拉框, 后处理下拉框)
        """
        return self.suanfa, self.sk, self.postprocessing_combo
    
    def set_voting_fusion_result(self, result_path):
        """设置投票融合结果路径并更新相关状态
        
        Args:
            result_path (str): 投票融合结果文件路径
        """
        self.voting_fusion_result = result_path
        self.postprocessing_enabled = True if result_path else False
    
    def set_file_name(self, file_name):
        """
        设置当前处理的文件路径
        
        Args:
            file_name (str): 医学图像文件的完整路径
        """
        self.file_name1 = file_name
    
    def get_file_name(self):
        """
        获取当前处理的文件路径
        
        Returns:
            str: 当前选择的医学图像文件路径
        """
        return self.file_name1
    
    def show_file_dialog(self, parent, vtk_integration, image_display, gong_box_check):
        """
        显示文件选择对话框并初始化相关组件
        
        该方法负责处理用户选择医学图像文件的完整流程，包括文件有效性验证、
        VTK组件初始化、用户界面更新等操作。是整个处理流程的起点。
        
        Args:
            parent: 父级窗口对象，用于模态对话框
            vtk_integration: VTK集成组件对象（VTKIntegration实例）
            image_display: 图像显示组件对象
            gong_box_check: 控制面板布局管理器 (QVBoxLayout)
        
        Returns:
            str: 成功选择的文件路径，如果失败则返回None
        """
        options = QFileDialog.Options()
        self.file_name1, _ = QFileDialog.getOpenFileName(
            parent, 
            "选择文件", 
            "", 
            "Medical Files (*.mhd *.mha *.nii *.nii.gz);;All Files (*)",
            options=options
        )
        
        if self.file_name1:
            # 验证文件是否存在
            if not os.path.exists(self.file_name1):
                QMessageBox.warning(parent, "文件错误", "选择的文件不存在！")
                self.file_name1 = None
                return None
                
            # 确保VTK集成组件已正确初始化
            if vtk_integration.vtk_viewer is None:
                vtk_integration.initialize()
            
            # 使用VTK集成组件加载新选择的文件
            vtk_integration.change_file(self.file_name1)
            
            # 创建对应文件的显示控制复选框
            file_name = os.path.basename(self.file_name1)
            checkBox_self = QCheckBox(file_name)
            # 将复选框添加到控制面板布局中
            gong_box_check.add_checkbox(checkBox_self)
            checkBox_self.setChecked(True)
            self.cboxself = 1
            
            # 为新创建的复选框绑定状态切换事件
            checkBox_self.stateChanged.connect(
                lambda state: self.toggle_actorself(vtk_integration)
            )
            checkBox_self.show()
        
        return self.file_name1
        
    def toggle_actorself(self, vtk_integration):
        """
        切换原始医学图像在3D视图中的显示状态
        
        该方法通过控制VTK渲染器中的actor对象来实现原始图像数据的
        显示/隐藏切换功能，为用户提供灵活的结果可视化控制能力。
        
        Args:
            vtk_integration: VTK集成组件对象，用于访问VTK渲染器
        """
        if not vtk_integration or not vtk_integration.vtk_viewer:
            return
            
        if hasattr(self, 'cboxself') and self.cboxself == 1:
            vtk_integration.vtk_viewer.delete_actorself()
            self.cboxself = 0
        else:
            vtk_integration.vtk_viewer.add_actorself()
            self.cboxself = 1
            
    def toggle_actor1(self, vtk_viewer):
        """
        切换模型1处理结果在3D视图中的显示状态
        
        Args:
            vtk_viewer: VTK查看器对象，用于控制3D渲染
        """
        if hasattr(self, 'cbox_b1') and self.cbox_b1 == 1:
            vtk_viewer.delete_actor1()
            self.cbox_b1 = 0
        else:
            vtk_viewer.add_actor1()
            self.cbox_b1 = 1
    
    def toggle_actor2(self, vtk_viewer):
        """
        切换模型2处理结果在3D视图中的显示状态
        
        Args:
            vtk_viewer: VTK查看器对象，用于控制3D渲染
        """
        if hasattr(self, 'cbox_b2') and self.cbox_b2 == 1:
            vtk_viewer.delete_actor2()
            self.cbox_b2 = 0
        else:
            vtk_viewer.add_actor2()
            self.cbox_b2 = 1
    
    def toggle_actor3(self, vtk_viewer):
        """
        切换模型3处理结果在3D视图中的显示状态
        
        Args:
            vtk_viewer: VTK查看器对象，用于控制3D渲染
        """
        if hasattr(self, 'cbox_b3') and self.cbox_b3 == 1:
            vtk_viewer.delete_actor3()
            self.cbox_b3 = 0
        else:
            vtk_viewer.add_actor3()
            self.cbox_b3 = 1
    
    def toggle_actor4(self, vtk_viewer):
        """
        切换投票融合结果在3D视图中的显示状态
        
        Args:
            vtk_viewer: VTK查看器对象，用于控制3D渲染
        """
        if hasattr(self, 'cbox_b4') and self.cbox_b4 == 1:
            vtk_viewer.delete_actor4()
            self.cbox_b4 = 0
        else:
            vtk_viewer.add_actor4()
            self.cbox_b4 = 1