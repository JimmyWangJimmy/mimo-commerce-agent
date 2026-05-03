from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo


DEFAULT_MODEL = "mimo-v2.5-pro"
DEFAULT_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"


class MiMoError(RuntimeError):
    pass


def _system_prompt() -> str:
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    return (
        "You are MiMo, an AI assistant developed by Xiaomi. "
        f"Today's date: {now:%Y-%m-%d %A}. "
        "Your knowledge cutoff date is December 2024."
    )


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.S)
        if not match:
            raise
        return json.loads(match.group(0))


def call_mimo_json(prompt: str, max_tokens: int = 4096, temperature: float = 0.6) -> dict:
    api_key = os.environ.get("MIMO_API_KEY")
    if not api_key:
        raise MiMoError("Missing MIMO_API_KEY.")
    base_url = os.environ.get("MIMO_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    payload = {
        "model": os.environ.get("MIMO_MODEL", DEFAULT_MODEL),
        "messages": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": prompt},
        ],
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "stream": False,
        "response_format": {"type": "json_object"},
    }
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise MiMoError(f"MiMo HTTP {exc.code}: {body}") from exc
    except TimeoutError as exc:
        raise MiMoError(f"MiMo request timed out: {exc}") from exc
    except urllib.error.URLError as exc:
        raise MiMoError(f"MiMo request failed: {exc}") from exc

    content = data["choices"][0]["message"]["content"]
    return extract_json(content)
