"""Step 8: README.md and reddit/post.md filled from data/results.json."""
from common import *

R = jload(f"{DATA}/results.json"); H = R["H12"]
e = lambda v: f"{v['b']:+.0f}% (95% CI {v['lo']:.0f} to {v['hi']:.0f})"
txt = f"""# Where the lifeboats go

Distance, timing and station workload in {R['n']:,} RNLI lifeboat launches, 2021 to 2025, from {R['n_stations']} stations in the UK, Ireland, the Isle of Man and the Channel Islands.

By Dr Tristan Hotham, Independent researcher, 2026.

Interactive page: {PAGE}
Paper: {{https://doi.org/10.5281/zenodo.24104520}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/lifeboat-launches/}}
Code and data: {REPO}

## Headline results

- Close to home: half of all {R['n_located']:,} located launches went less than {R['dist']['all_types']['med']:.1f} km from the station (straight line); {R['dist']['all_types']['within10']:.0f}% less than 10 km.
- Boat type (H1): median inshore launch {R['dist']['ILB']['med']:.1f} km, all-weather {R['dist']['ALB']['med']:.1f} km; within the same station all-weather launches went {e(H['alb'])} further, positive in all {R['robust_n']} checks; a within-station permutation placebo gives about 0.
- Casualty (H2): commercial casualties {e(H['commercial'])} further than people in the water (all checks); powered and sail craft {e(H['powered and sail craft'])}, not different.
- Season (H3): summer/winter rate ratio {R['H3']['powered and sail craft']['rr']:.1f} for powered and sail craft, {R['H3']['paddle and board craft']['rr']:.1f} for paddle and board craft, {R['H3']['commercial']['rr']:.1f} for commercial casualties. Weekend ratios: {R['H3b']['paddle and board craft']['rr']:.2f} paddle and board, {R['H3b']['commercial']['rr']:.2f} commercial.
- Darkness: {R['dark']['all']['pc']:.1f}% of launches in the dark; paddle and board craft {R['dark']['paddle and board craft']['pc']:.1f}%.
- Workload (H6): elasticity of station launches with respect to nearest coast length {R['H6']['el']:.2f} (95% CI {R['H6']['lo']:.2f} to {R['H6']['hi']:.2f}).
- Thames: Tower station made {R['stations_conc']['tower']:,} launches ({R['prose']['tower_pc']:.1f}% of all); the four Thames stations {R['stations_conc']['thames_pc']:.1f}%.
- Trend (H5): total {R['H5']['all']['b']:+.1f}% a year (95% CI {R['H5']['all']['lo']:.1f} to {R['H5']['all']['hi']:.1f}); the share recorded as casualty type "Other" rose from {R['prose']['other_2021']:.1f}% to {R['prose']['other_2025']:.1f}%, so group trends are not interpretable as real changes.
- Descriptive and observational; a launch is not an incident.

## Files

| File | What it is |
|---|---|
| `index.html`, `js/page.js` | Interactive MapLibre page: heat layer and 1 km squares of launches, stations sized by launches, coast shaded by station workload, filters by year, boat and casualty, search, popups, full screen, layers panel. |
| `header.png` | Social card, 1200 x 630. |
| `data/stations.csv` | Every station: type, region, country, point, river or lake flag, nearest coast length (1:10m, 1:50m, 30 km catchment), launches by year, boat and casualty group, median distance, share in the dark. |
| `data/grid_1km.csv` | Located launches counted on 1 km squares (ETRS89 LAEA), with totals by year, boat type and casualty group. |
| `data/monthly_counts.csv`, `data/hourly_counts.csv`, `data/casualty_types_by_year.csv` | Counts by month and group, hour and group or boat, casualty type and year. |
| `data/models.csv` | Every model coefficient (main and checks). |
| `data/results.json` | Every number quoted on the page, in the paper, blog, collage and post. |
| `data/site.json` | Page data (aggregates only). |
| `code/` | Numbered pipeline, templates, `qa.js`. |
| `release/` | Paper (`paper/`, with `cover_note.md`), blog post and figures (`blog/`), Zenodo files (`zenodo/`). |
| `reddit/` | Collage, looping GIF, `collage.py` and post text. |
| `NOTES.md` | The analysis plan (written before any outcome was computed), the log and reference notes. |

## Method in brief

- Records: RNLI Returns of Service 2021 to 2025, one row per launch ({R['flow']['raw']:,}); {R['flow']['training']} training launches dropped; {R['flow']['flipped']} longitudes with a lost minus sign corrected; {R['flow']['loc_err']} impossible positions excluded from distances and maps.
- Distance: great-circle km from station to incident. Darkness: sun more than 6 degrees below the horizon. Coast: Natural Earth coastline allocated to the nearest coastal station on 1 km pieces.
- Models: OLS of log distance with station, year and month fixed effects, clustered by station; Poisson models of monthly and daily counts by casualty group; Poisson trend with HAC errors; PPML of station launches on log coast length with region fixed effects. Placebo, alternative specifications, leave-one-region-out and measurement checks fixed in the plan.

## How to rerun

Python 3 with pandas, numpy, scipy, statsmodels, geopandas, shapely, pyproj, matplotlib, Pillow; xelatex, pdftotext; node with Playwright for `code/qa.js`. The RNLI records must be downloaded from the RNLI open data portal (Returns of Service, Lifeboat Station Locations) as JSON; paths in `code/common.py`; intermediates go to `LB_SCRATCH`.

```
python3 code/01_data.py        # cleaning, distances, darkness, coast allocation
python3 code/02_models.py      # the planned analysis and checks
python3 code/03_results.py     # results.json, aggregate tables, site.json
python3 code/04_figures.py     # figures
python3 code/05_build_site.py  # index.html
python3 code/06_paper.py       # paper PDF (DOI=10.5281/zenodo.N to fill the DOI)
python3 reddit/collage.py      # collage and header.png
python3 code/08_readme.py      # README and Reddit post
python3 code/07_release.py     # blog post and Zenodo files
node code/qa.js                # screenshots
```

## Sources and licences

- RNLI Returns of Service and RNLI Lifeboat Station Locations, RNLI open data portal (data-rnli.opendata.arcgis.com), retrieved 2026, under the RNLI's own open data licence. That licence is bespoke (adapted from the Open Government Licence); as published it is non-transferable, not sub-licensable and revocable, and it does not allow changes to the content of the datasets (clauses 1.2 and 1.3, as described by Boswarva 2018). The current licence text on the portal could not be retrieved for this release, so the release follows those terms: the launch records are not redistributed, and the data files are aggregates (counts by station, month, hour, casualty type and year, and 1 km grid square) and model results derived from them. Anyone wishing to rerun the pipeline should download the records from the portal and accept its terms there. (The Lifeboat Station Locations dataset is also listed on data.gov.ie under CC BY 4.0.)
- Natural Earth coastlines (public domain). Base map: OpenFreeMap, OpenStreetMap contributors (ODbL). MapLibre GL JS (BSD 3-Clause).
- Text, figures and aggregate data CC BY 4.0; code MIT (see `LICENSE`).

## Citation

Hotham, T. (2026). Where the Lifeboats Go: Distance, Timing and Station Workload in RNLI Lifeboat Launches, 2021 to 2025. Zenodo. {{https://doi.org/10.5281/zenodo.24104520}}

{AI}
"""
for bad in ("—", "–", "DSIT", "DCMS"):
    assert bad not in txt, bad
