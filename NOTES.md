# lifeboat-launches: working notes

Brief: /home/claude/work/new13/BRIEFS.md section J (+ the shared rules it points to: new12, new11, new10, new9, new8 tops,
house brief /home/claude/newdata/BRIEF.md, GIF brief /home/claude/gifs/BRIEF.md). Format refs: fame-half-life,
byelection-attention. Scratch: /home/claude/scratch/lifeboat-launches (delete by exact path at the end).

## What I looked at before writing the plan

Only the structure of the raw files, not any outcome: column names and value labels, row counts by year (2021 to 2025,
8,886 to 9,317 a year, 45,682 in all), RoSType by lifeboat class, CasualtyTypeFull by CasualtyCategory, the station list
(238 stations, ALB 120 / ILB 118; ENG, SCT, IRL, WAL, NIR, IOM, CHI), the station names that fail to match (case
differences; Chiswick, "Headquarters", "The Rnli College" absent from the station list), the coordinate ranges, and the
time zone of the two time fields. Facts found:

- x, y are WGS84 longitude and latitude in decimal degrees (y 49 to 61, x -15 to +5.4), not Web Mercator. No zeros or
  nulls. But some longitudes clearly lost their minus sign (Tighnabruaich x = +5.40, Fishguard +5.29, The Lizard +5.27,
  Salcombe +3.90): 7,742 rows have x > 0, most of them legitimately east of Greenwich (Thames estuary, East Anglia, Kent).
- DateOfLaunch + TimeOfLaunch are UK/Irish local clock time (UTC+1 from the last Sunday of March to the last Sunday of
  October); DateTimeOfLaunch is UTC epoch milliseconds. Hour-of-day analysis uses local clock time.
- Coordinates have 4 to 8 decimals; a few points repeat many times (e.g. -8.49583, 54.99933 60 times), probably a
  default position per station or a frequent spot.
- Each row is one lifeboat launch (ROSNumber unique). A single incident answered by two lifeboats is two rows.

## Data construction rules (fixed before any outcome)

