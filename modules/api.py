"""Module to download the NVE reservoir statistics (Magasinstatistikk) with Streamlit caching."""
import pandas as pd
import requests
import streamlit as st

NVE_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOffentligData"

# Same translation as in the Jupyter Notebook
COLUMNS = {
    "dato_Id": "date", "omrType": "area_type", "omrnr": "area_number",
    "iso_aar": "year", "iso_uke": "week", "fyllingsgrad": "filling_rate",
    "kapasitet_TWh": "capacity_twh", "fylling_TWh": "filling_twh",
    "neste_Publiseringsdato": "next_publish_date",
    "fyllingsgrad_forrige_uke": "filling_rate_last_week",
    "endring_fyllingsgrad": "filling_rate_change",
}

METRICS = {
    "filling_rate": "Filling rate (share of capacity)",
    "filling_twh": "Stored energy (TWh)",
    "capacity_twh": "Capacity (TWh)",
    "filling_rate_last_week": "Filling rate last week",
    "filling_rate_change": "Weekly change in filling rate",
}

AREA_TYPES = {"EL": "Price areas (EL)", "NO": "Whole country (NO)", "VASS": "River basins (VASS)"}

FIRST_MONTH = "1995-01"


def available_months():
    """All months from the start of the NVE series until today, as 'YYYY-MM' strings."""
    return pd.period_range(FIRST_MONTH, pd.Timestamp.now(), freq="M").strftime("%Y-%m").tolist()


def area_label(area_type, area_number):
    """Readable area names, as used by NVE (NO1-NO5, VASS1-VASS3, Norway)."""
    if area_type == "NO":
        return "Norway"
    if area_type == "EL":
        return f"NO{area_number}"
    return f"VASS{area_number}"

# st.cache_data stores the result for each interval of months; show_spinner is the message shown while loading
@st.cache_data(ttl=3600, show_spinner="Downloading reservoir statistics from NVE...")
def download_reservoirs(start_month, end_month):
    """Download the NVE reservoir statistics for the chosen interval of months ('YYYY-MM').

    The public NVE endpoint has no date parameters, so the interval is applied right after the
    download. Each interval is cached separately: moving the slider triggers a new download.
    """
    response = requests.get(NVE_URL, timeout=60)
    response.raise_for_status()
    df = pd.DataFrame(response.json()).rename(columns=COLUMNS)
    df["date"] = pd.to_datetime(df["date"])
    start = pd.Timestamp(start_month)                        # first day of the first month
    end = pd.Timestamp(end_month) + pd.offsets.MonthEnd(0)   # last day of the last month
    df = df[df["date"].between(start, end)].copy()
    df["area"] = [area_label(t, n) for t, n in zip(df["area_type"], df["area_number"])]
    return df.sort_values(["area_type", "area_number", "date"]).reset_index(drop=True)
 

AREAS_URL = "https://biapi.nve.no/magasinstatistikk/api/Magasinstatistikk/HentOmr%C3%A5der"  # "å" URL-encoded


@st.cache_data(ttl=86400, show_spinner="Downloading the list of areas from NVE...")
def download_areas():
    """Areas described by the NVE API (HentOmråder): whole country, price areas and river basins."""
    response = requests.get(AREAS_URL, timeout=60)
    response.raise_for_status()
    groups = response.json()[0]  # {"land": [...], "elspot": [...], "vassdrag": [...]}
    areas = pd.concat([pd.DataFrame(group) for group in groups.values()], ignore_index=True)
    return areas.rename(columns={"omrType": "area_type", "omrnr": "area_number", "navn": "name",
                                 "navn_langt": "long_name", "beskrivelse": "description"})