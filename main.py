
"""
THE VELORIA GRAND — Hotel Management System
============================================
University Project
Authors: Developed with Python & Tkinter

Dependencies (install before running):
    pip install tkcalendar matplotlib Pillow fpdf2

Usage:
    python main.py

Images: Place room photos in the "Images/" folder (same directory as main.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox, font as tkfont
import sys, os
from datetime import datetime

# ── Make sure the project root is on the path ──────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from database import Database
from styles  import apply_theme, make_scrollable
from styles  import (BG_MAIN, BG_SIDEBAR, BG_CARD, BG_INPUT,
                     GOLD, GOLD_DARK, GOLD_LIGHT, GOLD_SUBTLE, GOLD_BORDER,
                     CREAM, TEXT_LIGHT, TEXT_MUTED, BORDER, BORDER_GOLD,
                     SUCCESS, WARNING, DANGER, INFO,
                     BLUE_ACCENT, PURPLE_ACCENT, TEAL_ACCENT,
                     FONT_BRAND, FONT_HEADING, FONT_SUBHEAD, FONT_LABEL,
                     FONT_BODY, FONT_SMALL, SIDEBAR_WIDTH, TOPBAR_HEIGHT)

from frames.dashboard    import DashboardFrame
from frames.rooms        import RoomsFrame
from frames.show_rooms   import ShowRoomsFrame
from frames.clients      import ClientsFrame
from frames.reservations import ReservationsFrame
from frames.payments     import PaymentsFrame
from frames.analytics    import AnalyticsFrame


# ─── Nav Config ─────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("⬛", "🏛",  "Dashboard",    "dashboard"),
    ("⬛", "🚪",  "Rooms",        "rooms"),
    ("⬛", "📋",  "Show Rooms",   "show_rooms"),
    ("⬛", "👤",  "Clients",      "clients"),
    ("⬛", "📅",  "Reservations", "reservations"),
    ("⬛", "💳",  "Payments",     "payments"),
    ("⬛", "📊",  "Analytics",    "analytics"),
]


class HotelApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.db = Database()

        self.title("The Veloria Grand — Hotel Management System")
        self.geometry("1440x900")
        self.minsize(1200, 720)
        self.configure(bg=BG_MAIN)

        # App icon (skip silently if not found)
        icon_path = os.path.join(BASE_DIR, "Images", "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass

        apply_theme(self)
        self._build_ui()
        self._update_clock()
        self.show_frame("dashboard")
        self._center_window()

    # ─── Layout ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        self._root_frame = tk.Frame(self, bg=BG_MAIN)
        self._root_frame.pack(fill="both", expand=True)

        self._build_topbar()

        # Gold divider
        tk.Frame(self._root_frame, bg=GOLD, height=2).pack(fill="x")

        bottom = tk.Frame(self._root_frame, bg=BG_MAIN)
        bottom.pack(fill="both", expand=True)

        self._build_sidebar(bottom)
        # Thin gold border between sidebar and content
        tk.Frame(bottom, bg=GOLD_DARK, width=1).pack(side="left", fill="y")

        self._content = tk.Frame(bottom, bg=BG_MAIN)
        self._content.pack(side="left", fill="both", expand=True)

        self._init_frames()

    def _build_topbar(self):
        bar = tk.Frame(self._root_frame, bg=BG_SIDEBAR, height=TOPBAR_HEIGHT)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # ── Left: Logo & Name ────────────────────────────────────────────────────
        left = tk.Frame(bar, bg=BG_SIDEBAR)
        left.pack(side="left", fill="y", padx=26)
        # vertical centering
        tk.Frame(left, bg=BG_SIDEBAR).pack(expand=True)
        tk.Label(left, text="✦  THE VELORIA GRAND  ✦",
                 font=("Georgia", 22, "bold"), bg=BG_SIDEBAR, fg=GOLD).pack(anchor="w")
        tk.Label(left, text="Hotel & Resort  ·  Luxury Management System",
                 font=("Segoe UI", 9), bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(anchor="w")
        tk.Frame(left, bg=BG_SIDEBAR).pack(expand=True)

        # ── Middle divider ───────────────────────────────────────────────────────
        tk.Frame(bar, bg=GOLD_DARK, width=1).pack(side="right", fill="y", pady=10)

        # ── Right: Live Clock ────────────────────────────────────────────────────
        right = tk.Frame(bar, bg=BG_SIDEBAR)
        right.pack(side="right", fill="y", padx=(20, 26))
        tk.Frame(right, bg=BG_SIDEBAR).pack(expand=True)

        # Time (largest) — Georgia for a luxury serif feel
        self._lbl_time = tk.Label(right, text="",
                                   font=("Georgia", 28, "bold"),
                                   bg=BG_SIDEBAR, fg=GOLD)
        self._lbl_time.pack(anchor="e")

        # Date + Day in one row
        date_row = tk.Frame(right, bg=BG_SIDEBAR)
        date_row.pack(anchor="e")
        self._lbl_date = tk.Label(date_row, text="",
                                   font=("Segoe UI", 11, "bold"),
                                   bg=BG_SIDEBAR, fg=CREAM)
        self._lbl_date.pack(side="left")
        tk.Label(date_row, text="  |  ", font=("Segoe UI", 11),
                 bg=BG_SIDEBAR, fg=GOLD_DARK).pack(side="left")
        self._lbl_day = tk.Label(date_row, text="",
                                  font=("Segoe UI", 11, "bold italic"),
                                  bg=BG_SIDEBAR, fg=GOLD_LIGHT)
        self._lbl_day.pack(side="left")
        tk.Frame(right, bg=BG_SIDEBAR).pack(expand=True)

    def _update_clock(self):
        now = datetime.now()
        self._lbl_day.config(text=now.strftime("%A"))
        self._lbl_date.config(text=now.strftime("%d %B %Y"))
        self._lbl_time.config(text=now.strftime("%I:%M:%S %p"))
        self.after(1000, self._update_clock)

    def _build_sidebar(self, parent):
        self._sidebar = tk.Frame(parent, bg=BG_SIDEBAR, width=SIDEBAR_WIDTH)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        tk.Frame(self._sidebar, bg=BG_SIDEBAR, height=16).pack()

        self._nav_buttons = {}
        for _, icon, label, key in NAV_ITEMS:
            btn_data = self._make_nav_btn(self._sidebar, icon, label, key)
            self._nav_buttons[key] = btn_data

        # ── Bottom: About button + version ──────────────────────────────────────
        # push to bottom
        spacer = tk.Frame(self._sidebar, bg=BG_SIDEBAR)
        spacer.pack(fill="both", expand=True)

        tk.Frame(self._sidebar, bg=GOLD_DARK, height=1).pack(fill="x", padx=12, pady=(0, 4))

        # Images button
        images_btn = tk.Button(
            self._sidebar,
            text="🖼️   Hotel Images",
            font=("Segoe UI", 9, "bold"),
            bg=GOLD_SUBTLE, fg=GOLD,
            activebackground=BORDER_GOLD, activeforeground=GOLD_LIGHT,
            relief="flat", cursor="hand2", anchor="w",
            padx=14, pady=9,
            command=self._show_images)
        images_btn.pack(fill="x", padx=8, pady=(0, 2))

        # About button
        about_btn = tk.Button(
            self._sidebar,
            text="ℹ️   About This Project",
            font=("Segoe UI", 9, "bold"),
            bg=GOLD_SUBTLE, fg=GOLD,
            activebackground=BORDER_GOLD, activeforeground=GOLD_LIGHT,
            relief="flat", cursor="hand2", anchor="w",
            padx=14, pady=9,
            command=self._show_about)
        about_btn.pack(fill="x", padx=8, pady=(0, 4))

        tk.Label(self._sidebar, text="v1.0 · The Veloria Grand",
                 font=FONT_SMALL, bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(
                 padx=16, pady=(0, 10), anchor="w")

    def _make_nav_btn(self, parent, icon, label, key):
        container = tk.Frame(parent, bg=BG_SIDEBAR, height=52, cursor="hand2")
        container.pack(fill="x", padx=8, pady=1)
        container.pack_propagate(False)

        # Active indicator bar (left side)
        indicator = tk.Frame(container, bg=BG_SIDEBAR, width=4)
        indicator.pack(side="left", fill="y")

        inner = tk.Frame(container, bg=BG_SIDEBAR)
        inner.pack(side="left", fill="both", expand=True, padx=(10, 0))

        lbl_icon = tk.Label(inner, text=icon, font=("Segoe UI", 16),
                             bg=BG_SIDEBAR, fg=TEXT_MUTED)
        lbl_icon.pack(side="left", pady=4)

        lbl_text = tk.Label(inner, text=label, font=("Segoe UI", 11, "bold"),
                             bg=BG_SIDEBAR, fg=TEXT_MUTED)
        lbl_text.pack(side="left", padx=10)

        data = {
            "container": container, "indicator": indicator,
            "inner": inner, "icon": lbl_icon, "text": lbl_text,
            "active": False
        }

        def on_enter(e, d=data):
            if not d["active"]:
                for w in [d["container"], d["inner"]]:
                    w.config(bg="#0F1025")
                d["icon"].config(bg="#0F1025", fg=CREAM)
                d["text"].config(bg="#0F1025", fg=CREAM)

        def on_leave(e, d=data):
            if not d["active"]:
                for w in [d["container"], d["inner"]]:
                    w.config(bg=BG_SIDEBAR)
                d["icon"].config(bg=BG_SIDEBAR, fg=TEXT_MUTED)
                d["text"].config(bg=BG_SIDEBAR, fg=TEXT_MUTED)

        def on_click(e, k=key):
            self.show_frame(k)

        for widget in [container, inner, lbl_icon, lbl_text]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)

        return data

    def _set_active_nav(self, key):
        active_bg  = "#0F1028"
        for k, d in self._nav_buttons.items():
            if k == key:
                d["active"] = True
                d["indicator"].config(bg=GOLD)
                for w in [d["container"], d["inner"]]:
                    w.config(bg=active_bg)
                d["icon"].config(bg=active_bg, fg=GOLD)
                d["text"].config(bg=active_bg, fg=GOLD)
            else:
                d["active"] = False
                d["indicator"].config(bg=BG_SIDEBAR)
                for w in [d["container"], d["inner"]]:
                    w.config(bg=BG_SIDEBAR)
                d["icon"].config(bg=BG_SIDEBAR, fg=TEXT_MUTED)
                d["text"].config(bg=BG_SIDEBAR, fg=TEXT_MUTED)

    # ─── Frames ──────────────────────────────────────────────────────────────────
    def _init_frames(self):
        self._frames = {
            "dashboard":    DashboardFrame(self._content, self.db),
            "rooms":        RoomsFrame(self._content, self.db),
            "show_rooms":   ShowRoomsFrame(self._content, self.db),
            "clients":      ClientsFrame(self._content, self.db),
            "reservations": ReservationsFrame(self._content, self.db),
            "payments":     PaymentsFrame(self._content, self.db),
            "analytics":    AnalyticsFrame(self._content, self.db),
        }

    def show_frame(self, key):
        for frame in self._frames.values():
            frame.pack_forget()
        frame = self._frames.get(key)
        if frame:
            frame.pack(fill="both", expand=True)
            if hasattr(frame, "refresh"):
                try:
                    frame.refresh()
                except Exception:
                    pass
        self._set_active_nav(key)

    # ─── Window Utilities ─────────────────────────────────────────────────────────
    def _show_about(self):

        """Show the luxurious About This Project dialog."""
        win = tk.Toplevel(self)
        win.title("About — Hotel Management System")
        win.configure(bg=BG_MAIN)
        win.resizable(False, False)
        win.grab_set()   # modal

        W = 640
        win.geometry(f"{W}x720")
        # centre over parent
        self.update_idletasks()
        px = self.winfo_x() + (self.winfo_width()  - W) // 2
        py = self.winfo_y() + (self.winfo_height() - 720) // 2
        win.geometry(f"{W}x720+{px}+{py}")

        # ── Gold accent top bar ───────────────────────────────────────────────
        tk.Frame(win, bg=GOLD, height=4).pack(fill="x")

        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(win, bg=BG_SIDEBAR, pady=22)
        hdr.pack(fill="x")
        tk.Label(hdr, text="✦  THE VELORIA GRAND  ✦",
                 font=("Georgia", 18, "bold"),
                 bg=BG_SIDEBAR, fg=GOLD).pack()
        tk.Label(hdr, text="Hotel Management System",
                 font=("Georgia", 13, "bold"),
                 bg=BG_SIDEBAR, fg=CREAM).pack(pady=(4, 0))
        tk.Label(hdr, text="A University Academic Project",
                 font=("Segoe UI", 9), bg=BG_SIDEBAR, fg=TEXT_MUTED).pack()

        tk.Frame(win, bg=GOLD_DARK, height=1).pack(fill="x", padx=0)

        # ── Scrollable body ───────────────────────────────────────────────────
        container = tk.Frame(win, bg=BG_MAIN)
        container.pack(fill="both", expand=True)

        body_canvas = tk.Canvas(container, bg=BG_MAIN, highlightthickness=0)
        body_canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=body_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        body_canvas.configure(yscrollcommand=scrollbar.set)
        body_inner = tk.Frame(body_canvas, bg=BG_MAIN)
        body_canvas.create_window((0, 0), window=body_inner, anchor="nw", width=W-16)
        body_inner.bind("<Configure>", lambda e: body_canvas.configure(scrollregion=body_canvas.bbox("all")))

        def _section(parent, title, icon):
            sf = tk.Frame(parent, bg=BG_CARD,
                          highlightbackground=GOLD_DARK, highlightthickness=1)
            sf.pack(fill="x", padx=24, pady=(14, 0))
            sh = tk.Frame(sf, bg=GOLD_SUBTLE, padx=16, pady=8)
            sh.pack(fill="x")
            tk.Label(sh, text=f"{icon}  {title}",
                     font=("Segoe UI", 10, "bold"),
                     bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")
            sb = tk.Frame(sf, bg=BG_CARD, padx=20, pady=12)
            sb.pack(fill="x")
            return sb

        def _row(parent, label, value, val_color=CREAM):
            r = tk.Frame(parent, bg=BG_CARD)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label, font=("Segoe UI", 9, "bold"),
                     bg=BG_CARD, fg=TEXT_MUTED, width=22, anchor="w").pack(side="left")
            tk.Label(r, text=value, font=("Segoe UI", 9),
                     bg=BG_CARD, fg=val_color, anchor="w").pack(side="left")

        # ── Academic Info ─────────────────────────────────────────────────────
        sb = _section(body_inner, "Academic Information", "🎓")
        _row(sb, "Project Title",    "Hotel Management System", GOLD)
        _row(sb, "Academic Program", "Bachelor of Computer Applications (BCA)")
        _row(sb, "Semester",         "5th Semester")
        _row(sb, "Project Guide",    "Prof. Neha Jaswani", GOLD_LIGHT)
        _row(sb, "Project Type",     "Desktop Application · Python & Tkinter")

        # ── Developers ───────────────────────────────────────────────────
        dev_section = _section(body_inner, "Developed By", "👨‍💻")

        # Program + Guide mini-banner
        prog_bar = tk.Frame(dev_section, bg="#1A1208",
                            highlightbackground=GOLD_DARK, highlightthickness=1)
        prog_bar.pack(fill="x", pady=(0, 14))
        prog_inner = tk.Frame(prog_bar, bg="#1A1208", padx=16, pady=8)
        prog_inner.pack(fill="x")
        tk.Label(prog_inner, text="🎓  BCA — 5th Semester",
                 font=("Segoe UI", 9, "bold"),
                 bg="#1A1208", fg=GOLD).pack(side="left")
        tk.Label(prog_inner,
                 text="  ·  Guide: Prof. Neha Jaswani  ·  Project: Hotel Management System",
                 font=("Segoe UI", 9),
                 bg="#1A1208", fg=GOLD_LIGHT).pack(side="left")


        developers = [
            ("Smit Topiya",    "92400527136", "ST"),
            ("Devesh Sharma",  "92400527131", "DS"),
            ("Kevin Vekariya", "92400527081", "KV"),
        ]

        for i, (name, enroll, initials) in enumerate(developers):
            # Outer card
            card = tk.Frame(dev_section, bg=BG_INPUT,
                            highlightbackground=GOLD_DARK, highlightthickness=1)
            card.pack(fill="x", pady=5)

            # Left gold accent strip
            tk.Frame(card, bg=GOLD_DARK, width=4).pack(side="left", fill="y")

            # Avatar circle (Canvas)
            av_canvas = tk.Canvas(card, width=54, height=54,
                                  bg=BG_INPUT, highlightthickness=0)
            av_canvas.pack(side="left", padx=(12, 0), pady=10)
            av_colors = [GOLD_DARK, "#1A4A7A", "#2A0A50"]
            av_fg     = [BG_MAIN,   CREAM,      CREAM]
            av_canvas.create_oval(2, 2, 52, 52,
                                  fill=av_colors[i], outline=GOLD, width=1)
            av_canvas.create_text(27, 27, text=initials,
                                  font=("Segoe UI", 13, "bold"),
                                  fill=av_fg[i])

            # Info block
            info = tk.Frame(card, bg=BG_INPUT)
            info.pack(side="left", fill="x", expand=True, padx=14, pady=10)

            # Name + badge row
            name_row = tk.Frame(info, bg=BG_INPUT)
            name_row.pack(fill="x")
            tk.Label(name_row, text=name,
                     font=("Segoe UI", 12, "bold"),
                     bg=BG_INPUT, fg=CREAM).pack(side="left")
            tk.Label(name_row, text=f"  Developer #{i+1}  ",
                     font=("Segoe UI", 7, "bold"),
                     bg=GOLD_DARK, fg=BG_MAIN,
                     padx=4, pady=2).pack(side="left", padx=(10, 0))

            # Program line
            tk.Label(info,
                     text="BCA  ·  5th Semester  ·  The Veloria Grand HMS",
                     font=("Segoe UI", 8),
                     bg=BG_INPUT, fg=TEXT_MUTED).pack(anchor="w", pady=(3, 0))

            # Enrollment badge row
            enr_row = tk.Frame(info, bg=BG_INPUT)
            enr_row.pack(anchor="w", pady=(5, 0))
            tk.Label(enr_row, text="Enrollment No.",
                     font=("Segoe UI", 8, "bold"),
                     bg=BG_INPUT, fg=TEXT_MUTED).pack(side="left")
            tk.Label(enr_row, text=f"  {enroll}  ",
                     font=("Consolas", 10, "bold"),
                     bg=GOLD_SUBTLE, fg=GOLD,
                     padx=6, pady=2).pack(side="left", padx=(6, 0))


        # ── Technologies Used ─────────────────────────────────────────────────
        tb = _section(body_inner, "Technologies Used", "⚙️")
        technologies = [
            ("Python 3.x",     "Core programming language"),
            ("Tkinter",        "GUI framework — native desktop UI"),
            ("SQLite3",        "Embedded relational database"),
            ("tkcalendar",     "Date-picker calendar widget"),
            ("Matplotlib",     "Analytics charts & data visualisation"),
            ("Pillow (PIL)",   "Image loading & processing"),
            ("fpdf2",          "PDF invoice generation"),
            ("NumPy",          "Grouped bar chart data computation"),
        ]
        for tech, desc in technologies:
            r = tk.Frame(tb, bg=BG_CARD)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"◆  {tech}",
                     font=("Segoe UI", 9, "bold"),
                     bg=BG_CARD, fg=GOLD_LIGHT, width=22, anchor="w").pack(side="left")
            tk.Label(r, text=desc,
                     font=("Segoe UI", 9),
                     bg=BG_CARD, fg=TEXT_MUTED, anchor="w").pack(side="left")

        # ── Features ──────────────────────────────────────────────────────────
        fb = _section(body_inner, "Key Features", "🌟")
        features = [
            "Room management — Add, update, remove & search rooms",
            "Client management — Profiles with ID proof validation",
            "Reservation system — Booking with add-ons & meal plans",
            "Payments & billing — PDF invoice generation",
            "Live analytics — Charts for revenue, bookings & rooms",
            "Hotel image gallery — Showcases hotel views & amenities",
            "Real-time clock — Live date, day & time in top bar",
        ]
        for feat in features:
            tk.Label(fb, text=f"  ✓  {feat}",
                     font=("Segoe UI", 9), bg=BG_CARD,
                     fg=CREAM, anchor="w").pack(fill="x", pady=1)

        tk.Frame(body_inner, bg=BG_MAIN, height=20).pack()  # bottom spacer

        # ── Close button ──────────────────────────────────────────────────────
        tk.Frame(win, bg=GOLD_DARK, height=1).pack(fill="x")
        close_bar = tk.Frame(win, bg=BG_SIDEBAR, pady=12)
        close_bar.pack(fill="x")
        tk.Label(close_bar,
                 text="© 2026-2027  The Veloria Grand · BCA Semester 5 Project",
                 font=("Segoe UI", 8), bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(side="left", padx=20)
        ttk.Button(close_bar, text="  Close  ",
                   command=win.destroy).pack(side="right", padx=16)

    # ─── Image Gallery Window ─────────────────────────────────────────────────────────────
    def _show_images(self):
        """Full-screen gallery — left button panel + right image display."""
        try:
            from PIL import Image, ImageTk
        except ImportError:
            messagebox.showerror("Missing Library",
                                 "Pillow is required.\nRun: pip install Pillow")
            return

        img_dir = os.path.join(BASE_DIR, "Images")

        # ── Exact sequence requested by user ─────────────────────────────────────
        CATALOGUE = [
            ("DAY.png",                "☀️   Day View"),
            ("NIGHT.png",              "🌙  Night View"),
            ("RECEPTION.png",          "🏛   Reception Area"),
            ("POOL.png",               "🏊  Pool View"),
            ("STANDARD.png",           "🛏   Standard Room"),
            ("SUPERIOR.png",           "🛏   Superior Room"),
            ("DELUXE.png",             "🛏   Deluxe Room"),
            ("JUNIOR SUITE.png",       "🏨  Junior Suite"),
            ("DELUXE SUITE.png",       "🏨  Deluxe Suite"),
            ("GRAND SUITE.png",        "🏨  Grand Suite"),
            ("PRESIDENTIAL SUITE.png", "👑  Presidential Suite"),
            ("PENTHOUSE SUITE.png",    "🏙   Penthouse Suite"),
            ("OCEAN VIEW.png",         "🌊  Ocean View Room"),
            ("GARDEN VILLA.png",       "🌿  Garden Villa"),
        ]

        # Keep only files that exist
        entries = [(fn, lbl) for fn, lbl in CATALOGUE
                   if os.path.isfile(os.path.join(img_dir, fn))]

        # Auto-add any other images in folder not already listed
        known = {fn for fn, _ in entries}
        for fn in sorted(os.listdir(img_dir)):
            if fn.lower().endswith((".png", ".jpg", ".jpeg")) and fn not in known:
                entries.append((fn, f"🖼️  {os.path.splitext(fn)[0]}"))

        if not entries:
            messagebox.showinfo("No Images",
                                "No images found in the Images/ folder.")
            return

        # ── Gallery Toplevel ──────────────────────────────────────────────────────
        gal = tk.Toplevel(self)
        gal.title("Hotel Image Gallery — The Veloria Grand")
        gal.configure(bg=BG_MAIN)
        gal.resizable(True, True)
        gal.grab_set()

        GW, GH = 1020, 680
        self.update_idletasks()
        gx = self.winfo_x() + (self.winfo_width()  - GW) // 2
        gy = self.winfo_y() + (self.winfo_height() - GH) // 2
        gal.geometry(f"{GW}x{GH}+{max(gx,0)}+{max(gy,0)}")
        gal.minsize(800, 520)

        _idx   = [0]
        _cache = {}

        # ── Gold accent strip ─────────────────────────────────────────────────────
        tk.Frame(gal, bg=GOLD, height=4).pack(fill="x")

        # ── Header ───────────────────────────────────────────────────────────────
        top_bar = tk.Frame(gal, bg=BG_SIDEBAR, pady=10)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="🖼️   The Veloria Grand — Hotel Gallery",
                 font=("Georgia", 13, "bold"),
                 bg=BG_SIDEBAR, fg=GOLD).pack(side="left", padx=20)
        counter_lbl = tk.Label(top_bar, text="",
                               font=("Segoe UI", 9, "bold"),
                               bg=BG_SIDEBAR, fg=TEXT_MUTED)
        counter_lbl.pack(side="right", padx=20)
        tk.Frame(gal, bg=GOLD_DARK, height=1).pack(fill="x")

        # ── Body (left panel + right image) ──────────────────────────────────────
        body = tk.Frame(gal, bg=BG_MAIN)
        body.pack(fill="both", expand=True)

        # ─── LEFT: scrollable named-button column ────────────────────────────────
        left_wrap = tk.Frame(body, bg=BG_SIDEBAR, width=220)
        left_wrap.pack(side="left", fill="y")
        left_wrap.pack_propagate(False)

        # Column header
        col_hdr = tk.Frame(left_wrap, bg=GOLD_SUBTLE, pady=9, padx=14)
        col_hdr.pack(fill="x")
        tk.Label(col_hdr, text="📷  SELECT VIEW",
                 font=("Segoe UI", 8, "bold"),
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")
        tk.Frame(left_wrap, bg=GOLD_DARK, height=1).pack(fill="x")

        # Inner scrollable canvas for buttons
        btn_canvas = tk.Canvas(left_wrap, bg=BG_SIDEBAR,
                               highlightthickness=0)
        btn_vsb = tk.Scrollbar(left_wrap, orient="vertical",
                               command=btn_canvas.yview,
                               bg=BG_SIDEBAR, troughcolor=BG_MAIN, width=6)
        btn_canvas.configure(yscrollcommand=btn_vsb.set)
        btn_vsb.pack(side="right", fill="y")
        btn_canvas.pack(side="left", fill="both", expand=True)

        btn_inner = tk.Frame(btn_canvas, bg=BG_SIDEBAR)
        btn_canvas.create_window((0, 0), window=btn_inner,
                                 anchor="nw", width=208)
        btn_inner.bind("<Configure>",
            lambda e: btn_canvas.configure(
                scrollregion=btn_canvas.bbox("all")))

        # ─── RIGHT: caption + main image display ─────────────────────────────────
        right_col = tk.Frame(body, bg=BG_MAIN)
        right_col.pack(side="left", fill="both", expand=True)

        cap_bar = tk.Frame(right_col, bg=BG_CARD, pady=9, padx=16)
        cap_bar.pack(fill="x")
        cap_lbl = tk.Label(cap_bar, text="",
                           font=("Georgia", 12, "bold"),
                           bg=BG_CARD, fg=GOLD)
        cap_lbl.pack(anchor="w")

        img_canvas = tk.Canvas(right_col, bg="#000000",
                               highlightthickness=1,
                               highlightbackground=GOLD_DARK)
        img_canvas.pack(fill="both", expand=True, padx=8, pady=(4, 4))

        # ─── Bottom nav bar ───────────────────────────────────────────────────────
        tk.Frame(gal, bg=GOLD_DARK, height=1).pack(fill="x")
        nav_bar = tk.Frame(gal, bg=BG_SIDEBAR, pady=8)
        nav_bar.pack(fill="x")

        _nav_btns = []   # (indicator, container, inner, lbl_icon, lbl_text, sep)

        # ── Core show function ───────────────────────────────────────────────────
        def _show(idx):
            _idx[0] = idx % len(entries)
            fn, lbl = entries[_idx[0]]
            path    = os.path.join(img_dir, fn)

            gal.update_idletasks()
            cw = max(img_canvas.winfo_width(),  580)
            ch = max(img_canvas.winfo_height(), 360)

            if path not in _cache:
                _cache[path] = Image.open(path)
            raw = _cache[path].copy()
            raw.thumbnail((cw, ch), Image.LANCZOS)
            ph = ImageTk.PhotoImage(raw)
            img_canvas._photo = ph
            img_canvas.delete("all")
            img_canvas.create_image(cw // 2, ch // 2, image=ph, anchor="center")

            cap_lbl.config(text=lbl)
            counter_lbl.config(text=f"{_idx[0]+1}  /  {len(entries)}")

            # Highlight active left-panel nav button
            for j2, (ind, cont, inn, li, lt, sp) in enumerate(_nav_btns):
                active = (j2 == _idx[0])
                ind.config(bg=GOLD if active else BG_SIDEBAR)
                for w in (cont, inn, li, lt):
                    w.config(bg=GOLD_SUBTLE if active else BG_SIDEBAR)
                li.config(fg=GOLD      if active else TEXT_MUTED)
                lt.config(fg=GOLD      if active else TEXT_MUTED,
                          font=("Segoe UI", 9, "bold") if active
                               else ("Segoe UI", 9))
                sp.config(bg=GOLD_DARK if active else BORDER)

            # Auto-scroll active button into view
            btn_canvas.update_idletasks()
            total_h = max(btn_inner.winfo_height(), 1)
            item_h  = total_h / max(len(entries), 1)
            frac    = (_idx[0] * item_h) / total_h
            btn_canvas.yview_moveto(max(0.0, frac - 0.1))

        def _prev(): _show(_idx[0] - 1)
        def _next(): _show(_idx[0] + 1)

        gal.bind("<Left>",       lambda e: _prev())
        gal.bind("<Right>",      lambda e: _next())
        gal.bind("<Up>",         lambda e: _prev())
        gal.bind("<Down>",       lambda e: _next())
        gal.bind("<MouseWheel>",
                 lambda e: _show(_idx[0] - 1 if e.delta > 0 else _idx[0] + 1))

        # ── Build main-style nav buttons (like sidebar) ───────────────────────────
        ICONS = ["☀️","🌙","🏛","🏊","🛏","🛏","🛏","🏨","🏨","🏨","👑","🏙","🌊","🌿"]

        for j, (fn, lbl) in enumerate(entries):
            icon_char = ICONS[j] if j < len(ICONS) else "🖼️"
            # Strip the emoji prefix from lbl since we use a dedicated icon label
            display = lbl.strip().lstrip("☀️🌙🏛🏊🛏🏨👑🏙🌊🌿🖼️ ")

            container = tk.Frame(btn_inner, bg=BG_SIDEBAR,
                                 height=46, cursor="hand2")
            container.pack(fill="x", padx=4, pady=1)
            container.pack_propagate(False)

            # Left gold indicator bar (4 px wide)
            indicator = tk.Frame(container, bg=BG_SIDEBAR, width=4)
            indicator.pack(side="left", fill="y")

            inner = tk.Frame(container, bg=BG_SIDEBAR)
            inner.pack(side="left", fill="both", expand=True, padx=(6, 4))

            lbl_icon = tk.Label(inner, text=icon_char,
                                font=("Segoe UI Emoji", 13),
                                bg=BG_SIDEBAR, fg=TEXT_MUTED)
            lbl_icon.pack(side="left", pady=4)

            lbl_text = tk.Label(inner, text=display,
                                font=("Segoe UI", 9, "bold"),
                                bg=BG_SIDEBAR, fg=TEXT_MUTED,
                                anchor="w")
            lbl_text.pack(side="left", padx=(6, 0), fill="x", expand=True)

            sep = tk.Frame(btn_inner, bg=BORDER, height=1)
            sep.pack(fill="x", padx=4)

            # Click binding on all sub-widgets
            for widget in (container, inner, lbl_icon, lbl_text):
                widget.bind("<Button-1>", lambda e, j=j: _show(j))
                widget.bind("<Enter>", lambda e, c=container, ii=inner,
                            li=lbl_icon, lt=lbl_text:
                            [w.config(bg=GOLD_SUBTLE) for w in (c, ii, li, lt)]
                            if _idx[0] != entries.index(
                                (fn, lbl)) else None)
                widget.bind("<Leave>", lambda e, j2=j, c=container,
                            ii=inner, li=lbl_icon, lt=lbl_text:
                            [w.config(bg=GOLD_SUBTLE if _idx[0]==j2
                                      else BG_SIDEBAR)
                             for w in (c, ii, li, lt)])

            _nav_btns.append((indicator, container, inner, lbl_icon, lbl_text, sep))


        # ── Bottom nav buttons ────────────────────────────────────────────────────
        tk.Button(nav_bar, text="◄   PREV",
                  font=("Segoe UI", 9, "bold"),
                  bg=GOLD_SUBTLE, fg=GOLD,
                  activebackground=GOLD_DARK, activeforeground=CREAM,
                  relief="flat", cursor="hand2", padx=18, pady=6,
                  command=_prev).pack(side="left", padx=18)

        tk.Label(nav_bar, text="← ↑  /  → ↓  or scroll to navigate",
                 font=("Segoe UI", 8),
                 bg=BG_SIDEBAR, fg=TEXT_MUTED).pack(side="left", expand=True)

        tk.Button(nav_bar, text="NEXT   ►",
                  font=("Segoe UI", 9, "bold"),
                  bg=GOLD_SUBTLE, fg=GOLD,
                  activebackground=GOLD_DARK, activeforeground=CREAM,
                  relief="flat", cursor="hand2", padx=18, pady=6,
                  command=_next).pack(side="right", padx=18)

        ttk.Button(nav_bar, text=" Close ",
                   command=gal.destroy).pack(side="right", padx=6)

        # Show first image after window renders
        gal.after(150, lambda: _show(0))


    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.winfo_width()
        h  = self.winfo_height()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def on_close(self):
        if messagebox.askokcancel("Quit",
                                   "Close The Veloria Grand Management System?"):
            try:
                self.db.close()
            except Exception:
                pass
            self.destroy()

    def run(self):
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.mainloop()


# ─── Entry Point ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Ensure Images and Invoices folders exist
    for folder in ("Images", "Invoices"):
        os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)

    app = HotelApp()
    app.run()
