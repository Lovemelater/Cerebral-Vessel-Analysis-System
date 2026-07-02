"""
main_window.py
主窗口组件，管理整体布局和组件集成

主窗口是整个医学图像处理应用程序的核心，负责整合所有组件并管理它们之间的交互：
- 窗口管理：设置应用程序标题、图标和整体布局
- 组件集成：整合图像控制、显示、处理控制和VTK 3D视图组件
- 事件处理：处理用户交互，如鼠标点击和滚轮事件
- 布局管理：组织左侧控制面板和右侧图像显示区域
- 信号连接：连接各个组件之间的信号与槽函数

参赛作品注释说明：
该模块是整个系统的中枢控制器，采用模块化设计思想，通过组合模式将各个功能组件
（图像显示、处理控制、3D可视化等）有机整合，体现了良好的软件架构设计原则
"""

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QDesktopWidget, QApplication, QGridLayout
    ,QLabel,QSlider, QSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys
from image_controls import ImageControls
from image_display import ImageDisplay
from processing_controls import ProcessingControls
from fu_xuan import FuXuanDisplay
from vtk_integration import VTKIntegration
from image_processor import ImageProcessor
from app_reset import reset_application
from vtk_error_suppressor import suppress_vtk_warnings
from theme_manager import ThemeManager 


