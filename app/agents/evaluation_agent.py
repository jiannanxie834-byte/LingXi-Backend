TOPIC_KEYWORDS = [
    ("计算机网络", ["计网", "网络", "tcp", "udp", "三次握手", "四次挥手", "http", "https"]),
    ("Python 数据分析", ["python", "pandas", "数据分析", "numpy", "可视化", "matplotlib"]),
    ("人工智能导论", ["人工智能", "机器学习", "深度学习", "模型", "神经网络", "分类", "训练"]),
    ("高等数学", ["数学", "高数", "微积分", "导数", "积分", "极限", "函数", "建模"]),
    ("大学物理", ["物理", "力学", "电磁", "实验", "速度", "加速度", "牛顿", "能量"]),
    ("大学英语", ["英语", "阅读", "写作", "作文", "口语", "听力", "翻译", "词汇"]),
]


def _infer_topic(message: str):
    lowered = (message or "").lower()
    for topic, keywords in TOPIC_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return topic
    return "人工智能导论"


def _infer_intent(message: str):
    text = message or ""
    if any(word in text for word in ["规划", "路线", "怎么学", "计划", "安排"]):
        return "路径规划"
    if any(word in text for word in ["资源", "资料", "生成", "文档", "导图"]):
        return "生成资源"
    if any(word in text for word in ["题", "练习", "考试", "测验", "刷题"]):
        return "练习巩固"
    if any(word in text for word in ["项目", "实践", "实操", "案例", "实验", "应用"]):
        return "实操训练"
    if any(word in text for word in ["不会", "不懂", "解释", "讲一下", "原理", "为什么"]):
        return "概念讲解"
    return "综合学习"


def run(message: str):
    return {
        "intent": _infer_intent(message),
        "topic": _infer_topic(message),
        "score": 80
    }
