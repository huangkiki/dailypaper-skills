# CV/DL 概念知识库

> **维护规则**: 每次分析完一篇论文后，如果遇到新概念或现有概念的新应用，必须更新此文件。

---

## 如何使用本文件

1. **阅读论文时**: 快速查阅不熟悉的术语
2. **分析完论文后**: 将新学到的概念添加到对应分类
3. **概念分类原则**: 按技术领域 → 子领域 → 具体概念的层级组织

---

## 目录

1. [基础深度学习](#1-基础深度学习)
2. [计算机视觉](#2-计算机视觉)
3. [3D 视觉与几何](#3-3d-视觉与几何)
4. [生成模型](#4-生成模型)
5. [多模态与大模型](#5-多模态与大模型)
6. [机器人学与具身智能](#6-机器人学与具身智能)
7. [训练技术](#7-训练技术)
8. [常用数据集](#8-常用数据集)
9. [新概念暂存区](#9-新概念暂存区)

---

## 1. 基础深度学习

### 1.1 网络架构组件

| 术语 | 英文 | 说明 |
|------|------|------|
| 主干网络 | Backbone | 特征提取基础网络 (ResNet, ViT, etc.) |
| 颈部网络 | Neck | 连接 backbone 和 head 的模块 (FPN, PAN) |
| 检测头/分类头 | Head | 最终输出层 |
| 编码器 | Encoder | 将输入编码为特征表示 |
| 解码器 | Decoder | 将特征解码为输出 |
| 跳跃连接 | Skip Connection | 跨层连接，如 ResNet 的残差连接 |
| 多层感知机 | MLP | 全连接层堆叠 |

### 1.2 归一化与正则化

| 术语 | 英文 | 说明 |
|------|------|------|
| 批归一化 | Batch Normalization (BN) | 按 batch 维度归一化 |
| 层归一化 | Layer Normalization (LN) | Transformer 标准归一化 |
| 组归一化 | Group Normalization (GN) | 按 channel 分组归一化 |
| Dropout | Dropout | 随机丢弃神经元防止过拟合 |
| 权重衰减 | Weight Decay (WD) | L2 正则化 |

### 1.3 损失函数

| 术语 | 英文 | 公式/说明 |
|------|------|----------|
| 交叉熵 | Cross-Entropy | $-\sum y \log(\hat{y})$ |
| 均方误差 | MSE / L2 | $(y - \hat{y})^2$ |
| 平均绝对误差 | MAE / L1 | $\|y - \hat{y}\|$ |
| 平滑 L1 | Smooth L1 | Huber loss 变体 |
| 焦点损失 | Focal Loss | 处理类别不平衡 |
| Dice 损失 | Dice Loss | 分割常用，基于重叠度 |
| IoU 损失 | IoU Loss | 检测框回归 |
| 感知损失 | Perceptual Loss | 基于预训练网络特征 |
| 对抗损失 | Adversarial Loss | GAN 中判别器损失 |
| 对比损失 | Contrastive Loss | InfoNCE 等 |

### 1.4 优化器

| 术语 | 英文 | 说明 |
|------|------|------|
| 随机梯度下降 | SGD | 基础优化器 |
| 自适应矩估计 | Adam | 最常用的自适应优化器 |
| AdamW | AdamW | 解耦权重衰减的 Adam |
| 学习率 | Learning Rate (LR) | 梯度更新步长 |
| 学习率调度 | LR Scheduler | Cosine, StepLR, Warmup 等 |

---

## 2. 计算机视觉

### 2.1 目标检测

| 术语 | 英文 | 说明 |
|------|------|------|
| 锚框 | Anchor | 预定义的候选框 |
| 无锚框 | Anchor-free | 直接预测中心点 (FCOS, CenterNet) |
| 感兴趣区域池化 | RoI Pooling/Align | 提取固定大小特征 |
| 非极大值抑制 | NMS | 去除冗余检测框 |
| 特征金字塔网络 | FPN | 多尺度特征融合 |
| 交并比 | IoU | 框重叠度量 |
| 平均精度均值 | mAP | 检测评估指标 |

### 2.2 图像分割

| 术语 | 英文 | 说明 |
|------|------|------|
| 语义分割 | Semantic Segmentation | 像素级类别分类 |
| 实例分割 | Instance Segmentation | 区分不同实例 |
| 全景分割 | Panoptic Segmentation | 语义 + 实例 |
| 平均交并比 | mIoU | 分割评估指标 |

### 2.3 深度估计

| 术语 | 英文 | 说明 |
|------|------|------|
| 单目深度 | Monocular Depth | 单张图像估计深度 |
| 立体匹配 | Stereo Matching | 双目深度估计 |
| 视差 | Disparity | 双目中的像素偏移 |
| 尺度模糊性 | Scale Ambiguity | 单目深度的固有问题 |
| 相对深度 | Relative Depth | 无绝对尺度的深度 |
| 度量深度 | Metric Depth | 有真实尺度的深度 |
| 深度补全 | Depth Completion | 从稀疏深度恢复稠密 |

**评估指标**:
- AbsRel: 绝对相对误差
- RMSE: 均方根误差
- δ < 1.25: 阈值准确率

---

## 3. 3D 视觉与几何

### 3.1 3D 表示方法

| 术语 | 英文 | 说明 |
|------|------|------|
| 点云 | Point Cloud | 3D 点集合 |
| 体素 | Voxel | 3D 像素 |
| 网格 | Mesh | 三角面片表示 |
| 有符号距离场 | SDF | 隐式表面表示 |
| 神经辐射场 | NeRF | 神经隐式 3D 表示 |
| 3D 高斯泼溅 | 3D Gaussian Splatting (3DGS) | 显式 3D 高斯表示 |

### 3.2 3D 任务

| 术语 | 英文 | 说明 |
|------|------|------|
| 位姿估计 | Pose Estimation | 相机/物体姿态 |
| 同步定位与建图 | SLAM | 实时定位 + 地图构建 |
| 运动恢复结构 | SfM | 从图像重建 3D |
| 新视角合成 | Novel View Synthesis | 生成未见视角 |
| 多视图立体 | MVS | 多视图深度估计 |

### 3.3 相机与几何

| 术语 | 英文 | 说明 |
|------|------|------|
| 内参 | Intrinsics | 焦距、主点等 |
| 外参 | Extrinsics | 旋转、平移 |
| 重投影误差 | Reprojection Error | 3D→2D 投影误差 |
| 极线几何 | Epipolar Geometry | 双目几何约束 |
| 本质矩阵 | Essential Matrix | 相机间的几何关系 |

---

## 4. 生成模型

### 4.1 扩散模型 (Diffusion Models)

| 术语 | 英文 | 说明 |
|------|------|------|
| 去噪扩散概率模型 | DDPM | 扩散模型基础 |
| 噪声调度 | Noise Schedule | 噪声添加策略 (linear, cosine) |
| 去噪器 | Denoiser | 预测噪声的网络 |
| 采样步数 | Sampling Steps | 生成所需的迭代次数 |
| 无分类器引导 | Classifier-Free Guidance (CFG) | 条件生成增强 |
| 潜在扩散 | Latent Diffusion | 在潜空间做扩散 (Stable Diffusion) |
| Flow Matching | Flow Matching | 扩散的连续形式 |
| 整流流 | Rectified Flow | 更直的采样轨迹 |

#### Diffusion Model 详解

**前向过程 (加噪)**:
$$q(x_t | x_{t-1}) = \mathcal{N}(x_t; \sqrt{1-\beta_t} x_{t-1}, \beta_t I)$$

**反向过程 (去噪)**:
$$p_\theta(x_{t-1} | x_t) = \mathcal{N}(x_{t-1}; \mu_\theta(x_t, t), \Sigma_\theta(x_t, t))$$

**训练目标**: $\mathcal{L} = \mathbb{E}_{t, x_0, \epsilon} \| \epsilon - \epsilon_\theta(x_t, t) \|^2$

#### Flow Matching 详解

**前向过程**: $x^\tau = (1-\tau)\epsilon + \tau x_0$，其中 $\tau \in [0,1]$

**训练目标**: $\mathcal{L}_{FM} = \mathbb{E}_{x_0, \epsilon, \tau} \|v_\theta(x^\tau, \tau) - (x_0 - \epsilon)\|^2$

**采样**: $x^{\tau+\Delta\tau} = x^\tau + v_\theta(x^\tau, \tau) \cdot \Delta\tau$

| 特性 | Flow Matching | Diffusion |
|------|---------------|-----------|
| 路径 | 直线（Rectified） | 曲线（SDE/ODE） |
| 采样步数 | 通常更少 | 通常更多 |
| 训练目标 | 速度场 | 噪声/分数 |

#### EDM (Elucidating Diffusion Models)

统一的噪声调度: $\sigma(t) = t$

去噪目标: $\mathcal{L}(D_\theta, \sigma) = \mathbb{E}_{x_0, n} \|D_\theta(x_0 + n; \sigma) - x_0\|_2^2$

#### DiT (Diffusion Transformer)

用 Transformer 替代 U-Net 作为去噪网络：
- **Patchify**: 将图像分割成 patch 序列
- **AdaLN**: 用 Adaptive Layer Norm 注入时间步和条件
- **Self-Attention**: 全局建模 patch 间关系

### 4.2 其他生成模型

| 术语 | 英文 | 说明 |
|------|------|------|
| 生成对抗网络 | GAN | 对抗训练生成模型 |
| 变分自编码器 | VAE | 概率生成模型 |
| 自回归模型 | Autoregressive | 逐步生成 (GPT 风格) |
| 潜在空间 | Latent Space | 压缩表示空间 |

#### VAE 详解

**架构**: 输入 x → Encoder → μ, σ → 采样 z → Decoder → 重建 x'

**目标函数 (ELBO)**:
$$\mathcal{L} = \mathbb{E}_{q(z|x)}[\log p(x|z)] - D_{KL}(q(z|x) \| p(z))$$

**重参数化技巧**: $z = \mu + \sigma \odot \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)$

#### Autoregressive Generation 详解

$$p(x_1, x_2, ..., x_n) = \prod_{i=1}^{n} p(x_i | x_1, ..., x_{i-1})$$

| 方法 | 特点 |
|------|------|
| Autoregressive | 逐步生成，依赖历史 |
| Diffusion Model | 并行去噪，全局生成 |
| Flow Matching | 连续流，一步或少数步生成 |

#### Latent Diffusion 详解

```
图像 x → VAE Encoder → 潜在 z → Diffusion → 去噪 z' → VAE Decoder → 图像 x'
```

优势: 计算效率高，可生成高分辨率图像/视频

### 4.3 生成应用

| 术语 | 英文 | 说明 |
|------|------|------|
| 图像修复 | Inpainting | 补全缺失区域 |
| 超分辨率 | Super-Resolution | 图像放大 |
| 图像编辑 | Image Editing | 修改图像内容 |
| 文生图 | Text-to-Image | 从文本生成图像 |

---

## 5. 多模态与大模型

### 5.1 Transformer 架构

| 术语 | 英文 | 说明 |
|------|------|------|
| 自注意力 | Self-Attention | 序列内部关系建模 |
| 交叉注意力 | Cross-Attention | 序列间关系建模 |
| 多头注意力 | Multi-Head Attention | 并行多组注意力 |
| 位置编码 | Positional Encoding | 注入位置信息 (sinusoidal, RoPE, ALiBi) |
| 前馈网络 | Feed-Forward Network (FFN) | MLP 层 |
| KV 缓存 | KV Cache | 推理加速，缓存 key-value |

### 5.2 视觉 Transformer

| 术语 | 英文 | 说明 |
|------|------|------|
| Vision Transformer | ViT | 图像 Transformer |
| Swin Transformer | Swin | 窗口注意力 |
| 检测 Transformer | DETR | 端到端目标检测 |
| DINOv2 | DINOv2 | 自监督视觉特征 |

### 5.3 多模态模型

| 术语 | 英文 | 说明 |
|------|------|------|
| 视觉语言模型 | VLM | 理解图像和文本 |
| 大语言模型 | LLM | 文本生成模型 |
| CLIP | CLIP | 图文对比学习 |
| 视觉编码器 | Vision Encoder | 图像特征提取 (SigLIP, DINOv2) |
| 投影层 | Projector | 对齐不同模态的特征空间 |

---

## 6. 机器人学与具身智能

### 6.1 视觉-语言-动作模型 (VLA)

| 术语 | 英文 | 说明 |
|------|------|------|
| VLA | Vision-Language-Action | 端到端机器人策略 |
| 动作分块 | Action Chunking | 预测多步动作序列 |
| 动作专家 | Action Expert | 专门处理动作的模块 |
| 扩散策略 | Diffusion Policy | 用扩散模型生成动作 |
| Flow Matching Policy | Flow Matching Policy | 用 Flow Matching 生成动作 |

#### Action Chunking 详解

一次预测多个连续时间步的动作序列: $\mathbf{a}_t = (a_t, a_{t+1}, ..., a_{t+k-1})$

**优势**:
1. 时序一致性: 减少连续动作之间的抖动
2. 推理效率: 减少模型调用次数
3. 长程规划: 隐式建模更长时间范围的行为

**执行策略**: 全执行 / 重叠执行 / 加权平均

#### Inverse Dynamics Model (IDM)

给定当前状态和下一状态，预测导致状态转移的动作: $\hat{a}_t = f_{IDM}(s_t, s_{t+1})$

与 World Model（正向动力学）相反:
- **正向**: $(s_t, a_t) \rightarrow s_{t+1}$
- **逆向**: $(s_t, s_{t+1}) \rightarrow a_t$

**应用**: 从无动作标注的视频学习动作

### 6.2 模仿学习

| 术语 | 英文 | 说明 |
|------|------|------|
| 行为克隆 | Behavior Cloning (BC) | 直接模仿专家动作 |
| 逆强化学习 | Inverse RL | 从演示学习奖励 |
| 遥操作 | Teleoperation | 远程控制收集数据 |
| 演示数据 | Demonstration Data | 专家示范数据 |

### 6.3 强化学习

| 术语 | 英文 | 说明 |
|------|------|------|
| 马尔可夫决策过程 | MDP (Markov Decision Process) | RL 问题的标准数学框架 |
| 部分可观测 MDP | POMDP | 状态不完全可观测的 MDP |
| 策略梯度 | Policy Gradient | 直接优化策略 |
| PPO | Proximal Policy Optimization | 常用 on-policy RL 算法 |
| TRPO | Trust Region Policy Optimization | 信任域策略优化 |
| SAC | Soft Actor-Critic | Off-policy 最大熵 RL |
| DDPG | Deep Deterministic Policy Gradient | 确定性策略梯度 |
| ARS | Augmented Random Search | 无梯度进化策略 |
| 奖励塑形 | Reward Shaping | 设计奖励函数 |
| Sim-to-Real | Sim-to-Real | 仿真到真实迁移 |
| 域随机化 | Domain Randomization | 增加仿真多样性 |
| 域自适应 | Domain Adaptation | 显式/隐式辨识环境参数 |
| 课程学习 | Curriculum Learning | 渐进式增加任务难度 |
| 特权学习 | Privileged Learning | Teacher-Student 框架，教师有特权信息 |
| 稀疏奖励 | Sparse Reward | 只在任务完成时给奖励 |

#### MDP 详解

$$\langle S, A, T, R, H \rangle$$

- $S$: 状态空间 (State space)
- $A$: 动作空间 (Action space)
- $T: S \times A \rightarrow \Pi(S)$: 状态转移函数
- $R: S \times A \rightarrow \mathbb{R}$: 奖励函数
- $H$: 时间范围 (Horizon)

**马尔可夫性质**: $P(s_{t+1} | s_t, a_t, s_{t-1}, ...) = P(s_{t+1} | s_t, a_t)$

#### Policy 详解

**确定性策略**: $\pi: S \rightarrow A$

**随机策略**: $\pi: S \rightarrow \Pi(A)$

#### Value Function 详解

**State Value Function**:
$$V^\pi(s) = \mathbb{E}_{\tau \sim \pi}\left[\sum_{t=0}^{H} \gamma^t R(s_t, a_t) \mid s_0 = s\right]$$

**Q-Function**:
$$Q^\pi(s, a) = \mathbb{E}_{\tau \sim \pi}\left[\sum_{t=0}^{H} \gamma^t R(s_t, a_t) \mid s_0 = s, a_0 = a\right]$$

#### World Model 详解

学习预测环境动态: $\hat{s}_{t+1} = \hat{T}(s_t, a_t)$

**用途**: Model-Based RL / Data Augmentation / Imagination

#### Model-Based Planning 详解

利用学到的 World Model 在"想象"中搜索最优动作序列

**方法**:
- Best-of-N Sampling: 采样 N 个动作候选，选择最高价值
- MPC (Model Predictive Control): 规划 H 步，执行第一步，滚动时域
- Tree Search: MCTS, CEM

### 6.4 足式机器人运动 (Legged Locomotion)

| 术语 | 英文 | 说明 |
|------|------|------|
| 四足机器人 | Quadruped | 四条腿的机器人 (如 Unitree Go1/Go2, ANYmal) |
| 双足机器人 | Biped | 双腿机器人 |
| 人形机器人 | Humanoid | 人形形态的机器人 |
| 本体感知驱动 | Proprioceptive Actuation | 低传动比，可直接电流控制力矩 |
| 步态 | Gait | 行走模式 (trot, gallop, bound) |
| 中央模式发生器 | CPG (Central Pattern Generator) | 生成周期性运动的神经振荡器 |
| PD 策略 | PD Policy | 输出关节目标位置，由 PD 控制器跟踪 |
| 力矩策略 | Torque Policy | 直接输出关节力矩 |
| 高程图 | Elevation Map | 机器人周围的地形高度表示 |
| 感知运动 | Perceptive Locomotion | 使用视觉/深度感知的运动控制 |
| 运动模仿 | Motion Imitation | 从动捕数据学习运动 |
| 对抗运动先验 | AMP (Adversarial Motion Prior) | 用 GAIL 学习动作风格 |
| 轮腿混合 | Wheeled-Legged | 同时具有轮子和腿的机器人 |

### 6.5 移动操作 (Loco-manipulation)

| 术语 | 英文 | 说明 |
|------|------|------|
| 移动操作 | Loco-manipulation | 同时进行运动和操作 |
| 全身控制 | Whole-body Control | 协调全身运动的控制 |
| 分层控制 | Hierarchical Control | 高层规划 + 低层执行 |

### 6.6 机器人硬件

| 术语 | 英文 | 说明 |
|------|------|------|
| 末端执行器 | End-Effector | 机械臂末端 (夹爪等) |
| 自由度 | DoF (Degrees of Freedom) | 关节数量 |
| 本体感知 | Proprioception | 机器人自身状态感知 (IMU, 编码器) |
| 外部感知 | Exteroception | 环境感知 (相机, LiDAR) |
| 触觉传感 | Tactile Sensing | 触摸感知 |

### 6.7 仿真器

| 术语 | 英文 | 说明 |
|------|------|------|
| MuJoCo | MuJoCo | 常用物理仿真器 (开源) |
| Isaac Sim | Isaac Gym / Isaac Sim | NVIDIA GPU 并行仿真 |
| PyBullet | PyBullet | Python 物理仿真 |
| 刚性接触 | Rigid Contact | 仿真器中的刚体接触模型 |
| 可微分仿真器 | Differentiable Simulator | 支持梯度反传的仿真器 |

---

## 7. 训练技术

### 7.1 学习范式

| 术语 | 英文 | 说明 |
|------|------|------|
| 监督学习 | Supervised Learning | 使用标注数据训练 |
| 自监督学习 | Self-supervised Learning | 利用数据本身构造监督信号 |
| 半监督学习 | Semi-supervised Learning | 少量标注 + 大量无标注 |
| 对比学习 | Contrastive Learning | 通过正负样本对比学习 |
| 知识蒸馏 | Knowledge Distillation | 大模型指导小模型 |
| 微调 | Fine-tuning | 在预训练基础上调整 |
| 预训练 | Pre-training | 在大数据上初步训练 |

### 7.2 高效训练

| 术语 | 英文 | 说明 |
|------|------|------|
| LoRA | Low-Rank Adaptation | 低秩微调 |
| 量化 | Quantization | 降低精度 (INT8, INT4) |
| 混合精度 | Mixed Precision | FP16/BF16 训练 |
| 梯度累积 | Gradient Accumulation | 模拟大 batch |
| 梯度检查点 | Gradient Checkpointing | 用计算换内存 |

### 7.3 分布式训练

| 术语 | 英文 | 说明 |
|------|------|------|
| 数据并行 | Data Parallel (DP) | 复制模型，分割数据 |
| 模型并行 | Model Parallel | 分割模型到多卡 |
| 流水线并行 | Pipeline Parallel | 按层分割模型 |
| ZeRO | ZeRO | DeepSpeed 的优化器分片 |

---

## 8. 常用数据集

### 8.1 图像分类
- **ImageNet**: 1000 类, 120 万训练图像
- **CIFAR-10/100**: 10/100 类, 6 万图像

### 8.2 目标检测
- **COCO**: 80 类, 20 万图像
- **Pascal VOC**: 20 类, 1.1 万图像
- **Objects365**: 365 类, 200 万图像

### 8.3 语义分割
- **ADE20K**: 150 类, 2 万图像
- **Cityscapes**: 19 类, 5000 精细标注

### 8.4 深度估计
- **NYU Depth V2**: 室内, 1449 张
- **KITTI**: 室外驾驶场景
- **ScanNet**: 室内 3D 扫描

### 8.5 机器人操作
- **Open X-Embodiment**: 多机器人大规模数据集
- **DROID**: 机器人操作数据
- **RH20T**: 双手操作数据

---

## 9. 新概念暂存区

> **说明**: 分析论文时遇到的新概念先放这里，积累到一定数量后整理到上面对应分类。

| 概念 | 来源论文 | 简要说明 | 待归类到 |
|------|----------|----------|----------|
| *示例* | *Pi0.5* | *用 VLM 做机器人策略* | *6.1 VLA* |

---

## 更新日志

| 日期 | 更新内容 | 来源论文 |
|------|----------|----------|
| 2024-01 | 初始版本 | - |
| 2026-02-01 | 新增足式机器人运动、移动操作、仿真器等概念 | Ha et al. 2025 - Learning-based Legged Locomotion Survey |

---

*最后更新: 2026-02-01*
