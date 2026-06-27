# 第 2 章 Python、NumPy 与 PyTorch 基础

## 章节定位

从 Tensor、Dataset、DataLoader、Transforms、nn.Module 到 GPU 训练，建立可运行的工程基础。 本章不再使用概念占位模板，而是将 Pytorch安装；Pytorch加载数据；PyTorch神经网络基础；Tensorboard使用；Transforms使用；Dataloader使用；nn.Module模块使用；网络模型保存与读取 中的课程结构、公式线索和 notebook 实验顺序整理为统一讲义。学生端看到的是重构后的课程内容；原始来源只作为内部依据和可追溯证据。

## 来源融合说明

- **Pytorch安装**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example
  - 内容要点：# 1. 安装Anaconda # 2. 查看显卡驱动 ① 在任务管理器中，性能栏中，若GUP能正常显示型号，说明显卡的驱动已经安装了。
  - 内容要点：② 打开设备管理器，在显示适配器中可以看到自己的计算机的GPU型号。
- **Pytorch加载数据**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；course code example；PyTorch model definition
  - 内容要点：# 1. Pytorch加载数据 ① Pytorch中加载数据需要Dataset、Dataloader。
  - 内容要点：- Dataset提供一种方式去获取每个数据及其对应的label，告诉我们总共有多少个数据。
- **PyTorch神经网络基础**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；PyTorch model definition；PyTorch model definition
  - 内容要点：# 1. 层和块 ① nn.Sequential 定义了一种特殊的Module。
  - 内容要点：# 2. 自定义块 # 3. 顺序块 # 4. 正向传播 # 5. 混合组合块 # 6. 参数管理 # 7. 嵌套块 # 8 内置初始化 # 9. 参数替换 # 10. 参数绑定 # 11. 自定义层 # 12. 读写文件
- **Tensorboard使用**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；course code example；course code example
  - 内容要点：# 1. Tensorboard用途 ① Tensorboad 可以用来查看loss是否按照我们预想的变化，或者查看训练到某一步输出的图像是什么样。
  - 内容要点：# 2. Tensorboard 写日志 # 3. Tensorboard 读日志 ① 在 Anaconda 终端里面，激活py3.6.3环境，再输入 tensorboard --logdir=C:\Users\wangy\Desktop\03CV\logs 命令，将网址赋值浏览器的网址栏，回车，即可查看tensorboard显示日志情况。
- **Transforms使用**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；course code example；PyTorch model definition
  - 内容要点：# 1. Transforms用途 ① Transforms当成工具箱的话，里面的class就是不同的工具。
  - 内容要点：② Transforms拿一些特定格式的图片，经过Transforms里面的工具，获得我们想要的结果。
- **Dataloader使用**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：Dataset/DataLoader example；Dataset/DataLoader example；Dataset/DataLoader example
  - 内容要点：# 1. Dataloader使用 ① Dataset只是去告诉我们程序，我们的数据集在什么位置，数据集第一个数据给它一个索引0，它对应的是哪一个数据。
  - 内容要点：② Dataloader就是把数据加载到神经网络当中，Dataloader所做的事就是每次从Dataset中取数据，至于怎么取，是由Dataloader中的参数决定的。
- **nn.Module模块使用**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：PyTorch model definition；PyTorch model definition
  - 内容要点：# 1. nn.Module模块使用 ① nn.Module是对所有神经网络提供一个基本的类。
  - 内容要点：② 我们的神经网络是继承nn.Module这个类，即nn.Module为父类，nn.Module为所有神经网络提供一个模板，对其中一些我们不满意的部分进行修改。
- **网络模型保存与读取**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；course code example；course code example
  - 内容要点：# 1. 网络模型保存(方式一) # 2. 网络模型导入(方式一) # 3. 网络模型保存(方式二) # 4. 网络模型导入(方式二) # 5. 网络陷阱-创建模型 # 6. 网络陷阱-失败加载模型 ① 点击 Kernel，再点击 Restart。
  - 内容要点：② 再运行下面的代码，即下面为第1个代码块运行，无法直接导入网络模型。

