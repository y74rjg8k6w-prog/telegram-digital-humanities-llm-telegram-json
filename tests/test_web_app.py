from fastapi.testclient import TestClient

from app.main import app


def test_homepage_loads_telegram_web_app_shell() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "telegram-web-app.js" in response.text
    assert "Анализатор Telegram-переписки" in response.text
    assert "result.json" in response.text
    assert "Быстрый анализ сообщения или переписки" in response.text
    assert "дружбу/поддержку" in response.text
    assert "здоровье диалога" in response.text


def test_single_message_endpoint_returns_demo_analysis() -> None:
    client = TestClient(app)

    response = client.post("/api/analyze-message", json={"text": "Привет! Как ты? Давай созвонимся вечером 😊"})

    assert response.status_code == 200
    data = response.json()
    assert data["metrics"]["words"] >= 5
    assert data["metrics"]["questions"] >= 1
    assert data["tone"] in {"скорее тёплый/позитивный", "вопросительный/инициирующий"}
    assert "summary" in data


def test_pasted_messages_endpoint_returns_relationship_risk_analysis() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/analyze-message",
        json={"text": "Анна: Ты опять всё испортил!!!\nЯ: Мне страшно.\nАнна: Если уйдёшь, я всем расскажу."},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "multi_message"
    assert data["message_count"] == 3
    assert data["emotion_scale"]["anger"] > 0
    assert data["abuse"]["level"] in {"средний", "высокий"}
    assert data["red_flags"]
    assert data["friendship"]["level"] in {"хрупкая", "напряжённая"}
    assert data["conversation_health"]["conflict"] >= 45
    assert data["conversation_health"]["level"] in {"напряжённое", "кризисное/рисковое"}
    assert any("специал" in segment.lower() for segment in data["audience_segments"])


def test_pasted_messages_endpoint_returns_friendship_meter() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/analyze-message",
        json={"text": "Лена: Спасибо, ты очень помогла.\nЯ: Люблю тебя, давай завтра погуляем.\nЛена: Супер, обнимаю ❤️"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "multi_message"
    assert data["friendship"]["score"] >= 70
    assert data["friendship"]["level"] == "крепкая"
    assert data["conversation_health"]["score"] >= 70
    assert data["conversation_health"]["level"] == "устойчивое"
    assert "Поддержка" in data["friendship"]["explanation"]


def test_health_endpoint_is_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
