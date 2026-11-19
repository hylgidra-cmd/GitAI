export type Lang = "kaa" | "uz" | "ru" | "en";

export const LANG_LABELS: Record<Lang, { short: string; native: string }> = {
  kaa: { short: "KAA", native: "Qaraqalpaqsha" },
  uz: { short: "UZ", native: "O‘zbekcha" },
  ru: { short: "RU", native: "Русский" },
  en: { short: "EN", native: "English" },
};

export const UI_TEXT: Record<
  Lang,
  {
    brand: string;
    subtitle: string;
    tabExplore: string;
    tabRoutes: string;
    tabAI: string;
    tabGuides: string;
    tabAdmin: string;
    online: string;
    offlineMode: string;
    allClusters: string;
    allKinds: string;
    kindMuseum: string;
    kindFortress: string;
    kindMonument: string;
    listenNow: string;
    pause: string;
    speed: string;
    transcript: string;
    sourcesAndLicense: string;
    geofenceHint: string;
    geofenceAction: string;
    qrInstantBadge: string;
    favorite: string;
    history: string;
    downloadBundle: string;
    bundleDownloaded: string;
    bundleSizeLimit: string;
    aiTitle: string;
    aiSub: string;
    aiPlaceholder: string;
    aiAsk: string;
    aiVoiceBtn: string;
    aiPhotoBtn: string;
    aiBadge: string;
    aiHelpful: string;
    aiNotHelpful: string;
    aiReportError: string;
    aiOfflineNotice: string;
    guidesTitle: string;
    guidesSub: string;
    filter4x4: string;
    bookGuide: string;
    requestSent: string;
    timer24h: string;
    cmsTitle: string;
  }
