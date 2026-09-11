
# frames/reservations.py — Reservation System Frame
import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import (
    BG_MAIN, BG_SIDEBAR, BG_CARD, BG_INPUT, BG_ROW_ALT,
    GOLD, GOLD_LIGHT, GOLD_DARK, GOLD_SUBTLE, GOLD_BORDER,
    CREAM, TEXT_LIGHT, TEXT_MUTED,
    BORDER, BORDER_GOLD,
    SUCCESS, WARNING, DANGER, INFO,
    FONT_HEADING, FONT_SUBHEAD, FONT_LABEL, FONT_BODY, FONT_SMALL,
    make_scrollable,
)
from utils import fmt_currency, generate_res_id, days_between, get_room_image

try:
    from tkcalendar import DateEntry
    HAS_CALENDAR = True
except ImportError:
    HAS_CALENDAR = False

# ── Constants ─────────────────────────────────────────────────────────────────
MEAL_PLANS = {
    "No Meals":           0,
    "Breakfast Only":     650,
    "Half Board (B+D)":   1200,
    "Full Board (B+L+D)": 1800,
    "All Inclusive":      2800,
}

ADD_ONS = {
    "Private Pool Access":      2500,
    "Extra Bed":                1500,
    "Airport Transfer":         2000,
    "Spa Treatment":            3500,
    "Romantic Decoration":      5000,
    "Birthday Package":         3000,
    "Late Checkout (till 6PM)": 2000,
    "Early Check-in (8AM)":     1500,
}

# Add-ons that have a quantity spinner
QTY_ADDONS = {"Extra Bed", "Private Pool Access", "Airport Transfer", "Spa Treatment"}


# ── Widget helpers ─────────────────────────────────────────────────────────────
def _spinbox(parent, from_=1, to=20, command=None):
    return tk.Spinbox(
        parent, from_=from_, to=to, width=6, command=command,
        bg=BG_INPUT, fg=CREAM, buttonbackground=BG_SIDEBAR,
        activebackground=GOLD_DARK, insertbackground=GOLD,
        highlightthickness=1, highlightbackground=BORDER,
        highlightcolor=GOLD, relief="flat", font=FONT_BODY)


def _date_widget(parent, on_select=None):
    """Return a DateEntry (if tkcalendar installed) or a plain ttk.Entry."""
    if HAS_CALENDAR:
        w = DateEntry(
            parent, width=14, date_pattern="yyyy-mm-dd",
            background=BG_SIDEBAR, foreground=GOLD, bordercolor=GOLD_DARK,
            headersbackground=BG_CARD, headersforeground=GOLD,
            normalbackground=BG_CARD, normalforeground=CREAM,
            weekendbackground=BG_CARD, weekendforeground=GOLD_LIGHT,
            othermonthbackground=BG_MAIN, othermonthforeground=TEXT_MUTED,
            othermonthwebackground=BG_MAIN, othermonthweforeground=TEXT_MUTED,
            selectbackground=GOLD, selectforeground=BG_MAIN,
            disabledbackground=BG_INPUT, font=FONT_BODY)
        if on_select:
            w.bind("<<DateEntrySelected>>", lambda e: on_select())
    else:
        w = ttk.Entry(parent, width=15)
        w.insert(0, str(date.today()))
    return w


def _card(parent, title, icon="", bg_hdr=None):
    """Create a card with a coloured header and return the body frame."""
    if bg_hdr is None:
        bg_hdr = GOLD_SUBTLE
    outer = tk.Frame(parent, bg=BG_CARD,
                     highlightbackground=BORDER_GOLD, highlightthickness=1)
    outer.pack(fill="x", pady=(0, 8))
    tk.Frame(outer, bg=GOLD_DARK, height=2).pack(fill="x")
    hdr = tk.Frame(outer, bg=bg_hdr, pady=8, padx=16)
    hdr.pack(fill="x")
    tk.Label(hdr, text=f"{icon}  {title}" if icon else title,
             font=FONT_SUBHEAD, bg=bg_hdr, fg=GOLD).pack(anchor="w")
    body = tk.Frame(outer, bg=BG_CARD, padx=20, pady=12)
    body.pack(fill="x")
    return body


