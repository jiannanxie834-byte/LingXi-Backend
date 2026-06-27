# 第 8 章 经典 CNN 架构与图像分类实践

## 章节定位

以 LeNet、AlexNet、VGG、GoogLeNet、ResNet、迁移学习和 CIFAR-10 图像分类建立视觉实践主线。 本章不再使用概念占位模板，而是将 经典卷积网络；合并行连接的网络GoogLeNet；经典神经网络LeNet；深度卷积神经网络AlexNet；使用块的网络VGG；批量归一化；残差神经网络ResNet；微调 中的课程结构、公式线索和 notebook 实验顺序整理为统一讲义。学生端看到的是重构后的课程内容；原始来源只作为内部依据和可追溯证据。

## 来源融合说明

- **经典卷积网络**（Andrew Ng 笔记）：覆盖 经典卷积网络、LeNet-5、AlexNet、VGG、残差网络。
  - 公式线索：a^{[l]}；a^{[l+2]}；z^{[l+1]} = W^{[l+1]}a^{[l]} + b^{[l+1]}
  - 内容要点：深度卷积网络：实例探究 讲到的经典 CNN 模型包括： * LeNet-5 * AlexNet * VGG 此外还有 ResNet（Residual Network，残差网络），以及 Inception Neural Network。
  - 内容要点：## 经典卷积网络 ### LeNet-5 特点： * LeNet-5 针对灰度图像而训练，因此输入图片的通道数为 1。
- **合并行连接的网络GoogLeNet**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：PyTorch model definition；CNN convolution example；course code example
  - 内容要点：# 1. GoogLeNet ① 白色的卷积用来改变通道数，蓝色的卷积用来抽取信息。
  - 内容要点：② 最左边一条1X1卷积是用来抽取通道信息，其他的3X3卷积用来抽取空间信息。
- **经典神经网络LeNet**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：PyTorch model definition；course code example；course code example
  - 内容要点：# 1. LeNet网络 # 2. 总结 # 1. LeNet网络（使用自定义）
- **深度卷积神经网络AlexNet**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：CNN convolution example；course code example
  - 内容要点：# 1. AlexNet网络 # 2. 总结 # 1. AlexNet网络（使用自定义）
- **使用块的网络VGG**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：CNN convolution example；CNN convolution example
  - 内容要点：# 1. VGG网络 # 2. 总结 # 1. VGG网络（使用自定义）
- **批量归一化**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；PyTorch model definition；CNN convolution example
  - 内容要点：# 1. 正态分布 ① 正态分布，又叫做高斯分布。
  - 内容要点：# 2. 每层数据分布 ① 机器学习领域有个很重要的假设：I.I.D.（独立同分布）假设，就是假设训练数据和测试数据是满足相同分布的，这样就能做到通过训练数据获得的模型能够在测试集获得好的效果。
- **残差神经网络ResNet**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：PyTorch model definition；course code example；CNN convolution example
  - 内容要点：# 1. ResNet网络 ① 这样直接加保证了最优解“至少不会变差”，g(x)=0是和以前一样的。
  - 内容要点：② 这个x实际上是f0(x)，就是上幅图小的部分，f(x)是f1(x)，新函数包含原函数。
- **微调**（AccumulateMore/CV Notebook）：覆盖 未提取标题层级。
  - 代码线索：course code example；course code example；course code example
  - 内容要点：# 1. 微调 # 2. 总结 # 1. 微调

## 学习目标

- 能解释「LeNet」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「AlexNet」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「VGG」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「GoogLeNet」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「ResNet」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「BatchNorm」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「迁移学习」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。
- 能解释「CIFAR-10」的定义、来源中的具体语境、公式或代码位置，并完成至少一个可检查任务。

## 前置知识

学习本章前，应先确认上一章的核心对象、变量含义和实验边界。遇到公式时，不要只背符号，要能指出它在代码中对应哪一个张量、参数、损失或指标；遇到模型结构时，要能说清数据从输入到输出经过了哪些层。

