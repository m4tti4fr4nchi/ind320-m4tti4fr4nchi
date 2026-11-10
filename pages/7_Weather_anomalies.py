import pandas as pd
import requests
import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.session import selected_area
from modules.weather import WEATHER_VARIABLES, download_weather

st.set_page_config(layout="wide")
st.title("Weather Anomalies")
st.write("Hourly ERA5 reanalysis from open-meteo for the area chosen in the sidebar, averaged over random "
         "locations inside the area. The first tab finds outliers with Statistical Process Control, the second "
         "anomalies with the Local Outlier Factor.")

# Global area (sidebar) and a local choice of year: the weather download depends on both
_, area = selected_area()
this_year = pd.Timestamp.now().year
year = st.selectbox("Year", list(range(this_year - 1, 1999, -1)), index=1)  # complete years; default: last year but one

# Hidden download: cached per area and year, with a spinner while open-meteo answers
try:
    weather, locations = download_weather(area, year)
except requests.HTTPError as error:
    # The free API allows 600 calls per minute; one area and year with 10 locations counts as about 261 calls
    if error.response is not None and error.response.status_code == 429:
        st.warning("open-meteo's free API limit was reached (too many downloads in a short time). "
                   "Please wait a minute and reload the page.")
    else:
        st.error(f"The weather download failed: {error}")
    st.stop()
st.caption(f"ERA5 hourly data for {area}, {year}: average of {len(locations)} random locations "
           f"({len(weather):,} hours).")
with st.expander("Downloaded locations"):
    st.map(locations, latitude="latitude", longitude="longitude", size=3000)  # confirmation of the download

spc_tab, lof_tab = st.tabs(["Outliers (SPC)", "Anomalies (LOF)"])

# --- Outliers: DCT high-pass filter + SPC boundaries from robust statistics ---
with spc_tab:
    left, middle, right = st.columns(3)
    # Precipitation as in the assignment text; the temperature (as in last year's task) is one click away
    variable = left.selectbox("Variable", list(WEATHER_VARIABLES), format_func=WEATHER_VARIABLES.get,
                              index=list(WEATHER_VARIABLES).index("precipitation"), key="spc_variable")
    cutoff = middle.slider("DCT frequency cut-off", 10, 500, 100, step=10,
                           help="Components below the cut-off (slow, seasonal variations) are removed. "
                                "100 removes variations slower than about one week.")
    n_std = right.slider("Robust standard deviations", 1.0, 6.0, 3.0, step=0.5)

    fig, outliers, summary = spc_outliers(weather[variable], cutoff, n_std, label=WEATHER_VARIABLES[variable])
    st.plotly_chart(fig, width="stretch")

    # Summary statistics of the outliers
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Outliers", f"{summary['outliers']:,}")
    c2.metric("Share of hours", f"{summary['share']:.2f} %")
    c3.metric("Above / below", f"{summary['above']} / {summary['below']}")
    c4.metric("Robust SD of SATV", f"{summary['robust_sd']:.3f}")
    with st.expander("Outlier hours"):
        st.dataframe(outliers.sort_values("satv", key=abs, ascending=False), width="stretch")

# --- Anomalies: Local Outlier Factor on value and time ---
with lof_tab:
    left, right = st.columns(2)
    variable = left.selectbox("Variable", list(WEATHER_VARIABLES), format_func=WEATHER_VARIABLES.get,
                              index=list(WEATHER_VARIABLES).index("temperature_2m"), key="lof_variable")
    contamination = right.slider("Proportion of anomalies (%)", 0.1, 10.0, 1.0, step=0.1) / 100

    fig, anomalies, summary = lof_anomalies(weather[variable], contamination, label=WEATHER_VARIABLES[variable])
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomalies", f"{summary['anomalies']:,}")
    c2.metric("Share of hours", f"{summary['share']:.2f} %")
    c3.metric("Mean of anomalies / all", f"{summary['mean_anomalies']:.2f} / {summary['mean_all']:.2f}")
    c4.metric("LOF score threshold", f"{summary['threshold']:.2f}")
    with st.expander("Anomalous hours"):
        st.dataframe(anomalies.sort_values("lof_score", ascending=False), width="stretch")

with st.expander("Data source"):
    st.markdown(
        "- **Weather:** [open-meteo](https://open-meteo.com/en/docs/historical-weather-api) historical API, "
        "ERA5 reanalysis, hourly values in UTC.\n"
        "- **Locations:** 1000 random points per area were sampled in the notebook from the NVE shapefiles "
        "(atlas.nve.no) and stored in MongoDB; this page downloads 10 of them and averages them.\n"
        "- **Methods:** as in the notebook – DCT high-pass filter and SPC boundaries from the median and MAD; "
        "Local Outlier Factor on the standardised value and the time position."
    )