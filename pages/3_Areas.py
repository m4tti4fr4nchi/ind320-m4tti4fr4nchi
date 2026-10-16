import streamlit as st

from modules.api import AREA_TYPES, available_months, download_areas, download_reservoirs

st.set_page_config(layout="wide")
st.title("Areas")
st.write("The areas of Norway described by the NVE API, grouped by type. "
         "These are the options of the radio buttons on the Reservoirs page.")

# Same information as the notebook section "Identify the areas of Norway covered by the API"
areas = download_areas()

# Mark the areas that actually have data in the statistics (the latest twelve months are enough to check)
months = available_months()
latest = download_reservoirs(months[-12], months[-1])
with_data = set(zip(latest["area_type"], latest["area_number"]))
areas["has_data"] = [(t, n) in with_data for t, n in zip(areas["area_type"], areas["area_number"])]

# One table per type of area; column_config renames the columns and shows True/False as checkboxes
for area_type, label in AREA_TYPES.items():
    st.subheader(label)
    st.dataframe(
        areas[areas["area_type"] == area_type][["name", "long_name", "description", "has_data"]],
        column_config={
            "name": "Area", "long_name": "Name", "description": "Description",
            "has_data": st.column_config.CheckboxColumn("Has data"),
        },
        hide_index=True,
        width="stretch",
    )

st.caption("VASS4 (Northern Norway) is described by the API but has no data in the reservoir statistics.")