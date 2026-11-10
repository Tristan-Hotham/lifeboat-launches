"""Reddit collage (reddit/lifeboat_launches_collage.png, 2400 px wide) and the social card header.png (1200 x 630).
Run after code/03_results.py; reads the scratch launch table only to grid the located launches (aggregates drawn)."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LogNorm, LinearSegmentedColormap
import numpy as np, pandas as pd, geopandas as gpd
from pyproj import Transformer
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "IBMPlexMono-Regular.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name()
PAPER, INK, MUT, SEA, LAND, RULE = "#F6EED8", "#2B2119", "#6E604E", "#E4ECEE", "#F3EBD7", "#D9C9A3"
plt.rcParams.update({"font.family": "Source Serif 4", "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.edgecolor": MUT,
                     "xtick.color": MUT, "ytick.color": MUT, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=4, foreground=SEA)]
HP = [pe.withStroke(linewidth=4, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
L = pd.read_pickle(f"{SCR}/launches.pkl"); L = L[~L.loc_err]
S = pd.read_csv(f"{DATA}/stations.csv"); S = S[S.launches > 0]
tr = Transformer.from_crs(4326, 3035, always_xy=True)
L["ex"], L["ey"] = tr.transform(L.lon.values, L.lat.values)
S["ex"], S["ey"] = tr.transform(S.lon.values, S.lat.values)
land = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")
land = land[land.ADM0_A3.isin(["GBR", "IRL", "IMN", "GGY", "JEY", "FRA", "BEL", "NLD"])].to_crs(3035)
cm = LinearSegmentedColormap.from_list("lb", ["#F2C58B", "#E07A1F", "#B4442E", "#6B1F2A", "#2B0F14"])
bx = (float(np.quantile(L.ex, 0.0002)) - 30000, float(np.quantile(L.ex, 0.9998)) + 30000)
by = (float(np.quantile(L.ey, 0.0002)) - 30000, float(np.quantile(L.ey, 0.9998)) + 40000)
cell = 4000
H, xe, ye = np.histogram2d(L.ex, L.ey, bins=[np.arange(bx[0], bx[1] + cell, cell), np.arange(by[0], by[1] + cell, cell)])
H = np.ma.masked_where(H == 0, H)


def draw_map(ax, rings=True):
    ax.set_facecolor(SEA); land.plot(ax=ax, color=LAND, edgecolor="#CFC8B8", lw=0.5)
    pcm = ax.pcolormesh(xe, ye, H.T, cmap=cm, norm=LogNorm(1, H.max()), rasterized=True)
    if rings:
        ax.scatter(S.ex, S.ey, s=np.sqrt(S.launches) * 2.4, facecolor="none", edgecolor=np.where(S.stype == "ALB", BCOL["ALB"], "#7A4FA0"), lw=1.1, zorder=5)
    ax.set_xlim(*bx); ax.set_ylim(*by); ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
    for s_ in ax.spines.values(): s_.set_visible(False)
    return pcm


# ---------------- collage
fig = plt.figure(figsize=(16, 11.5), dpi=150)
fig.text(0.03, 0.955, "Where the lifeboats go", fontsize=40, family=DISP, fontweight="bold", color=INK, va="top")
fig.text(0.03, 0.895, f"{R['n']:,} RNLI lifeboat launches, 2021 to 2025, from {R['n_stations']} stations around the UK, Ireland, the Isle of Man and the Channel Islands",
         fontsize=16, color=MUT, va="top")
ax = fig.add_axes([0.01, 0.05, 0.47, 0.82])
pcm = draw_map(ax)
for nm, lon, lat, ha in [("Thames: Tower station alone\nmade %.1f%% of all launches" % R["prose"]["tower_pc"], 2.5, 51.75, "left"),
                         ("Firth of Forth", -1.9, 56.35, "left"), ("Blackpool", -3.6, 53.95, "right")]:
    x, y = tr.transform(lon, lat); ax.text(x, y, nm, fontsize=13, color=INK, ha=ha, va="center", path_effects=HALO, style="italic")
cax = fig.add_axes([0.04, 0.115, 0.18, 0.012]); cb = fig.colorbar(pcm, cax=cax, orientation="horizontal")
cb.set_ticks([1, 10, 100, 1000]); cb.set_ticklabels(["1", "10", "100", "1,000"]); cb.ax.tick_params(labelsize=11)
cb.set_label("Launches per 4 km square, 2021 to 2025", fontsize=12, color=INK)
ax.scatter([], [], s=150, facecolor="none", edgecolor=BCOL["ALB"], lw=1.4, label="station with an all-weather boat")
ax.scatter([], [], s=150, facecolor="none", edgecolor="#7A4FA0", lw=1.4, label="inshore boats only (ring size: launches)")
ax.legend(loc="upper left", bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=12)

# panel A: distance
a1 = fig.add_axes([0.56, 0.62, 0.40, 0.21])
for b, lab in (("ILB", "Inshore lifeboat"), ("ALB", "All-weather lifeboat")):
    q = np.sort(L[L.btype == b].dist.values); a1.plot(q, np.arange(1, len(q) + 1) / len(q) * 100, color=BCOL[b], lw=3)
    m = R["dist"][b]["med"]; a1.plot([m, m], [0, 50], color=BCOL[b], lw=1.2, ls=":")
    a1.text(m / 1.12 if b == "ILB" else m * 1.12, 74 if b == "ILB" else 30, f"{lab}\nhalf within {m:.1f} km", color=BCOL[b], fontsize=13, path_effects=HP, ha="right" if b == "ILB" else "left")
a1.set_xscale("log"); a1.set_xlim(0.2, 100); a1.set_ylim(0, 100); a1.axhline(50, color=RULE, lw=0.8)
a1.set_xticks([0.5, 1, 2, 5, 10, 20, 50, 100]); a1.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50", "100 km"], fontsize=11)
a1.tick_params(labelsize=11); a1.set_ylabel("% of launches within", fontsize=12)
a1.set_title(f"Most rescues are close: half within {R['dist']['all_types']['med']:.1f} km of the station", fontsize=15, loc="left", color=INK, family=DISP, fontweight="bold")

# panel B: season
a2 = fig.add_axes([0.56, 0.33, 0.40, 0.20])
mon = L.groupby(["group", "month"]).size().unstack(fill_value=0)
dim = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
for g, lab in (("powered and sail craft", "Motorboats, yachts, dinghies"), ("paddle and board craft", "Kayaks, paddleboards, boards"), ("commercial", "Commercial (mostly fishing)")):
    rate = mon.loc[g].values / dim; v = rate / rate.mean()
    a2.plot(range(1, 13), v, color=GCOL[g], lw=3, marker="o", ms=4)
    a2.text(12.3, {"powered and sail craft": 0.45, "paddle and board craft": 0.17, "commercial": v[11] + 0.14}[g], lab, color=GCOL[g], fontsize=12, va="center", path_effects=HP)
a2.set_xlim(0.7, 16.8); a2.set_xticks(range(1, 13)); a2.set_xticklabels(list("JFMAMJJASOND"), fontsize=11); a2.tick_params(labelsize=11)
a2.set_ylim(0.0, 2.65); a2.axhline(1, color=RULE, lw=0.8); a2.set_ylabel("Launch rate vs\nyear's average", fontsize=12)
a2.set_title(f"Summer is for leisure: {R['H3']['powered and sail craft']['rr']:.1f}x summer vs winter for leisure boats,\n{R['H3']['commercial']['rr']:.1f}x for commercial casualties",
             fontsize=15, loc="left", color=INK, family=DISP, fontweight="bold")

# panel C: busiest stations
a3 = fig.add_axes([0.66, 0.07, 0.30, 0.18])
top = R["top_stations"][:6]
a3.barh(range(len(top)), [t["launches"] for t in top], color=["#B4442E" if t["station"] in ("Tower", "Chiswick") else "#5E93C2" for t in top], height=0.65)
a3.set_yticks(range(len(top))); a3.set_yticklabels([t["station"] for t in top], fontsize=12); a3.invert_yaxis(); a3.tick_params(labelsize=11)
for i, t in enumerate(top):
    a3.text(t["launches"] + 40, i, f"{t['launches']:,}", va="center", fontsize=11, color=INK)
a3.set_xlim(0, max(t["launches"] for t in top) * 1.18)
a3.set_title("Busiest stations: two on the Thames (red)", fontsize=15, loc="left", color=INK, family=DISP, fontweight="bold")
fig.text(0.03, 0.012, "Data: RNLI Returns of Service open data (RNLI open data licence); Natural Earth. Straight-line distances.\nDr Tristan Hotham, Independent researcher, 2026 · maps.tristanhotham.com/lifeboat-launches",
         fontsize=11, family="IBM Plex Mono", color=MUT)
os.makedirs(os.path.join(ROOT, "reddit"), exist_ok=True)
fig.savefig(os.path.join(ROOT, "reddit", "lifeboat_launches_collage.png"), dpi=150, facecolor=PAPER)
plt.close(fig)

# ---------------- header 1200 x 630
fig = plt.figure(figsize=(12, 6.3), dpi=100)
ax = fig.add_axes([0.52, 0.0, 0.48, 1.0]); draw_map(ax, rings=False)
fig.text(0.05, 0.80, "Where the\nlifeboats go", fontsize=50, family=DISP, fontweight="bold", color=INK, va="top", linespacing=1.0)
fig.text(0.05, 0.40, f"{R['n']:,} RNLI launches, 2021 to 2025.\nHalf went less than {R['dist']['all_types']['med']:.1f} km from the station.", fontsize=17, color=MUT, va="top")
fig.text(0.05, 0.07, "maps.tristanhotham.com/lifeboat-launches", fontsize=12, family="IBM Plex Mono", color=MUT)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=PAPER)
plt.close(fig)
from PIL import Image
assert Image.open(os.path.join(ROOT, "header.png")).size == (1200, 630)
print("collage", Image.open(os.path.join(ROOT, "reddit", "lifeboat_launches_collage.png")).size)
