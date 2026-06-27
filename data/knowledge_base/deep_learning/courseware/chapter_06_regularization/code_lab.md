# 第 6 章 Dropout 与 BatchNorm 泛化对比实验

## 1. 实验目标
围绕「过拟合、Dropout、BatchNorm、权重衰减和 model.eval()」完成一个可运行实验，要求学生能解释输入 shape、模型输出、损失变化、关键超参数和实验结论之间的关系。

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
将下面代码保存为 `chapter_06_regularization_demo.py`。

```python
"""
Dropout 与 BatchNorm 泛化实验
实验目标：比较普通 MLP 与加入 BatchNorm/Dropout 的 MLP 在噪声数据上的表现。
依赖说明：pip install torch
学生任务：调整 dropout p、weight_decay，观察训练准确率和验证准确率差距。
调参建议：p 可试 0.1/0.3/0.5，weight_decay 可试 0/1e-4/1e-3。
常见报错：验证阶段忘记 model.eval() 会导致 Dropout 继续随机失活。
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def build_data(n=800, d=20):
    x = torch.randn(n, d)
    y = ((x[:, :5].sum(dim=1) + 0.5 * torch.randn(n)) > 0).long()
    return TensorDataset(x[:600], y[:600]), TensorDataset(x[600:], y[600:])


class Net(nn.Module):
    def __init__(self, regularized=False):
        super().__init__()
        layers = [nn.Linear(20, 64)]
        if regularized:
            layers.append(nn.BatchNorm1d(64))
        layers.append(nn.ReLU())
        if regularized:
            layers.append(nn.Dropout(0.3))
        layers.append(nn.Linear(64, 2))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


def accuracy(model, dataset):
    model.eval()
    loader = DataLoader(dataset, batch_size=128)
    correct = total = 0
    with torch.no_grad():
        for x, y in loader:
            pred = model(x).argmax(1)
            correct += int((pred == y).sum())
            total += x.size(0)
    return correct / total


def run(regularized=False):
    train_set, val_set = build_data()
    model = Net(regularized)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4 if regularized else 0)
    criterion = nn.CrossEntropyLoss()
    loader = DataLoader(train_set, batch_size=64, shuffle=True)
    for epoch in range(8):
        model.train()
        for x, y in loader:
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
    return accuracy(model, train_set), accuracy(model, val_set)


def main():
    torch.manual_seed(13)
    for flag in [False, True]:
        train_acc, val_acc = run(flag)
        print("regularized=" + str(flag), "train_acc=", round(train_acc, 3), "val_acc=", round(val_acc, 3))


if __name__ == "__main__":
    main()
```

## 5. 运行命令
```bash
python chapter_06_regularization_demo.py
```
如果在 notebook 中运行，请先确认当前内核已安装 torch，并逐单元执行完整代码。

## 6. 关键代码解释
- 数据构造部分负责控制输入维度、标签规则和 batch 组织方式。
- 模型结构部分体现本章主题：过拟合、Dropout、BatchNorm、权重衰减和 model.eval()。
- `loss.backward()` 负责把损失对参数的影响传回模型。
- `optimizer.step()` 根据梯度更新参数。
- 训练日志中的 loss、accuracy、shape 或参数量是判断实验是否正常的主要证据。

## 7. 学生任务
1. 打印第一批数据的输入 shape、标签 shape 和模型输出 shape。
2. 修改一个关键超参数，并记录至少 3 个 epoch 的变化。
3. 写出一次错误现象，例如 loss 不降、shape 不匹配或验证指标波动。
4. 用 150 字解释该实验如何帮助理解「过拟合、Dropout、BatchNorm、权重衰减和 model.eval()」。

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
