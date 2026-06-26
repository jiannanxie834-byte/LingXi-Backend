import torch
import torch.nn as nn


class TinyMLP(nn.Module):
    def __init__(self, in_features=28 * 28, hidden=128, num_classes=10):
        super().__init__()
        self.net = nn.Sequential(
            nn.Flatten(),
            nn.Linear(in_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, num_classes),
        )

    def forward(self, x):
        return self.net(x)


if __name__ == "__main__":
    model = TinyMLP()
    sample = torch.randn(4, 1, 28, 28)
    print(model(sample).shape)
