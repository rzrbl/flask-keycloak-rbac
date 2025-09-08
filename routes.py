from flask import Blueprint, render_template, session, redirect, url_for
from auth import required_roles, login_required
import toml

config = toml.load("config.toml")
keycloak_config = config["keycloak"]
admin_roles = keycloak_config["roles"]["admin_user"]

routes_bp = Blueprint("routes", __name__)


@routes_bp.route("/")
@login_required
def index():
    if "user" in session:
        data = {
            "name": session["user"]["name"],
            "email": session["user"]["email"],
            "roles": session["user"]["roles"]
        }

        return render_template("home.html", **data)

    return redirect(url_for("auth.login"))


@routes_bp.route("/admin")
@login_required
@required_roles(admin_roles)
def admin():
    return render_template("admin.html")

