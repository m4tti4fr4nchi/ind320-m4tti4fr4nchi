# IND320 – Norwegian Reservoirs, Weather and Cross-border Flows

- Author: Mattia Franchi
- Course: IND320 – Data to Decision, project work (parts 1–4)
- Streamlit app: https://ind320-m4tti4fr4nchi-ybf3fy4znakvdenhn4kked.streamlit.app/

The project combines Jupyter Notebooks, where the data are downloaded, processed and stored, with a Streamlit app that presents and analyses them.

- **NVE Magasinstatistikk API:** weekly reservoir statistics for Norway, its five price areas and its precipitation areas (from 1995). The app downloads them directly from the API.
- **ENTSO-E Transparency Platform:** hourly physical cross-border flows between Norway and its six neighbours. The notebook of part 2 downloads them, writes them to Cassandra with Spark, extracts them again with Spark and stores them in MongoDB, which the app reads.
- **NVE shapefiles (atlas.nve.no):** borders of the price areas and of the regions. The notebook of part 3 samples 1000 random locations inside each area; the notebook of part 4 converts the borders to GeoJSON for the map of the app.
- **open-meteo historical API:** hourly ERA5 weather reanalysis, 2021–2025. The notebook of part 4 downloads it once for all the sampled locations (grouped on a 1-degree grid) and stores the hourly mean of every area in MongoDB, which the app reads.
- **Norges Bank API:** daily EUR and USD exchange rates, used as optional exogenous variables in the forecast.

## File structure
```
├── .streamlit/
│   ├── config.toml               theme of the app (colours, fonts, borders, chart colours, sidebar)
│   └── secrets.toml              API token and MongoDB connection string (not on GitHub)
├── data/
│   └── areas.geojson             simplified outlines of the price areas and precipitation areas (part 4 notebook)
├── modules/
│   ├── __init__.py
│   ├── analysis.py               SPC, LOF, STL and spectrogram as Plotly figures (same methods as the notebook)
│   ├── api.py                    download of the NVE reservoir statistics and area list (cached)
│   ├── db.py                     MongoDB connection and queries of the cross-border flows (cached)
│   ├── forecast.py               weekly dataset, SNARIMAX forecast with River and error band (part 4 notebook)
│   ├── layout.py                 header shared by all pages: title, badges with the active area and period
│   ├── session.py                global area and period in st.session_state, and their selectors
│   ├── theme.py                  colours shared by all the Plotly charts
│   └── weather.py                hourly and weekly weather of the areas from MongoDB (cached)
├── notebooks/
│   ├── pw1.ipynb                 project work part 1
│   ├── pw2.ipynb                 project work part 2
│   ├── pw3.ipynb                 project work part 3
│   ├── pw4.ipynb                 project work part 4
│   └── layout_sketch.png         sketch of the app structure, shown in the part 4 notebook
├── pages/
│   ├── 1_Map.py                  interactive map: click an area, choose the period and the colouring
│   ├── 2_Reservoirs.py           tabs "Overview" (table with line charts) and "Trends" (line charts)
│   ├── 3_Areas.py                latest filling of every area and the areas covered by the NVE API
│   ├── 4_Cross_border_flows.py   pie chart and line plot of the ENTSO-E flows from MongoDB
│   ├── 6_Reservoir_analysis.py   tabs "STL decomposition" and "Spectrogram" of the filling rate
│   ├── 7_Weather_anomalies.py    tabs "Outliers (SPC on SATV)" and "Anomalies (LOF)" of the weather
│   ├── 8_Correlation.py          sliding window correlation between weather and reservoirs
│   └── 9_Forecasting.py          SNARIMAX forecast of the filling with a Plotly animation
├── app.py                        entry point: grouped menu with st.navigation and the global selectors
├── Home.py                       home page: key numbers and cards linking to the sections
├── requirements.txt              packages for Streamlit Cloud
├── pyproject.toml / uv.lock      local Python environment (uv)
└── README.md
```
The shapefiles and the raw weather downloads used by the notebooks are kept in a local `No_sync/` folder, which is excluded from Git.

## Pages
`app.py` builds the sidebar menu with `st.navigation`, grouped by task, in the order of the work flow: choose area and period on the map, look at the data, analyse, forecast. Below the menu, the **📍 Area** button opens the global area selector (type of area and area), and a caption shows the active period.

