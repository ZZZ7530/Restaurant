import pytest
from flask import session

from app.config import _get_bool, _get_secret_key


def test_production_requires_secret_key(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError):
        _get_secret_key("production")


def test_production_rejects_weak_secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "change-this-secret-key")

    with pytest.raises(RuntimeError):
        _get_secret_key("production")


def test_development_uses_generated_secret_without_weak_fallback(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)

    secret_key = _get_secret_key("development")

    assert secret_key
    assert secret_key != "dev-secret-key"
    assert secret_key != "change-this-secret-key"


def test_session_cookie_defaults_for_development():
    class DevelopmentConfig:
        TESTING = True
        SECRET_KEY = "test"
        DEBUG = True
        RESTAURANT_NAME = "測試餐廳"
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = "Lax"
        SESSION_COOKIE_SECURE = False

    from app import create_app

    app = create_app(DevelopmentConfig)

    assert app.config["DEBUG"] is True
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is False


def test_session_cookie_defaults_for_production():
    class ProductionConfig:
        TESTING = True
        SECRET_KEY = "test"
        DEBUG = False
        RESTAURANT_NAME = "測試餐廳"
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = "Lax"
        SESSION_COOKIE_SECURE = True

    from app import create_app

    app = create_app(ProductionConfig)

    assert app.config["DEBUG"] is False
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["SESSION_COOKIE_SECURE"] is True


def test_development_session_cookie_works_over_http():
    class DevelopmentConfig:
        TESTING = True
        SECRET_KEY = "test"
        DEBUG = True
        RESTAURANT_NAME = "測試餐廳"
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = "Lax"
        SESSION_COOKIE_SECURE = False

    from app import create_app

    app = create_app(DevelopmentConfig)

    @app.get("/set-session-for-test")
    def set_session_for_test():
        session["admin_logged_in"] = True
        return "ok"

    response = app.test_client().get("/set-session-for-test")
    cookie = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Secure" not in cookie


def test_production_session_cookie_uses_secure_flag():
    class ProductionConfig:
        TESTING = True
        SECRET_KEY = "test"
        DEBUG = False
        RESTAURANT_NAME = "測試餐廳"
        SESSION_COOKIE_HTTPONLY = True
        SESSION_COOKIE_SAMESITE = "Lax"
        SESSION_COOKIE_SECURE = True

    from app import create_app

    app = create_app(ProductionConfig)

    @app.get("/set-session-for-test")
    def set_session_for_test():
        session["admin_logged_in"] = True
        return "ok"

    response = app.test_client().get("/set-session-for-test")
    cookie = response.headers["Set-Cookie"]

    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Secure" in cookie


def test_env_bool_parser():
    assert _get_bool("MISSING_BOOL", default=True) is True
    assert _get_bool("MISSING_BOOL", default=False) is False
