import json
from types import SimpleNamespace

from app import create_app
from app.services.ai_recommendation_service import AiRecommendationService
from app.services.menu_service import MenuService


class BaseAIConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"
    RESTAURANT_NAME = "測試餐廳"
    AI_MOCK_MODE = True
    OPENAI_API_KEY = ""
    OPENAI_MODEL = ""
    OPENAI_API_BASE_URL = ""


class OpenAIConfig(BaseAIConfig):
    AI_MOCK_MODE = False
    OPENAI_API_KEY = "test-key"
    OPENAI_MODEL = "test-model"


class FakeResponses:
    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(output_text=json.dumps(self.payload, ensure_ascii=False))


class FakeOpenAIClient:
    def __init__(self, payload=None, error=None):
        self.responses = FakeResponses(payload=payload, error=error)


def setup_function():
    AiRecommendationService._ip_calls.clear()
    AiRecommendationService._session_calls.clear()


def test_mock_mode_never_calls_openai(monkeypatch):
    app = create_app(BaseAIConfig)
    app.config["OPENAI_API_KEY"] = "present-but-unused"
    app.config["OPENAI_MODEL"] = "present-but-unused"
    client = app.test_client()

    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: (_ for _ in ()).throw(AssertionError("OpenAI should not be called"))),
    )

    response = client.post("/api/ai/recommendations", json=_request_payload())

    data = response.get_json()
    assert response.status_code == 200
    assert data["ok"] is True
    assert data["items"]


def test_openai_mode_without_api_key_returns_503(monkeypatch):
    app = create_app(OpenAIConfig)
    app.config["OPENAI_API_KEY"] = ""
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))

    response = client.post("/api/ai/recommendations", json=_request_payload())

    assert response.status_code == 503
    assert response.get_json()["message"] == "AI 推薦目前尚未啟用"


def test_openai_mode_without_model_returns_503(monkeypatch):
    app = create_app(OpenAIConfig)
    app.config["OPENAI_MODEL"] = ""
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))

    response = client.post("/api/ai/recommendations", json=_request_payload())

    assert response.status_code == 503
    assert response.get_json()["message"] == "AI 推薦目前尚未啟用"


def test_openai_structured_response_is_validated_with_server_menu(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {
                    "menu_item_id": 2,
                    "quantity": 2,
                    "specification": "中",
                    "unit_price": 1,
                    "reason": "符合海鮮需求",
                },
                {
                    "menu_item_id": 3,
                    "quantity": 1,
                    "specification": "",
                    "unit_price": 9999,
                    "reason": "搭配一道時價料理",
                },
            ],
            "reason": "適合多人分享。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post("/api/ai/recommendations", json=_request_payload())

    data = response.get_json()
    assert response.status_code == 200
    assert data["ok"] is True
    assert fake_client.responses.calls
    assert fake_client.responses.calls[0]["model"] == "test-model"
    assert fake_client.responses.calls[0]["text"]["format"]["type"] == "json_schema"
    assert data["items"][0]["name"] == "塔香蛤蜊"
    assert data["items"][0]["unit_price"] == 420
    assert data["items"][0]["display_price_label"] == "中 NT$ 420"
    assert data["items"][1]["name"] == "烤鮮魚"
    assert data["items"][1]["unit_price"] == 0
    assert data["items"][1]["is_market_price"] is True
    assert 1750 <= data["fixed_total"] <= 2500
    assert data["market_price_count"] == 1
    assert "3900" not in data["reason"]
    assert "元" not in data["reason"]


def test_openai_invalid_items_are_excluded(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {"menu_item_id": 999, "quantity": 1, "specification": "", "reason": "不存在"},
                {"menu_item_id": 2, "quantity": 1, "specification": "特大", "reason": "錯誤規格"},
                {"menu_item_id": 1, "quantity": 1, "specification": "中", "reason": "不應有規格"},
                {"menu_item_id": 1, "quantity": 1, "specification": "", "reason": "有效餐點"},
            ],
            "reason": "測試排除錯誤品項。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post("/api/ai/recommendations", json=_request_payload())

    data = response.get_json()
    assert response.status_code == 200
    assert [item["menu_item_id"] for item in data["items"]] == [1]
    assert data["items"][0]["unit_price"] == 480


def test_openai_malformed_output_returns_friendly_503(monkeypatch):
    fake_client = SimpleNamespace(
        responses=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(output_text="not-json"))
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post("/api/ai/recommendations", json=_request_payload())

    assert response.status_code == 503
    assert response.get_json()["message"] == "AI 推薦目前暫時無法使用"


def test_openai_timeout_authentication_and_rate_limit_are_friendly(monkeypatch):
    class AuthenticationError(Exception):
        pass

    class RateLimitError(Exception):
        pass

    cases = [
        (TimeoutError("timeout"), "AI 服務忙碌中，請稍後再試"),
        (AuthenticationError("bad key"), "AI 推薦目前尚未啟用"),
        (RateLimitError("quota exceeded"), "AI 服務忙碌中，請稍後再試"),
    ]

    for error, expected_message in cases:
        setup_function()
        fake_client = FakeOpenAIClient(error=error)
        app = create_app(OpenAIConfig)
        client = app.test_client()
        monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
        monkeypatch.setattr(
            AiRecommendationService,
            "_create_openai_client",
            classmethod(lambda cls: fake_client),
        )

        response = client.post("/api/ai/recommendations", json=_request_payload())

        assert response.status_code == 503
        assert response.get_json()["message"] == expected_message


