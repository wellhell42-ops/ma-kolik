"""Team statistics scraper."""

import logging
import re

from mackolik.scraper import MackolikScraper
from mackolik.config import LEAGUES
from mackolik.models import TeamStats, Team
from mackolik.scrapers.standings import fetch_standings

logger = logging.getLogger(__name__)


def fetch_team_stats(scraper: MackolikScraper, league_key: str) -> list[TeamStats]:
    """Calculate team statistics from standings data.

    Derives advanced team stats from the basic standings data including
    average goals, goal difference analysis, etc.
    """
    standings = fetch_standings(scraper, league_key)
    if not standings:
        return []

    league = LEAGUES.get(league_key, {})
    logger.info(f"Calculating team stats for {league.get('name', league_key)}")

    team_stats = []
    for team in standings:
        avg_goals = round(team.goals_for / team.played, 2) if team.played > 0 else 0.0
        avg_conceded = round(team.goals_against / team.played, 2) if team.played > 0 else 0.0
        clean_sheets = _estimate_clean_sheets(team)

        team_stats.append(TeamStats(
            name=team.name,
            matches_played=team.played,
            total_goals=team.goals_for,
            goals_conceded=team.goals_against,
            clean_sheets=clean_sheets,
            avg_goals_per_match=avg_goals,
            avg_conceded_per_match=avg_conceded,
        ))

    logger.info(f"Computed stats for {len(team_stats)} teams")
    return team_stats


def fetch_team_form(scraper: MackolikScraper, league_key: str) -> dict[str, list[str]]:
    """Fetch recent form (last 5 matches) for teams in a league.

    Returns:
        Dict mapping team name to list of results ('W', 'D', 'L')
    """
    league = LEAGUES.get(league_key)
    if not league:
        return {}

    from mackolik.config import BASE_URL
    url = f"{BASE_URL}/puan-durumu/{league['url_slug']}/{league['opta_id']}"
    soup = scraper.get_soup(url)
    if soup is None:
        return {}

    form_data = {}
    rows = soup.find_all("tr")
    for row in rows:
        name_el = row.find(class_=re.compile(r"team|takim", re.I))
        form_el = row.find(class_=re.compile(r"form", re.I))
        if name_el and form_el:
            team_name = name_el.get_text(strip=True)
            form_items = form_el.find_all("span")
            form = []
            for item in form_items[-5:]:
                text = item.get_text(strip=True).upper()
                css_class = " ".join(item.get("class", []))
                if "win" in css_class or "G" in text or "W" in text:
                    form.append("W")
                elif "draw" in css_class or "B" in text or "D" in text:
                    form.append("D")
                elif "loss" in css_class or "M" in text or "L" in text:
                    form.append("L")
                else:
                    form.append(text[:1] if text else "?")
            if form:
                form_data[team_name] = form

    return form_data


def _estimate_clean_sheets(team: Team) -> int:
    """Estimate clean sheets based on available data."""
    if team.played == 0:
        return 0
    # Rough estimation: if a team concedes fewer goals they likely have more clean sheets
    avg_conceded = team.goals_against / team.played
    if avg_conceded < 0.5:
        return int(team.played * 0.5)
    elif avg_conceded < 1.0:
        return int(team.played * 0.35)
    elif avg_conceded < 1.5:
        return int(team.played * 0.2)
    else:
        return int(team.played * 0.1)