## 学习目标

- 能解释「Tensor」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「Dataset」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「DataLoader」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「Transforms」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「nn.Module」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「训练循环」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「GPU 训练」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「模型保存」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。

## 前置知识

学习本章前，应先确认上一章的核心对象、变量含义和实验边界。遇到公式时，不要只背符号，要能指出它在代码中对应哪一个张量、参数、损失或指标；遇到模型结构时，要能说清数据从输入到输出经过了哪些层。

## 知识结构总览

- **Tensor**：对应来源中的「Tensorboard使用」，学习时同时检查定义、流程、公式/代码和实验现象。
- **Dataset**：对应来源中的「Pytorch加载数据」，学习时同时检查定义、流程、公式/代码和实验现象。
- **DataLoader**：对应来源中的「Dataloader使用」，学习时同时检查定义、流程、公式/代码和实验现象。
- **Transforms**：对应来源中的「Transforms使用」，学习时同时检查定义、流程、公式/代码和实验现象。
- **nn.Module**：对应来源中的「nn.Module模块使用」，学习时同时检查定义、流程、公式/代码和实验现象。
- **训练循环**：对应来源中的「课程综合材料」，学习时同时检查定义、流程、公式/代码和实验现象。
- **GPU 训练**：对应来源中的「利用GPU训练」，学习时同时检查定义、流程、公式/代码和实验现象。
- **模型保存**：对应来源中的「网络模型保存与读取」，学习时同时检查定义、流程、公式/代码和实验现象。

## 1. Tensor

**来源位置**：Tensorboard使用。

**重构讲解**：Tensor 是 PyTorch 中承载数据和中间结果的多维数组，图像、标签、模型输出、损失计算都围绕张量形状和数据类型展开。

**来源要点摘录**：
- # 1. Tensorboard用途 ① Tensorboad 可以用来查看loss是否按照我们预想的变化，或者查看训练到某一步输出的图像是什么样。
- # 2. Tensorboard 写日志 # 3. Tensorboard 读日志 ① 在 Anaconda 终端里面，激活py3.6.3环境，再输入 tensorboard --logdir=C:\Users\wangy\Desktop\03CV\logs 命令，将网址赋值浏览器的网址栏，回车，即可查看tensorboard显示日志情况。
- ② 为避免多人使用端口导致冲突，也可以在后面加上后缀，使得端口独立，tensorboard --logdir=C:\Users\wangy\Desktop\03CV\logs --port=6008 ③ 输入网址可得Tensorboard界面。

**代码或实验落点**：
- course code example
- course code example
- course code example

**学习检查**：能说出一批 RGB 图片进入模型前常见形状为 N×C×H×W，并解释每个维度含义。

**常见误区**：只会打印 tensor，不检查 dtype、device 和 shape 是否满足模型输入要求。

## 2. Dataset

**来源位置**：Pytorch加载数据。

**重构讲解**：Dataset 定义样本如何按索引读取，以及每个样本返回哪些内容，通常包含输入数据和标签，是数据管道的起点。

**来源要点摘录**：
- # 1. Pytorch加载数据 ① Pytorch中加载数据需要Dataset、Dataloader。
- - Dataset提供一种方式去获取每个数据及其对应的label，告诉我们总共有多少个数据。
- # 2. 常用数据集两种形式 ① 常用的第一种数据形式，文件夹的名称是它的label。
- # 3. 路径直接加载数据 # 4. Dataset加载数据

**代码或实验落点**：
- course code example
- course code example
- PyTorch model definition

**学习检查**：能说明 `__len__` 和 `__getitem__` 的作用，并写出返回 image,label 的最小数据集。

**常见误区**：把 Dataset 和 DataLoader 混在一起，分不清谁负责取单个样本、谁负责组 batch。

## 3. DataLoader

**来源位置**：Dataloader使用。

