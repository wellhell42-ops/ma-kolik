"""Demo/sample data - 2024-25 season realistic data.

Provides realistic sample data for demonstration and offline testing.
"""

from mackolik.models import Team, PlayerStat, Match, LiveMatch, TeamStats


def get_sample_standings(league_key: str) -> list[Team]:
    """Return sample standings data for a league."""
    data = {
        "super-lig": [
            Team(name="Galatasaray", played=30, won=23, drawn=4, lost=3, goals_for=71, goals_against=21, goal_difference=50, points=73, position=1),
            Team(name="Fenerbahce", played=30, won=21, drawn=5, lost=4, goals_for=68, goals_against=25, goal_difference=43, points=68, position=2),
            Team(name="Besiktas", played=30, won=18, drawn=5, lost=7, goals_for=58, goals_against=32, goal_difference=26, points=59, position=3),
            Team(name="Trabzonspor", played=30, won=15, drawn=8, lost=7, goals_for=49, goals_against=30, goal_difference=19, points=53, position=4),
            Team(name="Basaksehir", played=30, won=14, drawn=7, lost=9, goals_for=44, goals_against=33, goal_difference=11, points=49, position=5),
            Team(name="Samsunspor", played=30, won=13, drawn=8, lost=9, goals_for=42, goals_against=35, goal_difference=7, points=47, position=6),
            Team(name="Eyupspor", played=30, won=12, drawn=9, lost=9, goals_for=40, goals_against=34, goal_difference=6, points=45, position=7),
            Team(name="Antalyaspor", played=30, won=12, drawn=7, lost=11, goals_for=38, goals_against=38, goal_difference=0, points=43, position=8),
            Team(name="Sivasspor", played=30, won=11, drawn=8, lost=11, goals_for=36, goals_against=37, goal_difference=-1, points=41, position=9),
            Team(name="Kasimpasa", played=30, won=10, drawn=9, lost=11, goals_for=38, goals_against=40, goal_difference=-2, points=39, position=10),
            Team(name="Konyaspor", played=30, won=10, drawn=7, lost=13, goals_for=33, goals_against=42, goal_difference=-9, points=37, position=11),
            Team(name="Gaziantep FK", played=30, won=9, drawn=8, lost=13, goals_for=31, goals_against=41, goal_difference=-10, points=35, position=12),
            Team(name="Kayserispor", played=30, won=9, drawn=6, lost=15, goals_for=30, goals_against=45, goal_difference=-15, points=33, position=13),
            Team(name="Rizespor", played=30, won=8, drawn=8, lost=14, goals_for=28, goals_against=43, goal_difference=-15, points=32, position=14),
            Team(name="Bodrumspor", played=30, won=8, drawn=7, lost=15, goals_for=27, goals_against=44, goal_difference=-17, points=31, position=15),
            Team(name="Hatayspor", played=30, won=7, drawn=8, lost=15, goals_for=26, goals_against=46, goal_difference=-20, points=29, position=16),
            Team(name="Goztepe", played=30, won=7, drawn=7, lost=16, goals_for=25, goals_against=48, goal_difference=-23, points=28, position=17),
            Team(name="Adana Demirspor", played=30, won=6, drawn=7, lost=17, goals_for=24, goals_against=50, goal_difference=-26, points=25, position=18),
            Team(name="Pendikspor", played=30, won=5, drawn=8, lost=17, goals_for=22, goals_against=49, goal_difference=-27, points=23, position=19),
        ],
        "premier-league": [
            Team(name="Liverpool", played=30, won=22, drawn=5, lost=3, goals_for=65, goals_against=22, goal_difference=43, points=71, position=1),
            Team(name="Arsenal", played=30, won=21, drawn=5, lost=4, goals_for=62, goals_against=24, goal_difference=38, points=68, position=2),
            Team(name="Nottingham Forest", played=30, won=18, drawn=6, lost=6, goals_for=52, goals_against=30, goal_difference=22, points=60, position=3),
            Team(name="Manchester City", played=30, won=17, drawn=5, lost=8, goals_for=58, goals_against=35, goal_difference=23, points=56, position=4),
            Team(name="Chelsea", played=30, won=16, drawn=6, lost=8, goals_for=55, goals_against=34, goal_difference=21, points=54, position=5),
            Team(name="Aston Villa", played=30, won=15, drawn=6, lost=9, goals_for=48, goals_against=38, goal_difference=10, points=51, position=6),
            Team(name="Brighton", played=30, won=13, drawn=8, lost=9, goals_for=47, goals_against=40, goal_difference=7, points=47, position=7),
            Team(name="Bournemouth", played=30, won=13, drawn=7, lost=10, goals_for=45, goals_against=38, goal_difference=7, points=46, position=8),
            Team(name="Newcastle", played=30, won=12, drawn=8, lost=10, goals_for=42, goals_against=36, goal_difference=6, points=44, position=9),
            Team(name="Fulham", played=30, won=11, drawn=9, lost=10, goals_for=38, goals_against=36, goal_difference=2, points=42, position=10),
        ],
        "la-liga": [
            Team(name="Barcelona", played=30, won=22, drawn=4, lost=4, goals_for=72, goals_against=28, goal_difference=44, points=70, position=1),
            Team(name="Real Madrid", played=30, won=20, drawn=6, lost=4, goals_for=60, goals_against=24, goal_difference=36, points=66, position=2),
            Team(name="Atletico Madrid", played=30, won=19, drawn=5, lost=6, goals_for=54, goals_against=28, goal_difference=26, points=62, position=3),
            Team(name="Athletic Bilbao", played=30, won=16, drawn=7, lost=7, goals_for=48, goals_against=30, goal_difference=18, points=55, position=4),
            Team(name="Villarreal", played=30, won=14, drawn=8, lost=8, goals_for=50, goals_against=38, goal_difference=12, points=50, position=5),
        ],
        "bundesliga": [
            Team(name="Bayern Munich", played=28, won=20, drawn=4, lost=4, goals_for=68, goals_against=28, goal_difference=40, points=64, position=1),
            Team(name="Bayer Leverkusen", played=28, won=18, drawn=6, lost=4, goals_for=58, goals_against=26, goal_difference=32, points=60, position=2),
            Team(name="Eintracht Frankfurt", played=28, won=16, drawn=5, lost=7, goals_for=55, goals_against=35, goal_difference=20, points=53, position=3),
            Team(name="Borussia Dortmund", played=28, won=15, drawn=5, lost=8, goals_for=52, goals_against=38, goal_difference=14, points=50, position=4),
            Team(name="RB Leipzig", played=28, won=14, drawn=6, lost=8, goals_for=48, goals_against=35, goal_difference=13, points=48, position=5),
        ],
        "serie-a": [
            Team(name="Napoli", played=30, won=22, drawn=4, lost=4, goals_for=55, goals_against=18, goal_difference=37, points=70, position=1),
            Team(name="Inter Milan", played=30, won=20, drawn=6, lost=4, goals_for=62, goals_against=24, goal_difference=38, points=66, position=2),
            Team(name="Atalanta", played=30, won=18, drawn=5, lost=7, goals_for=58, goals_against=30, goal_difference=28, points=59, position=3),
            Team(name="Juventus", played=30, won=14, drawn=12, lost=4, goals_for=48, goals_against=28, goal_difference=20, points=54, position=4),
            Team(name="Lazio", played=30, won=16, drawn=5, lost=9, goals_for=52, goals_against=38, goal_difference=14, points=53, position=5),
        ],
        "ligue-1": [
            Team(name="PSG", played=28, won=22, drawn=4, lost=2, goals_for=62, goals_against=18, goal_difference=44, points=70, position=1),
            Team(name="Marseille", played=28, won=17, drawn=5, lost=6, goals_for=52, goals_against=28, goal_difference=24, points=56, position=2),
            Team(name="Monaco", played=28, won=16, drawn=5, lost=7, goals_for=50, goals_against=30, goal_difference=20, points=53, position=3),
            Team(name="Lille", played=28, won=15, drawn=6, lost=7, goals_for=45, goals_against=28, goal_difference=17, points=51, position=4),
            Team(name="Lyon", played=28, won=14, drawn=6, lost=8, goals_for=48, goals_against=35, goal_difference=13, points=48, position=5),
        ],
    }

    if league_key in data:
        return data[league_key]

    return [
        Team(name=f"Takim {i}", played=30, won=max(0, 22 - i * 2), drawn=5,
             lost=min(25, 3 + i * 2), goals_for=max(10, 65 - i * 5),
             goals_against=20 + i * 3,
             goal_difference=max(10, 65 - i * 5) - (20 + i * 3),
             points=max(0, 22 - i * 2) * 3 + 5, position=i)
        for i in range(1, 11)
    ]


