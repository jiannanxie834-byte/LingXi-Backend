# 第 11 章 PyTorch 深度学习工程实践

## 一、学习定位与适用对象
PyTorch 工程实践是把深度学习概念转化为可运行实验的关键章节。本章适合已经理解神经网络、损失函数、优化器和 CNN/Transformer 基础，但在写训练脚本时容易复制代码、不检查 tensor shape、不记录实验参数的学生。学习目标是能独立组织 Dataset、DataLoader、nn.Module、训练循环、验证循环和实验报告。

## 二、本章在课程中的位置
前面章节解释模型为什么有效，本章关注如何让模型在真实代码中稳定训练。PyTorch 实验把课程中的张量、前向传播、反向传播、优化器和评价指标串成闭环。课程综合项目、图像分类实验、文本分类实验和调参复盘都依赖本章。

## 三、核心组件
Tensor 是 PyTorch 的基本数据结构，承载数值和 shape。Dataset 负责定义单个样本如何读取，DataLoader 负责按 batch 打包、打乱和并行加载。nn.Module 用于封装模型结构，forward 方法定义前向传播。损失函数 criterion 把预测和标签转成 loss。优化器 optimizer 根据梯度更新参数。训练循环负责重复执行前向、损失、反向和更新，验证循环负责在不更新参数的情况下评估模型。

## 四、标准训练流程
一次训练迭代通常包括：取出 batch，送入模型得到预测，计算 loss，清空旧梯度，执行 `loss.backward()`，执行 `optimizer.step()`。验证阶段要使用 `model.eval()` 和 `torch.no_grad()`，避免 Dropout、BatchNorm 和梯度记录影响评估结果。训练结束后应保存模型权重、超参数、随机种子、数据划分和指标曲线。

## 五、代码骨架
```python
import torch
import torch.nn as nn

model = MyModel()
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

for epoch in range(num_epochs):
    model.train()
    for x, y in train_loader:
        pred = model(x)
        loss = criterion(pred, y)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for x, y in val_loader:
            pred = model(x)
            correct += (pred.argmax(dim=1) == y).sum().item()
            total += y.numel()
    print(epoch, correct / total)
```
这段代码体现了训练和验证的分工。训练阶段更新参数，验证阶段只评估效果。

## 六、具体例子
例子 1：图像分类输入通常是 `(batch, channel, height, width)`。若模型第一层是 `Conv2d(3, 16, 3, padding=1)`，输入必须是 3 通道图片，输出通道会变为 16。

例子 2：文本分类输入可能是 token id 序列，需要先经过 embedding 层再进入 RNN、Transformer 或池化分类头。不同任务的数据 shape 不同，因此每次实验都要打印 batch shape。

## 七、实验记录与报告
一份合格实验报告应包含任务背景、数据集来源、训练/验证/测试划分、模型结构、关键超参数、训练曲线、最终指标、错误样本分析和复现实验步骤。只给准确率是不够的，因为管理员和教师需要判断模型是否真的学到了规律，还是过拟合或数据泄露。

## 八、常见误区与纠正
误区一：复制代码不检查 shape。纠正：每个阶段打印输入输出 shape，尤其是卷积层和全连接层连接处。
误区二：训练集和验证集混用。纠正：明确 DataLoader 的数据来源，验证集不参与参数更新。
误区三：忘记 `model.train()` 和 `model.eval()`。纠正：训练和评估模式会影响 Dropout、BatchNorm 等层。
误区四：没有固定随机种子。纠正：记录 seed，保证结果可复现。

## 九、自测题
1. `optimizer.zero_grad()` 为什么通常放在 `loss.backward()` 前？参考答案：避免上一轮梯度累加影响本轮更新。
2. 验证阶段为什么使用 `torch.no_grad()`？参考答案：节省显存和计算，不记录梯度，也不更新参数。
3. 实验报告除了准确率还应包含什么？参考答案：数据划分、超参数、训练曲线、错误分析和复现步骤。

## 十、下一步学习建议
掌握本章后，应完成一个小型 CNN 图像分类实验或 Transformer 文本分类实验。建议先跑通最小版本，再逐步加入数据增强、正则化、学习率调整和错误样本分析，形成课程综合项目的雏形。
