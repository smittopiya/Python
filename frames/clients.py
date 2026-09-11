
# frames/clients.py — Client Management Frame
import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *
from utils import (validate_id_proof, validate_phone, validate_nonempty,
                   ID_PROOF_TYPES, ID_PROOF_RULES)

GENDERS  = ["Male", "Female", "Other", "Prefer not to say"]
COUNTRIES = ["India", "USA", "UK", "UAE", "Canada", "Australia",
             "Germany", "France", "Japan", "Singapore", "Other"]


def _row(parent, bg=BG_CARD):
    f = tk.Frame(parent, bg=bg)
    f.pack(fill="x", pady=3)
    return f


def _lbl_e(parent, text, bg=BG_CARD, w=26):
    r = _row(parent, bg)
    tk.Label(r, text=text, font=FONT_LABEL, bg=bg,
             fg=GOLD, width=22, anchor="w").pack(side="left")
    e = ttk.Entry(r, width=w)
    e.pack(side="left", ipady=3)
    return e


def _lbl_c(parent, text, values, bg=BG_CARD, w=25):
    r = _row(parent, bg)
    tk.Label(r, text=text, font=FONT_LABEL, bg=bg,
             fg=GOLD, width=22, anchor="w").pack(side="left")
    c = ttk.Combobox(r, values=values, width=w, state="readonly")
    c.pack(side="left", ipady=3)
    return c


class ClientsFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db = db
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_MAIN, padx=30, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="CLIENT MANAGEMENT", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hdr, text="Clients", font=FONT_HEADING, bg=BG_MAIN, fg=GOLD).pack(anchor="w")
        tk.Frame(self, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # Sub-nav
        nav = tk.Frame(self, bg=BG_SIDEBAR, pady=10)
        nav.pack(fill="x", padx=30, pady=(12, 0))
        self._sub_btns = {}
        subs = [
            ("➕  Add Client",    "add"),
            ("📋  Show Clients",  "show"),
            ("✏️  Update Client", "update"),
            ("🗑  Delete Client", "delete"),
        ]
        for label, key in subs:
            btn = tk.Button(nav, text=label, font=FONT_LABEL,
                            bg=BG_CARD, fg=TEXT_MUTED, relief="flat",
                            activebackground=GOLD_DARK, activeforeground=CREAM,
                            cursor="hand2", padx=14, pady=8,
                            command=lambda k=key: self._show_sub(k))
            btn.pack(side="left", padx=4)
            self._sub_btns[key] = btn

        self._container = tk.Frame(self, bg=BG_MAIN)
        self._container.pack(fill="both", expand=True, padx=30, pady=12)

        self._subs = {
            "add":    self._build_add(),
            "show":   self._build_show(),
            "update": self._build_update(),
            "delete": self._build_delete(),
        }
        self._show_sub("add")

    def _show_sub(self, key):
        for frame in self._subs.values():
            frame.pack_forget()
        self._subs[key].pack(fill="both", expand=True)
        for k, btn in self._sub_btns.items():
            btn.config(bg=GOLD if k == key else BG_CARD,
                       fg=BG_MAIN if k == key else TEXT_MUTED)
        if key == "show":
            self._load_clients()
        if key == "delete":
            self._refresh_del_combo()

    # ─── ADD CLIENT ───────────────────────────────────────────────────────────────
    def _build_add(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)
        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER_GOLD, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg=GOLD_SUBTLE, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="➕  Register New Client", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")

        body = tk.Frame(card, bg=BG_CARD, padx=30, pady=16)
        body.pack(fill="both", expand=True)

        left  = tk.Frame(body, bg=BG_CARD)
        right = tk.Frame(body, bg=BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right.pack(side="left", fill="both", expand=True)

        self._a_id      = _lbl_e(left,  "Client ID *")
        self._a_name    = _lbl_e(left,  "Full Name *")
        self._a_gender  = _lbl_c(left,  "Gender *",  GENDERS)
        self._a_contact = _lbl_e(left,  "Contact (10 digits) *")

        self._a_addr    = _lbl_e(right, "Address")
        self._a_city    = _lbl_e(right, "City")
        self._a_state   = _lbl_e(right, "State")
        self._a_country = _lbl_c(right, "Country", COUNTRIES)
        self._a_country.set("India")

        # ID proof row with hint
        id_row = _row(right, BG_CARD)
        tk.Label(id_row, text="ID Proof Type *", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left")
        self._a_id_type = ttk.Combobox(id_row, values=ID_PROOF_TYPES,
                                        width=25, state="readonly")
        self._a_id_type.pack(side="left", ipady=3)
        self._a_id_type.bind("<<ComboboxSelected>>",
                              lambda e: self._update_id_hint("add"))

        num_row = _row(right, BG_CARD)
        tk.Label(num_row, text="ID Proof Number *", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left")
        self._a_id_num = ttk.Entry(num_row, width=26)
        self._a_id_num.pack(side="left", ipady=3)

        self._a_id_hint = tk.Label(right, text="", font=FONT_SMALL,
                                    bg=BG_CARD, fg=TEXT_MUTED)
        self._a_id_hint.pack(anchor="w", padx=(186, 0))

        tk.Frame(body, bg=GOLD_DARK, height=1).pack(
            fill="x", pady=(14, 10), side="bottom")
        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(side="bottom", anchor="e", pady=4)
        ttk.Button(btn_row, text="Clear", style="Info.TButton",
                   command=self._clear_add).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Register Client",
                   command=self._do_add).pack(side="left")

        return frame

    def _update_id_hint(self, which):
        id_type_widget = self._a_id_type if which == "add" else self._u_id_type
        hint_widget    = self._a_id_hint if which == "add" else self._u_id_hint
        t = id_type_widget.get()
        rule = ID_PROOF_RULES.get(t)
        if rule:
            hint_widget.config(text=f"Format: {rule['desc']}")
        else:
            hint_widget.config(text="")

    def _clear_add(self):
        for w in [self._a_id, self._a_name, self._a_contact,
                  self._a_addr, self._a_city, self._a_state, self._a_id_num]:
            w.delete(0, tk.END)
        self._a_gender.set("")
        self._a_country.set("India")
        self._a_id_type.set("")
        self._a_id_hint.config(text="")

    def _do_add(self):
        vals = {
            "Client ID":    self._a_id.get().strip(),
            "Full Name":    self._a_name.get().strip(),
            "Gender":       self._a_gender.get(),
            "Contact":      self._a_contact.get().strip(),
            "ID Proof Type": self._a_id_type.get(),
        }
        ok, msg = validate_nonempty(vals)
        if not ok:
            messagebox.showerror("Missing Field", msg)
            return

        ok, msg = validate_phone(self._a_contact.get().strip())
        if not ok:
            messagebox.showerror("Invalid Contact", msg)
            return

        id_num = self._a_id_num.get().strip().upper()
        ok, msg = validate_id_proof(self._a_id_type.get(), id_num)
        if not ok:
            messagebox.showerror("Invalid ID Proof", msg)
            return

        # Uniqueness check
        if not self.db.check_id_proof_unique(self._a_id_type.get(), id_num):
            messagebox.showerror("Duplicate ID Proof",
                                 f"This {self._a_id_type.get()} number ({id_num}) "
                                 f"is already registered with another client.\n"
                                 f"Each ID proof number must be unique.")
            return

        ok, msg = self.db.add_client(
            self._a_id.get().strip().upper(),
            self._a_name.get().strip(),
            self._a_gender.get(),
            self._a_contact.get().strip(),
            self._a_addr.get().strip(),
            self._a_city.get().strip(),
            self._a_state.get().strip(),
            self._a_country.get(),
            self._a_id_type.get(),
            id_num
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self._clear_add()
        else:
            messagebox.showerror("Error", msg)

    # ─── SHOW CLIENTS ────────────────────────────────────────────────────────────
    def _build_show(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)
        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg=BG_SIDEBAR, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="📋  All Clients", font=FONT_SUBHEAD,
                 bg=BG_SIDEBAR, fg=GOLD).pack(side="left")

        ctrl = tk.Frame(ch, bg=BG_SIDEBAR)
        ctrl.pack(side="right")
        ttk.Button(ctrl, text="🔄 Refresh", style="Info.TButton",
                   command=self._load_clients).pack(side="left")
        self._show_count = tk.Label(ctrl, text="", font=FONT_SMALL,
                                     bg=BG_SIDEBAR, fg=TEXT_MUTED)
        self._show_count.pack(side="left", padx=10)

        # Search in show
        srow = tk.Frame(card, bg=BG_CARD, padx=20, pady=8)
        srow.pack(fill="x")
        tk.Label(srow, text="Quick Search:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD).pack(side="left")
        self._show_search_var = tk.StringVar()
        ent = ttk.Entry(srow, textvariable=self._show_search_var, width=28)
        ent.pack(side="left", padx=8, ipady=3)
        ent.bind("<KeyRelease>", lambda e: self._filter_clients())

        wrap = tk.Frame(card, bg=BG_CARD)
        wrap.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        cols = ("Client ID", "Name", "Gender", "Contact",
                "City", "State", "Country", "ID Proof", "ID Number", "Registered")
        self._show_tree = ttk.Treeview(wrap, columns=cols, show="headings", height=15)
        widths = [90, 160, 80, 110, 100, 100, 100, 120, 140, 140]
        for col, w in zip(cols, widths):
            self._show_tree.heading(col, text=col)
            self._show_tree.column(col, width=w, anchor="center", minwidth=60)

        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self._show_tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal", command=self._show_tree.xview)
        self._show_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self._show_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)
        self._show_tree.tag_configure("odd", background=BG_ROW_ALT)
        self._all_clients_cache = []
        return frame

    def _load_clients(self):
        self._all_clients_cache = self.db.get_all_clients()
        self._populate_show(self._all_clients_cache)

    def _filter_clients(self):
        q = self._show_search_var.get().lower()
        if not q:
            self._populate_show(self._all_clients_cache)
            return
        filtered = [c for c in self._all_clients_cache
                    if q in str(c["name"]).lower()
                    or q in str(c["client_id"]).lower()
                    or q in str(c["contact"]).lower()]
        self._populate_show(filtered)

    def _populate_show(self, clients):
        for item in self._show_tree.get_children():
            self._show_tree.delete(item)
        for i, c in enumerate(clients):
            tag = "odd" if i % 2 else ""
            self._show_tree.insert("", "end", tags=(tag,), values=(
                c["client_id"], c["name"], c["gender"], c["contact"],
                c["city"], c["state"], c["country"],
                c["id_proof_type"], c["id_proof_number"],
                str(c["registered_date"])[:10]
            ))
        self._show_count.config(text=f"Total: {len(clients)} clients")

    # ─── UPDATE CLIENT ────────────────────────────────────────────────────────────
    def _build_update(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)
        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER_GOLD, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg=GOLD_SUBTLE, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="✏️  Update Client", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")

        srow = tk.Frame(card, bg=BG_CARD, padx=30, pady=10)
        srow.pack(fill="x")
        tk.Label(srow, text="Select Client ID:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD).pack(side="left")
        self._u_client_combo = ttk.Combobox(srow, width=22, state="readonly")
        self._u_client_combo.pack(side="left", padx=8, ipady=3)
        ttk.Button(srow, text="Load Client",
                   command=self._load_client_for_update).pack(side="left")

        tk.Frame(card, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        body = tk.Frame(card, bg=BG_CARD, padx=30, pady=16)
        body.pack(fill="both", expand=True)

        left  = tk.Frame(body, bg=BG_CARD)
        right = tk.Frame(body, bg=BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right.pack(side="left", fill="both", expand=True)

        # Client ID (read-only display)
        rid_row = _row(left, BG_CARD)
        tk.Label(rid_row, text="Client ID:", font=FONT_LABEL, bg=BG_CARD,
                 fg=GOLD, width=22, anchor="w").pack(side="left")
        self._u_id_var = tk.StringVar()
        tk.Label(rid_row, textvariable=self._u_id_var, font=("Segoe UI", 11, "bold"),
                 bg=BG_CARD, fg=CREAM).pack(side="left")

        self._u_name    = _lbl_e(left,  "Full Name *")
        self._u_gender  = _lbl_c(left,  "Gender *", GENDERS)
        self._u_contact = _lbl_e(left,  "Contact (10 digits) *")
        self._u_addr    = _lbl_e(right, "Address")
        self._u_city    = _lbl_e(right, "City")
        self._u_state   = _lbl_e(right, "State")
        self._u_country = _lbl_c(right, "Country", COUNTRIES)

        id_row = _row(right, BG_CARD)
        tk.Label(id_row, text="ID Proof Type *", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left")
        self._u_id_type = ttk.Combobox(id_row, values=ID_PROOF_TYPES,
                                        width=25, state="readonly")
        self._u_id_type.pack(side="left", ipady=3)
        self._u_id_type.bind("<<ComboboxSelected>>",
                              lambda e: self._update_id_hint("update"))

        num_row = _row(right, BG_CARD)
        tk.Label(num_row, text="ID Proof Number *", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left")
        self._u_id_num = ttk.Entry(num_row, width=26)
        self._u_id_num.pack(side="left", ipady=3)

        self._u_id_hint = tk.Label(right, text="", font=FONT_SMALL,
                                    bg=BG_CARD, fg=TEXT_MUTED)
        self._u_id_hint.pack(anchor="w", padx=(186, 0))

        tk.Frame(body, bg=GOLD_DARK, height=1).pack(
            fill="x", pady=(14, 10), side="bottom")
        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(side="bottom", anchor="e", pady=4)
        ttk.Button(btn_row, text="Clear Fields", style="Info.TButton",
                   command=self._clear_update).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Update Client",
                   command=self._do_update).pack(side="left")

        self._refresh_update_combo()
        return frame

    def _refresh_update_combo(self):
        clients = self.db.get_client_ids_names()
        vals = [f"{c[0]} — {c[1]}" for c in clients]
        self._u_client_combo["values"] = vals

    def _load_client_for_update(self):
        sel = self._u_client_combo.get()
        if not sel:
            messagebox.showwarning("Select Client", "Please select a client.")
            return
        client_id = sel.split("—")[0].strip()
        c = self.db.get_client_by_id(client_id)
        if not c:
            messagebox.showerror("Not Found", "Client not found.")
            return
        self._u_id_var.set(c["client_id"])
        for ent, key in [
            (self._u_name,    "name"),
            (self._u_contact, "contact"),
            (self._u_addr,    "address"),
            (self._u_city,    "city"),
            (self._u_state,   "state"),
        ]:
            ent.delete(0, tk.END)
            ent.insert(0, str(c[key] or ""))
        self._u_gender.set(c["gender"] or "")
        self._u_country.set(c["country"] or "India")
        self._u_id_type.set(c["id_proof_type"] or "")
        self._u_id_num.delete(0, tk.END)
        self._u_id_num.insert(0, c["id_proof_number"] or "")

    def _clear_update(self):
        self._u_client_combo.set("")
        self._u_id_var.set("")
        for w in [self._u_name, self._u_contact,
                  self._u_addr, self._u_city, self._u_state, self._u_id_num]:
            w.delete(0, tk.END)
        self._u_gender.set("")
        self._u_country.set("India")
        self._u_id_type.set("")
        self._u_id_hint.config(text="")

    def _do_update(self):
        client_id = self._u_id_var.get().strip()
        if not client_id:
            messagebox.showwarning("No Client Loaded", "Please load a client first.")
            return
        ok, msg = validate_nonempty({
            "Full Name":    self._u_name.get().strip(),
            "Gender":       self._u_gender.get(),
            "Contact":      self._u_contact.get().strip(),
            "ID Proof Type": self._u_id_type.get(),
        })
        if not ok:
            messagebox.showerror("Missing Field", msg)
            return
        ok, msg = validate_phone(self._u_contact.get().strip())
        if not ok:
            messagebox.showerror("Invalid Contact", msg)
            return
        id_num = self._u_id_num.get().strip().upper()
        ok, msg = validate_id_proof(self._u_id_type.get(), id_num)
        if not ok:
            messagebox.showerror("Invalid ID Proof", msg)
            return

        # Uniqueness check (exclude current client)
        client_id = self._u_id_var.get().strip()
        if not self.db.check_id_proof_unique(self._u_id_type.get(), id_num,
                                              exclude_client_id=client_id):
            messagebox.showerror("Duplicate ID Proof",
                                 f"This {self._u_id_type.get()} number ({id_num}) "
                                 f"is already registered with another client.")
            return

        ok, msg = self.db.update_client(
            client_id,
            self._u_name.get().strip(),
            self._u_gender.get(),
            self._u_contact.get().strip(),
            self._u_addr.get().strip(),
            self._u_city.get().strip(),
            self._u_state.get().strip(),
            self._u_country.get(),
            self._u_id_type.get(),
            id_num
        )
        if ok:
            messagebox.showinfo("Success", msg)
            self._clear_update()
            self._refresh_update_combo()
        else:
            messagebox.showerror("Error", msg)

    # ─── DELETE CLIENT ────────────────────────────────────────────────────────────
    def _build_delete(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)
        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg="#1A0808", pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="🗑  Delete Client", font=FONT_SUBHEAD,
                 bg="#1A0808", fg=DANGER).pack(anchor="w")

        body = tk.Frame(card, bg=BG_CARD, padx=30, pady=20)
        body.pack(fill="both", expand=True)

        row1 = tk.Frame(body, bg=BG_CARD)
        row1.pack(fill="x", pady=6)
        tk.Label(row1, text="Select Client:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=20, anchor="w").pack(side="left")
        self._del_client_combo = ttk.Combobox(row1, width=32, state="readonly")
        self._del_client_combo.pack(side="left", ipady=3)
        ttk.Button(row1, text="Load Details",
                   command=self._load_client_for_delete).pack(side="left", padx=8)

        # Info area
        self._del_client_info = {}
        for field in ["Name", "Contact", "City", "ID Proof"]:
            r = tk.Frame(body, bg=BG_CARD)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{field}:", font=FONT_LABEL, bg=BG_CARD,
                     fg=TEXT_MUTED, width=18, anchor="w").pack(side="left")
            lbl = tk.Label(r, text="—", font=FONT_BODY, bg=BG_CARD, fg=CREAM)
            lbl.pack(side="left")
            self._del_client_info[field] = lbl

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=12)
        tk.Label(body, text="⚠️  Clients with active reservations cannot be deleted.",
                 font=FONT_SMALL, bg=BG_CARD, fg=WARNING).pack(anchor="w")

        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(anchor="w", pady=10)
        ttk.Button(btn_row, text="Clear", style="Info.TButton",
                   command=self._clear_delete).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Delete Client", style="Danger.TButton",
                   command=self._do_delete).pack(side="left")

        return frame

    def _refresh_del_combo(self):
        clients = self.db.get_client_ids_names()
        self._del_client_combo["values"] = [f"{c[0]} — {c[1]}" for c in clients]

    def _load_client_for_delete(self):
        sel = self._del_client_combo.get()
        if not sel:
            messagebox.showwarning("Select", "Please select a client.")
            return
        client_id = sel.split("—")[0].strip()
        c = self.db.get_client_by_id(client_id)
        if not c:
            messagebox.showerror("Not Found", "Client not found.")
            return
        self._del_client_info["Name"].config(text=c["name"])
        self._del_client_info["Contact"].config(text=c["contact"])
        self._del_client_info["City"].config(text=c["city"] or "—")
        self._del_client_info["ID Proof"].config(
            text=f"{c['id_proof_type']} : {c['id_proof_number']}")

    def _clear_delete(self):
        self._del_client_combo.set("")
        for lbl in self._del_client_info.values():
            lbl.config(text="—")

    def _do_delete(self):
        sel = self._del_client_combo.get()
        if not sel:
            messagebox.showwarning("Select", "Please select a client.")
            return
        client_id = sel.split("—")[0].strip()
        name = self._del_client_info["Name"].cget("text")
        if not messagebox.askyesno("Confirm Delete",
                                   f"Delete client '{client_id} — {name}'?\nThis cannot be undone."):
            return
        ok, msg = self.db.delete_client(client_id)
        if ok:
            messagebox.showinfo("Deleted", msg)
            self._clear_delete()
            self._refresh_del_combo()
        else:
            messagebox.showerror("Error", msg)

    def refresh(self):
        self._refresh_update_combo()
        self._refresh_del_combo()
        if hasattr(self, '_all_clients_cache'):
            self._load_clients()
