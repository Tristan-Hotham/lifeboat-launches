"""Step 4: figures for the page (img/*.jpg), the blog (release/blog/b_*.png, 1800 px) and the paper (release/paper/f_*.pdf).
Light paper background; one fixed colour per casualty group and per boat type (common.GCOL, BCOL)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager as fm
from matplotlib.colors import LogNorm, LinearSegmentedColormap
import numpy as np, pandas as pd, geopandas as gpd
from PIL import Image
from pyproj import Transformer
from common import *

for f in ("FrauncesVar.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
SERIF = "Source Serif 4"; DISP = fm.FontProperties(fname=f"{FONTS}/FrauncesVar.ttf").get_name(); MONO = "IBM Plex Mono"
PAPER, INK, MUT, RULE, SEA, LAND = "#F6EED8", "#2B2119", "#6E604E", "#D9C9A3", "#E4ECEE", "#F3EBD7"
plt.rcParams.update({"font.family": SERIF, "font.size": 12, "axes.edgecolor": MUT, "axes.labelcolor": INK, "xtick.color": MUT,
                     "ytick.color": MUT, "axes.facecolor": PAPER, "figure.facecolor": PAPER, "axes.unicode_minus": False,
                     "pdf.fonttype": 42, "axes.spines.top": False, "axes.spines.right": False})
HALO = [pe.withStroke(linewidth=3, foreground=PAPER)]
R = jload(f"{DATA}/results.json")
L = pd.read_pickle(f"{SCR}/launches.pkl")
S = pd.read_csv(f"{DATA}/stations.csv")
BLOG, PAPD = f"{REL}/blog", f"{REL}/paper"
for d_ in (BLOG, PAPD):
    os.makedirs(d_, exist_ok=True)
FOOT = "Data: RNLI Returns of Service open data, 2021 to 2025; Natural Earth. maps.tristanhotham.com/lifeboat-launches"
GL = {g: GROUP_SHORT[g] for g in GROUPS}


def out(fig, name, page=True, blog=True, paper=True):
    if paper:
        fig.savefig(f"{PAPD}/f_{name}.pdf", facecolor=fig.get_facecolor(), dpi=300)
    fig.savefig(f"{SCR}/{name}.png", dpi=220, facecolor=fig.get_facecolor())
    plt.close(fig)
    im = Image.open(f"{SCR}/{name}.png").convert("RGB")
    if page:
        w = min(1500, im.size[0]); im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{IMG}/{name}.jpg", quality=85, optimize=True)
    if blog:
        w = 1800; im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS).save(f"{BLOG}/b_{name}.png", optimize=True)
    os.remove(f"{SCR}/{name}.png")


def title(fig, t, sub, y=0.965):
    fig.text(0.04, y, t, fontsize=21, fontweight="bold", family=DISP, color=INK, va="top")
    fig.text(0.04, y - 0.05, sub, fontsize=12, color=MUT, va="top")


def foot(fig, s=FOOT):
    fig.text(0.04, 0.015, s, fontsize=8.5, family=MONO, color=MUT)


tr = Transformer.from_crs(4326, 3035, always_xy=True)
land = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")
land = land[land.ADM0_A3.isin(["GBR", "IRL", "IMN", "GGY", "JEY", "FRA", "BEL", "NLD"])].to_crs(3035)
Lk = L[~L.loc_err].copy()
Lk["ex"], Lk["ey"] = tr.transform(Lk.lon.values, Lk.lat.values)
S["ex"], S["ey"] = tr.transform(S.lon.values, S.lat.values)
X0, Y0 = tr.transform(-11.2, 49.6); X1, Y1 = tr.transform(2.3, 60.95)
bx = (float(np.quantile(Lk.ex, 0.0002)) - 30000, float(np.quantile(Lk.ex, 0.9998)) + 30000); by = (float(np.quantile(Lk.ey, 0.0002)) - 30000, float(np.quantile(Lk.ey, 0.9998)) + 40000)

# ---------------- 1. map: density on 2 km cells
fig = plt.figure(figsize=(10, 12))
ax = fig.add_axes([0.02, 0.05, 0.96, 0.84]); ax.set_facecolor(SEA)
land.plot(ax=ax, color=LAND, edgecolor="#CFC8B8", lw=0.4)
cell = 4000
H, xe, ye = np.histogram2d(Lk.ex, Lk.ey, bins=[np.arange(bx[0], bx[1] + cell, cell), np.arange(by[0], by[1] + cell, cell)])
H = np.ma.masked_where(H == 0, H)
cm = LinearSegmentedColormap.from_list("lb", ["#F2C58B", "#E07A1F", "#B4442E", "#6B1F2A", "#2B0F14"])
pc_ = ax.pcolormesh(xe, ye, H.T, cmap=cm, norm=LogNorm(1, H.max()), rasterized=True)
ss = S[S.launches > 0]
ax.scatter(ss.ex, ss.ey, s=np.sqrt(ss.launches) * 1.6, facecolor="none", edgecolor="#1D3F6E", lw=0.9, zorder=5)
ax.set_xlim(*bx); ax.set_ylim(*by); ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel(""); [s_.set_visible(False) for s_ in ax.spines.values()]
for nm, lon, lat, ha in [("Thames: Tower and Chiswick", 1.75, 51.62, "left"), ("Solent and Poole", -1.6, 50.12, "left"), ("Firth of Forth", -2.2, 56.30, "left"),
                         ("Blackpool", -3.55, 53.95, "right")]:
    x, y = tr.transform(lon, lat)
    ax.text(x, y, nm, fontsize=10.5, color=INK, ha=ha, path_effects=HALO, style="italic")
cax = fig.add_axes([0.08, 0.10, 0.28, 0.015]); cb = fig.colorbar(pc_, cax=cax, orientation="horizontal")
cb.set_label("Launches 2021 to 2025 per 4 km square (log scale)", fontsize=10, color=INK); cb.ax.tick_params(labelsize=9); cb.set_ticks([1, 10, 100, 1000]); cb.set_ticklabels(["1", "10", "100", "1,000"])
ax.scatter([], [], s=np.sqrt(500) * 1.6, facecolor="none", edgecolor="#1D3F6E", lw=0.9, label="Lifeboat station (ring size: launches)")
ax.legend(loc="lower left", bbox_to_anchor=(0.04, 0.09), frameon=False, fontsize=10)
title(fig, "Where the lifeboats go", f"{R['n_located']:,} located RNLI lifeboat launches, 2021 to 2025, counted on 4 km squares; UK, Ireland, Isle of Man and Channel Islands")
foot(fig); out(fig, "map")

# ---------------- 2. distance
fig = plt.figure(figsize=(12, 6.6))
ax = fig.add_axes([0.07, 0.13, 0.42, 0.66])
for b in ("ILB", "ALB"):
    q = np.sort(Lk[Lk.btype == b].dist.values); yv = np.arange(1, len(q) + 1) / len(q)
    ax.plot(q, yv * 100, color=BCOL[b], lw=2.4)
    m = R["dist"][b]["med"]
    ax.plot([m, m], [0, 50], color=BCOL[b], lw=1, ls=":")
    ax.text(m * 1.08, 8 if b == "ILB" else 20, f"{'inshore' if b == 'ILB' else 'all-weather'}\nmedian {m:.1f} km", color=BCOL[b], fontsize=11, path_effects=HALO)
ax.set_xscale("log"); ax.set_xlim(0.1, 200); ax.set_xticks([0.1, 0.5, 1, 2, 5, 10, 20, 50, 100, 200]); ax.set_xticklabels(["0.1", "0.5", "1", "2", "5", "10", "20", "50", "100", "200"])
ax.set_ylim(0, 100); ax.axhline(50, color=RULE, lw=0.7); ax.set_xlabel("Straight-line distance from station to incident (km)"); ax.set_ylabel("Share of launches within that distance (%)")
ax.text(0.12, 92, "Inshore lifeboat", color=BCOL["ILB"], fontsize=12, fontweight="bold", path_effects=HALO)
ax.text(0.12, 85, "All-weather lifeboat", color=BCOL["ALB"], fontsize=12, fontweight="bold", path_effects=HALO)
ax2 = fig.add_axes([0.60, 0.13, 0.37, 0.66])
DG = R["dist_group"]; order = sorted(GROUPS, key=lambda g: DG[g]["med"])
for i, g in enumerate(order):
    ax2.plot([DG[g]["med_ilb"]], [i + 0.15], "o", color=BCOL["ILB"], ms=8)
    ax2.plot([DG[g]["med_alb"]], [i - 0.15], "s", color=BCOL["ALB"], ms=8)
    ax2.errorbar(DG[g]["med"], i, xerr=[[DG[g]["med"] - DG[g]["lo"]], [DG[g]["hi"] - DG[g]["med"]]], fmt="|", color=INK, ms=14, capsize=0, lw=1.6)
ax2.set_yticks(range(len(order))); ax2.set_yticklabels([GL[g] for g in order]); ax2.set_xlim(0, 15)
ax2.set_xlabel("Median distance (km)"); ax2.grid(axis="x", color=RULE, lw=0.6)
ax2.plot([], [], "o", color=BCOL["ILB"], label="inshore"); ax2.plot([], [], "s", color=BCOL["ALB"], label="all-weather"); ax2.plot([], [], "|", color=INK, ms=12, label="all boats (95% interval)")
ax2.legend(loc="lower right", frameon=False, fontsize=10)
title(fig, "Most rescues are close to home", f"Half of all launches went less than {R['dist']['all_types']['med']:.1f} km from the station; all-weather boats {R['prose']['alb_x']:.1f} times as far as inshore boats")
foot(fig); out(fig, "dist")

# ---------------- 3. season and weekend
fig = plt.figure(figsize=(12, 6.6))
ax = fig.add_axes([0.07, 0.13, 0.55, 0.66])
mon = L.groupby(["group", "month"]).size().unstack(fill_value=0)
dim = np.array([31, 28.25, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
for g in GROUPS:
    rate = mon.loc[g].values / dim; idx = rate / rate.mean()
    ax.plot(range(1, 13), idx, color=GCOL[g], lw=2.6 if g in ("powered and sail craft", "commercial") else 1.8, marker="o", ms=4)
lab_y = {g: (mon.loc[g].values / dim / (mon.loc[g].values / dim).mean())[7] for g in GROUPS}
ys = sorted(GROUPS, key=lambda g: lab_y[g]); pos = {}; last = -1
for g in ys:
    yv = max(lab_y[g], last + 0.13); pos[g] = yv; last = yv
for g in GROUPS:
    ax.text(12.3, pos[g] if g not in ("commercial",) else lab_y[g], GL[g], color=GCOL[g], fontsize=10.5, va="center", path_effects=HALO)
ax.set_xlim(0.7, 15.6); ax.set_xticks(range(1, 13)); ax.set_xticklabels(list("JFMAMJJASOND")); ax.axhline(1, color=RULE, lw=0.8)
ax.set_ylabel("Launches per day, relative to the year's average")
ax2 = fig.add_axes([0.73, 0.13, 0.24, 0.66])
W = R["H3b"]
for i, g in enumerate(GROUPS):
    v = W[g]; ax2.barh(i, v["rr"] - 1, left=1, color=GCOL[g], height=0.6)
    ax2.plot([v["lo"], v["hi"]], [i, i], color=INK, lw=1.2)
ax2.set_yticks(range(len(GROUPS))); ax2.set_yticklabels([GL[g] for g in GROUPS], fontsize=10); ax2.invert_yaxis()
ax2.axvline(1, color=MUT, lw=0.8); ax2.set_xlim(0.8, 2.4); ax2.set_xlabel("Weekend day vs weekday (rate ratio)")
title(fig, "Summer and the weekend belong to leisure", f"Powered and sail craft launches run {R['H3']['powered and sail craft']['rr']:.1f} times as high in summer as in winter; commercial casualties {R['H3']['commercial']['rr']:.1f} times")
foot(fig); out(fig, "season")

# ---------------- 4. hour and darkness
fig = plt.figure(figsize=(12, 6.6))
ax = fig.add_axes([0.07, 0.13, 0.55, 0.66])
for g in GROUPS:
    h = np.array(R["hour"][g], dtype=float); ax.plot(range(24), h / h.sum() * 100, color=GCOL[g], lw=2.2 if g == "paddle and board craft" else 1.6)
ax.set_xticks(range(0, 24, 3)); ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 3)]); ax.set_xlim(0, 23)
ax.set_ylabel("Share of the group's launches in each hour (%)"); ax.set_xlabel("Local clock time of launch")
ax.grid(axis="y", color=RULE, lw=0.6)
ax2 = fig.add_axes([0.73, 0.13, 0.24, 0.66])
DK = R["dark"]; ks = GROUPS + ["ALB", "ILB"]
for i, k in enumerate(ks):
    v = DK[k]; ax2.barh(i, v["pc"], color=GCOL.get(k, BCOL.get(k)), height=0.6); ax2.plot([v["lo"], v["hi"]], [i, i], color=INK, lw=1.2)
    ax2.text(v["hi"] + 0.8, i, f"{v['pc']:.0f}%", va="center", fontsize=10, color=INK)
ax2.set_yticks(range(len(ks))); ax2.set_yticklabels([GL.get(k, {"ALB": "All-weather boats", "ILB": "Inshore boats"}.get(k)) for k in ks], fontsize=10); ax2.invert_yaxis()
ax2.set_xlim(0, 38); ax2.set_xlabel("Launched in the dark (%)")
ax.legend(handles=[plt.Line2D([], [], color=GCOL[g], lw=2, label=GL[g]) for g in GROUPS], loc="upper left", frameon=False, fontsize=9.5)
title(fig, "Afternoon peaks, and who is out after dark", f"Busiest hour {R['hour_all']['peak']:02d}:00 to {R['hour_all']['peak'] + 1:02d}:00; {R['dark']['all']['pc']:.0f}% of launches after dusk (sun 6 degrees below the horizon), but only {R['dark']['paddle and board craft']['pc']:.1f}% for paddle and board craft")
foot(fig); out(fig, "hour")

# ---------------- 5. trend
fig = plt.figure(figsize=(12, 6.6))
axs = [fig.add_axes([0.06 + (i % 4) * 0.235, 0.47 - (i // 4) * 0.36, 0.19, 0.25]) for i in range(7)]
for ax, g in zip(axs, ["all"] + GROUPS):
    v = np.array(R["annual"][g]); col = GCOL.get(g, INK)
    ax.bar(YEARS, v, color=col, width=0.7)
    ax.set_ylim(0, v.max() * 1.25); ax.set_xticks(YEARS); ax.set_xticklabels(["21", "22", "23", "24", "25"], fontsize=9)
    e = R["H5"][g]
    ax.set_title(("All launches" if g == "all" else GL[g]) + f"\n{e['b']:+.1f}% a year [{e['lo']:+.1f}, {e['hi']:+.1f}]", fontsize=10.5, color=INK, loc="left")
    ax.tick_params(labelsize=9)
ax = fig.add_axes([0.06 + 3 * 0.235, 0.11, 0.19, 0.25])
ax.plot(YEARS, R["other_share"], color=GCOL["other or unknown"], lw=2.4, marker="o"); ax.set_ylim(0, 25); ax.set_xticks(YEARS); ax.set_xticklabels(["21", "22", "23", "24", "25"], fontsize=9)
ax.set_title("Share recorded as\ncasualty type \"Other\" (%)", fontsize=10.5, color=INK, loc="left"); ax.tick_params(labelsize=9)
title(fig, "Flat overall, but the labels are shifting", f"Launches each year by casualty group, with the planned trend estimate (% a year, 95% interval); \"Other\" rose from {R['other_share'][0]:.0f}% to {R['other_share'][-1]:.0f}% of launches")
foot(fig); out(fig, "trend")

# ---------------- 6. coast
C = S[~S.inland & (S.launches > 0)].copy()
fig = plt.figure(figsize=(12, 6.8))
ax = fig.add_axes([0.08, 0.13, 0.58, 0.66])
for t, col in (("ALB", BCOL["ALB"]), ("ILB", BCOL["ILB"])):
    q = C[C.stype == t]; ax.scatter(q.coast_km_10m, q.launches, s=26, color=col, alpha=0.8, edgecolor="white", lw=0.5, label="station with an all-weather boat" if t == "ALB" else "inshore boats only")
from matplotlib.ticker import FixedLocator, FixedFormatter
ax.set_xscale("log"); ax.set_yscale("log"); ax.xaxis.set_major_locator(FixedLocator([10, 20, 50, 100, 200, 500])); ax.xaxis.set_major_formatter(FixedFormatter(["10", "20", "50", "100", "200", "500"])); ax.yaxis.set_major_locator(FixedLocator([20, 50, 100, 200, 500, 1000])); ax.yaxis.set_major_formatter(FixedFormatter(["20", "50", "100", "200", "500", "1,000"])); ax.minorticks_off(); ax.set_xlabel("Coastline nearer to this station than to any other (km, Natural Earth 1:10m)"); ax.set_ylabel("Launches 2021 to 2025")
xx = np.geomspace(C.coast_km_10m.min(), C.coast_km_10m.max(), 50)
a = np.exp(np.log(C.launches).mean() - R["H6"]["el"] * np.log(C.coast_km_10m).mean())
ax.plot(xx, a * xx ** R["H6"]["el"], color=INK, lw=1.4, ls="--")
ax.plot(xx, np.exp(np.log(C.launches).mean() - np.log(C.coast_km_10m).mean()) * xx, color=MUT, lw=1, ls=":")
ax.text(xx[-1], a * xx[-1] ** R["H6"]["el"] * 1.15, f"fitted: elasticity {R['H6']['el']:.2f}", ha="right", fontsize=10.5, path_effects=HALO)
ax.text(xx[44], np.exp(np.log(C.launches).mean() - np.log(C.coast_km_10m).mean()) * xx[44] * 1.1, "if launches grew in\nstep with coast length", ha="right", va="bottom", fontsize=10, color=MUT, path_effects=HALO)
for nm in ["Blackpool", "Plymouth", "Aith", "Leverburgh"]:
    r_ = C[C.station == nm].iloc[0]
    ax.annotate(nm, (r_.coast_km_10m, r_.launches), xytext=(5, 3), textcoords="offset points", fontsize=9.5, color=INK, path_effects=HALO)
ax.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=10)
ax2 = fig.add_axes([0.75, 0.13, 0.22, 0.66])
top = R["per10"]["top"][:10]
ax2.barh(range(len(top)), [t["per10"] for t in top], color="#B4442E", height=0.6)
ax2.set_yticks(range(len(top))); ax2.set_yticklabels([t["station"] for t in top], fontsize=10); ax2.invert_yaxis()
ax2.set_xlabel("Launches per 10 km of coast"); ax2.axvline(R["per10"]["median"], color=MUT, lw=0.8, ls=":")
ax2.text(R["per10"]["median"] + 6, -0.75, f"median station: {R['per10']['median']:.0f}", fontsize=9, color=MUT)
title(fig, "Busy stations are not the ones with most coast", f"{len(C)} coastal stations; a station with twice the coastline had about {R['prose']['h6_double']:.0f}% more launches (95% interval {R['prose']['h6_double_lo']:.0f} to {R['prose']['h6_double_hi']:.0f}%)")
foot(fig); out(fig, "coast")

# ---------------- 7. robustness forest
fig = plt.figure(figsize=(12, 7.6))
rows = [dict(label="Main model", **{k: R["H12"][k] for k in ("alb", "commercial", "powered and sail craft")})] + R["H12_robust"]
for j, (k, nm) in enumerate((("alb", "All-weather vs inshore boat"), ("commercial", "Commercial vs people in the water"), ("powered and sail craft", "Powered and sail craft vs people in the water"))):
    ax = fig.add_axes([0.30 + j * 0.235, 0.08, 0.20, 0.76])
    for i, r_ in enumerate(rows):
        v = r_[k]; ax.plot([v["lo"], v["hi"]], [i, i], color=INK if i else "#B4442E", lw=1.4); ax.plot(v["b"], i, "o", color=INK if i else "#B4442E", ms=5)
    ax.axvline(0, color=MUT, lw=0.8); ax.set_ylim(len(rows) - 0.5, -0.5); ax.set_title(nm, fontsize=10.5, loc="left", color=INK)
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r_["label"] for r_ in rows] if j == 0 else [], fontsize=9.5)
    ax.set_xlabel("% difference in distance"); ax.grid(axis="x", color=RULE, lw=0.6)
title(fig, "The distance results across every planned check", "Within-station differences in distance from station to incident, 95% intervals clustered by station (main model in red)")
foot(fig); out(fig, "robust", blog=False)
print("figures done")
