"""Live scores scraper."""

import logging
import re

from mackolik.scraper import MackolikScraper
from mackolik.config import BASE_URL
from mackolik.models import LiveMatch

logger = logging.getLogger(__name__)


def fetch_live_scores(scraper: MackolikScraper) -> list[LiveMatch]:
    """Fetch current live match scores from Maçkolik.

    Returns:
        List of LiveMatch objects for currently active matches
    """
    url = f"{BASE_URL}/canli-sonuclar"
    logger.info("Fetching live scores")
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    matches = []

    # Try finding match containers
    match_containers = soup.find_all("div", class_=re.compile(r"match|mac|live|canli", re.I))

    for container in match_containers:
        match = _parse_live_match(container)
        if match:
            matches.append(match)

    if not matches:
        matches = _try_table_layout(soup)

    logger.info(f"Found {len(matches)} live matches")
    return matches


def fetch_todays_matches(scraper: MackolikScraper) -> list[LiveMatch]:
    """Fetch all of today's matches (live, played, scheduled).

    Returns:
        List of LiveMatch objects
    """
    url = f"{BASE_URL}/canli-sonuclar"
    logger.info("Fetching today's matches")
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    matches = []

    # Get league sections
    league_sections = soup.find_all("div", class_=re.compile(r"league|lig|competition", re.I))

    for section in league_sections:
        league_name = ""
        header = section.find(class_=re.compile(r"header|title|league-name", re.I))
        if header:
            league_name = header.get_text(strip=True)

        match_rows = section.find_all("div", class_=re.compile(r"match|mac|row", re.I))
        for row in match_rows:
            match = _parse_live_match(row)
            if match:
                match.league = league_name
                matches.append(match)

    if not matches:
        # Fallback: parse entire page
        all_rows = soup.find_all("div", class_=re.compile(r"match|mac", re.I))
        for row in all_rows:
            match = _parse_live_match(row)
            if match:
                matches.append(match)

    logger.info(f"Found {len(matches)} today's matches")
    return matches


def _parse_live_match(container) -> LiveMatch | None:
    """Parse a single live match from HTML element."""
    try:
        home_el = container.find(class_=re.compile(r"home|ev", re.I))
        away_el = container.find(class_=re.compile(r"away|dep|misafir", re.I))
        score_el = container.find(class_=re.compile(r"score|skor", re.I))
        minute_el = container.find(class_=re.compile(r"minute|dakika|min|time|status", re.I))

        if not home_el or not away_el:
            # Try extracting from links or spans
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
