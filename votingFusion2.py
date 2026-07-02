# -*- coding: utf-8 -*-
"""
医学图像多模型投票融合算法模块 (方案二)
=================================================

该模块实现了基于多模型预测结果的智能投票融合算法，用于提高脑血管分割的准确性和鲁棒性。

技术特点:
---------
1. 多模型融合策略：集成三个不同视角训练的UNet模型预测结果
2. 热力图权重机制：利用模型预测置信度热力图指导投票决策
3. 动态校正算法：基于模型置信度差异对初步投票结果进行智能修正
4. 维度自适应匹配：自动处理不同模型输出维度不一致问题

融合原理:
---------
- 基础投票：多数模型同意的像素点直接采用多数结果
- 智能校正：对于分歧较大的像素点，结合热力图置信度进行加权判断
- 置信度引导：热力图值越高表示模型对该像素预测越有信心

应用场景:
---------
适用于医学图像分割任务中的模型集成，特别针对脑血管图像分割任务优化设计
"""

import numpy as np
from basicfunction import load_mha, save_mha
import os

def readUnet1():
    """
    读取轴向视角(AXIS=0)UNet模型预测结果
    
    该模型专门针对轴向切片进行训练，对主要血管结构具有良好的识别能力
    预测结果存储在test1_1.mha文件中，用于后续投票融合处理
    """
    data_path = 'mha/test1_1.mha'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到文件: {data_path}")
    data, origin_data, spacing_data = load_mha(data_path)
    return data, origin_data, spacing_data

def readUnet2():
    """
    读取冠状面视角(AXIS=1)UNet模型预测结果
    
    该模型专门针对冠状面切片进行训练，能够有效识别血管的侧面特征
    预测结果存储在test2_2.mha文件中，补充轴向模型的不足
    """
    data_path = 'mha/test2_2.mha'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到文件: {data_path}")
    data, origin_data, spacing_data = load_mha(data_path)
    return data, origin_data, spacing_data

def readUnet3():
    """
    读取矢状面视角(AXIS=2)UNet模型预测结果
    
    该模型专门针对矢状面切片进行训练，提供血管的纵向特征信息
    预测结果存储在test3_3.mha文件中，与前两个模型形成三维互补
    """
    data_path = 'mha/test3_3.mha'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到文件: {data_path}")
    data, origin_data, spacing_data = load_mha(data_path)
    return data, origin_data, spacing_data

def readheatmap1():
    """
    读取轴向模型预测置信度热力图
    
    热力图反映模型对每个像素预测结果的置信度，值越高表示模型越确信
    用于在投票分歧时提供权重参考，提高融合决策的准确性
    """
    data_path = 'mha/heatmap1.npy'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到热力图文件: {data_path}")
    data = np.load(data_path)
    # 更安全的squeeze操作，避免不必要的维度压缩
    if data.ndim > 2 and data.shape[-1] == 1:
        data = np.squeeze(data, axis=-1)
    return data

def readheatmap2():
    """
    读取冠状面模型预测置信度热力图
    
    用于提供冠状面视角模型的预测置信度信息，在融合过程中作为权重参考
    """
    data_path = 'mha/heatmap2.npy'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到热力图文件: {data_path}")
    data = np.load(data_path)
    # 更安全的squeeze操作，避免不必要的维度压缩
    if data.ndim > 2 and data.shape[-1] == 1:
        data = np.squeeze(data, axis=-1)
    return data

def readheatmap3():
    """
    读取矢状面模型预测置信度热力图
    
    用于提供矢状面视角模型的预测置信度信息，在融合过程中作为权重参考
    """
    data_path = 'mha/heatmap3.npy'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"找不到热力图文件: {data_path}")
    data = np.load(data_path)
    # 更安全的squeeze操作，避免不必要的维度压缩
    if data.ndim > 2 and data.shape[-1] == 1:
        data = np.squeeze(data, axis=-1)
    return data

