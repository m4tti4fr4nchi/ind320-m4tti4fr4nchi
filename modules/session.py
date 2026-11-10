"""Module with the controls of the app: the global area selector and the local months slider."""
import streamlit as st

from .api import AREA_TYPES, available_months

# Areas of each type, with the same names as the "area" column of the NVE data (see area_label in api.py)
AREAS_BY_TYPE = {
    "EL": ["NO1", "NO2", "NO3", "NO4", "NO5"],
    "NO": ["Norway"],
    "VASS": ["VASS1", "VASS2", "VASS3"],
}

def _reset_area():
    # When the type of area changes, start from the first area of the new type
    st.session_state["area"] = AREAS_BY_TYPE[st.session_state["area_type"]][0]


def area_selector():
    """Global area selector, drawn in the sidebar by app.py as a compact popover button.

    Widgets created in the entry point (app.py) before page.run() are part of every page,
    so the chosen type of area and area stay the same when the user changes page.
    """
    # Defaults the first time the app is opened
    st.session_state.setdefault("area_type", "EL")
    st.session_state.setdefault("area", "NO1")

    with st.sidebar:
        # st.popover is a button that opens a small panel; its label always shows the active area
        with st.popover(f"📍 Area: {st.session_state['area']}", width="stretch"):
            area_type = st.radio("Type of area", list(AREA_TYPES), format_func=AREA_TYPES.get,
                                 key="area_type", on_change=_reset_area)
            st.selectbox("Area", AREAS_BY_TYPE[area_type], key="area")

def selected_area():
    """Type of area and area chosen in the global selector (read by the pages)."""
    # Defaults in case a page runs before the selector has been drawn (e.g. when a page URL is opened directly)
    st.session_state.setdefault("area_type", "EL")
    st.session_state.setdefault("area", "NO1")
    return st.session_state["area_type"], st.session_state["area"]


def months_slider():
    """Selection slider for the months to download from the NVE API (local to the Reservoirs page)."""
    months = available_months()
    # A tuple as value gives a range slider with two handles; default: the first month (January 1995), as in part 1
    start_month, end_month = st.select_slider("Months to download", options=months,
                                              value=(months[0], months[0]))
    return start_month, end_month