
# styles.py — The Veloria Grand Hotel Management System
import tkinter as tk
from tkinter import ttk

# ─── Color Palette ─────────────────────────────────────────────────────────────
BG_MAIN        = "#0B0C1A"
BG_SIDEBAR     = "#07080F"
BG_CARD        = "#11122A"
BG_CARD_HOVER  = "#171935"
BG_INPUT       = "#0D0E1F"
BG_ROW_ALT     = "#0E0F22"

GOLD           = "#C8A951"
GOLD_LIGHT     = "#E8C97A"
GOLD_DARK      = "#9A7A30"
GOLD_SUBTLE    = "#1E1A08"
GOLD_BORDER    = "#3A2E10"

CREAM          = "#F5EDE0"
TEXT_LIGHT     = "#B8AE98"
TEXT_MUTED     = "#5A5A70"

BORDER         = "#1E1F38"
BORDER_GOLD    = "#3A2E10"

SUCCESS        = "#27AE60"
SUCCESS_BG     = "#081A10"
WARNING        = "#F39C12"
WARNING_BG     = "#1A1008"
DANGER         = "#C0392B"
DANGER_BG      = "#1A0808"
INFO           = "#2980B9"
INFO_BG        = "#08101A"

BLUE_ACCENT    = "#5DADE2"
PURPLE_ACCENT  = "#9B59B6"
TEAL_ACCENT    = "#1ABC9C"

# ─── Fonts ─────────────────────────────────────────────────────────────────────
FONT_BRAND     = ("Georgia", 24, "bold")
FONT_HEADING   = ("Georgia", 16, "bold")
FONT_SUBHEAD   = ("Georgia", 13, "bold")
FONT_LABEL     = ("Segoe UI", 10, "bold")
FONT_BODY      = ("Segoe UI", 10)
FONT_SMALL     = ("Segoe UI", 9)
FONT_MONO      = ("Consolas", 10)
FONT_BIG_NUM   = ("Segoe UI", 26, "bold")

# ─── Dimensions ────────────────────────────────────────────────────────────────
SIDEBAR_WIDTH  = 215
TOPBAR_HEIGHT  = 80
PADDING        = 20
CARD_PAD       = 16

