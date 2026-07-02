import cv2
import numpy as np
import json
from zhuanhua import mask_to_polygons, polygons_to_mask
from basicfunction import load_mha, save_mha
import sys
import os
from PyQt5.QtWidgets import QMessageBox, QWidget, QVBoxLayout, QPushButton,QHBoxLayout, QLabel, QSlider, QSpinBox, QApplication
from PyQt5.QtCore import Qt
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class PolygonEditor:
    def __init__(self, mha_file_path=None, slice_index=None, slice_orientation='axial', polygons_path=None, background_mha_path=None):
        # 如果提供了mha文件路径和切片索引，则从mha文件中加载特定切片
        if mha_file_path and slice_index is not None:
            self.mha_data, self.origin, self.spacing = load_mha(mha_file_path)
            self.mha_file_path = mha_file_path
            self.slice_index = slice_index
            self.slice_orientation = slice_orientation

            # 提取特定切片
            if slice_orientation == 'axial':
                # 轴向切片 (index, :, :)
                self.original_image = self.mha_data[slice_index, :, :].astype(np.uint8)
            elif slice_orientation == 'coronal':
                # 冠状面切片 (:, index, :) - 需要与image_processor.py保持一致
                # 从image_processor.py中复制处理逻辑: np.flip(np.transpose(image_array, (1, 0, 2)), axis=(1, 0))
                transposed = np.flip(np.transpose(self.mha_data, (1, 0, 2)), axis=(1, 0))
                self.original_image = transposed[slice_index, :, :].astype(np.uint8)
            elif slice_orientation == 'sagittal':
                # 矢状面切片 (:, :, index) - 需要与image_processor.py保持一致
                # 从image_processor.py中复制处理逻辑: np.transpose(image_array, (2, 0, 1)) 和 np.flip(self.image_xz, axis=(0, 1))
                transposed = np.transpose(self.mha_data, (2, 0, 1))
                flipped = np.flip(transposed, axis=(0, 1))
                self.original_image = flipped[slice_index, :, :].astype(np.uint8)
            else:
                raise ValueError("slice_orientation must be 'axial', 'coronal', or 'sagittal'")
                
            # 如果提供了背景MHA文件路径，则加载背景图像
            if background_mha_path:
                self.background_mha_data, _, _ = load_mha(background_mha_path)
                # 确保背景图像与前景图像尺寸一致
                if self.background_mha_data.shape != self.mha_data.shape:
                    raise ValueError("前景和背景MHA文件的尺寸不一致")
                # 提取对应的背景切片
                if slice_orientation == 'axial':
                    self.background_image = self.background_mha_data[slice_index, :, :]
                elif slice_orientation == 'coronal':
                    # 冠状面背景切片处理 - 与前景图像保持一致
                    transposed_bg = np.flip(np.transpose(self.background_mha_data, (1, 0, 2)), axis=(1, 0))
                    self.background_image = transposed_bg[slice_index, :, :]
                elif slice_orientation == 'sagittal':
                    # 矢状面背景切片处理 - 与前景图像保持一致
                    transposed_bg = np.transpose(self.background_mha_data, (2, 0, 1))
                    flipped_bg = np.flip(transposed_bg, axis=(0, 1))
                    self.background_image = flipped_bg[slice_index, :, :]
            else:
                self.background_image = None

        # 初始化透明度控制变量
        self.overlay_alpha = 1.0  # 默认完全不透明

        # 初始化窗宽窗位参数
        self.window_width = 700   # 默认窗宽
        self.window_center = 350  # 默认窗位

        if self.background_image is not None:
            # 如果有背景图像，创建叠加显示图像
            self.update_display_image_with_window()
        else:
            # 没有背景图像时的原始行为
            self.display_image = cv2.cvtColor(self.original_image, cv2.COLOR_GRAY2BGR)
         
        # 加载或多边形数据（仅对前景图像进行polygon处理）
        if polygons_path and polygons_path.endswith('.json'):
            with open(polygons_path, 'r') as f:
                polygons_data = json.load(f)
                self.polygons = [np.array(polygon, dtype=np.int32) for polygon in polygons_data]
        else:
            # 对前景mask进行轻微膨胀操作以补偿可能的内缩
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (2, 2))
            dilated_mask = cv2.dilate(self.original_image, kernel, iterations=1)
            # 从膨胀后的mask生成多边形（不对背景图像处理）
            self.polygons = mask_to_polygons(dilated_mask)
        
        self.current_polygon_idx = 0 if len(self.polygons) > 0 else -1
        self.current_point_idx = -1
        self.dragging = False
        self.modified_polygons = [polygon.copy() for polygon in self.polygons]
        
        # 保存原始多边形的精确浮点坐标，用于精确缩放
        self.float_polygons = [polygon.astype(np.float64) for polygon in self.modified_polygons]
        
        # 缩放相关参数
        self.scale_factor = 2.0  # 初始放大倍数
        self.min_scale = 0.5     # 最小缩放
        self.max_scale = 100.0    # 最大缩放
        
        # 拖动查看相关参数
        self.offset_x = 0        # 水平偏移
        self.offset_y = 0        # 垂直偏移
        self.last_mouse_x = 0    # 上一次鼠标位置
        self.last_mouse_y = 0    # 上一次鼠标位置
        
        # 添加点相关
        self.waiting_for_add_point = False  # 是否正在等待添加点的点击位置
        self.waiting_for_new_polygon = False  # 是否正在等待创建新多边形
        self.new_polygon_points = []  # 新多边形的点（存储原始坐标）
        
        # 反转mask区域功能
        self.invert_mask_regions = []  # 存储需要反转的多边形索引
        
        # 版本控制
        self.version_counter = 0  # 保存版本计数器
        
        self.update_scaled_data()
        
        # 初始化时将图像居中显示
        self.center_view()
    
    def center_view(self):
        """将视图居中"""
        scaled_width = int(self.display_image.shape[1] * self.scale_factor)
        scaled_height = int(self.display_image.shape[0] * self.scale_factor)
        
        # 获取窗口尺寸
        view_width = min(900, max(scaled_width, 400))
        view_height = min(900, max(scaled_height, 400))
        
        # 计算居中位置的偏移量
        self.offset_x = max(0, (scaled_width - view_width) // 2)
        self.offset_y = max(0, (scaled_height - view_height) // 2)
    
    def update_scaled_data(self):
        """根据当前缩放因子更新缩放后的图像和多边形"""
        # 调整图像大小
        new_width = int(self.display_image.shape[1] * self.scale_factor)
        new_height = int(self.display_image.shape[0] * self.scale_factor)
        
        # 确保尺寸至少为1
        new_width = max(1, new_width)
        new_height = max(1, new_height)
        
        self.scaled_image = cv2.resize(self.display_image, (new_width, new_height), interpolation=cv2.INTER_LINEAR)
        
        # 调整多边形坐标以适应缩放后的图像（基于高精度浮点坐标计算）
        self.scaled_polygons = []
        for polygon in self.float_polygons:
            # 基于浮点坐标和当前缩放因子计算，避免累积误差
            scaled_polygon = np.round(polygon * self.scale_factor).astype(np.int32)
            self.scaled_polygons.append(scaled_polygon)
    
    def draw_polygons(self):
        # 创建显示图像的副本
        display = self.scaled_image.copy()
        
        # 绘制所有多边形
        for i, polygon in enumerate(self.scaled_polygons):
            if len(polygon) > 0:
                # 当前选中的多边形用绿色，其他用蓝色
                color = (0, 255, 0) if i == self.current_polygon_idx else (255, 100, 100)  # 淡蓝色
                thickness = 2 if i == self.current_polygon_idx else 1
                
                # 绘制多边形轮廓
                if len(polygon) >= 3:
                    cv2.polylines(display, [polygon], True, color, thickness)
                
                # 绘制顶点（只对当前选中的多边形显示顶点）
                if i == self.current_polygon_idx:
                    for j, point in enumerate(polygon):
                        # 当前选中的点用红色，其他顶点用黄色
                        point_color = (0, 0, 255) if j == self.current_point_idx else (0, 255, 255)
                        # 减小顶点大小
                        cv2.circle(display, tuple(point), 3, point_color, -1)
                        cv2.circle(display, tuple(point), 3, (0, 0, 0), 1)  # 黑色边框
                        
                        # 为顶点添加编号（只显示前50个，避免过于拥挤）
                        if len(polygon) <= 50:
                            cv2.putText(display, str(j), (point[0]+5, point[1]-5), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                        elif j % (len(polygon) // 10 + 1) == 0:  # 对于大量顶点，只显示部分编号
                            cv2.putText(display, str(j), (point[0]+5, point[1]-5), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
        
        # 绘制正在创建的新多边形
        if self.waiting_for_new_polygon and len(self.new_polygon_points) > 0:
            # 绘制已有的点（需要转换为缩放坐标）
            scaled_new_points = []
            for point in self.new_polygon_points:
                scaled_x = int(round(point[0] * self.scale_factor))
                scaled_y = int(round(point[1] * self.scale_factor))
                scaled_new_points.append([scaled_x, scaled_y])
            
            # 绘制已有的点
            for point in scaled_new_points:
                cv2.circle(display, tuple(point), 4, (0, 255, 0), -1)
                cv2.circle(display, tuple(point), 4, (0, 0, 0), 1)
            
            # 绘制连线
            if len(scaled_new_points) > 1:
                for i in range(len(scaled_new_points) - 1):
                    cv2.line(display, tuple(scaled_new_points[i]), 
                            tuple(scaled_new_points[i+1]), (0, 255, 0), 2)
        
        return display
    
    def find_closest_point(self, x, y, max_distance=15):
        """找到距离点击位置最近的顶点"""
        if self.current_polygon_idx < 0 or len(self.scaled_polygons[self.current_polygon_idx]) == 0:
            return -1
            
        min_dist = float('inf')
        closest_idx = -1
        
        # 考虑偏移量
        adjusted_x = x + self.offset_x
        adjusted_y = y + self.offset_y
        
        for i, point in enumerate(self.scaled_polygons[self.current_polygon_idx]):
            dist = np.sqrt((point[0] - adjusted_x)**2 + (point[1] - adjusted_y)**2)
            if dist < min_dist and dist <= max_distance:
                min_dist = dist
                closest_idx = i
                
        return closest_idx
    
    def find_polygon_containing_point(self, x, y):
        """找到包含指定点的多边形"""
        # 考虑偏移量
        adjusted_x = x + self.offset_x
        adjusted_y = y + self.offset_y
        
        # 将坐标转换为原始图像坐标
        original_x = int(round(adjusted_x / self.scale_factor))
        original_y = int(round(adjusted_y / self.scale_factor))
        
        # 边界检查
        if (original_y < 0 or original_y >= self.original_image.shape[0] or
            original_x < 0 or original_x >= self.original_image.shape[1]):
            return -1
        
        # 检查每个多边形是否包含该点（优先检查新创建的多边形）
        for i in range(len(self.modified_polygons)-1, -1, -1):  # 从后往前检查，优先选择新创建的
            polygon = self.modified_polygons[i]
            if len(polygon) >= 3:
                # 创建一个临时mask来测试点是否在多边形内
                temp_mask = np.zeros(self.original_image.shape, dtype=np.uint8)
                cv2.fillPoly(temp_mask, [polygon], 1)
                
                # 检查点是否在多边形内
                if temp_mask[original_y, original_x] == 1:
                    return i
        
        # 如果没有找到完全包含的多边形，找最近的多边形
        min_dist = float('inf')
        closest_polygon = 0
        
        for i, polygon in enumerate(self.scaled_polygons):
            if len(polygon) >= 3:
                # 计算点到多边形轮廓的距离
                for j in range(len(polygon)):
                    p1 = polygon[j]
                    p2 = polygon[(j + 1) % len(polygon)]
                    dist = self.point_to_line_distance(adjusted_x, adjusted_y, p1, p2)
                    if dist < min_dist:
                        min_dist = dist
                        closest_polygon = i
        
        # 如果距离不太远，认为是这个多边形
        if min_dist < max(20, 30 / self.scale_factor):  # 根据缩放调整阈值
            return closest_polygon
        
        return -1
    
    def delete_selected_polygon(self):
        """删除当前选中的多边形"""
        if self.current_polygon_idx < 0 or len(self.modified_polygons) <= 0:
            return False
            
        # 删除多边形
        deleted_polygon_idx = self.current_polygon_idx
        
        # 从反转列表中删除对应的索引
        if deleted_polygon_idx in self.invert_mask_regions:
            self.invert_mask_regions.remove(deleted_polygon_idx)
        
        # 更新反转列表中大于deleted_polygon_idx的索引
        self.invert_mask_regions = [idx-1 if idx > deleted_polygon_idx else idx for idx in self.invert_mask_regions]
        
        del self.modified_polygons[deleted_polygon_idx]
        del self.float_polygons[deleted_polygon_idx]
        del self.scaled_polygons[deleted_polygon_idx]
        
        # 更新当前选中的多边形索引
        if len(self.modified_polygons) > 0:
            # 如果删除的不是最后一个，保持当前索引
            # 如果删除的是最后一个，选择前一个
            if deleted_polygon_idx >= len(self.modified_polygons):
                self.current_polygon_idx = len(self.modified_polygons) - 1
            else:
                self.current_polygon_idx = deleted_polygon_idx
        else:
            # 没有多边形了
            self.current_polygon_idx = -1
            
        self.current_point_idx = -1
        return True
    
    def toggle_mask_invert(self):
        """切换当前多边形的mask反转状态"""
        if self.current_polygon_idx < 0:
            return
            
        if self.current_polygon_idx in self.invert_mask_regions:
            self.invert_mask_regions.remove(self.current_polygon_idx)
        else:
            self.invert_mask_regions.append(self.current_polygon_idx)
    
    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.last_mouse_x = x
            self.last_mouse_y = y
            
            # 如果正在等待添加点
            if self.waiting_for_add_point:
                self.add_point(x, y)
                self.waiting_for_add_point = False
                return
            
            # 如果正在创建新多边形
            if self.waiting_for_new_polygon:
                # 更精确地添加点到新多边形（存储原始坐标）
                original_x = int(round((x + self.offset_x) / self.scale_factor))
                original_y = int(round((y + self.offset_y) / self.scale_factor))
                self.new_polygon_points.append([original_x, original_y])
                return
            
            # 左键点击：检查是否点击到顶点
            if self.current_polygon_idx >= 0:
                point_idx = self.find_closest_point(x, y)
                if point_idx >= 0:
                    self.current_point_idx = point_idx
                    self.dragging = True
                
        elif event == cv2.EVENT_LBUTTONUP:
            self.dragging = False
            
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.dragging:
                if self.current_point_idx >= 0 and self.current_polygon_idx >= 0:
                    # 更新点的位置（考虑偏移量）
                    adjusted_x = x + self.offset_x
                    adjusted_y = y + self.offset_y
                    
                    # 同时更新原始坐标的点和浮点坐标的点
                    original_x = int(round(adjusted_x / self.scale_factor))
                    original_y = int(round(adjusted_y / self.scale_factor))
                    self.modified_polygons[self.current_polygon_idx][self.current_point_idx] = [original_x, original_y]
                    self.float_polygons[self.current_polygon_idx][self.current_point_idx] = [float(original_x), float(original_y)]
                    
                    # 更新缩放坐标点
                    self.scaled_polygons[self.current_polygon_idx][self.current_point_idx] = [adjusted_x, adjusted_y]
            
        elif event == cv2.EVENT_RBUTTONDOWN:
            # 如果正在等待添加点，右键不执行任何操作
            if self.waiting_for_add_point:
                return
                
            # 如果正在创建新多边形
            if self.waiting_for_new_polygon:
                # 完成新多边形创建
                if len(self.new_polygon_points) >= 3:
                    # 创建新多边形（使用原始坐标）
                    original_polygon = np.array(self.new_polygon_points, dtype=np.int32)
                    self.modified_polygons.append(original_polygon)
                    
                    # 创建高精度浮点坐标多边形
                    float_polygon = original_polygon.astype(np.float64)
                    self.float_polygons.append(float_polygon)
                    
                    # 创建缩放后的多边形
                    scaled_polygon = np.round(float_polygon * self.scale_factor).astype(np.int32)
                    self.scaled_polygons.append(scaled_polygon)
                    
                    # 更新当前多边形索引为新创建的多边形
                    self.current_polygon_idx = len(self.scaled_polygons) - 1
                else:
                    print("多边形至少需要3个点")
                
                # 重置状态
                self.waiting_for_new_polygon = False
                self.new_polygon_points = []
                return
                
            # 右键点击：选择多边形
            polygon_idx = self.find_polygon_containing_point(x, y)
            if polygon_idx >= 0:
                self.current_polygon_idx = polygon_idx
                self.current_point_idx = -1
    
    def move_view(self, dx, dy):
        """移动视图"""
        self.offset_x = max(0, self.offset_x + dx)
        self.offset_y = max(0, self.offset_y + dy)
    
    def zoom_in(self):
        """放大图像，以显示窗口中心为基准"""
        # 计算当前中心点
        center_x = self.offset_x + 450  # 900/2
        center_y = self.offset_y + 450  # 900/2
        
        # 执行缩放
        self.scale_factor *= 1.1
        self.scale_factor = min(self.max_scale, self.scale_factor)
        self.update_scaled_data()
        
        # 调整偏移量以保持中心点不变
        new_center_x = center_x * 1.1
        new_center_y = center_y * 1.1
        self.offset_x = max(0, int(new_center_x - 450))
        self.offset_y = max(0, int(new_center_y - 450))
    
    def zoom_out(self):
        """缩小图像，以显示窗口中心为基准"""
        # 计算当前中心点
        center_x = self.offset_x + 450  # 900/2
        center_y = self.offset_y + 450  # 900/2
        
        # 执行缩放
        self.scale_factor /= 1.1
        self.scale_factor = max(self.min_scale, self.scale_factor)
        self.update_scaled_data()
        
        # 调整偏移量以保持中心点不变
        new_center_x = center_x / 1.1
        new_center_y = center_y / 1.1
        self.offset_x = max(0, int(new_center_x - 450))
        self.offset_y = max(0, int(new_center_y - 450))
    
    def add_point(self, x, y):
        """在指定位置添加新点"""
        if self.current_polygon_idx < 0:
            return
            
        # 考虑偏移量
        adjusted_x = x + self.offset_x
        adjusted_y = y + self.offset_y
        original_x = int(round(adjusted_x / self.scale_factor))
        original_y = int(round(adjusted_y / self.scale_factor))
        
        polygon = self.scaled_polygons[self.current_polygon_idx]
        original_polygon = self.modified_polygons[self.current_polygon_idx]
        float_polygon = self.float_polygons[self.current_polygon_idx]
        
        if len(polygon) < 3:
            # 如果多边形点数少于3，直接添加
            self.scaled_polygons[self.current_polygon_idx] = np.append(polygon, [[adjusted_x, adjusted_y]], axis=0)
            self.modified_polygons[self.current_polygon_idx] = np.append(original_polygon, [[original_x, original_y]], axis=0)
            self.float_polygons[self.current_polygon_idx] = np.append(float_polygon, [[float(original_x), float(original_y)]], axis=0)
        else:
            # 找到距离点击位置最近的边
            min_dist = float('inf')
            insert_idx = 0
            
            for i in range(len(polygon)):
                p1 = polygon[i]
                p2 = polygon[(i + 1) % len(polygon)]
                
                # 计算点到线段的距离
                dist = self.point_to_line_distance(adjusted_x, adjusted_y, p1, p2)
                if dist < min_dist:
                    min_dist = dist
                    insert_idx = (i + 1) % len(polygon)
            
            # 在最近的边中间插入新点
            self.scaled_polygons[self.current_polygon_idx] = np.insert(polygon, insert_idx, [[adjusted_x, adjusted_y]], axis=0)
            self.modified_polygons[self.current_polygon_idx] = np.insert(original_polygon, insert_idx, [[original_x, original_y]], axis=0)
            self.float_polygons[self.current_polygon_idx] = np.insert(float_polygon, insert_idx, [[float(original_x), float(original_y)]], axis=0)
    
    def start_new_polygon(self):
        """开始创建新多边形"""
        self.waiting_for_new_polygon = True
        self.new_polygon_points = []
    
    def cancel_new_polygon(self):
        """取消创建新多边形"""
        self.waiting_for_new_polygon = False
        self.new_polygon_points = []
    
    def point_to_line_distance(self, x, y, line_point1, line_point2):
        """计算点到线段的距离"""
        x1, y1 = line_point1
        x2, y2 = line_point2
        
        # 线段长度的平方
        line_mag_sq = (x2 - x1)**2 + (y2 - y1)**2
        
        if line_mag_sq == 0:
            # 线段退化为点
            return np.sqrt((x - x1)**2 + (y - y1)**2)
        
        # 投影参数
        u = ((x - x1) * (x2 - x1) + (y - y1) * (y2 - y1)) / line_mag_sq
        
        # 限制在[0,1]范围内
        u = max(0, min(1, u))
        
        # 投影点坐标
        proj_x = x1 + u * (x2 - x1)
        proj_y = y1 + u * (y2 - y1)
        
        # 计算距离
        return np.sqrt((x - proj_x)**2 + (y - proj_y)**2)
    
    def remove_point(self):
        """移除当前选中的点"""
        if self.current_polygon_idx < 0 or self.current_point_idx < 0:
            return
            
        polygon = self.scaled_polygons[self.current_polygon_idx]
        original_polygon = self.modified_polygons[self.current_polygon_idx]
        float_polygon = self.float_polygons[self.current_polygon_idx]
        
        if len(polygon) > 3 and self.current_point_idx >= 0:  # 至少保持3个点
            self.scaled_polygons[self.current_polygon_idx] = np.delete(polygon, self.current_point_idx, axis=0)
            self.modified_polygons[self.current_polygon_idx] = np.delete(original_polygon, self.current_point_idx, axis=0)
            self.float_polygons[self.current_polygon_idx] = np.delete(float_polygon, self.current_point_idx, axis=0)
            self.current_point_idx = -1
        else:
            print("无法删除顶点：多边形至少需要3个顶点")
    
    def deselect_polygon(self):
        """取消多边形选择"""
        self.current_polygon_idx = -1
        self.current_point_idx = -1
    
    def save_polygons(self, output_path):
        """保存修改后的多边形（版本化保存）"""
        # 增加版本计数
        self.version_counter += 1
        
        # 生成版本化文件名
        base_name = output_path.replace('.json', '')
        versioned_path = f"{base_name}_v{self.version_counter}.json"
        
        polygons_list = [polygon.tolist() for polygon in self.modified_polygons]
        with open(versioned_path, 'w') as f:
            json.dump(polygons_list, f)
        
        # 保存为mask图像（考虑反转区域）
        if len(self.modified_polygons) > 0:
            # 创建基础mask
            mask = polygons_to_mask(self.modified_polygons, self.original_image.shape)
            
            # 应用反转区域
            for idx in self.invert_mask_regions:
                if idx < len(self.modified_polygons):
                    # 创建该多边形的mask
                    single_polygon_mask = np.zeros(self.original_image.shape, dtype=np.uint8)
                    cv2.fillPoly(single_polygon_mask, [self.modified_polygons[idx]], 1)
                    # 反转该区域
                    mask = np.where(single_polygon_mask == 1, 1 - mask, mask)
            
            mask_path = versioned_path.replace('.json', '_mask.png')
            cv2.imwrite(mask_path, mask * 255)  # 转换为0-255范围
            
            # 如果是从mha文件加载的，则将修改后的mask保存回原文件
            if hasattr(self, 'mha_file_path') and hasattr(self, 'slice_index'):
                # 创建新的mha数据副本
                new_mha_data = self.mha_data.copy()
                
                # 将修改后的mask应用到对应的切片
                if self.slice_orientation == 'axial':
                    new_mha_data[self.slice_index, :, :] = mask * 255
                elif self.slice_orientation == 'coronal':
                    new_mha_data[:, self.slice_index, :] = mask * 255
                elif self.slice_orientation == 'sagittal':
                    new_mha_data[:, :, self.slice_index] = mask * 255
                
                # 保存修改后的mha文件
                save_mha(new_mha_data, self.mha_file_path, self.origin, self.spacing)

         # 添加保存成功提示框，告知保存位置
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("保存成功")
        msg_box.setText(f"文件已成功保存到以下位置：\n\nJSON文件: {versioned_path}\nMask图像: {mask_path}")
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
    
    def apply_overlay(self):
        """应用标注覆盖层，支持透明度设置"""
        # 只有在有背景图像的情况下才进行处理
        if self.background_image is not None:
            # 始终从原始背景图像开始，确保背景图像不发生变化
            self.display_image = self.base_display_image.copy()
            
            # 只有在透明度大于0时才处理血管标注
            # 当透明度为0时，直接显示原始背景图像，不进行任何处理
            if self.overlay_alpha > 0:
                # 创建血管标注的掩码
                mask = self.original_image > 0
                
                # 对血管标注区域进行alpha混合
                # 背景颜色保持不变，红色通道根据透明度增加红色分量
                # 最终效果：透明度0时显示背景，透明度1时显示纯红色
                
                # 蓝色和绿色通道：背景 * (1 - alpha)
                self.display_image[mask, 0] = (
                    self.display_image[mask, 0] * (1 - self.overlay_alpha)
                ).astype(np.uint8)
                self.display_image[mask, 1] = (
                    self.display_image[mask, 1] * (1 - self.overlay_alpha)
                ).astype(np.uint8)
                
                # 红色通道：背景 * (1 - alpha) + 255 * alpha
                self.display_image[mask, 2] = (
                    self.display_image[mask, 2] * (1 - self.overlay_alpha) + 
                    255 * self.overlay_alpha
                ).astype(np.uint8)

    def update_display_image_with_window(self):
        """根据窗宽窗位参数更新显示图像"""
        if self.background_image is not None:
            # 计算窗宽窗位参数
            min_value = self.window_center - self.window_width / 2
            max_value = self.window_center + self.window_width / 2
            
            # 创建显示图像
            self.display_image = np.zeros((self.original_image.shape[0], self.original_image.shape[1], 3), dtype=np.uint8)
            
            # 应用窗宽窗位处理，与主界面保持一致的显示效果
            adjusted_bg = np.clip(self.background_image, min_value, max_value)
            adjusted_bg = ((adjusted_bg - min_value) / self.window_width * 255).astype(np.uint8)
                
            self.display_image[:,:,0] = adjusted_bg  # 蓝色通道
            self.display_image[:,:,1] = adjusted_bg  # 绿色通道
            self.display_image[:,:,2] = adjusted_bg  # 红色通道
            
            # 保存基础背景图像（不带标注）
            self.base_display_image = self.display_image.copy()
            
            # 将前景（标注）叠加到背景上（使用红色显示标注）
            mask = self.original_image > 0
            self.display_image[mask, 0] = 0    # 蓝色通道设为0
            self.display_image[mask, 1] = 0    # 绿色通道设为0
            self.display_image[mask, 2] = 255  # 红色通道显示标注
            
            # 应用透明度
            self.apply_overlay()

    def create_guide_window(self):
        """创建修改指南窗口"""
        # 创建指南窗口
        self.guide_window = QWidget()
        self.guide_window.setWindowTitle("修改指南")
        self.guide_window.setMinimumSize(400, 350)
        self.guide_window.setStyleSheet("background-color: #000000;")
        
        layout = QVBoxLayout(self.guide_window)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # 添加标题
        title_label = QLabel("修改标注使用说明")
        title_label.setStyleSheet("color: #00c6ff; font-weight: bold; font-size: 17px;")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 添加指南内容
        guide_text = """鼠标右键点击多边形 ——即选择多边形；
Q 键——取消多边形选择；
/ 键——删除当前选中的多边形；
I 键——反转当前多边形的mask(白色变黑色,黑色变白色);
鼠标左键点击并拖拽顶点 ——移动顶点；
W/A/S/D键 ——上/左/下/右移动视图；
1键 —— 缩小图像；
2键—— 放大图像；
+键 —— 在鼠标位置添加新点；
-键—— 删除当前选中的点；
N键 ——创建新多边形；
B 键——保存修改后的多边形，并保存至医学文件；
ESC键 ——退出；"""
        
        guide_label = QLabel(guide_text)
        guide_label.setStyleSheet("color: #e1e1e1; font-size: 16px;")
        guide_label.setWordWrap(True)
        layout.addWidget(guide_label)
        
        # 添加关闭按钮
        close_button = QPushButton("关闭")
        close_button.setStyleSheet("""
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
        close_button.clicked.connect(self.guide_window.close)
        layout.addWidget(close_button)
    
    def run(self):
        """运行编辑器"""
        # 创建Qt应用程序和透明度控制窗口
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建透明度控制窗口
        self.control_window = QWidget()
        self.control_window.setWindowTitle("Overlay Controls")
        self.control_window.setFixedSize(420, 150)  # 增加窗口高度以容纳更多控件
        self.control_window.setStyleSheet("background-color: #000000;")  # 设置背景色为黑色
        layout = QVBoxLayout(self.control_window)
        layout.setContentsMargins(0, 10, 10, 10)  # 左边距设为0，将在控件中添加空白
        layout.setSpacing(15)  # 增加控件之间的垂直间距
        
        # 标注透明度控制
        overlay_layout = QHBoxLayout()
        overlay_layout.setContentsMargins(20, 0, 0, 0)  # 左边距10像素
        self.overlay_label = QLabel("标注透明度:")
        self.overlay_label.setFixedSize(90, 20)
        self.overlay_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        overlay_layout.addWidget(self.overlay_label)
        
        self.overlay_slider = QSlider(Qt.Horizontal)
        self.overlay_slider.setFixedSize(200, 20)  # 调整滑块宽度，为数值选择器留出更多空间
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
        
        # 添加弹性空间，增加滑块和数值选择器之间的距离
        overlay_layout.addSpacing(20)
        
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
        
        layout.addLayout(overlay_layout)
        
        # 窗宽控制
        window_width_layout = QHBoxLayout()
        window_width_layout.setContentsMargins(20, 0, 0, 0)  # 左边距10像素，与标注透明度对齐
        self.window_width_label = QLabel("  窗宽:")
        self.window_width_label.setFixedSize(90, 20)
        self.window_width_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        window_width_layout.addWidget(self.window_width_label)
        
        self.window_width_slider = QSlider(Qt.Horizontal)
        self.window_width_slider.setFixedSize(200, 20)
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
        
        # 添加弹性空间，增加滑块和数值选择器之间的距离
        window_width_layout.addSpacing(20)
        
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
        
        layout.addLayout(window_width_layout)
        
        # 窗位控制
        window_center_layout = QHBoxLayout()
        window_center_layout.setContentsMargins(20, 0, 0, 0)  # 左边距10像素，与标注透明度对齐
        self.window_center_label = QLabel("  窗位:")
        self.window_center_label.setFixedSize(90, 20)
        self.window_center_label.setStyleSheet("color: #00c6ff; font-weight: bold;")
        window_center_layout.addWidget(self.window_center_label)
        
        self.window_center_slider = QSlider(Qt.Horizontal)
        self.window_center_slider.setFixedSize(200, 20)
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
        
        # 添加弹性空间，增加滑块和数值选择器之间的距离
        window_center_layout.addSpacing(20)
        
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
        
        layout.addLayout(window_center_layout)
        
        # 连接信号
        self.overlay_slider.valueChanged.connect(self.overlay_spinbox.setValue)
        self.overlay_spinbox.valueChanged.connect(self.overlay_slider.setValue)
        self.overlay_slider.valueChanged.connect(self.on_overlay_changed)
        
        # 连接窗宽信号
        self.window_width_slider.valueChanged.connect(self.window_width_spinbox.setValue)
        self.window_width_spinbox.valueChanged.connect(self.window_width_slider.setValue)
        self.window_width_slider.valueChanged.connect(self.on_window_width_changed)
        
        # 连接窗位信号
        self.window_center_slider.valueChanged.connect(self.window_center_spinbox.setValue)
        self.window_center_spinbox.valueChanged.connect(self.window_center_slider.setValue)
        self.window_center_slider.valueChanged.connect(self.on_window_center_changed)
        
        # 显示控制窗口
        self.control_window.show()

        self.control_window.move(350, 50)

         # 创建并显示指南窗口
        self.create_guide_window()
        self.guide_window.show()
        self.guide_window.move(290, 300)
        
        window_name = "HuiYiZhiYing - Manual Modification"
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        # 根据切片方向设置不同的窗口尺寸
        if self.slice_orientation == 'sagittal' or self.slice_orientation == 'coronal':
            view_width, view_height = 1800, 600
        elif self.slice_orientation == 'axial':
            view_width, view_height = 900, 900
        else:
            # 默认尺寸
            img_height, img_width = self.display_image.shape[:2]
            # 考虑2倍缩放后的尺寸
            scaled_width = int(img_width * self.scale_factor)
            scaled_height = int(img_height * self.scale_factor)
            
            # 设置合适的窗口大小，最大不超过900x900
            view_width = min(1200, max(scaled_width, 700))
            view_height = min(900, max(scaled_height, 700))
        
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, view_width, view_height)
        cv2.moveWindow(window_name, 800, 50)

       
        while True:
            display = self.draw_polygons()
            
            # 根据偏移量显示图像的一部分
            h, w = display.shape[:2]
            
            # 确保偏移量不超过边界
            max_offset_x = max(0, w - view_width)
            max_offset_y = max(0, h - view_height)
            self.offset_x = min(self.offset_x, max_offset_x)
            self.offset_y = min(self.offset_y, max_offset_y)
            
            # 确保始终显示view_width x view_height大小的区域
            if h >= view_height and w >= view_width:
                # 从缩放后的图像中截取视图部分
                view = display[self.offset_y:self.offset_y+view_height, self.offset_x:self.offset_x+view_width]
                cv2.imshow(window_name, view)
            else:
                # 如果图像小于窗口大小，创建一个黑色背景并将图像放在左上角
                background = np.zeros((view_height, view_width, 3), dtype=np.uint8)
                # 确保不会超出边界
                put_h = min(h, view_height)
                put_w = min(w, view_width)
                background[0:put_h, 0:put_w] = display[0:put_h, 0:put_w]
                cv2.imshow(window_name, background)
            
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27:  # ESC键退出
                # 如果正在等待添加点，ESC键取消操作
                if self.waiting_for_add_point:
                    self.waiting_for_add_point = False
                # 如果正在创建新多边形，ESC键取消操作
                elif self.waiting_for_new_polygon:
                    self.cancel_new_polygon()
                else:
                    break
            elif key == ord('q') or key == ord('Q'):
                self.deselect_polygon()
            elif key == ord('w') or key == ord('W'):
                self.move_view(0, -20)  # 向上移动
            elif key == ord('s') or key == ord('S'):
                self.move_view(0, 20)   # 向下移动
            elif key == ord('a') or key == ord('A'):
                self.move_view(-20, 0)  # 向左移动
            elif key == ord('d') or key == ord('D'):
                self.move_view(20, 0)   # 向右移动
            elif key == ord('1'):
                self.zoom_out()
            elif key == ord('2'):
                self.zoom_in()
            elif key == ord('+') or key == ord('='):
                # 激活添加点功能
                if self.current_polygon_idx >= 0:
                    self.waiting_for_add_point = True
                else:
                    print("请先选择一个多边形")
            elif key == ord('-') or key == ord('_'):
                self.remove_point()
            elif key == ord('n') or key == ord('N'):
                # 开始创建新多边形
                self.start_new_polygon()
            elif key == ord('/'):
                # 删除当前选中的多边形
                self.delete_selected_polygon()
            elif key == ord('i') or key == ord('I'):
                # 反转当前多边形的mask
                self.toggle_mask_invert()
            elif key == ord('b') or key == ord('B'):
                self.save_polygons(r"D:\mask to polygon\modified_polygons.json")
        
        cv2.destroyAllWindows()
        self.control_window.close()
        if hasattr(self, 'guide_window'):
            self.guide_window.close()

    
    def on_overlay_changed(self, val):
        """透明度控制变化回调函数"""
        # 将0-100的值转换为0-1范围
        self.overlay_alpha = val / 100.0
        # 重新应用覆盖层
        if self.background_image is not None:
            # 只有在有背景图像的情况下才进行处理
            if self.overlay_alpha > 0:
                self.apply_overlay()
            else:
                # 透明度为0时，直接使用原始背景图像
                self.display_image = self.base_display_image.copy()
            self.update_scaled_data()
    def on_window_width_changed(self, val):
        """窗宽控制变化回调函数"""
        self.window_width = val
        if self.background_image is not None:
            self.update_display_image_with_window()
            self.update_scaled_data()

    def on_window_center_changed(self, val):
        """窗位控制变化回调函数"""
        self.window_center = val
        if self.background_image is not None:
            self.update_display_image_with_window()
            self.update_scaled_data()

# 使用示例
if __name__ == "__main__":
    # 方式1: 从原始mask图像开始
    # editor = PolygonEditor(r"D:\mask to polygon\predicted_mask.png")
    
    # 方式2: 从已有的多边形文件开始（如果有的话）
    # editor = PolygonEditor(r"D:\mask to polygon\predicted_mask.png", 
    #                       r"D:\mask to polygon\polygons.json")
    
    # 方式3: 从mha文件的特定切片开始，同时加载背景图像
    editor = PolygonEditor(
        mha_file_path=r"mha/votingFusion_result.mha", 
        slice_index=20, 
        slice_orientation='axial',
        background_mha_path=r"mha/Normal001-MRA.mha"
    )
    editor.run()