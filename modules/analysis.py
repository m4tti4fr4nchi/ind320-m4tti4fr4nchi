"""Module with the analyses of the notebook (SPC on DCT-filtered data, LOF, STL, spectrogram) as interactive Plotly figures."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.fft import dct, idct
from scipy.signal import stft
from scipy.stats import median_abs_deviation
from sklearn.neighbors import LocalOutlierFactor
from statsmodels.tsa.seasonal import STL

LINE_COLOUR, OUTLIER_COLOUR, BOUND_COLOUR = "#3987e5", "#e66767", "#9aa0a6"


def spc_outliers(series, cutoff=100, n_std=3.0, label=None):
    """SPC on seasonally adjusted variations (SATV), as in the notebook.

    The DCT high-pass filter removes the components below `cutoff`; outliers are hours where the SATV is more
    than `n_std` robust standard deviations (MAD) from its median. Returns the figure, the outliers and a summary.
    """
    label = label or series.name
    values = series.to_numpy()
    coefficients = dct(values, type=1, norm="forward")
    coefficients[:cutoff] = 0
    satv = idct(coefficients, type=1, norm="forward")      # seasonally adjusted variations
    seasonal = values - satv                                # slow part, used to draw the boundaries

    centre = np.median(satv)
    robust_sd = median_abs_deviation(satv, scale="normal")
    upper, lower = centre + n_std * robust_sd, centre - n_std * robust_sd
    is_outlier = (satv > upper) | (satv < lower)

    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=series.index, y=values, mode="lines", name=label,
                               line=dict(width=1, color=LINE_COLOUR)))
    for bound, name in [(upper, "Upper SPC boundary"), (lower, "Lower SPC boundary")]:
        fig.add_trace(go.Scattergl(x=series.index, y=seasonal + bound, mode="lines", name=name,
                                   line=dict(width=1, dash="dash", color=BOUND_COLOUR)))
    fig.add_trace(go.Scattergl(x=series.index[is_outlier], y=values[is_outlier], mode="markers",
                               name="Outliers", marker=dict(size=5, color=OUTLIER_COLOUR)))
    fig.update_layout(xaxis_title="Time (UTC)", yaxis_title=label, height=450,
                      legend=dict(orientation="h", y=1.08), margin=dict(t=40))

    outliers = pd.DataFrame({"value": values[is_outlier], "satv": satv[is_outlier].round(3)},
                            index=series.index[is_outlier])
    summary = {
        "outliers": int(is_outlier.sum()),
        "share": 100 * is_outlier.mean(),
        "above": int((satv > upper).sum()),
        "below": int((satv < lower).sum()),
        "robust_sd": robust_sd,
    }
    return fig, outliers, summary


def lof_anomalies(series, contamination=0.01, n_neighbors=20, days_per_unit=7.0, label=None):
    """Local Outlier Factor on the standardised value and the time position, as in the notebook.

    Returns the figure, the anomalies and a summary.
    """
    label = label or series.name
    values = series.to_numpy()
    days = (series.index - series.index[0]) / pd.Timedelta(days=1)
    features = np.column_stack([(values - values.mean()) / values.std(), days / days_per_unit])

    lof = LocalOutlierFactor(n_neighbors=n_neighbors, contamination=contamination)
    is_anomaly = lof.fit_predict(features) == -1
    lof_score = -lof.negative_outlier_factor_

    fig = go.Figure()
    fig.add_trace(go.Scattergl(x=series.index, y=values, mode="lines", name=label,
                               line=dict(width=1, color=LINE_COLOUR)))
    fig.add_trace(go.Scattergl(x=series.index[is_anomaly], y=values[is_anomaly], mode="markers",
                               name="LOF anomalies", marker=dict(size=6, color=OUTLIER_COLOUR)))
    fig.update_layout(xaxis_title="Time (UTC)", yaxis_title=label, height=450,
                      legend=dict(orientation="h", y=1.08), margin=dict(t=40))

    anomalies = pd.DataFrame({"value": values[is_anomaly], "lof_score": lof_score[is_anomaly].round(2)},
                             index=series.index[is_anomaly])
    summary = {
        "anomalies": int(is_anomaly.sum()),
        "share": 100 * is_anomaly.mean(),
        "mean_anomalies": values[is_anomaly].mean(),
        "mean_all": values.mean(),
        "threshold": lof_score[is_anomaly].min(),
    }
    return fig, anomalies, summary

    

def stl_decomposition(series, period=52, seasonal=13, trend=105, robust=True, label=None):
    """Seasonal-Trend decomposition using LOESS of a weekly series, as in the notebook.

    Returns a figure with the observed series and its trend, seasonal and residual components.
    """
    label = label or series.name
    result = STL(series, period=period, seasonal=seasonal, trend=trend, robust=robust).fit()

    parts = [("Observed", result.observed), ("Trend", result.trend),
             ("Seasonal", result.seasonal), ("Residual", result.resid)]
    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.04,
                        subplot_titles=[name for name, _ in parts])
    for row, (name, values) in enumerate(parts, start=1):
        mode = "markers" if name == "Residual" else "lines"
        fig.add_trace(go.Scatter(x=values.index, y=values, mode=mode, name=name, showlegend=False,
                                 line=dict(width=1.2, color=LINE_COLOUR), marker=dict(size=3, color=LINE_COLOUR)),
                      row=row, col=1)
    fig.update_layout(height=750, margin=dict(t=40), yaxis_title=label)
    return fig


def spectrogram(series, window_length=104, window_overlap=78, label=None):
    """Spectrogram (short-time Fourier transform) of a weekly series, as in the notebook.

    Returns a heatmap with time (window centres) on the x-axis and frequency in cycles per year on the y-axis.
    """
    label = label or series.name
    values = series.to_numpy() - series.mean()   # remove the mean, otherwise frequency 0 dominates
    freqs, times, Z = stft(values, fs=1, nperseg=window_length, noverlap=window_overlap)
    window_centres = series.index[0] + pd.to_timedelta(times * 7, unit="D")
    cycles_per_year = freqs * 365.25 / 7

    keep = cycles_per_year <= 6   # the interesting part: up to 6 cycles per year
    fig = go.Figure(go.Heatmap(x=window_centres, y=cycles_per_year[keep], z=np.abs(Z)[keep],
                               colorscale="Viridis", zsmooth="best", colorbar=dict(title="Amplitude")))
    fig.update_layout(height=450, margin=dict(t=40), xaxis_title="Time (window centre)",
                      yaxis_title="Frequency (cycles per year)", title=label)
    return fig