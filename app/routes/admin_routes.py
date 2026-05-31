from functools import wraps

import mysql.connector
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

from app.services.menu_service import MenuService
from app.services.order_service import OrderService
from app.services.reservation_service import ReservationService
from app.services.daily_price_service import DailyPriceService
from app.services.table_service import TableService


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return view_func(*args, **kwargs)

    return wrapped_view


@admin_bp.get("/login")
def login():
    return render_template("admin/login.html", error=None)


@admin_bp.post("/login")
def login_post():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    if (
        username == current_app.config["ADMIN_USERNAME"]
        and password == current_app.config["ADMIN_PASSWORD"]
    ):
        session["admin_logged_in"] = True
        session["admin_username"] = username
        return redirect(url_for("admin.dashboard"))
    return render_template("admin/login.html", error="帳號或密碼錯誤"), 401


@admin_bp.get("/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("admin.login"))


@admin_bp.get("")
@admin_bp.get("/dashboard")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html")


def _render_admin_error(template_name, error, status=500, **context):
    return render_template(template_name, error=error, **context), status


@admin_bp.get("/reservations")
@admin_required
def reservations():
    try:
        reservations_data = ReservationService.list_reservations()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load reservations for admin.")
        reservations_data = []
        error = f"無法讀取訂位資料，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template(
        "admin/reservations.html",
        reservations=reservations_data,
        error=error,
    )


@admin_bp.get("/reservations/new")
@admin_required
def reservation_new():
    return render_template(
        "admin/reservation_form.html",
        reservation=None,
        statuses=ReservationService.STATUSES,
        error=None,
    )


@admin_bp.post("/reservations/new")
@admin_required
def reservation_create():
    try:
        ReservationService.create_reservation(request.form)
        return redirect(url_for("admin.reservations"))
    except (ValueError, mysql.connector.Error) as exc:
        return _render_admin_error(
            "admin/reservation_form.html",
            str(exc),
            status=400,
            reservation=request.form,
            statuses=ReservationService.STATUSES,
        )


@admin_bp.get("/reservations/<int:reservation_id>/edit")
@admin_required
def reservation_edit(reservation_id):
    reservation = ReservationService.get_reservation(reservation_id)
    if not reservation:
        return redirect(url_for("admin.reservations"))

    return render_template(
        "admin/reservation_form.html",
        reservation=reservation,
        statuses=ReservationService.STATUSES,
        error=None,
    )


@admin_bp.post("/reservations/<int:reservation_id>/edit")
@admin_required
def reservation_update(reservation_id):
    try:
        ReservationService.update_reservation(reservation_id, request.form)
        return redirect(url_for("admin.reservations"))
    except (ValueError, mysql.connector.Error) as exc:
        form_data = request.form.copy()
        form_data["id"] = reservation_id
        return _render_admin_error(
            "admin/reservation_form.html",
            str(exc),
            status=400,
            reservation=form_data,
            statuses=ReservationService.STATUSES,
        )


@admin_bp.post("/reservations/<int:reservation_id>/delete")
@admin_required
def reservation_delete(reservation_id):
    ReservationService.delete_reservation(reservation_id)
    return redirect(url_for("admin.reservations"))


@admin_bp.get("/orders")
@admin_required
def orders():
    try:
        orders_data = OrderService.list_takeout_orders()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load orders for admin.")
        orders_data = []
        error = f"無法讀取訂單資料，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template("admin/orders.html", orders=orders_data, error=error)


@admin_bp.get("/dine-in-orders")
@admin_required
def dine_in_orders():
    try:
        orders_data = OrderService.list_dine_in_orders()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load dine-in orders for admin.")
        orders_data = []
        error = f"無法讀取內用訂單資料，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template("admin/dine_in_orders.html", orders=orders_data, error=error)


@admin_bp.get("/table-qrcodes")
@admin_required
def table_qrcodes():
    try:
        table_groups = TableService.list_active_tables_grouped_by_floor()
        base_url = current_app.config.get("TABLE_ORDER_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
        for group in table_groups:
            group["tables"] = [
                {
                    **table,
                    "order_url": f"{base_url}/table-order/{table['table_number']}",
                }
                for table in group["tables"]
            ]
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load table QR codes.")
        table_groups = []
        error = f"讀取桌號 QR Code 資料失敗，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template(
        "admin/table_qrcodes.html",
        table_groups=table_groups,
        error=error,
    )


