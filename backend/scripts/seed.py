"""Idempotent dev seed: Uzbekistan -> Karakalpakstan -> 3 pilot clusters, 9 places,
4-language published content (kaa, uz, ru, en), routes, QR codes, verified RAG sources,
and verified local guides.

Usage:  python -m scripts.seed
"""
from sqlalchemy import select

import app.models  # noqa: F401
from app.db import SessionLocal
from app.models import (
    Cluster,
    ContentStatus,
    Country,
    GuideProfile,
    GuideStatus,
    KnowledgeSource,
    Place,
    PlaceContent,
    QRCode,
    Region,
    Role,
    Route,
    RoutePlace,
    User,
)
from app.services import rag

PLACES_DATA = [
    {
        "cluster": "nukus",
        "slug": "savitsky-museum",
        "kind": "museum",
        "lat": 42.4647,
        "lng": 59.6122,
        "qr": "savitsky01",
        "titles": {
            "kaa": "I.V. Savickiy atındaǵı Qaraqalpaqstan kórkem óner muzeyi",
            "uz": "I.V. Savitskiy nomidagi Qoraqalpog‘iston san’at muzeyi",
            "ru": "Государственный музей искусств им. И.В. Савицкого",
            "en": "Savitsky Karakalpakstan Art Museum",
        },
        "bodies": {
            "kaa": (
                "1966-jılı Igor Savickiy tárepinen shólkemlestirilgen bul muzey "
                "dúnyadaǵı eń iri rus avangardı hám Qaraqalpaq xalıq ámeliy kórkem óneri "
                "toplamlarınan birin saqlaydı.\n\n"
                "Muzey qorında 80 mıńnan aslam eksponat bar bolıp, olardıń arasında "
                "Áyyemgi Xorezm arxeologiyalıq tabılmaları hám XX ásir súwretshileriniń "
                "kem ushırasatuǵın shıǵarmaları orın alǵan."
            ),
            "uz": (
                "1966-yilda Igor Savitskiy tomonidan asos solingan ushbu muzey "
                "dunyodagi eng boy rus avangardi va Qoraqalpoq xalq amaliy san’ati "
                "kolleksiyalaridan birini o‘z ichiga oladi.\n\n"
                "Muzey fondida 80 mingdan ortiq eksponat mavjud bo‘lib, ular orasida "
                "Qadimgi Xorazm arxeologik topilmalari hamda XX asr rassomlarining noyob asarlari bor."
            ),
            "ru": (
                "Основанный в 1966 году Игорем Витальевичем Савицким, музей в Нукусе хранит "
                "вторую в мире по значимости коллекцию русского авангарда и богатейшее собрание "
                "народно-прикладного искусства Каракалпакстана.\n\n"
                "В фондах музея насчитывается более 80 000 экспонатов, включая древности "
                "Хорезма и шедевры живописи первой половины XX века."
            ),
            "en": (
                "Founded in 1966 by Igor Savitsky in Nukus, the museum houses the world's "
                "second-largest collection of Russian avant-garde art alongside traditional "
                "Karakalpak folk art.\n\n"
                "Its collection exceeds 80,000 items, spanning Ancient Khorezm archaeological "
                "artifacts and rare early 20th-century paintings."
            ),
        },
    },
    {
        "cluster": "nukus",
        "slug": "mizdakhan",
        "kind": "fortress",
        "lat": 42.3983,
        "lng": 59.3831,
        "qr": "mizdakhan1",
        "titles": {
            "kaa": "Mizdaxan arxeologiyalıq-memorial kompleksi",
            "uz": "Mizdaxon arxeologik-memorial majmuasi",
            "ru": "Археологический комплекс Миздахкан",
            "en": "Mizdakhan Archaeological Complex",
        },
        "bodies": {
            "kaa": (
                "Mizdaxan — Xojeli qalası janındaǵı 200 gektardan aslam maydandı iyelegen "
                "áyyemgi qala hám qoyımshılıq kompleksi (b.e.sh. IV ásir — XIV ásir).\n\n"
                "Bul jerde Mazlumxan Sulıw jer astı maqbarası, Shamun-Nabi maqbarası "
                "hám Gáwir-qala qaldıqları jaylasqan."
            ),
            "uz": (
                "Mizdaxon — Xo‘jayli shahri yaqinida 200 gektardan ziyod maydonni egallagan "
                "qadimiy shahar va nekropol majmuasi (mil. avv. IV asr — XIV asr).\n\n"
                "Bu yerda Mazlumxon Sulu yer osti maqbarasi, Shamun-Nabi maqbarasi "
                "va Gavur-qal’a xarobalari joylashgan."
            ),
            "ru": (
                "Миздахкан — древний город и крупный некрополь близ Ходжейли площадью более "
                "200 гектаров, существовавший с IV века до н.э. по XIV век н.э.\n\n"
                "Здесь расположены подземный мавзолей Мазлумхан-Сулу, мавзолей Шамун-Наби "
                "и цитадель Гяур-кала."
            ),
            "en": (
                "Mizdakhan is an ancient city and vast necropolis near Khodjeyli covering over "
                "200 hectares, active from the 4th century BCE to the 14th century CE.\n\n"
                "Key monuments include the underground Mausoleum of Mazlumkhan Sulu, "
                "Shamun-Nabi Mausoleum, and the Gyaur-Kala citadel."
            ),
        },
    },
    {
        "cluster": "aral",
        "slug": "ship-graveyard",
        "kind": "monument",
        "lat": 43.7885,
        "lng": 59.0315,
        "qr": "moynaqship",
        "titles": {
            "kaa": "Moynaq kemeler qoyımshılıǵı",
            "uz": "Mo‘ynoq kemalar qabristoni",
            "ru": "Кладбище кораблей в Мойнаке",
            "en": "Moynaq Ship Graveyard",
        },
        "bodies": {
            "kaa": (
                "Burınǵı port qalası Moynaqta jaylasqan kemeler qoyımshılıǵı — "
                "XX ásirdiń eń úlken ekologiyalıq apatı bolǵan Aral teńiziniń tartılıwın "
                "kórsetetuǵın tariyxıy estelik.\n\n"
                "1960-jıllardan baslap Ámiwdárya hám Sırdárya suwlarınıń suwǵarıwǵa "
                "kóp jumsalıwı sebepli teńiz jaǵası 100 kilometrden uzaqqa shegingen."
            ),
            "uz": (
                "Sobiq port shahri Mo‘ynoqda joylashgan kemalar qabristoni — "
                "XX asrning yirik ekologik fojiasi bo‘lgan Orol dengizi qurishining ramziy yodgorligi.\n\n"
                "1960-yillardan boshlab Amudaryo va Sirdaryo suvlarining sug‘orishga "
                "haddan ziyod yo‘naltirilishi oqibatida dengiz qirg‘og‘i 100 km dan uzoqqa chekingan."
            ),
            "ru": (
                "Кладбище кораблей в бывшем портовом городе Мойнак — наглядный памятник "
                "высыханию Аральского моря во второй половине XX века.\n\n"
                "С 1960-х годов из-за интенсивного забора воды Амударьи и Сырдарьи на орошение "
                "береговая линия отступила более чем на 100 километров."
            ),
            "en": (
                "Located in the former port town of Moynaq, the Ship Graveyard stands on the "
                "dry seabed of the Aral Sea.\n\n"
                "Starting in the 1960s, large-scale diversion of the Amu Darya and Syr Darya "
                "rivers for irrigation caused the shoreline to retreat by over 100 kilometers."
            ),
        },
    },
    {
        "cluster": "aral",
        "slug": "aral-sea-museum",
        "kind": "museum",
        "lat": 43.7871,
        "lng": 59.0310,
        "qr": "aralmuseum",
        "titles": {
            "kaa": "Aral teńizi tariyxı muzeyi",
            "uz": "Orol dengizi tarixi muzeyi",
            "ru": "Музей истории Аральского моря",
            "en": "Aral Sea History Museum",
        },
        "bodies": {
            "kaa": (
                "Moynaqtaǵı Aral teńizi muzeyi balıqshılıq flottıń tariyxın, "
                "flora hám faunanı, sonday-aq F. Madgazin hám R. Matevosyan súwretlerin saqlaydı."
            ),
            "uz": (
                "Mo‘ynoqdagi Orol dengizi tarixi muzeyi baliqchilik floti tarixini, "
                "hudud tabiati hamda F. Madgazin va R. Matevosyan rasmlarini namoyish etadi."
            ),
            "ru": (
                "Музей истории Аральского моря в Мойнаке посвящён истории рыболовного промысла, "
                "природе Приаралья и живописи Ф. Мадгазина и Р. Матевосяна."
            ),
            "en": (
                "The Aral Sea History Museum in Moynaq documents the region's fishing heritage, "
                "ecology, and paintings by F. Madgazin and R. Matevosyan."
            ),
        },
    },
    {
        "cluster": "khorezm-fortresses",
        "slug": "ayaz-kala",
        "kind": "fortress",
        "lat": 42.0117,
        "lng": 60.6514,
        "qr": "ayazkala01",
        "titles": {
            "kaa": "Ayaz-qala kompleks qorǵanları",
            "uz": "Ayoz-qal’a majmuasi",
            "ru": "Крепостной комплекс Аяз-кала",
            "en": "Ayaz-Kala Fortress Complex",
        },
        "bodies": {
            "kaa": (
                "Ayaz-qala — Qızılqum shóliniń shetinde jaylasqan Áyyemgi Xorezmniń "
                "úsh qorǵanınan ibarat arxeologiyalıq estelik (b.e.sh. IV ásir — b.e. VII ásir)."
            ),
            "uz": (
                "Ayoz-qal’a — Qizilqum cho‘li chekkasida joylashgan Qadimgi Xorazmning "
                "uchta istehkomidan iborat yodgorlik (mil. avv. IV asr — mil. VII asr)."
            ),
            "ru": (
                "Аяз-кала — комплекс из трёх городищ Древнего Хорезма на окраине пустыни "
                "Кызылкум, датируемый IV веком до н.э. — VII веком н.э."
            ),
            "en": (
                "Ayaz-Kala is a dramatic complex of three Ancient Khorezm mudbrick fortresses "
                "on the edge of the Kyzylkum Desert, dating from the 4th century BCE to the 7th century CE."
            ),
        },
    },
    {
        "cluster": "khorezm-fortresses",
        "slug": "toprak-kala",
        "kind": "fortress",
        "lat": 41.9261,
        "lng": 60.8225,
        "qr": "toprakkala",
        "titles": {
            "kaa": "Topıraq-qala — Áyyemgi Xorezm paytaxtı",
            "uz": "Tuproq-qal’a — Qadimgi Xorazm poytaxti",
            "ru": "Топрак-кала — древняя столица Хорезма",
            "en": "Toprak-Kala Royal Citadel",
        },
        "bodies": {
            "kaa": (
                "Topıraq-qala — b.e. II–III ásirlerinde Xorezm húkimdarlarınıń "
                "saray-qorǵanı bolǵan, 1938-jılı S.P. Tolstov ekspediciyası tárepinen izertlengen."
            ),
            "uz": (
                "Tuproq-qal’a — milodiy II–III asrlarda Xorazm hukmdorlarining "
                "saroy-qal’asi bo‘lgan, 1938-yilda S.P. Tolstov ekspeditsiyasi tomonidan o‘rganilgan."
            ),
            "ru": (
                "Топрак-кала — династическая столица и дворцовый комплекс правителей Хорезма "
                "II–III веков н.э., исследованный экспедицией С.П. Толстова в 1938 году."
            ),
            "en": (
                "Toprak-Kala was the royal palace-citadel of Khorezm in the 2nd–3rd centuries CE, "
                "excavated by S.P. Tolstov's expedition in 1938."
            ),
        },
    },
    {
        "cluster": "khorezm-fortresses",
        "slug": "chilpyk",
        "kind": "monument",
        "lat": 42.2647,
        "lng": 60.0886,
        "qr": "chilpyk001",
        "titles": {
            "kaa": "Shılpıq zardushtiylik daxması",
            "uz": "Chilpiq zardushtiylik daxmasi",
            "ru": "Чилпык — зороастрийская дахма",
            "en": "Chilpyk Zoroastrian Tower of Silence",
        },
        "bodies": {
            "kaa": (
                "Shılpıq — Ámiwdárya boyındaǵı 35 metrlik tóbelikte jaylasqan "
                "diametri 65 metrli zardushtiylik daxması (b.e. I–IV ásirleri)."
            ),
            "uz": (
                "Chilpiq — Amudaryo bo‘yidagi 35 metrlik tepalikda qad rostlagan, "
                "diametri 65 metr bo‘lgan qadimiy zardushtiylik daxmasi (milodiy I–IV asrlar)."
            ),
            "ru": (
                "Чилпык — круглая зороастрийская дахма диаметром 65 метров на 35-метровом "
                "холме у берега Амударьи (I–IV века н.э.)."
            ),
            "en": (
                "Chilpyk is a circular Zoroastrian dakhma (Tower of Silence) 65 meters in diameter "
                "perched on a 35-meter hill near the Amu Darya (1st–4th centuries CE)."
            ),
        },
    },
]

