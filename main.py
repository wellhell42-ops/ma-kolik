#!/usr/bin/env python3
"""
Maçkolik İstatistik Toplayıcı - Professional Football Statistics Scraper

Maçkolik.com'dan tüm futbol istatistiklerini çeker:
- Puan durumu
- Gol krallığı, asistler, kartlar
- Maç sonuçları ve fikstür
- Takım istatistikleri
- Canlı skorlar

Kullanım:
    python main.py --league super-lig --all
    python main.py --league premier-league --standings --scorers
    python main.py --live
    python main.py --all-leagues --all --format excel
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from mackolik.config import LEAGUES
from mackolik.scraper import MackolikScraper
from mackolik.scrapers import (
    fetch_standings,
    fetch_matches,
    fetch_results,
    fetch_fixtures,
    fetch_top_scorers,
    fetch_top_assists,
    fetch_yellow_cards,
    fetch_red_cards,
    fetch_all_player_stats,
    fetch_team_stats,
    fetch_team_form,
    fetch_live_scores,
    fetch_todays_matches,
    fetch_live_by_date,
)
from mackolik.exporters import export_json, export_csv, export_excel
from mackolik.models import LeagueData
from mackolik.demo import (
    get_sample_standings,
    get_sample_player_stats,
    get_sample_matches,
    get_sample_live_scores,
)

console = Console()


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def display_standings(teams: list, league_name: str):
    """Display standings in a rich table."""
    if not teams:
        console.print(f"[yellow]Puan durumu bulunamadı: {league_name}[/yellow]")
        return

    table = Table(
        title=f"⚽ {league_name} - Puan Durumu",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Takım", style="bold", min_width=20)
    table.add_column("O", justify="center", width=4)
    table.add_column("G", justify="center", width=4, style="green")
    table.add_column("B", justify="center", width=4, style="yellow")
    table.add_column("M", justify="center", width=4, style="red")
    table.add_column("AG", justify="center", width=5)
    table.add_column("YG", justify="center", width=5)
    table.add_column("AV", justify="center", width=5)
    table.add_column("P", justify="center", width=5, style="bold magenta")

    for team in teams:
        av_style = "green" if team.goal_difference > 0 else ("red" if team.goal_difference < 0 else "")
        table.add_row(
            str(team.position),
            team.name,
            str(team.played),
            str(team.won),
            str(team.drawn),
            str(team.lost),
            str(team.goals_for),
            str(team.goals_against),
            f"[{av_style}]{team.goal_difference:+d}[/{av_style}]" if av_style else str(team.goal_difference),
            str(team.points),
        )

    console.print(table)


def display_player_stats(players: list, title: str):
    """Display player statistics in a rich table."""
    if not players:
        console.print(f"[yellow]{title} verisi bulunamadı[/yellow]")
        return

    table = Table(title=f"📊 {title}", box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Oyuncu", style="bold", min_width=20)
    table.add_column("Takım", min_width=15)
    table.add_column("Maç", justify="center", width=6)
    table.add_column("Değer", justify="center", width=6, style="bold green")

    for player in players[:30]:  # Top 30
        table.add_row(
            str(player.rank),
            player.name,
            player.team,
            str(player.matches_played),
            str(player.value),
        )

    console.print(table)


def display_matches(matches: list, title: str):
    """Display matches in a rich table."""
    if not matches:
        console.print(f"[yellow]{title} verisi bulunamadı[/yellow]")
        return

    table = Table(title=f"🏟️  {title}", box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    table.add_column("Tarih", width=12, justify="center")
    table.add_column("Saat", width=6, justify="center")
    table.add_column("Ev Sahibi", min_width=15, justify="right")
    table.add_column("Skor", width=7, justify="center", style="bold")
    table.add_column("Deplasman", min_width=15)
    table.add_column("Durum", width=10, justify="center")

    for match in matches:
        if match.home_score is not None:
            score = f"{match.home_score} - {match.away_score}"
        else:
            score = "- : -"

        status_style = {
            "played": "green",
            "live": "bold red",
            "scheduled": "dim",
        }.get(match.status, "")

        table.add_row(
            match.date,
            match.time,
            match.home_team,
            score,
            match.away_team,
            f"[{status_style}]{match.status}[/{status_style}]" if status_style else match.status,
        )

    console.print(table)


def display_live_scores(matches: list):
    """Display live scores."""
    if not matches:
        console.print("[yellow]Şu an canlı maç bulunmuyor.[/yellow]")
        return

    table = Table(
        title="🔴 Canlı Skorlar",
        box=box.HEAVY,
        show_lines=True,
        title_style="bold red",
    )
    table.add_column("Lig", min_width=15)
    table.add_column("Ev Sahibi", min_width=15, justify="right")
    table.add_column("Skor", width=7, justify="center", style="bold")
    table.add_column("Deplasman", min_width=15)
    table.add_column("Dk", width=6, justify="center", style="bold yellow")
    table.add_column("Durum", width=10, justify="center")

    for match in matches:
        if match.home_score is not None and match.away_score is not None:
            score = f"{match.home_score} - {match.away_score}"
        else:
            score = "- : -"
        table.add_row(
            match.league,
            match.home_team,
            score,
            match.away_team,
            match.minute,
            match.status,
        )

    console.print(table)


def display_team_stats(stats: list, league_name: str):
    """Display team statistics."""
    if not stats:
        console.print(f"[yellow]Takım istatistikleri bulunamadı: {league_name}[/yellow]")
        return

    table = Table(
        title=f"📈 {league_name} - Takım İstatistikleri",
        box=box.ROUNDED,
        show_lines=True,
        title_style="bold cyan",
    )
    table.add_column("Takım", style="bold", min_width=20)
    table.add_column("Maç", justify="center", width=5)
    table.add_column("Gol", justify="center", width=5, style="green")
    table.add_column("Yenilen", justify="center", width=7, style="red")
    table.add_column("Ort. Gol", justify="center", width=8)
    table.add_column("Ort. Yenilen", justify="center", width=10)
    table.add_column("Gol Yememe", justify="center", width=10)

    for stat in stats:
        table.add_row(
            stat.name,
            str(stat.matches_played),
            str(stat.total_goals),
            str(stat.goals_conceded),
            f"{stat.avg_goals_per_match:.2f}",
            f"{stat.avg_conceded_per_match:.2f}",
            str(stat.clean_sheets),
        )

    console.print(table)


def collect_all_data(scraper: MackolikScraper, league_key: str, league_name: str) -> LeagueData:
    """Collect all statistics for a league."""
    data = LeagueData(league_name=league_name)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]{league_name} verileri toplanıyor...", total=None)

        progress.update(task, description=f"[cyan]{league_name} - Puan durumu...")
        data.standings = fetch_standings(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Gol krallığı...")
        data.top_scorers = fetch_top_scorers(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Asistler...")
        data.top_assists = fetch_top_assists(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Sarı kartlar...")
        data.yellow_cards = fetch_yellow_cards(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Kırmızı kartlar...")
        data.red_cards = fetch_red_cards(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Maçlar...")
        data.matches = fetch_matches(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Takım istatistikleri...")
        data.team_stats = fetch_team_stats(scraper, league_key)

    return data


@click.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys())), help="Lig seçimi")
@click.option("--all-leagues", is_flag=True, help="Tüm ligler için veri çek")
@click.option("--standings", "-s", is_flag=True, help="Puan durumu")
@click.option("--scorers", "-g", is_flag=True, help="Gol krallığı")
@click.option("--assists", "-a", is_flag=True, help="Asist sıralaması")
@click.option("--yellow-cards", "-y", is_flag=True, help="Sarı kart sıralaması")
@click.option("--red-cards", "-r", is_flag=True, help="Kırmızı kart sıralaması")
@click.option("--matches", "-m", is_flag=True, help="Maç sonuçları ve fikstür")
@click.option("--team-stats", "-t", is_flag=True, help="Takım istatistikleri")
@click.option("--live", is_flag=True, help="Canlı skorlar")
@click.option("--today", is_flag=True, help="Bugünkü maçlar")
@click.option("--all", "fetch_all", is_flag=True, help="Tüm istatistikleri çek")
@click.option("--format", "-f", "output_format", type=click.Choice(["json", "csv", "excel", "all"]), help="Dışa aktarma formatı")
@click.option("--output", "-o", "output_dir", default="output", help="Çıktı klasörü")
@click.option("--date", "match_date", default=None, help="Belirli bir tarih için maçlar (GG/AA/YYYY)")
@click.option("--demo", is_flag=True, help="Demo modu - örnek verilerle çalıştır")
@click.option("--verbose", "-v", is_flag=True, help="Detaylı log")
def main(league, all_leagues, standings, scorers, assists, yellow_cards, red_cards,
         matches, team_stats, live, today, fetch_all, output_format, output_dir,
         match_date, demo, verbose):
    """
    ⚽ Maçkolik İstatistik Toplayıcı

    Maçkolik.com'dan profesyonel futbol istatistiklerini çeker.

    \b
    Örnekler:
        python main.py --league super-lig --all
        python main.py --league premier-league --standings --scorers
        python main.py --live
        python main.py --date 24/03/2026
        python main.py --all-leagues --all --format excel
        python main.py -l super-lig -s -g -f json
        python main.py --demo --league super-lig --all
    """
    setup_logging(verbose)

    console.print(Panel.fit(
        "[bold cyan]⚽ Maçkolik İstatistik Toplayıcı[/bold cyan]\n"
        "[dim]Tüm futbol verilerini tek komutla çekin[/dim]",
        border_style="cyan",
    ))

    # If no specific stat is selected, show help
    if not any([standings, scorers, assists, yellow_cards, red_cards,
                matches, team_stats, live, today, fetch_all]):
        if not league and not all_leagues:
            console.print("[yellow]Kullanım: python main.py --help[/yellow]")
            console.print("\n[dim]Hızlı başlangıç:[/dim]")
            console.print("  python main.py --league super-lig --all")
            console.print("  python main.py --live")
            return

    # Demo mode
    if demo:
        console.print("[bold yellow]⚠ Demo modu - Örnek veriler kullanılıyor[/bold yellow]\n")
        if live or today:
            display_live_scores(get_sample_live_scores())
            return

        demo_league = league or "super-lig"
        league_info = LEAGUES.get(demo_league, {})
        league_name = league_info.get("name", demo_league)

        if fetch_all or standings:
            display_standings(get_sample_standings(demo_league), league_name)
        if fetch_all or scorers:
            display_player_stats(get_sample_player_stats(demo_league, "gol-kralligi"), f"{league_name} - Gol Krallığı")
        if fetch_all or assists:
            display_player_stats(get_sample_player_stats(demo_league, "asist"), f"{league_name} - Asist")
        if fetch_all or yellow_cards:
            display_player_stats(get_sample_player_stats(demo_league, "sari-kart"), f"{league_name} - Sarı Kart")
        if fetch_all or red_cards:
            display_player_stats(get_sample_player_stats(demo_league, "kirmizi-kart"), f"{league_name} - Kırmızı Kart")
        if fetch_all or matches:
            display_matches(get_sample_matches(demo_league), f"{league_name} - Maçlar")
        return

    with MackolikScraper() as scraper:
        # Live scores
        if live:
            live_matches = fetch_live_scores(scraper)
            display_live_scores(live_matches)
            if output_format:
                _export_data({"canli_skorlar": live_matches}, output_format, output_dir, "canli_skorlar")
            return

        # Today's matches
        if today:
            today_matches = fetch_todays_matches(scraper)
            display_live_scores(today_matches)
            if output_format:
                _export_data({"bugunun_maclari": today_matches}, output_format, output_dir, "bugunun_maclari")
            return

        # Specific date matches
        if match_date:
            try:
                date_obj = datetime.strptime(match_date, "%d/%m/%Y")
            except ValueError:
                console.print("[red]Geçersiz tarih formatı. Kullanım: GG/AA/YYYY[/red]")
                return
            date_matches = fetch_live_by_date(scraper, date_obj)
            display_live_scores(date_matches)
            if output_format:
                _export_data({"tarih_maclari": date_matches}, output_format, output_dir, f"maclar_{match_date.replace('/', '-')}")
            return

        # Determine which leagues to process
        leagues_to_process = []
        if all_leagues:
            leagues_to_process = list(LEAGUES.keys())
        elif league:
            leagues_to_process = [league]
        else:
            console.print("[red]Lütfen bir lig seçin (--league) veya --all-leagues kullanın[/red]")
            return

        all_league_data = {}

        for league_key in leagues_to_process:
            league_info = LEAGUES[league_key]
            league_name = league_info["name"]
            console.print(f"\n[bold blue]{'='*60}[/bold blue]")
            console.print(f"[bold blue]📋 {league_name}[/bold blue]")
            console.print(f"[bold blue]{'='*60}[/bold blue]\n")

            if fetch_all:
                league_data = collect_all_data(scraper, league_key, league_name)
                display_standings(league_data.standings, league_name)
                display_player_stats(league_data.top_scorers, f"{league_name} - Gol Krallığı")
                display_player_stats(league_data.top_assists, f"{league_name} - Asist")
                display_player_stats(league_data.yellow_cards, f"{league_name} - Sarı Kart")
                display_player_stats(league_data.red_cards, f"{league_name} - Kırmızı Kart")
                display_matches(league_data.matches, f"{league_name} - Maçlar")
                display_team_stats(league_data.team_stats, league_name)
                all_league_data[league_key] = league_data
            else:
                league_data = LeagueData(league_name=league_name)

                if standings:
                    league_data.standings = fetch_standings(scraper, league_key)
                    display_standings(league_data.standings, league_name)

                if scorers:
                    league_data.top_scorers = fetch_top_scorers(scraper, league_key)
                    display_player_stats(league_data.top_scorers, f"{league_name} - Gol Krallığı")

                if assists:
                    league_data.top_assists = fetch_top_assists(scraper, league_key)
                    display_player_stats(league_data.top_assists, f"{league_name} - Asist")

                if yellow_cards:
                    league_data.yellow_cards = fetch_yellow_cards(scraper, league_key)
                    display_player_stats(league_data.yellow_cards, f"{league_name} - Sarı Kart")

                if red_cards:
                    league_data.red_cards = fetch_red_cards(scraper, league_key)
                    display_player_stats(league_data.red_cards, f"{league_name} - Kırmızı Kart")

                if matches:
                    league_data.matches = fetch_matches(scraper, league_key)
                    display_matches(league_data.matches, f"{league_name} - Maçlar")

                if team_stats:
                    league_data.team_stats = fetch_team_stats(scraper, league_key)
                    display_team_stats(league_data.team_stats, league_name)

                all_league_data[league_key] = league_data

        # Export if requested
        if output_format and all_league_data:
            for lk, ld in all_league_data.items():
                _export_league_data(ld, lk, output_format, output_dir)

            console.print(f"\n[green]✅ Veriler '{output_dir}/' klasörüne aktarıldı![/green]")


def _export_league_data(league_data: LeagueData, league_key: str, fmt: str, output_dir: str):
    """Export league data in the specified format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"{output_dir}/{league_key}/{timestamp}"

    sheets = {}
    if league_data.standings:
        sheets["Puan Durumu"] = league_data.standings
    if league_data.top_scorers:
        sheets["Gol Krallığı"] = league_data.top_scorers
    if league_data.top_assists:
        sheets["Asist"] = league_data.top_assists
    if league_data.yellow_cards:
        sheets["Sarı Kart"] = league_data.yellow_cards
    if league_data.red_cards:
        sheets["Kırmızı Kart"] = league_data.red_cards
    if league_data.matches:
        sheets["Maçlar"] = league_data.matches
    if league_data.team_stats:
        sheets["Takım İstatistikleri"] = league_data.team_stats

    if fmt in ("json", "all"):
        export_json(league_data.to_dict(), f"{base_path}/data.json")

    if fmt in ("csv", "all"):
        for name, data in sheets.items():
            safe_name = name.lower().replace(" ", "_").replace("ı", "i").replace("ş", "s").replace("ö", "o").replace("ü", "u").replace("ğ", "g").replace("ç", "c")
            export_csv(data, f"{base_path}/{safe_name}.csv")

    if fmt in ("excel", "all"):
        export_excel(sheets, f"{base_path}/mackolik_{league_key}.xlsx")


def _export_data(data: dict, fmt: str, output_dir: str, name: str):
    """Export generic data."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"{output_dir}/{name}/{timestamp}"

    if fmt in ("json", "all"):
        export_json(data, f"{base_path}/{name}.json")
    if fmt in ("csv", "all"):
        for key, items in data.items():
            export_csv(items, f"{base_path}/{key}.csv")
    if fmt in ("excel", "all"):
        export_excel(data, f"{base_path}/{name}.xlsx")


if __name__ == "__main__":
    main()
