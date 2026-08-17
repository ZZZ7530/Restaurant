import base64
import hashlib
import hmac
import json

from app import create_app
import app.services.line_service as line_service_module
from app.repositories.line_customer_binding_repository import LineCustomerBindingRepository
from app.services.line_service import LineService


class TestConfig:
    TESTING = True
    DEBUG = False
    SECRET_KEY = "test"
    RESTAURANT_NAME = "測試餐廳"
    IS_PRODUCTION = False
    LINE_CHANNEL_ACCESS_TOKEN = ""
    LINE_CHANNEL_SECRET = "test-channel-secret"
    LINE_USER_ID = ""
    LINE_GROUP_ID = ""


def test_line_webhook_rejects_missing_signature():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.post("/line/webhook", data=b'{"events":[]}', content_type="application/json")

    assert response.status_code == 400


def test_line_webhook_rejects_invalid_signature():
    app = create_app(TestConfig)
    client = app.test_client()

    response = client.post(
        "/line/webhook",
        data=b'{"events":[]}',
        content_type="application/json",
        headers={"X-Line-Signature": "invalid-signature"},
    )

    assert response.status_code == 403


def test_line_webhook_accepts_valid_signature():
    app = create_app(TestConfig)
    client = app.test_client()
    body = json.dumps(
        {"events": [{"type": "message", "message": {"type": "text", "text": "hello"}}]},
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/line/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Line-Signature": _line_signature(body)},
    )

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_line_webhook_bind_phone_creates_binding_and_replies(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    captured = {}

    def fake_upsert(customer_phone, line_user_id, display_name=None):
        captured["customer_phone"] = customer_phone
        captured["line_user_id"] = line_user_id
        captured["display_name"] = display_name

    def fake_reply(reply_token, message):
        captured["reply_token"] = reply_token
        captured["reply_message"] = message
        return {"ok": True}

    monkeypatch.setattr(LineCustomerBindingRepository, "upsert", staticmethod(fake_upsert))
    monkeypatch.setattr(LineService, "safe_reply_text", classmethod(lambda cls, token, message: fake_reply(token, message)))

    body = json.dumps(
        {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"type": "user", "userId": "test-line-user-id"},
                    "message": {"type": "text", "text": "綁定 0912345678"},
                }
            ]
        },
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/line/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Line-Signature": _line_signature(body)},
    )

    assert response.status_code == 200
    assert captured["customer_phone"] == "0912345678"
    assert captured["line_user_id"] == "test-line-user-id"
    assert captured["display_name"] is None
    assert captured["reply_token"] == "reply-token"
    assert "綁定成功" in captured["reply_message"]


def test_line_webhook_bind_same_phone_can_update(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    calls = []

    monkeypatch.setattr(
        LineCustomerBindingRepository,
        "upsert",
        staticmethod(lambda customer_phone, line_user_id, display_name=None: calls.append((customer_phone, line_user_id))),
    )
    monkeypatch.setattr(LineService, "safe_reply_text", classmethod(lambda cls, token, message: {"ok": True}))

    for line_user_id in ("first-user", "second-user"):
        body = json.dumps(
            {
                "events": [
                    {
                        "type": "message",
                        "replyToken": "reply-token",
                        "source": {"type": "user", "userId": line_user_id},
                        "message": {"type": "text", "text": "綁定 0912345678"},
                    }
                ]
            },
            separators=(",", ":"),
        ).encode("utf-8")
        response = client.post(
            "/line/webhook",
            data=body,
            content_type="application/json",
            headers={"X-Line-Signature": _line_signature(body)},
        )
        assert response.status_code == 200

    assert calls == [("0912345678", "first-user"), ("0912345678", "second-user")]


def test_line_webhook_malformed_bind_command_replies_without_500(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()
    captured = {}

    monkeypatch.setattr(
        LineCustomerBindingRepository,
        "upsert",
        staticmethod(lambda customer_phone, line_user_id, display_name=None: (_ for _ in ()).throw(AssertionError("should not bind"))),
    )
    monkeypatch.setattr(
        LineService,
        "safe_reply_text",
        classmethod(lambda cls, token, message: captured.update(message=message) or {"ok": True}),
    )
    body = json.dumps(
        {
            "events": [
                {
                    "type": "message",
                    "replyToken": "reply-token",
                    "source": {"type": "user", "userId": "test-line-user-id"},
                    "message": {"type": "text", "text": "綁定 abc"},
                }
            ]
        },
        separators=(",", ":"),
    ).encode("utf-8")

    response = client.post(
        "/line/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Line-Signature": _line_signature(body)},
    )

    assert response.status_code == 200
    assert "格式不正確" in captured["message"]


def test_line_webhook_rejects_malformed_request_without_500():
    app = create_app(TestConfig)
    client = app.test_client()
    body = b"{not-json"

    response = client.post(
        "/line/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Line-Signature": _line_signature(body)},
    )

    assert response.status_code == 400