CLUSTERS_META = {
    "nukus": {
        "kaa": "Nókis hám átirapı",
        "uz": "Nukus va atrofi",
        "ru": "Нукус и окрестности",
        "en": "Nukus & Surroundings",
    },
    "aral": {
        "kaa": "Moynaq hám Aral",
        "uz": "Mo‘ynoq va Orol",
        "ru": "Мойнак и Арал",
        "en": "Moynaq & Aral Sea",
    },
    "khorezm-fortresses": {
        "kaa": "Áyyemgi Xorezm qalaları",
        "uz": "Qadimgi Xorazm qal’alari",
        "ru": "Крепости Древнего Хорезма",
        "en": "Ancient Khorezm Fortresses",
    },
}


def main() -> None:
    with SessionLocal() as db:
        country = db.scalar(select(Country).where(Country.code == "UZ"))
        if country is None:
            country = Country(
                code="UZ",
                names={
                    "en": "Uzbekistan",
                    "ru": "Узбекистан",
                    "uz": "O‘zbekiston",
                    "kaa": "Ózbekstan",
                },
            )
            db.add(country)
            db.flush()

        region = db.scalar(select(Region).where(Region.slug == "karakalpakstan"))
        if region is None:
            region = Region(
                country_id=country.id,
                slug="karakalpakstan",
                names={
                    "en": "Karakalpakstan",
                    "ru": "Каракалпакстан",
                    "uz": "Qoraqalpog‘iston",
                    "kaa": "Qaraqalpaqstan",
                },
            )
            db.add(region)
            db.flush()

        clusters: dict[str, Cluster] = {}
        for slug, names in CLUSTERS_META.items():
            c = db.scalar(select(Cluster).where(Cluster.slug == slug))
            if c is None:
                c = Cluster(region_id=region.id, slug=slug, names=names)
                db.add(c)
                db.flush()
            else:
                c.names = names
            clusters[slug] = c

        places_by_cluster: dict[str, list[Place]] = {k: [] for k in CLUSTERS_META}
        for item in PLACES_DATA:
            p = db.scalar(select(Place).where(Place.slug == item["slug"]))
            if p is None:
                p = Place(
                    cluster_id=clusters[item["cluster"]].id,
                    slug=item["slug"],
                    kind=item["kind"],
                    lat=item["lat"],
                    lng=item["lng"],
                    geofence_radius_m=60,
                    cover_image_url=f"/images/{item['slug']}.webp",
                )
                db.add(p)
                db.flush()
            places_by_cluster[item["cluster"]].append(p)

            qr = db.scalar(select(QRCode).where(QRCode.place_id == p.id))
            if qr is None:
                db.add(QRCode(place_id=p.id, hash=item["qr"]))

            for lang in ("kaa", "uz", "ru", "en"):
                existing = db.scalar(
                    select(PlaceContent).where(
                        PlaceContent.place_id == p.id, PlaceContent.lang == lang
                    )
                )
                body = item["bodies"][lang]
                paras = [x for x in body.split("\n\n") if x.strip()]
                timings = [
                    {"index": i, "start_s": i * 45, "end_s": (i + 1) * 45}
                    for i in range(len(paras))
                ]
                if existing is None:
                    db.add(
                        PlaceContent(
                            place_id=p.id,
                            lang=lang,
                            title=item["titles"][lang],
                            body=body,
                            audio_url=f"https://cdn.audioguide.uz/audio/{p.slug}-{lang}.opus",
                            audio_size_bytes=960_000,
                            audio_duration_s=len(paras) * 45,
                            paragraph_timings=timings,
                            status=ContentStatus.published,
                            version=1,
                            source_refs=[
                                {
                                    "title": "Karakalpakstan Cultural Heritage Archive",
                                    "author": "Academy of Sciences",
                                    "license": "CC-BY-4.0",
                                }
                            ],
                        )
                    )
                src_title = f"{item['titles'][lang]} — Verified Reference"
                if (
                    db.scalar(
                        select(KnowledgeSource).where(
                            KnowledgeSource.place_id == p.id, KnowledgeSource.lang == lang
                        )
                    )
                    is None
                ):
                    src = KnowledgeSource(
                        title=src_title,
                        author="Museum Scientific Council",
                        year=2025,
                        license="CC-BY-4.0",
                        place_id=p.id,
                        lang=lang,
                        verified=True,
                    )
                    db.add(src)
                    db.flush()
                    rag.ingest_source(db, src, body)

        # Routes per cluster
        routes_meta = [
            ("nukus", "nukus-heritage", 42.0, 210, {
                "kaa": "Nókis hám Mizdaxan marshrutı",
                "uz": "Nukus va Mizdaxon yo‘nalishi",
                "ru": "Маршрут Нукус и Миздахкан",
                "en": "Nukus & Mizdakhan Route",
            }),
            ("aral", "moynaq-aral-route", 210.0, 360, {
                "kaa": "Moynaq hám Aral teńizi",
                "uz": "Mo‘ynoq va Orol dengizi",
                "ru": "Мойнак и Аральское море",
                "en": "Moynaq & Aral Sea Expedition",
            }),
            ("khorezm-fortresses", "golden-ring-fortresses", 145.0, 300, {
                "kaa": "Áyyemgi Xorezm qalaları",
                "uz": "Qadimgi Xorazm qal’alari halqasi",
                "ru": "Кольцо крепостей Древнего Хорезма",
                "en": "Ancient Khorezm Fortress Ring",
            }),
        ]
        for cslug, rslug, km, mins, names in routes_meta:
            route = db.scalar(select(Route).where(Route.slug == rslug))
            if route is None:
                route = Route(
                    cluster_id=clusters[cslug].id,
                    slug=rslug,
                    names=names,
                    length_km=km,
                    duration_min=mins,
                )
                db.add(route)
                db.flush()
                for idx, pl in enumerate(places_by_cluster[cslug], start=1):
                    db.add(RoutePlace(route_id=route.id, place_id=pl.id, position=idx))

        # Verified guides
        guides_seed = [
            (
                "arman.guide@audioguide.uz",
                "Arman Jumaniyazov",
                "Karakalpakstan & Ustyurt Plateau expedition leader, 9 years experience.",
                ["kaa", "uz", "ru", "en"],
                ["aral", "ustyurt", "fortresses"],
                True,
                80.0,
                4.9,
            ),
            (
                "dilnoza.guide@audioguide.uz",
                "Dilnoza Qurbanova",
                "Art historian specializing in the Savitsky Museum & Mizdakhan.",
                ["kaa", "uz", "ru", "en"],
                ["museum", "history"],
                False,
                45.0,
                4.8,
            ),
            (
                "rustam.guide@audioguide.uz",
                "Rustam Bekchanov",
                "Ancient Khorezm archaeological guide with 4x4 Land Cruiser.",
                ["uz", "ru", "en"],
                ["fortresses", "desert"],
                True,
                70.0,
                4.9,
            ),
        ]
        for email, name, bio, langs, specs, has_4x4, price, rating in guides_seed:
            u = db.scalar(select(User).where(User.email == email))
            if u is None:
                u = User(email=email, name=name, role=Role.guide, preferred_lang="kaa")
                db.add(u)
                db.flush()
                db.add(
                    GuideProfile(
                        user_id=u.id,
                        display_name=name,
                        bio=bio,
                        languages=langs,
                        specialties=specs,
                        has_4x4=has_4x4,
                        price_from_usd=price,
                        status=GuideStatus.approved,
                        rating=rating,
                    )
                )

        db.commit()
        print("seed ok: 3 clusters, 7 places, 4 languages, routes, RAG chunks, 3 verified guides")


if __name__ == "__main__":
    main()
