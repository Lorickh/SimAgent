import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass


@dataclass
class LLMResponse:
    content: str
    raw: dict


class LLMClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None):
        self.base_url = base_url or os.environ.get("LLM_BASE_URL")
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4.1-mini")

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def chat(self, messages: list[dict]) -> LLMResponse:
        if not self.base_url:
            raise RuntimeError("LLM_BASE_URL is not configured")
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.api_key:
            request.add_header("Authorization", f"Bearer {self.api_key}")
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8") if exc.fp else ""
            raise RuntimeError(f"LLM request failed: {exc.code} {error_body}") from exc
        raw = json.loads(body)
        content = raw["choices"][0]["message"]["content"]
        return LLMResponse(content=content, raw=raw)
