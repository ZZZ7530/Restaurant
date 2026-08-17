import json
import re
from pathlib import Path

from flask import current_app

from app.repositories.menu_repository import MenuRepository
from app.services.daily_price_service import DailyPriceService


class MenuService:
    DEFAULT_CATEGORY_NAME = "未分類"
    PRICE_MAPPING_PATH = Path(__file__).resolve().parents[1] / "config" / "menu_price_mapping.json"
    MARKET_PRICE_LABEL = "時價"
    ASK_STORE_LABEL = "請洽店家"
    SPEC_PRICE_PATTERN = re.compile(r"^\s*([^\d/]+?)\s*(\d+)\s*(?:元)?\s*$")
    PRICE_MATCH_PREFIXES = (
        "菜單",
        "川燙",
        "三杯",
        "塔香",
        "涼拌",
        "清蒸",
        "紅燒",
        "綜合",
        "胡椒",
        "蒜泥",
        "蒜蓉",
        "蔥爆",
        "蠔油",
        "西瓜綿",
        "辣炒",
        "酸菜",
        "金莎",
        "香酥",
        "鮮魚",
        "龍蝦",
        "烤",
        "炒",
        "炸",
        "鹹酥",
        "麻油",
    )

    @staticmethod
    def list_menu_for_public():
        try:
            categories = MenuRepository.list_public_categories()
            items = MenuRepository.list_public_items()
        except Exception:
            return []

        price_mapping = MenuService.load_price_mapping()
        try:
            daily_price_mapping = DailyPriceService.list_active_price_mapping()
        except Exception:
            daily_price_mapping = {}

        normalized_items = []
        for item in items:
            normalized_items.append(
                MenuService.normalize_public_item(
                    item,
                    price_mapping=price_mapping,
                    daily_price_mapping=daily_price_mapping,
                )
            )

        items_by_category = {}
        for item in normalized_items:
            items_by_category.setdefault(item["category_id"], []).append(item)

        for category in categories:
            category["items"] = items_by_category.get(category["id"], [])

        return categories

    @classmethod
    def normalize_public_item(cls, item, price_mapping=None, daily_price_mapping=None):
        price_mapping = price_mapping if price_mapping is not None else cls.load_price_mapping()
        daily_price_mapping = daily_price_mapping or {}
        price_label = cls.get_price_label(item["name"], price_mapping, daily_price_mapping)
        mapped_price_value = cls.parse_price_value(price_label)
        price_options = cls.parse_price_options(price_label)
        has_mapped_price = price_label != cls.MARKET_PRICE_LABEL

        numeric_price = item.get("price") or 0
        if has_mapped_price:
            price_value = mapped_price_value if mapped_price_value is not None else numeric_price
            display_price_label = price_label
            takeout_price_label = cls.ASK_STORE_LABEL if mapped_price_value is None else price_label
            is_market_price = mapped_price_value is None
        else:
            price_value = numeric_price
            if numeric_price and numeric_price > 0:
                display_price_label = f"NT$ {numeric_price:.0f}"
                takeout_price_label = display_price_label
                is_market_price = False
            else:
                display_price_label = cls.MARKET_PRICE_LABEL
                takeout_price_label = cls.ASK_STORE_LABEL
                is_market_price = True

        image_url = item.get("image_url") or ""
        image_filename = None
        if image_url.startswith("images/background/"):
            image_filename = image_url.replace("images/background/", "", 1)

        return {
            **item,
            "price": price_value if price_value is not None else 0,
            "price_label": takeout_price_label,
            "display_price_label": display_price_label,
            "price_options": price_options,
            "has_price_options": len(price_options) > 1,
            "is_market_price": is_market_price,
            "image_filename": image_filename,
        }

    @classmethod
    def load_price_mapping(cls):
        if not cls.PRICE_MAPPING_PATH.exists():
            return {}

        try:
            with cls.PRICE_MAPPING_PATH.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (OSError, json.JSONDecodeError):
            current_app.logger.exception("Failed to load menu price mapping.")
            return {}

    @classmethod
    def normalize_price_name(cls, name):
        normalized = name.strip()
        if normalized.startswith("菜單-"):
            normalized = normalized.replace("菜單-", "", 1)

        for prefix in cls.PRICE_MATCH_PREFIXES:
            if normalized.startswith(prefix) and len(normalized) > len(prefix):
                return normalized[len(prefix):]

        return normalized

    @classmethod
    def get_price_label(cls, name, price_mapping, daily_price_mapping=None):
        daily_price_mapping = daily_price_mapping or {}
        normalized_name = cls.normalize_price_name(name)

        for mapping in (daily_price_mapping, price_mapping):
            if name in mapping:
                return mapping[name]
            if normalized_name in mapping:
                return mapping[normalized_name]

        return cls.MARKET_PRICE_LABEL

    @classmethod
    def parse_price_value(cls, price_label):
        if not price_label or price_label in {cls.MARKET_PRICE_LABEL, cls.ASK_STORE_LABEL}:
            return None

        match = re.search(r"\d+", str(price_label).replace(",", ""))
        if not match:
            return None

        return int(match.group())

    @classmethod
    def parse_price_options(cls, price_label):
        if not price_label or price_label in {cls.MARKET_PRICE_LABEL, cls.ASK_STORE_LABEL}:
            return []

        parts = [part.strip() for part in str(price_label).split("/") if part.strip()]
        if len(parts) <= 1:
            return []

        options = []
        for part in parts:
            match = cls.SPEC_PRICE_PATTERN.match(part)
            if not match:
                return []
            specification = match.group(1).strip()
            price = int(match.group(2))
            if not specification:
                return []
            options.append(
                {
                    "specification": specification,
                    "price": price,
                    "label": f"{specification} NT${price}",
                }
            )

        return options if len(options) > 1 else []

    @classmethod
    def list_synced_public_menu(cls):
        return cls.list_menu_for_public()

    @classmethod
    def list_ai_recommendable_items(cls):
        recommendable_items = []
        for category in cls.list_synced_public_menu():
            category_name = category.get("name") or ""
            for item in category.get("items", []):
                recommendable_items.append(
                    {
                        "menu_item_id": item.get("id"),
                        "name": item.get("name"),
                        "category_name": category_name,
                        "description": item.get("description"),
                        "price": item.get("price") or 0,
                        "display_price_label": item.get("display_price_label")
                        or item.get("price_label"),
                        "price_options": item.get("price_options") or [],
                        "is_market_price": bool(item.get("is_market_price")),
                        "image_filename": item.get("image_filename"),
                    }
                )
        return [
            item
            for item in recommendable_items
            if item["menu_item_id"] and item["name"]
        ]

    @staticmethod
    def list_featured_items():
        try:
            return MenuRepository.list_featured_items()
        except Exception:
            return []

    @staticmethod
    def list_admin_items():
        return MenuRepository.list_admin_items()

    @staticmethod
    def list_categories():
        return MenuRepository.list_all_categories()

    @staticmethod
    def get_item(item_id):
        return MenuRepository.get_item_by_id(item_id)

    @classmethod
    def ensure_default_category(cls):
        category = MenuRepository.get_category_by_name(cls.DEFAULT_CATEGORY_NAME)
        if category:
            return category["id"]
        return MenuRepository.create_category(cls.DEFAULT_CATEGORY_NAME, "後台新增菜色預設分類", 999)

    @classmethod
    def ensure_takeout_item(cls, name, image_filename=None, unit_price=0):
        item = MenuRepository.get_item_by_name(name)
        if item:
            return item["id"]

        data = {
            "category_id": cls.ensure_default_category(),
            "name": name,
            "description": None,
            "price": unit_price,
            "image_url": f"images/background/{image_filename}" if image_filename else None,
            "is_available": 1,
            "is_featured": 0,
            "sort_order": 999,
        }
        return MenuRepository.create_item(data)

    @classmethod
    def _normalize_admin_form_data(cls, form_data):
        name = form_data.get("name", "").strip()
        if not name:
            raise ValueError("菜名為必填")

        try:
            price = float(form_data.get("price", "").strip())
        except ValueError as exc:
            raise ValueError("價格必須是有效數字") from exc

        if price < 0:
            raise ValueError("價格不可小於 0")

        category_id = form_data.get("category_id", "").strip()
        if category_id:
            category_id = int(category_id)
        else:
            category_id = cls.ensure_default_category()

        sort_order = form_data.get("sort_order", "0").strip() or "0"
        data = {
            "category_id": category_id,
            "name": name,
            "description": form_data.get("description", "").strip() or None,
            "price": price,
            "image_url": form_data.get("image_url", "").strip() or None,
            "is_available": 1 if form_data.get("is_available") == "1" else 0,
            "is_featured": 1 if form_data.get("is_featured") == "1" else 0,
            "sort_order": int(sort_order),
        }
        return data

    @classmethod
    def create_item(cls, form_data):
        data = cls._normalize_admin_form_data(form_data)
        item_id = MenuRepository.create_item(data)
        return {"id": item_id, **data}

    @classmethod
    def update_item(cls, item_id, form_data):
        data = cls._normalize_admin_form_data(form_data)
        MenuRepository.update_item(item_id, data)
        return {"id": item_id, **data}

    @staticmethod
    def delete_item(item_id):
        MenuRepository.delete_item(item_id)
