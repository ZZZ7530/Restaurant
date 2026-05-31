from app import create_app


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
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin123"


def test_admin_dashboard_loads():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/admin")

    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_admin_login_allows_dashboard():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.post(
        "/admin/login",
        data={"username": "admin", "password": "admin123"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "後台總覽".encode() in response.data


def test_public_pages_load():
    app = create_app(TestConfig)
    client = app.test_client()

    assert client.get("/").status_code == 200
    assert client.get("/menu").status_code == 200
    assert client.get("/contact").status_code == 200
