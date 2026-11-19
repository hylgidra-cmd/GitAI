from datetime import timedelta
from uuid import UUID

from app.models import BookingRequest, Role
from app.models.types import utcnow
from app.services.notify import notifier

P = "/api/v1"
PROFILE = {"display_name": "Aziz", "languages": ["en", "uz"], "specialties": ["aral"],
           "has_4x4": True, "price_from_usd": 50}


def _approved_guide(client, make_user, db_admin_headers):
    guser, gh = make_user(Role.tourist, "guide@example.com")
    r = client.put(f"{P}/guides/me", json=PROFILE, headers=gh)
    assert r.status_code == 200
    gid = r.json()["id"]
    assert client.patch(f"{P}/admin/guides/{gid}/status", json={"status": "approved"},
                        headers=db_admin_headers).status_code == 200
    return guser, gh, gid


def _dates(days=5):
    d = utcnow().date() + timedelta(days=days)
    return {"date_from": str(d), "date_to": str(d + timedelta(days=2)), "group_size": 3}


def test_guide_hidden_until_approved_and_role_set(client, make_user):
    _, admin = make_user(Role.admin)
    guser, gh = make_user(Role.tourist)
    r = client.put(f"{P}/guides/me", json=PROFILE, headers=gh)
    assert r.json()["status"] == "pending"
    gid = r.json()["id"]
    assert client.get(f"{P}/guides").json() == []
    assert client.get(f"{P}/guides/{gid}").status_code == 404
    assert client.get(f"{P}/auth/me", headers=gh).json()["role"] == "guide"
    assert len(client.get(f"{P}/admin/guides", headers=admin).json()) == 1
    client.patch(f"{P}/admin/guides/{gid}/status", json={"status": "approved"}, headers=admin)
    assert len(client.get(f"{P}/guides").json()) == 1


def test_guide_filters(client, make_user):
    _, admin = make_user(Role.admin)
    _approved_guide(client, make_user, admin)
    assert len(client.get(f"{P}/guides?lang=uz").json()) == 1
    assert client.get(f"{P}/guides?lang=ru").json() == []
    assert len(client.get(f"{P}/guides?specialty=aral&has_4x4=true&max_price=60").json()) == 1
    assert client.get(f"{P}/guides?max_price=10").json() == []


def test_profile_validation(client, make_user):
    _, gh = make_user()
    bad = {**PROFILE, "languages": ["xx"]}
    assert client.put(f"{P}/guides/me", json=bad, headers=gh).status_code == 422
    assert client.put(f"{P}/guides/me", json={**PROFILE, "languages": []}, headers=gh).status_code == 422
    assert client.put(f"{P}/guides/me", json=PROFILE).status_code == 401


def test_edit_after_approval_requires_remoderation(client, make_user):
    _, admin = make_user(Role.admin)
    _, gh, gid = _approved_guide(client, make_user, admin)
    r = client.put(f"{P}/guides/me", json={**PROFILE, "bio": "new"}, headers=gh)
    assert r.json()["status"] == "pending"
    assert client.get(f"{P}/guides").json() == []


def test_documents_metadata(client, make_user):
    _, gh = make_user()
    assert client.post(f"{P}/guides/me/documents", headers=gh,
                       json={"kind": "id_card", "storage_key": "k"}).status_code == 404
    client.put(f"{P}/guides/me", json=PROFILE, headers=gh)
    assert client.post(f"{P}/guides/me/documents", headers=gh,
                       json={"kind": "guide_license", "storage_key": "private/1.pdf"}).status_code == 201
    assert client.post(f"{P}/guides/me/documents", headers=gh,
                       json={"kind": "selfie", "storage_key": "k"}).status_code == 422


