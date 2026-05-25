import json
import os
from pathlib import Path
import urllib.request
import urllib.error


# =========================
# 1. 加载 .env
# =========================
def _load_env_file():
    env_path = Path.cwd() / ".env"

    if not env_path.exists():
        print("[ENV] .env not found:", env_path)
        return

    print("[ENV] loading:", env_path)

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        k, v = line.split("=", 1)

        os.environ[k.strip()] = v.strip().strip('"').strip("'")

    # 👇 强制打印检查（关键）
    print("[ENV CHECK]")
    print("LINGXI_LLM_PROVIDER =", os.getenv("LINGXI_LLM_PROVIDER"))
    print("SPARK_API_PASSWORD =", "SET" if os.getenv("SPARK_API_PASSWORD") else "EMPTY")

_load_env_file()

DEFAULT_SPARK_API_URL = "https://spark-api-open.xf-yun.com/v1/chat/completions"


# =========================
# 2. 是否启用LLM
# =========================
def is_enabled():
    provider = os.getenv("LINGXI_LLM_PROVIDER", "local").strip().lower()
    password = os.getenv("SPARK_API_PASSWORD", "").strip()

    enabled = provider == "spark" and bool(password)

    print("[LLM ENABLE CHECK]", enabled)

    return enabled


# =========================
# 3. 调用LLM
# =========================
def chat(messages, temperature=0.5, max_tokens=1200):
    if not is_enabled():
        return {"ok": False, "error": "LLM disabled", "content": ""}

    api_password = os.getenv("SPARK_API_PASSWORD", "")
    api_url = os.getenv("SPARK_API_URL", DEFAULT_SPARK_API_URL)
    model = os.getenv("SPARK_MODEL", "generalv3")
    timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    print("[LLM REQUEST]", payload)
    print("[LLM URL]", api_url)
    print("[LLM MODEL]", model)

    req = urllib.request.Request(
        api_url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_password}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print("[LLM HTTP ERROR BODY]", err_body)
        return {"ok": False, "error": str(e), "content": ""}

    # 🚨 统一判断成功
    if data.get("code") != 0:
        return {"ok": False, "error": data.get("message", "fail"), "content": ""}

    choices = data.get("choices") or []
    print("[LLM RESPONSE RAW]", data)
    if not choices:
        return {"ok": False, "error": "no response", "content": ""}

    msg = choices[0].get("message", {})
    content = msg.get("content") or msg.get("text") or ""

    if not content:
        return {"ok": False, "error": "empty content", "content": ""}

    return {
        "ok": True,
        "content": content
    }