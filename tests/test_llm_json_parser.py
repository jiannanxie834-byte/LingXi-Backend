import io

from app.services import llm_provider
from app.services.llm_provider import _parse_spark_sse_response, extract_json_object


def test_extract_json_object_repairs_literal_newlines_inside_strings():
    content = '{"summary":"简介","content":"# 标题\n\n正文\n```python\nprint(1)\n```","personalization_reason":"基于画像"}'

    parsed = extract_json_object(content)

    assert parsed["summary"] == "简介"
    assert parsed["content"].startswith("# 标题\n\n正文")
    assert "print(1)" in parsed["content"]


def test_extract_json_object_still_rejects_structurally_invalid_json():
    try:
        extract_json_object('{"summary": "简介", "content": [}')
    except ValueError as exc:
        assert "not valid JSON" in str(exc) or "incomplete JSON" in str(exc)
    else:
        raise AssertionError("结构错误的 JSON 不应通过")


def test_parse_spark_sse_joins_content_and_ignores_reasoning():
    response = io.BytesIO(
        b'data:{"code":0,"choices":[{"delta":{"reasoning_content":"hidden"}}]}\n'
        b'data:{"code":0,"choices":[{"delta":{"content":"hello "}}]}\n'
        b'data:{"code":0,"choices":[{"delta":{"content":"world"}}]}\n'
        b'data:[DONE]\n'
    )

    result = _parse_spark_sse_response(response)

    assert result == {"ok": True, "content": "hello world"}


def test_chat_json_retries_when_required_content_is_missing(monkeypatch):
    responses = iter(
        [
            {"ok": True, "content": '{"summary":"只有摘要"}'},
            {"ok": True, "content": '{"content":"完整正文"}'},
        ]
    )
    calls = []

    def fake_chat(messages, **kwargs):
        calls.append(messages)
        return next(responses)

    monkeypatch.setattr(llm_provider, "chat", fake_chat)

    result = llm_provider.chat_json(
        [{"role": "user", "content": "生成资源"}],
        required_fields=["content"],
    )

    assert result["ok"] is True
    assert result["data"]["content"] == "完整正文"
    assert len(calls) == 2
    assert "必须包含这些字段：content" in calls[1][-1]["content"]


def test_chat_json_treats_blank_required_content_as_missing(monkeypatch):
    responses = iter(
        [
            {"ok": True, "content": '{"content":"   "}'},
            {"ok": True, "content": '{"content":"正文"}'},
        ]
    )
    monkeypatch.setattr(llm_provider, "chat", lambda *args, **kwargs: next(responses))

    result = llm_provider.chat_json([], required_fields=["content"])

    assert result["ok"] is True
    assert result["data"]["content"] == "正文"
