from app.services.locale_geo import haversine_m, resolve_lang


def test_resolve_lang_query_wins():
    assert resolve_lang("uz", "ru,en") == "uz"


def test_resolve_lang_accept_language_weights():
    assert resolve_lang(None, "fr;q=0.9,ru;q=0.8,en;q=0.5") == "ru"
    assert resolve_lang(None, "en-US,en;q=0.9") == "en"


def test_resolve_lang_karakalpak_alias_and_default():
    assert resolve_lang(None, "qq") == "kaa"
    assert resolve_lang(None, "de") == "en"
    assert resolve_lang("zz", None) == "en"


def test_haversine_known_distance():
    # Nukus -> Mizdakhan is roughly 40 km
    d = haversine_m(42.4617, 59.6166, 42.2300, 59.8800)
    assert 30_000 < d < 45_000


def test_catalog_languages(client):
    r = client.get("/api/v1/languages")
    assert r.json()["supported"] == ["kaa", "uz", "ru", "en"]


def test_places_language_and_fallback(client, seed):
    r = client.get("/api/v1/places?lang=ru")
    by_slug = {p["slug"]: p for p in r.json()}
    assert by_slug["savitsky-museum"]["title"] == "Музей Савицкого"
    assert by_slug["mizdakhan"]["title"] == "Mizdakhan"  # no ru -> falls back to en
    assert by_slug["mizdakhan"]["lang"] == "en"


def test_places_nearby_sorted_and_radius(client, seed):
    r = client.get("/api/v1/places?lat=42.46&lng=59.61&radius_km=10")
    assert [p["slug"] for p in r.json()] == ["savitsky-museum"]
    r = client.get("/api/v1/places?lat=42.46&lng=59.61&radius_km=100")
    assert [p["slug"] for p in r.json()] == ["savitsky-museum", "mizdakhan"]


def test_places_filter_cluster_kind(client, seed):
    assert len(client.get("/api/v1/places?cluster=nukus&kind=museum").json()) == 1
    assert client.get("/api/v1/places?cluster=nowhere").json() == []


def test_place_detail_and_unpublished_hidden(client, db, seed):
    from app.models import PlaceContent

    p = seed["p1"]
    db.add(PlaceContent(place_id=p.id, lang="uz", title="Draft", body="x"))  # draft
    db.commit()
    d = client.get(f"/api/v1/places/{p.id}?lang=uz").json()
    assert d["content"]["lang"] == "en"  # draft uz is invisible, falls back
    assert d["available_langs"] == ["en", "ru"]


def test_place_404(client, seed):
    assert client.get("/api/v1/places/00000000-0000-0000-0000-000000000000").status_code == 404


def test_qr_opens_place_and_records_scan(client, seed):
    r = client.get(f"/api/v1/q/{seed['qr'].hash}?lang=en&device=d1")
    assert r.status_code == 200 and r.json()["slug"] == "savitsky-museum"
    assert client.get("/api/v1/q/unknown").status_code == 404


def test_route_detail_and_bundle(client, seed):
    rid = seed["route"].id
    d = client.get(f"/api/v1/routes/{rid}").json()
    assert d["place_ids"] == [str(seed["p1"].id), str(seed["p2"].id)]
    b = client.get(f"/api/v1/routes/{rid}/bundle?lang=en").json()
    assert b["total_bytes"] == 2_000_000 and not b["over_limit"]
    assert len(b["places"]) == 2
    ru = client.get(f"/api/v1/routes/{rid}/bundle?lang=ru").json()
    assert len(ru["places"]) == 1  # only published ru content
    assert ru["version"] != b["version"]
