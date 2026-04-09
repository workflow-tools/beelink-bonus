"""
Query API — Flask blueprint for product consumers.

Endpoints:
    GET  /api/changes/{product}  — query change log with optional filters
    GET  /api/status             — system health + watch count
    POST /api/triage/test        — manual triage test with fake diff

The API runs on :5050 and is accessible over Tailscale from the MacBook.
This is how Upskill News's assembler agent pulls classified changes.
"""

import logging
from flask import Blueprint, request, jsonify, current_app

from regwatch.log import read_changes
from regwatch.triage import triage_change

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


@api_bp.route("/changes/<product>", methods=["GET"])
def get_changes(product: str):
    """Query the change log for a specific product.

    Query params:
        since: ISO date string (e.g., '2026-04-01')
        urgency: Comma-separated urgency levels (e.g., 'P0,P1')

    Returns:
        JSON array of change entries, newest first.
    """
    config = current_app.config.get("REGWATCH")

    # Validate product exists
    if config and not config.get_product(product):
        return jsonify({"error": f"Unknown product: {product}"}), 404

    since = request.args.get("since")
    urgency_param = request.args.get("urgency", "")
    urgency_filter = [u.strip() for u in urgency_param.split(",") if u.strip()] or None

    changes = read_changes(product, since=since, urgency_filter=urgency_filter)

    return jsonify({
        "product": product,
        "count": len(changes),
        "changes": changes,
    })


@api_bp.route("/status", methods=["GET"])
def get_status():
    """System health check.

    Returns:
        JSON with watch count, product list, and service status.
    """
    config = current_app.config.get("REGWATCH")

    if not config:
        return jsonify({"status": "error", "message": "Config not loaded"}), 500

    products = list(config.products.keys())
    watches_by_product = {
        name: len(watches) for name, watches in config.get_all_watches().items()
    }

    return jsonify({
        "status": "ok",
        "version": "0.1.0",
        "products": products,
        "watches": watches_by_product,
        "total_watches": config.watch_count(),
    })


@api_bp.route("/triage/test", methods=["POST"])
def test_triage():
    """Manual triage test — send a URL + fake diff, get triage result.

    Request body (JSON):
        url: The URL to simulate a change for.
        diff_text: The diff text to triage.
        product: (optional) Product name to use for prompt context.

    Returns:
        The triage result JSON.
    """
    data = request.get_json(silent=True) or {}

    url = data.get("url", "")
    diff_text = data.get("diff_text", "")
    product = data.get("product", "")

    if not url or not diff_text:
        return jsonify({"error": "url and diff_text are required"}), 400

    config = current_app.config.get("REGWATCH")

    # Try to find a matching watch config, or build a minimal one
    watch_config = None
    prompt_config = None

    if config:
        watch_config = config.get_watch_by_url(url)
        if product:
            prompt_config = config.get_prompt(product)

    if not watch_config:
        watch_config = {
            "url": url,
            "context": {
                "product": product or "test",
                "corridors": [],
                "likely_steps": [],
                "likely_fields": [],
                "note": "Manual triage test",
            },
        }

    try:
        result = triage_change(
            url=url,
            diff_text=diff_text,
            watch_config=watch_config,
            prompt_config=prompt_config,
        )
        return jsonify({"status": "ok", "triage": result})
    except Exception as e:
        logger.error(f"Test triage failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