def get_sample_player_stats(league_key: str, category: str) -> list[PlayerStat]:
    """Return sample player statistics - 2024-25 season."""
    stats = {
        "gol-kralligi": {
            "super-lig": [
                PlayerStat(rank=1, name="Victor Osimhen", team="Galatasaray", value=24, matches_played=28, category="Gol Kralligi"),
                PlayerStat(rank=2, name="Edin Dzeko", team="Fenerbahce", value=18, matches_played=29, category="Gol Kralligi"),
                PlayerStat(rank=3, name="Ciro Immobile", team="Besiktas", value=16, matches_played=27, category="Gol Kralligi"),
                PlayerStat(rank=4, name="Youssef En-Nesyri", team="Fenerbahce", value=14, matches_played=26, category="Gol Kralligi"),
                PlayerStat(rank=5, name="Michy Batshuayi", team="Galatasaray", value=13, matches_played=25, category="Gol Kralligi"),
                PlayerStat(rank=6, name="Simon Falette", team="Basaksehir", value=11, matches_played=28, category="Gol Kralligi"),
                PlayerStat(rank=7, name="Cenk Tosun", team="Besiktas", value=10, matches_played=24, category="Gol Kralligi"),
                PlayerStat(rank=8, name="Joao Pedro", team="Trabzonspor", value=10, matches_played=27, category="Gol Kralligi"),
                PlayerStat(rank=9, name="Bertrand Traore", team="Basaksehir", value=9, matches_played=26, category="Gol Kralligi"),
                PlayerStat(rank=10, name="Semih Kilicsoy", team="Besiktas", value=8, matches_played=22, category="Gol Kralligi"),
            ],
            "premier-league": [
                PlayerStat(rank=1, name="Mohamed Salah", team="Liverpool", value=21, matches_played=28, category="Gol Kralligi"),
                PlayerStat(rank=2, name="Erling Haaland", team="Manchester City", value=19, matches_played=27, category="Gol Kralligi"),
                PlayerStat(rank=3, name="Alexander Isak", team="Newcastle", value=16, matches_played=28, category="Gol Kralligi"),
                PlayerStat(rank=4, name="Bryan Mbeumo", team="Brentford", value=15, matches_played=29, category="Gol Kralligi"),
                PlayerStat(rank=5, name="Chris Wood", team="Nottingham Forest", value=14, matches_played=28, category="Gol Kralligi"),
            ],
        },
        "asist": {
            "super-lig": [
                PlayerStat(rank=1, name="Dries Mertens", team="Galatasaray", value=14, matches_played=28, category="Asist"),
                PlayerStat(rank=2, name="Fred", team="Fenerbahce", value=12, matches_played=30, category="Asist"),
                PlayerStat(rank=3, name="Barys Alper Yilmaz", team="Galatasaray", value=10, matches_played=27, category="Asist"),
                PlayerStat(rank=4, name="Gedson Fernandes", team="Besiktas", value=9, matches_played=26, category="Asist"),
                PlayerStat(rank=5, name="Abdulkerim Bardakci", team="Galatasaray", value=8, matches_played=29, category="Asist"),
                PlayerStat(rank=6, name="Dusan Tadic", team="Fenerbahce", value=8, matches_played=25, category="Asist"),
                PlayerStat(rank=7, name="Rachid Ghezzal", team="Besiktas", value=7, matches_played=24, category="Asist"),
                PlayerStat(rank=8, name="Arda Guler", team="Fenerbahce", value=7, matches_played=20, category="Asist"),
                PlayerStat(rank=9, name="Kerem Akturk.", team="Galatasaray", value=6, matches_played=27, category="Asist"),
                PlayerStat(rank=10, name="Visca", team="Basaksehir", value=6, matches_played=28, category="Asist"),
            ],
            "premier-league": [
                PlayerStat(rank=1, name="Mohamed Salah", team="Liverpool", value=13, matches_played=28, category="Asist"),
                PlayerStat(rank=2, name="Bukayo Saka", team="Arsenal", value=11, matches_played=26, category="Asist"),
                PlayerStat(rank=3, name="Cole Palmer", team="Chelsea", value=10, matches_played=28, category="Asist"),
            ],
        },
        "sari-kart": {
            "super-lig": [
                PlayerStat(rank=1, name="Atakan Karazor", team="Sivasspor", value=11, matches_played=28, category="Sari Kart"),
                PlayerStat(rank=2, name="Okay Yokuslu", team="Trabzonspor", value=10, matches_played=27, category="Sari Kart"),
                PlayerStat(rank=3, name="Ismail Yuksek", team="Fenerbahce", value=9, matches_played=29, category="Sari Kart"),
                PlayerStat(rank=4, name="Lucas Torreira", team="Galatasaray", value=9, matches_played=26, category="Sari Kart"),
                PlayerStat(rank=5, name="Salih Ucan", team="Besiktas", value=8, matches_played=25, category="Sari Kart"),
                PlayerStat(rank=6, name="Mehmet Topal", team="Basaksehir", value=8, matches_played=28, category="Sari Kart"),
                PlayerStat(rank=7, name="Stefano Denswil", team="Kasimpasa", value=7, matches_played=24, category="Sari Kart"),
                PlayerStat(rank=8, name="Hakan Arslan", team="Sivasspor", value=7, matches_played=27, category="Sari Kart"),
            ],
            "premier-league": [
                PlayerStat(rank=1, name="Joao Palhinha", team="Manchester City", value=9, matches_played=26, category="Sari Kart"),
                PlayerStat(rank=2, name="Declan Rice", team="Arsenal", value=8, matches_played=28, category="Sari Kart"),
            ],
        },
        "kirmizi-kart": {
            "super-lig": [
                PlayerStat(rank=1, name="Saiss", team="Besiktas", value=2, matches_played=25, category="Kirmizi Kart"),
                PlayerStat(rank=2, name="Ndao", team="Kasimpasa", value=2, matches_played=22, category="Kirmizi Kart"),
                PlayerStat(rank=3, name="Trezeguet", team="Trabzonspor", value=2, matches_played=24, category="Kirmizi Kart"),
                PlayerStat(rank=4, name="Marcao", team="Galatasaray", value=1, matches_played=20, category="Kirmizi Kart"),
                PlayerStat(rank=5, name="Zeki Celik", team="Fenerbahce", value=1, matches_played=26, category="Kirmizi Kart"),
            ],
            "premier-league": [
                PlayerStat(rank=1, name="William Saliba", team="Arsenal", value=2, matches_played=26, category="Kirmizi Kart"),
                PlayerStat(rank=2, name="Rodrigo Bentancur", team="Tottenham", value=1, matches_played=20, category="Kirmizi Kart"),
            ],
        },
    }

    league_data = stats.get(category, {})
    result = league_data.get(league_key, [])

    if not result and league_key != "super-lig":
        result = league_data.get("super-lig", [])

    return result