**重构讲解**：DataLoader 负责把 Dataset 中的样本按 batch 组织起来，并处理 shuffle、batch_size、多进程加载等训练所需行为。

**来源要点摘录**：
- # 1. Dataloader使用 ① Dataset只是去告诉我们程序，我们的数据集在什么位置，数据集第一个数据给它一个索引0，它对应的是哪一个数据。
- ② Dataloader就是把数据加载到神经网络当中，Dataloader所做的事就是每次从Dataset中取数据，至于怎么取，是由Dataloader中的参数决定的。

**代码或实验落点**：
- Dataset/DataLoader example
- Dataset/DataLoader example
- Dataset/DataLoader example

**学习检查**：能解释 batch_size、shuffle、num_workers 对训练流程的影响。

**常见误区**：只改 batch_size，不检查最后一个 batch、标签维度和随机打乱是否合理。

## 4. Transforms

**来源位置**：Transforms使用。

**重构讲解**：Transforms 是输入预处理和数据增强工具链，常用于把图片转成 Tensor、归一化、裁剪、翻转或改变尺寸。

**来源要点摘录**：
- # 1. Transforms用途 ① Transforms当成工具箱的话，里面的class就是不同的工具。
- ② Transforms拿一些特定格式的图片，经过Transforms里面的工具，获得我们想要的结果。
- # 2. Transforms该如何使用 ## 2.1 transforms.Totensor使用 ## 2.2 需要Tensor数据类型原因 ① Tensor有一些属性，比如反向传播、梯度等属性，它包装了神经网络需要的一些属性。
- # 3. 常见的Transforms工具 ① Transforms的工具主要关注他的输入、输出、作用。

**代码或实验落点**：
- course code example
- course code example
- PyTorch model definition

**学习检查**：能写出 ToTensor、Normalize、Resize/RandomCrop 在图像任务中的顺序和作用。

**常见误区**：训练集和测试集使用完全相同的随机增强，导致评价不稳定。

## 5. nn.Module

**来源位置**：nn.Module模块使用。

**重构讲解**：nn.Module 是 PyTorch 神经网络的基类，用来组织层、参数和 forward 计算过程。自定义模型通常继承它并实现 forward。

**来源要点摘录**：
- # 1. nn.Module模块使用 ① nn.Module是对所有神经网络提供一个基本的类。
- ② 我们的神经网络是继承nn.Module这个类，即nn.Module为父类，nn.Module为所有神经网络提供一个模板，对其中一些我们不满意的部分进行修改。
- ② Myclass类继承nn.Module，super(Myclass, self).\_\_init__()就是对继承自父类nn.Module的属性进行初始化。
- 而且是用nn.Module的初始化方法来初始化继承的属性。

**代码或实验落点**：
- PyTorch model definition
- PyTorch model definition

**学习检查**：能解释 `__init__` 中定义层、`forward` 中描述数据流的区别。

**常见误区**：把层写在 forward 内每次重新创建，导致参数无法被优化器正确管理。

## 6. 训练循环

**来源位置**：课程综合材料。

**重构讲解**：训练循环通常包含取 batch、前向计算、计算损失、清空梯度、反向传播、优化器更新和指标记录，是所有模型实验的共同骨架。

**来源要点摘录**：
- 本节作为课程组织知识点，由课程地图、章节讲义和后续实验共同支撑。

**代码或实验落点**：
- 本节重点是概念、公式或结构理解；可在章节练习中补充最小实验。

**学习检查**：能按顺序写出 `optimizer.zero_grad()`、`loss.backward()`、`optimizer.step()` 的位置。

**常见误区**：忘记清空梯度或在验证阶段仍然更新参数。

## 7. GPU 训练

**来源位置**：利用GPU训练。

**重构讲解**：GPU 训练要求模型、输入张量和标签在同一 device 上，并通过 CUDA 加速张量运算；核心不是“有显卡”，而是正确迁移数据和模型。

