"""Step 6: the paper. Fills code/paper_template.tex from data/results.json, adds the tables, compiles with xelatex.
Output: release/paper/Hotham_Lifeboat_Launches.pdf and .tex beside the f_*.pdf figures.
The DOI stays a placeholder (https://doi.org/10.5281/zenodo.24104520 printed) unless DOI is set: DOI=10.5281/zenodo.N python3 code/06_paper.py"""
import subprocess
import numpy as np, pandas as pd
from scipy.stats import norm as N
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Lifeboat_Launches"
tex = lambda s: str(s).replace("\\", "").replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("$", "\\$")


def num(v, d=0):
    s = f"{float(v):.{d}f}"
    if float(s) == 0: s = s.lstrip("-")
    return s.replace("-", "$-$")


def tfmt(v, f):
    if f == "int": return f"{int(round(float(v))):,}"
    if f == "abs": return f"{abs(float(v)):.0f}"
    for k in ("f0", "f1", "f2", "f3", "f4"):
        if f == k: return num(v, int(k[1]))
    return tex(str(v))


pc = lambda v: (f"{num(v['b'])} [{num(v['lo'])}, {num(v['hi'])}]") if v else ""
rr = lambda v, d=2: f"{v['rr']:.{d}f} [{v['lo']:.{d}f}, {v['hi']:.{d}f}]"
GS = [g for g in GROUPS]
F = R["flow"]

# Holm for the five H3 contrasts with commercial
cons = {g: R["H3"]["vs_commercial_" + g] for g in GROUPS[1:]}
p = {g: 2 * (1 - N.cdf(abs(v["coef"] / v["se"]))) for g, v in cons.items()}
order = sorted(p, key=p.get); holm = {}; run = 0
for i, g in enumerate(order):
    run = max(run, min(1, (len(order) - i) * p[g])); holm[g] = run
for g in ("powered and sail craft", "paddle and board craft", "people in the water"):
    assert holm[g] < 0.05, g
for g in ("people on the shore", "other or unknown"):
    assert holm[g] > 0.05, g
assert R["H12_robust"][5]["label"].startswith("Arrived") and R["H12_robust"][6]["label"].startswith("No stood-down")
assert R["H12_robust"][5]["powered and sail craft"]["lo"] > -1 and R["H12_robust"][6]["powered and sail craft"]["lo"] < 0
assert R["H12_robust"][4]["label"].startswith("Coastal")
assert R["H6_robust"][1]["label"].startswith("Coastline at 1:50m")
assert R["per10"]["bottom"][0]["coast"] > 400 and R["per10"]["bottom"][1]["coast"] > 400
assert R["dark"]["commercial"]["pc"] < R["dark"]["all"]["pc"] and R["dark"]["commercial"]["pc"] > R["dark"]["powered and sail craft"]["pc"]

