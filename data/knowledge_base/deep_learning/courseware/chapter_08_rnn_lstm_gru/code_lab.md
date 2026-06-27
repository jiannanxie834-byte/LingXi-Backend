# 第 8 章 LSTM 序列分类与门控机制实验

## 1. 实验目标
围绕「循环状态、梯度消失、LSTM门控、GRU 和序列分类」完成一个可运行实验，要求学生能解释输入 shape、模型输出、损失变化、关键超参数和实验结论之间的关系。

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
将下面代码保存为 `chapter_08_lstm_sequence_classification.py`。

```python
"""
LSTM 序列分类实验
实验目标：用 nn.LSTM 对合成序列做二分类，理解 batch_first、out[:, -1, :]、h_n/c_n 的 shape。
依赖说明：pip install torch
学生任务：修改 seq_len、hidden_size、learning_rate，观察 loss 和准确率变化。
调参建议：hidden_size 可试 8/16/32，学习率可试 1e-2/1e-3。
常见报错：输入 shape 应为 [batch, seq_len, feature]；标签 shape 应为 [batch]。
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def build_data(n=512, seq_len=12, feature=4):
    x = torch.randn(n, seq_len, feature)
    # 若后半段均值大于前半段，标为 1，否则 0。
    y = (x[:, seq_len // 2 :, :].mean(dim=(1, 2)) > x[:, : seq_len // 2, :].mean(dim=(1, 2))).long()
    return TensorDataset(x, y)


class LSTMClassifier(nn.Module):
    def __init__(self, input_size=4, hidden_size=16, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, (h_n, c_n) = self.lstm(x)
        last = out[:, -1, :]
        return self.fc(last)


def main():
    torch.manual_seed(7)
    loader = DataLoader(build_data(), batch_size=32, shuffle=True)
    model = LSTMClassifier()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(5):
        correct = total = 0
        running_loss = 0.0
        for x, y in loader:
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            running_loss += float(loss) * x.size(0)
            correct += int((logits.argmax(dim=1) == y).sum())
            total += x.size(0)
        print(f"epoch={epoch} loss={running_loss/total:.4f} acc={correct/total:.3f}")


if __name__ == "__main__":
    main()
```

## 5. 运行命令
```bash
python chapter_08_lstm_sequence_classification.py
```
如果在 notebook 中运行，请先确认当前内核已安装 torch，并逐单元执行完整代码。

## 6. 关键代码解释
- 数据构造部分负责控制输入维度、标签规则和 batch 组织方式。
- 模型结构部分体现本章主题：循环状态、梯度消失、LSTM门控、GRU 和序列分类。
- `loss.backward()` 负责把损失对参数的影响传回模型。
- `optimizer.step()` 根据梯度更新参数。
- 训练日志中的 loss、accuracy、shape 或参数量是判断实验是否正常的主要证据。

## 7. 学生任务
1. 打印第一批数据的输入 shape、标签 shape 和模型输出 shape。
2. 修改一个关键超参数，并记录至少 3 个 epoch 的变化。
3. 写出一次错误现象，例如 loss 不降、shape 不匹配或验证指标波动。
4. 用 150 字解释该实验如何帮助理解「循环状态、梯度消失、LSTM门控、GRU 和序列分类」。

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
