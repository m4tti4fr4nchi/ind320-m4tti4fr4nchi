import streamlit as st

from modules.api import available_months, download_reservoirs

st.title("Extra: Regional Dashboard")
st.write("A cross-sectional comparison of the Norwegian areas for the most recent date available.")

# Only the latest week is needed here, so the last twelve months are enough
months = available_months()
df = download_reservoirs(months[-12], months[-1])

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
        area_name = row.area
        current_rate = row.filling_rate * 100
        change = row.filling_rate_change * 100
        st.metric(label=area_name, value=f"{current_rate:.1f}%", delta=f"{change:.2f}%")

