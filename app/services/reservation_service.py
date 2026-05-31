from app.repositories.reservation_repository import ReservationRepository
from app.services.line_service import LineService


class ReservationService:
    STATUSES = ("pending", "confirmed", "cancelled", "completed")
    REQUIRED_FIELDS = (
        "customer_name",
        "customer_phone",
        "reservation_date",
        "reservation_time",
        "party_size",
    )

    @classmethod
    def create_reservation(cls, form_data):
        data = cls._normalize_form_data(form_data)
        reservation_id = ReservationRepository.create(data)
        reservation = {"id": reservation_id, **data}
        LineService.notify_new_reservation(reservation)

        return reservation

    @classmethod
    def _normalize_form_data(cls, form_data, include_status=False):
        data = {field: form_data.get(field, "").strip() for field in cls.REQUIRED_FIELDS}
        missing = [field for field, value in data.items() if not value]
        if missing:
            raise ValueError(f"缺少必要欄位：{', '.join(missing)}")

        try:
            data["party_size"] = int(data["party_size"])
        except ValueError as exc:
            raise ValueError("人數必須是有效數字") from exc

        if data["party_size"] <= 0:
            raise ValueError("人數必須大於 0")

        data["note"] = form_data.get("note", "").strip() or None

        if include_status:
            status = form_data.get("status", "pending").strip() or "pending"
            if status not in cls.STATUSES:
                raise ValueError("訂位狀態不正確")
            data["status"] = status

        return data

    @staticmethod
    def list_reservations():
        return ReservationRepository.list_all()

    @staticmethod
    def get_reservation(reservation_id):
        return ReservationRepository.get_by_id(reservation_id)

    @classmethod
    def update_reservation(cls, reservation_id, form_data):
        data = cls._normalize_form_data(form_data, include_status=True)
        ReservationRepository.update(reservation_id, data)
        return {"id": reservation_id, **data}

    @staticmethod
    def delete_reservation(reservation_id):
        ReservationRepository.delete(reservation_id)
