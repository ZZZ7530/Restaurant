import mysql.connector
from flask import Blueprint, current_app, jsonify, render_template, request

from app.services.menu_service import MenuService
from app.services.order_service import OrderService


order_bp = Blueprint("orders", __name__, url_prefix="/orders")


@order_bp.get("/takeout")
def takeout_form():
    categories = MenuService.list_synced_public_menu()
    return render_template("takeout.html", categories=categories)



@order_bp.post("")
def create_order():
    try:
        order = OrderService.create_order(request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to create takeout order.")
        return jsonify({"error": f"資料庫寫入失敗，請確認 MySQL 可正常連線。({exc.errno})"}), 503
    except Exception:
        current_app.logger.exception("Unexpected error while creating takeout order.")
        return jsonify({"error": "訂單建立時發生未預期錯誤，請查看伺服器終端機 traceback。"}), 500

    return jsonify({"message": "外帶訂單已送出，店家將盡快確認。", "order": order}), 201


@order_bp.post("/dine-in")
def create_dine_in_order():
    try:
        order = OrderService.create_dine_in_order(request.get_json(silent=True) or {})
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to create dine-in order.")
        return jsonify({"error": f"資料庫寫入失敗，請確認 MySQL 可正常連線。({exc.errno})"}), 503
    except Exception:
        current_app.logger.exception("Unexpected error while creating dine-in order.")
        return jsonify({"error": "內用訂單建立時發生未預期錯誤，請查看伺服器終端機 traceback。"}), 500

    return jsonify({"message": "內用訂單已送出，請稍候出餐。", "order": order}), 201
