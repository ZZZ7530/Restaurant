from app.repositories.db import get_cursor


class RevenueRepository:
    COMPLETED_DATE_EXPR = "DATE(COALESCE(completed_at, created_at))"
    ORDER_COMPLETED_DATE_EXPR = "DATE(COALESCE(o.completed_at, o.created_at))"

    @classmethod
    def get_summary(cls, start_date, end_date):
        sql = f"""
            SELECT
                COALESCE(SUM(total_amount), 0) AS total_revenue,
                COUNT(*) AS completed_order_count,
                COALESCE(SUM(CASE WHEN order_type = 'dine_in' THEN total_amount ELSE 0 END), 0)
                    AS dine_in_revenue,
                COALESCE(SUM(CASE WHEN order_type = 'takeout' THEN total_amount ELSE 0 END), 0)
                    AS takeout_revenue
            FROM orders
            WHERE status = 'completed'
                AND {cls.COMPLETED_DATE_EXPR} BETWEEN %s AND %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (start_date, end_date))
            return cursor.fetchone()

    @classmethod
    def get_daily_revenue(cls, start_date, end_date):
        sql = f"""
            SELECT
                {cls.COMPLETED_DATE_EXPR} AS revenue_date,
                COUNT(*) AS completed_order_count,
                COALESCE(SUM(CASE WHEN order_type = 'dine_in' THEN total_amount ELSE 0 END), 0)
                    AS dine_in_revenue,
                COALESCE(SUM(CASE WHEN order_type = 'takeout' THEN total_amount ELSE 0 END), 0)
                    AS takeout_revenue,
                COALESCE(SUM(total_amount), 0) AS total_revenue
            FROM orders
            WHERE status = 'completed'
                AND {cls.COMPLETED_DATE_EXPR} BETWEEN %s AND %s
            GROUP BY revenue_date
            ORDER BY revenue_date ASC
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (start_date, end_date))
            return cursor.fetchall()

    @classmethod
    def get_top_items(cls, start_date, end_date, limit=5):
        sql = f"""
            SELECT
                oi.item_name,
                COALESCE(SUM(oi.quantity), 0) AS total_quantity,
                COALESCE(SUM(oi.line_total), 0) AS total_sales
            FROM orders o
            INNER JOIN order_items oi ON oi.order_id = o.id
            WHERE o.status = 'completed'
                AND {cls.ORDER_COMPLETED_DATE_EXPR} BETWEEN %s AND %s
            GROUP BY oi.item_name
            ORDER BY total_quantity DESC, total_sales DESC, oi.item_name ASC
            LIMIT %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (start_date, end_date, limit))
            return cursor.fetchall()
