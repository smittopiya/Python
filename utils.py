
# utils.py -- The Veloria Grand Hotel Management System
import re
import os
from datetime import datetime

# --- ID Proof Validation Rules -------------------------------------------------
ID_PROOF_TYPES = [
    "Aadhaar Card", "PAN Card", "Passport", "Driving Licence", "Voter ID",
]

ID_PROOF_RULES = {
    "Aadhaar Card":   {"pattern": r"^\d{12}$",                 "desc": "12 digits only (e.g. 123456789012)"},
    "PAN Card":       {"pattern": r"^[A-Z]{5}[0-9]{4}[A-Z]$", "desc": "5 letters+4 digits+1 letter (e.g. ABCDE1234F)"},
    "Passport":       {"pattern": r"^[A-Z]\d{7}$",             "desc": "1 letter + 7 digits (e.g. A1234567)"},
    "Driving Licence":{"pattern": r"^[A-Z]{2}\d{13}$",         "desc": "2 letters + 13 digits"},
    "Voter ID":       {"pattern": r"^[A-Z]{3}\d{7}$",          "desc": "3 letters + 7 digits"},
}

def validate_id_proof(id_type, id_number):
    if not id_type or not id_number:
        return False, "ID proof type and number are required."
    rule = ID_PROOF_RULES.get(id_type)
    if not rule:
        return True, ""
    if not re.match(rule["pattern"], id_number.strip().upper()):
        return False, f"{id_type} format: {rule['desc']}"
    return True, ""

def validate_phone(phone):
    if not re.match(r"^\d{10}$", phone.strip()):
        return False, "Contact must be exactly 10 digits."
    return True, ""

def validate_nonempty(fields: dict):
    for label, val in fields.items():
        if not str(val).strip():
            return False, f"'{label}' is required."
    return True, ""

def days_between(d1: str, d2: str, fmt="%Y-%m-%d") -> int:
    a = datetime.strptime(d1, fmt)
    b = datetime.strptime(d2, fmt)
    return max((b - a).days, 1)

def fmt_currency(amount) -> str:
    try:
        return f"Rs.{float(amount):,.2f}"
    except Exception:
        return "Rs.0.00"

def generate_res_id():
    return f"RES{datetime.now().strftime('%Y%m%d%H%M%S')}"

def generate_invoice_no():
    return f"INV-VG-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def get_images_folder():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images")

def get_invoices_folder():
    folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Invoices")
    os.makedirs(folder, exist_ok=True)
    return folder

def get_room_image(photo_path):
    if not photo_path:
        return None
    full = os.path.join(get_images_folder(), photo_path)
    return full if os.path.exists(full) else None


