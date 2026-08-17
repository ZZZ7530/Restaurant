import secrets

from flask import Blueprint, jsonify, request, session

from app.services.ai_recommendation_service import (
    AIRateLimitError,
    AIUnavailableError,
    AiRecommendationService,
)


ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.post("/recommendations")
def recommendations():
    session.setdefault("ai_rate_id", secrets.token_urlsafe(16))
    try:
        result = AiRecommendationService.build_recommendation(
            request.get_json(silent=True) or {},
            client_ip=request.headers.get("X-Forwarded-For", request.remote_addr),
            session_id=session["ai_rate_id"],
        )
    except AIRateLimitError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 429
    except ValueError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 400
    except AIUnavailableError as exc:
        return jsonify({"ok": False, "message": str(exc)}), 503

    return jsonify(result)