def _row(parent, label, width=20):
    """A label-aligned form row inside a card body."""
    r = tk.Frame(parent, bg=BG_CARD)
    r.pack(fill="x", pady=4)
    tk.Label(r, text=label, font=FONT_LABEL, bg=BG_CARD,
             fg=GOLD, width=width, anchor="w").pack(side="left")
    return r


# =============================================================================
class ReservationsFrame(tk.Frame):
    """Main Reservations page — two sub-tabs: New Reservation | All Reservations."""

    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db = db
        self._room_details = {}   # room_id -> Row  (used by New Reservation)
        self._addon_vars   = {}   # name -> (BooleanVar, IntVar, price)
        self._calc         = {}   # last bill calculation result
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Page heading
        hdr = tk.Frame(self, bg=BG_MAIN, padx=30, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="RESERVATIONS", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hdr, text="Reservations", font=FONT_HEADING,
                 bg=BG_MAIN, fg=GOLD).pack(anchor="w")
        tk.Frame(self, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # Sub-nav bar
        nav = tk.Frame(self, bg=BG_SIDEBAR, pady=10)
        nav.pack(fill="x", padx=30, pady=(10, 0))
        self._sub_btns = {}
        for label, key in [("📝  New Reservation", "new"),
                            ("📋  All Reservations", "all")]:
            btn = tk.Button(nav, text=label, font=FONT_LABEL,
                            bg=BG_CARD, fg=TEXT_MUTED, relief="flat",
                            activebackground=GOLD_DARK, activeforeground=CREAM,
                            cursor="hand2", padx=14, pady=8,
                            command=lambda k=key: self._show_sub(k))
            btn.pack(side="left", padx=4)
            self._sub_btns[key] = btn

        self._container = tk.Frame(self, bg=BG_MAIN)
        self._container.pack(fill="both", expand=True, padx=30, pady=10)

        self._subs = {
            "new": self._build_new_reservation(),
            "all": self._build_all_reservations(),
        }
        self._show_sub("new")

    def _show_sub(self, key):
        for frame in self._subs.values():
            frame.pack_forget()
        self._subs[key].pack(fill="both", expand=True)
        for k, btn in self._sub_btns.items():
            btn.config(bg=GOLD if k == key else BG_CARD,
                       fg=BG_MAIN if k == key else TEXT_MUTED)
        if key == "all":
            self._load_all_reservations()
        if key == "new":
            self._refresh_client_combo()
            self._refresh_room_combo()

    # ==========================================================================
    # ── NEW RESERVATION ────────────────────────────────────────────────────────
    # ==========================================================================
    def _build_new_reservation(self):
        outer     = tk.Frame(self._container, bg=BG_MAIN)
        left_col  = tk.Frame(outer, bg=BG_MAIN)
        right_col = tk.Frame(outer, bg=BG_MAIN)
        left_col.pack(side="left",  fill="both", expand=True, padx=(0, 8))
        right_col.pack(side="left", fill="both", expand=True)

        _, sf = make_scrollable(left_col, BG_MAIN)

        # ── Client card ────────────────────────────────────────────────────────
        body = _card(sf, "Guest & Room Selection", "👤")
        r = _row(body, "Select Client *")
        self._r_client_combo = ttk.Combobox(r, width=34, state="readonly")
        self._r_client_combo.pack(side="left", ipady=3)

        # ── Dates card ─────────────────────────────────────────────────────────
        body = _card(sf, "Stay Dates", "📅")
        ci_r = _row(body, "Check-In Date *")
        self._r_checkin = _date_widget(ci_r, self._on_date_change)
        self._r_checkin.pack(side="left", ipady=4)

        co_r = _row(body, "Check-Out Date *")
        self._r_checkout = _date_widget(co_r, self._on_date_change)
        self._r_checkout.pack(side="left", ipady=4)

        nb = tk.Frame(body, bg=BG_CARD)
        nb.pack(fill="x")
        tk.Label(nb, text="", width=20, bg=BG_CARD).pack(side="left")
        self._r_nights_badge = tk.Label(nb, text="📅  Select dates",
                                         font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED)
        self._r_nights_badge.pack(side="left")

        # ── Room card ──────────────────────────────────────────────────────────
        body = _card(sf, "Room Selection", "🛏")
        rr = _row(body, "Select Room *")
        self._r_room_combo = ttk.Combobox(rr, width=22, state="readonly")
        self._r_room_combo.pack(side="left", ipady=3)
        self._r_room_combo.bind("<<ComboboxSelected>>", lambda e: self._on_room_select())
        ttk.Button(rr, text="Check Availability",
                   command=self._check_availability).pack(side="left", padx=8)

        # Room info strip
        info_strip = tk.Frame(body, bg=BG_CARD)
        info_strip.pack(fill="x", pady=(0, 4))
        self._r_type_var  = tk.StringVar(value="—")
        self._r_price_var = tk.StringVar(value="—")
        self._r_cap_var   = tk.StringVar(value="—")
        self._r_eph_var   = tk.StringVar(value="—")
        for lbl, var in [("Type:", self._r_type_var), ("Price/Night:", self._r_price_var),
                          ("Capacity:", self._r_cap_var), ("Extra/Head:", self._r_eph_var)]:
            f = tk.Frame(info_strip, bg=BG_CARD)
            f.pack(side="left", padx=(0, 18))
            tk.Label(f, text=lbl, font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED).pack()
            tk.Label(f, textvariable=var, font=FONT_LABEL, bg=BG_CARD, fg=GOLD).pack()

        # Description / amenities
        desc_r = tk.Frame(body, bg=BG_CARD)
        desc_r.pack(fill="x", pady=(0, 4))
        tk.Label(desc_r, text="Description:", font=FONT_LABEL, bg=BG_CARD,
                 fg=GOLD, width=20, anchor="w").pack(side="left")
        self._r_desc_lbl = tk.Label(desc_r, text="—", font=FONT_SMALL,
                                     bg=BG_CARD, fg=TEXT_MUTED,
                                     anchor="w", wraplength=320, justify="left")
        self._r_desc_lbl.pack(side="left")

        # ── Guests card ────────────────────────────────────────────────────────
        body = _card(sf, "Guests", "👥")
        gr = _row(body, "Adults *")
        self._r_adults = _spinbox(gr, from_=1, to=20, command=self._recalculate)
        self._r_adults.delete(0, "end"); self._r_adults.insert(0, "1")
        self._r_adults.pack(side="left", ipady=4)
        tk.Label(gr, text="  Children:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD).pack(side="left", padx=(16, 0))
        self._r_children = _spinbox(gr, from_=0, to=20, command=self._recalculate)
        self._r_children.delete(0, "end"); self._r_children.insert(0, "0")
        self._r_children.pack(side="left", ipady=4)
        self._r_extra_warn = tk.Label(body, text="", font=FONT_SMALL,
                                       bg=BG_CARD, fg=WARNING)
        self._r_extra_warn.pack(anchor="w")

        # ── Add-Ons card ───────────────────────────────────────────────────────
        ao_outer = tk.Frame(sf, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
        ao_outer.pack(fill="x", pady=(0, 8))
        tk.Frame(ao_outer, bg=GOLD_DARK, height=2).pack(fill="x")
        ao_hdr = tk.Frame(ao_outer, bg=BG_SIDEBAR, pady=8, padx=16)
        ao_hdr.pack(fill="x")
        tk.Label(ao_hdr, text="🎁  Add-On Services", font=FONT_SUBHEAD,
                 bg=BG_SIDEBAR, fg=GOLD).pack(anchor="w")
        ao_body = tk.Frame(ao_outer, bg=BG_CARD, padx=20, pady=10)
        ao_body.pack(fill="x")

        self._addon_vars = {}
        for name, price in ADD_ONS.items():
            r = tk.Frame(ao_body, bg=BG_CARD)
            r.pack(fill="x", pady=2)
            var     = tk.BooleanVar()
            qty_var = tk.IntVar(value=1)
            tk.Checkbutton(r, text=name, variable=var, bg=BG_CARD, fg=CREAM,
                            selectcolor=BG_INPUT, activebackground=BG_CARD,
                            font=FONT_BODY, command=self._recalculate).pack(side="left")
            tk.Label(r, text=fmt_currency(price), font=FONT_LABEL,
                     bg=BG_CARD, fg=GOLD).pack(side="left", padx=8)
            if name in QTY_ADDONS:
                tk.Label(r, text="Qty:", font=FONT_SMALL,
                         bg=BG_CARD, fg=TEXT_MUTED).pack(side="left", padx=(16, 2))
                qs = tk.Spinbox(r, from_=1, to=10, width=4,
                                textvariable=qty_var, command=self._recalculate,
                                bg=BG_INPUT, fg=CREAM, buttonbackground=BG_SIDEBAR,
                                activebackground=GOLD_DARK, insertbackground=GOLD,
                                highlightthickness=1, highlightbackground=BORDER,
                                highlightcolor=GOLD, relief="flat", font=FONT_BODY)
                qs.pack(side="left")
            self._addon_vars[name] = (var, qty_var, price)

        # ── Meal plan card ─────────────────────────────────────────────────────
        body = _card(sf, "Meal Plan", "🍽️", bg_hdr=BG_SIDEBAR)
        mr = _row(body, "Select Meal Plan:")
        meal_labels = [f"{k}  ({fmt_currency(v)}/head)" for k, v in MEAL_PLANS.items()]
        self._r_meal_combo = ttk.Combobox(mr, values=meal_labels, width=32, state="readonly")
        self._r_meal_combo.current(0)
        self._r_meal_combo.pack(side="left", ipady=3)
        self._r_meal_combo.bind("<<ComboboxSelected>>", lambda e: self._recalculate())

        mq = _row(body, "Persons for Meals:")
        self._r_meal_qty = _spinbox(mq, from_=1, to=20, command=self._recalculate)
        self._r_meal_qty.delete(0, "end"); self._r_meal_qty.insert(0, "1")
        self._r_meal_qty.pack(side="left", ipady=4)

        # ── Notes card ─────────────────────────────────────────────────────────
        body = _card(sf, "Notes / Special Requests", "📝", bg_hdr=BG_SIDEBAR)
        self._r_notes = tk.Text(body, height=3, bg=BG_INPUT, fg=CREAM,
                                 insertbackground=GOLD, relief="flat",
                                 font=FONT_BODY, padx=6, pady=4)
        self._r_notes.pack(fill="x")

        # ── Action buttons ─────────────────────────────────────────────────────
        btn_bar = tk.Frame(sf, bg=BG_MAIN)
        btn_bar.pack(fill="x", pady=6)
        ttk.Button(btn_bar, text="Clear Form",
                   command=self._clear_reservation).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="💰  Recalculate",
                   command=self._recalculate).pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="✅  Confirm Reservation",
                   command=self._confirm_reservation).pack(side="left")

        # ── RIGHT: Photo preview + Bill summary ────────────────────────────────
        right_wrap = tk.Frame(right_col, bg=BG_MAIN)
        right_wrap.pack(fill="both", expand=True)

        # Photo card
        pc = tk.Frame(right_wrap, bg=BG_CARD,
                      highlightbackground=BORDER_GOLD, highlightthickness=1)
        pc.pack(fill="x", pady=(0, 10))
        ph = tk.Frame(pc, bg=GOLD_SUBTLE, pady=8, padx=16)
        ph.pack(fill="x")
        tk.Label(ph, text="🖼  Room Preview", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")
        self._photo_canvas = tk.Canvas(pc, bg="#050510", width=400, height=220,
                                        highlightthickness=0, bd=0)
        self._photo_canvas.pack(padx=12, pady=10)
        self._photo_canvas_img = None
        self._photo_canvas.create_text(200, 110, text="Select a room to see preview",
                                        fill=TEXT_MUTED, font=FONT_SMALL)

        # Bill card
        bc = tk.Frame(right_wrap, bg=BG_CARD,
                      highlightbackground=BORDER_GOLD, highlightthickness=1)
        bc.pack(fill="both", expand=True)
        bh = tk.Frame(bc, bg=GOLD_SUBTLE, pady=8, padx=16)
        bh.pack(fill="x")
        tk.Label(bh, text="💰  Bill Summary", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")
        bb = tk.Frame(bc, bg=BG_CARD, padx=16, pady=12)
        bb.pack(fill="both", expand=True)

        self._bill_lines = {}
        for label, key in [("Room Base Charge",    "base_room"),
                            ("Extra Person Charge", "extra_person"),
                            ("Add-On Services",     "addons"),
                            ("Meal Plan",           "meals")]:
            r = tk.Frame(bb, bg=BG_CARD)
            r.pack(fill="x", pady=3)
            tk.Label(r, text=label+":", font=FONT_BODY, bg=BG_CARD,
                     fg=TEXT_LIGHT, width=22, anchor="w").pack(side="left")
            v = tk.Label(r, text="₹0.00", font=FONT_LABEL, bg=BG_CARD, fg=CREAM)
            v.pack(side="right")
            self._bill_lines[key] = v

        tk.Frame(bb, bg=GOLD_DARK, height=1).pack(fill="x", pady=8)
        tr = tk.Frame(bb, bg=BG_CARD)
        tr.pack(fill="x")
        tk.Label(tr, text="TOTAL AMOUNT:", font=("Segoe UI", 13, "bold"),
                 bg=BG_CARD, fg=GOLD).pack(side="left")
        self._total_lbl = tk.Label(tr, text="₹0.00",
                                    font=("Segoe UI", 18, "bold"),
                                    bg=BG_CARD, fg=GOLD_LIGHT)
        self._total_lbl.pack(side="right")

        nr = tk.Frame(bb, bg=BG_CARD)
        nr.pack(fill="x", pady=4)
        self._nights_lbl = tk.Label(nr, text="Nights: 0",
                                     font=FONT_SMALL, bg=BG_CARD, fg=TEXT_MUTED)
        self._nights_lbl.pack(side="left")

        return outer

    # ── New Reservation — helpers ──────────────────────────────────────────────
    def _check_availability(self):
        ci, co = self._get_dates()
        if not ci:
            return
        rooms = self.db.get_available_rooms_for_dates(ci, co)
        self._r_room_combo["values"] = [r["room_id"] for r in rooms]
        self._room_details = {r["room_id"]: r for r in rooms}
        if rooms:
            messagebox.showinfo("Availability",
                                f"{len(rooms)} room(s) available for {ci} → {co}.")
        else:
            messagebox.showwarning("No Rooms", "No rooms available for the selected dates.")

    def _get_dates(self):
        try:
            if HAS_CALENDAR:
                ci = self._r_checkin.get_date().strftime("%Y-%m-%d")
                co = self._r_checkout.get_date().strftime("%Y-%m-%d")
            else:
                ci = self._r_checkin.get().strip()
                co = self._r_checkout.get().strip()
            if ci >= co:
                messagebox.showerror("Date Error", "Check-out must be after check-in.")
                return None, None
            return ci, co
        except Exception as e:
            messagebox.showerror("Date Error", str(e))
            return None, None

    def _on_date_change(self):
        try:
            if HAS_CALENDAR:
                ci_date = self._r_checkin.get_date()
                co_date = self._r_checkout.get_date()
                min_co  = ci_date + timedelta(days=1)
                self._r_checkout.config(mindate=min_co)
                if co_date <= ci_date:
                    self._r_checkout.set_date(min_co)
                    co_date = min_co
                nights = (co_date - ci_date).days
                self._r_nights_badge.config(
                    text=(f"📅  {ci_date.strftime('%d %b %Y')}  →  "
                          f"{co_date.strftime('%d %b %Y')}   ·   "
                          f"{nights} night{'s' if nights != 1 else ''}"),
                    fg=GOLD)
            else:
                from datetime import datetime as _dt
                ci_d  = _dt.strptime(self._r_checkin.get().strip(), "%Y-%m-%d").date()
                co_d  = _dt.strptime(self._r_checkout.get().strip(), "%Y-%m-%d").date()
                n     = (co_d - ci_d).days
                if n > 0:
                    self._r_nights_badge.config(
                        text=f"📅  {n} night{'s' if n != 1 else ''}", fg=GOLD)
                else:
                    self._r_nights_badge.config(
                        text="⚠️  Check-out must be after check-in", fg=WARNING)
        except Exception:
            pass
        self._recalculate()

    def _on_room_select(self):
        room_id = self._r_room_combo.get()
        if not room_id:
            return
        room = self._room_details.get(room_id) or self.db.get_room_by_id(room_id)
        if not room:
            return
        self._r_type_var.set(room["room_type"])
        self._r_price_var.set(fmt_currency(room["price"]))
        self._r_cap_var.set(str(room["capacity"]))
        self._r_eph_var.set(fmt_currency(room["extra_per_head"]))
        self._r_desc_lbl.config(text=room["description"] or "—")
        self._load_room_photo(room["photo_path"] or "")
        self._recalculate()

    def _load_room_photo(self, photo_path):
        self._photo_canvas.delete("all")
        try:
            from PIL import Image, ImageTk
            p = get_room_image(photo_path)
            if p:
                img = Image.open(p).resize((400, 220), Image.LANCZOS)
                ph  = ImageTk.PhotoImage(img)
                self._photo_canvas_img = ph
                self._photo_canvas.create_image(200, 110, image=ph, anchor="center")
                return
        except Exception:
            pass
        self._photo_canvas.create_rectangle(0, 0, 400, 220, fill="#050510", outline="")
        self._photo_canvas.create_text(200, 110, text="🖼️  No Photo Available",
                                        fill=TEXT_MUTED, font=("Segoe UI", 11))

    def _recalculate(self):
        ci, co = self._get_dates()
        if not ci:
            return
        nights = days_between(ci, co)
        self._nights_lbl.config(text=f"Nights: {nights}")

        room_id = self._r_room_combo.get()
        if not room_id:
            return
        room = self._room_details.get(room_id) or self.db.get_room_by_id(room_id)
        if not room:
            return

        price    = float(room["price"])
        capacity = int(room["capacity"])
        extra_ph = float(room["extra_per_head"])

        try:    adults   = int(self._r_adults.get())
        except: adults   = 1
        try:    children = int(self._r_children.get())
        except: children = 0

        extra_persons = max(0, adults + children - capacity)
        extra_charge  = extra_persons * extra_ph * nights
        if extra_persons > 0:
            self._r_extra_warn.config(
                text=f"⚠️  {extra_persons} extra × ₹{extra_ph:,.0f}/head/night"
                     f" = {fmt_currency(extra_charge)}")
        else:
            self._r_extra_warn.config(text="")

        base_room   = price * nights
        addon_total = 0
        for name, (var, qty_var, unit_price) in self._addon_vars.items():
            if var.get():
                try:    qty = int(qty_var.get())
                except: qty = 1
                addon_total += unit_price * qty

        meal_sel  = self._r_meal_combo.get()
        meal_name = meal_sel.split("(")[0].strip() if "(" in meal_sel else meal_sel
        meal_pp   = MEAL_PLANS.get(meal_name, 0)
        try:    meal_qty = int(self._r_meal_qty.get())
        except: meal_qty = 1
        meal_total = meal_pp * meal_qty * nights

        total = base_room + extra_charge + addon_total + meal_total

        self._bill_lines["base_room"].config(text=fmt_currency(base_room))
        self._bill_lines["extra_person"].config(text=fmt_currency(extra_charge))
        self._bill_lines["addons"].config(text=fmt_currency(addon_total))
        self._bill_lines["meals"].config(text=fmt_currency(meal_total))
        self._total_lbl.config(text=fmt_currency(total))

        self._calc = {
            "nights": nights, "base_room": base_room,
            "extra_charge": extra_charge, "extra_persons": extra_persons,
            "addon_total": addon_total, "meal_total": meal_total, "total": total,
            "meal_name": meal_name, "meal_qty": meal_qty,
            "adults": adults, "children": children,
        }

    def _confirm_reservation(self):
        ci, co = self._get_dates()
        if not ci:
            return
        client_sel = self._r_client_combo.get()
        room_id    = self._r_room_combo.get()
        if not client_sel or not room_id:
            messagebox.showerror("Incomplete", "Please select both a client and a room.")
            return
        if not self._calc:
            self._recalculate()
        if not self._calc:
            messagebox.showerror("Error", "Could not calculate price. Fill in all fields.")
            return

        client_id   = client_sel.split("—")[0].strip()
        addon_parts = []
        for name, (var, qty_var, unit_price) in self._addon_vars.items():
            if var.get():
                try:    qty = int(qty_var.get())
                except: qty = 1
                addon_parts.append(f"{name} (x{qty}):{unit_price * qty}")
        add_ons_str = "|".join(addon_parts)
        notes       = self._r_notes.get("1.0", tk.END).strip()
        res_id      = generate_res_id()

        ok, msg = self.db.add_reservation(
            res_id, client_id, room_id, ci, co,
            self._calc["adults"],        self._calc["children"],
            self._calc["extra_persons"], self._calc["extra_charge"],
            add_ons_str,
            self._calc["meal_name"],     self._calc["meal_qty"],
            self._calc["meal_total"],    self._calc["nights"],
            self._calc["base_room"],     self._calc["total"],
            notes)
        if ok:
            messagebox.showinfo("Confirmed",
                                f"✅ {msg}\nReservation ID: {res_id}\n"
                                f"Total Bill: {fmt_currency(self._calc['total'])}")
            self._clear_reservation()
        else:
            messagebox.showerror("Error", msg)

    def _clear_reservation(self):
        self._r_client_combo.set("")
        self._r_room_combo.set("")
        self._r_adults.delete(0, "end");    self._r_adults.insert(0, "1")
        self._r_children.delete(0, "end"); self._r_children.insert(0, "0")
        self._r_meal_combo.current(0)
        self._r_meal_qty.delete(0, "end"); self._r_meal_qty.insert(0, "1")
        self._r_notes.delete("1.0", tk.END)
        for var, qty_var, _ in self._addon_vars.values():
            var.set(False); qty_var.set(1)
        self._r_type_var.set("—");  self._r_price_var.set("—")
        self._r_cap_var.set("—");   self._r_eph_var.set("—")
        self._r_desc_lbl.config(text="—")
        self._total_lbl.config(text="₹0.00")
        for lbl in self._bill_lines.values():
            lbl.config(text="₹0.00")
        self._nights_lbl.config(text="Nights: 0")
        self._r_extra_warn.config(text="")
        self._photo_canvas.delete("all")
        self._photo_canvas.create_text(200, 110, text="Select a room to see preview",
                                        fill=TEXT_MUTED, font=FONT_SMALL)
        self._photo_canvas_img = None
        self._calc = {}

    def _refresh_client_combo(self):
        clients = self.db.get_client_ids_names()
        self._r_client_combo["values"] = [f"{c[0]} — {c[1]}" for c in clients]

    def _refresh_room_combo(self):
        rooms = self.db.get_all_rooms()
        self._r_room_combo["values"] = [r["room_id"] for r in rooms]
        self._room_details = {r["room_id"]: r for r in rooms}

    # ==========================================================================
    # ── ALL RESERVATIONS ───────────────────────────────────────────────────────
    # ==========================================================================
    def _build_all_reservations(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)
        card  = tk.Frame(frame, bg=BG_CARD,
                         highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        # Header with buttons
        ch = tk.Frame(card, bg=BG_SIDEBAR, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="📋  All Reservations", font=FONT_SUBHEAD,
                 bg=BG_SIDEBAR, fg=GOLD).pack(side="left")

        ttk.Button(ch, text="🔄 Refresh", style="Info.TButton",
                   command=self._load_all_reservations).pack(side="right")
        ttk.Button(ch, text="❌ Cancel Selected", style="Danger.TButton",
                   command=self._cancel_selected).pack(side="right", padx=8)

        # Treeview
        wrap = tk.Frame(card, bg=BG_CARD)
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        cols = ("Res. ID", "Client", "Room", "Type",
                "Check-In", "Check-Out", "Nights",
                "Adults", "Children", "Total", "Payment", "Status", "Created")
        self._all_tree = ttk.Treeview(wrap, columns=cols, show="headings", height=16)
        widths = [130, 140, 80, 120, 100, 100, 70, 70, 80, 110, 90, 100, 140]
        for col, w in zip(cols, widths):
            self._all_tree.heading(col, text=col)
            self._all_tree.column(col, width=w, anchor="center", minwidth=60)

        vsb = ttk.Scrollbar(wrap, orient="vertical",   command=self._all_tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=self._all_tree.xview)
        self._all_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._all_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        self._all_tree.tag_configure("odd",       background=BG_ROW_ALT)
        self._all_tree.tag_configure("paid",      foreground=SUCCESS)
        self._all_tree.tag_configure("cancelled", foreground=DANGER)

        return frame

    def _load_all_reservations(self):
        rows = self.db.get_all_reservations()
        for item in self._all_tree.get_children():
            self._all_tree.delete(item)
        for i, r in enumerate(rows):
            tags = []
            if i % 2:                         tags.append("odd")
            if r["payment_status"] == "Paid":  tags.append("paid")
            if r["status"] == "Cancelled":     tags.append("cancelled")
            self._all_tree.insert("", "end", tags=tuple(tags), values=(
                r["reservation_id"], r["client_name"], r["room_id"], r["room_type"],
                r["check_in"], r["check_out"], r["nights"],
                r["adults"], r["children"],
                fmt_currency(r["total_amount"]),
                r["payment_status"], r["status"],
                str(r["created_at"])[:16]
            ))

    def _cancel_selected(self):
        sel = self._all_tree.selection()
        if not sel:
            messagebox.showwarning("Select Row", "Please select a reservation to cancel.")
            return
        res_id = str(self._all_tree.item(sel[0])["values"][0])
        if not messagebox.askyesno("Confirm Cancel", f"Cancel reservation {res_id}?"):
            return
        ok, msg = self.db.cancel_reservation(res_id)
        if ok:
            messagebox.showinfo("Cancelled", msg)
            self._load_all_reservations()
        else:
            messagebox.showerror("Error", msg)

    # ==========================================================================
    # ── SHARED ─────────────────────────────────────────────────────────────────
    # ==========================================================================
    def refresh(self):
        self._refresh_client_combo()
        self._refresh_room_combo()
