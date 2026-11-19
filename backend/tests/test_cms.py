from app.models import PlaceContent, Role

P = "/api/v1"


def _new_content(client, headers, place_id, **over):
    body = {"lang": "uz", "title": "Sarlavha", "body": "Matn bu yerda.",
            "source_refs": [{"title": "Kitob", "license": "CC-BY"}]}
    body.update(over)
    return client.post(f"{P}/admin/places/{place_id}/content", json=body, headers=headers)


def test_admin_endpoints_require_role(client, make_user, seed):
    _, tourist = make_user(Role.tourist)
    assert client.post(f"{P}/admin/places/{seed['p1'].id}/qr").status_code == 401
    assert client.post(f"{P}/admin/places/{seed['p1'].id}/qr", headers=tourist).status_code == 403
    assert client.get(f"{P}/admin/dashboard", headers=tourist).status_code == 403


def test_two_step_publication_flow(client, make_user, seed):
    _, cm = make_user(Role.content_manager)
    _, editor = make_user(Role.editor)
    pid = seed["p1"].id
    cid = _new_content(client, cm, pid).json()["id"]

    # not visible until published
    assert "uz" not in client.get(f"{P}/places/{pid}").json()["available_langs"]

    assert client.post(f"{P}/admin/content/{cid}/transition",
                       json={"target": "in_review"}, headers=cm).status_code == 200
    # content manager cannot publish; editor can
    assert client.post(f"{P}/admin/content/{cid}/transition",
                       json={"target": "published"}, headers=cm).status_code == 403
    assert client.post(f"{P}/admin/content/{cid}/transition",
                       json={"target": "published"}, headers=editor).status_code == 200
    assert "uz" in client.get(f"{P}/places/{pid}").json()["available_langs"]


def test_cannot_skip_review(client, make_user, seed):
    _, editor = make_user(Role.editor)
    cid = _new_content(client, editor, seed["p1"].id).json()["id"]
    r = client.post(f"{P}/admin/content/{cid}/transition", json={"target": "published"},
                    headers=editor)
    assert r.status_code == 409


def test_publish_requires_license(client, make_user, seed):
    _, editor = make_user(Role.editor)
    cid = _new_content(client, editor, seed["p1"].id,
                       source_refs=[{"title": "Kitob"}]).json()["id"]
    client.post(f"{P}/admin/content/{cid}/transition", json={"target": "in_review"}, headers=editor)
    r = client.post(f"{P}/admin/content/{cid}/transition", json={"target": "published"},
                    headers=editor)
    assert r.status_code == 422 and r.json()["detail"] == "source_license_required"


def test_published_is_immutable_new_version(client, make_user, db, seed):
    _, admin = make_user(Role.admin)
    en = db.query(PlaceContent).filter_by(place_id=seed["p1"].id, lang="en").one()
    body = {"lang": "en", "title": "T", "body": "B"}
    assert client.put(f"{P}/admin/content/{en.id}", json=body, headers=admin).status_code == 409
    r = _new_content(client, admin, seed["p1"].id, lang="en")
    assert r.json()["version"] == 2


def test_unsupported_language_rejected(client, make_user, seed):
    _, admin = make_user(Role.admin)
    assert _new_content(client, admin, seed["p1"].id, lang="de").status_code == 422


def test_editing_in_review_resets_to_draft(client, make_user, db, seed):
    _, editor = make_user(Role.editor)
    cid = _new_content(client, editor, seed["p1"].id).json()["id"]
    client.post(f"{P}/admin/content/{cid}/transition", json={"target": "in_review"}, headers=editor)
    r = client.put(f"{P}/admin/content/{cid}",
                   json={"lang": "uz", "title": "Yangi", "body": "Yangi matn"}, headers=editor)
    assert r.json()["status"] == "draft"


def test_create_place_qr_and_slug_conflict(client, make_user, seed):
    _, cm = make_user(Role.content_manager)
    body = {"cluster_id": str(seed["cluster"].id), "slug": "ayaz-kala", "kind": "fortress",
            "lat": 41.8, "lng": 60.4, "geofence_radius_m": 80}
    r = client.post(f"{P}/admin/places", json=body, headers=cm)
    assert r.status_code == 201
    assert client.post(f"{P}/admin/places", json=body, headers=cm).status_code == 409
    qr = client.post(f"{P}/admin/places/{r.json()['id']}/qr", headers=cm).json()
    assert qr["path"] == f"/q/{qr['hash']}"
    assert client.post(f"{P}/admin/places", headers=cm,
                       json={**body, "slug": "x", "geofence_radius_m": 500}).status_code == 422


def test_audit_log_and_dashboard(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _new_content(client, admin, seed["p1"].id)
    log = client.get(f"{P}/admin/audit", headers=admin).json()
    assert log[0]["action"] == "create" and log[0]["entity"] == "content"
    dash = client.get(f"{P}/admin/dashboard", headers=admin).json()
    assert dash["ai_enabled"] is True and dash["ai_cost_today_usd"] == 0


def test_narrator_audio_and_tts_draft_blocks_kaa(client, make_user, seed):
    _, cm = make_user(Role.content_manager)
    pid = seed["p1"].id
    uz_id = _new_content(client, cm, pid, lang="uz", body="Birinchi abzas.\n\nIkkinchi abzas.").json()["id"]
    tts_r = client.post(f"{P}/admin/content/{uz_id}/tts", headers=cm)
    assert tts_r.status_code == 200 and tts_r.json()["is_tts"] is True

    kaa_id = _new_content(client, cm, pid, lang="kaa", body="Qaraqalpaqsha tekst.").json()["id"]
    # CM-03: TTS draft is forbidden for Karakalpak by default
    assert client.post(f"{P}/admin/content/{kaa_id}/tts", headers=cm).status_code == 422
    # CM-02: Narrator recording works for Karakalpak and normalizes to -16 LUFS
    nar = client.post(
        f"{P}/admin/content/{kaa_id}/audio",
        headers=cm,
        json={"audio_url": "https://cdn.test/kaa-1.opus", "size_bytes": 500_000, "duration_s": 120},
    )
    assert nar.status_code == 200 and nar.json()["loudness_lufs"] == -16.0

    stand = client.get(f"{P}/admin/places/{pid}/qr/stand", headers=cm)
    assert stand.status_code == 200 and stand.json()["stand_layout"]["format"] == "A4"

