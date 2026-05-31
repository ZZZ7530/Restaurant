from app import create_app
from app.repositories.reservation_repository import ReservationRepository


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


def test_reservation_page_loads():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/reservations")

    assert response.status_code == 200
    assert "線上訂位".encode() in response.data


def test_create_reservation(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(ReservationRepository, "create", staticmethod(lambda data: 7))

    response = client.post(
        "/reservations",
        data={
            "customer_name": "王小明",
            "customer_phone": "0912345678",
            "reservation_date": "2026-05-22",
            "reservation_time": "18:30",
            "party_size": "4",
            "note": "靠窗",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["reservation"]["id"] == 7
