import mysql.connector
from flask import Blueprint, current_app, jsonify, render_template, request

from app.services.reservation_service import ReservationService


reservation_bp = Blueprint("reservation", __name__, url_prefix="/reservations")


@reservation_bp.get("")
def reservation_form():
    return render_template("reservation.html")


@reservation_bp.post("")
def create_reservation():
    try:
        reservation = ReservationService.create_reservation(request.form)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to create reservation because MySQL is unavailable.")
        return jsonify({"error": f"資料庫連線失敗，請確認 MySQL 已啟動並可連線。({exc.errno})"}), 503
    except Exception:
        current_app.logger.exception("Unexpected error while creating reservation.")
        return jsonify({"error": "訂位建立時發生未預期錯誤，請查看伺服器終端機 traceback。"}), 500

    return jsonify({"message": "訂位已送出，店家將盡快確認。", "reservation": reservation}), 201
