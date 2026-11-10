import streamlit as st

from modules.analysis import spectrogram, stl_decomposition
from modules.api import FIRST_MONTH, available_months, download_reservoirs
from modules.session import selected_area

st.set_page_config(layout="wide")
st.title("Reservoir Analysis")
st.write("Decomposition and frequency content of the weekly filling rate of the area chosen in the sidebar, "
         "for the whole NVE series since 1995.")

# Global area (sidebar); both analyses use the complete series, so no download interval is needed here
_, area = selected_area()
df = download_reservoirs(FIRST_MONTH, available_months()[-1])
filling = (df[df["area"] == area].set_index("date")["filling_rate"]
           .asfreq("W-SUN"))   # one value per week (every NVE date is a Sunday), as STL needs a regular series
st.caption(f"Filling rate of {area}: {len(filling):,} weeks from {filling.index[0].date()} "
           f"to {filling.index[-1].date()}.")

stl_tab, spectrogram_tab = st.tabs(["STL decomposition", "Spectrogram"])

# --- STL: seasonal smoother, trend smoother and robustness as user choices (defaults as in the notebook) ---
with stl_tab:
    left, middle, right = st.columns(3)
    seasonal = left.slider("Seasonal smoother (years)", 7, 51, 13, step=2,
                           help="Odd number. Larger values give a seasonal pattern that changes less between years.")
    trend = middle.slider("Trend smoother (weeks)", 53, 261, 105, step=2,
                          help="Odd number. 105 weeks (about two years) follows wet and dry years, not the season.")
    robust = right.toggle("Robust fitting", value=True,
                          help="Down-weights unusual weeks so they do not distort the trend and the season.")
    st.plotly_chart(stl_decomposition(filling, seasonal=seasonal, trend=trend, robust=robust,
                                      label="Filling rate"), width="stretch")

# --- Spectrogram: window length and overlap as user choices ---
with spectrogram_tab:
    left, right = st.columns(2)
    window_length = left.slider("Window length (weeks)", 26, 260, 104, step=2,
                                help="104 weeks = two years, so the yearly cycle fits twice in each window.")
    overlap_share = right.slider("Window overlap (%)", 0, 90, 75, step=5)
    window_overlap = int(window_length * overlap_share / 100)   # stft needs the overlap in weeks
    st.plotly_chart(spectrogram(filling, window_length, window_overlap,
                                label=f"Filling rate of {area} (window {window_length} weeks, "
                                      f"overlap {window_overlap} weeks)"), width="stretch")
    st.caption("A bright band at 1 cycle per year is the seasonal cycle: the reservoirs are emptied in winter "
               "and refilled after the snowmelt.")

with st.expander("Data source"):
    st.markdown(
        "- **Data:** weekly filling rate from the [NVE Magasinstatistikk API]"
        "(https://biapi.nve.no/magasinstatistikk/swagger/index.html), downloaded directly by the app.\n"
        "- **Methods:** as in the notebook – STL from statsmodels, and a spectrogram computed with SciPy's "
        "short-time Fourier transform."
    )