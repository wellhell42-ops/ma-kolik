#!/usr/bin/env python3
"""
Maçkolik İstatistik Toplayıcı - Windows Masaüstü Uygulaması

Tkinter tabanlı GUI ile tüm futbol istatistiklerini çekin.
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
)


# --- Color theme ---
BG_DARK = "#1a1a2e"
BG_CARD = "#16213e"
BG_INPUT = "#0f3460"
FG_TEXT = "#e0e0e0"
FG_DIM = "#8892a0"
FG_TITLE = "#ffffff"
ACCENT = "#e94560"
ACCENT_HOVER = "#ff6b81"
GREEN = "#2ecc71"
YELLOW = "#f1c40f"
BLUE = "#3498db"


class MackolikApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Maçkolik İstatistik Toplayıcı")
        self.root.geometry("1100x750")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        # Try to set icon (won't fail if missing)
        try:
            self.root.iconbitmap("mackolik.ico")
        except tk.TclError:
            pass

        self.demo_mode = tk.BooleanVar(value=False)
        self.is_fetching = False
        self.current_data = None

        self._setup_styles()
        self._build_ui()

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG_DARK, foreground=FG_TITLE, font=("Segoe UI", 18, "bold"))
        style.configure("Subtitle.TLabel", background=BG_DARK, foreground=FG_DIM, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=BG_CARD, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background=BG_CARD, foreground=FG_TITLE, font=("Segoe UI", 11, "bold"))
        style.configure("Status.TLabel", background=BG_DARK, foreground=GREEN, font=("Segoe UI", 9))

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

        style.configure("Live.TButton", background="#c0392b", foreground="white",
                         font=("Segoe UI", 11, "bold"), padding=(20, 10))
        style.map("Live.TButton", background=[("active", "#e74c3c")])

        style.configure("Treeview", background=BG_CARD, foreground=FG_TEXT,
                         fieldbackground=BG_CARD, font=("Segoe UI", 9),
                         rowheight=28)
        style.configure("Treeview.Heading", background=BG_INPUT, foreground=FG_TITLE,
                         font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", ACCENT)])

    def _build_ui(self):
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=20, pady=(15, 5))

        ttk.Label(header, text="Maçkolik İstatistik Toplayıcı",
                  style="Title.TLabel").pack(side="left")

        # Demo toggle in header
        demo_frame = ttk.Frame(header)
        demo_frame.pack(side="right")
        ttk.Checkbutton(demo_frame, text="Demo Modu",
                         variable=self.demo_mode,
                         style="TCheckbutton").pack(side="right", padx=5)

        ttk.Label(header, text="Tüm futbol verilerini tek tıkla çekin",
                  style="Subtitle.TLabel").pack(side="left", padx=(15, 0))

        # Main content area
        content = ttk.Frame(self.root)
        content.pack(fill="both", expand=True, padx=20, pady=10)

        # Left panel - Controls
        left = ttk.Frame(content, style="Card.TFrame", width=280)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._build_controls(left)

        # Right panel - Results
        right = ttk.Frame(content)
        right.pack(side="left", fill="both", expand=True)

        self._build_results(right)

        # Status bar
        self.status_var = tk.StringVar(value="Hazır")
        status_bar = ttk.Frame(self.root)
        status_bar.pack(fill="x", padx=20, pady=(0, 10))
        self.status_label = ttk.Label(status_bar, textvariable=self.status_var,
                                       style="Status.TLabel")
        self.status_label.pack(side="left")

    def _build_controls(self, parent):
        pad = {"padx": 15, "pady": 5}

        # League selection
        ttk.Label(parent, text="Lig Seçimi", style="CardTitle.TLabel").pack(padx=15, anchor="w", pady=(15, 5))

        league_names = {k: v["name"] for k, v in LEAGUES.items()}
        self.league_var = tk.StringVar(value="super-lig")
        league_combo = ttk.Combobox(parent, textvariable=self.league_var,
                                     values=list(league_names.keys()),
                                     state="readonly", width=28)
        league_combo.pack(**pad, anchor="w")

        # Display league name
        self.league_name_var = tk.StringVar(value=league_names.get("super-lig", ""))
        ttk.Label(parent, textvariable=self.league_name_var,
                  style="Card.TLabel").pack(padx=15, anchor="w")

        league_combo.bind("<<ComboboxSelected>>",
                          lambda e: self.league_name_var.set(
                              league_names.get(self.league_var.get(), "")))

        # Separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=15, pady=10)

        # Stats checkboxes
        ttk.Label(parent, text="İstatistikler", style="CardTitle.TLabel").pack(**pad, anchor="w")

        self.cb_vars = {}
        checks = [
            ("standings", "Puan Durumu"),
            ("scorers", "Gol Krallığı"),
            ("assists", "Asist Sıralaması"),
            ("yellow_cards", "Sarı Kartlar"),
            ("red_cards", "Kırmızı Kartlar"),
            ("matches", "Maç Sonuçları"),
            ("team_stats", "Takım İstatistikleri"),
        ]
        for key, label in checks:
            var = tk.BooleanVar(value=True)
            self.cb_vars[key] = var
            ttk.Checkbutton(parent, text=label, variable=var,
                             style="TCheckbutton").pack(padx=20, anchor="w", pady=2)

        # Separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=15, pady=10)

        # Action buttons
        ttk.Label(parent, text="İşlemler", style="CardTitle.TLabel").pack(**pad, anchor="w")

        self.fetch_btn = ttk.Button(parent, text="Verileri Çek",
                                     style="Accent.TButton",
                                     command=self._on_fetch)
        self.fetch_btn.pack(padx=15, pady=5, fill="x")

        self.live_btn = ttk.Button(parent, text="Canlı Skorlar",
                                    style="Live.TButton",
                                    command=self._on_live)
        self.live_btn.pack(padx=15, pady=5, fill="x")

        ttk.Button(parent, text="Bugünün Maçları",
                    style="Secondary.TButton",
                    command=self._on_today).pack(padx=15, pady=5, fill="x")

        # Separator
        ttk.Separator(parent, orient="horizontal").pack(fill="x", padx=15, pady=10)

        # Export buttons
        ttk.Label(parent, text="Dışa Aktar", style="CardTitle.TLabel").pack(**pad, anchor="w")

        export_frame = ttk.Frame(parent, style="Card.TFrame")
        export_frame.pack(padx=15, fill="x")

        ttk.Button(export_frame, text="JSON", style="Secondary.TButton",
                    command=lambda: self._export("json")).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(export_frame, text="CSV", style="Secondary.TButton",
                    command=lambda: self._export("csv")).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(export_frame, text="Excel", style="Secondary.TButton",
                    command=lambda: self._export("excel")).pack(side="left", expand=True, fill="x", padx=2)

    def _build_results(self, parent):
        # Tabs for different result types
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        # Create tabs
        self.tabs = {}
        tab_names = [
            ("standings", "Puan Durumu"),
            ("scorers", "Gol Krallığı"),
            ("assists", "Asist"),
            ("yellow_cards", "Sarı Kart"),
            ("red_cards", "Kırmızı Kart"),
            ("matches", "Maçlar"),
            ("team_stats", "Takım İst."),
            ("live", "Canlı Skorlar"),
        ]

        for key, label in tab_names:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=f"  {label}  ")
            tree = self._create_treeview(frame, key)
            self.tabs[key] = tree

    def _create_treeview(self, parent, tab_key) -> ttk.Treeview:
        """Create a treeview with scrollbar for a tab."""
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True)

        # Scrollbars
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

    def _populate_tree(self, tree: ttk.Treeview, columns: list[tuple[str, int]],
                       rows: list[list[str]]):
        """Clear and populate a treeview with data."""
        # Clear existing
        tree.delete(*tree.get_children())
        tree["columns"] = [c[0] for c in columns]

        for col_name, width in columns:
            tree.heading(col_name, text=col_name)
            tree.column(col_name, width=width, minwidth=50, anchor="center")

        # Left-align name columns
        for col_name, _ in columns:
            if col_name in ("Takım", "Oyuncu", "İsim", "Ev Sahibi", "Deplasman", "Lig"):
                tree.column(col_name, anchor="w")

        for row in rows:
            tree.insert("", "end", values=row)

    def _set_status(self, text: str, color: str = GREEN):
        self.status_var.set(text)
        style = ttk.Style()
        style.configure("Status.TLabel", foreground=color)

    def _set_fetching(self, active: bool):
        self.is_fetching = active
        state = "disabled" if active else "normal"
        self.fetch_btn.configure(state=state)
        self.live_btn.configure(state=state)

    # --- Data fetching ---

    def _on_fetch(self):
        if self.is_fetching:
            return
        self._set_fetching(True)
        self._set_status("Veriler çekiliyor...", YELLOW)
        threading.Thread(target=self._fetch_league_data, daemon=True).start()

    def _on_live(self):
        if self.is_fetching:
            return
        self._set_fetching(True)
        self._set_status("Canlı skorlar yükleniyor...", YELLOW)
        threading.Thread(target=self._fetch_live_data, daemon=True).start()

    def _on_today(self):
        if self.is_fetching:
            return
        self._set_fetching(True)
        self._set_status("Bugünün maçları yükleniyor...", YELLOW)
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
            else:
                with MackolikScraper() as scraper:
                    data = LeagueData(league_name=league_name)
                    if self.cb_vars["standings"].get():
                        self._set_status(f"{league_name} - Puan durumu...", YELLOW)
                        data.standings = fetch_standings(scraper, league_key)
                    if self.cb_vars["scorers"].get():
                        self._set_status(f"{league_name} - Gol krallığı...", YELLOW)
                        data.top_scorers = fetch_top_scorers(scraper, league_key)
                    if self.cb_vars["assists"].get():
                        self._set_status(f"{league_name} - Asistler...", YELLOW)
                        data.top_assists = fetch_top_assists(scraper, league_key)
                    if self.cb_vars["yellow_cards"].get():
                        self._set_status(f"{league_name} - Sarı kartlar...", YELLOW)
                        data.yellow_cards = fetch_yellow_cards(scraper, league_key)
                    if self.cb_vars["red_cards"].get():
                        self._set_status(f"{league_name} - Kırmızı kartlar...", YELLOW)
                        data.red_cards = fetch_red_cards(scraper, league_key)
                    if self.cb_vars["matches"].get():
                        self._set_status(f"{league_name} - Maçlar...", YELLOW)
                        data.matches = fetch_matches(scraper, league_key)
                    if self.cb_vars["team_stats"].get():
                        self._set_status(f"{league_name} - Takım istatistikleri...", YELLOW)
                        data.team_stats = fetch_team_stats(scraper, league_key)

            self.current_data = data
            self.root.after(0, lambda: self._display_league_data(data))
            self.root.after(0, lambda: self._set_status(
                f"{league_name} verileri yüklendi" +
                (" (Demo)" if self.demo_mode.get() else ""), GREEN))

        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Hata: {e}", ACCENT))
        finally:
            self.root.after(0, lambda: self._set_fetching(False))

    def _fetch_live_data(self):
        try:
            if self.demo_mode.get():
                matches = get_sample_live_scores()
            else:
                with MackolikScraper() as scraper:
                    matches = fetch_live_scores(scraper)

            self.root.after(0, lambda: self._display_live(matches))
            count = len(matches)
            self.root.after(0, lambda: self._set_status(
                f"{count} canlı maç bulundu" +
                (" (Demo)" if self.demo_mode.get() else ""), GREEN))

        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Hata: {e}", ACCENT))
        finally:
            self.root.after(0, lambda: self._set_fetching(False))

    def _fetch_today_data(self):
        try:
            if self.demo_mode.get():
                matches = get_sample_live_scores()
            else:
                with MackolikScraper() as scraper:
                    matches = fetch_todays_matches(scraper)

            self.root.after(0, lambda: self._display_live(matches))
            count = len(matches)
            self.root.after(0, lambda: self._set_status(
                f"Bugün {count} maç bulundu" +
                (" (Demo)" if self.demo_mode.get() else ""), GREEN))

        except Exception as e:
            self.root.after(0, lambda: self._set_status(f"Hata: {e}", ACCENT))
        finally:
            self.root.after(0, lambda: self._set_fetching(False))

    # --- Display methods ---

    def _display_league_data(self, data: LeagueData):
        # Standings
        if data.standings:
            cols = [("#", 40), ("Takım", 160), ("O", 40), ("G", 40), ("B", 40),
                    ("M", 40), ("AG", 50), ("YG", 50), ("AV", 50), ("P", 50)]
            rows = [[t.position, t.name, t.played, t.won, t.drawn, t.lost,
                      t.goals_for, t.goals_against,
                      f"{t.goal_difference:+d}" if t.goal_difference != 0 else "0",
                      t.points] for t in data.standings]
            self._populate_tree(self.tabs["standings"], cols, rows)
            self.notebook.select(0)

        # Player stats
        self._display_player_stats(data.top_scorers, "scorers")
        self._display_player_stats(data.top_assists, "assists")
        self._display_player_stats(data.yellow_cards, "yellow_cards")
        self._display_player_stats(data.red_cards, "red_cards")

        # Matches
        if data.matches:
            cols = [("Tarih", 90), ("Saat", 60), ("Ev Sahibi", 140),
                    ("Skor", 70), ("Deplasman", 140), ("Durum", 80)]
            rows = []
            for m in data.matches:
                score = f"{m.home_score} - {m.away_score}" if m.home_score is not None else "- : -"
                rows.append([m.date, m.time, m.home_team, score, m.away_team, m.status])
            self._populate_tree(self.tabs["matches"], cols, rows)

        # Team stats
        if data.team_stats:
            cols = [("Takım", 160), ("Maç", 50), ("Gol", 50), ("Yenilen", 60),
                    ("Ort.Gol", 70), ("Ort.Yen.", 70), ("Gol Yememe", 80)]
            rows = [[s.name, s.matches_played, s.total_goals, s.goals_conceded,
                      f"{s.avg_goals_per_match:.2f}", f"{s.avg_conceded_per_match:.2f}",
                      s.clean_sheets] for s in data.team_stats]
            self._populate_tree(self.tabs["team_stats"], cols, rows)

    def _display_player_stats(self, players: list, tab_key: str):
        if not players:
            return
        cols = [("#", 40), ("Oyuncu", 180), ("Takım", 140), ("Maç", 50), ("Değer", 60)]
        rows = [[p.rank, p.name, p.team, p.matches_played, p.value] for p in players]
        self._populate_tree(self.tabs[tab_key], cols, rows)

    def _display_live(self, matches: list):
        cols = [("Lig", 140), ("Ev Sahibi", 140), ("Skor", 70),
                ("Deplasman", 140), ("Dk", 60), ("Durum", 80)]
        rows = []
        for m in matches:
            if m.home_score is not None and m.away_score is not None:
                score = f"{m.home_score} - {m.away_score}"
            else:
                score = "- : -"
            rows.append([m.league, m.home_team, score, m.away_team, m.minute, m.status])
        self._populate_tree(self.tabs["live"], cols, rows)

        # Switch to live tab
        self.notebook.select(7)

    # --- Export ---

    def _export(self, fmt: str):
        if self.current_data is None:
            messagebox.showwarning("Uyarı", "Önce veri çekmeniz gerekiyor!")
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
            directory = filedialog.askdirectory(title="CSV dosyaları için klasör seçin")
            if directory:
                sheets = self._get_export_sheets()
                for name, items in sheets.items():
                    safe = name.lower().replace(" ", "_")
                    for tr_char, en_char in [("ı", "i"), ("ş", "s"), ("ö", "o"),
                                              ("ü", "u"), ("ğ", "g"), ("ç", "c")]:
                        safe = safe.replace(tr_char, en_char)
                    export_csv(items, f"{directory}/{safe}_{timestamp}.csv")
                self._set_status(f"CSV dosyaları kaydedildi: {directory}", GREEN)

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
                sheets["Gol Krallığı"] = d.top_scorers
            if d.top_assists:
                sheets["Asist"] = d.top_assists
            if d.yellow_cards:
                sheets["Sarı Kart"] = d.yellow_cards
            if d.red_cards:
                sheets["Kırmızı Kart"] = d.red_cards
            if d.matches:
                sheets["Maçlar"] = d.matches
            if d.team_stats:
                sheets["Takım İstatistikleri"] = d.team_stats
        return sheets


def main():
    root = tk.Tk()
    app = MackolikApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
