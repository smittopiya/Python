
# frames/rooms.py — Room Management Frame
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *
from utils import get_images_folder, get_room_image

ROOM_TYPES = [
    "Standard Room", "Superior Room", "Deluxe Room",
    "Junior Suite", "Deluxe Suite", "Grand Suite",
    "Presidential Suite", "Penthouse Suite", "Ocean View Room", "Garden Villa"
]


def _lbl_entry(parent, text, bg=BG_CARD, entry_width=28):
    """Helper: creates label + entry pair, returns entry widget."""
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", pady=4)
    tk.Label(row, text=text, font=FONT_LABEL, bg=bg,
             fg=GOLD, width=22, anchor="w").pack(side="left")
    ent = ttk.Entry(row, width=entry_width)
    ent.pack(side="left", ipady=3)
    return ent


def _lbl_combo(parent, text, values, bg=BG_CARD, cb_width=27):
    row = tk.Frame(parent, bg=bg)
    row.pack(fill="x", pady=4)
    tk.Label(row, text=text, font=FONT_LABEL, bg=bg,
             fg=GOLD, width=22, anchor="w").pack(side="left")
    combo = ttk.Combobox(row, values=values, width=cb_width, state="readonly")
    combo.pack(side="left", ipady=3)
    return combo


class RoomsFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db = db
        self._selected_photo = tk.StringVar()
        self._build_ui()

    def _build_ui(self):
        # ── Top Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_MAIN, padx=30, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ROOM MANAGEMENT", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")
        tk.Label(hdr, text="Rooms", font=FONT_HEADING, bg=BG_MAIN, fg=GOLD).pack(anchor="w")
        tk.Frame(self, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        # ── Sub-nav Buttons ──────────────────────────────────────────────────────
        nav = tk.Frame(self, bg=BG_SIDEBAR, pady=10)
        nav.pack(fill="x", padx=30, pady=(12, 0))

        self._sub_btns = {}
        subs = [
            ("➕  Add Room",    "add"),
            ("✏️  Update Room", "update"),
            ("🗑  Remove Room", "remove"),
            ("🔍  Search Room", "search"),
        ]
        for label, key in subs:
            btn = tk.Button(nav, text=label, font=FONT_LABEL,
                            bg=BG_CARD, fg=TEXT_MUTED, relief="flat",
                            activebackground=GOLD_DARK, activeforeground=CREAM,
                            cursor="hand2", padx=16, pady=8,
                            command=lambda k=key: self._show_sub(k))
            btn.pack(side="left", padx=4)
            self._sub_btns[key] = btn

        # ── Sub-frame Container ──────────────────────────────────────────────────
        self._container = tk.Frame(self, bg=BG_MAIN)
        self._container.pack(fill="both", expand=True, padx=30, pady=12)

        self._subs = {
            "add":    self._build_add_room(),
            "update": self._build_update_room(),
            "remove": self._build_remove_room(),
            "search": self._build_search_room(),
        }

        self._show_sub("add")

    # ─── Sub-panel switcher ──────────────────────────────────────────────────────
    def _show_sub(self, key):
        for k, frame in self._subs.items():
            frame.pack_forget()
        self._subs[key].pack(fill="both", expand=True)
        for k, btn in self._sub_btns.items():
            if k == key:
                btn.config(bg=GOLD, fg=BG_MAIN)
            else:
                btn.config(bg=BG_CARD, fg=TEXT_MUTED)

    # ─── ADD ROOM ────────────────────────────────────────────────────────────────
    def _build_add_room(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER_GOLD, highlightthickness=1)
        card.pack(fill="both", expand=True)

        # Card header
        ch = tk.Frame(card, bg=GOLD_SUBTLE, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="➕  Add New Room", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")

        body = tk.Frame(card, bg=BG_CARD, padx=30, pady=20)
        body.pack(fill="both", expand=True)

        # Two columns
        left  = tk.Frame(body, bg=BG_CARD)
        right = tk.Frame(body, bg=BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right.pack(side="left", fill="both", expand=True)

        self._add_room_id    = _lbl_entry(left,  "Room ID *")
        self._add_room_type  = _lbl_combo(left,  "Room Type *", ROOM_TYPES)
        self._add_price      = _lbl_entry(left,  "Price / Night (₹) *")
        self._add_capacity   = _lbl_entry(left,  "Capacity (persons) *")

        self._add_extra_ph   = _lbl_entry(right, "Extra Charge / Head (₹) *")
        self._add_floor      = _lbl_entry(right, "Floor Number")

        # Photo picker
        photo_row = tk.Frame(right, bg=BG_CARD)
        photo_row.pack(fill="x", pady=4)
        tk.Label(photo_row, text="Room Photo (filename):", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left")
        photo_ent = ttk.Entry(photo_row, textvariable=self._selected_photo, width=18)
        photo_ent.pack(side="left", ipady=3)
        ttk.Button(photo_row, text="Browse",
                   command=self._browse_photo_add).pack(side="left", padx=6)
        self._add_photo_var = self._selected_photo

        # Description
        desc_row = tk.Frame(right, bg=BG_CARD)
        desc_row.pack(fill="x", pady=4)
        tk.Label(desc_row, text="Description:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left", anchor="n")
        self._add_desc = tk.Text(desc_row, width=28, height=3,
                                  bg=BG_INPUT, fg=CREAM, insertbackground=GOLD,
                                  relief="flat", font=FONT_BODY, padx=6, pady=4)
        self._add_desc.pack(side="left")

        # Buttons
        tk.Frame(body, bg=GOLD_DARK, height=1).pack(fill="x", pady=(14, 10),
                                                     side="bottom")
        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(side="bottom", anchor="e", pady=4)
        ttk.Button(btn_row, text="Clear",    style="Info.TButton",
                   command=self._clear_add).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Add Room", command=self._do_add_room).pack(side="left")

        return frame

    def _browse_photo_add(self):
        img_dir = get_images_folder()
        os.makedirs(img_dir, exist_ok=True)
        path = filedialog.askopenfilename(
            initialdir=img_dir, title="Select Room Photo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if path:
            self._selected_photo.set(os.path.basename(path))

    def _clear_add(self):
        for w in [self._add_room_id, self._add_price,
                  self._add_capacity, self._add_extra_ph, self._add_floor]:
            w.delete(0, tk.END)
        self._add_room_type.set("")
        self._selected_photo.set("")
        self._add_desc.delete("1.0", tk.END)

    def _do_add_room(self):
        room_id    = self._add_room_id.get().strip().upper()
        room_type  = self._add_room_type.get()
        price      = self._add_price.get().strip()
        capacity   = self._add_capacity.get().strip()
        extra_ph   = self._add_extra_ph.get().strip()
        floor      = self._add_floor.get().strip() or "1"
        photo      = self._selected_photo.get().strip()
        desc       = self._add_desc.get("1.0", tk.END).strip()

        if not room_id or not room_type or not price or not capacity or not extra_ph:
            messagebox.showerror("Missing Fields",
                                 "Room ID, Type, Price, Capacity, and Extra/Head are required.")
            return
        try:
            price    = float(price)
            capacity = int(capacity)
            extra_ph = float(extra_ph)
            floor    = int(floor)
        except ValueError:
            messagebox.showerror("Invalid Input",
                                 "Price, Capacity, Extra/Head and Floor must be numbers.")
            return

        ok, msg = self.db.add_room(room_id, room_type, price, capacity,
                                   extra_ph, photo, desc, floor)
        if ok:
            messagebox.showinfo("Success", msg)
            self._clear_add()
        else:
            messagebox.showerror("Error", msg)

    # ─── UPDATE ROOM ─────────────────────────────────────────────────────────────
    def _build_update_room(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER_GOLD, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg=GOLD_SUBTLE, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="✏️  Update / Manage Room", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")

        # Search row
        search_area = tk.Frame(card, bg=BG_CARD, padx=30, pady=12)
        search_area.pack(fill="x")
        tk.Label(search_area, text="Enter Room ID to Load:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD).pack(side="left")
        self._upd_search_id = ttk.Entry(search_area, width=16)
        self._upd_search_id.pack(side="left", padx=8, ipady=3)
        ttk.Button(search_area, text="Load Room",
                   command=self._load_room_for_update).pack(side="left")

        tk.Frame(card, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        body = tk.Frame(card, bg=BG_CARD, padx=30, pady=16)
        body.pack(fill="both", expand=True)

        left  = tk.Frame(body, bg=BG_CARD)
        right = tk.Frame(body, bg=BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 20))
        right.pack(side="left", fill="both", expand=True)

        # read-only room id display
        rid_row = tk.Frame(left, bg=BG_CARD)
        rid_row.pack(fill="x", pady=4)
        tk.Label(rid_row, text="Room ID:", font=FONT_LABEL, bg=BG_CARD,
                 fg=GOLD, width=22, anchor="w").pack(side="left")
        self._upd_rid_var = tk.StringVar()
        tk.Label(rid_row, textvariable=self._upd_rid_var, font=("Segoe UI", 11, "bold"),
                 bg=BG_CARD, fg=CREAM).pack(side="left")

        self._upd_room_type  = _lbl_combo(left,  "Room Type *", ROOM_TYPES)
        self._upd_price      = _lbl_entry(left,  "Price / Night (₹) *")
        self._upd_capacity   = _lbl_entry(left,  "Capacity *")

        self._upd_extra_ph   = _lbl_entry(right, "Extra Charge / Head (₹) *")
        self._upd_floor      = _lbl_entry(right, "Floor Number")

        self._upd_photo_var = tk.StringVar()
        photo_row = tk.Frame(right, bg=BG_CARD)
        photo_row.pack(fill="x", pady=4)
        tk.Label(photo_row, text="Room Photo:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left")
        ttk.Entry(photo_row, textvariable=self._upd_photo_var, width=18).pack(side="left", ipady=3)
        ttk.Button(photo_row, text="Browse",
                   command=self._browse_photo_upd).pack(side="left", padx=6)

        desc_row = tk.Frame(right, bg=BG_CARD)
        desc_row.pack(fill="x", pady=4)
        tk.Label(desc_row, text="Description:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=22, anchor="w").pack(side="left", anchor="n")
        self._upd_desc = tk.Text(desc_row, width=28, height=3,
                                  bg=BG_INPUT, fg=CREAM, insertbackground=GOLD,
                                  relief="flat", font=FONT_BODY, padx=6, pady=4)
        self._upd_desc.pack(side="left")

        # Status
        self._upd_status = _lbl_combo(left, "Status",
                                       ["Available", "Booked", "Maintenance"])

        tk.Frame(body, bg=GOLD_DARK, height=1).pack(fill="x", pady=(14, 10),
                                                     side="bottom")
        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(side="bottom", anchor="e", pady=4)
        ttk.Button(btn_row, text="Clear Fields", style="Info.TButton",
                   command=self._clear_update).pack(side="left", padx=6)
        ttk.Button(btn_row, text="Update Room",
                   command=self._do_update_room).pack(side="left")

        return frame

    def _browse_photo_upd(self):
        img_dir = get_images_folder()
        os.makedirs(img_dir, exist_ok=True)
        path = filedialog.askopenfilename(
            initialdir=img_dir, title="Select Room Photo",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if path:
            self._upd_photo_var.set(os.path.basename(path))

    def _load_room_for_update(self):
        room_id = self._upd_search_id.get().strip().upper()
        if not room_id:
            messagebox.showwarning("Input Required", "Please enter a Room ID.")
            return
        room = self.db.get_room_by_id(room_id)
        if not room:
            messagebox.showerror("Not Found", f"Room '{room_id}' not found.")
            return
        self._upd_rid_var.set(room["room_id"])
        self._upd_room_type.set(room["room_type"])
        for ent, val in [
            (self._upd_price,    room["price"]),
            (self._upd_capacity, room["capacity"]),
            (self._upd_extra_ph, room["extra_per_head"]),
            (self._upd_floor,    room["floor"]),
        ]:
            ent.delete(0, tk.END)
            ent.insert(0, str(val))
        self._upd_photo_var.set(room["photo_path"] or "")
        self._upd_desc.delete("1.0", tk.END)
        self._upd_desc.insert("1.0", room["description"] or "")
        self._upd_status.set(room["status"])

    def _clear_update(self):
        self._upd_search_id.delete(0, tk.END)
        self._upd_rid_var.set("")
        self._upd_room_type.set("")
        for w in [self._upd_price, self._upd_capacity,
                  self._upd_extra_ph, self._upd_floor]:
            w.delete(0, tk.END)
        self._upd_photo_var.set("")
        self._upd_desc.delete("1.0", tk.END)
        self._upd_status.set("")

    def _do_update_room(self):
        room_id = self._upd_rid_var.get().strip()
        if not room_id:
            messagebox.showwarning("No Room Loaded", "Please load a room first.")
            return
        room_type = self._upd_room_type.get()
        price     = self._upd_price.get().strip()
        capacity  = self._upd_capacity.get().strip()
        extra_ph  = self._upd_extra_ph.get().strip()
        floor     = self._upd_floor.get().strip() or "1"
        photo     = self._upd_photo_var.get().strip()
        desc      = self._upd_desc.get("1.0", tk.END).strip()
        status    = self._upd_status.get()

        if not room_type or not price or not capacity or not extra_ph:
            messagebox.showerror("Missing Fields",
                                 "Type, Price, Capacity and Extra/Head are required.")
            return
        try:
            price    = float(price)
            capacity = int(capacity)
            extra_ph = float(extra_ph)
            floor    = int(floor)
        except ValueError:
            messagebox.showerror("Invalid Input", "Numeric fields must be valid numbers.")
            return

        ok, msg = self.db.update_room(room_id, room_type, price, capacity,
                                      extra_ph, photo, desc, floor)
        if ok and status:
            self.db.update_room_status(room_id, status)
        if ok:
            messagebox.showinfo("Success", msg)
            self._clear_update()
        else:
            messagebox.showerror("Error", msg)

    # ─── REMOVE ROOM ─────────────────────────────────────────────────────────────
    def _build_remove_room(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg="#1A0808", pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="🗑  Remove Room", font=FONT_SUBHEAD,
                 bg="#1A0808", fg=DANGER).pack(anchor="w")

        body = tk.Frame(card, bg=BG_CARD, padx=30, pady=20)
        body.pack(fill="both", expand=True)

        # Select room by combo
        row1 = tk.Frame(body, bg=BG_CARD)
        row1.pack(fill="x", pady=6)
        tk.Label(row1, text="Select Room ID:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD, width=20, anchor="w").pack(side="left")
        self._del_room_combo = ttk.Combobox(row1, width=24, state="readonly")
        self._del_room_combo.pack(side="left", ipady=3)
        ttk.Button(row1, text="Load Details",
                   command=self._load_room_for_delete).pack(side="left", padx=8)

        # Info display
        self._del_info_frame = tk.Frame(body, bg=BG_CARD)
        self._del_info_frame.pack(fill="x", pady=10)

        self._del_info_labels = {}
        fields = ["Room Type", "Price/Night", "Capacity", "Status"]
        for f in fields:
            r = tk.Frame(self._del_info_frame, bg=BG_CARD)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=f"{f}:", font=FONT_LABEL, bg=BG_CARD,
                     fg=TEXT_MUTED, width=18, anchor="w").pack(side="left")
            lbl = tk.Label(r, text="—", font=FONT_BODY, bg=BG_CARD, fg=CREAM)
            lbl.pack(side="left")
            self._del_info_labels[f] = lbl

        tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=12)

        # Warning
        tk.Label(body, text="⚠️  Deleting a room with active reservations is not allowed.",
                 font=FONT_SMALL, bg=BG_CARD, fg=WARNING).pack(anchor="w")

        btn_row = tk.Frame(body, bg=BG_CARD)
        btn_row.pack(anchor="w", pady=10)
        ttk.Button(btn_row, text="Clear", style="Info.TButton",
                   command=self._clear_delete).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text="Delete Room", style="Danger.TButton",
                   command=self._do_delete_room).pack(side="left")

        self._refresh_del_combo()
        return frame

    def _refresh_del_combo(self):
        rooms = self.db.get_all_rooms()
        self._del_room_combo["values"] = [r["room_id"] for r in rooms]

    def _load_room_for_delete(self):
        room_id = self._del_room_combo.get()
        if not room_id:
            messagebox.showwarning("Select Room", "Please select a room.")
            return
        room = self.db.get_room_by_id(room_id)
        if not room:
            messagebox.showerror("Not Found", "Room not found.")
            return
        self._del_info_labels["Room Type"].config(text=room["room_type"])
        self._del_info_labels["Price/Night"].config(
            text=f"\u20b9{float(room['price']):,.2f}")
        self._del_info_labels["Capacity"].config(text=str(room["capacity"]))
        self._del_info_labels["Status"].config(text=room["status"])

    def _clear_delete(self):
        self._del_room_combo.set("")
        for lbl in self._del_info_labels.values():
            lbl.config(text="—")

    def _do_delete_room(self):
        room_id = self._del_room_combo.get()
        if not room_id:
            messagebox.showwarning("Select Room", "Please select a room to delete.")
            return
        if not messagebox.askyesno("Confirm Delete",
                                   f"Are you sure you want to delete Room '{room_id}'?\nThis cannot be undone."):
            return
        ok, msg = self.db.delete_room(room_id)
        if ok:
            messagebox.showinfo("Deleted", msg)
            self._clear_delete()
            self._refresh_del_combo()
        else:
            messagebox.showerror("Error", msg)

    # ─── SEARCH ROOM ─────────────────────────────────────────────────────────────
    def _build_search_room(self):
        frame = tk.Frame(self._container, bg=BG_MAIN)

        card = tk.Frame(frame, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True)

        ch = tk.Frame(card, bg=BG_SIDEBAR, pady=10, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text="🔍  Search Rooms", font=FONT_SUBHEAD,
                 bg=BG_SIDEBAR, fg=GOLD).pack(anchor="w")

        srow = tk.Frame(card, bg=BG_CARD, padx=20, pady=12)
        srow.pack(fill="x")
        tk.Label(srow, text="Search:", font=FONT_LABEL,
                 bg=BG_CARD, fg=GOLD).pack(side="left")
        self._search_var = tk.StringVar()
        ent = ttk.Entry(srow, textvariable=self._search_var, width=32)
        ent.pack(side="left", padx=8, ipady=3)
        ent.bind("<Return>", lambda e: self._do_search())
        ttk.Button(srow, text="Search", command=self._do_search).pack(side="left")
        ttk.Button(srow, text="Show All", style="Info.TButton",
                   command=self._show_all_rooms).pack(side="left", padx=8)

        # Results table
        tbl_frame = tk.Frame(card, bg=BG_CARD)
        tbl_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        cols = ("Room ID", "Type", "Price/Night", "Capacity",
                "Extra/Head", "Floor", "Status")
        self._search_tree = ttk.Treeview(tbl_frame, columns=cols,
                                          show="headings", height=14)
        widths = [80, 160, 110, 90, 100, 70, 100]
        for col, w in zip(cols, widths):
            self._search_tree.heading(col, text=col)
            self._search_tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tbl_frame, orient="vertical",
                             command=self._search_tree.yview)
        self._search_tree.configure(yscrollcommand=vsb.set)
        self._search_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._search_tree.tag_configure("odd", background=BG_ROW_ALT)

        self._show_all_rooms()
        return frame

    def _do_search(self):
        q = self._search_var.get().strip()
        if not q:
            self._show_all_rooms()
            return
        rooms = self.db.search_rooms(q)
        self._populate_search_tree(rooms)

    def _show_all_rooms(self):
        rooms = self.db.get_all_rooms()
        self._populate_search_tree(rooms)

    def _populate_search_tree(self, rooms):
        for item in self._search_tree.get_children():
            self._search_tree.delete(item)
        for i, r in enumerate(rooms):
            tag = "odd" if i % 2 else ""
            self._search_tree.insert("", "end", tags=(tag,), values=(
                r["room_id"], r["room_type"],
                f"\u20b9{float(r['price']):,.2f}",
                r["capacity"],
                f"\u20b9{float(r['extra_per_head']):,.2f}",
                r["floor"], r["status"]
            ))

    def refresh(self):
        self._refresh_del_combo()
        self._show_all_rooms()