def test_ai_input_validation_and_rate_limit(monkeypatch):
    app = create_app(BaseAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))

    assert client.post("/api/ai/recommendations", json={**_request_payload(), "party_size": 0}).status_code == 400
    setup_function()
    assert client.post("/api/ai/recommendations", json={**_request_payload(), "budget": -1}).status_code == 400
    setup_function()
    assert client.post("/api/ai/recommendations", json={**_request_payload(), "message": "x" * 501}).status_code == 400

    setup_function()
    for _ in range(5):
        assert client.post("/api/ai/recommendations", json=_request_payload()).status_code == 200
    assert client.post("/api/ai/recommendations", json=_request_payload()).status_code == 429


def test_budget_is_server_side_hard_cap_for_common_budget_levels(monkeypatch):
    budgets = [1000, 1500, 2500, 4000]

    for budget in budgets:
        setup_function()
        fake_client = FakeOpenAIClient(
            payload={
                "items": [
                    {"menu_item_id": 4, "quantity": 2, "specification": "", "reason": "故意超過預算"},
                    {"menu_item_id": 5, "quantity": 2, "specification": "", "reason": "故意超過預算"},
                    {"menu_item_id": 2, "quantity": 3, "specification": "中", "reason": "測試規格與數量"},
                    {"menu_item_id": 3, "quantity": 1, "specification": "", "reason": "時價不計固定價格"},
                ],
                "reason": "測試預算硬上限。",
            }
        )
        app = create_app(OpenAIConfig)
        client = app.test_client()
        monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_rich_menu_items))
        monkeypatch.setattr(
            AiRecommendationService,
            "_create_openai_client",
            classmethod(lambda cls: fake_client),
        )

        response = client.post(
            "/api/ai/recommendations",
            json={**_request_payload(), "budget": budget, "party_size": 6},
        )

        data = response.get_json()
        assert response.status_code == 200
        assert data["fixed_total"] <= budget
        assert any(item["is_market_price"] for item in data["items"])


def test_budget_utilization_improves_when_matching_items_are_available(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {"menu_item_id": 1, "quantity": 1, "specification": "", "reason": "先給低預算利用率"}
            ],
            "reason": "測試提高預算利用率。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_rich_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post(
        "/api/ai/recommendations",
        json={**_request_payload(), "budget": 4000, "party_size": 6},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert 2800 <= data["fixed_total"] <= 4000
    assert len(data["items"]) <= 7


def test_quantity_and_specification_prices_are_recomputed_server_side(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {
                    "menu_item_id": 2,
                    "quantity": 3,
                    "specification": "中",
                    "unit_price": 1,
                    "reason": "偽造價格但有效規格",
                }
            ],
            "reason": "測試數量與規格價格。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post(
        "/api/ai/recommendations",
        json={**_request_payload(), "budget": 1500},
    )

    data = response.get_json()
    assert response.status_code == 200
    spec_item = next(item for item in data["items"] if item["menu_item_id"] == 2)
    assert spec_item["unit_price"] == 420
    assert spec_item["quantity"] == 3
    assert data["fixed_total"] <= 1500
    assert data["fixed_total"] >= 1260


def test_market_price_warning_notes_budget_can_change(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {"menu_item_id": 3, "quantity": 1, "specification": "", "reason": "時價料理"}
            ],
            "reason": "測試時價。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_fake_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post("/api/ai/recommendations", json={**_request_payload(), "budget": 1000})

    data = response.get_json()
    assert response.status_code == 200
    market_item = next(item for item in data["items"] if item["menu_item_id"] == 3)
    assert market_item["unit_price"] == 0
    assert market_item["is_market_price"] is True
    assert data["fixed_total"] <= 1000
    assert "時價料理未計入固定價格合計" in " ".join(data["warnings"])


def test_budget_utilization_does_not_force_unmatched_items(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {"menu_item_id": 1, "quantity": 1, "specification": "", "reason": "唯一符合限制的餐點"}
            ],
            "reason": "限制太多時不要硬塞。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_rich_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post(
        "/api/ai/recommendations",
        json={
            **_request_payload(),
            "budget": 4000,
            "preferences": ["只想吃白灼蝦"],
            "dietary_needs": ["不要其他菜"],
            "message": "只想吃白灼蝦，不要其他菜",
        },
    )

    data = response.get_json()
    assert response.status_code == 200
    assert data["fixed_total"] < 2800
    assert {item["menu_item_id"] for item in data["items"] if not item["is_market_price"]} == {1}


