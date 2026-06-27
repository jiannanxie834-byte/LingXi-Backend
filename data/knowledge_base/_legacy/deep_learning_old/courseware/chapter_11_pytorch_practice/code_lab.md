# 第 11 章 PyTorch 标准训练循环与模型保存实验

## 1. 实验目标
围绕「Dataset、DataLoader、训练循环、模型保存和实验记录」完成一个可运行实验，要求学生能解释输入 shape、模型输出、损失变化、关键超参数和实验结论之间的关系。

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
将下面代码保存为 `chapter_11_training_loop_checkpoint.py`。

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from pathlib import Path

torch.manual_seed(11)
x = torch.randn(700, 12)
y = ((x[:, :3].sum(1) - x[:, 3:6].sum(1)) > 0).long()
train_set = TensorDataset(x[:560], y[:560])
val_set = TensorDataset(x[560:], y[560:])
train_loader = DataLoader(train_set, batch_size=64, shuffle=True)
val_loader = DataLoader(val_set, batch_size=128)

model = nn.Sequential(nn.Linear(12, 32), nn.ReLU(), nn.Linear(32, 2))
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)

def evaluate():
    model.eval()
    correct = total = 0
    with torch.no_grad():
        for batch_x, batch_y in val_loader:
            pred = model(batch_x).argmax(1)
            correct += int((pred == batch_y).sum())
            total += batch_x.size(0)
    return correct / total

best_acc = 0.0
for epoch in range(8):
    model.train()
    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        loss = criterion(model(batch_x), batch_y)
        loss.backward()
        optimizer.step()
    val_acc = evaluate()
    print(f"epoch={epoch} val_acc={val_acc:.3f}")
    if val_acc > best_acc:
        best_acc = val_acc
        Path("outputs").mkdir(exist_ok=True)
        torch.save(model.state_dict(), "outputs/chapter_11_best.pt")
print("best_acc=", round(best_acc, 3))
```

## 5. 运行命令
```bash
python chapter_11_training_loop_checkpoint.py
```
如果在 notebook 中运行，请先确认当前内核已安装 torch，并逐单元执行完整代码。

## 6. 关键代码解释
- 数据构造部分负责控制输入维度、标签规则和 batch 组织方式。
- 模型结构部分体现本章主题：Dataset、DataLoader、训练循环、模型保存和实验记录。
- `loss.backward()` 负责把损失对参数的影响传回模型。
- `optimizer.step()` 根据梯度更新参数。
- 训练日志中的 loss、accuracy、shape 或参数量是判断实验是否正常的主要证据。

## 7. 学生任务
1. 打印第一批数据的输入 shape、标签 shape 和模型输出 shape。
2. 修改一个关键超参数，并记录至少 3 个 epoch 的变化。
3. 写出一次错误现象，例如 loss 不降、shape 不匹配或验证指标波动。
4. 用 150 字解释该实验如何帮助理解「Dataset、DataLoader、训练循环、模型保存和实验记录」。

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
