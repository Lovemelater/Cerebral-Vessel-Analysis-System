import torch
from torch.utils.data import DataLoader
from model import UNet, FocalLoss 
import torch.nn as nn  # 添加这个导入
from dataset import MRADataset
from tqdm import tqdm
import numpy as np

def get_data_paths():
    #训练集：20个样本（编号01-20）
    train_data = [f'/home/guo/brain_data/Normal-0{i:02d}/MRA/Normal0{i:02d}-MRA.mha' for i in range(1, 21)]
    train_label = [f'/home/guo/brain_data/Normal-0{i:02d}/MRA/{i:03d}.mha' for i in range(1, 21)]
    #验证集：5个样本（编号21-25）
    val_data = [f'/home/guo/brain_data/Normal-0{i:02d}/MRA/Normal0{i:02d}-MRA.mha' for i in range(21, 26)]
    val_label = [f'/home/guo/brain_data/Normal-0{i}/MRA/0{i}.mha' for i in range(21, 26)]
    return train_data, train_label, val_data, val_label

def dice_coefficient(pred, target, smooth=1e-6):
    """
    计算Dice系数
    """
    pred = torch.sigmoid(pred) > 0.5
    pred = pred.view(-1).float()
    target = target.view(-1).float()
    
    intersection = (pred * target).sum()
    dice = (2. * intersection + smooth) / (pred.sum() + target.sum() + smooth)
    return dice

def train():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')#设备选择：自动选择GPU或CPU
    train_data, train_label, val_data, val_label = get_data_paths()
    
    # 使用axis=0（轴向切片）
    train_dataset = MRADataset(train_data, train_label, axis=0)
    val_dataset = MRADataset(val_data, val_label, axis=0)
    
    train_loader = DataLoader(train_dataset, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=4)
    
    model = UNet().to(device)
    criterion = FocalLoss(alpha=0.25, gamma=2.0)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    # 使用更积极的学习率衰减策略
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=5, factor=0.5, verbose=True)
    
    # 早停机制参数
    best_val_dice = 0.0
    best_train_dice = 0.0
    patience = 10
    patience_counter = 0

    for epoch in range(50):  # 增加到100个epoch
        model.train()
        total_loss = 0
        total_dice = 0
        
        # 训练进度条
        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/50 (Train)", total=len(train_loader))
        for images, labels in train_pbar:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            optimizer.zero_grad()
            loss.backward()
            
            # 添加梯度裁剪防止梯度爆炸
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            total_loss += loss.item()
            dice = dice_coefficient(outputs, labels)
            total_dice += dice.item()
            train_pbar.set_postfix({'loss': f'{loss.item():.8f}', 'dice': f'{dice.item():.8f}'})
        
        # 验证进度条
        model.eval()
        val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/50 (Val)", total=len(val_loader))
        with torch.no_grad():
            val_loss = 0
            val_dice = 0
            for images, labels in val_pbar:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                dice = dice_coefficient(outputs, labels)
                val_loss += loss.item()
                val_dice += dice.item()
                val_pbar.set_postfix({'loss': f'{loss.item():.8f}', 'dice': f'{dice.item():.8f}'})
        
        # 输出最终loss和dice
        avg_train_loss = total_loss / len(train_loader)
        avg_train_dice = total_dice / len(train_loader)
        avg_val_loss = val_loss / len(val_loader)
        avg_val_dice = val_dice / len(val_loader)
        current_lr = optimizer.param_groups[0]['lr']
        print(f'Epoch {epoch+1}/50 - Train Loss: {avg_train_loss:.8f}, Train Dice: {avg_train_dice:.8f} - Val Loss: {avg_val_loss:.8f}, Val Dice: {avg_val_dice:.8f} - LR: {current_lr:.8f}')
        
        # 调整学习率
        scheduler.step(avg_val_dice)
        
        # 保存训练集上Dice最高的模型
        if avg_train_dice > best_train_dice:
            best_train_dice = avg_train_dice
            torch.save(model.state_dict(), 'unet1_best_t.pth')
            print(f"  -> 保存了训练集最佳模型，训练Dice系数: {avg_train_dice:.4f}")
        
        # 保存验证集上Dice最高的模型
        if avg_val_dice > best_val_dice:
            best_val_dice = avg_val_dice
            patience_counter = 0
            torch.save(model.state_dict(), 'unet1_best_v.pth')
            print(f"  -> 保存了验证集最佳模型，验证Dice系数: {avg_val_dice:.4f}")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  -> 早停在第 {epoch+1} 个epoch")
                break
    
    print(f"训练完成！最佳验证Dice系数: {best_val_dice:.4f}，最佳训练Dice系数: {best_train_dice:.4f}")
    return model

if __name__ == '__main__':
    train()