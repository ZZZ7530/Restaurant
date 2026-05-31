from app import create_app
from app.repositories.order_repository import OrderRepository


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


def test_takeout_page_loads_without_database():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.get("/orders/takeout")

    assert response.status_code == 200
    assert "外帶訂餐".encode() in response.data


def test_create_order(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(OrderRepository, "create_order", staticmethod(lambda order_data, items: 11))

    response = client.post(
        "/orders",
        json={
            "customer_name": "陳小姐",
            "customer_phone": "0987654321",
            "pickup_date": "2026-05-22",
            "pickup_time": "19:00",
            "items": [
                {
                    "menu_item_id": 1,
                    "item_name": "三杯雞",
                    "unit_price": 280,
                    "quantity": 2,
                }
            ],
        },
    )

    data = response.get_json()
    assert response.status_code == 201
    assert data["order"]["id"] == 11
    assert data["order"]["total_amount"] == 560.0
