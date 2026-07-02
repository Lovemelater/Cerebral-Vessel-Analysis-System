import torch
import torch.nn as nn
import torch.nn.functional as F

class UNet(nn.Module):
    def __init__(self, in_channels=1, out_channels=1):
        super(UNet, self).__init__()
        
        def CBR(in_channels, out_channels):
            return nn.Sequential(
                nn.Conv2d(in_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),  # 添加BatchNorm层
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, 3, padding=1),
                nn.BatchNorm2d(out_channels),  # 添加BatchNorm层
                nn.ReLU(inplace=True)
            )
        
        self.down1 = CBR(in_channels, 64)
        self.down2 = CBR(64, 128)
        self.down3 = CBR(128, 256)
        self.down4 = CBR(256, 512)
        self.down5 = CBR(512, 1024)
        
        self.maxpool = nn.MaxPool2d(2)
        self.up4 = nn.ConvTranspose2d(1024, 512, 2, stride=2)
        self.up3 = nn.ConvTranspose2d(512, 256, 2, stride=2)
        self.up2 = nn.ConvTranspose2d(256, 128, 2, stride=2)
        self.up1 = nn.ConvTranspose2d(128, 64, 2, stride=2)
        
        # 在上采样后也添加BatchNorm
        self.bn4 = nn.BatchNorm2d(512)
        self.bn3 = nn.BatchNorm2d(256)
        self.bn2 = nn.BatchNorm2d(128)
        self.bn1 = nn.BatchNorm2d(64)
        
        self.up_conv4 = CBR(1024, 512)
        self.up_conv3 = CBR(512, 256)
        self.up_conv2 = CBR(256, 128)
        self.up_conv1 = CBR(128, 64)
        
        self.final_conv = nn.Conv2d(64, out_channels, 1)
        
        # 初始化权重
        self._initialize_weights()

    def _initialize_weights(self):
        """
        _initialize_weights 方法作用：
        对网络中的所有参数进行手动初始化
        为不同类型的层使用不同的初始化策略
        """
        for m in self.modules():
            """
            使用 Kaiming 正态分布初始化权重（适合 ReLU 激活函数）
            """
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.ConvTranspose2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def forward(self, x):
        # 添加梯度检查点以减少内存使用并稳定训练
        conv1 = self.down1(x)
        x = self.maxpool(conv1)
        
        conv2 = self.down2(x)
        x = self.maxpool(conv2)
        
        conv3 = self.down3(x)
        x = self.maxpool(conv3)
        
        conv4 = self.down4(x)
        x = self.maxpool(conv4)
        
        x = self.down5(x)
        
        x = self.up4(x)
        x = self.bn4(x)  # 添加BatchNorm
        x = torch.cat((conv4, x), dim=1)
        x = self.up_conv4(x)
        
        x = self.up3(x)
        x = self.bn3(x)  # 添加BatchNorm
        x = torch.cat((conv3, x), dim=1)
        x = self.up_conv3(x)
        
        x = self.up2(x)
        x = self.bn2(x)  # 添加BatchNorm
        x = torch.cat((conv2, x), dim=1)
        x = self.up_conv2(x)
        
        x = self.up1(x)
        x = self.bn1(x)  # 添加BatchNorm
        x = torch.cat((conv1, x), dim=1)
        x = self.up_conv1(x)
        
        return self.final_conv(x) 

class FocalLoss(nn.Module):

    """
    继承自 nn.Module：使该类成为一个 PyTorch 模块，可以像其他损失函数一样使用
    """
    def __init__(self, alpha=0.25, gamma=2.0, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha #控制正负样本的权重平衡（默认 0.25，表示更关注正样本）
        self.gamma = gamma #gamma：聚焦参数，控制易分样本的权重衰减（默认 2.0）
        self.reduction = reduction #指定损失值的聚合方式（'mean'、'sum' 或 'none'）


    def forward(self, inputs, targets):
        """
        接收两个参数：inputs（模型输出的 logits）和 targets（真实标签）
        将输入展平为一维张量便于计算
        """
        inputs = inputs.view(-1)
        targets = targets.view(-1)
        
        # 使用binary cross entropy with logits作为基础损失函数
        bce_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        probs = torch.sigmoid(inputs)
        
        # 计算 pt (预测正确的概率)
        pt = torch.where(targets == 1, probs, 1 - probs)

        """
        正样本时为预测为正的概率
        负样本时为预测为负的概率
        """
        
        # 计算 alpha_t (针对类别不平衡)
        alpha_t = torch.where(targets == 1, self.alpha, 1 - self.alpha)
        #计算 alpha_t：根据类别分配不同的权重
        
        # 计算 focal loss
        focal_loss = alpha_t * (1 - pt) ** self.gamma * bce_loss #使用 (1 - pt) ** gamma 作为调制因子，降低易分样本的权重
        
        if self.reduction == 'mean':
            return focal_loss.mean()
        elif self.reduction == 'sum':
            return focal_loss.sum()
        else:
            return focal_loss
        """
        解决类别不平衡：通过 alpha 参数调整类别权重
        聚焦难分样本：通过 gamma 参数降低易分样本的损失贡献
        避免梯度消失：对误分类样本给予更多关注，保持较大的梯度
        """