assert "--" not in txt.replace("|---|---|", "")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(txt)
post = f"""# Reddit post

**Title:** [OC] Half of all RNLI lifeboat launches went less than {R['dist']['all_types']['med']:.1f} km from the station, and the busiest station is on the Thames in London ({R['n']:,} launches, 2021 to 2025)

**Image:** lifeboat_launches_collage.png (or the GIF, lifeboat-launches.gif)

**Body:**

I mapped every RNLI lifeboat launch from 2021 to 2025 that has a position ({R['n_located']:,} of {R['n']:,}), from {R['n_stations']} stations around the UK, Ireland, the Isle of Man and the Channel Islands.

- Half went less than {R['dist']['all_types']['med']:.1f} km from the station in a straight line; {R['dist']['all_types']['within10']:.0f}% less than 10 km.
- Inshore lifeboats: typical trip {R['dist']['ILB']['med']:.1f} km. All-weather lifeboats: {R['dist']['ALB']['med']:.1f} km.
- Launches to motorboats, yachts and dinghies were {R['H3']['powered and sail craft']['rr']:.1f} times as frequent in summer as in winter; to fishing and other commercial boats, {R['H3']['commercial']['rr']:.1f} times.
- Only {R['dark']['paddle and board craft']['pc']:.1f}% of launches to paddleboards, kayaks and other boards were in the dark, against {R['dark']['all']['pc']:.0f}% overall.
- Tower station on the Thames launched {R['stations_conc']['tower']:,} times, {R['prose']['tower_pc']:.1f}% of all launches.
- Stations with more coastline were barely busier: coast length alone says little about how busy a station is.

Interactive map (filter by year, boat and casualty; tap any station): {PAGE}

**Source comment:**

Data: RNLI Returns of Service and lifeboat station locations from the RNLI open data portal (RNLI open data licence); coastlines from Natural Earth. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Distances are straight lines from station to incident, not the route. A launch is not an incident: two boats to one call are two launches, and coastguard helicopters, lifeguards and others handle many emergencies. {R['flow']['flipped']} positions had lost the minus sign on their longitude and were corrected. The analysis plan was written before any results were computed; paper, data and code are linked from the page.
"""
for bad in ("—", "–", "--", "DSIT", "DCMS"):
    assert bad not in post, bad
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(post)
print("README", len(txt.split()), "words; post", len(post.split()))