@admin_bp.get("/kitchen")
@admin_required
def kitchen():
    try:
        kitchen_orders = OrderService.list_kitchen_orders()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load kitchen board.")
        kitchen_orders = []
        error = f"無法讀取出餐資料，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template("admin/kitchen.html", orders=kitchen_orders, error=error)


@admin_bp.get("/completed-orders")
@admin_required
def completed_orders():
    try:
        completed_orders_data = OrderService.list_completed_orders()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load completed orders.")
        completed_orders_data = []
        error = f"無法讀取完成訂單，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template(
        "admin/completed_orders.html",
        orders=completed_orders_data,
        error=error,
    )


@admin_bp.post("/orders/<int:order_id>/complete")
@admin_required
def order_complete(order_id):
    try:
        OrderService.complete_order(order_id)
    except mysql.connector.Error:
        current_app.logger.exception("Failed to complete order.")
    return redirect(url_for("admin.kitchen"))


@admin_bp.post("/orders/<int:order_id>/delete-permanently")
@admin_required
def order_delete_permanently(order_id):
    OrderService.delete_order(order_id)
    return redirect(url_for("admin.completed_orders"))


@admin_bp.post("/order-items/<int:item_id>/complete")
@admin_required
def order_item_complete(item_id):
    try:
        OrderService.mark_order_item_completed(item_id)
    except (ValueError, mysql.connector.Error) as exc:
        current_app.logger.exception("Failed to mark order item completed.")
    return redirect(url_for("admin.kitchen"))


@admin_bp.post("/order-items/<int:item_id>/undo-complete")
@admin_required
def order_item_undo_complete(item_id):
    try:
        OrderService.undo_order_item_completed(item_id)
    except (ValueError, mysql.connector.Error) as exc:
        current_app.logger.exception("Failed to undo order item completion.")
    return redirect(url_for("admin.kitchen"))


@admin_bp.get("/orders/new")
@admin_required
def order_new():
    return render_template(
        "admin/order_form.html",
        order=None,
        statuses=OrderService.STATUSES,
        error=None,
    )


@admin_bp.post("/orders/new")
@admin_required
def order_create():
    try:
        OrderService.create_admin_order(request.form)
        return redirect(url_for("admin.orders"))
    except (ValueError, mysql.connector.Error) as exc:
        return _render_admin_error(
            "admin/order_form.html",
            str(exc),
            status=400,
            order=request.form,
            statuses=OrderService.STATUSES,
        )


@admin_bp.get("/orders/<int:order_id>")
@admin_required
def order_detail(order_id):
    order = OrderService.get_order(order_id)
    if not order:
        return redirect(url_for("admin.orders"))
    return render_template("admin/order_detail.html", order=order)


@admin_bp.get("/orders/<int:order_id>/edit")
@admin_required
def order_edit(order_id):
    order = OrderService.get_order(order_id)
    if not order:
        return redirect(url_for("admin.orders"))

    return render_template(
        "admin/order_form.html",
        order=order,
        statuses=OrderService.STATUSES,
        error=None,
    )


@admin_bp.post("/orders/<int:order_id>/edit")
@admin_required
def order_update(order_id):
    try:
        OrderService.update_admin_order(order_id, request.form)
        return redirect(url_for("admin.orders"))
    except (ValueError, mysql.connector.Error) as exc:
        form_data = request.form.copy()
        form_data["id"] = order_id
        return _render_admin_error(
            "admin/order_form.html",
            str(exc),
            status=400,
            order=form_data,
            statuses=OrderService.STATUSES,
        )


@admin_bp.post("/orders/<int:order_id>/delete")
@admin_required
def order_delete(order_id):
    OrderService.delete_order(order_id)
    return redirect(url_for("admin.orders"))


