import datetime
import json
import unittest

from app.models.schemas import ResourceArtifact
from app.services.data_services import resource_artifact_type_service as artifact_types
from app.services.data_services import (
    content_guard_service,
    resource_artifact_service,
    resource_quality_gate,
)
from app.services.data_services.resource_quality_gate import validate_teaching_quality


def _complete_multihead_attention_note():
    sections = [
        (
            "学习定位与适用对象",
            "多头注意力是 Transformer 章节中的核心知识点，适合已经理解矩阵乘法、向量相似度和基本神经网络前向传播的学生。"
            "本讲义的目标不是泛泛介绍深度学习，而是帮助学生把 Query、Key、Value、注意力分数、Softmax、head 拼接 concat 和输出投影连成一条可计算的流程。"
            "如果学生基础较弱，可以先复习张量形状、矩阵乘法和序列建模。"
        ),
        (
            "本节知识点在《深度学习》课程中的位置",
            "多头注意力位于 Attention 与 Transformer 单元，是从 RNN 序列建模过渡到并行序列建模的重要桥梁。"
            "它承接点积注意力、缩放点积注意力和位置编码，后续会连接 Transformer Encoder、Decoder、预训练语言模型和视觉 Transformer。"
        ),
        (
            "前置知识回顾",
            "前置知识包括矩阵乘法、线性映射、Softmax 归一化和张量 shape。"
            "学生需要知道输入序列会被映射成 Query、Key、Value 三组向量，并且每个 head 都在一个子空间里独立计算注意力权重。"
        ),
        (
            "核心概念详细解释",
            "定义：多头注意力是把同一组输入通过多组线性变换拆成多个 head，每个 head 分别计算注意力，然后把结果 concat 后经过输出投影。"
            "Query 表示当前 token 想查询什么，Key 表示每个 token 可以被匹配的特征，Value 表示被聚合的信息内容。"
            "注意力分数来自 Query 与 Key 的点积，Softmax 把分数变成权重，输出投影把多个 head 的结果重新混合为模型维度。"
        ),
        (
            "关键公式与符号含义",
            "公式：Attention(Q,K,V)=softmax(QK^T/sqrt(d_k))V。"
            "其中 Q 是查询矩阵，K 是键矩阵，V 是值矩阵，d_k 是每个 head 的 Key 维度，sqrt(d_k) 用来控制点积数值尺度，避免 Softmax 过早饱和。"
            "多头形式可以写成 head_i=Attention(QW_i^Q,KW_i^K,VW_i^V)，MultiHead=Concat(head_1,...,head_h)W^O。"
        ),
        (
            "算法流程",
            "原理流程分为四步：第一步把输入 X 线性映射为 Q、K、V；第二步在每个 head 内计算 QK^T/sqrt(d_k)；第三步通过 Softmax 得到注意力权重并加权求和 Value；第四步把多个 head concat 后做输出投影。"
            "这个机制让模型能同时关注局部依赖、长距离依赖和不同语义关系。"
        ),
        (
            "具体例子一",
            "例子：句子「我 喜欢 深度 学习」中，token「学习」的 Query 可能会与「深度」的 Key 得到较高分数，因为它们构成短语。"
            "另一个 head 可能关注「我」与「喜欢」的主谓关系。这个案例说明多个 head 不是重复计算，而是在不同表示子空间里捕捉不同关系。"
        ),
        (
            "具体例子二",
            "示例：在图像 patch 序列中，一个 head 可以关注相邻 patch 的纹理关系，另一个 head 可以关注远距离 patch 的整体轮廓。"
            "这解释了为什么多头注意力也能用于视觉 Transformer，而不只服务于文本。"
        ),
        (
            "PyTorch 代码示例",
            "代码示例：可以使用 torch.nn.MultiheadAttention(embed_dim=64, num_heads=4, batch_first=True)。"
            "输入张量 x 的形状为 batch、seq_len、embed_dim，调用 output, weights = layer(x, x, x) 后，output 保持同样的模型维度，weights 可用于观察注意力权重。"
            "这段 PyTorch 示例的重点是检查 embed_dim 必须能被 num_heads 整除。"
        ),
        (
            "常见误区与纠正",
            "误区一：把注意力权重当成绝对解释。纠正：权重能提供参考，但不能直接等价为因果解释。"
            "误区二：忽略位置编码。纠正：自注意力本身不包含顺序信息，Transformer 需要位置编码或相对位置机制。"
            "误区三：以为 head 越多越好。纠正：head 数受模型维度、数据规模和计算预算共同限制。"
        ),
        (
            "课堂小练习",
            "自测题 1：为什么点积注意力要除以 sqrt(d_k)？参考答案：为了控制点积方差，避免 Softmax 饱和导致梯度变小。解析：维度越高，随机点积幅度越大，缩放能稳定训练。"
            "练习 2：embed_dim=128、num_heads=8 时，每个 head 的维度是多少？答案：16。解析：128 除以 8 等于 16。"
            "自测题 3：多头注意力中的 concat 后为什么还需要输出投影？参考答案：输出投影用于融合不同 head 的信息，并映射回模型后续层需要的表示空间。"
        ),
        (
            "下一步学习建议",
            "下一步建议先做一个小型注意力权重可视化实验，再学习 Transformer Encoder。"
            "检查清单包括：能解释 Q/K/V，能写出公式，能说明 Softmax 和输出投影作用，能用 PyTorch 跑通 MultiheadAttention。"
            "参考依据 evidence_id: kb_dl_multihead_attention_001。"
        ),
    ]
    content = "\n\n".join(f"## {heading}\n{text}" for heading, text in sections)
    return content + "\n\n" + "补充说明：" + "多头注意力需要把数学公式、张量形状、代码实验和可视化权重结合起来学习。" * 18


