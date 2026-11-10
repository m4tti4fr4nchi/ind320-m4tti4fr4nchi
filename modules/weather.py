"""Module to download hourly ERA5 weather data from open-meteo for the locations sampled in the notebook."""
import pandas as pd
import requests
import streamlit as st

from .db import get_collection

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Same hourly variables as in the notebook (at most 10, so open-meteo counts one call per location and 2 weeks)
WEATHER_VARIABLES = {
    "temperature_2m": "Temperature (°C)",
    "precipitation": "Precipitation (mm)",
    "rain": "Rain (mm)",
    "snowfall": "Snowfall (cm)",
    "relative_humidity_2m": "Relative humidity (%)",
    "cloud_cover": "Cloud cover (%)",
    "wind_speed_10m": "Wind speed (km/h)",
    "wind_gusts_10m": "Wind gusts (km/h)",
}

PRICE_AREAS = ["NO1", "NO2", "NO3", "NO4", "NO5"]


@st.cache_data(ttl=86400)
def get_locations(area, n_locations=10, seed=42):
    """Random locations of one area, taken from the 1000 points per area stored in MongoDB by the notebook.

    "Norway" has no points of its own, so the same number of points is taken from each price area.
    """
    areas = PRICE_AREAS if area == "Norway" else [area]
    points = pd.DataFrame(list(get_collection("sample_points").find({"area": {"$in": areas}}, {"_id": 0})))
    per_area = max(1, n_locations // len(areas))
    return (points.groupby("area", group_keys=False)
            .apply(lambda group: group.sample(n=per_area, random_state=seed))
            .reset_index(drop=True))


# Download "hidden" in the app: cached for a day, so each area and year is downloaded only once
@st.cache_data(ttl=86400, show_spinner="Downloading ERA5 weather data from open-meteo...")
def download_weather(area, year, n_locations=10):
    """Hourly ERA5 reanalysis for the sampled locations of an area and one year (as in the notebook).

    Returns the hourly average over the locations (one row per hour) and the table of locations.
    """
    locations = get_locations(area, n_locations)
    params = {
        "latitude": ",".join(locations["latitude"].astype(str)),     # several locations in one request
        "longitude": ",".join(locations["longitude"].astype(str)),
        "start_date": f"{year}-01-01",
        "end_date": f"{year}-12-31",
        "hourly": ",".join(WEATHER_VARIABLES),
        "models": "era5",
        "timezone": "UTC",
    }
    response = requests.get(ARCHIVE_URL, params=params, timeout=120)
    response.raise_for_status()
    blocks = response.json()
    if isinstance(blocks, dict):  # one location -> one JSON object, several -> a list
        blocks = [blocks]

    hourly = pd.concat([pd.DataFrame(block["hourly"]) for block in blocks])
    hourly["time"] = pd.to_datetime(hourly["time"])
    regional_mean = hourly.groupby("time")[list(WEATHER_VARIABLES)].mean()  # average over the locations
    return regional_mean, locations