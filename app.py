import streamlit as st

# st.navigation defines the menu in the sidebar: the order of the pages and the name shown for each one.
# This replaces the automatic menu built from the file names, so the first page can be called "Home".
pages = [
    st.Page("Home.py", title="Home", icon="🏠", default=True),
    st.Page("pages/2_Reservoirs.py", title="Reservoirs"),
    st.Page("pages/3_Areas.py", title="Areas"),
    st.Page("pages/4_Cross_border_flows.py", title="Cross-border flows"),
    st.Page("pages/5_Extra.py", title="Extra"),
]
st.navigation(pages).run()