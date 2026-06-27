# 深度学习资源库审计报告

## 0. 原始数据源扫描

- 原始章节讲义：12 个文件
- 细粒度知识单元：71 条
- 外部公开视频目录：24 条
- 本地实验脚本：8 个

| 类型 | 文件/目录 | 数量 | 治理建议 |
| --- | --- | ---: | --- |
| 原始章节讲义 | data/knowledge_base/deep_learning/chapters | 12 | 保留为内部知识底稿，学生端优先展示 courseware 章节资源 |
| 课程图谱单元 | knowledge_units.jsonl | 71 | 用于语义接地和章节索引，不再直接生成平铺小卡片 |
| 视频目录 | video_catalog.json | 24 | 仅作 link_only 推荐，不下载、不搬运、不重托管 |
| 实验脚本 | labs/*.py | 8 | 合并进章节 code_lab 或作为可运行实验附件依据 |

## 1. 章节文件质量

| 章节 | 文件 | 字数 | 二级标题 | 公式/流程 | 例子 | 题目数 | 答案解析 | 代码/伪代码 | 参考说明 |
| --- | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- |
| 第 1 章 深度学习导论与学习诊断 | chapter_01_intro/main_note.md | 3560 | 17 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 1 章 深度学习导论与学习诊断 | chapter_01_intro/mind_map.mmd | 125 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 1 章 深度学习导论与学习诊断 | chapter_01_intro/exercises.md | 2700 | 0 | 是 | 否 | 8 | 是 | 是 | 否 |
| 第 1 章 深度学习导论与学习诊断 | chapter_01_intro/reading_video_guide.md | 965 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 2 章 数学与机器学习前置知识 | chapter_02_prerequisites/main_note.md | 3537 | 17 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 2 章 数学与机器学习前置知识 | chapter_02_prerequisites/mind_map.mmd | 120 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 2 章 数学与机器学习前置知识 | chapter_02_prerequisites/exercises.md | 2730 | 0 | 是 | 否 | 8 | 是 | 是 | 否 |
| 第 2 章 数学与机器学习前置知识 | chapter_02_prerequisites/reading_video_guide.md | 962 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 2 章 数学与机器学习前置知识 | chapter_02_prerequisites/code_lab.md | 1574 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 3 章 神经网络基础与感知机 | chapter_03_neural_network/main_note.md | 3563 | 17 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 3 章 神经网络基础与感知机 | chapter_03_neural_network/mind_map.mmd | 121 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 3 章 神经网络基础与感知机 | chapter_03_neural_network/exercises.md | 2745 | 0 | 是 | 否 | 8 | 是 | 是 | 否 |
| 第 3 章 神经网络基础与感知机 | chapter_03_neural_network/reading_video_guide.md | 961 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 3 章 神经网络基础与感知机 | chapter_03_neural_network/code_lab.md | 1920 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 4 章 反向传播 | chapter_04_backpropagation/main_note.md | 4805 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 4 章 反向传播 | chapter_04_backpropagation/mind_map.mmd | 115 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 4 章 反向传播 | chapter_04_backpropagation/exercises.md | 4170 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 4 章 反向传播 | chapter_04_backpropagation/reading_video_guide.md | 955 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 4 章 反向传播 | chapter_04_backpropagation/interactive_animation.json | 606 | 0 | 是 | 否 | 0 | 否 | 否 | 否 |
| 第 5 章 优化算法 | chapter_05_optimization/main_note.md | 4794 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 5 章 优化算法 | chapter_05_optimization/mind_map.mmd | 120 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 5 章 优化算法 | chapter_05_optimization/exercises.md | 4180 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 5 章 优化算法 | chapter_05_optimization/reading_video_guide.md | 961 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 5 章 优化算法 | chapter_05_optimization/code_lab.md | 2368 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 6 章 正则化与泛化 | chapter_06_regularization/main_note.md | 4889 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 6 章 正则化与泛化 | chapter_06_regularization/mind_map.mmd | 121 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 6 章 正则化与泛化 | chapter_06_regularization/exercises.md | 4234 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 6 章 正则化与泛化 | chapter_06_regularization/reading_video_guide.md | 966 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 6 章 正则化与泛化 | chapter_06_regularization/code_lab.md | 2869 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 7 章 卷积神经网络 CNN | chapter_07_cnn/main_note.md | 4795 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 7 章 卷积神经网络 CNN | chapter_07_cnn/mind_map.mmd | 119 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 7 章 卷积神经网络 CNN | chapter_07_cnn/exercises.md | 4033 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 7 章 卷积神经网络 CNN | chapter_07_cnn/reading_video_guide.md | 959 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 7 章 卷积神经网络 CNN | chapter_07_cnn/code_lab.md | 1956 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 7 章 卷积神经网络 CNN | chapter_07_cnn/interactive_animation.json | 598 | 0 | 是 | 否 | 0 | 否 | 否 | 否 |
| 第 8 章 RNN/LSTM/GRU 序列建模 | chapter_08_rnn_lstm_gru/main_note.md | 4879 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 8 章 RNN/LSTM/GRU 序列建模 | chapter_08_rnn_lstm_gru/mind_map.mmd | 131 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 8 章 RNN/LSTM/GRU 序列建模 | chapter_08_rnn_lstm_gru/exercises.md | 4149 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 8 章 RNN/LSTM/GRU 序列建模 | chapter_08_rnn_lstm_gru/reading_video_guide.md | 970 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 8 章 RNN/LSTM/GRU 序列建模 | chapter_08_rnn_lstm_gru/code_lab.md | 2576 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 8 章 RNN/LSTM/GRU 序列建模 | chapter_08_rnn_lstm_gru/interactive_animation.json | 614 | 0 | 是 | 否 | 0 | 否 | 否 | 否 |
| 第 9 章 Attention/Transformer | chapter_09_transformer/main_note.md | 4920 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 9 章 Attention/Transformer | chapter_09_transformer/mind_map.mmd | 137 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 9 章 Attention/Transformer | chapter_09_transformer/exercises.md | 4638 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 9 章 Attention/Transformer | chapter_09_transformer/reading_video_guide.md | 980 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 9 章 Attention/Transformer | chapter_09_transformer/code_lab.md | 1666 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 9 章 Attention/Transformer | chapter_09_transformer/interactive_animation.json | 624 | 0 | 是 | 否 | 0 | 否 | 否 | 否 |
| 第 10 章 生成模型 | chapter_10_generative_models/main_note.md | 3495 | 17 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 10 章 生成模型 | chapter_10_generative_models/mind_map.mmd | 115 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 10 章 生成模型 | chapter_10_generative_models/exercises.md | 2760 | 0 | 是 | 否 | 8 | 是 | 是 | 否 |
| 第 10 章 生成模型 | chapter_10_generative_models/reading_video_guide.md | 958 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 11 章 PyTorch 实践 | chapter_11_pytorch_practice/main_note.md | 4965 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 11 章 PyTorch 实践 | chapter_11_pytorch_practice/mind_map.mmd | 132 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 11 章 PyTorch 实践 | chapter_11_pytorch_practice/exercises.md | 4324 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 11 章 PyTorch 实践 | chapter_11_pytorch_practice/reading_video_guide.md | 976 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 11 章 PyTorch 实践 | chapter_11_pytorch_practice/code_lab.md | 2361 | 10 | 是 | 否 | 0 | 否 | 是 | 否 |
| 第 12 章 课程综合项目 | chapter_12_final_project/main_note.md | 4703 | 20 | 是 | 是 | 0 | 否 | 是 | 是 |
| 第 12 章 课程综合项目 | chapter_12_final_project/mind_map.mmd | 119 | 0 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 12 章 课程综合项目 | chapter_12_final_project/exercises.md | 3980 | 0 | 是 | 否 | 12 | 是 | 是 | 否 |
| 第 12 章 课程综合项目 | chapter_12_final_project/reading_video_guide.md | 962 | 9 | 是 | 是 | 0 | 否 | 否 | 是 |
| 第 12 章 课程综合项目 | chapter_12_final_project/project_brief.md | 1483 | 7 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 12 章 课程综合项目 | chapter_12_final_project/rubric.md | 1389 | 6 | 是 | 是 | 0 | 否 | 否 | 否 |
| 第 12 章 课程综合项目 | chapter_12_final_project/report_template.md | 1426 | 14 | 否 | 是 | 0 | 否 | 否 | 是 |

## 2. 数据库资源概览

- Resource 总数：169
- ResourceArtifact 总数：169

| 章节 | 资源数 |
| --- | ---: |
| chapter_01_intro | 4 |
| chapter_02_prerequisites | 5 |
| chapter_03_neural_network | 5 |
| chapter_04_backpropagation | 5 |
| chapter_05_optimization | 5 |
| chapter_06_regularization | 5 |
| chapter_07_cnn | 6 |
| chapter_08_rnn_lstm | 6 |
| chapter_09_transformer | 6 |
| chapter_10_generative_models | 4 |
| chapter_11_pytorch_practice | 5 |
| chapter_12_final_project | 7 |
| 未标注 | 106 |

## 3. 每个资源正文长度与质量等级

| ID | 标题 | 类型 | 状态 | 章节 | 正文字数 | 教学质量 |
| --- | --- | --- | --- | --- | ---: | --- |
| KB-DL-CH01 | 第 1 章 深度学习导论与学习诊断 | 课程讲解文档 | archived_shallow | 未标注 | 370 | low |
| KB-DL-CH01-CHAPTER-01-INTRO-EXERCISES-MD | 第 1 章 深度学习导论与学习诊断 章节练习题集 | 练习题集 | 已通过 | chapter_01_intro | 2700 | passed |
| KB-DL-CH01-CHAPTER-01-INTRO-MAIN-NOTE-MD | 第 1 章 深度学习导论与学习诊断：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_01_intro | 3560 | passed |
| KB-DL-CH01-CHAPTER-01-INTRO-MIND-MAP-MMD | 第 1 章 深度学习导论与学习诊断 思维导图 | 知识点思维导图 | 已通过 | chapter_01_intro | 125 | passed |
| KB-DL-CH01-CHAPTER-01-INTRO-READING-VIDEO-GUIDE-MD | 第 1 章 深度学习导论与学习诊断 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_01_intro | 965 | passed |
| KB-DL-CH02 | 第 2 章 数学与机器学习前置知识 | 课程讲解文档 | legacy_demo_only | 未标注 | 1904 | low |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-CODE-LAB-MD | 第 2 章 数学与机器学习前置知识 PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_02_prerequisites | 1574 | passed |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-EXERCISES-MD | 第 2 章 数学与机器学习前置知识 章节练习题集 | 练习题集 | 已通过 | chapter_02_prerequisites | 2730 | passed |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-MAIN-NOTE-MD | 第 2 章 数学与机器学习前置知识：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_02_prerequisites | 3537 | passed |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-MIND-MAP-MMD | 第 2 章 数学与机器学习前置知识 思维导图 | 知识点思维导图 | 已通过 | chapter_02_prerequisites | 120 | passed |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-READING-VIDEO-GUIDE-MD | 第 2 章 数学与机器学习前置知识 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_02_prerequisites | 962 | passed |
| KB-DL-CH03 | 第 3 章 神经网络基础与感知机 | 知识点思维导图 | legacy_demo_only | 未标注 | 272 | curated |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-CODE-LAB-MD | 第 3 章 神经网络基础与感知机 PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_03_neural_network | 1920 | passed |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-EXERCISES-MD | 第 3 章 神经网络基础与感知机 章节练习题集 | 练习题集 | 已通过 | chapter_03_neural_network | 2745 | passed |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-MAIN-NOTE-MD | 第 3 章 神经网络基础与感知机：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_03_neural_network | 3563 | passed |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-MIND-MAP-MMD | 第 3 章 神经网络基础与感知机 思维导图 | 知识点思维导图 | 已通过 | chapter_03_neural_network | 121 | passed |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-READING-VIDEO-GUIDE-MD | 第 3 章 神经网络基础与感知机 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_03_neural_network | 961 | passed |
| KB-DL-CH04 | 第 4 章 反向传播与损失函数 | 交互动画规格 | legacy_demo_only | 未标注 | 1828 | curated |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-EXERCISES-MD | 第 4 章 反向传播 章节练习题集 | 练习题集 | 已通过 | chapter_04_backpropagation | 4170 | passed |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-INTERACTIVE-ANIMATION-JSON | 第 4 章 反向传播 交互动画规格 | 交互动画规格 | 已通过 | chapter_04_backpropagation | 606 | passed |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-MAIN-NOTE-MD | 第 4 章 反向传播：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_04_backpropagation | 4805 | passed |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-MIND-MAP-MMD | 第 4 章 反向传播 思维导图 | 知识点思维导图 | 已通过 | chapter_04_backpropagation | 115 | passed |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-READING-VIDEO-GUIDE-MD | 第 4 章 反向传播 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_04_backpropagation | 955 | passed |
| KB-DL-CH05 | 第 5 章 优化算法与训练技巧 | 拓展阅读包 | merged_into_chapter_pack | 未标注 | 1968 | low |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-CODE-LAB-MD | 第 5 章 优化算法 PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_05_optimization | 2368 | passed |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-EXERCISES-MD | 第 5 章 优化算法 章节练习题集 | 练习题集 | 已通过 | chapter_05_optimization | 4180 | passed |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-MAIN-NOTE-MD | 第 5 章 优化算法：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_05_optimization | 4794 | passed |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-MIND-MAP-MMD | 第 5 章 优化算法 思维导图 | 知识点思维导图 | 已通过 | chapter_05_optimization | 120 | passed |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-READING-VIDEO-GUIDE-MD | 第 5 章 优化算法 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_05_optimization | 961 | passed |
| KB-DL-CH06 | 第 6 章 正则化与泛化 | 课程讲解文档 | legacy_demo_only | 未标注 | 1957 | low |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-CODE-LAB-MD | 第 6 章 正则化与泛化 PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_06_regularization | 2869 | passed |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-EXERCISES-MD | 第 6 章 正则化与泛化 章节练习题集 | 练习题集 | 已通过 | chapter_06_regularization | 4234 | passed |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-MAIN-NOTE-MD | 第 6 章 正则化与泛化：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_06_regularization | 4889 | passed |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-MIND-MAP-MMD | 第 6 章 正则化与泛化 思维导图 | 知识点思维导图 | 已通过 | chapter_06_regularization | 121 | passed |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-READING-VIDEO-GUIDE-MD | 第 6 章 正则化与泛化 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_06_regularization | 966 | passed |
| KB-DL-CH07 | 第 7 章 卷积神经网络 CNN | 交互动画规格 | legacy_demo_only | 未标注 | 1858 | curated |
| KB-DL-CH07-CHAPTER-07-CNN-CODE-LAB-MD | 第 7 章 卷积神经网络 CNN PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_07_cnn | 1956 | passed |
| KB-DL-CH07-CHAPTER-07-CNN-EXERCISES-MD | 第 7 章 卷积神经网络 CNN 章节练习题集 | 练习题集 | 已通过 | chapter_07_cnn | 4033 | passed |
| KB-DL-CH07-CHAPTER-07-CNN-INTERACTIVE-ANIMATION-JSON | 第 7 章 卷积神经网络 CNN 交互动画规格 | 交互动画规格 | 已通过 | chapter_07_cnn | 598 | passed |
| KB-DL-CH07-CHAPTER-07-CNN-MAIN-NOTE-MD | 第 7 章 卷积神经网络 CNN：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_07_cnn | 4795 | passed |
| KB-DL-CH07-CHAPTER-07-CNN-MIND-MAP-MMD | 第 7 章 卷积神经网络 CNN 思维导图 | 知识点思维导图 | 已通过 | chapter_07_cnn | 119 | passed |
| KB-DL-CH07-CHAPTER-07-CNN-READING-VIDEO-GUIDE-MD | 第 7 章 卷积神经网络 CNN 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_07_cnn | 959 | passed |
| KB-DL-CH08 | 第 8 章 RNN/LSTM/GRU 序列建模 | 知识点思维导图 | legacy_demo_only | 未标注 | 2613 | curated |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-CODE-LAB-MD | 第 8 章 RNN/LSTM/GRU 序列建模 PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_08_rnn_lstm | 2576 | passed |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-EXERCISES-MD | 第 8 章 RNN/LSTM/GRU 序列建模 章节练习题集 | 练习题集 | 已通过 | chapter_08_rnn_lstm | 4149 | passed |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-INTERACTIVE-ANIMATION-JSON | 第 8 章 RNN/LSTM/GRU 序列建模 交互动画规格 | 交互动画规格 | 已通过 | chapter_08_rnn_lstm | 614 | passed |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-MAIN-NOTE-MD | 第 8 章 RNN/LSTM/GRU 序列建模：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_08_rnn_lstm | 4879 | passed |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-MIND-MAP-MMD | 第 8 章 RNN/LSTM/GRU 序列建模 思维导图 | 知识点思维导图 | 已通过 | chapter_08_rnn_lstm | 131 | passed |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-READING-VIDEO-GUIDE-MD | 第 8 章 RNN/LSTM/GRU 序列建模 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_08_rnn_lstm | 970 | passed |
| KB-DL-CH09 | 第 9 章 Attention 与 Transformer | 交互动画规格 | legacy_demo_only | 未标注 | 1727 | curated |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-CODE-LAB-MD | 第 9 章 Attention/Transformer PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_09_transformer | 1666 | passed |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-EXERCISES-MD | 第 9 章 Attention/Transformer 章节练习题集 | 练习题集 | 已通过 | chapter_09_transformer | 4638 | passed |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-INTERACTIVE-ANIMATION-JSON | 第 9 章 Attention/Transformer 交互动画规格 | 交互动画规格 | 已通过 | chapter_09_transformer | 624 | passed |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-MAIN-NOTE-MD | 第 9 章 Attention/Transformer：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_09_transformer | 4920 | passed |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-MIND-MAP-MMD | 第 9 章 Attention/Transformer 思维导图 | 知识点思维导图 | 已通过 | chapter_09_transformer | 137 | passed |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-READING-VIDEO-GUIDE-MD | 第 9 章 Attention/Transformer 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_09_transformer | 980 | passed |
| KB-DL-CH10 | 第 10 章 生成模型入门 | 课程讲解文档 | legacy_demo_only | 未标注 | 1648 | low |
| KB-DL-CH10-CHAPTER-10-GENERATIVE-MODELS-EXERCISES-MD | 第 10 章 生成模型 章节练习题集 | 练习题集 | 已通过 | chapter_10_generative_models | 2760 | passed |
| KB-DL-CH10-CHAPTER-10-GENERATIVE-MODELS-MAIN-NOTE-MD | 第 10 章 生成模型：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_10_generative_models | 3495 | passed |
| KB-DL-CH10-CHAPTER-10-GENERATIVE-MODELS-MIND-MAP-MMD | 第 10 章 生成模型 思维导图 | 知识点思维导图 | 已通过 | chapter_10_generative_models | 115 | passed |
| KB-DL-CH10-CHAPTER-10-GENERATIVE-MODELS-READING-VIDEO-GUIDE-MD | 第 10 章 生成模型 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_10_generative_models | 958 | passed |
| KB-DL-CH11 | 第 11 章 PyTorch 深度学习工程实践 | PyTorch 实操案例 | legacy_demo_only | 未标注 | 1892 | low |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-CODE-LAB-MD | 第 11 章 PyTorch 实践 PyTorch 实验 | PyTorch 实操案例 | 已通过 | chapter_11_pytorch_practice | 2361 | passed |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-EXERCISES-MD | 第 11 章 PyTorch 实践 章节练习题集 | 练习题集 | 已通过 | chapter_11_pytorch_practice | 4324 | passed |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-MAIN-NOTE-MD | 第 11 章 PyTorch 实践：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_11_pytorch_practice | 4965 | passed |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-MIND-MAP-MMD | 第 11 章 PyTorch 实践 思维导图 | 知识点思维导图 | 已通过 | chapter_11_pytorch_practice | 132 | passed |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-READING-VIDEO-GUIDE-MD | 第 11 章 PyTorch 实践 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_11_pytorch_practice | 976 | passed |
| KB-DL-CH12 | 第 12 章 深度学习课程综合项目 | 课程实践项目任务书 | legacy_demo_only | 未标注 | 1424 | curated |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-EXERCISES-MD | 第 12 章 课程综合项目 章节练习题集 | 练习题集 | 已通过 | chapter_12_final_project | 3980 | passed |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-MAIN-NOTE-MD | 第 12 章 课程综合项目：教材式主讲义 | 课程讲解文档 | 已通过 | chapter_12_final_project | 4703 | passed |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-MIND-MAP-MMD | 第 12 章 课程综合项目 思维导图 | 知识点思维导图 | 已通过 | chapter_12_final_project | 119 | passed |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-PROJECT-BRIEF-MD | 第 12 章 深度学习课程综合项目任务书 | 课程实践项目任务书 | 已通过 | chapter_12_final_project | 1483 | passed |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-READING-VIDEO-GUIDE-MD | 第 12 章 课程综合项目 阅读与视频学习指南 | 个性化视频观看指南 | 已通过 | chapter_12_final_project | 962 | passed |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-REPORT-TEMPLATE-MD | 课程综合项目报告模板 | 课程实践项目任务书 | 已通过 | chapter_12_final_project | 1426 | passed |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-RUBRIC-MD | 课程综合项目评分 Rubric | 课程实践项目任务书 | 已通过 | chapter_12_final_project | 1389 | passed |
| KB-DL-LAB-CNN-SHAPE | CNN 输出特征图尺寸调试实验 | PyTorch 实操案例 | legacy_demo_only | 未标注 | 766 | low |
| KB-DL-LAB-GRU | GRU 序列分类实验 | PyTorch 实操案例 | legacy_demo_only | 未标注 | 1265 | low |
| KB-DL-LAB-LSTM | LSTM 序列分类实验 | PyTorch 实操案例 | legacy_demo_only | 未标注 | 1367 | low |
| KB-DL-LAB-OPT | SGD Momentum Adam 优化器对比实验 | PyTorch 实操案例 | legacy_demo_only | 未标注 | 1154 | low |
| KB-DL-LAB-REG | Dropout 与 BatchNorm 泛化实验 | PyTorch 实操案例 | legacy_demo_only | 未标注 | 1628 | low |
| KB-DL-UNIT-DL_ACTIVATION_RELU_SIGMOID_TANH | ReLU、Sigmoid 与 Tanh 激活函数 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 624 | low |
| KB-DL-UNIT-DL_ADAM_OPTIMIZER | Adam 优化器 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 553 | low |
| KB-DL-UNIT-DL_ATTENTION_INTRO | 注意力机制入门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 584 | low |
| KB-DL-UNIT-DL_ATTENTION_QKV | Q、K、V 表示 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 588 | low |
| KB-DL-UNIT-DL_AUTOENCODER | 自编码器 AutoEncoder · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 612 | low |
| KB-DL-UNIT-DL_BACKPROP_BASIC | 反向传播基础 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 588 | low |
| KB-DL-UNIT-DL_BATCHNORM | BatchNorm 批归一化 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 601 | low |
| KB-DL-UNIT-DL_BPTT | BPTT 时间反向传播 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 538 | low |
| KB-DL-UNIT-DL_CHAIN_RULE | 链式法则 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 486 | low |
| KB-DL-UNIT-DL_CHAIN_RULE_BACKPROP | 链式法则在反向传播中的应用 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 583 | low |
| KB-DL-UNIT-DL_CNN_CHANNEL_FEATUREMAP | 通道数与特征图 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 555 | low |
| KB-DL-UNIT-DL_CNN_CLASSIC_ARCH | 经典 CNN 架构 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 528 | low |
| KB-DL-UNIT-DL_CNN_CONV_BASIC | CNN 卷积操作基础 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 579 | low |
| KB-DL-UNIT-DL_CNN_IMAGE_CLASSIFICATION_LAB | CNN 图像分类实验 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 603 | low |
| KB-DL-UNIT-DL_CNN_INTRO | 卷积神经网络 CNN 总览 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 550 | low |
| KB-DL-UNIT-DL_CNN_OUTPUT_SIZE | CNN 输出特征图尺寸计算 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 579 | low |
| KB-DL-UNIT-DL_CNN_PADDING_STRIDE | Padding 与 Stride · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 558 | low |
| KB-DL-UNIT-DL_CNN_POOLING | 池化层 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 526 | low |
| KB-DL-UNIT-DL_COMPUTATION_GRAPH | 计算图 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 509 | low |
| KB-DL-UNIT-DL_DATA_AUGMENTATION | 数据增强 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 533 | low |
| KB-DL-UNIT-DL_DIFFUSION_INTRO | 扩散模型入门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 555 | low |
| KB-DL-UNIT-DL_DROPOUT | Dropout 随机失活 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 527 | low |
| KB-DL-UNIT-DL_EARLY_STOPPING | 早停 Early Stopping · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 599 | low |
| KB-DL-UNIT-DL_FORWARD_PROPAGATION | 前向传播 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 527 | low |
| KB-DL-UNIT-DL_GAN_INTRO | GAN 生成对抗网络入门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 574 | low |
| KB-DL-UNIT-DL_GENERATIVE_MODELS_COMPARISON | 生成模型对比 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 636 | low |
| KB-DL-UNIT-DL_GRADIENT_BASIC | 梯度基本概念 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 519 | low |
| KB-DL-UNIT-DL_GRADIENT_DESCENT | 梯度下降 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 528 | low |
| KB-DL-UNIT-DL_GRADIENT_FLOW | 梯度流、梯度消失与梯度爆炸 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 585 | low |
| KB-DL-UNIT-DL_GRADIENT_VANISHING | RNN 梯度消失与长期依赖 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 562 | low |
| KB-DL-UNIT-DL_GRU_BASIC | GRU 门控循环单元 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 567 | low |
| KB-DL-UNIT-DL_INTRO_DIAGNOSIS | 《深度学习》课程导学 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 552 | low |
| KB-DL-UNIT-DL_L2_REGULARIZATION | L2 正则化与权重衰减 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 546 | low |
| KB-DL-UNIT-DL_LEARNING_RATE_SCHEDULE | 学习率与学习率调度 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 557 | low |
| KB-DL-UNIT-DL_LOSS_FUNCTION_BASIC | 损失函数基础 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 569 | low |
| KB-DL-UNIT-DL_LSTM_CELL | LSTM 长短期记忆网络 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 713 | low |
| KB-DL-UNIT-DL_LSTM_CELL_HIDDEN_STATE | LSTM 细胞状态与隐藏状态 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 588 | low |
| KB-DL-UNIT-DL_LSTM_FORGET_GATE | LSTM 遗忘门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 617 | low |
| KB-DL-UNIT-DL_LSTM_INPUT_GATE | LSTM 输入门与候选记忆 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 662 | low |
| KB-DL-UNIT-DL_LSTM_OUTPUT_GATE | LSTM 输出门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 640 | low |
| KB-DL-UNIT-DL_MATRIX_MULTIPLICATION | 矩阵乘法与线性变换 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 539 | low |
| KB-DL-UNIT-DL_MLP | 多层感知机 MLP · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 543 | low |
| KB-DL-UNIT-DL_MOMENTUM | Momentum 动量优化 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 543 | low |
| KB-DL-UNIT-DL_MULTIHEAD_ATTENTION | 多头注意力 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 566 | low |
| KB-DL-UNIT-DL_OVERFITTING | 过拟合与泛化 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 601 | low |
| KB-DL-UNIT-DL_OVERFITTING_UNDERFITTING_INTRO | 过拟合与欠拟合入门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 583 | low |
| KB-DL-UNIT-DL_PARAMETER_UPDATE | 参数更新 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 538 | low |
| KB-DL-UNIT-DL_PERCEPTRON | 感知机与神经元模型 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 499 | low |
| KB-DL-UNIT-DL_POSITIONAL_ENCODING | 位置编码 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 565 | low |
| KB-DL-UNIT-DL_PREREQ_MATH_ML | 数学与机器学习前置知识总览 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 607 | low |
| KB-DL-UNIT-DL_PROJECT_IMAGE_CLASSIFICATION | CNN 图像分类项目 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 699 | low |
| KB-DL-UNIT-DL_PROJECT_REPORT_RUBRIC | 项目报告与评分 Rubric · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 630 | low |
| KB-DL-UNIT-DL_PROJECT_TEXT_CLASSIFICATION | 文本分类项目 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 611 | low |
| KB-DL-UNIT-DL_PROJECT_TIMESERIES_PREDICTION | 时间序列预测项目 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 603 | low |
| KB-DL-UNIT-DL_PYTORCH_DATASET_DATALOADER | Dataset 与 DataLoader · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 683 | low |
| KB-DL-UNIT-DL_PYTORCH_DEBUG_SHAPE | PyTorch Shape 调试 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 629 | low |
| KB-DL-UNIT-DL_PYTORCH_MODEL_EVALUATION | 模型评估与实验记录 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 608 | low |
| KB-DL-UNIT-DL_PYTORCH_NN_MODULE | nn.Module 模型定义 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 607 | low |
| KB-DL-UNIT-DL_PYTORCH_TENSOR | PyTorch Tensor 基础 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 590 | low |
| KB-DL-UNIT-DL_PYTORCH_TRAINING_LOOP | PyTorch 训练循环 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 619 | low |
| KB-DL-UNIT-DL_RNN_BASIC | RNN 循环神经网络基础 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 595 | low |
| KB-DL-UNIT-DL_SCALED_DOT_PRODUCT_ATTENTION | 缩放点积注意力 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 626 | low |
| KB-DL-UNIT-DL_SEQUENCE_CLASSIFICATION_LAB | 序列分类实验 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 638 | low |
| KB-DL-UNIT-DL_SGD | 随机梯度下降 SGD · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 545 | low |
| KB-DL-UNIT-DL_TENSOR_SHAPE | 张量形状与维度表示 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 552 | low |
| KB-DL-UNIT-DL_TRAIN_VAL_TEST_SPLIT | 训练集、验证集与测试集划分 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 562 | low |
| KB-DL-UNIT-DL_TRAINING_CURVE_DIAGNOSIS | 训练曲线诊断 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 563 | low |
| KB-DL-UNIT-DL_TRANSFORMER_ATTENTION_LAB | Transformer 注意力实验 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 641 | low |
| KB-DL-UNIT-DL_TRANSFORMER_DECODER | Transformer Decoder · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 651 | low |
| KB-DL-UNIT-DL_TRANSFORMER_ENCODER | Transformer Encoder · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 656 | low |
| KB-DL-UNIT-DL_VAE_INTRO | VAE 变分自编码器入门 · 初始知识点资源卡 | 课程讲解文档 | merged_into_chapter_pack | 未标注 | 566 | low |
| RES20260626152140347375 | 卷积神经网络中的卷积操作 · 课程讲解文档 | 课程讲解文档 | 已通过 | 未标注 | 1263 | low |
| RES20260626152140349401 | 卷积神经网络中的卷积操作 · 知识点思维导图 | 知识点思维导图 | 已通过 | 未标注 | 484 | curated |
| RES20260626152140351200 | 卷积神经网络中的卷积操作 · 练习题集 | 练习题集 | merged_into_chapter_pack | 未标注 | 1400 | low |
| RES20260626152140353333 | 卷积神经网络中的卷积操作 · 拓展阅读包 | 拓展阅读包 | merged_into_chapter_pack | 未标注 | 1258 | low |
| RES20260626152140355036 | 卷积神经网络中的卷积操作 · PPT 大纲 | PPT 大纲 | 已通过 | 未标注 | 1535 | curated |
| RES20260626152140356804 | 卷积神经网络中的卷积操作 · 个性化视频观看指南 | 个性化视频观看指南 | merged_into_chapter_pack | 未标注 | 2276 | low |
| RES20260626152140358795 | 卷积神经网络中的卷积操作 · PyTorch 实操案例 | PyTorch 实操案例 | 已通过 | 未标注 | 3097 | low |
| RES20260626152140360889 | 卷积神经网络中的卷积操作 · 交互动画规格 | 交互动画规格 | merged_into_chapter_pack | 未标注 | 524 | curated |
| RES20260626152140362226 | 卷积神经网络中的卷积操作 · 动画分镜 | 动画分镜 | merged_into_chapter_pack | 未标注 | 355 | curated |
| RES20260626160954079703 | 卷积神经网络中的卷积操作 · 外部公开视频推荐卡 | 外部公开视频推荐卡 | 已通过 | 未标注 | 2861 | low |
| RES20260626160954092713 | 卷积神经网络中的卷积操作 · 课程实践项目任务书 | 课程实践项目任务书 | 已通过 | 未标注 | 1644 | curated |
| RES20260626164400838118 | 深度学习导论与学习诊断 平台自动诊断报告 | 诊断与补弱报告 | 待审核 | 未标注 | 523 | curated |
| RES20260627143037810003 | RNN、LSTM 与 GRU 序列建模 · 课程讲解文档 | 课程讲解文档 | 已通过 | 未标注 | 4767 | passed |
| RES20260627143037815736 | RNN、LSTM 与 GRU 序列建模 · 练习题集 | 练习题集 | merged_into_chapter_pack | 未标注 | 1708 | passed |
| RES20260627143037819806 | RNN、LSTM 与 GRU 序列建模 · PPT 大纲 | PPT 大纲 | 已通过 | 未标注 | 1901 | passed |
| RES20260627143037823857 | RNN、LSTM 与 GRU 序列建模 · 外部公开视频推荐卡 | 外部公开视频推荐卡 | archived_shallow | 未标注 | 2810 | failed |
| RES20260627143037827692 | RNN、LSTM 与 GRU 序列建模 · 个性化视频观看指南 | 个性化视频观看指南 | merged_into_chapter_pack | 未标注 | 2271 | failed |
| RES20260627143037830636 | RNN、LSTM 与 GRU 序列建模 · PyTorch 实操案例 | PyTorch 实操案例 | 已通过 | 未标注 | 3023 | passed |

## 4. 浅资源列表

| ID | 标题 | 类型 | 章节 | 字数 | 建议 |
| --- | --- | --- | --- | ---: | --- |
| KB-DL-CH01 | 第 1 章 深度学习导论与学习诊断 | 课程讲解文档 | 未标注 | 370 | 合并进章节 courseware 或归档 |
| KB-DL-CH01-CHAPTER-01-INTRO-MIND-MAP-MMD | 第 1 章 深度学习导论与学习诊断 思维导图 | 知识点思维导图 | chapter_01_intro | 125 | 合并进章节 courseware 或归档 |
| KB-DL-CH01-CHAPTER-01-INTRO-READING-VIDEO-GUIDE-MD | 第 1 章 深度学习导论与学习诊断 阅读与视频学习指南 | 个性化视频观看指南 | chapter_01_intro | 965 | 合并进章节 courseware 或归档 |
| KB-DL-CH02 | 第 2 章 数学与机器学习前置知识 | 课程讲解文档 | 未标注 | 1904 | 合并进章节 courseware 或归档 |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-MIND-MAP-MMD | 第 2 章 数学与机器学习前置知识 思维导图 | 知识点思维导图 | chapter_02_prerequisites | 120 | 合并进章节 courseware 或归档 |
| KB-DL-CH02-CHAPTER-02-PREREQUISITES-READING-VIDEO-GUIDE-MD | 第 2 章 数学与机器学习前置知识 阅读与视频学习指南 | 个性化视频观看指南 | chapter_02_prerequisites | 962 | 合并进章节 courseware 或归档 |
| KB-DL-CH03 | 第 3 章 神经网络基础与感知机 | 知识点思维导图 | 未标注 | 272 | 合并进章节 courseware 或归档 |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-MIND-MAP-MMD | 第 3 章 神经网络基础与感知机 思维导图 | 知识点思维导图 | chapter_03_neural_network | 121 | 合并进章节 courseware 或归档 |
| KB-DL-CH03-CHAPTER-03-NEURAL-NETWORK-READING-VIDEO-GUIDE-MD | 第 3 章 神经网络基础与感知机 阅读与视频学习指南 | 个性化视频观看指南 | chapter_03_neural_network | 961 | 合并进章节 courseware 或归档 |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-INTERACTIVE-ANIMATION-JSON | 第 4 章 反向传播 交互动画规格 | 交互动画规格 | chapter_04_backpropagation | 606 | 合并进章节 courseware 或归档 |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-MIND-MAP-MMD | 第 4 章 反向传播 思维导图 | 知识点思维导图 | chapter_04_backpropagation | 115 | 合并进章节 courseware 或归档 |
| KB-DL-CH04-CHAPTER-04-BACKPROPAGATION-READING-VIDEO-GUIDE-MD | 第 4 章 反向传播 阅读与视频学习指南 | 个性化视频观看指南 | chapter_04_backpropagation | 955 | 合并进章节 courseware 或归档 |
| KB-DL-CH05 | 第 5 章 优化算法与训练技巧 | 拓展阅读包 | 未标注 | 1968 | 合并进章节 courseware 或归档 |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-MIND-MAP-MMD | 第 5 章 优化算法 思维导图 | 知识点思维导图 | chapter_05_optimization | 120 | 合并进章节 courseware 或归档 |
| KB-DL-CH05-CHAPTER-05-OPTIMIZATION-READING-VIDEO-GUIDE-MD | 第 5 章 优化算法 阅读与视频学习指南 | 个性化视频观看指南 | chapter_05_optimization | 961 | 合并进章节 courseware 或归档 |
| KB-DL-CH06 | 第 6 章 正则化与泛化 | 课程讲解文档 | 未标注 | 1957 | 合并进章节 courseware 或归档 |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-MIND-MAP-MMD | 第 6 章 正则化与泛化 思维导图 | 知识点思维导图 | chapter_06_regularization | 121 | 合并进章节 courseware 或归档 |
| KB-DL-CH06-CHAPTER-06-REGULARIZATION-READING-VIDEO-GUIDE-MD | 第 6 章 正则化与泛化 阅读与视频学习指南 | 个性化视频观看指南 | chapter_06_regularization | 966 | 合并进章节 courseware 或归档 |
| KB-DL-CH07-CHAPTER-07-CNN-INTERACTIVE-ANIMATION-JSON | 第 7 章 卷积神经网络 CNN 交互动画规格 | 交互动画规格 | chapter_07_cnn | 598 | 合并进章节 courseware 或归档 |
| KB-DL-CH07-CHAPTER-07-CNN-MIND-MAP-MMD | 第 7 章 卷积神经网络 CNN 思维导图 | 知识点思维导图 | chapter_07_cnn | 119 | 合并进章节 courseware 或归档 |
| KB-DL-CH07-CHAPTER-07-CNN-READING-VIDEO-GUIDE-MD | 第 7 章 卷积神经网络 CNN 阅读与视频学习指南 | 个性化视频观看指南 | chapter_07_cnn | 959 | 合并进章节 courseware 或归档 |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-INTERACTIVE-ANIMATION-JSON | 第 8 章 RNN/LSTM/GRU 序列建模 交互动画规格 | 交互动画规格 | chapter_08_rnn_lstm | 614 | 合并进章节 courseware 或归档 |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-MIND-MAP-MMD | 第 8 章 RNN/LSTM/GRU 序列建模 思维导图 | 知识点思维导图 | chapter_08_rnn_lstm | 131 | 合并进章节 courseware 或归档 |
| KB-DL-CH08-CHAPTER-08-RNN-LSTM-GRU-READING-VIDEO-GUIDE-MD | 第 8 章 RNN/LSTM/GRU 序列建模 阅读与视频学习指南 | 个性化视频观看指南 | chapter_08_rnn_lstm | 970 | 合并进章节 courseware 或归档 |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-INTERACTIVE-ANIMATION-JSON | 第 9 章 Attention/Transformer 交互动画规格 | 交互动画规格 | chapter_09_transformer | 624 | 合并进章节 courseware 或归档 |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-MIND-MAP-MMD | 第 9 章 Attention/Transformer 思维导图 | 知识点思维导图 | chapter_09_transformer | 137 | 合并进章节 courseware 或归档 |
| KB-DL-CH09-CHAPTER-09-TRANSFORMER-READING-VIDEO-GUIDE-MD | 第 9 章 Attention/Transformer 阅读与视频学习指南 | 个性化视频观看指南 | chapter_09_transformer | 980 | 合并进章节 courseware 或归档 |
| KB-DL-CH10 | 第 10 章 生成模型入门 | 课程讲解文档 | 未标注 | 1648 | 合并进章节 courseware 或归档 |
| KB-DL-CH10-CHAPTER-10-GENERATIVE-MODELS-MIND-MAP-MMD | 第 10 章 生成模型 思维导图 | 知识点思维导图 | chapter_10_generative_models | 115 | 合并进章节 courseware 或归档 |
| KB-DL-CH10-CHAPTER-10-GENERATIVE-MODELS-READING-VIDEO-GUIDE-MD | 第 10 章 生成模型 阅读与视频学习指南 | 个性化视频观看指南 | chapter_10_generative_models | 958 | 合并进章节 courseware 或归档 |
| KB-DL-CH11 | 第 11 章 PyTorch 深度学习工程实践 | PyTorch 实操案例 | 未标注 | 1892 | 合并进章节 courseware 或归档 |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-MIND-MAP-MMD | 第 11 章 PyTorch 实践 思维导图 | 知识点思维导图 | chapter_11_pytorch_practice | 132 | 合并进章节 courseware 或归档 |
| KB-DL-CH11-CHAPTER-11-PYTORCH-PRACTICE-READING-VIDEO-GUIDE-MD | 第 11 章 PyTorch 实践 阅读与视频学习指南 | 个性化视频观看指南 | chapter_11_pytorch_practice | 976 | 合并进章节 courseware 或归档 |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-MIND-MAP-MMD | 第 12 章 课程综合项目 思维导图 | 知识点思维导图 | chapter_12_final_project | 119 | 合并进章节 courseware 或归档 |
| KB-DL-CH12-CHAPTER-12-FINAL-PROJECT-READING-VIDEO-GUIDE-MD | 第 12 章 课程综合项目 阅读与视频学习指南 | 个性化视频观看指南 | chapter_12_final_project | 962 | 合并进章节 courseware 或归档 |
| KB-DL-LAB-CNN-SHAPE | CNN 输出特征图尺寸调试实验 | PyTorch 实操案例 | 未标注 | 766 | 合并进章节 courseware 或归档 |
| KB-DL-LAB-GRU | GRU 序列分类实验 | PyTorch 实操案例 | 未标注 | 1265 | 合并进章节 courseware 或归档 |
| KB-DL-LAB-LSTM | LSTM 序列分类实验 | PyTorch 实操案例 | 未标注 | 1367 | 合并进章节 courseware 或归档 |
| KB-DL-LAB-OPT | SGD Momentum Adam 优化器对比实验 | PyTorch 实操案例 | 未标注 | 1154 | 合并进章节 courseware 或归档 |
| KB-DL-LAB-REG | Dropout 与 BatchNorm 泛化实验 | PyTorch 实操案例 | 未标注 | 1628 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_ACTIVATION_RELU_SIGMOID_TANH | ReLU、Sigmoid 与 Tanh 激活函数 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 624 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_ADAM_OPTIMIZER | Adam 优化器 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 553 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_ATTENTION_INTRO | 注意力机制入门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 584 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_ATTENTION_QKV | Q、K、V 表示 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 588 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_AUTOENCODER | 自编码器 AutoEncoder · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 612 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_BACKPROP_BASIC | 反向传播基础 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 588 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_BATCHNORM | BatchNorm 批归一化 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 601 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_BPTT | BPTT 时间反向传播 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 538 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CHAIN_RULE | 链式法则 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 486 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CHAIN_RULE_BACKPROP | 链式法则在反向传播中的应用 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 583 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_CHANNEL_FEATUREMAP | 通道数与特征图 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 555 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_CLASSIC_ARCH | 经典 CNN 架构 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 528 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_CONV_BASIC | CNN 卷积操作基础 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 579 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_IMAGE_CLASSIFICATION_LAB | CNN 图像分类实验 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 603 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_INTRO | 卷积神经网络 CNN 总览 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 550 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_OUTPUT_SIZE | CNN 输出特征图尺寸计算 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 579 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_PADDING_STRIDE | Padding 与 Stride · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 558 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_CNN_POOLING | 池化层 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 526 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_COMPUTATION_GRAPH | 计算图 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 509 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_DATA_AUGMENTATION | 数据增强 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 533 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_DIFFUSION_INTRO | 扩散模型入门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 555 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_DROPOUT | Dropout 随机失活 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 527 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_EARLY_STOPPING | 早停 Early Stopping · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 599 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_FORWARD_PROPAGATION | 前向传播 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 527 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GAN_INTRO | GAN 生成对抗网络入门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 574 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GENERATIVE_MODELS_COMPARISON | 生成模型对比 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 636 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GRADIENT_BASIC | 梯度基本概念 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 519 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GRADIENT_DESCENT | 梯度下降 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 528 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GRADIENT_FLOW | 梯度流、梯度消失与梯度爆炸 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 585 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GRADIENT_VANISHING | RNN 梯度消失与长期依赖 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 562 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_GRU_BASIC | GRU 门控循环单元 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 567 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_INTRO_DIAGNOSIS | 《深度学习》课程导学 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 552 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_L2_REGULARIZATION | L2 正则化与权重衰减 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 546 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LEARNING_RATE_SCHEDULE | 学习率与学习率调度 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 557 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LOSS_FUNCTION_BASIC | 损失函数基础 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 569 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LSTM_CELL | LSTM 长短期记忆网络 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 713 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LSTM_CELL_HIDDEN_STATE | LSTM 细胞状态与隐藏状态 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 588 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LSTM_FORGET_GATE | LSTM 遗忘门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 617 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LSTM_INPUT_GATE | LSTM 输入门与候选记忆 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 662 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_LSTM_OUTPUT_GATE | LSTM 输出门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 640 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_MATRIX_MULTIPLICATION | 矩阵乘法与线性变换 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 539 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_MLP | 多层感知机 MLP · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 543 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_MOMENTUM | Momentum 动量优化 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 543 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_MULTIHEAD_ATTENTION | 多头注意力 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 566 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_OVERFITTING | 过拟合与泛化 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 601 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_OVERFITTING_UNDERFITTING_INTRO | 过拟合与欠拟合入门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 583 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PARAMETER_UPDATE | 参数更新 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 538 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PERCEPTRON | 感知机与神经元模型 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 499 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_POSITIONAL_ENCODING | 位置编码 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 565 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PREREQ_MATH_ML | 数学与机器学习前置知识总览 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 607 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PROJECT_IMAGE_CLASSIFICATION | CNN 图像分类项目 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 699 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PROJECT_REPORT_RUBRIC | 项目报告与评分 Rubric · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 630 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PROJECT_TEXT_CLASSIFICATION | 文本分类项目 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 611 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PROJECT_TIMESERIES_PREDICTION | 时间序列预测项目 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 603 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PYTORCH_DATASET_DATALOADER | Dataset 与 DataLoader · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 683 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PYTORCH_DEBUG_SHAPE | PyTorch Shape 调试 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 629 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PYTORCH_MODEL_EVALUATION | 模型评估与实验记录 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 608 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PYTORCH_NN_MODULE | nn.Module 模型定义 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 607 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PYTORCH_TENSOR | PyTorch Tensor 基础 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 590 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_PYTORCH_TRAINING_LOOP | PyTorch 训练循环 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 619 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_RNN_BASIC | RNN 循环神经网络基础 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 595 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_SCALED_DOT_PRODUCT_ATTENTION | 缩放点积注意力 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 626 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_SEQUENCE_CLASSIFICATION_LAB | 序列分类实验 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 638 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_SGD | 随机梯度下降 SGD · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 545 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_TENSOR_SHAPE | 张量形状与维度表示 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 552 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_TRAIN_VAL_TEST_SPLIT | 训练集、验证集与测试集划分 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 562 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_TRAINING_CURVE_DIAGNOSIS | 训练曲线诊断 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 563 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_TRANSFORMER_ATTENTION_LAB | Transformer 注意力实验 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 641 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_TRANSFORMER_DECODER | Transformer Decoder · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 651 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_TRANSFORMER_ENCODER | Transformer Encoder · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 656 | 合并进章节 courseware 或归档 |
| KB-DL-UNIT-DL_VAE_INTRO | VAE 变分自编码器入门 · 初始知识点资源卡 | 课程讲解文档 | 未标注 | 566 | 合并进章节 courseware 或归档 |
| RES20260626152140347375 | 卷积神经网络中的卷积操作 · 课程讲解文档 | 课程讲解文档 | 未标注 | 1263 | 合并进章节 courseware 或归档 |
| RES20260626152140349401 | 卷积神经网络中的卷积操作 · 知识点思维导图 | 知识点思维导图 | 未标注 | 484 | 合并进章节 courseware 或归档 |
| RES20260626152140351200 | 卷积神经网络中的卷积操作 · 练习题集 | 练习题集 | 未标注 | 1400 | 合并进章节 courseware 或归档 |
| RES20260626152140353333 | 卷积神经网络中的卷积操作 · 拓展阅读包 | 拓展阅读包 | 未标注 | 1258 | 合并进章节 courseware 或归档 |
| RES20260626152140356804 | 卷积神经网络中的卷积操作 · 个性化视频观看指南 | 个性化视频观看指南 | 未标注 | 2276 | 合并进章节 courseware 或归档 |
| RES20260626152140358795 | 卷积神经网络中的卷积操作 · PyTorch 实操案例 | PyTorch 实操案例 | 未标注 | 3097 | 合并进章节 courseware 或归档 |
| RES20260626152140360889 | 卷积神经网络中的卷积操作 · 交互动画规格 | 交互动画规格 | 未标注 | 524 | 合并进章节 courseware 或归档 |
| RES20260626152140362226 | 卷积神经网络中的卷积操作 · 动画分镜 | 动画分镜 | 未标注 | 355 | 合并进章节 courseware 或归档 |
| RES20260626160954079703 | 卷积神经网络中的卷积操作 · 外部公开视频推荐卡 | 外部公开视频推荐卡 | 未标注 | 2861 | 合并进章节 courseware 或归档 |
| RES20260626164400838118 | 深度学习导论与学习诊断 平台自动诊断报告 | 诊断与补弱报告 | 未标注 | 523 | 合并进章节 courseware 或归档 |
| RES20260627143037823857 | RNN、LSTM 与 GRU 序列建模 · 外部公开视频推荐卡 | 外部公开视频推荐卡 | 未标注 | 2810 | 合并进章节 courseware 或归档 |
| RES20260627143037827692 | RNN、LSTM 与 GRU 序列建模 · 个性化视频观看指南 | 个性化视频观看指南 | 未标注 | 2271 | 合并进章节 courseware 或归档 |

## 5. 重复资源列表

- 未发现完全同名同类型重复资源。

## 6. 建议合并的资源列表

- `KB-DL-UNIT-*` 初始知识点资源卡：合并为章节主讲义、章节练习题集或阅读指南。
- 少于 1200 字的讲义、只有链接的阅读材料、只有几行说明的动画分镜：归档为 `archived_shallow` 或 `merged_into_chapter_pack`。

## 7. 每章缺失资源类型

- 第 1 章 深度学习导论与学习诊断：无
- 第 2 章 数学与机器学习前置知识：无
- 第 3 章 神经网络基础与感知机：无
- 第 4 章 反向传播：无
- 第 5 章 优化算法：无
- 第 6 章 正则化与泛化：无
- 第 7 章 卷积神经网络 CNN：无
- 第 8 章 RNN/LSTM/GRU 序列建模：无
- 第 9 章 Attention/Transformer：无
- 第 10 章 生成模型：无
- 第 11 章 PyTorch 实践：无
- 第 12 章 课程综合项目：无

## 8. 学生端不应展示的内部字段

- 资源编码 / resource_id / artifact_id
- 数据库 ID、审核状态、status
- 生成 Agent 内部名、agent_trace_id、agent_notes
- 推荐分数、命中标签、内部质量原始 JSON
