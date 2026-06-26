import re
from typing import Dict, List, Optional


COURSE_ID = "deep_learning"
COURSE_NAME = "深度学习"
COURSE_DISPLAY_NAME = "《深度学习》"
COURSE_POSITIONING = "面向人工智能、计算机科学与技术、软件工程、电子信息等专业本科高年级或研究生低年级学生的专业核心课程"


DEEP_LEARNING_CHAPTERS = [
    {"chapter_id": "chapter_01_intro", "title": "深度学习导论与学习诊断"},
    {"chapter_id": "chapter_02_prerequisites", "title": "数学与机器学习前置知识"},
    {"chapter_id": "chapter_03_neural_network", "title": "神经网络基础与感知机"},
    {"chapter_id": "chapter_04_backpropagation", "title": "前向传播、损失函数与反向传播"},
    {"chapter_id": "chapter_05_optimization", "title": "优化算法与训练技巧"},
    {"chapter_id": "chapter_06_regularization", "title": "正则化与泛化"},
    {"chapter_id": "chapter_07_cnn", "title": "卷积神经网络 CNN"},
    {"chapter_id": "chapter_08_rnn_lstm", "title": "循环神经网络 RNN/LSTM/GRU"},
    {"chapter_id": "chapter_09_transformer", "title": "Attention 与 Transformer"},
    {"chapter_id": "chapter_10_generative_models", "title": "自编码器、GAN 与扩散模型入门"},
    {"chapter_id": "chapter_11_pytorch_practice", "title": "PyTorch 深度学习工程实践"},
    {"chapter_id": "chapter_12_final_project", "title": "课程综合项目"},
]


