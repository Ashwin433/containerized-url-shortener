import os
import secrets
import string

import redis
from flask import Flask, jsonify, redirect, request
from sqlalchemy import text

from app.models import URL, db


def create_app():
    app = Flask(__name__)

    database_url = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://urluser:urlpassword@db:3306/urlshortener",
    )

    redis_url = os.getenv(
        "REDIS_URL",
        "redis://redis:6379/0",
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    redis_client = redis.from_url(
        redis_url,
        decode_responses=True,
    )

    with app.app_context():
        db.create_all()

    def generate_short_code(length=6):
        characters = string.ascii_letters + string.digits

        while True:
            code = "".join(secrets.choice(characters) for _ in range(length))

            if not db.session.query(
                URL.query.filter_by(short_url=code).exists()
            ).scalar():
                return code

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            redis_client.ping()

            return jsonify(
                {
                    "status": "healthy",
                    "database": "ok",
                    "redis": "ok",
                }
            ), 200

        except Exception:
            return jsonify({"status": "unhealthy"}), 503

    @app.post("/shorten")
    def shorten_url():
        data = request.get_json(silent=True) or {}

        original_url = data.get("url")

        if not original_url:
            return jsonify({"error": "URL is required"}), 400

        code = generate_short_code()

        url = URL(
            original_url=original_url,
            short_url=code,
        )

        db.session.add(url)
        db.session.commit()

        redis_client.set(
            f"url:{code}",
            original_url,
        )

        return jsonify(
            {
                "original_url": original_url,
                "short_url": f"/{code}",
                "code": code,
                "click_count": 0,
            }
        ), 201

    @app.get("/stats/<code>")
    def stats(code):
        url = URL.query.filter_by(short_url=code).first()

        if not url:
            return jsonify({"error": "URL not found"}), 404

        return jsonify(
            {
                "original_url": url.original_url,
                "short_url": url.short_url,
                "created_at": url.created_at.isoformat(),
                "click_count": url.click_count,
            }
        )

    @app.get("/<code>")
    def redirect_url(code):
        cache_key = f"url:{code}"

        original_url = redis_client.get(cache_key)

        if not original_url:
            url = URL.query.filter_by(short_url=code).first()

            if not url:
                return jsonify({"error": "Short URL not found"}), 404

            original_url = url.original_url

            redis_client.set(
                cache_key,
                original_url,
            )

        url = URL.query.filter_by(short_url=code).first()

        if url:
            url.click_count += 1
            db.session.commit()

        return redirect(original_url)

    @app.get("/")
    def home():
        return jsonify(
            {
                "service": "URL Shortener",
                "status": "running",
            }
        )

    return app


app = create_app()
