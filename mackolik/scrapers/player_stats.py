"""Player statistics scraper (goals, assists, cards, etc.)."""

import logging
import re
from typing import Optional

from mackolik.scraper import MackolikScraper
from mackolik.config import BASE_URL, LEAGUES, STAT_CATEGORIES
from mackolik.models import PlayerStat

logger = logging.getLogger(__name__)


def fetch_top_scorers(scraper: MackolikScraper, league_key: str) -> list[PlayerStat]:
    """Fetch top scorers for a league."""
    return _fetch_player_stat(scraper, league_key, "gol-kralligi")


def fetch_top_assists(scraper: MackolikScraper, league_key: str) -> list[PlayerStat]:
    """Fetch top assist providers for a league."""
    return _fetch_player_stat(scraper, league_key, "asist")


def fetch_yellow_cards(scraper: MackolikScraper, league_key: str) -> list[PlayerStat]:
    """Fetch yellow card leaders for a league."""
    return _fetch_player_stat(scraper, league_key, "sari-kart")


def fetch_red_cards(scraper: MackolikScraper, league_key: str) -> list[PlayerStat]:
    """Fetch red card leaders for a league."""
    return _fetch_player_stat(scraper, league_key, "kirmizi-kart")


def fetch_all_player_stats(scraper: MackolikScraper, league_key: str) -> dict[str, list[PlayerStat]]:
    """Fetch all available player statistics for a league.

    Returns:
        Dict mapping category name to list of PlayerStat
    """
    results = {}
    for cat_key, cat_name in STAT_CATEGORIES.items():
        stats = _fetch_player_stat(scraper, league_key, cat_key)
        if stats:
            results[cat_name] = stats
    return results


def _fetch_player_stat(scraper: MackolikScraper, league_key: str, stat_key: str) -> list[PlayerStat]:
    """Fetch a specific player statistic category."""
    league = LEAGUES.get(league_key)
    if not league:
        logger.error(f"Unknown league: {league_key}")
        return []

    cat_name = STAT_CATEGORIES.get(stat_key, stat_key)
    logger.info(f"Fetching {cat_name}: {league['name']}")

    # Try multiple URL patterns
    urls = [
        f"{BASE_URL}/istatistik/{league['url_slug']}/{stat_key}/{league['opta_id']}",
        f"{BASE_URL}/puan-durumu/{league['url_slug']}/istatistik/{stat_key}/{league['opta_id']}",
        f"{BASE_URL}/{league['url_slug']}/istatistik/{stat_key}",
    ]

    for url in urls:
        soup = scraper.get_soup(url)
        if soup is None:
            continue

        players = _parse_player_stats_page(soup, cat_name)
        if players:
            logger.info(f"Found {len(players)} players for {cat_name}")
            return players

    logger.warning(f"Could not fetch {cat_name} for {league['name']}")
    return []


def _parse_player_stats_page(soup, category: str) -> list[PlayerStat]:
    """Parse player statistics from page HTML."""
    players = []

    # Method 1: Table-based layout
    table = soup.find("table", class_=re.compile(r"stat|istatistik|player|ranking", re.I))
    if not table:
        table = soup.find("table")

    if table:
        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = row.find_all("td")
            if len(cells) < 3:
                continue
            try:
                rank_text = cells[0].get_text(strip=True)
                rank = _clean_int(rank_text) if rank_text else len(players) + 1

                name = cells[1].get_text(strip=True)
                # Sometimes name cell contains team too
                team = cells[2].get_text(strip=True) if len(cells) > 3 else ""

                # Value is usually the last significant column
                value_idx = -1
                for idx in range(len(cells) - 1, 1, -1):
                    val_text = cells[idx].get_text(strip=True)
                    if val_text and re.match(r"^\d+$", val_text):
                        value_idx = idx
                        break

                value = _clean_int(cells[value_idx].get_text(strip=True)) if value_idx > 0 else 0

                matches_played = 0
                if len(cells) > 4:
                    for idx in range(3, len(cells) - 1):
                        mp_text = cells[idx].get_text(strip=True)
                        if mp_text and re.match(r"^\d+$", mp_text):
                            matches_played = int(mp_text)
                            break

                if name:
                    players.append(PlayerStat(
                        rank=rank or len(players) + 1,
                        name=name,
                        team=team,
                        value=value,
                        matches_played=matches_played,
                        category=category,
                    ))
            except (ValueError, IndexError) as e:
                logger.debug(f"Skipping player row: {e}")
                continue

    if players:
        return players

    # Method 2: Div-based layout
    stat_rows = soup.find_all("div", class_=re.compile(r"player-row|stat-row|ranking-row", re.I))
    for i, row in enumerate(stat_rows):
        try:
            name_el = row.find(class_=re.compile(r"player-name|name", re.I))
            team_el = row.find(class_=re.compile(r"team-name|team", re.I))
            value_el = row.find(class_=re.compile(r"stat-value|value|count|goal|assist|card", re.I))

            if name_el:
                players.append(PlayerStat(
                    rank=i + 1,
                    name=name_el.get_text(strip=True),
                    team=team_el.get_text(strip=True) if team_el else "",
                    value=_clean_int(value_el.get_text(strip=True)) if value_el else 0,
                    category=category,
                ))
        except Exception as e:
            logger.debug(f"Skipping div row: {e}")
            continue

    return players


def _clean_int(text: str) -> int:
    """Extract integer from text."""
    cleaned = re.sub(r"[^\d]", "", text)
    return int(cleaned) if cleaned else 0
