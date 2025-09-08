from flask import Flask, render_template
from flask_wtf import CSRFProtect
from flask_talisman import Talisman
from datetime import timedelta
import toml, signal, sys, os

from logging_config import setup_logging
from auth import auth_bp, keycloak_client
from routes import routes_bp

config = toml.load("config.toml")

logging_config = config["logging"]
setup_logging(logging_config["log_level"], logging_config["log_file"])

app_config = config["app"]
session_config = app_config["session"]


def signal_handler(sig, frame):
    sys.exit(0)


app = Flask(__name__)

app.config.update({
    "SECRET_KEY": os.environ.get("SECRET_KEY", app_config["secret_key"]),
    "DEBUG": True,
    "SESSION_COOKIE_SECURE": session_config.get("session_cookie_secure", True),
    "SESSION_COOKIE_HTTPONLY": session_config.get("session_cookie_httponly", True),
    "SESSION_COOKIE_SAMESITE": session_config.get("session_cookie_samesite", "Strict"),
    "PERMANENT_SESSION_LIFETIME": timedelta(
        minutes=session_config.get("permanent_session_lifetime", 30)
    )
})

app.register_blueprint(auth_bp)
app.register_blueprint(routes_bp)


@app.errorhandler(400)
def bad_request(e):
    return render_template("400.html"), 400


@app.errorhandler(403)
def forbidden(e):
    return render_template("unauthorized.html"), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("500.html"), 500


@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error("Unhandled exception", exc_info=e)
    return render_template("500.html"), 500


@app.route("/health")
def health_check():
    return {"status": "healthy"}, 200


csrf = CSRFProtect(app)

csp = {
    "default-src": "'self'",
    "script-src": [
        "'self'",
        "https://cdn.jsdelivr.net",
        "https://cdnjs.cloudflare.com"
    ],
    "style-src": [
        "'self'",
        "'unsafe-inline'",
        "https://cdn.jsdelivr.net",
        "https://fonts.googleapis.com"
    ],
    "font-src": [
        "'self'",
        "https://fonts.gstatic.com"
    ],
    "img-src": [
        "'self'",
        "data:",
    ]
}

Talisman(
    app=app,
    content_security_policy=csp,
    force_https=True,
    session_cookie_secure=True,
    session_cookie_http_only=True,
    referrer_policy="no-referrer",
    feature_policy={
        "geolocation": "'none'",
        "camera": "'none'",
        "microphone": "'none'"
    }
)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    app.run()
