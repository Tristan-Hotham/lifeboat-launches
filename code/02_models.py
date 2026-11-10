"""Step 2: the planned analysis (NOTES.md, H1 to H6, hotspots, checks). Writes SCR/models.json and data/models.csv."""
import warnings
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
from pyproj import Transformer
from common import *

warnings.filterwarnings("ignore")
L = pd.read_pickle(f"{SCR}/launches.pkl")
S = pd.read_csv(f"{DATA}/stations.csv")
OUT = {}; ROWS = []
rng = np.random.default_rng(20261110)


def pc(b, se, z=1.959964):
    return dict(b=100 * (np.exp(b) - 1), lo=100 * (np.exp(b - z * se) - 1), hi=100 * (np.exp(b + z * se) - 1), coef=b, se=se,
                p=float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(b / se)))))


def rr(b, se, z=1.959964):
    return dict(rr=np.exp(b), lo=np.exp(b - z * se), hi=np.exp(b + z * se), coef=b, se=se)


def rec(model, label, key, v, n):
    ROWS.append(dict(model=model, label=label, term=key, n=n, **{k: v[k] for k in v if k in ("b", "lo", "hi", "rr", "coef", "se", "p")}))


D = L[~L.loc_err & L.btype.isin(["ALB", "ILB"])].copy()
D["ld"] = np.log(D.dist + 0.1)
D["alb"] = (D.btype == "ALB").astype(int)
D["sy"] = D.key + "_" + D.year.astype(str)
GREF = "people in the water"
GO = [g for g in GROUPS if g != GREF]


def h12(df, label, cluster="key", fe="C(key) + C(year) + C(month)"):
    """H1 and H2 in one call: returns ALB effect (H1 model) and group effects (H2 model)."""
    df = df.copy()
    m1 = smf.ols(f"ld ~ alb + {fe}", df).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df[cluster])[0]})
    res = {"n": int(m1.nobs), "stations": int(df.key.nunique()), "alb": pc(m1.params["alb"], m1.bse["alb"])}
    df["g"] = pd.Categorical(df.group, categories=[GREF] + GO)
    m2 = smf.ols(f"ld ~ C(g) + alb + {fe}", df).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df[cluster])[0]})
    for g in GO:
        k = f"C(g)[T.{g}]"
        res[g] = pc(m2.params[k], m2.bse[k])
    res["alb_h2"] = pc(m2.params["alb"], m2.bse["alb"])
    rec("H1", label, "alb", res["alb"], res["n"])
    for g in GO:
        rec("H2", label, g, res[g], res["n"])
    return res


# ---------------- H1 / H2 main
OUT["H12"] = h12(D, "main")
print("H1", OUT["H12"]["alb"])

# medians with station-cluster bootstrap
def boot_median(df, B=1000, q=0.5):
    arrs = [g.dist.values for _, g in df.groupby("key")]
    est = float(np.quantile(df.dist, q)); bs = []
    for _ in range(B):
        idx = rng.integers(0, len(arrs), len(arrs))
        bs.append(np.quantile(np.concatenate([arrs[i] for i in idx]), q))
    return dict(med=est, lo=float(np.quantile(bs, .025)), hi=float(np.quantile(bs, .975)), n=len(df))


OUT["dist"] = {"all": boot_median(D), "ALB": boot_median(D[D.alb == 1]), "ILB": boot_median(D[D.alb == 0])}
Dall = L[~L.loc_err]
OUT["dist"]["all_types"] = dict(med=float(Dall.dist.median()), n=len(Dall), within2=float((Dall.dist <= 2).mean() * 100),
                               within5=float((Dall.dist <= 5).mean() * 100), within10=float((Dall.dist <= 10).mean() * 100),
                               over20=float((Dall.dist > 20).mean() * 100), over50=float((Dall.dist > 50).mean() * 100),
                               p90=float(Dall.dist.quantile(.9)), p99=float(Dall.dist.quantile(.99)), max=float(Dall.dist.max()))
