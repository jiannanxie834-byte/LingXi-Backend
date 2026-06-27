# 第 11 章 PyTorch 深度学习工程实践

## 1. 学习定位
PyTorch 实践是把理论落到可运行实验的桥梁。学生需要能组织数据、定义模型、写训练循环、调试 shape、评估模型和记录实验，而不是只复制代码。

## 2. 本章在课程中的位置
本章贯穿 CNN、RNN/LSTM、Transformer 和课程项目。前面章节提供模型原理，本章提供工程实现方法。

## 3. 学习目标
- 熟悉 Tensor、Dataset、DataLoader、nn.Module、训练循环。
- 能定位 shape mismatch、device mismatch、梯度未更新等常见错误。
- 能输出训练/验证指标并保存实验记录。
- 能把 CNN、LSTM 或 Transformer 小模型改造成课程项目 baseline。

## 4. Tensor 与 shape
张量 shape 是调试入口。CNN 常用 `[N, C, H, W]`，RNN/LSTM 在 `batch_first=True` 时常用 `[N, T, F]`，Transformer 通常需要关注 `[batch, seq_len, hidden]` 以及 mask shape。

## 5. Dataset 与 DataLoader
Dataset 负责定义单个样本如何读取，DataLoader 负责批量、shuffle、多进程加载。自定义 Dataset 至少实现 `__len__` 和 `__getitem__`。

## 6. nn.Module 模型定义
模型类通常在 `__init__` 中声明层，在 `forward` 中描述数据流。不要在 `forward` 中临时创建需要训练的层，否则参数不会被优化器管理。

## 7. 训练循环流程
标准训练循环包括：设为 train 模式、取 batch、搬到 device、前向、loss、zero_grad、backward、step、记录指标。验证阶段应使用 `model.eval()` 和 `torch.no_grad()`。

## 8. Shape 调试流程
遇到 RuntimeError 时先打印每层输入输出 shape，再检查 batch 维、通道维、序列维是否被交换。CNN 输出尺寸可用公式计算，LSTM 输入要确认 `batch_first`。

## 9. 模型评估
分类任务至少报告 accuracy；类别不平衡时还应报告 precision、recall、F1 或混淆矩阵。项目报告中必须说明训练集、验证集、测试集划分。

## 10. 例子一：训练循环最小代码
```python
import torch
import torch.nn as nn

model = nn.Sequential(nn.Linear(5, 16), nn.ReLU(), nn.Linear(16, 2))
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
criterion = nn.CrossEntropyLoss()

for epoch in range(3):
    x = torch.randn(32, 5)
    y = torch.randint(0, 2, (32,))
    model.train()
    optimizer.zero_grad()
    logits = model(x)
    loss = criterion(logits, y)
    loss.backward()
    optimizer.step()
    print(epoch, float(loss))
```

## 11. 例子二：验证阶段
```python
model.eval()
with torch.no_grad():
    logits = model(torch.randn(16, 5))
    pred = logits.argmax(dim=1)
    print(pred.shape)
```

## 12. 常见误区
- 忘记 `optimizer.zero_grad()`。
- 在验证阶段仍然启用 Dropout。
- 把 `[N, C, H, W]` 写成 `[N, H, W, C]`。
- 只保存最终准确率，不保存超参数和随机种子。
- 在 `forward` 中创建新层。

## 13. 自测题与答案
1. 为什么验证时要使用 `torch.no_grad()`？
   答：减少显存和计算，不需要构建反向传播图。
2. `optimizer.step()` 前为什么要先 `loss.backward()`？
   答：优化器需要参数的梯度，梯度由反向传播计算。
3. CNN 输入 shape `[32, 3, 64, 64]` 中 3 表示什么？
   答：通道数，通常 RGB 图像为 3。

## 14. 下一步学习建议
完成 `cnn_output_shape_debug.py` 熟悉 shape 调试，再根据个人目标选择 CNN 图像分类、LSTM 序列分类或 Transformer 注意力实验。
