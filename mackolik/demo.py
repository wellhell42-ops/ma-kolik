"""Demo/sample data for testing without network access.

When the scraper can't reach mackolik.com (e.g., geo-blocked, network issues),
this module provides realistic sample data for demonstration purposes.
"""

from mackolik.models import Team, PlayerStat, Match, LiveMatch, TeamStats


def get_sample_standings(league_key: str) -> list[Team]:
    """Return sample standings data for a league."""
    if league_key == "super-lig":
        return [
            Team(name="Galatasaray", played=30, won=22, drawn=5, lost=3, goals_for=68, goals_against=22, goal_difference=46, points=71, position=1),
            Team(name="Fenerbahçe", played=30, won=21, drawn=6, lost=3, goals_for=72, goals_against=28, goal_difference=44, points=69, position=2),
            Team(name="Beşiktaş", played=30, won=17, drawn=5, lost=8, goals_for=55, goals_against=35, goal_difference=20, points=56, position=3),
            Team(name="Trabzonspor", played=30, won=15, drawn=7, lost=8, goals_for=48, goals_against=32, goal_difference=16, points=52, position=4),
            Team(name="Başakşehir", played=30, won=14, drawn=8, lost=8, goals_for=42, goals_against=30, goal_difference=12, points=50, position=5),
            Team(name="Adana Demirspor", played=30, won=13, drawn=6, lost=11, goals_for=45, goals_against=40, goal_difference=5, points=45, position=6),
            Team(name="Antalyaspor", played=30, won=12, drawn=7, lost=11, goals_for=38, goals_against=36, goal_difference=2, points=43, position=7),
            Team(name="Konyaspor", played=30, won=11, drawn=8, lost=11, goals_for=35, goals_against=38, goal_difference=-3, points=41, position=8),
            Team(name="Sivasspor", played=30, won=10, drawn=9, lost=11, goals_for=33, goals_against=37, goal_difference=-4, points=39, position=9),
            Team(name="Kasımpaşa", played=30, won=10, drawn=7, lost=13, goals_for=38, goals_against=45, goal_difference=-7, points=37, position=10),
        ]
    # Generic sample for other leagues
    return [
        Team(name=f"Takım {i}", played=30, won=max(0, 20 - i * 2), drawn=5, lost=min(25, 5 + i * 2),
             goals_for=max(10, 60 - i * 5), goals_against=20 + i * 3,
             goal_difference=max(10, 60 - i * 5) - (20 + i * 3),
             points=max(0, 20 - i * 2) * 3 + 5, position=i)
        for i in range(1, 11)
    ]


def get_sample_player_stats(league_key: str, category: str) -> list[PlayerStat]:
    """Return sample player statistics."""
    if category == "gol-kralligi":
        return [
            PlayerStat(rank=1, name="Victor Osimhen", team="Galatasaray", value=22, matches_played=28, category="Gol Krallığı"),
            PlayerStat(rank=2, name="Edin Dzeko", team="Fenerbahçe", value=18, matches_played=29, category="Gol Krallığı"),
            PlayerStat(rank=3, name="Ciro Immobile", team="Beşiktaş", value=15, matches_played=27, category="Gol Krallığı"),
            PlayerStat(rank=4, name="Mauro Icardi", team="Galatasaray", value=14, matches_played=22, category="Gol Krallığı"),
            PlayerStat(rank=5, name="Vincent Aboubakar", team="Trabzonspor", value=12, matches_played=26, category="Gol Krallığı"),
        ]
    elif category == "asist":
        return [
            PlayerStat(rank=1, name="Dries Mertens", team="Galatasaray", value=14, matches_played=28, category="Asist"),
            PlayerStat(rank=2, name="Fred", team="Fenerbahçe", value=11, matches_played=30, category="Asist"),
            PlayerStat(rank=3, name="Hakan Çalhanoğlu", team="Fenerbahçe", value=10, matches_played=25, category="Asist"),
            PlayerStat(rank=4, name="Rachid Ghezzal", team="Beşiktaş", value=9, matches_played=27, category="Asist"),
            PlayerStat(rank=5, name="Kerem Aktürkoğlu", team="Galatasaray", value=8, matches_played=29, category="Asist"),
        ]
    elif category == "sari-kart":
        return [
            PlayerStat(rank=1, name="Atakan Karazor", team="Sivasspor", value=10, matches_played=28, category="Sarı Kart"),
            PlayerStat(rank=2, name="Okay Yokuşlu", team="Trabzonspor", value=9, matches_played=27, category="Sarı Kart"),
            PlayerStat(rank=3, name="İsmail Yüksek", team="Fenerbahçe", value=8, matches_played=29, category="Sarı Kart"),
        ]
    elif category == "kirmizi-kart":
        return [
            PlayerStat(rank=1, name="Saiss", team="Beşiktaş", value=2, matches_played=25, category="Kırmızı Kart"),
            PlayerStat(rank=2, name="Ndao", team="Kasımpaşa", value=2, matches_played=22, category="Kırmızı Kart"),
        ]
    return []


def get_sample_matches(league_key: str) -> list[Match]:
    """Return sample match data."""
    return [
        Match(home_team="Galatasaray", away_team="Fenerbahçe", home_score=2, away_score=1, date="15.03.2026", time="20:00", status="played", week=28),
        Match(home_team="Beşiktaş", away_team="Trabzonspor", home_score=1, away_score=1, date="15.03.2026", time="17:00", status="played", week=28),
        Match(home_team="Başakşehir", away_team="Antalyaspor", home_score=3, away_score=0, date="16.03.2026", time="19:00", status="played", week=28),
        Match(home_team="Fenerbahçe", away_team="Beşiktaş", home_score=None, away_score=None, date="22.03.2026", time="20:00", status="scheduled", week=29),
        Match(home_team="Trabzonspor", away_team="Galatasaray", home_score=None, away_score=None, date="23.03.2026", time="19:00", status="scheduled", week=29),
    ]


def get_sample_live_scores() -> list[LiveMatch]:
    """Return sample live score data."""
    return [
        LiveMatch(home_team="Galatasaray", away_team="Sivasspor", home_score=2, away_score=0, minute="67'", league="Süper Lig", status="live"),
        LiveMatch(home_team="Fenerbahçe", away_team="Kasımpaşa", home_score=1, away_score=1, minute="DV", league="Süper Lig", status="half-time"),
        LiveMatch(home_team="Manchester City", away_team="Arsenal", home_score=0, away_score=0, minute="12'", league="Premier Lig", status="live"),
        LiveMatch(home_team="Barcelona", away_team="Real Madrid", home_score=3, away_score=2, minute="MS", league="La Liga", status="finished"),
        LiveMatch(home_team="Beşiktaş", away_team="Trabzonspor", home_score=None, away_score=None, minute="21:00", league="Süper Lig", status="scheduled"),  # type: ignore[arg-type]
    ]
