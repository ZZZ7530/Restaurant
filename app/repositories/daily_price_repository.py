from app.repositories.db import get_cursor


class DailyPriceRepository:
    @staticmethod
    def list_all():
        sql = """
            SELECT id, item_name, price_text, is_active, updated_at
            FROM daily_menu_prices
            ORDER BY is_active DESC, item_name
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def list_active():
        sql = """
            SELECT item_name, price_text
            FROM daily_menu_prices
            WHERE is_active = 1
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def get_by_id(price_id):
        sql = """
            SELECT id, item_name, price_text, is_active, updated_at
            FROM daily_menu_prices
            WHERE id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (price_id,))
            return cursor.fetchone()

    @staticmethod
    def create(data):
        sql = """
            INSERT INTO daily_menu_prices (item_name, price_text, is_active)
            VALUES (%s, %s, %s)
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (data["item_name"], data["price_text"], data["is_active"]))
            return cursor.lastrowid

    @staticmethod
    def update(price_id, data):
        sql = """
            UPDATE daily_menu_prices
            SET item_name = %s, price_text = %s, is_active = %s
            WHERE id = %s
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (data["item_name"], data["price_text"], data["is_active"], price_id))

    @staticmethod
    def delete(price_id):
        sql = "DELETE FROM daily_menu_prices WHERE id = %s"
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (price_id,))
