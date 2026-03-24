"""Maçkolik scraper modules."""

from mackolik.scrapers.standings import fetch_standings
from mackolik.scrapers.matches import fetch_matches, fetch_results, fetch_fixtures
from mackolik.scrapers.player_stats import (
    fetch_top_scorers,
    fetch_top_assists,
    fetch_yellow_cards,
    fetch_red_cards,
    fetch_all_player_stats,
)
from mackolik.scrapers.team_stats import fetch_team_stats, fetch_team_form
from mackolik.scrapers.live_scores import fetch_live_scores, fetch_todays_matches, fetch_live_by_date

__all__ = [
    "fetch_standings",
    "fetch_matches",
    "fetch_results",
    "fetch_fixtures",
    "fetch_top_scorers",
    "fetch_top_assists",
    "fetch_yellow_cards",
    "fetch_red_cards",
    "fetch_all_player_stats",
    "fetch_team_stats",
    "fetch_team_form",
    "fetch_live_scores",
    "fetch_todays_matches",
    "fetch_live_by_date",
]
