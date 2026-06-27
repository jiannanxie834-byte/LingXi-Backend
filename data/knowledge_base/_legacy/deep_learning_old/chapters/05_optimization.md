# 第 5 章 优化算法与训练技巧

## 1. 学习定位
优化算法回答的是“模型已经能计算梯度之后，参数到底怎样更新”。在《深度学习》课程中，它连接反向传播和实际训练效果，是学生从“会推导”走向“能训练模型”的关键章节。

## 2. 本章在课程中的位置
前一章讨论前向传播、损失函数和反向传播，本章使用这些梯度更新参数；后一章讨论正则化与泛化，需要依赖本章对训练曲线和验证曲线的理解。

## 3. 学习目标
- 解释梯度下降、SGD、Momentum、Adam 的更新思想。
- 说明学习率为什么会影响收敛速度和稳定性。
- 能根据 loss/accuracy 曲线判断学习率过大、过小、过拟合或欠拟合。
- 能在 PyTorch 中替换优化器并记录对比实验。

## 4. 前置知识
需要掌握梯度、链式法则、反向传播、损失函数、训练集/验证集划分，以及基本 PyTorch 训练循环。

## 5. 核心概念详细解释
### 梯度下降
梯度指向损失上升最快的方向，因此参数更新通常沿负梯度方向移动：

```text
theta_{t+1} = theta_t - eta * grad(theta_t)
```

其中 `theta` 是参数，`eta` 是学习率，`grad` 是损失对参数的梯度。学习率过小会收敛很慢，过大可能在最优点附近震荡甚至发散。

### SGD
随机梯度下降使用 mini-batch 估计整体梯度。它引入噪声，但计算更快，且噪声有时能帮助模型跳出尖锐局部区域。SGD 的缺点是对学习率较敏感，训练曲线可能抖动。

### Momentum
Momentum 维护一个速度项，把历史梯度方向累积起来：

```text
v_t = beta * v_{t-1} + grad_t
theta_t = theta_{t-1} - eta * v_t
```

当梯度方向稳定时，动量能加速；当某个方向来回震荡时，动量能抵消部分抖动。

### Adam
Adam 同时估计梯度的一阶矩和二阶矩，为不同参数提供自适应步长。它通常上手快、初期收敛稳定，但并不意味着泛化一定优于 SGD。课堂实验中应比较训练曲线和验证曲线，而不是只看前几轮 loss。

### 学习率调度
固定学习率不一定适合整个训练过程。常见策略包括 StepLR、CosineAnnealing、ReduceLROnPlateau 和 warmup。调度器的目标是早期快速探索，后期小步收敛。

## 6. 公式、流程与算法机制
一次训练迭代的流程是：取 batch、前向计算、计算 loss、清空旧梯度、反向传播、优化器更新、记录指标。注意 `optimizer.zero_grad()` 必须在每轮反传前执行，否则梯度会累积。

## 7. 例子一：学习率过大
如果训练 loss 大幅震荡，甚至一会儿变小一会儿变大，常见原因是学习率过大。此时不应马上怀疑模型结构，而应先把学习率降低一个数量级，例如从 `1e-2` 改为 `1e-3`。

## 8. 例子二：Adam 与 SGD 的取舍
在小数据集上，Adam 可能前几轮下降更快；在一些视觉任务中，调好学习率和动量的 SGD 可能验证集表现更稳。因此报告中应写清优化器、学习率、调度器、batch size 和随机种子。

## 9. PyTorch 代码示例
```python
import torch
import torch.nn as nn

model = nn.Sequential(nn.Linear(10, 32), nn.ReLU(), nn.Linear(32, 2))
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

x = torch.randn(16, 10)
y = torch.randint(0, 2, (16,))
optimizer.zero_grad()
logits = model(x)
loss = criterion(logits, y)
loss.backward()
optimizer.step()
print(float(loss))
```

## 10. 常见误区
- 认为 Adam 一定比 SGD 好。
- 只看训练 loss，不看验证集指标。
- 学习率过大时误以为模型不适合任务。
- 忘记清空梯度导致更新异常。
- 只报告最终准确率，不记录训练曲线。

## 11. 自测题与答案
1. 为什么学习率过大会导致 loss 震荡？
   答：参数更新步长过大，可能跨过低损失区域，在损失面两侧来回跳动。
2. Momentum 为什么能减轻震荡？
   答：它累积历史梯度方向，在稳定方向加速，在来回变化方向相互抵消。
3. Adam 的自适应学习率是否总能带来最佳泛化？
   答：不能。Adam 常收敛快，但泛化还取决于数据、模型、正则化和训练设置。

## 12. 下一步学习建议
完成 `optimizer_comparison.py`，对比 SGD、Momentum、Adam 的 loss 曲线，再进入正则化章节分析训练集与验证集的差距。
