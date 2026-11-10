"""Step 3: data/results.json (every quoted number), aggregate data tables and data/site.json for the page.
Only aggregates are written: counts by station, by month, by hour and on a 1 km grid (the RNLI licence does not permit
redistributing the launch records)."""
import numpy as np, pandas as pd
from pyproj import Transformer
from common import *

L = pd.read_pickle(f"{SCR}/launches.pkl")
S = pd.read_csv(f"{DATA}/stations.csv")
M = jload(f"{SCR}/models.json")
F = jload(f"{SCR}/flow.json")
R = dict(M)
R["flow"] = F
R["n"] = F["analysed"]
R["n_located"] = F["located"]
R["years"] = "2021 to 2025"
R["n_stations"] = int((S.launches > 0).sum())
R["per_day"] = F["analysed"] / 1826
R["per_year"] = F["analysed"] / 5
R["flow"]["flipped_pc"] = F["flipped"] / F["analysed"] * 100
R["flow"]["loc_err_pc"] = F["loc_err"] / F["analysed"] * 100
R["flow"]["x_pos_ok"] = F["x_pos"] - F["flipped"]
R["btype_pc"] = {k: v / F["analysed"] * 100 for k, v in M["btype_n"].items()}
R["group_pc"] = {k: v / F["analysed"] * 100 for k, v in M["group_n"].items()}
oth = L.groupby("year").apply(lambda q: (q.ctype == "Other").mean() * 100)
R["other_share"] = [float(v) for v in oth.values]
R["other_n"] = [int(v) for v in L[L.ctype == "Other"].groupby("year").size().values]
R["specific_trend"] = {}
# prose helpers
d = M["dist"]
R["prose"] = dict(
    alb_x=d["ALB"]["med"] / d["ILB"]["med"],
    alb_pc=M["H12"]["alb"]["b"],
    pw_vs_comm_summer=M["H3"]["vs_commercial_powered and sail craft"]["rr"],
    other_2021=R["other_share"][0], other_2025=R["other_share"][-1],
    total_2021=M["annual"]["all"][0], total_2025=M["annual"]["all"][-1],
    paddle_dark=M["dark"]["paddle and board craft"]["pc"],
    tower_pc=M["stations_conc"]["tower"] / F["analysed"] * 100,
    tower_per_day=M["stations_conc"]["tower"] / 1826,
    h6_el=M["H6"]["el"],
    h6_double=100 * (2 ** M["H6"]["el"] - 1),
    h6_double_lo=100 * (2 ** M["H6"]["lo"] - 1), h6_double_hi=100 * (2 ** M["H6"]["hi"] - 1),
    per10_ratio=M["per10"]["top"][0]["per10"] / M["per10"]["median"],
)
# checks summary
rb = M["H12_robust"]
R["robust_n"] = len(rb)
R["robust_range"] = dict(alb_min=min(x["alb"]["b"] for x in rb), alb_max=max(x["alb"]["b"] for x in rb),
                         alb_lo_min=min(x["alb"]["lo"] for x in rb),
                         comm_min=min(x["commercial"]["b"] for x in rb), comm_max=max(x["commercial"]["b"] for x in rb),
                         comm_sig=sum(x["commercial"]["lo"] > 0 for x in rb),
                         pw_sig_pos=sum(x["powered and sail craft"]["lo"] > 0 for x in rb),
                         pw_sig_neg=sum(x["powered and sail craft"]["hi"] < 0 for x in rb),
                         paddle_sig_neg=sum(x["paddle and board craft"]["hi"] < 0 for x in rb))
h6r = M["H6_robust"]
R["h6_range"] = dict(n=len(h6r), lo=min(x["el"] for x in h6r), hi=max(x["el"] for x in h6r), n_sig=sum(x["lo"] > 0 for x in h6r),
                     max_hi=max(x["hi"] for x in h6r))
h5r = M["H5_robust"]
R["h5_range"] = dict(n=len(h5r), all_lo=min(x["all"]["b"] for x in h5r), all_hi=max(x["all"]["b"] for x in h5r),
                     all_sig=sum((x["all"]["lo"] > 0) or (x["all"]["hi"] < 0) for x in h5r),
                     paddle_sig=sum(x["paddle and board craft"]["hi"] < 0 for x in h5r),
                     other_sig=sum(x["other or unknown"]["lo"] > 0 for x in h5r))
