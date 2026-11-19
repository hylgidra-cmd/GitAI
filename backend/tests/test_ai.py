from app.models import Role

P = "/api/v1"
DEV = {"X-Device-Id": "device-1"}
HISTORY = ("The Savitsky Museum in Nukus holds a collection of avant-garde art. "
           "It was founded in 1966 by Igor Savitsky in Karakalpakstan.")


def _add_source(client, admin, place_id, lang="en", verify=True, license="CC-BY", text=HISTORY):
    r = client.post(f"{P}/admin/sources", headers=admin, json={
        "title": "Museum guide", "license": license, "lang": lang,
        "place_id": str(place_id), "text": text})
    assert r.status_code == 201
    sid = r.json()["id"]
    if verify:
        assert client.post(f"{P}/admin/sources/{sid}/verify", headers=admin).status_code == 200
    return sid


def test_grounded_answer_with_citation(client, make_user, seed):
    _, admin = make_user(Role.admin)
    sid = _add_source(client, admin, seed["p1"].id)
    r = client.post(f"{P}/ai/chat", headers=DEV, json={
        "question": "Who founded the Savitsky Museum and when?",
        "place_id": str(seed["p1"].id), "lang": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is True and "1966" in body["answer"]
    assert body["citations"][0]["source_id"] == sid
    assert body["remaining_today"] == 9


def test_refuses_when_not_in_knowledge_base(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _add_source(client, admin, seed["p1"].id)
    r = client.post(f"{P}/ai/chat?lang=en", headers=DEV, json={
        "question": "What is the capital of Australia?", "place_id": str(seed["p1"].id)})
    assert r.json()["grounded"] is False and r.json()["citations"] == []
    assert "don't know" in r.json()["answer"].lower()


def test_refusal_is_localized(client, seed):
    r = client.post(f"{P}/ai/chat?lang=ru", headers=DEV, json={"question": "Что здесь?"})
    assert r.json()["grounded"] is False and "Не знаю" in r.json()["answer"]
    r = client.post(f"{P}/ai/chat?lang=uz", headers=DEV, json={"question": "Bu nima?"})
    assert "Bilmayman" in r.json()["answer"]


def test_unverified_source_is_ignored(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _add_source(client, admin, seed["p1"].id, verify=False)
    r = client.post(f"{P}/ai/chat?lang=en", headers=DEV, json={
        "question": "Who founded the Savitsky Museum?", "place_id": str(seed["p1"].id)})
    assert r.json()["grounded"] is False


def test_verify_requires_license_and_reviewer_role(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _, cm = make_user(Role.content_manager)
    sid = _add_source(client, admin, seed["p1"].id, verify=False, license="")
    assert client.post(f"{P}/admin/sources/{sid}/verify", headers=admin).status_code == 422
    assert client.post(f"{P}/admin/sources/{sid}/verify", headers=cm).status_code == 403


def test_language_isolation(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _add_source(client, admin, seed["p1"].id, lang="en")
    r = client.post(f"{P}/ai/chat?lang=ru", headers=DEV, json={
        "question": "Who founded the Savitsky Museum?", "place_id": str(seed["p1"].id)})
    assert r.json()["grounded"] is False  # no verified ru source


def test_anonymous_daily_limit_and_registered_higher(client, make_user, seed):
    for i in range(10):
        assert client.post(f"{P}/ai/chat", headers=DEV, json={"question": f"question {i}?"}).status_code == 200
    assert client.post(f"{P}/ai/chat", headers=DEV, json={"question": "one more?"}).status_code == 429
    # a different device is independent
    assert client.post(f"{P}/ai/chat", headers={"X-Device-Id": "other"},
                       json={"question": "hello there"}).status_code == 200
    # registered users get the higher limit on the same device
    _, auth = make_user(Role.tourist)
    r = client.post(f"{P}/ai/chat", headers={**DEV, **auth}, json={"question": "registered?"})
    assert r.status_code == 200 and r.json()["remaining_today"] == 29


def test_kill_switch_and_setting_limit(client, make_user, seed):
    _, admin = make_user(Role.admin)
    assert client.put(f"{P}/admin/settings/ai_enabled", headers=admin,
                      json={"value": False}).status_code == 200
    assert client.post(f"{P}/ai/chat", headers=DEV, json={"question": "anything?"}).status_code == 503
    client.put(f"{P}/admin/settings/ai_enabled", headers=admin, json={"value": True})
    client.put(f"{P}/admin/settings/ai_limit_anonymous", headers=admin, json={"value": 1})
    assert client.post(f"{P}/ai/chat", headers=DEV, json={"question": "first one"}).status_code == 200
    assert client.post(f"{P}/ai/chat", headers=DEV, json={"question": "second one"}).status_code == 429
    assert client.put(f"{P}/admin/settings/jwt_secret", headers=admin,
                      json={"value": "x"}).status_code == 404


def test_budget_hard_stop(client, make_user, db, seed):
    from app.models import AIMessage, AISession

    _, admin = make_user(Role.admin)
    client.put(f"{P}/admin/settings/ai_daily_budget_usd", headers=admin, json={"value": 1.0})
    s = AISession(device_id="x", lang="en")
    db.add(s)
    db.flush()
    db.add(AIMessage(session_id=s.id, role="assistant", text="t", cost_usd=1.3))
    db.commit()
    assert client.post(f"{P}/ai/chat", headers=DEV, json={"question": "anything?"}).status_code == 503


def test_feedback_only_by_same_device(client, seed):
    mid = client.post(f"{P}/ai/chat", headers=DEV, json={"question": "hello?"}).json()["message_id"]
    ok = client.post(f"{P}/ai/messages/{mid}/feedback", headers=DEV,
                     json={"feedback": "not_helpful", "error_report": "wrong"})
    assert ok.status_code == 204
    other = client.post(f"{P}/ai/messages/{mid}/feedback", headers={"X-Device-Id": "evil"},
                        json={"feedback": "helpful"})
    assert other.status_code == 404
    assert client.post(f"{P}/ai/messages/{mid}/feedback", headers=DEV,
                       json={"feedback": "bogus"}).status_code == 422


def test_device_header_required_and_unknown_place(client):
    assert client.post(f"{P}/ai/chat", json={"question": "hello?"}).status_code == 400
    r = client.post(f"{P}/ai/chat", headers=DEV, json={
        "question": "hello?", "place_id": "00000000-0000-0000-0000-000000000000"})
    assert r.status_code == 404


def test_chunking_and_number_postcheck():
    from app.services.rag import _numbers, chunk_text

    chunks = chunk_text("\n\n".join(["a" * 400, "b" * 400, "c" * 100]))
    assert len(chunks) == 2
    assert _numbers("founded in 1966 by 2 people") == {"1966", "2"}


def test_chat_sse_stream(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _add_source(client, admin, seed["p1"].id)
    r = client.post(
        f"{P}/ai/chat?stream=true",
        headers=DEV,
        json={"question": "Who founded the Savitsky Museum?", "place_id": str(seed["p1"].id), "lang": "en"},
    )
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    assert "event: done" in r.text and "1966" in r.text


def test_voice_stt_rag_tts_and_kaa_restriction(client, make_user, seed):
    _, admin = make_user(Role.admin)
    _add_source(client, admin, seed["p1"].id, lang="en")
    r = client.post(
        f"{P}/ai/voice",
        headers=DEV,
        json={"transcript_hint": "Who founded the Savitsky Museum?", "place_id": str(seed["p1"].id), "lang": "en"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["grounded"] is True and body["audio_url"].endswith(".opus")
    # By default kaa is not in voice_enabled_langs (AC-06)
    r_kaa = client.post(f"{P}/ai/voice", headers=DEV, json={"transcript_hint": "Savitsky", "lang": "kaa"})
    assert r_kaa.status_code == 422


def test_image_ocr_exif_strip_and_24h_purge(client, make_user, db, seed):
    import base64
    from datetime import timedelta
    from uuid import UUID

    from app.models import AIMediaJob
    from app.models.types import utcnow

    _, admin = make_user(Role.admin)
    _add_source(client, admin, seed["p1"].id, lang="en")
    raw_b64 = base64.b64encode(b"Savitsky Museum founded 1966").decode()
    r = client.post(
        f"{P}/ai/image",
        headers=DEV,
        json={"image_base64": raw_b64, "place_id": str(seed["p1"].id), "lang": "en"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["exif_stripped"] is True and data["grounded"] is True
    job = db.get(AIMediaJob, UUID(data["job_id"]))
    assert job is not None and job.storage_key is not None
    # Simulate 24 hours elapsed -> purge must wipe storage_key (AC-11)
    job.expires_at = utcnow() - timedelta(minutes=1)
    db.commit()
    pr = client.post(f"{P}/ai/media/purge")
    assert pr.status_code == 200 and pr.json()["purged"] == 1
    db.refresh(job)
    assert job.status == "purged" and job.storage_key is None

