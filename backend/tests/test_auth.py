"""
Auth tests — register, login, token validation.

Note: register/login endpoints don't use get_current_user, so the `client`
fixture (which overrides both get_db AND get_current_user) works fine here.
The get_current_user override simply won't be triggered.
"""

from passlib.context import CryptContext
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ─── Register ─────────────────────────────────────────────────────────────────

def test_register_new_user_returns_token(client, mock_db):
    mock_db.set("users", [])
    mock_db.set("profiles", [])
    r = client.post("/api/auth/register", json={"username": "alice", "password": "pass123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_username_returns_400(client, mock_db):
    mock_db.set("users", [{"id": "x", "username": "alice"}])
    r = client.post("/api/auth/register", json={"username": "alice", "password": "pass"})
    assert r.status_code == 400
    assert "already taken" in r.json()["detail"]


# ─── Login ────────────────────────────────────────────────────────────────────

def test_login_correct_credentials_returns_token(client, mock_db):
    hashed = _pwd.hash("secret")
    mock_db.set("users", [{"id": "u1", "username": "dev", "password_hash": hashed}])
    r = client.post("/api/auth/login", json={"username": "dev", "password": "secret"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_wrong_password_returns_401(client, mock_db):
    hashed = _pwd.hash("correct")
    mock_db.set("users", [{"id": "u1", "username": "dev", "password_hash": hashed}])
    r = client.post("/api/auth/login", json={"username": "dev", "password": "wrong"})
    assert r.status_code == 401


def test_login_unknown_user_returns_401(client, mock_db):
    mock_db.set("users", [])
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "p"})
    assert r.status_code == 401


# ─── Protected route guard ────────────────────────────────────────────────────

def test_protected_route_without_token_is_rejected():
    """HTTPBearer returns 403 when Authorization header is absent."""
    app.dependency_overrides.clear()
    with TestClient(app) as c:
        r = c.get("/api/applications")
    assert r.status_code in (401, 403)
