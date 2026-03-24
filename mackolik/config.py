"""Maçkolik scraper configuration."""

BASE_URL = "https://www.mackolik.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

REQUEST_TIMEOUT = 30
REQUEST_DELAY = 1.5  # seconds between requests to be respectful

# Popular leagues with their Maçkolik URL slugs
LEAGUES = {
    "super-lig": {
        "name": "Türkiye Süper Lig",
        "country": "Türkiye",
        "url_slug": "turkiye-super-lig",
        "opta_id": "482ofyysbdbeoxauk19yg7tdt",
    },
    "1-lig": {
        "name": "Türkiye 1. Lig",
        "country": "Türkiye",
        "url_slug": "turkiye-1-lig",
        "opta_id": "a]",
    },
    "premier-league": {
        "name": "İngiltere Premier Lig",
        "country": "İngiltere",
        "url_slug": "ingiltere-premier-lig",
        "opta_id": "1jt5mxgn4q5r6mknmlqv5qjh0",
    },
    "la-liga": {
        "name": "İspanya La Liga",
        "country": "İspanya",
        "url_slug": "ispanya-la-liga",
        "opta_id": "34pl8szyvrbwcmfkuocjm3r6t",
    },
    "bundesliga": {
        "name": "Almanya Bundesliga",
        "country": "Almanya",
        "url_slug": "almanya-bundesliga",
        "opta_id": "6by3h89i2eykc341oz7lv1ddd",
    },
    "serie-a": {
        "name": "İtalya Serie A",
        "country": "İtalya",
        "url_slug": "italya-serie-a",
        "opta_id": "1r097lpxe0xn03ihb7wi98kao",
    },
    "ligue-1": {
        "name": "Fransa Ligue 1",
        "country": "Fransa",
        "url_slug": "fransa-ligue-1",
        "opta_id": "dm5ka0os1e3dxcp3vh05kmp33",
    },
    "champions-league": {
        "name": "UEFA Şampiyonlar Ligi",
        "country": "Avrupa",
        "url_slug": "sampiyonlar-ligi",
        "opta_id": "4oogyu6o156iphvdvphwpck10",
    },
}

# Statistics categories available on Maçkolik
STAT_CATEGORIES = {
    "gol-kralligi": "Gol Krallığı",
    "asist": "Asist",
    "sari-kart": "Sarı Kart",
    "kirmizi-kart": "Kırmızı Kart",
    "penalti": "Penaltı",
    "kendi-kalesine-gol": "Kendi Kalesine Gol",
    "ilk-11": "İlk 11",
    "yedek": "Yedek",
    "gol-dakikalari": "Gol Dakikaları",
}
