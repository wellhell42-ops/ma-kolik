"""Puan durumu (league standings) scraper."""

import logging
import re
from typing import Optional

from mackolik.scraper import MackolikScraper
from mackolik.config import BASE_URL, LEAGUES
from mackolik.models import Team

logger = logging.getLogger(__name__)


def fetch_standings(scraper: MackolikScraper, league_key: str) -> list[Team]:
    """Fetch league standings for a given league.

    Args:
        scraper: MackolikScraper instance
        league_key: Key from LEAGUES config (e.g., 'super-lig')

    Returns:
        List of Team objects with standings data
    """
    league = LEAGUES.get(league_key)
    if not league:
        logger.error(f"Unknown league: {league_key}")
        return []

    url = f"{BASE_URL}/puan-durumu/{league['url_slug']}/{league['opta_id']}"
    logger.info(f"Fetching standings: {league['name']}")
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    teams = []
    table = soup.find("table", class_=re.compile(r"standing|puan", re.I))
    if not table:
        table = soup.find("table")

    if not table:
        logger.warning(f"No standings table found for {league['name']}")
        return _try_alternative_standings(scraper, league)

    rows = table.find_all("tr")
    for row in rows[1:]:  # skip header
        cells = row.find_all("td")
        if len(cells) < 8:
            continue
        try:
            position = _clean_int(cells[0].get_text(strip=True))
            name = cells[1].get_text(strip=True)
            played = _clean_int(cells[2].get_text(strip=True))
            won = _clean_int(cells[3].get_text(strip=True))
            drawn = _clean_int(cells[4].get_text(strip=True))
            lost = _clean_int(cells[5].get_text(strip=True))

            # Goals for:against format or separate columns
            goals_text = cells[6].get_text(strip=True)
            if ":" in goals_text:
                gf, ga = goals_text.split(":")
                goals_for = _clean_int(gf)
                goals_against = _clean_int(ga)
                points = _clean_int(cells[7].get_text(strip=True))
            else:
                goals_for = _clean_int(goals_text)
                goals_against = _clean_int(cells[7].get_text(strip=True))
                points = _clean_int(cells[8].get_text(strip=True)) if len(cells) > 8 else 0

            teams.append(Team(
                name=name,
                played=played,
                won=won,
                drawn=drawn,
                lost=lost,
                goals_for=goals_for,
                goals_against=goals_against,
                goal_difference=goals_for - goals_against,
                points=points,
                position=position,
            ))
        except (ValueError, IndexError) as e:
            logger.debug(f"Skipping row: {e}")
            continue

    logger.info(f"Found {len(teams)} teams in standings for {league['name']}")
    return teams


def _try_alternative_standings(scraper: MackolikScraper, league: dict) -> list[Team]:
    """Try alternative page structure for standings."""
    url = f"{BASE_URL}/{league['url_slug']}/puan-durumu"
    soup = scraper.get_soup(url)
    if soup is None:
        return []

    teams = []
    # Try div-based layout
    rows = soup.find_all("div", class_=re.compile(r"standing-row|team-row", re.I))
    for i, row in enumerate(rows):
        name_el = row.find(class_=re.compile(r"team-name|name", re.I))
        if not name_el:
            continue
        cells = row.find_all(class_=re.compile(r"cell|col|stat", re.I))
        if len(cells) < 7:
            continue
        try:
            teams.append(Team(
                name=name_el.get_text(strip=True),
                played=_clean_int(cells[0].get_text(strip=True)),
                won=_clean_int(cells[1].get_text(strip=True)),
                drawn=_clean_int(cells[2].get_text(strip=True)),
                lost=_clean_int(cells[3].get_text(strip=True)),
                goals_for=_clean_int(cells[4].get_text(strip=True)),
                goals_against=_clean_int(cells[5].get_text(strip=True)),
                goal_difference=0,
                points=_clean_int(cells[6].get_text(strip=True)),
                position=i + 1,
            ))
        except (ValueError, IndexError):
            continue

    if teams:
        for t in teams:
            t.goal_difference = t.goals_for - t.goals_against

    return teams


def _clean_int(text: str) -> int:
    """Extract integer from text, handling various formats."""
    cleaned = re.sub(r"[^\d-]", "", text)
    return int(cleaned) if cleaned else 0
