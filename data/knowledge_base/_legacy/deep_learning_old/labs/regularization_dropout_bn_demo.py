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
