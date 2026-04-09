"""Data models for Maçkolik statistics."""

from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Team:
    name: str
    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0
    goal_difference: int = 0
    points: int = 0
    position: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class PlayerStat:
    rank: int
    name: str
    team: str
    value: int  # goals, assists, cards, etc.
    matches_played: int = 0
    category: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Match:
    home_team: str
    away_team: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    date: str = ""
    time: str = ""
    status: str = ""  # played, scheduled, live
    week: int = 0
    stadium: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TeamStats:
    name: str
    matches_played: int = 0
    total_goals: int = 0
    goals_conceded: int = 0
    clean_sheets: int = 0
    avg_goals_per_match: float = 0.0
    avg_conceded_per_match: float = 0.0
    home_wins: int = 0
    away_wins: int = 0
    home_draws: int = 0
    away_draws: int = 0
    home_losses: int = 0
    away_losses: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LiveMatch:
    home_team: str
    away_team: str
    home_score: Optional[int] = 0
    away_score: Optional[int] = 0
    minute: str = ""
    league: str = ""
    status: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class LeagueData:
    league_name: str
    season: str = ""
    standings: list = field(default_factory=list)
    top_scorers: list = field(default_factory=list)
    top_assists: list = field(default_factory=list)
    yellow_cards: list = field(default_factory=list)
    red_cards: list = field(default_factory=list)
    matches: list = field(default_factory=list)
    team_stats: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "league_name": self.league_name,
            "season": self.season,
            "standings": [t.to_dict() if hasattr(t, "to_dict") else t for t in self.standings],
            "top_scorers": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.top_scorers],
            "top_assists": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.top_assists],
            "yellow_cards": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.yellow_cards],
            "red_cards": [p.to_dict() if hasattr(p, "to_dict") else p for p in self.red_cards],
            "matches": [m.to_dict() if hasattr(m, "to_dict") else m for m in self.matches],
            "team_stats": [t.to_dict() if hasattr(t, "to_dict") else t for t in self.team_stats],
        }
