import base64
import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app


class LineService:
    PUSH_MESSAGE_URL = "https://api.line.me/v2/bot/message/push"
    REPLY_MESSAGE_URL = "https://api.line.me/v2/bot/message/reply"

    @staticmethod
    def verify_webhook_signature(body, signature):
        channel_secret = current_app.config.get("LINE_CHANNEL_SECRET", "").strip()
        if not channel_secret:
            current_app.logger.warning("LINE webhook rejected: channel secret is not configured.")
            return False
        if not signature:
            current_app.logger.warning("LINE webhook rejected: missing signature.")
            return False

        try:
            digest = hmac.new(
                channel_secret.encode("utf-8"),
                body,
                hashlib.sha256,
            ).digest()
            expected_signature = base64.b64encode(digest).decode("utf-8")
        except Exception:
            current_app.logger.exception("LINE webhook signature calculation failed.")
            return False

        return hmac.compare_digest(expected_signature, signature.strip())

    @staticmethod
    def is_user_notification_configured():
        return bool(
            current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN")
            and current_app.config.get("LINE_USER_ID")
        )

    @staticmethod
    def is_store_notification_configured():
        return bool(
            current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN")
            and (
                current_app.config.get("LINE_GROUP_ID")
                or current_app.config.get("LINE_USER_ID")
            )
        )

    @classmethod
    def send_test_message(cls):
        message = "\u3010Restaurant System Demo\u3011\nLINE \u901a\u77e5\u6e2c\u8a66\u6210\u529f"
        return cls.send_text_to_user(message)

    @classmethod
    def notify_new_reservation(cls, reservation):
        message = "\n".join(
            [
                "\u3010\u65b0\u8a02\u4f4d\u3011",
                f"\u59d3\u540d\uff1a{reservation.get('customer_name') or '-'}",
                f"\u96fb\u8a71\uff1a{reservation.get('customer_phone') or '-'}",
                f"\u65e5\u671f\uff1a{reservation.get('reservation_date') or '-'}",
                f"\u6642\u9593\uff1a{reservation.get('reservation_time') or '-'}",
                f"\u4eba\u6578\uff1a{reservation.get('party_size') or '-'}",
                f"\u5099\u8a3b\uff1a{reservation.get('note') or '-'}",
            ]
        )
        return cls._safe_store_notification(message)

    @classmethod
    def notify_new_takeout_order(cls, order):
        pickup_time = f"{order.get('pickup_date') or '-'} {order.get('pickup_time') or '-'}"
        message = "\n".join(
            [
                "\u3010\u65b0\u5916\u5e36\u8a02\u55ae\u3011",
                f"\u59d3\u540d\uff1a{order.get('customer_name') or '-'}",
                f"\u96fb\u8a71\uff1a{order.get('customer_phone') or '-'}",
                f"\u53d6\u9910\u6642\u9593\uff1a{pickup_time}",
                f"\u9910\u9ede\uff1a{cls._format_items(order.get('items', []))}",
                f"\u7e3d\u91d1\u984d\uff1a{cls._format_total(order.get('total_amount'))}",
            ]
        )
        return cls._safe_store_notification(message)

    @classmethod
    def notify_new_dine_in_order(cls, order):
        table_label = order.get("table_display_name") or order.get("table_number") or "-"
        message = "\n".join(
            [
                "\u3010\u65b0\u5167\u7528\u8a02\u55ae\u3011",
                f"\u684c\u865f\uff1a{table_label}",
                f"\u9910\u9ede\uff1a{cls._format_items(order.get('items', []))}",
                f"\u7e3d\u91d1\u984d\uff1a{cls._format_total(order.get('total_amount'))}",
            ]
        )
        return cls._safe_store_notification(message)

    @classmethod
    def notify_customer_reservation_success(cls, reservation):
        from app.services.line_customer_binding_service import LineCustomerBindingService

        line_user_id = LineCustomerBindingService.find_active_user_id_by_phone(
            reservation.get("customer_phone")
        )
        if not line_user_id:
            return {"ok": False, "skipped": True, "error": "customer line binding not found"}

        message = "\n".join(
            [
                "【訂位成功】",
                "您的訂位已建立",
                f"日期：{reservation.get('reservation_date') or '-'}",
                f"時間：{reservation.get('reservation_time') or '-'}",
                f"人數：{reservation.get('party_size') or '-'}",
                "感謝您的預約。",
            ]
        )
        return cls._safe_customer_notification(line_user_id, message)

    @classmethod
    def notify_customer_takeout_order_success(cls, order):
        from app.services.line_customer_binding_service import LineCustomerBindingService

        line_user_id = LineCustomerBindingService.find_active_user_id_by_phone(
            order.get("customer_phone")
        )
        if not line_user_id:
            return {"ok": False, "skipped": True, "error": "customer line binding not found"}

        pickup_time = f"{order.get('pickup_date') or '-'} {order.get('pickup_time') or '-'}"
        message = "\n".join(
            [
                "【外帶訂單建立成功】",
                f"訂單編號：{order.get('order_no') or '-'}",
                f"取餐時間：{pickup_time}",
                f"總金額：{cls._format_total(order.get('total_amount'))}",
                "請依預定時間到店取餐。",
            ]
        )
        return cls._safe_customer_notification(line_user_id, message)

    @classmethod
    def send_text_to_user(cls, message):
        token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        user_id = current_app.config.get("LINE_USER_ID", "").strip()

        if not token or not user_id:
            current_app.logger.info("LINE notification skipped: missing token or user id.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "LINE_CHANNEL_ACCESS_TOKEN or LINE_USER_ID is missing.",
            }

        return cls._push_message(token=token, target_id=user_id, message=message)

    @classmethod
    def send_text_to_line_user(cls, line_user_id, message):
        token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        target_id = str(line_user_id or "").strip()

        if not token or not target_id:
            current_app.logger.info("LINE customer notification skipped: missing token or user id.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "LINE_CHANNEL_ACCESS_TOKEN or customer line user id is missing.",
            }

        return cls._push_message(token=token, target_id=target_id, message=message)

    @classmethod
    def send_text_to_store(cls, message):
        token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        group_id = current_app.config.get("LINE_GROUP_ID", "").strip()
        user_id = current_app.config.get("LINE_USER_ID", "").strip()
        target_id = group_id or user_id
        target_type = "group" if group_id else "user"

        if not token or not target_id:
            current_app.logger.info("LINE notification skipped: missing token or target id.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "LINE_CHANNEL_ACCESS_TOKEN and LINE_USER_ID or LINE_GROUP_ID are required.",
            }

        current_app.logger.info("LINE store notification target type: %s", target_type)
        return cls._push_message(token=token, target_id=target_id, message=message)

    @classmethod
    def _safe_store_notification(cls, message):
        try:
            return cls.send_text_to_store(message)
        except Exception as exc:
            current_app.logger.exception("LINE store notification failed without blocking request.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": str(exc),
            }

    @classmethod
    def _safe_customer_notification(cls, line_user_id, message):
        try:
            return cls.send_text_to_line_user(line_user_id, message)
        except Exception:
            current_app.logger.exception("LINE customer notification failed without blocking request.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "customer notification failed",
            }

    @classmethod
    def safe_reply_text(cls, reply_token, message):
        try:
            return cls.reply_text(reply_token, message)
        except Exception:
            current_app.logger.exception("LINE reply failed without blocking webhook.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "reply failed",
            }

    @classmethod
    def reply_text(cls, reply_token, message):
        token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        reply_token = str(reply_token or "").strip()

        if not token or not reply_token:
            current_app.logger.info("LINE reply skipped: missing token or reply token.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "LINE_CHANNEL_ACCESS_TOKEN or reply token is missing.",
            }

        payload = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": message}],
        }
        return cls._send_line_request(cls.REPLY_MESSAGE_URL, token, payload)

    @staticmethod
    def _format_items(items):
        formatted_items = []
        for item in items:
            name = item.get("item_name") or "-"
            specification = item.get("specification")
            quantity = item.get("quantity") or 0
            if specification:
                formatted_items.append(f"{name}\uff08{specification}\uff09 x{quantity}")
            else:
                formatted_items.append(f"{name} x{quantity}")
        return "\u3001".join(formatted_items) if formatted_items else "-"

    @staticmethod
    def _format_total(total_amount):
        try:
            return f"NT${float(total_amount):.0f}"
        except (TypeError, ValueError):
            return "\u9700\u5e97\u5bb6\u78ba\u8a8d"

    @classmethod
    def _push_message(cls, token, target_id, message):
        payload = {
            "to": target_id,
            "messages": [
                {
                    "type": "text",
                    "text": message,
                }
            ],
        }
        return cls._send_line_request(cls.PUSH_MESSAGE_URL, token, payload)

    @classmethod
    def _send_line_request(cls, url, token, payload):
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=10) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                current_app.logger.info(
                    "LINE message request completed. status=%s ok=%s",
                    response.status,
                    200 <= response.status < 300,
                )
                return {
                    "ok": 200 <= response.status < 300,
                    "status_code": response.status,
                    "response_body": response_body,
                    "error": None,
                }
        except HTTPError as exc:
            exc.read()
            current_app.logger.exception("LINE message request failed. status=%s", exc.code)
            return {
                "ok": False,
                "status_code": exc.code,
                "response_body": "",
                "error": str(exc),
            }
        except URLError:
            current_app.logger.exception("LINE message request failed: network error.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "network error",
            }
        except Exception:
            current_app.logger.exception("LINE message request failed: unexpected error.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "unexpected error",
            }
