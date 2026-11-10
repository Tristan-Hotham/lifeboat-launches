"""Step 1: clean the launches (rules C1 to C10 in NOTES.md), match stations, distances, darkness; coastline per station.
Writes the cleaned row-level table to SCR/launches.pkl (scratch only: the RNLI licence does not allow redistribution of
the records) and data/stations.csv (station attributes, coast length, counts)."""
import numpy as np, pandas as pd, geopandas as gpd
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import unary_union
from pyproj import Transformer
from common import *

L = pd.DataFrame(jload(f"{RAW}/rnli_return_of_service.json"))
S = pd.DataFrame([dict(x["attributes"], gx=x["geometry"]["x"], gy=x["geometry"]["y"]) for x in jload(f"{RAW}/rnli_stations.json")])
n_raw = len(L)
assert L.ROSNumber.is_unique and n_raw == 45682

# ---- stations (C1)
S["key"] = S.Station.map(norm)
S = S.rename(columns={"Station": "station", "StationType": "stype", "Lat": "lat", "Long": "lon"})
L["key"] = L.LifeboatStationNameProper.map(norm)
train = L.key.isin(["headquarters", "the rnli college"])
ch = L.key == "chiswick"
# Chiswick: not in the current station list; display point = median of its own located launches (C1)
chis = dict(station="Chiswick", stype="ILB", County="Greater London", Division="South East", Region="South East", Country="ENG",
            lat=float(L.loc[ch, "y"].median()), lon=float(L.loc[ch, "x"].median()), key="chiswick", URL="", ALBType=None,
            AllAssets="E-Class", ILBType="E-Class")
S = pd.concat([S, pd.DataFrame([chis])], ignore_index=True)
assert S.key.is_unique
unmatched = sorted(set(L.loc[~train, "key"]) - set(S.key))
assert not unmatched, unmatched
L = L[~train].copy()
st = S.set_index("key")
L["slat"] = L.key.map(st.lat); L["slon"] = L.key.map(st.lon)
L["station"] = L.key.map(st.station); L["region"] = L.key.map(st.Region); L["country"] = L.key.map(st.Country)

# ---- longitude sign (C2) and errors (C3)
d0 = km(L.slat, L.slon, L.y, L.x)
d1 = km(L.slat, L.slon, L.y, -L.x)
flip = (L.x > 0) & (d1 < FLIP_KM) & (d0 > 2 * d1)
L["flipped"] = flip
L["lon"] = np.where(flip, -L.x, L.x); L["lat"] = L.y
L["dist"] = km(L.slat, L.slon, L.lat, L.lon)
L["btype"] = L.RoSType
L["loc_err"] = L.dist > L.btype.map(ERR_KM)
L["stacked"] = L.dist < STACK_KM

# ---- groups (C6), time, darkness (C10)
L["group"] = [group_of(c, t) for c, t in zip(L.CasualtyCategory, L.CasualtyTypeFull)]
L["date"] = pd.to_datetime(L.DateOfLaunch)
L["year"] = L.YearofCall
L["month"] = L.date.dt.month
L["hour"] = L.TimeOfLaunch.str[:2].astype(int)
L["dow"] = L.date.dt.dayofweek
L["weekend"] = (L.dow >= 5).astype(int)
L["sun"] = sun_alt(L.lat.values, L.lon.values, L.DateTimeOfLaunch.values)
L["dark"] = (L.sun < -6).astype(int)
L["outcome"] = L.OutcomeOfService
L["arrived"] = (L.ArrivedOnScene == "Yes").astype(int)
L["standdown"] = L.OutcomeOfService.isin(["Stood down", "False alarm"]).astype(int)
L["sea"] = L.SeaConditionsAtIncident.fillna("UNKNOWN").str.strip()
L["vis"] = L.VisibilityAtIncident.fillna("UNKNOWN").str.strip()
L["ctype"] = L.CasualtyTypeFull.str.strip().str.replace("Motor Vehicle", "Motor vehicle").str.replace("Unknown Craft", "Unknown craft")

# ---- coastline (C5, C9)
tr = Transformer.from_crs(4326, 3035, always_xy=True)
def coast_lines(res):
    if res == "10m":
        g = gpd.read_file(f"{GEO}/ne_10m_admin_0_countries.geojson")
        g = g[g.ADM0_A3.isin(["GBR", "IRL", "IMN", "GGY", "JEY"])]
    else:
        g = gpd.read_file(f"{GEO}/ne_50m_land.geojson").cx[-11.5:2.5, 49:61.5]
    u = unary_union(list(g.to_crs(3035).geometry))
    b = u.boundary
    lines = list(b.geoms) if hasattr(b, "geoms") else [b]
    # keep only rings in the study box
    out = []
    x0, y0 = tr.transform(-11.5, 49.0); x1, y1 = tr.transform(2.5, 61.5)
    for ln in lines:
        c = ln.representative_point()
        lon, lat = Transformer.from_crs(3035, 4326, always_xy=True).transform(c.x, c.y)
        if -11.5 < lon < 2.5 and 49 < lat < 61.5:
            out.append(ln)
    return out