| Section | Page | Content | Data source |
|---|---|---|---|
| | Home | Latest filling of Norway and the price areas with a mini chart of the last year; cards linking to every section | NVE API |
| Map | Map | Price areas or precipitation areas coloured by reservoir filling or a weather variable in the chosen period; a click selects the area (thicker contrast outline); week slider for the global period | NVE API, MongoDB (weather), GeoJSON |
| Reservoirs | Reservoirs | Months to download; one row per data column with a line chart per area, and weekly trends | NVE API |
| | Areas | Latest filling of every area of the chosen type, and the areas described by the API | NVE API |
| Weather | Weather anomalies | Outliers with SPC on the DCT-filtered series (variable, default temperature; cut-off in days; standard deviations) and anomalies with LOF (variable, default precipitation; proportion) in the chosen area and period | MongoDB (weather) |
| Analysis | Reservoir analysis | STL decomposition and spectrogram of the filling rate of the chosen area | NVE API |
| | Sliding window correlation | Correlation between a weather variable and a reservoir variable, with selectable window length and lag; the chosen period is shaded | NVE API, MongoDB (weather) |
| Forecast | Forecasting | SNARIMAX with selectable order, seasonal order, learning rate, training history, horizon and exogenous variables; Plotly animation with a 90 % error band | NVE API, MongoDB (weather), Norges Bank |
| Electricity | Cross-border flows | Pie chart of yearly import/export per connection, line plot of hourly flows for any months | ENTSO-E, via MongoDB |

### Selections shared by the pages
Two selections are kept in `st.session_state` (`modules/session.py`), so they stay the same while the user moves between pages:
- the **area**, chosen with the sidebar button or by clicking the map (the map's `on_select` callback stores it);
- the **period**, chosen with the week slider of the Map page. Streamlit deletes the state of a widget when its page is left, so the slider value is copied to a normal key of `st.session_state` in its `on_change` callback. The weather, correlation and forecasting pages use it as default (the forecast starts at the end of the period, and the training ends there).

Local choices that only matter for one page (months to download, variables, model parameters) stay on that page, in a bordered box above the chart. Each page starts with the same header (`modules/layout.py`): title, a blue badge with the active area and, where it is used, an orange badge with the active period.

### Theme
`.streamlit/config.toml` sets a dark theme with a cyan primary colour, the fonts Inter (text) and Space Grotesk (titles), rounded corners, widget borders and a darker sidebar. `modules/theme.py` contains the same colours for the Plotly charts, so all the plots follow the theme; all plots are interactive (Plotly or Streamlit charts), with no static matplotlib figures. On the map, water variables go from dark blue (little) to bright cyan (much) and temperature from blue to red.

### Waiting time and errors
Every download and database query is cached with `st.cache_data` (the MongoDB connection with `st.cache_resource`), with a `show_spinner` message while it runs; the forecast and its error band are cached too, so moving the animation or changing page does not retrain the model. Empty selections and too short training periods give a warning in the app instead of an error, and if the Norges Bank API is not reachable the forecast still works without the currencies.

## Running the project locally
1. Create the environment with `uv sync` (or install `requirements.txt`).
2. Create `.streamlit/secrets.toml` (see below).
3. Start the app from the project folder: `uv run streamlit run app.py`.

The notebooks additionally need Cassandra running in Docker and Spark with Java 17 (and the winutils drivers on Windows), as described in the IND320 book. On Windows, Spark receives the Pandas data through Apache Arrow, which avoids crashes of the Spark Python workers. The notebooks of parts 3 and 4 need the NVE shapefiles in `No_sync/`. The weather download of part 4 (about 17 000 open-meteo calls) is saved in `No_sync/` chunk by chunk, so it can be stopped and resumed.

## Secrets
`secrets.toml` is excluded from Git by `.gitignore`. It has this structure:
```toml
[entsoe]
api_token = "..."   # ENTSO-E security token (used by the notebook only)

[mongo]
uri = "mongodb+srv://..."   # MongoDB Atlas connection string
```
On Streamlit Cloud only the `[mongo]` section is needed; it is pasted under the app's *Settings → Secrets* instead of being stored on GitHub.
