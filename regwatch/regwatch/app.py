"""
Flask application — webhook receiver + API mount point.

This is the main entry point for the RegWatch orchestrator.
It receives webhooks from changedetection.io, orchestrates the
triage pipeline, and mounts the query API for product consumers.

Endpoints:
    POST /webhook              — changedetection.io webhook receiver
    GET  /api/changes/{product} — query change log (see api.py)
    GET  /api/status           — system health check (see api.py)
    POST /api/triage/test      — manual triage test (see api.py)
"""

import logging
from flask import Flask, request, jsonify

from regwatch.config import load_config
from regwatch.triage import triage_change
from regwatch.notify import route_notification
from regwatch.log import append_change, is_duplicate
from regwatch.api import api_bp

logger = logging.getLogger(__name__)


def create_app(config_dir: str = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_dir: Path to configuration directory containing domains.yaml,
                    watches/, and prompts/. Defaults to parent of this package.

    Returns:
        Configured Flask app instance.
    """
    app = Flask(__name__)

    # Load YAML configuration
    config = load_config(config_dir)
    app.config["REGWATCH"] = config

    # Register API blueprint
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.route("/webhook", methods=["POST"])
    def webhook():
        """Receive a change notification from changedetection.io.

        Expected payload (changedetection.io webhook format):
            - url: The URL that changed
            - watch_uuid: changedetection.io watch ID
            - current_snapshot: Current page text
            - previous_snapshot: Previous page text (if available)
            - diff: Text diff of the change
        """
        payload = request.get_json(silent=True) or {}

        url = payload.get("url", "")
        diff_text = payload.get("diff", "")
        watch_uuid = payload.get("watch_uuid", "")

        if not url:
            logger.warning("Webhook received with no URL")
            return jsonify({"error": "missing url"}), 400

        # Find matching watch config
        watch = config.get_watch_by_url(url)
        if not watch:
            logger.info(f"No watch config for URL: {url}")
            return jsonify({"status": "ignored", "reason": "no matching watch"}), 200

        # Deduplicate
        if is_duplicate(url, diff_text):
            logger.info(f"Duplicate webhook for {url}, skipping")
            return jsonify({"status": "skipped", "reason": "duplicate"}), 200

        # Triage via Ollama
        try:
            triage_result = triage_change(
                url=url,
                diff_text=diff_text,
                watch_config=watch,
                prompt_config=config.get_prompt(watch["context"]["product"]),
            )
        except Exception as e:
            logger.error(f"Triage failed for {url}: {e}")
            # Rule 6: No silent failures — log and send fallback notification
            route_notification(
                product=watch["context"]["product"],
                triage_result={"error": str(e), "url": url},
                product_config=config.get_product(watch["context"]["product"]),
                is_error=True,
            )
            return jsonify({"status": "error", "message": str(e)}), 500

        # Log to JSONL
        append_change(
            product=watch["context"]["product"],
            url=url,
            triage_result=triage_result,
            watch_uuid=watch_uuid,
        )

        # Route notification based on urgency
        route_notification(
            product=watch["context"]["product"],
            triage_result=triage_result,
            product_config=config.get_product(watch["context"]["product"]),
        )

        return jsonify({"status": "processed", "triage": triage_result}), 200

    @app.route("/health", methods=["GET"])
    def health():
        """Simple health check endpoint."""
        return jsonify({"status": "ok", "version": "0.1.0"}), 200

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.run(host="0.0.0.0", port=5050, debug=False)
