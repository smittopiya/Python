# frames/payments.py — Payments & Billing Frame (Fixed Layout)
import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *
from utils import fmt_currency, generate_pdf_invoice, get_invoices_folder


def _register_small_btn_styles(widget):
    """Register compact button styles used only in Payments."""
    s = ttk.Style(widget)
    # Small gold button
    s.configure("Small.TButton",
                font=("Segoe UI", 8, "bold"),
                padding=(8, 5))
    s.map("Small.TButton",
          background=[("active", GOLD_LIGHT), ("pressed", GOLD_DARK)],
          foreground=[("active", BG_MAIN)])
    # Small success (green) button
    s.configure("SmallSuccess.TButton",
                background=SUCCESS, foreground=CREAM,
                font=("Segoe UI", 8, "bold"),
                padding=(8, 5))
    s.map("SmallSuccess.TButton",
          background=[("active", "#2ECC71"), ("pressed", "#1A7A42")])


PAYMENT_METHODS = ["Cash", "Credit Card", "Debit Card",
                   "UPI", "Net Banking", "Cheque"]


class PaymentsFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db = db
        self._selected_res = None
        self._build_ui()

    def _build_ui(self):
        # ── Page header ─────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_MAIN, padx=30, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="BILLING", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hdr, text="Payment / Billing", font=FONT_HEADING,
                 bg=BG_MAIN, fg=GOLD).pack(anchor="w")
        tk.Frame(self, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # ── Two-column body ──────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=30, pady=10)

        # Use grid so we can control column widths
        body.columnconfigure(0, weight=3)   # table takes 3 parts
        body.columnconfigure(1, weight=0)   # fixed thin divider
        body.columnconfigure(2, weight=2)   # details panel takes 2 parts
        body.rowconfigure(0, weight=1)

        left_col  = tk.Frame(body, bg=BG_MAIN)
        sep_col   = tk.Frame(body, bg=GOLD_DARK, width=1)
        right_col = tk.Frame(body, bg=BG_MAIN, width=420)

        left_col.grid(row=0, column=0, sticky="nsew")
        sep_col.grid(row=0, column=1, sticky="ns", padx=6)
        right_col.grid(row=0, column=2, sticky="nsew")
        right_col.pack_propagate(False)   # keep fixed width

        # ── LEFT: Reservations table ─────────────────────────────────────────────
        tbl_card = tk.Frame(left_col, bg=BG_CARD,
                            highlightbackground=BORDER, highlightthickness=1)
        tbl_card.pack(fill="both", expand=True)

        # Table header
        th = tk.Frame(tbl_card, bg=BG_SIDEBAR, pady=10, padx=16)
        th.pack(fill="x")
        tk.Label(th, text="📋  All Reservations", font=FONT_SUBHEAD,
                 bg=BG_SIDEBAR, fg=GOLD).pack(side="left")
        ttk.Button(th, text="🔄 Refresh", style="Info.TButton",
                   command=self._load_all).pack(side="right")

        # Filter row
        filt = tk.Frame(tbl_card, bg=BG_CARD, padx=16, pady=8)
        filt.pack(fill="x")
        tk.Label(filt, text="Filter:", font=FONT_LABEL, bg=BG_CARD, fg=GOLD).pack(side="left")
        self._filter_var = tk.StringVar(value="All")
        for val in ["All", "Pending", "Paid", "Cancelled"]:
            tk.Radiobutton(filt, text=val, value=val, variable=self._filter_var,
                           bg=BG_CARD, fg=CREAM, selectcolor=BG_INPUT,
                           activebackground=BG_CARD, font=FONT_BODY,
                           command=self._load_all).pack(side="left", padx=8)

        # Treeview
        wrap = tk.Frame(tbl_card, bg=BG_CARD)
        wrap.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        cols = ("Res. ID", "Client", "Room", "Check-In",
                "Check-Out", "Total", "Payment", "Status")
        self._pay_tree = ttk.Treeview(wrap, columns=cols, show="headings", height=18)
        widths = [130, 150, 80, 100, 100, 120, 90, 100]
        for col, w in zip(cols, widths):
            self._pay_tree.heading(col, text=col,
                                   command=lambda c=col: self._sort_by(c))
            self._pay_tree.column(col, width=w, anchor="center", minwidth=60)

        vsb = ttk.Scrollbar(wrap, orient="vertical",   command=self._pay_tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=self._pay_tree.xview)
        self._pay_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._pay_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        self._pay_tree.tag_configure("odd",       background=BG_ROW_ALT)
        self._pay_tree.tag_configure("paid",      foreground=SUCCESS)
        self._pay_tree.tag_configure("pending",   foreground=WARNING)
        self._pay_tree.tag_configure("cancelled", foreground=DANGER)
        self._pay_tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── RIGHT: Detail panel (split into scrollable info + fixed action bar) ──
        right_col.rowconfigure(0, weight=1)   # top part expands
        right_col.rowconfigure(1, weight=0)   # bottom bar fixed

        # ── TOP: scrollable bill details ────────────────────────────────────────
        detail_card = tk.Frame(right_col, bg=BG_CARD,
                               highlightbackground=BORDER_GOLD, highlightthickness=1)
        detail_card.pack(fill="both", expand=True, pady=(0, 6))

        dh = tk.Frame(detail_card, bg=GOLD_SUBTLE, pady=10, padx=16)
        dh.pack(fill="x")
        tk.Label(dh, text="💼  Bill Details", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(side="left")
        tk.Label(dh, text="Click a row to view", font=FONT_SMALL,
                 bg=GOLD_SUBTLE, fg=TEXT_MUTED).pack(side="right")

        # Canvas + scrollbar inside detail_card
        canvas_frame = tk.Frame(detail_card, bg=BG_CARD)
        canvas_frame.pack(fill="both", expand=True)

        self._detail_canvas = tk.Canvas(canvas_frame, bg=BG_CARD,
                                         highlightthickness=0)
        detail_vsb = ttk.Scrollbar(canvas_frame, orient="vertical",
                                    command=self._detail_canvas.yview)
        self._detail_inner = tk.Frame(self._detail_canvas, bg=BG_CARD)
        self._detail_inner.bind(
            "<Configure>",
            lambda e: self._detail_canvas.configure(
                scrollregion=self._detail_canvas.bbox("all")))

        self._detail_canvas.create_window((0, 0), window=self._detail_inner,
                                           anchor="nw", tags="inner")
        self._detail_canvas.configure(yscrollcommand=detail_vsb.set)

        # Bind canvas width to inner frame width
        self._detail_canvas.bind(
            "<Configure>",
            lambda e: self._detail_canvas.itemconfig("inner", width=e.width))

        self._detail_canvas.pack(side="left", fill="both", expand=True)
        detail_vsb.pack(side="right", fill="y")

        # Mousewheel binding
        self._detail_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._detail_canvas.yview_scroll(-1*(e.delta//120), "units"))

        # Placeholder
        self._detail_placeholder = tk.Label(
            self._detail_inner,
            text="⬅  Select a reservation from\nthe list to view bill details.",
            font=FONT_BODY, bg=BG_CARD, fg=TEXT_MUTED, justify="center")
        self._detail_placeholder.pack(pady=60)

        # Bill detail fields
        self._detail_labels = {}
        detail_fields = [
            ("Reservation ID",   "reservation_id"),
            ("Client Name",      "client_name"),
            ("Contact",          "contact"),
            ("Room ID",          "room_id"),
            ("Room Type",        "room_type"),
            ("Check-In Date",    "check_in"),
            ("Check-Out Date",   "check_out"),
            ("No. of Nights",    "nights"),
            ("Adults",           "adults"),
            ("Children",         "children"),
            ("Extra Persons",    "extra_persons"),
            ("Extra Charge",     "extra_charge_fmt"),
            ("Add-On Services",  "add_ons"),
            ("Meal Plan",        "meal_plan"),
            ("Meal Charge",      "meal_price_fmt"),
            ("Base Room Charge", "base_amount_fmt"),
        ]
        for label, key in detail_fields:
            r = tk.Frame(self._detail_inner, bg=BG_CARD, padx=14, pady=1)
            r.pack(fill="x")
            tk.Label(r, text=f"{label}:", font=FONT_SMALL, bg=BG_CARD,
                     fg=TEXT_MUTED, width=17, anchor="nw").pack(side="left", pady=3)
            lbl = tk.Label(r, text="—", font=FONT_BODY, bg=BG_CARD,
                           fg=CREAM, wraplength=200, anchor="w", justify="left")
            lbl.pack(side="left", fill="x", expand=True, pady=3)
            self._detail_labels[key] = lbl

        # Divider
        tk.Frame(self._detail_inner, bg=GOLD_DARK, height=1).pack(
            fill="x", padx=14, pady=8)

        # Total
        tot_row = tk.Frame(self._detail_inner, bg=BG_CARD, padx=14)
        tot_row.pack(fill="x")
        tk.Label(tot_row, text="TOTAL AMOUNT:", font=("Segoe UI", 11, "bold"),
                 bg=BG_CARD, fg=GOLD).pack(side="left")
        self._detail_total_lbl = tk.Label(tot_row, text="—",
                                           font=("Segoe UI", 15, "bold"),
                                           bg=BG_CARD, fg=GOLD_LIGHT)
        self._detail_total_lbl.pack(side="right", pady=6)

        # Payment status badge
        status_row = tk.Frame(self._detail_inner, bg=BG_CARD, padx=14)
        status_row.pack(fill="x", pady=(0, 10))
        tk.Label(status_row, text="Payment Status:", font=FONT_LABEL,
                 bg=BG_CARD, fg=TEXT_MUTED).pack(side="left")
        self._pay_status_lbl = tk.Label(status_row, text="—",
                                         font=("Segoe UI", 10, "bold"),
                                         bg=BG_CARD, fg=TEXT_MUTED)
        self._pay_status_lbl.pack(side="left", padx=8)

        # ── BOTTOM: Always-visible action bar ────────────────────────────────────
        action_bar = tk.Frame(right_col, bg=BG_CARD,
                              highlightbackground=BORDER_GOLD, highlightthickness=1)
        action_bar.pack(fill="x", pady=(0, 0))

        # Payment method row
        pm_row = tk.Frame(action_bar, bg=BG_CARD, padx=14, pady=10)
        pm_row.pack(fill="x")
        tk.Label(pm_row, text="Payment Method:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=17, anchor="w").pack(side="left")
        self._pay_method_combo = ttk.Combobox(pm_row, values=PAYMENT_METHODS,
                                               width=18, state="readonly")
        self._pay_method_combo.set("Cash")
        self._pay_method_combo.pack(side="left", ipady=3)

        # Action buttons — 3 in a row with icons
        btn_frame = tk.Frame(action_bar, bg=BG_CARD, padx=14, pady=8)
        btn_frame.pack(fill="x")
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        _register_small_btn_styles(self)

        ttk.Button(btn_frame, text="📄  View Bill",
                   style="Small.TButton",
                   command=self._generate_bill).grid(
                   row=0, column=0, sticky="ew", padx=(0, 4), ipady=4)
        ttk.Button(btn_frame, text="✅  Mark Paid",
                   style="SmallSuccess.TButton",
                   command=self._mark_paid).grid(
                   row=0, column=1, sticky="ew", padx=4, ipady=4)
        ttk.Button(btn_frame, text="💾  PDF Invoice",
                   style="Small.TButton",
                   command=self._save_pdf).grid(
                   row=0, column=2, sticky="ew", padx=(4, 0), ipady=4)

        self._load_all()

    # ─── Table loading ────────────────────────────────────────────────────────────
    def _sort_by(self, col):
        """Basic toggle sort on a column."""
        items = [(self._pay_tree.set(k, col), k)
                 for k in self._pay_tree.get_children("")]
        rev = getattr(self, "_sort_rev", False)
        items.sort(reverse=rev)
        for idx, (_, k) in enumerate(items):
            self._pay_tree.move(k, "", idx)
        self._sort_rev = not rev

    def _load_all(self):
        rows = self.db.get_all_reservations_for_billing()
        filt = self._filter_var.get()
        for item in self._pay_tree.get_children():
            self._pay_tree.delete(item)
        row_num = 0
        for r in rows:
            if filt != "All" and r["payment_status"] != filt:
                if filt == "Cancelled" and r["status"] != "Cancelled":
                    continue
                elif filt != "Cancelled":
                    continue
            tags = []
            if row_num % 2:
                tags.append("odd")
            if r["payment_status"] == "Paid":
                tags.append("paid")
            elif r["payment_status"] == "Pending":
                tags.append("pending")
            if r["status"] == "Cancelled":
                tags.append("cancelled")
            self._pay_tree.insert("", "end", iid=r["reservation_id"],
                                   tags=tuple(tags), values=(
                r["reservation_id"], r["client_name"], r["room_id"],
                r["check_in"], r["check_out"],
                fmt_currency(r["total_amount"]),
                r["payment_status"], r["status"]
            ))
            row_num += 1

    def _on_select(self, event):
        sel = self._pay_tree.selection()
        if not sel:
            return
        res_id = sel[0]
        detail = self.db.get_reservation_detail(res_id)
        if not detail:
            return
        self._selected_res = dict(detail)
        self._detail_placeholder.pack_forget()

        mapping = {
            "reservation_id":   detail["reservation_id"],
            "client_name":      detail["client_name"],
            "contact":          detail["contact"],
            "room_id":          detail["room_id"],
            "room_type":        detail["room_type"],
            "check_in":         detail["check_in"],
            "check_out":        detail["check_out"],
            "nights":           str(detail["nights"]),
            "adults":           str(detail["adults"]),
            "children":         str(detail["children"]),
            "extra_persons":    str(detail["extra_persons"]),
            "extra_charge_fmt": fmt_currency(detail["extra_charge"]),
            "add_ons":          (detail["add_ons"] or "None").replace("|", "\n"),
            "meal_plan":        detail["meal_plan"],
            "meal_price_fmt":   fmt_currency(detail["meal_price"]),
            "base_amount_fmt":  fmt_currency(detail["base_amount"]),
        }
        for key, lbl in self._detail_labels.items():
            lbl.config(text=str(mapping.get(key, "—")))
        self._detail_total_lbl.config(text=fmt_currency(detail["total_amount"]))

        # Status badge colour
        status = self._selected_res.get("payment_status", "—")
        colour = SUCCESS if status == "Paid" else (DANGER if status == "Cancelled" else WARNING)
        self._pay_status_lbl.config(text=status, fg=colour)

        # Scroll to top
        self._detail_canvas.yview_moveto(0)

    # ─── Bill viewer popup ────────────────────────────────────────────────────────
    def _generate_bill(self):
        if not self._selected_res:
            messagebox.showwarning("No Selection",
                                   "Please select a reservation first.")
            return
        r = self._selected_res
        addon_total = (r.get("total_amount", 0)
                       - r.get("base_amount", 0)
                       - r.get("extra_charge", 0)
                       - r.get("meal_price", 0))

        sep  = "═" * 50
        sep2 = "─" * 50
        msg = (
            f"\n  THE VELORIA GRAND HOTEL\n"
            f"  {sep}\n"
            f"           BILL OF CHARGES\n"
            f"  {sep}\n"
            f"  Reservation ID  : {r.get('reservation_id','')}\n"
            f"  Client          : {r.get('client_name','')}\n"
            f"  Contact         : {r.get('contact','')}\n"
            f"  Room            : {r.get('room_id','')} — {r.get('room_type','')}\n"
            f"  Check-In        : {r.get('check_in','')}\n"
            f"  Check-Out       : {r.get('check_out','')}\n"
            f"  Nights          : {r.get('nights','')}\n"
            f"  Adults          : {r.get('adults','')}\n"
            f"  Children        : {r.get('children','')}\n"
            f"  {sep2}\n"
            f"  Base Room Charge: {fmt_currency(r.get('base_amount', 0))}\n"
            f"  Extra Persons   : {fmt_currency(r.get('extra_charge', 0))}\n"
            f"  Add-On Services : {fmt_currency(addon_total)}\n"
            f"  Meal Plan       : {r.get('meal_plan','')}\n"
            f"  Meal Charge     : {fmt_currency(r.get('meal_price', 0))}\n"
            f"  {sep}\n"
            f"  TOTAL AMOUNT    : {fmt_currency(r.get('total_amount', 0))}\n"
            f"  Payment Status  : {r.get('payment_status','')}\n"
            f"  {sep}\n\n"
            f"  Terms & Conditions:\n"
            f"  • Check-out by 12:00 Noon\n"
            f"  • Late payments incur 2% daily interest\n"
            f"  • Non-refundable within 24 hours of check-in\n"
        )

        win = tk.Toplevel(self)
        win.title(f"Bill — {r.get('reservation_id','')}")
        win.configure(bg=BG_MAIN)
        win.geometry("600x640")
        win.resizable(True, True)

        # Header
        tk.Label(win, text="THE VELORIA GRAND — INVOICE",
                 font=("Georgia", 14, "bold"), bg=BG_MAIN, fg=GOLD).pack(pady=(14, 0))
        tk.Frame(win, bg=GOLD_DARK, height=1).pack(fill="x", padx=20, pady=8)

        # Text area with scrollbar
        txt_frame = tk.Frame(win, bg=BG_CARD)
        txt_frame.pack(fill="both", expand=True, padx=14, pady=4)
        text = tk.Text(txt_frame, bg=BG_CARD, fg=CREAM, font=FONT_MONO,
                       padx=12, pady=10, relief="flat", wrap="word")
        tsb  = ttk.Scrollbar(txt_frame, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=tsb.set)
        text.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")
        text.insert("1.0", msg)
        text.config(state="disabled")

        # Bottom close button
        tk.Frame(win, bg=BG_MAIN, height=1).pack(fill="x", padx=14)
        btn_row = tk.Frame(win, bg=BG_MAIN)
        btn_row.pack(pady=10)
        ttk.Button(btn_row, text="💾  Save PDF", command=self._save_pdf).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Close", style="Info.TButton",
                   command=win.destroy).pack(side="left")

    # ─── Mark as paid ─────────────────────────────────────────────────────────────
    def _mark_paid(self):
        if not self._selected_res:
            messagebox.showwarning("No Selection", "Please select a reservation first.")
            return
        res_id = self._selected_res["reservation_id"]
        if self._selected_res.get("payment_status") == "Paid":
            messagebox.showinfo("Already Paid",
                                f"Reservation {res_id} is already marked as Paid.")
            return
        method = self._pay_method_combo.get() or "Cash"
        if not messagebox.askyesno("Mark as Paid",
                                   f"Mark reservation {res_id} as PAID via {method}?"):
            return
        ok, msg = self.db.update_reservation_payment(res_id, "Paid", method)
        if ok:
            messagebox.showinfo("Success", f"✅ {msg}")
            self._load_all()
            self._selected_res["payment_status"] = "Paid"
            self._pay_status_lbl.config(text="Paid", fg=SUCCESS)
        else:
            messagebox.showerror("Error", msg)

    # ─── Save PDF ─────────────────────────────────────────────────────────────────
    def _save_pdf(self):
        if not self._selected_res:
            messagebox.showwarning("No Selection", "Please select a reservation first.")
            return
        res_id = self._selected_res["reservation_id"]
        detail = self.db.get_reservation_detail(res_id)
        if not detail:
            messagebox.showerror("Error", "Could not load reservation details.")
            return

        folder   = get_invoices_folder()
        filename = f"Invoice_{res_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        path     = os.path.join(folder, filename)

        try:
            generate_pdf_invoice(dict(detail), path)
            messagebox.showinfo("PDF Saved",
                                f"✅ Invoice saved to:\n{path}")
        except ImportError:
            messagebox.showerror("Library Missing",
                                 "fpdf2 is not installed.\nRun: pip install fpdf2")
        except Exception as e:
            messagebox.showerror("PDF Error", str(e))

    def refresh(self):
        self._load_all()
