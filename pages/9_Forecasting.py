import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.forecast import CURRENCIES, error_quantiles, forecast_filling, weekly_dataset
from modules.theme import ACCENT, BACKGROUND, GREY, PRIMARY, TEXT
from modules.session import selected_area, selected_period
from modules.weather import WEATHER_VARIABLES
from modules.layout import page_header

EXOG_OPTIONS = {**WEATHER_VARIABLES, **CURRENCIES}
ACTUAL_COLOUR, FORECAST_COLOUR = GREY, ACCENT   # modules/theme.py
BAND_FILL = "rgba(244, 162, 97, 0.2)"


@st.cache_data(show_spinner="Training SNARIMAX and computing the forecast...")
def run_forecast(area, train_end, horizon, history_weeks, exog, order, seasonal_order, learning_rate, band):
    """Forecast and (optionally) the 90 % band, cached for each combination of the inputs."""
    data = weekly_dataset(area)
    settings = dict(history_weeks=history_weeks, exog=exog, order=order, seasonal_order=seasonal_order,
                    learning_rate=learning_rate)
    result = forecast_filling(data, train_end, horizon=horizon, **settings)
    if band:
        quantiles = error_quantiles(data, train_end, horizon, **settings)
        if quantiles is not None:
            result["lower"] = (result["forecast"] + quantiles[0.05].to_numpy()).clip(0, 1)
            result["upper"] = (result["forecast"] + quantiles[0.95].to_numpy()).clip(0, 1)
    return data, result


page_header("Forecasting", "🔮",
            "Weekly forecast of the reservoir filling of the chosen area with River's SNARIMAX, the streaming "
            "version of SARIMAX (see the notebook of part 4). The default settings are the best ones found in the "
            "notebook: SNARIMAX(1,1,1)(1,1,0,52) with precipitation as exogenous variable.", show_period=True)

_, area = selected_area()
_, period_end = selected_period()
data = weekly_dataset(area)
latest_week = data["filling_rate"].dropna().index.max()

# --- Training end: synchronised with the period of the Map page, or the latest published week ---
mode = st.radio("Training data until", ["map", "latest"], horizontal=True,
                format_func={"map": f"End of the period on the Map page ({period_end:%d %b %Y})",
                             "latest": f"Latest NVE week ({latest_week:%d %b %Y}): forecast the real future"}.get)
train_end = period_end if mode == "map" else latest_week

c1, c2, c3 = st.container(border=True).columns([1, 1, 2])
horizon = c1.slider("Horizon (weeks)", 1, 52, 12)
history_weeks = c2.slider("Training history (weeks)", 104, 1600, 1000, step=52,
                          help="Counted back from the end of the training data. With exogenous variables the "
                               "history starts in 2021 at the earliest, when the weather data start.")
exog = c3.multiselect("Exogenous variables", list(EXOG_OPTIONS), default=["precipitation"] if mode == "map" else [],
                      format_func=EXOG_OPTIONS.get, disabled=mode == "latest",
                      help="Their values must be known for the forecast weeks. The weather data end in 2025, "
                           "so the real future is forecast without exogenous variables.")

with st.expander("Model parameters"):
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    order = (m1.number_input("p", 0, 4, 1), m2.number_input("d", 0, 2, 1), m3.number_input("q", 0, 4, 1))
    seasonal_order = (m4.number_input("P", 0, 2, 1), m5.number_input("D", 0, 1, 1), m6.number_input("Q", 0, 2, 0),
                      52)
    learning_rate = m7.select_slider("Learning rate", [0.001, 0.003, 0.01, 0.03], value=0.01)
    st.caption("(p, d, q): autoregressive lags, differencing and moving-average lags of the weekly series; "
               "(P, D, Q): the same for the seasonal part with a period of 52 weeks.")
band = st.toggle("Show the 90 % confidence band", value=True,
                 help="Quantiles (5 % and 95 %) of the errors of the same model forecasting from 20 earlier "
                      "origins: the band widens with the horizon, as the errors do. It is wide for forecasts "
                      "over spring and summer, because the timing of the snow melt is hard to predict.")

# --- Forecast (cached), with clear messages instead of errors when the inputs do not fit ---
try:
    data, result = run_forecast(area, train_end, horizon, history_weeks, tuple(exog), tuple(order),
                                seasonal_order, learning_rate, band)
except ValueError as error:
    st.warning(f"{error} Try a shorter horizon, an earlier period on the Map page or fewer exogenous variables.")
    st.stop()

# --- Plotly animation: the forecast is drawn one week at a time ---
history = data.loc[:train_end, "filling_rate"].iloc[-104:] * 100          # last two years before the forecast
actual_after = result["actual"].dropna() * 100
forecast = result["forecast"] * 100
has_band = "lower" in result


