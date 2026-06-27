from typing import Dict, List

from app.services.data_services import (
    deep_learning_course_map_service,
    resource_artifact_type_service as artifact_types,
)


DEEP_LEARNING_COURSE_NOTE_SECTIONS = [
    "一、学习定位与适用对象",
    "二、本节知识点在《深度学习》课程中的位置",
    "三、学习目标",
    "四、前置知识回顾",
    "五、核心概念逐项讲解",
    "六、关键公式、计算过程或算法流程",
    "七、结合深度学习模型的具体例子",
    "八、代码或伪代码示例",
    "九、常见误区与纠正",
    "十、课堂小练习",
    "十一、学习检查清单",
    "十二、下一步学习建议",
]


COURSE_NOTE_QUALITY_RULES = {
    "min_chars": 1800,
    "min_headings": 8,
    "min_core_concepts": 5,
    "min_examples": 2,
    "min_exercises": 3,
    "must_include_topic": True,
    "must_include_course_position": True,
    "must_include_prerequisites": True,
    "must_include_misconceptions": True,
    "must_include_next_step": True,
}


TOPIC_SPECIFIC_REQUIREMENTS = {
    "dl_cnn": ["卷积核", "步幅", "填充", "特征图", "局部连接", "参数共享", "输出尺寸计算"],
    "dl_backprop": ["损失函数", "梯度", "链式法则", "前向传播", "反向传播", "参数更新"],
    "dl_transformer": ["Query", "Key", "Value", "注意力分数", "Softmax", "多头注意力", "位置编码"],
    "dl_optimization": ["SGD", "Momentum", "Adam", "学习率", "梯度下降", "收敛", "局部最优"],
    "dl_regularization": ["过拟合", "L1", "L2", "Dropout", "BatchNorm", "数据增强", "早停"],
    "dl_pytorch": ["Tensor", "Dataset", "DataLoader", "nn.Module", "训练循环", "loss.backward", "optimizer.step"],
    "dl_prereq": ["矩阵", "向量", "张量 shape", "梯度", "链式法则", "损失函数", "训练集", "验证集", "测试集"],
}


UNIT_REQUIREMENT_KEYS = {
    "dl_cnn_conv_basic": "dl_cnn",
    "dl_backprop_basic": "dl_backprop",
    "dl_transformer_attention": "dl_transformer",
    "dl_optimization_adam": "dl_optimization",
    "dl_regularization_dropout_bn": "dl_regularization",
    "dl_pytorch_practice": "dl_pytorch",
    "dl_prereq_math_ml": "dl_prereq",
}


DEEP_LEARNING_SPECS = {
    artifact_types.COURSE_NOTE: {
        "requirements": [
            "课程定位",
            "知识点定义",
            "为什么需要该知识点",
            "核心概念逐项解释",
            "公式或算法流程",
            "深度学习模型中的作用",
            "具体例子",
            "代码或伪代码",
            "常见误区",
            "自测题",
            "下一步学习建议",
        ],
        "quality_constraints": [
            "必须紧扣当前知识点，不得只写通用深度学习概述",
            "必须解释该知识点在深度学习课程中的位置",
            "必须包含不少于 5 个核心概念解释",
            "必须包含至少 2 个具体例子",
            "必须包含至少 3 道自测题",
            "正文不少于 1800 个中文字符",
            "禁止只输出提纲式摘要",
        ],
    },
    "专业课程讲解文档": {
        "requirements": [
            "课程定位",
            "知识点定义",
            "为什么需要该知识点",
            "核心概念逐项解释",
            "公式或算法流程",
            "深度学习模型中的作用",
            "具体例子",
            "代码或伪代码",
            "常见误区",
            "自测题",
            "下一步学习建议",
        ],
        "quality_constraints": [
            "必须紧扣当前知识点，不得只写通用深度学习概述",
            "必须解释该知识点在深度学习课程中的位置",
            "必须包含不少于 5 个核心概念解释",
            "必须包含至少 2 个具体例子",
            "必须包含至少 3 道自测题",
            "正文不少于 1800 个中文字符",
            "禁止只输出提纲式摘要",
        ],
    },
    artifact_types.MIND_MAP: {
        "requirements": ["中心主题", "先修知识", "核心概念", "公式或流程", "模型应用", "易错点", "后续知识点"],
    },
    artifact_types.EXERCISE_SET: {
        "requirements": ["选择题", "判断题", "计算题", "简答题", "代码理解题", "实验分析题", "标准答案", "详细解析", "对应知识点"],
    },
    artifact_types.PROJECT_BRIEF: {
        "requirements": ["任务背景", "任务目标", "数据或场景", "实现步骤", "代码骨架", "提交物", "评分标准", "扩展挑战"],
    },
}


def is_course_note(resource_type: str) -> bool:
    normalized = artifact_types.normalize_artifact_type(resource_type)
    return normalized in {artifact_types.COURSE_NOTE, "专业课程讲解文档"}


def is_deep_learning_context(subject_category: str = "", semantic_result: Dict = None) -> bool:
    semantic_result = semantic_result or {}
    return (
        semantic_result.get("course_id") == deep_learning_course_map_service.COURSE_ID
        or semantic_result.get("subject_category") == "deep_learning"
        or subject_category == "deep_learning"
        or bool(semantic_result.get("deep_learning_course_map"))
        or bool(semantic_result.get("ai_course_map"))
    )


def get_deep_learning_spec(resource_type: str) -> Dict:
    normalized = artifact_types.normalize_artifact_type(resource_type)
    return DEEP_LEARNING_SPECS.get(normalized) or DEEP_LEARNING_SPECS.get(resource_type, {})


