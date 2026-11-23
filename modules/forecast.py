"""Module with the weekly forecast of the reservoir filling (River SNARIMAX), as in the notebook of part 4."""
import io

import numpy as np
import pandas as pd
import requests
import streamlit as st
from river import linear_model, optim, preprocessing, time_series

from .api import FIRST_MONTH, available_months, download_reservoirs
from .weather import FIRST_DAY, LAST_DAY, load_weather, weekly

NB_URL = "https://data.norges-bank.no/api/data/EXR/B.{currencies}.NOK.SP"
CURRENCIES = {"EUR": "EUR exchange rate (NOK)", "USD": "USD exchange rate (NOK)"}


@st.cache_data(ttl=86400, show_spinner="Downloading exchange rates from Norges Bank...")
def download_exchange_rates(start_date, end_date, currencies=("EUR", "USD")):
    """Daily exchange rates (NOK per unit of currency) from Norges Bank, as in the notebook."""
    params = {"format": "csv", "startPeriod": start_date, "endPeriod": end_date, "locale": "en"}
    response = requests.get(NB_URL.format(currencies="+".join(currencies)), params=params, timeout=60)
    response.raise_for_status()
    raw = pd.read_csv(io.StringIO(response.text), sep=";")
    rates = raw.pivot(index="TIME_PERIOD", columns="BASE_CUR", values="OBS_VALUE").rename_axis(columns=None)
    rates.index = pd.to_datetime(rates.index)
    return rates[list(currencies)]


@st.cache_data(ttl=3600, show_spinner="Preparing the weekly data...")
def weekly_dataset(area):
    """Weekly table of one area (weeks ending on Sunday): filling from NVE (from 1995), weather from MongoDB
    (2021-2025) and exchange rates from Norges Bank (forward-filled over weekends and holidays)."""
    reservoirs = download_reservoirs(FIRST_MONTH, available_months()[-1])
    filling = reservoirs[reservoirs["area"] == area].set_index("date")[["filling_rate"]].sort_index()
    weather = weekly(load_weather(area, FIRST_DAY, LAST_DAY))
    try:
        rates = download_exchange_rates(f"{filling.index.min():%Y-%m-%d}", f"{filling.index.max():%Y-%m-%d}")
        rates = rates.asfreq("D").ffill().resample("W-SUN").mean()
    except requests.RequestException:
        rates = pd.DataFrame(columns=list(CURRENCIES))   # the forecast still works without the currencies
    return filling.join(weather).join(rates)


def forecast_filling(data, train_end, horizon=12, history_weeks=1000, exog=(), order=(1, 1, 1),
                     seasonal_order=(1, 1, 0, 52), target="filling_rate", learning_rate=0.01):
    """Forecast of the weekly filling with River's SNARIMAX (same function as in the notebook).

    Returns a DataFrame with the forecast and, where available, the actual values.
    """
    exog = list(exog)
    available = data[[target] + exog].dropna()
    train = available[available.index <= train_end].iloc[-history_weeks:]
    if len(train) < 2 * seasonal_order[3] * max(1, seasonal_order[1]):
        raise ValueError("The training history is too short for the seasonal part of the model.")
    dates = pd.date_range(train.index[-1], periods=horizon + 1, freq="W-SUN")[1:]
    if exog:
        future = data[exog].reindex(dates)
        if future.isna().any().any():
            raise ValueError("The exogenous variables are not known for all the forecast weeks.")
        xs = future.to_dict("records")
    else:
        xs = [{}] * horizon

    p, d, q = order
    sp, sd, sq, m = seasonal_order
    regressor = (preprocessing.StandardScaler() |
                 linear_model.LinearRegression(optimizer=optim.SGD(learning_rate), intercept_lr=0.1))
    model = time_series.SNARIMAX(p=p, d=d, q=q, m=m, sp=sp, sd=sd, sq=sq, regressor=regressor)
    for _, row in train.iterrows():
        model.learn_one(row[target], {column: row[column] for column in exog})

    result = pd.DataFrame({"forecast": model.forecast(horizon=horizon, xs=xs)}, index=dates)
    result["actual"] = data[target].reindex(dates)
    return result


def error_quantiles(data, train_end, horizon, quantiles=(0.05, 0.95), n_origins=20, step=4, **settings):
    """Empirical quantiles of the forecast error for each week of the horizon.

    The same model is used to forecast from `n_origins` earlier origins (every `step` weeks before `train_end`,
    so only data known at `train_end` is used); the quantiles of the errors at each step of the horizon give a
    confidence band that widens with the horizon. Returns None if there are too few earlier origins.
    """
    errors = []
    for k in range(1, n_origins + 1):
        origin = pd.Timestamp(train_end) - pd.Timedelta(weeks=step * k + horizon)   # forecast ends before train_end
        try:
            past = forecast_filling(data, origin, horizon=horizon, **settings)
        except ValueError:
            break   # not enough history (or no exogenous values) further back
        errors.append((past["actual"] - past["forecast"]).to_numpy())
    if len(errors) < 5:
        return None
    errors = np.array(errors)
    return pd.DataFrame({q: np.nanquantile(errors, q, axis=0) for q in quantiles})
