"""
app_reset.py
应用重置功能模块，负责清空所有文件和重置应用状态

该模块提供完整的应用状态重置功能，确保用户在进行新任务时拥有干净的工作环境。
主要功能包括：
- 清空所有加载的医学图像数据
- 重置用户界面控件到初始状态
- 释放内存资源并重新初始化显示组件
- 恢复默认视图设置
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap


def reset_application(main_window):
    """
    全局重置应用程序到初始状态，为新任务准备干净环境
    
    该函数执行完整的应用状态重置流程，确保所有组件和数据恢复到初始状态，
    为用户开始新的医学图像处理任务提供干净的工作环境。此功能在用户需要
    处理新的MRA数据集时尤为重要，可以避免前一次任务的数据残留影响新任务结果。
    
    Args:
        main_window: 主窗口实例，包含所有需要重置的组件和数据
    """
    # 重置处理控制组件的状态和数据，清除所有处理结果
    main_window.processing_controls.file_name1 = None
    main_window.processing_controls.voting_fusion_result = None
    main_window.processing_controls.postprocessing_enabled = False
    main_window.processing_controls.one = 0
    main_window.processing_controls.two = 0
    main_window.processing_controls.three = 0
    main_window.processing_controls.four = 0
    
    # 清空图像显示组件的数据缓存，释放内存资源
    main_window.image_display.image_xy = None
    main_window.image_display.image_xz = None
    main_window.image_display.image_yz = None
    
    # 重置所有用户交互滑块控件到初始状态
    reset_sliders(main_window)
    
    # 清空所有复选框选择状态，恢复默认配置
    main_window.image_controls.clear_checkboxes()
    
    # 重置高级显示状态标志，确保后续处理流程正确执行
    main_window.voting_fusion_displayed = False
    main_window.postprocessing_displayed = False
    main_window.voting_fusion_data = None
    main_window.postprocessing_data = None
    main_window.combined_data = None
    main_window.original_data_for_voting = None
    main_window.original_data_for_postprocessing = None
    main_window.original_image_data = None
    
    # 禁用后处理下拉框并重置到默认选项，防止无效操作
    _, _, postprocessing_combo = main_window.processing_controls.get_comboboxes()
    postprocessing_combo.setEnabled(False)
    postprocessing_combo.setCurrentIndex(0)
    
    # 重置VTK 3D可视化显示组件，释放相关资源
    if main_window.vtk_integration.vtk_viewer:
        # 清除所有3D场景中的可视化对象（actors）
        main_window.vtk_integration.vtk_viewer.clear_actors()
        # 重新初始化VTK查看器，为下次3D显示做准备
        main_window.vtk_integration.vtk_viewer.all()
        
    # 显示默认占位图像，提供用户友好的界面反馈
    display_default_images(main_window)

def reset_sliders(main_window):
    """
    重置所有滑块控件到初始状态，包括切片选择和窗宽窗位调节滑块
    
    该函数负责将用户界面中的所有滑块控件恢复到初始状态，确保在新任务开始时
    不会保留之前任务的参数设置。包括医学图像的三个正交视图切片控制滑块和
    图像显示参数调节滑块，为用户提供一致的操作起点。
    
    Args:
        main_window: 主窗口实例，包含所有需要重置的滑块控件
    """
    # 重置轴向视图（Axial View）切片选择滑块范围和当前值
    main_window.axial_sild.setMaximum(0)
    main_window.axial_sild.setMinimum(0)
    main_window.axial_sild.setValue(0)
    main_window.axial_intbtn.setMaximum(0)
    main_window.axial_intbtn.setMinimum(0)
    main_window.axial_intbtn.setValue(0)
    
    # 重置矢状面视图（Sagittal View）切片选择滑块范围和当前值
    main_window.sagittal_sild.setMaximum(0)
    main_window.sagittal_sild.setMinimum(0)
    main_window.sagittal_sild.setValue(0)
    main_window.sagittal_intbtn.setMaximum(0)
    main_window.sagittal_intbtn.setMinimum(0)
    main_window.sagittal_intbtn.setValue(0)
    
    # 重置冠状面视图（Coronal View）切片选择滑块范围和当前值
    main_window.coronal_sild.setMaximum(0)
    main_window.coronal_sild.setMinimum(0)
    main_window.coronal_sild.setValue(0)
    main_window.coronal_intbtn.setMaximum(0)
    main_window.coronal_intbtn.setMinimum(0)
    main_window.coronal_intbtn.setValue(0)
    
    # 重置窗宽（Window Width）调节滑块，控制图像对比度
    main_window.window_width_sild.setMaximum(0)
    main_window.window_width_sild.setMinimum(0)
    main_window.window_width_sild.setValue(0)
    main_window.window_width_intbtn.setMaximum(0)
    main_window.window_width_intbtn.setMinimum(0)
    main_window.window_width_intbtn.setValue(0)
    
    # 重置窗位（Window Position/Center）调节滑块，控制图像亮度
    main_window.window_possion_slid.setMaximum(0)
    main_window.window_possion_slid.setMinimum(0)
    main_window.window_possion_slid.setValue(0)
    main_window.window_possion_intbtn.setMaximum(0)
    main_window.window_possion_intbtn.setMinimum(0)
    main_window.window_possion_intbtn.setValue(0)

def display_default_images(main_window):
    """
    显示默认占位图像，为用户提供清晰的界面状态反馈
    
    当应用重置或没有加载数据时，显示默认的占位图像以保持用户界面的一致性
    和友好性。这有助于用户理解当前应用状态，并为后续的图像加载操作提供
    明确的视觉指示。默认图像采用医学图像处理领域常见的视觉风格设计。
    
    Args:
        main_window: 主窗口实例，包含需要显示默认图像的标签组件
    """
    # 加载并显示默认前景图像，用于2D视图占位
    pixmap1 = QPixmap("image/agg.png")
    main_window.image_display.lab1_foreground.setPixmap(pixmap1)
    main_window.image_display.lab2_foreground.setPixmap(pixmap1)
    
    # 加载并显示3D视图默认图像，进行尺寸适配处理
    pixmap3 = QPixmap("image/agg.png")
    if not pixmap3.isNull():
        # 对3D视图图像进行缩放处理，保持宽高比并应用平滑变换算法
        main_window.image_display.lab3_foreground.setPixmap(pixmap3.scaled(400, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    else:
        # 当默认图像加载失败时，创建纯黑色背景作为替代方案
        default_pixmap = QPixmap(400, 400)
        default_pixmap.fill(Qt.black)
        main_window.image_display.lab3_foreground.setPixmap(default_pixmap)