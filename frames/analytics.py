
# frames/analytics.py — Analytics & Graphs Frame
import tkinter as tk
from tkinter import ttk, messagebox
import sys, os
from datetime import datetime, date
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from styles import *

try:
    import matplotlib
    import matplotlib.ticker
    matplotlib.use("TkAgg")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


class AnalyticsFrame(tk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent, bg=BG_MAIN)
        self.db = db
        self._canvases = []
        self._build_ui()

    def _build_ui(self):
        hdr = tk.Frame(self, bg=BG_MAIN, padx=30, pady=16)
        hdr.pack(fill="x")
        tk.Label(hdr, text="ANALYTICS", font=("Segoe UI", 8, "bold"),
                 bg=BG_MAIN, fg=TEXT_MUTED).pack(anchor="w")

        hdr_row = tk.Frame(hdr, bg=BG_MAIN)
        hdr_row.pack(fill="x")
        tk.Label(hdr_row, text="Graphs & Analysis", font=FONT_HEADING,
                 bg=BG_MAIN, fg=GOLD).pack(side="left")
        ttk.Button(hdr_row, text="🔄  Refresh All Charts",
                   command=self._draw_all).pack(side="right")

        tk.Frame(self, bg=GOLD_DARK, height=1).pack(fill="x", padx=30)

        if not HAS_MPL:
            msg_frame = tk.Frame(self, bg=BG_CARD, padx=40, pady=40)
            msg_frame.pack(fill="both", expand=True, padx=30, pady=20)
            tk.Label(msg_frame,
                     text="⚠️  Matplotlib is not installed.\n\n"
                          "Please install it by running:\n\n"
                          "    pip install matplotlib\n\n"
                          "Then restart the application.",
                     font=("Segoe UI", 13), bg=BG_CARD, fg=WARNING,
                     justify="center").pack(expand=True)
            return

        # Scrollable container for all 6 charts
        _, sf = make_scrollable(self, BG_MAIN)

        # ── EXISTING Chart 1: Reservations by Room — Grouped ─────────────────
        c1 = self._make_chart_card(
            sf, "1",
            "Reservations by Room ID — Current, Upcoming & Completed",
            "Grouped Bar Chart  ·  Blue = Active Today  ·  Gold = Upcoming  ·  Grey = Completed")
        self._fig1, self._ax1 = self._make_figure(c1, height=4.4)

        # ── EXISTING Chart 2: Room Category Distribution ──────────────────────
        c2 = self._make_chart_card(sf, "2", "Room Category Distribution",
                                   "Pie Chart — Rooms by type")
        self._fig2, self._ax2 = self._make_figure(c2)

        # ── EXISTING Chart 3: Occupied vs Available by Category ───────────────
        c3 = self._make_chart_card(sf, "3",
                                   "Occupied vs Available Rooms by Category — Today",
                                   "Grouped Bar Chart — Current occupancy")
        self._fig3, self._ax3 = self._make_figure(c3)

        # ── NEW Chart 4: Monthly Revenue Trend ───────────────────────────────
        c4 = self._make_chart_card(sf, "4", "Monthly Revenue Trend",
                                   "Line Chart — Total revenue generated per month (INR)")
        self._fig4, self._ax4 = self._make_figure(c4, height=3.8)

        # ── NEW Chart 5: Reservation Status Distribution ──────────────────────
        c5 = self._make_chart_card(sf, "5", "Reservation Status Distribution",
                                   "Donut Chart — Confirmed / Cancelled / Completed")
        self._fig5, self._ax5 = self._make_figure(c5, height=3.8)

        # ── NEW Chart 6: Top 10 Highest-Earning Rooms ─────────────────────────
        c6 = self._make_chart_card(sf, "6", "Top Rooms by Revenue Earned",
                                   "Horizontal Bar Chart — Total revenue per room (INR)")
        self._fig6, self._ax6 = self._make_figure(c6, height=4.0)

        self._draw_all()

    # ── Chart card shell ───────────────────────────────────────────────────────
    def _make_chart_card(self, parent, num, title, subtitle):
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER_GOLD, highlightthickness=1)
        card.pack(fill="x", padx=30, pady=10)
        ch = tk.Frame(card, bg=GOLD_SUBTLE, pady=8, padx=20)
        ch.pack(fill="x")
        tk.Label(ch, text=f"📊  Chart {num}: {title}", font=FONT_SUBHEAD,
                 bg=GOLD_SUBTLE, fg=GOLD).pack(anchor="w")
        tk.Label(ch, text=subtitle, font=FONT_SMALL,
                 bg=GOLD_SUBTLE, fg=TEXT_MUTED).pack(anchor="w")
        return card

    def _make_figure(self, parent, height=3.8):
        fig = Figure(figsize=(11, height), dpi=96,
                     facecolor="#11122A", edgecolor="#11122A")
        ax  = fig.add_subplot(111)
        ax.set_facecolor("#11122A")
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().pack(fill="x", padx=10, pady=10)
        self._canvases.append(canvas)
        return fig, ax

    # ── Axis styling ───────────────────────────────────────────────────────────
    def _style_ax(self, ax, fig=None):
        ax.tick_params(colors="#B8AE98", labelsize=9)
        ax.spines["bottom"].set_color("#2A2840")
        ax.spines["left"].set_color("#2A2840")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.xaxis.label.set_color("#B8AE98")
        ax.yaxis.label.set_color("#B8AE98")
        ax.title.set_color("#C8A951")
        if fig:
            fig.tight_layout(pad=2)

    # ── Chart 1: Reservations by Room ─────────────────────────────────────────
    def _draw_chart1(self):
        self._ax1.clear()
        try:
            import numpy as np
            rooms, current, upcoming, completed = self.db.get_reservations_by_room_grouped()
            if not rooms:
                self._ax1.text(0.5, 0.5, "No room data found.\nAdd rooms first.",
                               ha="center", va="center", color=TEXT_MUTED,
                               transform=self._ax1.transAxes, fontsize=11)
            else:
                x     = np.arange(len(rooms))
                width = 0.26
                gap   = 0.02
                C_C   = "#5DADE2"
                C_U   = GOLD
                C_D   = "#4A4A6A"

                bc = self._ax1.bar(x - width - gap, current,  width, label="Active Today",
                                   color=C_C, edgecolor="#0B0C1A", linewidth=0.7)
                bu = self._ax1.bar(x,               upcoming, width, label="Upcoming",
                                   color=C_U, edgecolor="#0B0C1A", linewidth=0.7)
                bd = self._ax1.bar(x + width + gap, completed,width, label="Completed",
                                   color=C_D, edgecolor="#0B0C1A", linewidth=0.7)

                def _lbl(bars, color):
                    for b in bars:
                        h = b.get_height()
                        if h > 0:
                            self._ax1.text(b.get_x()+b.get_width()/2, h+0.06,
                                           str(int(h)), ha="center", va="bottom",
                                           fontsize=8, fontweight="bold", color=color)
                _lbl(bc, C_C); _lbl(bu, "#E8D5A3"); _lbl(bd, "#8888AA")

                for i,(c,u,d) in enumerate(zip(current,upcoming,completed)):
                    t = c+u+d
                    if t:
                        self._ax1.annotate(f"Total:{t}",
                            xy=(x[i],max(c,u,d)+0.5), ha="center", va="bottom",
                            fontsize=7.5, color=CREAM, style="italic")

                self._ax1.set_ylim(0, max(max(current),max(upcoming),max(completed),1)+2)
                self._ax1.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
                self._ax1.set_xlabel("Room ID", fontsize=9, labelpad=8)
                self._ax1.set_ylabel("Number of Reservations", fontsize=9)
                self._ax1.set_title("Reservations by Room — Current | Upcoming | Completed",
                                    fontsize=11, fontweight="bold", pad=12)
                self._ax1.set_xticks(x)
                self._ax1.set_xticklabels(rooms, rotation=40, ha="right", fontsize=8.5)
                self._ax1.yaxis.grid(True, color="#2A2840", linestyle="--",
                                     linewidth=0.6, alpha=0.7)
                self._ax1.set_axisbelow(True)
                leg = self._ax1.legend(fontsize=9, facecolor="#11122A",
                                       edgecolor=GOLD_DARK, loc="upper right", framealpha=0.85)
                for t in leg.get_texts(): t.set_color(CREAM)
        except ImportError:
            self._ax1.text(0.5,0.5,"numpy not installed.\npip install numpy",
                           ha="center",va="center",color=WARNING,
                           transform=self._ax1.transAxes,fontsize=10)
        except Exception as e:
            self._ax1.text(0.5,0.5,f"Chart Error:\n{e}",ha="center",va="center",
                           color=DANGER,transform=self._ax1.transAxes,fontsize=9)
        self._style_ax(self._ax1, self._fig1)
        self._fig1.canvas.draw()

    # ── Chart 2: Room Category Distribution ───────────────────────────────────
    def _draw_chart2(self):
        self._ax2.clear()
        try:
            types, counts = self.db.get_room_type_distribution()
            if not types:
                self._ax2.text(0.5,0.5,"No room data available",
                               ha="center",va="center",color=TEXT_MUTED,
                               transform=self._ax2.transAxes,fontsize=11)
            else:
                COLORS  = ["#C8A951","#5DADE2","#27AE60","#E74C3C",
                           "#9B59B6","#F39C12","#1ABC9C","#E67E22","#2ECC71"]
                wedges, texts, autotexts = self._ax2.pie(
                    counts, labels=types, autopct="%1.1f%%",
                    colors=COLORS[:len(types)], startangle=90, pctdistance=0.75,
                    wedgeprops=dict(edgecolor="#0B0C1A", linewidth=2))
                for t in texts:
                    t.set_color(CREAM); t.set_fontsize(9)
                for at in autotexts:
                    at.set_color(BG_MAIN); at.set_fontsize(8); at.set_fontweight("bold")
                self._ax2.set_title("Room Category Distribution",
                                    fontsize=11, fontweight="bold", color=GOLD, pad=10)
        except Exception as e:
            self._ax2.text(0.5,0.5,f"Error: {e}",ha="center",va="center",
                           color=DANGER,transform=self._ax2.transAxes)
        self._fig2.tight_layout(pad=2)
        self._fig2.canvas.draw()

    # ── Chart 3: Occupied vs Available ────────────────────────────────────────
    def _draw_chart3(self):
        self._ax3.clear()
        try:
            import numpy as np
            categories, available, booked = self.db.get_occupied_vs_available_by_type()
            if not categories:
                self._ax3.text(0.5,0.5,"No room data available",
                               ha="center",va="center",color=TEXT_MUTED,
                               transform=self._ax3.transAxes,fontsize=11)
            else:
                x=np.arange(len(categories)); w=0.35
                b1=self._ax3.bar(x-w/2,available,w,label="Available",
                                  color=SUCCESS,edgecolor="#0B0C1A",linewidth=0.8)
                b2=self._ax3.bar(x+w/2,booked,   w,label="Booked",
                                  color=DANGER, edgecolor="#0B0C1A",linewidth=0.8)
                for bars in [b1,b2]:
                    for b in bars:
                        h=b.get_height()
                        if h>0:
                            self._ax3.text(b.get_x()+b.get_width()/2,h+0.05,
                                           str(int(h)),ha="center",va="bottom",
                                           fontsize=8,color=CREAM,fontweight="bold")
                self._ax3.set_xlabel("Room Category",fontsize=9)
                self._ax3.set_ylabel("Count",fontsize=9)
                self._ax3.set_title("Occupied vs Available Rooms by Category — Today",
                                    fontsize=11, fontweight="bold", pad=10)
                self._ax3.set_xticks(x)
                self._ax3.set_xticklabels(categories,rotation=30,ha="right",fontsize=8)
                leg=self._ax3.legend(fontsize=8,facecolor=BG_CARD,edgecolor=GOLD_DARK)
                for t in leg.get_texts(): t.set_color(CREAM)
        except ImportError:
            self._ax3.text(0.5,0.5,"numpy not found.",ha="center",va="center",
                           color=WARNING,transform=self._ax3.transAxes)
        except Exception as e:
            self._ax3.text(0.5,0.5,f"Error: {e}",ha="center",va="center",
                           color=DANGER,transform=self._ax3.transAxes)
        self._style_ax(self._ax3, self._fig3)
        self._fig3.canvas.draw()

    # ── NEW Chart 4: Monthly Revenue Trend ────────────────────────────────────
    def _draw_chart4(self):
        self._ax4.clear()
        try:
            rows = self.db.get_all_reservations_for_billing()
            monthly = defaultdict(float)
            for r in (rows or []):
                d = dict(r)
                if d.get("payment_status") == "Paid" and d.get("created_at"):
                    try:
                        mo = str(d["created_at"])[:7]   # "YYYY-MM"
                        monthly[mo] += float(d.get("total_amount", 0) or 0)
                    except Exception:
                        pass

            if not monthly:
                self._ax4.text(0.5, 0.5,
                               "No paid reservations yet.\nRevenue will appear after payments.",
                               ha="center", va="center", color=TEXT_MUTED,
                               transform=self._ax4.transAxes, fontsize=11)
            else:
                months = sorted(monthly.keys())
                values = [monthly[m] for m in months]

                # Format labels as "Jan '26"
                def fmt_month(ym):
                    try:
                        dt = datetime.strptime(ym, "%Y-%m")
                        return dt.strftime("%b '%y")
                    except Exception:
                        return ym

                labels = [fmt_month(m) for m in months]

                self._ax4.plot(labels, values, color=GOLD, linewidth=2.5,
                               marker="o", markersize=7,
                               markerfacecolor=GOLD_LIGHT, markeredgecolor=BG_MAIN,
                               markeredgewidth=1.5, zorder=5)

                # Fill under line
                self._ax4.fill_between(labels, values, alpha=0.15, color=GOLD)

                # Value annotations
                for i, (lbl, val) in enumerate(zip(labels, values)):
                    self._ax4.annotate(
                        f"\u20b9{val/1000:.1f}K" if val >= 1000 else f"\u20b9{val:.0f}",
                        xy=(i, val), xytext=(0, 10),
                        textcoords="offset points",
                        ha="center", fontsize=8,
                        color=GOLD_LIGHT, fontweight="bold")

                self._ax4.yaxis.set_major_formatter(
                    matplotlib.ticker.FuncFormatter(
                        lambda x, _: f"\u20b9{x/1000:.0f}K" if x >= 1000 else f"\u20b9{x:.0f}"))
                self._ax4.set_xlabel("Month", fontsize=9, labelpad=8)
                self._ax4.set_ylabel("Revenue (INR)", fontsize=9)
                self._ax4.set_title("Monthly Revenue Trend",
                                    fontsize=11, fontweight="bold", pad=12)
                self._ax4.yaxis.grid(True, color="#2A2840", linestyle="--",
                                     linewidth=0.6, alpha=0.7)
                self._ax4.set_axisbelow(True)
                if len(labels) > 1:
                    self._ax4.set_xlim(-0.5, len(labels)-0.5)

        except Exception as e:
            self._ax4.text(0.5,0.5,f"Chart Error:\n{e}",ha="center",va="center",
                           color=DANGER,transform=self._ax4.transAxes,fontsize=9)
        self._style_ax(self._ax4, self._fig4)
        self._fig4.canvas.draw()

    # ── NEW Chart 5: Reservation Status Distribution (Donut) ──────────────────
    def _draw_chart5(self):
        self._ax5.clear()
        try:
            rows  = self.db.get_all_reservations()
            today = date.today()

            # Dynamically classify each reservation by date
            counts = defaultdict(int)
            for r in (rows or []):
                d  = dict(r)
                st = (d.get("status") or "").strip()

                if st == "Cancelled":
                    counts["Cancelled"] += 1
                    continue

                try:
                    ci = datetime.strptime(str(d["check_in"]),  "%Y-%m-%d").date()
                    co = datetime.strptime(str(d["check_out"]), "%Y-%m-%d").date()
                except Exception:
                    counts["Confirmed"] += 1
                    continue

                if co <= today:
                    counts["Completed"] += 1
                elif ci <= today < co:
                    counts["Active Today"] += 1
                else:
                    counts["Upcoming"] += 1

            if not counts:
                self._ax5.text(0.5, 0.5,
                               "No reservation data available.",
                               ha="center", va="center", color=TEXT_MUTED,
                               transform=self._ax5.transAxes, fontsize=11)
            else:
                # Order: Completed → Active → Upcoming → Cancelled
                order  = ["Completed", "Active Today", "Upcoming", "Cancelled"]
                labels = [k for k in order if k in counts]
                sizes  = [counts[k] for k in labels]

                SCOLORS = {
                    "Completed":   "#5DADE2",   # blue
                    "Active Today": GOLD,        # gold
                    "Upcoming":    "#27AE60",   # green
                    "Cancelled":   "#C0392B",   # red
                }
                colors = [SCOLORS[l] for l in labels]

                wedges, _, autotexts = self._ax5.pie(
                    sizes, labels=None, autopct="%1.1f%%",
                    colors=colors, startangle=90,
                    pctdistance=0.72,
                    wedgeprops=dict(edgecolor="#0B0C1A",
                                   linewidth=2, width=0.55))
                for at in autotexts:
                    at.set_color("white")
                    at.set_fontsize(8.5)
                    at.set_fontweight("bold")

                # Centre: total count
                total = sum(sizes)
                self._ax5.text(0, 0, f"{total}\nTotal",
                               ha="center", va="center",
                               fontsize=14, fontweight="bold", color=GOLD)

                # Legend with counts
                leg = self._ax5.legend(
                    wedges,
                    [f"{l}  ({counts[l]})" for l in labels],
                    loc="center left", bbox_to_anchor=(1, 0, 0.5, 1),
                    fontsize=9, facecolor="#11122A",
                    edgecolor=GOLD_DARK, framealpha=0.9)
                for t in leg.get_texts():
                    t.set_color(CREAM)

                self._ax5.set_title(
                    "Reservation Status Distribution\n"
                    "(Completed = past checkout  ·  Active = checked in today  ·  "
                    "Upcoming = future)",
                    fontsize=10, fontweight="bold", color=GOLD, pad=10)

        except Exception as e:
            self._ax5.text(0.5, 0.5, f"Chart Error:\n{e}",
                           ha="center", va="center",
                           color=DANGER, transform=self._ax5.transAxes, fontsize=9)
        self._fig5.tight_layout(pad=2)
        self._fig5.canvas.draw()

    # ── NEW Chart 6: Top Rooms by Revenue ─────────────────────────────────────
    def _draw_chart6(self):
        self._ax6.clear()
        try:
            rows = self.db.get_all_reservations_for_billing()
            room_rev = defaultdict(float)
            for r in (rows or []):
                d = dict(r)
                if d.get("payment_status") == "Paid":
                    rid = d.get("room_id", "?")
                    rtype = d.get("room_type", "")
                    label = f"{rid}\n({rtype[:14]})" if rtype else str(rid)
                    room_rev[label] += float(d.get("total_amount", 0) or 0)

            if not room_rev:
                self._ax6.text(0.5, 0.5,
                               "No paid reservations found.\nRevenue by room will appear after payments.",
                               ha="center", va="center", color=TEXT_MUTED,
                               transform=self._ax6.transAxes, fontsize=11)
            else:
                sorted_rooms = sorted(room_rev.items(), key=lambda x: x[1], reverse=True)[:10]
                labels = [r[0] for r in sorted_rooms]
                values = [r[1] for r in sorted_rooms]

                # Gradient colours: gold → teal
                bar_colors = []
                n = len(values)
                for i in range(n):
                    ratio = i / max(n - 1, 1)
                    r_ = int(200 + (28 - 200) * ratio)
                    g_ = int(169 + (174 - 169) * ratio)
                    b_ = int(81  + (96  - 81)  * ratio)
                    bar_colors.append(f"#{r_:02X}{g_:02X}{b_:02X}")

                bars = self._ax6.barh(labels[::-1], values[::-1],
                                      color=bar_colors[::-1],
                                      edgecolor="#0B0C1A", linewidth=0.7,
                                      height=0.6)

                # Value labels
                for bar, val in zip(bars, values[::-1]):
                    self._ax6.text(
                        bar.get_width() + max(values) * 0.01, bar.get_y() + bar.get_height()/2,
                        f"\u20b9{val/1000:.1f}K" if val >= 1000 else f"\u20b9{val:.0f}",
                        va="center", ha="left", fontsize=8.5,
                        color=GOLD_LIGHT, fontweight="bold")

                self._ax6.set_xlabel("Total Revenue (INR)", fontsize=9)
                self._ax6.set_title("Top Rooms by Revenue Earned",
                                    fontsize=11, fontweight="bold", pad=12)
                self._ax6.xaxis.set_major_formatter(
                    matplotlib.ticker.FuncFormatter(
                        lambda x, _: f"\u20b9{x/1000:.0f}K" if x >= 1000 else f"\u20b9{x:.0f}"))
                self._ax6.xaxis.grid(True, color="#2A2840", linestyle="--",
                                     linewidth=0.6, alpha=0.7)
                self._ax6.set_axisbelow(True)
                xlim_max = max(values) * 1.2 if values else 1
                self._ax6.set_xlim(0, xlim_max)

        except Exception as e:
            self._ax6.text(0.5,0.5,f"Chart Error:\n{e}",ha="center",va="center",
                           color=DANGER,transform=self._ax6.transAxes,fontsize=9)
        self._style_ax(self._ax6, self._fig6)
        self._fig6.canvas.draw()

    # ── Draw all ───────────────────────────────────────────────────────────────
    def _draw_all(self):
        if not HAS_MPL:
            return
        self._draw_chart1()
        self._draw_chart2()
        self._draw_chart3()
        self._draw_chart4()
        self._draw_chart5()
        self._draw_chart6()

    def refresh(self):
        self._draw_all()
