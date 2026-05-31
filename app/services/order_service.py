from datetime import datetime
from decimal import Decimal

from app.services.menu_service import MenuService
from app.services.line_service import LineService
from app.services.table_service import TableService
from app.repositories.order_repository import OrderRepository


class OrderService:
    STATUSES = ("pending", "preparing", "completed", "cancelled")

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
            raise ValueError("請先選擇至少一項餐點。")

        now = datetime.now()
        table_number = str(payload.get("table_number", "")).strip()
        if order_type == "dine_in":
            if not table_number:
                raise ValueError("缺少桌號。")
            payload = {
                **payload,
                "customer_name": f"桌號 {table_number}",
                "customer_phone": "",
                "pickup_date": now.strftime("%Y-%m-%d"),
                "pickup_time": now.strftime("%H:%M"),
            }
        else:
            required_fields = ("customer_name", "customer_phone", "pickup_date", "pickup_time")
            missing = [field for field in required_fields if not str(payload.get(field, "")).strip()]
            if missing:
                raise ValueError(f"缺少必要欄位：{', '.join(missing)}")

        normalized_items = []
        subtotal = Decimal("0")
        for item in items:
            quantity = int(item["quantity"])
            if quantity <= 0:
                raise ValueError("餐點數量必須大於 0")
            is_market_price = bool(item.get("is_market_price"))
            unit_price = Decimal("0") if is_market_price else Decimal(str(item["unit_price"]))
            line_total = unit_price * quantity
            subtotal += line_total
            item_name = item["item_name"]
            specification = (item.get("specification") or "").strip() or None
            menu_item_id = item.get("menu_item_id")
            if not menu_item_id:
                menu_item_id = MenuService.ensure_takeout_item(
                    item_name,
                    image_filename=item.get("image_filename"),
                    unit_price=unit_price,
                )
            normalized_items.append(
                {
                    "menu_item_id": menu_item_id,
                    "item_name": item_name,
                    "specification": specification,
                    "item_status": "pending",
                    "unit_price": unit_price,
                    "quantity": quantity,
                    "line_total": line_total,
                    "note": "時價餐點，金額需店家確認" if is_market_price else item.get("note"),
                }
            )

        order_data = {
            "order_no": datetime.now().strftime(("DI" if order_type == "dine_in" else "TO") + "%Y%m%d%H%M%S%f"),
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
            table = TableService.get_active_table(table_number)
            order["table_display_name"] = (table or {}).get("display_name") or table_number
            LineService.notify_new_dine_in_order(order)
        else:
            LineService.notify_new_takeout_order(order)

        return order

    @staticmethod
    def _build_takeout_note(payload):
        note = (payload.get("note") or "").strip()
        if payload.get("has_market_price_item"):
            suffix = "含時價餐點，總金額需店家確認。"
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
            raise ValueError(f"缺少必要欄位：{', '.join(missing)}")

        try:
            data["total_amount"] = Decimal(data["total_amount"])
        except Exception as exc:
            raise ValueError("總金額必須是有效數字") from exc

        if data["total_amount"] < 0:
            raise ValueError("總金額不可小於 0")

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
            raise ValueError("找不到此餐點明細")

        OrderRepository.update_order_item_status(item_id, "completed")
        cls._sync_order_status_from_items(order_id)
        return order_id

    @classmethod
    def undo_order_item_completed(cls, item_id):
        order_id = OrderRepository.get_order_id_by_item_id(item_id)
        if not order_id:
            raise ValueError("找不到此餐點明細")

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