DEEP_LEARNING_UNITS = [
    {
        "unit_id": "dl_intro_diagnosis",
        "chapter_id": "chapter_01_intro",
        "title": "深度学习导论与学习诊断",
        "aliases": ["深度学习", "deep learning", "dl", "深度学习入门", "深度学习课程", "神经网络学习路线"],
        "prerequisites": ["Python 基础", "线性代数基础", "机器学习基本概念"],
        "learning_outcomes": ["说明深度学习解决的问题", "区分深度学习与传统机器学习", "完成学习基础诊断"],
        "core_concepts": ["表示学习", "神经网络", "端到端学习", "数据驱动"],
        "formulas": [],
        "common_misconceptions": ["把深度学习等同于所有人工智能", "忽略数据和训练成本"],
        "visual_suggestions": ["课程地图", "学习路径时间轴"],
        "code_lab": "运行一个最小 MLP 分类示例",
        "exercise_blueprints": ["概念辨析题", "学习基础诊断题"],
        "resource_focus": ["课程讲解", "学习诊断", "学习路径"],
        "difficulty": "beginner",
    },
    {
        "unit_id": "dl_prereq_math_ml",
        "chapter_id": "chapter_02_prerequisites",
        "title": "数学与机器学习前置知识",
        "aliases": ["前置知识", "线性代数", "矩阵", "概率", "梯度", "导数", "机器学习基础", "损失函数前置"],
        "prerequisites": ["高等数学", "线性代数", "概率统计", "Python 基础"],
        "learning_outcomes": ["解释矩阵乘法在神经网络中的作用", "理解梯度和损失函数", "区分训练集、验证集和测试集"],
        "core_concepts": ["矩阵运算", "梯度", "概率分布", "训练/验证/测试划分"],
        "formulas": ["矩阵乘法", "链式法则", "经验风险最小化"],
        "common_misconceptions": ["只会套公式但不理解梯度方向", "混淆验证集与测试集"],
        "visual_suggestions": ["矩阵变换示意图", "训练数据划分图"],
        "code_lab": "用 NumPy 手写线性分类器的前向计算",
        "exercise_blueprints": ["矩阵尺寸题", "梯度方向判断题", "训练集划分题"],
        "resource_focus": ["前置知识自查", "公式图解", "基础练习"],
        "difficulty": "beginner",
    },
    {
        "unit_id": "dl_nn_perceptron",
        "chapter_id": "chapter_03_neural_network",
        "title": "神经网络基础与感知机",
        "aliases": ["感知机", "神经元", "多层感知机", "MLP", "激活函数", "神经网络基础", "全连接网络"],
        "prerequisites": ["矩阵运算", "线性分类", "梯度基本概念"],
        "learning_outcomes": ["解释神经元的线性组合和非线性激活", "画出 MLP 结构", "理解隐藏层表示"],
        "core_concepts": ["神经元", "权重", "偏置", "激活函数", "隐藏层"],
        "formulas": ["z = Wx + b", "a = sigma(z)"],
        "common_misconceptions": ["认为层数越深一定越好", "忽略非线性激活的作用"],
        "visual_suggestions": ["MLP 层级结构图", "激活函数曲线"],
        "code_lab": "用 PyTorch 搭建一个两层 MLP",
        "exercise_blueprints": ["结构标注题", "前向计算题", "激活函数辨析题"],
        "resource_focus": ["结构图", "公式讲解", "PyTorch 入门"],
        "difficulty": "beginner",
    },
    {
        "unit_id": "dl_backprop_basic",
        "chapter_id": "chapter_04_backpropagation",
        "title": "反向传播与损失函数",
        "aliases": ["反向传播", "BP", "backprop", "backpropagation", "链式法则", "前向传播", "损失函数", "梯度传播", "梯度反传"],
        "prerequisites": ["神经网络基础", "链式法则", "损失函数"],
        "learning_outcomes": ["解释前向传播和反向传播的分工", "用链式法则说明梯度如何传递", "识别梯度消失和梯度爆炸现象"],
        "core_concepts": ["前向传播", "损失函数", "链式法则", "梯度", "参数更新"],
        "formulas": ["dL/dw = dL/dz * dz/dw", "theta = theta - lr * gradient"],
        "common_misconceptions": ["把反向传播理解成反向运行模型", "只记公式不理解局部梯度相乘"],
        "visual_suggestions": ["计算图梯度流动画", "链式法则路径高亮"],
        "code_lab": "用 PyTorch autograd 查看梯度",
        "exercise_blueprints": ["链式法则计算题", "梯度方向判断题", "代码补全题"],
        "resource_focus": ["图解", "推导练习", "交互动画", "代码实验"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_optimization_adam",
        "chapter_id": "chapter_05_optimization",
        "title": "优化算法与训练技巧",
        "aliases": ["优化器", "SGD", "Momentum", "Adam", "学习率", "学习率调度", "梯度下降", "训练技巧", "optimizer"],
        "prerequisites": ["反向传播", "梯度下降", "损失函数"],
        "learning_outcomes": ["比较 SGD、Momentum 和 Adam", "解释学习率对收敛的影响", "能观察训练曲线并调整超参数"],
        "core_concepts": ["SGD", "Momentum", "Adam", "学习率", "收敛", "训练曲线"],
        "formulas": ["theta = theta - lr * g", "一阶矩估计", "二阶矩估计"],
        "common_misconceptions": ["以为 Adam 总是最优", "忽略学习率过大导致震荡"],
        "visual_suggestions": ["损失曲线对比", "优化路径动画"],
        "code_lab": "比较 SGD 与 Adam 在同一模型上的训练曲线",
        "exercise_blueprints": ["参数选择题", "曲线分析题", "实验报告题"],
        "resource_focus": ["曲线分析", "实验对比", "调参任务"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_regularization_dropout_bn",
        "chapter_id": "chapter_06_regularization",
        "title": "正则化、Dropout 与 BatchNorm",
        "aliases": ["正则化", "L1", "L2", "Dropout", "BatchNorm", "Batch Normalization", "数据增强", "早停", "过拟合", "泛化"],
        "prerequisites": ["训练集/验证集", "损失函数", "优化算法"],
        "learning_outcomes": ["解释过拟合与泛化", "比较 L1/L2、Dropout、BatchNorm、数据增强", "设计缓解过拟合的实验方案"],
        "core_concepts": ["过拟合", "泛化", "Dropout", "BatchNorm", "数据增强", "早停"],
        "formulas": ["L2 penalty", "BatchNorm 标准化公式"],
        "common_misconceptions": ["把 BatchNorm 当作简单归一化预处理", "训练和推理时 Dropout 行为混淆"],
        "visual_suggestions": ["训练/验证曲线对比", "Dropout 掩码示意图"],
        "code_lab": "在 PyTorch 模型中加入 Dropout 和 BatchNorm 对比泛化效果",
        "exercise_blueprints": ["现象判断题", "实验分析题", "代码阅读题"],
        "resource_focus": ["实验分析", "对比表", "代码实践"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_cnn_conv_basic",
        "chapter_id": "chapter_07_cnn",
        "title": "卷积神经网络中的卷积操作",
        "aliases": ["CNN", "cnn", "卷积神经网络", "卷积", "卷积层", "卷积核", "Convolutional Neural Network", "特征图", "池化", "图像分类"],
        "prerequisites": ["矩阵运算", "神经网络基础", "前向传播"],
        "learning_outcomes": ["解释卷积核的作用", "计算特征图尺寸", "理解局部连接和参数共享"],
        "core_concepts": ["卷积核", "步幅", "填充", "感受野", "特征图", "池化"],
        "formulas": ["输出尺寸 = floor((输入尺寸 + 2*padding - kernel_size) / stride) + 1"],
        "common_misconceptions": ["把卷积核当成固定图片滤镜", "不理解通道数变化", "混淆 padding 和 stride 对输出尺寸的影响"],
        "visual_suggestions": ["卷积滑窗动画", "输入特征图到输出特征图流程图"],
        "code_lab": "用 PyTorch 实现一个简单 CNN 图像分类器",
        "exercise_blueprints": ["尺寸计算题", "概念辨析题", "代码补全题", "实验分析题"],
        "resource_focus": ["图解", "代码实验", "练习题", "交互动画", "视频推荐"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_rnn_lstm_gru",
        "chapter_id": "chapter_08_rnn_lstm",
        "title": "RNN、LSTM 与 GRU 序列建模",
        "aliases": ["RNN", "rnn", "循环神经网络", "LSTM", "lstm", "GRU", "gru", "序列模型", "长短期记忆", "门控机制", "时间序列"],
        "prerequisites": ["反向传播", "神经网络基础", "序列数据"],
        "learning_outcomes": ["解释循环连接如何处理序列", "比较 RNN、LSTM、GRU", "理解长期依赖与梯度问题"],
        "core_concepts": ["隐状态", "长期依赖", "遗忘门", "输入门", "输出门", "门控机制"],
        "formulas": ["h_t = f(x_t, h_{t-1})", "LSTM 门控更新公式"],
        "common_misconceptions": ["认为 LSTM 可以解决所有长序列问题", "混淆门控向量和隐藏状态"],
        "visual_suggestions": ["时间展开图", "LSTM 单元结构图"],
        "code_lab": "用 PyTorch 写一个 LSTM 序列分类或预测实验",
        "exercise_blueprints": ["结构标注题", "门控机制辨析题", "序列预测实验题"],
        "resource_focus": ["结构图", "对比表", "代码实验", "练习题"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_transformer_attention",
        "chapter_id": "chapter_09_transformer",
        "title": "自注意力机制与 Transformer",
        "aliases": ["Transformer", "transformer", "Attention", "attention", "注意力机制", "自注意力", "self attention", "多头注意力", "QKV", "Query", "Key", "Value", "位置编码", "Encoder", "Decoder"],
        "prerequisites": ["矩阵乘法", "神经网络基础", "序列建模"],
        "learning_outcomes": ["解释 Q/K/V 的含义", "计算注意力权重", "说明多头注意力和位置编码的作用"],
        "core_concepts": ["Query", "Key", "Value", "点积注意力", "softmax", "多头注意力", "位置编码"],
        "formulas": ["Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V"],
        "common_misconceptions": ["把注意力权重当成绝对解释", "忽略缩放因子和位置编码"],
        "visual_suggestions": ["Q/K/V 流程图", "attention 权重热力图", "多头并行示意图"],
        "code_lab": "用 PyTorch 实现缩放点积注意力 demo",
        "exercise_blueprints": ["Q/K/V 维度题", "softmax 权重题", "代码补全题"],
        "resource_focus": ["图解", "公式拆解", "代码 demo", "交互动画", "视频推荐"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_generative_intro",
        "chapter_id": "chapter_10_generative_models",
        "title": "自编码器、GAN 与扩散模型入门",
        "aliases": ["自编码器", "AutoEncoder", "AE", "GAN", "生成对抗网络", "扩散模型", "Diffusion", "生成模型", "VAE"],
        "prerequisites": ["神经网络基础", "损失函数", "概率分布"],
        "learning_outcomes": ["区分判别模型和生成模型", "说明自编码器、GAN、扩散模型的核心思路", "理解生成质量评价的基本风险"],
        "core_concepts": ["编码器", "解码器", "生成器", "判别器", "去噪", "潜变量"],
        "formulas": ["重构损失", "GAN min-max 目标", "扩散去噪目标"],
        "common_misconceptions": ["把生成模型等同于图像生成工具", "忽略数据分布和训练不稳定性"],
        "visual_suggestions": ["编码-解码流程图", "GAN 对抗流程图", "扩散去噪过程图"],
        "code_lab": "用 PyTorch 训练一个简单自编码器",
        "exercise_blueprints": ["概念对比题", "流程排序题", "实验观察题"],
        "resource_focus": ["流程图", "对比表", "实验观察"],
        "difficulty": "advanced",
    },
    {
        "unit_id": "dl_pytorch_practice",
        "chapter_id": "chapter_11_pytorch_practice",
        "title": "PyTorch 深度学习工程实践",
        "aliases": ["PyTorch", "pytorch", "torch", "Dataset", "DataLoader", "训练循环", "模型训练", "代码实验", "图像分类实验", "深度学习代码"],
        "prerequisites": ["Python 基础", "神经网络基础", "优化器", "数据集划分"],
        "learning_outcomes": ["搭建 Dataset/DataLoader", "编写模型、损失函数和优化器", "完成训练、验证和保存模型"],
        "core_concepts": ["Tensor", "Dataset", "DataLoader", "Module", "训练循环", "验证集"],
        "formulas": [],
        "common_misconceptions": ["只复制代码不检查 tensor shape", "训练集和验证集混用"],
        "visual_suggestions": ["训练流程图", "模型输入输出 shape 表"],
        "code_lab": "完成 CNN 图像分类 PyTorch 实验",
        "exercise_blueprints": ["代码补全题", "报错排查题", "实验报告题"],
        "resource_focus": ["代码实验", "调参任务", "实验报告模板"],
        "difficulty": "medium",
    },
    {
        "unit_id": "dl_final_project",
        "chapter_id": "chapter_12_final_project",
        "title": "深度学习课程综合项目",
        "aliases": ["综合项目", "课程项目", "项目任务", "图像分类项目", "文本分类项目", "时间序列预测项目", "两周项目", "毕业设计", "项目实战"],
        "prerequisites": ["神经网络基础", "CNN 或 Transformer", "PyTorch 训练流程", "模型评估"],
        "learning_outcomes": ["定义项目目标和数据集", "拆解模型训练与评估步骤", "形成实验报告和展示材料"],
        "core_concepts": ["数据集", "baseline", "训练验证", "指标评估", "误差分析", "项目复盘"],
        "formulas": ["准确率", "召回率", "F1"],
        "common_misconceptions": ["只追求高分不做误差分析", "没有固定训练/验证划分"],
        "visual_suggestions": ["项目路线图", "实验结果对比图"],
        "code_lab": "完成一个图像分类、文本分类或时间序列预测小项目",
        "exercise_blueprints": ["项目拆解题", "实验报告题", "误差分析题"],
        "resource_focus": ["项目任务书", "代码实验", "PPT 大纲", "评价 Rubric"],
        "difficulty": "advanced",
    },
]


CHAPTER_BY_ID = {chapter["chapter_id"]: chapter for chapter in DEEP_LEARNING_CHAPTERS}
UNIT_BY_ID = {unit["unit_id"]: unit for unit in DEEP_LEARNING_UNITS}
DEEP_LEARNING_COURSE_MAP = [
    {
        "chapter_id": chapter["chapter_id"],
        "chapter": chapter["title"],
        "topics": [unit["title"] for unit in DEEP_LEARNING_UNITS if unit["chapter_id"] == chapter["chapter_id"]],
        "aliases": [
            alias
            for unit in DEEP_LEARNING_UNITS
            if unit["chapter_id"] == chapter["chapter_id"]
            for alias in unit.get("aliases", [])
        ],
    }
    for chapter in DEEP_LEARNING_CHAPTERS
]


def _compact(value: str) -> str:
    return re.sub(r"[\s_\-·：:，,。！？!?.、/\\（）()《》]+", "", str(value or "").lower())


def _tokenize(value: str) -> List[str]:
    text = str(value or "").lower()
    return re.findall(r"[a-z0-9+#.]+|[\u4e00-\u9fff]{2,}", text)


def _intent_from_message(message: str) -> str:
    compact = _compact(message)
    if any(word in compact for word in ["错题", "错因", "做错", "算错", "不会这类题", "总是错"]):
        return "evaluation"
    if any(word in compact for word in ["项目", "实战", "两周", "完成一个", "做一个"]):
        return "project"
    if any(word in compact for word in ["代码", "pytorch", "实验", "实现", "训练", "调参"]):
        return "code_lab"
    if any(word in compact for word in ["练习", "题", "刷题", "测验"]):
        return "practice"
    if any(word in compact for word in ["规划", "路线", "计划", "安排", "怎么学", "学习路径", "我要学", "想学", "帮我学", "系统学习", "入门", "怎么入门"]):
        return "path_planning"
    if any(word in compact for word in ["生成", "资源", "资料", "课件", "ppt", "导图", "视频", "动画", "多模态"]):
        return "resource_generation"
    return "concept_explanation"


def _score_unit(unit: Dict, message: str, topic: str = "") -> Dict:
    text = "\n".join([topic or "", message or ""])
    compact_text = _compact(text)
    if not compact_text:
        return {"score": 0.0, "aliases": []}

    matched_aliases = []
    score = 0.0
    for alias in unit.get("aliases", []) + [unit.get("title", "")]:
        compact_alias = _compact(alias)
        if not compact_alias:
            continue
        if compact_alias == compact_text:
            score += 1.0
            matched_aliases.append(alias)
        elif compact_alias in compact_text:
            alias_len = len(compact_alias)
            if alias_len <= 2:
                score += 0.62
            elif alias_len <= 4:
                score += 0.72
            else:
                score += min(0.92, 0.72 + alias_len / 100)
            matched_aliases.append(alias)

    text_tokens = set(_tokenize(text))
    concept_tokens = set()
    for field in ["core_concepts", "prerequisites", "learning_outcomes", "resource_focus"]:
        for item in unit.get(field, []):
            concept_tokens.update(_tokenize(item))
    token_hits = text_tokens & concept_tokens
    if token_hits:
        score += min(0.25, 0.05 * len(token_hits))

    title_tokens = set(_tokenize(unit.get("title", "")))
    title_hits = text_tokens & title_tokens
    if title_hits:
        score += min(0.18, 0.06 * len(title_hits))

    # Project-like requests about image classification should prefer the project unit
    # unless the user explicitly asks for CNN concept explanation.
    compact_unit_title = _compact(unit.get("title", ""))
    if "图像分类" in compact_text and "项目" in compact_text and "综合项目" in compact_unit_title:
        score += 0.35
    if "图像分类" in compact_text and "pytorch" in compact_text and "pytorch" in compact_unit_title:
        score += 0.35

    return {
        "score": round(min(score, 1.0), 3),
        "aliases": list(dict.fromkeys(matched_aliases)),
    }


def get_unit(unit_id: str) -> Optional[Dict]:
    unit = UNIT_BY_ID.get(unit_id)
    return dict(unit) if unit else None


def list_units() -> List[Dict]:
    return [dict(unit) for unit in DEEP_LEARNING_UNITS]


def is_deep_learning_scope(topic: str = "", message: str = "") -> bool:
    return bool(match_deep_learning_topic(topic, message).get("matched"))


def match_deep_learning_topic(topic: str = "", message: str = "") -> Dict:
    raw_topic = str(topic or "").strip()
    raw_message = str(message or "").strip()
    combined = "\n".join([raw_topic, raw_message])
    compact = _compact(combined)
    if not compact:
        return {"matched": False}

    best_unit = None
    best = {"score": 0.0, "aliases": []}
    for unit in DEEP_LEARNING_UNITS:
        current = _score_unit(unit, raw_message, raw_topic)
        if current["score"] > best["score"]:
            best_unit = unit
            best = current

    if not best_unit:
        return {"matched": False}

    # A general deep-learning request is still in scope even if it does not name a
    # detailed knowledge unit yet.
    general_scope = any(alias in compact for alias in ["深度学习", "deeplearning", "神经网络"])
    if best["score"] < 0.58 and not general_scope:
        return {"matched": False}

    if best["score"] < 0.58 and general_scope:
        best_unit = UNIT_BY_ID["dl_intro_diagnosis"]
        best = {"score": 0.62, "aliases": ["深度学习"]}

    chapter = CHAPTER_BY_ID.get(best_unit["chapter_id"], {})
    need_type = _intent_from_message(combined)
    requires_code = (
        need_type in {"code_lab", "project"}
        or any(word in compact for word in ["代码", "pytorch", "torch", "实验", "实现", "训练", "项目"])
        or "代码实验" in " ".join(best_unit.get("resource_focus", []))
    )
    requires_multimodal = (
        any(word in compact for word in ["图解", "动画", "导图", "视频", "多模态", "可视化"])
        or any(item in best_unit.get("resource_focus", []) for item in ["图解", "交互动画", "视频推荐"])
    )

    confidence = best["score"]
    return {
        "matched": True,
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "raw_topic": raw_topic or raw_message,
        "normalized_topic": best_unit["title"],
        "chapter_id": best_unit["chapter_id"],
        "chapter": chapter.get("title", ""),
        "unit_id": best_unit["unit_id"],
        "unit": dict(best_unit),
        "topic": best_unit["title"],
        "intent": need_type,
        "learning_need_type": need_type,
        "scope_type": "in_course",
        "difficulty": best_unit.get("difficulty", "beginner"),
        "requires_code": requires_code,
        "requires_multimodal": requires_multimodal,
        "confidence": round(confidence, 2),
        "matched_aliases": best["aliases"],
        "matched_alias": best["aliases"][0] if best["aliases"] else "",
        "core_topics": best_unit.get("core_concepts", []),
        "prerequisites": best_unit.get("prerequisites", []),
        "resource_focus": best_unit.get("resource_focus", []),
        "practice_tasks": [best_unit.get("code_lab", "")] + best_unit.get("exercise_blueprints", []),
        "learning_outcomes": best_unit.get("learning_outcomes", []),
        "common_misconceptions": best_unit.get("common_misconceptions", []),
        "visual_suggestions": best_unit.get("visual_suggestions", []),
        "formulas": best_unit.get("formulas", []),
    }


def format_course_map_for_prompt(course_match: Dict) -> str:
    if not course_match or not course_match.get("matched"):
        return f"未匹配到{COURSE_DISPLAY_NAME}课程图谱章节。"

    unit = course_match.get("unit") or {}
    return "\n".join([
        f"课程：{COURSE_DISPLAY_NAME}",
        f"章节：{course_match.get('chapter') or unit.get('chapter_id') or ''}",
        f"知识单元：{course_match.get('normalized_topic') or course_match.get('topic') or unit.get('title') or ''}",
        f"知识单元 ID：{course_match.get('unit_id') or unit.get('unit_id') or ''}",
        f"核心概念：{'、'.join(course_match.get('core_topics') or unit.get('core_concepts') or [])}",
        f"前置知识：{'、'.join(course_match.get('prerequisites') or unit.get('prerequisites') or []) or '无'}",
        f"学习产出：{'；'.join(course_match.get('learning_outcomes') or unit.get('learning_outcomes') or [])}",
        f"常见误区：{'；'.join(course_match.get('common_misconceptions') or unit.get('common_misconceptions') or [])}",
        f"推荐资源重点：{'、'.join(course_match.get('resource_focus') or unit.get('resource_focus') or [])}",
        f"推荐实践任务：{'；'.join(course_match.get('practice_tasks') or [])}",
    ])


def course_map_payload() -> Dict:
    chapters = []
    for chapter in DEEP_LEARNING_CHAPTERS:
        units = [
            dict(unit)
            for unit in DEEP_LEARNING_UNITS
            if unit.get("chapter_id") == chapter["chapter_id"]
        ]
        chapters.append({**chapter, "units": units})
    return {
        "course_id": COURSE_ID,
        "course_name": COURSE_NAME,
        "course_display_name": COURSE_DISPLAY_NAME,
        "course_positioning": COURSE_POSITIONING,
        "chapters": chapters,
        "units": list_units(),
        "unit_count": len(DEEP_LEARNING_UNITS),
    }
