import streamlit as st

# Page settings for the home page (each file in pages/ sets its own, e.g. the wide layout)
st.set_page_config(page_title="IND320 Energy App", page_icon="💧")

st.title("Norwegian Reservoirs, Weather and Cross-border Flows")
st.write("Project work for IND320. Start on the **Map**: click an area and choose a period. The area and the "
         "period are kept while you move between the pages, and are shown below the menu in the sidebar "
         "(the **📍 Area** button changes the area from any page).")

# Short guide to the pages, grouped as in the menu (st.markdown renders Markdown text, including tables)
st.markdown("""
| Section | Page | Content | Data source |
|---|---|---|---|
| Map | **Map** | Price areas or precipitation areas coloured by reservoir filling or a weather variable in the chosen period; click an area to select it | NVE shapefiles (GeoJSON), NVE API, MongoDB |
| Reservoirs | **Reservoirs** | Overview with one mini line chart per data column and area, and the weekly trends with one line per area | NVE Magasinstatistikk API |
| | **Areas** | Latest filling rate of every area, and the areas covered by the NVE statistics | NVE Magasinstatistikk API |
| Weather | **Weather anomalies** | Outliers with SPC on the seasonally adjusted variations (temperature by default) and anomalies with the Local Outlier Factor | ERA5 from open-meteo, stored in MongoDB |
| Analysis | **Reservoir analysis** | STL decomposition and spectrogram of the weekly filling rate | NVE Magasinstatistikk API |
| | **Sliding window correlation** | Correlation between a weather variable and a reservoir variable in a sliding window, with a lag | NVE API, MongoDB |
| Forecast | **Forecasting** | Weekly forecast of the filling rate with SNARIMAX (River), exogenous variables, 90 % band and animation | NVE API, MongoDB, Norges Bank |
| Electricity | **Cross-border flows** | Yearly import/export per connection and hourly flows for any months | ENTSO-E, stored in MongoDB |
""")

st.caption("The reservoir data are downloaded directly from the NVE API when a page needs them, and the exchange "
           "rates from Norges Bank. The cross-border flows were downloaded from ENTSO-E in the notebook of part 2, "
           "processed with Cassandra and Spark, and stored in MongoDB. The weather was downloaded from open-meteo in "
           "the notebook of part 4 for all the locations sampled in part 3 (grouped on a 1-degree grid), averaged "
           "per area and stored in MongoDB, which this app reads.")
