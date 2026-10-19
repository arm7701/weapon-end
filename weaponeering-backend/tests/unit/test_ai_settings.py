from __future__ import annotations

from maap_app.config.ai_settings import AiSettings
from maap_app.modules.ai.adapter import HttpChatAdapter, RuleBasedLocalAdapter
from maap_app.modules.ai.context import ContextBundle
from maap_app.modules.ai.service import AiAssistantService


def test_ai_settings_persist_local_and_openai_fields(tmp_path) -> None:
    settings = AiSettings(
        adapter_mode="local_model",
        local_server_url="http://10.222.22.222:11434/api/chat",
        local_model="llama3.1:8b",
        openai_base_url="https://api.openai.com/v1/chat/completions",
        openai_model="configured-model",
        openai_api_key="test-key",
    )

    settings.save(tmp_path)
    loaded = AiSettings.load(tmp_path)

    assert loaded.adapter_mode == "local_model"
    assert loaded.local_server_url == "http://10.222.22.222:11434/api/chat"
    assert loaded.local_model == "llama3.1:8b"
    assert loaded.openai_base_url == "https://api.openai.com/v1/chat/completions"
    assert loaded.openai_model == "configured-model"
    assert loaded.openai_api_key == "test-key"


def test_ai_settings_normalizes_host_slash_before_port(tmp_path) -> None:
    settings = AiSettings(
        adapter_mode="local_model",
        local_server_url="http://10.225.120.221/:11434/api/chat",
        local_model="llama3.1:8b",
    )

    settings.save(tmp_path)
    loaded = AiSettings.load(tmp_path)

    assert loaded.local_server_url == "http://10.225.120.221:11434/api/chat"


def test_rule_based_connection_test_returns_success() -> None:
    service = AiAssistantService(
        repository=None,
        context_builder=None,
        guardrail_service=None,
        audit_service=None,
        ai_settings=AiSettings(adapter_mode="rule_based"),
    )

    ok, message = service.test_connection(AiSettings(adapter_mode="rule_based"))

    assert ok is True
    assert "Rule-based" in message


def test_http_chat_adapter_message_structure() -> None:
    adapter = HttpChatAdapter(AiSettings(adapter_mode="local_model"))
    messages = adapter._messages(
        "chat_with_context",
        ContextBundle(scenario={"name": "Thai scenario"}),
        "ช่วยอธิบายข้อมูล Target นี้",
    )

    # Single merged system message: instructions + context (Gemini-compatible)
    assert messages[0]["role"] == "system"
    assert "MAAP" in messages[0]["content"]
    assert "Thai" in messages[0]["content"]
    assert "=== MAAP CONTEXT (SIMULATION DATA) ===" in messages[0]["content"]
    # Last message is the user question, not escaped
    assert messages[-1]["role"] == "user"
    assert "ช่วยอธิบายข้อมูล Target นี้" in messages[-1]["content"]
    assert "\\u0e0a" not in messages[-1]["content"]


def test_rule_based_chat_replies_in_thai_when_prompt_is_thai() -> None:
    adapter = RuleBasedLocalAdapter()
    payload = adapter.generate(
        "chat_with_context",
        ContextBundle(target={"label": "TGT-TH"}),
        "ช่วยสรุปข้อมูล",
    )

    assert "คำตอบโหมดฝึกจำลอง" in payload.summary
