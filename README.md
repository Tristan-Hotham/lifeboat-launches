# Where the lifeboats go

Distance, timing and station workload in 45,673 RNLI lifeboat launches, 2021 to 2025, from 238 stations in the UK, Ireland, the Isle of Man and the Channel Islands.

By Dr Tristan Hotham, Independent researcher, 2026.

Interactive page: https://maps.tristanhotham.com/lifeboat-launches/
Paper: https://doi.org/10.5281/zenodo.24104520
Blog post: https://blog.tristanhotham.com/2026/10/31/lifeboat-launches/
Code and data: https://github.com/Tristan-Hotham/lifeboat-launches

## Headline results

- Close to home: half of all 45,650 located launches went less than 4.5 km from the station (straight line); 77% less than 10 km.
- Boat type (H1): median inshore launch 3.5 km, all-weather 9.3 km; within the same station all-weather launches went +150% (95% CI 119 to 185) further, positive in all 14 checks; a within-station permutation placebo gives about 0.
- Casualty (H2): commercial casualties +27% (95% CI 16 to 40) further than people in the water (all checks); powered and sail craft -4% (95% CI -11 to 4), not different.
- Season (H3): summer/winter rate ratio 10.6 for powered and sail craft, 6.9 for paddle and board craft, 2.2 for commercial casualties. Weekend ratios: 2.04 paddle and board, 1.16 commercial.
- Darkness: 22.8% of launches in the dark; paddle and board craft 2.4%.
- Workload (H6): elasticity of station launches with respect to nearest coast length 0.10 (95% CI -0.02 to 0.22).
- Thames: Tower station made 3,077 launches (6.7% of all); the four Thames stations 11.8%.
- Trend (H5): total +0.3% a year (95% CI -1.4 to 2.0); the share recorded as casualty type "Other" rose from 8.2% to 21.2%, so group trends are not interpretable as real changes.
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

- Records: RNLI Returns of Service 2021 to 2025, one row per launch (45,682); 9 training launches dropped; 135 longitudes with a lost minus sign corrected; 23 impossible positions excluded from distances and maps.
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

Hotham, T. (2026). Where the Lifeboats Go: Distance, Timing and Station Workload in RNLI Lifeboat Launches, 2021 to 2025. Zenodo. https://doi.org/10.5281/zenodo.24104520

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
