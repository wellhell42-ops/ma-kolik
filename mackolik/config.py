"""Mackolik scraper configuration - Pro Version."""

BASE_URL = "https://www.mackolik.com"
ARCHIVE_URL = "https://arsiv.mackolik.com"

# JSON API endpoints
API_URLS = {
    "livedata": "https://vd.mackolik.com/livedata",
    "livedata_legacy": "http://goapi.mackolik.com/livedata",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.mackolik.com/",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}

API_HEADERS = {
    "User-Agent": HEADERS["User-Agent"],
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.mackolik.com/",
    "X-Requested-With": "XMLHttpRequest",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
}

REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.5

# Leagues with Mackolik URL slugs and Opta IDs
LEAGUES = {
    "super-lig": {
        "name": "Trendyol Super Lig",
        "country": "Turkiye",
        "url_slug": "turkiye-super-lig",
        "opta_id": "482ofyysbdbeoxauk19yg7tdt",
        "archive_id": 1,
        "league_id": 1,
    },
    "1-lig": {
        "name": "Trendyol 1. Lig",
        "country": "Turkiye",
        "url_slug": "turkiye-trendyol-1-lig",
        "opta_id": "2o9svokc5s7diish3ycrzk7jm",
        "archive_id": 13,
        "league_id": 13,
    },
    "premier-league": {
        "name": "Premier League",
        "country": "Ingiltere",
        "url_slug": "ingiltere-premier-lig",
        "opta_id": "2kwbbcootiqqgmrzs6o5inle5",
        "archive_id": 2,
        "league_id": 2,
    },
    "la-liga": {
        "name": "La Liga",
        "country": "Ispanya",
        "url_slug": "ispanya-la-liga",
        "opta_id": "34pl8szyvrbwcmfkuocjm3r6t",
        "archive_id": 7,
        "league_id": 7,
    },
    "bundesliga": {
        "name": "Bundesliga",
        "country": "Almanya",
        "url_slug": "almanya-bundesliga",
        "opta_id": "6by3h89i2eykc341oz7lv1ddd",
        "archive_id": 4,
        "league_id": 4,
    },
    "serie-a": {
        "name": "Serie A",
        "country": "Italya",
        "url_slug": "italya-serie-a",
        "opta_id": "1r097lpxe0xn03ihb7wi98kao",
        "archive_id": 5,
        "league_id": 5,
    },
    "ligue-1": {
        "name": "Ligue 1",
        "country": "Fransa",
        "url_slug": "fransa-ligue-1",
        "opta_id": "dm5ka0os1e3dxcp3vh05kmp33",
        "archive_id": 6,
        "league_id": 6,
    },
    "champions-league": {
        "name": "UEFA Sampiyonlar Ligi",
        "country": "Avrupa",
        "url_slug": "avrupa-sampiyonlar-ligi",
        "opta_id": "4oogyu6o156iphvdvphwpck10",
        "archive_id": 42,
        "league_id": 42,
        "is_cup": True,
    },
    "europa-league": {
        "name": "UEFA Avrupa Ligi",
        "country": "Avrupa",
        "url_slug": "avrupa-avrupa-ligi",
        "opta_id": "4c1nfi2j1m731hcay25fcgndq",
        "archive_id": 73,
        "league_id": 73,
        "is_cup": True,
    },
}

URL_PATTERNS = {
    "standings": "/puan-durumu/{slug}/{opta_id}",
    "standings_season": "/puan-durumu/{slug}/{season}/{opta_id}",
    "statistics": "/puan-durumu/{slug}/istatistik/{opta_id}",
    "statistics_season": "/puan-durumu/{slug}/{season}/istatistik/{opta_id}",
    "fixtures": "/puan-durumu/{slug}/fikstur/{opta_id}",
    "cup_standings": "/kupa/{slug}/{season}/{opta_id}",
    "cup_statistics": "/kupa/{slug}/{season}/istatistik/{opta_id}",
    "live_scores": "/canli-sonuclar",
    "archive_standings": "/Puan-Durumu/{archive_id}",
}

STAT_CATEGORIES = {
    "gol-kralligi": "Gol Kralligi",
    "asist": "Asist",
    "sari-kart": "Sari Kart",
    "kirmizi-kart": "Kirmizi Kart",
    "penalti": "Penalti",
    "kendi-kalesine-gol": "Kendi Kalesine Gol",
    "ilk-11": "Ilk 11",
    "yedek": "Yedek",
}