def test_request_flow_notifies_and_guide_decides(client, make_user):
    _, admin = make_user(Role.admin)
    _, gh, gid = _approved_guide(client, make_user, admin)
    tuser, th = make_user(Role.tourist, "tourist@example.com")
    notifier.outbox.clear()
    r = client.post(f"{P}/guides/{gid}/requests", json=_dates(), headers=th)
    assert r.status_code == 201 and r.json()["status"] == "pending"
    assert any(m["to"] == "guide@example.com" for m in notifier.outbox)
    rid = r.json()["id"]
    assert len(client.get(f"{P}/requests/incoming", headers=gh).json()) == 1
    assert len(client.get(f"{P}/requests/mine", headers=th).json()) == 1

    # tourist cannot decide; guide can, only once
    assert client.patch(f"{P}/requests/{rid}", json={"status": "accepted"}, headers=th).status_code == 403
    assert client.patch(f"{P}/requests/{rid}", json={"status": "pending"}, headers=gh).status_code == 422
    ok = client.patch(f"{P}/requests/{rid}", json={"status": "accepted"}, headers=gh)
    assert ok.status_code == 200 and ok.json()["status"] == "accepted"
    assert client.patch(f"{P}/requests/{rid}", json={"status": "declined"}, headers=gh).status_code == 409
    assert any(m["to"] == "tourist@example.com" for m in notifier.outbox)


def test_telegram_notification_when_chat_linked(client, make_user, db):
    _, admin = make_user(Role.admin)
    guser, gh, gid = _approved_guide(client, make_user, admin)
    guser.telegram_chat_id = "12345"
    db.merge(guser)
    db.commit()
    _, th = make_user()
    client.post(f"{P}/guides/{gid}/requests", json=_dates(), headers=th)
    assert any(m["channel"] == "telegram" and m["to"] == "12345" for m in notifier.outbox)


def test_request_validation(client, make_user):
    _, admin = make_user(Role.admin)
    guser, gh, gid = _approved_guide(client, make_user, admin)
    _, th = make_user()
    past = {"date_from": str(utcnow().date() - timedelta(days=1)),
            "date_to": str(utcnow().date()), "group_size": 2}
    assert client.post(f"{P}/guides/{gid}/requests", json=past, headers=th).status_code == 422
    inverted = {**_dates(), "date_to": str(utcnow().date())}
    assert client.post(f"{P}/guides/{gid}/requests", json=inverted, headers=th).status_code == 422
    assert client.post(f"{P}/guides/{gid}/requests", json=_dates()).status_code == 401
    assert client.post(f"{P}/guides/{gid}/requests", json=_dates(), headers=gh).status_code == 409
    assert client.post(f"{P}/guides/{gid}/requests", json={**_dates(), "group_size": 0},
                       headers=th).status_code == 422


def test_request_to_unapproved_guide_rejected(client, make_user):
    _, gh = make_user()
    gid = client.put(f"{P}/guides/me", json=PROFILE, headers=gh).json()["id"]
    _, th = make_user()
    assert client.post(f"{P}/guides/{gid}/requests", json=_dates(), headers=th).status_code == 404


def test_overdue_request_expires(client, make_user, db):
    _, admin = make_user(Role.admin)
    _, gh, gid = _approved_guide(client, make_user, admin)
    _, th = make_user()
    rid = client.post(f"{P}/guides/{gid}/requests", json=_dates(), headers=th).json()["id"]
    req = db.get(BookingRequest, UUID(rid))
    req.respond_by = utcnow() - timedelta(hours=1)
    db.commit()
    r = client.patch(f"{P}/requests/{rid}", json={"status": "accepted"}, headers=gh)
    assert r.status_code == 409 and r.json()["detail"] == "request_expired"
    assert client.get(f"{P}/requests/mine", headers=th).json()[0]["status"] == "expired"


def test_guide_documents_require_signed_url(client, make_user):
    _, admin = make_user(Role.admin)
    _, gh, gid = _approved_guide(client, make_user, admin)
    doc = client.post(
        f"{P}/guides/me/documents",
        headers=gh,
        json={"kind": "guide_license", "storage_key": "private/lic.pdf"},
    ).json()
    # Direct access without signature is forbidden (AC-09)
    assert client.get(f"{P}/files/documents/{doc['id']}").status_code == 403
    assert client.get(f"{P}/files/documents/{doc['id']}?expires=9999999999&sig=bad").status_code == 403
    # Admin obtains signed URL -> valid access
    docs = client.get(f"{P}/admin/guides/{gid}/documents", headers=admin).json()
    assert len(docs) == 1
    ok = client.get(docs[0]["signed_url"])
    assert ok.status_code == 200 and ok.json()["storage_key"] == "private/lic.pdf"

