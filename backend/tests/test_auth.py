import re

from app.core.config import settings
from app.services.notify import notifier


def _code_for(email: str) -> str:
    mail = [m for m in notifier.outbox if m["to"] == email][-1]
    return re.search(r"\d{6}", mail["body"]).group(0)


def test_otp_login_flow_sets_cookies_and_me(client):
    assert client.post("/api/v1/auth/otp/request", json={"email": "A@Example.com"}).status_code == 202
    r = client.post("/api/v1/auth/otp/verify",
                    json={"email": "a@example.com", "code": _code_for("a@example.com")})
    assert r.status_code == 200 and r.json()["user"]["role"] == "tourist"
    assert "httponly" in r.headers["set-cookie"].lower()
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200 and me.json()["email"] == "a@example.com"
    assert client.post("/api/v1/auth/refresh").status_code == 200
    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/auth/me").status_code == 401


def test_otp_wrong_code_and_attempt_limit(client):
    client.post("/api/v1/auth/otp/request", json={"email": "b@example.com"})
    good = _code_for("b@example.com")
    bad = "000000" if good != "000000" else "111111"
    for _ in range(settings.otp_max_attempts):
        assert client.post("/api/v1/auth/otp/verify",
                           json={"email": "b@example.com", "code": bad}).status_code == 400
    # even the right code is rejected after too many attempts
    assert client.post("/api/v1/auth/otp/verify",
                       json={"email": "b@example.com", "code": good}).status_code == 400


def test_otp_code_single_use(client):
    client.post("/api/v1/auth/otp/request", json={"email": "c@example.com"})
    code = _code_for("c@example.com")
    assert client.post("/api/v1/auth/otp/verify",
                       json={"email": "c@example.com", "code": code}).status_code == 200
    assert client.post("/api/v1/auth/otp/verify",
                       json={"email": "c@example.com", "code": code}).status_code == 400


def test_otp_request_rate_limited(client):
    assert client.post("/api/v1/auth/otp/request", json={"email": "d@example.com"}).status_code == 202
    assert client.post("/api/v1/auth/otp/request", json={"email": "d@example.com"}).status_code == 429


def test_invalid_email_and_unauthenticated(client):
    assert client.post("/api/v1/auth/otp/request", json={"email": "nope"}).status_code == 422
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/auth/me", headers={"Authorization": "Bearer junk"}).status_code == 401


def test_refresh_token_cannot_act_as_access(client, make_user):
    from app.core.security import create_refresh_token

    user, _ = make_user()
    r = client.get("/api/v1/auth/me",
                   headers={"Authorization": f"Bearer {create_refresh_token(str(user.id))}"})
    assert r.status_code == 401