def get_sample_matches(league_key: str) -> list[Match]:
    """Return sample match data - 2024-25 season."""
    data = {
        "super-lig": [
            Match(home_team="Galatasaray", away_team="Fenerbahce", home_score=3, away_score=1, date="15.03.2025", time="20:00", status="Bitti", week=28),
            Match(home_team="Besiktas", away_team="Trabzonspor", home_score=2, away_score=2, date="15.03.2025", time="17:00", status="Bitti", week=28),
            Match(home_team="Basaksehir", away_team="Antalyaspor", home_score=3, away_score=0, date="16.03.2025", time="19:00", status="Bitti", week=28),
            Match(home_team="Samsunspor", away_team="Sivasspor", home_score=1, away_score=0, date="16.03.2025", time="16:00", status="Bitti", week=28),
            Match(home_team="Kasimpasa", away_team="Konyaspor", home_score=2, away_score=1, date="17.03.2025", time="20:00", status="Bitti", week=28),
            Match(home_team="Fenerbahce", away_team="Besiktas", home_score=None, away_score=None, date="22.03.2025", time="20:00", status="Planli", week=29),
            Match(home_team="Trabzonspor", away_team="Galatasaray", home_score=None, away_score=None, date="23.03.2025", time="19:00", status="Planli", week=29),
            Match(home_team="Antalyaspor", away_team="Samsunspor", home_score=None, away_score=None, date="23.03.2025", time="16:00", status="Planli", week=29),
            Match(home_team="Sivasspor", away_team="Basaksehir", home_score=None, away_score=None, date="24.03.2025", time="20:00", status="Planli", week=29),
        ],
        "premier-league": [
            Match(home_team="Liverpool", away_team="Arsenal", home_score=2, away_score=1, date="15.03.2025", time="18:30", status="Bitti", week=28),
            Match(home_team="Manchester City", away_team="Chelsea", home_score=1, away_score=1, date="16.03.2025", time="17:00", status="Bitti", week=28),
            Match(home_team="Newcastle", away_team="Aston Villa", home_score=3, away_score=0, date="16.03.2025", time="15:00", status="Bitti", week=28),
            Match(home_team="Arsenal", away_team="Manchester City", home_score=None, away_score=None, date="22.03.2025", time="18:30", status="Planli", week=29),
        ],
    }

    if league_key in data:
        return data[league_key]
    return data["super-lig"]


