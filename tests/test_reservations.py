from app import create_app
from app.repositories.reservation_repository import ReservationRepository
from app.services.line_service import LineService


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
    monkeypatch.setattr(LineService, "notify_new_reservation", classmethod(lambda cls, reservation: None))
    monkeypatch.setattr(
        LineService,
        "notify_customer_reservation_success",
        classmethod(lambda cls, reservation: None),
    )

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


def test_create_reservation_notifies_store_and_bound_customer(monkeypatch):
    calls = []
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(ReservationRepository, "create", staticmethod(lambda data: 8))
    monkeypatch.setattr(
        LineService,
        "notify_new_reservation",
        classmethod(lambda cls, reservation: calls.append(("store", reservation["customer_phone"]))),
    )
    monkeypatch.setattr(
        LineService,
        "notify_customer_reservation_success",
        classmethod(lambda cls, reservation: calls.append(("customer", reservation["customer_phone"]))),
    )

    response = client.post(
        "/reservations",
        data={
            "customer_name": "王小明",
            "customer_phone": "0912345678",
            "reservation_date": "2026-05-22",
            "reservation_time": "18:30",
            "party_size": "4",
        },
    )

    assert response.status_code == 201
    assert calls == [("store", "0912345678"), ("customer", "0912345678")]


def test_customer_reservation_notification_failure_does_not_block(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(ReservationRepository, "create", staticmethod(lambda data: 9))
    monkeypatch.setattr(LineService, "notify_new_reservation", classmethod(lambda cls, reservation: None))
    monkeypatch.setattr(
        LineService,
        "notify_customer_reservation_success",
        classmethod(lambda cls, reservation: (_ for _ in ()).throw(RuntimeError("line failed"))),
    )

    response = client.post(
        "/reservations",
        data={
            "customer_name": "王小明",
            "customer_phone": "0912345678",
            "reservation_date": "2026-05-22",
            "reservation_time": "18:30",
            "party_size": "4",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["reservation"]["id"] == 9
