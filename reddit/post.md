# Reddit post

**Title:** [OC] Half of all RNLI lifeboat launches went less than 4.5 km from the station, and the busiest station is on the Thames in London (45,673 launches, 2021 to 2025)

**Image:** lifeboat_launches_collage.png (or the GIF, lifeboat-launches.gif)

**Body:**

I mapped every RNLI lifeboat launch from 2021 to 2025 that has a position (45,650 of 45,673), from 238 stations around the UK, Ireland, the Isle of Man and the Channel Islands.

- Half went less than 4.5 km from the station in a straight line; 77% less than 10 km.
- Inshore lifeboats: typical trip 3.5 km. All-weather lifeboats: 9.3 km.
- Launches to motorboats, yachts and dinghies were 10.6 times as frequent in summer as in winter; to fishing and other commercial boats, 2.2 times.
- Only 2.4% of launches to paddleboards, kayaks and other boards were in the dark, against 23% overall.
- Tower station on the Thames launched 3,077 times, 6.7% of all launches.
- Stations with more coastline were barely busier: coast length alone says little about how busy a station is.

Interactive map (filter by year, boat and casualty; tap any station): https://maps.tristanhotham.com/lifeboat-launches/

**Source comment:**

Data: RNLI Returns of Service and lifeboat station locations from the RNLI open data portal (RNLI open data licence); coastlines from Natural Earth. Tools: Python (pandas, statsmodels, matplotlib), MapLibre. Distances are straight lines from station to incident, not the route. A launch is not an incident: two boats to one call are two launches, and coastguard helicopters, lifeguards and others handle many emergencies. 135 positions had lost the minus sign on their longitude and were corrected. The analysis plan was written before any results were computed; paper, data and code are linked from the page.
