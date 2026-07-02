import numpy as np
from basicfunction import load_mha, save_mha, NormalizeImageData, ComposeBinaryLabelData
from model import UNet
import torch
import os
import gc

def predict2(file_name="D:/brain_data/Normal-001/MRA/Normal001-MRA.mha", i=2):
    try:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"使用设备: {device}")
        
        # 加载模型
        model_path = 'unet2_best_t.pth'  # 根据你实际保存的模型文件名调整
        model = UNet().to(device)
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        model.eval()
        
        # 加载体积数据
        data, origin, spacing = load_mha(file_name)
        print(f"数据形状: {data.shape}")
        slices = data.shape[1]  # axis=1 对应冠状面切片
        
        # 逐切片预测（沿axis=1方向）
        results = []
        for slice_idx in range(slices):
            data_slice = data[:, slice_idx, :]  # 提取冠状面切片
            data_slice = NormalizeImageData(data_slice)
            
            if np.allclose(data_slice, 0):
                print(f"警告: 切片 {slice_idx} 归一化后全为 0")

            if data_slice.dtype == np.uint16:
                data_slice = data_slice.astype(np.float32)
            
            data_tensor = torch.FloatTensor(data_slice).unsqueeze(0).unsqueeze(0).to(device)
            
            with torch.no_grad():
                logits = model(data_tensor)
                # 应用sigmoid将logits转换为概率值
                pred = torch.sigmoid(logits).cpu().numpy()
            results.append(pred[0, 0])
        
        # 合并结果并重新排列维度以匹配原始数据形状
        result_volume = np.stack(results, axis=1)  # axis=1对应训练时的切片方向
        print(f"预测结果范围: {result_volume.min():.6f}, {result_volume.max():.6f}")
        
        # 保存热力图到mha文件夹
        heatmap_path = os.path.join('mha', f'heatmap{i}.npy')
        os.makedirs(os.path.dirname(heatmap_path), exist_ok=True)
        np.save(heatmap_path, result_volume)
        
        # 应用阈值生成二值标签
        save_result = ComposeBinaryLabelData(result_volume)
        save_path = os.path.join('mha', f'test2_{i}.mha')
        
        # 确保保存目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        save_mha(save_result, save_path, origin, spacing)
        
        print(f"预测完成，热力图保存至 {heatmap_path}")
        print(f"结果保存至 {save_path}")
        gc.collect()
        return save_path
    except Exception as e:
        print(f"执行错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    predict2()