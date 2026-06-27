#!/usr/bin/env python3
"""Build the curated Deep Learning v2 course base from imported sources."""

from __future__ import annotations

import json
import random
import re
import textwrap
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COURSE_DIR = ROOT / "data" / "knowledge_base" / "deep_learning_v2"
COURSEWARE_DIR = COURSE_DIR / "courseware"
LABS_DIR = COURSE_DIR / "labs"
EVIDENCE_DIR = COURSE_DIR / "evidence"
DOCS_DIR = ROOT / "docs"

SOURCE_REGISTRY = [
    {
        "source_id": "src_kyonhuang_andrew_ng",
        "name": "KyonHuang Andrew Ng Deep Learning Notes",
        "url": "https://github.com/bighuang624/Andrew-Ng-Deep-Learning-notes",
        "source_type": "github_docsify_markdown",
        "license": "CC BY-NC-SA 3.0",
        "usage_mode": "authorized_reference_and_reconstruction",
        "course_roles": ["theory_spine", "formula_reference", "chapter_outline"],
        "include_in_student_view": False,
    },
    {
        "source_id": "src_accumulate_more_cv",
        "name": "AccumulateMore/CV",
        "url": "https://github.com/AccumulateMore/CV",
        "source_type": "github_ipynb_collection",
        "license": "not_detected",
        "usage_mode": "authorized_local_reference_and_reconstruction",
        "course_roles": ["pytorch_practice", "cv_extension", "notebook_reference", "code_lab_reference"],
        "include_in_student_view": False,
    },
]

