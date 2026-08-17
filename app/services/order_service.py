from datetime import datetime
from decimal import Decimal

from flask import current_app

from app.repositories.order_repository import OrderRepository
from app.services.line_service import LineService
from app.services.menu_service import MenuService
from app.services.table_service import TableService


class OrderService:
    STATUSES = ("pending", "preparing", "completed", "cancelled")
    MAX_ITEM_QUANTITY = 99

    @classmethod
    def create_order(cls, payload):
        return cls._create_customer_order(payload, order_type="takeout")

    @classmethod
    def create_dine_in_order(cls, payload):
        return cls._create_customer_order(payload, order_type="dine_in")

    @classmethod
    def _create_customer_order(cls, payload, order_type="takeout"):
        items = payload.get("items", [])
        if not items:
            raise ValueError("請至少選擇一項餐點")

        now = datetime.now()
        table_number = str(payload.get("table_number", "")).strip()
        if order_type == "dine_in":
            if not table_number:
                raise ValueError("請提供桌號")
            table = TableService.get_active_table(table_number)
            if not table:
                raise ValueError("桌號不存在或尚未啟用")
            payload = {
                **payload,
                "customer_name": f"桌號 {table_number}",
                "customer_phone": "",
                "pickup_date": now.strftime("%Y-%m-%d"),
                "pickup_time": now.strftime("%H:%M"),
            }
        else:
            required_fields = ("customer_name", "customer_phone", "pickup_date", "pickup_time")
            missing = [
                field for field in required_fields if not str(payload.get(field, "")).strip()
            ]
            if missing:
                raise ValueError(f"請填寫必要欄位：{', '.join(missing)}")

        normalized_items = []
        subtotal = Decimal("0")
        menu_items = cls._get_orderable_menu_item_map()
        for item in items:
            menu_item = cls._get_orderable_menu_item(menu_items, item)
            quantity = cls._normalize_item_quantity(item)
            specification = cls._normalize_item_specification(menu_item, item)
            is_market_price = bool(menu_item.get("is_market_price"))
            unit_price = cls._resolve_unit_price(menu_item, specification)
            line_total = unit_price * quantity
            subtotal += line_total
            note = item.get("note")
            if is_market_price:
                note = "時價餐點，需由店家確認價格"
            normalized_items.append(
                {
                    "menu_item_id": menu_item["menu_item_id"],
                    "item_name": menu_item["name"],
                    "specification": specification,
                    "item_status": "pending",
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "line_total": line_total,
                    "note": note,
                }
            )

        order_data = {
            "order_no": datetime.now().strftime(
                ("DI" if order_type == "dine_in" else "TO") + "%Y%m%d%H%M%S%f"
            ),
            "order_type": order_type,
            "table_number": table_number if order_type == "dine_in" else None,
            "customer_name": payload["customer_name"],
            "customer_phone": payload["customer_phone"],
            "pickup_date": payload["pickup_date"],
            "pickup_time": payload["pickup_time"],
            "subtotal": subtotal,
            "total_amount": subtotal,
            "note": cls._build_takeout_note(payload),
        }
        order_id = OrderRepository.create_order(order_data, normalized_items)

        response_items = [
            {
                **item,
                "unit_price": float(item["unit_price"]),
                "line_total": float(item["line_total"]),
            }
            for item in normalized_items
        ]
        response_order = {
            **order_data,
            "subtotal": float(order_data["subtotal"]),
            "total_amount": float(order_data["total_amount"]),
        }
        order = {"id": order_id, **response_order, "items": response_items}
        if order_type == "dine_in":
            order["table_display_name"] = (table or {}).get("display_name") or table_number
            LineService.notify_new_dine_in_order(order)
        else:
            LineService.notify_new_takeout_order(order)
            try:
                LineService.notify_customer_takeout_order_success(order)
            except Exception:
                current_app.logger.exception(
                    "LINE customer takeout notification failed without blocking request."
                )

        return order

    @staticmethod
    def _get_orderable_menu_item_map():
        return {
            int(item["menu_item_id"]): item
            for item in MenuService.list_ai_recommendable_items()
            if item.get("menu_item_id") and item.get("name")
        }

    @staticmethod
    def _get_orderable_menu_item(menu_items, item):
        raw_menu_item_id = item.get("menu_item_id")
        if isinstance(raw_menu_item_id, bool):
            raise ValueError("餐點資料不正確")

        try:
            menu_item_id = int(raw_menu_item_id)
        except (TypeError, ValueError) as exc:
            raise ValueError("餐點資料不正確") from exc

        menu_item = menu_items.get(menu_item_id)
        if not menu_item:
            raise ValueError("餐點不存在或目前未開放點餐")
        return menu_item

    @classmethod
    def _normalize_item_quantity(cls, item):
        raw_quantity = item.get("quantity")
        if isinstance(raw_quantity, bool):
            raise ValueError("餐點數量格式不正確")

        try:
            quantity = int(raw_quantity)
        except (TypeError, ValueError) as exc:
            raise ValueError("餐點數量格式不正確") from exc

        if quantity <= 0:
            raise ValueError("餐點數量必須大於 0")
        if quantity > cls.MAX_ITEM_QUANTITY:
            raise ValueError(f"單項餐點數量不可超過 {cls.MAX_ITEM_QUANTITY}")
        return quantity

    @staticmethod
    def _normalize_item_specification(menu_item, item):
        specification = (item.get("specification") or "").strip()
        price_options = menu_item.get("price_options") or []

        if not price_options:
            if specification:
                raise ValueError("餐點規格不正確")
            return specification or None

        valid_specifications = {
            str(option.get("specification", "")).strip()
            for option in price_options
            if str(option.get("specification", "")).strip()
        }
        if specification not in valid_specifications:
            raise ValueError("餐點規格不正確")
        return specification

    @staticmethod
    def _resolve_unit_price(menu_item, specification=None):
        if menu_item.get("is_market_price"):
            return Decimal("0")

        for option in menu_item.get("price_options") or []:
            if str(option.get("specification", "")).strip() == specification:
                return Decimal(str(option.get("price") or 0))

        return Decimal(str(menu_item.get("price") or 0))

    @staticmethod
    def _build_takeout_note(payload):
        note = (payload.get("note") or "").strip()
        if payload.get("has_market_price_item"):
            suffix = "包含時價餐點，實際金額需由店家確認"
            return f"{note}\n{suffix}" if note else suffix
        return note or None

    @staticmethod
    def list_orders():
        return OrderRepository.list_all()

    @staticmethod
    def list_takeout_orders():
        return OrderRepository.list_by_type("takeout")

    @staticmethod
    def list_dine_in_orders():
        return OrderRepository.list_by_type("dine_in")

    @staticmethod
    def list_kitchen_orders():
        return OrderRepository.list_kitchen_orders()

    @staticmethod
    def list_completed_orders():
        return OrderRepository.list_completed_orders()

    @staticmethod
    def get_order(order_id):
        order = OrderRepository.get_by_id(order_id)
        if order:
            order["items"] = OrderRepository.list_items(order_id)
        return order

    @classmethod
    def _normalize_admin_form_data(cls, form_data):
        required_fields = (
            "customer_name",
            "customer_phone",
            "pickup_date",
            "pickup_time",
            "total_amount",
        )
        data = {field: form_data.get(field, "").strip() for field in required_fields}
        missing = [field for field, value in data.items() if not value]
        if missing:
            raise ValueError(f"請填寫必要欄位：{', '.join(missing)}")

        try:
            data["total_amount"] = Decimal(data["total_amount"])
        except Exception as exc:
            raise ValueError("訂單金額格式不正確") from exc

        if data["total_amount"] < 0:
            raise ValueError("訂單金額不可小於 0")

        status = form_data.get("status", "pending").strip() or "pending"
        if status not in cls.STATUSES:
            raise ValueError("訂單狀態不正確")

        data["status"] = status
        data["note"] = form_data.get("note", "").strip() or None
        return data

    @classmethod
    def create_admin_order(cls, form_data):
        data = cls._normalize_admin_form_data(form_data)
        data["order_no"] = datetime.now().strftime("ADM%Y%m%d%H%M%S%f")
        order_id = OrderRepository.create_admin_order(data)
        return {"id": order_id, **data}

    @classmethod
    def update_admin_order(cls, order_id, form_data):
        data = cls._normalize_admin_form_data(form_data)
        OrderRepository.update(order_id, data)
        return {"id": order_id, **data}

    @staticmethod
    def delete_order(order_id):
        OrderRepository.delete(order_id)

    @staticmethod
    def complete_order(order_id):
        OrderRepository.mark_order_completed(order_id)

    @classmethod
    def mark_order_item_completed(cls, item_id):
        order_id = OrderRepository.get_order_id_by_item_id(item_id)
        if not order_id:
            raise ValueError("找不到此餐點所屬訂單")

        OrderRepository.update_order_item_status(item_id, "completed")
        cls._sync_order_status_from_items(order_id)
        return order_id

    @classmethod
    def undo_order_item_completed(cls, item_id):
        order_id = OrderRepository.get_order_id_by_item_id(item_id)
        if not order_id:
            raise ValueError("找不到此餐點所屬訂單")

        OrderRepository.update_order_item_status(item_id, "pending")
        OrderRepository.mark_order_preparing(order_id)
        return order_id

    @staticmethod
    def _sync_order_status_from_items(order_id):
        counts = OrderRepository.get_order_item_completion_counts(order_id)
        if not counts or not counts["total_count"]:
            return

        if counts["completed_count"] == counts["total_count"]:
            OrderRepository.mark_order_completed(order_id)
        else:
            OrderRepository.mark_order_preparing(order_id)
