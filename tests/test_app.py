import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.main import create_app


def test_home():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_shorten():
    app = create_app()
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