for b in ("ALB", "ILB", "IRH", "RWC"):
    q = Dall[Dall.btype == b].dist
    OUT["dist"].setdefault(b, {}).update(dict(p25=float(q.quantile(.25)), p75=float(q.quantile(.75)), p90=float(q.quantile(.9)),
                                              within5=float((q <= 5).mean() * 100), over20=float((q > 20).mean() * 100), n_all=len(q),
                                              med_all=float(q.median())))
OUT["dist_group"] = {}
for g in GROUPS:
    q = D[D.group == g]
    OUT["dist_group"][g] = dict(boot_median(q, B=400), alb_pc=float(q.alb.mean() * 100),
                                med_alb=float(q[q.alb == 1].dist.median()), med_ilb=float(q[q.alb == 0].dist.median()),
                                p90=float(q.dist.quantile(.9)))
# within-station paired comparison (stations with both boat types, 30+ launches each): share where ALB median > ILB median
both = D.groupby(["key", "alb"]).dist.agg(["median", "size"]).unstack()
both = both[(both[("size", 0)] >= 30) & (both[("size", 1)] >= 30)]
OUT["paired"] = dict(n=len(both), alb_further=int((both[("median", 1)] > both[("median", 0)]).sum()),
                     ratio_median=float((both[("median", 1)] / both[("median", 0)]).median()))

# placebo: permute boat type within station
X = pd.get_dummies(D[["key", "year", "month"]].astype(str), drop_first=True).astype(float).values
X = np.c_[np.ones(len(D)), X]
y = D.ld.values
Q, _ = np.linalg.qr(X)
ry = y - Q @ (Q.T @ y)
def coef_of(a):
    ra = a - Q @ (Q.T @ a)
    return float(ra @ ry / (ra @ ra))
obs = coef_of(D.alb.values.astype(float))
grp = D.key.values; alb = D.alb.values.astype(float); perm = []
idx_by = [np.where(grp == k)[0] for k in np.unique(grp)]
for _ in range(200):
    a = alb.copy()
    for ix in idx_by:
        a[ix] = rng.permutation(a[ix])
    perm.append(coef_of(a))
perm = np.array(perm)
OUT["placebo_perm"] = dict(obs=obs, obs_pc=100 * (np.exp(obs) - 1), mean=float(perm.mean()), mean_pc=float(100 * (np.exp(perm.mean()) - 1)),
                           p025=float(100 * (np.exp(np.quantile(perm, .025)) - 1)), p975=float(100 * (np.exp(np.quantile(perm, .975)) - 1)),
                           max_pc=float(100 * (np.exp(perm.max()) - 1)), n_perm=len(perm), share_ge=float((perm >= obs).mean()))
print("placebo", OUT["placebo_perm"])

# ---------------- H1/H2 checks
R = []
def chk(label, group, df, **kw):
    r = h12(df, label, **kw); r.update(label=label, group=group); R.append(r)
chk("Station-year clusters", "Inference", D, cluster="sy")
chk("Station-by-year fixed effects", "Specification", D, fe="C(sy) + C(month)")
chk("No sign-flipped longitudes", "Measurement", D[~D.flipped])
chk("No points at the station (within 50 m)", "Measurement", D[~D.stacked])
chk("Coastal stations only (no rivers or lakes)", "Measurement", D[~D.inland.astype(bool)])
chk("Arrived on scene only", "Sample", D[D.arrived == 1])
chk("No stood-down or false-alarm launches", "Sample", D[D.standdown == 0])
D2 = L[L.btype.isin(["ALB", "ILB"]) & (L.dist <= L.btype.map({"ALB": 150.0, "ILB": 60.0}))].copy()
D2["ld"] = np.log(D2.dist + 0.1); D2["alb"] = (D2.btype == "ALB").astype(int); D2["sy"] = D2.key + "_" + D2.year.astype(str)
chk("Error cut-offs 60 km (inshore) and 150 km (all-weather)", "Measurement", D2)
for reg in sorted(D.region.unique()):
    chk(f"Without {reg}", "Leave one region out", D[D.region != reg])
