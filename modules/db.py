"""Module to read the data that the Jupyter Notebooks stored in MongoDB (cross-border flows, sampled locations)."""
import pandas as pd
import pymongo
import streamlit as st

# st.cache_resource keeps one shared object (here the database connection) for all users and reruns
@st.cache_resource
def get_client():
    """One MongoDB connection for the whole app (the URI is read from the Streamlit secrets)."""
    return pymongo.MongoClient(st.secrets["mongo"]["uri"])


def get_collection(name="cross_border_flows"):
    """A collection of the ind320 database: the ENTSO-E flows by default, or e.g. "sample_points"."""
    return get_client()["ind320"][name]

# st.cache_data stores the returned data; ttl=3600 refreshes it after one hour
@st.cache_data(ttl=3600)
def get_options():
    """Connections and years available in the database, used to fill the controls."""
    collection = get_collection()
    return sorted(collection.distinct("connection")), sorted(collection.distinct("year"))


@st.cache_data(ttl=3600)
def get_yearly_totals(connection, year):
    """Total energy in and out of Norway for one connection and one year (aggregated in MongoDB)."""
    pipeline = [
        {"$match": {"connection": connection, "year": year}},
        {"$group": {"_id": "$direction", "energy_mwh": {"$sum": "$quantity_mw"}, "hours": {"$sum": 1}}},
    ]
    totals = pd.DataFrame(list(get_collection().aggregate(pipeline)))
    return totals.rename(columns={"_id": "direction"})


@st.cache_data(ttl=3600, show_spinner="Loading hourly flows from MongoDB...")
def get_hourly_flows(year, months):
    """Hourly flows of all connections and directions for the chosen months of one year."""
    query = {"year": year, "month": {"$in": list(months)}}
    projection = {"_id": 0, "connection": 1, "direction": 1, "timestamp": 1, "quantity_mw": 1}
    return pd.DataFrame(list(get_collection().find(query, projection)))