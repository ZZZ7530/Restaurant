from app.repositories.daily_price_repository import DailyPriceRepository


class DailyPriceService:
    @staticmethod
    def list_prices():
        return DailyPriceRepository.list_all()

    @staticmethod
    def list_active_price_mapping():
        return {
            row["item_name"]: row["price_text"]
            for row in DailyPriceRepository.list_active()
        }

    @staticmethod
    def get_price(price_id):
        return DailyPriceRepository.get_by_id(price_id)

    @staticmethod
    def _normalize_form_data(form_data):
        item_name = form_data.get("item_name", "").strip()
        price_text = form_data.get("price_text", "").strip()
        if not item_name:
            raise ValueError("菜名為必填")
        if not price_text:
            raise ValueError("今日價格為必填")

        return {
            "item_name": item_name,
            "price_text": price_text,
            "is_active": 1 if form_data.get("is_active") == "1" else 0,
        }

    @classmethod
    def create_price(cls, form_data):
        data = cls._normalize_form_data(form_data)
        price_id = DailyPriceRepository.create(data)
        return {"id": price_id, **data}

    @classmethod
    def update_price(cls, price_id, form_data):
        data = cls._normalize_form_data(form_data)
        DailyPriceRepository.update(price_id, data)
        return {"id": price_id, **data}

    @staticmethod
    def delete_price(price_id):
        DailyPriceRepository.delete(price_id)
