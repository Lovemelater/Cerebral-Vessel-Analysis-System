# -*- coding: utf-8 -*-
"""
vtk_integration.py
VTK集成组件，管理VTK 3D视图相关操作
负责3D可视化功能的集成：

VTK查看器管理：初始化和管理VTK 3D视图
文件处理：加载和显示3D医学图像
窗宽窗位设置：调整3D视图的显示参数
切片控制：同步2D切片与3D视图
算法集成：集成各种处理算法的结果显示
复选框控制：管理处理结果的显示/隐藏

参赛作品注释规范：
- 模块级注释说明整体功能和架构设计
- 类注释阐明设计模式和核心职责
- 方法注释详述参数含义、返回值和异常处理
- 关键业务逻辑添加实现原理说明
- 界面交互部分说明用户体验考虑
"""

import os
from PyQt5.QtWidgets import QCheckBox
from VIT_Window import VtkViewer1

class VTKIntegration:
    """
    VTK集成组件类
    
    本类实现了医学图像三维可视化的完整集成方案，采用组合模式将VTK查看器
    与Qt界面框架无缝集成。主要功能包括：
    1. VTK查看器生命周期管理
    2. 多模态医学图像数据的3D渲染
    3. 2D/3D视图联动显示控制
    4. 多种算法处理结果的可视化集成
    5. 用户交互响应与界面状态同步
    """
    
    def __init__(self, frame, processing_controls=None):
        """
        初始化VTK集成组件
        
        Args:
            frame: 3D视图框架容器，用于嵌入VTK渲染窗口
            processing_controls: 处理控制组件引用，用于状态同步和数据共享
        """
        self.vtk_viewer = None
        self.frame = frame
        self.processing_controls = processing_controls
        self.actor1 = None  # 添加对actor1的引用
    
    def initialize(self):
        """
        初始化VTK查看器实例
        
        创建并配置VTK查看器，设置固定尺寸并显示。此方法确保只初始化一次查看器实例，
        避免重复创建造成的资源浪费和显示异常。
        
        Returns:
            VtkViewer1: 初始化后的VTK查看器实例
        """
        if self.vtk_viewer is None:
            self.vtk_viewer = VtkViewer1(self.frame)
            self.vtk_viewer.all()  # 初始化但不加载文件
            self.vtk_viewer.setFixedSize(600, 400)
            self.vtk_viewer.show()
        return self.vtk_viewer
    
    def change_file(self, file_name):
        """
        更换当前显示的医学图像文件
        
        Args:
            file_name (str): 新的医学图像文件路径（通常为MHA格式）
        """
        if self.vtk_viewer:
            self.vtk_viewer.change_file(file_name)
    
    def set_window_level(self, window_width, window_center):
        """
        设置窗宽窗位参数以优化图像显示效果
        
        窗宽窗位是医学图像显示的关键技术，用于突出特定组织结构的细节信息：
        - 窗宽(WW)控制显示的对比度范围
        - 窗位(WC)控制显示的亮度中心点
        
        Args:
            window_width (int/float): 窗宽值，决定显示灰度范围
            window_center (int/float): 窗位值，决定显示灰度中心
        """
        if self.vtk_viewer:
            self.vtk_viewer.set_window_level(window_width, window_center)
    
    def change_slice(self, plane_index, slice_index):
        """
        更新指定平面的切片显示
        
        实现2D切片视图与3D视图的联动显示，确保用户在任一视图的操作都能同步反映到其他视图中。
        
        Args:
            plane_index (int): 平面索引（0-横断面，1-冠状面，2-矢状面）
            slice_index (int): 切片索引，表示在该平面方向上的切片序号
        """
        if self.vtk_viewer:
            self.vtk_viewer.change_slice(plane_index, slice_index)
    
    def process_voting_fusion(self, file_name, sk_index, gong_box_check):
        """
        处理多模型投票融合算法结果的3D可视化
        
        采用多数投票机制融合三个独立模型的预测结果，提高脑血管分割的准确性和鲁棒性，
        并将融合结果在3D视图中进行可视化呈现。支持本地计算和远程服务两种处理模式。
        
        Args:
            file_name (str): 输入的原始医学图像文件路径
            sk_index (int): 处理模式索引（0-本地模式，1-SOCKET远程模式）
            gong_box_check (QVBoxLayout): 控制面板布局，用于添加结果控制复选框
            
        Returns:
            str: 处理结果文件路径，失败时返回None
        """
        try:
            from votingFusion2 import votingFusion2
            from filename import start_client, name
        except ImportError as e:
            print(f"导入模块失败: {e}")
            import traceback
            traceback.print_exc()
            return None

        print(f"开始投票融合处理，文件: {file_name}, 模式索引: {sk_index}")
        
        if sk_index == 0:  # 本地模式
            print("使用本地模式进行投票融合")
            try:
                file_name = votingFusion2(file_name)
                print(f"投票融合完成，结果文件: {file_name}")
            except Exception as e:
                print(f"投票融合处理失败: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:  # SOCKET模式
            print("使用SOCKET模式进行投票融合")
            try:
                file_name = start_client(file_name, 4)
                print(f"SOCKET通信完成，结果文件: {file_name}")
            except Exception as e:
                print(f"SOCKET通信失败: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        if file_name and os.path.exists(file_name):
            print(f"结果文件存在: {file_name}")
            try:
                if hasattr(self.vtk_viewer, 'gong_neng4'):
                    self.vtk_viewer.gong_neng4(file_name)
                    print("已调用gong_neng4")
                if hasattr(self.vtk_viewer, 'add_actor4'):
                    self.vtk_viewer.add_actor4()
                    print("已调用add_actor4")
                
                checkBox_b4 = QCheckBox(name(file_name))
                # 使用布局的addWidget方法添加复选框
                gong_box_check.add_checkbox(checkBox_b4)
                checkBox_b4.setChecked(True)
                
                # 正确连接信号，传递状态参数
                checkBox_b4.stateChanged.connect(
                    lambda state: self.toggle_actor4(state)
                )
                checkBox_b4.show()
                
                # 立即触发显示更新，确保2D视图也显示结果
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.voting_fusion_displayed = True
                    if hasattr(main_window, 'processing_controls'):
                        voting_result = main_window.processing_controls.voting_fusion_result
                        if voting_result and os.path.exists(voting_result):
                            main_window.fu_xuan_display.overlay_voting_fusion_result(voting_result)
                
                print("成功添加融合结果复选框")
                return file_name
            except Exception as e:
                print(f"VTK查看器操作失败: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            print(f"结果文件不存在或为空: {file_name}")
            return None

    def process_algorithm(self, file_name, algorithm_index, sk_index, gong_box_check):
        """
        处理单模型预测算法结果的3D可视化
        
        针对三种不同视角（横断面、冠状面、矢状面）训练的专用模型，分别进行推理预测并将结果可视化。
        每个模型专注于特定视角下的特征提取和分割任务，提高预测精度。支持本地和远程两种执行模式。
        
        Args:
            file_name (str): 输入的原始医学图像文件路径
            algorithm_index (int): 算法索引（1-横断面模型，2-冠状面模型，3-矢状面模型）
            sk_index (int): 处理模式索引（0-本地模式，1-SOCKET远程模式）
            gong_box_check (QVBoxLayout): 控制面板布局，用于添加结果控制复选框
            
        Returns:
            str: 处理结果文件路径，失败时返回None
        """
        try:
            from filename import start_client, name
            from predict1 import predict1
            from predict2 import predict2
            from predict3 import predict3
        except ImportError as e:
            print(f"导入模块失败: {e}")
            return None

        if algorithm_index == 1:  # 导出横截面
            try:
                if sk_index == 0:
                    file_name = predict1(file_name)
                else:
                    file_name = start_client(file_name, 1)
            except Exception as e:
                print(f"算法1处理失败: {e}")
                return None
        elif algorithm_index == 2:  # 导出冠状面
            try:
                if sk_index == 0:
                    file_name = predict2(file_name)
                else:
                    file_name = start_client(file_name, 2)
            except Exception as e:
                print(f"算法2处理失败: {e}")
                return None
        elif algorithm_index == 3:  # 导出矢状面
            try:
                if sk_index == 0:
                    file_name = predict3(file_name)
                else:
                    file_name = start_client(file_name, 3)
            except Exception as e:
                print(f"算法3处理失败: {e}")
                return None
        else:
            return None
        
        if file_name and os.path.exists(file_name):
            try:
                if algorithm_index == 1:
                    if hasattr(self.vtk_viewer, 'gong_neng1'):
                        self.vtk_viewer.gong_neng1(file_name)
                    if hasattr(self.vtk_viewer, 'add_actor1'):
                        self.vtk_viewer.add_actor1()
                    
                    checkBox_b1 = QCheckBox(name(file_name))
                    # 修复：使用新的方法添加复选框
                    gong_box_check.add_checkbox(checkBox_b1)
                    checkBox_b1.setChecked(True)
                    
                    # 修复：正确连接信号，传递状态参数
                    checkBox_b1.stateChanged.connect(
                        lambda state: self.toggle_actor1(state)
                    )
                    checkBox_b1.show()
                    
                    # 手动触发一次toggle_actor1以确保2D视图正确显示
                    self.toggle_actor1(2)  # 2表示Qt.Checked状态
                    
                    # 保存actor1引用
                    self.actor1 = self.vtk_viewer.actor1

                elif algorithm_index == 2:
                    if hasattr(self.vtk_viewer, 'gong_neng2'):
                        self.vtk_viewer.gong_neng2(file_name)
                    if hasattr(self.vtk_viewer, 'add_actor2'):
                        self.vtk_viewer.add_actor2()
                    
                    checkBox_b2 = QCheckBox(name(file_name))
                    # 修复：使用新的方法添加复选框
                    gong_box_check.add_checkbox(checkBox_b2)
                    checkBox_b2.setChecked(True)
                    
                    # 修复：正确连接信号，传递状态参数
                    checkBox_b2.stateChanged.connect(
                        lambda state: self.toggle_actor2(state)
                    )
                    checkBox_b2.show()
                    
                    # 手动触发一次toggle_actor2以确保2D视图正确显示
                    self.toggle_actor2(2)  
                    
                elif algorithm_index == 3:
                    if hasattr(self.vtk_viewer, 'gong_neng3'):
                        self.vtk_viewer.gong_neng3(file_name)
                    if hasattr(self.vtk_viewer, 'add_actor3'):
                        self.vtk_viewer.add_actor3()
                    
                    checkBox_b3 = QCheckBox(name(file_name))
                    # 修复：使用新的方法添加复选框
                    gong_box_check.add_checkbox(checkBox_b3) 
                    checkBox_b3.setChecked(True)
                    
                    # 修复：正确连接信号，传递状态参数
                    checkBox_b3.stateChanged.connect(
                        lambda state: self.toggle_actor3(state)
                    )
                    checkBox_b3.show()
                    
                    # 手动触发一次toggle_actor3以确保2D视图正确显示
                    self.toggle_actor3(2)  # 2表示Qt.Checked状态
                
                return file_name
            except Exception as e:
                print(f"VTK查看器操作失败: {e}")
                return None
        return None
    def process_postprocessing(self, file_name, gong_box_check, min_voxel_num=100):
        """
        处理后处理算法结果的3D可视化
        
        对模型预测结果进行形态学后处理操作，包括噪声去除、空洞填充和平滑处理等步骤，
        有效改善分割结果的质量和临床可用性。通过体素数量阈值过滤微小噪声区域，保留有意义的血管结构。
        
        Args:
            file_name (str): 待处理的投票融合结果文件路径
            gong_box_check (QVBoxLayout): 控制面板布局，用于添加结果控制复选框
            min_voxel_num (int): 最小体素数阈值，用于过滤噪声，默认值为100
            
        Returns:
            str: 后处理结果文件路径，失败时返回None
        """
        try:
            from postprocessing import postprocessing
            print(f"成功导入postprocessing模块")
        except ImportError as e:
            print(f"导入postprocessing模块失败: {e}")
            import traceback
            traceback.print_exc()
            return None

        try:
            # 执行后处理，传递用户输入的参数
            result_file = postprocessing(file_name, min_voxel_num=min_voxel_num)
            print(f"后处理完成，结果文件: {result_file}")
        except Exception as e:
            print(f"后处理失败: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        if result_file and os.path.exists(result_file):
            try:
                # 添加后处理结果到VTK视图
                if hasattr(self.vtk_viewer, 'gong_neng_post'):
                    self.vtk_viewer.gong_neng_post(result_file)
                    print("已调用gong_neng_post")
                if hasattr(self.vtk_viewer, 'add_actor_post'):
                    self.vtk_viewer.add_actor_post()
                    print("已调用add_actor_post")
                
                
                                # 添加复选框
                checkBox_post = QCheckBox("Post-processing Result")
                gong_box_check.add_checkbox(checkBox_post)
                checkBox_post.setChecked(True)
                
                # 连接信号
                checkBox_post.stateChanged.connect(
                    lambda state: self.toggle_actor_post(state)
                )
                checkBox_post.show()
                
                # 立即触发显示更新，确保2D视图也显示结果
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.postprocessing_displayed = True
                    # 获取后处理结果文件路径
                    post_result = "mha/Postprocessed_result.mha"  # 默认路径
                    # 如果有处理控件，尝试获取实际路径
                    if hasattr(main_window.processing_controls, 'postprocessing_result'):
                        post_result = main_window.processing_controls.postprocessing_result
                    # 确保路径不为None且文件存在
                    if post_result and os.path.exists(post_result):
                        main_window.fu_xuan_display.overlay_postprocessing_result(post_result)
                    else:
                        print(f"后处理结果文件不存在或路径无效: {post_result}")
                
                print("成功添加后处理结果复选框")
                
                return result_file
            except Exception as e:
                print(f"VTK查看器操作失败: {e}")
                import traceback
                traceback.print_exc()
                return None
        else:
            print(f"后处理结果文件不存在或为空: {result_file}")
            return None
    def toggle_actor1(self, state):
        """
        切换模型1（横断面）预测结果的显示状态
        
        根据复选框状态控制3D视图中模型1预测结果的可见性，并同步更新2D视图显示内容，
        实现多视图一致性显示控制。当取消选中时，检查是否需要恢复原始图像显示或更新组合显示状态。
        
        Args:
            state (int): 复选框状态（2-选中，0-未选中）
        """
        if self.vtk_viewer:
            if state == 2:  # Qt.Checked
                self.vtk_viewer.add_actor1()
                # 通知主窗口显示test1_1结果
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.test1_1_displayed = True
                    # 获取test1_1结果文件路径
                    test1_1_result = "mha/test1_1.mha"  # 默认路径
                    if os.path.exists(test1_1_result):
                        main_window.fu_xuan_display.overlay_test1_1_result(test1_1_result)
            else:
                self.vtk_viewer.delete_actor1()
                # 通知主窗口更新显示状态
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.test1_1_displayed = False
                    # 检查是否其他结果都未显示
                    if not (main_window.test2_2_displayed or main_window.test3_3_displayed or main_window.voting_fusion_displayed or main_window.postprocessing_displayed):
                        main_window.fu_xuan_display.restore_original_display()
                    else:
                        main_window.fu_xuan_display.update_combined_display()
    def toggle_actor2(self, state):
        """
        切换模型2（冠状面）预测结果的显示状态
        
        根据复选框状态控制3D视图中模型2预测结果的可见性，并同步更新2D视图显示内容，
        实现多视图一致性显示控制。当取消选中时，检查是否需要恢复原始图像显示或更新组合显示状态。
        
        Args:
            state (int): 复选框状态（2-选中，0-未选中）
        """
        if self.vtk_viewer:
            if state == 2:  # Qt.Checked
                self.vtk_viewer.add_actor2()
                # 通知主窗口显示test2_2结果
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.test2_2_displayed = True
                    # 获取test2_2结果文件路径
                    test2_2_result = "mha/test2_2.mha"  # 默认路径
                    if os.path.exists(test2_2_result):
                        main_window.fu_xuan_display.overlay_test2_2_result(test2_2_result)
            else:
                self.vtk_viewer.delete_actor2()
                # 通知主窗口更新显示状态
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.test2_2_displayed = False
                    # 检查是否其他结果都未显示
                    if not (main_window.test1_1_displayed or main_window.test3_3_displayed or main_window.voting_fusion_displayed or main_window.postprocessing_displayed):
                        main_window.fu_xuan_display.restore_original_display()
                    else:
                        main_window.fu_xuan_display.update_combined_display()

    
    def toggle_actor3(self, state):
        """
        切换模型3（矢状面）预测结果的显示状态
        
        根据复选框状态控制3D视图中模型3预测结果的可见性，并同步更新2D视图显示内容，
        实现多视图一致性显示控制。当取消选中时，检查是否需要恢复原始图像显示或更新组合显示状态。
        
        Args:
            state (int): 复选框状态（2-选中，0-未选中）
        """
        if self.vtk_viewer:
            if state == 2:  # Qt.Checked
                self.vtk_viewer.add_actor3()
                # 通知主窗口显示test3_3结果
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.test3_3_displayed = True
                    # 获取test3_3结果文件路径
                    test3_3_result = "mha/test3_3.mha"  # 默认路径
                    if os.path.exists(test3_3_result):
                        main_window.fu_xuan_display.overlay_test3_3_result(test3_3_result)
            else:
                self.vtk_viewer.delete_actor3()
                # 通知主窗口更新显示状态
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.test3_3_displayed = False
                    # 检查是否其他结果都未显示
                    if not (main_window.test1_1_displayed or main_window.test2_2_displayed or main_window.voting_fusion_displayed or main_window.postprocessing_displayed):
                        main_window.fu_xuan_display.restore_original_display()
                    else:
                        main_window.fu_xuan_display.update_combined_display()
    def toggle_actor4(self, state):
        """
        切换投票融合结果的显示状态
        
        根据复选框状态控制3D视图中投票融合结果的可见性，并同步更新2D视图显示内容，
        实现多视图一致性显示控制。当取消选中时，检查是否需要恢复原始图像显示或更新组合显示状态。
        
        Args:
            state (int): 复选框状态（2-选中，0-未选中）
        """
        if self.vtk_viewer:
            if state == 2:  # Qt.Checked
                self.vtk_viewer.add_actor4()
                # 通知主窗口显示votingFusion结果
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    if hasattr(self.vtk_viewer.main_window, 'processing_controls'):
                        main_window = self.vtk_viewer.main_window
                        main_window.voting_fusion_displayed = True
                        voting_result = main_window.processing_controls.voting_fusion_result
                        if voting_result and os.path.exists(voting_result):
                            main_window.fu_xuan_display.overlay_voting_fusion_result(voting_result)
            else:
                self.vtk_viewer.delete_actor4()
                # 通知主窗口更新显示状态
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.voting_fusion_displayed = False
                    # 检查是否其他结果都未显示
                    if not (main_window.test1_1_displayed or main_window.test2_2_displayed or main_window.test3_3_displayed or main_window.postprocessing_displayed):
                        main_window.fu_xuan_display.restore_original_display()
                    else:
                        main_window.fu_xuan_display.update_combined_display()
    def toggle_actor_post(self, state):
        """
        切换后处理结果的显示状态
        
        根据复选框状态控制3D视图中后处理结果的可见性，并同步更新2D视图显示内容，
        实现多视图一致性显示控制。当取消选中时，检查是否需要恢复原始图像显示或更新组合显示状态。
        
        Args:
            state (int): 复选框状态（2-选中，0-未选中）
        """
        if self.vtk_viewer:
            if state == 2:  # Qt.Checked
                self.vtk_viewer.add_actor_post()
                # 通知主窗口显示后处理结果的2D切片
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    # 获取后处理结果文件路径，使用动态获取而不是硬编码
                    if hasattr(self.vtk_viewer.main_window, 'processing_controls'):
                        main_window = self.vtk_viewer.main_window
                        main_window.postprocessing_displayed = True
                        post_result = "mha/Postprocessed_result.mha"  # 默认路径
                        # 如果有处理控件，尝试获取实际路径
                        if hasattr(main_window.processing_controls, 'postprocessing_result'):
                            post_result = main_window.processing_controls.postprocessing_result
                        if os.path.exists(post_result):
                            main_window.overlay_postprocessing_result(post_result)
                        else:
                            print(f"后处理结果文件不存在: {post_result}")
            else:
                self.vtk_viewer.delete_actor_post()
                # 通知主窗口更新显示状态
                if hasattr(self.vtk_viewer, 'main_window') and self.vtk_viewer.main_window:
                    main_window = self.vtk_viewer.main_window
                    main_window.postprocessing_displayed = False
                    # 检查是否其他结果都未显示
                    if not (main_window.test1_1_displayed or main_window.test2_2_displayed or main_window.test3_3_displayed or main_window.voting_fusion_displayed):
                        main_window.fu_xuan_display.restore_original_display()
                    else:
                        main_window.fu_xuan_display.update_combined_display()

    def resize_viewer(self, width, height):
        """
        调整VTK查看器显示尺寸以适应界面布局变化
        
        Args:
            width (int): 目标宽度（像素）
            height (int): 目标高度（像素）
        """
        if self.vtk_viewer:
            # 修复：使用Qt内置的resize方法替代不存在的resize_viewer
            self.vtk_viewer.resize(width, height)
            # 确保渲染窗口也更新大小
            self.vtk_viewer.GetRenderWindow().SetSize(width, height)