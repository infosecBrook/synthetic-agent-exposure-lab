from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    load_dotenv = None


DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "llama3.1:8b"
DEFAULT_PROVIDER = "mock"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
_ENV_LOADED = False


@dataclass
class LocalLLMResponse:
    content: str
    provider: str
    model: str


class LocalLLMError(RuntimeError):
    pass


def load_project_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    if load_dotenv:
        load_dotenv(PROJECT_ROOT / ".env")
    _ENV_LOADED = True


def configured_provider() -> str:
    load_project_env()
    return os.getenv("AGENT_PROVIDER", DEFAULT_PROVIDER).strip().lower()


def ollama_model() -> str:
    load_project_env()
    return os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL).strip() or DEFAULT_OLLAMA_MODEL


def _ollama_url(path: str) -> str:
    load_project_env()
    host = os.getenv("OLLAMA_HOST", DEFAULT_OLLAMA_HOST).rstrip("/")
    return f"{host}{path}"


def call_ollama(messages: list[dict[str, str]], *, temperature: float = 0.0) -> LocalLLMResponse:
    model = ollama_model()
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": temperature,
            "num_predict": 700,
        },
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        _ollama_url("/api/chat"),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise LocalLLMError(
            "Ollama is not reachable. Start it with `ollama serve` and pull a model with "
            f"`ollama pull {model}`, or set AGENT_PROVIDER=mock."
        ) from exc
    except json.JSONDecodeError as exc:
        raise LocalLLMError("Ollama returned a non-JSON response.") from exc

    content = body.get("message", {}).get("content", "")
    return LocalLLMResponse(content=content, provider="ollama", model=model)


def parse_json_object(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LocalLLMError(f"Model did not return valid JSON: {content[:200]}") from exc
    if not isinstance(parsed, dict):
        raise LocalLLMError("Model JSON response was not an object.")
    return parsed
