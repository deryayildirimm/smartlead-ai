import pytest

from app import create_app


@pytest.fixture(autouse=True)
def block_real_ai(monkeypatch):
    def blocked_request(*args, **kwargs):
        raise AssertionError(
            "Test sırasında gerçek Groq çağrısı yapılmamalı."
        )

    monkeypatch.setattr(
        "app.services.ai_service.requests.post",
        blocked_request,
    )


@pytest.fixture
def app(tmp_path):
    return create_app(
        config_name="development",
        test_config={
            "TESTING": True,
            "DEBUG": False,
            "SECRET_KEY": "only-for-tests",
            "DATABASE_URL": str(tmp_path / "test.db"),
            "AI_PROVIDER": "groq",
            "GROQ_API_KEY": "fake-key-for-tests",
            "GROQ_MODEL": "test-model",
            "BUSINESS_CONTEXT": "Yalnızca test için kullanılan talimat.",
        },
    )


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def ai_service(app):
    return app.extensions["ai_service"]