def votingFusion2(file_path):
    """
    基于置信度引导的多模型投票融合算法 (方案二)
    
    采用智能投票策略融合三个不同视角训练的UNet模型预测结果，
    通过模型预测置信度热力图指导分歧像素的决策过程，提高分割精度
    
    算法流程:
    --------
    1. 加载原始医学图像获取元数据信息
    2. 读取三个模型的预测结果和对应置信度热力图
    3. 自动匹配预测结果与热力图的维度结构
    4. 执行基础多数投票策略
    5. 基于置信度热力图对分歧像素进行智能校正
    6. 保存融合结果并返回保存路径
    
    Args:
        file_path (str): 输入医学图像文件路径，用于获取图像元数据
        
    Returns:
        str or None: 成功时返回保存结果的文件路径，失败时返回None
        
    Raises:
        FileNotFoundError: 当必需的输入文件不存在时
        ValueError: 当数据维度不匹配且无法自动调整时
        Exception: 其他处理过程中出现的异常
    """
    try:
        # 加载原始数据获取origin和spacing元数据信息
        print(f"开始加载原始数据: {file_path}")
        data, origin, spacing = load_mha(file_path)
        print(f"原始数据形状: {data.shape}")
        
        # 读取三个模型的预测结果
        print("开始读取三个模型的预测结果")
        data1, _, _ = readUnet1()
        data2, _, _ = readUnet2()
        data3, _, _ = readUnet3()
        
        # 读取三个模型的热力图
        print("开始读取三个模型的热力图")
        heatmap1 = readheatmap1()
        heatmap2 = readheatmap2()
        heatmap3 = readheatmap3()
        
        print(f"data1 shape: {data1.shape}")
        print(f"data2 shape: {data2.shape}")
        print(f"data3 shape: {data3.shape}")
        print(f"heatmap1 shape: {heatmap1.shape}")
        print(f"heatmap2 shape: {heatmap2.shape}")
        print(f"heatmap3 shape: {heatmap3.shape}")
        
        # 根据预测结果的维度来调整热力图维度
        # 确保热力图与对应预测结果的维度一致，以保证后续计算的正确性
        if heatmap1.shape != data1.shape:
            print("警告: heatmap1和data1维度不匹配，尝试调整...")
            # 根据需要进行维度调整
            if len(heatmap1.shape) == 3 and len(data1.shape) == 3:
                # 如果维度顺序不同，尝试不同的轴交换
                # 这里我们尝试匹配data1的形状
                heatmap1 = np.transpose(heatmap1, (1, 2, 0)) if heatmap1.shape[0] != data1.shape[0] else heatmap1
                # 尝试其他可能的转置
                if heatmap1.shape != data1.shape:
                    heatmap1 = np.transpose(heatmap1, (2, 0, 1))
                
        if heatmap2.shape != data2.shape:
            print("警告: heatmap2和data2维度不匹配，尝试调整...")
            if len(heatmap2.shape) == 3 and len(data2.shape) == 3:
                # 对于unet2，数据是按axis=1切片的，需要相应调整
                heatmap2 = np.transpose(heatmap2, (1, 0, 2)) if heatmap2.shape[1] != data2.shape[1] else heatmap2
                # 尝试其他可能的转置
                if heatmap2.shape != data2.shape:
                    heatmap2 = np.transpose(heatmap2, (2, 0, 1))
                
        if heatmap3.shape != data3.shape:
            print("警告: heatmap3和data3维度不匹配，尝试调整...")
            if len(heatmap3.shape) == 3 and len(data3.shape) == 3:
                # 对于unet3，数据是按axis=2切片的，需要相应调整
                heatmap3 = np.transpose(heatmap3, (2, 0, 1)) if heatmap3.shape[2] != data3.shape[2] else heatmap3
                # 尝试其他可能的转置
                if heatmap3.shape != data3.shape:
                    heatmap3 = np.transpose(heatmap3, (1, 2, 0))
        
        print(f"调整后 heatmap1 shape: {heatmap1.shape}")
        print(f"调整后 heatmap2 shape: {heatmap2.shape}")
        print(f"调整后 heatmap3 shape: {heatmap3.shape}")
        
        # 检查调整后维度是否匹配，确保后续计算的正确性
        if heatmap1.shape != data1.shape:
            raise ValueError(f"热力图1与预测结果1维度不匹配: {heatmap1.shape} vs {data1.shape}")
        if heatmap2.shape != data2.shape:
            raise ValueError(f"热力图2与预测结果2维度不匹配: {heatmap2.shape} vs {data2.shape}")
        if heatmap3.shape != data3.shape:
            raise ValueError(f"热力图3与预测结果3维度不匹配: {heatmap3.shape} vs {data3.shape}")
        
        print("维度匹配成功，开始投票融合")
        
        # 初始化投票结果，以第一个模型的预测结果为基准
        votingResult = data1.copy()
        
        # 计算模型一致性指标，用于识别分歧区域
        temp23 = data2 + data3
        
        # 智能校正策略一：处理"多数反对"情况
        # 识别data1预测为正类(1)但其他两个模型都预测为负类(0)的像素点
        correct1_0 = (temp23 == 0) & (data1 == 1)
        # 构建置信度差异指标：2*heatmap1 - (1-heatmap2) - (1-heatmap3)
        # 该项表示模型1的置信度与其他两个模型反向置信度的差异
        tempheat1_0 = 2 * heatmap1 - (1 - heatmap2) - (1 - heatmap3)
        # 当置信度差异指标小于0时，认为模型1预测错误，进行校正
        votingResult[(tempheat1_0 < 0) & correct1_0] = 0
        
        # 智能校正策略二：处理"多数支持"情况
        # 识别data1预测为负类(0)但其他两个模型都预测为正类(1)的像素点
        correct0_1 = (temp23 == 2) & (data1 == 0)
        # 构建置信度差异指标：2*(1-heatmap1) - heatmap2 - heatmap3
        # 该项表示模型1反向置信度与其他两个模型置信度的差异
        tempheat0_1 = 2 * (1 - heatmap1) - heatmap2 - heatmap3
        # 当置信度差异指标小于0时，认为模型1预测错误，进行校正
        votingResult[(tempheat0_1 < 0) & correct0_1] = 1
        
        # 保存最终融合结果
        
        save_path = 'mha/votingFusion_result.mha'
        print(f"准备保存结果到: {save_path}")
        
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        votingResult = votingResult.astype('int')
        save_mha(votingResult, save_path, origin, spacing)
        print(f"投票融合完成，结果保存至 {save_path}")
        
        return save_path
        
    except FileNotFoundError as e:
        print(f"文件未找到错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"投票融合错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # 测试代码 - 传入正确的文件路径
    test_file_path = "D:/brain_data/Normal-001/MRA/Normal001-MRA.mha"
    result_path = votingFusion2(test_file_path)
    if result_path:
        print(f"投票融合完成，结果保存至: {result_path}")
    else:
        print("投票融合失败")