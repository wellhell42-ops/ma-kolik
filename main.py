#!/usr/bin/env python3
"""
Mackolik Istatistik Toplayici PRO - CLI

Mackolik.com'dan tum futbol istatistiklerini ceker.
Online basarisiz olursa otomatik demo verilere duser.

Kullanim:
    python main.py --league super-lig --all
    python main.py --league premier-league --standings --scorers
    python main.py --live
    python main.py --all-leagues --all --format excel
    python main.py --demo --league super-lig --all
"""

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
    get_sample_team_stats,
)

console = Console()


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# --- Display functions ---

def display_standings(teams: list, league_name: str):
    if not teams:
        console.print(f"[yellow]Puan durumu bulunamadi: {league_name}[/yellow]")
        return

    table = Table(
        title=f"{league_name} - Puan Durumu",
        box=box.ROUNDED, show_lines=True, title_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Takim", style="bold", min_width=20)
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
        av_text = f"[{av_style}]{team.goal_difference:+d}[/{av_style}]" if av_style else str(team.goal_difference)
        table.add_row(
            str(team.position), team.name, str(team.played),
            str(team.won), str(team.drawn), str(team.lost),
            str(team.goals_for), str(team.goals_against),
            av_text, str(team.points),
        )
    console.print(table)


def display_player_stats(players: list, title: str):
    if not players:
        console.print(f"[yellow]{title} verisi bulunamadi[/yellow]")
        return

    table = Table(title=title, box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    table.add_column("#", style="dim", width=4, justify="center")
    table.add_column("Oyuncu", style="bold", min_width=20)
    table.add_column("Takim", min_width=15)
    table.add_column("Mac", justify="center", width=6)
    table.add_column("Deger", justify="center", width=6, style="bold green")

    for player in players[:30]:
        table.add_row(
            str(player.rank), player.name, player.team,
            str(player.matches_played), str(player.value),
        )
    console.print(table)


def display_matches(matches: list, title: str):
    if not matches:
        console.print(f"[yellow]{title} verisi bulunamadi[/yellow]")
        return

    table = Table(title=title, box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    table.add_column("Tarih", width=12, justify="center")
    table.add_column("Saat", width=6, justify="center")
    table.add_column("Ev Sahibi", min_width=15, justify="right")
    table.add_column("Skor", width=7, justify="center", style="bold")
    table.add_column("Deplasman", min_width=15)
    table.add_column("Durum", width=10, justify="center")

    status_styles = {"played": "green", "Bitti": "green", "live": "bold red",
                     "Canli": "bold red", "scheduled": "dim", "Planli": "dim"}

    for match in matches:
        score = f"{match.home_score} - {match.away_score}" if match.home_score is not None else "- : -"
        st = status_styles.get(match.status, "")
        status_text = f"[{st}]{match.status}[/{st}]" if st else match.status
        table.add_row(match.date, match.time, match.home_team, score, match.away_team, status_text)
    console.print(table)


def display_live_scores(matches: list):
    if not matches:
        console.print("[yellow]Su an canli mac bulunmuyor.[/yellow]")
        return

    table = Table(title="Canli Skorlar", box=box.HEAVY, show_lines=True, title_style="bold red")
    table.add_column("Lig", min_width=15)
    table.add_column("Ev Sahibi", min_width=15, justify="right")
    table.add_column("Skor", width=7, justify="center", style="bold")
    table.add_column("Deplasman", min_width=15)
    table.add_column("Dk", width=8, justify="center", style="bold yellow")
    table.add_column("Durum", width=12, justify="center")

    for match in matches:
        if match.home_score is not None and match.away_score is not None:
            score = f"{match.home_score} - {match.away_score}"
        else:
            score = "- : -"
        table.add_row(match.league, match.home_team, score, match.away_team, match.minute, match.status)
    console.print(table)


def display_team_stats(stats: list, league_name: str):
    if not stats:
        console.print(f"[yellow]Takim istatistikleri bulunamadi: {league_name}[/yellow]")
        return

    table = Table(title=f"{league_name} - Takim Istatistikleri",
                  box=box.ROUNDED, show_lines=True, title_style="bold cyan")
    table.add_column("Takim", style="bold", min_width=20)
    table.add_column("Mac", justify="center", width=5)
    table.add_column("Gol", justify="center", width=5, style="green")
    table.add_column("Yenilen", justify="center", width=7, style="red")
    table.add_column("Ort.Gol", justify="center", width=8)
    table.add_column("Ort.Yen.", justify="center", width=10)
    table.add_column("Gol Yememe", justify="center", width=10)

    for stat in stats:
        table.add_row(
            stat.name, str(stat.matches_played), str(stat.total_goals),
            str(stat.goals_conceded), f"{stat.avg_goals_per_match:.2f}",
            f"{stat.avg_conceded_per_match:.2f}", str(stat.clean_sheets),
        )
    console.print(table)


# --- Data collection with auto-fallback ---

def collect_demo_data(league_key: str, league_name: str,
                      standings=True, scorers=True, assists=True,
                      yellow_cards=True, red_cards=True,
                      matches=True, team_stats=True) -> LeagueData:
    """Collect demo data for a league."""
    data = LeagueData(league_name=league_name)
    if standings:
        data.standings = get_sample_standings(league_key)
    if scorers:
        data.top_scorers = get_sample_player_stats(league_key, "gol-kralligi")
    if assists:
        data.top_assists = get_sample_player_stats(league_key, "asist")
    if yellow_cards:
        data.yellow_cards = get_sample_player_stats(league_key, "sari-kart")
    if red_cards:
        data.red_cards = get_sample_player_stats(league_key, "kirmizi-kart")
    if matches:
        data.matches = get_sample_matches(league_key)
    if team_stats:
        data.team_stats = get_sample_team_stats(league_key)
    return data


def collect_all_data(scraper: MackolikScraper, league_key: str, league_name: str) -> tuple[LeagueData, bool]:
    """Collect all statistics. Returns (data, used_fallback)."""
    data = LeagueData(league_name=league_name)

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
                  console=console) as progress:
        task = progress.add_task(f"[cyan]{league_name} verileri toplaniyor...", total=None)

        progress.update(task, description=f"[cyan]{league_name} - Puan durumu...")
        data.standings = fetch_standings(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Gol kralligi...")
        data.top_scorers = fetch_top_scorers(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Asistler...")
        data.top_assists = fetch_top_assists(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Sari kartlar...")
        data.yellow_cards = fetch_yellow_cards(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Kirmizi kartlar...")
        data.red_cards = fetch_red_cards(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Maclar...")
        data.matches = fetch_matches(scraper, league_key)

        progress.update(task, description=f"[cyan]{league_name} - Takim istatistikleri...")
        data.team_stats = fetch_team_stats(scraper, league_key)

    # Check if anything was fetched
    has_any = (data.standings or data.top_scorers or data.top_assists
               or data.yellow_cards or data.red_cards
               or data.matches or data.team_stats)

    if not has_any:
        console.print("[bold yellow]Site verisi alinamadi, demo veriler yukleniyor...[/bold yellow]")
        data = collect_demo_data(league_key, league_name)
        return data, True

    return data, False


def display_all_data(data: LeagueData, league_name: str,
                     standings=True, scorers=True, assists=True,
                     yellow_cards=True, red_cards=True,
                     matches=True, team_stats=True):
    """Display all requested statistics."""
    if standings and data.standings:
        display_standings(data.standings, league_name)
    if scorers and data.top_scorers:
        display_player_stats(data.top_scorers, f"{league_name} - Gol Kralligi")
    if assists and data.top_assists:
        display_player_stats(data.top_assists, f"{league_name} - Asist")
    if yellow_cards and data.yellow_cards:
        display_player_stats(data.yellow_cards, f"{league_name} - Sari Kart")
    if red_cards and data.red_cards:
        display_player_stats(data.red_cards, f"{league_name} - Kirmizi Kart")
    if matches and data.matches:
        display_matches(data.matches, f"{league_name} - Maclar")
    if team_stats and data.team_stats:
        display_team_stats(data.team_stats, league_name)


# --- Export ---

def _export_league_data(league_data: LeagueData, league_key: str, fmt: str, output_dir: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"{output_dir}/{league_key}/{timestamp}"

    sheets = {}
    if league_data.standings:
        sheets["Puan Durumu"] = league_data.standings
    if league_data.top_scorers:
        sheets["Gol Kralligi"] = league_data.top_scorers
    if league_data.top_assists:
        sheets["Asist"] = league_data.top_assists
    if league_data.yellow_cards:
        sheets["Sari Kart"] = league_data.yellow_cards
    if league_data.red_cards:
        sheets["Kirmizi Kart"] = league_data.red_cards
    if league_data.matches:
        sheets["Maclar"] = league_data.matches
    if league_data.team_stats:
        sheets["Takim Istatistikleri"] = league_data.team_stats

    if fmt in ("json", "all"):
        path = export_json(league_data.to_dict(), f"{base_path}/data.json")
        console.print(f"  [dim]JSON: {path}[/dim]")
    if fmt in ("csv", "all"):
        for name, items in sheets.items():
            safe = name.lower().replace(" ", "_")
            for tr, en in [("i", "i"), ("s", "s"), ("o", "o"), ("u", "u"), ("g", "g"), ("c", "c")]:
                safe = safe.replace(tr, en)
            export_csv(items, f"{base_path}/{safe}.csv")
        console.print(f"  [dim]CSV: {base_path}/[/dim]")
    if fmt in ("excel", "all"):
        path = export_excel(sheets, f"{base_path}/mackolik_{league_key}.xlsx")
        console.print(f"  [dim]Excel: {path}[/dim]")


def _export_data(data: dict, fmt: str, output_dir: str, name: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = f"{output_dir}/{name}/{timestamp}"

    if fmt in ("json", "all"):
        export_json(data, f"{base_path}/{name}.json")
    if fmt in ("csv", "all"):
        for key, items in data.items():
            export_csv(items, f"{base_path}/{key}.csv")
    if fmt in ("excel", "all"):
        export_excel(data, f"{base_path}/{name}.xlsx")
    console.print(f"[green]Veriler kaydedildi: {base_path}/[/green]")


# --- CLI ---

@click.command()
@click.option("--league", "-l", type=click.Choice(list(LEAGUES.keys())), help="Lig secimi")
@click.option("--all-leagues", is_flag=True, help="Tum ligler icin veri cek")
@click.option("--standings", "-s", is_flag=True, help="Puan durumu")
@click.option("--scorers", "-g", is_flag=True, help="Gol kralligi")
@click.option("--assists", "-a", is_flag=True, help="Asist siralamasi")
@click.option("--yellow-cards", "-y", is_flag=True, help="Sari kart siralamasi")
@click.option("--red-cards", "-r", is_flag=True, help="Kirmizi kart siralamasi")
@click.option("--matches", "-m", is_flag=True, help="Mac sonuclari ve fikstur")
@click.option("--team-stats", "-t", is_flag=True, help="Takim istatistikleri")
@click.option("--live", is_flag=True, help="Canli skorlar")
@click.option("--today", is_flag=True, help="Bugunku maclar")
@click.option("--all", "fetch_all", is_flag=True, help="Tum istatistikleri cek")
@click.option("--format", "-f", "output_format", type=click.Choice(["json", "csv", "excel", "all"]), help="Disa aktarma formati")
@click.option("--output", "-o", "output_dir", default="output", help="Cikti klasoru")
@click.option("--date", "match_date", default=None, help="Belirli tarih icin maclar (GG/AA/YYYY)")
@click.option("--demo", is_flag=True, help="Demo modu - ornek verilerle calistir")
@click.option("--verbose", "-v", is_flag=True, help="Detayli log")
def main(league, all_leagues, standings, scorers, assists, yellow_cards, red_cards,
         matches, team_stats, live, today, fetch_all, output_format, output_dir,
         match_date, demo, verbose):
    """
    Mackolik Istatistik Toplayici PRO

    Mackolik.com'dan profesyonel futbol istatistiklerini ceker.
    Online erisim basarisiz olursa otomatik demo verilerle calisir.

    \b
    Ornekler:
        python main.py --league super-lig --all
        python main.py --league premier-league --standings --scorers
        python main.py --live
        python main.py --today
        python main.py --date 24/03/2025
        python main.py --all-leagues --all --format excel
        python main.py -l super-lig -s -g -f json
        python main.py --demo --league super-lig --all
    """
    setup_logging(verbose)

    console.print(Panel.fit(
        "[bold cyan]Mackolik Istatistik Toplayici PRO[/bold cyan]\n"
        "[dim]Tum futbol verilerini tek komutla cekin[/dim]",
        border_style="cyan",
    ))

    # No options selected - show help
    if not any([standings, scorers, assists, yellow_cards, red_cards,
                matches, team_stats, live, today, fetch_all]):
        if not league and not all_leagues:
            console.print("[yellow]Kullanim: python main.py --help[/yellow]")
            console.print("\n[dim]Hizli baslangic:[/dim]")
            console.print("  python main.py --demo --league super-lig --all")
            console.print("  python main.py --league super-lig --all")
            console.print("  python main.py --live")
            console.print("  python main.py --all-leagues --all --format excel")
            return

    # When --all is used, enable everything
    if fetch_all:
        standings = scorers = assists = yellow_cards = red_cards = matches = team_stats = True

    # --- Demo mode ---
    if demo:
        console.print("[bold yellow]Demo modu - Ornek veriler kullaniliyor[/bold yellow]\n")
        if live or today:
            display_live_scores(get_sample_live_scores())
            if output_format:
                _export_data({"canli_skorlar": get_sample_live_scores()}, output_format, output_dir, "canli_skorlar")
            return

        leagues = list(LEAGUES.keys()) if all_leagues else [league or "super-lig"]
        for lk in leagues:
            ln = LEAGUES.get(lk, {}).get("name", lk)
            console.print(f"\n[bold blue]{'='*60}[/bold blue]")
            console.print(f"[bold blue]{ln}[/bold blue]")
            console.print(f"[bold blue]{'='*60}[/bold blue]\n")

            data = collect_demo_data(lk, ln, standings, scorers, assists,
                                     yellow_cards, red_cards, matches, team_stats)
            display_all_data(data, ln, standings, scorers, assists,
                             yellow_cards, red_cards, matches, team_stats)
            if output_format:
                _export_league_data(data, lk, output_format, output_dir)

        if output_format:
            console.print(f"\n[green]Veriler '{output_dir}/' klasorune aktarildi![/green]")
        return

    # --- Online mode with auto-fallback ---
    with MackolikScraper() as scraper:
        # Live scores
        if live:
            live_matches = fetch_live_scores(scraper)
            if not live_matches:
                console.print("[yellow]Site erisimi basarisiz, demo veriler gosteriliyor...[/yellow]")
                live_matches = get_sample_live_scores()
            display_live_scores(live_matches)
            if output_format:
                _export_data({"canli_skorlar": live_matches}, output_format, output_dir, "canli_skorlar")
            return

        # Today's matches
        if today:
            today_matches = fetch_todays_matches(scraper)
            if not today_matches:
                console.print("[yellow]Site erisimi basarisiz, demo veriler gosteriliyor...[/yellow]")
                today_matches = get_sample_live_scores()
            display_live_scores(today_matches)
            if output_format:
                _export_data({"bugunun_maclari": today_matches}, output_format, output_dir, "bugunun_maclari")
            return

        # Specific date
        if match_date:
            try:
                date_obj = datetime.strptime(match_date, "%d/%m/%Y")
            except ValueError:
                console.print("[red]Gecersiz tarih formati. Kullanim: GG/AA/YYYY[/red]")
                return
            date_matches = fetch_live_by_date(scraper, date_obj)
            if not date_matches:
                console.print("[yellow]Bu tarih icin mac bulunamadi.[/yellow]")
                return
            display_live_scores(date_matches)
            if output_format:
                _export_data({"tarih_maclari": date_matches}, output_format, output_dir,
                             f"maclar_{match_date.replace('/', '-')}")
            return

        # League data
        leagues = list(LEAGUES.keys()) if all_leagues else ([league] if league else [])
        if not leagues:
            console.print("[red]Lutfen bir lig secin (--league) veya --all-leagues kullanin[/red]")
            return

        all_league_data = {}

        for league_key in leagues:
            league_info = LEAGUES[league_key]
            league_name = league_info["name"]
            console.print(f"\n[bold blue]{'='*60}[/bold blue]")
            console.print(f"[bold blue]{league_name}[/bold blue]")
            console.print(f"[bold blue]{'='*60}[/bold blue]\n")

            data, used_fallback = collect_all_data(scraper, league_key, league_name)

            if used_fallback:
                console.print("[bold yellow]Otomatik demo verileri yuklendi[/bold yellow]\n")

            display_all_data(data, league_name, standings, scorers, assists,
                             yellow_cards, red_cards, matches, team_stats)
            all_league_data[league_key] = data

        # Export
        if output_format and all_league_data:
            console.print(f"\n[cyan]Veriler disa aktariliyor...[/cyan]")
            for lk, ld in all_league_data.items():
                _export_league_data(ld, lk, output_format, output_dir)
            console.print(f"\n[green]Veriler '{output_dir}/' klasorune aktarildi![/green]")


if __name__ == "__main__":
    main()