def pieces(lines, step=1000.0):
    P = []
    for ln in lines:
        n = max(1, int(ln.length // step))
        for i in range(n):
            a, b = i * ln.length / n, (i + 1) * ln.length / n
            pa, pb = ln.interpolate(a), ln.interpolate(b)
            P.append(((pa.x + pb.x) / 2, (pa.y + pb.y) / 2, b - a))
    return np.array(P)


sx, sy = tr.transform(S.lon.values, S.lat.values)
S["ex"], S["ey"] = sx, sy
coast = {}
for res in ("10m", "50m"):
    P = pieces(coast_lines(res))
    coast[res] = P
    # distance from each station to nearest coast piece
    dd = np.sqrt((P[:, 0][None, :] - sx[:, None]) ** 2 + (P[:, 1][None, :] - sy[:, None]) ** 2) / 1000
    S[f"coast_d_{res}"] = dd.min(1)
S["inland"] = (S.coast_d_10m > INLAND_KM) | S.key.isin(THAMES)
coastal = ~S.inland.values
for res in ("10m", "50m"):
    P = coast[res]
    dd = np.sqrt((P[:, 0][None, :] - sx[coastal][:, None]) ** 2 + (P[:, 1][None, :] - sy[coastal][:, None]) ** 2) / 1000
    near = dd.argmin(0); dmin = dd.min(0)
    for cut in (CATCH_KM, 30.0):
        w = np.where(dmin <= cut, P[:, 2], 0.0)
        tot = np.bincount(near, weights=w, minlength=coastal.sum()) / 1000
        col = f"coast_km_{res}" + ("" if cut == CATCH_KM else f"_{int(cut)}")
        S[col] = 0.0
        S.loc[coastal, col] = tot
    S.loc[coastal, f"coast_total_{res}"] = P[:, 2].sum() / 1000
# coast pieces for the map/figures: 10m pieces with their station (simplified later)
P = coast["10m"]
dd = np.sqrt((P[:, 0][None, :] - sx[coastal][:, None]) ** 2 + (P[:, 1][None, :] - sy[coastal][:, None]) ** 2) / 1000
np.save(f"{SCR}/coast10.npy", np.c_[P, S.index.values[coastal][dd.argmin(0)], dd.min(0)])

# ---- station counts
L["inland"] = L.key.map(S.set_index("key").inland)
cnt = L.groupby("key").size()
S["launches"] = S.key.map(cnt).fillna(0).astype(int)
for b in ("ALB", "ILB"):
    S[f"n_{b}"] = S.key.map(L[L.btype == b].groupby("key").size()).fillna(0).astype(int)
S["has_alb"] = (S.stype == "ALB").astype(int)
for y in YEARS:
    S[f"y{y}"] = S.key.map(L[L.year == y].groupby("key").size()).fillna(0).astype(int)
S["med_km"] = S.key.map(L[~L.loc_err].groupby("key").dist.median())
L.to_pickle(f"{SCR}/launches.pkl")
keep = ["station", "key", "stype", "Region", "Division", "Country", "County", "lat", "lon", "AllAssets", "URL", "inland",
        "coast_d_10m", "coast_km_10m", "coast_km_50m", "coast_km_10m_30", "launches", "n_ALB", "n_ILB"] + [f"y{y}" for y in YEARS] + ["med_km"]
S[keep].sort_values("launches", ascending=False).to_csv(f"{DATA}/stations.csv", index=False, float_format="%.4f")
flow = dict(raw=n_raw, training=int(train.sum()), analysed=len(L), flipped=int(flip.sum()), x_pos=int((L.x > 0).sum()),
            loc_err=int(L.loc_err.sum()), stacked=int(L.stacked.sum()), located=int((~L.loc_err).sum()),
            chiswick=int(ch.sum()), stations=len(S), stations_with_launches=int((S.launches > 0).sum()),
            inland_stations=int(S.inland.sum()), coastal_stations=int((~S.inland).sum()),
            coast_total_10m=float(coast["10m"][:, 2].sum() / 1000), coast_total_50m=float(coast["50m"][:, 2].sum() / 1000))
jsave(flow, f"{SCR}/flow.json", indent=1)
print(flow)
print(S[S.inland][["station", "coast_d_10m", "launches"]].to_string())
print(L.btype.value_counts(), L.group.value_counts())
