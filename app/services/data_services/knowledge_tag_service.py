import re
from collections import OrderedDict
from typing import Iterable, List, Optional


MAX_KNOWLEDGE_TAGS = 8

_NON_KNOWLEDGE_TAGS = {
    "概念讲解",
    "实操训练",
    "路径规划",
    "练习巩固",
    "综合学习",
    "生成学习路径",
    "制定计划",
    "生成资源",
    "错题诊断",
    "平台自动诊断",
    "初学者",
    "进阶",
    "熟练",
    "高级",
    "低",
    "中",
    "高",
}

_DROP_PATTERNS = [
    "需要",
    "适合",
    "建议",
    "进一步",
    "强化",
    "提升",
    "修复",
    "复盘",
    "学习目标",
    "学习路线",
    "学习计划",
    "暂无",
    "当前主题",
]

_ALIASES = [
    (("深度学习", "deep learning"), "深度学习基础"),
    (("矩阵", "线性代数", "梯度", "链式法则", "概率"), "数学前置基础"),
    (("神经网络", "感知机", "mlp", "激活函数"), "神经网络基础"),
    (("反向传播", "bp", "backprop", "损失函数"), "反向传播"),
    (("sgd", "momentum", "adam", "优化器", "学习率"), "优化算法"),
    (("dropout", "batchnorm", "正则化", "数据增强", "泛化", "过拟合"), "正则化与泛化"),
    (("cnn", "卷积神经网络", "卷积", "卷积层", "卷积核", "池化", "图像分类"), "CNN 卷积神经网络"),
    (("rnn", "lstm", "gru", "循环神经网络", "序列模型", "门控机制"), "RNN/LSTM/GRU"),
    (("transformer", "attention", "自注意力", "多头注意力", "qkv", "位置编码"), "Transformer 自注意力"),
    (("gan", "扩散模型", "diffusion", "自编码器", "vae", "生成模型"), "生成模型"),
    (("pytorch", "torch", "dataloader", "dataset", "训练循环", "代码实验"), "PyTorch 实战"),
    (("课程项目", "综合项目", "图像分类项目", "文本分类项目", "时间序列预测项目"), "深度学习课程项目"),
]

_SUPPRESS_WHEN_PRESENT = {
    "深度学习基础": {"神经网络基础"},
}


def _compact_text(value: str) -> str:
    return re.sub(r"\s+", "", value.lower())


def normalize_knowledge_tag(value: Optional[str]) -> Optional[str]:
    if not value:
        return None

    tag = str(value).strip()
    tag = tag.strip("「」『』“”\"'` ，,。.;；:/\\|[]（）()")
    if not tag or tag in _NON_KNOWLEDGE_TAGS:
        return None

    compact = _compact_text(tag)
    if compact in {_compact_text(item) for item in _NON_KNOWLEDGE_TAGS}:
        return None

    if any(pattern in tag for pattern in _DROP_PATTERNS):
        return None

    for keys, normalized in _ALIASES:
        if any(key in compact for key in keys):
            return normalized

    if len(tag) < 2 or len(tag) > 18:
        return None

    return tag


def extract_knowledge_tags_from_text(text: Optional[str]) -> List[str]:
    if not text:
        return []

    compact = _compact_text(str(text))
    tags = []

    for keys, normalized in _ALIASES:
        if any(key in compact for key in keys):
            tags.append(normalized)

    return summarize_knowledge_tags(tags)


def summarize_knowledge_tags(
    candidates: Iterable[Optional[str]],
    max_count: int = MAX_KNOWLEDGE_TAGS
) -> List[str]:
    result = OrderedDict()

    for item in candidates:
        normalized = normalize_knowledge_tag(item)
        if normalized:
            result.setdefault(normalized, None)

    tags = list(result.keys())
    tag_set = set(tags)
    collapsed = [
        tag
        for tag in tags
        if not (
            tag in _SUPPRESS_WHEN_PRESENT
            and _SUPPRESS_WHEN_PRESENT[tag].intersection(tag_set)
        )
    ]

    return collapsed[:max_count]
