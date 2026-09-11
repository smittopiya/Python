
# frames/dashboard.py — Dashboard Frame
import tkinter as tk
from tkinter import ttk
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *
from utils import fmt_currency


class DashboardFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db = db
        self.stat_labels = {}
        self._build_ui()

    # ─── Main Layout ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        sf = tk.Frame(self, bg=BG_MAIN)
        sf.pack(fill="both", expand=True)

        # ── Page Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(sf, bg=BG_MAIN, padx=30, pady=18)
        hdr.pack(fill="x")

        hdr_left = tk.Frame(hdr, bg=BG_MAIN)
        hdr_left.pack(side="left", fill="x", expand=True)
        tk.Label(hdr_left, text="OVERVIEW", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hdr_left, text="Dashboard", font=FONT_HEADING,
                 bg=BG_MAIN, fg=GOLD).pack(anchor="w")
        tk.Label(hdr_left,
                 text="Welcome to The Veloria Grand — 7-Star Luxury Management Console",
                 font=FONT_SMALL, bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")

        # Refresh button
        ttk.Button(hdr, text="🔄  Refresh Stats",
                   command=self.refresh).pack(side="right", padx=4)

        tk.Frame(sf, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # ── Stats Grid (2 rows × 3 cols) ────────────────────────────────────────
        grid_wrap = tk.Frame(sf, bg=BG_MAIN)
        grid_wrap.pack(fill="x", padx=25, pady=20)

        stats_config = [
            ("🏨", "Total Rooms",       "total_rooms",        GOLD,          "All registered rooms"),
            ("👥", "Active Guests",     "active_guests",      BLUE_ACCENT,   "Checked-in today"),
            ("📋", "Registered Guests", "registered_clients", SUCCESS,       "All-time client records"),
            ("💳", "Pending Payments",  "pending_payments",   DANGER,        "Awaiting settlement"),
            ("📅", "Total Bookings",    "total_bookings",     PURPLE_ACCENT, "All reservations ever"),
            ("💰", "Revenue Earned",    "total_revenue",      TEAL_ACCENT,   "Total paid invoices"),
        ]

        for i, (icon, title, key, color, sub) in enumerate(stats_config):
            card = self._make_stat_card(grid_wrap, icon, title, key, color, sub)
            card.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")

        for c in range(3):
            grid_wrap.columnconfigure(c, weight=1)

        tk.Frame(sf, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # ── Infinity Pool & Cabanas info card (full width) ───────────────────────
        self._build_pool_card(sf)

        tk.Frame(sf, bg=GOLD_DARK, height=1).pack(fill="x", padx=30, pady=(14, 20))

    # ─── Stat Card ────────────────────────────────────────────────────────────────
    def _make_stat_card(self, parent, icon, title, key, color, subtitle):
        outer = tk.Frame(parent, bg=BG_CARD,
                         highlightbackground=BORDER, highlightthickness=1)

        # Accent top bar
        bar = tk.Canvas(outer, bg=color, height=4, highlightthickness=0, bd=0)
        bar.pack(fill="x")

        body = tk.Frame(outer, bg=BG_CARD, padx=22, pady=16)
        body.pack(fill="both", expand=True)

        top = tk.Frame(body, bg=BG_CARD)
        top.pack(fill="x")
        tk.Label(top, text=icon, font=("Segoe UI Emoji", 22),
                 bg=BG_CARD, fg=color).pack(side="left")
        val_lbl = tk.Label(top, text="—", font=FONT_BIG_NUM,
                           bg=BG_CARD, fg=CREAM)
        val_lbl.pack(side="right")

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(12, 8))
        tk.Label(body, text=title, font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_LIGHT).pack(anchor="w")
        tk.Label(body, text=subtitle, font=FONT_SMALL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(anchor="w")

        self.stat_labels[key] = val_lbl
        return outer

    # ─── Pool Card (full-width) ─────────────────────────────────────────────────────
    def _build_pool_card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER_GOLD, highlightthickness=1)
        card.pack(fill="x", padx=25, pady=(14, 0))

        hdr = tk.Frame(card, bg=GOLD_SUBTLE, pady=10, padx=20)
        hdr.pack(fill="x")
        tk.Label(hdr, text="🏊  INFINITY POOL & CABANAS", font=("Segoe UI", 11, "bold"),
                 bg=GOLD_SUBTLE, fg=BLUE_ACCENT).pack(side="left")
        tk.Label(hdr, text="Veloria Grand · Exclusive Amenity", font=FONT_SMALL,
                 bg=GOLD_SUBTLE, fg=TEXT_MUTED).pack(side="right")

        body = tk.Frame(card, bg=BG_CARD, padx=20, pady=14)
        body.pack(fill="x")

        # 6 info items in 2 rows × 3 cols for a wide card
        info = [
            ("Pool Length",     "50 Metres · Infinity Edge"),
            ("Depth Range",     "1.2 m — 2.4 m"),
            ("Private Cabanas", "12 Luxury Units"),
            ("Open Hours",      "6:00 AM — 10:00 PM"),
            ("Total Area",      "6,800 sq. ft."),
            ("Features",        "Heated · LED Lit · Bar Access"),
        ]
        for col_idx in range(3):
            body.columnconfigure(col_idx, weight=1)

        for i, (lbl, val) in enumerate(info):
            cell = tk.Frame(body, bg=BG_CARD)
            cell.grid(row=i // 3, column=i % 3, sticky="w", padx=16, pady=4)
            tk.Label(cell, text=f"{lbl}:", font=FONT_LABEL,
                     bg=BG_CARD, fg=BLUE_ACCENT).pack(anchor="w")
            tk.Label(cell, text=val, font=FONT_BODY,
                     bg=BG_CARD, fg=CREAM).pack(anchor="w")

    # ─── Stats Refresh ────────────────────────────────────────────────────────────
    def refresh(self):
        stats = self.db.get_dashboard_stats()
        for key, lbl in self.stat_labels.items():
            val = stats.get(key, 0)
            lbl.config(text=fmt_currency(val) if key == "total_revenue" else str(val))