> = {
  kaa: {
    brand: "Audio Guide Qaraqalpaqstan & Ózbekstan",
    subtitle: "QR yamasa karta arqalı 1 tap penen óz tilińizde tıńlań, AI-gidsinen sorań hám jergilikli gidti jaldań",
    tabExplore: "Obyektler & Karta",
    tabRoutes: "Marshrutlar & Oflayn",
    tabAI: "AI-Gid (RAG + Foto)",
    tabGuides: "Jergilikli Gidler",
    tabAdmin: "CMS & Admin",
    online: "Onlayn",
    offlineMode: "Oflayn rejim (Kesh)",
    allClusters: "Barlıq klasterler",
    allKinds: "Barlıq túrler",
    kindMuseum: "Muzey",
    kindFortress: "Qala / Qorǵan",
    kindMonument: "Estelik",
    listenNow: "Tıńlaw",
    pause: "Тоqtatıw",
    speed: "Tezlik",
    transcript: "Tekst hám abzas boyınsha sinxronizaciya",
    sourcesAndLicense: "Tastıyıqlanǵan derekler hám licenziya",
    geofenceHint: "Siz geozonaǵa kirdińiz (50 m). Audiogidti tıńlaysız ba?",
    geofenceAction: "Tıńlawdı baslaw",
    qrInstantBadge: "QR Tez ashılıw — registraciyasız",
    favorite: "Saylanǵanlar",
    history: "Tıńlaw tariyxı",
    downloadBundle: "Oflayn paketti júklep alıw (Wi-Fi)",
    bundleDownloaded: "Oflaynǵa saqlandı (Samolyot rejiminde isleydi)",
    bundleSizeLimit: "Klaster paketi ≤ 150 MB (Opus 64 kbps + WebP + PMTiles)",
    aiTitle: "Tastıyıqlanǵan bilim bazası boyınsha AI-Gid",
    aiSub: "Hár bir juwap derekke silteme beredi. Bazada joq bolsa — oylap تاپpay «Bilmeymen» deydi.",
    aiPlaceholder: "Mısalı: Savickiy muzeyi qashan ashılǵan yamasa Aral nege tartılǵan?",
    aiAsk: "Soraw beriw",
    aiVoiceBtn: "Dawıslı soraw (Push-to-talk)",
    aiPhotoBtn: "Foto + OCR (Arab/Latın/Kirill)",
    aiBadge: "Juwap AI tárepinen tastıyıqlanǵan baza tiykarında jaratıldı",
    aiHelpful: "Paydalı",
    aiNotHelpful: "Paydasız",
    aiReportError: "Qáte haqqında xabarlaw",
    aiOfflineNotice: "AI-gid hám gidke arza jiberiw ushın internet kerek. Oflayn audiogid hám karta isleydi.",
    guidesTitle: "Verifikaciyadan ótken jergilikli gidler",
    guidesSub: "Tiller, 4×4 jol таńlamas avtomobil hám баǵа boyınsha saylań. Gid 24 saat ishinde Telegram/Email arqalı juwap beredi.",
    filter4x4: "Tek 4×4 jol tańlamas",
    bookGuide: "Arza jiberiw",
    requestSent: "Arza گidke Telegram hám Email arqalı jiberildi!",
    timer24h: "Juwap taymeri: 24 saat (MVP da tólem tikkeley gidke)",
    cmsTitle: "CMS Контент-конвейер & Admin Panel",
  },
  uz: {
    brand: "Audio Guide Qoraqalpog‘iston & O‘zbekiston",
    subtitle: "QR yoki xarita orqali 1 tapda o‘z tilingizda tinglang, AI-giddan so‘rang va mahalliy gid yollang",
    tabExplore: "Obyektlar & Xarita",
    tabRoutes: "Marshrutlar & Oflayn",
    tabAI: "AI-Gid (RAG + Foto)",
    tabGuides: "Mahalliy Gidlar",
    tabAdmin: "CMS & Admin",
    online: "Onlayn",
    offlineMode: "Oflayn rejim (Kesh)",
    allClusters: "Barcha klasterlar",
    allKinds: "Barcha turlar",
    kindMuseum: "Muzey",
    kindFortress: "Qal’a / Imlo",
    kindMonument: "Yodgorlik",
    listenNow: "Tinglash",
    pause: "To‘xtatish",
    speed: "Tezlik",
    transcript: "Transkript va abzas bo‘yicha sinxronizatsiya",
    sourcesAndLicense: "Tasdiqlangan manbalar va litsenziya",
    geofenceHint: "Siz obyekt geozonasiga kirdingiz (50 m). Tinglaysizmi?",
    geofenceAction: "Tinglashni boshlash",
    qrInstantBadge: "QR Tezkor ochilish — ro‘yxatdan o‘tmasdan",
    favorite: "Sevimlilar",
    history: "Tinglash tarixi",
    downloadBundle: "Oflayn paketni yuklab olish (Wi-Fi)",
    bundleDownloaded: "Oflaynga saqlandi (Samolyot rejimida ishlaydi)",
    bundleSizeLimit: "Klaster paketi ≤ 150 MB (Opus 64 kbps + WebP + PMTiles)",
    aiTitle: "Tasdiqlangan bilimlar bazasi bo‘yicha AI-Gid",
    aiSub: "Har bir javob manbaga havola ko‘rsatadi. Bazada bo‘lmasa — to‘qimasdan «Bilmayman» deydi.",
    aiPlaceholder: "Masalan: Savitskiy muzeyi qachon ochilgan yoki Orol nega qurigan?",
    aiAsk: "So‘rash",
    aiVoiceBtn: "Ovozli savol (Push-to-talk)",
    aiPhotoBtn: "Foto + OCR (Arab/Lotin/Kirill)",
    aiBadge: "Javob AI tomonidan tasdiqlangan baza asosida yaratildi",
    aiHelpful: "Foydali",
    aiNotHelpful: "Foydali emas",
    aiReportError: "Xato haqida xabar berish",
    aiOfflineNotice: "AI-gid va gidlarga so‘rov yuborish uchun internet kerak. Oflayn audiogid va xarita to‘liq ishlaydi.",
    guidesTitle: "Tasdiqlangan (Verifikatsiyalangan) Gidlar",
    guidesSub: "Til, 4×4 yo‘ltanlamas va narx bo‘yicha tanlang. Gid 24 soat ichida Telegram va Email orqali javob beradi.",
    filter4x4: "Faqat 4×4 yo‘ltanlamas",
    bookGuide: "So‘rov yuborish",
    requestSent: "So‘rov gidga Telegram va Email orqali yuborildi!",
    timer24h: "Javob taymeri: 24 soat (MVP da to‘lov bevosita gidga)",
    cmsTitle: "CMS Kontent-konveyer & Admin Panel",
  },
  ru: {
    brand: "Audio Guide Каракалпакстан и Узбекистан",
    subtitle: "За один тап (QR или карта) слушайте рассказ на своём языке, спрашивайте AI-гида и бронируйте живого гида",
    tabExplore: "Объекты и Карта",
    tabRoutes: "Маршруты и Офлайн",
    tabAI: "AI-Гид (RAG + Фото)",
    tabGuides: "Каталог Гидов",
    tabAdmin: "CMS и Админка",
    online: "Онлайн",
    offlineMode: "Офлайн-режим (Кэш)",
    allClusters: "Все кластеры",
    allKinds: "Все типы",
    kindMuseum: "Музей",
    kindFortress: "Крепость",
    kindMonument: "Памятник",
    listenNow: "Слушать",
    pause: "Пауза",
    speed: "Скорость",
    transcript: "Транскрипт с подсветкой текущего абзаца",
    sourcesAndLicense: "Проверенные источники и лицензия",
    geofenceHint: "Вы вошли в геозону объекта (50 м). Слушать аудиогид?",
    geofenceAction: "Слушать",
    qrInstantBadge: "Открытие по QR — без установки и регистрации",
    favorite: "Избранное",
    history: "История",
    downloadBundle: "Скачать офлайн-пакет по Wi-Fi",
    bundleDownloaded: "Пакет сохранён офлайн (работает в режиме «в самолёте»)",
    bundleSizeLimit: "Размер пакета кластера ≤ 150 МБ (Opus 64 кбит/с + WebP + PMTiles)",
    aiTitle: "AI-Гид по проверенной базе знаний (RAG)",
    aiSub: "Каждый ответ со ссылкой на источник; вне базы — честное «не знаю» без выдумки (Groundedness ≥ 95%).",
    aiPlaceholder: "Например: когда основан музей Савицкого или почему высох Арал?",
    aiAsk: "Спросить",
    aiVoiceBtn: "Голос (Push-to-talk)",
    aiPhotoBtn: "Фото + OCR (Араб/Лат/Кир)",
    aiBadge: "Ответ создан AI по проверенной базе",
    aiHelpful: "Полезно",
    aiNotHelpful: "Нет",
    aiReportError: "Сообщить об ошибке",
    aiOfflineNotice: "Для AI-гида и заявок гидам нужен интернет. Офлайн-аудиогид, карта и транскрипты работают без сети.",
    guidesTitle: "Верифицированные гиды региона",
    guidesSub: "Фильтр по языку, специализации и внедорожнику 4×4. Уведомление гиду в Telegram и на email (таймер 24 ч).",
    filter4x4: "Только с внедорожником 4×4",
    bookGuide: "Отправить заявку",
    requestSent: "Заявка отправлена гиду в Telegram и на Email!",
    timer24h: "Таймер ответа: 24 ч (в MVP оплата напрямую гиду)",
    cmsTitle: "CMS Конвейер Контента и Админ-дашборд",
  },
  en: {
    brand: "Audio Guide Karakalpakstan & Uzbekistan",
    subtitle: "Listen in 1 tap (QR or map) in your language, ask the grounded AI guide, or book a verified local guide",
    tabExplore: "Places & Map",
    tabRoutes: "Routes & Offline",
    tabAI: "AI Guide (RAG + Photo)",
    tabGuides: "Local Guides",
    tabAdmin: "CMS & Admin",
    online: "Online",
    offlineMode: "Offline Mode (Cached)",
    allClusters: "All clusters",
    allKinds: "All types",
    kindMuseum: "Museum",
    kindFortress: "Fortress",
    kindMonument: "Monument",
    listenNow: "Listen",
    pause: "Pause",
    speed: "Speed",
    transcript: "Synchronized Transcript",
    sourcesAndLicense: "Verified Sources & License",
    geofenceHint: "You entered the object geofence (50m). Listen to the audio guide?",
    geofenceAction: "Start Listening",
    qrInstantBadge: "1-Tap QR Open — No Install or Signup",
    favorite: "Favorites",
    history: "History",
    downloadBundle: "Download Offline Route Bundle (Wi-Fi)",
    bundleDownloaded: "Saved Offline (Works in Airplane Mode)",
    bundleSizeLimit: "Cluster bundle ≤ 150 MB (Opus 64 kbps + WebP + PMTiles)",
    aiTitle: "Grounded AI Guide (Verified Knowledge Base)",
    aiSub: "Every answer cites a verified museum source; outside the base it honestly replies 'I don't know'.",
    aiPlaceholder: "e.g., When was the Savitsky Museum founded, or why did the Aral Sea shrink?",
    aiAsk: "Ask AI",
    aiVoiceBtn: "Voice (Push-to-talk)",
    aiPhotoBtn: "Photo + OCR (Arab/Lat/Cyr)",
    aiBadge: "Answer generated by AI from verified sources",
    aiHelpful: "Helpful",
    aiNotHelpful: "Not helpful",
    aiReportError: "Report inaccuracy",
    aiOfflineNotice: "Internet is required for AI chat and guide requests. Downloaded audio guides, map, and transcripts work offline.",
    guidesTitle: "Verified Local Guides",
    guidesSub: "Filter by language, specialty, and 4×4 vehicle. Instant Telegram & Email notification with 24h response timer.",
    filter4x4: "4×4 off-road vehicle only",
    bookGuide: "Send Booking Request",
    requestSent: "Request delivered to guide via Telegram & Email!",
    timer24h: "24h response timer (direct payment to guide in MVP)",
    cmsTitle: "CMS Content Pipeline & Admin Dashboard",
  },
};
