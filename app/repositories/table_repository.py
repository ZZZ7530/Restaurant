from app.repositories.db import get_cursor


class TableRepository:
    @staticmethod
    def list_active():
        sql = """
            SELECT id, table_number, display_name, floor, is_active
            FROM restaurant_tables
            WHERE is_active = 1
            ORDER BY
                CASE floor WHEN '一樓' THEN 1 WHEN '二樓' THEN 2 ELSE 9 END,
                FIELD(table_number, '1', '2', '3', '5', '6', '27', '23', '22', '21', '20', '28', '26', '25', '01', '02', '03', '05', '06', '07', '08'),
                table_number
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def get_active_by_number(table_number):
        sql = """
            SELECT id, table_number, display_name, floor, is_active
            FROM restaurant_tables
            WHERE table_number = %s AND is_active = 1
            LIMIT 1
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (str(table_number),))
            return cursor.fetchone()
