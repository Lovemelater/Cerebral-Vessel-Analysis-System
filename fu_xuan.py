import numpy as np
from basicfunction import load_mha

class FuXuanDisplay:
    """
    医学图像融合显示组件 - 负责处理和显示多个医学图像处理结果的叠加显示
   
    该组件实现了多模型结果的可视化融合，支持将多个血管分割模型的输出结果
    以不同颜色叠加显示在同一图像上，便于医生进行对比分析和诊断决策支持
   
    功能特性:
    1. 多模型结果融合显示 (voting fusion, postprocessing, test1_1, test2_2, test3_3)
    2. 多视图同步更新 (XY轴向, XZ冠状, YZ矢状)
    3. 颜色编码区分不同模型结果
    4. 显示优先级管理 (红色>黄色>蓝色>绿色>白色)
    5. 原始图像与处理结果的无缝切换
    """
    

    def __init__(self, image_display, image_processor, processing_controls):
        """
        初始化FuXuanDisplay组件 - 医学图像融合显示管理器
       
        Args:
            image_display (ImageDisplay): 图像显示组件，负责实际的图像渲染
            image_processor (ImageProcessor): 图像处理器，包含原始图像数据和处理逻辑
            processing_controls (ProcessingControls): 处理控制组件，用于获取文件路径等控制信息
        """
        self.image_display = image_display
        self.image_processor = image_processor
        self.processing_controls = processing_controls
        
        # 状态变量 - 跟踪各处理结果的显示状态
        self.voting_fusion_displayed = False  # 投票融合结果显示状态
        self.postprocessing_displayed = False  # 后处理结果显示状态
        self.test1_1_displayed = False  # test1_1模型结果显示状态
        self.test2_2_displayed = False  # test2_2模型结果显示状态
        self.test3_3_displayed = False  # test3_3模型结果显示状态
        
        # 数据存储 - 缓存各处理结果的四通道图像数据
        self.voting_fusion_data = None  # 投票融合结果数据 (黄色)
        self.postprocessing_data = None  # 后处理结果数据 (红色)
        self.test1_1_data = None  # test1_1模型结果数据 (白色)
        self.test2_2_data = None  # test2_2模型结果数据 (绿色)
        self.test3_3_data = None  # test3_3模型结果数据 (蓝色)
        self.original_image_data = None  # 原始图像数据
        self.original_data_for_voting = None  # 投票融合使用的原始数据
        self.original_data_for_postprocessing = None  # 后处理使用的原始数据
        self.original_data_for_test1_1 = None  # test1_1模型使用的原始数据
        self.original_data_for_test2_2 = None  # test2_2模型使用的原始数据
        self.original_data_for_test3_3 = None  # test3_3模型使用的原始数据


    def update_combined_display(self):
        """根据当前选中状态更新组合显示 - 实现多模型结果的智能融合显示
       
        该方法实现了医学图像处理中关键的可视化融合功能，采用颜色编码策略
        将多个模型的血管分割结果叠加显示在原始图像上，便于医生进行对比分析
       
        颜色编码方案 (显示优先级从高到低):
        1. 红色 (color_marker=0) - 后处理结果 (最高优先级)
        2. 黄色 (color_marker=1) - 投票融合结果
        3. 蓝色 (color_marker=4) - test3_3模型结果
        4. 绿色 (color_marker=3) - test2_2模型结果
        5. 白色 (color_marker=2) - test1_1模型结果 (最低优先级)
       
        四通道数据结构说明:
        - 第0通道: 原始图像数据，用于窗宽窗位调整
        - 第1通道: 血管标记通道，标记血管区域为1，其他为0
        - 第2通道: 保留通道，目前未使用
        - 第3通道: 颜色标记通道，用于区分不同模型结果
        """
        try:
            # 检查哪些结果正在显示
            # 确保与主窗口的状态同步
            if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                main_window = self.image_processor.main_window
                self.voting_fusion_displayed = main_window.voting_fusion_displayed
                self.postprocessing_displayed = main_window.postprocessing_displayed
                self.test1_1_displayed = main_window.test1_1_displayed
                self.test2_2_displayed = main_window.test2_2_displayed  # 同步test2_2状态
                self.test3_3_displayed = main_window.test3_3_displayed  # 同步test3_3状态
                
            voting_shown = self.voting_fusion_displayed and (self.voting_fusion_data is not None)
            post_shown = self.postprocessing_displayed and (self.postprocessing_data is not None)
            test1_1_shown = self.test1_1_displayed and (self.test1_1_data is not None)
            test2_2_shown = self.test2_2_displayed and (self.test2_2_data is not None)  # 检查test2_2是否显示
            test3_3_shown = self.test3_3_displayed and (self.test3_3_data is not None)  # 检查test3_3是否显示
            
            # 计算显示结果的数量
            shown_count = sum([int(voting_shown), int(post_shown), int(test1_1_shown), int(test2_2_shown), int(test3_3_shown)])
            
            # 如果多个结果都显示，创建组合显示
            if shown_count > 1:
                # 初始化组合数据为原始数据（四通道）
                if hasattr(self, 'original_image_data') and self.original_image_data:
                    original_data, image_xy, image_xz, image_yz = self.original_image_data
                    combined_xy = np.stack([
                        original_data,                    # 原始数据用于窗宽窗位调整
                        np.zeros_like(original_data),     # 血管标记
                        np.zeros_like(original_data),     # 占位符
                        np.zeros_like(original_data)      # 颜色标记
                    ], axis=-1)
                    combined_xz = np.stack([
                        np.transpose(original_data, (2, 0, 1)),     # XZ平面原始数据
                        np.zeros_like(np.transpose(original_data, (2, 0, 1))),     # XZ平面血管标记
                        np.zeros_like(np.transpose(original_data, (2, 0, 1))),  # 占位符
                        np.zeros_like(np.transpose(original_data, (2, 0, 1)))   # 颜色标记
                    ], axis=-1)
                    combined_xz = np.flip(combined_xz, axis=(0, 1))
                    combined_yz = np.stack([
                        np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0)),  # YZ平面原始数据
                        np.flip(np.transpose(np.zeros_like(original_data), (1, 0, 2)), axis=(1, 0)),  # YZ平面血管标记
                        np.zeros_like(np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0))),  # 占位符
                        np.zeros_like(np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0)))   # 颜色标记
                    ], axis=-1)
                else:
                    return
                
                # 按优先级叠加数据：test1_1 (白色) < test2_2 (绿色) < test3_3 (蓝色) < votingFusion (黄色) < postprocessing (红色)
                if test1_1_shown:
                    test_xy, test_xz, test_yz = self.test1_1_data
                    # 白色标记 (color_marker=2)
                    combined_xy[test_xy[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xy[test_xy[:, :, :, 1] == 1, 3] = 2  # 白色标记
                    
                    combined_xz[test_xz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xz[test_xz[:, :, :, 1] == 1, 3] = 2  # 白色标记
                    
                    combined_yz[test_yz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_yz[test_yz[:, :, :, 1] == 1, 3] = 2  # 白色标记
                
                if test2_2_shown:
                    test2_xy, test2_xz, test2_yz = self.test2_2_data
                    # 绿色标记 (color_marker=3)
                    combined_xy[test2_xy[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xy[test2_xy[:, :, :, 1] == 1, 3] = 3  # 绿色标记
                    
                    combined_xz[test2_xz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xz[test2_xz[:, :, :, 1] == 1, 3] = 3  # 绿色标记
                    
                    combined_yz[test2_yz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_yz[test2_yz[:, :, :, 1] == 1, 3] = 3  # 绿色标记
                    
                if test3_3_shown:
                    test3_xy, test3_xz, test3_yz = self.test3_3_data
                    # 蓝色标记 (color_marker=4)
                    combined_xy[test3_xy[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xy[test3_xy[:, :, :, 1] == 1, 3] = 4  # 蓝色标记
                    
                    combined_xz[test3_xz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xz[test3_xz[:, :, :, 1] == 1, 3] = 4  # 蓝色标记
                    
                    combined_yz[test3_yz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_yz[test3_yz[:, :, :, 1] == 1, 3] = 4  # 蓝色标记
                
                if voting_shown:
                    voting_xy, voting_xz, voting_yz = self.voting_fusion_data
                    # 黄色标记 (color_marker=1)
                    combined_xy[voting_xy[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xy[voting_xy[:, :, :, 1] == 1, 3] = 1  # 黄色标记
                    
                    combined_xz[voting_xz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xz[voting_xz[:, :, :, 1] == 1, 3] = 1  # 黄色标记
                    
                    combined_yz[voting_yz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_yz[voting_yz[:, :, :, 1] == 1, 3] = 1  # 黄色标记
                
                if post_shown:
                    post_xy, post_xz, post_yz = self.postprocessing_data
                    # 红色标记 (color_marker=0) - 最高优先级
                    combined_xy[post_xy[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xy[post_xy[:, :, :, 1] == 1, 3] = 0  # 红色标记
                    
                    combined_xz[post_xz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_xz[post_xz[:, :, :, 1] == 1, 3] = 0  # 红色标记
                    
                    combined_yz[post_yz[:, :, :, 1] == 1, 1] = 1  # 血管标记
                    combined_yz[post_yz[:, :, :, 1] == 1, 3] = 0  # 红色标记
                
                # 更新显示
                self.image_display.set_image_data(combined_xy, combined_xz, combined_yz)
                # 使用MainWindow实例的update_image_displays方法
                if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                    self.image_processor.main_window.update_image_displays()
                print("已组合显示test1_1（白色）、test2_2（绿色）、test3_3（蓝色）、votingFusion（黄色）和postprocessing（红色）结果")
                
            # 如果只显示一个结果
            elif test1_1_shown:
                test_xy, test_xz, test_yz = self.test1_1_data
                self.image_display.set_image_data(test_xy, test_xz, test_yz)
                # 使用MainWindow实例的update_image_displays方法
                if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                    self.image_processor.main_window.update_image_displays()
                print("已显示test1_1结果（白色）")
                
            elif test2_2_shown:
                test2_xy, test2_xz, test2_yz = self.test2_2_data
                self.image_display.set_image_data(test2_xy, test2_xz, test2_yz)
                # 使用MainWindow实例的update_image_displays方法
                if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                    self.image_processor.main_window.update_image_displays()
                print("已显示test2_2结果（绿色）")
                
            elif test3_3_shown:
                test3_xy, test3_xz, test3_yz = self.test3_3_data
                self.image_display.set_image_data(test3_xy, test3_xz, test3_yz)
                # 使用MainWindow实例的update_image_displays方法
                if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                    self.image_processor.main_window.update_image_displays()
                print("已显示test3_3结果（蓝色）")
                
            elif voting_shown:
                voting_xy, voting_xz, voting_yz = self.voting_fusion_data
                self.image_display.set_image_data(voting_xy, voting_xz, voting_yz)
                # 使用MainWindow实例的update_image_displays方法
                if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                    self.image_processor.main_window.update_image_displays()
                print("已显示votingFusion结果（黄色）")
                
            elif post_shown:
                post_xy, post_xz, post_yz = self.postprocessing_data
                self.image_display.set_image_data(post_xy, post_xz, post_yz)
                # 使用MainWindow实例的update_image_displays方法
                if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                    self.image_processor.main_window.update_image_displays()
                print("已显示postprocessing结果（红色）")
                
            # 如果没有结果显示，恢复原始图像
            else:
                self.restore_original_display()
                
        except Exception as e:
            print(f"更新组合显示时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def combine_overlay_data(self, voting_data, post_data):
        """
        组合votingFusion和postprocessing的叠加数据 - 实现双模型结果融合
       
        Args:
            voting_data: votingFusion四通道数据 (黄色标记)
            post_data: postprocessing四通道数据 (红色标记)
            
        Returns:
            combined_data: 组合后的四通道数据，红色标记优先级高于黄色
        """
        # 创建组合数据，后处理结果优先显示为红色，voting结果显示为黄色
        combined_data = np.copy(voting_data)  # 以voting数据为基础
        
        # 获取后处理标记
        post_mask = post_data[:, :, :, 1] == 1  # 后处理标记为1的位置
        
        # 在后处理标记位置设置红色（color_marker=0）
        combined_data[post_mask, 1] = post_data[post_mask, 1]  # 血管标记
        combined_data[post_mask, 3] = 0  # 红色标记
        
        return combined_data

    def restore_original_display(self):
        """恢复显示原始图像 - 重置视图为原始医学图像
       
        当所有处理结果的显示都被关闭时，调用此方法恢复到原始图像显示状态
        确保用户能够随时回到未经处理的原始医学图像状态
        """
        # 检查是否有保存的原始数据
        if hasattr(self, 'original_image_data') and self.original_image_data:
            original_data, image_xy, image_xz, image_yz = self.original_image_data
            
            # 恢复原始图像数据
            self.image_display.set_image_data(image_xy, image_xz, image_yz)
            
            # 更新图像显示
            if hasattr(self.image_processor, 'main_window') and self.image_processor.main_window:
                self.image_processor.main_window.update_image_displays()
            print("已恢复原始图像显示")

    def create_four_channel_overlay(self, original_data, overlay_data, color_marker=0):
        """
        创建四通道叠加图像数据 - 统一多模型结果的可视化格式
       
        该方法将二值化的血管分割结果转换为统一的四通道格式，确保所有模型结果
        在可视化时具有一致的数据结构和显示效果
       
        四通道数据结构说明:
        - 第0通道: 原始图像数据，用于窗宽窗位调整
        - 第1通道: 血管标记通道，标记血管区域为1，其他为0
        - 第2通道: 保留通道，目前未使用，统一设为0
        - 第3通道: 颜色标记通道，用于区分不同模型结果
       
        Args:
            original_data (numpy.ndarray): 原始医学图像数据 (3D)
            overlay_data (numpy.ndarray): 待叠加的处理结果数据 (3D)
            color_marker (int): 颜色标记 (0=红色,1=黄色,2=白色,3=绿色,4=蓝色)
            
        Returns:
            tuple: (overlay_xy, overlay_xz, overlay_yz) 三个方向的四通道叠加数据
                  - overlay_xy: XY平面(轴向)四通道数据
                  - overlay_xz: XZ平面(冠状)四通道数据
                  - overlay_yz: YZ平面(矢状)四通道数据
        """
        try:
            print(f"原始数据形状: {original_data.shape}")
            print(f"叠加数据形状: {overlay_data.shape}")
            print(f"叠加数据值范围: {overlay_data.min()} - {overlay_data.max()}")
            
            # 确保两个数据的形状一致
            if original_data.shape != overlay_data.shape:
                raise ValueError(f"原始数据和叠加数据形状不匹配: {original_data.shape} vs {overlay_data.shape}")
            
            # 将叠加数据二值化，确保只有0和1
            overlay_binary = (overlay_data > 0).astype(np.uint8)
            print(f"二值化叠加数据值范围: {overlay_binary.min()} - {overlay_binary.max()}")
            
            # 创建带有标记信息的图像数据
            # XY平面（轴向视图）- 沿着Z轴切片 (对应image_xy)
            overlay_data_xy = np.stack([
                original_data,                    # 原始数据用于窗宽窗位调整
                overlay_binary,                   # XY平面血管标记
                np.zeros_like(original_data),     # 占位符
                np.full_like(original_data, color_marker)  # 颜色标记
            ], axis=-1)
            
            # XZ平面（冠状视图）- 沿着Y轴切片 (对应image_xz)
            overlay_data_xz = np.stack([
                np.transpose(original_data, (2, 0, 1)),     # XZ平面原始数据
                np.transpose(overlay_binary, (2, 0, 1)),    # XZ平面血管标记
                np.zeros_like(np.transpose(original_data, (2, 0, 1))),  # 占位符
                np.full_like(np.transpose(original_data, (2, 0, 1)), color_marker)  # 颜色标记
            ], axis=-1)
            overlay_data_xz = np.flip(overlay_data_xz, axis=(0, 1))
            
            # YZ平面（矢状视图）- 沿着X轴切片 (对应image_yz)
            overlay_data_yz = np.stack([
                np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0)),  # YZ平面原始数据
                np.flip(np.transpose(overlay_binary, (1, 0, 2)), axis=(1, 0)), # YZ平面血管标记
                np.zeros_like(np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0))),  # 占位符
                np.full_like(np.flip(np.transpose(original_data, (1, 0, 2)), axis=(1, 0)), color_marker)  # 颜色标记
            ], axis=-1)
            
            return overlay_data_xy, overlay_data_xz, overlay_data_yz
                
        except Exception as e:
            print(f"创建四通道叠加数据时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, None, None


    def overlay_test1_1_result(self, test1_1_file):
        """将test1_1结果叠加到原始图像上（白色显示）- 加载并显示test1_1模型结果
       
        Args:
            test1_1_file (str): test1_1模型结果文件路径 (.mha格式)
        """
        try:
            # 获取原始文件路径
            original_file = self.processing_controls.get_file_name()
            if not original_file:
                print("未找到原始文件")
                return
                
            # 加载原始数据和test1_1数据
            original_data, _, _ = load_mha(original_file)
            test1_1_data, _, _ = load_mha(test1_1_file)
            
            # 创建与votingFusion相同的四通道格式数据，白色显示
            overlay_xy, overlay_xz, overlay_yz = self.create_four_channel_overlay(
                original_data, test1_1_data, color_marker=2)  # 2表示白色
            
            if overlay_xy is not None and overlay_xz is not None and overlay_yz is not None:
                # 保存test1_1数据
                self.test1_1_data = (overlay_xy, overlay_xz, overlay_yz)
                self.original_data_for_test1_1 = (original_data, 
                                                 self.image_processor.image_xy, 
                                                 self.image_processor.image_xz, 
                                                 self.image_processor.image_yz)
                if not hasattr(self, 'original_image_data') or self.original_image_data is None:
                    self.original_image_data = (original_data, 
                                                self.image_processor.image_xy, 
                                                self.image_processor.image_xz, 
                                                self.image_processor.image_yz)
                # 更新显示状态
                self.test1_1_displayed = True
                
                # 根据当前显示状态更新界面
                self.update_combined_display()
                
        except Exception as e:
            print(f"叠加test1_1结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            

    def overlay_test2_2_result(self, test2_2_file):
        """将test2_2结果叠加到原始图像上（绿色显示）- 加载并显示test2_2模型结果
       
        Args:
            test2_2_file (str): test2_2模型结果文件路径 (.mha格式)
        """
        try:
            # 获取原始文件路径
            original_file = self.processing_controls.get_file_name()
            if not original_file:
                print("未找到原始文件")
                return
                
            # 加载原始数据和test2_2数据
            original_data, _, _ = load_mha(original_file)
            test2_2_data, _, _ = load_mha(test2_2_file)
            
            # 创建与votingFusion相同的四通道格式数据，绿色显示
            overlay_xy, overlay_xz, overlay_yz = self.create_four_channel_overlay(
                original_data, test2_2_data, color_marker=3)  # 3表示绿色
            
            if overlay_xy is not None and overlay_xz is not None and overlay_yz is not None:
                # 保存test2_2数据
                self.test2_2_data = (overlay_xy, overlay_xz, overlay_yz)
                self.original_data_for_test2_2 = (original_data, 
                                                 self.image_processor.image_xy, 
                                                 self.image_processor.image_xz, 
                                                 self.image_processor.image_yz)
                if not hasattr(self, 'original_image_data') or self.original_image_data is None:
                    self.original_image_data = (original_data, 
                                                self.image_processor.image_xy, 
                                                self.image_processor.image_xz, 
                                                self.image_processor.image_yz)
                # 更新显示状态
                self.test2_2_displayed = True
                
                # 根据当前显示状态更新界面
                self.update_combined_display()
                
        except Exception as e:
            print(f"叠加test2_2结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def overlay_test3_3_result(self, test3_3_file):
        """将test3_3结果叠加到原始图像上（蓝色显示）- 加载并显示test3_3模型结果
       
        Args:
            test3_3_file (str): test3_3模型结果文件路径 (.mha格式)
        """
        try:
            # 获取原始文件路径
            original_file = self.processing_controls.get_file_name()
            if not original_file:
                print("未找到原始文件")
                return
                
            # 加载原始数据和test3_3数据
            original_data, _, _ = load_mha(original_file)
            test3_3_data, _, _ = load_mha(test3_3_file)
            
            # 创建与votingFusion相同的四通道格式数据，蓝色显示
            overlay_xy, overlay_xz, overlay_yz = self.create_four_channel_overlay(
                original_data, test3_3_data, color_marker=4)  # 4表示蓝色
            
            if overlay_xy is not None and overlay_xz is not None and overlay_yz is not None:
                # 保存test3_3数据
                self.test3_3_data = (overlay_xy, overlay_xz, overlay_yz)
                self.original_data_for_test3_3 = (original_data, 
                                                 self.image_processor.image_xy, 
                                                 self.image_processor.image_xz, 
                                                 self.image_processor.image_yz)
                if not hasattr(self, 'original_image_data') or self.original_image_data is None:
                    self.original_image_data = (original_data, 
                                                self.image_processor.image_xy, 
                                                self.image_processor.image_xz, 
                                                self.image_processor.image_yz)
                # 更新显示状态
                self.test3_3_displayed = True
                
                # 根据当前显示状态更新界面
                self.update_combined_display()
                
        except Exception as e:
            print(f"叠加test3_3结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()


    def overlay_postprocessing_result(self, postprocessing_file):
        """将后处理结果叠加到原始图像上（红色显示）- 加载并显示后处理结果
       
        Args:
            postprocessing_file (str): 后处理结果文件路径 (.mha格式)
        """
        try:
            # 获取原始文件路径
            original_file = self.processing_controls.get_file_name()
            if not original_file:
                print("未找到原始文件")
                return
                
            # 加载原始数据和后处理数据
            original_data, _, _ = load_mha(original_file)
            postprocessing_data, _, _ = load_mha(postprocessing_file)
            
            # 创建与votingFusion相同的四通道格式数据，红色显示
            overlay_xy, overlay_xz, overlay_yz = self.create_four_channel_overlay(
                original_data, postprocessing_data, color_marker=0)  # 0表示红色
            
            if overlay_xy is not None and overlay_xz is not None and overlay_yz is not None:
                # 保存后处理数据
                self.postprocessing_data = (overlay_xy, overlay_xz, overlay_yz)
                self.original_data_for_postprocessing = (original_data, 
                                                        self.image_processor.image_xy, 
                                                        self.image_processor.image_xz, 
                                                        self.image_processor.image_yz)
                if not hasattr(self, 'original_image_data') or self.original_image_data is None:
                    self.original_image_data = (original_data, 
                                                self.image_processor.image_xy, 
                                                self.image_processor.image_xz, 
                                                self.image_processor.image_yz)
                # 更新显示状态
                self.postprocessing_displayed = True
                
                # 根据当前显示状态更新界面
                self.update_combined_display()
                print(f"成功加载并显示后处理结果: {postprocessing_file}")
            else:
                print("创建后处理叠加数据失败")
                
        except Exception as e:
            print(f"叠加后处理结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()

    def overlay_voting_fusion_result(self, voting_file):
        """将投票融合结果叠加到原始图像上（黄色显示）- 加载并显示投票融合结果
       
        Args:
            voting_file (str): 投票融合结果文件路径 (.mha格式)
        """
        try:
            # 获取原始文件路径
            original_file = self.processing_controls.get_file_name()
            if not original_file:
                print("未找到原始文件")
                return
                
            # 加载原始数据和投票融合数据
            original_data, _, _ = load_mha(original_file)
            voting_data, _, _ = load_mha(voting_file)
            
            # 创建与votingFusion相同的四通道格式数据，黄色显示
            overlay_xy, overlay_xz, overlay_yz = self.create_four_channel_overlay(
                original_data, voting_data, color_marker=1)  # 1表示黄色
            
            if overlay_xy is not None and overlay_xz is not None and overlay_yz is not None:
                # 保存投票融合数据
                self.voting_fusion_data = (overlay_xy, overlay_xz, overlay_yz)
                self.original_data_for_voting = (original_data, 
                                                self.image_processor.image_xy, 
                                                self.image_processor.image_xz, 
                                                self.image_processor.image_yz)
                if not hasattr(self, 'original_image_data') or self.original_image_data is None:
                    self.original_image_data = (original_data, 
                                                self.image_processor.image_xy, 
                                                self.image_processor.image_xz, 
                                                self.image_processor.image_yz)
                # 更新显示状态
                self.voting_fusion_displayed = True
                
                # 根据当前显示状态更新界面
                self.update_combined_display()
                print(f"成功加载并显示投票融合结果: {voting_file}")
            else:
                print("创建投票融合叠加数据失败")
                
        except Exception as e:
            print(f"叠加投票融合结果时出错: {str(e)}")
            import traceback
            traceback.print_exc()