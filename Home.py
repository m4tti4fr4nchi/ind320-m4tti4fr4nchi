import streamlit as st

from modules.api import available_months, download_reservoirs

# Page settings for the home page (each page sets its own through page_header in modules/layout.py)
st.set_page_config(page_title="IND320 Energy App", page_icon="💧", layout="wide")

st.title("💧 Reservoirs, Weather and Power Flows in Norway")
st.write("Project work for IND320. Start on the **Map**: click an area and choose a period. The area and the "
         "period are kept while you move between the pages, and are shown below the menu in the sidebar.")

# --- Key numbers: latest filling rate of Norway and of the price areas, with the last year as a mini chart ---
months = available_months()
reservoirs = download_reservoirs(months[-13], months[-1])   # the last twelve months (plus the current one)
latest_date = reservoirs["date"].max()
st.subheader(f"Reservoir filling, week ending {latest_date:%d %B %Y}")
cards = st.columns(6)
for card, area in zip(cards, ["Norway", "NO1", "NO2", "NO3", "NO4", "NO5"]):
    series = reservoirs[reservoirs["area"] == area].sort_values("date")
    last = series.iloc[-1]
    card.metric(area, f"{last['filling_rate'] * 100:.1f} %",
                delta=f"{last['filling_rate_change'] * 100:+.1f} pts/week",
                delta_color="off",   # neutral: emptying in winter and filling in spring are normal, not alarms
                chart_data=(series["filling_rate"] * 100).round(1).tolist(),   # mini line: the last year
                chart_type="area", border=True)

# --- The sections of the app as cards, with a link to each page (same grouping as the menu) ---
st.subheader("Explore the app")
SECTIONS = [
    ("🗺️ Map", "Choose the area and the period on a map of Norway, coloured by reservoir filling or weather.",
     [("pages/1_Map.py", "Map", "🗺️")]),
    ("💧 Reservoirs", "Weekly NVE reservoir statistics of all areas, and the latest filling of each area.",
     [("pages/2_Reservoirs.py", "Reservoirs", "💧"), ("pages/3_Areas.py", "Areas", "📋")]),
    ("🌦️ Weather", "Outliers and anomalies in the hourly ERA5 weather of the chosen area and period.",
     [("pages/7_Weather_anomalies.py", "Weather anomalies", "🌦️")]),
    ("📈 Analysis", "Seasonal decomposition, spectrogram and the sliding window correlation with the weather.",
     [("pages/6_Reservoir_analysis.py", "Reservoir analysis", "📈"),
      ("pages/8_Correlation.py", "Sliding window correlation", "🔗")]),
    ("🔮 Forecast", "Weekly forecast of the filling with SNARIMAX, exogenous variables and a 90 % band.",
     [("pages/9_Forecasting.py", "Forecasting", "🔮")]),
    ("⚡ Electricity", "Import and export of electricity between Norway and its neighbours (ENTSO-E).",
     [("pages/4_Cross_border_flows.py", "Cross-border flows", "⚡")]),
]
for row in range(0, len(SECTIONS), 3):
    for column, (title, text, links) in zip(st.columns(3), SECTIONS[row:row + 3]):
        with column.container(border=True, height="stretch"):
            st.markdown(f"#### {title}")
            st.caption(text)
            for page, label, icon in links:
                st.page_link(page, label=label, icon=icon)   # link to a page registered in app.py

with st.expander("Data sources and processing"):
    st.markdown(
        "- **Reservoirs:** NVE Magasinstatistikk API, downloaded by the app when a page needs it.\n"
        "- **Weather:** ERA5 reanalysis from open-meteo, downloaded in the notebook of part 4 for all the "
        "locations sampled in part 3 (grouped on a 1-degree grid), averaged per area and stored in MongoDB.\n"
        "- **Exchange rates:** Norges Bank API (EUR and USD), used as exogenous variables in the forecast.\n"
        "- **Cross-border flows:** ENTSO-E, processed with Cassandra and Spark in part 2 and stored in MongoDB.\n"
        "- **Areas:** price areas and NVE regions from atlas.nve.no, converted to GeoJSON in the notebook."
    )
