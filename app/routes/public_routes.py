from flask import Blueprint, abort, current_app, jsonify, render_template, request

from app.services.menu_service import MenuService
from app.services.table_service import TableService
from app.services.line_service import LineService
from app.services.line_customer_binding_service import LineCustomerBindingService


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
    if current_app.config.get("IS_PRODUCTION"):
        abort(404)

    if not LineService.is_user_notification_configured():
        return "LINE \u8a2d\u5b9a\u5c1a\u672a\u5b8c\u6210", 200

    result = LineService.send_test_message()
    if result["ok"]:
        return "LINE \u901a\u77e5\u6e2c\u8a66\u5df2\u9001\u51fa", 200

    return (
        "LINE \u901a\u77e5\u767c\u9001\u5931\u6557\u3002\n"
        f"HTTP Status: {result['status_code']}\n"
        f"Error: {result['error']}"
    ), 200


@public_bp.post("/line/webhook")
def line_webhook():
    if not current_app.config.get("LINE_CHANNEL_SECRET", "").strip():
        current_app.logger.warning("LINE webhook rejected: channel secret is not configured.")
        return jsonify({"error": "LINE webhook is not configured."}), 503

    signature = request.headers.get("X-Line-Signature", "")
    if not signature:
        current_app.logger.warning("LINE webhook rejected: missing signature.")
        return jsonify({"error": "Missing LINE signature."}), 400

    body = request.get_data(cache=True)
    if not LineService.verify_webhook_signature(body, signature):
        current_app.logger.warning("LINE webhook rejected: invalid signature.")
        return jsonify({"error": "Invalid LINE signature."}), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        current_app.logger.warning("LINE webhook rejected: malformed JSON.")
        return jsonify({"error": "Malformed webhook payload."}), 400

    events = payload.get("events", [])
    if not isinstance(events, list):
        current_app.logger.warning("LINE webhook rejected: malformed events.")
        return jsonify({"error": "Malformed webhook events."}), 400

    if not events:
        current_app.logger.info("LINE webhook received without events.")
        return jsonify({"status": "ok"}), 200

    for event in events:
        if not isinstance(event, dict):
            continue
        current_app.logger.info("LINE webhook event received: type=%s", event.get("type"))
        if event.get("type") != "message":
            continue
        message = event.get("message") or {}
        if message.get("type") != "text":
            continue

        result = LineCustomerBindingService.bind_from_message_event(event)
        if result.get("reply_text"):
            LineService.safe_reply_text(event.get("replyToken"), result["reply_text"])

    return jsonify({"status": "ok"}), 200


@public_bp.get("/table-order/<table_number>")
def table_order(table_number):
    table = TableService.get_active_table(table_number)
    if not table:
        abort(404)

    categories = MenuService.list_synced_public_menu()
    return render_template("table_order.html", categories=categories, table=table)