OUT["H12_robust"] = R
# median (quantile) regression: within-station via demeaned? use station dummies on a 50% station-stratified sample for speed
qr = smf.quantreg("ld ~ alb + C(g) + C(key)", D.assign(g=pd.Categorical(D.group, categories=[GREF] + GO))).fit(q=0.5, max_iter=2000)
OUT["H12_quant"] = {"alb": float(100 * (np.exp(qr.params["alb"]) - 1)), "alb_lo": float(100 * (np.exp(qr.conf_int().loc["alb", 0]) - 1)),
                    "alb_hi": float(100 * (np.exp(qr.conf_int().loc["alb", 1]) - 1))}
for g in GO:
    k = f"C(g)[T.{g}]"; ci = qr.conf_int().loc[k]
    OUT["H12_quant"][g] = dict(b=float(100 * (np.exp(qr.params[k]) - 1)), lo=float(100 * (np.exp(ci[0]) - 1)), hi=float(100 * (np.exp(ci[1]) - 1)))
print("quant", OUT["H12_quant"]["alb"])

# ---------------- H3 season (monthly counts by group)
L["ym"] = L.year * 100 + L.month
M = L.groupby(["group", "year", "month"]).size().reindex(pd.MultiIndex.from_product([GROUPS, YEARS, range(1, 13)], names=["group", "year", "month"]), fill_value=0).rename("n").reset_index()
M["summer"] = M.month.isin([6, 7, 8]).astype(int); M["winter"] = M.month.isin([12, 1, 2]).astype(int)
M["g"] = pd.Categorical(M.group, categories=GROUPS)


def season(Mx, label):
    m = smf.glm("n ~ C(g):C(year) + C(g):summer + C(g):winter - 1", Mx, family=sm.families.Poisson()).fit(cov_type="HC1")
    res = {}
    V = m.cov_params()
    for g in GROUPS:
        a, b = f"C(g)[{g}]:summer", f"C(g)[{g}]:winter"
        est = m.params[a] - m.params[b]; se = np.sqrt(V.loc[a, a] + V.loc[b, b] - 2 * V.loc[a, b])
        res[g] = rr(est, se); res[g]["summer_share"] = float(Mx[(Mx.group == g) & (Mx.summer == 1)].n.sum() / Mx[Mx.group == g].n.sum() * 100)
        rec("H3", label, g, res[g], int(Mx[Mx.group == g].n.sum()))
    ca, cb = "C(g)[commercial]:summer", "C(g)[commercial]:winter"
    for g in GROUPS[1:]:
        a, b = f"C(g)[{g}]:summer", f"C(g)[{g}]:winter"
        w = pd.Series(0.0, index=m.params.index); w[a] = 1; w[b] = -1; w[ca] = -1; w[cb] = 1
        est = float(w @ m.params); se = float(np.sqrt(w @ V @ w))
        res["vs_commercial_" + g] = rr(est, se)
    return res


OUT["H3"] = season(M, "main")
tot = L.groupby("month").size()
OUT["season_all"] = dict(summer_share=float(tot[[6, 7, 8]].sum() / tot.sum() * 100), winter_share=float(tot[[12, 1, 2]].sum() / tot.sum() * 100),
                         aug_per_day=float(tot[8] / 5 / 31), jan_per_day=float(tot[1] / 5 / 31), peak_month=int(tot.idxmax()), low_month=int(tot.idxmin()))
OUT["season_all"]["aug_jan"] = OUT["season_all"]["aug_per_day"] / OUT["season_all"]["jan_per_day"]
print("H3", {g: round(OUT["H3"][g]["rr"], 2) for g in GROUPS})

