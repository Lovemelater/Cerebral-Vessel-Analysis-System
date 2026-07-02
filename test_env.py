import sys, os
print(f'Python: {sys.version.split()[0]}')
print(f'路径: {os.getcwd()}')

# 1. 测试 PyTorch GPU
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA 可用: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'显卡型号: {torch.cuda.get_device_name(0)}')
    print(f'显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB')

# 2. 测试 SimpleITK
import SimpleITK as sitk
print(f'SimpleITK: {sitk.__version__}')

# 3. 测试 OpenCV
import cv2
print(f'OpenCV: {cv2.__version__}')

# 4. 测试 VTK
import vtk
print(f'VTK: {vtk.VTK_VERSION}')

# 5. 测试 PyQt5
from PyQt5.QtWidgets import QApplication
print('PyQt5: OK')

print('\\n✅ 环境创建成功！所有库已就绪。')
"