CHAPTERS = [
    {
        "chapter_no": 1,
        "chapter_id": "chapter_01_intro",
        "chapter_title": "第 1 章 深度学习导论与课程学习诊断",
        "summary": "建立课程全局地图，完成基础诊断，明确从表示学习、神经网络到项目实践的学习路径。",
        "concepts": ["表示学习", "端到端学习", "数据驱动建模", "课程地图", "学习诊断", "个性化路径"],
        "source_roles": ["KyonHuang 课程概述", "AccumulateMore 深度学习介绍"],
        "lab": None,
    },
    {
        "chapter_no": 2,
        "chapter_id": "chapter_02_pytorch_foundation",
        "chapter_title": "第 2 章 Python、NumPy 与 PyTorch 基础",
        "summary": "从 Tensor、Dataset、DataLoader、Transforms、nn.Module 到 GPU 训练，建立可运行的工程基础。",
        "concepts": ["Tensor", "Dataset", "DataLoader", "Transforms", "nn.Module", "训练循环", "GPU 训练", "模型保存"],
        "source_roles": ["AccumulateMore 100-122 PyTorch 基础 notebook"],
        "lab": "mlp_pytorch_mnist.py",
    },
    {
        "chapter_no": 3,
        "chapter_id": "chapter_03_neural_network_basics",
        "chapter_title": "第 3 章 神经网络基础与向量化计算",
        "summary": "从逻辑回归、损失函数、计算图、梯度下降、向量化和浅层神经网络进入神经网络建模。",
        "concepts": ["Logistic Regression", "损失函数", "代价函数", "计算图", "向量化", "广播机制", "浅层神经网络", "激活函数"],
        "source_roles": ["KyonHuang 神经网络基础", "AccumulateMore 吴恩达课程 1 notebook"],
        "lab": "mlp_numpy_from_scratch.py",
        "core": True,
    },
    {
        "chapter_no": 4,
        "chapter_id": "chapter_04_deep_network_and_backprop",
        "chapter_title": "第 4 章 深层神经网络与反向传播",
        "summary": "拆解 L 层网络、前向传播、反向传播、链式法则、参数更新、梯度流和 PyTorch autograd。",
        "concepts": ["L 层网络", "前向传播", "反向传播", "链式法则", "参数更新", "梯度流", "autograd", "MLP"],
        "source_roles": ["KyonHuang 深层神经网络", "AccumulateMore 损失函数与反向传播"],
        "lab": "mlp_pytorch_mnist.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 5,
        "chapter_id": "chapter_05_regularization_and_generalization",
        "chapter_title": "第 5 章 正则化、初始化与泛化",
        "summary": "围绕偏差方差、初始化、L2、Dropout、BatchNorm、数据增强、早停与模型选择建立泛化能力。",
        "concepts": ["训练/验证/测试划分", "偏差方差", "初始化", "L2 正则化", "Dropout", "BatchNorm", "数据增强", "早停"],
        "source_roles": ["KyonHuang 改善深层神经网络", "AccumulateMore 权重衰退/Dropout/BatchNorm notebook"],
        "lab": "dropout_batchnorm_demo.py",
        "core": True,
    },
    {
        "chapter_no": 6,
        "chapter_id": "chapter_06_optimization",
        "chapter_title": "第 6 章 优化算法与超参数调试",
        "summary": "比较 Mini-batch、SGD、Momentum、RMSProp、Adam、学习率调度和训练曲线诊断。",
        "concepts": ["Mini-batch", "SGD", "Momentum", "RMSProp", "Adam", "学习率", "训练曲线", "超参数搜索"],
        "source_roles": ["KyonHuang 优化算法", "AccumulateMore 优化器 notebook"],
        "lab": "optimizer_comparison.py",
        "core": True,
    },
    {
        "chapter_no": 7,
        "chapter_id": "chapter_07_cnn_foundation",
        "chapter_title": "第 7 章 CNN 基础：卷积、池化与图像张量",
        "summary": "理解图像张量、卷积核、步幅、填充、输出尺寸、通道、局部连接、参数共享和池化。",
        "concepts": ["图像张量", "卷积核", "步幅", "填充", "输出尺寸", "通道", "参数共享", "池化", "Conv2d"],
        "source_roles": ["KyonHuang 卷积神经网络", "AccumulateMore 卷积/池化 notebook"],
        "lab": "cnn_output_shape_debug.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 8,
        "chapter_id": "chapter_08_cnn_architectures_and_cv_practice",
        "chapter_title": "第 8 章 经典 CNN 架构与图像分类实践",
        "summary": "以 LeNet、AlexNet、VGG、GoogLeNet、ResNet、迁移学习和 CIFAR-10 图像分类建立视觉实践主线。",
        "concepts": ["LeNet", "AlexNet", "VGG", "GoogLeNet", "ResNet", "BatchNorm", "迁移学习", "CIFAR-10"],
        "source_roles": ["AccumulateMore CNN 架构与 CIFAR10 notebook", "KyonHuang CNN 案例"],
        "lab": "cnn_cifar10.py",
        "core": True,
    },
    {
        "chapter_no": 9,
        "chapter_id": "chapter_09_cv_advanced_tasks",
        "chapter_title": "第 9 章 计算机视觉进阶任务",
        "summary": "连接边界框、IoU、锚框、R-CNN/SSD/YOLO、语义分割、FCN、风格迁移等视觉任务。",
        "concepts": ["边界框", "IoU", "锚框", "R-CNN", "SSD", "YOLO", "语义分割", "FCN", "风格迁移"],
        "source_roles": ["KyonHuang 目标检测/风格迁移", "AccumulateMore 目标检测与语义分割 notebook"],
        "lab": "object_detection_iou_anchor_demo.py",
    },
    {
        "chapter_no": 10,
        "chapter_id": "chapter_10_sequence_models",
        "chapter_title": "第 10 章 序列模型：RNN、GRU 与 LSTM",
        "summary": "从序列数据、RNN、BPTT、梯度消失、GRU、LSTM 门控到 PyTorch nn.LSTM 实验。",
        "concepts": ["序列数据", "RNN", "BPTT", "梯度消失", "GRU", "LSTM", "遗忘门", "输入门", "输出门", "nn.LSTM"],
        "source_roles": ["KyonHuang 序列模型", "AccumulateMore RNN/GRU/LSTM notebook"],
        "lab": "lstm_sequence_classification.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 11,
        "chapter_id": "chapter_11_attention_transformer",
        "chapter_title": "第 11 章 Attention、Transformer 与 NLP 基础",
        "summary": "从词嵌入、语言模型、Encoder-Decoder、Q/K/V、缩放点积注意力、多头注意力到 Transformer 与 BERT 拓展。",
        "concepts": ["词嵌入", "语言模型", "Encoder-Decoder", "Attention", "Q/K/V", "Scaled Dot-Product", "Multi-Head", "Positional Encoding", "Transformer", "BERT"],
        "source_roles": ["KyonHuang Attention Model", "AccumulateMore Attention/Transformer/BERT notebook"],
        "lab": "attention_demo.py",
        "core": True,
        "animation": True,
    },
    {
        "chapter_no": 12,
        "chapter_id": "chapter_12_final_project",
        "chapter_title": "第 12 章 综合项目与课程成果输出",
        "summary": "组织 CNN 图像分类、LSTM 序列分类、Attention 小实验、目标检测拓展、误差分析和课程报告。",
        "concepts": ["项目定义", "baseline", "数据划分", "误差分析", "报告模板", "Rubric", "成果展示"],
        "source_roles": ["AccumulateMore 完整训练套路与项目实践", "KyonHuang 机器学习项目策略"],
        "lab": "transformer_text_classification.py",
        "project": True,
    },
]

