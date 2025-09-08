from flask import Blueprint, redirect, url_for, session, request, abort
from keycloak import KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError
from functools import wraps
from datetime import datetime, timezone
from dotenv import load_dotenv
import uuid, toml, jwt, os

load_dotenv(".env")

config = toml.load("config.toml")
keycloak_config = config["keycloak"]

admin_roles = keycloak_config["roles"]["admin_user"]

SERVER_URL = keycloak_config["server_url"]
REALM = keycloak_config["realm"]
REDIRECT_URI = keycloak_config["redirect_uri"]

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

if not CLIENT_ID or not CLIENT_SECRET:
    raise RuntimeError("CLIENT_ID or CLIENT_SECRET not set as environment variables.")

keycloak_client = KeycloakOpenID(
    server_url=SERVER_URL,
    client_id=CLIENT_ID,
    client_secret_key=CLIENT_SECRET,
    realm_name=REALM,
    verify=True
)

print(f"[auth] Keycloak client configured for realm '{REALM}' at '{SERVER_URL}' with client ID '{CLIENT_ID}'")

auth_bp = Blueprint("auth", __name__)


def required_roles(required_roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session:
                return redirect(url_for("auth.login"))

            user_roles = session["user"].get("roles", [])
            if any(role in user_roles for role in required_roles):
                return f(*args, **kwargs)
            else:
                return abort(403)
        return decorated_function
    return wrapper


def refresh_access_token():
    if "user" not in session or "refresh_token" not in session["user"]:
        return False
    
    refresh_token = session["user"]["refresh_token"]

    try:
        token = keycloak_client.refresh_token(refresh_token)

        session["user"]["refresh_token"] = token.get("refresh_token")
        session["user"]["access_token"] = token.get("access_token")
        
        return True

    except Exception:
        session.clear()

        return False


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth.login"))
        
        access_token = session["user"].get("access_token")

        if access_token:
            decoded = jwt.decode(jwt=access_token, options={"verify_signature": False})
            exp = datetime.fromtimestamp(decoded["exp"], timezone.utc)

            if datetime.now(timezone.utc) > exp and not refresh_access_token():
                return redirect(url_for("auth.login"))
        else:
            return redirect(url_for("auth.login"))
        
        return f(*args, **kwargs)
    return decorated_function


@auth_bp.route("/login", methods=["GET"])
def login():
    state = str(uuid.uuid4())
    session["oauth_state"] = state

    auth_url = keycloak_client.auth_url(
        redirect_uri=REDIRECT_URI,
        scope="openid profile email",
        state=state
    )

    return redirect(auth_url)

@auth_bp.route("/callback")
def callback():
    code = request.args.get("code")
    state = request.args.get("state")

    if not code:
        return "Error: No code received.", 400

    if state != session.get("oauth_state"):
        return abort(400, "Invalid state parameter")

    try:
        token = keycloak_client.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri=REDIRECT_URI
        )

        if "access_token" not in token:
            return "Failed to fetch tokens, no access token found.", 400

        userinfo = keycloak_client.userinfo(token["access_token"])
        token_info = keycloak_client.introspect(token["access_token"])
        roles = token_info.get("realm_access", {}).get("roles", [])

        session["user"] = {
            "name": userinfo.get("name"),
            "email": userinfo.get("email"),
            "roles": roles,
            "access_token": token.get("access_token"),
            "refresh_token": token.get("refresh_token")
        }

        return redirect(url_for("routes.index"))

    except KeycloakAuthenticationError as e:
        return f"Authentication failed with Keycloak: {e}", 401
    except Exception:
        return "Unexpected error during login.", 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    try:
        if "user" in session:
            keycloak_client.logout(session["user"]["refresh_token"])

        session.clear()

        return redirect(url_for("auth.login"))
    except Exception:
        return "Failed to logout. Please try again.", 500
