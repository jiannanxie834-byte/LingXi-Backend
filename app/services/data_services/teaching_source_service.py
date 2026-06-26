import hashlib
import re
from typing import Dict, Iterable, List

from app.services.data_services import resource_artifact_type_service as artifact_types


DEFAULT_LIMIT = 10


CONCEPT_CATALOG = [
    {"id": "dl_intro", "label": "深度学习导论", "aliases": ["深度学习", "deep learning", "神经网络", "表示学习"]},
    {"id": "backprop", "label": "反向传播", "aliases": ["反向传播", "BP", "backprop", "链式法则", "梯度传播", "损失函数"]},
    {"id": "optimization", "label": "优化算法", "aliases": ["SGD", "Momentum", "Adam", "优化器", "学习率", "训练曲线"]},
    {"id": "regularization", "label": "正则化与泛化", "aliases": ["正则化", "Dropout", "BatchNorm", "数据增强", "早停", "过拟合"]},
    {"id": "cnn", "label": "CNN 卷积神经网络", "aliases": ["CNN", "卷积神经网络", "卷积", "卷积层", "卷积核", "池化", "图像分类"]},
    {"id": "rnn_lstm", "label": "RNN/LSTM/GRU", "aliases": ["RNN", "LSTM", "GRU", "循环神经网络", "序列模型", "门控机制"]},
    {"id": "transformer", "label": "Transformer 与自注意力", "aliases": ["Transformer", "Attention", "注意力机制", "自注意力", "多头注意力", "QKV", "位置编码"]},
    {"id": "generative", "label": "生成模型", "aliases": ["自编码器", "VAE", "GAN", "扩散模型", "Diffusion", "生成模型"]},
    {"id": "pytorch", "label": "PyTorch 实战", "aliases": ["PyTorch", "torch", "Dataset", "DataLoader", "训练循环", "代码实验"]},
    {"id": "project", "label": "课程综合项目", "aliases": ["课程项目", "综合项目", "图像分类项目", "文本分类项目", "时间序列预测项目", "Rubric"]},
]


