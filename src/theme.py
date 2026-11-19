"""Institutional visual tokens used across the Streamlit application."""

CICY_BLUE = "#005680"
CICY_GREEN = "#7B8323"

UI_COLORS = {
    "background": "#F7F9F9",
    "surface": "#FFFFFF",
    "surface_muted": "#F0F4F5",
    "border": "#D8E1E4",
    "text": "#222222",
    "muted": "#5D676B",
    "blue": CICY_BLUE,
    "blue_soft": "#E7F1F5",
    "green": CICY_GREEN,
    "green_soft": "#F0F2E5",
    "success_bg": "#E8F6EA",
    "success_text": "#2F7D42",
    "error_bg": "#FDE9E4",
    "error_text": "#A24C34",
}

# These colors encode climate and water-series meaning. Keep them independent
# from the institutional palette so presentation changes do not alter science.
SCIENCE_COLORS = {
    "ocher": "#C59F4A",
    "soft_yellow": "#ECE94B",
    "warm_yellow": "#F3C04B",
    "orange": "#FF8B4B",
    "green": "#7EB86D",
    "sky": "#58C5E8",
    "blue": "#4A89E8",
    "deep_blue": "#5570A6",
}

FONT_FAMILY = '"Noto Sans", "Segoe UI", sans-serif'
PLOT_FONT_FAMILY = "Noto Sans, Segoe UI, sans-serif"
