"""Shared paths, constants and helpers for the lifeboat-launches study ("Where the lifeboats go").

Inputs (read in place, never modified):
  RAW/rnli_return_of_service.json  RNLI Returns of Service open data (RNLI open data portal on ArcGIS Hub, retrieved 2026):
                                   45,682 lifeboat launches, 1 January 2021 to 31 December 2025, one row per launch:
                                   station, year, local date and time, UTC epoch time, lifeboat class and number, RoSType
                                   (ALB all-weather, ILB inshore, IRH hovercraft, RWC rescue water craft), casualty
                                   category and type, reason for launch, outcome, weather, sea, wind, visibility at launch
                                   and incident, arrived on scene, x/y = incident longitude/latitude (WGS84 degrees).
                                   RNLI open data licence: row-level records are NOT redistributed here; only aggregates.
  RAW/rnli_stations.json           RNLI lifeboat stations (same portal): 238 stations with type, county, division,
                                   region, country, boats, URL and point.
  GEO/ne_10m_admin_0_countries.geojson, GEO/ne_50m_land.geojson
                                   Natural Earth (public domain) coastlines at 1:10m and 1:50m.
"""
import json, gzip, os, re, math, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("LB_RAW", "/home/claude/newdata/raw_new13")
GEO = os.environ.get("LB_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("LB_FONTS", "/home/claude/ref/fonts")
SCR = os.environ.get("LB_SCRATCH", "/home/claude/scratch/lifeboat-launches")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "lifeboat-launches"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
YEARS = [2021, 2022, 2023, 2024, 2025]

# C2, C3, C4 thresholds (NOTES.md)
FLIP_KM = 60.0
ERR_KM = {"ALB": 250.0, "ILB": 100.0, "IRH": 100.0, "RWC": 100.0, "Unknown": 100.0}
STACK_KM = 0.05
INLAND_KM = 3.0
CATCH_KM = 60.0
THAMES = {"tower", "chiswick", "teddington", "gravesend"}

GROUPS = ["commercial", "powered and sail craft", "paddle and board craft", "people in the water",
          "people on the shore", "other or unknown"]
GROUP_SHORT = {"commercial": "Commercial", "powered and sail craft": "Powered and sail craft",
               "paddle and board craft": "Paddle and board craft", "people in the water": "People in the water",
               "people on the shore": "People on the shore", "other or unknown": "Other or unknown"}
GCOL = {"commercial": "#55606B", "powered and sail craft": "#2F6A9E", "paddle and board craft": "#2E9C9C",
        "people in the water": "#B4442E", "people on the shore": "#D08A1E", "other or unknown": "#A79F92"}
BCOL = {"ALB": "#1D3F6E", "ILB": "#E07A1F", "IRH": "#7A4FA0", "RWC": "#3B8B5A"}
_G = {
    "powered and sail craft": ["motorboat", "sailing vessel", "sailing dinghy", "jet ski", "inflatable", "rowing boat",
                               "angler from boat", "diving vessel", "waterskier"],
    "paddle and board craft": ["kayak/canoe", "paddleboard", "surfboard", "bodyboard", "kitesurf", "windsurf", "skimboard"],
    "people in the water": ["person in water", "swimmer", "scuba diver", "tombstoner", "multiple persons on the water"],
    "people on the shore": ["person ashore", "walker/runner", "climber", "angler from shore", "waterside activity",
                            "coasteerer", "motor vehicle", "animal (dog)", "animal (other)"],
}
TYPE2GROUP = {t: g for g, ts in _G.items() for t in ts}


def group_of(cat, typ):
    if str(cat).upper() == "COMMERCIAL":
        return "commercial"
    return TYPE2GROUP.get(str(typ).strip().lower(), "other or unknown")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("&", "and")
    s = re.sub(r"[’'`]", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def km(lat1, lon1, lat2, lon2):
    import numpy as np
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(np.asarray(lon2) - np.asarray(lon1)) / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def sun_alt(lat, lon, epoch_ms):
    """Solar altitude in degrees (NOAA general solar position approximation), vectorised."""
    import numpy as np
    t = np.asarray(epoch_ms, dtype=float) / 1000.0
    jd = t / 86400.0 + 2440587.5
    n = jd - 2451545.0
    L = np.radians((280.46 + 0.9856474 * n) % 360)
    g = np.radians((357.528 + 0.9856003 * n) % 360)
    lam = L + np.radians(1.915) * np.sin(g) + np.radians(0.020) * np.sin(2 * g)
    eps = np.radians(23.439 - 0.0000004 * n)
    ra = np.arctan2(np.cos(eps) * np.sin(lam), np.cos(lam))
    dec = np.arcsin(np.sin(eps) * np.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    ha = np.radians(gmst * 15 + np.asarray(lon)) - ra
    la = np.radians(lat)
    return np.degrees(np.arcsin(np.sin(la) * np.sin(dec) + np.cos(la) * np.cos(dec) * np.cos(ha)))


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jsave(obj, path, indent=None, keepdash=False):
    obj = nonan(obj) if keepdash else dash(nonan(obj))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, allow_nan=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "x1": return f"{float(v):.1f} times"
    if f == "abs0": return f"{abs(float(v)):.0f}"
    if f == "abs1": return f"{abs(float(v)):.1f}"
    raise ValueError(f)
