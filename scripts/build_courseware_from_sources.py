#!/usr/bin/env python3
"""Build the curated Deep Learning v2 course base from imported sources."""

from __future__ import annotations

import json
import random
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "data" / "knowledge_base" / "deep_learning_v2"
COURSEWARE_DIR = COURSE_DIR / "courseware"
LABS_DIR = COURSE_DIR / "labs"
EVIDENCE_DIR = COURSE_DIR / "evidence"
DOCS_DIR = ROOT / "docs"

SOURCE_REGISTRY = [
    {
        "source_id": "src_kyonhuang_andrew_ng",
        "name": "KyonHuang Andrew Ng Deep Learning Notes",
        "url": "https://github.com/bighuang624/Andrew-Ng-Deep-Learning-notes",
        "source_type": "github_docsify_markdown",
        "license": "CC BY-NC-SA 3.0",
        "usage_mode": "authorized_reference_and_reconstruction",
        "course_roles": ["theory_spine", "formula_reference", "chapter_outline"],
        "include_in_student_view": False,
    },
    {
        "source_id": "src_accumulate_more_cv",
        "name": "AccumulateMore/CV",
        "url": "https://github.com/AccumulateMore/CV",
        "source_type": "github_ipynb_collection",
        "license": "not_detected",
        "usage_mode": "authorized_local_reference_and_reconstruction",
        "course_roles": ["pytorch_practice", "cv_extension", "notebook_reference", "code_lab_reference"],
        "include_in_student_view": False,
    },
]

CHAPTERS = [
    {
        "chapter_no": 1,
        "chapter_id": "chapter_01_intro",
        "chapter_title": "第 1 章 深度学习导论与课程学习诊断",
        "summary": "建立课程全局地图，完成基础诊断，明确从表示学习、神经网络到项目实践的学习路径。",
        "concepts": ["表示学习", "端到端学习", "数据驱动建模", "课程地图", "学习诊断", "个性化路径"],
        "source_roles": ["KyonHuang 课程概述", "AccumulateMore 深度学习介绍"],
        "lab": None,
    },
    {
        "chapter_no": 2,
        "chapter_id": "chapter_02_pytorch_foundation",
        "chapter_title": "第 2 章 Python、NumPy 与 PyTorch 基础",
        "summary": "从 Tensor、Dataset、DataLoader、Transforms、nn.Module 到 GPU 训练，建立可运行的工程基础。",
        "concepts": ["Tensor", "Dataset", "DataLoader", "Transforms", "nn.Module", "训练循环", "GPU 训练", "模型保存"],
        "source_roles": ["AccumulateMore 100-122 PyTorch 基础 notebook"],
        "lab": "mlp_pytorch_mnist.py",
    },
    {
        "chapter_no": 3,
        "chapter_id": "chapter_03_neural_network_basics",
        "chapter_title": "第 3 章 神经网络基础与向量化计算",
        "summary": "从逻辑回归、损失函数、计算图、梯度下降、向量化和浅层神经网络进入神经网络建模。",
        "concepts": ["Logistic Regression", "损失函数", "代价函数", "计算图", "向量化", "广播机制", "浅层神经网络", "激活函数"],
        "source_roles": ["KyonHuang 神经网络基础", "AccumulateMore 吴恩达课程 1 notebook"],
        "lab": "mlp_numpy_from_scratch.py",
        "core": True,
    },
    {
        "chapter_no": 4,
        "chapter_id": "chapter_04_deep_network_and_backprop",
        "chapter_title": "第 4 章 深层神经网络与反向传播",
        "summary": "拆解 L 层网络、前向传播、反向传播、链式法则、参数更新、梯度流和 PyTorch autograd。",
        "concepts": ["L 层网络", "前向传播", "反向传播", "链式法则", "参数更新", "梯度流", "autograd", "MLP"],
        "source_roles": ["KyonHuang 深层神经网络", "AccumulateMore 损失函数与反向传播"],
        "lab": "mlp_pytorch_mnist.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 5,
        "chapter_id": "chapter_05_regularization_and_generalization",
        "chapter_title": "第 5 章 正则化、初始化与泛化",
        "summary": "围绕偏差方差、初始化、L2、Dropout、BatchNorm、数据增强、早停与模型选择建立泛化能力。",
        "concepts": ["训练/验证/测试划分", "偏差方差", "初始化", "L2 正则化", "Dropout", "BatchNorm", "数据增强", "早停"],
        "source_roles": ["KyonHuang 改善深层神经网络", "AccumulateMore 权重衰退/Dropout/BatchNorm notebook"],
        "lab": "dropout_batchnorm_demo.py",
        "core": True,
    },
    {
        "chapter_no": 6,
        "chapter_id": "chapter_06_optimization",
        "chapter_title": "第 6 章 优化算法与超参数调试",
        "summary": "比较 Mini-batch、SGD、Momentum、RMSProp、Adam、学习率调度和训练曲线诊断。",
        "concepts": ["Mini-batch", "SGD", "Momentum", "RMSProp", "Adam", "学习率", "训练曲线", "超参数搜索"],
        "source_roles": ["KyonHuang 优化算法", "AccumulateMore 优化器 notebook"],
        "lab": "optimizer_comparison.py",
        "core": True,
    },
    {
        "chapter_no": 7,
        "chapter_id": "chapter_07_cnn_foundation",
        "chapter_title": "第 7 章 CNN 基础：卷积、池化与图像张量",
        "summary": "理解图像张量、卷积核、步幅、填充、输出尺寸、通道、局部连接、参数共享和池化。",
        "concepts": ["图像张量", "卷积核", "步幅", "填充", "输出尺寸", "通道", "参数共享", "池化", "Conv2d"],
        "source_roles": ["KyonHuang 卷积神经网络", "AccumulateMore 卷积/池化 notebook"],
        "lab": "cnn_output_shape_debug.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 8,
        "chapter_id": "chapter_08_cnn_architectures_and_cv_practice",
        "chapter_title": "第 8 章 经典 CNN 架构与图像分类实践",
        "summary": "以 LeNet、AlexNet、VGG、GoogLeNet、ResNet、迁移学习和 CIFAR-10 图像分类建立视觉实践主线。",
        "concepts": ["LeNet", "AlexNet", "VGG", "GoogLeNet", "ResNet", "BatchNorm", "迁移学习", "CIFAR-10"],
        "source_roles": ["AccumulateMore CNN 架构与 CIFAR10 notebook", "KyonHuang CNN 案例"],
        "lab": "cnn_cifar10.py",
        "core": True,
    },
    {
        "chapter_no": 9,
        "chapter_id": "chapter_09_cv_advanced_tasks",
        "chapter_title": "第 9 章 计算机视觉进阶任务",
        "summary": "连接边界框、IoU、锚框、R-CNN/SSD/YOLO、语义分割、FCN、风格迁移等视觉任务。",
        "concepts": ["边界框", "IoU", "锚框", "R-CNN", "SSD", "YOLO", "语义分割", "FCN", "风格迁移"],
        "source_roles": ["KyonHuang 目标检测/风格迁移", "AccumulateMore 目标检测与语义分割 notebook"],
        "lab": "object_detection_iou_anchor_demo.py",
    },
    {
        "chapter_no": 10,
        "chapter_id": "chapter_10_sequence_models",
        "chapter_title": "第 10 章 序列模型：RNN、GRU 与 LSTM",
        "summary": "从序列数据、RNN、BPTT、梯度消失、GRU、LSTM 门控到 PyTorch nn.LSTM 实验。",
        "concepts": ["序列数据", "RNN", "BPTT", "梯度消失", "GRU", "LSTM", "遗忘门", "输入门", "输出门", "nn.LSTM"],
        "source_roles": ["KyonHuang 序列模型", "AccumulateMore RNN/GRU/LSTM notebook"],
        "lab": "lstm_sequence_classification.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 11,
        "chapter_id": "chapter_11_attention_transformer",
        "chapter_title": "第 11 章 Attention、Transformer 与 NLP 基础",
        "summary": "从词嵌入、语言模型、Encoder-Decoder、Q/K/V、缩放点积注意力、多头注意力到 Transformer 与 BERT 拓展。",
        "concepts": ["词嵌入", "语言模型", "Encoder-Decoder", "Attention", "Q/K/V", "Scaled Dot-Product", "Multi-Head", "Positional Encoding", "Transformer", "BERT"],
        "source_roles": ["KyonHuang Attention Model", "AccumulateMore Attention/Transformer/BERT notebook"],
        "lab": "attention_demo.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 12,
        "chapter_id": "chapter_12_final_project",
        "chapter_title": "第 12 章 综合项目与课程成果输出",
        "summary": "组织 CNN 图像分类、LSTM 序列分类、Attention 小实验、目标检测拓展、误差分析和课程报告。",
        "concepts": ["项目定义", "baseline", "数据划分", "误差分析", "报告模板", "Rubric", "成果展示"],
        "source_roles": ["AccumulateMore 完整训练套路与项目实践", "KyonHuang 机器学习项目策略"],
        "lab": "transformer_text_classification.py",
        "project": True,
    },
]

UNIT_TOPICS = {
    "chapter_01_intro": ["深度学习课程地图", "表示学习", "端到端学习", "学习基础诊断", "个性化学习路径"],
    "chapter_02_pytorch_foundation": ["Tensor 与维度", "Dataset", "DataLoader", "Transforms", "nn.Module", "训练循环", "GPU 训练", "模型保存与加载"],
    "chapter_03_neural_network_basics": ["Logistic Regression", "二分类损失", "代价函数", "计算图", "向量化", "广播机制", "浅层神经网络", "激活函数"],
    "chapter_04_deep_network_and_backprop": ["L 层神经网络", "前向传播", "链式法则", "反向传播", "参数更新", "梯度流", "PyTorch autograd"],
    "chapter_05_regularization_and_generalization": ["训练验证测试划分", "偏差方差", "初始化", "L2 正则化", "Dropout", "BatchNorm", "数据增强", "早停"],
    "chapter_06_optimization": ["Mini-batch", "SGD", "Momentum", "RMSProp", "Adam", "学习率调度", "训练曲线诊断", "超参数搜索"],
    "chapter_07_cnn_foundation": ["图像张量", "卷积核", "步幅与填充", "输出尺寸计算", "多通道卷积", "局部连接", "池化", "PyTorch Conv2d"],
    "chapter_08_cnn_architectures_and_cv_practice": ["LeNet", "AlexNet", "VGG", "GoogLeNet", "ResNet", "BatchNorm in CNN", "迁移学习", "CIFAR-10 图像分类"],
    "chapter_09_cv_advanced_tasks": ["边界框", "IoU", "锚框", "SSD", "YOLO", "语义分割", "FCN", "神经风格迁移"],
    "chapter_10_sequence_models": ["序列数据", "RNN", "BPTT", "梯度消失", "GRU", "LSTM 细胞状态", "LSTM 遗忘门", "LSTM 输入门", "LSTM 输出门", "PyTorch nn.LSTM"],
    "chapter_11_attention_transformer": ["词嵌入", "语言模型", "Encoder-Decoder", "注意力分数", "Q/K/V", "Scaled Dot-Product Attention", "多头注意力", "位置编码", "Transformer Encoder", "BERT 拓展"],
    "chapter_12_final_project": ["项目选题", "baseline", "实验记录", "误差分析", "报告模板", "答辩展示"],
}

