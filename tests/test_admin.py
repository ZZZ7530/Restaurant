from app import create_app
from app.repositories.admin_repository import AdminRepository
from werkzeug.security import check_password_hash, generate_password_hash


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"
    RESTAURANT_NAME = "測試餐廳"
    MYSQL_HOST = "localhost"
    MYSQL_PORT = 3306
    MYSQL_USER = "root"
    MYSQL_PASSWORD = ""
    MYSQL_DATABASE = "traditional_restaurant_test"


def test_admin_dashboard_loads():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/admin")

    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_admin_login_allows_dashboard(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    password_hash = generate_password_hash("safe-test-password")
    monkeypatch.setattr(
        AdminRepository,
        "find_by_username",
        staticmethod(lambda username: _fake_admin(password_hash) if username == "secure-admin" else None),
    )

    response = client.post(
        "/admin/login",
        data={"username": "secure-admin", "password": "safe-test-password"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "後台總覽".encode() in response.data
    with client.session_transaction() as sess:
        assert sess["admin_logged_in"] is True
        assert sess["admin_username"] == "secure-admin"
        assert sess["admin_user_id"] == 1


def test_admin_login_rejects_wrong_password(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    password_hash = generate_password_hash("safe-test-password")
    monkeypatch.setattr(
        AdminRepository,
        "find_by_username",
        staticmethod(lambda username: _fake_admin(password_hash) if username == "secure-admin" else None),
    )

    response = client.post(
        "/admin/login",
        data={"username": "secure-admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert "帳號或密碼錯誤".encode() in response.data
    with client.session_transaction() as sess:
        assert not sess.get("admin_logged_in")


def test_admin_login_rejects_unknown_username(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(AdminRepository, "find_by_username", staticmethod(lambda username: None))

    response = client.post(
        "/admin/login",
        data={"username": "missing-admin", "password": "anything"},
    )

    assert response.status_code == 401
    assert "帳號或密碼錯誤".encode() in response.data
    with client.session_transaction() as sess:
        assert not sess.get("admin_logged_in")


def test_admin_logout_clears_session(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    password_hash = generate_password_hash("safe-test-password")
    monkeypatch.setattr(
        AdminRepository,
        "find_by_username",
        staticmethod(lambda username: _fake_admin(password_hash) if username == "secure-admin" else None),
    )

    login_response = client.post(
        "/admin/login",
        data={"username": "secure-admin", "password": "safe-test-password"},
    )
    assert login_response.status_code == 302
    assert client.get("/admin/dashboard").status_code == 200

    logout_response = client.get("/admin/logout")

    assert logout_response.status_code == 302
    assert "/admin/login" in logout_response.headers["Location"]
    response = client.get("/admin/dashboard")
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_weak_config_fallback_does_not_login(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(AdminRepository, "find_by_username", staticmethod(lambda username: None))

    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "known-weak-test-password"},
    )

    assert response.status_code == 401
    with client.session_transaction() as sess:
        assert not sess.get("admin_logged_in")


def test_admin_password_is_hash_verified():
    password_hash = generate_password_hash("safe-test-password")

    assert password_hash != "safe-test-password"
    assert check_password_hash(password_hash, "safe-test-password")
    assert not check_password_hash(password_hash, "wrong-password")


def _fake_admin(password_hash):
    return {
        "id": 1,
        "username": "secure-admin",
        "password_hash": password_hash,
        "display_name": "測試管理員",
        "role": "owner",
        "is_active": 1,
    }


def test_public_pages_load():
    app = create_app(TestConfig)
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/menu").status_code == 200
    assert client.get("/contact").status_code == 200
