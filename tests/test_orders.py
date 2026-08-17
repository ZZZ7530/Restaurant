from app import create_app
from app.repositories.order_repository import OrderRepository
from app.services.line_service import LineService
from app.services.menu_service import MenuService
from app.services.table_service import TableService


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
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(LineService, "notify_new_takeout_order", classmethod(lambda cls, order: None))
    monkeypatch.setattr(LineService, "notify_customer_takeout_order_success", classmethod(lambda cls, order: None))

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
                    "unit_price": 1,
                    "quantity": 2,
                }
            ],
        },
    )

    data = response.get_json()
    assert response.status_code == 201
    assert data["order"]["id"] == 11
    assert data["order"]["items"][0]["item_name"] == "白灼蝦"
    assert data["order"]["items"][0]["unit_price"] == 480.0
    assert data["order"]["total_amount"] == 960.0


def test_create_order_uses_server_side_price_and_name(monkeypatch):
    captured = {}
    app = create_app(TestConfig)
    client = app.test_client()

    def fake_create_order(order_data, items):
        captured["order_data"] = order_data
        captured["items"] = items
        return 21

    monkeypatch.setattr(OrderRepository, "create_order", staticmethod(fake_create_order))
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(LineService, "notify_new_takeout_order", classmethod(lambda cls, order: None))
    monkeypatch.setattr(LineService, "notify_customer_takeout_order_success", classmethod(lambda cls, order: None))

    response = client.post(
        "/orders",
        json={
            "customer_name": "陳小姐",
            "customer_phone": "0987654321",
            "pickup_date": "2026-05-22",
            "pickup_time": "19:00",
            "total_amount": 1,
            "items": [
                {
                    "menu_item_id": 1,
                    "item_name": "偽造菜名",
                    "unit_price": 1,
                    "quantity": 1,
                    "line_total": 1,
                    "is_market_price": True,
                },
                {
                    "menu_item_id": 2,
                    "item_name": "偽造規格菜名",
                    "specification": "中",
                    "unit_price": 1,
                    "quantity": 2,
                    "is_market_price": False,
                },
            ],
        },
    )

    data = response.get_json()
    assert response.status_code == 201
    assert data["order"]["total_amount"] == 1320.0
    assert captured["order_data"]["total_amount"] == 1320
    assert captured["order_data"]["subtotal"] == 1320
    assert captured["items"][0]["item_name"] == "白灼蝦"
    assert captured["items"][0]["unit_price"] == 480
    assert captured["items"][0]["line_total"] == 480
    assert captured["items"][1]["item_name"] == "塔香蛤蜊"
    assert captured["items"][1]["specification"] == "中"
    assert captured["items"][1]["unit_price"] == 420
    assert captured["items"][1]["line_total"] == 840


def test_market_price_is_decided_by_server(monkeypatch):
    captured = {}
    app = create_app(TestConfig)
    client = app.test_client()

    monkeypatch.setattr(
        OrderRepository,
        "create_order",
        staticmethod(lambda order_data, items: captured.update(order_data=order_data, items=items) or 22),
    )
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(LineService, "notify_new_takeout_order", classmethod(lambda cls, order: None))
    monkeypatch.setattr(LineService, "notify_customer_takeout_order_success", classmethod(lambda cls, order: None))

    response = client.post(
        "/orders",
        json={
            "customer_name": "陳小姐",
            "customer_phone": "0987654321",
            "pickup_date": "2026-05-22",
            "pickup_time": "19:00",
            "items": [
                {
                    "menu_item_id": 3,
                    "item_name": "烤鮮魚",
                    "unit_price": 9999,
                    "quantity": 2,
                    "is_market_price": False,
                }
            ],
        },
    )

    assert response.status_code == 201
    assert captured["order_data"]["total_amount"] == 0
    assert captured["items"][0]["item_name"] == "烤鮮魚"
    assert captured["items"][0]["unit_price"] == 0
    assert captured["items"][0]["line_total"] == 0
    assert captured["items"][0]["note"] == "時價餐點，需由店家確認價格"


def test_rejects_invalid_customer_order_items(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))

    base_payload = {
        "customer_name": "陳小姐",
        "customer_phone": "0987654321",
        "pickup_date": "2026-05-22",
        "pickup_time": "19:00",
    }
    invalid_items = [
        {"menu_item_id": 999, "quantity": 1},
        {"menu_item_id": 2, "specification": "特大", "quantity": 1},
        {"menu_item_id": 1, "specification": "中", "quantity": 1},
        {"menu_item_id": 1, "quantity": 0},
        {"menu_item_id": 1, "quantity": -1},
        {"menu_item_id": 1, "quantity": 100},
    ]

    for invalid_item in invalid_items:
        response = client.post("/orders", json={**base_payload, "items": [invalid_item]})
        assert response.status_code == 400