# ---------------- H3b weekend (daily counts by group)
days = pd.date_range("2021-01-01", "2025-12-31")
Dd = L.groupby(["group", "date"]).size().reindex(pd.MultiIndex.from_product([GROUPS, days], names=["group", "date"]), fill_value=0).rename("n").reset_index()
Dd["weekend"] = (Dd.date.dt.dayofweek >= 5).astype(int); Dd["ym"] = Dd.date.dt.year * 100 + Dd.date.dt.month
Dd["g"] = pd.Categorical(Dd.group, categories=GROUPS)
mw = smf.glm("n ~ C(g):C(ym) + C(g):weekend - 1", Dd, family=sm.families.Poisson()).fit(cov_type="HC1")
OUT["H3b"] = {}
V = mw.cov_params()
for g in GROUPS:
    a = f"C(g)[{g}]:weekend"; OUT["H3b"][g] = rr(mw.params[a], mw.bse[a]); rec("H3b", "main", g, OUT["H3b"][g], int(Dd[Dd.group == g].n.sum()))
for g in GROUPS[1:]:
    a, c = f"C(g)[{g}]:weekend", "C(g)[commercial]:weekend"
    est = mw.params[a] - mw.params[c]; se = np.sqrt(V.loc[a, a] + V.loc[c, c] - 2 * V.loc[a, c]); OUT["H3b"]["vs_commercial_" + g] = rr(est, se)
tw = L.groupby("weekend").size(); nwd = (days.dayofweek >= 5).sum()
OUT["H3b"]["all_ratio"] = float((tw[1] / nwd) / (tw[0] / (len(days) - nwd)))
print("H3b", {g: round(OUT["H3b"][g]["rr"], 2) for g in GROUPS})

# ---------------- H4 hour and darkness
def wilson(k, n, z=1.959964):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return dict(pc=100 * p, lo=100 * (c - h), hi=100 * (c + h), n=int(n), k=int(k))


Lk = L[~L.loc_err]
OUT["dark"] = {"all": wilson(Lk.dark.sum(), len(Lk))}
for b in ("ALB", "ILB"):
    OUT["dark"][b] = wilson(Lk[Lk.btype == b].dark.sum(), (Lk.btype == b).sum())
for g in GROUPS:
    OUT["dark"][g] = wilson(Lk[Lk.group == g].dark.sum(), (Lk.group == g).sum())
hp = L.groupby(["group", "hour"]).size().unstack(fill_value=0)
OUT["hour"] = {g: [int(v) for v in hp.loc[g].values] for g in GROUPS}
OUT["hour"]["ALB"] = [int(v) for v in L[L.btype == "ALB"].groupby("hour").size().reindex(range(24), fill_value=0)]
OUT["hour"]["ILB"] = [int(v) for v in L[L.btype == "ILB"].groupby("hour").size().reindex(range(24), fill_value=0)]
ha = L.groupby("hour").size()
OUT["hour_all"] = dict(peak=int(ha.idxmax()), low=int(ha.idxmin()), peak_n=int(ha.max()), low_n=int(ha.min()),
                       day_10_20=float(ha[10:20].sum() / ha.sum() * 100))

# ---------------- H5 trend
def trend(df, label, years=YEARS, fam="poisson"):
    res = {}
    for g in GROUPS + ["all"]:
        q = df if g == "all" else df[df.group == g]
        c = q.groupby(["year", "month"]).size().reindex(pd.MultiIndex.from_product([years, range(1, 13)], names=["year", "month"]), fill_value=0).rename("n").reset_index()
        c["t"] = c.year - 2023
        famobj = sm.families.Poisson() if fam == "poisson" else sm.families.NegativeBinomial(alpha=0.05)
        m = smf.glm("n ~ t + C(month)", c, family=famobj).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
        res[g] = pc(m.params["t"], m.bse["t"]); res[g]["n"] = int(c.n.sum())
        rec("H5", label, g, res[g], int(c.n.sum()))
    return res


OUT["H5"] = trend(L, "main")
OUT["H5_robust"] = [dict(label="Negative binomial", **trend(L, "Negative binomial", fam="nb")),
                    dict(label="Without 2021", **trend(L[L.year > 2021], "Without 2021", years=YEARS[1:])),
                    dict(label="No stood-down or false-alarm launches", **trend(L[L.standdown == 0], "No stood-down")),
                    dict(label="Coastal stations only", **trend(L[~L.inland.astype(bool)], "Coastal only"))]
