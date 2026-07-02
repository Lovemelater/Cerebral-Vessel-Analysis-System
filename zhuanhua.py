import cv2
import numpy as np

# 修改后的函数，提供更好的精度控制
def mask_to_polygons(mask, epsilon_factor=0, min_polygon_points=3):
    """Convert binary mask to polygons with better precision control"""
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    polygons = []
    for contour in contours:
        # 可以选择是否使用轮廓简化
        if epsilon_factor > 0:
            epsilon = epsilon_factor * cv2.arcLength(contour, True)
            approx_contour = cv2.approxPolyDP(contour, epsilon, True)
        else:
            # 不进行轮廓简化，使用所有点
            approx_contour = contour
            
        polygon = approx_contour.reshape(-1, 2)
        if len(polygon) >= min_polygon_points:
            polygons.append(polygon)
    return polygons

def polygons_to_mask(polygons, shape):
    mask = np.zeros(shape, dtype=np.uint8)
    """
    创建一个指定形状(shape)的全零数组作为初始掩码
    数据类型为 np.uint8(8位无符号整数)适合表示二值图像
    掩码初始值全为0(黑色背景)
    """
    for polygon in polygons:
        cv2.fillPoly(mask, [polygon], 1)
        """
        遍历输入的每个 polygon（多边形）
        使用 cv2.fillPoly 函数将多边形内部区域填充为指定值
        [polygon] 将单个多边形包装成列表形式（函数要求的格式）
        1 是填充的值，表示该区域为前景（白色）
        """
    return mask