for g in GROUPS:
    R["h5_range"][g + "_sig"] = sum((x[g]["hi"] < 0) for x in h5r)

# assertions for every claim made in words
assert M["H12"]["alb"]["lo"] > 0 and all(x["alb"]["lo"] > 0 for x in rb)
assert M["H12"]["commercial"]["lo"] > 0 and R["robust_range"]["comm_sig"] == len(rb)
assert M["H12"]["powered and sail craft"]["lo"] < 0 < M["H12"]["powered and sail craft"]["hi"]
assert M["placebo_perm"]["share_ge"] == 0
for g in ("powered and sail craft", "paddle and board craft", "people in the water"):
    assert M["H3"]["vs_commercial_" + g]["lo"] > 1
assert M["H3"]["vs_commercial_people on the shore"]["lo"] < 1 < M["H3"]["vs_commercial_people on the shore"]["hi"]
assert M["H3b"]["commercial"]["lo"] > 1  # commercial also busier at weekends (said so)
assert all(M["H3b"]["vs_commercial_" + g]["lo"] > 1 for g in ("powered and sail craft", "paddle and board craft", "people in the water", "people on the shore"))
assert M["H5"]["all"]["lo"] < 0 < M["H5"]["all"]["hi"] and M["H5"]["other or unknown"]["lo"] > 0
assert M["H6"]["lo"] < 0 < M["H6"]["hi"] and M["H6"]["hi"] < 0.5
assert M["dark"]["paddle and board craft"]["hi"] < 5
assert abs(M["dark"]["ALB"]["pc"] - M["dark"]["ILB"]["pc"]) < 1.5
assert M["top_stations"][0]["station"] == "Tower" and M["top_stations"][1]["station"] == "Chiswick"
assert M["season_all"]["peak_month"] == 8

# ---------- data tables
mc = L.groupby(["year", "month", "group"]).size().unstack(fill_value=0).reindex(columns=GROUPS, fill_value=0)
mc["all"] = mc.sum(axis=1); mc.reset_index().to_csv(f"{DATA}/monthly_counts.csv", index=False)
hc = L.groupby(["hour", "group"]).size().unstack(fill_value=0).reindex(columns=GROUPS, fill_value=0)
hc["ALB"] = L[L.btype == "ALB"].groupby("hour").size(); hc["ILB"] = L[L.btype == "ILB"].groupby("hour").size()
hc.reset_index().to_csv(f"{DATA}/hourly_counts.csv", index=False)
tc = L.groupby(["year", "ctype"]).size().unstack(0, fill_value=0)
tc["group"] = [L[L.ctype == t].group.mode()[0] for t in tc.index]
tc.reset_index().to_csv(f"{DATA}/casualty_types_by_year.csv", index=False)

# station table with groups
S = S.drop(columns=[c for c in GROUPS + ["per10km_coast", "dark_pc"] if c in S.columns])
gs = L.groupby(["key", "group"]).size().unstack(fill_value=0).reindex(columns=GROUPS, fill_value=0)
S = S.join(gs, on="key").fillna({g: 0 for g in GROUPS})
S["per10km_coast"] = np.where(S.coast_km_10m > 0, S.launches / S.coast_km_10m.replace(0, np.nan) * 10, np.nan)
S["dark_pc"] = S.key.map(L[~L.loc_err].groupby("key").dark.mean() * 100)
S.to_csv(f"{DATA}/stations.csv", index=False, float_format="%.4f")