def test_line_webhook_rejects_when_channel_secret_missing():
    class MissingSecretConfig(TestConfig):
        LINE_CHANNEL_SECRET = ""

    app = create_app(MissingSecretConfig)
    client = app.test_client()
    body = b'{"events":[]}'

    response = client.post(
        "/line/webhook",
        data=body,
        content_type="application/json",
        headers={"X-Line-Signature": "anything"},
    )

    assert response.status_code == 503


def test_test_line_endpoint_disabled_in_production():
    class ProductionConfig(TestConfig):
        IS_PRODUCTION = True

    app = create_app(ProductionConfig)
    client = app.test_client()

    response = client.get("/test-line")

    assert response.status_code == 404


def test_line_push_message_still_sends_sanitized_request(monkeypatch):
    class NotificationConfig(TestConfig):
        LINE_CHANNEL_ACCESS_TOKEN = "test-token"
        LINE_GROUP_ID = "test-group-id"

    captured = {}

    class FakeResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        @staticmethod
        def read():
            return b'{"sentMessages":[]}'

    def fake_urlopen(request, timeout=10):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["content_type"] = request.get_header("Content-type")
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse()

    app = create_app(NotificationConfig)
    monkeypatch.setattr(line_service_module, "urlopen", fake_urlopen)

    with app.app_context():
        result = LineService.send_text_to_store("測試通知")

    assert result["ok"] is True
    assert captured["url"] == LineService.PUSH_MESSAGE_URL
    assert captured["authorization"] == "Bearer test-token"
    assert captured["content_type"] == "application/json"
    assert captured["payload"]["to"] == "test-group-id"
    assert captured["payload"]["messages"][0]["text"] == "測試通知"
    assert captured["timeout"] == 10


def test_customer_reservation_notification_uses_bound_line_user(monkeypatch):
    class NotificationConfig(TestConfig):
        LINE_CHANNEL_ACCESS_TOKEN = "test-token"

    captured = {}
    app = create_app(NotificationConfig)
    monkeypatch.setattr(
        LineCustomerBindingRepository,
        "find_active_by_phone",
        staticmethod(lambda phone: {"line_user_id": "customer-user-id"} if phone == "0912345678" else None),
    )
    monkeypatch.setattr(
        LineService,
        "send_text_to_line_user",
        classmethod(lambda cls, user_id, message: captured.update(user_id=user_id, message=message) or {"ok": True}),
    )

    with app.app_context():
        result = LineService.notify_customer_reservation_success(
            {
                "customer_phone": "0912345678",
                "reservation_date": "2026-05-22",
                "reservation_time": "18:30",
                "party_size": 4,
            }
        )

    assert result["ok"] is True
    assert captured["user_id"] == "customer-user-id"
    assert "【訂位成功】" in captured["message"]
    assert "日期：2026-05-22" in captured["message"]


def test_customer_takeout_notification_uses_bound_line_user(monkeypatch):
    class NotificationConfig(TestConfig):
        LINE_CHANNEL_ACCESS_TOKEN = "test-token"

    captured = {}
    app = create_app(NotificationConfig)
    monkeypatch.setattr(
        LineCustomerBindingRepository,
        "find_active_by_phone",
        staticmethod(lambda phone: {"line_user_id": "customer-user-id"} if phone == "0912345678" else None),
    )
    monkeypatch.setattr(
        LineService,
        "send_text_to_line_user",
        classmethod(lambda cls, user_id, message: captured.update(user_id=user_id, message=message) or {"ok": True}),
    )

    with app.app_context():
        result = LineService.notify_customer_takeout_order_success(
            {
                "customer_phone": "0912345678",
                "order_no": "TO202605220001",
                "pickup_date": "2026-05-22",
                "pickup_time": "19:00",
                "total_amount": 960,
            }
        )

    assert result["ok"] is True
    assert captured["user_id"] == "customer-user-id"
    assert "【外帶訂單建立成功】" in captured["message"]
    assert "訂單編號：TO202605220001" in captured["message"]


def test_customer_notification_skips_unbound_phone(monkeypatch):
    app = create_app(TestConfig)
    monkeypatch.setattr(LineCustomerBindingRepository, "find_active_by_phone", staticmethod(lambda phone: None))
    monkeypatch.setattr(
        LineService,
        "send_text_to_line_user",
        classmethod(lambda cls, user_id, message: (_ for _ in ()).throw(AssertionError("should not send"))),
    )

    with app.app_context():
        result = LineService.notify_customer_reservation_success({"customer_phone": "0999999999"})

    assert result["skipped"] is True


def test_public_html_does_not_expose_line_secrets():
    class SecretConfig(TestConfig):
        LINE_CHANNEL_ACCESS_TOKEN = "test-token"
        LINE_CHANNEL_SECRET = "test-channel-secret"
        LINE_USER_ID = "test-user-id"
        LINE_GROUP_ID = "test-group-id"

    app = create_app(SecretConfig)
    client = app.test_client()

    response = client.get("/")

    assert b"test-token" not in response.data
    assert b"test-channel-secret" not in response.data
    assert b"test-user-id" not in response.data
    assert b"test-group-id" not in response.data


def _line_signature(body):
    digest = hmac.new(
        TestConfig.LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256,
    ).digest()
    return base64.b64encode(digest).decode("utf-8")
