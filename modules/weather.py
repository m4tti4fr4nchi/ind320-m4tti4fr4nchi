"""Module to read the hourly ERA5 weather of the areas from MongoDB.

The weather was downloaded in the notebook of part 4 for all 8000 sampled locations (grouped on a 1-degree grid)
and averaged per area; the app only reads the results, so no open-meteo request is needed here.
"""
import pandas as pd
import streamlit as st

from .db import get_collection

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
SUM_VARIABLES = ["precipitation", "rain", "snowfall"]   # added up over a week; the other variables are averaged
PRICE_AREAS = ["NO1", "NO2", "NO3", "NO4", "NO5"]

# Period stored in MongoDB by the notebook (hourly values in UTC)
FIRST_DAY, LAST_DAY = pd.Timestamp("2021-01-01"), pd.Timestamp("2025-12-31")


@st.cache_data(ttl=86400, show_spinner="Loading hourly weather from MongoDB...")
def load_weather(area, start, end):
    """Hourly weather of one area from the first hour of `start` to the last hour of `end` (one row per hour).

    "Norway" has no weather of its own, so it is the mean of the five price areas.
    """
    areas = PRICE_AREAS if area == "Norway" else [area]
    query = {"area": {"$in": areas},
             "time": {"$gte": pd.Timestamp(start).to_pydatetime(),
                      "$lt": (pd.Timestamp(end) + pd.Timedelta(days=1)).to_pydatetime()}}
    hourly = pd.DataFrame(list(get_collection("weather_hourly").find(query, {"_id": 0})))
    if hourly.empty:
        return pd.DataFrame(columns=list(WEATHER_VARIABLES))
    return hourly.groupby("time")[list(WEATHER_VARIABLES)].mean()


def weekly(hourly):
    """Weekly weather (weeks ending on Sunday, as in Magasinstatistikk): totals for precipitation, rain and
    snowfall, means for the other variables. Weeks with missing hours are left out."""
    weeks = hourly.resample("W-SUN")
    rules = {column: "sum" if column in SUM_VARIABLES else "mean" for column in hourly.columns}
    return weeks.agg(rules)[weeks.size() == 7 * 24]


@st.cache_data(ttl=86400, show_spinner="Computing the weather of all areas...")
def weather_by_area(variable, start, end):
    """One value per area for the map: mean weekly total (precipitation, rain, snowfall) or mean value (the other
    variables) between `start` and `end`. The average is computed in MongoDB, so only 8 numbers are transferred."""
    hours_per_week = 7 * 24 if variable in SUM_VARIABLES else 1   # mean per hour -> mean weekly total
    pipeline = [
        {"$match": {"time": {"$gte": pd.Timestamp(start).to_pydatetime(),
                             "$lt": (pd.Timestamp(end) + pd.Timedelta(days=1)).to_pydatetime()}}},
        {"$group": {"_id": "$area", "value": {"$avg": f"${variable}"}}},
    ]
    result = pd.DataFrame(list(get_collection("weather_hourly").aggregate(pipeline)))
    result = result.rename(columns={"_id": "area"})
    result["value"] = (result["value"] * hours_per_week).round(2)
    return result.sort_values("area").reset_index(drop=True)