# ==============================================================================
# LUXURY SINGLE-PAGE PDF INVOICE  --  The Veloria Grand
# ==============================================================================
def generate_pdf_invoice(res_detail: dict, output_path: str) -> str:
    """
    Single-page luxury invoice. First-design visual style with proper alignment.
    All text is Latin-1 safe for Helvetica font compatibility.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise ImportError("fpdf2 is not installed. Run: pip install fpdf2")

    # ── Colour palette ──────────────────────────────────────────────────────────
    DARK    = (11,  12,  26)
    DARK2   = (20,  22,  48)
    GOLD    = (200, 169, 81)
    GOLD_LT = (232, 201, 122)
    GOLD_DK = (154, 122, 48)
    CREAM   = (245, 237, 224)
    WHITE   = (255, 255, 255)
    GREY1   = (246, 245, 250)
    GREY2   = (238, 237, 245)
    MUTED   = (110, 108, 130)
    SUCCESS = (39,  174, 96)
    DANGER  = (192, 57,  43)

    # ── Layout grid (mm) ────────────────────────────────────────────────────────
    # Page: A4 = 210 x 297mm
    # Border: 5mm from edge → content from x=10 to x=200, width=190
    PL      = 10        # page left edge of content
    PR      = 200       # page right edge of content
    PW      = 190       # content width
    PAD     = 3.5       # standard inner padding

    # Bill table columns (must sum to PW=190)
    C1_X    = PL            # description X
    C1_W    = 110           # description width
    C2_X    = C1_X + C1_W  # qty X  (= 120)
    C2_W    = 34            # qty width
    C3_X    = C2_X + C2_W  # amount X  (= 154)
    C3_W    = PW - C1_W - C2_W  # amount width (= 46)

    # Two info cards (gap=6mm between them)
    CL_X    = PL            # left card X
    CL_W    = 92            # left card width
    CR_X    = PL + CL_W + 6 # right card X  (= 108)
    CR_W    = PW - CL_W - 6 # right card width (= 92)

    # Meta bar: 4 equal columns
    M_COL   = PW / 4        # 47.5mm each

    # Stats bar: 5 equal columns
    S_COL   = PW / 5        # 38mm each

    # ── Latin-1 safe ────────────────────────────────────────────────────────────
    def safe(text):
        text = str(text)
        for s, d in {'\u2014':'-','\u2013':'-','\u2019':"'",
                     '\u201c':'"','\u201d':'"','\u2022':'-',
                     '\u2026':'...','\u20b9':'Rs.','\u2605':'*'}.items():
            text = text.replace(s, d)
        return text.encode('latin-1', errors='replace').decode('latin-1')

    # ── Custom PDF ───────────────────────────────────────────────────────────────
    class PDF(FPDF):

        def double_rule(self):
            """Two thin gold horizontal rules across the content width."""
            y = self.get_y()
            self.set_draw_color(*GOLD_DK)
            self.set_line_width(0.18)
            self.line(PL, y,       PR, y)
            self.line(PL, y + 1.2, PR, y + 1.2)

        def section_head(self, title, rh=7.5):
            """Dark navy full-width ribbon with gold left accent and title."""
            y = self.get_y()
            # Dark fill
            self.set_fill_color(*DARK)
            self.rect(PL, y, PW, rh, "F")
            # Gold accent bar
            self.set_fill_color(*GOLD)
            self.rect(PL, y, 3, rh, "F")
            # Title text
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*GOLD_LT)
            self.set_xy(PL + 3 + PAD, y + (rh - 4) / 2)
            self.cell(PW - 10, 4, safe(title.upper()), ln=True)
            self.ln(1.5)

        def info_card(self, x, y, w, rows, header):
            """
            Styled info card at position (x,y) with width w.
            Returns card height drawn.
            HDR bar + label/value rows, gold left accent.
            """
            HDR_H  = 7.5
            ROW_H  = 4.8
            LBL_W  = 22
            ACC    = 3.0
            h      = HDR_H + len(rows) * ROW_H + 3

            # Card background
            self.set_fill_color(*GREY1)
            self.rect(x, y, w, h, "F")
            # Gold left accent (full height)
            self.set_fill_color(*GOLD)
            self.rect(x, y, ACC, h, "F")
            # Header bar
            self.set_fill_color(*DARK2)
            self.rect(x + ACC, y, w - ACC, HDR_H, "F")
            # Header text
            self.set_font("Helvetica", "B", 7.5)
            self.set_text_color(*GOLD_LT)
            self.set_xy(x + ACC + PAD, y + (HDR_H - 4) / 2)
            self.cell(w - ACC - PAD, 4, safe(header.upper()), ln=False)

            # Rows
            ry = y + HDR_H + 1.5
            for lk, lv in rows:
                self.set_font("Helvetica", "B", 6.5)
                self.set_text_color(*MUTED)
                self.set_xy(x + ACC + PAD, ry)
                self.cell(LBL_W, ROW_H, safe(str(lk) + ":"), ln=False)
                self.set_font("Helvetica", "", 7.5)
                self.set_text_color(*DARK)
                self.set_x(x + ACC + PAD + LBL_W)
                self.cell(w - ACC - PAD - LBL_W - 1, ROW_H, safe(str(lv)[:28]), ln=False)
                ry += ROW_H

            return h

    # ── Instantiate ─────────────────────────────────────────────────────────────
    pdf = PDF()
    pdf.set_margins(PL, 10, PL)
    pdf.add_page()
    pdf.set_auto_page_break(auto=False)

    # ── Extract data ─────────────────────────────────────────────────────────────
    inv_no       = generate_invoice_no()
    date_str     = datetime.now().strftime("%d %b %Y, %I:%M %p")
    status       = safe(res_detail.get("payment_status", "Pending") or "Pending")
    nights       = int(res_detail.get("nights",         1)  or 1)
    room_price   = float(res_detail.get("room_price",   0)  or 0)
    extra_charge = float(res_detail.get("extra_charge", 0)  or 0)
    extra_p      = int(res_detail.get("extra_persons",  0)  or 0)
    meal_price   = float(res_detail.get("meal_price",   0)  or 0)
    meal_qty     = int(res_detail.get("meal_quantity",  1)  or 1)
    meal_name    = safe(res_detail.get("meal_plan", "No Meals") or "No Meals")
    badge_col    = SUCCESS if status == "Paid" else (DANGER if status == "Cancelled" else MUTED)

    # ==========================================================================
    # A. PAGE BORDER  -- gold double rectangle frame
    # ==========================================================================
    pdf.set_draw_color(*GOLD_DK)
    pdf.set_line_width(0.9)
    pdf.rect(5, 5, 200, 287)
    pdf.set_line_width(0.2)
    pdf.rect(7, 7, 196, 283)

    # ==========================================================================
    # B. HEADER  (y=5..47, h=42mm)
    # ==========================================================================
    HDR_Y, HDR_H = 5, 44
    HDR_END      = HDR_Y + HDR_H

    # Deep navy fill
    pdf.set_fill_color(*DARK)
    pdf.rect(5, HDR_Y, 200, HDR_H, "F")
    # Top gold stripe
    pdf.set_fill_color(*GOLD_DK)
    pdf.rect(5, HDR_Y, 200, 2, "F")

    # Star rating  *  *  *  *  *  *  *
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*GOLD_DK)
    pdf.set_y(HDR_Y + 3.5)
    pdf.cell(0, 4.5, "*   *   *   *   *   *   *", align="C", ln=True)

    # Hotel name
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(*GOLD_LT)
    pdf.set_y(HDR_Y + 9)
    pdf.cell(0, 10, "THE  VELORIA  GRAND", align="C", ln=True)

    # Tagline
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*CREAM)
    pdf.cell(0, 5, "Hotel & Resort  -  Where Luxury Meets Elegance", align="C", ln=True)

    # Address / contact
    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(175, 165, 145)
    pdf.cell(0, 4,
             "123 Luxury Boulevard, Mumbai 400001  |  +91-22-12345678  |  reservations@veloriagrade.com",
             align="C", ln=True)

    # Document label bar (centred)
    pdf.ln(2)
    LBL_W = 140
    LBL_X = (210 - LBL_W) / 2
    pdf.set_x(LBL_X)
    pdf.set_fill_color(*GOLD_DK)
    pdf.set_font("Helvetica", "B", 8.5)
    pdf.set_text_color(*DARK)
    pdf.cell(LBL_W, 7, "OFFICIAL INVOICE  /  BILL OF CHARGES", align="C", fill=True, ln=True)

    # Bottom header gold stripe
    pdf.set_fill_color(*GOLD_DK)
    pdf.rect(5, HDR_END, 200, 1.5, "F")

    # ==========================================================================
    # C. META BAR  (y=HDR_END+3, h=13mm)
    # ==========================================================================
    pdf.set_y(HDR_END + 3)
    META_Y = pdf.get_y()
    META_H = 13

    pdf.set_fill_color(*GREY1)
    pdf.rect(PL, META_Y, PW, META_H, "F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(PL, META_Y, 3, META_H, "F")

    # Label row
    meta_labels = ["INVOICE NUMBER", "ISSUED ON", "RESERVATION ID", "PAYMENT STATUS"]
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(*MUTED)
    for i, lbl in enumerate(meta_labels):
        pdf.set_xy(PL + 3 + PAD + i * M_COL, META_Y + 1.5)
        pdf.cell(M_COL, 3.5, lbl, ln=False)

    # Value row
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK)
    for i, val in enumerate([safe(inv_no), safe(date_str),
                              safe(res_detail.get("reservation_id", ""))]):
        pdf.set_xy(PL + 3 + PAD + i * M_COL, META_Y + 6.5)
        pdf.cell(M_COL, 5, val, ln=False)

    # Status badge (4th column)
    BDG_X = PL + 3 + PAD + 3 * M_COL
    BDG_W = M_COL - PAD - 3
    pdf.set_xy(BDG_X, META_Y + 6)
    pdf.set_fill_color(*badge_col)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(BDG_W, 6.5, f"  {status.upper()}  ", align="C", fill=True, ln=True)

    pdf.set_y(META_Y + META_H + 3)
    pdf.double_rule()
    pdf.ln(3.5)

    # ==========================================================================
    # D. GUEST + ROOM INFO CARDS  (side by side, equal height)
    # ==========================================================================
    guest_rows = [
        ("Name",       res_detail.get("client_name", "")),
        ("Contact",    res_detail.get("contact", "")),
        ("City/State", f"{res_detail.get('city','')} / {res_detail.get('state','')}"),
        ("Country",    res_detail.get("country", "India")),
        ("ID Proof",   f"{res_detail.get('id_proof_type','')} : {res_detail.get('id_proof_number','')}"),
    ]
    room_rows = [
        ("Room No.",   res_detail.get("room_id", "")),
        ("Type",       res_detail.get("room_type", "")),
        ("Check-In",   res_detail.get("check_in", "")),
        ("Check-Out",  res_detail.get("check_out", "")),
        ("Guests",     f"{res_detail.get('adults',1)} Adults | {res_detail.get('children',0)} Children"),
    ]

    CY = pdf.get_y()
    h_left  = pdf.info_card(CL_X, CY, CL_W, guest_rows, "Guest Information")
    h_right = pdf.info_card(CR_X, CY, CR_W, room_rows,  "Room & Stay Details")
    pdf.set_y(CY + max(h_left, h_right) + 3)

    pdf.double_rule()
    pdf.ln(3.5)

    # ==========================================================================
    # E. STAY SUMMARY BAR  (5 stats, full-width, h=12mm)
    # ==========================================================================
    SB_Y, SB_H = pdf.get_y(), 12
    pdf.set_fill_color(*DARK)
    pdf.rect(PL, SB_Y, PW, SB_H, "F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(PL, SB_Y, 3, SB_H, "F")

    stats = [
        ("DURATION",   f"{nights} Night{'s' if nights != 1 else ''}"),
        ("RATE/NIGHT", f"INR {room_price:,.0f}"),
        ("ADULTS",     str(res_detail.get("adults", 1))),
        ("CHILDREN",   str(res_detail.get("children", 0))),
        ("MEAL PLAN",  meal_name[:15]),
    ]
    for i, (k, v) in enumerate(stats):
        sx = PL + 3 + PAD + i * S_COL
        pdf.set_xy(sx, SB_Y + 1.5)
        pdf.set_font("Helvetica", "B", 6)
        pdf.set_text_color(*GOLD_DK)
        pdf.cell(S_COL - 2, 3.5, k, ln=False)
        pdf.set_xy(sx, SB_Y + 5.5)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*CREAM)
        pdf.cell(S_COL - 2, 5, safe(v), ln=False)

    pdf.set_y(SB_Y + SB_H + 3.5)

    # ==========================================================================
    # F. ITEMISED BILL TABLE
    # ==========================================================================
    pdf.section_head("Itemised Bill of Charges")

    # Table column header
    TH_Y, TH_H = pdf.get_y(), 7
    pdf.set_fill_color(*DARK2)
    pdf.rect(PL, TH_Y, PW, TH_H, "F")
    pdf.set_fill_color(*GOLD)
    pdf.rect(PL, TH_Y, 3, TH_H, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*GOLD_LT)
    VCTR = (TH_H - 4) / 2   # vertical centre offset
    pdf.set_xy(C1_X + 3 + PAD, TH_Y + VCTR)
    pdf.cell(C1_W - 3 - PAD - 1, 4, "DESCRIPTION",  ln=False)
    pdf.set_x(C2_X)
    pdf.cell(C2_W, TH_H, "QTY / UNIT",   align="C", ln=False)
    pdf.set_x(C3_X)
    pdf.cell(C3_W, TH_H, "AMOUNT (INR)", align="R", ln=True)
    pdf.ln(0.5)

    # Build bill rows
    rows = []
    rows.append((
        f"Room Accommodation - {safe(res_detail.get('room_type',''))}",
        f"{nights} night(s) @ INR {room_price:,.0f}",
        room_price * nights,
    ))
    if extra_p > 0:
        rows.append((
            f"Extra Person Surcharge ({extra_p} pax)",
            f"{nights} night(s)",
            extra_charge,
        ))
    for addon in (res_detail.get("add_ons", "") or "").split("|"):
        parts = addon.strip().split(":")
        if len(parts) == 2:
            try:
                rows.append((f"Add-On Service - {safe(parts[0].strip())}", "1 x", float(parts[1])))
            except Exception:
                pass
    if meal_name != "No Meals" and meal_price > 0:
        rows.append((f"Meal Plan - {meal_name}", f"{meal_qty} pax", meal_price))

    sub_total = sum(r[2] for r in rows)
    gst       = round(sub_total * 0.12, 2)
    grand     = sub_total + gst

    ROW_H = 6.5
    alt   = False
    for desc, qty, amt in rows:
        bg  = GREY1 if alt else WHITE
        alt = not alt
        yy  = pdf.get_y()
        pdf.set_fill_color(*bg)
        pdf.rect(PL, yy, PW, ROW_H, "F")
        pdf.set_fill_color(*GOLD_DK)
        pdf.rect(PL, yy, 1.5, ROW_H, "F")
        # Description
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(30, 30, 45)
        pdf.set_xy(C1_X + 1.5 + PAD, yy + (ROW_H - 4) / 2)
        pdf.cell(C1_W - 1.5 - PAD - 1, 4, safe(desc), ln=False)
        # Qty
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(*MUTED)
        pdf.set_x(C2_X)
        pdf.cell(C2_W, ROW_H, safe(qty), align="C", ln=False)
        # Amount
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*DARK)
        pdf.set_x(C3_X)
        pdf.cell(C3_W, ROW_H, f"{amt:,.2f}", align="R", ln=True)

    # Gold separator line
    pdf.set_draw_color(*GOLD_DK)
    pdf.set_line_width(0.25)
    pdf.line(PL, pdf.get_y(), PR, pdf.get_y())
    pdf.ln(0.5)

    # Sub-total
    ST_H = 6.5
    yy   = pdf.get_y()
    pdf.set_fill_color(*GREY2)
    pdf.rect(PL, yy, PW, ST_H, "F")
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*DARK)
    pdf.set_xy(C1_X + PAD + 4, yy + (ST_H - 4) / 2)
    pdf.cell(C1_W + C2_W - PAD - 4 - 2, 4, "Sub-Total (before tax)", ln=False)
    pdf.set_x(C3_X)
    pdf.cell(C3_W, ST_H, f"{sub_total:,.2f}", align="R", ln=True)

    # GST
    yy = pdf.get_y()
    pdf.set_fill_color(*GREY1)
    pdf.rect(PL, yy, PW, ST_H, "F")
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(C1_X + PAD + 4, yy + (ST_H - 4) / 2)
    pdf.cell(C1_W + C2_W - PAD - 4 - 2, 4, "GST / Service Tax  (12%)", ln=False)
    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*DARK)
    pdf.set_x(C3_X)
    pdf.cell(C3_W, ST_H, f"{gst:,.2f}", align="R", ln=True)
    pdf.ln(1.5)

    # Grand Total -- full-width dark bar with gold side pillars
    GT_Y, GT_H = pdf.get_y(), 13
    PILLAR_W   = 4
    pdf.set_fill_color(*DARK)
    pdf.rect(PL, GT_Y, PW, GT_H, "F")
    # Gold side pillars
    pdf.set_fill_color(*GOLD)
    pdf.rect(PL,           GT_Y, PILLAR_W, GT_H, "F")
    pdf.rect(PR - PILLAR_W, GT_Y, PILLAR_W, GT_H, "F")
    # Top & bottom gold rule lines
    pdf.set_fill_color(*GOLD_DK)
    pdf.rect(PL, GT_Y,             PW, 1,   "F")
    pdf.rect(PL, GT_Y + GT_H - 1,  PW, 1,   "F")
    # Label
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*GOLD_LT)
    pdf.set_xy(PL + PILLAR_W + PAD, GT_Y + (GT_H - 6) / 2)
    pdf.cell(C1_W + C2_W - PILLAR_W - PAD, 6, "GRAND TOTAL  (Incl. GST @ 12%)", ln=False)
    # Amount
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_x(C3_X)
    pdf.cell(C3_W - PILLAR_W - 1, GT_H, f"INR  {grand:,.2f}", align="R", ln=True)

    pdf.ln(4)

    # ==========================================================================
    # G. STATUS STAMP + NOTES  (side-by-side, same row height)
    # ==========================================================================
    SN_Y    = pdf.get_y()
    SN_H    = 14
    STAMP_W = 52
    NOTES_W = PW - STAMP_W - 5

    # Notes card
    notes = safe((res_detail.get("notes") or "").strip())
    pdf.set_fill_color(*GREY1)
    pdf.rect(PL, SN_Y, NOTES_W, SN_H, "F")
    pdf.set_fill_color(*GOLD_DK)
    pdf.rect(PL, SN_Y, 2.5, SN_H, "F")
    pdf.set_font("Helvetica", "B", 6.5)
    pdf.set_text_color(*MUTED)
    pdf.set_xy(PL + 2.5 + PAD, SN_Y + 2)
    pdf.cell(NOTES_W - 6, 3.5, "SPECIAL REQUESTS & NOTES", ln=False)
    pdf.set_font("Helvetica", "I", 7.5)
    pdf.set_text_color(50, 50, 70)
    pdf.set_xy(PL + 2.5 + PAD, SN_Y + 7)
    note_text = (notes[:92] + "...") if len(notes) > 92 else (notes if notes else "None")
    pdf.cell(NOTES_W - 6, 4.5, note_text, ln=False)

    # Status stamp (double-bordered box, right-aligned)
    STAMP_X   = PL + NOTES_W + 5
    stamp_col = SUCCESS if status == "Paid" else (DANGER if status == "Cancelled" else MUTED)
    pdf.set_draw_color(*stamp_col)
    pdf.set_line_width(1.2)
    pdf.rect(STAMP_X, SN_Y, STAMP_W, SN_H, "D")
    pdf.set_line_width(0.35)
    pdf.rect(STAMP_X + 2, SN_Y + 2, STAMP_W - 4, SN_H - 4, "D")
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(*stamp_col)
    pdf.set_xy(STAMP_X, SN_Y + (SN_H - 6) / 2)
    pdf.cell(STAMP_W, 6, status.upper(), align="C", ln=False)

    pdf.set_y(SN_Y + SN_H + 3.5)

    # ==========================================================================
    # H. TERMS & CONDITIONS  (alternating full-width stripes, 2-col for space)
    # ==========================================================================
    pdf.section_head("Terms & Conditions")

    terms = [
        "1. Check-in: 2:00 PM  |  Check-out: 12:00 Noon",
        "5. Cancellations within 24 hrs of check-in are non-refundable",
        "2. Late checkout subject to availability; extra charges may apply",
        "6. All prices are in INR inclusive of applicable government taxes",
        "3. Pets are not permitted anywhere on the hotel premises",
        "7. Smoking is prohibited indoors; outdoor zones are available",
        "4. Hotel not liable for loss of valuables; please use the in-room safe",
        "8. Outside food & beverages are not permitted in the hotel",
    ]

    T_ROW_H  = 5.2
    T_COL_W  = (PW - 4) / 2     # 93mm each column
    T_COL2_X = PL + T_COL_W + 4
    T_Y      = pdf.get_y()
    ACC      = 1.5

    for i, t in enumerate(terms):
        row  = i // 2
        col  = i %  2
        tx   = PL if col == 0 else T_COL2_X
        yy   = T_Y + row * T_ROW_H
        bg   = GREY1 if row % 2 == 0 else WHITE
        pdf.set_fill_color(*bg)
        pdf.rect(tx, yy, T_COL_W, T_ROW_H, "F")
        pdf.set_fill_color(*GOLD_DK)
        pdf.rect(tx, yy, ACC, T_ROW_H, "F")
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_text_color(55, 55, 72)
        pdf.set_xy(tx + ACC + PAD, yy + (T_ROW_H - 3.5) / 2)
        pdf.cell(T_COL_W - ACC - PAD - 1, 3.5, t, ln=False)

    pdf.set_y(T_Y + (len(terms) // 2) * T_ROW_H + 4)

    # ==========================================================================
    # I. FOOTER
    # ==========================================================================
    pdf.double_rule()
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 7.5)
    pdf.set_text_color(*GOLD_DK)
    pdf.cell(0, 4, "*   *   *", align="C", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(*GOLD_DK)
    pdf.cell(0, 5, "Thank you for choosing The Veloria Grand.", align="C", ln=True)

    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 4.5, "We look forward to welcoming you again!", align="C", ln=True)
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 6.5)
    pdf.set_text_color(*MUTED)
    pdf.cell(0, 3.5,
             "Computer-generated invoice. No physical signature required.   |   *   *   *",
             align="C", ln=True)

    # Bottom gold band
    pdf.set_fill_color(*GOLD_DK)
    pdf.rect(5, 289, 200, 2.5, "F")

    pdf.output(output_path)
    return output_path