def test_dine_in_order_validates_active_table_and_server_price(monkeypatch):
    captured = {}
    app = create_app(TestConfig)
    client = app.test_client()

    monkeypatch.setattr(
        OrderRepository,
        "create_order",
        staticmethod(lambda order_data, items: captured.update(order_data=order_data, items=items) or 31),
    )
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        TableService,
        "get_active_table",
        staticmethod(lambda table_number: {"table_number": "1", "display_name": "1 號桌"} if table_number == "1" else None),
    )
    monkeypatch.setattr(LineService, "notify_new_dine_in_order", classmethod(lambda cls, order: None))

    response = client.post(
        "/orders/dine-in",
        json={
            "table_number": "1",
            "total_amount": 1,
            "items": [
                {
                    "menu_item_id": 2,
                    "item_name": "偽造菜名",
                    "specification": "小",
                    "unit_price": 1,
                    "quantity": 3,
                }
            ],
        },
    )

    data = response.get_json()
    assert response.status_code == 201
    assert data["order"]["total_amount"] == 900.0
    assert captured["order_data"]["table_number"] == "1"
    assert captured["items"][0]["item_name"] == "塔香蛤蜊"
    assert captured["items"][0]["unit_price"] == 300


def test_takeout_order_notifies_store_and_bound_customer(monkeypatch):
    calls = []
    app = create_app(TestConfig)
    client = app.test_client()

    monkeypatch.setattr(OrderRepository, "create_order", staticmethod(lambda order_data, items: 41))
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        LineService,
        "notify_new_takeout_order",
        classmethod(lambda cls, order: calls.append(("store", order["customer_phone"]))),
    )
    monkeypatch.setattr(
        LineService,
        "notify_customer_takeout_order_success",
        classmethod(lambda cls, order: calls.append(("customer", order["customer_phone"]))),
    )

    response = client.post(
        "/orders",
        json={
            "customer_name": "陳小姐",
            "customer_phone": "0987654321",
            "pickup_date": "2026-05-22",
            "pickup_time": "19:00",
            "items": [{"menu_item_id": 1, "quantity": 1}],
        },
    )

    assert response.status_code == 201
    assert calls == [("store", "0987654321"), ("customer", "0987654321")]


def test_customer_takeout_notification_failure_does_not_block(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()

    monkeypatch.setattr(OrderRepository, "create_order", staticmethod(lambda order_data, items: 42))
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(LineService, "notify_new_takeout_order", classmethod(lambda cls, order: None))
    monkeypatch.setattr(
        LineService,
        "notify_customer_takeout_order_success",
        classmethod(lambda cls, order: (_ for _ in ()).throw(RuntimeError("line failed"))),
    )

    response = client.post(
        "/orders",
        json={
            "customer_name": "陳小姐",
            "customer_phone": "0987654321",
            "pickup_date": "2026-05-22",
            "pickup_time": "19:00",
            "items": [{"menu_item_id": 1, "quantity": 1}],
        },
    )

    assert response.status_code == 201
    assert response.get_json()["order"]["id"] == 42


def test_dine_in_order_only_notifies_store(monkeypatch):
    calls = []
    app = create_app(TestConfig)
    client = app.test_client()

    monkeypatch.setattr(OrderRepository, "create_order", staticmethod(lambda order_data, items: 43))
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        TableService,
        "get_active_table",
        staticmethod(lambda table_number: {"table_number": "1", "display_name": "1 號桌"} if table_number == "1" else None),
    )
    monkeypatch.setattr(
        LineService,
        "notify_new_dine_in_order",
        classmethod(lambda cls, order: calls.append(("store", order["table_number"]))),
    )
    monkeypatch.setattr(
        LineService,
        "notify_customer_takeout_order_success",
        classmethod(lambda cls, order: calls.append(("customer", order["customer_phone"]))),
    )

    response = client.post(
        "/orders/dine-in",
        json={
            "table_number": "1",
            "items": [{"menu_item_id": 1, "quantity": 1}],
        },
    )

    assert response.status_code == 201
    assert calls == [("store", "1")]


def test_dine_in_order_rejects_inactive_table(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    monkeypatch.setattr(TableService, "get_active_table", staticmethod(lambda table_number: None))

    response = client.post(
        "/orders/dine-in",
        json={
            "table_number": "404",
            "items": [{"menu_item_id": 1, "quantity": 1}],
        },
    )

    assert response.status_code == 400


def _fake_menu_items():
    return [
        {
            "menu_item_id": 1,
            "name": "白灼蝦",
            "category_name": "海鮮",
            "description": "",
            "price": 480,
            "display_price_label": "NT$ 480",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 2,
            "name": "塔香蛤蜊",
            "category_name": "熱炒",
            "description": "",
            "price": 300,
            "display_price_label": "小 NT$ 300 / 中 NT$ 420",
            "price_options": [
                {"specification": "小", "price": 300, "label": "小 NT$300"},
                {"specification": "中", "price": 420, "label": "中 NT$420"},
            ],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 3,
            "name": "烤鮮魚",
            "category_name": "時價料理",
            "description": "",
            "price": 0,
            "display_price_label": "時價",
            "price_options": [],
            "is_market_price": True,
            "image_filename": "",
        },
    ]
