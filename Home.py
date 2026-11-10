import streamlit as st

# Page settings for the home page (each file in pages/ sets its own, e.g. the wide layout)
st.set_page_config(page_title="IND320 Energy App", page_icon="💧")

st.title("Norwegian Reservoirs, Weather and Cross-border Flows")
st.write("Project work for IND320. Use the menu in the sidebar to move between the pages, and the "
         "**📍 Area** button below it to choose the area shown by the reservoir and weather pages.")

# Short guide to the pages, grouped as in the menu (st.markdown renders Markdown text, including tables)
st.markdown("""
| Section | Page | Content | Data source |
|---|---|---|---|
| Reservoirs | **Reservoirs** | Two tabs: one row per data column with a line chart for each area, and the weekly trends with one line per area | NVE Magasinstatistikk API |
| | **Reservoir analysis** | Two tabs: STL decomposition and spectrogram of the weekly filling rate of the chosen area | NVE Magasinstatistikk API |
| | **Areas** | The areas of Norway covered by the NVE statistics | NVE Magasinstatistikk API |
| | **Extra** | Latest filling rate of every area | NVE Magasinstatistikk API |
| Weather | **Weather anomalies** | Two tabs: outliers with SPC on DCT-filtered data, and anomalies with the Local Outlier Factor, for the chosen area and year | open-meteo (ERA5), locations from MongoDB |
| Electricity | **Cross-border flows** | Yearly import/export per connection and hourly flows for any months | ENTSO-E, stored in MongoDB |
""")

st.caption("The reservoir data are downloaded directly from the NVE API when a page needs them. "
           "The cross-border flows were downloaded from ENTSO-E in the Jupyter Notebook, processed with "
           "Cassandra and Spark, and stored in MongoDB, which this app reads. The weather data are downloaded "
           "from open-meteo for random locations inside the chosen area, sampled in the notebook from the NVE "
           "shapefiles and stored in MongoDB.")