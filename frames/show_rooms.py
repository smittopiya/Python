
# frames/show_rooms.py -- Room Gallery | 3 Tabs | Live Auto-Refresh
import tkinter as tk
from tkinter import ttk
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import (
    BG_MAIN, BG_CARD, BG_SIDEBAR, BG_INPUT,
    GOLD, GOLD_DARK, GOLD_LIGHT, GOLD_SUBTLE, GOLD_BORDER,
    CREAM, TEXT_LIGHT, TEXT_MUTED, BORDER, BORDER_GOLD,
    SUCCESS, WARNING, DANGER, INFO,
    FONT_HEADING, FONT_SUBHEAD, FONT_LABEL, FONT_BODY, FONT_SMALL,
)
from utils import get_room_image

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Card dimensions ────────────────────────────────────────────────────────────
CARD_W     = 270
IMG_W      = 270
IMG_H      = 160
CARD_PAD   = 16
REFRESH_MS = 5000

# ── Colour palette for cards ───────────────────────────────────────────────────
CARD_BG       = "#16183A"   # slightly lighter than BG_CARD for visibility
CARD_HDR      = "#1E2050"   # card header strip
INFO_STRIP_BG = "#1C1E48"   # stats row background
GUEST_BG      = "#1A2E1A"   # green-tinted background for guest info (available)
BOOKED_BG     = "#2E1A1A"   # red-tinted for booked guest info


def _to_dict(row):
    try:
        return dict(row)
    except Exception:
        return {k: row[k] for k in row.keys()}


class ShowRoomsFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db             = db
        self._photo_refs    = []
        self._active_tab    = tk.StringVar(value="all")
        self._last_hash     = None
        self._is_visible    = False
        self._current_rooms = []
        self._window_id     = None
        self._build_ui()
        self._schedule_next()

    def pack(self, **kw):
        super().pack(**kw)
        self._is_visible = True
        self._last_hash  = None
        self._do_refresh()

    def pack_forget(self):
        super().pack_forget()
        self._is_visible = False

    # ── UI ─────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=BG_MAIN, padx=30, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ROOM GALLERY", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hdr, text="Show Rooms", font=FONT_HEADING,
                 bg=BG_MAIN, fg=GOLD).pack(anchor="w")
        tk.Frame(self, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # Tab bar
        tab_bar = tk.Frame(self, bg="#0D0E20", pady=10)
        tab_bar.pack(fill="x", padx=30, pady=(10, 0))

        self._tab_btns = {}
        tab_defs = [
            ("all",       "🏨  All Rooms",       "#1A1B3A", GOLD),
            ("available", "✅  Available Rooms",  "#1A1B3A", GOLD),
            ("booked",    "📅  Booked Today",     "#1A1B3A", GOLD),
        ]
        for key, label, nbg, nfg in tab_defs:
            btn = tk.Button(tab_bar, text=label,
                            font=("Segoe UI", 10, "bold"),
                            bg=nbg, fg=TEXT_MUTED,
                            activebackground=GOLD_DARK, activeforeground=CREAM,
                            relief="flat", cursor="hand2", padx=20, pady=9,
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side="left", padx=5)
            self._tab_btns[key] = btn

        # Live dot
        live_f = tk.Frame(tab_bar, bg="#0D0E20")
        live_f.pack(side="right", padx=8)
        self._live_dot = tk.Label(live_f, text="●", font=("Segoe UI", 10),
                                  bg="#0D0E20", fg=SUCCESS)
        self._live_dot.pack(side="left")
        tk.Label(live_f, text=" LIVE", font=("Segoe UI", 7, "bold"),
                 bg="#0D0E20", fg=SUCCESS).pack(side="left")
        self._updated_lbl = tk.Label(live_f, text="",
                                     font=("Segoe UI", 7),
                                     bg="#0D0E20", fg=TEXT_MUTED)
        self._updated_lbl.pack(side="left", padx=(6, 0))

        self._count_lbl = tk.Label(tab_bar, text="",
                                   font=("Segoe UI", 9, "bold"),
                                   bg="#0D0E20", fg=GOLD_LIGHT)
        self._count_lbl.pack(side="right", padx=12)

        # ── Canvas (correct tkinter scrollable pattern) ────────────────────────
        scroll_area = tk.Frame(self, bg=BG_MAIN)
        scroll_area.pack(fill="both", expand=True, padx=30, pady=12)

        self._canvas = tk.Canvas(scroll_area, bg=BG_MAIN, highlightthickness=0)
        vsb = ttk.Scrollbar(scroll_area, orient="vertical",
                            command=self._canvas.yview)
        self._gallery = tk.Frame(self._canvas, bg=BG_MAIN)

        self._gallery.bind(
            "<Configure>",
            lambda e: self._canvas.configure(
                scrollregion=self._canvas.bbox("all")))

        self._window_id = self._canvas.create_window(
            (0, 0), window=self._gallery, anchor="nw")

        self._canvas.configure(yscrollcommand=vsb.set)
        self._canvas.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Stretch inner frame width to match canvas
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._canvas.bind_all("<MouseWheel>",
            lambda e: self._canvas.yview_scroll(
                -1 * (e.delta // 120), "units"))

        self._switch_tab("all")

    def _on_canvas_resize(self, event):
        if self._window_id:
            self._canvas.itemconfig(self._window_id, width=event.width)
        if self._current_rooms:
            self._render(self._current_rooms)

    # ── Data fetching ──────────────────────────────────────────────────────────
    def _fetch_rooms(self, tab):
        base = {_to_dict(r)["room_id"]: _to_dict(r)
                for r in (self.db.get_all_rooms() or [])}

        if tab == "all":
            rows = self.db.get_all_rooms_with_today_status() or []
            result = []
            for r in rows:
                d = _to_dict(r)
                b = base.get(d.get("room_id"), {})
                d["photo_path"]     = b.get("photo_path", "")
                d["extra_per_head"] = d.get("extra_per_head") or b.get("extra_per_head", 0)
                d["status"]         = d.get("today_status", "Available Today")
                result.append(d)
            return result

        elif tab == "available":
            rows = self.db.get_rooms_available_today() or []
            result = []
            for r in rows:
                d = _to_dict(r)
                d["status"] = "Available Today"
                result.append(d)
            return result

        else:  # booked
            rows = self.db.get_rooms_booked_today() or []
            result = []
            for r in rows:
                d = _to_dict(r)
                b = base.get(d.get("room_id"), {})
                d["photo_path"]     = b.get("photo_path", "")
                d["floor"]          = b.get("floor", "—")
                d["extra_per_head"] = b.get("extra_per_head", 0)
                d["description"]    = b.get("description", "")
                d["status"]         = "Booked Today"
                result.append(d)
            return result

    # ── Live refresh ───────────────────────────────────────────────────────────
    def _schedule_next(self):
        try:
            self.after(REFRESH_MS, self._tick)
        except Exception:
            pass

    def _tick(self):
        if self._is_visible:
            self._do_refresh()
        self._schedule_next()

    def _do_refresh(self):
        tab = self._active_tab.get()
        try:
            rooms    = self._fetch_rooms(tab)
            new_hash = hash(str(rooms))
            if new_hash != self._last_hash:
                self._last_hash     = new_hash
                self._current_rooms = rooms
                self._render(rooms)
            self._blink_dot()
            self._updated_lbl.config(
                text=f"  {datetime.now().strftime('%I:%M:%S %p')}")
        except Exception:
            pass

    def _blink_dot(self):
        self._live_dot.config(fg=GOLD_LIGHT)
        try:
            self.after(300, lambda: self._live_dot.config(fg=SUCCESS))
        except Exception:
            pass

    # ── Tab switch ─────────────────────────────────────────────────────────────
    def _switch_tab(self, key):
        self._active_tab.set(key)
        self._last_hash = None
        for k, btn in self._tab_btns.items():
            if k == key:
                btn.config(bg=GOLD, fg="#0B0C1A")
            else:
                btn.config(bg="#1A1B3A", fg=TEXT_MUTED)
        self._do_refresh()

    # ── Render grid ────────────────────────────────────────────────────────────
    def _render(self, rooms):
        for w in self._gallery.winfo_children():
            w.destroy()
        self._photo_refs.clear()

        tab   = self._active_tab.get()
        count = len(rooms)
        labels = {
            "all":       f"{count} Room{'s' if count!=1 else ''}",
            "available": f"{count} Available Today",
            "booked":    f"{count} Booked Today",
        }
        self._count_lbl.config(text=labels[tab])

        if not rooms:
            self._empty_state(tab)
            return

        try:
            cw   = self._canvas.winfo_width() or 900
            cols = max(1, (cw - 20) // (CARD_W + CARD_PAD))
        except Exception:
            cols = 3

        for idx, room in enumerate(rooms):
            card = self._make_card(room, tab)
            card.grid(in_=self._gallery,
                      row=idx // cols, column=idx % cols,
                      padx=CARD_PAD // 2, pady=CARD_PAD // 2,
                      sticky="nsew")

        for c in range(cols):
            self._gallery.columnconfigure(c, weight=1)

    def _empty_state(self, tab):
        msgs = {
            "all":       ("🏨", "No rooms in the database.",     "Add rooms from the Rooms section."),
            "available": ("✅", "No rooms available today.",      "All rooms are booked or under maintenance."),
            "booked":    ("📅", "No rooms are booked today.",     "No active reservations for today."),
        }
        icon, title, sub = msgs[tab]
        box = tk.Frame(self._gallery, bg=BG_MAIN)
        box.grid(row=0, column=0, pady=80, padx=40)
        tk.Label(box, text=icon,  font=("Segoe UI", 40), bg=BG_MAIN, fg=GOLD_DARK).pack()
        tk.Label(box, text=title, font=FONT_SUBHEAD,     bg=BG_MAIN, fg=CREAM).pack(pady=(8,2))
        tk.Label(box, text=sub,   font=FONT_SMALL,       bg=BG_MAIN, fg=TEXT_MUTED).pack()

    # ── Room card ──────────────────────────────────────────────────────────────
    def _make_card(self, room, tab):
        status = room.get("status", "Available Today")
        is_booked = "Occupied" in status or "Booked" in status

        # Status colours
        if is_booked:
            pill_bg = "#C0392B"
            pill_fg = "#FFFFFF"
            top_bar = "#8B1A1A"
        else:
            pill_bg = "#1E8449"
            pill_fg = "#FFFFFF"
            top_bar = "#145A32"

        card = tk.Frame(self._gallery, bg=CARD_BG,
                        highlightbackground=BORDER_GOLD,
                        highlightthickness=1)

        # Coloured top accent bar
        tk.Frame(card, bg=top_bar, height=4).pack(fill="x")

        # Photo
        cv = tk.Canvas(card, width=IMG_W, height=IMG_H,
                       bg="#080910", highlightthickness=0)
        cv.pack(fill="x")
        self._load_photo(cv, room.get("photo_path", ""))

        # ── Room ID bar ────────────────────────────────────────────────────────
        id_bar = tk.Frame(card, bg=CARD_HDR, pady=6)
        id_bar.pack(fill="x")
        tk.Label(id_bar, text=f"  🔑  Room  {room.get('room_id','—')}",
                 font=("Segoe UI", 10, "bold"),
                 bg=CARD_HDR, fg="#E8D5A3").pack(side="left")
        pill = tk.Frame(id_bar, bg=pill_bg, padx=8, pady=3)
        pill.pack(side="right", padx=8)
        tk.Label(pill, text=status, font=("Segoe UI", 7, "bold"),
                 bg=pill_bg, fg=pill_fg).pack()

        # ── Room type ──────────────────────────────────────────────────────────
        tk.Label(card, text=room.get("room_type", "—"),
                 font=("Segoe UI", 12, "bold"), bg=CARD_BG, fg=GOLD,
                 wraplength=CARD_W - 24, justify="left"
                 ).pack(anchor="w", padx=14, pady=(10, 2))

        # ── Price ──────────────────────────────────────────────────────────────
        pr = tk.Frame(card, bg=CARD_BG)
        pr.pack(fill="x", padx=14, pady=(0, 6))
        try:
            p = f"\u20b9{float(room.get('price', 0)):,.0f}"
        except Exception:
            p = "N/A"
        tk.Label(pr, text=p, font=("Segoe UI", 16, "bold"),
                 bg=CARD_BG, fg="#F0D080").pack(side="left")
        tk.Label(pr, text=" / night", font=("Segoe UI", 9),
                 bg=CARD_BG, fg="#7A7A9A").pack(side="left", pady=6)

        # ── Stats row (distinct background) ───────────────────────────────────
        info_bg = "#1A1C42"
        info = tk.Frame(card, bg=info_bg, pady=8)
        info.pack(fill="x")
        try:
            ex = f"\u20b9{float(room.get('extra_per_head', 0)):,.0f}/extra"
        except Exception:
            ex = "—"
        for ico, val, sub in [
            ("👥", str(room.get('capacity','—')), "Capacity"),
            ("🏢", f"Floor {room.get('floor','—')}", "Level"),
            ("💰", ex, "Extra/Head"),
        ]:
            col = tk.Frame(info, bg=info_bg)
            col.pack(side="left", expand=True)
            tk.Label(col, text=ico, font=("Segoe UI", 13),
                     bg=info_bg).pack()
            tk.Label(col, text=val, font=("Segoe UI", 8, "bold"),
                     bg=info_bg, fg="#D8D8F8").pack()
            tk.Label(col, text=sub, font=("Segoe UI", 7),
                     bg=info_bg, fg="#5A5A8A").pack()

        # ── Guest strip (occupied / booked) ───────────────────────────────────
        guest   = room.get("guest_name") or room.get("client_name", "")
        res_id  = room.get("res_id", "") or room.get("reservation_id", "")
        chk_in  = room.get("check_in",  "")
        chk_out = room.get("check_out", "")
        adults  = room.get("adults",    "")
        children= room.get("children",  "")
        contact = room.get("contact",   "")
        total   = room.get("total_amount", "")

        if guest and is_booked:
            gc = tk.Frame(card, bg="#1E1420", pady=6)
            gc.pack(fill="x")
            tk.Frame(gc, bg="#5A1A5A", height=1).pack(fill="x", pady=(0,4))

            def _row(ico, txt, bold=False, color="#D8B8D8"):
                r = tk.Frame(gc, bg="#1E1420")
                r.pack(fill="x", padx=12, pady=2)
                tk.Label(r, text=ico, font=("Segoe UI", 9),
                         bg="#1E1420", fg="#C8A8C8").pack(side="left", padx=(0,6))
                tk.Label(r, text=txt,
                         font=("Segoe UI", 8, "bold") if bold else ("Segoe UI", 8),
                         bg="#1E1420", fg=color).pack(side="left")

            _row("👤", guest, bold=True, color="#F0D0F0")
            if contact:
                _row("📞", contact, color="#D0B0D0")
            if chk_in:
                _row("📅", f"{chk_in}  →  {chk_out}", color="#D0B0D0")
            pax = []
            if adults:   pax.append(f"{adults} Adults")
            if children: pax.append(f"{children} Children")
            if pax:
                _row("👨‍👩‍👧", "  |  ".join(pax), color="#D0B0D0")
            if res_id:
                _row("🔖", f"Res ID: {res_id}", color="#B090B0")
            if total:
                try:
                    _row("💳", f"\u20b9{float(total):,.2f}", bold=True, color="#F0D0F0")
                except Exception:
                    pass
            tk.Frame(gc, bg="#5A1A5A", height=1).pack(fill="x", pady=(4,0))

        # ── Description ────────────────────────────────────────────────────────
        desc  = (room.get("description") or
                 "Premium room with world-class amenities.").strip()
        short = (desc[:68] + "...") if len(desc) > 68 else desc
        tk.Label(card, text=short, font=("Segoe UI", 8),
                 bg=CARD_BG, fg="#7878A8",
                 wraplength=CARD_W - 28, justify="left"
                 ).pack(anchor="w", padx=14, pady=(6, 12))

        return card

    # ── Photo ──────────────────────────────────────────────────────────────────
    def _load_photo(self, canvas, photo_path):
        if HAS_PIL and photo_path:
            full = get_room_image(photo_path)
            if full:
                try:
                    img = Image.open(full).resize((IMG_W, IMG_H), Image.LANCZOS)
                    ph  = ImageTk.PhotoImage(img)
                    self._photo_refs.append(ph)
                    canvas.create_image(0, 0, image=ph, anchor="nw")
                    return
                except Exception:
                    pass
        # Dark elegant placeholder
        canvas.create_rectangle(0, 0, IMG_W, IMG_H, fill="#080910", outline="")
        for x1,y1,x2,y2 in [
            (0,0,24,4),(0,0,4,24),(IMG_W-24,0,IMG_W,4),(IMG_W-4,0,IMG_W,24),
            (0,IMG_H-4,24,IMG_H),(0,IMG_H-24,4,IMG_H),
            (IMG_W-24,IMG_H-4,IMG_W,IMG_H),(IMG_W-4,IMG_H-24,IMG_W,IMG_H),
        ]:
            canvas.create_rectangle(x1,y1,x2,y2, fill=GOLD_DARK, outline="")
        canvas.create_text(IMG_W//2, IMG_H//2-12, text="✦  THE VELORIA GRAND  ✦",
                           font=("Georgia", 10, "bold"), fill=GOLD_DARK)
        canvas.create_text(IMG_W//2, IMG_H//2+10, text="No Photo Available",
                           font=("Segoe UI", 9), fill="#3A3A5A")

    def refresh(self):
        self._last_hash = None
        self._do_refresh()
