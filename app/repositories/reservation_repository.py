from app.repositories.db import get_cursor


class ReservationRepository:
    @staticmethod
    def create(data):
        sql = """
            INSERT INTO reservations (
                customer_name, customer_phone, reservation_date,
                reservation_time, party_size, note
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            data["customer_name"],
            data["customer_phone"],
            data["reservation_date"],
            data["reservation_time"],
            data["party_size"],
            data.get("note"),
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, values)
            return cursor.lastrowid

    @staticmethod
    def list_all():
        sql = """
            SELECT
                id, customer_name, customer_phone, reservation_date,
                reservation_time, party_size, note, status, created_at
            FROM reservations
            ORDER BY reservation_date DESC, reservation_time DESC, created_at DESC
        """
        with get_cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @staticmethod
    def get_by_id(reservation_id):
        sql = """
            SELECT
                id, customer_name, customer_phone, reservation_date,
                reservation_time, party_size, note, status, created_at
            FROM reservations
            WHERE id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (reservation_id,))
            return cursor.fetchone()

    @staticmethod
    def update(reservation_id, data):
        sql = """
            UPDATE reservations
            SET
                customer_name = %s,
                customer_phone = %s,
                reservation_date = %s,
                reservation_time = %s,
                party_size = %s,
                note = %s,
                status = %s
            WHERE id = %s
        """
        values = (
            data["customer_name"],
            data["customer_phone"],
            data["reservation_date"],
            data["reservation_time"],
            data["party_size"],
            data.get("note"),
            data["status"],
            reservation_id,
        )
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, values)

    @staticmethod
    def delete(reservation_id):
        sql = "DELETE FROM reservations WHERE id = %s"
        with get_cursor(commit=True) as cursor:
            cursor.execute(sql, (reservation_id,))
