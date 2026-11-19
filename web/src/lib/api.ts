import { Lang } from "@/i18n/messages";
import { getDeviceId } from "./offline";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ParagraphTiming {
  index: number;
  start_s: number;
  end_s: number;
}

export interface SourceRef {
  title: string;
  author?: string;
  license: string;
}

export interface PlaceItem {
  id: string;
  cluster_slug: string;
  slug: string;
  kind: "museum" | "fortress" | "monument";
  lat: number;
  lng: number;
  geofence_radius_m: number;
  qr_hash: string;
  titles: Record<Lang, string>;
  bodies: Record<Lang, string>;
  audio_duration_s: number;
  paragraph_timings: ParagraphTiming[];
  source_refs: SourceRef[];
  status: "draft" | "in_review" | "published";
  version: number;
}

export interface RouteItem {
  id: string;
  slug: string;
  cluster_slug: string;
  names: Record<Lang, string>;
  length_km: number;
  duration_min: number;
  place_slugs: string[];
  bundle_mb: number;
}

export interface GuideItem {
  id: string;
  display_name: string;
  bio: string;
  languages: Lang[];
  specialties: string[];
  has_4x4: boolean;
  price_from_usd: number;
  rating: number;
  status: "pending" | "approved" | "rejected";
}

export interface CitationItem {
  chunk_id: string;
  source_id: string;
  source_title: string;
  score: number;
}

export interface AIResponse {
  message_id: string;
  answer: string;
  grounded: boolean;
  citations: CitationItem[];
  lang: Lang;
  remaining_today: number;
  audio_url?: string | null;
  ocr_text?: string;
  exif_stripped?: boolean;
  expires_at?: string;
}

/**
 * Built-in CDN/static fallback dataset (TZ Section 9 Principle 2:
 * "Прослушивание не зависит от живого API: опубликованный контент выкладывается в CDN
 * как статические JSON и аудио, поэтому падение сервера не останавливает туристов у объекта.")
 */
