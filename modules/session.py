"""Module with the controls of the reservoir page (area type and months to download)."""
import streamlit as st

from .api import AREA_TYPES, available_months


def reservoir_controls():
    """Radio buttons for the type of area and a selection slider for the months to download."""
    months = available_months()

    # Controls at the top of the page: area type on the left, download interval on the right
    left, right = st.columns([2, 3])
    with left:
        area_type = st.radio("Type of area", list(AREA_TYPES), format_func=AREA_TYPES.get)
    with right:
                # A tuple as value gives a range slider with two handles; default: the first month (January 1995), as in part 1
        start_month, end_month = st.select_slider("Months to download", options=months,
                                                  value=(months[0], months[0]))
    st.divider()
    return area_type, (start_month, end_month)