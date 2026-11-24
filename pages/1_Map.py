import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules.api import FIRST_MONTH, available_months, download_reservoirs
from modules.theme import PRIMARY as HIGHLIGHT
from modules.session import AREAS_BY_TYPE, period_days, period_slider, select_area, selected_area
from modules.weather import SUM_VARIABLES, WEATHER_VARIABLES, load_weather, weather_by_area, weekly
from modules.layout import page_header

FILLING = "filling_rate"
COLOUR_OPTIONS = {FILLING: "Reservoir filling (%)", **WEATHER_VARIABLES}
# Water: from dark blue (little) to the bright cyan of the theme (much), so on the dark map the areas with much
# water stand out (a white-to-blue scale would make the areas with little water the brightest ones)
WATER = [[0, "#1e3a5f"], [0.5, "#2b8cc4"], [1, "#a5f3fc"]]
# Colour scales that match the meaning of each variable (blue = water, red/blue = warm/cold); Viridis and Cividis
# (readable also with colour blindness, see the course book) for the variables without a natural colour
COLOUR_SCALES = {FILLING: WATER, "temperature_2m": "RdBu_r", "precipitation": WATER, "rain": WATER,
                 "snowfall": "Purples", "relative_humidity_2m": "Viridis", "cloud_cover": "Cividis",
                 "wind_speed_10m": "Viridis", "wind_gusts_10m": "Viridis"}


@st.cache_data
def load_areas():
    """Outlines of the price areas and precipitation areas, made from the NVE shapefiles in the notebook."""
    return json.loads(Path("data/areas.geojson").read_text(encoding="utf-8"))


def on_map_click():
    # Callback of the map: runs before the page is drawn again, so it may change the global area
    points = st.session_state["map"]["selection"]["points"]
    if points:
        select_area(points[0]["location"])


page_header("Map", "🗺️",
            "Price areas and precipitation areas of Norway, coloured by reservoir filling or by a weather "
            "variable in the chosen period. **Click an area** to select it: the area and the period are used by "
            "all the other pages.", show_period=True)

# --- Controls: type of areas, colour and period (the period is stored in st.session_state) ---
global_type, area = selected_area()
controls = st.container(border=True)   # all the controls of the map in one bordered box
left, right = controls.columns([1, 2])
area_type = left.radio("Areas", ["EL", "VASS"], horizontal=True, index=1 if global_type == "VASS" else 0,
                       format_func={"EL": "Price areas (NO1–NO5)", "VASS": "Precipitation areas (VASS1–3)"}.get)
colour = right.selectbox("Colour by", list(COLOUR_OPTIONS), format_func=COLOUR_OPTIONS.get)
with controls:
    period_slider()
start, end = period_days()

# --- One value per area in the period ---
if colour == FILLING:
    reservoirs = download_reservoirs(FIRST_MONTH, available_months()[-1])
    in_period = reservoirs[reservoirs["date"].between(start, end) & (reservoirs["area_type"] == area_type)]
    values = (in_period.groupby("area")[FILLING].mean() * 100).round(1).rename("value").reset_index()
    value_label = "Mean filling (%)"
else:
    values = weather_by_area(colour, start, end)
    values = values[values["area"].isin(AREAS_BY_TYPE[area_type])]
    value_label = COLOUR_OPTIONS[colour] + (", mean weekly total" if colour in SUM_VARIABLES else ", mean")

geojson = load_areas()
features = {"type": "FeatureCollection",
            "features": [f for f in geojson["features"] if f["properties"]["area_type"] == area_type]}

# --- Choropleth map: one coloured polygon per area, plus a thick outline around the selected area ---
fig = px.choropleth_map(values, geojson=features, locations="area", featureidkey="properties.area",
                        color="value", color_continuous_scale=COLOUR_SCALES[colour], opacity=0.75,
                        labels={"value": value_label}, hover_name="area",
                        map_style="carto-darkmatter", center={"lat": 64.5, "lon": 15}, zoom=3.3)
fig.update_traces(marker_line_color="white", marker_line_width=0.8)
if area in values["area"].tolist():
    fig.add_trace(go.Choroplethmap(geojson=features, locations=[area], featureidkey="properties.area", z=[0],
                                   colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]], showscale=False,
                                   marker_line_color=HIGHLIGHT, marker_line_width=4, hoverinfo="skip"))
fig.update_layout(height=620, margin=dict(l=0, r=0, t=0, b=0),
                  coloraxis_colorbar=dict(title=value_label, title_side="right"))

map_column, info_column = st.columns([3, 1])
with map_column:
    # on_select: a click on an area reruns the page and calls on_map_click with the clicked area
    st.plotly_chart(fig, key="map", on_select=on_map_click, selection_mode="points", width="stretch")

with info_column:
    st.subheader(f"📍 {area}")
    st.caption(f"{start:%d %b %Y} – {end:%d %b %Y}")
    if area in values["area"].tolist():
        value = values.set_index("area").loc[area, "value"]
        mean_all = values["value"].mean()
        st.metric(value_label, f"{value:.1f}", delta=f"{value - mean_all:+.1f} vs. mean of the areas",
                  delta_color="off", border=True)
        ranking = values.sort_values("value", ascending=False).reset_index(drop=True)
        st.dataframe(ranking.rename(columns={"area": "Area", "value": value_label}), hide_index=True,
                     width="stretch")
    else:
        st.info(f"{area} is not one of the areas shown. Click an area on the map to select it.")

# --- Weekly time series of the selected area in the period ---
if area in values["area"].tolist():
    if colour == FILLING:
        series = (in_period[in_period["area"] == area].set_index("date")[FILLING] * 100).rename(COLOUR_OPTIONS[colour])
    else:
        series = weekly(load_weather(area, start, end))[colour].rename(COLOUR_OPTIONS[colour])
    line = px.line(series, labels={"value": COLOUR_OPTIONS[colour], "index": "Week", "date": "Week", "time": "Week"},
                   title=f"{COLOUR_OPTIONS[colour]} in {area}, weekly")
    line.update_traces(line_color=HIGHLIGHT)
    line.update_layout(showlegend=False, height=300, margin=dict(t=40, b=0))
    st.plotly_chart(line, width="stretch")

with st.expander("Data sources"):
    st.markdown(
        "- **Areas:** price areas (Budområder) and NVE regions from [atlas.nve.no](https://atlas.nve.no), "
        "converted to GeoJSON in the notebook; the precipitation areas join the NVE regions as in "
        "Magasinstatistikk (VASS1 = East + South, VASS2 = West, VASS3 = Central + North).\n"
        "- **Reservoir filling:** NVE Magasinstatistikk API, weekly.\n"
        "- **Weather:** ERA5 from open-meteo, hourly mean of all the sampled locations of each area (MongoDB)."
    )