for reg in sorted(L.region.dropna().unique()):
    OUT["H5_robust"].append(dict(label=f"Without {reg}", **trend(L[L.region != reg], f"Without {reg}")))
yr = L.groupby(["group", "year"]).size().unstack(fill_value=0)
OUT["annual"] = {g: [int(v) for v in yr.loc[g].values] for g in GROUPS}
OUT["annual"]["all"] = [int(v) for v in L.groupby("year").size().values]
OUT["annual"]["ALB"] = [int(v) for v in L[L.btype == "ALB"].groupby("year").size().values]
OUT["annual"]["ILB"] = [int(v) for v in L[L.btype == "ILB"].groupby("year").size().values]
for t in ("paddleboard", "kayak/canoe", "person in water", "motorboat", "commercial fishing", "walker/runner", "animal (dog)"):
    OUT["annual"]["t_" + t] = [int(v) for v in L[L.ctype.str.lower() == t].groupby("year").size().reindex(YEARS, fill_value=0).values]
pb = L[L.ctype.str.lower() == "paddleboard"]
c = pb.groupby(["year", "month"]).size().reindex(pd.MultiIndex.from_product([YEARS, range(1, 13)], names=["year", "month"]), fill_value=0).rename("n").reset_index(); c["t"] = c.year - 2023
m = smf.glm("n ~ t + C(month)", c, family=sm.families.Poisson()).fit(cov_type="HAC", cov_kwds={"maxlags": 12})
OUT["H5_paddleboard_explore"] = pc(m.params["t"], m.bse["t"])
print("H5", {g: round(OUT["H5"][g]["b"], 1) for g in OUT["H5"]})

# ---------------- H6 station workload vs coast
CS = S[~S.inland & (S.launches > 0)].copy()
CS["lc"] = np.log(CS.coast_km_10m); CS["lc50"] = np.log(CS.coast_km_50m.clip(lower=1)); CS["lc30"] = np.log(CS.coast_km_10m_30.clip(lower=1))
CS["alb"] = (CS.stype == "ALB").astype(int)


def h6(df, label, x="lc", fam="ppml"):
    if fam == "ppml":
        m = smf.glm(f"launches ~ {x} + alb + C(Region)", df, family=sm.families.Poisson()).fit(cov_type="HC1")
    else:
        m = smf.ols(f"np.log(launches) ~ {x} + alb + C(Region)", df).fit(cov_type="HC1")
    ci = m.conf_int().loc[x]
    r = dict(el=float(m.params[x]), lo=float(ci[0]), hi=float(ci[1]), se=float(m.bse[x]), n=int(m.nobs),
             alb=pc(m.params["alb"], m.bse["alb"]), label=label)
    ROWS.append(dict(model="H6", label=label, term="log coast km", n=r["n"], coef=r["el"], se=r["se"], lo=r["lo"], hi=r["hi"]))
    return r


OUT["H6"] = h6(CS, "main")
OUT["H6_robust"] = [h6(CS, "OLS of log launches", fam="ols"), h6(CS, "Coastline at 1:50m", x="lc50"), h6(CS, "Catchment 30 km", x="lc30")]
for reg in sorted(CS.Region.unique()):
    OUT["H6_robust"].append(h6(CS[CS.Region != reg], f"Without {reg}"))
CS["per10"] = CS.launches / CS.coast_km_10m * 10
C10 = CS[CS.coast_km_10m >= 10]
OUT["per10"] = dict(median=float(CS.per10.median()), top=[dict(station=r.station, per10=float(r.per10), launches=int(r.launches), coast=float(r.coast_km_10m))
                                                         for r in C10.sort_values("per10", ascending=False).head(12).itertuples()],
                    bottom=[dict(station=r.station, per10=float(r.per10), launches=int(r.launches), coast=float(r.coast_km_10m))
                            for r in C10.sort_values("per10").head(5).itertuples()], n=len(C10))
OUT["corr_coast"] = float(np.corrcoef(CS.lc, np.log(CS.launches))[0, 1])
print("H6", OUT["H6"])