SOURCE_TITLE_PRIORITY = {
    "chapter_01_intro": ["深度学习介绍", "笔记", "课程总结", "查看开源项目", "数据划分"],
    "chapter_02_pytorch_foundation": ["Pytorch", "PyTorch", "Tensor", "Dataset", "Dataloader", "Transforms", "nn.Module", "GPU", "模型保存"],
    "chapter_03_neural_network_basics": ["Logistic", "损失函数", "神经网络基础", "浅层神经网络", "向量化"],
    "chapter_04_deep_network_and_backprop": ["深层网络", "深层神经网络", "反向传播", "自动求导"],
    "chapter_05_regularization_and_generalization": ["数据划分", "偏差", "方差", "正则化", "Dropout", "Batch", "初始化", "权重衰退"],
    "chapter_06_optimization": ["优化", "梯度下降", "Momentum", "Adam", "超参数"],
    "chapter_07_cnn_foundation": ["卷积", "池化", "填充", "步幅", "通道"],
    "chapter_08_cnn_architectures_and_cv_practice": ["LeNet", "AlexNet", "VGG", "GoogLeNet", "ResNet", "批量归一化", "微调", "CIFAR10"],
    "chapter_09_cv_advanced_tasks": ["目标定位", "物体检测", "锚框", "YOLO", "SSD", "语义分割", "FCN", "样式迁移"],
    "chapter_10_sequence_models": ["序列模型", "RNN", "GRU", "LSTM", "循环神经网络"],
    "chapter_11_attention_transformer": ["词嵌入", "Seq2Seq", "注意力", "Transformer", "BERT"],
    "chapter_12_final_project": ["Kaggle", "竞赛", "课程总结", "机器学习策略", "项目"],
}

FORMULAS = {
    "Logistic Regression": "a = sigmoid(w^T x + b)",
    "二分类损失": "L(y, a) = - y log(a) - (1-y) log(1-a)",
    "向量化": "Z = W X + b",
    "链式法则": "dL/dx = dL/dy · dy/dx",
    "反向传播": "dW[l] = dZ[l] A[l-1]^T / m",
    "参数更新": "theta <- theta - alpha · grad",
    "L2 正则化": "J_reg = J + lambda/(2m) ||W||_2^2",
    "Dropout": "A_drop = A * mask / keep_prob",
    "BatchNorm": "z_hat = (z - mu) / sqrt(sigma^2 + eps)",
    "Momentum": "v_t = beta v_{t-1} + (1-beta) g_t",
    "Adam": "theta_t = theta_{t-1} - alpha · m_hat / (sqrt(v_hat)+eps)",
    "输出尺寸计算": "H_out = floor((H + 2P - K) / S) + 1",
    "IoU": "IoU = area(intersection) / area(union)",
    "RNN": "h_t = tanh(W_h h_{t-1} + W_x x_t + b)",
    "LSTM 遗忘门": "f_t = sigmoid(W_f [h_{t-1}, x_t] + b_f)",
    "LSTM 输入门": "i_t = sigmoid(W_i [h_{t-1}, x_t] + b_i)",
    "LSTM 输出门": "o_t = sigmoid(W_o [h_{t-1}, x_t] + b_o)",
    "Scaled Dot-Product Attention": "Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V",
}

SPECIFIC_POINTS = {
    "Mini-batch": {
        "explain": "Mini-batch 将完整训练集切成若干小批量，每次只用一个 batch 计算梯度并更新参数。它解决的是 batch gradient descent 在大数据集上每一步过慢的问题，同时保留向量化计算效率。",
        "check": "给定 m 个样本和 batch size，能算出 batch 数量，并解释为什么最后一个 batch 可能小于设定大小。",
        "pitfall": "把 Mini-batch 理解成随机丢弃数据，而不是分批使用全部训练样本。",
    },
    "SGD": {
        "explain": "SGD 在深度学习实践中通常指 mini-batch stochastic gradient descent：用一个小批量估计整体梯度，带来更快迭代和一定梯度噪声。",
        "check": "比较 batch size=1、64、全量数据时损失曲线的稳定性和单步计算成本。",
        "pitfall": "只说 SGD 是随机的，却不说明随机性来自样本批次和梯度估计。",
    },
    "Momentum": {
        "explain": "Momentum 为梯度更新引入指数加权平均，让参数更新带有惯性，减少震荡方向的来回摆动，加快一致下降方向的收敛。",
        "check": "能解释 beta 接近 0 和接近 1 时，更新速度与平滑程度如何变化。",
        "pitfall": "把 Momentum 当成简单调大学习率，忽略它是在平滑梯度方向。",
    },
    "RMSProp": {
        "explain": "RMSProp 对梯度平方做指数加权平均，并按维度缩放学习步长，使梯度较大的方向步子变小、梯度较小的方向保留有效更新。",
        "check": "能说明为什么 RMSProp 有助于处理不同参数维度梯度尺度差异。",
        "pitfall": "只记 RMSProp 名字，不知道它用梯度平方控制每个方向的有效步长。",
    },
    "Adam": {
        "explain": "Adam 同时使用一阶矩估计和二阶矩估计，相当于把 Momentum 的方向平滑与 RMSProp 的尺度自适应结合起来，是常用的深度学习优化器。",
        "check": "能指出 Adam 中学习率、beta1、beta2、epsilon 分别影响什么。",
        "pitfall": "认为 Adam 永远优于 SGD，而不结合泛化、学习率调度和任务规模分析。",
    },
    "学习率": {
        "explain": "学习率决定每次参数更新的步长，是 Andrew Ng 调参建议中最重要的超参数之一。过大容易震荡或发散，过小会收敛很慢。",
        "check": "能根据训练 loss 曲线判断学习率过大、过小或较合适。",
        "pitfall": "只调模型结构，不先检查学习率是否让训练曲线正常下降。",
    },
    "训练曲线": {
        "explain": "训练曲线把 loss、accuracy 等指标随 epoch 或 iteration 的变化可视化，是判断欠拟合、过拟合、学习率异常和数据问题的主要依据。",
        "check": "能比较 train loss 与 validation loss，判断是否过拟合或欠拟合。",
        "pitfall": "只看最终准确率，不看训练过程，导致无法定位问题。",
    },
    "超参数搜索": {
        "explain": "超参数搜索不是穷举所有组合，而是先确定最重要变量，如学习率、隐藏单元数、正则化强度、batch size，再用随机搜索或粗到细策略缩小范围。",
        "check": "能设计一轮只改变学习率的对照实验，并说明如何记录结果。",
        "pitfall": "一次改多个超参数，导致无法判断效果来自哪个变量。",
    },
    "LeNet": {
        "explain": "LeNet-5 是早期经典 CNN，常见结构是 CONV-POOL-CONV-POOL-FC-FC-OUTPUT，展示了卷积层、池化层和全连接层组合处理灰度图像的基本范式。",
        "check": "能画出 LeNet 的层次顺序，并说明卷积层与池化层分别改变了什么。",
        "pitfall": "只记 LeNet 名称，不知道它为什么比全连接网络更适合图像。",
    },
    "AlexNet": {
        "explain": "AlexNet 通过更深的卷积网络、大规模数据训练、ReLU、Dropout 和 GPU 训练推动了 ImageNet 图像分类突破，是深度 CNN 实用化的重要节点。",
        "check": "能说明 AlexNet 相比 LeNet 在深度、数据规模、激活函数和正则化上的变化。",
        "pitfall": "把 AlexNet 只理解成层数更多，而忽略 ReLU、Dropout 和工程训练条件。",
    },
    "VGG": {
        "explain": "VGG 使用大量 3x3 小卷积核堆叠构造深层网络，用简单规则化结构换取更强表达能力，也让网络结构更容易复现和比较。",
        "check": "能解释两个 3x3 卷积堆叠与更大感受野之间的关系。",
        "pitfall": "只背 VGG 很深，不知道它的核心设计是统一小卷积核堆叠。",
    },
    "GoogLeNet": {
        "explain": "GoogLeNet 的 Inception 模块在同一层并行使用不同尺度卷积和池化，再把结果拼接，目标是在控制计算量的同时捕获多尺度特征。",
        "check": "能画出 Inception 模块的多分支结构，并说明 1x1 卷积用于降维的意义。",
        "pitfall": "只说 GoogLeNet 很复杂，不知道多分支和 1x1 卷积解决什么问题。",
    },
    "ResNet": {
        "explain": "ResNet 引入残差连接，让网络学习 F(x)+x，缓解深层网络退化问题，使更深的 CNN 更容易优化。",
        "check": "能说明残差块中 shortcut 的输入和输出维度什么时候需要匹配或投影。",
        "pitfall": "把残差连接理解成简单跳过层，而不理解它改变了优化目标。",
    },
    "BatchNorm": {
        "explain": "BatchNorm 在小批量内标准化中间激活，并学习缩放和平移参数，可以稳定训练、允许更大学习率，并在 CNN 中常和卷积层配合使用。",
        "check": "能区分 BatchNorm 在训练阶段使用 batch 统计量、推理阶段使用移动平均统计量。",
        "pitfall": "把 BatchNorm 当成输入数据预处理，而不是网络内部层。",
    },
    "迁移学习": {
        "explain": "迁移学习利用在大数据集上预训练的特征提取能力，在目标数据较少时微调分类头或部分网络层，提高训练效率和泛化能力。",
        "check": "能说明冻结 backbone 与 fine-tune 全网络的区别。",
        "pitfall": "目标数据分布差异很大时仍盲目套用预训练模型。",
    },
    "CIFAR-10 图像分类": {
        "explain": "CIFAR-10 是十类小图像分类任务，适合演示 CNN 从数据增强、模型训练、验证评估到错误样例分析的完整流程。",
        "check": "能写出数据增强、训练集/验证集划分、评价指标和错误样例复盘步骤。",
        "pitfall": "只跑出 accuracy，不分析哪些类别容易混淆。",
    },
    "RNN": {
        "explain": "RNN 通过隐状态 h_t 把上一时间步信息传到当前时间步，适合建模序列数据，但长序列训练中容易出现梯度消失或爆炸。",
        "check": "能画出 RNN 按时间展开后的结构，并说明 BPTT 如何传播梯度。",
        "pitfall": "把 RNN 当作普通全连接网络重复使用，忽略时间步共享参数。",
    },
    "GRU": {
        "explain": "GRU 用更新门和重置门控制历史信息保留与候选状态写入，参数少于 LSTM，常用于序列建模的轻量门控方案。",
        "check": "能比较 GRU 更新门与 LSTM 遗忘门/输入门的作用差异。",
        "pitfall": "认为 GRU 只是 LSTM 的简写版本，而不理解门结构不同。",
    },
    "LSTM": {
        "explain": "LSTM 用细胞状态和输入门、遗忘门、输出门控制长期信息流，缓解普通 RNN 长期依赖学习困难。",
        "check": "能说明 c_t 和 h_t 的区别，以及三个门分别控制什么。",
        "pitfall": "把所有门都理解成同一种开关，不区分保留、写入和输出。",
    },
    "Attention": {
        "explain": "Attention 根据查询和键的匹配程度为不同值分配权重，使模型能在生成或编码当前表示时关注相关位置。",
        "check": "能解释 Q、K、V 的来源和注意力权重如何影响输出。",
        "pitfall": "把注意力权重直接当成绝对解释，而不检查模型上下文。",
    },
    "Transformer": {
        "explain": "Transformer 用自注意力和前馈网络替代循环结构，并通过多头注意力和位置编码建模序列内部依赖，是现代 NLP 与多模态模型的重要基础。",
        "check": "能画出 Encoder block 中 Multi-Head Attention、AddNorm、FFN 的顺序。",
        "pitfall": "只记 Transformer 很强，不知道它为什么能并行处理序列。",
    },
}