export const STATIC_PLACES: PlaceItem[] = [
  {
    id: "11111111-1111-1111-1111-111111111101",
    cluster_slug: "nukus",
    slug: "savitsky-museum",
    kind: "museum",
    lat: 42.4647,
    lng: 59.6122,
    geofence_radius_m: 60,
    qr_hash: "savitsky01",
    titles: {
      kaa: "I.V. Savickiy atındaǵı Qaraqalpaqstan kórkem óner muzeyi",
      uz: "I.V. Savitskiy nomidagi Qoraqalpog‘iston san’at muzeyi",
      ru: "Государственный музей искусств им. И.В. Савицкого",
      en: "Savitsky Karakalpakstan Art Museum",
    },
    bodies: {
      kaa:
        "1966-jılı Igor Savickiy tárepinen shólkemlestirilgen bul muzey dúnyadaǵı eń iri rus avangardı hám Qaraqalpaq xalıq ámeliy kórkem óneri toplamlarınan birin saqlaydı.\n\n" +
        "Muzey qorında 80 mıńnan aslam eksponat bar bolıp, olardıń arasında Áyyemgi Xorezm arxeologiyalıq tabılmaları hám XX ásir súwretshileriniń kem ushırasatuǵın shıǵarmaları orın alǵan.\n\n" +
        "Bul jerde qaraqalpaq zergerlik buyımları, gilemshilik hám milliylikti sáwlelendiriwshi biybaha miyraslar kórsetiledi.",
      uz:
        "1966-yilda Igor Savitskiy tomonidan asos solingan ushbu muzey dunyodagi eng boy rus avangardi va Qoraqalpoq xalq amaliy san’ati kolleksiyalaridan birini o‘z ichiga oladi.\n\n" +
        "Muzey fondida 80 mingdan ortiq eksponat mavjud bo‘lib, ular orasida Qadimgi Xorazm arxeologik topilmalari hamda XX asr rassomlarining noyob asarlari bor.\n\n" +
        "Ekspozitsiyada qoraqalpoq milliy zargarlik buyumlari, kashtachilik va gilamdo‘zlik namunalari alohida o‘rin egallaydi.",
      ru:
        "Основанный в 1966 году Игорем Витальевичем Савицким, музей в Нукусе хранит вторую в мире по значимости коллекцию русского авангарда и богатейшее собрание народно-прикладного искусства Каракалпакстана.\n\n" +
        "В фондах музея насчитывается более 80 000 экспонатов, включая древности Хорезма и шедевры живописи первой половины XX века.\n\n" +
        "Особую ценность представляют каракалпакские ювелирные украшения, вышивка и предметы кочевого быта Приаралья.",
      en:
        "Founded in 1966 by Igor Savitsky in Nukus, the museum houses the world's second-largest collection of Russian avant-garde art alongside traditional Karakalpak folk art.\n\n" +
        "Its collection exceeds 80,000 items, spanning Ancient Khorezm archaeological artifacts and rare early 20th-century paintings.\n\n" +
        "Visitors can explore galleries dedicated to Karakalpak jewelry, textile patterns, and terracotta sculptures.",
    },
    audio_duration_s: 135,
    paragraph_timings: [
      { index: 0, start_s: 0, end_s: 45 },
      { index: 1, start_s: 45, end_s: 90 },
      { index: 2, start_s: 90, end_s: 135 },
    ],
    source_refs: [
      {
        title: "Savitsky Museum Scientific Catalogue (Nukus, 2024)",
        author: "Museum Curatorial Board",
        license: "CC-BY-4.0 / Museum Agreement #14",
      },
    ],
    status: "published",
    version: 1,
  },
  {
    id: "11111111-1111-1111-1111-111111111102",
    cluster_slug: "nukus",
    slug: "mizdakhan",
    kind: "fortress",
    lat: 42.3983,
    lng: 59.3831,
    geofence_radius_m: 80,
    qr_hash: "mizdakhan1",
    titles: {
      kaa: "Mizdaxan arxeologiyalıq-memorial kompleksi",
      uz: "Mizdaxon arxeologik-memorial majmuasi",
      ru: "Археологический комплекс Миздахкан",
      en: "Mizdakhan Archaeological Complex",
    },
    bodies: {
      kaa:
        "Mizdaxan — Xojeli qalası janındaǵı 200 gektardan aslam maydandı iyelegen áyyemgi qala hám qoyımshılıq kompleksi (b.e.sh. IV ásir — XIV ásir).\n\n" +
        "Bul jerde Mazlumxan Sulıw jer astı maqbarası, Shamun-Nabi maqbarası, Xalifa Erejep hám Gáwir-qala qaldıqları jaylasqan.",
      uz:
        "Mizdaxon — Xo‘jayli shahri yaqinida 200 gektardan ziyod maydonni egallagan qadimiy shahar va nekropol majmuasi (mil. avv. IV asr — XIV asr).\n\n" +
        "Bu yerda Mazlumxon Sulu yer osti maqbarasi, Shamun-Nabi maqbarasi, Xalifa Erejep va Gavur-qal’a xarobalari joylashgan.",
      ru:
        "Миздахкан — древний город и крупный некрополь близ Ходжейли площадью более 200 гектаров, существовавший с IV века до н.э. по XIV век н.э.\n\n" +
        "Здесь расположены подземный мавзолей Мазлумхан-Сулу, мавзолей Шамун-Наби, Халифа Ереджеп и цитадель Гяур-кала.",
      en:
        "Mizdakhan is an ancient city and vast necropolis near Khodjeyli covering over 200 hectares, active from the 4th century BCE to the 14th century CE.\n\n" +
        "Key monuments include the underground Mausoleum of Mazlumkhan Sulu, Shamun-Nabi Mausoleum, Khalifa Yerejep, and the Gyaur-Kala citadel.",
    },
    audio_duration_s: 90,
    paragraph_timings: [
      { index: 0, start_s: 0, end_s: 45 },
      { index: 1, start_s: 45, end_s: 90 },
    ],
    source_refs: [
      {
        title: "Archaeology of Ancient Khorezm & Mizdakhan",
        author: "V.N. Yagodin / Karakalpak Branch Academy of Sciences",
        license: "CC-BY-4.0",
      },
    ],
    status: "published",
    version: 1,
  },
  {
    id: "11111111-1111-1111-1111-111111111103",
    cluster_slug: "aral",
    slug: "ship-graveyard",
    kind: "monument",
    lat: 43.7885,
    lng: 59.0315,
    geofence_radius_m: 100,
    qr_hash: "moynaqship",
    titles: {
      kaa: "Moynaq kemeler qoyımshılıǵı",
      uz: "Mo‘ynoq kemalar qabristoni",
      ru: "Кладбище кораблей в Мойнаке",
      en: "Moynaq Ship Graveyard",
    },
    bodies: {
      kaa:
        "Burınǵı port qalası Moynaqta jaylasqan kemeler qoyımshılıǵı — XX ásirdiń eń úlken ekologiyalıq apatı bolǵan Aral teńiziniń tartılıwın kórsetetuǵın tariyxıy estelik.\n\n" +
        "1960-jıllardan baslap Ámiwdárya hám Sırdárya suwlarınıń suwǵarıwǵa kóp jumsalıwı sebepli teńiz jaǵası 100 kilometrden uzaqqa shegingen.",
      uz:
        "Sobiq port shahri Mo‘ynoqda joylashgan kemalar qabristoni — XX asrning yirik ekologik fojiasi bo‘lgan Orol dengizi qurishining ramziy yodgorligi.\n\n" +
        "1960-yillardan boshlab Amudaryo va Sirdaryo suvlarining sug‘orishga haddan ziyod yo‘naltirilishi oqibatida dengiz qirg‘og‘i 100 km dan uzoqqa chekingan.",
      ru:
        "Кладбище кораблей в бывшем портовом городе Мойнак — наглядный памятник высыханию Аральского моря во второй половине XX века.\n\n" +
        "С 1960-х годов из-за интенсивного забора воды Амударьи и Сырдарьи на орошение береговая линия отступила более чем на 100 километров.",
      en:
        "Located in the former port town of Moynaq, the Ship Graveyard stands on the dry seabed of the Aral Sea.\n\n" +
        "Starting in the 1960s, large-scale diversion of the Amu Darya and Syr Darya rivers for irrigation caused the shoreline to retreat by over 100 kilometers.",
    },
    audio_duration_s: 90,
    paragraph_timings: [
      { index: 0, start_s: 0, end_s: 45 },
      { index: 1, start_s: 45, end_s: 90 },
    ],
    source_refs: [
      {
        title: "Aral Sea Basin Historical & Ecological Archive",
        author: "Moynaq Museum of the Aral Sea",
        license: "CC-BY-4.0",
      },
    ],
    status: "published",
    version: 1,
  },
  {
    id: "11111111-1111-1111-1111-111111111104",
    cluster_slug: "aral",
    slug: "aral-sea-museum",
    kind: "museum",
    lat: 43.7871,
    lng: 59.031,
    geofence_radius_m: 60,
    qr_hash: "aralmuseum",
    titles: {
      kaa: "Aral teńizi tariyxı muzeyi",
      uz: "Orol dengizi tarixi muzeyi",
      ru: "Музей истории Аральского моря",
      en: "Aral Sea History Museum",
    },
    bodies: {
      kaa:
        "Moynaqtaǵı Aral teńizi muzeyi balıqshılıq flottıń tariyxın, flora hám faunanı, sonday-aq F. Madgazin hám R. Matevosyan súwretlerin saqlaydı.",
      uz:
        "Mo‘ynoqdagi Orol dengizi tarixi muzeyi baliqchilik floti tarixini, hudud tabiati hamda F. Madgazin va R. Matevosyan rasmlarini namoyish etadi.",
      ru:
        "Музей истории Аральского моря в Мойнаке посвящён истории рыболовного промысла, природе Приаралья и живописи Ф. Мадгазина и Р. Матевосяна.",
      en:
        "The Aral Sea History Museum in Moynaq documents the region's fishing heritage, ecology, and paintings by F. Madgazin and R. Matevosyan.",
    },
    audio_duration_s: 60,
    paragraph_timings: [{ index: 0, start_s: 0, end_s: 60 }],
    source_refs: [
      {
        title: "Moynaq Aral Sea Museum Guidebook",
        author: "Ministry of Culture & Tourism",
        license: "CC-BY-4.0",
      },
    ],
    status: "published",
    version: 1,
  },
  {
    id: "11111111-1111-1111-1111-111111111105",
    cluster_slug: "khorezm-fortresses",
    slug: "ayaz-kala",
    kind: "fortress",
    lat: 42.0117,
    lng: 60.6514,
    geofence_radius_m: 100,
    qr_hash: "ayazkala01",
    titles: {
      kaa: "Ayaz-qala kompleks qorǵanları",
      uz: "Ayoz-qal’a majmuasi",
      ru: "Крепостной комплекс Аяз-кала",
      en: "Ayaz-Kala Fortress Complex",
    },
    bodies: {
      kaa:
        "Ayaz-qala — Qızılqum shóliniń shetinde jaylasqan Áyyemgi Xorezmniń úsh qorǵanınan ibarat arxeologiyalıq estelik (b.e.sh. IV ásir — b.e. VII ásir).",
      uz:
        "Ayoz-qal’a — Qizilqum cho‘li chekkasida joylashgan Qadimgi Xorazmning uchta istehkomidan iborat yodgorlik (mil. avv. IV asr — mil. VII asr).",
      ru:
        "Аяз-кала — комплекс из трёх городищ Древнего Хорезма на окраине пустыни Кызылкум, датируемый IV веком до н.э. — VII веком н.э.",
      en:
        "Ayaz-Kala is a dramatic complex of three Ancient Khorezm mudbrick fortresses on the edge of the Kyzylkum Desert, dating from the 4th century BCE to the 7th century CE.",
    },
    audio_duration_s: 75,
    paragraph_timings: [{ index: 0, start_s: 0, end_s: 75 }],
    source_refs: [
      {
        title: "Ancient Khorezm Fortresses Monograph",
        author: "S.P. Tolstov Expedition Archive",
        license: "CC-BY-4.0",
      },
    ],
    status: "published",
    version: 1,
  },
  {
    id: "11111111-1111-1111-1111-111111111106",
    cluster_slug: "khorezm-fortresses",
    slug: "toprak-kala",
    kind: "fortress",
    lat: 41.9261,
    lng: 60.8225,
    geofence_radius_m: 90,
    qr_hash: "toprakkala",
    titles: {
      kaa: "Topıraq-qala — Áyyemgi Xorezm paytaxtı",
      uz: "Tuproq-qal’a — Qadimgi Xorazm poytaxti",
      ru: "Топрак-кала — древняя столица Хорезма",
      en: "Toprak-Kala Royal Citadel",
    },
    bodies: {
      kaa:
        "Topıraq-qala — b.e. II–III ásirlerinde Xorezm húkimdarlarınıń saray-qorǵanı bolǵan, 1938-jılı S.P. Tolstov ekspediciyası tárepinen izertlengen.",
      uz:
        "Tuproq-qal’a — milodiy II–III asrlarda Xorazm hukmdorlarining saroy-qal’asi bo‘lgan, 1938-yilda S.P. Tolstov ekspeditsiyasi tomonidan o‘rganilgan.",
      ru:
        "Топрак-кала — династическая столица и дворцовый комплекс правителей Хорезма II–III веков н.э., исследованный экспедицией С.П. Толстова в 1938 году.",
      en:
        "Toprak-Kala was the royal palace-citadel of Khorezm in the 2nd–3rd centuries CE, excavated by S.P. Tolstov's expedition in 1938.",
    },
    audio_duration_s: 70,
    paragraph_timings: [{ index: 0, start_s: 0, end_s: 70 }],
    source_refs: [
      {
        title: "Toprak-Kala Palace Excavations",
        author: "Khorezm Archaeological Expedition",
        license: "CC-BY-4.0",
      },
    ],
    status: "published",
    version: 1,
  },
  {
    id: "11111111-1111-1111-1111-111111111107",
    cluster_slug: "khorezm-fortresses",
    slug: "chilpyk",
    kind: "monument",
    lat: 42.2647,
    lng: 60.0886,
    geofence_radius_m: 80,
    qr_hash: "chilpyk001",
    titles: {
      kaa: "Shılpıq zardushtiylik daxması",
      uz: "Chilpiq zardushtiylik daxmasi",
      ru: "Чилпык — зороастрийская дахма",
      en: "Chilpyk Zoroastrian Tower of Silence",
    },
    bodies: {
      kaa:
        "Shılpıq — Ámiwdárya boyındaǵı 35 metrlik tóbelikte jaylasqan diametri 65 metrli zardushtiylik daxması (b.e. I–IV ásirleri).",
      uz:
        "Chilpiq — Amudaryo bo‘yidagi 35 metrlik tepalikda qad rostlagan, diametri 65 metr bo‘lgan qadimiy zardushtiylik daxmasi (milodiy I–IV asrlar).",
      ru:
        "Чилпык — круглая зороастрийская дахма диаметром 65 метров на 35-метровом холме у берега Амударьи (I–IV века н.э.).",
      en:
        "Chilpyk is a circular Zoroastrian dakhma (Tower of Silence) 65 meters in diameter perched on a 35-meter hill near the Amu Darya (1st–4th centuries CE).",
    },
    audio_duration_s: 65,
    paragraph_timings: [{ index: 0, start_s: 0, end_s: 65 }],
    source_refs: [
      {
        title: "Monuments of Ancient Khorezm",
        author: "Institute of History & Archaeology",
        license: "CC-BY-4.0",
      },
    ],
    status: "published",
    version: 1,
  },
];