TEACHING_RESOURCE_CATALOG = [
    {
        "title": "蒲公英书《神经网络与深度学习》开放资源",
        "platform": "蒲公英书",
        "source": "邱锡鹏等",
        "material_type": "开放教材/可视化资源",
        "url": "https://nndl.github.io/",
        "summary": "中文开放深度学习教材，覆盖神经网络基础、卷积网络、循环网络、注意力机制与实践案例。",
        "integration_mode": "作为中文主教材入口；系统据此生成章节导读、公式图解、练习题、代码实验和复盘任务。",
        "copyright_note": "只引用公开入口和开放资源说明；具体 PDF、代码和图片按原站授权要求使用。",
        "concepts": ["dl_intro", "backprop", "cnn", "rnn_lstm", "transformer", "generative"],
        "modalities": ["text", "diagram", "code", "exercise"],
        "base_score": 96,
    },
    {
        "title": "Dive into Deep Learning 中文版",
        "platform": "D2L.ai",
        "source": "Aston Zhang 等",
        "material_type": "开放教材/代码教程",
        "url": "https://zh.d2l.ai/",
        "summary": "面向动手实践的深度学习开放教材，包含 PyTorch 代码、CNN、RNN、Attention 与 Transformer 等章节。",
        "integration_mode": "作为代码实验和项目实践入口；系统转成 PyTorch 实操案例、练习题和项目任务。",
        "copyright_note": "只引用开放教材入口；内容使用需遵循原站许可。",
        "concepts": ["dl_intro", "cnn", "rnn_lstm", "transformer", "pytorch", "project"],
        "modalities": ["text", "code", "exercise"],
        "base_score": 95,
    },
    {
        "title": "PyTorch 官方 Tutorials",
        "platform": "PyTorch",
        "source": "PyTorch 官方文档",
        "material_type": "官方文档/代码教程",
        "url": "https://pytorch.org/tutorials/",
        "summary": "官方 PyTorch 教程，覆盖 tensor、autograd、模型训练、数据集、迁移学习和图像分类实践。",
        "integration_mode": "作为代码实验权威入口；系统生成运行步骤、报错排查、调参任务和实验报告模板。",
        "copyright_note": "引用官方公开文档链接，不复制大段文档正文。",
        "concepts": ["pytorch", "cnn", "project", "backprop"],
        "modalities": ["text", "code"],
        "base_score": 94,
    },
    {
        "title": "Stanford CS231n Convolutional Neural Networks for Visual Recognition",
        "platform": "Stanford CS231n",
        "source": "Stanford University",
        "material_type": "公开课程/讲义",
        "url": "https://cs231n.github.io/",
        "summary": "计算机视觉与 CNN 经典公开课程资料，适合作为 CNN、图像分类和项目实践的拓展入口。",
        "integration_mode": "作为 CNN 项目拓展阅读；系统生成观看/阅读问题、卷积尺寸练习和图像分类项目任务书。",
        "copyright_note": "只引用公开课程入口；讲义和图片按课程站点许可使用。",
        "concepts": ["cnn", "pytorch", "project"],
        "modalities": ["text", "video", "diagram", "exercise"],
        "base_score": 91,
    },
    {
        "title": "3Blue1Brown 神经网络可视化系列",
        "platform": "3Blue1Brown / YouTube",
        "source": "公开视频",
        "material_type": "公开视频",
        "url": "https://www.youtube.com/playlist?list=PLZHQObOWTQDMp_VZelDYjka8tnXNpXhzJ",
        "summary": "用动画解释神经网络、梯度下降和反向传播，适合图解型学习者建立直观理解。",
        "integration_mode": "作为视频推荐卡和个性化观看指南入口；系统只保存原始链接、推荐片段和观看任务。",
        "copyright_note": "只提供原始公开视频链接和学习建议，不下载、不搬运、不重新分发视频内容。",
        "concepts": ["dl_intro", "backprop", "optimization"],
        "modalities": ["video", "diagram"],
        "base_score": 88,
    },
    {
        "title": "The Illustrated Transformer",
        "platform": "Jay Alammar Blog",
        "source": "公开教程",
        "material_type": "图解教程",
        "url": "https://jalammar.github.io/illustrated-transformer/",
        "summary": "用图解方式讲解 Transformer、Encoder/Decoder、自注意力和多头注意力。",
        "integration_mode": "作为 Transformer 图解阅读入口；系统生成 Q/K/V 练习题、观看指南和交互动画规格。",
        "copyright_note": "只引用公开教程入口，不复制大段图文内容。",
        "concepts": ["transformer"],
        "modalities": ["text", "diagram"],
        "base_score": 90,
    },
    {
        "title": "MIT 6.S191 Introduction to Deep Learning",
        "platform": "MIT",
        "source": "MIT 公开课程",
        "material_type": "公开课程/视频",
        "url": "https://introtodeeplearning.com/",
        "summary": "MIT 深度学习入门公开课程，覆盖神经网络、CNN、序列建模、生成模型和项目实践。",
        "integration_mode": "作为英文补充公开课；中文资源不足时提供英文入口，并生成观看前词汇与观看后任务。",
        "copyright_note": "只引用公开课程入口和授权资料，不下载、不重新托管视频。",
        "concepts": ["dl_intro", "cnn", "rnn_lstm", "generative", "project"],
        "modalities": ["video", "text", "code"],
        "base_score": 87,
    },
    {
        "title": "清华大学出版社《深度学习》相关教材目录",
        "platform": "清华大学出版社",
        "source": "出版社公开图书页",
        "material_type": "教材目录/简介",
        "url": "https://www.tup.tsinghua.edu.cn/",
        "summary": "用于演示出版社教材入口与课程知识库的关联，具体教材需由教师按授权选定。",
        "integration_mode": "作为教材目录入口；系统生成阅读顺序和章节导读，不复制教材正文。",
        "copyright_note": "只引用出版社公开入口；正文、样章和课件需授权后入库。",
        "concepts": ["dl_intro", "backprop", "cnn", "transformer"],
        "modalities": ["text"],
        "base_score": 78,
    },
]


def _compact(value: str) -> str:
    return re.sub(r"\s+", "", str(value or "").lower())


def _clip(text: str, limit: int = 180) -> str:
    compact = " ".join((text or "").split())
    return compact if len(compact) <= limit else compact[:limit].rstrip() + "..."


def _concept_labels(concept_ids: Iterable[str]) -> List[str]:
    id_to_label = {item["id"]: item["label"] for item in CONCEPT_CATALOG}
    return [id_to_label[concept_id] for concept_id in concept_ids if concept_id in id_to_label]


