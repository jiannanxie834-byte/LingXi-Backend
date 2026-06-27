# 第 6 章 优化算法与超参数调试 代码实验

## 实验目标
围绕本章主题完成 `optimizer_comparison.py`，把概念落到可运行代码、日志和实验报告中。

## 环境依赖
```bash
python >= 3.10
pip install torch torchvision numpy matplotlib
```

## 运行方式
```bash
python data/knowledge_base/deep_learning_v2/labs/optimizer_comparison.py
```

## 学生任务
- 跑通默认参数，记录训练/验证指标。
- 修改一个模型结构或超参数，比较前后变化。
- 解释输出 shape、损失变化和错误样例。

## 调参建议
- 每次只改一个变量，例如学习率、batch size、层数或 dropout。
- 保留随机种子和数据划分，避免把随机波动误认为方法改进。

## 常见报错
- shape mismatch：打印每层输入输出维度。
- CUDA out of memory：减小 batch size 或切回 CPU。
- loss 不下降：检查学习率、标签格式和模型输出。