export const STATIC_ROUTES: RouteItem[] = [
  {
    id: "22222222-2222-2222-2222-222222222201",
    slug: "nukus-heritage",
    cluster_slug: "nukus",
    names: {
      kaa: "Nókis hám Mizdaxan marshrutı",
      uz: "Nukus va Mizdaxon yo‘nalishi",
      ru: "Маршрут Нукус и Миздахкан",
      en: "Nukus & Mizdakhan Cultural Route",
    },
    length_km: 42,
    duration_min: 210,
    place_slugs: ["savitsky-museum", "mizdakhan"],
    bundle_mb: 24.5,
  },
  {
    id: "22222222-2222-2222-2222-222222222202",
    slug: "moynaq-aral-route",
    cluster_slug: "aral",
    names: {
      kaa: "Moynaq hám Aral teńizi ekspediciyası",
      uz: "Mo‘ynoq va Orol dengizi yo‘nalishi",
      ru: "Мойнак и Аральское море",
      en: "Moynaq & Aral Sea Expedition",
    },
    length_km: 210,
    duration_min: 360,
    place_slugs: ["ship-graveyard", "aral-sea-museum"],
    bundle_mb: 38.2,
  },
  {
    id: "22222222-2222-2222-2222-222222222203",
    slug: "golden-ring-fortresses",
    cluster_slug: "khorezm-fortresses",
    names: {
      kaa: "Áyyemgi Xorezm qalaları",
      uz: "Qadimgi Xorazm qal’alari halqasi",
      ru: "Кольцо крепостей Древнего Хорезма",
      en: "Ancient Khorezm Fortress Ring",
    },
    length_km: 145,
    duration_min: 300,
    place_slugs: ["chilpyk", "ayaz-kala", "toprak-kala"],
    bundle_mb: 52.0,
  },
];