def get_topic_specific_terms(unit_id: str = "", topic: str = "") -> List[str]:
    key = UNIT_REQUIREMENT_KEYS.get(unit_id or "")
    if not key:
        compact_topic = str(topic or "").lower()
        if any(word in compact_topic for word in ["cnn", "卷积"]):
            key = "dl_cnn"
        elif "反向传播" in compact_topic or "backprop" in compact_topic:
            key = "dl_backprop"
        elif "transformer" in compact_topic or "注意力" in compact_topic:
            key = "dl_transformer"
        elif any(word in compact_topic for word in ["优化", "adam", "sgd", "学习率"]):
            key = "dl_optimization"
        elif any(word in compact_topic for word in ["正则", "dropout", "batchnorm", "过拟合"]):
            key = "dl_regularization"
        elif "pytorch" in compact_topic or "torch" in compact_topic:
            key = "dl_pytorch"
        elif any(word in compact_topic for word in ["前置", "矩阵", "梯度", "链式法则"]):
            key = "dl_prereq"
    return list(TOPIC_SPECIFIC_REQUIREMENTS.get(key or "", []))


def format_evidence_chunks(evidence_chunks: List[Dict]) -> str:
    if not evidence_chunks:
        return "当前知识库中该知识点证据不足，已生成知识库补充任务。"

    lines = []
    for index, item in enumerate(evidence_chunks, start=1):
        lines.append(
            "\n".join([
                f"{index}. evidence_id: {item.get('evidence_id') or item.get('id') or 'unknown'}",
                f"   title: {item.get('title', '')}",
                f"   source_path: {item.get('source_path') or item.get('source', '')}",
                f"   content_excerpt: {item.get('content_excerpt') or item.get('excerpt', '')}",
            ])
        )
    return "\n".join(lines)


def build_course_note_prompt(plan_item: Dict, profile: Dict, intent: str, evidence_chunks: List[Dict], teaching_sources_prompt: str = "") -> str:
    course_match = plan_item.get("deep_learning_course_map") or plan_item.get("ai_course_map") or {}
    unit = course_match.get("unit") or deep_learning_course_map_service.get_unit(plan_item.get("unit_id", "")) or {}
    topic = plan_item.get("unit_title") or course_match.get("normalized_topic") or plan_item.get("topic") or "深度学习知识点"
    topic_terms = get_topic_specific_terms(plan_item.get("unit_id", ""), topic)
    sections = "\n".join(f"- {item}" for item in DEEP_LEARNING_COURSE_NOTE_SECTIONS)
    constraints = "\n".join(f"- {item}" for item in plan_item.get("quality_constraints", []))
    evidence_text = format_evidence_chunks(evidence_chunks)

    return f"""
你是高校《深度学习》课程教师，正在为学生生成一份可直接学习的课程讲义。
不要只输出提纲，不要只写摘要，不要泛泛介绍。
必须紧扣当前知识点，结合课程图谱、学生画像和证据材料生成详细讲解。

输出边界：
- 只输出 JSON 对象
- 不输出解释
- 不输出思考过程
- 不要用 Markdown 代码块包裹 JSON
- sections 必须是对象数组，items 必须是字符串数组
- 每个 items 字符串要写成完整段落或完整题目，不要只写短词

输入上下文：
1. 当前课程：深度学习
2. 当前章节：{plan_item.get('chapter') or course_match.get('chapter') or unit.get('chapter_id') or ''}
3. 当前 unit_id：{plan_item.get('unit_id') or unit.get('unit_id') or ''}
4. 当前知识点标题：{topic}
5. aliases：{'、'.join(unit.get('aliases', []) or course_match.get('matched_aliases', []) or [])}
6. prerequisites：{'、'.join(unit.get('prerequisites', []) or course_match.get('prerequisites', []) or [])}
7. learning_outcomes：{'；'.join(unit.get('learning_outcomes', []) or course_match.get('learning_outcomes', []) or [])}
8. common_misconceptions：{'；'.join(unit.get('common_misconceptions', []) or course_match.get('common_misconceptions', []) or [])}
9. 学生画像：知识基础={profile.get('level', '未确认')}；学习目标={intent}；偏好={profile.get('preference', '') or profile.get('style', '') or '未确认'}；短板={profile.get('weakness', '') or profile.get('weak_points', '') or '未确认'}；实践能力={profile.get('practice_ability', '') or '未确认'}
10. evidence_chunks：
{evidence_text}
11. resource_type：{plan_item.get('type')}
12. quality_constraints：
{constraints or '- 必须生成完整课程讲义'}

主题专项必含词：{'、'.join(topic_terms) if topic_terms else '按课程图谱核心概念覆盖'}

输出格式要求：
JSON 字段必须为：
{{
  "summary": "不超过 120 字的讲义摘要",
  "sections": [
    {{"heading": "一、学习定位与适用对象", "items": ["完整段落"]}}
  ],
  "source_notes": ["evidence_id: xxx"]
}}

sections 必须覆盖以下 12 个二级标题，标题文字必须一致：
{sections}

最低输出要求：
- 正文不少于 1800 个中文字符。
- 至少包含 8 个二级标题。
- 至少解释 5 个核心概念。
- 至少给出 2 个具体例子。
- 至少给出 3 道自测题，并附参考答案。
- 如果涉及公式或计算，必须解释每个符号的含义。
- 如果涉及代码实践，必须给出 Python/PyTorch 代码或伪代码。
- 必须在“参考依据”或 source_notes 中引用 evidence_id。
- 不得虚构教材、MOOC、论文或链接；证据不足时明确写“需管理员补充证据”，不要编造来源。

外部教学资料候选：
{teaching_sources_prompt}
"""