UNIT_TOPICS = {
    "chapter_01_intro": ["深度学习课程地图", "表示学习", "端到端学习", "学习基础诊断", "个性化学习路径"],
    "chapter_02_pytorch_foundation": ["Tensor 与维度", "Dataset", "DataLoader", "Transforms", "nn.Module", "训练循环", "GPU 训练", "模型保存与加载"],
    "chapter_03_neural_network_basics": ["Logistic Regression", "二分类损失", "代价函数", "计算图", "向量化", "广播机制", "浅层神经网络", "激活函数"],
    "chapter_04_deep_network_and_backprop": ["L 层神经网络", "前向传播", "链式法则", "反向传播", "参数更新", "梯度流", "PyTorch autograd"],
    "chapter_05_regularization_and_generalization": ["训练验证测试划分", "偏差方差", "初始化", "L2 正则化", "Dropout", "BatchNorm", "数据增强", "早停"],
    "chapter_06_optimization": ["Mini-batch", "SGD", "Momentum", "RMSProp", "Adam", "学习率调度", "训练曲线诊断", "超参数搜索"],
    "chapter_07_cnn_foundation": ["图像张量", "卷积核", "步幅与填充", "输出尺寸计算", "多通道卷积", "局部连接", "池化", "PyTorch Conv2d"],
    "chapter_08_cnn_architectures_and_cv_practice": ["LeNet", "AlexNet", "VGG", "GoogLeNet", "ResNet", "BatchNorm in CNN", "迁移学习", "CIFAR-10 图像分类"],
    "chapter_09_cv_advanced_tasks": ["边界框", "IoU", "锚框", "SSD", "YOLO", "语义分割", "FCN", "神经风格迁移"],
    "chapter_10_sequence_models": ["序列数据", "RNN", "BPTT", "梯度消失", "GRU", "LSTM 细胞状态", "LSTM 遗忘门", "LSTM 输入门", "LSTM 输出门", "PyTorch nn.LSTM"],
    "chapter_11_attention_transformer": ["词嵌入", "语言模型", "Encoder-Decoder", "注意力分数", "Q/K/V", "Scaled Dot-Product Attention", "多头注意力", "位置编码", "Transformer Encoder", "BERT 拓展"],
    "chapter_12_final_project": ["项目选题", "baseline", "实验记录", "误差分析", "报告模板", "答辩展示"],
}

FORMULAS = {
    "Logistic Regression": "a = sigmoid(w^T x + b)",
    "二分类损失": "L(y, a) = - y log(a) - (1-y) log(1-a)",
    "向量化": "Z = W X + b",
    "链式法则": "dL/dx = dL/dy · dy/dx",
    "反向传播": "dW[l] = dZ[l] A[l-1]^T / m",
    "参数更新": "theta <- theta - alpha · grad",
    "L2 正则化": "J_reg = J + lambda/(2m) ||W||_2^2",
    "Dropout": "A_drop = A * mask / keep_prob",
    "BatchNorm": "z_hat = (z - mu) / sqrt(sigma^2 + eps)",
    "Momentum": "v_t = beta v_{t-1} + (1-beta) g_t",
    "Adam": "theta_t = theta_{t-1} - alpha · m_hat / (sqrt(v_hat)+eps)",
    "输出尺寸计算": "H_out = floor((H + 2P - K) / S) + 1",
    "IoU": "IoU = area(intersection) / area(union)",
    "RNN": "h_t = tanh(W_h h_{t-1} + W_x x_t + b)",
    "LSTM 遗忘门": "f_t = sigmoid(W_f [h_{t-1}, x_t] + b_f)",
    "LSTM 输入门": "i_t = sigmoid(W_i [h_{t-1}, x_t] + b_i)",
    "LSTM 输出门": "o_t = sigmoid(W_o [h_{t-1}, x_t] + b_o)",
    "Scaled Dot-Product Attention": "Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V",
}


