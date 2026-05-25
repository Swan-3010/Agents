from __future__ import annotations

import os
import requests


def _get_env(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value else default


class OllamaLLMClient:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: float = 180.0,
    ):
        self.model = model or _get_env("OLLAMA_MODEL", "qwen2.5:7b-instruct")
        self.base_url = (base_url or _get_env("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        return payload["response"]
