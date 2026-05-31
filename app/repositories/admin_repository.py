from app.repositories.db import get_cursor


class AdminRepository:
    @staticmethod
    def find_by_username(username):
        sql = """
            SELECT id, username, password_hash, display_name, role, is_active
            FROM admin_users
            WHERE username = %s
            LIMIT 1
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (username,))
            return cursor.fetchone()
