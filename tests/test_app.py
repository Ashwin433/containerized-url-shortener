import os

import fakeredis

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.main import create_app


def create_test_app(monkeypatch):
    fake_redis = fakeredis.FakeRedis(decode_responses=True)

    monkeypatch.setattr(
        "app.main.redis.from_url",
        lambda *args, **kwargs: fake_redis,
    )

    return create_app()


def test_home(monkeypatch):
    app = create_test_app(monkeypatch)
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_shorten(monkeypatch):
    app = create_test_app(monkeypatch)
    client = app.test_client()

    response = client.post(
        "/shorten",
        json={"url": "https://github.com"},
    )

    assert response.status_code == 201

    data = response.get_json()

    assert data["original_url"] == "https://github.com"
    assert "code" in data
    assert "short_url" in data
