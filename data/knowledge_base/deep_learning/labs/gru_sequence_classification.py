"""
GRU 序列分类实验
实验目标：与 LSTM 实验对比，观察 GRU 参数更少、结构更简洁的特点。
依赖说明：pip install torch
学生任务：把 GRUClassifier 换成 LSTMClassifier，对比参数量和准确率。
调参建议：hidden_size、层数和学习率与 LSTM 实验保持一致，便于公平比较。
常见报错：GRU 只返回 h_n，没有 c_n。
"""
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


def build_data(n=512, seq_len=10, feature=3):
    x = torch.randn(n, seq_len, feature)
    y = (x[:, :, 0].sum(dim=1) > 0).long()
    return TensorDataset(x, y)


class GRUClassifier(nn.Module):
    def __init__(self, input_size=3, hidden_size=12, num_classes=2):
        super().__init__()
        self.gru = nn.GRU(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out, h_n = self.gru(x)
        return self.fc(out[:, -1, :])


def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def main():
    torch.manual_seed(11)
    model = GRUClassifier()
    print("trainable parameters:", count_parameters(model))
    loader = DataLoader(build_data(), batch_size=32, shuffle=True)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()
    for epoch in range(5):
        correct = total = 0
        for x, y in loader:
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            correct += int((logits.argmax(1) == y).sum())
            total += x.size(0)
        print(f"epoch={epoch} acc={correct/total:.3f}")


if __name__ == "__main__":
    main()
