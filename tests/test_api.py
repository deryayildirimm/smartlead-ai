import pytest
from app.exceptions import AIServiceError
from unittest.mock import Mock


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {
        "basari": True,
        "durum": "aktif",
    }


def test_create_and_list_lead(client):
    payload = {
        "isim": "Demo Kullanıcı",
        "telefon": "05000000000",
        "email": "demo@example.com",
        "mesaj": "Kısa okumalarla ilgileniyorum.",
        "seri": "ince_bir_mizah",
    }

    create_response = client.post(
        "/api/leads",
        json=payload,
    )

    assert create_response.status_code == 201

    created = create_response.get_json()

    assert created["basari"] is True
    assert isinstance(created["id"], int)

    list_response = client.get("/api/leads")

    assert list_response.status_code == 200

    records = list_response.get_json()["leadler"]

    assert len(records) == 1
    assert records[0]["id"] == created["id"]

    for field, value in payload.items():
        assert records[0][field] == value


@pytest.mark.parametrize(
    "changed_field, invalid_value",
    [
        ("isim", ""),
        ("telefon", "abc"),
        ("email", "gecersiz-email"),
        ("seri", "olmayan_seri"),
    ],
)
def test_invalid_lead_is_not_saved(
    client,
    changed_field,
    invalid_value,
):
    payload = {
        "isim": "Demo Kullanıcı",
        "telefon": "05000000000",
        "email": "demo@example.com",
        "mesaj": "",
        "seri": "karisik",
    }

    payload[changed_field] = invalid_value

    response = client.post("/api/leads", json=payload)

    assert response.status_code == 400
    assert response.get_json()["basari"] is False

    records = client.get("/api/leads").get_json()["leadler"]

    assert records == []


def test_chat_success(client, monkeypatch, ai_service):
    def fake_reply(message, history):
        assert message == "Mizahi okumalar istiyorum."
        assert history == []

        return "İnce Bir Mizah demo serisini inceleyebilirsin."

    monkeypatch.setattr(
        ai_service,
        "yanit_uret",
        fake_reply,
    )

    response = client.post(
        "/api/sohbet",
        json={
            "mesaj": "Mizahi okumalar istiyorum.",
            "gecmis": [],
        },
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "basari": True,
        "cevap": "İnce Bir Mizah demo serisini inceleyebilirsin.",
    }

def test_empty_message_does_not_call_ai(client, monkeypatch, ai_service):
    calls = []

    def fake_groq_request(messages):
        calls.append(messages)
        return "Bu fonksiyon çağrılmamalı."

    monkeypatch.setattr(
        ai_service,
        "_groq_yaniti_al",
        fake_groq_request,
    )

    response = client.post(
        "/api/sohbet",
        json={"mesaj": "   ", "gecmis": []},
    )

    assert response.status_code == 400
    assert response.get_json()["basari"] is False
    assert calls == []


def test_ai_failure_returns_503(client, monkeypatch, ai_service):
    def failing_reply(message, history):
        raise AIServiceError(
            "Asistana şu anda ulaşılamıyor."
        )

    monkeypatch.setattr(
        ai_service,
        "yanit_uret",
        failing_reply,
    )

    response = client.post(
        "/api/sohbet",
        json={"mesaj": "Merhaba", "gecmis": []},
    )

    assert response.status_code == 503
    assert response.get_json() == {
        "basari": False,
        "hata": "Asistana şu anda ulaşılamıyor.",
    }


def test_unexpected_error_hides_details(client, monkeypatch, ai_service):
    def broken_reply(message, history):
        raise RuntimeError("INTERNAL_DETAIL_TEST")

    monkeypatch.setattr(
        ai_service,
        "yanit_uret",
        broken_reply,
    )

    response = client.post(
        "/api/sohbet",
        json={"mesaj": "Merhaba", "gecmis": []},
    )

    assert response.status_code == 500
    assert response.get_json()["basari"] is False

    # Teknik hata kullanıcıya dönen yanıtta bulunmamalı.
    assert "INTERNAL_DETAIL_TEST" not in response.get_data(
        as_text=True
    )


def test_unknown_api_returns_json(client):
    response = client.get("/api/olmayan-adres")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["basari"] is False


def test_wrong_method_returns_405(client):
    response = client.get("/api/sohbet")

    assert response.status_code == 405
    assert response.is_json
    assert response.get_json()["basari"] is False

    # Merkezi hata yönetimi gerekli HTTP başlığını korumalı.
    assert "POST" in response.headers["Allow"]


def test_malformed_json_returns_400(client):
    response = client.post(
        "/api/leads",
        data='{"isim":',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.is_json
    assert response.get_json()["basari"] is False

def test_chat_uses_application_settings(client, monkeypatch):
    response = Mock()
    response.json.return_value = {
        "choices": [
            {"message": {"content": "Test yanıtı."}}
        ]
    }

    fake_post = Mock(return_value=response)

    monkeypatch.setattr(
        "app.services.ai_service.requests.post",
        fake_post,
    )

    result = client.post(
        "/api/sohbet",
        json={
            "mesaj": "Merhaba",
            "gecmis": [],
        },
    )

    assert result.status_code == 200
    assert result.get_json()["cevap"] == "Test yanıtı."

    fake_post.assert_called_once()

    sent = fake_post.call_args.kwargs

    assert sent["json"]["model"] == "test-model"

    assert sent["json"]["messages"][0] == {
        "role": "system",
        "content": "Yalnızca test için kullanılan talimat.",
    }

    assert sent["headers"]["Authorization"] == (
        "Bearer fake-key-for-tests"
    )