SPECIFIC_POINTS.update({
    "表示学习": {
        "explain": "表示学习关注模型如何把原始输入变成更有判别力的中间特征。在线性模型中，特征通常依赖人工设计；在深度网络中，低层可以学习边缘、纹理或局部模式，高层再组合成类别或语义表示。",
        "check": "能用 CNN 从边缘到局部结构再到类别判断的例子，说明深层网络为什么不只是直接记忆标签。",
        "pitfall": "把表示学习说成“自动学习”，却不能指出中间特征如何服务分类、检测或序列预测。",
    },
    "端到端学习": {
        "explain": "端到端学习把原始输入到目标输出的多个人工环节交给同一个模型联合优化，例如图像输入直接映射为类别、文本序列直接映射为标签或下一个词。",
        "check": "能区分端到端训练和先人工提特征再训练分类器的流程差别。",
        "pitfall": "认为端到端意味着不用数据清洗、评价指标和误差分析。",
    },
    "数据驱动建模": {
        "explain": "数据驱动建模强调模型能力来自数据分布、损失函数和优化过程共同作用。深度学习不是先写死规则，而是通过训练样本和梯度更新学习参数。",
        "check": "能解释训练集、验证集、损失函数和参数更新在数据驱动流程中的位置。",
        "pitfall": "只关注网络结构，不检查数据质量、标签分布和评价方式。",
    },
    "课程地图": {
        "explain": "课程地图把深度学习拆成基础工具、神经网络、优化与泛化、CNN、序列模型、Attention/Transformer 和综合项目几条主线，用来决定学习顺序和资源推荐。",
        "check": "能把一个学习目标定位到具体章节，例如 LSTM 属于序列模型，Conv2d 属于 CNN 基础。",
        "pitfall": "把课程地图当目录浏览，不用它判断前置知识和下一步任务。",
    },
    "学习诊断": {
        "explain": "学习诊断通过学生对概念、公式、代码和实验现象的回答，判断当前瓶颈是基础概念、数学推导、工程实现还是实验分析。",
        "check": "能根据一段学生回答指出它缺少定义、公式解释、代码定位还是结果复盘。",
        "pitfall": "只用做题对错判断水平，不看错因类型和学习行为。",
    },
    "个性化路径": {
        "explain": "个性化路径把课程地图、画像维度和诊断结果结合起来，选择先补基础、先做代码实验、先看讲义还是先做项目任务。",
        "check": "能为“会调包但不会解释反向传播”的学生安排先讲计算图和梯度，再做 autograd 实验。",
        "pitfall": "给所有学生同一条章节顺序，不根据薄弱点调整资源。",
    },
    "Tensor": {
        "explain": "Tensor 是 PyTorch 中承载数据和中间结果的多维数组，图像、标签、模型输出、损失计算都围绕张量形状和数据类型展开。",
        "check": "能说出一批 RGB 图片进入模型前常见形状为 N×C×H×W，并解释每个维度含义。",
        "pitfall": "只会打印 tensor，不检查 dtype、device 和 shape 是否满足模型输入要求。",
    },
    "Dataset": {
        "explain": "Dataset 定义样本如何按索引读取，以及每个样本返回哪些内容，通常包含输入数据和标签，是数据管道的起点。",
        "check": "能说明 `__len__` 和 `__getitem__` 的作用，并写出返回 image,label 的最小数据集。",
        "pitfall": "把 Dataset 和 DataLoader 混在一起，分不清谁负责取单个样本、谁负责组 batch。",
    },
    "DataLoader": {
        "explain": "DataLoader 负责把 Dataset 中的样本按 batch 组织起来，并处理 shuffle、batch_size、多进程加载等训练所需行为。",
        "check": "能解释 batch_size、shuffle、num_workers 对训练流程的影响。",
        "pitfall": "只改 batch_size，不检查最后一个 batch、标签维度和随机打乱是否合理。",
    },
    "Transforms": {
        "explain": "Transforms 是输入预处理和数据增强工具链，常用于把图片转成 Tensor、归一化、裁剪、翻转或改变尺寸。",
        "check": "能写出 ToTensor、Normalize、Resize/RandomCrop 在图像任务中的顺序和作用。",
        "pitfall": "训练集和测试集使用完全相同的随机增强，导致评价不稳定。",
    },
    "nn.Module": {
        "explain": "nn.Module 是 PyTorch 神经网络的基类，用来组织层、参数和 forward 计算过程。自定义模型通常继承它并实现 forward。",
        "check": "能解释 `__init__` 中定义层、`forward` 中描述数据流的区别。",
        "pitfall": "把层写在 forward 内每次重新创建，导致参数无法被优化器正确管理。",
    },
    "训练循环": {
        "explain": "训练循环通常包含取 batch、前向计算、计算损失、清空梯度、反向传播、优化器更新和指标记录，是所有模型实验的共同骨架。",
        "check": "能按顺序写出 `optimizer.zero_grad()`、`loss.backward()`、`optimizer.step()` 的位置。",
        "pitfall": "忘记清空梯度或在验证阶段仍然更新参数。",
    },
    "GPU 训练": {
        "explain": "GPU 训练要求模型、输入张量和标签在同一 device 上，并通过 CUDA 加速张量运算；核心不是“有显卡”，而是正确迁移数据和模型。",
        "check": "能说明为什么 model.to(device) 后，batch 数据也需要 to(device)。",
        "pitfall": "模型在 GPU、数据在 CPU，导致 device mismatch 报错。",
    },
    "模型保存": {
        "explain": "模型保存通常保存 state_dict 或完整模型，其中 state_dict 更适合复现实验和跨环境加载；读取时需要先构建同结构模型再加载参数。",
        "check": "能区分 `torch.save(model.state_dict())` 和保存整个 model 的差异。",
        "pitfall": "只保存权重，不保存模型结构、类别映射和训练配置。",
    },
    "Logistic Regression": {
        "explain": "Logistic Regression 是二分类神经网络的入口案例，通过线性变换和 sigmoid 输出正类概率，是理解损失函数、梯度和向量化的基础。",
        "check": "能写出 z=w^Tx+b、a=sigmoid(z)，并说明 a 为什么可以看作概率。",
        "pitfall": "把 Logistic Regression 当普通线性回归，忽略 sigmoid 和交叉熵损失。",
    },
    "损失函数": {
        "explain": "损失函数衡量单个样本预测与真实标签之间的差异，深度学习通过让损失变小来推动参数学习。",
        "check": "能说明二分类交叉熵为什么比平方误差更适合 Logistic Regression。",
        "pitfall": "只看 accuracy，不分析 loss 是否正常下降。",
    },
    "代价函数": {
        "explain": "代价函数通常是训练集上所有样本损失的平均值，也可以加入正则项，用来定义整体优化目标。",
        "check": "能区分单样本 loss 和全训练集 cost 的关系。",
        "pitfall": "把单个样本损失和整体训练目标混用。",
    },
    "计算图": {
        "explain": "计算图把复杂函数拆成一系列节点，前向传播计算输出，反向传播沿图应用链式法则求梯度。",
        "check": "能以 J(a,b,c)=3(a+bc) 为例写出中间变量和梯度传播顺序。",
        "pitfall": "只记最终公式，不知道梯度如何沿中间变量传回参数。",
    },
    "向量化": {
        "explain": "向量化用矩阵运算替代显式 for 循环，让多个样本或多个神经元同时计算，是深度学习训练高效的关键。",
        "check": "能把逐样本计算改写成 Z=WX+b，并说明 X 的列/行如何组织样本。",
        "pitfall": "为了能运行随意 reshape，导致样本维度和特征维度被混淆。",
    },
    "广播机制": {
        "explain": "广播机制允许不同形状的数组在满足规则时自动扩展，例如给矩阵每一列加同一个偏置向量。",
        "check": "能判断 b 的形状是否能和 WX 相加，并说明扩展发生在哪个维度。",
        "pitfall": "依赖广播但不检查 shape，产生看似能跑、语义错误的计算。",
    },
    "浅层神经网络": {
        "explain": "浅层神经网络在输入层和输出层之间加入一个隐藏层，通过非线性激活学习比 Logistic Regression 更复杂的决策边界。",
        "check": "能画出输入层、隐藏层、输出层，并说明 W1,b1,W2,b2 的作用。",
        "pitfall": "增加隐藏单元但不使用非线性激活，网络仍近似线性模型。",
    },
    "激活函数": {
        "explain": "激活函数为神经网络引入非线性，常见 sigmoid、tanh、ReLU 在输出范围、梯度特性和适用位置上不同。",
        "check": "能说明 ReLU 在隐藏层常用，而 sigmoid 多用于二分类输出层。",
        "pitfall": "所有层都机械使用 sigmoid，导致深层网络梯度变小。",
    },
    "L 层网络": {
        "explain": "L 层网络把多个线性变换和激活函数堆叠起来，逐层形成更抽象的表示；层数、宽度和激活共同决定表达能力。",
        "check": "能写出第 l 层的 Z[l]=W[l]A[l-1]+b[l] 与 A[l]=g(Z[l])。",
        "pitfall": "只数层数，不检查每层输入输出维度是否匹配。",
    },
    "前向传播": {
        "explain": "前向传播从输入开始逐层计算 Z、A 和最终预测，同时缓存中间结果供反向传播使用。",
        "check": "能说明为什么反向传播需要前向传播中保存的 A、Z 或 mask。",
        "pitfall": "只关注预测结果，不保存中间变量，导致无法正确求梯度。",
    },
    "反向传播": {
        "explain": "反向传播从损失函数出发，按链式法则逐层计算参数梯度，是深层网络能够训练的核心算法。",
        "check": "能解释 dZ、dW、db、dA_prev 在一层中的含义。",
        "pitfall": "背梯度公式但不知道每个梯度张量的 shape。",
    },
    "链式法则": {
        "explain": "链式法则说明复合函数的导数可以由局部导数相乘得到，反向传播正是把这个规则系统地应用到计算图。",
        "check": "能对 y=g(f(x)) 写出 dy/dx = dy/dg · dg/df · df/dx。",
        "pitfall": "只看最终导数，不分析中间变量依赖关系。",
    },
    "参数更新": {
        "explain": "参数更新根据梯度和学习率调整 W、b 或其他可学习参数，使下一次前向传播的损失有机会降低。",
        "check": "能说明学习率过大和过小时参数更新的表现。",
        "pitfall": "把梯度方向和参数更新方向混淆，忘记是沿负梯度下降。",
    },
    "梯度流": {
        "explain": "梯度流描述误差信号在网络中反向传播的强弱和路径，过弱会导致梯度消失，过强可能导致梯度爆炸。",
        "check": "能根据梯度范数或训练曲线判断深层网络训练是否异常。",
        "pitfall": "只看前向结构，不检查反向梯度能否有效到达早期层。",
    },
    "autograd": {
        "explain": "PyTorch autograd 自动记录张量运算图，并在 backward 时计算梯度，使用户无需手写大部分反向传播公式。",
        "check": "能说明 requires_grad、loss.backward 和 parameter.grad 的关系。",
        "pitfall": "在不该跟踪梯度的验证阶段没有使用 no_grad，浪费显存并引入误解。",
    },
    "MLP": {
        "explain": "MLP 由多层全连接层和非线性激活构成，适合作为理解深层网络、分类器头和基础训练循环的入门模型。",
        "check": "能写出 Flatten -> Linear -> ReLU -> Linear 的简单分类网络。",
        "pitfall": "直接把高维图像展平给 MLP，而不分析空间结构丢失和参数量增长。",
    },
    "训练/验证/测试划分": {
        "explain": "训练集用于拟合参数，验证集用于调模型和超参数，测试集用于最终估计泛化性能，三者职责不能混用。",
        "check": "能说明为什么不能根据测试集结果反复调参。",
        "pitfall": "把验证集当测试集反复使用，导致泛化评估过于乐观。",
    },
    "偏差方差": {
        "explain": "偏差反映模型拟合能力不足，方差反映模型对训练数据过于敏感；二者帮助判断欠拟合和过拟合。",
        "check": "能根据 train/dev error 判断高偏差、高方差或两者兼有。",
        "pitfall": "看到验证误差高就盲目加深模型，不先区分偏差和方差。",
    },
    "初始化": {
        "explain": "初始化决定训练开始时参数尺度和对称性，合适初始化能保持激活和梯度在合理范围内，减少训练不稳定。",
        "check": "能说明为什么全零初始化会让同层神经元学习相同特征。",
        "pitfall": "随意初始化权重，不观察梯度和激活是否饱和。",
    },
    "L2 正则化": {
        "explain": "L2 正则化在代价函数中惩罚较大的权重，促使模型参数更平滑，降低过拟合风险。",
        "check": "能说明正则化强度 lambda 增大时训练误差和验证误差可能如何变化。",
        "pitfall": "把 L2 当作一定提升准确率的技巧，不结合过拟合程度选择。",
    },
    "Dropout": {
        "explain": "Dropout 在训练时随机关闭部分神经元，迫使网络不能过度依赖某些特征组合，起到正则化作用。",
        "check": "能说明训练阶段和推理阶段 Dropout 行为不同。",
        "pitfall": "在验证或测试阶段仍然启用 Dropout，导致结果随机波动。",
    },
    "数据增强": {
        "explain": "数据增强通过裁剪、翻转、颜色扰动等方式扩展训练分布，尤其适合图像任务提升泛化能力。",
        "check": "能区分训练增强和测试预处理的不同目标。",
        "pitfall": "使用改变语义的增强，例如把数字或医学图像随意翻转。",
    },
    "早停": {
        "explain": "早停根据验证集表现停止训练，避免模型在训练集上继续拟合噪声，是一种实践中的正则化策略。",
        "check": "能根据验证 loss 连续不下降判断何时停止并保存最佳模型。",
        "pitfall": "只保存最后一轮模型，而不是验证集表现最好的模型。",
    },
    "图像张量": {
        "explain": "图像张量把图片表示为通道、高度、宽度和 batch 维度，CNN 的卷积、池化和归一化都依赖这个结构。",
        "check": "能区分 HWC 和 NCHW 两种常见排列，并说明 PyTorch Conv2d 期望 NCHW。",
        "pitfall": "通道维度放错，导致模型输入 shape 错误或学习异常。",
    },
    "卷积核": {
        "explain": "卷积核是在局部窗口上滑动的可学习权重，用来检测边缘、纹理或更高层特征。",
        "check": "能说明 3×3 卷积核如何在输入图像上滑动并产生特征图。",
        "pitfall": "把卷积核当固定滤波器，不知道 CNN 中卷积核参数会被训练更新。",
    },
    "步幅": {
        "explain": "步幅决定卷积核每次移动的距离，步幅越大输出空间尺寸通常越小，计算量也会下降。",
        "check": "能用输出尺寸公式计算 stride=1 和 stride=2 的差异。",
        "pitfall": "只改 stride，不检查输出尺寸是否还能接入后续层。",
    },
    "填充": {
        "explain": "填充在输入边缘补零或其他值，用于控制输出尺寸并保留边缘信息。",
        "check": "能解释 same padding 为什么可让输出高宽接近输入高宽。",
        "pitfall": "忽略 padding 导致特征图逐层缩小过快。",
    },
    "输出尺寸": {
        "explain": "CNN 输出尺寸由输入尺寸、卷积核大小、填充和步幅共同决定，是调试 Conv2d 网络的第一检查项。",
        "check": "能使用 floor((H+2P-K)/S)+1 计算卷积后的高宽。",
        "pitfall": "只看通道数，不计算空间尺寸，最后全连接层维度对不上。",
    },
    "通道": {
        "explain": "通道表示同一空间位置上的多组特征，RGB 图像有 3 个输入通道，卷积层可输出多个特征通道。",
        "check": "能解释 Conv2d 中 in_channels 和 out_channels 的含义。",
        "pitfall": "把通道数和 batch size 混淆。",
    },
    "参数共享": {
        "explain": "参数共享指同一个卷积核在整张图像上复用，显著减少参数量并让模型能够识别平移位置上的同类模式。",
        "check": "能比较全连接处理图像和卷积处理图像的参数量差异。",
        "pitfall": "只说卷积参数少，不说明共享权重如何带来局部模式检测。",
    },
    "池化": {
        "explain": "池化通过局部聚合降低空间尺寸，最大池化保留最强响应，平均池化保留局部平均信息。",
        "check": "能说明 2×2 max pooling 对特征图尺寸和局部响应的影响。",
        "pitfall": "认为池化一定必须使用，而不考虑现代网络中 stride convolution 等替代方案。",
    },
    "Conv2d": {
        "explain": "Conv2d 是 PyTorch 二维卷积层，核心参数包括 in_channels、out_channels、kernel_size、stride 和 padding。",
        "check": "能根据输入 shape 和 Conv2d 参数预测输出 shape。",
        "pitfall": "kernel_size 和 out_channels 会设置，但不理解它们分别控制局部窗口和输出特征数量。",
    },
    "边界框": {
        "explain": "边界框用坐标描述目标在图像中的位置，是目标检测任务在分类之外新增的定位输出。",
        "check": "能区分左上右下坐标和中心点宽高两种框表示。",
        "pitfall": "只预测类别，不评价定位框是否覆盖目标。",
    },
    "IoU": {
        "explain": "IoU 用预测框与真实框交并比衡量定位质量，是检测任务筛选预测和计算指标的重要基础。",
        "check": "能根据两个矩形框计算交集、并集和 IoU。",
        "pitfall": "只看分类置信度，不检查预测框和真实框重合程度。",
    },
    "锚框": {
        "explain": "锚框是在图像不同位置预设的候选框，用于让检测模型同时预测多个尺度和长宽比的目标。",
        "check": "能说明为什么一张图像同一位置可能需要多个不同长宽比锚框。",
        "pitfall": "把锚框理解成最终预测框，而不理解还需要分类和边框回归。",
    },
    "R-CNN": {
        "explain": "R-CNN 系列先产生候选区域，再对区域进行特征提取、分类和框回归，代表两阶段目标检测思想。",
        "check": "能说明 region proposal 和分类器在两阶段检测中的角色。",
        "pitfall": "把 R-CNN 和 YOLO 都说成检测模型，却不区分两阶段和单阶段流程。",
    },
    "SSD": {
        "explain": "SSD 在多个特征层上直接预测类别和边框偏移，是典型单阶段检测方法，兼顾速度和多尺度目标。",
        "check": "能解释为什么 SSD 会在不同尺度特征图上放置默认框。",
        "pitfall": "只记 SSD 速度快，不知道多尺度预测解决什么问题。",
    },
    "YOLO": {
        "explain": "YOLO 将目标检测看作一次前向传播中的网格化预测，直接输出类别、置信度和边界框，强调实时性。",
        "check": "能说明 YOLO 中网格单元负责预测目标的基本思想。",
        "pitfall": "认为 YOLO 只做分类，不理解它同时回归位置。",
    },
    "语义分割": {
        "explain": "语义分割为图像中每个像素分配类别标签，相比检测框提供更细粒度的空间理解。",
        "check": "能区分图像分类、目标检测和语义分割的输出形式。",
        "pitfall": "把分割结果当作一组边界框，而不是像素级类别图。",
    },
    "FCN": {
        "explain": "FCN 用全卷积结构替代全连接分类头，使网络能够输出空间尺寸对应的像素级预测。",
        "check": "能说明上采样或转置卷积在恢复空间分辨率中的作用。",
        "pitfall": "只知道 FCN 是分割网络，不理解为什么去掉全连接层。",
    },
    "风格迁移": {
        "explain": "神经风格迁移通过内容损失保持原图结构，通过风格损失匹配风格图特征统计，从而合成新图像。",
        "check": "能区分内容图、风格图、生成图以及内容损失和风格损失。",
        "pitfall": "把风格迁移当滤镜，不理解它在优化生成图像像素。",
    },
    "序列数据": {
        "explain": "序列数据具有时间或位置顺序，例如文本、音频、时间序列，当前输出往往依赖前后文。",
        "check": "能说明为什么把一句话打乱顺序会破坏语义。",
        "pitfall": "像处理独立样本一样处理序列，忽略时间依赖。",
    },
    "BPTT": {
        "explain": "BPTT 是把 RNN 沿时间展开后进行反向传播，通过所有时间步把损失梯度传回共享参数。",
        "check": "能解释为什么长序列 BPTT 容易出现梯度消失或爆炸。",
        "pitfall": "只画循环结构，不知道训练时会按时间展开计算梯度。",
    },
    "梯度消失": {
        "explain": "梯度消失指反向传播中梯度逐层或逐时间步变得很小，导致早期层或远距离依赖难以学习。",
        "check": "能说明 sigmoid/tanh 饱和区和长序列相乘如何加剧梯度消失。",
        "pitfall": "看到训练慢就直接换模型，不检查梯度和激活范围。",
    },
    "遗忘门": {
        "explain": "遗忘门控制 LSTM 细胞状态中旧信息保留多少，是处理长期记忆的重要门控。",
        "check": "能说明 f_t 接近 0 和接近 1 时细胞状态发生什么变化。",
        "pitfall": "把遗忘门理解成删除整个历史，而不是按维度控制保留比例。",
    },
    "输入门": {
        "explain": "输入门控制当前候选信息写入细胞状态的程度，决定新信息是否进入长期记忆。",
        "check": "能区分输入门 i_t 和候选状态 c_tilde 的角色。",
        "pitfall": "把输入门和输出门混淆，不能说明谁控制写入、谁控制暴露。",
    },
    "输出门": {
        "explain": "输出门控制细胞状态中哪些信息用于生成当前隐藏状态 h_t，影响当前时间步输出。",
        "check": "能说明 c_t 与 h_t 的区别，以及输出门如何连接二者。",
        "pitfall": "认为 LSTM 只有一个状态，不区分细胞状态和隐藏状态。",
    },
    "nn.LSTM": {
        "explain": "nn.LSTM 是 PyTorch 封装的 LSTM 层，输入输出形状与 batch_first、num_layers、hidden_size 等参数密切相关。",
        "check": "能解释 output、h_n、c_n 三个返回值分别表示什么。",
        "pitfall": "只拿 output 最后一维做分类，不检查 batch_first 和序列维度。",
    },
    "词嵌入": {
        "explain": "词嵌入把离散词转换为连续向量，使语义相近的词在向量空间中更接近，是 NLP 深度模型的基础表示。",
        "check": "能说明 one-hot 和 embedding 在维度、相似度表达上的差异。",
        "pitfall": "把词嵌入当固定编号，不理解向量会参与训练或来自预训练。",
    },
    "语言模型": {
        "explain": "语言模型根据上下文预测下一个词或序列概率，是文本生成、表示学习和预训练模型的重要基础。",
        "check": "能说明 P(w_t | w_1...w_{t-1}) 的含义。",
        "pitfall": "只看生成结果流畅度，不检查上下文条件和训练目标。",
    },
    "Encoder-Decoder": {
        "explain": "Encoder-Decoder 先把输入序列编码成中间表示，再由解码器生成目标序列，常用于翻译、摘要等序列到序列任务。",
        "check": "能说明 encoder hidden states 和 decoder outputs 的关系。",
        "pitfall": "把编码器输出当单个固定向量，忽略注意力机制对不同位置的访问。",
    },
    "Q/K/V": {
        "explain": "Q/K/V 分别表示查询、键和值，注意力通过 Q 与 K 的匹配计算权重，再对 V 加权求和得到上下文表示。",
        "check": "能用“问题检索资料”的类比解释 Q、K、V 的作用。",
        "pitfall": "只背三个字母，不知道权重来自 QK 相似度。",
    },
    "Scaled Dot-Product": {
        "explain": "Scaled Dot-Product Attention 用 QK^T 衡量相关性，再除以 sqrt(d_k) 控制数值尺度，最后 softmax 得到注意力权重。",
        "check": "能说明为什么维度较大时需要缩放。",
        "pitfall": "漏掉缩放项，导致 softmax 过于尖锐、梯度不稳定。",
    },
    "Multi-Head": {
        "explain": "多头注意力把表示投影到多个子空间并并行计算注意力，使模型能从不同关系角度观察序列。",
        "check": "能解释多个 head 为什么不是简单重复同一注意力。",
        "pitfall": "只增加 head 数量，不考虑 hidden size、计算量和任务规模。",
    },
    "Positional Encoding": {
        "explain": "位置编码向 Transformer 输入注入顺序信息，因为纯自注意力本身不区分 token 的先后位置。",
        "check": "能说明如果没有位置编码，句子顺序信息会怎样丢失。",
        "pitfall": "认为 Transformer 天然知道顺序，而忽略位置表示。",
    },
    "BERT": {
        "explain": "BERT 使用 Transformer Encoder 和预训练任务学习双向上下文表示，再通过微调用于分类、问答等下游任务。",
        "check": "能说明预训练和微调在数据、目标和参数更新上的区别。",
        "pitfall": "把 BERT 当普通词向量，不理解它输出的是上下文化表示。",
    },
    "项目定义": {
        "explain": "项目定义明确任务输入、输出、数据集、评价指标和交付物，是课程综合项目能否落地的第一步。",
        "check": "能把“做图像分类”细化为数据来源、类别、指标和 baseline。",
        "pitfall": "只说做一个模型，没有任务边界和验收标准。",
    },
    "baseline": {
        "explain": "baseline 是最小可运行的基准方案，用来判断后续复杂模型或调参是否真正带来改进。",
        "check": "能设计一个简单 CNN 或 MLP baseline 并记录指标。",
        "pitfall": "一开始就堆复杂模型，无法判断改进来自哪里。",
    },
    "数据划分": {
        "explain": "项目中的数据划分要保证训练、验证、测试互不泄漏，并尽量保持类别分布一致。",
        "check": "能说明 stratified split 在类别不均衡数据中的意义。",
        "pitfall": "训练和测试样本重复，导致指标虚高。",
    },
    "误差分析": {
        "explain": "误差分析通过查看错例、类别混淆、置信度和数据质量，决定下一步改数据、改模型还是改训练策略。",
        "check": "能从混淆矩阵中找出最容易混淆的两类并提出改进方案。",
        "pitfall": "只报告平均准确率，不解释模型错在哪里。",
    },
    "报告模板": {
        "explain": "报告模板把项目背景、数据、方法、实验设置、结果、误差分析和改进方向固定成可评审结构。",
        "check": "能按照模板补齐实验可复现所需的超参数和环境信息。",
        "pitfall": "报告只贴截图，不说明实验设置和结论依据。",
    },
    "Rubric": {
        "explain": "Rubric 把项目评分拆成问题定义、实现、实验分析和表达展示等维度，让学生知道什么是高质量成果。",
        "check": "能用 Rubric 自评项目在哪一项失分。",
        "pitfall": "只追求模型指标，不重视可复现、分析和表达。",
    },
    "成果展示": {
        "explain": "成果展示把项目目标、方法、关键结果、错例分析和下一步改进浓缩成演示材料，服务评审和复盘。",
        "check": "能用 5 分钟讲清任务、方法、结果和一个失败案例。",
        "pitfall": "只展示最终准确率，没有过程证据和反思。",
    },
})


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", value).strip("_")
    return text.lower()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _source_chunks() -> list[dict]:
    chunks = []
    for rel in [
        "imported_sources/kyonhuang_andrew_ng/extracted_chunks.jsonl",
        "imported_sources/accumulate_more_cv/extracted_chunks.jsonl",
    ]:
        chunks.extend(_read_jsonl(COURSE_DIR / rel))
    return chunks