def test_budget_utilization_continues_when_ai_already_returned_max_items(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {"menu_item_id": 1, "quantity": 1, "specification": "", "reason": "海鮮"},
                {"menu_item_id": 2, "quantity": 1, "specification": "", "reason": "魚"},
                {"menu_item_id": 3, "quantity": 1, "specification": "", "reason": "蝦"},
                {"menu_item_id": 4, "quantity": 1, "specification": "", "reason": "海鮮"},
                {"menu_item_id": 5, "quantity": 1, "specification": "", "reason": "海鮮"},
                {"menu_item_id": 6, "quantity": 1, "specification": "", "reason": "海鮮"},
                {"menu_item_id": 7, "quantity": 1, "specification": "", "reason": "時價"},
            ],
            "reason": "固定價格合計約3900元。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_iterative_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post(
        "/api/ai/recommendations",
        json={
            **_request_payload(),
            "party_size": 6,
            "budget": 4000,
            "preferences": ["海鮮", "魚", "蝦"],
            "dietary_needs": ["不要辣"],
        },
    )

    data = response.get_json()
    assert response.status_code == 200
    assert 2800 <= data["fixed_total"] <= 4000
    assert len(data["items"]) == 7
    assert any(item["quantity"] > 1 for item in data["items"] if not item["is_market_price"])
    assert "3900" not in data["reason"]
    assert "2350" not in data["reason"]
    assert "元" not in data["reason"]


def test_budget_utilization_runs_after_invalid_ai_items_are_removed(monkeypatch):
    fake_client = FakeOpenAIClient(
        payload={
            "items": [
                {"menu_item_id": 999, "quantity": 1, "specification": "", "reason": "不存在"},
                {"menu_item_id": 1, "quantity": 1, "specification": "", "reason": "低利用率"},
            ],
            "reason": "固定價格合計約3900元。",
        }
    )
    app = create_app(OpenAIConfig)
    client = app.test_client()
    monkeypatch.setattr(MenuService, "list_ai_recommendable_items", staticmethod(_rich_menu_items))
    monkeypatch.setattr(
        AiRecommendationService,
        "_create_openai_client",
        classmethod(lambda cls: fake_client),
    )

    response = client.post(
        "/api/ai/recommendations",
        json={**_request_payload(), "party_size": 6, "budget": 4000},
    )

    data = response.get_json()
    assert response.status_code == 200
    assert 2800 <= data["fixed_total"] <= 4000
    assert 999 not in {item["menu_item_id"] for item in data["items"]}
    assert "3900" not in data["reason"]


def _request_payload():
    return {
        "mode": "takeout",
        "party_size": 4,
        "budget": 2500,
        "preferences": ["海鮮", "魚", "蝦"],
        "dietary_needs": ["不辣"],
        "message": "希望有魚、有蝦、有湯",
    }


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


def _rich_menu_items():
    items = _fake_menu_items()
    items.extend(
        [
            {
                "menu_item_id": 4,
                "name": "海鮮拼盤",
                "category_name": "海鮮",
                "description": "多人分享海鮮料理",
                "price": 1200,
                "display_price_label": "NT$ 1,200",
                "price_options": [],
                "is_market_price": False,
                "image_filename": "",
            },
            {
                "menu_item_id": 5,
                "name": "清蒸魚",
                "category_name": "海鮮",
                "description": "不辣魚料理",
                "price": 880,
                "display_price_label": "NT$ 880",
                "price_options": [],
                "is_market_price": False,
                "image_filename": "",
            },
            {
                "menu_item_id": 6,
                "name": "蒜蓉蝦",
                "category_name": "海鮮",
                "description": "蝦料理",
                "price": 680,
                "display_price_label": "NT$ 680",
                "price_options": [],
                "is_market_price": False,
                "image_filename": "",
            },
        ]
    )
    return items


def _iterative_menu_items():
    return [
        {
            "menu_item_id": 1,
            "name": "白灼蝦",
            "category_name": "海鮮",
            "description": "蝦料理",
            "price": 480,
            "display_price_label": "NT$ 480",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 2,
            "name": "清蒸魚",
            "category_name": "海鮮",
            "description": "魚料理",
            "price": 420,
            "display_price_label": "NT$ 420",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 3,
            "name": "蒜蓉蝦",
            "category_name": "海鮮",
            "description": "蝦料理",
            "price": 350,
            "display_price_label": "NT$ 350",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 4,
            "name": "炒海瓜子",
            "category_name": "海鮮",
            "description": "海鮮熱炒",
            "price": 300,
            "display_price_label": "NT$ 300",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 5,
            "name": "海鮮炒飯",
            "category_name": "主食",
            "description": "海鮮主食",
            "price": 400,
            "display_price_label": "NT$ 400",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 6,
            "name": "蛤蜊湯",
            "category_name": "湯品",
            "description": "海鮮湯",
            "price": 400,
            "display_price_label": "NT$ 400",
            "price_options": [],
            "is_market_price": False,
            "image_filename": "",
        },
        {
            "menu_item_id": 7,
            "name": "現流鮮魚",
            "category_name": "時價料理",
            "description": "魚料理",
            "price": 0,
            "display_price_label": "時價",
            "price_options": [],
            "is_market_price": True,
            "image_filename": "",
        },
    ]
