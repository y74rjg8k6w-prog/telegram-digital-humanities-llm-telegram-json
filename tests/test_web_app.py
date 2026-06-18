from fastapi.testclient import TestClient

from app.main import app


def test_homepage_loads_telegram_web_app_shell() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "telegram-web-app.js" in response.text
    assert "Анализатор Telegram-переписки" in response.text
    assert "result.json" in response.text


def test_health_endpoint_is_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
