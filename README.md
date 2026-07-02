# CereVAS — Cerebral Vessel Analysis System

脑血管 MRA 分割与可视化系统

脑血管 MRA 分割与可视化系统 —— 基于深度学习的医学图像血管自动分割、交互式标注与三维可视化平台。

## 功能特性

- **多视角 UNet 血管分割**：三个独立训练的 UNet 模型分别从轴向（Axial）、冠状面（Coronal）、矢状面（Sagittal）逐切片预测脑血管
- **置信度引导投票融合**：结合热力图置信度的智能投票算法，集成三个模型结果，提高分割精度
- **形态学后处理**：连通域分析去除小噪声区域，保留有临床意义的血管结构
- **2D 多视图叠加显示**：正交三视图（横截面/矢状面/冠状面）+ 颜色编码区分不同模型结果
- **3D 可视化**：基于 VTK 的体绘制与 Marching Cubes 等值面提取
- **MIP 最大密度投影**：支持任意切面方向的 MIP 显示
- **交互式标注编辑**：多边形编辑器支持手动修改分割标注
- **模型重训练**：支持基于新标注数据重新训练模型

## 技术栈

| 技术 | 用途 |
|------|------|
| PyQt5 | GUI 框架 |
| VTK | 3D 可视化 |
| SimpleITK | 医学图像读写 |
| PyTorch | 深度学习模型训练/推理 |
| OpenCV | 图像处理与多边形编辑 |
| NumPy | 数据处理 |

## 项目结构

```
HYZY2.0/
├── main_window.py          # 主窗口，整合所有组件
├── image_display.py         # 2D 正交三视图显示
├── image_processor.py       # 医学图像加载与预处理
├── processing_controls.py   # 控制面板（文件/算法/后处理选择）
├── image_controls.py        # 复选框管理面板
├── fu_xuan.py               # 多模型结果融合叠加显示
├── VIT_Window.py            # VTK 3D 体绘制查看器
├── vtk_integration.py       # VTK 与 Qt 集成层
├── ts.py                    # MIP 最大密度投影查看器
│
├── model.py                 # UNet 网络定义 + FocalLoss
├── dataset.py               # MRA 数据集类（多方向切片）
├── predict1.py              # 轴向模型推理
├── predict2.py              # 冠状面模型推理
├── predict3.py              # 矢状面模型推理
├── votingFusion2.py         # 三模型置信度投票融合
├── postprocessing.py        # 连通域分析后处理
├── train_unet1.py           # 模型训练脚本
├── re_train.py              # 模型重训练模块
│
├── biaozu.py                # 图像标注对话框
├── dianji.py                # 可点击标注组件
├── xiu_biaozu.py            # 多边形编辑器（OpenCV）
├── zhuanhua.py              # mask/多边形互转工具
│
├── basicfunction.py         # 基础工具函数
├── theme_manager.py         # 深色/浅色主题切换
├── app_reset.py             # 应用重置
├── styles.css               # 全局深色主题样式
├── versions.py              # 环境版本检测
├── vtk_error_suppressor.py  # VTK 错误抑制器
│
├── unet1_best_t.pth         # 轴向模型权重（LFS）
├── unet2_best_t.pth         # 冠状面模型权重（LFS）
├── unet3_best_t.pth         # 矢状面模型权重（LFS）
│
├── mha/                     # 中间处理结果目录
└── image/                   # 图片资源目录
```

## 环境配置

### 依赖安装

```bash
pip install PyQt5>=5.15 vtk>=9.0 SimpleITK>=2.0 numpy>=1.20 torch opencv-python
```

### 克隆项目

```bash
# 安装 Git LFS 以获取模型权重
git lfs install
git clone git@github.com:Lovemelater/HYZY2.0.git
cd HYZY2.0
git lfs pull
```

## 使用说明

### 启动应用

```bash
python main_window.py
```

### 工作流程

1. **加载图像**：点击 "文件" → "选择文件"，选择 `.mha` / `.mhd` / `.nii` 格式的脑 MRA 图像
2. **血管分割**：选择导出方向（横截面/冠状面/矢状面），模型自动推理分割血管
3. **结果融合**：选择 "投票融合" 将三个模型结果融合为更准确的分割
4. **后处理**：选择 "后处理" 去除噪声小区域
5. **查看结果**：通过复选框控制不同结果的叠加显示，不同颜色区分不同模型
6. **3D 浏览**：右侧 3D 视图支持旋转、缩放、切片交互

### 三维视图交互

- **鼠标左键**：旋转视角
- **鼠标滚轮**：缩放
- **鼠标中键**：平移
- **点击 2D 视图**：打开标注编辑对话框

### 标注编辑

在 ImageDialog 中点击 "修改标注" 可进入多边形编辑器，支持：
- 拖动顶点修改形状
- 添加/删除顶点和多边形
- 反转 mask 区域
- 保存修改回 MHA 文件

## 模型训练

```bash
# 训练轴向模型
python train_unet1.py

# 训练冠状面模型
python train_unet2.py

# 训练矢状面模型
python train_unet3.py
```

训练数据需放置在 `D:/brain_data/` 或 `/home/guo/brain_data/` 目录下，包含 Normal-01 至 Normal-25 共 25 个受试者的 MRA 与标注数据。

## 许可证

本项目为学术竞赛作品，仅供学习研究使用。
