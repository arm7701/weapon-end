from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from maap_app.config.settings import APP_DIR_NAME

ADAPTER_MODES = ("disabled", "rule_based", "local_model", "openai", "gemini", "sandboxed")


def normalize_chat_url(url: str) -> str:
    value = str(url).strip()
    return value.replace("/:11434", ":11434").replace("/:8000", ":8000")


@dataclass
class AiSettings:
    adapter_mode: str = "rule_based"
    local_server_url: str = "http://127.0.0.1:11434/api/chat"
    local_model: str = "llama3.1:8b"
    local_context_window: int = 8192
    local_request_timeout: int = 60
    openai_base_url: str = "https://api.openai.com/v1/chat/completions"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    guardrail_enabled: bool = True
    strip_chain_of_thought: bool = True
    enable_chain_of_thought: bool = True

    @classmethod
    def load(cls, data_dir: Path | None = None) -> AiSettings:
        base = data_dir or Path.home() / ".local" / "share" / APP_DIR_NAME
        path = base / "ai_settings.json"
        if not path.exists():
            return cls()
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return cls()
        mode = str(payload.get("adapter_mode", "rule_based"))
        if mode not in ADAPTER_MODES:
            mode = "rule_based"
        return cls(
            adapter_mode=mode,
            local_server_url=normalize_chat_url(
                payload.get("local_server_url", "http://127.0.0.1:11434/api/chat")
            ),
            local_model=str(payload.get("local_model", "llama3.1:8b")),
            local_context_window=int(payload.get("local_context_window", 8192)),
            local_request_timeout=int(payload.get("local_request_timeout", 60)),
            openai_base_url=normalize_chat_url(
                payload.get(
                    "openai_base_url",
                    "https://api.openai.com/v1/chat/completions",
                )
            ),
            openai_api_key=str(payload.get("openai_api_key", "")),
            openai_model=str(payload.get("openai_model", "")),
            gemini_base_url=normalize_chat_url(
                payload.get(
                    "gemini_base_url",
                    "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
                )
            ),
            gemini_api_key=str(payload.get("gemini_api_key", "")),
            gemini_model=str(payload.get("gemini_model", "gemini-flash-latest")),
            guardrail_enabled=bool(payload.get("guardrail_enabled", True)),
            strip_chain_of_thought=bool(payload.get("strip_chain_of_thought", True)),
            enable_chain_of_thought=bool(payload.get("enable_chain_of_thought", True)),
        )

    def save(self, data_dir: Path | None = None) -> None:
        base = data_dir or Path.home() / ".local" / "share" / APP_DIR_NAME
        base.mkdir(parents=True, exist_ok=True)
        path = base / "ai_settings.json"
        path.write_text(
            json.dumps(
                {
                    "adapter_mode": self.adapter_mode,
                    "local_server_url": self.local_server_url,
                    "local_model": self.local_model,
                    "local_context_window": self.local_context_window,
                    "local_request_timeout": self.local_request_timeout,
                    "openai_base_url": self.openai_base_url,
                    "openai_api_key": self.openai_api_key,
                    "openai_model": self.openai_model,
                    "gemini_base_url": self.gemini_base_url,
                    "gemini_api_key": self.gemini_api_key,
                    "gemini_model": self.gemini_model,
                    "guardrail_enabled": self.guardrail_enabled,
                    "strip_chain_of_thought": self.strip_chain_of_thought,
                    "enable_chain_of_thought": self.enable_chain_of_thought,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
