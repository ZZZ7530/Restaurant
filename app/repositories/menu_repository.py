from app.repositories.db import get_cursor


class MenuRepository:
    @staticmethod
    def list_all_categories():
        sql = """
            SELECT id, name, description, sort_order, is_active
            FROM menu_categories
            ORDER BY sort_order, id
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def get_category_by_name(name):
        sql = "SELECT id, name FROM menu_categories WHERE name = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (name,))
            return cursor.fetchone()

    @staticmethod
    def create_category(name, description=None, sort_order=0):
        sql = """
            INSERT INTO menu_categories (name, description, sort_order)
            VALUES (%s, %s, %s)
        """
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (name, description, sort_order))
            return cursor.lastrowid

    @staticmethod
    def list_public_categories():
        sql = """
            SELECT id, name, description
            FROM menu_categories
            WHERE is_active = 1
            ORDER BY sort_order, id
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def list_public_items():
        sql = """
            SELECT id, category_id, name, description, price, image_url, is_featured
            FROM menu_items
            WHERE is_available = 1
            ORDER BY sort_order, id
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def list_featured_items(limit=4):
        sql = """
            SELECT id, name, description, price, image_url
            FROM menu_items
            WHERE is_available = 1 AND is_featured = 1
            ORDER BY sort_order, id
            LIMIT %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (limit,))
            return cursor.fetchall()

    @staticmethod
    def list_admin_items():
        sql = """
            SELECT
                mi.id, mi.category_id, mi.name, mi.description, mi.price,
                mi.image_url, mi.is_available, mi.is_featured, mi.sort_order,
                mc.name AS category_name
            FROM menu_items mi
            LEFT JOIN menu_categories mc ON mc.id = mi.category_id
            ORDER BY mc.sort_order, mi.sort_order, mi.id
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def get_item_by_id(item_id):
        sql = """
            SELECT
                id, category_id, name, description, price, image_url,
                is_available, is_featured, sort_order
            FROM menu_items
            WHERE id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (item_id,))
            return cursor.fetchone()

    @staticmethod
    def get_item_by_name(name):
        sql = """
            SELECT id, category_id, name, description, price, image_url
            FROM menu_items
            WHERE name = %s
            ORDER BY id
            LIMIT 1
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (name,))
            return cursor.fetchone()

    @staticmethod
    def create_item(data):
        sql = """
            INSERT INTO menu_items (
                category_id, name, description, price, image_url,
                is_available, is_featured, sort_order
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            data["category_id"],
            data["name"],
            data.get("description"),
            data["price"],
            data.get("image_url"),
            data["is_available"],
            data["is_featured"],
            data["sort_order"],
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, values)
            return cursor.lastrowid

    @staticmethod
    def update_item(item_id, data):
        sql = """
            UPDATE menu_items
            SET
                category_id = %s,
                name = %s,
                description = %s,
                price = %s,
                image_url = %s,
                is_available = %s,
                is_featured = %s,
                sort_order = %s
            WHERE id = %s
        """
        values = (
            data["category_id"],
            data["name"],
            data.get("description"),
            data["price"],
            data.get("image_url"),
            data["is_available"],
            data["is_featured"],
            data["sort_order"],
            item_id,
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, values)

    @staticmethod
    def delete_item(item_id):
        sql = "DELETE FROM menu_items WHERE id = %s"
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (item_id,))
