"""Match results and fixtures scraper."""

import logging
import re
from typing import Optional

from mackolik.scraper import MackolikScraper
from mackolik.config import BASE_URL, LEAGUES
from mackolik.models import Match

logger = logging.getLogger(__name__)


def fetch_matches(scraper: MackolikScraper, league_key: str, week: Optional[int] = None) -> list[Match]:
    """Fetch match results/fixtures for a league.

    Args:
        scraper: MackolikScraper instance
        league_key: Key from LEAGUES config
        week: Optional matchday/week number

    Returns:
        List of Match objects
    """
    league = LEAGUES.get(league_key)
    if not league:
        logger.error(f"Unknown league: {league_key}")
        return []

    url = f"{BASE_URL}/program/{league['url_slug']}/{league['opta_id']}"
    if week:
        url += f"?hafta={week}"

    logger.info(f"Fetching matches: {league['name']}" + (f" (Week {week})" if week else ""))
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    matches = []

    # Try to find match containers
    match_rows = soup.find_all("div", class_=re.compile(r"match|mac-row|fixture", re.I))
    if not match_rows:
        match_rows = soup.find_all("tr", class_=re.compile(r"match|mac", re.I))

    if not match_rows:
        # Try table-based layout
        return _parse_table_matches(soup, league)

    for row in match_rows:
        match = _parse_match_row(row)
        if match:
            matches.append(match)

    logger.info(f"Found {len(matches)} matches for {league['name']}")
    return matches


def fetch_results(scraper: MackolikScraper, league_key: str) -> list[Match]:
    """Fetch completed match results."""
    league = LEAGUES.get(league_key)
    if not league:
        return []

    url = f"{BASE_URL}/sonuclar/{league['url_slug']}/{league['opta_id']}"
    logger.info(f"Fetching results: {league['name']}")
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    return _extract_matches_from_page(soup)


def fetch_fixtures(scraper: MackolikScraper, league_key: str) -> list[Match]:
    """Fetch upcoming fixtures."""
    league = LEAGUES.get(league_key)
    if not league:
        return []

    url = f"{BASE_URL}/program/{league['url_slug']}/{league['opta_id']}"
    logger.info(f"Fetching fixtures: {league['name']}")
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    return _extract_matches_from_page(soup)


def _parse_match_row(row) -> Optional[Match]:
    """Parse a single match row element."""
    try:
        home_el = row.find(class_=re.compile(r"home|ev-sahibi", re.I))
        away_el = row.find(class_=re.compile(r"away|deplasman|misafir", re.I))
        score_el = row.find(class_=re.compile(r"score|skor|sonuc", re.I))
        time_el = row.find(class_=re.compile(r"time|saat|tarih", re.I))

        if not home_el or not away_el:
            # Try link-based extraction
            links = row.find_all("a")
            team_links = [l for l in links if "/takim/" in str(l.get("href", "")) or "/team/" in str(l.get("href", ""))]
            if len(team_links) >= 2:
                home_team = team_links[0].get_text(strip=True)
                away_team = team_links[1].get_text(strip=True)
            else:
                return None
        else:
            home_team = home_el.get_text(strip=True)
            away_team = away_el.get_text(strip=True)

        home_score = None
        away_score = None
        status = "scheduled"

        if score_el:
            score_text = score_el.get_text(strip=True)
            score_match = re.search(r"(\d+)\s*[-–:]\s*(\d+)", score_text)
            if score_match:
                home_score = int(score_match.group(1))
                away_score = int(score_match.group(2))
                status = "played"

        date_str = ""
        time_str = ""
        if time_el:
            dt_text = time_el.get_text(strip=True)
            date_match = re.search(r"(\d{2}\.\d{2}\.\d{4})", dt_text)
            time_match = re.search(r"(\d{2}:\d{2})", dt_text)
            if date_match:
                date_str = date_match.group(1)
            if time_match:
                time_str = time_match.group(1)

        return Match(
            home_team=home_team,
            away_team=away_team,
            home_score=home_score,
            away_score=away_score,
            date=date_str,
            time=time_str,
            status=status,
        )
    except Exception as e:
        logger.debug(f"Failed to parse match row: {e}")
        return None


def _parse_table_matches(soup, league: dict) -> list[Match]:
    """Parse matches from table layout."""
    matches = []
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            texts = [c.get_text(strip=True) for c in cells]
            # Look for pattern: home_team  score  away_team
            for i in range(len(texts) - 2):
                score_match = re.search(r"^(\d+)\s*[-–:]\s*(\d+)$", texts[i + 1])
                if score_match and texts[i] and texts[i + 2]:
                    matches.append(Match(
                        home_team=texts[i],
                        away_team=texts[i + 2],
                        home_score=int(score_match.group(1)),
                        away_score=int(score_match.group(2)),
                        status="played",
                    ))
                    break

    return matches


def _extract_matches_from_page(soup) -> list[Match]:
    """Generic match extraction from any page."""
    matches = []

    # Method 1: div-based
    match_divs = soup.find_all("div", class_=re.compile(r"match|mac|fixture|game", re.I))
    for div in match_divs:
        m = _parse_match_row(div)
        if m:
            matches.append(m)

    if matches:
        return matches

    # Method 2: table-based
    return _parse_table_matches(soup, {})
