# IND320 – Norwegian Reservoirs, Weather and Cross-border Flows

- Author: Mattia Franchi
- Course: IND320 – Data to Decision, project work
- Streamlit app: https://ind320-m4tti4fr4nchi-ybf3fy4znakvdenhn4kked.streamlit.app/

The project combines Jupyter Notebooks, where data are downloaded, processed and stored, with a Streamlit app that presents them.

- **NVE Magasinstatistikk API:** weekly reservoir statistics for Norway, its five price areas and its river basins. The app downloads them directly from the API.
- **ENTSO-E Transparency Platform:** hourly physical cross-border flows between Norway and its six neighbours. The notebook downloads them, writes them to Cassandra with Spark, extracts them again with Spark and stores them in MongoDB, which the app reads.
- **NVE shapefiles (atlas.nve.no):** borders of the price areas and of the regions. The notebook samples 1000 random locations inside each area with GeoPandas and stores them in MongoDB.
- **open-meteo historical API:** hourly ERA5 weather reanalysis. The app downloads it for some of the sampled locations of the chosen area and averages them.

## File structure
```
├── .streamlit/
│   ├── config.toml               theme of the app
│   └── secrets.toml              API token and MongoDB connection string (not on GitHub)
├── modules/
│   ├── __init__.py
│   ├── analysis.py               SPC, LOF, STL and spectrogram as Plotly figures (same methods as the notebook)
│   ├── api.py                    download of the NVE reservoir statistics and area list (cached)
│   ├── db.py                     MongoDB connection and queries (cached)
│   ├── session.py                global area selector and the months slider of the Reservoirs page
│   └── weather.py                sampled locations from MongoDB and open-meteo download (cached)
├── notebooks/
│   ├── pw1.ipynb                 project work part 1
│   ├── pw2.ipynb                 project work part 2
│   └── pw3.ipynb                 project work part 3
├── pages/
│   ├── 2_Reservoirs.py           tabs "Overview" (table with line charts) and "Trends" (line charts)
│   ├── 3_Areas.py                areas of Norway covered by the NVE API
│   ├── 4_Cross_border_flows.py   pie chart and line plot of the ENTSO-E flows from MongoDB
│   ├── 5_Extra.py                latest filling rate of every area
│   ├── 6_Reservoir_analysis.py   tabs "STL decomposition" and "Spectrogram" of the filling rate
│   └── 7_Weather_anomalies.py    tabs "Outliers (SPC)" and "Anomalies (LOF)" of the weather data
├── app.py                        entry point: menu with st.navigation and the global area selector
├── Home.py                       home page with a guide to the other pages
├── requirements.txt              packages for Streamlit Cloud
├── pyproject.toml / uv.lock      local Python environment (uv)
└── README.md
```
The shapefiles used by the notebook are kept in a local `No_sync/` folder, which is excluded from Git.

### Pages
`app.py` builds the sidebar menu with `st.navigation`, which sets the name, order and section of each page. Below the menu, the **📍 Area** button opens the global area selector (area type EL, NO or VASS and the area), which is shared by all pages.

| Section | Page | Content | Data source |
|---|---|---|---|
| | Home | Guide to the pages | – |
| Reservoirs | Reservoirs | Slider with the months to download; one row per data column with a line chart per area, and weekly trends | NVE API |
| | Reservoir analysis | STL decomposition (seasonal and trend smoothers, robust fitting) and spectrogram (window length and overlap) of the filling rate of the chosen area | NVE API |
| | Areas | The areas of Norway described by the API | NVE API |
| | Extra | Latest filling rate of every area | NVE API |
| Weather | Weather anomalies | Year selector; outliers with SPC on DCT-filtered data (cut-off and number of standard deviations) and anomalies with LOF (proportion of anomalies) | open-meteo (ERA5), locations from MongoDB |
| Electricity | Cross-border flows | Pie chart of yearly import/export per connection, line plot of hourly flows for any months | ENTSO-E, via MongoDB |

### modules/
Code shared by the pages, so that each page only contains its layout:
- `analysis.py` contains the analyses of the third notebook (SPC, LOF, STL and spectrogram) with the same parameters and defaults, but returns interactive Plotly figures.
- `api.py` downloads the NVE data with `requests`, translates the column names to English (as in the notebook) and caches the result with `st.cache_data`.
- `db.py` opens one MongoDB connection with `st.cache_resource` and runs the queries of the cross-border page, including an aggregation that sums the yearly energy in MongoDB.
- `session.py` draws the global area selector in the sidebar and the months slider of the Reservoirs page.
- `weather.py` reads the sampled locations from MongoDB and downloads one year of hourly ERA5 data from open-meteo for 10 of them. The download is cached for a day, so each area and year is downloaded only once.

## Running the project locally
1. Create the environment with `uv sync` (or install `requirements.txt`).
2. Create `.streamlit/secrets.toml` (see below).
3. Start the app from the project folder: `streamlit run app.py`.

The notebooks additionally need Cassandra running in Docker and Spark with Java 17 (and the winutils drivers on Windows), as described in the IND320 book. On Windows, Spark receives the Pandas data through Apache Arrow, which avoids crashes of the Spark Python workers. The third notebook needs the NVE shapefiles in `No_sync/`.

## Secrets
`secrets.toml` is excluded from Git by `.gitignore`. It has this structure:
```toml
[entsoe]
api_token = "..."   # ENTSO-E security token (used by the notebook only)

[mongo]
uri = "mongodb+srv://..."   # MongoDB Atlas connection string
```
On Streamlit Cloud only the `[mongo]` section is needed; it is pasted under the app's *Settings → Secrets* instead of being stored on GitHub.
