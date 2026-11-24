import streamlit as st

from modules.analysis import lof_anomalies, spc_outliers
from modules.session import period_days, selected_area
from modules.weather import WEATHER_VARIABLES, load_weather
from modules.layout import page_header

page_header("Weather Anomalies", "🌦️",
            "Hourly ERA5 reanalysis for the chosen area and period. The first tab finds outliers with Statistical "
            "Process Control on the seasonally adjusted variations (SATV), the second anomalies with the Local "
            "Outlier Factor.", show_period=True)

# Global area (sidebar) and global period (Map page): both are kept in st.session_state
_, area = selected_area()
start, end = period_days()
weather = load_weather(area, start, end)
if weather.empty:
    st.warning("No weather data for this area and period.")
    st.stop()
st.caption(f"Hourly weather of {area} from {start:%d %b %Y} to {end:%d %b %Y} ({len(weather):,} hours). "
           "Weighted mean of all the locations sampled inside the area.")

spc_tab, lof_tab = st.tabs(["Outliers (SPC on SATV)", "Anomalies (LOF)"])

# --- Outliers: DCT high-pass filter + SPC boundaries from robust statistics ---
with spc_tab:
    left, middle, right = st.container(border=True).columns(3)
    variable = left.selectbox("Variable", list(WEATHER_VARIABLES), format_func=WEATHER_VARIABLES.get,
                              index=list(WEATHER_VARIABLES).index("temperature_2m"), key="spc_variable")
    slowest_days = middle.slider("Remove variations slower than (days)", 1, 30, 7,
                                 help="The DCT high-pass filter removes the slow, seasonal part of the series; "
                                      "what is left is the seasonally adjusted variation (SATV).")
    n_std = right.slider("Robust standard deviations", 1.0, 6.0, 3.0, step=0.5)

    # DCT component k has a period of 2N/k hours (N = number of hours), so the cut-off follows the chosen days
    cutoff = max(1, round(2 * len(weather) / (slowest_days * 24)))
    fig, outliers, summary = spc_outliers(weather[variable], cutoff, n_std, label=WEATHER_VARIABLES[variable])
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Outliers", f"{summary['outliers']:,}", border=True)
    c2.metric("Share of hours", f"{summary['share']:.2f} %", border=True)
    c3.metric("Above / below", f"{summary['above']} / {summary['below']}", border=True)
    c4.metric("Robust SD of SATV", f"{summary['robust_sd']:.3f}", border=True)
    with st.expander("Outlier hours"):
        st.dataframe(outliers.sort_values("satv", key=abs, ascending=False), width="stretch")

# --- Anomalies: Local Outlier Factor on value and time ---
with lof_tab:
    left, right = st.container(border=True).columns(2)
    variable = left.selectbox("Variable", list(WEATHER_VARIABLES), format_func=WEATHER_VARIABLES.get,
                              index=list(WEATHER_VARIABLES).index("precipitation"), key="lof_variable")
    contamination = right.slider("Proportion of anomalies (%)", 0.1, 10.0, 1.0, step=0.1) / 100

    fig, anomalies, summary = lof_anomalies(weather[variable], contamination, label=WEATHER_VARIABLES[variable])
    st.plotly_chart(fig, width="stretch")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Anomalies", f"{summary['anomalies']:,}", border=True)
    c2.metric("Share of hours", f"{summary['share']:.2f} %", border=True)
    c3.metric("Mean of anomalies / all", f"{summary['mean_anomalies']:.2f} / {summary['mean_all']:.2f}", border=True)
    c4.metric("LOF score threshold", f"{summary['threshold']:.2f}", border=True)
    with st.expander("Anomalous hours"):
        st.dataframe(anomalies.sort_values("lof_score", ascending=False), width="stretch")

with st.expander("Data source"):
    st.markdown(
        "- **Weather:** [open-meteo](https://open-meteo.com/en/docs/historical-weather-api) historical API, "
        "ERA5 reanalysis, hourly values in UTC, 2021–2025.\n"
        "- **Locations:** all 1000 points sampled per area in part 3, grouped on a 1-degree grid (130 locations "
        "in total). The notebook of part 4 downloaded each location once and stored the weighted mean of every "
        "area in MongoDB, which this page reads.\n"
        "- **Methods:** as in the notebook – DCT high-pass filter and SPC boundaries from the median and MAD; "
        "Local Outlier Factor on the standardised value and the time position."
    )
