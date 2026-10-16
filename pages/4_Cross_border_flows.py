import calendar

import plotly.express as px
import streamlit as st

from modules.db import get_hourly_flows, get_options, get_yearly_totals

st.set_page_config(layout="wide")
st.title("Cross-border Flows")
st.write("Physical electricity flows between Norway and its neighbours, read from MongoDB.")

# Connections and years found in MongoDB fill the controls (no hard-coded lists)
connections, years = get_options()
MONTHS = {number: calendar.month_abbr[number] for number in range(1, 13)}  # 1 -> "Jan", ...
COLOURS = {"import": "#1f77b4", "export": "#ff7f0e"}  # same colours as in the notebook
LABELS = {"import": "Import to Norway", "export": "Export from Norway"}
CONNECTION_COLOURS = dict(zip(connections, px.colors.qualitative.Plotly))  # same colour whatever is selected

# st.columns splits the page in two; everything inside "with left:" / "with right:" goes in that column
left, right = st.columns(2)

# Left: one connection and one year -> pie chart of energy in and out of Norway (as in the notebook)
with left:
    connection = st.radio("Connection", connections, horizontal=True)
    # Year selection with a different control (drop-down menu); 2025 is the only complete year
    year = st.selectbox("Year", years, index=years.index(2025) if 2025 in years else 0)

    totals = get_yearly_totals(connection, year)
    totals["energy_gwh"] = totals["energy_mwh"] / 1000   # hourly MW summed over a year = MWh
    totals["label"] = totals["direction"].map(LABELS)

    # Plotly charts are interactive (values on hover); st.plotly_chart shows them in the page
    fig = px.pie(totals, names="label", values="energy_gwh", color="direction",
                 color_discrete_map=COLOURS, title=f"{connection}, {year}")
    fig.update_traces(texttemplate="%{percent:.1%}<br>%{value:,.0f} GWh", sort=False)
    st.plotly_chart(fig, width="stretch")

    # 2024 and 2026 are only partly in the two-year window: say so under the chart
    hours = int(totals["hours"].max())
    hours_in_year = 8784 if calendar.isleap(year) else 8760
    if hours < hours_in_year:
        st.caption(f"Partial year: {hours:,} of {hours_in_year:,} hours are in the database.")

# Right: any set of months of the same year -> one line per connection and direction (as in the notebook)
with right:
    # st.pills shows the months as buttons; with selection_mode="multi" it returns a list, e.g. [1, 2]
    months = st.pills("Months", list(MONTHS), format_func=MONTHS.get, selection_mode="multi", default=[1])
        # st.multiselect lets the user choose the connections to draw (none selected by default)
    shown = st.multiselect("Connections to show", connections, default=[])

    if not months:
        st.info("Select at least one month.")
    elif not shown:
        st.info("Choose one or more connections to draw the hourly flows.")
    else:
        # A tuple (not a list) is passed, because the arguments of a cached function must be hashable
        flows = get_hourly_flows(year, tuple(sorted(months)))
        if flows.empty:
            st.info(f"No data for the selected months of {year}.")
        else:
            # Filter after loading: the cached MongoDB query stays the same when only the connections change
            flows = flows[flows["connection"].isin(shown)].sort_values(["connection", "direction", "timestamp"])
            fig = px.line(flows, x="timestamp", y="quantity_mw", color="connection", line_dash="direction",
                          color_discrete_map=CONNECTION_COLOURS,
                          labels={"timestamp": "Time (UTC)", "quantity_mw": "Hourly flow (MW)",
                                  "connection": "Connection", "direction": "Direction"},
                          title=f"Hourly flows, {', '.join(MONTHS[m] for m in sorted(months))} {year}",
                          render_mode="webgl")  # WebGL draws many points (several months of hours) faster
            fig.update_traces(line_width=1)
            st.plotly_chart(fig, width="stretch")

# Below the columns: short documentation of the data source, hidden until opened
with st.expander("Data source"):
    st.markdown(
        "- **Source:** [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/), "
        "*Cross-Border Physical Flows* (document type A11), retrieved with the ENTSO-E REST API.\n"
        "- **Coverage:** the last two years for the six connections of Norway "
        "(Sweden, Denmark, Finland, Germany, the Netherlands, Great Britain), in both directions.\n"
        "- **Processing (Jupyter Notebook):** 15-minute values averaged to hourly values, so that one row is "
        "the energy in MWh for that hour; times in UTC; one missing hour filled by linear interpolation.\n"
        "- **Pipeline:** API → Cassandra (written with Spark) → extracted with Spark → MongoDB → this page."
    )