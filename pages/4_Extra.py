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

st.title("Extra: Regional Dashboard")
st.write("A cross-sectional comparison of the 5 Norwegian price areas for the most recent date available.")

df = load_and_clean_data()

#I took the latest date from the dataset and displayed it as a subheader to indicate the snapshot status of the data being presented.
latest_date = df['date'].max()
st.subheader(f"Snapshot status for: {latest_date.strftime('%Y-%m-%d')}")

#Extract all available area types and create a dropdown menu for the user
available_types = df['area_type'].unique()
selected_type = st.selectbox(
    "Select Geographical Grouping:", 
    options=available_types, 
    index=list(available_types).index('EL') 
)

#From the user selection, I filter the dataframe to show only the latest date and the selected area type. I then sort the data by area number to ensure a consistent display order.
latest_data = df[(df['date'] == latest_date) & (df['area_type'] == selected_type)].copy()
latest_data = latest_data.sort_values('area_number')

#I created a 5-column layout to display the metrics for each area side by side, with the filing rate and the change from the previous week. I use a loop to iterate through the rows of the filtered dataframe and display each metric in its respective column.
cols = st.columns(5)
for i, row in enumerate(latest_data.itertuples()):
    with cols[i % 5]:
        area_name = f"Area {row.area_number}"
        current_rate = row.filling_rate * 100
        change = row.filling_rate_change * 100
        st.metric(label=area_name, value=f"{current_rate:.1f}%", delta=f"{change:.2f}%")