# 1 km grid
Lk = L[~L.loc_err].copy()
tr = Transformer.from_crs(4326, 3035, always_xy=True); bk = Transformer.from_crs(3035, 4326, always_xy=True)
ex, ey = tr.transform(Lk.lon.values, Lk.lat.values)
Lk["cx"] = np.floor(ex / 1000).astype(int); Lk["cy"] = np.floor(ey / 1000).astype(int)
BT = ["ALB", "ILB", "other"]
Lk["bi"] = Lk.btype.map({"ALB": 0, "ILB": 1}).fillna(2).astype(int)
Lk["gi"] = Lk.group.map({g: i for i, g in enumerate(GROUPS)})
Lk["yi"] = Lk.year - 2021
g = Lk.groupby(["cx", "cy", "yi", "bi", "gi"]).size().rename("n").reset_index()
cells = g.groupby(["cx", "cy"])
rows, site_cells = [], []
for (cx, cy), q in cells:
    lon, lat = bk.transform(cx * 1000 + 500, cy * 1000 + 500)
    n = int(q.n.sum())
    site_cells.append([round(lon, 4), round(lat, 4), [[int(a), int(b), int(c), int(m)] for a, b, c, m in q[["yi", "bi", "gi", "n"]].values]])
    rows.append(dict(lon=round(lon, 5), lat=round(lat, 5), launches=n, **{f"y{y}": int(q[q.yi == y - 2021].n.sum()) for y in YEARS},
                     **{f"b_{b}": int(q[q.bi == i].n.sum()) for i, b in enumerate(BT)}, **{g_: int(q[q.gi == i].n.sum()) for i, g_ in enumerate(GROUPS)}))
G = pd.DataFrame(rows)
G.sort_values("launches", ascending=False).to_csv(f"{DATA}/grid_1km.csv", index=False)
R["grid1"] = dict(n_cells=len(G), max=int(G.launches.max()), single=int((G.launches == 1).sum()))

# coast dots for the page (every second 1 km piece), coloured by the station's launches per 10 km of coast
P = np.load(f"{SCR}/coast10.npy")
Sall = pd.read_csv(f"{DATA}/stations.csv")
Sraw = pd.DataFrame([dict(x["attributes"]) for x in jload(f"{RAW}/rnli_stations.json")])
# station index in coast10 refers to the 01_data.py frame order (station list + Chiswick); rebuild that order
order = list(Sraw.Station.map(norm)) + ["chiswick"]
P = P[P[:, 4] <= CATCH_KM][::2]
cl, ca = bk.transform(P[:, 0], P[:, 1])
site_coast = [[round(a, 3), round(b, 3), Sall.index[Sall.key == order[int(i)]][0]] for a, b, i in zip(cl, ca, P[:, 3])]

# site.json
stns = []
for r in Sall.itertuples():
    if r.launches == 0:
        continue
    q = L[L.key == r.key]
    stns.append(dict(n=r.station, la=round(r.lat, 4), lo=round(r.lon, 4), t=r.stype, rg=r.Region, c=r.Country, u=r.URL if isinstance(r.URL, str) else "",
                     a=r.AllAssets if isinstance(r.AllAssets, str) else "", N=int(r.launches),
                     y=[int(getattr(r, f"y{y}")) for y in YEARS], b=[int(r.n_ALB), int(r.n_ILB), int(r.launches - r.n_ALB - r.n_ILB)],
                     g=[int((q.group == g_).sum()) for g_ in GROUPS],
                     md=None if pd.isna(r.med_km) else round(float(r.med_km), 1),
                     ck=None if r.inland else round(float(r.coast_km_10m), 0),
                     p10=None if (r.inland or r.coast_km_10m <= 0) else round(float(r.launches / r.coast_km_10m * 10), 1),
                     inl=bool(r.inland), dk=None if pd.isna(r.dark_pc) else round(float(r.dark_pc), 0),
                     tp=q.ctype.value_counts().head(3).index.tolist(),
                     x=[[int(a), int(b), int(c), int(m)] for (a, b, c), m in q.assign(yi=q.year - 2021, bi=q.btype.map({'ALB': 0, 'ILB': 1}).fillna(2).astype(int), gi=q.group.map({g_: i for i, g_ in enumerate(GROUPS)})).groupby(['yi', 'bi', 'gi']).size().items()]))
site = dict(groups=GROUPS, cells=site_cells, stations=stns, coast=[[a, b, int(i)] for a, b, i in site_coast])
jsave(site, f"{DATA}/site.json", keepdash=True)
print("site.json", os.path.getsize(f"{DATA}/site.json") // 1024, "KB", len(site_cells), "cells", len(stns), "stations", len(site_coast), "coast dots")
jsave(R, f"{DATA}/results.json", indent=1, keepdash=True)
print("results.json written")
