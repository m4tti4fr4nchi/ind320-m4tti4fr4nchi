import streamlit as st

from modules.session import area_selector

# st.navigation defines the menu in the sidebar: the order of the pages, the name shown for each one
# and the sections they are grouped in (a dictionary: section title -> list of pages; "" = no title).
# The menu follows the work flow: choose area and period on the map, look at the data, analyse, forecast.
pages = {
    "": [st.Page("Home.py", title="Home", icon="🏠", default=True)],
    "Map": [
        st.Page("pages/1_Map.py", title="Map", icon="🗺️"),
    ],
    "Reservoirs": [
        st.Page("pages/2_Reservoirs.py", title="Reservoirs", icon="💧"),
        st.Page("pages/3_Areas.py", title="Areas", icon="📋"),
    ],
    "Weather": [
        st.Page("pages/7_Weather_anomalies.py", title="Weather anomalies", icon="🌦️"),
    ],
    "Analysis": [
        st.Page("pages/6_Reservoir_analysis.py", title="Reservoir analysis", icon="📈"),
        st.Page("pages/8_Correlation.py", title="Sliding window correlation", icon="🔗"),
    ],
    "Forecast": [
        st.Page("pages/9_Forecasting.py", title="Forecasting", icon="🔮"),
    ],
    "Electricity": [
        st.Page("pages/4_Cross_border_flows.py", title="Cross-border flows", icon="⚡"),
    ],
}
page = st.navigation(pages)

# Global area selector (and the active period) in the sidebar: drawn here, before page.run(), so it is
# shared by all pages; the values are kept in st.session_state
area_selector()

page.run()
