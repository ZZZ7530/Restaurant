from calendar import monthrange
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.repositories.revenue_repository import RevenueRepository


class RevenueService:
    PRESETS = ("today", "week", "month", "last7", "last30", "custom")

    @classmethod
    def build_dashboard(cls, args):
        filters = cls._parse_filters(args)
        start_date = filters["start_date"]
        end_date = filters["end_date"]

        summary = cls._normalize_summary(
            RevenueRepository.get_summary(start_date, end_date)
        )
        month_start, month_end = cls._month_range(date.today())
        month_summary = cls._normalize_summary(
            RevenueRepository.get_summary(month_start, month_end)
        )

        daily_rows = cls._fill_daily_rows(
            start_date,
            end_date,
            RevenueRepository.get_daily_revenue(start_date, end_date),
        )
        daily_detail_rows = list(reversed(daily_rows))
        top_items = cls._normalize_top_items(
            RevenueRepository.get_top_items(start_date, end_date, limit=5)
        )

        total_revenue = summary["total_revenue"]
        completed_order_count = summary["completed_order_count"]
        average_order_value = (
            total_revenue / completed_order_count
            if completed_order_count
            else Decimal("0")
        )
        dine_in_revenue = summary["dine_in_revenue"]
        takeout_revenue = summary["takeout_revenue"]

        return {
            "filters": filters,
            "summary": {
                "total_revenue": total_revenue,
                "completed_order_count": completed_order_count,
                "average_order_value": average_order_value,
                "month_revenue": month_summary["total_revenue"],
                "dine_in_revenue": dine_in_revenue,
                "takeout_revenue": takeout_revenue,
                "dine_in_ratio": cls._percentage(dine_in_revenue, total_revenue),
                "takeout_ratio": cls._percentage(takeout_revenue, total_revenue),
            },
            "trend_rows": daily_rows,
            "daily_detail_rows": daily_detail_rows,
            "has_daily_data": any(
                row["completed_order_count"] > 0 for row in daily_rows
            ),
            "top_items": top_items,
            "chart_data": {
                "trend_labels": [row["date_label"] for row in daily_rows],
                "trend_revenue": [float(row["total_revenue"]) for row in daily_rows],
                "order_counts": [row["completed_order_count"] for row in daily_rows],
                "type_labels": ["內用", "外帶"],
                "type_revenue": [float(dine_in_revenue), float(takeout_revenue)],
            },
        }

    @classmethod
    def empty_dashboard(cls, args):
        filters = cls._parse_filters(args)
        zero = Decimal("0")
        return {
            "filters": filters,
            "summary": {
                "total_revenue": zero,
                "completed_order_count": 0,
                "average_order_value": zero,
                "month_revenue": zero,
                "dine_in_revenue": zero,
                "takeout_revenue": zero,
                "dine_in_ratio": zero,
                "takeout_ratio": zero,
            },
            "trend_rows": [],
            "daily_detail_rows": [],
            "has_daily_data": False,
            "top_items": [],
            "chart_data": {
                "trend_labels": [],
                "trend_revenue": [],
                "order_counts": [],
                "type_labels": ["內用", "外帶"],
                "type_revenue": [0, 0],
            },
        }

    @classmethod
    def _parse_filters(cls, args):
        today = date.today()
        preset = (args.get("preset") or "month").strip()
        if preset not in cls.PRESETS:
            preset = "month"

        error = None
        custom_start = (args.get("start_date") or "").strip()
        custom_end = (args.get("end_date") or "").strip()

        if preset == "today":
            start_date = today
            end_date = today
            label = "今天"
        elif preset == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = today
            label = "本週"
        elif preset == "last7":
            start_date = today - timedelta(days=6)
            end_date = today
            label = "最近 7 天"
        elif preset == "last30":
            start_date = today - timedelta(days=29)
            end_date = today
            label = "最近 30 天"
        elif preset == "custom":
            try:
                start_date = cls._parse_date(custom_start)
                end_date = cls._parse_date(custom_end)
                if start_date > end_date:
                    raise ValueError("開始日期不可晚於結束日期")
                label = f"{start_date.isoformat()} 至 {end_date.isoformat()}"
            except ValueError as exc:
                start_date, end_date = cls._month_range(today)
                label = "本月"
                preset = "month"
                error = f"自訂日期無效，已改為顯示本月：{exc}"
        else:
            start_date, end_date = cls._month_range(today)
            label = "本月"

        return {
            "preset": preset,
            "start_date": start_date,
            "end_date": end_date,
            "start_date_value": start_date.isoformat(),
            "end_date_value": end_date.isoformat(),
            "custom_start": custom_start,
            "custom_end": custom_end,
            "label": label,
            "error": error,
        }

    @staticmethod
    def _parse_date(value):
        if not value:
            raise ValueError("請輸入開始日期與結束日期")
        return datetime.strptime(value, "%Y-%m-%d").date()

    @staticmethod
    def _month_range(day):
        last_day = monthrange(day.year, day.month)[1]
        return date(day.year, day.month, 1), date(day.year, day.month, last_day)

    @staticmethod
    def _normalize_summary(row):
        row = row or {}
        return {
            "total_revenue": Decimal(row.get("total_revenue") or 0),
            "completed_order_count": int(row.get("completed_order_count") or 0),
            "dine_in_revenue": Decimal(row.get("dine_in_revenue") or 0),
            "takeout_revenue": Decimal(row.get("takeout_revenue") or 0),
        }

    @classmethod
    def _fill_daily_rows(cls, start_date, end_date, rows):
        row_map = {}
        for row in rows or []:
            revenue_date = row["revenue_date"]
            if isinstance(revenue_date, datetime):
                revenue_date = revenue_date.date()
            elif isinstance(revenue_date, str):
                revenue_date = cls._parse_date(revenue_date)
            row_map[revenue_date] = row

        filled_rows = []
        current = start_date
        while current <= end_date:
            row = row_map.get(current, {})
            filled_rows.append(
                {
                    "date": current,
                    "date_label": current.strftime("%m/%d"),
                    "completed_order_count": int(row.get("completed_order_count") or 0),
                    "dine_in_revenue": Decimal(row.get("dine_in_revenue") or 0),
                    "takeout_revenue": Decimal(row.get("takeout_revenue") or 0),
                    "total_revenue": Decimal(row.get("total_revenue") or 0),
                }
            )
            current += timedelta(days=1)
        return filled_rows

    @staticmethod
    def _normalize_top_items(rows):
        return [
            {
                "item_name": row["item_name"],
                "total_quantity": int(row.get("total_quantity") or 0),
                "total_sales": Decimal(row.get("total_sales") or 0),
            }
            for row in rows or []
        ]

    @staticmethod
    def _percentage(part, total):
        if not total:
            return Decimal("0")
        return ((Decimal(part) / Decimal(total)) * Decimal("100")).quantize(
            Decimal("0.1"),
            rounding=ROUND_HALF_UP,
        )