TF = ("\\begin{table}[tbp]\\centering\\small\\caption{From the published records to the analysis samples.}\\label{tab:flow}\\begin{tabular}{lr}\\toprule Step & Launches\\\\\\midrule\n"
      f"Returns of Service, 2021 to 2025 & {F['raw']:,}\\\\\n"
      f"\\quad less: training launches (headquarters, college) & $-${F['training']:,}\\\\\\midrule\n"
      f"Launches analysed & {F['analysed']:,}\\\\\n"
      f"\\quad of which longitude sign corrected (rule C2) & {F['flipped']:,}\\\\\n"
      f"\\quad of which positions beyond the error cut-offs (C3) & {F['loc_err']:,}\\\\\n"
      f"Located launches (maps, distances, darkness) & {F['located']:,}\\\\\n"
      f"\\quad of which all-weather or inshore (H1, H2) & {R['H12']['n']:,}\\\\\n"
      f"\\quad of which within 50 m of the station point (C4, kept) & {F['stacked']:,}\\\\\\midrule\n"
      f"Stations with launches & {R['n_stations']:,}\\\\\n"
      f"\\quad coastal stations (H6) & {R['H6']['n']:,}\\\\\n"
      f"\\quad river and lake stations & {F['inland_stations'] - 1:,}\\\\\n"
      "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for k, lab in [("ALB", "All-weather lifeboat"), ("ILB", "Inshore lifeboat")]:
    d = R["dist"][k]
    rows += f"{lab} & {R['btype_n'][k]:,} & {R['btype_pc'][k]:.1f} & {d['med']:.1f} [{d['lo']:.1f}, {d['hi']:.1f}] & {d['p90']:.1f} & {R['dark'][k]['pc']:.1f} & & \\\\\n"
rows += "\\midrule\n"
for g in GS:
    d = R["dist_group"][g]
    rows += (f"{tex(GROUP_SHORT[g])} & {R['group_n'][g]:,} & {R['group_pc'][g]:.1f} & {d['med']:.1f} [{d['lo']:.1f}, {d['hi']:.1f}] & {d['p90']:.1f} & {R['dark'][g]['pc']:.1f} & "
             f"{R['H3'][g]['summer_share']:.1f} & {d['alb_pc']:.0f}\\\\\n")
rows += f"\\midrule All & {R['n']:,} & 100.0 & {R['dist']['all_types']['med']:.1f} & {R['dist']['all_types']['p90']:.1f} & {R['dark']['all']['pc']:.1f} & {R['season_all']['summer_share']:.1f} & \\\\\n"
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{Launches by boat type and casualty group: number and share; median straight-line distance with 95\\% station-cluster bootstrap interval and 90th percentile (all-weather and inshore launches; all located launches in the last row); share launched in the dark; share in June to August; share of the group's launches made by an all-weather boat.}\\label{tab:desc}"
      "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{lrrlrrrr}\\toprule & $N$ & \\% & Median km & P90 km & Dark \\% & Summer \\% & ALB \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
H = R["H12"]
rows = f"All-weather lifeboat (vs inshore) & {pc(H['alb'])} & {pc(H['alb_h2'])}\\\\\n"
for g in GROUPS:
    if g == "people in the water": continue
    rows += f"{tex(GROUP_SHORT[g])} (vs people in the water) & & {pc(H[g])}\\\\\n"
rows += f"\\midrule Station, year and month fixed effects & yes & yes\\\\\n$N$ launches (stations) & {H['n']:,} ({H['stations']}) & {H['n']:,} ({H['stations']})\\\\\n"
TH = ("\\begin{table}[tbp]\\centering\\small\\caption{Planned models for distance (H1, H2): percentage difference in straight-line distance from station to incident, with 95\\% confidence intervals clustered by station. OLS of $\\log(d+0.1)$.}\\label{tab:h12}"
      "\\begin{tabular}{lll}\\toprule & H1 & H2\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for g in GROUPS:
    s = R["H3"][g]; w = R["H3b"][g]
    if g == "commercial":
        rows += f"{tex(GROUP_SHORT[g])} & {rr(s)} & (reference) & & {rr(w)} & (reference)\\\\\n"
    else:
        c = R["H3"]["vs_commercial_" + g]; cw = R["H3b"]["vs_commercial_" + g]
        hp = f"{holm[g]:.3f}" if holm[g] >= 0.001 else "$<$0.001"
        rows += f"{tex(GROUP_SHORT[g])} & {rr(s)} & {rr(c)} & {hp} & {rr(w)} & {rr(cw)}\\\\\n"
TS = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Season (H3) and weekend (H3b). Summer (June to August) to winter (December to February) rate ratios from a Poisson model of monthly counts by group with group-by-year fixed effects; their ratio to the commercial group's, with Holm-adjusted p-values for the five contrasts; weekend-day to weekday rate ratios from a Poisson model of daily counts with group-by-month fixed effects, and their ratio to the commercial group's. 95\\% intervals from HC1 standard errors.}\\label{tab:season}"
      "\\setlength{\\tabcolsep}{3pt}\\begin{tabular}{llllll}\\toprule Group & Summer/winter & vs commercial & Holm $p$ & Weekend/weekday & vs commercial\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for g in ["all"] + GROUPS:
    a = R["annual"][g]; e = R["H5"][g]
    lab = "All launches" if g == "all" else GROUP_SHORT[g]
    nsig = "" if g == "all" else f"{R['h5_range'][g + '_sig'] if g not in ('other or unknown',) else R['h5_range']['other_sig']}"
    rows += f"{tex(lab)} & " + " & ".join(f"{x:,}" for x in a) + f" & {pc(e).replace('[', '[').replace(' [', ' [')}\\\\\n".replace("$-$", "$-$")
TT = ("\\begin{table}[tbp]\\centering\\small\\caption{Launches by year and the planned trend estimate (H5): \\% change a year from a Poisson model of monthly counts with calendar-month fixed effects and HAC standard errors (12 lags), 95\\% intervals.}\\label{tab:trend}"
      "\\setlength{\\tabcolsep}{4pt}\\begin{tabular}{lrrrrrl}\\toprule Group & 2021 & 2022 & 2023 & 2024 & 2025 & \\% a year\\\\\\midrule\n" + rows +
      f"\\midrule Recorded as ``Other'' (\\%) & " + " & ".join(f"{x:.1f}" for x in R["other_share"]) + " & \\\\\n\\bottomrule\\end{tabular}\\end{table}")
rows = ""
for x in [R["H6"]] + R["H6_robust"]:
    rows += f"{tex(x['label'].capitalize() if x['label'] == 'main' else x['label'])} & {x['n']} & {num(x['el'], 3)} & [{num(x['lo'], 3)}, {num(x['hi'], 3)}]\\\\\n"
TH6 = ("\\begin{table}[tbp]\\centering\\small\\caption{Station workload and coast length (H6): elasticity of five-year launches with respect to the length of coast nearest to each coastal station. Poisson pseudo-maximum likelihood with an all-weather indicator and region fixed effects (main), HC1 95\\% intervals; checks below.}\\label{tab:h6}"
       "\\begin{tabular}{lrrl}\\toprule Specification & $N$ & Elasticity & 95\\% CI\\\\\\midrule\n" + rows.replace("Main", "Main model", 1) + "\\bottomrule\\end{tabular}\\end{table}")
KEYS = [("alb", "All-weather"), ("commercial", "Commercial"), ("powered and sail craft", "Powered/sail"), ("paddle and board craft", "Paddle/board"), ("people on the shore", "Shore")]
rows = f"Main model & {H['n']:,} & " + " & ".join(pc(H[k]) for k, _ in KEYS) + "\\\\\n\\midrule\n"
grp = None
for x in R["H12_robust"]:
    if x["group"] != grp:
        rows += f"\\multicolumn{{7}}{{l}}{{\\textit{{{tex(x['group'])}}}}}\\\\\n"; grp = x["group"]
    rows += f"\\quad {tex(x['label'])} & {x['n']:,} & " + " & ".join(pc(x[k]) for k, _ in KEYS) + "\\\\\n"
q = R["H12_quant"]
rows += f"\\multicolumn{{7}}{{l}}{{\\textit{{Median regression}}}}\\\\\n\\quad Quantile 0.5, station indicators & {H['n']:,} & {q['alb']:.0f} [{q['alb_lo']:.0f}, {q['alb_hi']:.0f}] & " + " & ".join(pc(q[k]) for k, _ in KEYS[1:]) + "\\\\\n"
TB = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Robustness of the distance models (H1, H2): percentage differences with 95\\% intervals for all-weather vs inshore boats and for commercial, powered and sail craft, paddle and board craft and people on the shore vs people in the water.}\\label{tab:robust}"
      "\\setlength{\\tabcolsep}{2pt}\\resizebox{\\textwidth}{!}{\\begin{tabular}{p{5.4cm}rlllll}\\toprule Check & $N$ & " + " & ".join(n for _, n in KEYS) + "\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}}\\end{table}")