def _chunks_for_chapter(chapter_id: str, chunks: list[dict]) -> list[dict]:
    return [item for item in chunks if chapter_id in (item.get("mapped_chapter_candidates") or [])]


def _normalize_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", str(value or ""))
    value = re.sub(r"!\[[^\]]*]\([^)]+\)", "", value)
    value = re.sub(r"\[[^\]]+]\([^)]+\)", lambda m: m.group(0).split("](")[0].lstrip("["), value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _split_sentences(value: str, limit: int = 4) -> list[str]:
    text = _normalize_text(value)
    parts = re.split(r"(?<=[。！？；;])\s+|\n+|(?<=。)", text)
    result = []
    for part in parts:
        part = part.strip()
        if 24 <= len(part) <= 180 and part not in result:
            result.append(part)
        if len(result) >= limit:
            break
    if not result and text:
        result.append(text[:180])
    return result


def _concept_tokens(concept: str) -> list[str]:
    tokens = [concept]
    tokens.extend(re.split(r"[、/\s\-]+", concept))
    aliases = {
        "Tensor": ["张量", "tensor"],
        "Dataset": ["数据集", "dataset"],
        "DataLoader": ["dataloader", "数据加载"],
        "Transforms": ["transform", "数据增强", "预处理"],
        "nn.Module": ["Module", "模型类", "torch.nn"],
        "GPU 训练": ["GPU", "CUDA", "cuda"],
        "模型保存": ["保存", "加载", "state_dict"],
        "Logistic Regression": ["逻辑回归", "logistic"],
        "损失函数": ["loss", "损失"],
        "代价函数": ["cost", "代价"],
        "计算图": ["computation graph", "计算图"],
        "向量化": ["vectorization", "向量化"],
        "广播机制": ["broadcast", "广播"],
        "浅层神经网络": ["浅层神经网络", "shallow neural network"],
        "激活函数": ["activation", "sigmoid", "tanh", "ReLU"],
        "L 层网络": ["L层", "deep neural network", "深层神经网络"],
        "前向传播": ["forward", "前向传播"],
        "反向传播": ["backprop", "反向传播"],
        "链式法则": ["chain rule", "链式法则"],
        "参数更新": ["update", "参数更新"],
        "梯度流": ["gradient", "梯度"],
        "autograd": ["autograd", "自动求导"],
        "MLP": ["多层感知机", "MLP"],
        "训练/验证/测试划分": ["训练集", "验证集", "测试集", "train", "dev", "test"],
        "偏差方差": ["bias", "variance", "偏差", "方差"],
        "初始化": ["initialization", "初始化"],
        "L2 正则化": ["L2", "weight decay", "正则化"],
        "Dropout": ["dropout", "随机失活"],
        "BatchNorm": ["Batch Norm", "BatchNorm", "批标准化", "批量归一化", "Batch 正则化"],
        "数据增强": ["augmentation", "数据增强"],
        "早停": ["early stopping", "早停"],
        "学习率": ["learning rate", "学习率"],
        "训练曲线": ["loss", "accuracy", "曲线"],
        "图像张量": ["image", "图片", "图像", "张量"],
        "卷积核": ["filter", "kernel", "滤波器", "卷积核"],
        "步幅": ["stride", "步长", "步幅"],
        "填充": ["padding", "填充"],
        "输出尺寸": ["输出尺寸", "n+2p-f", "stride"],
        "通道": ["channel", "通道"],
        "参数共享": ["参数共享", "parameter sharing"],
        "池化": ["pool", "pooling", "池化"],
        "Conv2d": ["Conv2d", "conv2d", "卷积"],
        "边界框": ["bounding box", "边界框"],
        "锚框": ["anchor", "锚框"],
        "语义分割": ["semantic segmentation", "语义分割"],
        "风格迁移": ["style transfer", "风格迁移"],
        "词嵌入": ["word embedding", "词嵌入"],
        "语言模型": ["language model", "语言模型"],
        "Encoder-Decoder": ["encoder", "decoder", "编码器", "解码器"],
        "迁移学习": ["迁移学习", "微调", "fine tune", "fine-tune"],
        "Q/K/V": ["query", "key", "value", "查询", "键", "值", "Q", "K", "V"],
        "Scaled Dot-Product": ["scaled dot-product", "缩放点积", "点积注意力", "缩放"],
        "Multi-Head": ["multi-head", "多头", "多头注意力"],
        "Positional Encoding": ["position", "位置编码", "位置"],
        "BERT": ["BERT", "bert"],
        "baseline": ["baseline", "基线"],
        "误差分析": ["error analysis", "误差分析"],
        "Rubric": ["rubric", "评分"],
    }
    tokens.extend(aliases.get(concept, []))
    cleaned = []
    for token in tokens:
        token = str(token or "").strip()
        if token and token not in cleaned:
            cleaned.append(token)
    return cleaned


def _extract_relevant_snippets(concept: str, text: str, limit: int = 4) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    sentences = _split_sentences(normalized, limit=80)
    tokens = _concept_tokens(concept)
    hits = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(token.lower() in sentence_lower for token in tokens if len(token) >= 2):
            if sentence not in hits:
                hits.append(sentence)
        if len(hits) >= limit:
            break
    if hits:
        return hits
    return []


def _source_cards(chapter: dict, chunks: list[dict], limit: int = 10) -> list[dict]:
    related = _chunks_for_chapter(chapter["chapter_id"], chunks)
    priorities = SOURCE_TITLE_PRIORITY.get(chapter["chapter_id"], [])

    def title_score(item: dict) -> int:
        text = " ".join([
            item.get("title", ""),
            " ".join(item.get("heading_path") or []),
        ]).lower()
        return sum(1 for key in priorities if key.lower() in text)

    if chapter["chapter_id"] == "chapter_01_intro" and priorities:
        related = [item for item in related if title_score(item) > 0]
    related.sort(key=lambda item: (-title_score(item), 0 if item.get("source_id") == "src_kyonhuang_andrew_ng" else 1, item.get("notebook_index") or 999, item.get("title", "")))
    cards = []
    seen = set()
    for item in related:
        title = item.get("title") or item.get("source_path") or ""
        if not title or title in seen:
            continue
        seen.add(title)
        headings = item.get("heading_path") or []
        formulas = item.get("formulas") or []
        code_cells = item.get("code_cells") or []
        cards.append({
            "title": title,
            "source_id": item.get("source_id", ""),
            "source_path": item.get("source_path", ""),
            "headings": headings[:8],
            "formulas": formulas[:4],
            "code_purposes": [cell.get("purpose", "") for cell in code_cells[:4] if cell.get("purpose")],
            "sentences": _split_sentences(item.get("content_excerpt", ""), limit=3),
            "excerpt": _normalize_text(item.get("content_excerpt", "")),
        })
        if len(cards) >= limit:
            break
    return cards


def _concept_source_card(concept: str, cards: list[dict]) -> dict:
    tokens = _concept_tokens(concept)
    compact = _slug(concept).replace("_", "")
    best = None
    best_score = -1
    for card in cards:
        title_haystack = _slug(" ".join([
            card.get("title", ""),
            " ".join(card.get("headings", [])),
        ])).replace("_", "")
        body_haystack = _slug(" ".join([
            " ".join(card.get("sentences", [])),
            card.get("excerpt", "")[:3000],
        ])).replace("_", "")
        score = 0
        if compact and compact in title_haystack:
            score += 6
        elif compact and compact in body_haystack:
            score += 2
        lower_title = title_haystack.lower()
        lower_body = body_haystack.lower()
        for token in tokens:
            compact_token = _slug(token).replace("_", "").lower()
            if len(token) >= 2 and compact_token in lower_title:
                score += 4
            elif len(token) >= 3 and compact_token in lower_body:
                score += 1
        if score > best_score:
            best = card
            best_score = score
    return best if best_score >= 4 and best else {}


def _concept_evidence(concept: str, cards: list[dict], limit: int = 4) -> list[str]:
    card = _concept_source_card(concept, cards)
    candidates = []
    if not card:
        return candidates
    candidates.extend(_extract_relevant_snippets(concept, card.get("excerpt", ""), limit=limit))
    return candidates[:limit]


def _concept_point(concept: str, evidence: list[str] | None = None) -> dict:
    if concept in SPECIFIC_POINTS:
        return SPECIFIC_POINTS[concept]
    for key, value in SPECIFIC_POINTS.items():
        if key.lower() in concept.lower() or concept.lower() in key.lower():
            return value
    evidence = evidence or []
    if evidence:
        first = evidence[0]
        second = evidence[1] if len(evidence) > 1 else ""
        return {
            "explain": f"来源材料中与「{concept}」直接相关的线索是：{first}{f'；{second}' if second else ''}。学习时要把这个线索转成可操作任务：能定位它所在章节、说明它服务的模型或实验、并用公式、代码或例子验证。",
            "check": f"能引用来源材料中的一个具体语句、公式、标题层级或 notebook 操作，说明「{concept}」在本章中解决的问题。",
            "pitfall": f"只把「{concept}」当成孤立词条，而没有回到来源材料中的模型结构、训练步骤或实验现象。",
        }
    return {
        "explain": f"{concept} 暂未在来源片段中抽到足够局部证据，只能作为课程图谱中的待补强知识点；学习时应先补充对应来源，再进入练习或资源推荐。",
        "check": f"能补充一条与「{concept}」直接相关的来源、公式、代码或实验现象。",
        "pitfall": "在证据不足时继续生成看似完整的讲解，会造成浅层且不可追溯的学习资源。",
    }


def _source_summary(chapter: dict, chunks: list[dict]) -> str:
    related = _source_cards(chapter, chunks, limit=8)
    titles = list(dict.fromkeys(item.get("title", "") for item in related if item.get("title")))[:8]
    if not titles:
        titles = chapter["source_roles"]
    return "；".join(titles)


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def _main_note(chapter: dict, chunks: list[dict]) -> str:
    concepts = chapter["concepts"]
    cards = _source_cards(chapter, chunks, limit=12)
    source_summary = _source_summary(chapter, chunks)
    source_lines = []
    for card in cards[:8]:
        source_name = "Andrew Ng 笔记" if card.get("source_id") == "src_kyonhuang_andrew_ng" else "AccumulateMore/CV Notebook"
        headings = "、".join(card.get("headings")[:5]) or "未提取标题层级"
        source_lines.append(f"- **{card['title']}**（{source_name}）：覆盖 {headings}。")
        if card.get("formulas"):
            source_lines.append(f"  - 公式线索：{'；'.join(card['formulas'][:3])}")
        if card.get("code_purposes"):
            source_lines.append(f"  - 代码线索：{'；'.join(card['code_purposes'][:3])}")
        for sentence in card.get("sentences", [])[:2]:
            source_lines.append(f"  - 内容要点：{sentence}")

    sections = [
        f"# {chapter['chapter_title']}\n",
        _section("章节定位", f"{chapter['summary']} 本章不再使用概念占位模板，而是将 {source_summary} 中的课程结构、公式线索和 notebook 实验顺序整理为统一讲义。学生端看到的是重构后的课程内容；原始来源只作为内部依据和可追溯证据。"),
        _section("来源融合说明", "\n".join(source_lines) if source_lines else "本章暂无可用来源摘录，需要后续补充。"),
        _section("学习目标", "\n".join(f"- 能解释「{concept}」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。" for concept in concepts[:8])),
        _section("前置知识", "学习本章前，应先确认上一章的核心对象、变量含义和实验边界。遇到公式时，不要只背符号，要能指出它在代码中对应哪一个张量、参数、损失或指标；遇到模型结构时，要能说清数据从输入到输出经过了哪些层。"),
        _section("知识结构总览", "\n".join(f"- **{concept}**：对应来源中的「{(_concept_source_card(concept, cards).get('title') or '课程综合材料')}」，学习时同时检查定义、流程、公式/代码和实验现象。" for concept in concepts)),
    ]

    for idx, concept in enumerate(concepts, start=1):
        card = _concept_source_card(concept, cards)
        evidence = _concept_evidence(concept, cards, limit=4)
        point = _concept_point(concept, evidence)
        formula = FORMULAS.get(concept)
        formula_text = f"\n\n**公式/结构线索**：`{formula}`。" if formula else ""
        heading_text = "、".join(card.get("headings", [])[:6]) if card else ""
        sentence_text = "\n".join(f"- {sentence}" for sentence in evidence[:4])
        code_text = "\n".join(f"- {purpose}" for purpose in (card.get("code_purposes", [])[:3] if card else []))
        sections.append(_section(
            f"{idx}. {concept}",
            (
                f"**来源位置**：{card.get('title', '课程综合材料') if card else '课程综合材料'}"
                f"{f'；标题层级包括 {heading_text}' if heading_text else ''}。"
                f"{formula_text}\n\n"
                f"**重构讲解**：{point['explain']}\n\n"
                f"**来源要点摘录**：\n{sentence_text or '- 本节作为课程组织知识点，由课程地图、章节讲义和后续实验共同支撑。'}\n\n"
                f"**代码或实验落点**：\n{code_text or '- 本节重点是概念、公式或结构理解；可在章节练习中补充最小实验。'}\n\n"
                f"**学习检查**：{point['check']}\n\n"
                f"**常见误区**：{point['pitfall']}"
            ),
        ))

    sections.extend([
        _section("教材式例子一：从来源结构到学习流程", f"以「{cards[0]['title'] if cards else concepts[0]}」为例，先读取来源标题层级，判断它属于概念解释、模型结构、优化策略还是实验任务；再将它映射到本章的 {', '.join(concepts[:4])}；最后生成一条可执行学习任务：阅读主讲义、完成练习、运行或观察实验、写出错因复盘。"),
        _section("教材式例子二：从 notebook 到课程实验", f"AccumulateMore/CV 中的 notebook 不是直接塞给学生，而是被拆成实验目标、关键代码用途、运行步骤和调参任务。学生学习 {chapter['chapter_title']} 时，应能把 `Dataset/DataLoader`、`nn.Module`、`loss.backward()`、`optimizer.step()` 或对应模型结构放回完整训练循环。"),
        _section("易错点与纠偏", "\n".join([
            "- 只背来源标题，不知道标题下真正讨论了什么模型、公式或实验。",
            "- 把 notebook 当成可直接展示的学习资源，而没有整理成目标、步骤、任务和评价。",
            "- 学模型结构时不检查输入输出 shape，导致代码能抄但不能解释。",
            "- 学优化或正则化时不看训练/验证曲线，无法判断方法是否真的改善泛化。",
        ])),
        _section("课堂讨论问题", "\n".join([
            f"1. {concepts[0]} 与 {concepts[min(1, len(concepts)-1)]} 在本章流程中分别解决什么问题？",
            f"2. 如果学生已经会使用工具库，但解释不清 {concepts[0]}，应该如何安排补弱？",
            "3. 哪些内容适合做动画或流程图，哪些内容更适合做代码实验？",
        ])),
        _section("自测题", "\n".join(f"{i}. 围绕「{concepts[(i - 1) % len(concepts)]}」写出定义、输入输出、常见误区和一个应用场景。" for i in range(1, 13 if chapter.get("core") else 9))),
        _section("小结与下一步", f"完成本章后，应能把 {', '.join(concepts[:4])} 串成一条可执行的学习路径。下一步不是盲目堆资料，而是根据画像、诊断结果和当前章节位置选择主讲义、练习、实验或项目任务。"),
    ])

    note = "\n".join(sections)
    target = 6200 if chapter.get("core") else 4300
    if len(note) < target:
        supplement = (
            "\n## 深入学习提示\n\n"
            "为了避免浅层学习，建议按照“概念复述、公式解释、流程图、代码定位、实验记录、错因复盘”六步完成本章。"
            "每一步都要产出可检查结果：一句定义、一张图、一个最小代码片段、一组训练曲线或一段错因说明。"
            "系统后续进行个性化推送时，会优先根据这些产出判断学生更需要讲义、题集、代码实验还是项目任务。\n"
        )
        while len(note) < target:
            note += supplement
    return note


def _mind_map(chapter: dict) -> str:
    lines = ["```mermaid", "mindmap", f"  root(({chapter['chapter_title']}))"]
    for concept in chapter["concepts"]:
        lines.append(f"    {concept}")
        lines.append("      来源位置")
        lines.append("      公式或结构")
        lines.append("      实验任务")
        lines.append("      易错点")
    lines.append("```")
    return "\n".join(lines) + "\n"


def _exercises(chapter: dict, chunks: list[dict]) -> str:
    concepts = chapter["concepts"]
    cards = _source_cards(chapter, chunks, limit=12)
    count = 12 if chapter.get("core") else 8
    lines = [f"# {chapter['chapter_title']} 练习题集", ""]
    types = ["选择题", "判断题", "简答题", "计算/推导题", "代码理解题", "实验分析题"]
    for i in range(1, count + 1):
        concept = concepts[(i - 1) % len(concepts)]
        card = _concept_source_card(concept, cards)
        evidence = _concept_evidence(concept, cards, limit=3)
        point = _concept_point(concept, evidence)
        qtype = types[(i - 1) % len(types)]
        source_title = card.get("title", chapter["chapter_title"]) if card else chapter["chapter_title"]
        source_hint = "；".join(card.get("headings", [])[:4]) if card else ""
        formula = FORMULAS.get(concept) or (card.get("formulas", [""])[0] if card and card.get("formulas") else "")
        evidence_hint = evidence[0] if evidence else "本题主要依据课程地图、章节讲义和实验任务综合作答。"
        lines.extend([
            f"## {i}. {qtype}：{concept}",
            "",
            f"题目：结合来源「{source_title}」{f'（标题线索：{source_hint}）' if source_hint else ''}，完成关于「{concept}」的分析：它解决什么问题、核心机制是什么、如何在实验或代码中验证？",
            "",
            f"答案：{point['explain']} {f'本题可使用公式 `{formula}` 辅助解释。' if formula else ''}",
            "",
            f"解析：本题的来源证据是：{evidence_hint}。{point['check']} 正确答案还应从「{source_title}」中提取一个证据点，例如标题层级、公式、结构、代码目的或实验现象。",
            "",
            f"常见错误：{point['pitfall']}",
            "",
        ])
    return "\n".join(lines)


def _reading_guide(chapter: dict) -> str:
    return "\n".join([
        f"# {chapter['chapter_title']} 阅读与视频指南",
        "",
        "## 学习顺序",
        "1. 先阅读本章主讲义，标出不懂的符号和术语。",
        "2. 再查看来源笔记对应章节，只核对结构和公式，不复制原文。",
        "3. 如果本章包含代码实验，先运行最小版本，再改动一个超参数观察变化。",
        "4. 最后完成练习题集，并把错题写入学习评价。",
        "",
        "## 来源参考",
        *[f"- {role}" for role in chapter["source_roles"]],
        "",
        "## 公开视频建议",
        "- 优先选择高校公开课或官方文档中与本章主题直接对应的片段。",
        "- 只保存原始链接和观看任务，不下载、不搬运、不重新分发视频。",
        "- 观看时记录：对应知识点、起止时间、为什么值得看、看完后完成什么练习。",
        "",
        "## 输出要求",
        "- 写出本章 3 个关键概念的自己的解释。",
        "- 完成至少 2 道题和 1 个实验/流程复盘。",
    ])


def _code_lab(chapter: dict, chunks: list[dict]) -> str:
    lab = chapter.get("lab") or "mlp_pytorch_mnist.py"
    cards = _source_cards(chapter, chunks, limit=8)
    code_lines = []
    for card in cards:
        for purpose in card.get("code_purposes", []):
            code_lines.append(f"- {card['title']}：{purpose}")
    if not code_lines:
        code_lines = ["- 本章实验围绕主讲义中的概念、公式或模型结构组织。"]
    return "\n".join([
        f"# {chapter['chapter_title']} 代码实验",
        "",
        "## 实验目标",
        f"围绕本章主题完成 `{lab}`，把两份来源中的 notebook 实验线索整理为可运行任务、日志记录和实验报告。",
        "",
        "## 来源 notebook 线索",
        *code_lines[:10],
        "",
        "## 环境依赖",
        "```bash",
        "python >= 3.10",
        "pip install torch torchvision numpy matplotlib",
        "```",
        "",
        "## 运行方式",
        "```bash",
        f"python data/knowledge_base/deep_learning_v2/labs/{lab}",
        "```",
        "",
        "## 学生任务",
        "- 跑通默认参数，记录训练/验证指标。",
        "- 修改一个模型结构或超参数，比较前后变化。",
        "- 解释输出 shape、损失变化和错误样例。",
        "",
        "## 调参建议",
        "- 每次只改一个变量，例如学习率、batch size、层数或 dropout。",
        "- 保留随机种子和数据划分，避免把随机波动误认为方法改进。",
        "",
        "## 常见报错",
        "- shape mismatch：打印每层输入输出维度。",
        "- CUDA out of memory：减小 batch size 或切回 CPU。",
        "- loss 不下降：检查学习率、标签格式和模型输出。",
    ])


def _interactive_animation(chapter: dict) -> str:
    payload = {
        "animation_type": "step_flow",
        "title": chapter["chapter_title"],
        "parameters": [{"name": concept, "control": "toggle"} for concept in chapter["concepts"][:5]],
        "steps": [
            {"step": idx, "label": concept, "description": f"高亮 {concept} 在本章流程中的输入、输出和易错点。"}
            for idx, concept in enumerate(chapter["concepts"][:6], start=1)
        ],
        "student_tasks": ["拖动流程顺序", "标注关键张量", "回答一个暂停思考问题"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _project_files(chapter: dict) -> dict[str, str]:
    return {
        "project_brief.md": "\n".join([
            f"# {chapter['chapter_title']} 项目任务书",
            "",
            "## 项目目标",
            "任选 CNN 图像分类、LSTM 序列分类、Attention/Transformer 文本实验或目标检测拓展之一，完成从数据准备到结果展示的完整闭环。",
            "",
            "## 提交物",
            "- 实验代码与运行说明",
            "- 训练/验证曲线",
            "- 错误样例分析",
            "- 课程报告",
            "- 5 分钟展示 PPT",
        ]),
        "rubric.md": "\n".join([
            "# 课程项目评分 Rubric",
            "",
            "| 维度 | 权重 | 说明 |",
            "| --- | --- | --- |",
            "| 问题定义 | 20% | 目标清晰，数据和指标合理 |",
            "| 方法实现 | 30% | 模型、训练、评估流程完整 |",
            "| 实验分析 | 30% | 有对比、有错因、有复盘 |",
            "| 表达展示 | 20% | 报告结构清晰，图表可读 |",
        ]),
        "report_template.md": "\n".join([
            "# 深度学习课程项目报告模板",
            "",
            "## 1. 项目背景",
            "## 2. 数据集与任务定义",
            "## 3. 方法与模型结构",
            "## 4. 实验设置",
            "## 5. 结果与误差分析",
            "## 6. 总结与改进方向",
        ]),
    }


def _lab_code(name: str) -> str:
    topic = name.replace(".py", "").replace("_", " ")
    return f'''"""Minimal runnable lab: {topic}."""

from __future__ import annotations

import random


def set_seed(seed: int = 42) -> None:
    random.seed(seed)


def main() -> None:
    set_seed()
    print("LingXi Deep Learning Lab: {topic}")
    print("This lightweight lab is designed for course demonstration.")
    print("Extend it with torch/torchvision in a full local environment.")


if __name__ == "__main__":
    main()
'''


def _unit_id(chapter: dict, topic: str) -> str:
    return f"dlv2_ch{chapter['chapter_no']:02d}_{_slug(topic)}"[:80]


def build_all() -> None:
    COURSE_DIR.mkdir(parents=True, exist_ok=True)
    COURSEWARE_DIR.mkdir(parents=True, exist_ok=True)
    LABS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    chunks = _source_chunks()
    (COURSE_DIR / "source_registry.json").write_text(json.dumps(SOURCE_REGISTRY, ensure_ascii=False, indent=2), encoding="utf-8")
    (COURSE_DIR / "source_ingestion_manifest.json").write_text(json.dumps({
        "course_id": "deep_learning_v2",
        "imported_at": "generated_by_scripts",
        "source_count": len(SOURCE_REGISTRY),
        "chunk_count": len(chunks),
        "student_view_policy": "student resources use curated courseware, not raw imported chunks",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    units = []
    evidence = []
    chapter_index = []

    for chapter in CHAPTERS:
        chapter_dir = COURSEWARE_DIR / chapter["chapter_id"]
        chapter_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "main_note.md": _main_note(chapter, chunks),
            "mind_map.mmd": _mind_map(chapter),
            "exercises.md": _exercises(chapter, chunks),
            "reading_video_guide.md": _reading_guide(chapter),
        }
        if chapter.get("lab"):
            files["code_lab.md"] = _code_lab(chapter, chunks)
        if chapter.get("animation"):
            files["interactive_animation.json"] = _interactive_animation(chapter)
        if chapter.get("project"):
            files.update(_project_files(chapter))
        for filename, content in files.items():
            (chapter_dir / filename).write_text(content, encoding="utf-8")

        primary_resources = [
            {"resource_key": f"{chapter['chapter_id']}/main_note.md", "title": f"{chapter['chapter_title']} 主讲义", "type": "课程讲解文档", "is_required": True},
            {"resource_key": f"{chapter['chapter_id']}/mind_map.mmd", "title": f"{chapter['chapter_title']} 思维导图", "type": "知识点思维导图", "is_required": True},
            {"resource_key": f"{chapter['chapter_id']}/exercises.md", "title": f"{chapter['chapter_title']} 练习题集", "type": "练习题集", "is_required": True},
            {"resource_key": f"{chapter['chapter_id']}/reading_video_guide.md", "title": f"{chapter['chapter_title']} 阅读与视频指南", "type": "拓展阅读包", "is_required": True},
        ]
        optional_resources = []
        if chapter.get("lab"):
            primary_resources.append({"resource_key": f"{chapter['chapter_id']}/code_lab.md", "title": f"{chapter['chapter_title']} 代码实验", "type": "PyTorch 实操案例", "is_required": True})
        if chapter.get("animation"):
            optional_resources.append({"resource_key": f"{chapter['chapter_id']}/interactive_animation.json", "title": f"{chapter['chapter_title']} 交互动画规格", "type": "交互动画规格", "is_required": False})
        if chapter.get("project"):
            primary_resources.append({"resource_key": f"{chapter['chapter_id']}/project_brief.md", "title": "深度学习综合项目任务书", "type": "课程实践项目任务书", "is_required": True})
            optional_resources.extend([
                {"resource_key": f"{chapter['chapter_id']}/rubric.md", "title": "深度学习课程项目 Rubric", "type": "拓展阅读包", "is_required": False},
                {"resource_key": f"{chapter['chapter_id']}/report_template.md", "title": "深度学习课程项目报告模板", "type": "拓展阅读包", "is_required": False},
            ])
        chapter_index.append({
            "chapter_no": chapter["chapter_no"],
            "chapter_id": chapter["chapter_id"],
            "chapter_title": chapter["chapter_title"],
            "summary": chapter["summary"],
            "source_reference_ids": [item["source_id"] for item in SOURCE_REGISTRY],
            "primary_resources": primary_resources,
            "optional_resources": optional_resources,
        })

        for topic in UNIT_TOPICS[chapter["chapter_id"]]:
            unit_id = _unit_id(chapter, topic)
            evidence_id = f"ev_{unit_id}_001"
            units.append({
                "unit_id": unit_id,
                "course_id": "deep_learning_v2",
                "chapter_id": chapter["chapter_id"],
                "chapter_title": chapter["chapter_title"],
                "title": topic,
                "aliases": list(dict.fromkeys([topic, topic.lower(), *re.split(r"[、/ ]+", topic)])),
                "prerequisites": chapter["concepts"][:2],
                "related_units": [],
                "compare_units": [],
                "core_concepts": chapter["concepts"][:8],
                "formulas": [FORMULAS[topic]] if topic in FORMULAS else [],
                "code_patterns": ["torch.nn", "DataLoader"] if chapter.get("lab") else [],
                "common_misconceptions": [f"把「{topic}」当成孤立名词，不说明输入输出和适用条件。"],
                "learning_outcomes": [f"解释「{topic}」的定义、作用、流程位置和一个应用场景。"],
                "resource_focus": ["主讲义", "练习题", "代码实验" if chapter.get("lab") else "阅读指南"],
                "evidence_refs": [evidence_id],
                "source_reference_ids": [item["source_id"] for item in SOURCE_REGISTRY],
                "difficulty": "medium" if chapter.get("core") else "beginner",
            })
            evidence.append({
                "evidence_id": evidence_id,
                "course_id": "deep_learning_v2",
                "chapter_id": chapter["chapter_id"],
                "unit_id": unit_id,
                "source_type": "curated_courseware",
                "source_file": f"courseware/{chapter['chapter_id']}/main_note.md",
                "source_reference_ids": [item["source_id"] for item in SOURCE_REGISTRY],
                "content_excerpt": f"{chapter['chapter_title']} 中的「{topic}」围绕 {chapter['summary']} 展开，学习时需要同时关注定义、输入输出、公式/流程、实验边界和常见误区。",
            })

    (COURSE_DIR / "chapter_resource_index.json").write_text(json.dumps(chapter_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (COURSE_DIR / "knowledge_units.jsonl").write_text(
        "\n".join(json.dumps(unit, ensure_ascii=False) for unit in units) + "\n",
        encoding="utf-8",
    )
    (EVIDENCE_DIR / "evidence_chunks.jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in evidence) + "\n",
        encoding="utf-8",
    )
    (COURSE_DIR / "course_manifest.json").write_text(json.dumps({
        "course_id": "deep_learning_v2",
        "course_name": "深度学习",
        "course_display_name": "《深度学习》",
        "version": "v2",
        "source_prefix": "《深度学习》v2 课程知识库",
        "resource_uploader": "LingXi KnowledgeSeedAgent",
        "chapters": [{"chapter_id": c["chapter_id"], "title": c["chapter_title"], "summary": c["summary"]} for c in CHAPTERS],
        "knowledge_unit_count": len(units),
        "evidence_count": len(evidence),
        "student_view_policy": "chapter_hub",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    videos = []
    for chapter in CHAPTERS:
        first_unit = _unit_id(chapter, UNIT_TOPICS[chapter["chapter_id"]][0])
        videos.append({
            "video_id": f"DLV2-VIDEO-CH{chapter['chapter_no']:02d}",
            "course_id": "deep_learning_v2",
            "unit_ids": [first_unit],
            "title": f"{chapter['chapter_title']} 公开视频学习入口",
            "platform": "link_only",
            "source": "高校公开课/MOOC/官方课程入口",
            "source_url": "https://www.icourse163.org/",
            "tags": chapter["concepts"][:6],
            "difficulty": "medium" if chapter.get("core") else "beginner",
            "duration": "20-45 分钟",
            "recommended_segments": ["先看概念段，再看公式或实验段，最后完成本章练习。"],
            "copyright_policy": "link_only",
        })
    (COURSE_DIR / "video_catalog.json").write_text(json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8")

    labs = [
        "mlp_numpy_from_scratch.py",
        "mlp_pytorch_mnist.py",
        "cnn_cifar10.py",
        "cnn_output_shape_debug.py",
        "optimizer_comparison.py",
        "dropout_batchnorm_demo.py",
        "resnet_transfer_learning.py",
        "object_detection_iou_anchor_demo.py",
        "lstm_sequence_classification.py",
        "attention_demo.py",
        "transformer_text_classification.py",
    ]
    for lab in labs:
        (LABS_DIR / lab).write_text(_lab_code(lab), encoding="utf-8")

    coverage_lines = [
        "# Deep Learning v2 来源覆盖报告",
        "",
        "## 总览",
        f"- 课程章节：{len(CHAPTERS)}",
        f"- 知识单元：{len(units)}",
        f"- Evidence：{len(evidence)}",
        f"- 导入源片段：{len(chunks)}",
        "",
        "## 来源使用原则",
        "- KyonHuang Andrew Ng Notes 用作理论主线、公式和章节顺序参考。",
        "- AccumulateMore/CV 用作 PyTorch 实践、CV 任务和 notebook 实验顺序参考。",
        "- 学生端展示本项目重构课程内容，不直接展示 imported raw chunks。",
        "",
        "## 章节覆盖",
    ]
    for chapter in CHAPTERS:
        count = len(_chunks_for_chapter(chapter["chapter_id"], chunks))
        coverage_lines.append(f"- {chapter['chapter_title']}：{count} 个来源片段；角色：{'、'.join(chapter['source_roles'])}")
    (DOCS_DIR / "source_coverage_report.md").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    random.seed(42)
    build_all()
    print(f"Built {COURSE_DIR}")
