# 第 7 章 CNN 图像分类与卷积输出尺寸实验

## 1. 实验目标
围绕「卷积核、步幅填充、池化、经典网络和图像分类」完成一个可运行实验，要求学生能解释输入 shape、模型输出、损失变化、关键超参数和实验结论之间的关系。

## 2. 环境依赖
- Python 3.10+
- torch
- 可选：matplotlib，用于把 loss 或 accuracy 记录成折线图

安装命令：
```bash
pip install torch
```

## 3. 数据集说明
本实验默认使用合成张量数据或随机样本，保证离线演示时不依赖外部下载。正式课程项目中可以把数据替换为 MNIST、CIFAR-10、IMDB 或课程自建数据集，但必须保持训练/验证拆分和指标记录。

## 4. 完整代码
将下面代码保存为 `chapter_07_cnn_image_classification.py`。

```python
"""
CNN 输出尺寸调试实验
实验目标：用公式和 PyTorch 输出同时验证卷积/池化后的特征图尺寸。
依赖说明：pip install torch
学生任务：修改 kernel_size、stride、padding，先手算再运行代码验证。
调参建议：固定输入 32x32，分别尝试 padding=0/1、stride=1/2。
常见报错：忘记 floor；混淆通道数 C 和空间尺寸 H/W。
"""
import math
import torch
import torch.nn as nn


def conv_out(size, kernel_size, stride=1, padding=0, dilation=1):
    return math.floor((size + 2 * padding - dilation * (kernel_size - 1) - 1) / stride + 1)


def main():
    x = torch.randn(4, 3, 32, 32)
    conv = nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1)
    y = conv(x)
    expected_h = conv_out(32, kernel_size=3, stride=2, padding=1)
    print("input shape :", tuple(x.shape))
    print("output shape:", tuple(y.shape))
    print("formula H/W :", expected_h)
    assert y.shape == (4, 16, expected_h, expected_h)

    pool = nn.MaxPool2d(kernel_size=2, stride=2)
    z = pool(y)
    print("after pool  :", tuple(z.shape))


if __name__ == "__main__":
    main()
```

## 5. 运行命令
```bash
python chapter_07_cnn_image_classification.py
```
如果在 notebook 中运行，请先确认当前内核已安装 torch，并逐单元执行完整代码。

## 6. 关键代码解释
- 数据构造部分负责控制输入维度、标签规则和 batch 组织方式。
- 模型结构部分体现本章主题：卷积核、步幅填充、池化、经典网络和图像分类。
- `loss.backward()` 负责把损失对参数的影响传回模型。
- `optimizer.step()` 根据梯度更新参数。
- 训练日志中的 loss、accuracy、shape 或参数量是判断实验是否正常的主要证据。

## 7. 学生任务
1. 打印第一批数据的输入 shape、标签 shape 和模型输出 shape。
2. 修改一个关键超参数，并记录至少 3 个 epoch 的变化。
3. 写出一次错误现象，例如 loss 不降、shape 不匹配或验证指标波动。
4. 用 150 字解释该实验如何帮助理解「卷积核、步幅填充、池化、经典网络和图像分类」。

## 8. 调参建议
- 每次只修改一个变量，避免无法判断原因。
- 学习率优先尝试 `1e-2`、`1e-3`、`3e-4`。
- 如果训练不稳定，先检查输入/标签 shape，再检查损失函数和优化器。
- 如果训练集指标高而验证集指标低，优先考虑正则化、数据划分和模型容量。

## 9. 常见报错
- `Expected input batch_size`：模型输出和标签 batch 维度不一致。
- `mat1 and mat2 shapes cannot be multiplied`：线性层输入维度与张量 shape 不匹配。
- loss 长时间不变：学习率不合适、标签构造错误或模型表达能力不足。
- 验证指标异常：忘记 `model.eval()`，或把训练集和验证集混用。

## 10. 实验报告要求
报告需要包含实验目标、代码截图或关键片段、运行命令、至少一张日志表、错误分析、改进方案和本章概念复盘。不得只提交运行截图。