# ---------------- stations and hotspots
Sx = S[S.launches > 0].sort_values("launches", ascending=False)
OUT["top_stations"] = [dict(station=r.station, launches=int(r.launches), per_year=float(r.launches / 5), stype=r.stype, region=r.Region) for r in Sx.head(15).itertuples()]
v = np.sort(Sx.launches.values)
gini = lambda v: float(1 - 2 * np.sum(np.cumsum(v) / v.sum()) / len(v) + 1 / len(v))
OUT["stations_conc"] = dict(n=len(v), gini=gini(v), top10_share=float(v[-10:].sum() / v.sum() * 100), median=float(np.median(v)),
                            median_per_year=float(np.median(v) / 5), thames=int(L[L.key.isin(THAMES)].shape[0]),
                            thames_pc=float(L.key.isin(THAMES).mean() * 100), tower=int((L.key == "tower").sum()))
tr = Transformer.from_crs(4326, 3035, always_xy=True)
ex, ey = tr.transform(Lk.lon.values, Lk.lat.values)
cell = 2000
cx, cy = (np.floor(ex / cell)).astype(int), (np.floor(ey / cell)).astype(int)
cid = pd.Series(list(zip(cx, cy)))
cc = cid.value_counts()
vv = cc.values
OUT["cells"] = dict(km=cell / 1000, n_cells=len(cc), top1_share=float(vv[:max(1, len(vv) // 100)].sum() / vv.sum() * 100),
                    top10_share=float(vv[:len(vv) // 10].sum() / vv.sum() * 100), gini=gini(np.sort(vv)), single=int((vv == 1).sum()),
                    half_cells=int(np.searchsorted(np.cumsum(vv), vv.sum() / 2) + 1))
OUT["cells"]["half_cells_pc"] = OUT["cells"]["half_cells"] / len(cc) * 100
Lk = Lk.assign(cell=cid.values)
top = []
for (a, b), n in cc.head(12).items():
    q = Lk[Lk.cell == (a, b)]
    top.append(dict(n=int(n), station=q.station.value_counts().index[0], lat=float(q.lat.mean()), lon=float(q.lon.mean()),
                    main_group=q.group.value_counts().index[0], main_type=q.ctype.value_counts().index[0]))
OUT["top_cells"] = top
# conditions and outcomes
OUT["conditions"] = dict(calm_slight=float(L.sea.isin(["CALM", "SMOOTH", "SLIGHT"]).sum() / (L.sea != "UNKNOWN").sum() * 100),
                         rough_high=float(L.sea.isin(["ROUGH", "HIGH"]).sum() / (L.sea != "UNKNOWN").sum() * 100),
                         vis_good=float(L.vis.isin(["GOOD", "EXCELLENT"]).sum() / (L.vis != "UNKNOWN").sum() * 100),
                         sea_known=int((L.sea != "UNKNOWN").sum()), vis_known=int((L.vis != "UNKNOWN").sum()))
OUT["conditions_by"] = {}
for k, q in [("ALB", L[L.btype == "ALB"]), ("ILB", L[L.btype == "ILB"])] + [(g, L[L.group == g]) for g in GROUPS]:
    kn = q[q.sea != "UNKNOWN"]
    OUT["conditions_by"][k] = dict(rough_high=float(kn.sea.isin(["ROUGH", "HIGH", "MOD/CHOP"]).mean() * 100), n=len(kn))
OUT["outcome"] = {k: float(v) for k, v in (L.outcome.value_counts(normalize=True) * 100).items()}
OUT["arrived_pc"] = float(L.arrived.mean() * 100)
OUT["btype_n"] = {k: int(v) for k, v in L.btype.value_counts().items()}
OUT["group_n"] = {k: int(v) for k, v in L.group.value_counts().items()}
OUT["ctype_n"] = {k: int(v) for k, v in L.ctype.value_counts().items()}
jsave(OUT, f"{SCR}/models.json", indent=1, keepdash=True)
pd.DataFrame(ROWS).to_csv(f"{DATA}/models.csv", index=False, float_format="%.5f")
print("done", len(ROWS), "rows")
