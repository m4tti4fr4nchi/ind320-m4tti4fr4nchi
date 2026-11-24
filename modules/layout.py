"""Module with the header shared by all pages: title with icon, badges with the active area and period, text."""
import streamlit as st

from .session import period_days, selected_area


def page_header(title, icon, description, show_area=True, show_period=False):
    """Same header on every page, so the user always sees which area and period the page shows.

    The badges are Streamlit Markdown (":blue-badge[...]"); the area and period come from st.session_state.
    """
    st.set_page_config(page_title=title, page_icon=icon, layout="wide")
    st.title(f"{icon} {title}")
    badges = []
    if show_area:
        badges.append(f":blue-badge[📍 {selected_area()[1]}]")
    if show_period:
        start, end = period_days()
        badges.append(f":orange-badge[🗓️ {start:%d %b %Y} – {end:%d %b %Y}]")
    if badges:
        st.markdown(" ".join(badges))
    st.write(description)
