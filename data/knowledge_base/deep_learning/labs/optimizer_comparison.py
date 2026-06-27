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
