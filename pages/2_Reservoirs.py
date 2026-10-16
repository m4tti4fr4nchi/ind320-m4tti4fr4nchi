import streamlit as st

from modules.api import AREA_TYPES, METRICS, download_reservoirs
from modules.session import reservoir_controls

ALL_COLUMNS = "all"

# Wide layout: use the whole browser width, so that all area columns of the table fit
st.set_page_config(layout="wide")
st.title("Reservoirs")
st.write("Weekly reservoir statistics from the NVE API. Choose the type of area and the months to download; "
         "both tabs below use the same selection.")

# Radio buttons (area type) and selection slider (months to download), see modules/session.py
area_type, (start_month, end_month) = reservoir_controls()

# Download only the chosen months (cached with st.cache_data, see modules/api.py)
df = download_reservoirs(start_month, end_month)
df_type = df[df["area_type"] == area_type]

if df_type.empty:
    st.warning("No data available for this selection.")
    st.stop()  # stop the script here instead of drawing empty charts

# st.tabs creates tabs on the same page; everything inside "with <tab>:" is drawn in that tab
overview, trends = st.tabs(["Overview", "Trends"])

with overview:
    # As in part 1: one row per data column. New in part 2: one line chart per area number.
    # LineChartColumn draws a list of numbers as a small line chart inside a table cell
    areas = df_type["area"].unique().tolist()
    rows = []
    for metric, label in METRICS.items():
        row = {"Column": label}
        for area, group in df_type.groupby("area", sort=False):
            row[area] = group[metric].tolist()
        rows.append(row)

    st.subheader(f"{AREA_TYPES[area_type]}, {start_month} to {end_month}")
    st.dataframe(
        rows,
        column_config={area: st.column_config.LineChartColumn(area) for area in areas},
        hide_index=True,
        width="stretch",
    )
    # st.caption writes a small grey note
    st.caption("Each mini chart is scaled to its own minimum and maximum. Stored energy equals filling rate × capacity, "
               "capacity is constant, and last week's filling rate is the same series shifted by one week: "
               "this is why several rows have the same shape.")

    # st.expander hides the raw data until the user opens it
    with st.expander("Downloaded data"):
        st.dataframe(df_type, hide_index=True, width="stretch")

with trends:
    # Drop-down menu (st.selectbox) with any single column or all columns, as in part 1;
    # format_func changes only the text shown, the returned value is the column name
    choice = st.selectbox("Column", [ALL_COLUMNS] + list(METRICS),
                          format_func=lambda c: "All columns" if c == ALL_COLUMNS else METRICS[c])

    # The columns have different scales, so "All columns" shows one chart per column instead of one shared axis
    metrics = list(METRICS) if choice == ALL_COLUMNS else [choice]
    for metric in metrics:
        # Wide format: one column (= one line) per area number; st.line_chart draws one line per column
        chart_data = df_type.pivot(index="date", columns="area", values=metric)
        st.subheader(f"{METRICS[metric]} - {AREA_TYPES[area_type]}, {start_month} to {end_month}")
        st.line_chart(chart_data, x_label="Date", y_label=METRICS[metric],
                      height=250 if len(metrics) > 1 else 450)