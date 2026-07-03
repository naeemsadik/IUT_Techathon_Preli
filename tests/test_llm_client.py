"""LLM client tests."""

import httpx
import pytest

from bot.services.llm_client import GROQ_CHAT_COMPLETIONS_URL, LlmClient, LlmClientError


@pytest.mark.asyncio
async def test_llm_client_sends_groq_chat_completion_request() -> None:
    seen: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers["Authorization"]
        seen["payload"] = request.read().decode()
        return httpx.Response(
            200,
            json={
                "choices": [
                    {"message": {"content": "Everything looks steady and friendly."}}
                ]
            },
        )

    http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = LlmClient(
        api_key="test-key",
        model="llama-3.3-70b-versatile",
        http_client=http_client,
    )

    reply = await client.command_reply("status", "Total Power: 40W")
    await client.close()

    assert reply == "Everything looks steady and friendly."
    assert seen["url"] == GROQ_CHAT_COMPLETIONS_URL
    assert seen["authorization"] == "Bearer test-key"
    assert "llama-3.3-70b-versatile" in str(seen["payload"])
    assert "Total Power: 40W" in str(seen["payload"])


@pytest.mark.asyncio
async def test_llm_client_disabled_without_key() -> None:
    client = LlmClient(api_key="", model="llama-3.3-70b-versatile")

    assert client.is_enabled is False
    with pytest.raises(LlmClientError):
        await client.alert_reply("After-hours usage detected.")
    await client.close()


@pytest.mark.asyncio
async def test_llm_client_raises_for_malformed_response() -> None:
    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={}))
    )
    client = LlmClient(
        api_key="test-key",
        model="llama-3.3-70b-versatile",
        http_client=http_client,
    )

    with pytest.raises(LlmClientError):
        await client.command_reply("usage", "Daily: 18.4 kWh")
    await client.close()
