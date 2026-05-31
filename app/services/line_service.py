import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app


class LineService:
    PUSH_MESSAGE_URL = "https://api.line.me/v2/bot/message/push"

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
    def send_text_to_user(cls, message):
        token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        user_id = current_app.config.get("LINE_USER_ID", "").strip()
        print(f"LINE token loaded: {bool(token)}")
        print(f"LINE user id loaded: {bool(user_id)}")
        print(f"LINE target user id: {user_id or '(missing)'}")
        current_app.logger.warning("LINE token loaded: %s", bool(token))
        current_app.logger.warning("LINE user id loaded: %s", bool(user_id))
        current_app.logger.warning("LINE target user id: %s", user_id or "(missing)")

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
    def send_text_to_store(cls, message):
        token = current_app.config.get("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
        group_id = current_app.config.get("LINE_GROUP_ID", "").strip()
        user_id = current_app.config.get("LINE_USER_ID", "").strip()
        target_id = group_id or user_id
        target_type = "group" if group_id else "user"

        print(f"LINE token loaded: {bool(token)}")
        print(f"LINE store target loaded: {bool(target_id)}")
        print(f"LINE target type: {target_type if target_id else '(missing)'}")
        print(f"LINE target id: {target_id or '(missing)'}")
        current_app.logger.warning("LINE token loaded: %s", bool(token))
        current_app.logger.warning("LINE store target loaded: %s", bool(target_id))
        current_app.logger.warning("LINE target type: %s", target_type if target_id else "(missing)")
        current_app.logger.warning("LINE target id: %s", target_id or "(missing)")

        if not token or not target_id:
            current_app.logger.info("LINE notification skipped: missing token or target id.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "LINE_CHANNEL_ACCESS_TOKEN and LINE_USER_ID or LINE_GROUP_ID are required.",
            }

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
        request = Request(
            cls.PUSH_MESSAGE_URL,
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
                print(f"LINE API HTTP Status Code: {response.status}")
                print(f"LINE API Response Body: {response_body}")
                current_app.logger.warning("LINE API HTTP Status Code: %s", response.status)
                current_app.logger.warning("LINE API Response Body: %s", response_body)
                return {
                    "ok": 200 <= response.status < 300,
                    "status_code": response.status,
                    "response_body": response_body,
                    "error": None,
                }
        except HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            print(f"LINE API HTTP Status Code: {exc.code}")
            print(f"LINE API Response Body: {error_body}")
            current_app.logger.exception(
                "LINE push message failed. status=%s body=%s",
                exc.code,
                error_body,
            )
            return {
                "ok": False,
                "status_code": exc.code,
                "response_body": error_body,
                "error": str(exc),
            }
        except URLError:
            print("LINE API Error: network error.")
            current_app.logger.exception("LINE push message failed: network error.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "network error",
            }
        except Exception:
            print("LINE API Error: unexpected error.")
            current_app.logger.exception("LINE push message failed: unexpected error.")
            return {
                "ok": False,
                "status_code": None,
                "response_body": "",
                "error": "unexpected error",
            }
