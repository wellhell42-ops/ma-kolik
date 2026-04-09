"""Live scores scraper with JSON API and HTML fallback support."""

import logging
import re
from datetime import datetime

from mackolik.scraper import MackolikScraper
from mackolik.config import BASE_URL, API_URLS, API_HEADERS
from mackolik.models import LiveMatch

logger = logging.getLogger(__name__)

# Known league ID to name mapping from the livedata API
_LEAGUE_NAMES = {}


def fetch_live_scores(scraper: MackolikScraper) -> list[LiveMatch]:
    """Fetch current live match scores.

    Tries JSON API first, falls back to HTML scraping.

    Returns:
        List of LiveMatch objects for currently active matches
    """
    logger.info("Fetching live scores")

    # Try JSON API first
    matches = _fetch_via_json_api(scraper)
    if matches:
        return matches

    # Fallback to HTML scraping
    return _fetch_via_html(scraper)


def fetch_todays_matches(scraper: MackolikScraper) -> list[LiveMatch]:
    """Fetch all of today's matches (live, played, scheduled).

    Returns:
        List of LiveMatch objects
    """
    logger.info("Fetching today's matches")

    # Try JSON API first (returns all matches for the day)
    matches = _fetch_via_json_api(scraper)
    if matches:
        return matches

    # Fallback to HTML scraping
    return _fetch_via_html(scraper)


def fetch_live_by_date(scraper: MackolikScraper, date: datetime) -> list[LiveMatch]:
    """Fetch match data for a specific date via the JSON API.

    Args:
        scraper: MackolikScraper instance
        date: The date to fetch matches for

    Returns:
        List of LiveMatch objects
    """
    date_str = date.strftime("%d/%m/%Y")
    logger.info(f"Fetching matches for date: {date_str}")
    return _fetch_via_json_api(scraper, date_str=date_str)


def _fetch_via_json_api(scraper: MackolikScraper, date_str: str | None = None) -> list[LiveMatch]:
    """Fetch live data from the Maçkolik JSON API.

    The API returns match data in a compact array format where each match
    is an indexed array with fields at known positions.

    API response structure:
        m: list of match arrays
        Each match array indices:
            0: match_id
            1: league_id
            2: home_team name
            3: home_team_id
            4: away_team name
            5: away_team_id
            6: status (e.g., "MS" = full-time, "1Y" = first half, "DV" = half-time)
            7: half-time score ("1-0")
            16: match_time ("21:45")
            23: sport_type (1 = football)
            29: home_score (full-time)
            30: away_score (full-time)
            36: metadata list (index 9 = league name)
    """
    # Try primary API endpoint
    for api_key in ("livedata", "livedata_legacy"):
        api_url = API_URLS.get(api_key)
        if not api_url:
            continue

        params = {}
        if date_str:
            params["date"] = date_str

        data = scraper.get_json(api_url, params=params, headers=API_HEADERS)
        if data and "m" in data:
            return _parse_livedata_json(data)

    return []


def _parse_livedata_json(data: dict) -> list[LiveMatch]:
    """Parse the livedata JSON response into LiveMatch objects."""
    matches = []
    match_list = data.get("m", [])

    for m in match_list:
        try:
            if not isinstance(m, (list, tuple)) or len(m) < 7:
                continue

            # Only football matches (sport_type == 1)
            sport_type = m[23] if len(m) > 23 else 1
            if sport_type != 1:
                continue

            home_team = str(m[2]) if m[2] else ""
            away_team = str(m[4]) if m[4] else ""
            if not home_team or not away_team:
                continue

            # Extract scores
            home_score = 0
            away_score = 0

            # Try full-time score first (indices 29-30)
            if len(m) > 30 and m[29] is not None and m[30] is not None:
                try:
                    home_score = int(m[29])
                    away_score = int(m[30])
                except (ValueError, TypeError):
                    pass

            # Fall back to half-time score if no full-time score
            if home_score == 0 and away_score == 0 and m[7]:
                score_text = str(m[7])
                score_match = re.search(r"(\d+)\s*[-–]\s*(\d+)", score_text)
                if score_match:
                    home_score = int(score_match.group(1))
                    away_score = int(score_match.group(2))

            # Status mapping
            raw_status = str(m[6]) if m[6] else ""
            status, minute = _map_status(raw_status)

            # Match time
            match_time = str(m[16]) if len(m) > 16 and m[16] else ""
            if not minute and match_time:
                minute = match_time

            # League name from metadata
            league_name = ""
            if len(m) > 36 and isinstance(m[36], (list, tuple)) and len(m[36]) > 9:
                league_name = str(m[36][9]) if m[36][9] else ""

            # Cache league name by ID
            league_id = m[1] if len(m) > 1 else None
            if league_name and league_id:
                _LEAGUE_NAMES[league_id] = league_name
            elif not league_name and league_id and league_id in _LEAGUE_NAMES:
                league_name = _LEAGUE_NAMES[league_id]

            matches.append(LiveMatch(
                home_team=home_team,
                away_team=away_team,
                home_score=home_score,
                away_score=away_score,
                minute=minute,
                league=league_name,
                status=status,
            ))
        except (IndexError, TypeError, ValueError) as e:
            logger.debug(f"Skipping match entry: {e}")
            continue

    logger.info(f"Parsed {len(matches)} matches from JSON API")
    return matches


