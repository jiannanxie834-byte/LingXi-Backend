import hashlib
import re
from typing import Dict, Iterable, List


DEFAULT_LIMIT = 10


CONCEPT_CATALOG = [
    {
        "id": "ai_intro",
        "label": "人工智能",
        "aliases": ["人工智能导论", "人工智能", "AI", "智能体"],
    },
    {
        "id": "machine_learning",
        "label": "机器学习",
        "aliases": ["机器学习", "Machine Learning", "ML"],
    },
    {
        "id": "supervised_learning",
        "label": "监督学习",
        "aliases": ["监督学习", "分类", "回归", "有监督学习"],
    },
    {
        "id": "model_evaluation",
        "label": "模型评估",
        "aliases": ["模型评估", "准确率", "精确率", "召回率", "F1", "交叉验证", "不均衡数据"],
    },
    {
        "id": "confusion_matrix",
        "label": "混淆矩阵",
        "aliases": ["混淆矩阵", "TP", "FP", "TN", "FN"],
    },
    {
        "id": "deep_learning",
        "label": "深度学习",
        "aliases": ["深度学习", "神经网络", "反向传播", "梯度下降"],
    },
    {
        "id": "lstm",
        "label": "LSTM 与序列建模",
        "aliases": ["LSTM", "长短期记忆网络", "RNN", "循环神经网络", "序列模型", "门控机制"],
    },
    {
        "id": "transformer",
        "label": "Transformer 与注意力机制",
        "aliases": ["Transformer", "注意力机制", "自注意力", "多头注意力", "BERT", "GPT"],
    },
    {
        "id": "nlp_llm",
        "label": "自然语言处理与大语言模型",
        "aliases": ["自然语言处理", "NLP", "大语言模型", "LLM", "提示词"],
    },
    {
        "id": "rag",
        "label": "检索增强生成",
        "aliases": ["RAG", "检索增强", "检索增强生成"],
    },
    {
        "id": "multimodal_resource",
        "label": "多模态学习资源",
        "aliases": ["多模态", "PPT", "流程图", "Mermaid", "课件", "题解"],
    },
    {
        "id": "practice_project",
        "label": "实践项目",
        "aliases": ["实践", "实验", "项目", "代码注释", "应用任务"],
    },
    {
        "id": "ai_safety",
        "label": "AI 安全与防幻觉",
        "aliases": ["AI 安全", "人工智能安全", "防幻觉", "内容安全", "隐私保护"],
    },
    {
        "id": "information_security",
        "label": "信息安全基础",
        "aliases": ["信息安全", "网络安全", "密码学", "身份认证", "访问控制", "系统安全"],
    },
]


