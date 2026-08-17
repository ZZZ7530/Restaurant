import json
import time
from collections import defaultdict, deque
from decimal import Decimal, InvalidOperation

from flask import current_app

from app.services.menu_service import MenuService


class AIRateLimitError(ValueError):
    pass


class AIUnavailableError(RuntimeError):
    pass


class AiRecommendationService:
    MODES = {"menu", "takeout", "dine_in"}
    MAX_LIST_ITEMS = 12
    MAX_TEXT_LENGTH = 500
    MAX_LIST_TEXT_LENGTH = 40
    IP_LIMIT = (5, 60)
    SESSION_LIMIT = (20, 600)

    _ip_calls = defaultdict(deque)
    _session_calls = defaultdict(deque)

    @classmethod
    def build_recommendation(cls, payload, client_ip=None, session_id=None):
        cls._check_rate_limit(client_ip, session_id)
        request_data = cls._normalize_request(payload)
        menu_items = MenuService.list_ai_recommendable_items()

        if not menu_items:
            return {
                "ok": True,
                "summary": cls._build_summary(request_data),
                "items": [],
                "fixed_total": 0,
                "market_price_count": 0,
                "reason": "目前沒有可推薦的菜色。",
                "warnings": ["目前菜單暫無可推薦品項。"],
            }

        if current_app.config.get("AI_MOCK_MODE"):
            return cls._build_mock_recommendation(request_data, menu_items)

        if not current_app.config.get("OPENAI_API_KEY"):
            raise AIUnavailableError("AI 推薦目前尚未啟用")

        if not current_app.config.get("OPENAI_MODEL"):
            raise AIUnavailableError("AI 推薦目前尚未啟用")

        return cls._build_openai_recommendation(request_data, menu_items)

    @classmethod
    def validate_ai_items(cls, request_data, ai_items, reason=""):
        menu_items = MenuService.list_ai_recommendable_items()
        item_map = {item["menu_item_id"]: item for item in menu_items}

        validated_items = []
        warnings = []
        for ai_item in ai_items or []:
            try:
                menu_item_id = int(ai_item.get("menu_item_id"))
            except (TypeError, ValueError):
                continue

            menu_item = item_map.get(menu_item_id)
            if not menu_item:
                continue

            specification = cls._valid_specification(
                menu_item,
                str(ai_item.get("specification") or "").strip(),
            )
            if specification is None:
                continue
            quantity = cls._normalize_quantity(ai_item.get("quantity"))
            unit_price = cls._price_for_specification(menu_item, specification)
            is_market_price = bool(menu_item["is_market_price"]) or unit_price is None
            display_price_label = cls._display_price_label(
                menu_item,
                specification,
                unit_price,
                is_market_price,
            )

            validated_items.append(
                {
                    "menu_item_id": menu_item_id,
                    "name": menu_item["name"],
                    "quantity": quantity,
                    "specification": specification,
                    "unit_price": 0 if is_market_price else int(unit_price),
                    "display_price_label": display_price_label,
                    "is_market_price": is_market_price,
                    "image_filename": menu_item.get("image_filename"),
                    "reason": cls._trim_text(ai_item.get("reason") or "符合本次需求。", 120),
                }
            )

        validated_items, budget_warnings = cls._apply_budget_policy(
            request_data,
            validated_items,
            menu_items,
        )
        warnings.extend(budget_warnings)

        fixed_total = sum(
            item["unit_price"] * item["quantity"]
            for item in validated_items
            if not item["is_market_price"]
        )
        market_price_count = sum(1 for item in validated_items if item["is_market_price"])
        if market_price_count:
            warnings.append(
                f"另有 {market_price_count} 道時價料理未計入固定價格合計，實際總額可能因時價餐點超過預算。"
            )
        if not validated_items:
            warnings.append("AI 未提供可用的真實菜單品項。")

        return {
            "ok": True,
            "summary": cls._build_summary(request_data),
            "items": validated_items,
            "fixed_total": int(fixed_total),
            "market_price_count": market_price_count,
            "reason": cls._build_final_reason(request_data, validated_items),
            "warnings": warnings,
        }

    @classmethod
    def _build_mock_recommendation(cls, request_data, menu_items):
        budget = request_data["budget"]
        target_count = min(max(request_data["party_size"] + 1, 4), 7, len(menu_items))
        terms = cls._recommendation_terms(request_data)

        fixed_items = [item for item in menu_items if not item.get("is_market_price")]
        market_items = [item for item in menu_items if item.get("is_market_price")]
        fixed_items.sort(key=lambda item: cls._mock_score(item, terms), reverse=True)
        market_items.sort(key=lambda item: cls._mock_score(item, terms), reverse=True)

        selected = []
        fixed_total = 0
        for item in fixed_items:
            specification = cls._default_specification(item)
            price = cls._price_for_specification(item, specification) or 0
            if budget and selected and fixed_total + price > budget and len(selected) >= 4:
                continue
            selected.append(
                {
                    "menu_item_id": item["menu_item_id"],
                    "quantity": 1,
                    "specification": specification,
                    "reason": cls._mock_reason(item, terms),
                }
            )
            fixed_total += price
            if len(selected) >= target_count:
                break

        if market_items and len(selected) < target_count:
            selected.append(
                {
                    "menu_item_id": market_items[0]["menu_item_id"],
                    "quantity": 1,
                    "specification": "",
                    "reason": "可搭配一道時價料理，實際價格請以店家現場為準。",
                }
            )

        if not selected and market_items:
            selected.append(
                {
                    "menu_item_id": market_items[0]["menu_item_id"],
                    "quantity": 1,
                    "specification": "",
                    "reason": "目前可推薦品項以時價料理為主。",
                }
            )

        return cls.validate_ai_items(
            request_data,
            selected,
            reason="Mock 模式依目前真實菜單、預算與偏好產生推薦；正式 AI 啟用前不會呼叫 OpenAI API。",
        )

    @classmethod
    def _build_openai_recommendation(cls, request_data, menu_items):
        started_at = time.perf_counter()
        try:
            raw_result = cls._call_openai(request_data, menu_items)
            result = cls.validate_ai_items(
                request_data,
                raw_result.get("items", []),
                reason=raw_result.get("reason", ""),
            )
        except AIUnavailableError:
            raise
        except Exception as exc:
            raise cls._friendly_openai_error(exc) from exc

        current_app.logger.info(
            "OpenAI recommendation completed: items=%s duration_ms=%s",
            len(result.get("items", [])),
            int((time.perf_counter() - started_at) * 1000),
        )
        return result

    @classmethod
    def _call_openai(cls, request_data, menu_items):
        client = cls._create_openai_client()
        response = client.responses.create(
            model=current_app.config["OPENAI_MODEL"],
            input=[
                {
                    "role": "system",
                    "content": (
                        "你是餐廳點餐推薦助手。你只能從提供的真實菜單中挑選餐點，"
                        "只能使用提供的 menu_item_id，不得發明新餐點、價格或規格。"
                        "價格與時價判斷由伺服器重新驗證，你只需要挑選品項、數量、有效規格與簡短理由。"
                        "未知時價不可自行估價，預算只需盡量遵守固定價格餐點。"
                        "budget 是整桌預算上限，不是每人預算；固定價格餐點合計不可超過 budget。"
                        "在符合人數、喜好與飲食需求的前提下，盡量使用 70% 到 100% 的整桌預算。"
                        "不要單純為湊預算加入不符合需求或數量過多的餐點。"
                        "推薦理由不得提到任何估算總價或合計金額。"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "request": {
                                "mode": request_data["mode"],
                                "party_size": request_data["party_size"],
                                "budget": request_data["budget"],
                                "preferences": request_data["preferences"],
                                "dietary_needs": request_data["dietary_needs"],
                                "message": request_data["message"],
                            },
                            "menu_items": cls._openai_menu_payload(menu_items),
                            "recommendation_rules": {
                                "target_item_count": "4 到 7 道，依人數與需求合理調整",
                                "quantity": "每道 1 到 20 份",
                                "specification": "只能使用 price_options 中存在的 specification，沒有規格則用空字串",
                                "budget": "budget 是整桌固定價格餐點合計硬上限，盡量使用 70% 到 100%，但不得超過",
                                "pricing_text": "reason 不得包含估算總價、約多少元、合計金額等價格文字",
                                "reason": "每道餐點理由不超過 120 字，整體理由不超過 240 字",
                            },
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "restaurant_menu_recommendation",
                    "strict": True,
                    "schema": cls._openai_response_schema(),
                }
            },
        )
        return cls._parse_openai_response(response)

    @classmethod
    def _create_openai_client(cls):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise AIUnavailableError("AI 推薦目前尚未啟用") from exc

        kwargs = {
            "api_key": current_app.config["OPENAI_API_KEY"],
            "timeout": 20.0,
        }
        base_url = str(current_app.config.get("OPENAI_API_BASE_URL") or "").strip()
        if base_url:
            kwargs["base_url"] = base_url
        return OpenAI(**kwargs)

    @staticmethod
    def _openai_response_schema():
        return {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "items": {
                    "type": "array",
                    "minItems": 0,
                    "maxItems": 7,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "menu_item_id": {"type": "integer"},
                            "quantity": {"type": "integer", "minimum": 1, "maximum": 20},
                            "specification": {"type": "string", "maxLength": 40},
                            "reason": {"type": "string", "maxLength": 120},
                        },
                        "required": ["menu_item_id", "quantity", "specification", "reason"],
                    },
                },
                "reason": {"type": "string", "maxLength": 240},
            },
            "required": ["items", "reason"],
        }

    @classmethod
    def _openai_menu_payload(cls, menu_items):
        payload = []
        for item in menu_items:
            payload.append(
                {
                    "menu_item_id": item["menu_item_id"],
                    "name": item["name"],
                    "category_name": item.get("category_name") or "",
                    "description": cls._trim_text(item.get("description") or "", 120),
                    "price": cls._json_number(item.get("price")),
                    "display_price_label": item.get("display_price_label") or "",
                    "is_market_price": bool(item.get("is_market_price")),
                    "price_options": [
                        {
                            "specification": option.get("specification") or "",
                            "price": cls._json_number(option.get("price")),
                        }
                        for option in item.get("price_options") or []
                    ],
                }
            )
        return payload

    @staticmethod
    def _json_number(value):
        if isinstance(value, Decimal):
            return int(value)
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    @classmethod
    def _parse_openai_response(cls, response):
        output_text = getattr(response, "output_text", None)
        if not output_text:
            raise AIUnavailableError("AI 推薦目前暫時無法使用")

        try:
            parsed = json.loads(output_text)
        except (TypeError, json.JSONDecodeError) as exc:
            raise AIUnavailableError("AI 推薦目前暫時無法使用") from exc

        if not isinstance(parsed, dict):
            raise AIUnavailableError("AI 推薦目前暫時無法使用")
        if not isinstance(parsed.get("items"), list):
            raise AIUnavailableError("AI 推薦目前暫時無法使用")
        return parsed

    @staticmethod
    def _friendly_openai_error(exc):
        error_type = type(exc).__name__
        safe_type = error_type.lower()
        current_app.logger.warning("OpenAI recommendation failed: error_type=%s", error_type)

        if "authentication" in safe_type or "permission" in safe_type:
            return AIUnavailableError("AI 推薦目前尚未啟用")
        if "timeout" in safe_type:
            return AIUnavailableError("AI 服務忙碌中，請稍後再試")
        if "ratelimit" in safe_type or "rate_limit" in safe_type or "quota" in safe_type:
            return AIUnavailableError("AI 服務忙碌中，請稍後再試")
        if "api" in safe_type or "connection" in safe_type or "service" in safe_type:
            return AIUnavailableError("AI 推薦目前暫時無法使用")
        return AIUnavailableError("AI 推薦目前暫時無法使用")

    @classmethod
    def _apply_budget_policy(cls, request_data, validated_items, menu_items):
        budget = request_data["budget"]
        if budget <= 0:
            return validated_items, []

        warnings = []
        capped_items, adjusted = cls._cap_fixed_total_to_budget(validated_items, budget)
        if adjusted:
            warnings.append("部分固定價格餐點因超過預算上限，已由系統自動調整。")

        improved_items, low_utilization_warning = cls._improve_budget_utilization(
            request_data,
            capped_items,
            menu_items,
        )
        if low_utilization_warning:
            warnings.append(low_utilization_warning)
        return improved_items, warnings

    @classmethod
    def _cap_fixed_total_to_budget(cls, items, budget):
        capped_items = []
        fixed_total = 0
        adjusted = False

        for item in items:
            if item["is_market_price"]:
                capped_items.append(item)
                continue

            unit_price = int(item["unit_price"] or 0)
            quantity = int(item["quantity"] or 1)
            if unit_price <= 0:
                capped_items.append(item)
                continue

            remaining_budget = budget - fixed_total
            if remaining_budget <= 0:
                adjusted = True
                continue

            allowed_quantity = min(quantity, remaining_budget // unit_price)
            if allowed_quantity <= 0:
                adjusted = True
                continue

            if allowed_quantity != quantity:
                adjusted = True
                item = {**item, "quantity": allowed_quantity}

            capped_items.append(item)
            fixed_total += unit_price * allowed_quantity

        return capped_items, adjusted

    @classmethod
    def _improve_budget_utilization(cls, request_data, items, menu_items):
        budget = request_data["budget"]
        target_total = int(budget * Decimal("0.7"))
        max_item_count = cls._target_recommendation_count(request_data, menu_items)
        target_quantity = cls._target_quantity_per_item(request_data)
        terms = cls._recommendation_terms(request_data)

        while cls._fixed_total(items) < target_total:
            action = cls._next_budget_action(
                request_data,
                items,
                menu_items,
                terms,
                budget,
                max_item_count,
                target_quantity,
            )
            if not action:
                break

            action_type, payload = action
            if action_type == "increase":
                payload["quantity"] += 1
                continue

            menu_item, specification, price = payload
            items.append(
                cls._build_validated_item(
                    menu_item,
                    quantity=1,
                    specification=specification,
                    unit_price=price,
                    reason="為了更符合人數與整桌預算，補入目前菜單中符合需求的餐點。",
                )
            )

        warning = None
        if cls._fixed_total(items) < target_total:
            warning = "依目前條件可搭配的固定價格餐點較少，因此未完全使用預算。"
        return items, warning

    @classmethod
    def _next_budget_action(
        cls,
        request_data,
        items,
        menu_items,
        terms,
        budget,
        max_item_count,
        target_quantity,
    ):
        actions = cls._budget_actions(
            request_data,
            items,
            menu_items,
            terms,
            budget,
            max_item_count,
            target_quantity,
        )
        if not actions:
            return None
        actions.sort(key=lambda action: action[0], reverse=True)
        return actions[0][1]

    @classmethod
    def _budget_actions(
        cls,
        request_data,
        items,
        menu_items,
        terms,
        budget,
        max_item_count,
        target_quantity,
    ):
        fixed_total = cls._fixed_total(items)
        remaining_budget = budget - fixed_total
        if remaining_budget <= 0:
            return []

        actions = []
        menu_map = {item["menu_item_id"]: item for item in menu_items}

        for item in items:
            if item["is_market_price"] or int(item["quantity"] or 1) >= target_quantity:
                continue
            menu_item = menu_map.get(item["menu_item_id"])
            if not menu_item or cls._violates_dietary_needs(menu_item, request_data):
                continue
            unit_price = int(item["unit_price"] or 0)
            if unit_price <= 0 or unit_price > remaining_budget:
                continue
            score = cls._preference_match_score(menu_item, terms)
            if terms and score <= 0:
                continue
            actions.append(((3, score, unit_price), ("increase", item)))

        if len(items) < max_item_count:
            used_keys = {
                (item["menu_item_id"], item.get("specification") or "")
                for item in items
            }
            for menu_item in menu_items:
                if menu_item.get("is_market_price") or cls._violates_dietary_needs(
                    menu_item,
                    request_data,
                ):
                    continue
                score = cls._preference_match_score(menu_item, terms)
                if terms and score <= 0:
                    continue
                option = cls._best_budget_option(menu_item, remaining_budget, used_keys)
                if not option:
                    continue
                specification, price = option
                actions.append(((2, score, price), ("add", (menu_item, specification, price))))

        return actions

    @staticmethod
    def _fixed_total(items):
        return sum(
            int(item["unit_price"] or 0) * int(item["quantity"] or 1)
            for item in items
            if not item["is_market_price"]
        )

    @classmethod
    def _target_recommendation_count(cls, request_data, menu_items):
        return min(max(request_data["party_size"] + 1, 4), 7, len(menu_items))

    @staticmethod
    def _target_quantity_per_item(request_data):
        party_size = request_data["party_size"]
        if party_size >= 8:
            return 3
        if party_size >= 4:
            return 2
        return 1

    @classmethod
    def _best_budget_option(cls, menu_item, remaining_budget, used_keys):
        options = menu_item.get("price_options") or []
        if options:
            valid_options = []
            for option in options:
                specification = option.get("specification") or ""
                price = cls._json_number(option.get("price"))
                if (
                    price > 0
                    and price <= remaining_budget
                    and (menu_item["menu_item_id"], specification) not in used_keys
                ):
                    valid_options.append((specification, price))
            if not valid_options:
                return None
            return max(valid_options, key=lambda option: option[1])

        price = cls._price_for_specification(menu_item, "")
        if (
            price
            and price <= remaining_budget
            and (menu_item["menu_item_id"], "") not in used_keys
        ):
            return "", int(price)
        return None

    @staticmethod
    def _preference_match_score(item, terms):
        if not terms:
            return 1
        haystack = " ".join(
            str(value or "")
            for value in (
                item.get("name"),
                item.get("category_name"),
                item.get("description"),
                item.get("display_price_label"),
            )
        )
        return sum(1 for term in terms if term and term in haystack)

    @staticmethod
    def _violates_dietary_needs(item, request_data):
        needs_text = " ".join(request_data["dietary_needs"] + [request_data["message"]])
        haystack = " ".join(
            str(value or "")
            for value in (
                item.get("name"),
                item.get("category_name"),
                item.get("description"),
                item.get("display_price_label"),
            )
        )

        if any(term in needs_text for term in ("不辣", "不要辣", "不吃辣")) and "辣" in haystack:
            return True
        if "不要其他菜" in needs_text and request_data["preferences"]:
            preference_text = " ".join(request_data["preferences"])
            return not any(term and term in haystack for term in preference_text.split())
        return False

    @classmethod
    def _build_validated_item(cls, menu_item, quantity, specification, unit_price, reason):
        return {
            "menu_item_id": menu_item["menu_item_id"],
            "name": menu_item["name"],
            "quantity": quantity,
            "specification": specification,
            "unit_price": int(unit_price),
            "display_price_label": cls._display_price_label(
                menu_item,
                specification,
                unit_price,
                False,
            ),
            "is_market_price": False,
            "image_filename": menu_item.get("image_filename"),
            "reason": reason,
        }

    @staticmethod
    def _build_final_reason(request_data, items):
        if not items:
            return "目前條件下沒有可用的推薦餐點。"

        parts = [f"此組合適合 {request_data['party_size']} 人分享"]
        if request_data["preferences"]:
            parts.append(f"以{'、'.join(request_data['preferences'][:3])}為主")
        if request_data["dietary_needs"]:
            parts.append(f"並已考量{'、'.join(request_data['dietary_needs'][:2])}")
        return "，".join(parts) + "。"

    @classmethod
    def _normalize_request(cls, payload):
        payload = payload or {}
        mode = str(payload.get("mode") or "menu").strip()
        if mode not in cls.MODES:
            raise ValueError("AI 推薦模式不正確")

        party_size = cls._parse_int(payload.get("party_size"), "用餐人數", allow_empty=False)
        if party_size < 1 or party_size > 20:
            raise ValueError("用餐人數必須介於 1 到 20")

        budget = cls._parse_int(payload.get("budget", 0), "預算")
        if budget < 0 or budget > 100000:
            raise ValueError("預算必須介於 0 到 100000")

        message = str(payload.get("message") or "").strip()
        if len(message) > cls.MAX_TEXT_LENGTH:
            raise ValueError(f"其他需求不可超過 {cls.MAX_TEXT_LENGTH} 字")

        return {
            "mode": mode,
            "party_size": party_size,
            "budget": budget,
            "preferences": cls._normalize_text_list(payload.get("preferences")),
            "dietary_needs": cls._normalize_text_list(payload.get("dietary_needs")),
            "message": message,
        }

    @classmethod
    def _check_rate_limit(cls, client_ip, session_id):
        now = time.time()
        if client_ip:
            cls._check_bucket(cls._ip_calls[str(client_ip)], now, *cls.IP_LIMIT)
        if session_id:
            cls._check_bucket(cls._session_calls[str(session_id)], now, *cls.SESSION_LIMIT)

    @staticmethod
    def _check_bucket(bucket, now, limit, window_seconds):
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            raise AIRateLimitError("AI 推薦呼叫太頻繁，請稍後再試")
        bucket.append(now)

    @classmethod
    def _normalize_text_list(cls, value):
        if isinstance(value, str):
            parts = [value]
        elif isinstance(value, list):
            parts = value
        else:
            parts = []

        normalized = []
        if len(parts) > cls.MAX_LIST_ITEMS:
            raise ValueError(f"偏好與飲食需求最多各 {cls.MAX_LIST_ITEMS} 項")

        normalized = []
        for part in parts:
            text = str(part or "").strip()
            if len(text) > cls.MAX_LIST_TEXT_LENGTH:
                raise ValueError(f"偏好與飲食需求單項不可超過 {cls.MAX_LIST_TEXT_LENGTH} 字")
            if text:
                normalized.append(text)
        return normalized

    @staticmethod
    def _parse_int(value, label, allow_empty=True):
        if isinstance(value, bool):
            raise ValueError(f"{label}必須是數字")
        try:
            if value in (None, ""):
                if not allow_empty:
                    raise ValueError(f"{label}必須是數字")
                return 0
            parsed = Decimal(str(value))
            if not parsed.is_finite() or parsed != parsed.to_integral_value():
                raise ValueError
            return int(parsed)
        except (TypeError, ValueError, InvalidOperation) as exc:
            raise ValueError(f"{label}必須是數字") from exc

    @staticmethod
    def _normalize_quantity(value):
        try:
            quantity = int(value)
        except (TypeError, ValueError):
            quantity = 1
        return min(max(quantity, 1), 20)

    @staticmethod
    def _trim_text(value, max_length):
        text = str(value or "").strip()
        return text[:max_length]

    @staticmethod
    def _valid_specification(menu_item, specification):
        options = menu_item.get("price_options") or []
        if options:
            valid_specs = {option.get("specification") for option in options}
            return specification if specification in valid_specs else None
        if specification:
            return None
        return ""

    @staticmethod
    def _price_for_specification(menu_item, specification):
        for option in menu_item.get("price_options") or []:
            if option.get("specification") == specification:
                return option.get("price")
        if menu_item.get("is_market_price"):
            return None
        price = menu_item.get("price")
        if isinstance(price, Decimal):
            price = int(price)
        return int(price or 0)

    @staticmethod
    def _display_price_label(menu_item, specification, unit_price, is_market_price):
        if specification and unit_price is not None:
            return f"{specification} NT$ {int(unit_price)}"
        if is_market_price:
            return menu_item.get("display_price_label") or "時價"
        return menu_item.get("display_price_label") or f"NT$ {int(unit_price or 0)}"

    @staticmethod
    def _build_summary(request_data):
        parts = [f"{request_data['party_size']} 人"]
        if request_data["budget"]:
            parts.append(f"預算 NT$ {request_data['budget']:,}")
        parts.extend(request_data["preferences"][:3])
        parts.extend(request_data["dietary_needs"][:2])
        return "｜".join(parts)

    @classmethod
    def _recommendation_terms(cls, request_data):
        text = " ".join(
            request_data["preferences"]
            + request_data["dietary_needs"]
            + [request_data["message"]]
        )
        return [
            term[: cls.MAX_LIST_TEXT_LENGTH]
            for term in text.replace("，", " ").replace("、", " ").split()
            if term.strip()
        ][: cls.MAX_LIST_ITEMS]

    @staticmethod
    def _mock_score(item, terms):
        haystack = " ".join(
            str(value or "")
            for value in (
                item.get("name"),
                item.get("category_name"),
                item.get("description"),
                item.get("display_price_label"),
            )
        )
        score = sum(3 for term in terms if term and term in haystack)
        if item.get("price_options"):
            score += 1
        if item.get("is_market_price"):
            score -= 2
        return score

    @classmethod
    def _default_specification(cls, item):
        options = item.get("price_options") or []
        if not options:
            return ""
        middle_index = len(options) // 2
        return options[middle_index].get("specification") or ""

    @staticmethod
    def _mock_reason(item, terms):
        for term in terms:
            haystack = " ".join(
                str(value or "")
                for value in (item.get("name"), item.get("category_name"), item.get("description"))
            )
            if term and term in haystack:
                return f"符合「{term}」需求，且為目前菜單可點品項。"
        return "符合人數與預算搭配，且為目前菜單可點品項。"
