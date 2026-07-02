import torch
import torch.nn as nn
from model import UNet

def test_learning_capability():
    print("Testing model learning capability...")
    
    # 创建模型
    model = UNet(in_channels=1, out_channels=1)
    criterion = nn.BCEWithLogitsLoss()  # 使用PyTorch内置的BCEWithLogitsLoss
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    # 创建一个简单但有意义的训练样本
    # 创建一个带有明显特征的输入和对应的标签
    torch.manual_seed(42)  # 确保可重复性
    
    # 创建输入 - 添加一些结构化特征
    x = torch.randn(1, 1, 128, 128)
    # 在输入中添加一个明显的圆形区域
    center_x, center_y = 64, 64
    for i in range(128):
        for j in range(128):
            if (i - center_x)**2 + (j - center_y)**2 < 20**2:
                x[0, 0, i, j] = 5.0  # 明显的高值区域
    
    # 创建对应的目标 - 圆形区域标记为1
    y = torch.zeros(1, 1, 128, 128)
    for i in range(128):
        for j in range(128):
            if (i - center_x)**2 + (j - center_y)**2 < 20**2:
                y[0, 0, i, j] = 1.0
    
    print(f"Input shape: {x.shape}")
    print(f"Target shape: {y.shape}")
    
    # 初始预测
    model.eval()
    with torch.no_grad():
        initial_output = model(x)
        initial_loss = criterion(initial_output, y)
        print(f"Initial loss: {initial_loss.item():.6f}")
        print(f"Initial output range: [{initial_output.min():.4f}, {initial_output.max():.4f}]")
    
    # 训练几个epoch观察loss变化
    model.train()
    losses = []
    
    for epoch in range(50):
        optimizer.zero_grad()
        output = model(x)
        loss = criterion(output, y)
        loss.backward()
        optimizer.step()
        
        losses.append(loss.item())
        
        if epoch % 10 == 0:
            print(f"Epoch {epoch:2d}, Loss: {loss.item():.6f}")
    
    # 最终评估
    model.eval()
    with torch.no_grad():
        final_output = model(x)
        final_loss = criterion(final_output, y)
        print(f"Final loss: {final_loss.item():.6f}")
        print(f"Final output range: [{final_output.min():.4f}, {final_output.max():.4f}]")
    
    # 检查是否学习了
    loss_improvement = initial_loss.item() - final_loss.item()
    print(f"Loss improvement: {loss_improvement:.6f}")
    
    if loss_improvement > 0.01:  # 显著改善
        print("✅ Model successfully learned - architecture is working correctly!")
        return True
    else:
        print("❌ Model failed to learn significantly - may need further investigation")
        return False

if __name__ == "__main__":
    test_learning_capability()