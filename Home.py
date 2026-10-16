import streamlit as st

# Page settings for the home page (each file in pages/ sets its own, e.g. the wide layout)
st.set_page_config(page_title="IND320 Energy App", page_icon="💧")

st.title("Norwegian Reservoirs and Cross-border Flows")
st.write("Project work for IND320. Use the menu in the sidebar to move between the pages.")

# Short guide to the pages (st.markdown renders Markdown text, including tables)
st.markdown("""
| Page | Content | Data source |
|---|---|---|
| **Reservoirs** | Two tabs: one row per data column with a line chart for each area, and the weekly trends with one line per area | NVE Magasinstatistikk API |
| **Areas** | The areas of Norway covered by the NVE statistics | NVE Magasinstatistikk API |
| **Cross-border flows** | Yearly import/export per connection and hourly flows for any months | ENTSO-E, stored in MongoDB |
| **Extra** | Latest filling rate of every area | NVE Magasinstatistikk API |
""")

st.caption("The reservoir data are downloaded directly from the NVE API when a page needs them. "
           "The cross-border flows were downloaded from ENTSO-E in the Jupyter Notebook, processed with "
           "Cassandra and Spark, and stored in MongoDB, which this app reads.")