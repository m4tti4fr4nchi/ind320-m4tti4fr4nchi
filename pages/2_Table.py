import streamlit as st
import pandas as pd

@st.cache_data
def load_and_clean_data():
    # Read the local CSV file
    df = pd.read_csv(r"C:\Users\matti\Desktop\ind320-m4tti4fr4nchi\data\reservoirs.csv")
    
    # Rename columns using the same dictionary from the Jupyter Notebook
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

st.title("Imported Data Overview")

df = load_and_clean_data()

# Isolate the first month of the data series based on the earliest dates available
first_month_df = df[df['date'] < '1995-02-01']

# I did not want to include categorical text columns in the chart, so I filtered for purely numerical columns
numeric_columns = ["filling_rate", "capacity_twh", "filling_twh", "filling_rate_last_week", "filling_rate_change"] 
    # i tried to filter the columns to only include the numeric ones, but it was not working properly, so I manually selected the numeric columns instead.

# Restructure the data: each original column becomes a row containing a list of its values
table_data = {
    "Metric Name": numeric_columns,
    "First Month Trend": [first_month_df[col].tolist() for col in numeric_columns]
}
df_chart = pd.DataFrame(table_data)

# Render the dataframe configuring the trend column to display as an inline sparkline chart
st.dataframe(
    df_chart,
    column_config={
        "First Month Trend": st.column_config.LineChartColumn(
            "First Month Trend (Jan 1995)"
        )
    },
    hide_index=True,
    use_container_width=True
)