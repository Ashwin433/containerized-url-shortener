import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from app.main import create_app


def test_home():
    app = create_app()
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200


def test_health_endpoint():
    app = create_app()
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code in [200, 503]