## 知识结构总览

- **LeNet**：对应来源中的「经典卷积网络」，学习时同时检查定义、流程、公式/代码和实验现象。
- **AlexNet**：对应来源中的「经典卷积网络」，学习时同时检查定义、流程、公式/代码和实验现象。
- **VGG**：对应来源中的「经典卷积网络」，学习时同时检查定义、流程、公式/代码和实验现象。
- **GoogLeNet**：对应来源中的「合并行连接的网络GoogLeNet」，学习时同时检查定义、流程、公式/代码和实验现象。
- **ResNet**：对应来源中的「残差神经网络ResNet」，学习时同时检查定义、流程、公式/代码和实验现象。
- **BatchNorm**：对应来源中的「批量归一化」，学习时同时检查定义、流程、公式/代码和实验现象。
- **迁移学习**：对应来源中的「微调」，学习时同时检查定义、流程、公式/代码和实验现象。
- **CIFAR-10**：对应来源中的「实战Kaggle比赛图像分类CIFAR10」，学习时同时检查定义、流程、公式/代码和实验现象。

## 1. LeNet

**来源位置**：经典卷积网络；标题层级包括 经典卷积网络、LeNet-5、AlexNet、VGG、残差网络、残差网络有效的原因。

**重构讲解**：LeNet-5 是早期经典 CNN，常见结构是 CONV-POOL-CONV-POOL-FC-FC-OUTPUT，展示了卷积层、池化层和全连接层组合处理灰度图像的基本范式。

**来源要点摘录**：
- 深度卷积网络：实例探究 讲到的经典 CNN 模型包括： * LeNet-5 * AlexNet * VGG 此外还有 ResNet（Residual Network，残差网络），以及 Inception Neural Network。
- ## 经典卷积网络 ### LeNet-5 特点： * LeNet-5 针对灰度图像而训练，因此输入图片的通道数为 1。
- * 典型的 LeNet-5 结构包含卷积层（CONV layer），池化层（POOL layer）和全连接层（FC layer），排列顺序一般为 CONV layer->POOL layer->CONV layer->POOL layer->FC layer->FC layer->OUTPUT layer。
- * 当 LeNet-5模型被提出时，其池化层使用的是平均池化，而且各层激活函数一般选用 Sigmoid 和 tanh。

**代码或实验落点**：
- 本节重点是概念、公式或结构理解；可在章节练习中补充最小实验。

**学习检查**：能画出 LeNet 的层次顺序，并说明卷积层与池化层分别改变了什么。

**常见误区**：只记 LeNet 名称，不知道它为什么比全连接网络更适合图像。

## 2. AlexNet

**来源位置**：经典卷积网络；标题层级包括 经典卷积网络、LeNet-5、AlexNet、VGG、残差网络、残差网络有效的原因。

**重构讲解**：AlexNet 通过更深的卷积网络、大规模数据训练、ReLU、Dropout 和 GPU 训练推动了 ImageNet 图像分类突破，是深度 CNN 实用化的重要节点。

**来源要点摘录**：
- 深度卷积网络：实例探究 讲到的经典 CNN 模型包括： * LeNet-5 * AlexNet * VGG 此外还有 ResNet（Residual Network，残差网络），以及 Inception Neural Network。
- ### AlexNet 特点： * AlexNet 模型与 LeNet-5 模型类似，但是更复杂，包含约 6000 万个参数。
- 另外，AlexNet 模型使用了 ReLU 函数。
- * 当用于训练图像和数据集时，AlexNet 能够处理非常相似的基本构造模块，这些模块往往包含大量的隐藏单元或数据。

**代码或实验落点**：
- 本节重点是概念、公式或结构理解；可在章节练习中补充最小实验。

**学习检查**：能说明 AlexNet 相比 LeNet 在深度、数据规模、激活函数和正则化上的变化。

