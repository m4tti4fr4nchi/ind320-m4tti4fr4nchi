# IND320 – Norwegian Reservoirs and Cross-border Flows

- Author: Mattia Franchi
- Course: IND320 – Data to Decision, project work
- Streamlit app: https://ind320-m4tti4fr4nchi-ybf3fy4znakvdenhn4kked.streamlit.app/

The project combines Jupyter Notebooks, where data are downloaded, processed and stored, with a Streamlit app that presents them.

- **NVE Magasinstatistikk API:** weekly reservoir statistics for Norway, its five price areas and its river basins. The app downloads them directly from the API.
- **ENTSO-E Transparency Platform:** hourly physical cross-border flows between Norway and its six neighbours. The notebook downloads them, writes them to Cassandra with Spark, extracts them again with Spark and stores them in MongoDB, which the app reads.

## File structure
```
├── .streamlit/
│   ├── config.toml               theme of the app
│   └── secrets.toml              API token and MongoDB connection string (not on GitHub)
├── modules/
│   ├── __init__.py
│   ├── api.py                    download of the NVE reservoir statistics and area list (cached)
│   ├── db.py                     MongoDB connection and queries (cached)
│   └── session.py                controls of the Reservoirs page (area type and months to download)
├── notebooks/
│   ├── pw1.ipynb                 project work part 1
│   └── pw2.ipynb                 project work part 2
├── pages/
│   ├── 2_Reservoirs.py           tabs "Overview" (table with line charts) and "Trends" (line charts)
│   ├── 3_Areas.py                areas of Norway covered by the NVE API
│   ├── 4_Cross_border_flows.py   pie chart and line plot of the ENTSO-E flows from MongoDB
│   └── 5_Extra.py                latest filling rate of every area
├── app.py                        entry point: defines the menu with st.navigation
├── Home.py                       home page with a guide to the other pages
├── requirements.txt              packages for Streamlit Cloud
├── pyproject.toml / uv.lock      local Python environment (uv)
└── README.md
```

### Pages
`app.py` builds the sidebar menu with `st.navigation`, which sets the name and order of each page:

| Page | Content | Data source |
|---|---|---|
| Home | Guide to the pages | – |
| Reservoirs | Radio buttons (EL, NO, VASS) and a slider that sets the months to download; one row per data column with a line chart per area, and weekly trends | NVE API |
| Areas | The areas of Norway described by the API | NVE API |
| Cross-border flows | Pie chart of yearly import/export per connection, line plot of hourly flows for any months | ENTSO-E, via MongoDB |
| Extra | Latest filling rate of every area | NVE API |

### modules/
Code shared by the pages, so that each page only contains its layout:
- `api.py` downloads the NVE data with `requests`, translates the column names to English (as in the notebook) and caches the result with `st.cache_data`.
- `db.py` opens one MongoDB connection with `st.cache_resource` and runs the queries of the cross-border page, including an aggregation that sums the yearly energy in MongoDB.
- `session.py` draws the radio buttons and the selection slider of the Reservoirs page.

## Running the project locally
1. Create the environment with `uv sync` (or install `requirements.txt`).
2. Create `.streamlit/secrets.toml` (see below).
3. Start the app from the project folder: `streamlit run app.py`.

The notebooks additionally need Cassandra running in Docker and Spark with Java 17 (and the winutils drivers on Windows), as described in the IND320 book. On Windows, Spark receives the Pandas data through Apache Arrow, which avoids crashes of the Spark Python workers.

## Secrets
`secrets.toml` is excluded from Git by `.gitignore`. It has this structure:
```toml
[entsoe]
api_token = "..."   # ENTSO-E security token (used by the notebook only)

[mongo]
uri = "mongodb+srv://..."   # MongoDB Atlas connection string
```
On Streamlit Cloud only the `[mongo]` section is needed; it is pasted under the app's *Settings → Secrets* instead of being stored on GitHub.