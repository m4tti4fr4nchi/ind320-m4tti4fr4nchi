"""Colours shared by all the charts, so that every page follows the dark theme of .streamlit/config.toml."""

PRIMARY = "#4cc9f0"      # primaryColor of the theme: reservoirs, selected items, main lines
ACCENT = "#f4a261"       # weather and forecasts
GREY = "#9aa0a6"         # reference lines, boundaries, actual values
ALERT = "#e66767"        # outliers and anomalies
BACKGROUND = "#1f2937"   # buttons drawn inside Plotly charts
TEXT = "#e5e7eb"         # textColor of the theme

# Categorical colours, in the same order as chartCategoricalColors in .streamlit/config.toml
CATEGORICAL = ["#4cc9f0", "#f4a261", "#90be6d", "#e66767", "#b392f0", "#f9c74f", "#43aa8b", "#9aa0a6"]