**常见误区**：把 AlexNet 只理解成层数更多，而忽略 ReLU、Dropout 和工程训练条件。

## 3. VGG

**来源位置**：经典卷积网络；标题层级包括 经典卷积网络、LeNet-5、AlexNet、VGG、残差网络、残差网络有效的原因。

**重构讲解**：VGG 使用大量 3x3 小卷积核堆叠构造深层网络，用简单规则化结构换取更强表达能力，也让网络结构更容易复现和比较。

**来源要点摘录**：
- 深度卷积网络：实例探究 讲到的经典 CNN 模型包括： * LeNet-5 * AlexNet * VGG 此外还有 ResNet（Residual Network，残差网络），以及 Inception Neural Network。
- ### VGG 特点： * VGG 又称 VGG-16 网络，“16”指网络中包含 16 个卷积层和全连接层。
- * VGG 需要训练的特征数量巨大，包含多达约 1.38 亿个参数。

**代码或实验落点**：
- 本节重点是概念、公式或结构理解；可在章节练习中补充最小实验。

**学习检查**：能解释两个 3x3 卷积堆叠与更大感受野之间的关系。

**常见误区**：只背 VGG 很深，不知道它的核心设计是统一小卷积核堆叠。

## 4. GoogLeNet

**来源位置**：合并行连接的网络GoogLeNet。

**重构讲解**：GoogLeNet 的 Inception 模块在同一层并行使用不同尺度卷积和池化，再把结果拼接，目标是在控制计算量的同时捕获多尺度特征。

**来源要点摘录**：
- # 1. GoogLeNet ① 白色的卷积用来改变通道数，蓝色的卷积用来抽取信息。
- # 2. 总结 # 1. GoogLeNet（使用自定义） ① 在实际的项目当中，我们往往预先只知道的是输入数据和输出数据的大小，而不知道核与步长的大小。

**代码或实验落点**：
- PyTorch model definition
- CNN convolution example
- course code example

**学习检查**：能画出 Inception 模块的多分支结构，并说明 1x1 卷积用于降维的意义。

**常见误区**：只说 GoogLeNet 很复杂，不知道多分支和 1x1 卷积解决什么问题。

## 5. ResNet

**来源位置**：残差神经网络ResNet。

**重构讲解**：ResNet 引入残差连接，让网络学习 F(x)+x，缓解深层网络退化问题，使更深的 CNN 更容易优化。

**来源要点摘录**：
- # 1. ResNet网络 ① 这样直接加保证了最优解“至少不会变差”，g(x)=0是和以前一样的。
- # 2. 总结 # 1. ResNet网络（使用自定义）

**代码或实验落点**：
- PyTorch model definition
- course code example
- CNN convolution example

**学习检查**：能说明残差块中 shortcut 的输入和输出维度什么时候需要匹配或投影。

**常见误区**：把残差连接理解成简单跳过层，而不理解它改变了优化目标。

## 6. BatchNorm

**来源位置**：批量归一化。

**公式/结构线索**：`z_hat = (z - mu) / sqrt(sigma^2 + eps)`。

**重构讲解**：BatchNorm 在小批量内标准化中间激活，并学习缩放和平移参数，可以稳定训练、允许更大学习率，并在 CNN 中常和卷积层配合使用。

**来源要点摘录**：
- # 3. 批量归一化 ① 既然可以把原始训练样本做归一化，那么如果在深度神经网络的每一层，都可以有类似的手段，也就是说把层之间传递的数据移到0点附近，那么训练效果就应该会很理想。

**代码或实验落点**：
- course code example
- PyTorch model definition
- CNN convolution example

**学习检查**：能区分 BatchNorm 在训练阶段使用 batch 统计量、推理阶段使用移动平均统计量。

**常见误区**：把 BatchNorm 当成输入数据预处理，而不是网络内部层。

## 7. 迁移学习

**来源位置**：微调。

**重构讲解**：迁移学习利用在大数据集上预训练的特征提取能力，在目标数据较少时微调分类头或部分网络层，提高训练效率和泛化能力。