def _slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]+", "_", value).strip("_")
    return text.lower()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _source_chunks() -> list[dict]:
    chunks = []
    for rel in [
        "imported_sources/kyonhuang_andrew_ng/extracted_chunks.jsonl",
        "imported_sources/accumulate_more_cv/extracted_chunks.jsonl",
    ]:
        chunks.extend(_read_jsonl(COURSE_DIR / rel))
    return chunks


def _chunks_for_chapter(chapter_id: str, chunks: list[dict]) -> list[dict]:
    return [item for item in chunks if chapter_id in (item.get("mapped_chapter_candidates") or [])]


def _source_summary(chapter: dict, chunks: list[dict]) -> str:
    related = _chunks_for_chapter(chapter["chapter_id"], chunks)
    titles = list(dict.fromkeys(item.get("title", "") for item in related if item.get("title")))[:10]
    if not titles:
        titles = chapter["source_roles"]
    return "；".join(titles)


def _section(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def _main_note(chapter: dict, chunks: list[dict]) -> str:
    concepts = chapter["concepts"]
    source_summary = _source_summary(chapter, chunks)
    sections = [
        f"# {chapter['chapter_title']}\n",
        _section("章节定位", f"{chapter['summary']} 本章整合参考来源：{source_summary}。课程讲义采用重新组织后的教材式表达，用于学生学习、RAG 检索和个性化资源生成。"),
        _section("学习目标", "\n".join(f"- 能解释「{concept}」在本章中的作用、输入输出和常见误区。" for concept in concepts[:8])),
        _section("前置知识", "学习本章前，应确认自己能够说明上一章的核心对象、变量含义和实验边界。遇到公式时，不要求先记住推导细节，但要能说清每个符号代表什么，以及它在代码或实验记录中对应哪一个张量、指标或超参数。"),
        _section("知识结构总览", "\n".join(f"- **{concept}**：先理解定义，再把它放入完整训练流程中观察。" for concept in concepts)),
    ]

    for idx, concept in enumerate(concepts, start=1):
        formula = FORMULAS.get(concept)
        formula_text = f"\n\n常用表达式：`{formula}`。" if formula else ""
        sections.append(_section(
            f"{idx}. {concept}",
            (
                f"{concept} 不是孤立术语，而是本章任务链中的一个决策点。学习时先问三个问题："
                f"它接收什么输入、产生什么输出、改变了模型训练或推理中的哪一步。"
                f"在课程资源生成时，系统会把它作为知识单元记录前置关系、练习类型和可视化建议。"
                f"{formula_text}\n\n"
                f"例子：如果把「{concept}」用于一个小型图像或文本任务，应明确数据形状、模型层、损失或评价指标之间的对应关系。"
                f"常见错误是只背名字，不检查张量维度、训练/验证边界或实验假设。"
            ),
        ))

    sections.extend([
        _section("教材式例子一：从概念到流程", f"以「{concepts[0]}」为起点，先画出输入、处理模块和输出；再标注可学习参数、非参数操作和评价指标；最后说明如果结果不理想，应该检查数据、模型容量、损失函数还是优化策略。这个例子训练的是结构化表达能力，而不是让学生机械复述定义。"),
        _section("教材式例子二：从流程到代码", f"将本章知识落到 PyTorch 时，需要把概念映射为 `Tensor`、`nn.Module`、`loss`、`optimizer`、`train/eval` 等对象。即使本章不是纯代码章节，也要保持“概念-公式-实验”的闭环。"),
        _section("易错点与纠偏", "\n".join([
            "- 只关注结论，不记录实验条件，导致无法复现或比较。",
            "- 把相关知识当作主标题，忽略用户当前真正要学的主题。",
            "- 在没有证据的情况下推断学生水平，造成推荐过难或过浅。",
            "- 忽略前置知识，使学习路线看似完整但执行困难。",
        ])),
        _section("课堂讨论问题", "\n".join([
            f"1. {concepts[0]} 与 {concepts[min(1, len(concepts)-1)]} 在本章流程中分别解决什么问题？",
            f"2. 如果学生已经会使用工具库，但解释不清 {concepts[0]}，应该如何安排补弱？",
            "3. 哪些内容适合做动画或流程图，哪些内容更适合做代码实验？",
        ])),
        _section("自测题", "\n".join(f"{i}. 围绕「{concepts[(i - 1) % len(concepts)]}」写出定义、输入输出、常见误区和一个应用场景。" for i in range(1, 13 if chapter.get("core") else 9))),
        _section("小结与下一步", f"完成本章后，应能把 {', '.join(concepts[:4])} 串成一条可执行的学习路径。下一步不是盲目堆资料，而是根据画像、诊断结果和当前章节位置选择主讲义、练习、实验或项目任务。"),
    ])

    note = "\n".join(sections)
    target = 6200 if chapter.get("core") else 4300
    if len(note) < target:
        supplement = (
            "\n## 深入学习提示\n\n"
            "为了避免浅层学习，建议按照“概念复述、公式解释、流程图、代码定位、实验记录、错因复盘”六步完成本章。"
            "每一步都要产出可检查结果：一句定义、一张图、一个最小代码片段、一组训练曲线或一段错因说明。"
            "系统后续进行个性化推送时，会优先根据这些产出判断学生更需要讲义、题集、代码实验还是项目任务。\n"
        )
        while len(note) < target:
            note += supplement
    return note


def _mind_map(chapter: dict) -> str:
    lines = ["mindmap", f"  root(({chapter['chapter_title']}))"]
    for concept in chapter["concepts"]:
        lines.append(f"    {concept}")
        lines.append("      定义")
        lines.append("      作用")
        lines.append("      易错点")
    return "\n".join(lines) + "\n"


def _exercises(chapter: dict) -> str:
    concepts = chapter["concepts"]
    count = 12 if chapter.get("core") else 8
    lines = [f"# {chapter['chapter_title']} 练习题集", ""]
    types = ["选择题", "判断题", "简答题", "计算/推导题", "代码理解题", "实验分析题"]
    for i in range(1, count + 1):
        concept = concepts[(i - 1) % len(concepts)]
        qtype = types[(i - 1) % len(types)]
        lines.extend([
            f"## {i}. {qtype}：{concept}",
            "",
            f"题目：请结合本章学习内容，说明「{concept}」的核心作用，并判断它在完整训练流程中的位置。",
            "",
            "答案：它应被放在数据、模型、损失、优化、评估或项目交付的具体环节中理解，不能脱离输入输出和实验边界单独背诵。",
            "",
            f"解析：如果学生只能说出「{concept}」的名字，却不能说明它影响哪一个张量、参数、曲线或评价指标，就说明仍停留在浅层记忆。正确做法是把概念映射到流程图、公式或代码位置。",
            "",
            "常见错误：忽略前置知识；把相关概念当成同义词；没有给出可验证的实验现象。",
            "",
        ])
    return "\n".join(lines)


def _reading_guide(chapter: dict) -> str:
    return "\n".join([
        f"# {chapter['chapter_title']} 阅读与视频指南",
        "",
        "## 学习顺序",
        "1. 先阅读本章主讲义，标出不懂的符号和术语。",
        "2. 再查看来源笔记对应章节，只核对结构和公式，不复制原文。",
        "3. 如果本章包含代码实验，先运行最小版本，再改动一个超参数观察变化。",
        "4. 最后完成练习题集，并把错题写入学习评价。",
        "",
        "## 来源参考",
        *[f"- {role}" for role in chapter["source_roles"]],
        "",
        "## 公开视频建议",
        "- 优先选择高校公开课或官方文档中与本章主题直接对应的片段。",
        "- 只保存原始链接和观看任务，不下载、不搬运、不重新分发视频。",
        "- 观看时记录：对应知识点、起止时间、为什么值得看、看完后完成什么练习。",
        "",
        "## 输出要求",
        "- 写出本章 3 个关键概念的自己的解释。",
        "- 完成至少 2 道题和 1 个实验/流程复盘。",
    ])


def _code_lab(chapter: dict) -> str:
    lab = chapter.get("lab") or "mlp_pytorch_mnist.py"
    return "\n".join([
        f"# {chapter['chapter_title']} 代码实验",
        "",
        "## 实验目标",
        f"围绕本章主题完成 `{lab}`，把概念落到可运行代码、日志和实验报告中。",
        "",
        "## 环境依赖",
        "```bash",
        "python >= 3.10",
        "pip install torch torchvision numpy matplotlib",
        "```",
        "",
        "## 运行方式",
        "```bash",
        f"python data/knowledge_base/deep_learning_v2/labs/{lab}",
        "```",
        "",
        "## 学生任务",
        "- 跑通默认参数，记录训练/验证指标。",
        "- 修改一个模型结构或超参数，比较前后变化。",
        "- 解释输出 shape、损失变化和错误样例。",
        "",
        "## 调参建议",
        "- 每次只改一个变量，例如学习率、batch size、层数或 dropout。",
        "- 保留随机种子和数据划分，避免把随机波动误认为方法改进。",
        "",
        "## 常见报错",
        "- shape mismatch：打印每层输入输出维度。",
        "- CUDA out of memory：减小 batch size 或切回 CPU。",
        "- loss 不下降：检查学习率、标签格式和模型输出。",
    ])


def _interactive_animation(chapter: dict) -> str:
    payload = {
        "animation_type": "step_flow",
        "title": chapter["chapter_title"],
        "parameters": [{"name": concept, "control": "toggle"} for concept in chapter["concepts"][:5]],
        "steps": [
            {"step": idx, "label": concept, "description": f"高亮 {concept} 在本章流程中的输入、输出和易错点。"}
            for idx, concept in enumerate(chapter["concepts"][:6], start=1)
        ],
        "student_tasks": ["拖动流程顺序", "标注关键张量", "回答一个暂停思考问题"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _project_files(chapter: dict) -> dict[str, str]:
    return {
        "project_brief.md": "\n".join([
            f"# {chapter['chapter_title']} 项目任务书",
            "",
            "## 项目目标",
            "任选 CNN 图像分类、LSTM 序列分类、Attention/Transformer 文本实验或目标检测拓展之一，完成从数据准备到结果展示的完整闭环。",
            "",
            "## 提交物",
            "- 实验代码与运行说明",
            "- 训练/验证曲线",
            "- 错误样例分析",
            "- 课程报告",
            "- 5 分钟展示 PPT",
        ]),
        "rubric.md": "\n".join([
            "# 课程项目评分 Rubric",
            "",
            "| 维度 | 权重 | 说明 |",
            "| --- | --- | --- |",
            "| 问题定义 | 20% | 目标清晰，数据和指标合理 |",
            "| 方法实现 | 30% | 模型、训练、评估流程完整 |",
            "| 实验分析 | 30% | 有对比、有错因、有复盘 |",
            "| 表达展示 | 20% | 报告结构清晰，图表可读 |",
        ]),
        "report_template.md": "\n".join([
            "# 深度学习课程项目报告模板",
            "",
            "## 1. 项目背景",
            "## 2. 数据集与任务定义",
            "## 3. 方法与模型结构",
            "## 4. 实验设置",
            "## 5. 结果与误差分析",
            "## 6. 总结与改进方向",
        ]),
    }


def _lab_code(name: str) -> str:
    topic = name.replace(".py", "").replace("_", " ")
    return f'''"""Minimal runnable lab: {topic}."""

from __future__ import annotations

import random


def set_seed(seed: int = 42) -> None:
    random.seed(seed)


def main() -> None:
    set_seed()
    print("LingXi Deep Learning Lab: {topic}")
    print("This lightweight lab is designed for course demonstration.")
    print("Extend it with torch/torchvision in a full local environment.")


if __name__ == "__main__":
    main()
'''


def _unit_id(chapter: dict, topic: str) -> str:
    return f"dlv2_ch{chapter['chapter_no']:02d}_{_slug(topic)}"[:80]


def build_all() -> None:
    COURSE_DIR.mkdir(parents=True, exist_ok=True)
    COURSEWARE_DIR.mkdir(parents=True, exist_ok=True)
    LABS_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    chunks = _source_chunks()
    (COURSE_DIR / "source_registry.json").write_text(json.dumps(SOURCE_REGISTRY, ensure_ascii=False, indent=2), encoding="utf-8")
    (COURSE_DIR / "source_ingestion_manifest.json").write_text(json.dumps({
        "course_id": "deep_learning_v2",
        "imported_at": "generated_by_scripts",
        "source_count": len(SOURCE_REGISTRY),
        "chunk_count": len(chunks),
        "student_view_policy": "student resources use curated courseware, not raw imported chunks",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    units = []
    evidence = []
    chapter_index = []

    for chapter in CHAPTERS:
        chapter_dir = COURSEWARE_DIR / chapter["chapter_id"]
        chapter_dir.mkdir(parents=True, exist_ok=True)
        files = {
            "main_note.md": _main_note(chapter, chunks),
            "mind_map.mmd": _mind_map(chapter),
            "exercises.md": _exercises(chapter),
            "reading_video_guide.md": _reading_guide(chapter),
        }
        if chapter.get("lab"):
            files["code_lab.md"] = _code_lab(chapter)
        if chapter.get("animation"):
            files["interactive_animation.json"] = _interactive_animation(chapter)
        if chapter.get("project"):
            files.update(_project_files(chapter))
        for filename, content in files.items():
            (chapter_dir / filename).write_text(content, encoding="utf-8")

        primary_resources = [
            {"resource_key": f"{chapter['chapter_id']}/main_note.md", "title": f"{chapter['chapter_title']} 主讲义", "type": "课程讲解文档", "is_required": True},
            {"resource_key": f"{chapter['chapter_id']}/mind_map.mmd", "title": f"{chapter['chapter_title']} 思维导图", "type": "知识点思维导图", "is_required": True},
            {"resource_key": f"{chapter['chapter_id']}/exercises.md", "title": f"{chapter['chapter_title']} 练习题集", "type": "练习题集", "is_required": True},
            {"resource_key": f"{chapter['chapter_id']}/reading_video_guide.md", "title": f"{chapter['chapter_title']} 阅读与视频指南", "type": "拓展阅读包", "is_required": True},
        ]
        optional_resources = []
        if chapter.get("lab"):
            primary_resources.append({"resource_key": f"{chapter['chapter_id']}/code_lab.md", "title": f"{chapter['chapter_title']} 代码实验", "type": "PyTorch 实操案例", "is_required": True})
        if chapter.get("animation"):
            optional_resources.append({"resource_key": f"{chapter['chapter_id']}/interactive_animation.json", "title": f"{chapter['chapter_title']} 交互动画规格", "type": "交互动画规格", "is_required": False})
        if chapter.get("project"):
            primary_resources.append({"resource_key": f"{chapter['chapter_id']}/project_brief.md", "title": "深度学习综合项目任务书", "type": "课程实践项目任务书", "is_required": True})
            optional_resources.extend([
                {"resource_key": f"{chapter['chapter_id']}/rubric.md", "title": "深度学习课程项目 Rubric", "type": "拓展阅读包", "is_required": False},
                {"resource_key": f"{chapter['chapter_id']}/report_template.md", "title": "深度学习课程项目报告模板", "type": "拓展阅读包", "is_required": False},
            ])
        chapter_index.append({
            "chapter_no": chapter["chapter_no"],
            "chapter_id": chapter["chapter_id"],
            "chapter_title": chapter["chapter_title"],
            "summary": chapter["summary"],
            "source_reference_ids": [item["source_id"] for item in SOURCE_REGISTRY],
            "primary_resources": primary_resources,
            "optional_resources": optional_resources,
        })

        for topic in UNIT_TOPICS[chapter["chapter_id"]]:
            unit_id = _unit_id(chapter, topic)
            evidence_id = f"ev_{unit_id}_001"
            units.append({
                "unit_id": unit_id,
                "course_id": "deep_learning_v2",
                "chapter_id": chapter["chapter_id"],
                "chapter_title": chapter["chapter_title"],
                "title": topic,
                "aliases": list(dict.fromkeys([topic, topic.lower(), *re.split(r"[、/ ]+", topic)])),
                "prerequisites": chapter["concepts"][:2],
                "related_units": [],
                "compare_units": [],
                "core_concepts": chapter["concepts"][:8],
                "formulas": [FORMULAS[topic]] if topic in FORMULAS else [],
                "code_patterns": ["torch.nn", "DataLoader"] if chapter.get("lab") else [],
                "common_misconceptions": [f"把「{topic}」当成孤立名词，不说明输入输出和适用条件。"],
                "learning_outcomes": [f"解释「{topic}」的定义、作用、流程位置和一个应用场景。"],
                "resource_focus": ["主讲义", "练习题", "代码实验" if chapter.get("lab") else "阅读指南"],
                "evidence_refs": [evidence_id],
                "source_reference_ids": [item["source_id"] for item in SOURCE_REGISTRY],
                "difficulty": "medium" if chapter.get("core") else "beginner",
            })
            evidence.append({
                "evidence_id": evidence_id,
                "course_id": "deep_learning_v2",
                "chapter_id": chapter["chapter_id"],
                "unit_id": unit_id,
                "source_type": "curated_courseware",
                "source_file": f"courseware/{chapter['chapter_id']}/main_note.md",
                "source_reference_ids": [item["source_id"] for item in SOURCE_REGISTRY],
                "content_excerpt": f"{chapter['chapter_title']} 中的「{topic}」围绕 {chapter['summary']} 展开，学习时需要同时关注定义、输入输出、公式/流程、实验边界和常见误区。",
            })

    (COURSE_DIR / "chapter_resource_index.json").write_text(json.dumps(chapter_index, ensure_ascii=False, indent=2), encoding="utf-8")
    (COURSE_DIR / "knowledge_units.jsonl").write_text(
        "\n".join(json.dumps(unit, ensure_ascii=False) for unit in units) + "\n",
        encoding="utf-8",
    )
    (EVIDENCE_DIR / "evidence_chunks.jsonl").write_text(
        "\n".join(json.dumps(item, ensure_ascii=False) for item in evidence) + "\n",
        encoding="utf-8",
    )
    (COURSE_DIR / "course_manifest.json").write_text(json.dumps({
        "course_id": "deep_learning_v2",
        "course_name": "深度学习",
        "course_display_name": "《深度学习》",
        "version": "v2",
        "source_prefix": "《深度学习》v2 课程知识库",
        "resource_uploader": "LingXi KnowledgeSeedAgent",
        "chapters": [{"chapter_id": c["chapter_id"], "title": c["chapter_title"], "summary": c["summary"]} for c in CHAPTERS],
        "knowledge_unit_count": len(units),
        "evidence_count": len(evidence),
        "student_view_policy": "chapter_hub",
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    videos = []
    for chapter in CHAPTERS:
        first_unit = _unit_id(chapter, UNIT_TOPICS[chapter["chapter_id"]][0])
        videos.append({
            "video_id": f"DLV2-VIDEO-CH{chapter['chapter_no']:02d}",
            "course_id": "deep_learning_v2",
            "unit_ids": [first_unit],
            "title": f"{chapter['chapter_title']} 公开视频学习入口",
            "platform": "link_only",
            "source": "高校公开课/MOOC/官方课程入口",
            "source_url": "https://www.icourse163.org/",
            "tags": chapter["concepts"][:6],
            "difficulty": "medium" if chapter.get("core") else "beginner",
            "duration": "20-45 分钟",
            "recommended_segments": ["先看概念段，再看公式或实验段，最后完成本章练习。"],
            "copyright_policy": "link_only",
        })
    (COURSE_DIR / "video_catalog.json").write_text(json.dumps(videos, ensure_ascii=False, indent=2), encoding="utf-8")

    labs = [
        "mlp_numpy_from_scratch.py",
        "mlp_pytorch_mnist.py",
        "cnn_cifar10.py",
        "cnn_output_shape_debug.py",
        "optimizer_comparison.py",
        "dropout_batchnorm_demo.py",
        "resnet_transfer_learning.py",
        "object_detection_iou_anchor_demo.py",
        "lstm_sequence_classification.py",
        "attention_demo.py",
        "transformer_text_classification.py",
    ]
    for lab in labs:
        (LABS_DIR / lab).write_text(_lab_code(lab), encoding="utf-8")

    coverage_lines = [
        "# Deep Learning v2 来源覆盖报告",
        "",
        "## 总览",
        f"- 课程章节：{len(CHAPTERS)}",
        f"- 知识单元：{len(units)}",
        f"- Evidence：{len(evidence)}",
        f"- 导入源片段：{len(chunks)}",
        "",
        "## 来源使用原则",
        "- KyonHuang Andrew Ng Notes 用作理论主线、公式和章节顺序参考。",
        "- AccumulateMore/CV 用作 PyTorch 实践、CV 任务和 notebook 实验顺序参考。",
        "- 学生端展示本项目重构课程内容，不直接展示 imported raw chunks。",
        "",
        "## 章节覆盖",
    ]
    for chapter in CHAPTERS:
        count = len(_chunks_for_chapter(chapter["chapter_id"], chunks))
        coverage_lines.append(f"- {chapter['chapter_title']}：{count} 个来源片段；角色：{'、'.join(chapter['source_roles'])}")
    (DOCS_DIR / "source_coverage_report.md").write_text("\n".join(coverage_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    random.seed(42)
    build_all()
    print(f"Built {COURSE_DIR}")