def extract_catalog_concepts(text: str) -> List[str]:
    compact_text = _compact(text)
    matched = []
    for concept in CONCEPT_CATALOG:
        aliases = [_compact(alias) for alias in concept.get("aliases", [])]
        if any(alias and alias in compact_text for alias in aliases):
            matched.append(concept["id"])
    return list(dict.fromkeys(matched))


def _resource_match_score(resource: Dict, concept_ids: List[str]) -> int:
    matched_count = len(set(resource.get("concepts", [])) & set(concept_ids))
    if matched_count == 0:
        return 0
    return min(100, int(resource.get("base_score", 70)) + matched_count * 2)


def _normalize_resource(resource: Dict, concept_ids: List[str]) -> Dict:
    matched_concepts = [
        concept_id
        for concept_id in resource.get("concepts", [])
        if concept_id in concept_ids
    ]
    return {
        "title": resource["title"],
        "platform": resource["platform"],
        "source": resource["source"],
        "source_type": resource["material_type"],
        "material_type": resource["material_type"],
        "url": resource["url"],
        "open_url": resource["url"],
        "language": "中文" if "MIT" not in resource["platform"] and "YouTube" not in resource["platform"] else "英文/可选字幕",
        "summary": _clip(resource["summary"], 240),
        "abstract": _clip(resource["summary"], 240),
        "integration_mode": resource["integration_mode"],
        "copyright_note": resource["copyright_note"],
        "concepts": resource.get("concepts", []),
        "matched_concepts": matched_concepts,
        "matched_concept_labels": _concept_labels(matched_concepts),
        "modalities": resource.get("modalities", []),
        "score": _resource_match_score(resource, concept_ids),
        "reason": "、".join(_concept_labels(matched_concepts)),
    }


def select_teaching_sources(query: str, limit: int = DEFAULT_LIMIT) -> Dict:
    concept_ids = extract_catalog_concepts(query)
    if not concept_ids:
        return {
            "items": [],
            "meta": {
                "query": query or "",
                "matched_concepts": [],
                "strategy": "深度学习课程知识点目录匹配",
                "total_count": 0,
            },
        }

    items = [
        _normalize_resource(resource, concept_ids)
        for resource in TEACHING_RESOURCE_CATALOG
        if _resource_match_score(resource, concept_ids) > 0
    ]
    items.sort(key=lambda item: (len(item.get("matched_concepts", [])), item.get("score", 0), item.get("title", "")), reverse=True)
    limited = items[:max(1, min(limit, 30))]
    return {
        "items": limited,
        "meta": {
            "query": query or "",
            "matched_concepts": _concept_labels(concept_ids),
            "strategy": "深度学习课程知识点目录匹配",
            "copyright_policy": "只引用公开入口、官方简介、目录和授权资料；不抓取教材正文，不下载视频。",
            "total_count": len(limited),
            "sources": sorted({item.get("platform", "") for item in limited if item.get("platform")}),
            "material_types": sorted({item.get("material_type", "") for item in limited if item.get("material_type")}),
        },
    }


def format_teaching_sources_for_prompt(result: Dict, max_items: int = 6) -> str:
    items = (result or {}).get("items") or []
    if not items:
        return "本轮没有匹配到目录化外部教学资料；生成内容只使用《深度学习》课程知识库依据，并标注需要管理员补充授权资料。"

    lines = ["以下资料来自系统维护的《深度学习》教学资料目录，只引用公开入口、官方简介、目录或授权内容。"]
    for index, item in enumerate(items[:max_items], start=1):
        lines.append(
            f"{index}. {item.get('title', '教学资料')}｜{item.get('material_type', '教学资料')}｜{item.get('platform', '未知平台')}\n"
            f"   链接：{item.get('open_url') or item.get('url') or '暂无'}\n"
            f"   匹配知识点：{'、'.join(item.get('matched_concept_labels', [])) or '未标注'}\n"
            f"   整合方式：{item.get('integration_mode', '链接引用')}\n"
            f"   资料说明：{_clip(item.get('summary', ''), 160)}\n"
            f"   版权边界：{item.get('copyright_note', '仅使用公开入口和授权资料')}"
        )
    return "\n".join(lines)


def _source_lines(items: List[Dict], max_items: int = 3) -> str:
    return "\n".join([
        f"- [{item.get('title', '教学资料')}]({item.get('open_url') or item.get('url')})（{item.get('platform') or item.get('source') or '教学平台'}）"
        for item in items[:max_items]
    ])


