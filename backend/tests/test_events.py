from app.models import Event, Role

P = "/api/v1"


def test_events_accepted_filtered_and_scrubbed(client, db, make_user):
    r = client.post(f"{P}/events", json={"device_id": "d1", "events": [
        {"name": "audio_play", "props": {"place_id": "p", "email": "x@y.z", "lat": 1.0}},
        {"name": "not_an_event", "props": {}},
    ]})
    assert r.status_code == 202 and r.json()["accepted"] == 1
    ev = db.query(Event).one()
    assert ev.props == {"place_id": "p"}  # personal keys stripped


def test_events_batch_limit(client):
    evs = [{"name": "place_view"}] * 101
    assert client.post(f"{P}/events", json={"device_id": "d", "events": evs}).status_code == 413


def test_dashboard_counts_events(client, make_user):
    _, admin = make_user(Role.admin)
    client.post(f"{P}/events", json={"device_id": "d", "events": [
        {"name": "qr_scan"}, {"name": "qr_scan"}, {"name": "audio_complete"}]})
    d = client.get(f"{P}/admin/dashboard", headers=admin).json()
    assert d["qr_scans"] == 2 and d["audio_completes"] == 1
