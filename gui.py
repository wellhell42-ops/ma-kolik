#!/usr/bin/env python3
"""
Mackolik Istatistik Toplayici PRO - Windows Masaustu Uygulamasi
Tkinter tabanli GUI ile tum futbol istatistiklerini cekin.
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime

from mackolik.config import LEAGUES
from mackolik.scraper import MackolikScraper
from mackolik.scrapers import (
    fetch_standings,
    fetch_matches,
    fetch_top_scorers,
    fetch_top_assists,
    fetch_yellow_cards,
    fetch_red_cards,
    fetch_team_stats,
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


# --- Color theme ---
BG_DARK = "#0d1117"
BG_CARD = "#161b22"
BG_INPUT = "#21262d"
BG_HOVER = "#30363d"
FG_TEXT = "#e6edf3"
FG_DIM = "#8b949e"
FG_TITLE = "#ffffff"
ACCENT = "#e94560"
ACCENT_HOVER = "#ff6b81"
GREEN = "#3fb950"
YELLOW = "#d29922"
BLUE = "#58a6ff"
RED = "#f85149"
ORANGE = "#f0883e"
LIVE_RED = "#da3633"
LIVE_PULSE = "#ff7b72"


class MackolikApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Mackolik Istatistik Toplayici PRO")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG_DARK)

        try:
            self.root.iconbitmap("mackolik.ico")
        except tk.TclError:
            pass

        self.demo_mode = tk.BooleanVar(value=False)
        self.auto_refresh = tk.BooleanVar(value=False)
        self.is_fetching = False
        self.current_data = None
        self.live_data = None
        self._refresh_job = None

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG_DARK, foreground=FG_TITLE, font=("Segoe UI", 20, "bold"))
        style.configure("Subtitle.TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=BG_CARD, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=BG_CARD, foreground=FG_TITLE, font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", background=BG_DARK, foreground=GREEN, font=("Segoe UI", 9))
        style.configure("Pro.TLabel", background=BG_DARK, foreground=ACCENT, font=("Segoe UI", 10, "bold"))

        style.configure("TCheckbutton", background=BG_CARD, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.map("TCheckbutton", background=[("active", BG_CARD)])

        style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_INPUT,
                         foreground=FG_TEXT, font=("Segoe UI", 10))

        style.configure("Accent.TButton", background=ACCENT, foreground="white",
                         font=("Segoe UI", 11, "bold"), padding=(20, 10))
        style.map("Accent.TButton",
                   background=[("active", ACCENT_HOVER), ("disabled", "#555555")])

        style.configure("Secondary.TButton", background=BG_INPUT, foreground=FG_TEXT,
                         font=("Segoe UI", 10), padding=(12, 6))
        style.map("Secondary.TButton",
                   background=[("active", BLUE), ("disabled", "#333333")])

        style.configure("Live.TButton", background=LIVE_RED, foreground="white",
                         font=("Segoe UI", 11, "bold"), padding=(20, 10))
        style.map("Live.TButton", background=[("active", LIVE_PULSE)])

        style.configure("Today.TButton", background=ORANGE, foreground="white",
                         font=("Segoe UI", 10, "bold"), padding=(14, 8))
        style.map("Today.TButton", background=[("active", YELLOW)])

        style.configure("Treeview", background=BG_CARD, foreground=FG_TEXT,
                         fieldbackground=BG_CARD, font=("Segoe UI", 9),
                         rowheight=30)
        style.configure("Treeview.Heading", background=BG_INPUT, foreground=FG_TITLE,
                         font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])

        style.configure("green.Horizontal.TProgressbar",
                         troughcolor=BG_INPUT, background=GREEN)

    def _build_ui(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(15, 5))

        title_frame = ttk.Frame(header)
        title_frame.pack(side="left")
        ttk.Label(title_frame, text="Mackolik Istatistik",
                  style="Title.TLabel").pack(side="left")
        ttk.Label(title_frame, text=" PRO",
                  style="Pro.TLabel", font=("Segoe UI", 20, "bold")).pack(side="left")

        # Right side controls in header
        header_right = ttk.Frame(header)
        header_right.pack(side="right")

        ttk.Checkbutton(header_right, text="Demo Modu",
                         variable=self.demo_mode,
                         style="TCheckbutton").pack(side="right", padx=10)

        ttk.Label(header, text="Tum futbol verilerini tek tikla cekin",
                  style="Subtitle.TLabel").pack(side="left", padx=(15, 0))

        # Main content area
        content = ttk.Frame(self.root)
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Controls
        left = ttk.Frame(content, style="Card.TFrame", width=300)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_controls(left)

        # Right panel - Results
        right = ttk.Frame(content)
        right.pack(side="left", fill="both", expand=True)
        self._build_results(right)

        # Status bar
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.status_var = tk.StringVar(value="Hazir - Bir lig secip 'Verileri Cek' butonuna basin")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                       style="Status.TLabel")
        self.status_label.pack(side="left")

        self.progress = ttk.Progressbar(status_frame, style="green.Horizontal.TProgressbar",
                                         mode="indeterminate", length=150)
        self.progress.pack(side="right")

    def _build_controls(self, parent):
        pad_x = 15

        # League selection
        ttk.Label(parent, text="Lig Secimi", style="CardTitle.TLabel").pack(
            padx=pad_x, anchor="w", pady=(15, 5))

        self.league_names = {k: v["name"] for k, v in LEAGUES.items()}
        self.league_var = tk.StringVar(value="super-lig")

        # Show league name in combobox instead of key
        display_values = [f"{v['name']}" for v in LEAGUES.values()]
        self.league_combo = ttk.Combobox(parent, textvariable=tk.StringVar(),
                                          values=display_values,
                                          state="readonly", width=30)
        self.league_combo.current(0)
        self.league_combo.pack(padx=pad_x, pady=5, anchor="w")
        self.league_combo.bind("<<ComboboxSelected>>", self._on_league_change)

        # League info
        self.league_info_var = tk.StringVar(value="Turkiye - Trendyol Super Lig")
        ttk.Label(parent, textvariable=self.league_info_var,
                  style="Card.TLabel").pack(padx=pad_x, anchor="w")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=pad_x, pady=10)

        # Stats checkboxes
        ttk.Label(parent, text="Istatistikler", style="CardTitle.TLabel").pack(
            padx=pad_x, pady=5, anchor="w")

        self.cb_vars = {}
        checks = [
            ("standings", "Puan Durumu"),
            ("scorers", "Gol Kralligi"),
            ("assists", "Asist Siralamasi"),
            ("yellow_cards", "Sari Kartlar"),
            ("red_cards", "Kirmizi Kartlar"),
            ("matches", "Mac Sonuclari"),
            ("team_stats", "Takim Istatistikleri"),
        ]
        for key, label in checks:
            var = tk.BooleanVar(value=True)
            self.cb_vars[key] = var
            ttk.Checkbutton(parent, text=label, variable=var,
                             style="TCheckbutton").pack(padx=25, anchor="w", pady=2)

        # Select All / None buttons
        sel_frame = ttk.Frame(parent, style="Card.TFrame")
        sel_frame.pack(padx=pad_x, pady=5, fill="x")
        tk.Button(sel_frame, text="Tumunu Sec", command=self._select_all,
                  bg=BG_INPUT, fg=FG_DIM, relief="flat", font=("Segoe UI", 8),
                  activebackground=BG_HOVER, activeforeground=FG_TEXT,
                  cursor="hand2").pack(side="left", padx=2)
        tk.Button(sel_frame, text="Temizle", command=self._select_none,
                  bg=BG_INPUT, fg=FG_DIM, relief="flat", font=("Segoe UI", 8),
                  activebackground=BG_HOVER, activeforeground=FG_TEXT,
                  cursor="hand2").pack(side="left", padx=2)

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=pad_x, pady=10)

        # Action buttons
        ttk.Label(parent, text="Islemler", style="CardTitle.TLabel").pack(
            padx=pad_x, pady=5, anchor="w")

        self.fetch_btn = ttk.Button(parent, text="Verileri Cek",
                                     style="Accent.TButton",
                                     command=self._on_fetch)
        self.fetch_btn.pack(padx=pad_x, pady=5, fill="x")

        self.live_btn = ttk.Button(parent, text="Canli Skorlar",
                                    style="Live.TButton",
                                    command=self._on_live)
        self.live_btn.pack(padx=pad_x, pady=5, fill="x")

        self.today_btn = ttk.Button(parent, text="Bugunun Maclari",
                                     style="Today.TButton",
                                     command=self._on_today)
        self.today_btn.pack(padx=pad_x, pady=5, fill="x")

        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=pad_x, pady=10)

        # Export buttons
        ttk.Label(parent, text="Disa Aktar", style="CardTitle.TLabel").pack(
            padx=pad_x, pady=5, anchor="w")

        export_frame = ttk.Frame(parent, style="Card.TFrame")
        export_frame.pack(padx=pad_x, fill="x")

        for fmt, label in [("json", "JSON"), ("csv", "CSV"), ("excel", "Excel")]:
            ttk.Button(export_frame, text=label, style="Secondary.TButton",
                        command=lambda f=fmt: self._export(f)).pack(
                            side="left", expand=True, fill="x", padx=2)

    def _build_results(self, parent):
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        self.tabs = {}
        tab_names = [
            ("standings", "Puan Durumu"),
            ("scorers", "Gol Kralligi"),
            ("assists", "Asist"),
            ("yellow_cards", "Sari Kart"),
            ("red_cards", "Kirmizi Kart"),
            ("matches", "Maclar"),
            ("team_stats", "Takim Ist."),
            ("live", "Canli Skorlar"),
        ]

        for key, label in tab_names:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"  {label}  ")

            # Info label at top of each tab
            info_frame = ttk.Frame(frame)
            info_frame.pack(fill="x", pady=(5, 0))
            info_var = tk.StringVar(value="")
            ttk.Label(info_frame, textvariable=info_var,
                      style="Subtitle.TLabel").pack(side="left", padx=10)
            count_var = tk.StringVar(value="")
            ttk.Label(info_frame, textvariable=count_var,
                      style="Subtitle.TLabel").pack(side="right", padx=10)

            tree = self._create_treeview(frame, key)
            self.tabs[key] = {
                "tree": tree,
                "info": info_var,
                "count": count_var,
            }

    def _create_treeview(self, parent, tab_key) -> ttk.Treeview:
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        yscroll = ttk.Scrollbar(container, orient="vertical")
        xscroll = ttk.Scrollbar(container, orient="horizontal")

        tree = ttk.Treeview(container, show="headings",
                             yscrollcommand=yscroll.set,
                             xscrollcommand=xscroll.set)

        yscroll.config(command=tree.yview)
        xscroll.config(command=tree.xview)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        return tree

    def _populate_tree(self, tab_key: str, columns: list[tuple[str, int]],
                       rows: list[list], info_text: str = "", count_text: str = ""):
        tab = self.tabs[tab_key]
        tree = tab["tree"]

        tree.delete(*tree.get_children())
        tree["columns"] = [c[0] for c in columns]

        for col_name, width in columns:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=width, minwidth=40, anchor="center")

        # Left-align name columns
        for col_name, _ in columns:
            if col_name in ("Takim", "Oyuncu", "Isim", "Ev Sahibi", "Deplasman", "Lig"):
                tree.column(col_name, anchor="w")

        for row in rows:
            tree.insert("", "end", values=row)

        tab["info"].set(info_text)
        tab["count"].set(count_text)

    # --- Event handlers ---

    def _on_league_change(self, event=None):
        idx = self.league_combo.current()
        keys = list(LEAGUES.keys())
        if 0 <= idx < len(keys):
            self.league_var.set(keys[idx])
            league = LEAGUES[keys[idx]]
            self.league_info_var.set(f"{league['country']} - {league['name']}")

    def _select_all(self):
        for var in self.cb_vars.values():
            var.set(True)

    def _select_none(self):
        for var in self.cb_vars.values():
            var.set(False)

    def _set_status(self, text: str, color: str = GREEN):
        self.status_var.set(text)
        ttk.Style().configure("Status.TLabel", foreground=color)

    def _set_fetching(self, active: bool):
        self.is_fetching = active
        state = "disabled" if active else "normal"
        self.fetch_btn.configure(state=state)
        self.live_btn.configure(state=state)
        self.today_btn.configure(state=state)
        if active:
            self.progress.start(10)
        else:
            self.progress.stop()

    # --- Data fetching ---

    def _on_fetch(self):
        if self.is_fetching:
            return
        # Check at least one stat selected
        if not any(v.get() for v in self.cb_vars.values()):
            messagebox.showwarning("Uyari", "En az bir istatistik secmelisiniz!")
            return
        self._set_fetching(True)
        self._set_status("Veriler cekiliyor...", YELLOW)
        threading.Thread(target=self._fetch_league_data, daemon=True).start()

    def _on_live(self):
        if self.is_fetching:
            return
        self._set_fetching(True)
        self._set_status("Canli skorlar yukleniyor...", YELLOW)
        threading.Thread(target=self._fetch_live_data, daemon=True).start()

    def _on_today(self):
        if self.is_fetching:
            return
        self._set_fetching(True)
        self._set_status("Bugunun maclari yukleniyor...", YELLOW)
        threading.Thread(target=self._fetch_today_data, daemon=True).start()

    def _fetch_league_data(self):
        try:
            league_key = self.league_var.get()
            league_name = LEAGUES.get(league_key, {}).get("name", league_key)

            if self.demo_mode.get():
                data = LeagueData(league_name=league_name)
                if self.cb_vars["standings"].get():
                    data.standings = get_sample_standings(league_key)
                if self.cb_vars["scorers"].get():
                    data.top_scorers = get_sample_player_stats(league_key, "gol-kralligi")
                if self.cb_vars["assists"].get():
                    data.top_assists = get_sample_player_stats(league_key, "asist")
                if self.cb_vars["yellow_cards"].get():
                    data.yellow_cards = get_sample_player_stats(league_key, "sari-kart")
                if self.cb_vars["red_cards"].get():
                    data.red_cards = get_sample_player_stats(league_key, "kirmizi-kart")
                if self.cb_vars["matches"].get():
                    data.matches = get_sample_matches(league_key)
                if self.cb_vars["team_stats"].get():
                    data.team_stats = get_sample_team_stats(league_key)
            else:
                with MackolikScraper() as scraper:
                    data = LeagueData(league_name=league_name)
                    total = sum(1 for v in self.cb_vars.values() if v.get())
                    done = 0

                    if self.cb_vars["standings"].get():
                        self.root.after(0, lambda: self._set_status(
                            f"[{done+1}/{total}] {league_name} - Puan durumu...", YELLOW))
                        data.standings = fetch_standings(scraper, league_key)
                        done += 1

                    if self.cb_vars["scorers"].get():
                        self.root.after(0, lambda d=done, t=total: self._set_status(
                            f"[{d+1}/{t}] {league_name} - Gol kralligi...", YELLOW))
                        data.top_scorers = fetch_top_scorers(scraper, league_key)
                        done += 1

                    if self.cb_vars["assists"].get():
                        self.root.after(0, lambda d=done, t=total: self._set_status(
                            f"[{d+1}/{t}] {league_name} - Asistler...", YELLOW))
                        data.top_assists = fetch_top_assists(scraper, league_key)
                        done += 1

                    if self.cb_vars["yellow_cards"].get():
                        self.root.after(0, lambda d=done, t=total: self._set_status(
                            f"[{d+1}/{t}] {league_name} - Sari kartlar...", YELLOW))
                        data.yellow_cards = fetch_yellow_cards(scraper, league_key)
                        done += 1

                    if self.cb_vars["red_cards"].get():
                        self.root.after(0, lambda d=done, t=total: self._set_status(
                            f"[{d+1}/{t}] {league_name} - Kirmizi kartlar...", YELLOW))
                        data.red_cards = fetch_red_cards(scraper, league_key)
                        done += 1

                    if self.cb_vars["matches"].get():
                        self.root.after(0, lambda d=done, t=total: self._set_status(
                            f"[{d+1}/{t}] {league_name} - Maclar...", YELLOW))
                        data.matches = fetch_matches(scraper, league_key)
                        done += 1

                    if self.cb_vars["team_stats"].get():
                        self.root.after(0, lambda d=done, t=total: self._set_status(
                            f"[{d+1}/{t}] {league_name} - Takim istatistikleri...", YELLOW))
                        data.team_stats = fetch_team_stats(scraper, league_key)
                        done += 1

            self.current_data = data
            self.root.after(0, lambda: self._display_league_data(data))

            # Build summary
            parts = []
            if data.standings:
                parts.append(f"{len(data.standings)} takim")
            if data.top_scorers:
                parts.append(f"{len(data.top_scorers)} golcu")
            if data.matches:
                parts.append(f"{len(data.matches)} mac")
            summary = ", ".join(parts) if parts else "Veri bulunamadi"

            mode = " (Demo)" if self.demo_mode.get() else ""
            self.root.after(0, lambda: self._set_status(
                f"{league_name} yuklendi: {summary}{mode}", GREEN))

        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Hata: {e}", RED))
        finally:
            self.root.after(0, lambda: self._set_fetching(False))

    def _fetch_live_data(self):
        try:
            if self.demo_mode.get():
                matches = get_sample_live_scores()
            else:
                with MackolikScraper() as scraper:
                    matches = fetch_live_scores(scraper)

            self.live_data = matches
            self.root.after(0, lambda: self._display_live(matches))
            count = len(matches)
            live_count = sum(1 for m in matches if m.status in ("Canli", "live"))
            mode = " (Demo)" if self.demo_mode.get() else ""
            self.root.after(0, lambda: self._set_status(
                f"{count} mac bulundu, {live_count} canli{mode}", GREEN))

        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Hata: {e}", RED))
        finally:
            self.root.after(0, lambda: self._set_fetching(False))

    def _fetch_today_data(self):
        try:
            if self.demo_mode.get():
                matches = get_sample_live_scores()
            else:
                with MackolikScraper() as scraper:
                    matches = fetch_todays_matches(scraper)

            self.live_data = matches
            self.root.after(0, lambda: self._display_live(matches))
            count = len(matches)
            mode = " (Demo)" if self.demo_mode.get() else ""
            self.root.after(0, lambda: self._set_status(
                f"Bugun {count} mac bulundu{mode}", GREEN))

        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Hata: {e}", RED))
        finally:
            self.root.after(0, lambda: self._set_fetching(False))

    # --- Display methods ---

    def _display_league_data(self, data: LeagueData):
        league = data.league_name

        # Standings
        if data.standings:
            cols = [("#", 35), ("Takim", 170), ("O", 35), ("G", 35), ("B", 35),
                    ("M", 35), ("AG", 45), ("YG", 45), ("AV", 50), ("P", 45)]
            rows = []
            for t in data.standings:
                av = f"{t.goal_difference:+d}" if t.goal_difference != 0 else "0"
                rows.append([t.position, t.name, t.played, t.won, t.drawn, t.lost,
                              t.goals_for, t.goals_against, av, t.points])
            self._populate_tree("standings", cols, rows,
                                info_text=f"{league} - 2024/25 Sezonu",
                                count_text=f"{len(data.standings)} takim")
            self.notebook.select(0)

        # Player stats
        self._display_player_stats(data.top_scorers, "scorers", f"{league} - Gol Kralligi")
        self._display_player_stats(data.top_assists, "assists", f"{league} - Asist Siralamasi")
        self._display_player_stats(data.yellow_cards, "yellow_cards", f"{league} - Sari Kartlar")
        self._display_player_stats(data.red_cards, "red_cards", f"{league} - Kirmizi Kartlar")

        # Matches
        if data.matches:
            cols = [("Tarih", 90), ("Saat", 60), ("Ev Sahibi", 150),
                    ("Skor", 70), ("Deplasman", 150), ("Durum", 80)]
            rows = []
            for m in data.matches:
                if m.home_score is not None:
                    score = f"{m.home_score} - {m.away_score}"
                else:
                    score = "- : -"
                rows.append([m.date, m.time, m.home_team, score, m.away_team, m.status])
            self._populate_tree("matches", cols, rows,
                                info_text=f"{league} - Mac Programi",
                                count_text=f"{len(data.matches)} mac")

        # Team stats
        if data.team_stats:
            cols = [("Takim", 170), ("Mac", 50), ("Gol", 50), ("Yenilen", 60),
                    ("Ort.Gol", 70), ("Ort.Yen.", 70), ("Gol Yememe", 80)]
            rows = [[s.name, s.matches_played, s.total_goals, s.goals_conceded,
                      f"{s.avg_goals_per_match:.2f}", f"{s.avg_conceded_per_match:.2f}",
                      s.clean_sheets] for s in data.team_stats]
            self._populate_tree("team_stats", cols, rows,
                                info_text=f"{league} - Takim Istatistikleri",
                                count_text=f"{len(data.team_stats)} takim")

    def _display_player_stats(self, players: list, tab_key: str, title: str):
        if not players:
            return
        cols = [("#", 35), ("Oyuncu", 190), ("Takim", 150), ("Mac", 50), ("Deger", 60)]
        rows = [[p.rank, p.name, p.team, p.matches_played, p.value] for p in players]
        self._populate_tree(tab_key, cols, rows,
                            info_text=title,
                            count_text=f"{len(players)} oyuncu")

    def _display_live(self, matches: list):
        cols = [("Lig", 160), ("Ev Sahibi", 150), ("Skor", 70),
                ("Deplasman", 150), ("Dk", 60), ("Durum", 90)]
        rows = []
        for m in matches:
            if m.home_score is not None and m.away_score is not None:
                score = f"{m.home_score} - {m.away_score}"
            else:
                score = "- : -"
            rows.append([m.league, m.home_team, score, m.away_team, m.minute, m.status])

        now = datetime.now().strftime("%H:%M:%S")
        live_count = sum(1 for m in matches if m.status in ("Canli", "live"))

        self._populate_tree("live", cols, rows,
                            info_text=f"Son guncelleme: {now}",
                            count_text=f"{len(matches)} mac ({live_count} canli)")

        # Switch to live tab
        self.notebook.select(7)

    # --- Export ---

    def _export(self, fmt: str):
        if self.current_data is None:
            messagebox.showwarning("Uyari", "Once veri cekmeniz gerekiyor!")
            return

        league_key = self.league_var.get()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if fmt == "json":
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
                initialfile=f"mackolik_{league_key}_{timestamp}.json",
            )
            if path:
                export_json(self.current_data.to_dict(), path)
                self._set_status(f"JSON kaydedildi: {path}", GREEN)

        elif fmt == "csv":
            directory = filedialog.askdirectory(title="CSV dosyalari icin klasor secin")
            if directory:
                sheets = self._get_export_sheets()
                for name, items in sheets.items():
                    safe = name.lower().replace(" ", "_")
                    for tr_char, en_char in [("i", "i"), ("s", "s"), ("o", "o"),
                                              ("u", "u"), ("g", "g"), ("c", "c")]:
                        safe = safe.replace(tr_char, en_char)
                    export_csv(items, f"{directory}/{safe}_{timestamp}.csv")
                self._set_status(f"CSV dosyalari kaydedildi: {directory}", GREEN)

        elif fmt == "excel":
            path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile=f"mackolik_{league_key}_{timestamp}.xlsx",
            )
            if path:
                sheets = self._get_export_sheets()
                export_excel(sheets, path)
                self._set_status(f"Excel kaydedildi: {path}", GREEN)

    def _get_export_sheets(self) -> dict:
        sheets = {}
        if self.current_data:
            d = self.current_data
            if d.standings:
                sheets["Puan Durumu"] = d.standings
            if d.top_scorers:
                sheets["Gol Kralligi"] = d.top_scorers
            if d.top_assists:
                sheets["Asist"] = d.top_assists
            if d.yellow_cards:
                sheets["Sari Kart"] = d.yellow_cards
            if d.red_cards:
                sheets["Kirmizi Kart"] = d.red_cards
            if d.matches:
                sheets["Maclar"] = d.matches
            if d.team_stats:
                sheets["Takim Istatistikleri"] = d.team_stats
        return sheets


def main():
    root = tk.Tk()
    MackolikApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
