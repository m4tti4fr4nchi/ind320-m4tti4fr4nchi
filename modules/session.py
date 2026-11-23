"""Module with the controls shared by the pages: the global area, the global period and the local months slider."""
import pandas as pd
import streamlit as st

from .api import AREA_TYPES, available_months
from .weather import FIRST_DAY, LAST_DAY

# Areas of each type, with the same names as the "area" column of the NVE data (see area_label in api.py)
AREAS_BY_TYPE = {
    "EL": ["NO1", "NO2", "NO3", "NO4", "NO5"],
    "NO": ["Norway"],
    "VASS": ["VASS1", "VASS2", "VASS3"],
}

# Weeks ending on Sunday (as in Magasinstatistikk) inside the period with weather data
WEEKS = pd.date_range(FIRST_DAY, LAST_DAY, freq="W-SUN")
DEFAULT_PERIOD = (pd.Timestamp("2024-01-07"), pd.Timestamp("2024-12-29"))   # the last complete year with weather


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
    st.session_state.setdefault("period", DEFAULT_PERIOD)

    with st.sidebar:
        # st.popover is a button that opens a small panel; its label always shows the active area
        with st.popover(f"📍 Area: {st.session_state['area']}", width="stretch"):
            area_type = st.radio("Type of area", list(AREA_TYPES), format_func=AREA_TYPES.get,
                                 key="area_type", on_change=_reset_area)
            st.selectbox("Area", AREAS_BY_TYPE[area_type], key="area")
        start, end = period_days()
        st.caption(f"🗓️ Period: {start:%d %b %Y} – {end:%d %b %Y} (chosen on the Map page)")


def selected_area():
    """Type of area and area chosen in the global selector (read by the pages)."""
    # Defaults in case a page runs before the selector has been drawn (e.g. when a page URL is opened directly)
    st.session_state.setdefault("area_type", "EL")
    st.session_state.setdefault("area", "NO1")
    return st.session_state["area_type"], st.session_state["area"]


def select_area(area):
    """Make `area` the global area (used when an area is clicked on the map). Must be called from a callback."""
    st.session_state["area_type"] = "VASS" if area.startswith("VASS") else "EL"
    st.session_state["area"] = area


def selected_period():
    """First and last week (Sundays) of the global period."""
    st.session_state.setdefault("period", DEFAULT_PERIOD)
    return st.session_state["period"]


def period_days():
    """First and last day of the global period: from the Monday of the first week to the last Sunday."""
    first_week, last_week = selected_period()
    return first_week - pd.Timedelta(days=6), last_week


def _store_period():
    # Copy the slider value to a key that is not tied to a widget: Streamlit deletes the state of a widget when
    # the user opens a page without it, but "period" must survive the change of page
    st.session_state["period"] = st.session_state["period_slider"]


def period_slider():
    """Range slider over the weeks with weather data; the chosen period is shared by all pages."""
    return st.select_slider("Period (weeks ending on Sunday)", options=list(WEEKS), value=selected_period(),
                            format_func=lambda week: f"{week:%d %b %Y}", key="period_slider",
                            on_change=_store_period)


def months_slider():
    """Selection slider for the months to download from the NVE API (local to the Reservoirs page)."""
    months = available_months()
    # A tuple as value gives a range slider with two handles; default: the first month (January 1995), as in part 1
    start_month, end_month = st.select_slider("Months to download", options=months,
                                              value=(months[0], months[0]))
    return start_month, end_month