export const STATIC_GUIDES: GuideItem[] = [
  {
    id: "33333333-3333-3333-3333-333333333301",
    display_name: "Arman Jumaniyazov",
    bio: "Ustyurt Plateau & Aral Sea expedition guide, 9 years experience, satellite communicator.",
    languages: ["kaa", "uz", "ru", "en"],
    specialties: ["aral", "ustyurt", "fortresses"],
    has_4x4: true,
    price_from_usd: 80,
    rating: 4.9,
    status: "approved",
  },
  {
    id: "33333333-3333-3333-3333-333333333302",
    display_name: "Dilnoza Qurbanova",
    bio: "Art historian specializing in the Savitsky Museum collection & Mizdakhan complex.",
    languages: ["kaa", "uz", "ru", "en"],
    specialties: ["museum", "history"],
    has_4x4: false,
    price_from_usd: 45,
    rating: 4.8,
    status: "approved",
  },
  {
    id: "33333333-3333-3333-3333-333333333303",
    display_name: "Rustam Bekchanov",
    bio: "Ancient Khorezm archaeological fortress specialist with 4×4 Toyota Land Cruiser.",
    languages: ["uz", "ru", "en"],
    specialties: ["fortresses", "desert"],
    has_4x4: true,
    price_from_usd: 70,
    rating: 4.9,
    status: "approved",
  },
];

