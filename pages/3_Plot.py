import streamlit as st
import pandas as pd

@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("data/reservoirs.csv")
    translation_dict = {
        'dato_Id': 'date', 'omrType': 'area_type', 'omrnr': 'area_number',
        'iso_aar': 'year', 'iso_uke': 'week', 'fyllingsgrad': 'filling_rate',
        'kapasitet_TWh': 'capacity_twh', 'fylling_TWh': 'filling_twh',
        'neste_Publiseringsdato': 'next_publish_date',
        'fyllingsgrad_forrige_uke': 'filling_rate_last_week',
        'endring_fyllingsgrad': 'filling_rate_change'
    }
    df = df.rename(columns=translation_dict)
    df['date'] = pd.to_datetime(df['date'])
    return df

st.title("Interactive Reservoir Trends")
st.write("Explore the historical data. Select specific metrics below and interact with the chart to zoom in on specific years.")

df = load_and_clean_data()

numeric_columns = ['filling_rate', 'capacity_twh', 'filling_twh', 'filling_rate_last_week', 'filling_rate_change']

# Aggregate data by date to create a clean national average (just like we did in Jupyter)
df_national = df.groupby('date')[numeric_columns].mean()

# I create an interactive multi-select box for the user
selected_metrics = st.multiselect("Select one or more metrics to plot:", options=numeric_columns,
)

min_date = df["date"].min()
max_date = df["date"].max()

start_date, end_date = st.slider(
    "Select a date range to zoom in on the chart:",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    format="MM-YYYY"
)

df_window = df[(df["date"] >= pd.Timestamp(start_date)) & (df["date"] <= pd.Timestamp(end_date))].copy()
df_national = df_window.groupby("date")[numeric_columns].mean()

if selected_metrics:
    st.line_chart(df_national[selected_metrics])
else:
    st.warning("Please select at least one metric from the dropdown menu above and a date range.") 
    # now i create a line chart based on the selected metrics. If no metrics are selected, I display a warning message.