S = pd.read_csv(f"{DATA}/stations.csv")
rows = ""
for r in S[S.launches > 0].head(15).itertuples():
    p10 = "" if r.inland else f"{r.launches / r.coast_km_10m * 10:.0f}"
    rows += f"{tex(r.station)} & {r.stype} & {tex(r.Region)} & {r.launches:,} & {r.med_km:.1f} & {p10}\\\\\n"
TST = ("\\begin{table}[tbp]\\centering\\small\\caption{The fifteen busiest stations, 2021 to 2025: type (ALB: has an all-weather boat), RNLI region, launches, median distance (km) and launches per 10 km of nearest coast (blank for river stations).}\\label{tab:stations}"
       "\\begin{tabular}{lllrrr}\\toprule Station & Type & Region & Launches & Median km & Per 10 km\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
TC = pd.read_csv(f"{DATA}/casualty_types_by_year.csv")
TC["n"] = TC[[str(y) for y in YEARS]].sum(axis=1)
rows = ""
for g in GROUPS:
    q = TC[TC.group == g].sort_values("n", ascending=False)
    rows += f"{tex(GROUP_SHORT[g])} & {', '.join(f'{tex(t)} ({n:,})' for t, n in zip(q.ctype, q.n))}\\\\\n"
TTY = ("\\begin{table}[tbp]\\centering\\scriptsize\\caption{Casualty groups and the RNLI casualty types they contain, with launches 2021 to 2025 (each type listed under the group most of its launches fall in; commercial is the RNLI's commercial category, which overrides the type).}\\label{tab:types}"
       "\\begin{tabular}{lp{12.2cm}}\\toprule Group & Casualty types (launches)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")

t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read()
t = t.replace("{{AI}}", AI).replace("{{PAGE}}", PAGE).replace("{{REPO}}", REPO)
for k, v in (("TABLE_FLOW", TF), ("TABLE_DESC", TD), ("TABLE_H12", TH), ("TABLE_SEASON", TS), ("TABLE_TREND", TT), ("TABLE_H6", TH6), ("TABLE_ROBUST", TB), ("TABLE_STATIONS", TST), ("TABLE_TYPES", TTY)):
    t = t.replace("{{" + k + "}}", v)
t = re.sub(r"\{\{(?!TABLE_|DOI)([^}|]+)(\|(\w+))?\}\}", lambda m: tfmt(get(R, m.group(1)), m.group(3) or "raw"), t)
DOI = os.environ.get("DOI")
t = t.replace("https://doi.org/10.5281/zenodo.24104520", f"\\url{{https://doi.org/{DOI}}}" if DOI else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t and "—" not in t and "–" not in t, re.findall(r"\{\{[^}]*\}\}", t)[:5]
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l or l.startswith("!")][:15])
for ext in (".aux", ".log", ".out", ".bbl", ".blg"):
    q_ = os.path.join(OUT, NAME + ext)
    if os.path.exists(q_): os.remove(q_)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
body = txt.split("\nReferences\n")[0]
ab = re.search(r"Abstract\n(.*?)Keywords", txt, re.S).group(1)
print("paper", r.returncode, len(txt.split()), "words total;", len(body.split()), "before references; abstract", len(ab.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("—") + txt.count("–"))
cites = set(re.findall(r"\\cite\w*\{([^}]+)\}", t)); cites = {c.strip() for x in cites for c in x.split(",")}
bibs = set(re.findall(r"\\bibitem\[[^\]]*\]\{([^}]+)\}", t))
print("uncited:", bibs - cites, "missing:", cites - bibs, "refs:", len(bibs))
print("unreferenced labels:", [l for l in re.findall(r"\\label\{([^}]+)\}", t) if "\\ref{" + l + "}" not in t])
