from flask import Blueprint, abort, current_app, jsonify, render_template, request

from app.services.menu_service import MenuService
from app.services.table_service import TableService
from app.services.line_service import LineService


public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def index():
    featured_items = MenuService.list_featured_items()
    return render_template("index.html", featured_items=featured_items)


@public_bp.get("/menu")
def menu():
    categories = MenuService.list_synced_public_menu()
    return render_template("menu.html", categories=categories)


@public_bp.get("/contact")
def contact():
    return render_template("contact.html")


@public_bp.get("/newyear-menu.html")
def newyear_menu():
    return render_template("newyear-menu.html")


@public_bp.get("/test-line")
def test_line():
    if not LineService.is_user_notification_configured():
        return "LINE \u8a2d\u5b9a\u5c1a\u672a\u5b8c\u6210", 200

    result = LineService.send_test_message()
    if result["ok"]:
        return "LINE \u901a\u77e5\u6e2c\u8a66\u5df2\u9001\u51fa", 200

    return (
        "LINE \u901a\u77e5\u767c\u9001\u5931\u6557\u3002\n"
        f"HTTP Status: {result['status_code']}\n"
        f"Response Body: {result['response_body']}\n"
        f"Error: {result['error']}"
    ), 200


@public_bp.post("/line/webhook")
def line_webhook():
    payload = request.get_json(silent=True) or {}
    events = payload.get("events", [])

    if not events:
        current_app.logger.info("LINE webhook received without events: %s", payload)
        return jsonify({"status": "ok"}), 200

    for event in events:
        source = event.get("source", {})
        user_id = source.get("userId")
        group_id = source.get("groupId")
        room_id = source.get("roomId")
        current_app.logger.info(
            "LINE webhook source: userId=%s groupId=%s roomId=%s",
            user_id,
            group_id,
            room_id,
        )

        message = event.get("message", {})
        if message.get("type") == "text":
            current_app.logger.info("LINE webhook text message: %s", message.get("text", ""))

    return jsonify({"status": "ok"}), 200


@public_bp.get("/table-order/<table_number>")
def table_order(table_number):
    table = TableService.get_active_table(table_number)
    if not table:
        abort(404)

    categories = MenuService.list_synced_public_menu()
    return render_template("table_order.html", categories=categories, table=table)
