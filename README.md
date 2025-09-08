# Flask App with Keycloak SSO

This project provides a minimal Flask application demonstrating Keycloak integration with role-based access control (RBAC). It includes login, logout, role-protected routes, session handling, CSRF protection, and a dark-themed minimal UI.

---

## Features

- 🔑 Single Sign-On (SSO) integration with Keycloak using `python-keycloak`
- 👥 Role-based access control (RBAC) to restrict routes to specific roles
- 🛡️ Session management with secure cookies, timeouts, and refresh token handling
- 📜 Structured logging with rotating file handlers for better observability
- 🎨 Bootstrap-based UI with a dark minimalistic layout
- 🚫 Custom error pages for unauthorized (403), bad request (400), not found (404), and server errors (500)
- ⚡ Easily extendable roles: create new roles in Keycloak, assign them to users, and protect routes with the `@required_roles` decorator
- 🧩 CSRF protection for forms
- 🕵️ Security headers via Flask-Talisman (CSP, HSTS, X-Frame-Options, XSS protection)
- 📂 Rotating file logging for debugging and monitoring

---

## Requirements

- Python 3.10+
- Docker (for running Keycloak, optional if you already have a server)

Start your Keycloak server using [Docker](https://www.keycloak.org/getting-started/getting-started-docker):

```bash
docker run -d --name keycloak_server -p 8080:8080 -e KC_BOOTSTRAP_ADMIN_USERNAME=admin -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin quay.io/keycloak/keycloak:26.3.3 start-dev
```

> Note: Keycloak may take a minute to fully start and initialize.

Create the necessary realm, client (setup endpoints needed such as the redirect URI), users and roles in Keycloak.

---

## Keycloak Setup

### 1. Configuration

An example of how I configured the client created in Keycloak is as follows:

- Realm: `master`
- Client ID: `flask_app`
- Access Settings
  - Root URL → `http://localhost:5000`
  - Home URL → `http://localhost:5000`
  - Valid Redirect URIs → `http://localhost:5000/callback`
  - Valid Post Logout Redirect URIs → `http://localhost:5000*`
  - Web Origins → `http://localhost:5000`
  - Admin URL → `http://localhost:5000`
- Capability Config
  - Client authentication → On
  - Authentication flow (enabled)
    - Direct access grants (password grant)
    - Standard flow (authentication with authorization code)
    - Service accounts roles (retrieve access token dedicated to the client)

### 2. Testing Authentication

The following `curl` command can be used to quickly confirm the Keycloak setup works before even running the app:

```shell
curl -X POST http://localhost:8080/realms/master/protocol/openid-connect/token \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET" \
  -d "grant_type=password" \
  -d "username=testuser" \
  -d "password=testpass"
```

> This example retrieves a token manually from Keycloak.

### 3. Security Notes

- Change default admin credentials immediately.
- Use HTTPS in production for Keycloak
- Limit valid redirect URIs strictly (avoid using wildcards like /\* in production).

---

## Project Setup

### 1. Virtual Environment

Install the `virtualenv` package (if not installed):

```bash
python -m pip install virtualenv
```

Create a virtual environment:

```bash
python -m venv [env_name]
```

Activate it:

```bash
# Linux / macOS
source [env_name]/bin/activate

# Windows
[env_name]/Scripts/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Edit the `config.toml` file with your Keycloak settings and app configurations, you can create it based on the `config.toml.example` file.

> Make sure the roles match what you configured in Keycloak.

Create the `.env` file based on the `.env.example` file and add your Keycloak client-id and client secret.

---

## Running the App

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

- Home page: Displays user info and roles.
- Admin page: Accessible only to users with the admin role.
- Logout: Clears the session safely.

---

## Project Structure

```php
project/
│── app.py            # Main Flask app
│── auth.py           # Authentication and token handling
│── routes.py         # Route definitions
│── logging_config.py # Logging setup
│── templates/        # HTML templates
│    ├── base.html
│    ├── home.html
│    └── admin.html
│── static/           # Static assets (CSS, JS, etc.)
│── config.toml       # App and Keycloak configuration
│── .env              # Stores client-id and client secret
│── requirements.txt
└── README.md
```

---

## Security

- CSRF protection enabled for forms.
- CSP and security headers added via Flask-Talisman.
- Sessions are HTTPOnly and can be set secure if using HTTPS.
- Role-based access uses a decorator with a 403 error page.
- Access tokens in this demo are not signature-verified for simplicity.
- For production, verify JWT signatures against Keycloak’s JWKS to ensure tokens are authentic.
- Tokens are stored in server-side session only (not in client cookies).

---

## Optional Enhancements

- Enforce HTTPS in production and set SESSION_COOKIE_SECURE=True.
- Rate-limiting for login attempts (e.g., Flask-Limiter) to avoid brute-force login attempts.
- Use refresh tokens securely and rotate them if turning this into a real application.
- Create environment variables on your system instead of using the `.env` file.
- Use environment variables only for data such as the `secret key` for the Flask app.

---

## Adding New Roles and Protecting Routes

Each route can require one or more roles to allow access.

### 1. Create a Role in Keycloak

- Go to your realm in Keycloak.
- Navigate to Realm Roles → Create Role (or on the client created, go to Roles → Create Role)
- Give it a name (e.g., manager) and description if needed and save.

### 2. Assign the Role to Users

- Navigate to Users → [Select User] → Role Mapping → Assign role (either client or relam role).
- Assign your newly created role to the user.

### 3. Add Role to config.toml

You can optionally list new roles in your configuration if working with the `.toml` file:

```toml
[roles]
admin_user = ["admin"]
manager_user = ["manager"]

```

### 4. Protect Routes in Flask

Use the `required_roles` decorator in your route:

```python
from auth import required_roles

@app.route("/manager")
@required_roles(["manager"]) # or use the `manager_user` list imported from the TOML file
def manager_dashboard():
    return render_template("manager.html")
```

> In this example, users without the `manager` role will see the unauthorized (403) page.

Multiple roles can be required:

```python
@required_roles(["admin", "manager"])
def admin_or_manager():
    ...
```

> This ensures that only users with the specified roles can access sensitive routes.

---

## Health check

There's a `/health` route which returns `200` if the app is up and running.

Containers can use this to confirm it's healthy, if it fails, Docker marks it unhealthy which is good for orchestrators like Docker Swarm or Kubernetes.

The route can be found in the `app.py` file:

```python
@app.route("/health")
def health():
    return {"status": "healthy"}, 200
```
