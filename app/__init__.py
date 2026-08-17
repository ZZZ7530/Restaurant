from flask import Flask, jsonify

from app.config import Config
from app.routes.admin_routes import admin_bp
from app.routes.ai_routes import ai_bp
from app.routes.order_routes import order_bp
from app.routes.public_routes import public_bp
from app.routes.reservation_routes import reservation_bp


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    app.register_blueprint(public_bp)
    app.register_blueprint(reservation_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)

    @app.context_processor
    def inject_brand():
        return {"restaurant_name": app.config["RESTAURANT_NAME"]}

    @app.errorhandler(ValueError)
    def handle_value_error(error):
        return jsonify({"error": str(error)}), 400

    return app