def _map_status(raw: str) -> tuple[str, str]:
    """Map Maçkolik status codes to readable status and minute.

    Known status codes:
        MS = Maç Sonu (full-time)
        1Y = 1. Yarı (first half)
        2Y = 2. Yarı (second half)
        DV = Devre (half-time)
        YO = Yarıda (abandoned)
        IP = İptal (cancelled)
        ER = Ertelendi (postponed)
        UZ = Uzatma (extra time)
        PEN = Penaltı (penalties)
        HS = Henüz Başlamadı (not started)
    """
    status_map = {
        "MS": ("finished", "MS"),
        "1Y": ("live", ""),
        "2Y": ("live", ""),
        "DV": ("half-time", "DV"),
        "YO": ("abandoned", "YO"),
        "IP": ("cancelled", "İP"),
        "ER": ("postponed", "ERT"),
        "UZ": ("extra-time", "UZ"),
        "PEN": ("penalties", "PEN"),
        "HS": ("scheduled", ""),
    }

    # Check if status contains a minute number (e.g., "45", "90+3")
    minute_match = re.match(r"^(\d+(?:\+\d+)?)['\u2032]?$", raw.strip())
    if minute_match:
        return "live", f"{minute_match.group(1)}'"

    if raw in status_map:
        return status_map[raw]

    return raw or "unknown", raw


# --- HTML fallback methods ---

def _fetch_via_html(scraper: MackolikScraper) -> list[LiveMatch]:
    """Fallback: fetch live scores via HTML scraping."""
    url = f"{BASE_URL}/canli-sonuclar"
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    matches = []

    # Try finding match containers
    match_containers = soup.find_all("div", class_=re.compile(r"match|mac|live|canli", re.I))

    for container in match_containers:
        match = _parse_live_match_html(container)
        if match:
            matches.append(match)

    if not matches:
        matches = _try_table_layout(soup)

    logger.info(f"Found {len(matches)} matches via HTML scraping")
    return matches


def _parse_live_match_html(container) -> LiveMatch | None:
    """Parse a single live match from HTML element."""
    try:
        home_el = container.find(class_=re.compile(r"home|ev", re.I))
        away_el = container.find(class_=re.compile(r"away|dep|misafir", re.I))
        score_el = container.find(class_=re.compile(r"score|skor", re.I))
        minute_el = container.find(class_=re.compile(r"minute|dakika|min|time|status", re.I))

        if not home_el or not away_el:
            teams = container.find_all("a", class_=re.compile(r"team|takim", re.I))
            if len(teams) < 2:
                teams = container.find_all("span", class_=re.compile(r"team|takim", re.I))
            if len(teams) < 2:
                return None
            home_team = teams[0].get_text(strip=True)
            away_team = teams[1].get_text(strip=True)
        else:
            home_team = home_el.get_text(strip=True)
            away_team = away_el.get_text(strip=True)

        if not home_team or not away_team:
            return None

        home_score = 0
        away_score = 0
        if score_el:
            score_text = score_el.get_text(strip=True)
            score_match = re.search(r"(\d+)\s*[-–:]\s*(\d+)", score_text)
            if score_match:
                home_score = int(score_match.group(1))
                away_score = int(score_match.group(2))

        minute = ""
        status = ""
        if minute_el:
            minute_text = minute_el.get_text(strip=True)
            min_match = re.search(r"(\d+)['\u2032]?", minute_text)
            if min_match:
                minute = min_match.group(1) + "'"
                status = "live"
            elif re.search(r"(MS|FT|Bitti)", minute_text, re.I):
                status = "finished"
            elif re.search(r"(DV|HT|Devre)", minute_text, re.I):
                status = "half-time"
                minute = "DV"
            else:
                minute = minute_text
                status = "scheduled"

        return LiveMatch(
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            minute=minute,
            status=status,
        )
    except Exception as e:
        logger.debug(f"Failed to parse live match: {e}")
        return None


def _try_table_layout(soup) -> list[LiveMatch]:
    """Fallback: try parsing live scores from table layout."""
    matches = []
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            texts = [c.get_text(strip=True) for c in cells]
            for i in range(len(texts) - 2):
                score_match = re.search(r"^(\d+)\s*[-–:]\s*(\d+)$", texts[i + 1])
                if score_match and texts[i] and texts[i + 2]:
                    matches.append(LiveMatch(
                        home_team=texts[i],
                        away_team=texts[i + 2],
                        home_score=int(score_match.group(1)),
                        away_score=int(score_match.group(2)),
                        status="live",
                    ))
                    break
    return matches
