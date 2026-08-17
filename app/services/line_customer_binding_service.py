import re

from app.repositories.line_customer_binding_repository import LineCustomerBindingRepository


class LineCustomerBindingService:
    BIND_PREFIX = "綁定"
    PHONE_PATTERN = re.compile(r"^09\d{8}$")

    @classmethod
    def bind_from_message_event(cls, event):
        source = event.get("source") or {}
        line_user_id = str(source.get("userId") or "").strip()
        message = event.get("message") or {}
        text = str(message.get("text") or "").strip()

        if not line_user_id:
            return {
                "handled": False,
                "reply_text": "無法取得 LINE 使用者資訊，請使用一對一聊天室重新綁定。",
            }

        if not text.startswith(cls.BIND_PREFIX):
            return {"handled": False, "reply_text": None}

        customer_phone = cls._extract_phone(text)
        if not customer_phone:
            return {
                "handled": True,
                "reply_text": "綁定格式不正確，請輸入：綁定 09xxxxxxxx",
            }

        LineCustomerBindingRepository.upsert(
            customer_phone=customer_phone,
            line_user_id=line_user_id,
            display_name=None,
        )
        return {
            "handled": True,
            "reply_text": f"綁定成功，之後使用 {customer_phone} 訂位或外帶時會收到 LINE 通知。",
        }

    @classmethod
    def find_active_user_id_by_phone(cls, customer_phone):
        normalized_phone = cls.normalize_phone(customer_phone)
        if not normalized_phone:
            return None

        binding = LineCustomerBindingRepository.find_active_by_phone(normalized_phone)
        if not binding:
            return None
        return binding.get("line_user_id")

    @classmethod
    def _extract_phone(cls, text):
        phone_text = text[len(cls.BIND_PREFIX):].strip()
        return cls.normalize_phone(phone_text)

    @classmethod
    def normalize_phone(cls, phone):
        normalized = re.sub(r"[\s\-()]+", "", str(phone or "").strip())
        return normalized if cls.PHONE_PATTERN.fullmatch(normalized) else None
