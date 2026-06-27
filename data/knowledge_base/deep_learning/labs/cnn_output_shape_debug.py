"""
CNN 输出尺寸调试实验
实验目标：用公式和 PyTorch 输出同时验证卷积/池化后的特征图尺寸。
依赖说明：pip install torch
学生任务：修改 kernel_size、stride、padding，先手算再运行代码验证。
调参建议：固定输入 32x32，分别尝试 padding=0/1、stride=1/2。
常见报错：忘记 floor；混淆通道数 C 和空间尺寸 H/W。
"""
import math
import torch
import torch.nn as nn


def conv_out(size, kernel_size, stride=1, padding=0, dilation=1):
    return math.floor((size + 2 * padding - dilation * (kernel_size - 1) - 1) / stride + 1)


def main():
    x = torch.randn(4, 3, 32, 32)
    conv = nn.Conv2d(3, 16, kernel_size=3, stride=2, padding=1)
    y = conv(x)
    expected_h = conv_out(32, kernel_size=3, stride=2, padding=1)
    print("input shape :", tuple(x.shape))
    print("output shape:", tuple(y.shape))
    print("formula H/W :", expected_h)
    assert y.shape == (4, 16, expected_h, expected_h)

    pool = nn.MaxPool2d(kernel_size=2, stride=2)
    z = pool(y)
    print("after pool  :", tuple(z.shape))


if __name__ == "__main__":
    main()