TEACHING_RESOURCE_CATALOG = [
    {
        "title": "中国大学MOOC《机器学习》：第2章模型评估",
        "platform": "中国大学MOOC",
        "source": "中国地质大学（武汉）",
        "material_type": "MOOC课程小节",
        "url": "https://www.icourse163.org/learn/CUG-1003556007",
        "summary": "课程以分类任务为切入点，第2章讲解模型评估的方法、指标以及比较检验。",
        "integration_mode": "作为视频导学和章节学习任务引用；系统据此生成观看问题、评价指标练习和错题复盘。",
        "copyright_note": "只引用课程公开页和课程大纲，不复制课程视频和课件正文。",
        "concepts": ["machine_learning", "supervised_learning", "model_evaluation", "confusion_matrix"],
        "modalities": ["video", "exercise", "text"],
        "base_score": 96,
    },
    {
        "title": "国家高等教育智慧教育平台《机器学习与人工智能》：监督学习评价",
        "platform": "国家高等教育智慧教育平台",
        "source": "智慧高教",
        "material_type": "公开课小节",
        "url": "https://higher.smartedu.cn/course/62354d779906eace0490a1bb",
        "summary": "课程包含机器学习基本算法、交叉验证方法，并设置“监督学习的评价”“不均衡数据预测的评估方法”等内容。",
        "integration_mode": "作为权威公开课入口引用；系统转成学习路线、视频任务、测验前置知识和复盘问题。",
        "copyright_note": "只引用国家平台公开课程页和大纲信息，具体视频/课件按平台授权观看。",
        "concepts": ["ai_intro", "machine_learning", "supervised_learning", "model_evaluation"],
        "modalities": ["video", "text", "exercise"],
        "base_score": 95,
    },
    {
        "title": "学堂在线《机器学习初步》：模型评估与选择",
        "platform": "学堂在线",
        "source": "南京大学",
        "material_type": "MOOC课程小节",
        "url": "https://www.xuetangx.com/course/nju0802bt",
        "summary": "课程覆盖绪论、模型评估与选择、线性模型、决策树、支持向量机、神经网络、贝叶斯分类器等内容。",
        "integration_mode": "作为章节化学习材料引用；系统生成知识结构图、章节导读和配套练习。",
        "copyright_note": "只引用课程公开页和课程说明，不复制平台课程内容。",
        "concepts": ["machine_learning", "model_evaluation", "deep_learning"],
        "modalities": ["video", "text", "exercise"],
        "base_score": 93,
    },
    {
        "title": "学堂在线《机器学习概论》",
        "platform": "学堂在线",
        "source": "清华大学",
        "material_type": "MOOC课程",
        "url": "https://www.xuetangx.com/course/THU0809003188/",
        "summary": "课程讲解机器学习的基本概念和思想，介绍不同类型学习方法的主要思想和代表性算法。",
        "integration_mode": "作为概念导学和拓展课入口引用；系统转化为课程讲解文档和导图资源。",
        "copyright_note": "只引用课程公开页和简介，具体视频/课件按平台授权使用。",
        "concepts": ["machine_learning", "supervised_learning"],
        "modalities": ["video", "text"],
        "base_score": 88,
    },
    {
        "title": "Bilibili 公开课《吴恩达机器学习》：监督学习小节",
        "platform": "Bilibili",
        "source": "公开课转载/课程视频",
        "material_type": "教学视频小节",
        "url": "https://www.bilibili.com/video/BV1By4y1J7A5/",
        "summary": "视频选集包含“监督学习”“无监督学习”“模型描述”“代价函数”等小节。",
        "integration_mode": "作为课后视频补充引用；系统生成观看前问题、观看后练习和概念对照表。",
        "copyright_note": "只引用公开视频入口，不下载、不二次分发视频；正式提交时优先选择高校/机构官方授权资源。",
        "concepts": ["machine_learning", "supervised_learning"],
        "modalities": ["video"],
        "base_score": 82,
    },
    {
        "title": "清华大学出版社《机器学习》",
        "platform": "清华大学出版社",
        "source": "清华大学出版社",
        "material_type": "教材目录/简介",
        "url": "https://www.tup.tsinghua.edu.cn/bookscenter/book_06402703.html",
        "summary": "经典中文机器学习教材，覆盖基础概念、监督学习、经典算法、进阶专题和习题。",
        "integration_mode": "引用官方图书页；用目录映射知识点；结合自有知识库生成讲解、练习和错题诊断。",
        "copyright_note": "正文不自动入库；仅使用官方公开简介、目录和资源下载入口。",
        "concepts": ["machine_learning", "supervised_learning", "model_evaluation"],
        "modalities": ["text", "exercise"],
        "base_score": 92,
    },
    {
        "title": "清华大学出版社《机器学习方法（第2版）》",
        "platform": "清华大学出版社",
        "source": "清华大学出版社",
        "material_type": "教材目录/简介",
        "url": "https://www.tup.tsinghua.edu.cn/bookscenter/book_10948801.html",
        "summary": "覆盖监督学习、无监督学习、深度学习和强化学习等机器学习方法，适合进阶补充阅读和章节化学习路线。",
        "integration_mode": "引用官方图书页；抽取目录主题作为进阶路径；生成配套例题和代码注释案例。",
        "copyright_note": "正文和课件需以官方试读、资源下载或授权上传为准。",
        "concepts": ["machine_learning", "supervised_learning", "deep_learning"],
        "modalities": ["text", "exercise"],
        "base_score": 90,
    },
    {
        "title": "蒲公英书《神经网络与深度学习》在线开放资源",
        "platform": "蒲公英书",
        "source": "邱锡鹏等",
        "material_type": "开放教材/可视化资源",
        "url": "https://nndl.ai/",
        "summary": "蒲公英书系列提供神经网络与深度学习、案例实践和大模型与智能体等开放学习入口，包含序列建模、注意力与 Transformer 可视化资源。",
        "integration_mode": "引用开放教材入口和可视化资源；系统据此生成章节导读、结构图、代码注释案例和复盘题。",
        "copyright_note": "只引用公开入口和开放资源说明；具体 PDF、代码和图示按原站授权要求使用。",
        "concepts": ["deep_learning", "lstm", "transformer", "nlp_llm"],
        "modalities": ["text", "diagram", "code", "exercise"],
        "base_score": 94,
    },
    {
        "title": "机械工业出版社《人工智能基础与应用》数字教材",
        "platform": "机械工业出版社教育服务网",
        "source": "机械工业出版社",
        "material_type": "数字教材",
        "url": "https://www.cmpedu.com/books/bookNums/21.htm",
        "summary": "人工智能基础与应用相关数字教材入口，适合演示课程知识库与出版社资源的关联。",
        "integration_mode": "链接引用；结合课程知识库生成章节导学、概念卡片和练习题。",
        "copyright_note": "数字教材正文按平台授权使用；系统不自动复制付费或登录后内容。",
        "concepts": ["ai_intro", "machine_learning"],
        "modalities": ["text", "exercise"],
        "base_score": 84,
    },
    {
        "title": "机械工业出版社《人工智能安全基础》数字教材",
        "platform": "机械工业出版社教育服务网",
        "source": "机械工业出版社",
        "material_type": "数字教材",
        "url": "https://www.cmpedu.com/books/bookNums/218.htm",
        "summary": "人工智能安全方向数字教材入口，可作为人工智能课程的拓展阅读、安全伦理、隐私保护和信息安全基础模块补充。",
        "integration_mode": "链接引用；用于拓展阅读、课程安全模块、信息安全导学和讨论题生成。",
        "copyright_note": "仅引用公开入口；正文、课件和下载文件需授权后入库。",
        "concepts": ["ai_intro", "ai_safety", "information_security"],
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
    matched_concepts = list(dict.fromkeys([
        concept_id
        for concept_id in resource.get("concepts", [])
        if concept_id in concept_ids
    ]))
    return {
        "title": resource["title"],
        "platform": resource["platform"],
        "source": resource["source"],
        "source_type": resource["material_type"],
        "material_type": resource["material_type"],
        "url": resource["url"],
        "open_url": resource["url"],
        "language": "中文",
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
                "strategy": "课程知识点目录匹配",
                "total_count": 0,
            },
        }

    items = [
        _normalize_resource(resource, concept_ids)
        for resource in TEACHING_RESOURCE_CATALOG
        if _resource_match_score(resource, concept_ids) > 0
    ]
    items.sort(
        key=lambda item: (
            len(item.get("matched_concepts", [])),
            item.get("score", 0),
            item.get("title", ""),
        ),
        reverse=True,
    )
    limited = items[:max(1, min(limit, 30))]
    return {
        "items": limited,
        "meta": {
            "query": query or "",
            "matched_concepts": _concept_labels(concept_ids),
            "strategy": "课程知识点目录匹配",
            "copyright_policy": "只引用公开入口、官方简介、目录和授权资料；不抓取教材正文，不下载视频。",
            "total_count": len(limited),
            "sources": sorted(list({item.get("platform", "") for item in limited if item.get("platform")})),
            "material_types": sorted(list({item.get("material_type", "") for item in limited if item.get("material_type")})),
        },
    }


def format_teaching_sources_for_prompt(result: Dict, max_items: int = 6) -> str:
    items = (result or {}).get("items") or []
    if not items:
        return "本轮没有匹配到目录化外部教学资料；生成内容只使用课程知识库依据，并标注需要管理员补充授权资料。"

    lines = [
        "以下资料来自系统维护的课程教学资料目录，只引用公开入口、官方简介、目录或授权内容。"
    ]
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
    lines = []
    for item in items[:max_items]:
        lines.append(
            f"- [{item.get('title', '教学资料')}]({item.get('open_url') or item.get('url')})"
            f"（{item.get('platform') or item.get('source') or '教学平台'}）"
        )
    return "\n".join(lines)


def _card_id(prefix: str, title: str, concepts: List[str]) -> str:
    digest = hashlib.md5(f"{prefix}|{title}|{'|'.join(concepts)}".encode("utf-8")).hexdigest()[:10].upper()
    return f"AUTO-{prefix}-{digest}"


def _card_score(base_score: int, concept_ids: List[str], sources: List[Dict]) -> int:
    return min(100, base_score + len(concept_ids) * 3 + len(sources) * 2)


def _card_common(
    prefix: str,
    title: str,
    resource_type: str,
    concept_ids: List[str],
    sources: List[Dict],
    score: int,
    reason: str,
) -> Dict:
    labels = _concept_labels(concept_ids)
    return {
        "id": _card_id(prefix, title, concept_ids),
        "title": title,
        "type": resource_type,
        "status": "系统推送",
        "uploader": "教学资源推荐 Agent",
        "applicant_username": "",
        "time": "",
        "source": "课程知识库 + 教学资料目录",
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
    exercise_sources = [item for item in sources if "exercise" in item.get("modalities", [])]

    if video_sources:
        title = f"{topic}主题导学包"
        card = _card_common(
            "MEDIA",
            title,
            "主题学习包",
            concept_ids,
            video_sources,
            _card_score(76, concept_ids, video_sources),
            "系统将公开视频/公开课入口整理为观看任务、核心图解和复盘问题。",
        )
        card.update({
            "summary": f"围绕「{topic}」推送公开视频/公开课入口，并组织成可执行的观看与复盘任务。",
            "content": f"""## {topic}主题导学包

### 学习方式
1. 先看课程/视频入口，建立整体印象。
2. 对照本系统课程知识库中的核心概念，补齐定义和公式。
3. 完成观看后复盘：用自己的话解释关键概念，并写出一个应用场景。

### 可参考来源
{_source_lines(video_sources)}

### 版权边界
系统只引用公开入口和官方简介，不下载、不复制课程视频或课件正文。"""
        })
        cards.append(card)

    if text_sources:
        title = f"{topic}教材导读卡"
        card = _card_common(
            "TEXTBOOK",
            title,
            "拓展阅读材料",
            concept_ids,
            text_sources,
            _card_score(74, concept_ids, text_sources),
            "系统将教材目录、课程页和公开简介整理成章节导读。",
        )
        card.update({
            "summary": f"围绕「{topic}」推送教材、课程页或数字教材入口，并生成适合当前阶段的阅读顺序。",
            "content": f"""## {topic}教材导读卡

### 阅读目标
- 明确这一主题在高校课程中的章节位置。
- 优先掌握定义、典型例题、常见误区和应用场景。
- 阅读后回到系统资源库完成练习与错题诊断。

### 建议阅读顺序
1. 先浏览教材目录或章节简介，定位相关小节。
2. 重点阅读概念定义、例题说明和评价指标。
3. 把不理解的概念记录到学习评价页，触发后续诊断和路线调整。

### 可参考来源
{_source_lines(text_sources)}

### 版权边界
教材正文、样章和课件只使用官方公开试读或授权上传内容；系统不抓取付费正文。"""
        })
        cards.append(card)

    title = f"{topic}知识结构图解"
    card = _card_common(
        "MAP",
        title,
        "知识点思维导图",
        concept_ids,
        sources,
        _card_score(72, concept_ids, sources),
        "系统将课程知识点和资料目录整理成概念关系图。",
    )
    card.update({
        "summary": f"围绕「{topic}」整理图解式学习路线，帮助定位前后置知识。",
        "content": f"""## {topic}知识结构图解

```mermaid
flowchart TD
  A["学习目标"] --> B["核心概念"]
  B --> C["典型例题"]
  C --> D["练习巩固"]
  D --> E["错题诊断"]
  E --> F["资源再推送"]
```

### 使用方式
- 从“核心概念”开始补定义。
- 遇到公式或指标时进入“典型例题”。
- 错题较多时回到“资源再推送”，系统会继续调整推荐。

### 来源依据
{_source_lines(sources)}"""
    })
    cards.append(card)

    if exercise_sources:
        title = f"{topic}巩固练习与实践任务"
        card = _card_common(
            "PRACTICE",
            title,
            "不同类型练习题目",
            concept_ids,
            exercise_sources,
            _card_score(70, concept_ids, exercise_sources),
            "系统将课程小节和教材入口转成检测性练习与复盘任务。",
        )
        card.update({
            "summary": f"围绕「{topic}」推送配套练习与实践任务，用来检测理解、定位错因并触发后续诊断。",
            "content": f"""## {topic}巩固练习与实践任务

### 练习任务
1. 用一句话解释本主题的核心概念。
2. 列出 2 个常见误区，并给出纠正方法。
3. 结合课程知识库，完成一道基础题和一道迁移题。

### 实践任务
- 找一个真实学习或业务场景，说明该知识点如何发挥作用。
- 如果涉及代码，请写出关键步骤和注释，不要求完整项目。

### 参考来源
{_source_lines(exercise_sources)}

### 后续动作
完成后进入“学习评价”，系统会根据结果更新画像并调整资源推送。"""
        })
        cards.append(card)

    cards.sort(
        key=lambda item: (
            item.get("_recommend_rank", 0),
            item.get("type", ""),
            item.get("title", ""),
        ),
        reverse=True,
    )
    return cards[:max(1, min(limit, len(cards)))]