C1 Stations. Launch station names matched to the 238-station list by a normalised name (lower case, "&" to "and",
   punctuation folded). Chiswick (not in the current list; the RNLI's Thames station at Chiswick Pier) gets a point
   from its own launches' locations only for display, and is grouped with the Thames stations; "Headquarters" and
   "The Rnli College" (training launches, 9 rows) are dropped from station-level analyses.
C2 Longitude sign. A row with x > 0 is flipped to -x when the flipped point is within 60 km of its station and the
   unflipped point is more than twice as far. Count reported.
C3 Location errors. After C2, a launch whose incident point is more than 100 km from its station (ILB, hovercraft,
   rescue water craft) or 250 km (ALB) is flagged as a location error: kept in counts, dropped from distance and maps.
C4 Stacked points. Incident points within 50 m of the station point are flagged (possibly the station entered as the
   position); kept in the main analysis, dropped in a sensitivity check.
C5 Water bodies. Stations on rivers and lakes (Thames: Tower, Chiswick, Teddington, Gravesend; Lough Erne, Lough Derg,
   Lough Ree, Windermere, Loch Ness and other inland stations identified from the station list by distance to the
   Natural Earth 1:10m coastline > 3 km) are labelled "inland or river" and kept, with a check that drops them.
C6 Casualty groups (from CasualtyTypeFull, case folded; CasualtyCategory COMMERCIAL overrides):
   - commercial: CasualtyCategory = COMMERCIAL (the RNLI's own category: fishing, other commercial activity)
   - powered and sail craft: motorboat, sailing vessel, sailing dinghy, jet ski, inflatable, rowing boat, angler from
     boat, diving vessel, waterskier
   - paddle and board craft: kayak/canoe, paddleboard, surfboard, bodyboard, kitesurf, windsurf, skimboard
   - people in the water: person in water, swimmer, scuba diver, tombstoner, multiple persons on the water
   - people on the shore: person ashore, walker/runner, climber, angler from shore, waterside activity, coasteerer,
     motor vehicle, animal (dog), animal (other) (animals counted here because the call is usually a dog and its owner
     on the shore)
   - other or unknown: everything else (other, unknown, unknown person, unknown craft, person in distress, person on
     craft, false alarm, mass rescue, aircraft, distress signals, object in the sea)
C7 Boat type: RoSType ALB (all-weather lifeboat) and ILB (inshore lifeboat); IRH (hovercraft) and RWC (rescue water
   craft) reported descriptively; 4 "Unknown" (SUV4X4) dropped from boat-type comparisons.
C8 Distance: great-circle distance (km) from the station point to the incident point. A straight line, not the route.
C9 Coast length per station: the Natural Earth 1:10m coastline of Britain, Ireland, the Isle of Man and the Channel
   Islands, cut into 1 km pieces in an equal-area projection (ETRS89 LAEA, EPSG:3035), each piece given to the nearest
   coastal station (straight line, within 60 km). Inland and river stations get no coast.
C10 Darkness: sun altitude at the incident point and launch time (NOAA solar position formulae, UTC epoch); dark =
   sun below -6 degrees (civil twilight).

## Analysis plan (written before computing any distance, trend, seasonal or station outcome)

Questions (brief): where launches go (density, hotspots); how far from station; how this differs by boat type, casualty
type, season and hour; which stations are busiest relative to coast length; the trend by type over 2021 to 2025.
Unit: one lifeboat launch (N = 45,682), or counts of launches aggregated as stated. Design: descriptive and
observational throughout; launches measure the demand that reached the RNLI and how it was met, not all incidents
at sea (coastguard helicopters, other lifeboats, lifeguards and the public handle others).

H1 Boat type and distance. ALB launches reach incidents further from the station than ILB launches.
   Main specification: OLS of log(distance km + 0.1) on an ALB indicator with station fixed effects (so the comparison
   is within stations that have both kinds of boat), year and calendar-month fixed effects; standard errors clustered
   by station. Effect = 100 (exp(b) - 1)% with 95% CI. Also medians by type with 95% CIs from a station-cluster
   bootstrap (1,000 draws). Against H1: CI including 0 or negative.
H2 Casualty group and distance. Commercial and powered/sail craft incidents are further from the station than people
   in the water and people on the shore. Same model with casualty group dummies (reference: people in the water) and
   boat type; station-clustered CIs. Against: commercial or powered/sail CI including 0.
H3 Season. Launches to leisure groups (powered and sail, paddle and board, people in the water, people on the shore)
   are more concentrated in summer than launches to commercial casualties. Main: Poisson GLM of monthly launch counts
   by group (60 months x 6 groups) with group-by-year fixed effects and group-specific summer (June to August) and
   winter (December to February) indicators (spring and autumn the reference); summer-to-winter rate ratio per group
   with 95% CI (HC1 robust SE); contrast of each leisure group's ratio against commercial. Against: leisure ratios
   not above the commercial ratio.
H3b Weekend (falsification of the leisure reading). Launches per weekend day vs per weekday: leisure groups higher at
   weekends, commercial not (fishing and work boats are a weekday activity). Poisson of daily counts by group with
   group x weekend and group x month fixed effects; robust SE; bank holidays not adjusted (said so).
H4 Hour and darkness (descriptive, pre-specified): hour-of-day profile by boat type and group; share of launches in
   darkness by group and boat type with Wilson 95% CIs. Expectation: ALB and commercial launches more often in the dark.
H5 Trend. Annual launches 2021 to 2025 by group. Main: Poisson GLM of monthly counts per group with a linear year
   term and calendar-month fixed effects, Newey-West (HAC, 12 lags) SE; % change a year with 95% CI. Pre-set
   expectation (two-sided): paddle and board launches rose (the paddleboard boom). Total launches: no expectation.
   Against: CI including 0 means no detectable trend over five years; say so plainly.
H6 Station workload and coast. Elasticity of a station's 2021 to 2025 launches with respect to its coast length.
   Main: Poisson GLM (PPML) of launches per coastal station on log coast km, an indicator for stations with an ALB,
   region fixed effects (the six RNLI regions); HC1 SE. Expectation: elasticity well below 1 (launches follow people
   and harbours more than coastline). Descriptive: launches per 10 km of coast; the busiest stations per km.
Hotspots (descriptive): incident counts on a 2 km grid in EPSG:3035; share of located launches in the busiest 1% and
   10% of occupied cells; the 10 busiest cells named by their nearest station; Lorenz curve and Gini of launches across
   stations and across cells.

Checks (pre-specified):
- Placebo for H1: boat type randomly permuted within station (200 permutations): coefficient distribution centred
  on 0; observed coefficient outside it.
- Alternative specifications: H1 and H2 as median (quantile 0.5) regression with station FE dummies, and with
  station-by-year FE; H5 with negative binomial; H6 with OLS of log launches.
- Leave one region out (6 RNLI regions) for H1, H2, H5 and H6.
- Measurement: drop sign-flipped rows; drop points within 50 m of the station (C4); drop inland and river stations
  (C5); arrived on scene only; drop false alarms and stood-down launches; distance cut-offs 60/150 km instead of
  100/250 km; H5 without 2021 (lockdown months in early 2021); H6 coastline at Natural Earth 1:50m instead of 1:10m
  (coast length depends on map scale: Mandelbrot's point) and catchment radius 30 km.
- Inference: H1/H2 SE clustered by station-year instead of station.

What would count against the overall picture: no difference by boat type (H1), commercial calls as seasonal as leisure
(H3) or as weekend-heavy (H3b), station workloads proportional to coast length (H6 elasticity near 1).

## Results (first and only run of the plan; all numbers in data/results.json)

- 45,682 rows; 9 training launches dropped (45,673 analysed); 135 longitudes flipped (C2); 23 location errors (C3); 45,650 located; 55 points within 50 m of the station (kept).
- H1 supported: median ILB 3.5 km, ALB 9.3 km; within-station ALB +150% [119, 185] (N 45,082, 238 stations); positive in all 14 checks (135 to 162%); permutation placebo mean 0.0%, max 6.3%; median regression +127%. ALB longer at 67 of 68 stations with 30+ of each.
- H2 partly supported: commercial +27% [16, 40] vs people in the water (significant in all 14 checks); powered and sail craft -4% [-11, 4] (expected positive: not supported); paddle and board -7% [-14, 0] (significant in 7 of 14: not robust).
- H3 supported: summer/winter RR powered/sail 10.6, paddle/board 6.9, in water 3.6, shore 2.4, other 2.4, commercial 2.2; contrasts vs commercial clear (Holm) for powered/sail, paddle/board, in water; not for shore and other.
- H3b: weekend RR paddle/board 2.04, powered/sail 1.81 ... commercial 1.16 [1.04, 1.29] (expected about 1: commercial is also weekend-heavy; reported).
- H4: dark 22.8% overall; paddle/board 2.4%; ALB 22.6% vs ILB 23.0% (expectation of more ALB launches in the dark not met).
- H5: total +0.3%/yr [-1.4, 2.0]; paddle/board -6.2% (expected rise: not supported); other or unknown +11.5%. Casualty type "Other" rose from 8.2% (2021) to 21.2% (2025): recording drift, group trends not interpretable. Exploratory: paddleboard alone -0.1%/yr [-6, 6].
- H6 supported: elasticity 0.10 [-0.02, 0.22]; checks 0.05 to 0.20, upper bound never above 0.36; ALB stations +26% [6, 49].
- Concentration: half of located launches in 599 of 9,689 occupied 2 km squares; Tower 3,077 launches (6.7%); Thames stations 11.8%.
- Licence: the RNLI open data licence (bespoke, adapted from OGL; described in 2018 as revocable, no sub-licensing, no content changes) means row-level records are NOT released; only aggregates. The current licence text could not be fetched (portal not reachable): the lead should confirm it before publishing, in particular whether the 1 km aggregate grid and station tables are acceptable.

## References: verification

WebSearch allowance for this turn was exhausted after one search (shared by all builders), and WebFetch only reaches URLs that appeared in results, so new academic references could NOT be verified in this build. The paper cites only:
- verified now via WebFetch: RNLI "Our research" page; ODI 2021 case study (24 March 2021; RNLI responds to about 50% of incidents; 2019 8,941 launches, 17,356 lifeguard incidents); Wright, RICS Land Journal (March 2021, updated; 238 stations, four on the Thames, predictive modelling of station placement); Roberts, RNLI Innovate blog (November 2018 URL; open by default with Esri); Boswarva 2018 blog on the licence (4 December 2018).
- verified in earlier reviewed builds (reused exactly): Abadie et al. 2023; Cameron and Miller 2015; Efron and Tibshirani 1993; Holm 1979; Koenker and Bassett 1978; Lorenz 1905; MacKinnon and White 1985; Mandelbrot 1967; Meeus 1998; Santos Silva and Tenreyro 2006; Seabold and Perktold 2010; Young 2019; Natural Earth.
That is 19 references, below the 25 to 50 asked. Candidates to verify and add (NOT cited): Norrington, Quigley, Russell and Van der Meer 2008 (Reliability Engineering and System Safety, SAR reliability with RNLI data); Akbari, Pelot and Eiselt 2018 (SAR vessel location, INFOR / Annals of OR); Razi and Karatas 2016 (EJOR, SAR boat location); Woodward et al. 2013 (J Coastal Research SI 65, UK rip current incidents); Scott et al. 2007/2008 (J Coastal Research SI 50, beach rescue statistics SW England); Castelle et al. 2016 (Earth-Science Reviews, rip currents); Szpilman et al. 2012 (NEJM, drowning); WHO 2014 Global report on drowning; Tipton 1989 (Clinical Science, cold water immersion); Roberts 2010 (Accident Analysis and Prevention, fishing fatalities); Newey and West 1987 (Econometrica, HAC); Wilson 1927 (JASA, score interval); Weisburd 2015 (Criminology, law of concentration); National Water Safety Forum WAID reports; RNLI annual reports and operational statistics 2021 to 2025 (e.g. the 2019 ops stats PDF linked from the ODI page).
Journal word limits and APCs (Ocean and Coastal Management, Maritime Studies, Journal of Maps) not checked for the same reason.

## Deliverables
index.html + js/page.js (QA qa/*.jpg, 0 console errors at 1280 and 390 px); header.png; data/* (aggregates only); code/01..08 + templates + qa.js; release/paper (PDF 18 pp, about 7,550 words before references incl. tables, abstract 235 words, 19 references, cover_note.md); release/blog (post.html, 6 figures, meta.json); release/zenodo; reddit/collage.py + collage + post.md + GIF (/home/claude/gifs/scripts/lifeboat-launches.py). Scratch deleted at the end.

## Independent review (2026)

- Reproduction: 01 to 03 rerun from the raw files in a scratch copy; results.json and every data CSV identical to the published versions.
- References: 17 peer-reviewed references verified online (title, authors, year, venue, volume, pages, DOI; abstract read for each claim) and integrated in a new Background subsection (2.2) and the methods: Razi and Karatas 2016; Akbari, Pelot and Eiselt 2018; Norrington et al. 2008; Breivik and Allen 2008; Pitman, Wright and Hocken 2019 (Safety Science 111, RNLI data); Szpilman et al. 2012; Hills et al. 2021 (WAID); Hills et al. 2024 (air temperature and drowning); Scott et al. 2007; Woodward et al. 2013; Castelle et al. 2016; Brander et al. 2013; Peden, Franklin and Leggat 2016; Willcox-Pidgeon et al. 2019; Weisburd 2015; Newey and West 1987; Wilson 1927. Total 36. Not added (abstract not reachable): Roberts 2010, Tipton 1989, WHO 2014.
- Licence: the portal (data-rnli.opendata.arcgis.com) could not be reached from the workspace; terms taken from Boswarva 2018 (clauses 1.2, 1.3: non-transferable, not sub-licensable, revocable, no content changes). Release stays aggregates only. data.gov.ie lists the Lifeboat Stations dataset under CC BY 4.0. The lead should still read the current licence on the portal before publishing.
- Journals: cover_note.md rewritten; Journal of Maps (full OA, APC) and Journal of Coastal Research (page charges) excluded; Maritime Studies model unconfirmed; Ocean and Coastal Management and Safety Science (hybrid, no charge on subscription route) listed; their word limits not confirmed.
- Text: removed untested claims ("lifeboats go where people are", "close to people", "shaped by leisure", "richest open record"), qualified the leisure-boating explanation, fixed table minus signs and negative zeros, collage label overlaps, GIF subtitle overlap.