def get_sample_live_scores() -> list[LiveMatch]:
    """Return sample live score data."""
    return [
        LiveMatch(home_team="Galatasaray", away_team="Sivasspor", home_score=2, away_score=0, minute="67'", league="Trendyol Super Lig", status="Canli"),
        LiveMatch(home_team="Fenerbahce", away_team="Kasimpasa", home_score=1, away_score=1, minute="DV", league="Trendyol Super Lig", status="Devre Arasi"),
        LiveMatch(home_team="Besiktas", away_team="Trabzonspor", home_score=0, away_score=0, minute="23'", league="Trendyol Super Lig", status="Canli"),
        LiveMatch(home_team="Manchester City", away_team="Arsenal", home_score=0, away_score=1, minute="55'", league="Premier League", status="Canli"),
        LiveMatch(home_team="Barcelona", away_team="Real Madrid", home_score=3, away_score=2, minute="MS", league="La Liga", status="Bitti"),
        LiveMatch(home_team="Bayern Munich", away_team="Dortmund", home_score=2, away_score=1, minute="78'", league="Bundesliga", status="Canli"),
        LiveMatch(home_team="Napoli", away_team="Inter Milan", home_score=1, away_score=0, minute="45+2'", league="Serie A", status="Canli"),
        LiveMatch(home_team="PSG", away_team="Marseille", home_score=2, away_score=0, minute="MS", league="Ligue 1", status="Bitti"),
        LiveMatch(home_team="Samsunspor", away_team="Antalyaspor", home_score=None, away_score=None, minute="21:00", league="Trendyol Super Lig", status="Planli"),
        LiveMatch(home_team="Basaksehir", away_team="Eyupspor", home_score=None, away_score=None, minute="19:00", league="Trendyol Super Lig", status="Planli"),
    ]


def get_sample_team_stats(league_key: str) -> list[TeamStats]:
    """Return sample team statistics."""
    standings = get_sample_standings(league_key)
    stats = []
    for team in standings:
        avg_goals = round(team.goals_for / team.played, 2) if team.played > 0 else 0.0
        avg_conceded = round(team.goals_against / team.played, 2) if team.played > 0 else 0.0
        avg_c = team.goals_against / team.played if team.played > 0 else 1.0
        if avg_c < 0.5:
            cs = int(team.played * 0.5)
        elif avg_c < 1.0:
            cs = int(team.played * 0.35)
        elif avg_c < 1.5:
            cs = int(team.played * 0.2)
        else:
            cs = int(team.played * 0.1)

        stats.append(TeamStats(
            name=team.name,
            matches_played=team.played,
            total_goals=team.goals_for,
            goals_conceded=team.goals_against,
            clean_sheets=cs,
            avg_goals_per_match=avg_goals,
            avg_conceded_per_match=avg_conceded,
        ))
    return stats