const LOCAL_REFUSAL: Record<Lang, string> = {
  kaa: "Bilmeymen. Bul soraw boyınsha tastıyıqlanǵan bazada maǵlıwmat joq. Gidke muraját etiń.",
  uz: "Bilmayman. Bu savol bo‘yicha tasdiqlangan bazada ma’lumot topilmadi. Iltimos, gidga murojaat qiling.",
  ru: "Не знаю. В проверенной базе знаний нет подтверждённого фрагмента по этому вопросу. Пожалуйста, обратитесь к гиду.",
  en: "I don't know. There is no verified passage in the museum knowledge base for this question. Please ask a local guide.",
};

export async function askAIGuide(
  question: string,
  lang: Lang,
  placeId?: string
): Promise<AIResponse> {
  try {
    const res = await fetch(`${API_BASE}/ai/chat?lang=${lang}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Device-Id": getDeviceId(),
      },
      body: JSON.stringify({ question, place_id: placeId, lang }),
    });
    if (res.ok) {
      return (await res.json()) as AIResponse;
    }
  } catch {
    // Fallback to local grounded RAG over STATIC_PLACES when backend isn't reachable
  }

  const q = question.toLowerCase();
  const tokens = q.split(/\W+/).filter((w) => w.length > 3);
  let bestPlace: PlaceItem | null = null;
  let bestScore = 0;

  for (const p of STATIC_PLACES) {
    const haystack = `${p.titles[lang]} ${p.bodies[lang]} ${p.titles.en} ${p.bodies.en}`.toLowerCase();
    const hits = tokens.filter((t) => haystack.includes(t)).length;
    const score = tokens.length ? hits / tokens.length : 0;
    if (score > bestScore) {
      bestScore = score;
      bestPlace = p;
    }
  }

  if (!bestPlace || bestScore < 0.25) {
    return {
      message_id: "local-" + Date.now(),
      answer: LOCAL_REFUSAL[lang],
      grounded: false,
      citations: [],
      lang,
      remaining_today: 9,
    };
  }

  return {
    message_id: "local-" + Date.now(),
    answer: bestPlace.bodies[lang],
    grounded: true,
    citations: [
      {
        chunk_id: bestPlace.id,
        source_id: bestPlace.slug,
        source_title: bestPlace.source_refs[0]?.title || bestPlace.titles[lang],
        score: Number(bestScore.toFixed(2)),
      },
    ],
    lang,
    remaining_today: 9,
  };
}
