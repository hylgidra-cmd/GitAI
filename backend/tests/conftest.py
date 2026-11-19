import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  (register all tables)
from app.core.security import create_access_token, new_qr_hash
from app.db import Base, get_db
from app.main import app
from app.models import (
    Cluster,
    ContentStatus,
    Country,
    Place,
    PlaceContent,
    QRCode,
    Region,
    Role,
    Route,
    RoutePlace,
    User,
)
from app.services.notify import notifier


@pytest.fixture()
def session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, expire_on_commit=False)
    engine.dispose()


@pytest.fixture()
def db(session_factory):
    with session_factory() as s:
        yield s


@pytest.fixture()
def client(session_factory):
    def _get_db():
        with session_factory() as s:
            yield s

    app.dependency_overrides[get_db] = _get_db
    notifier.outbox.clear()
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture()
def make_user(db):
    def _make(role: Role = Role.tourist, email: str | None = None) -> tuple[User, dict]:
        u = User(email=email or f"{uuid.uuid4().hex[:8]}@example.com", role=role)
        db.add(u)
        db.commit()
        return u, {"Authorization": f"Bearer {create_access_token(str(u.id))}"}

    return _make


@pytest.fixture()
def seed(db):
    country = Country(code="UZ", names={"en": "Uzbekistan"})
    db.add(country)
    db.flush()
    region = Region(country_id=country.id, slug="karakalpakstan", names={"en": "Karakalpakstan"})
    db.add(region)
    db.flush()
    cluster = Cluster(region_id=region.id, slug="nukus", names={"en": "Nukus"})
    db.add(cluster)
    db.flush()
    p1 = Place(cluster_id=cluster.id, slug="savitsky-museum", kind="museum", lat=42.4617, lng=59.6166)
    p2 = Place(cluster_id=cluster.id, slug="mizdakhan", kind="fortress", lat=42.2300, lng=59.8800)
    db.add_all([p1, p2])
    db.flush()
    for p, title in ((p1, "Savitsky Museum"), (p2, "Mizdakhan")):
        db.add(PlaceContent(
            place_id=p.id, lang="en", title=title, body=f"About {title}.",
            audio_url=f"https://cdn.test/{p.slug}-en.opus", audio_size_bytes=1_000_000,
            status=ContentStatus.published, source_refs=[{"title": "Book", "license": "CC-BY"}],
        ))
    db.add(PlaceContent(
        place_id=p1.id, lang="ru", title="Музей Савицкого", body="О музее.",
        status=ContentStatus.published, source_refs=[{"title": "Book", "license": "CC-BY"}],
    ))
    qr = QRCode(place_id=p1.id, hash=new_qr_hash())
    db.add(qr)
    route = Route(cluster_id=cluster.id, slug="nukus-day", names={"en": "Nukus day"},
                  length_km=12, duration_min=180)
    db.add(route)
    db.flush()
    db.add_all([RoutePlace(route_id=route.id, place_id=p1.id, position=1),
                RoutePlace(route_id=route.id, place_id=p2.id, position=2)])
    db.commit()
    return {"cluster": cluster, "p1": p1, "p2": p2, "qr": qr, "route": route}
