from fastapi.testclient import TestClient

from app.main import app


def test_homepage_loads_telegram_web_app_shell() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "telegram-web-app.js" in response.text
    assert "Анализатор Telegram-переписки" in response.text
    assert "result.json" in response.text
    assert "Быстрый пример по одному сообщению" in response.text


def test_single_message_endpoint_returns_demo_analysis() -> None:
    client = TestClient(app)

    response = client.post("/api/analyze-message", json={"text": "Привет! Как ты? Давай созвонимся вечером 😊"})

    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["words"] >= 5
    assert data["metrics"]["questions"] >= 1
    assert data["tone"] in {"скорее тёплый/позитивный", "вопросительный/инициирующий"}
    assert "summary" in data


def test_health_endpoint_is_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