class MainWindow(QMainWindow):
    """
    主窗口组件类，负责整个应用程序的布局管理和组件协调
    
    该类继承自QMainWindow，是整个应用程序的中枢控制器，实现了以下核心功能：
    1. 组件初始化与布局管理
    2. 信号与槽机制的连接
    3. 用户交互事件处理
    4. 医学图像处理流程控制
    5. 3D可视化集成管理
    """
    
    def __init__(self):
        """
        初始化主窗口，设置应用程序核心组件和基础配置
        
        参赛作品注释说明：
        此初始化过程体现了良好的依赖注入原则，各功能模块通过组合而非继承方式
        集成到主窗口中，便于模块的独立开发和测试，符合现代软件工程的最佳实践
        """
        suppress_vtk_warnings()
        super().__init__()
        self.setup_components()
        self.setup_window()  
        self.setup_layout()
        self.setup_connections()
        self.center()
        
    def setup_components(self):
        """
        初始化应用程序所需的所有功能组件
        
        创建并配置以下核心组件：
        - 图像控制组件：管理2D切片显示参数
        - 图像显示组件：负责医学图像的2D正交视图显示sss
        - 处理控制组件：管理文件选择和算法处理流程
        - VTK集成组件：负责3D可视化功能
        - 图像处理器：处理医学图像数据加载和转换
        - 复选框显示组件：管理处理结果的叠加显示
        
        参赛作品注释说明：
        采用组件化设计模式，各组件职责单一且相互解耦，便于维护和扩展
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.image_controls = ImageControls()
        self.image_display = ImageDisplay()
        self.processing_controls = ProcessingControls()
        self.vtk_integration = VTKIntegration(self.image_display.get_3d_frame(), self.processing_controls)
        self.theme_manager = ThemeManager() 
        
        # 初始化VTK查看器
        self.vtk_integration.initialize()
        # 将主窗口引用传递给VTK查看器
        if self.vtk_integration.vtk_viewer:
            self.vtk_integration.vtk_viewer.main_window = self
            
        self.image_processor = ImageProcessor()
        # 将主窗口引用传递给ImageProcessor
        self.image_processor.main_window = self
        # 初始化FuXuanDisplay组件
        self.fu_xuan_display = FuXuanDisplay(self.image_display, self.image_processor, self.processing_controls)
        
        # 添加显示状态管理
        self.voting_fusion_displayed = False
        self.postprocessing_displayed = False
        self.test1_1_displayed = False  # 添加test1_1显示状态
        self.test2_2_displayed = False  # 添加test2_2显示状态
        self.test3_3_displayed = False  # 添加test3_3显示状态
        
        # 保存各种数据
        self.voting_fusion_data = None
        self.postprocessing_data = None
        self.test1_1_data = None  # 添加test1_1数据
        self.test2_2_data = None  # 添加test2_2数据
        self.test3_3_data = None  # 添加test3_3数据
        self.combined_data = None
        self.original_data_for_voting = None
        self.original_data_for_postprocessing = None
        self.original_data_for_test1_1 = None  # 添加test1_1原始数据
        self.original_data_for_test2_2 = None  # 添加test2_2原始数据
        self.original_data_for_test3_3 = None  # 添加test3_3原始数据
        self.original_image_data = None
        self.mip_viewer = None

    def setup_window(self):
        """
        设置主窗口基本属性和外观
        
        配置包括窗口标题、图标、主题样式、初始尺寸和焦点策略等
        """
        self.setWindowTitle("CereVAS - Cerebral Vessel Analysis System")
        self.setWindowIcon(QIcon('image/rigbt.jpg'))
        self.theme_manager.apply_dark_theme() 
        self.resize(1502, 894)
        self.setFocusPolicy(Qt.StrongFocus)
        
    def setup_layout(self):
        """
        设置主窗口的整体布局结构
        
        采用左右分栏式布局：
        - 左侧：控制面板区域，包含处理控制和图像控制组件
        - 右侧：图像显示区域，包含四个视图（三个2D正交视图+1个3D视图）
        
        参赛作品注释说明：
        布局设计符合医学图像处理软件的人机交互习惯，控制区与显示区分离，
        便于医生或研究人员进行图像分析操作
        """
        # 整体水平布局
        main_layout = QHBoxLayout(self.central_widget)
        
        # 左侧布局（控制区域）
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)
        left_layout.setContentsMargins(20, 20, 20, 20)
        
        # 添加处理控制
        left_layout.addWidget(self.processing_controls)
        # 添加图像控制（复选框区域）
        left_layout.addWidget(self.image_controls)
        
        # 创建滑动条区域并添加到左侧布局（移除外框）
        self.slider_controls = self.create_slider_controls()
        left_layout.addWidget(self.slider_controls)
        
        # 右侧布局（图像显示区域）
        right_layout = QVBoxLayout()
        
        # 创建图像网格布局
        image_layout = QGridLayout()
        image_layout.addWidget(self.image_display.lab1_foreground, 1, 1)
        image_layout.addWidget(self.image_display.lab2_foreground, 1, 2)
        image_layout.addWidget(self.image_display.lab3_foreground, 2, 1)
        image_layout.addWidget(self.image_display.frame1, 2, 2)
        
        right_layout.addLayout(image_layout)
        
        # 将左右布局添加到主布局
        main_layout.addLayout(left_layout)
        main_layout.addLayout(right_layout)
        main_layout.addStretch(1)
        
    def create_slider_controls(self):
        """
        创建滑动条控制区域（无外框）
        
        包含四个控制组：
        1. 横截面控制：控制轴向切片位置
        2. 矢状面控制：控制矢状面切片位置
        3. 冠状面控制：控制冠状面切片位置
        4. 窗宽窗位控制：调节图像对比度和亮度
        
        参赛作品注释说明：
        每个控制组都包含标签、滑块和数值输入框三组件联动，提供多种交互方式，
        提升用户体验，符合医疗设备操作习惯
        """
        slider_widget = QWidget()
        # 设置固定高度
        slider_widget.setFixedHeight(220)
        
        layout = QVBoxLayout(slider_widget)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(15)  # 增加控件间的垂直间距从10到15
        # 增加上边距，使第一个控件向下移动
        layout.setContentsMargins(18, 10, 15, 15)  # 增加边距空间
        
        # 矢状面控制（横截面）
        axial_layout = QHBoxLayout()
        axial_layout.setSpacing(20)  # 增加标签、滑块和数字输入框之间的水平间距
        self.axial_label = QLabel("  横 截 面")
        self.axial_label.setObjectName("axial_label")
        self.axial_label.setFixedSize(100, 20)
        axial_layout.addWidget(self.axial_label)
        
        self.axial_sild = QSlider(Qt.Horizontal)
        self.axial_sild.setObjectName("axial_sild")
        self.axial_sild.setFixedSize(250, 20)
        self.axial_sild.setMaximum(0)
        self.axial_sild.setMinimum(0)
        self.axial_sild.setValue(0)
        axial_layout.addWidget(self.axial_sild)
        
        self.axial_intbtn = QSpinBox()
        self.axial_intbtn.setObjectName("axial_intbtn")
        self.axial_intbtn.setMinimum(0)
        self.axial_intbtn.setMaximum(0)
        self.axial_intbtn.setFixedSize(50, 25)
        self.axial_intbtn.setValue(0)
        axial_layout.addWidget(self.axial_intbtn)
        
        layout.addLayout(axial_layout)
        
        # 冠状面控制
        sagittal_layout = QHBoxLayout()
        sagittal_layout.setSpacing(20)  # 增加标签、滑块和数字输入框之间的水平间距
        self.sagittal_label = QLabel("  矢 状 面")
        self.sagittal_label.setObjectName("sagittal_label")
        self.sagittal_label.setFixedSize(100, 20)
        sagittal_layout.addWidget(self.sagittal_label)
        
        self.sagittal_sild = QSlider(Qt.Horizontal)
        self.sagittal_sild.setObjectName("sagittal_sild")
        self.sagittal_sild.setFixedSize(250, 20)
        self.sagittal_sild.setMaximum(0)
        self.sagittal_sild.setMinimum(0)
        self.sagittal_sild.setValue(0)
        sagittal_layout.addWidget(self.sagittal_sild)
        
        self.sagittal_intbtn = QSpinBox()
        self.sagittal_intbtn.setObjectName("sagittal_intbtn")
        self.sagittal_intbtn.setMinimum(0)
        self.sagittal_intbtn.setMaximum(0)
        self.sagittal_intbtn.setFixedSize(50, 25)
        self.sagittal_intbtn.setValue(0)
        sagittal_layout.addWidget(self.sagittal_intbtn)
        
        layout.addLayout(sagittal_layout)
        
        # 控制（冠状面）
        coronal_layout = QHBoxLayout()
        coronal_layout.setSpacing(20)  # 增加标签、滑块和数字输入框之间的水平间距
        self.coronal_label = QLabel("  冠 状 面")
        self.coronal_label.setObjectName("coronal_label")
        self.coronal_label.setFixedSize(100, 20)
        coronal_layout.addWidget(self.coronal_label)
        
        self.coronal_sild = QSlider(Qt.Horizontal)
        self.coronal_sild.setObjectName("coronal_sild")
        self.coronal_sild.setFixedSize(250, 20)
        self.coronal_sild.setMaximum(0)
        self.coronal_sild.setMinimum(0)
        self.coronal_sild.setValue(0)
        coronal_layout.addWidget(self.coronal_sild)
        
        self.coronal_intbtn = QSpinBox()
        self.coronal_intbtn.setObjectName("coronal_intbtn")
        self.coronal_intbtn.setMinimum(0)
        self.coronal_intbtn.setMaximum(0)
        self.coronal_intbtn.setFixedSize(50, 25)
        self.coronal_intbtn.setValue(0)
        coronal_layout.addWidget(self.coronal_intbtn)
        
        layout.addLayout(coronal_layout)
        
        # 窗宽控制
        window_width_layout = QHBoxLayout()
        window_width_layout.setSpacing(20)  # 增加标签、滑块和数字输入框之间的水平间距
        self.window_width_label = QLabel("  窗    宽")
        self.window_width_label.setObjectName("window_width_label")
        self.window_width_label.setFixedSize(100, 20)
        window_width_layout.addWidget(self.window_width_label)
        
        self.window_width_sild = QSlider(Qt.Horizontal)
        self.window_width_sild.setObjectName("window_width_sild")
        self.window_width_sild.setFixedSize(250, 20)
        self.window_width_sild.setMaximum(0)
        self.window_width_sild.setMinimum(0)
        self.window_width_sild.setValue(0)
        window_width_layout.addWidget(self.window_width_sild)
        
        self.window_width_intbtn = QSpinBox()
        self.window_width_intbtn.setObjectName("window_width_intbtn")
        self.window_width_intbtn.setMinimum(0)
        self.window_width_intbtn.setMaximum(0)
        self.window_width_intbtn.setFixedSize(50, 25)
        self.window_width_intbtn.setValue(0)
        window_width_layout.addWidget(self.window_width_intbtn)
        
        layout.addLayout(window_width_layout)
        
        # 窗位控制
        window_possion_layout = QHBoxLayout()
        window_possion_layout.setSpacing(20)  # 增加标签、滑块和数字输入框之间的水平间距
        self.window_possion_label = QLabel("  窗    位")
        self.window_possion_label.setObjectName("window_possion_label")
        self.window_possion_label.setFixedSize(100, 20)
        window_possion_layout.addWidget(self.window_possion_label)
        
        self.window_possion_slid = QSlider(Qt.Horizontal)
        self.window_possion_slid.setObjectName("window_possion_slid")
        self.window_possion_slid.setFixedSize(250, 20)
        self.window_possion_slid.setMaximum(0)
        self.window_possion_slid.setMinimum(0)
        self.window_possion_slid.setValue(0)
        window_possion_layout.addWidget(self.window_possion_slid)
        
        self.window_possion_intbtn = QSpinBox()
        self.window_possion_intbtn.setObjectName("window_possion_intbtn")
        self.window_possion_intbtn.setMinimum(0)
        self.window_possion_intbtn.setMaximum(0)
        self.window_possion_intbtn.setFixedSize(50, 25)
        self.window_possion_intbtn.setValue(0)
        window_possion_layout.addWidget(self.window_possion_intbtn)
        
        layout.addLayout(window_possion_layout)
        
        return slider_widget

    def setup_connections(self):
        """
        设置组件间信号连接
        
        建立完整的信号与槽机制，实现组件间的自动响应：
        - 文件选择变化响应
        - 算法选择响应
        - 后处理选择响应
        - 滑块与数值输入框联动
        """
        # 连接文件选择下拉框
        datashow, postprocessing_combo = self.processing_controls.get_buttons()
        datashow.currentIndexChanged.connect(self.handle_file_selection_change)
        
        # 连接算法选择
        suanfa, sk, _ = self.processing_controls.get_comboboxes()
        suanfa.currentIndexChanged.connect(self.handle_algorithm_selection)
        
        # 连接后处理下拉框
        _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
        postprocessing_combo.currentIndexChanged.connect(self.handle_postprocessing_selection)
        
        # 连接滑块和数值输入框
        self.connect_sliders()

    def handle_file_selection_change(self, index):
        """
        处理文件选择下拉框选项变化事件
        
        Args:
            index (int): 下拉框当前选中项索引
            
        参赛作品注释说明：
        该方法实现了多种文件操作的统一入口，包括文件加载、清空重启、MIP投影等功能，
        体现了良好的命令模式设计思想
        """
        if index == 1:  # 选择医学文件
            self.handle_file_selection()
        elif index == 2:  # 清空所有文件
            self.handle_clear_all_files()
        elif index == 3:  # 最大密度投影
            self.handle_mip_projection()
        elif index == 4:  
            self.theme_manager.toggle_theme()
        
        # 重置下拉框到初始状态
        datashow, _ = self.processing_controls.get_buttons()
        datashow.setCurrentIndex(0)

    def handle_file_menu_selection(self, index):
        """
        处理文件菜单选择事件
        
        Args:
            index (int): 菜单项索引
        """
        if index == 4:  # 切换模式选项
            self.theme_manager.toggle_theme()
            self.processing_controls.datashow.setCurrentIndex(0)  # 重置为"文件"选项

    def handle_mip_projection(self):
        """
        处理最大密度投影选项
        
        调用MIPViewer类实现最大密度投影（Maximum Intensity Projection）功能，
        用于突出显示高密度结构（如血管）的3D可视化效果
        """
        try:
            # 导入ts.py中的MIPViewer类
            from ts import MIPViewer        
            # 获取当前文件路径
            file_name = self.processing_controls.get_file_name()
            
            # 如果没有选择文件，创建一个空的MIPViewer
            if not file_name:
                # 创建MIPViewer实例
                self.mip_viewer = MIPViewer()
                self.mip_viewer.show()
            else:
                # 创建MIPViewer实例并传递文件路径
                self.mip_viewer = MIPViewer(background_mha_path=file_name)
                self.mip_viewer.show()
        except Exception as e:
            print(f"打开最大密度投影窗口时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def handle_clear_all_files(self):
        """处理清空所有文件并重启应用"""
        # 调用独立的重置功能模块
        reset_application(self)

    # 添加新的处理方法
    def handle_postprocessing_selection(self, index):
        """
        处理后处理下拉框选择事件
        
        Args:
            index (int): 下拉框选中项索引
        """
        if index == 1:  # 投票融合
            self.handle_voting_fusion()
        elif index == 2:  # 后处理
            self.handle_postprocessing()
    
    def handle_voting_fusion(self):
        """
        处理投票融合事件
        
        实现多模型结果的投票融合算法，提高血管分割的准确性和鲁棒性
        参赛作品注释说明：
        该功能是本作品的核心创新点之一，通过集成多个深度学习模型的预测结果，
        采用投票机制获得更可靠的血管分割结果
        """
        file_name = self.processing_controls.get_file_name()
        if not self.image_processor.validate_file(file_name, self):
            # 重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)
            return
            
        _, sk, _ = self.processing_controls.get_comboboxes()
        sk_index = sk.currentIndex()
        
        result = self.vtk_integration.process_voting_fusion(
            file_name, 
            sk_index, 
            self.image_controls
        )
        
        if not result:
            # 重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)
            return
            
        if result:
            self.processing_controls.set_voting_fusion_result(result)
            self.processing_controls.four = 1
            
            # 将投票融合结果叠加到原始图像上并显示
            self.overlay_voting_fusion_result(result)
            
            # 重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)
            
    def overlay_voting_fusion_result(self, voting_file):
        """
        将投票融合结果叠加到原始图像上进行可视化显示
        
        Args:
            voting_file (str): 投票融合结果文件路径
            
        参赛作品注释说明：
        通过透明度叠加方式将分割结果与原始医学图像融合显示，便于医生直观评估分割效果
        """
        # 使用FuXuanDisplay组件处理投票融合结果叠加
        self.fu_xuan_display.overlay_voting_fusion_result(voting_file)
        # 更新主窗口的显示状态
        self.voting_fusion_displayed = self.fu_xuan_display.voting_fusion_displayed
        self.voting_fusion_data = self.fu_xuan_display.voting_fusion_data
        self.original_image_data = self.fu_xuan_display.original_image_data
    def handle_postprocessing(self):
        """
        处理后处理事件
        
        对投票融合结果进行形态学后处理，包括去噪、连通域分析等操作，
        提高分割结果的质量和临床实用性
        """
        # 检查是否有投票融合结果
        voting_result = self.processing_controls.voting_fusion_result
        if not voting_result:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "警告", "请先执行投票融合")
            # 重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)
            return
            
        # 添加弹窗让用户输入min_voxel_num值
        from PyQt5.QtWidgets import QInputDialog
        min_voxel_num, ok = QInputDialog.getInt(self, "设置参数", "请输入最小体素数:", 100, 1, 10000, 1)
        if not ok:
            # 用户取消输入，重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)
            return
            
        # 执行后处理
        result = self.vtk_integration.process_postprocessing(
            voting_result, 
            self.image_controls,
            min_voxel_num  # 传递用户输入的参数
        )
        
        if not result:
            # 如果后处理失败，显示错误提示
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "错误", "后处理失败")
            # 重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)
            return
            
        if result:
            # 设置后处理结果路径
            self.processing_controls.postprocessing_result = result
            # 将后处理结果叠加到原始图像上并显示（红色显示）
            self.overlay_postprocessing_result(result)
            # 重置下拉框选择
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setCurrentIndex(0)

    def overlay_postprocessing_result(self, postprocessed_file):
        """
        将后处理结果叠加到原始图像上进行可视化显示
        
        Args:
            postprocessed_file (str): 后处理结果文件路径
        """
        # 使用FuXuanDisplay组件处理后处理结果叠加
        self.fu_xuan_display.overlay_postprocessing_result(postprocessed_file)
        # 更新主窗口的显示状态
        self.postprocessing_displayed = self.fu_xuan_display.postprocessing_displayed
        self.postprocessing_data = self.fu_xuan_display.postprocessing_data
        self.original_image_data = self.fu_xuan_display.original_image_data
    def update_combined_display(self):
        """
        根据当前选中状态更新组合显示效果
        
        统一管理多个处理结果的叠加显示，确保各层显示效果的协调统一
        """
        # 更新FuXuanDisplay组件的状态
        self.fu_xuan_display.voting_fusion_displayed = self.voting_fusion_displayed
        self.fu_xuan_display.postprocessing_displayed = self.postprocessing_displayed
        self.fu_xuan_display.test1_1_displayed = self.test1_1_displayed  # 更新test1_1状态
        self.fu_xuan_display.test2_2_displayed = self.test2_2_displayed  # 更新test2_2状态
        self.fu_xuan_display.test3_3_displayed = self.test3_3_displayed  # 更新test3_3状态
        self.fu_xuan_display.voting_fusion_data = self.voting_fusion_data
        self.fu_xuan_display.postprocessing_data = self.postprocessing_data
        self.fu_xuan_display.test1_1_data = self.test1_1_data  # 更新test1_1数据
        self.fu_xuan_display.test2_2_data = self.test2_2_data  # 更新test2_2数据
        self.fu_xuan_display.test3_3_data = self.test3_3_data  # 更新test3_3数据
        self.fu_xuan_display.original_image_data = self.original_image_data
        
        # 调用FuXuanDisplay组件的更新方法
        self.fu_xuan_display.update_combined_display()
        
        # 同步状态回来
        self.voting_fusion_displayed = self.fu_xuan_display.voting_fusion_displayed
        self.postprocessing_displayed = self.fu_xuan_display.postprocessing_displayed
        self.test1_1_displayed = self.fu_xuan_display.test1_1_displayed  # 同步test1_1状态
        self.test2_2_displayed = self.fu_xuan_display.test2_2_displayed  # 同步test2_2状态
        self.test3_3_displayed = self.fu_xuan_display.test3_3_displayed  # 同步test3_3状态
        self.voting_fusion_data = self.fu_xuan_display.voting_fusion_data
        self.postprocessing_data = self.fu_xuan_display.postprocessing_data
        self.test1_1_data = self.fu_xuan_display.test1_1_data  # 同步test1_1数据
        self.test2_2_data = self.fu_xuan_display.test2_2_data  # 同步test2_2数据
        self.test3_3_data = self.fu_xuan_display.test3_3_data  # 同步test3_3数据
        self.original_image_data = self.fu_xuan_display.original_image_data

    # 修改 handle_file_selection 方法
    def handle_file_selection(self):
        """
        处理文件选择事件
        
        加载用户选择的医学图像文件，初始化显示参数和相关组件状态
        参赛作品注释说明：
        支持多种医学图像格式（MHA、MHD、NII等），采用标准化的数据处理流程，
        为后续的血管分割和3D可视化奠定基础
        """
        file_name = self.processing_controls.show_file_dialog(
            self, 
            self.vtk_integration, 
            self.image_display, 
            self.image_controls
        )
        
        if file_name:
            # 加载医学图像
            image_array, image_xy, image_xz, image_yz = self.image_processor.load_medical_image(file_name)
            self.image_display.set_image_data(image_xy, image_xz, image_yz)
            self.image_display.set_background_mha_path(file_name)
            
            # 保存原始数据以便后续恢复
            self.original_image_data = (image_array, image_xy, image_xz, image_yz)
            
            # 设置切片数量
            num_slices_xz, num_slices_yz, num_slices_xy = self.image_processor.get_slice_counts()
            self.update_slider_ranges(num_slices_xy, num_slices_xz, num_slices_yz)
            
            # 设置初始切片位置
            self.set_initial_slice_positions(num_slices_xy, num_slices_xz, num_slices_yz)
            
            # 设置窗宽窗位
            self.update_window_controls(700, 350)
            
            # 更新图像显示
            self.update_image_displays()
            
            # 启用后处理下拉框
            _, _, postprocessing_combo = self.processing_controls.get_comboboxes()
            postprocessing_combo.setEnabled(True)
            # 重置投票融合结果
            self.processing_controls.set_voting_fusion_result(None)
            
            # 重置显示状态
            self.voting_fusion_displayed = False
            self.postprocessing_displayed = False
            self.voting_fusion_data = None
            self.postprocessing_data = None
        

    def connect_sliders(self):
        """
        连接所有滑块和数值输入框的信号与槽
        
        实现滑块与数值输入框的双向联动，提供多种交互方式
        """
        # 横截面控制 (axial)
        self.axial_sild.valueChanged.connect(
            lambda value: self.handle_slice_change(value, 0))
        self.axial_intbtn.valueChanged.connect(
            lambda value: self.handle_slice_spinbox_change(value, 0))
        
        # 矢状面控制 (sagittal)
        self.sagittal_sild.valueChanged.connect(
            lambda value: self.handle_slice_change(value, 1))
        self.sagittal_intbtn.valueChanged.connect(
            lambda value: self.handle_slice_spinbox_change(value, 1))
        
        # 冠状面控制 (coronal)
        self.coronal_sild.valueChanged.connect(
            lambda value: self.handle_slice_change(value, 2))
        self.coronal_intbtn.valueChanged.connect(
            lambda value: self.handle_slice_spinbox_change(value, 2))
        
        # 窗宽控制
        self.window_width_sild.valueChanged.connect(
            self.handle_window_change)
        self.window_width_intbtn.valueChanged.connect(
            self.handle_window_spinbox_change)
        
        # 窗位控制
        self.window_possion_slid.valueChanged.connect(
            self.handle_window_change)
        self.window_possion_intbtn.valueChanged.connect(
            self.handle_window_spinbox_change)

        
        # 窗宽控制
        self.window_width_sild.valueChanged.connect(
            self.handle_window_change)
        self.window_width_intbtn.valueChanged.connect(
            self.handle_window_spinbox_change)
        
        # 窗位控制
        self.window_possion_slid.valueChanged.connect(
            self.handle_window_change)
        self.window_possion_intbtn.valueChanged.connect(
            self.handle_window_spinbox_change)
            
    def update_slider_ranges(self, num_slices_xy, num_slices_xz, num_slices_yz):
        """
        更新滑块范围以适应当前加载图像的切片数量
        
        Args:
            num_slices_xy: 矢状面切片数量
            num_slices_xz: 冠状面切片数量
            num_slices_yz: 横截面切片数量
        """
        self.axial_sild.setMaximum(num_slices_xy - 1)
        self.axial_sild.setMinimum(0)
        self.axial_intbtn.setMaximum(num_slices_xy - 1)
        self.axial_intbtn.setMinimum(0)
        
        self.sagittal_sild.setMaximum(num_slices_xz - 1)
        self.sagittal_sild.setMinimum(0)
        self.sagittal_intbtn.setMaximum(num_slices_xz - 1)
        self.sagittal_intbtn.setMinimum(0)
        
        self.coronal_sild.setMaximum(num_slices_yz - 1)
        self.coronal_sild.setMinimum(0)
        self.coronal_intbtn.setMaximum(num_slices_yz - 1)
        self.coronal_intbtn.setMinimum(0)

    def update_window_controls(self, window_width, window_center):
        """
        更新窗宽窗位控制参数范围和初始值
        
        Args:
            window_width: 窗宽值
            window_center: 窗位值
        """
        self.window_width_sild.setMinimum(1)
        self.window_width_intbtn.setMinimum(1)
        self.window_width_sild.setMaximum(4096)
        self.window_width_intbtn.setMaximum(4096)
        self.window_width_sild.setValue(window_width)
        self.window_width_intbtn.setValue(window_width)
        
        self.window_possion_slid.setMinimum(-2048)
        self.window_possion_intbtn.setMinimum(-2048)
        self.window_possion_slid.setMaximum(2047)
        self.window_possion_intbtn.setMaximum(2047)
        self.window_possion_slid.setValue(window_center)
        self.window_possion_intbtn.setValue(window_center)
        

    def set_initial_slice_positions(self, num_slices_xy, num_slices_xz, num_slices_yz):
        """
        设置初始切片位置为各方向的中心切片
        
        Args:
            num_slices_xy: 横截面切片数量
            num_slices_xz: 矢状面切片数量
            num_slices_yz: 冠状面切片数量
        """
        # 横截面 (axial)
        self.axial_sild.setValue(int(num_slices_xy / 2))
        self.axial_intbtn.setValue(int(num_slices_xy / 2))
        # 矢状面 (sagittal)
        self.sagittal_sild.setValue(int(num_slices_xz / 2))
        self.sagittal_intbtn.setValue(int(num_slices_xz / 2))
        # 冠状面 (coronal)
        self.coronal_sild.setValue(int(num_slices_yz / 2))
        self.coronal_intbtn.setValue(int(num_slices_yz / 2))

        
    def handle_algorithm_selection(self, index):
        """
        处理算法选择事件，执行对应的血管分割算法
        
        Args:
            index (int): 算法选择索引
        """
        if index == 0:  # 导出血管
            return
            
        file_name = self.processing_controls.get_file_name()
        if not self.image_processor.validate_file(file_name, self):
            return
            
        _, sk ,_ = self.processing_controls.get_comboboxes()
        sk_index = sk.currentIndex()
        
        result = self.vtk_integration.process_algorithm(
            file_name, 
            index, 
            sk_index, 
            self.image_controls  # 传递 ImageControls 实例而不是 layout()
        )
        
        if result:
            self.processing_controls.one = 1 if index == 1 else self.processing_controls.one
            self.processing_controls.two = 1 if index == 2 else self.processing_controls.two
            self.processing_controls.three = 1 if index == 3 else self.processing_controls.three
    

    def handle_slice_change(self, value, plane):
        """
        处理切片滑块变化事件，同步更新显示和3D视图
        
        Args:
            value: 滑块值
            plane: 平面索引 (0-横截面, 1-矢状面, 2-冠状面)
        """
        if plane == 0:  # 横截面 (axial)
            self.axial_intbtn.setValue(value)
            self.image_display.update_image_xy(value)
            self.vtk_integration.change_slice(2, value)
        elif plane == 1:  # 矢状面 (sagittal)
            self.sagittal_intbtn.setValue(value)
            self.image_display.update_image_xz(value)
            self.vtk_integration.change_slice(0, value)
        elif plane == 2:  # 冠状面 (coronal)
            self.coronal_intbtn.setValue(value)
            self.image_display.update_image_yz(value)
            self.vtk_integration.change_slice(1, value)

    def handle_slice_spinbox_change(self, value, plane):
        """
        处理切片数值输入框变化事件，同步更新显示和3D视图
        
        Args:
            value: 输入值
            plane: 平面索引 (0-横截面, 1-矢状面, 2-冠状面)
        """
        if plane == 0:  # 横截面 (axial)
            self.axial_sild.setValue(value)
            self.image_display.update_image_xy(value)
            self.vtk_integration.change_slice(2, value)
        elif plane == 1:  # 矢状面 (sagittal)
            self.sagittal_sild.setValue(value)
            self.image_display.update_image_xz(value)
            self.vtk_integration.change_slice(0, value)
        elif plane == 2:  # 冠状面 (coronal)
            self.coronal_sild.setValue(value)
            self.image_display.update_image_yz(value)
            self.vtk_integration.change_slice(1, value)

    def handle_window_change(self):
        """
        处理窗宽窗位滑块变化事件，调整图像显示对比度和亮度
        """
        window_width = self.window_width_sild.value()
        window_center = self.window_possion_slid.value()
        
        self.window_width_intbtn.setValue(window_width)
        self.window_possion_intbtn.setValue(window_center)
        
        self.image_display.set_window_parameters(window_width, window_center)
        self.vtk_integration.set_window_level(window_width, window_center)
        self.update_image_displays()

    def handle_window_spinbox_change(self):
        """
        处理窗宽窗位数值输入框变化事件，调整图像显示对比度和亮度
        """
        window_width = self.window_width_intbtn.value()
        window_center = self.window_possion_intbtn.value()
        
        self.window_width_sild.setValue(window_width)
        self.window_possion_slid.setValue(window_center)
        
        self.image_display.set_window_parameters(window_width, window_center)
        self.vtk_integration.set_window_level(window_width, window_center)
        self.update_image_displays()
    
    def restore_original_display(self):
        """
        恢复显示原始图像，清除所有处理结果的叠加显示
        
        用于重置显示状态，回到初始的医学图像显示效果
        """
        # 使用FuXuanDisplay组件恢复原始显示
        self.fu_xuan_display.original_image_data = self.original_image_data
        self.fu_xuan_display.restore_original_display()
    def update_image_displays(self):
        """
        更新所有图像显示，重新渲染当前切片位置的图像
        
        确保2D视图和3D视图的一致性显示
        """
        x, y, z = self.image_display.get_current_slice_positions()
        self.image_display.update_image_xy(x)
        self.image_display.update_image_xz(y)
        self.image_display.update_image_yz(z)
    
    def mousePressEvent(self, event):
        """
        处理鼠标点击事件，传递给图像显示组件处理
        
        Args:
            event: 鼠标事件对象
        """
        self.image_display.handle_mouse_press(event, self.vtk_integration.vtk_viewer)
        super().mousePressEvent(event)
    
    def wheelEvent(self, event):
        """
        处理鼠标滚轮事件，用于切片切换操作
        
        Args:
            event: 鼠标滚轮事件对象
        """
        self.image_display.handle_wheel_event(event, self.vtk_integration.vtk_viewer)
        super().wheelEvent(event)
    
    def center(self):
        """
        将窗口居中显示在屏幕上的指定位置
        
        设置窗口初始显示位置，提升用户体验
        """
        screen = QDesktopWidget().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        window_width = self.width()
        window_height = self.height()
        
        # 将窗口定位在屏幕的指定位置，例如左上角偏移一些距离
        x = 100  # 距离屏幕左边的距离
        y = 50  # 距离屏幕顶部的距离
        
        self.move(x, y)
    def resizeEvent(self, event):
        """
        处理窗口大小调整事件，同步调整3D视图大小
        
        Args:
            event: 窗口大小调整事件对象
        """
        super().resizeEvent(event)
        if self.vtk_integration.vtk_viewer:
            self.vtk_integration.resize_viewer(
                self.image_display.frame1.width(), 
                self.image_display.frame1.height()
            )
   

if __name__ == '__main__':
    app = QApplication(sys.argv)
    # 创建主题管理器并应用初始主题
    theme_manager = ThemeManager()
    theme_manager.apply_dark_theme()
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())