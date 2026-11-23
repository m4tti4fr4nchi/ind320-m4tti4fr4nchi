import streamlit as st

from modules.api import AREA_TYPES, available_months, download_areas, download_reservoirs
from modules.session import selected_area

st.set_page_config(layout="wide")
st.title("Areas")
st.write("The areas of Norway in the NVE reservoir statistics: the latest filling rate of every area of the type "
         "chosen in the sidebar, and the description of all the areas covered by the API.")

# The latest twelve months are enough for the snapshot and to check which areas have data
months = available_months()
latest = download_reservoirs(months[-12], months[-1])
latest_date = latest["date"].max()

# --- Snapshot (the "Extra" page of part 1): latest filling rate and weekly change of each area ---
area_type, area = selected_area()
st.subheader(f"Latest week: {latest_date:%d %B %Y}")
snapshot = latest[(latest["date"] == latest_date) & (latest["area_type"] == area_type)].sort_values("area_number")
columns = st.columns(max(len(snapshot), 1))
for column, row in zip(columns, snapshot.itertuples()):
    # The area chosen in the sidebar (or on the map) is marked with the pin
    column.metric(("📍 " if row.area == area else "") + row.area, f"{row.filling_rate * 100:.1f} %",
                  delta=f"{row.filling_rate_change * 100:+.2f} points in a week")
st.caption(f"Areas shown: {AREA_TYPES[area_type]} (change the type of area in the sidebar).")
st.divider()

# --- Areas described by the NVE API (HentOmråder), as in the notebook of part 1 ---
areas = download_areas()
with_data = set(zip(latest["area_type"], latest["area_number"]))
areas["has_data"] = [(t, n) in with_data for t, n in zip(areas["area_type"], areas["area_number"])]

for kind, label in AREA_TYPES.items():
    st.subheader(label)
    st.dataframe(
        areas[areas["area_type"] == kind][["name", "long_name", "description", "has_data"]],
        column_config={
            "name": "Area", "long_name": "Name", "description": "Description",
            "has_data": st.column_config.CheckboxColumn("Has data"),
        },
        hide_index=True,
        width="stretch",
    )
st.caption("VASS4 (Northern Norway) is described by the API but has no data in the reservoir statistics.")