**来源要点摘录**：
- # 1. 利用GPU训练(方式一) ① GPU训练主要有三部分，网络模型、数据(输入、标注)、损失函数，这三部分放到GPU上。
- # 2. GPU训练时间 # 3. CPU训练时间 # 4. 利用GPU训练(方式二) ① 电脑上有两个显卡时，可以用指定cuda:0、cuda:1。

**代码或实验落点**：
- Dataset/DataLoader example
- Dataset/DataLoader example
- Dataset/DataLoader example

**学习检查**：能说明为什么 model.to(device) 后，batch 数据也需要 to(device)。

**常见误区**：模型在 GPU、数据在 CPU，导致 device mismatch 报错。

## 8. 模型保存

**来源位置**：网络模型保存与读取。

**重构讲解**：模型保存通常保存 state_dict 或完整模型，其中 state_dict 更适合复现实验和跨环境加载；读取时需要先构建同结构模型再加载参数。

**来源要点摘录**：
- # 1. 网络模型保存(方式一) # 2. 网络模型导入(方式一) # 3. 网络模型保存(方式二) # 4. 网络模型导入(方式二) # 5. 网络陷阱-创建模型 # 6. 网络陷阱-失败加载模型 ① 点击 Kernel，再点击 Restart。
- # 7. 网络陷阱-成功加载模型(方式一) # 8. 网络陷阱-成功加载模型(方式二)

**代码或实验落点**：
- course code example
- course code example
- course code example

**学习检查**：能区分 `torch.save(model.state_dict())` 和保存整个 model 的差异。

**常见误区**：只保存权重，不保存模型结构、类别映射和训练配置。

## 教材式例子一：从来源结构到学习流程

以「Pytorch安装」为例，先读取来源标题层级，判断它属于概念解释、模型结构、优化策略还是实验任务；再将它映射到本章的 Tensor, Dataset, DataLoader, Transforms；最后生成一条可执行学习任务：阅读主讲义、完成练习、运行或观察实验、写出错因复盘。

## 教材式例子二：从 notebook 到课程实验

AccumulateMore/CV 中的 notebook 不是直接塞给学生，而是被拆成实验目标、关键代码用途、运行步骤和调参任务。学生学习 第 2 章 Python、NumPy 与 PyTorch 基础 时，应能把 `Dataset/DataLoader`、`nn.Module`、`loss.backward()`、`optimizer.step()` 或对应模型结构放回完整训练循环。

## 易错点与纠偏

- 只背来源标题，不知道标题下真正讨论了什么模型、公式或实验。
- 把 notebook 当成可直接展示的学习资源，而没有整理成目标、步骤、任务和评价。
- 学模型结构时不检查输入输出 shape，导致代码能抄但不能解释。
- 学优化或正则化时不看训练/验证曲线，无法判断方法是否真的改善泛化。

## 课堂讨论问题

1. Tensor 与 Dataset 在本章流程中分别解决什么问题？
2. 如果学生已经会使用工具库，但解释不清 Tensor，应该如何安排补弱？
3. 哪些内容适合做动画或流程图，哪些内容更适合做代码实验？

## 自测题

1. 围绕「Tensor」写出定义、输入输出、常见误区和一个应用场景。
2. 围绕「Dataset」写出定义、输入输出、常见误区和一个应用场景。
3. 围绕「DataLoader」写出定义、输入输出、常见误区和一个应用场景。
4. 围绕「Transforms」写出定义、输入输出、常见误区和一个应用场景。
5. 围绕「nn.Module」写出定义、输入输出、常见误区和一个应用场景。
6. 围绕「训练循环」写出定义、输入输出、常见误区和一个应用场景。
7. 围绕「GPU 训练」写出定义、输入输出、常见误区和一个应用场景。
8. 围绕「模型保存」写出定义、输入输出、常见误区和一个应用场景。

## 小结与下一步

完成本章后，应能把 Tensor, Dataset, DataLoader, Transforms 串成一条可执行的学习路径。下一步不是盲目堆资料，而是根据画像、诊断结果和当前章节位置选择主讲义、练习、实验或项目任务。
