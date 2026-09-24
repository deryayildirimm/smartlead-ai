from unittest.mock import Mock

import pytest
import requests

from app.exceptions import AIServiceError
from app.services.ai_service import AIService


class TestSettings:
    AI_PROVIDER = "groq"
    GROQ_API_KEY = "fake-key-for-tests"
    GROQ_MODEL = "openai/gpt-oss-20b"
    BUSINESS_CONTEXT = "Türkçe konuşan bir okuma rehberisin."


@pytest.fixture
def service():
    return AIService(settings=TestSettings)


@pytest.fixture(autouse=True)
def fake_post(monkeypatch):
    # Bu dosyadaki bütün testlerde gerçek HTTP çağrısını engelle.
    mocked = Mock()

    monkeypatch.setattr(
        "app.services.ai_service.requests.post",
        mocked,
    )

    return mocked


def test_success_preserves_message_order(service, fake_post):
    response = Mock()
    response.json.return_value = {
        "choices": [
            {"message": {"content": "  Örnek yanıt.  "}}
        ]
    }
    fake_post.return_value = response

    history = [
        {"role": "user", "content": "Öykü seviyorum."},
        {"role": "assistant", "content": "Ne kadar zamanın var?"},
    ]

    result = service.yanit_uret("İki dakika.", history)

    assert result == "Örnek yanıt."

    fake_post.assert_called_once()
    response.raise_for_status.assert_called_once()

    payload = fake_post.call_args.kwargs["json"]

    assert payload["messages"] == [
        {
            "role": "system",
            "content": TestSettings.BUSINESS_CONTEXT,
        },
        *history,
        {"role": "user", "content": "İki dakika."},
    ]

    # Servis kendisine verilen geçmiş listesini değiştirmemeli.
    assert len(history) == 2


def test_timeout_becomes_service_error(service, fake_post):
    fake_post.side_effect = requests.Timeout()

    with pytest.raises(AIServiceError, match="uzun sürdü"):
        service.yanit_uret("Merhaba")


def test_http_error_becomes_service_error(service, fake_post):
    response = Mock()
    response.status_code = 429

    response.raise_for_status.side_effect = requests.HTTPError(
        "Provider internal detail",
        response=response,
    )

    fake_post.return_value = response

    with pytest.raises(AIServiceError) as captured:
        service.yanit_uret("Merhaba")

    assert "ulaşılamıyor" in str(captured.value)
    assert "Provider internal detail" not in str(captured.value)


def test_invalid_json_becomes_service_error(service, fake_post):
    response = Mock()
    response.json.side_effect = ValueError("Invalid JSON")

    fake_post.return_value = response

    with pytest.raises(AIServiceError, match="geçerli bir yanıt"):
        service.yanit_uret("Merhaba")


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"content": None}}]},
        {"choices": [{"message": {"content": "   "}}]},
    ],
)
def test_invalid_response_body(service, fake_post, body):
    response = Mock()
    response.json.return_value = body

    fake_post.return_value = response

    with pytest.raises(AIServiceError, match="geçerli bir yanıt"):
        service.yanit_uret("Merhaba")


def test_missing_key_returns_demo_without_http(fake_post):
    class NoKeySettings(TestSettings):
        GROQ_API_KEY = ""

    service = AIService(settings=NoKeySettings)

    result = service.yanit_uret("Merhaba")

    assert result.startswith("Demo modu:")
    fake_post.assert_not_called()