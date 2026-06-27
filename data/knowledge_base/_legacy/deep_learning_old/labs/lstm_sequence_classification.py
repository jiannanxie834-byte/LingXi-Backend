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