# ─── Apply Theme ───────────────────────────────────────────────────────────────
def apply_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG_MAIN, foreground=CREAM,
                    font=FONT_BODY, borderwidth=0, relief="flat")

    style.configure("TFrame", background=BG_MAIN)
    style.configure("Card.TFrame", background=BG_CARD)
    style.configure("Sidebar.TFrame", background=BG_SIDEBAR)
    style.configure("Input.TFrame", background=BG_INPUT)

    style.configure("TLabel", background=BG_MAIN, foreground=CREAM, font=FONT_BODY)
    style.configure("Heading.TLabel", background=BG_MAIN, foreground=GOLD, font=FONT_HEADING)
    style.configure("Sub.TLabel", background=BG_MAIN, foreground=CREAM, font=FONT_SUBHEAD)
    style.configure("Card.TLabel", background=BG_CARD, foreground=CREAM, font=FONT_BODY)
    style.configure("Gold.TLabel", background=BG_MAIN, foreground=GOLD, font=FONT_LABEL)
    style.configure("Muted.TLabel", background=BG_MAIN, foreground=TEXT_MUTED, font=FONT_SMALL)
    style.configure("CardHead.TLabel", background=BG_CARD, foreground=GOLD, font=FONT_SUBHEAD)

    style.configure("TButton", background=GOLD, foreground=BG_MAIN,
                    font=("Segoe UI", 10, "bold"), padding=(14, 7), relief="flat", borderwidth=0)
    style.map("TButton",
              background=[("active", GOLD_LIGHT), ("pressed", GOLD_DARK)],
              foreground=[("active", BG_MAIN)])

    style.configure("Danger.TButton", background=DANGER, foreground=CREAM,
                    font=("Segoe UI", 10, "bold"), padding=(14, 7))
    style.map("Danger.TButton",
              background=[("active", "#E74C3C"), ("pressed", "#7B241C")])

    style.configure("Success.TButton", background=SUCCESS, foreground=CREAM,
                    font=("Segoe UI", 10, "bold"), padding=(14, 7))
    style.map("Success.TButton",
              background=[("active", "#2ECC71"), ("pressed", "#1A7A42")])

    style.configure("Info.TButton", background=INFO, foreground=CREAM,
                    font=("Segoe UI", 10, "bold"), padding=(14, 7))
    style.map("Info.TButton",
              background=[("active", "#3498DB"), ("pressed", "#1A5276")])

    style.configure("TEntry", fieldbackground=BG_INPUT, foreground=CREAM,
                    insertcolor=GOLD, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER,
                    borderwidth=1, relief="solid", padding=(8, 6))
    style.map("TEntry",
              bordercolor=[("focus", GOLD)],
              lightcolor=[("focus", GOLD)],
              darkcolor=[("focus", GOLD)])

    style.configure("TCombobox", fieldbackground=BG_INPUT, background=BG_INPUT,
                    foreground=CREAM, selectbackground=GOLD_DARK, selectforeground=CREAM,
                    bordercolor=BORDER, arrowcolor=GOLD, padding=(8, 6))
    style.map("TCombobox",
              fieldbackground=[("readonly", BG_INPUT)],
              foreground=[("readonly", CREAM)],
              bordercolor=[("focus", GOLD)],
              arrowcolor=[("active", GOLD_LIGHT)])

    style.configure("Treeview", background=BG_CARD, foreground=CREAM,
                    fieldbackground=BG_CARD, rowheight=30, font=FONT_BODY,
                    borderwidth=0, relief="flat")
    style.configure("Treeview.Heading", background=BG_SIDEBAR, foreground=GOLD,
                    font=("Segoe UI", 10, "bold"), borderwidth=0, relief="flat",
                    padding=(6, 8))
    style.map("Treeview",
              background=[("selected", GOLD_DARK)],
              foreground=[("selected", CREAM)])
    style.map("Treeview.Heading",
              background=[("active", BORDER)])

    style.configure("TScrollbar", background=BORDER, troughcolor=BG_SIDEBAR,
                    arrowcolor=GOLD, borderwidth=0, relief="flat", width=10)
    style.map("TScrollbar", background=[("active", GOLD_DARK)])

    style.configure("TNotebook", background=BG_MAIN, borderwidth=0, tabmargins=[0, 0, 0, 0])
    style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_MUTED,
                    font=("Segoe UI", 10, "bold"), padding=(18, 9), borderwidth=0)
    style.map("TNotebook.Tab",
              background=[("selected", BG_SIDEBAR)],
              foreground=[("selected", GOLD)],
              expand=[("selected", [1, 1, 1, 0])])

    style.configure("TCheckbutton", background=BG_MAIN, foreground=CREAM, font=FONT_BODY)
    style.map("TCheckbutton",
              background=[("active", BG_MAIN)],
              foreground=[("active", GOLD)])

    style.configure("TSeparator", background=BORDER)
    style.configure("Gold.TSeparator", background=GOLD_DARK)

    return style


def make_scrollable(parent, bg=None):
    """Create a scrollable frame and return (canvas, inner_frame)."""
    if bg is None:
        bg = BG_MAIN
    canvas = tk.Canvas(parent, bg=bg, highlightthickness=0)
    vsb = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=bg)
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=vsb.set)
    canvas.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    def _on_mousewheel(e):
        try:
            canvas.yview_scroll(-1 * (e.delta // 120), "units")
        except Exception:
            pass   # canvas already destroyed (e.g. dialog closed)

    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # Unbind global handler when this canvas is destroyed (dialog closed, etc.)
    canvas.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
    return canvas, inner


def gold_separator(parent, padx=0, pady=8):
    tk.Frame(parent, bg=GOLD_DARK, height=1).pack(fill="x", padx=padx, pady=pady)


def section_header(parent, title, subtitle=None, bg=None):
    if bg is None:
        bg = BG_MAIN
    f = tk.Frame(parent, bg=bg)
    f.pack(fill="x", pady=(6, 4))
    tk.Label(f, text=title, font=FONT_HEADING, bg=bg, fg=GOLD).pack(anchor="w")
    if subtitle:
        tk.Label(f, text=subtitle, font=FONT_SMALL, bg=bg, fg=TEXT_MUTED).pack(anchor="w")
    return f
