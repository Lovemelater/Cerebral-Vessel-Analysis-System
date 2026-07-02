"""
re_train.py
模型重训练模块，负责血管分割模型的再训练功能

主要功能：
1. 模型再训练：基于新的数据集对UNet模型进行再训练
2. 多线程处理：继承QThread实现后台训练，避免阻塞UI界面
3. 进度监控：通过信号机制向UI界面发送训练进度信息
4. 模型保存：自动保存最佳验证性能的模型参数
5. 错误处理：完善的异常处理机制，确保训练过程稳定

医学背景：
该模块用于脑血管分割模型的再训练，采用Focal Loss解决血管像素与背景像素不平衡问题，
使用UNet网络架构进行血管分割任务，针对脑部MRA（磁共振血管造影）图像进行处理。
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import torch
from torch.utils.data import DataLoader
from PyQt5.QtCore import QThread, pyqtSignal

from model import UNet, FocalLoss
from dataset import MRADataset

class ModelTrainer(QThread):
    """
    模型训练器类，继承自QThread实现多线程训练
    
    信号说明：
    - progress_updated: 训练进度文本更新信号
    - epoch_progress_updated: 单轮训练进度更新信号（0-100）
    - total_progress_updated: 总体训练进度更新信号（0-100）
    - training_finished: 训练完成信号
    """
    
    # 定义信号，用于向UI发送进度信息
    progress_updated = pyqtSignal(str)
    epoch_progress_updated = pyqtSignal(int)
    total_progress_updated = pyqtSignal(int)
    training_finished = pyqtSignal()
    
    def __init__(self):
        """
        初始化模型训练器
        """
        super().__init__()
        
    def run(self):
        """
        训练主流程，QThread的入口函数
        实现完整的模型训练循环，包括数据加载、模型训练、验证和模型保存
        """
        try:
            self.progress_updated.emit("开始模型训练...")
            
            # 设备选择：优先使用GPU加速训练，若无GPU则使用CPU
            device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            self.progress_updated.emit(f"使用设备: {device}")
            
            # 数据路径配置：训练集20个样本(编号01-20)，验证集5个样本(编号21-25)
            train_data = [f'D:/brain_data/Normal-0{i:02d}/MRA/Normal0{i:02d}-MRA.mha' for i in range(1, 21)]
            train_label = [f'D:/brain_data/Normal-0{i:02d}/MRA/{i:03d}.mha' for i in range(1, 21)]
            val_data = [f'D:/brain_data/Normal-0{i:02d}/MRA/Normal0{i:02d}-MRA.mha' for i in range(21, 26)]
            val_label = [f'D:/brain_data/Normal-0{i}/MRA/0{i}.mha' for i in range(21, 26)]
            
            # 数据完整性检查：验证所有训练和验证数据文件是否存在
            missing_files = []
            for path in train_data + train_label + val_data + val_label:
                if not os.path.exists(path):
                    missing_files.append(path)
            
            if missing_files:
                self.progress_updated.emit("错误：以下数据文件缺失:")
                for file in missing_files:
                    self.progress_updated.emit(f"  {file}")
                self.training_finished.emit()
                return
            
            # 创建数据集：使用轴向切片(axis=0)构建训练和验证数据集
            self.progress_updated.emit("正在加载训练数据...")
            train_dataset = MRADataset(train_data, train_label, axis=0)
            val_dataset = MRADataset(val_data, val_label, axis=0)
            
            # 数据加载器配置：训练数据打乱顺序，批次大小为4
            train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
            val_loader = DataLoader(val_dataset, batch_size=4)
            
            # 模型和优化器配置
            self.progress_updated.emit("正在创建模型...")
            model = UNet().to(device)
            # 使用Focal Loss解决血管像素(前景)与背景像素严重不平衡问题
            # alpha=0.25调节正负样本权重，gamma=2.0聚焦难分样本
            criterion = FocalLoss(alpha=0.25, gamma=2.0)
            # Adam优化器，学习率1e-4，适合深度学习模型训练
            optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
            # 学习率调度器：每30个epoch将学习率减半，实现自适应学习率调整
            scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.5)
            
            # 初始化最佳验证指标：用于模型选择和保存
            best_val_loss = float('inf')
            best_val_dice = 0.0
            
            # 训练参数设置：总共训练100个epoch
            total_epochs = 100
            
            # 训练循环：执行模型训练和验证的主要循环
            self.progress_updated.emit("开始训练循环...")
            for epoch in range(total_epochs):
                model.train()
                total_loss = 0
                
                # 更新总体训练进度（0-100%）
                total_progress = int((epoch / total_epochs) * 100)
                self.total_progress_updated.emit(total_progress)
                
                # 训练阶段：在训练数据上进行前向传播和反向传播
                train_batches = len(train_loader)
                for batch_idx, (images, labels) in enumerate(train_loader):
                    # 数据迁移至指定设备（GPU/CPU）
                    images, labels = images.to(device), labels.to(device)
                    # 前向传播：获取模型输出
                    outputs = model(images)
                    # 计算损失值
                    loss = criterion(outputs, labels)
                    
                    # 反向传播和参数更新
                    optimizer.zero_grad()
                    loss.backward()
                    # 梯度裁剪：防止梯度爆炸，提高训练稳定性
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
                    optimizer.step()
                    
                    # 累计训练损失
                    total_loss += loss.item() * images.size(0)
                    
                    # 更新当前epoch进度（0-100%）
                    epoch_progress = int(((batch_idx + 1) / train_batches) * 100)
                    self.epoch_progress_updated.emit(epoch_progress)
                    
                    # 每10个batch报告一次详细进度，便于监控训练状态
                    if batch_idx % 10 == 0:
                        self.progress_updated.emit(f"Epoch {epoch+1}/{total_epochs} - Batch {batch_idx+1}/{train_batches} - Loss: {loss.item():.6f}")
                
                # 学习率调度：根据预设策略调整学习率
                scheduler.step()
                
                # 验证阶段：在验证集上评估模型性能
                model.eval()
                val_loss = 0
                with torch.no_grad():
                    for images, labels in val_loader:
                        images, labels = images.to(device), labels.to(device)
                        outputs = model(images)
                        loss = criterion(outputs, labels)
                        val_loss += loss.item() * images.size(0)
                
                # 计算平均损失：用于评估模型性能和模型选择
                avg_train_loss = total_loss / len(train_dataset)
                avg_val_loss = val_loss / len(val_dataset)
                current_lr = optimizer.param_groups[0]['lr']
                
                self.progress_updated.emit(f'Epoch {epoch+1}/{total_epochs} - Train Loss: {avg_train_loss:.6f} - Val Loss: {avg_val_loss:.6f} - LR: {current_lr:.6f}')
                
                # 模型保存策略：保存验证损失最低的模型
                if avg_val_loss < best_val_loss:
                    best_val_loss = avg_val_loss
                    torch.save(model.state_dict(), 'unet1_best.pth')
                    self.progress_updated.emit(f"  -> 保存了新的最佳模型，验证损失: {avg_val_loss:.6f}")
            
            # 完成训练：设置进度条为100%，发送完成信号
            self.total_progress_updated.emit(100)
            self.epoch_progress_updated.emit(100)
            self.progress_updated.emit(f"训练完成。最佳验证损失: {best_val_loss:.6f}")
            
        except Exception as e:
            # 异常处理：捕获并报告训练过程中的所有错误
            self.progress_updated.emit(f"训练过程中出现错误: {str(e)}")
            import traceback
            self.progress_updated.emit(traceback.format_exc())
        finally:
            # 确保训练完成信号被发送，无论训练成功与否
            self.training_finished.emit()