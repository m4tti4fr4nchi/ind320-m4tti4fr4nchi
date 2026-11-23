import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from modules.api import FIRST_MONTH, available_months, download_reservoirs
from modules.theme import ACCENT, GREY, PRIMARY, TEXT
from modules.session import period_days, selected_area
from modules.weather import FIRST_DAY, LAST_DAY, WEATHER_VARIABLES, load_weather, weekly

# Magasinstatistikk variables that make sense to compare with the weather
RESERVOIR_VARIABLES = {
    "filling_rate_change": "Weekly change in filling rate",
    "filling_rate": "Filling rate",
    "filling_twh": "Stored energy (TWh)",
}
WEATHER_COLOUR, RESERVOIR_COLOUR, CORRELATION_COLOUR = ACCENT, PRIMARY, TEXT   # modules/theme.py

st.set_page_config(layout="wide")
st.title("Sliding Window Correlation")
st.write("Correlation between a weather variable and a reservoir variable of the area chosen in the sidebar, "
         "computed in a window that slides over the weekly series (2021–2025). A lag shifts the weather forward, "
         "to compare the reservoirs with the weather of some weeks before. The period chosen on the Map page is "
         "shaded.")

_, area = selected_area()
start, end = period_days()

# --- Controls ---
c1, c2, c3, c4 = st.columns(4)
weather_variable = c1.selectbox("Weather variable", list(WEATHER_VARIABLES), format_func=WEATHER_VARIABLES.get,
                                index=list(WEATHER_VARIABLES).index("precipitation"))
reservoir_variable = c2.selectbox("Reservoir variable", list(RESERVOIR_VARIABLES),
                                  format_func=RESERVOIR_VARIABLES.get)
window = c3.slider("Window (weeks)", 5, 53, 13, step=2,
                   help="Odd number, so the window is centred on each week. 13 weeks = about one season.")
lag = c4.slider("Lag of the weather (weeks)", -12, 12, 0,
                help="Positive: the reservoir value of a week is compared with the weather of `lag` weeks before.")

# --- Weekly data: NVE (weeks ending on Sunday) and the weather of the area aggregated to the same weeks ---
reservoirs = download_reservoirs(FIRST_MONTH, available_months()[-1])
reservoir = (reservoirs[reservoirs["area"] == area].set_index("date")[reservoir_variable]
             .loc[FIRST_DAY:LAST_DAY])
if reservoir_variable != "filling_twh":
    reservoir = reservoir * 100   # shares -> percent
weather = weekly(load_weather(area, FIRST_DAY, LAST_DAY))[weather_variable]

# Same weekly index for both series; the lag moves the weather `lag` weeks forward in time
data = pd.DataFrame({"reservoir": reservoir, "weather": weather.shift(lag)}).dropna()
if len(data) < window:
    st.warning("Not enough weeks with data for this window.")
    st.stop()
correlation = data["reservoir"].rolling(window, center=True).corr(data["weather"])

# --- Figure: the two series (two y-axes) and the sliding window correlation below ---
fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.06, row_heights=[0.55, 0.45],
                    specs=[[{"secondary_y": True}], [{}]])
fig.add_trace(go.Scatter(x=data.index, y=data["weather"], name=WEATHER_VARIABLES[weather_variable]
                         + (f" ({lag:+d} weeks)" if lag else ""), line=dict(color=WEATHER_COLOUR, width=1.3)),
              row=1, col=1)
fig.add_trace(go.Scatter(x=data.index, y=data["reservoir"], name=RESERVOIR_VARIABLES[reservoir_variable],
                         line=dict(color=RESERVOIR_COLOUR, width=1.6)), row=1, col=1, secondary_y=True)
fig.add_trace(go.Scatter(x=correlation.index, y=correlation, name=f"Correlation ({window}-week window)",
                         line=dict(color=CORRELATION_COLOUR, width=1.6)), row=2, col=1)
fig.add_hline(y=0, line=dict(color="grey", dash="dot", width=1), row=2, col=1)
for row in (1, 2):
    fig.add_vrect(x0=start, x1=end, fillcolor=RESERVOIR_COLOUR, opacity=0.08, line_width=0, row=row, col=1)
fig.update_yaxes(title_text=WEATHER_VARIABLES[weather_variable], row=1, col=1, secondary_y=False)
fig.update_yaxes(title_text=RESERVOIR_VARIABLES[reservoir_variable], row=1, col=1, secondary_y=True)
fig.update_yaxes(title_text="Correlation", range=[-1, 1], row=2, col=1)
fig.update_layout(height=620, hovermode="x unified", legend=dict(orientation="h", y=1.08), margin=dict(t=40))
st.plotly_chart(fig, width="stretch")

# --- Summary: whole series, chosen period, and the correlation for every lag ---
in_period = correlation.loc[start:end]
m1, m2, m3 = st.columns(3)
m1.metric("Correlation, all weeks", f"{data['reservoir'].corr(data['weather']):.2f}")
m2.metric("Mean sliding correlation in the period", f"{in_period.mean():.2f}" if in_period.notna().any() else "–")
seasonal = correlation.groupby(correlation.index.month).mean()   # mean sliding correlation per calendar month
month_name = lambda month: pd.Timestamp(2000, month, 1).strftime("%b")
m3.metric("Strongest / weakest month (mean)", f"{month_name(seasonal.idxmax())} / {month_name(seasonal.idxmin())}")

left, right = st.columns(2)
with left:
    # Correlation of the whole series for every lag: shows how long the weather takes to reach the reservoirs
    lags = range(-12, 13)
    lag_corr = [reservoir.corr(weather.shift(k)) for k in lags]
    bars = go.Figure(go.Bar(x=list(lags), y=lag_corr, marker_color=[RESERVOIR_COLOUR if k == lag else GREY
                                                                     for k in lags]))
    bars.update_layout(title="Correlation of all weeks for each lag", xaxis_title="Lag of the weather (weeks)",
                       yaxis_title="Correlation", yaxis_range=[-1, 1], height=330, margin=dict(t=40))
    st.plotly_chart(bars, width="stretch")
with right:
    # Mean sliding correlation per month: the relationship changes with the season
    months = go.Figure(go.Bar(x=[month_name(month) for month in seasonal.index], y=seasonal,
                              marker_color=RESERVOIR_COLOUR))
    months.update_layout(title="Mean sliding correlation per month", yaxis_title="Correlation",
                         yaxis_range=[-1, 1], height=330, margin=dict(t=40))
    st.plotly_chart(months, width="stretch")

with st.expander("How to read this page"):
    st.markdown(
        "- The correlation is computed with `rolling(window, center=True).corr(...)` from pandas, as in the "
        "course book: for each week, the Pearson correlation of the two series in the surrounding window.\n"
        "- **Weekly change in filling rate vs. precipitation:** strong in autumn and winter (rain fills the "
        "reservoirs within the same week), weak in spring and early summer, when the inflow comes from the "
        "melting snow of the previous winter and not from the rain of the same week.\n"
        "- **Weekly change vs. temperature:** strong in spring (warm weeks melt the snow) and in late autumn, "
        "and close to zero or negative in summer.\n"
        "- **Filling rate vs. temperature:** the correlation grows with the lag and is largest after about "
        "10–12 weeks, the delay between the yearly temperature cycle and the filling of the reservoirs."
    )
