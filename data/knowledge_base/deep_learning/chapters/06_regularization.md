# 第 6 章 正则化与泛化

## 1. 学习定位
正则化与泛化回答“模型为什么训练集很好、验证集很差”。它不是单一技巧，而是一组控制模型复杂度、训练过程和数据分布的工程方法。

## 2. 本章在课程中的位置
本章依赖训练/验证/测试划分、损失函数和优化算法。后续 CNN、Transformer 和项目实践都会用到 Dropout、BatchNorm、数据增强和早停。

## 3. 学习目标
- 区分过拟合、欠拟合和正常收敛。
- 解释 L2 正则化、Dropout、BatchNorm、数据增强和早停的作用。
- 能从训练/验证曲线判断是否需要正则化。
- 能在 PyTorch 模型中加入 Dropout 和 BatchNorm。

## 4. 前置知识
训练集、验证集、测试集划分；损失函数；优化器；基本神经网络结构；PyTorch Module 写法。

## 5. 核心概念详细解释
### 过拟合
过拟合表现为训练集 loss 持续下降、训练准确率很高，但验证集 loss 上升或验证准确率停滞。它说明模型记住了训练样本中的偶然模式，而不是学到了可泛化规律。

### L2 正则化
L2 正则化在损失中加入权重平方和：

```text
L_total = L_data + lambda * ||W||_2^2
```

它鼓励权重不要过大，从而降低模型复杂度。PyTorch 中常通过优化器的 `weight_decay` 实现。

### Dropout
Dropout 在训练时随机屏蔽部分神经元，让模型不能过度依赖某些特征。推理时不再随机屏蔽。学生常见错误是忘记 `model.train()` 与 `model.eval()` 的差异。

### BatchNorm
BatchNorm 使用 mini-batch 统计量对中间激活进行标准化，再用可学习的 gamma、beta 调整。它能改善训练稳定性，但训练和推理时使用的统计量不同。

### 数据增强
数据增强通过随机裁剪、翻转、颜色扰动等保持标签不变的变换扩大数据多样性。它适合图像任务，但必须保证增强不会改变语义。

### 早停
早停监控验证集指标，当连续若干轮没有提升时停止训练，并保存最佳权重。它本质上用验证集表现控制训练时间。

## 6. 公式、流程与机制
正则化流程可以写成：先建立 baseline，观察训练/验证曲线，再选择策略。若训练和验证都差，优先增强模型或训练；若训练好验证差，再考虑 L2、Dropout、数据增强和早停。

## 7. 例子一：Dropout 使用场景
MLP 在小数据集上训练准确率 99%，验证准确率 70%，加入 Dropout 后训练准确率下降到 94%，验证准确率上升到 82%。这说明训练集表现下降不一定是坏事，关键看泛化。

## 8. 例子二：BatchNorm 的训练/推理差异
训练时 BatchNorm 使用当前 mini-batch 的均值和方差；推理时使用训练过程中累积的 running mean 和 running var。如果忘记 `model.eval()`，单张图片预测可能非常不稳定。

## 9. PyTorch 代码示例
```python
import torch
import torch.nn as nn

class RegularizedMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(20, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(p=0.3),
            nn.Linear(64, 2),
        )
    def forward(self, x):
        return self.net(x)

model = RegularizedMLP()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
print(model(torch.randn(8, 20)).shape)
```

## 10. 常见误区
- 把 BatchNorm 当作普通输入归一化。
- 训练和推理都开 Dropout。
- 不看验证集，只看训练准确率。
- 数据增强改变了标签语义却仍然使用原标签。
- 过拟合时只盲目加深网络。

## 11. 自测题与答案
1. Dropout 为什么只在训练时随机失活？
   答：训练时迫使模型学习冗余表示，推理时需要使用完整网络获得稳定输出。
2. `weight_decay` 对应哪种正则化思想？
   答：通常对应 L2 正则化，惩罚过大的权重。
3. 验证集 loss 上升但训练 loss 下降，优先考虑什么？
   答：过拟合，可尝试数据增强、L2、Dropout、早停或减少模型容量。

## 12. 下一步学习建议
完成 `regularization_dropout_bn_demo.py`，记录有无 Dropout/BatchNorm 时的训练曲线，再进入 CNN 章节分析图像任务中的数据增强。
