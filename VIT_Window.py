"""
VIT_Window.py
VTK三维可视化组件，负责医学图像的三维重建和交互式可视化

主要功能包括：
1. 三维体绘制：支持MHA格式医学图像的三维可视化
2. 多模态显示：可同时显示原始图像和多种处理结果（血管分割、脑区分割等）
3. 交互控制：提供窗宽窗位调节、切片浏览等交互功能
4. 多视图同步：支持四个视图的联动显示（三切面视图+3D视图）

技术特点：
- 基于VTK（Visualization Toolkit）实现高性能三维渲染
- 使用Marching Cubes算法进行等值面提取
- 支持多标签数据的独立显示和叠加显示
"""

from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
from PyQt5.QtWidgets import QFrame, QMessageBox
import os

class VtkViewer1(QVTKRenderWindowInteractor):
    """
    VTK三维可视化查看器类
    实现医学图像的三维重建和交互式操作功能
    """
    
    def __init__(self, parent: QFrame):
        """
        初始化VTK查看器
        
        Args:
            parent (QFrame): 父级容器组件
        """
        super().__init__(parent=parent)
        # 初始化所有必要的VTK组件属性
        self.reader = None                      # 图像数据读取器
        self.vessel_mapper = None               # 多边形数据映射器
        self.outline_actor = None               # 轮廓演员（基础图像表示）
        self.ren = []                           # 渲染器列表
        self.ren_win = None                     # 渲染窗口
        self.iren = None                        # 交互器
        self.picker = None                      # 单元拾取器
        self.ipw_prop = None                    # 平面属性
        self.image_prop = None                  # 图像属性
        self.plane_widgets = []                 # 切片平面控件列表
        self.actor1 = None                      # 功能演员1（白色）
        self.actor2 = None                      # 功能演员2（绿色）
        self.actor3 = None                      # 功能演员3（蓝色）
        self.actor4 = None                      # 功能演员4（黄色）
        self.actor_post = None                  # 后处理结果演员（红色）
        
        # 添加空状态标志，标识是否有数据加载
        self.is_empty = True

    def all(self):
        """
        初始化VTK组件系统，构建完整的三维可视化环境
        不加载实际数据，仅建立可视化框架
        """
        # 创建元图像读取器但暂不关联文件
        self.reader = vtk.vtkMetaImageReader()
        
        # 创建多边形数据映射器，用于等值面渲染
        self.vessel_mapper = vtk.vtkPolyDataMapper()
        
        # 创建轮廓演员作为基础图像表示
        self.outline_actor = vtk.vtkActor()
        self.outline_actor.SetMapper(self.vessel_mapper)

        # 配置渲染窗口，禁用多重采样以提高性能
        self.ren_win = self.GetRenderWindow()
        self.ren_win.SetMultiSamples(0)

        # 创建四个渲染器（虽然目前只使用第4个）
        self.ren = []  # 重新初始化渲染器列表
        for i in range(4):
            self.ren.append(vtk.vtkRenderer())

        # 将主渲染器添加到渲染窗口
        self.ren_win.AddRenderer(self.ren[3])
        self.iren = self.GetRenderWindow().GetInteractor()

        # 配置单元拾取器，用于交互选择
        self.picker = vtk.vtkCellPicker()
        self.picker.SetTolerance(0.005)
        
        # 设置平面和图像属性
        self.ipw_prop = vtk.vtkProperty()
        self.image_prop = vtk.vtkImageProperty()
        self.image_prop.SetColorLevel(0)  # 设置窗位初始值
        self.image_prop.SetColorWindow(0)  # 设置窗宽初始值

        # 创建三个正交平面控件（矢状面、冠状面、横截面）
        self.plane_widgets = []  # 重新初始化平面控件列表
        for i in range(3):
            self.plane_widgets.append(vtk.vtkImagePlaneWidget())

        # 配置平面控件的基本属性
        for i in range(3):
            self.plane_widgets[i].SetInteractor(self.iren)
            self.plane_widgets[i].SetPicker(self.picker)
            self.plane_widgets[i].RestrictPlaneToVolumeOn()
            # 设置平面颜色（RGB），分别对应不同方向
            color = [0, 0, 0]
            color[i] = 1
            self.plane_widgets[i].GetPlaneProperty().SetColor(color)
            self.plane_widgets[i].SetTexturePlaneProperty(self.ipw_prop)
            self.plane_widgets[i].TextureInterpolateOff()
            self.plane_widgets[i].SetResliceInterpolateToLinear()
            self.plane_widgets[i].SetPlaneOrientation(i)
            self.plane_widgets[i].SetSliceIndex(0)
            self.plane_widgets[i].SetWindowLevel(4096, 0)
            self.plane_widgets[i].Off()  # 初始关闭平面小部件
            self.plane_widgets[i].InteractionOff()

        # 添加基础演员到渲染器并设置背景色
        self.ren[3].AddActor(self.outline_actor)
        self.ren[3].SetBackground(0.245, 0.245, 0.245)  # 深灰色背景
        
        # 重置相机并执行首次渲染
        self.ren[3].ResetCamera()
        self.ren_win.Render()

        # 设置交互样式为轨迹球相机模式
        self.style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.style)
        
        # 标记为无数据状态
        self.is_empty = True

    def clear_actors(self):
        """
        清除所有添加的可视化演员对象
        用于重置显示状态或切换数据集时清理旧的可视化内容
        """
        # 移除所有可能添加的演员对象
        if self.actor1:
            self.ren[3].RemoveActor(self.actor1)
        if self.actor2:
            self.ren[3].RemoveActor(self.actor2)
        if self.actor3:
            self.ren[3].RemoveActor(self.actor3)
        if self.actor4:
            self.ren[3].RemoveActor(self.actor4)
        if self.actor_post:
            self.ren[3].RemoveActor(self.actor_post)
            
        # 重置演员引用
        self.actor1 = None
        self.actor2 = None
        self.actor3 = None
        self.actor4 = None
        self.actor_post = None
        
        # 重新渲染场景
        if self.ren_win:
            self.ren_win.Render()

    def setup_camera(self):
        """
        精确设置相机参数，解决初始视图过大和旋转中心偏移问题
        确保三维对象完整显示在视口中且具有良好的观察角度
        """
        # 检查数据有效性
        if not self.reader or not self.reader.GetOutput():
            return
            
        try:
            bounds = self.reader.GetOutput().GetBounds()
            # 检查边界是否有效
            if bounds[1] <= bounds[0] or bounds[3] <= bounds[2] or bounds[5] <= bounds[4]:
                return
        except:
            return
            
        # 计算对象包围盒的中心点
        center = [
            (bounds[0] + bounds[1]) / 2.0,
            (bounds[2] + bounds[3]) / 2.0,
            (bounds[4] + bounds[5]) / 2.0
        ]
        
        # 计算包围盒对角线长度，用于确定观察距离
        diagonal = (
            (bounds[1] - bounds[0]) ** 2 +
            (bounds[3] - bounds[2]) ** 2 +
            (bounds[5] - bounds[4]) ** 2
        ) ** 0.5
        
        # 获取当前活动相机
        camera = self.ren[3].GetActiveCamera()
        # 设置相机焦点为中心点
        camera.SetFocalPoint(center[0], center[1], center[2])
        
        # 设置相机位置，确保能看到整个对象
        camera.SetPosition(
            center[0], 
            center[1], 
            center[2] + diagonal * 1.5  # 距离中心1.5倍对角线长度
        )
        
        # 设置相机朝上方向为Y轴正向
        camera.SetViewUp(0, 1, 0)
        
        # 设置近裁剪面和远裁剪面范围
        camera.SetClippingRange(diagonal * 0.1, diagonal * 10.0)
        
        # 重置相机，使其适应整个场景
        self.ren[3].ResetCamera()
        
        # 微调视角，适度放大视图
        camera.Zoom(0.8)
        
        self.ren_win.Render()

    def change_file(self, file_name):
        """
        更换当前显示的医学图像文件
        
        Args:
            file_name (str): 新的MHA图像文件路径
        """
        # 检查文件是否存在
        if not os.path.exists(file_name):
            QMessageBox.warning(None, "文件错误", f"文件 {file_name} 不存在！")
            return
            
        try:
            # 设置新文件并更新读取器
            self.reader.SetFileName(file_name)
            self.reader.Update()
            
            # 检查数据是否有效
            if not self.reader.GetOutput() or self.reader.GetOutput().GetNumberOfPoints() == 0:
                QMessageBox.warning(None, "数据错误", "文件没有有效数据！")
                return
                
            # 更新等值面映射器的输入连接
            self.vessel_mapper.SetInputConnection(self.reader.GetOutputPort())
            
            # 重置平面控件以适配新数据
            self.reset_plane_widgets()
            
            # 文件更改后重新设置相机参数
            self.setup_camera()
            
            self.is_empty = False
            
            # 开启所有平面控件的交互功能
            for widget in self.plane_widgets:
                widget.On()
                widget.InteractionOn()
                
            self.ren_win.Render()
        except Exception as e:
            QMessageBox.critical(None, "加载错误", f"加载文件失败: {str(e)}")

    def reset_plane_widgets(self):
        """
        重置平面控件，确保其正确连接到当前数据源
        保证各方向切片能够正确显示当前数据
        """
        if not self.reader:
            return
            
        # 为每个平面控件设置正确的输入连接
        for i, plane_widget in enumerate(self.plane_widgets):
            # 确保平面方向设置正确
            if plane_widget.GetPlaneOrientation() != i:
                plane_widget.SetPlaneOrientation(i)
            plane_widget.SetInputConnection(self.reader.GetOutputPort())

    def set_window_level(self, window_width, window_level):
        """
        设置窗宽窗位参数，控制图像对比度和亮度显示效果
        
        Args:
            window_width (float): 窗宽值，控制对比度
            window_level (float): 窗位值，控制亮度
        """
        # 为所有平面控件应用新的窗宽窗位设置
        for plane_widget in self.plane_widgets:
            plane_widget.SetWindowLevel(window_width, window_level)
        self.ren_win.Render()

    def change_slice(self, plane_index, slice_index):
        """
        更改指定方向的切片索引
        
        Args:
            plane_index (int): 平面索引（0-矢状面，1-冠状面，2-横截面）
            slice_index (int): 切片索引
        """
        # 边界检查后设置指定平面的切片索引
        if 0 <= plane_index < len(self.plane_widgets):
            self.plane_widgets[plane_index].SetSliceIndex(slice_index)
            self.ren_win.Render()
        
    def create_actor(self, filename, r, g, b):
        """
        创建三维可视化演员对象的通用方法
        使用Marching Cubes算法提取等值面并创建对应的可视化演员
        
        Args:
            filename (str): 数据文件路径
            r (float): 红色分量 (0.0-1.0)
            g (float): 绿色分量 (0.0-1.0)
            b (float): 蓝色分量 (0.0-1.0)
            
        Returns:
            vtkActor: 创建的演员对象
        """
        # 创建元图像读取器并加载数据
        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(filename)
        reader.Update()

        # 使用Marching Cubes算法提取等值面
        marchingCubes = vtk.vtkMarchingCubes()
        marchingCubes.SetInputConnection(reader.GetOutputPort())
        marchingCubes.SetValue(0, 100)

        # 根据文件名判断数据类型并设置合适的阈值
        if "votingFusion" in filename:
            marchingCubes.SetValue(0, 0.5)  # 投票融合结果使用0.5作为阈值
        elif "test1" in filename:
            marchingCubes.SetValue(0, 0.5)  # 矢状面数据使用0.5作为阈值
        elif "test2" in filename:
            marchingCubes.SetValue(0, 0.5)  # 冠状面数据使用0.5作为阈值
        elif "test3" in filename:
            marchingCubes.SetValue(0, 0.5)  # 横截面数据使用0.5作为阈值
        else:
            marchingCubes.SetValue(0, 0.5)  # 默认使用0.5作为阈值


        # 剔除冗余的数据单元，优化网格结构
        stripper = vtk.vtkStripper()
        stripper.SetInputConnection(marchingCubes.GetOutputPort())

        # 创建多边形数据映射器
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(stripper.GetOutputPort())
        mapper.ScalarVisibilityOff()

        # 创建演员对象并设置材质属性
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(r, g, b)  # 设置颜色
        actor.GetProperty().SetSpecular(.3)    # 设置镜面反射强度
        actor.GetProperty().SetSpecularPower(50)  # 设置高光系数
        actor.GetProperty().SetAmbient(0.3)    # 增加环境光反射
        actor.GetProperty().SetDiffuse(0.7)    # 设置漫反射强度
        
        return actor

    def gong_neng1(self, filename):
        """
        创建功能1的可视化演员（白色）
        
        Args:
            filename (str): 功能1对应的数据文件路径
        """
        self.actor1 = self.create_actor(filename, 1, 1, 1)  # 白色

    def gong_neng2(self, filename):
        """
        创建功能2的可视化演员（绿色）
        
        Args:
            filename (str): 功能2对应的数据文件路径
        """
        self.actor2 = self.create_actor(filename, 0, 1, 0)  # 绿色

    def gong_neng3(self, filename):
        """
        创建功能3的可视化演员（蓝色）
        
        Args:
            filename (str): 功能3对应的数据文件路径
        """
        self.actor3 = self.create_actor(filename, 0, 0, 1)  # 蓝色

    def gong_neng4(self, filename):
        """
        创建功能4的可视化演员（黄色）
        
        Args:
            filename (str): 功能4对应的数据文件路径
        """
        self.actor4 = self.create_actor(filename, 1, 1, 0)  # 黄色

    def add_actor4(self):
        """将功能4演员添加到渲染场景中并刷新显示"""
        self.ren[3].AddActor(self.actor4)
        self.reader.Update()
        self.ren_win.Render()

    def delete_actor4(self):
        """从渲染场景中移除功能4演员并刷新显示"""
        self.ren[3].RemoveActor(self.actor4)
        self.reader.Update()
        self.ren_win.Render()

    def add_actor1(self):
        """将功能1演员添加到渲染场景中并刷新显示"""
        self.ren[3].AddActor(self.actor1)
        self.reader.Update()
        self.ren_win.Render()
        
    def delete_actor1(self):
        """从渲染场景中移除功能1演员并刷新显示"""
        self.ren[3].RemoveActor(self.actor1)
        self.reader.Update()
        self.ren_win.Render()

    def add_actor2(self):
        """将功能2演员添加到渲染场景中并刷新显示"""
        self.ren[3].AddActor(self.actor2)
        self.reader.Update()
        self.ren_win.Render()
        
    def delete_actor2(self):
        """从渲染场景中移除功能2演员并刷新显示"""
        self.ren[3].RemoveActor(self.actor2)
        self.reader.Update()
        self.ren_win.Render()

    def add_actor3(self):
        """将功能3演员添加到渲染场景中并刷新显示"""
        self.ren[3].AddActor(self.actor3)
        self.reader.Update()
        self.ren_win.Render()
        
    def delete_actor3(self):
        """从渲染场景中移除功能3演员并刷新显示"""
        self.ren[3].RemoveActor(self.actor3)
        self.reader.Update()
        self.ren_win.Render()

    def add_actorself(self):
        """将基础图像演员添加到渲染场景中并刷新显示"""
        self.ren[3].AddActor(self.outline_actor)
        self.reader.Update()
        self.ren_win.Render()

    def delete_actorself(self):
        """从渲染场景中移除基础图像演员并刷新显示"""
        self.ren[3].RemoveActor(self.outline_actor)
        self.reader.Update()
        self.ren_win.Render()
        
    def gong_neng_post(self, filename):
        """
        创建后处理结果的可视化演员（红色）
        
        Args:
            filename (str): 后处理结果数据文件路径
        """
        self.actor_post = self.create_actor(filename, 1, 0, 0)  # 红色

    def add_actor_post(self):
        """添加后处理结果演员到渲染器并刷新显示"""
        if self.actor_post:
            self.ren[3].AddActor(self.actor_post)
            self.reader.Update()
            self.ren_win.Render()

    def delete_actor_post(self):
        """从渲染器中移除后处理结果演员并刷新显示"""
        if self.actor_post:
            self.ren[3].RemoveActor(self.actor_post)
            self.reader.Update()
            self.ren_win.Render()

    # 添加控制2D切片显示的方法
    def show_slice_actors(self):
        """显示投票融合结果的三个方向切片视图"""
        # 通知主窗口显示切片
        if hasattr(self, 'main_window'):
            self.main_window.show_voting_fusion_slices()
    
    def hide_slice_actors(self):
        """隐藏投票融合结果的三个方向切片视图"""
        # 通知主窗口隐藏切片
        if hasattr(self, 'main_window'):
            self.main_window.hide_voting_fusion_slices()