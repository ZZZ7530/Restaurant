from app.repositories.db import get_cursor


class OrderRepository:
    _ITEMS_SUMMARY_SQL = """
        SELECT
            order_id,
            GROUP_CONCAT(
                CONCAT(
                    item_name,
                    IF(specification IS NULL OR specification = '', '', CONCAT('（', specification, '）')),
                    ' x',
                    quantity
                )
                ORDER BY id
                SEPARATOR '、'
            ) AS items_summary
        FROM order_items
        GROUP BY order_id
    """

    _STATUS_COMPLETED_AT_SQL = """
        completed_at = CASE
            WHEN %s = 'completed' AND status <> 'completed' THEN CURRENT_TIMESTAMP
            WHEN %s = 'completed' AND status = 'completed' THEN completed_at
            ELSE NULL
        END
    """

    @staticmethod
    def list_all():
        sql = f"""
            SELECT
                o.id, o.order_no, o.customer_name, o.customer_phone, o.pickup_date,
                o.pickup_time, o.order_type, o.table_number, o.total_amount, o.status, o.note,
                o.completed_at, o.created_at,
                rt.display_name AS table_display_name,
                rt.floor AS table_floor,
                item_summary.items_summary
            FROM orders o
            LEFT JOIN restaurant_tables rt ON rt.table_number = o.table_number
            LEFT JOIN ({OrderRepository._ITEMS_SUMMARY_SQL}) item_summary
                ON item_summary.order_id = o.id
            ORDER BY o.pickup_date DESC, o.pickup_time DESC, o.created_at DESC
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def list_by_type(order_type):
        sql = f"""
            SELECT
                o.id, o.order_no, o.customer_name, o.customer_phone, o.pickup_date,
                o.pickup_time, o.order_type, o.table_number, o.total_amount, o.status, o.note,
                o.completed_at, o.created_at,
                rt.display_name AS table_display_name,
                rt.floor AS table_floor,
                item_summary.items_summary
            FROM orders o
            LEFT JOIN restaurant_tables rt ON rt.table_number = o.table_number
            LEFT JOIN ({OrderRepository._ITEMS_SUMMARY_SQL}) item_summary
                ON item_summary.order_id = o.id
            WHERE o.order_type = %s
            ORDER BY o.created_at DESC, o.pickup_date DESC, o.pickup_time DESC
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (order_type,))
            return cursor.fetchall()

    @staticmethod
    def get_by_id(order_id):
        sql = """
            SELECT
                o.id, o.order_no, o.customer_name, o.customer_phone, o.pickup_date,
                o.pickup_time, o.order_type, o.table_number, o.subtotal, o.total_amount,
                o.payment_method, o.status, o.note, o.completed_at, o.created_at,
                rt.display_name AS table_display_name,
                rt.floor AS table_floor
            FROM orders o
            LEFT JOIN restaurant_tables rt ON rt.table_number = o.table_number
            WHERE o.id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (order_id,))
            return cursor.fetchone()

    @staticmethod
    def list_items(order_id):
        sql = """
            SELECT
                id, item_name, specification, unit_price, quantity,
                line_total, note, item_status
            FROM order_items
            WHERE order_id = %s
            ORDER BY id
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (order_id,))
            return cursor.fetchall()

    @staticmethod
    def create_order(order_data, items):
        order_sql = """
            INSERT INTO orders (
                order_no, customer_name, customer_phone, order_type, table_number, pickup_date,
                pickup_time, subtotal, total_amount, note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        item_sql = """
            INSERT INTO order_items (
                order_id, menu_item_id, item_name, specification, item_status, unit_price,
                quantity, line_total, note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(
                order_sql,
                (
                    order_data["order_no"],
                    order_data["customer_name"],
                    order_data["customer_phone"],
                    order_data.get("order_type", "takeout"),
                    order_data.get("table_number"),
                    order_data["pickup_date"],
                    order_data["pickup_time"],
                    order_data["subtotal"],
                    order_data["total_amount"],
                    order_data.get("note"),
                ),
            )
            order_id = cursor.lastrowid
            for item in items:
                cursor.execute(
                    item_sql,
                    (
                        order_id,
                        item["menu_item_id"],
                        item["item_name"],
                        item.get("specification"),
                        item.get("item_status", "pending"),
                        item["unit_price"],
                        item["quantity"],
                        item["line_total"],
                        item.get("note"),
                    ),
                )
            return order_id

    @staticmethod
    def create_admin_order(order_data):
        sql = """
            INSERT INTO orders (
                order_no, customer_name, customer_phone, pickup_date,
                pickup_time, subtotal, total_amount, status, completed_at, note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                CASE WHEN %s = 'completed' THEN CURRENT_TIMESTAMP ELSE NULL END,
                %s
            )
        """
        total_amount = order_data["total_amount"]
        values = (
            order_data["order_no"],
            order_data["customer_name"],
            order_data["customer_phone"],
            order_data["pickup_date"],
            order_data["pickup_time"],
            total_amount,
            total_amount,
            order_data["status"],
            order_data["status"],
            order_data.get("note"),
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, values)
            return cursor.lastrowid

    @classmethod
    def update(cls, order_id, order_data):
        sql = f"""
            UPDATE orders
            SET
                customer_name = %s,
                customer_phone = %s,
                pickup_date = %s,
                pickup_time = %s,
                subtotal = %s,
                total_amount = %s,
                status = %s,
                {cls._STATUS_COMPLETED_AT_SQL},
                note = %s
            WHERE id = %s
        """
        total_amount = order_data["total_amount"]
        values = (
            order_data["customer_name"],
            order_data["customer_phone"],
            order_data["pickup_date"],
            order_data["pickup_time"],
            total_amount,
            total_amount,
            order_data["status"],
            order_data["status"],
            order_data["status"],
            order_data.get("note"),
            order_id,
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, values)

    @staticmethod
    def delete(order_id):
        sql = "DELETE FROM orders WHERE id = %s"
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (order_id,))

    @staticmethod
    def list_kitchen_orders():
        orders_sql = """
            SELECT
                o.id, o.order_no, o.order_type, o.customer_name, o.customer_phone,
                o.table_number, o.pickup_date, o.pickup_time, o.subtotal, o.total_amount,
                o.status, o.note, o.completed_at, o.created_at,
                rt.display_name AS table_display_name,
                rt.floor AS table_floor
            FROM orders o
            LEFT JOIN restaurant_tables rt ON rt.table_number = o.table_number
            WHERE o.status NOT IN ('completed', 'cancelled')
            ORDER BY
                CASE o.status
                    WHEN 'pending' THEN 1
                    WHEN 'accepted' THEN 2
                    WHEN 'preparing' THEN 3
                    WHEN 'ready' THEN 4
                    WHEN 'completed' THEN 5
                    ELSE 6
                END,
                o.pickup_date ASC,
                o.pickup_time ASC,
                o.created_at ASC
        """
        items_sql = """
            SELECT
                id, order_id, item_name, specification, quantity,
                unit_price, line_total, note, item_status
            FROM order_items
            WHERE order_id IN ({placeholders})
            ORDER BY id
        """
        with get_cursor() as cursor:
            cursor.execute(orders_sql)
            orders = cursor.fetchall()
            if not orders:
                return []

            order_ids = [order["id"] for order in orders]
            placeholders = ", ".join(["%s"] * len(order_ids))
            cursor.execute(items_sql.format(placeholders=placeholders), order_ids)
            items = cursor.fetchall()

        items_by_order = {}
        for item in items:
            items_by_order.setdefault(item["order_id"], []).append(item)

        for order in orders:
            order_items = items_by_order.get(order["id"], [])
            order["items"] = order_items
            order["all_items_completed"] = bool(order_items) and all(
                item["item_status"] == "completed" for item in order_items
            )
        return orders

    @staticmethod
    def list_completed_orders():
        orders_sql = """
            SELECT
                o.id, o.order_no, o.order_type, o.customer_name, o.customer_phone,
                o.table_number, o.pickup_date, o.pickup_time, o.subtotal, o.total_amount,
                o.status, o.note, o.completed_at, o.created_at,
                rt.display_name AS table_display_name,
                rt.floor AS table_floor
            FROM orders o
            LEFT JOIN restaurant_tables rt ON rt.table_number = o.table_number
            WHERE o.status = 'completed'
            ORDER BY
                o.completed_at DESC,
                o.created_at DESC
        """
        items_sql = """
            SELECT
                id, order_id, item_name, specification, quantity,
                unit_price, line_total, note, item_status
            FROM order_items
            WHERE order_id IN ({placeholders})
            ORDER BY id
        """
        with get_cursor() as cursor:
            cursor.execute(orders_sql)
            orders = cursor.fetchall()
            if not orders:
                return []

            order_ids = [order["id"] for order in orders]
            placeholders = ", ".join(["%s"] * len(order_ids))
            cursor.execute(items_sql.format(placeholders=placeholders), order_ids)
            items = cursor.fetchall()

        items_by_order = {}
        for item in items:
            items_by_order.setdefault(item["order_id"], []).append(item)

        for order in orders:
            order["items"] = items_by_order.get(order["id"], [])
        return orders

    @staticmethod
    def update_order_item_status(item_id, item_status):
        sql = "UPDATE order_items SET item_status = %s WHERE id = %s"
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (item_status, item_id))

    @staticmethod
    def get_order_id_by_item_id(item_id):
        sql = "SELECT order_id FROM order_items WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (item_id,))
            row = cursor.fetchone()
            return row["order_id"] if row else None

    @staticmethod
    def get_order_item_completion_counts(order_id):
        sql = """
            SELECT
                COUNT(*) AS total_count,
                COALESCE(SUM(CASE WHEN item_status = 'completed' THEN 1 ELSE 0 END), 0)
                    AS completed_count
            FROM order_items
            WHERE order_id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (order_id,))
            return cursor.fetchone()

    @classmethod
    def update_order_status(cls, order_id, status):
        sql = f"""
            UPDATE orders
            SET
                status = %s,
                {cls._STATUS_COMPLETED_AT_SQL}
            WHERE id = %s
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (status, status, status, order_id))

    @staticmethod
    def mark_order_completed(order_id):
        sql = """
            UPDATE orders
            SET status = 'completed', completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
            WHERE id = %s
        """
        item_sql = """
            UPDATE order_items
            SET item_status = 'completed'
            WHERE order_id = %s
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (order_id,))
            cursor.execute(item_sql, (order_id,))

    @staticmethod
    def mark_order_preparing(order_id):
        sql = """
            UPDATE orders
            SET status = 'preparing', completed_at = NULL
            WHERE id = %s
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (order_id,))
