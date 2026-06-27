# 第 8 章 RNN、LSTM 与 GRU 序列建模

## 1. 学习定位
本章关注序列数据：文本、时间序列、语音、日志和传感器数据。它不是只背 RNN/LSTM/GRU 名称，而是理解“信息如何沿时间传递、为什么会遗忘、门控如何控制记忆”。

## 2. 本章在《深度学习》课程中的位置
本章建立在 MLP、反向传播、梯度流和 PyTorch 训练循环之上，并为 Transformer 的注意力机制学习提供对照。RNN 系列强调递归状态，Transformer 强调全局注意力，两者适合做结构比较。

## 3. 学习目标
- 解释 RNN 如何用隐状态处理序列。
- 说明 BPTT 的时间展开和梯度连乘问题。
- 理解梯度消失与长期依赖。
- 解释 LSTM 的细胞状态 `c_t`、隐藏状态 `h_t`、遗忘门、输入门、候选记忆和输出门。
- 比较 LSTM、GRU、普通 RNN 的结构和适用场景。
- 能使用 PyTorch `nn.LSTM` 完成简单序列分类。

## 4. 前置知识
需要掌握神经网络基础、反向传播、链式法则、梯度流、张量 shape、PyTorch Module 和训练循环。

## 5. RNN 基础
普通 RNN 在每个时间步接收当前输入 `x_t` 和上一时刻隐状态 `h_{t-1}`，得到当前隐状态 `h_t`：

```text
h_t = tanh(W_x x_t + W_h h_{t-1} + b)
```

`h_t` 可以理解为截至当前时间步的上下文摘要。RNN 的优势是参数在时间上共享，能处理可变长度序列；缺点是长序列中早期信息容易被后续更新覆盖。

## 6. BPTT 与梯度消失
BPTT 是 Backpropagation Through Time，即把 RNN 沿时间展开后做反向传播。若每个时间步的梯度都要乘上相似的权重矩阵和激活函数导数，长距离梯度会不断变小或变大，形成梯度消失或梯度爆炸。梯度消失会让模型难以学习很早之前的信息，这就是长期依赖问题。

## 7. LSTM 总体结构
LSTM 通过一条相对直接的细胞状态通道 `c_t` 保存长期信息，并用门控机制决定保留、写入和输出。核心流程是：

```text
f_t = sigmoid(W_f [h_{t-1}, x_t] + b_f)       # 遗忘门
i_t = sigmoid(W_i [h_{t-1}, x_t] + b_i)       # 输入门
g_t = tanh(W_g [h_{t-1}, x_t] + b_g)          # 候选记忆
c_t = f_t * c_{t-1} + i_t * g_t               # 细胞状态更新
o_t = sigmoid(W_o [h_{t-1}, x_t] + b_o)       # 输出门
h_t = o_t * tanh(c_t)                         # 隐藏状态
```

其中 `sigmoid` 输出 0 到 1 之间的比例，`*` 表示逐元素相乘。

## 8. 细胞状态 c_t 与隐藏状态 h_t
细胞状态 `c_t` 更像长期记忆通道，负责携带跨时间步的信息；隐藏状态 `h_t` 更像当前时间步对外输出的表示。混淆这两个状态是学习 LSTM 时最常见的问题之一。

## 9. 遗忘门、输入门、候选记忆、输出门
遗忘门 `f_t` 决定上一时刻细胞状态保留多少；输入门 `i_t` 决定新候选记忆写入多少；候选记忆 `g_t` 提供待写入的新内容；输出门 `o_t` 决定细胞状态中哪些信息转成当前隐藏状态。

## 10. LSTM 与 RNN、GRU 对比
普通 RNN 结构简单但长期依赖能力弱。LSTM 门更多，表达能力强但参数多。GRU 合并了部分门控结构，只维护隐藏状态，没有显式细胞状态，参数更少，训练可能更快。实际项目中应通过验证集比较，而不是凭名称决定模型。

## 11. PyTorch nn.LSTM 输入输出 shape
`nn.LSTM(input_size, hidden_size, batch_first=True)` 常见输入 shape 是 `[batch, seq_len, feature]`。输出 `out` 的 shape 是 `[batch, seq_len, hidden_size]`，最后隐状态 `h_n` 的 shape 是 `[num_layers * num_directions, batch, hidden_size]`。如果分类任务只用最后时间步，可取 `out[:, -1, :]`。

## 12. 序列分类代码示例
```python
import torch
import torch.nn as nn

class LSTMClassifier(nn.Module):
    def __init__(self, input_size=8, hidden_size=16, num_classes=2):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
    def forward(self, x):
        out, (h_n, c_n) = self.lstm(x)
        last = out[:, -1, :]
        return self.fc(last)

model = LSTMClassifier()
x = torch.randn(4, 10, 8)  # batch=4, seq_len=10, feature=8
logits = model(x)
print(logits.shape)  # [4, 2]
```

## 13. 常见误区
- 把 LSTM 理解为“更深的 RNN”，忽略细胞状态通道。
- 把细胞状态 `c_t` 和隐藏状态 `h_t` 混为一谈。
- 只背遗忘门、输入门、输出门名称，不理解它们控制的信息流。
- 忽略 `batch_first` 导致 shape 维度写反。
- 认为 LSTM 一定优于 GRU 或 Transformer。

## 14. 自测题与答案
1. 遗忘门的输出为什么在 0 到 1 之间？
   答：它使用 sigmoid，表示上一时刻细胞状态中每个维度保留的比例。
2. `out[:, -1, :]` 在序列分类中代表什么？
   答：batch 中每个序列最后一个时间步的隐藏表示。
3. LSTM 为什么能缓解长期依赖？
   答：细胞状态提供较直接的信息通道，门控控制信息保留和写入，减轻长距离梯度连乘造成的信息衰减。
4. GRU 和 LSTM 的主要区别是什么？
   答：GRU 结构更简洁，通常只有更新门和重置门，没有显式细胞状态。

## 15. 下一步学习建议
先完成 `lstm_sequence_classification.py`，观察输入输出 shape；再运行 `gru_sequence_classification.py` 比较参数量和验证指标；最后与 Transformer 的自注意力机制做对比。
