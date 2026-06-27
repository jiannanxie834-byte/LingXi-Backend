# 第 5 章 SGD、Momentum 与 Adam 优化器对比实验

## 1. 实验目标
围绕「梯度下降、SGD、Momentum、Adam 和学习率敏感性」完成一个可运行实验，要求学生能解释输入 shape、模型输出、损失变化、关键超参数和实验结论之间的关系。

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
将下面代码保存为 `chapter_05_optimizer_comparison.py`。

```python
"""
优化器对比实验
实验目标：在同一合成分类任务上比较 SGD、Momentum、Adam 的收敛曲线。
依赖说明：pip install torch
学生任务：修改学习率，记录 loss 曲线是否震荡。
调参建议：SGD 可尝试 lr=0.1/0.01，Adam 可尝试 lr=0.001/0.0003。
常见报错：不同优化器对学习率敏感度不同，不能直接用同一个最优学习率下结论。
"""
import copy
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def build_data(n=600):
    x = torch.randn(n, 2)
    y = ((x[:, 0] * x[:, 1] + 0.25 * x[:, 0]) > 0).long()
    return DataLoader(TensorDataset(x, y), batch_size=64, shuffle=True)


def make_model():
    return nn.Sequential(nn.Linear(2, 16), nn.ReLU(), nn.Linear(16, 2))


def train(name, model, optimizer, loader):
    criterion = nn.CrossEntropyLoss()
    for epoch in range(8):
        total_loss = total = 0
        for x, y in loader:
            optimizer.zero_grad()
            loss = criterion(model(x), y)
            loss.backward()
            optimizer.step()
            total_loss += float(loss) * x.size(0)
            total += x.size(0)
        print(f"{name:8s} epoch={epoch} loss={total_loss/total:.4f}")


def main():
    torch.manual_seed(3)
    loader = build_data()
    base = make_model()
    configs = [
        ("SGD", torch.optim.SGD, {"lr": 0.05}),
        ("Momentum", torch.optim.SGD, {"lr": 0.05, "momentum": 0.9}),
        ("Adam", torch.optim.Adam, {"lr": 0.001}),
    ]
    for name, optim_cls, kwargs in configs:
        model = copy.deepcopy(base)
        train(name, model, optim_cls(model.parameters(), **kwargs), loader)


if __name__ == "__main__":
    main()
```

## 5. 运行命令
```bash
python chapter_05_optimizer_comparison.py
```
如果在 notebook 中运行，请先确认当前内核已安装 torch，并逐单元执行完整代码。

## 6. 关键代码解释
- 数据构造部分负责控制输入维度、标签规则和 batch 组织方式。
- 模型结构部分体现本章主题：梯度下降、SGD、Momentum、Adam 和学习率敏感性。
- `loss.backward()` 负责把损失对参数的影响传回模型。
- `optimizer.step()` 根据梯度更新参数。
- 训练日志中的 loss、accuracy、shape 或参数量是判断实验是否正常的主要证据。

## 7. 学生任务
1. 打印第一批数据的输入 shape、标签 shape 和模型输出 shape。
2. 修改一个关键超参数，并记录至少 3 个 epoch 的变化。
3. 写出一次错误现象，例如 loss 不降、shape 不匹配或验证指标波动。
4. 用 150 字解释该实验如何帮助理解「梯度下降、SGD、Momentum、Adam 和学习率敏感性」。

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