def frame_traces(k):
    """Traces of the forecast and band for the first k weeks (the history and actual values never change)."""
    traces = [go.Scatter(x=forecast.index[:k], y=forecast.iloc[:k])]
    if has_band:
        x = list(result.index[:k]) + list(result.index[:k][::-1])
        y = list(result["upper"].iloc[:k] * 100) + list(result["lower"].iloc[:k][::-1] * 100)
        traces.append(go.Scatter(x=x, y=y))
    return traces


fig = go.Figure()
fig.add_trace(go.Scatter(x=history.index, y=history, name="Filling (training data)",
                         line=dict(color=ACTUAL_COLOUR, width=2)))
fig.add_trace(go.Scatter(x=actual_after.index, y=actual_after, name="Filling (actual, not used for training)",
                         line=dict(color=ACTUAL_COLOUR, width=2, dash="dot")))
# The page opens with the complete forecast; Play redraws it from the first week
complete = frame_traces(horizon)
fig.add_trace(go.Scatter(x=complete[0].x, y=complete[0].y, name="Forecast (SNARIMAX)",
                         mode="lines+markers", line=dict(color=FORECAST_COLOUR, width=3), marker=dict(size=5)))
if has_band:
    fig.add_trace(go.Scatter(x=complete[1].x, y=complete[1].y, name="90 % confidence band", fill="toself",
                             fillcolor=BAND_FILL, line=dict(width=0), hoverinfo="skip"))
animated = [2, 3] if has_band else [2]          # indices of the traces that change in the frames
fig.frames = [go.Frame(data=frame_traces(k), traces=animated, name=str(k)) for k in range(1, horizon + 1)]
fig.add_vline(x=train_end, line=dict(color="grey", dash="dash", width=1))

y_values = pd.concat([history, actual_after, forecast] + ([result[["lower", "upper"]].stack() * 100] if has_band else []))
fig.update_layout(
    height=580, margin=dict(t=60, b=130), hovermode="x unified", legend=dict(orientation="h", y=1.12),
    yaxis=dict(title="Filling rate (%)", range=[max(0, y_values.min() - 5), min(100, y_values.max() + 5)]),
    xaxis=dict(title="Week", range=[history.index[0], forecast.index[-1] + pd.Timedelta(weeks=2)]),
    updatemenus=[dict(type="buttons", x=0, y=-0.16, xanchor="left", yanchor="top", direction="left", showactive=False,
                      bgcolor=BACKGROUND, bordercolor=PRIMARY, font=dict(color=TEXT), buttons=[
        dict(label="▶ Play", method="animate",
             args=[None, dict(frame=dict(duration=150, redraw=False), transition=dict(duration=0),
                              fromcurrent=False, mode="immediate")]),
        dict(label="⏸ Pause", method="animate",
             args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate")]),
    ])],
    sliders=[dict(x=0.22, len=0.78, y=-0.12, yanchor="top", active=horizon - 1,
                  currentvalue=dict(prefix="Weeks ahead: ", xanchor="right", font=dict(color=TEXT)),
                  bgcolor=BACKGROUND, activebgcolor=PRIMARY, font=dict(color=TEXT),
                  steps=[dict(label=str(k), method="animate",
                              args=[[str(k)], dict(frame=dict(duration=0, redraw=False), mode="immediate")])
                         for k in range(1, horizon + 1)])],
)
st.plotly_chart(fig, width="stretch")
st.caption("Press ▶ Play to see the forecast week by week; the slider jumps to a given week ahead.")

# --- Numbers: error on the weeks that are already known, and the table of forecast values ---
known = result.dropna(subset=["actual"])
c1, c2, c3 = st.columns(3)
c1.metric("Forecast in the last week", f"{forecast.iloc[-1]:.1f} %",
          delta=f"{forecast.iloc[-1] - history.iloc[-1]:+.1f} points vs. the last training week", border=True)
if len(known):
    c2.metric(f"Mean absolute error ({len(known)} known weeks)",
              f"{(known['forecast'] - known['actual']).abs().mean() * 100:.1f} points", border=True)
else:
    c2.metric("Mean absolute error", "–", help="The forecast weeks are in the future: no actual values yet.", border=True)
c3.metric("Training", f"{min(history_weeks, len(data.loc[:train_end].dropna(subset=['filling_rate'] + exog)))} weeks",
          delta="exogenous: " + (", ".join(exog) if exog else "none"), delta_color="off", border=True)

with st.expander("Forecast values"):
    table = (result * 100).round(1).rename(columns={"forecast": "Forecast (%)", "actual": "Actual (%)",
                                                    "lower": "Lower 5 % (%)", "upper": "Upper 95 % (%)"})
    st.dataframe(table, width="stretch")