def _card_id(prefix: str, title: str, concepts: List[str]) -> str:
    digest = hashlib.md5(f"{prefix}|{title}|{'|'.join(concepts)}".encode("utf-8")).hexdigest()[:10].upper()
    return f"AUTO-{prefix}-{digest}"


def _card_score(base_score: int, concept_ids: List[str], sources: List[Dict]) -> int:
    return min(100, base_score + len(concept_ids) * 3 + len(sources) * 2)


def _card_common(prefix: str, title: str, resource_type: str, concept_ids: List[str], sources: List[Dict], score: int) -> Dict:
    return {
        "id": _card_id(prefix, title, concept_ids),
        "title": title,
        "type": resource_type,
        "status": "系统推送",
        "uploader": "教学资源推荐 Agent",
        "applicant_username": "",
        "time": "",
        "source": "深度学习课程知识库 + 教学资料目录",
        "agent_notes": "",
        "safety_review": {},
        "review_comment": "",
        "reviewed_at": "",
        "auto_pushed": True,
        "_recommend_rank": score,
    }


def build_pushed_teaching_resource_cards(query: str, limit: int = 4) -> List[Dict]:
    concept_ids = extract_catalog_concepts(query)
    if not concept_ids:
        return []

    result = select_teaching_sources(query, limit=10)
    sources = result.get("items", [])
    if not sources:
        return []

    topic = "、".join(_concept_labels(concept_ids)[:2])
    cards = []
    video_sources = [item for item in sources if "video" in item.get("modalities", [])]
    text_sources = [item for item in sources if "text" in item.get("modalities", [])]
    code_sources = [item for item in sources if "code" in item.get("modalities", [])]

    if video_sources:
        card = _card_common("VIDEO", f"{topic}公开视频推荐卡", artifact_types.VIDEO_RECOMMENDATION, concept_ids, video_sources, _card_score(78, concept_ids, video_sources))
        card.update({
            "summary": f"围绕「{topic}」整理公开视频/公开课入口，并组织成可执行的观看与复盘任务。",
            "content": f"""## {topic}公开视频推荐卡

### 推荐方式
1. 打开原始公开课或公开视频入口。
2. 对照本系统课程知识库中的核心概念完成观看任务。
3. 观看后完成 2 道复盘题或一个代码实验。

### 可参考来源
{_source_lines(video_sources)}

### 版权说明
仅提供原始链接和学习建议，不复制、不下载、不重新分发视频内容。"""
        })
        cards.append(card)

    if text_sources:
        card = _card_common("READ", f"{topic}拓展阅读包", artifact_types.READING_PACK, concept_ids, text_sources, _card_score(76, concept_ids, text_sources))
        card.update({
            "summary": f"围绕「{topic}」推送开放教材、课程页或官方文档入口，并生成阅读顺序。",
            "content": f"""## {topic}拓展阅读包

### 阅读目标
- 明确该主题在《深度学习》课程中的章节位置。
- 优先掌握定义、公式、图解、易错点和实验任务。
- 阅读后回到系统完成练习题集或代码实验。

### 建议阅读顺序
1. 先浏览章节目录，定位相关小节。
2. 重点阅读概念定义、图示和例题。
3. 把不理解的公式或代码记录到学习评价页，触发后续补弱。

### 可参考来源
{_source_lines(text_sources)}

### 版权边界
教材正文、样章和课件只使用官方公开试读或授权上传内容；系统不抓取付费正文。"""
        })
        cards.append(card)

    if code_sources:
        card = _card_common("CODE", f"{topic}PyTorch 实操入口", artifact_types.CODE_LAB, concept_ids, code_sources, _card_score(75, concept_ids, code_sources))
        card.update({
            "summary": f"围绕「{topic}」整理官方代码教程入口，便于生成可运行实验和调参任务。",
            "content": f"""## {topic}PyTorch 实操入口

### 实验目标
- 跑通最小训练流程。
- 检查 tensor shape、loss 曲线和验证指标。
- 把报错和实验现象记录到报告模板。

### 参考入口
{_source_lines(code_sources)}

### 后续动作
打开资源生成入口后，可继续生成完整 PyTorch 实操案例。"""
        })
        cards.append(card)

    cards.sort(key=lambda item: (item.get("_recommend_rank", 0), item.get("type", ""), item.get("title", "")), reverse=True)
    return cards[:max(1, min(limit, len(cards)))]
