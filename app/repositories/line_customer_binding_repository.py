from app.repositories.db import get_cursor


class LineCustomerBindingRepository:
    @staticmethod
    def upsert(customer_phone, line_user_id, display_name=None):
        sql = """
            INSERT INTO line_customer_bindings (
                customer_phone, line_user_id, display_name, is_active, last_interaction_at
            )
            VALUES (%s, %s, %s, 1, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                customer_phone = VALUES(customer_phone),
                line_user_id = VALUES(line_user_id),
                display_name = VALUES(display_name),
                is_active = 1,
                last_interaction_at = CURRENT_TIMESTAMP
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (customer_phone, line_user_id, display_name))

    @staticmethod
    def find_active_by_phone(customer_phone):
        sql = """
            SELECT id, customer_phone, line_user_id, display_name, is_active
            FROM line_customer_bindings
            WHERE customer_phone = %s AND is_active = 1
            ORDER BY updated_at DESC
            LIMIT 1
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (customer_phone,))
            return cursor.fetchone()