@admin_bp.get("/menu")
@admin_bp.get("/menu-items")
@admin_required
def menu_items():
    try:
        items = MenuService.list_admin_items()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load menu items for admin.")
        items = []
        error = f"無法讀取菜單資料，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template("admin/menu_items.html", items=items, error=error)


@admin_bp.get("/menu-items/new")
@admin_bp.get("/menu-items/<int:item_id>/edit")
@admin_required
def menu_form(item_id=None):
    item = MenuService.get_item(item_id) if item_id else None
    if item_id and not item:
        return redirect(url_for("admin.menu_items"))

    return render_template(
        "admin/menu_form.html",
        item=item,
        categories=MenuService.list_categories(),
        error=None,
    )


@admin_bp.post("/menu-items/new")
@admin_required
def menu_create():
    try:
        MenuService.create_item(request.form)
        return redirect(url_for("admin.menu_items"))
    except (ValueError, mysql.connector.Error) as exc:
        return _render_admin_error(
            "admin/menu_form.html",
            str(exc),
            status=400,
            item=request.form,
            categories=MenuService.list_categories(),
        )


@admin_bp.post("/menu-items/<int:item_id>/edit")
@admin_required
def menu_update(item_id):
    try:
        MenuService.update_item(item_id, request.form)
        return redirect(url_for("admin.menu_items"))
    except (ValueError, mysql.connector.Error) as exc:
        form_data = request.form.copy()
        form_data["id"] = item_id
        return _render_admin_error(
            "admin/menu_form.html",
            str(exc),
            status=400,
            item=form_data,
            categories=MenuService.list_categories(),
        )


@admin_bp.post("/menu-items/<int:item_id>/delete")
@admin_required
def menu_delete(item_id):
    try:
        MenuService.delete_item(item_id)
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to delete menu item.")
        return _render_admin_error(
            "admin/menu_items.html",
            f"刪除失敗，可能已有訂單明細參考此菜色。({exc.errno})",
            status=400,
            items=MenuService.list_admin_items(),
        )
    return redirect(url_for("admin.menu_items"))


@admin_bp.get("/daily-prices")
@admin_required
def daily_prices():
    try:
        prices = DailyPriceService.list_prices()
        error = None
    except mysql.connector.Error as exc:
        current_app.logger.exception("Failed to load daily menu prices.")
        prices = []
        error = f"無法讀取時價資料，請確認 MySQL 已啟動並可連線。({exc.errno})"

    return render_template("admin/daily_prices.html", prices=prices, error=error)


@admin_bp.get("/daily-prices/new")
@admin_required
def daily_price_new():
    return render_template("admin/daily_price_form.html", price=None, error=None)


@admin_bp.post("/daily-prices/new")
@admin_required
def daily_price_create():
    try:
        DailyPriceService.create_price(request.form)
        return redirect(url_for("admin.daily_prices"))
    except (ValueError, mysql.connector.Error) as exc:
        return _render_admin_error(
            "admin/daily_price_form.html",
            str(exc),
            status=400,
            price=request.form,
        )


@admin_bp.get("/daily-prices/<int:price_id>/edit")
@admin_required
def daily_price_edit(price_id):
    price = DailyPriceService.get_price(price_id)
    if not price:
        return redirect(url_for("admin.daily_prices"))
    return render_template("admin/daily_price_form.html", price=price, error=None)


@admin_bp.post("/daily-prices/<int:price_id>/edit")
@admin_required
def daily_price_update(price_id):
    try:
        DailyPriceService.update_price(price_id, request.form)
        return redirect(url_for("admin.daily_prices"))
    except (ValueError, mysql.connector.Error) as exc:
        form_data = request.form.copy()
        form_data["id"] = price_id
        return _render_admin_error(
            "admin/daily_price_form.html",
            str(exc),
            status=400,
            price=form_data,
        )


@admin_bp.post("/daily-prices/<int:price_id>/delete")
@admin_required
def daily_price_delete(price_id):
    DailyPriceService.delete_price(price_id)
    return redirect(url_for("admin.daily_prices"))


@admin_bp.get("/revenue")
@admin_required
def revenue():
    return render_template("admin/revenue.html")


@admin_bp.get("/settings")
@admin_required
def settings():
    return render_template("admin/settings.html")