**来源要点摘录**：
- # 1. 微调 # 2. 总结 # 1. 微调

**代码或实验落点**：
- course code example
- course code example
- course code example

**学习检查**：能说明冻结 backbone 与 fine-tune 全网络的区别。

**常见误区**：目标数据分布差异很大时仍盲目套用预训练模型。

## 8. CIFAR-10

**来源位置**：实战Kaggle比赛图像分类CIFAR10。

**重构讲解**：CIFAR-10 是十类小图像分类任务，适合演示 CNN 从数据增强、模型训练、验证评估到错误样例分析的完整流程。

**来源要点摘录**：
- # 1. 实战Kaggle比赛图像分类CIFAR10 ① 比赛的网址是 https://www.kaggle.com/c/cifar-10

**代码或实验落点**：
- course code example
- course code example
- course code example

**学习检查**：能写出数据增强、训练集/验证集划分、评价指标和错误样例复盘步骤。

**常见误区**：只跑出 accuracy，不分析哪些类别容易混淆。

## 教材式例子一：从来源结构到学习流程

以「经典卷积网络」为例，先读取来源标题层级，判断它属于概念解释、模型结构、优化策略还是实验任务；再将它映射到本章的 LeNet, AlexNet, VGG, GoogLeNet；最后生成一条可执行学习任务：阅读主讲义、完成练习、运行或观察实验、写出错因复盘。

## 教材式例子二：从 notebook 到课程实验

AccumulateMore/CV 中的 notebook 不是直接塞给学生，而是被拆成实验目标、关键代码用途、运行步骤和调参任务。学生学习 第 8 章 经典 CNN 架构与图像分类实践 时，应能把 `Dataset/DataLoader`、`nn.Module`、`loss.backward()`、`optimizer.step()` 或对应模型结构放回完整训练循环。

## 易错点与纠偏

- 只背来源标题，不知道标题下真正讨论了什么模型、公式或实验。
- 把 notebook 当成可直接展示的学习资源，而没有整理成目标、步骤、任务和评价。
- 学模型结构时不检查输入输出 shape，导致代码能抄但不能解释。
- 学优化或正则化时不看训练/验证曲线，无法判断方法是否真的改善泛化。

## 课堂讨论问题

1. LeNet 与 AlexNet 在本章流程中分别解决什么问题？
2. 如果学生已经会使用工具库，但解释不清 LeNet，应该如何安排补弱？
3. 哪些内容适合做动画或流程图，哪些内容更适合做代码实验？

## 自测题

1. 围绕「LeNet」写出定义、输入输出、常见误区和一个应用场景。
2. 围绕「AlexNet」写出定义、输入输出、常见误区和一个应用场景。
3. 围绕「VGG」写出定义、输入输出、常见误区和一个应用场景。
4. 围绕「GoogLeNet」写出定义、输入输出、常见误区和一个应用场景。
5. 围绕「ResNet」写出定义、输入输出、常见误区和一个应用场景。
6. 围绕「BatchNorm」写出定义、输入输出、常见误区和一个应用场景。
7. 围绕「迁移学习」写出定义、输入输出、常见误区和一个应用场景。
8. 围绕「CIFAR-10」写出定义、输入输出、常见误区和一个应用场景。
9. 围绕「LeNet」写出定义、输入输出、常见误区和一个应用场景。
10. 围绕「AlexNet」写出定义、输入输出、常见误区和一个应用场景。
11. 围绕「VGG」写出定义、输入输出、常见误区和一个应用场景。
12. 围绕「GoogLeNet」写出定义、输入输出、常见误区和一个应用场景。

## 小结与下一步

完成本章后，应能把 LeNet, AlexNet, VGG, GoogLeNet 串成一条可执行的学习路径。下一步不是盲目堆资料，而是根据画像、诊断结果和当前章节位置选择主讲义、练习、实验或项目任务。
