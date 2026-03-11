import os
import sys
import signal
import time
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from src_python.config import config
from src_python.logger import logger
from src_python.database import init_database, close_database
from src_python.routes.patients import patients_bp
from src_python.routes.call_logs import call_logs_bp
from src_python.routes.vapi_webhook import vapi_webhook_bp

_start_time = time.time()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "src", "public"),
        static_url_path="",
    )
    app.url_map.strict_slashes = False

    # ─── CORS ───────────────────────────────────────────────────────────────────
    CORS(app)

    # ─── Rate Limiting ──────────────────────────────────────────────────────────
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[],
        storage_uri="memory://",
    )
    limiter.limit("100 per 15 minutes")(patients_bp)

    # ─── Register Blueprints ────────────────────────────────────────────────────
    app.register_blueprint(patients_bp, url_prefix="/patients")
    app.register_blueprint(call_logs_bp, url_prefix="/call-logs")
    app.register_blueprint(vapi_webhook_bp, url_prefix="/vapi")

    # ─── Health Check ───────────────────────────────────────────────────────────
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "uptime": round(time.time() - _start_time, 2),
            "version": "1.0.0",
        }), 200

    # ─── Serve Dashboard (static index.html) ────────────────────────────────────
    @app.route("/", methods=["GET"])
    def index():
        return send_from_directory(app.static_folder, "index.html")

    # ─── 404 Handler ────────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    # ─── Global Error Handler ───────────────────────────────────────────────────
    @app.errorhandler(500)
    def internal_error(e):
        logger.error(f"Unhandled error: {e}", exc_info=True)
        msg = "Internal server error" if config["env"] == "production" else str(e)
        return jsonify({"error": msg}), 500

    # ─── Request Logging ────────────────────────────────────────────────────────
    @app.after_request
    def log_request(response):
        logger.info(
            f'{request.remote_addr} - "{request.method} {request.path} HTTP/1.1" {response.status_code}'
        )
        return response

    return app



def start_server():
    """Initialize database and start the Flask server."""
    # Initialize database
    init_database()

    port = config["port"]
    env = config["env"]

    logger.info(f"Server running on port {port}")
    logger.info(f"Dashboard: http://localhost:{port}")
    logger.info(f"API Base: http://localhost:{port}")
    logger.info(f"Vapi Webhook: http://localhost:{port}/vapi/webhook")
    logger.info(f"Environment: {env}")

    app = create_app()

    # Graceful shutdown
    def shutdown_handler(signum, frame):
        sig_name = "SIGTERM" if signum == signal.SIGTERM else "SIGINT"
        logger.info(f"{sig_name} received. Shutting down gracefully...")
        close_database()
        logger.info("Server closed")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    app.run(host="0.0.0.0", port=port, debug=(env == "development"))


if __name__ == "__main__":
    start_server()