class TeachingQualityGateTest(unittest.TestCase):
    def test_short_course_note_is_rejected_as_fatal(self):
        item = {
            "title": "卷积神经网络中的卷积操作 · 课程讲解文档",
            "type": artifact_types.COURSE_NOTE,
            "summary": "简短摘要",
            "content": "## 学习目标\n了解 CNN。\n## 核心内容\nCNN 可以处理图像。\n## 常见误区\n不要混淆概念。",
            "source": "深度学习初始知识库",
            "unit_id": "dl_cnn_conv_basic",
        }
        result = validate_teaching_quality(
            item,
            {
                "topic": "卷积神经网络中的卷积操作",
                "unit_id": "dl_cnn_conv_basic",
                "resource_type": artifact_types.COURSE_NOTE,
                "evidence_chunks": [],
            },
        )

        self.assertFalse(result["passed"])
        self.assertTrue(result["fatal"])
        self.assertLess(result["teaching_quality_score"], 60)
        self.assertTrue(any("内容过短" in issue for issue in result["issues"]))
        self.assertTrue(any("核心主题词覆盖不足" in issue for issue in result["issues"]))

    def test_complete_course_note_passes_with_graph_terms(self):
        result = validate_teaching_quality(
            {
                "title": "多头注意力 · 课程讲解文档",
                "type": artifact_types.COURSE_NOTE,
                "summary": "解释多头注意力的 Q/K/V、Softmax、concat 和输出投影。",
                "content": _complete_multihead_attention_note(),
                "source": "evidence_id: kb_dl_multihead_attention_001",
                "unit_id": "dl_multihead_attention",
            },
            {
                "topic": "多头注意力",
                "unit_id": "dl_multihead_attention",
                "resource_type": artifact_types.COURSE_NOTE,
                "evidence_chunks": [{"evidence_id": "kb_dl_multihead_attention_001"}],
            },
        )

        self.assertTrue(result["passed"], result["issues"])
        self.assertGreaterEqual(result["teaching_quality_score"], 80)
        self.assertGreaterEqual(result["metrics"]["heading_count"], 8)
        self.assertIn("Query", result["covered_terms"])
        self.assertIn("多头注意力", result["covered_terms"])

    def test_artifact_dict_exposes_separate_reviews(self):
        safety_note = content_guard_service.attach_review_note(
            "",
            {
                "reviewer": "内容安全 Agent",
                "score": 100,
                "risk_level": "低风险",
                "checks": ["敏感内容：未发现明显风险词"],
                "suggestions": ["建议管理员按课程标准复核。"],
                "requires_human_review": True,
            },
        )
        notes = resource_quality_gate.attach_teaching_quality_note(
            safety_note,
            {
                "teaching_quality_score": 86,
                "score": 86,
                "status": "passed",
                "passed": True,
                "fatal": False,
                "issues": ["教学质量门控通过"],
                "repair_suggestions": [],
            },
        )
        review_bundle = resource_artifact_service._review_bundle_from_notes(
            notes,
            ["kb_dl_multihead_attention_001"],
        )
        row = ResourceArtifact(
            artifact_id="artifact_test_001",
            resource_id="res_test_001",
            course_id="deep_learning",
            unit_ids_json=json.dumps(["dl_multihead_attention"], ensure_ascii=False),
            student_id="student",
            type=artifact_types.COURSE_NOTE,
            title="多头注意力 · 课程讲解文档",
            summary="完整讲义",
            content_format="markdown",
            content=_complete_multihead_attention_note(),
            assets_json=json.dumps([review_bundle], ensure_ascii=False),
            evidence_refs_json=json.dumps(["kb_dl_multihead_attention_001"], ensure_ascii=False),
            quality_score=86,
            risk_level="低风险",
            status="needs_review",
            agent_name="ResourcePlanningAgent",
            created_at=datetime.datetime(2026, 1, 1, 8, 0, 0),
            updated_at=datetime.datetime(2026, 1, 1, 8, 5, 0),
        )

        data = resource_artifact_service.to_dict(row)

        self.assertEqual(data["safety_review"]["score"], 100)
        self.assertEqual(data["teaching_quality_review"]["teaching_quality_score"], 86)
        self.assertTrue(data["evidence_review"]["evidence_ok"])
        self.assertEqual(data["quality_score"], 86)
        self.assertFalse(any(item.get("kind") == "quality_review" for item in data["assets"]))


if __name__ == "__main__":
    unittest.main()
