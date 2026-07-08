from pathlib import Path
from typing import Optional

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Mapa interactivo de estaciones climáticas de México",
    layout="wide",
    initial_sidebar_state="expanded",
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Fuentes"
SOURCE_DIRS = [
    DATA_DIR,
    BASE_DIR / "assets",
    BASE_DIR,
]
MONTH_ORDER = [
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
]
STATION_ORDER = [
    "Mérida, Yucatán",
    "Chetumal, Quintana Roo",
    "Villahermosa, Tabasco",
    "Mexicali, Baja California",
    "Guadalajara, Jalisco",
]
STATION_REFERENCE = {
    "Mérida, Yucatán": {
        "station_id": 31097,
        "lat": 20.98416667,
        "lon": -89.65805556,
        "climate_type": "Cálido subhúmedo",
    },
    "Chetumal, Quintana Roo": {
        "station_id": 23032,
        "lat": 18.50055556,
        "lon": -88.3275,
        "climate_type": "Cálido húmedo / Caribe",
    },
    "Villahermosa, Tabasco": {
        "station_id": 27054,
        "lat": 17.99666667,
        "lon": -92.92833333,
        "climate_type": "Cálido húmedo",
    },
    "Mexicali, Baja California": {
        "station_id": 2034,
        "lat": 32.55,
        "lon": -115.4666667,
        "climate_type": "Árido",
    },
    "Guadalajara, Jalisco": {
        "station_id": 14066,
        "lat": 20.67638889,
        "lon": -103.3461111,
        "climate_type": "Templado / semicálido subhúmedo",
    },
}
COLORS = {
    "paper": "#f4eddc",
    "card": "#fff9ee",
    "sand": "#efe3c6",
    "brown": "#b79247",
    "ocher": "#c59f4a",
    "soft_yellow": "#ece94b",
    "warm_yellow": "#f3c04b",
    "orange": "#ff8b4b",
    "green": "#9ec44d",
    "sky": "#58c5e8",
    "blue": "#4a89e8",
    "deep_blue": "#5570a6",
    "text": "#3a3225",
    "muted": "#6f6554",
}


def find_first_existing_path(candidates: list[str]) -> Optional[Path]:
    for candidate in candidates:
        for root in SOURCE_DIRS:
            path = root / candidate
            if path.exists():
                return path
    return None


@st.cache_data(show_spinner=False)
def load_dataset() -> tuple[pd.DataFrame, Path]:
    dataset_path = find_first_existing_path(
        ["dataset_mapa_clima_demo_2015_2024.csv", "dataset_mapa_clima_demo_2015_2024.xlsx"]
    )
    if dataset_path is None:
        raise FileNotFoundError("No se encontró el dataset principal dentro del proyecto.")

    if dataset_path.suffix.lower() == ".xlsx":
        df = pd.read_excel(dataset_path)
    else:
        df = pd.read_csv(dataset_path, encoding="utf-8-sig")

    numeric_cols = [
        "station_id",
        "lat",
        "lon",
        "altitude_m",
        "year",
        "month",
        "precipitation_mm",
        "tmax_c",
        "tmin_c",
        "tmean_c",
    ]
    for column in numeric_cols:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")

    df["date_month"] = pd.to_datetime(df["date_month"], errors="coerce")
    df["month_name"] = pd.Categorical(df["month_name"], categories=MONTH_ORDER, ordered=True)
    return df, dataset_path


@st.cache_data(show_spinner=False)
def load_stations(dataset: pd.DataFrame) -> tuple[pd.DataFrame, Optional[Path]]:
    stations_path = find_first_existing_path(["estaciones_demo_clima_2015_2024.csv"])
    if stations_path is not None:
        stations = pd.read_csv(stations_path, encoding="utf-8-sig")
    else:
        columns = [
            "station_id",
            "station_display_name",
            "station_name",
            "state",
            "municipality",
            "status",
            "lat",
            "lon",
            "altitude_m",
            "climate_type",
            "marker_group",
        ]
        stations = (
            dataset[columns]
            .drop_duplicates(subset=["station_display_name"])
            .assign(period_demo="2015-2024")
        )
        stations_path = None

    for column in ("lat", "lon", "altitude_m"):
        if column in stations.columns:
            stations[column] = pd.to_numeric(stations[column], errors="coerce")
    return stations, stations_path


def station_options(dataset: pd.DataFrame) -> list[str]:
    available = dataset["station_display_name"].dropna().unique().tolist()
    ordered = [name for name in STATION_ORDER if name in available]
    extras = sorted(name for name in available if name not in ordered)
    return ordered + extras


@st.cache_data(show_spinner=False)
def load_reference_image_path() -> Optional[Path]:
    return find_first_existing_path(["image.jpeg", "image.jpg", "image.png"])


def build_annual_summary(station_df: pd.DataFrame) -> pd.DataFrame:
    return (
        station_df.groupby("year", as_index=False)
        .agg(
            precipitation_total_mm=("precipitation_mm", "sum"),
            tmax_avg_c=("tmax_c", "mean"),
            tmin_avg_c=("tmin_c", "mean"),
        )
        .sort_values("year")
    )


def style_chart(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        paper_bgcolor=COLORS["card"],
        plot_bgcolor=COLORS["card"],
        font={"family": "Trebuchet MS, Gill Sans, sans-serif", "color": COLORS["text"]},
        margin={"l": 20, "r": 20, "t": 70, "b": 30},
        hoverlabel={"bgcolor": "#fffdf6", "font_color": COLORS["text"]},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
    )
    fig.update_xaxes(showgrid=False, linecolor="#d8cdb9")
    fig.update_yaxes(gridcolor="#e8deca", zeroline=False, linecolor="#d8cdb9")
    return fig


def build_monthly_precip_chart(year_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        [
            go.Scatter(
                x=year_df["month_name"],
                y=year_df["precipitation_mm"],
                mode="lines+markers",
                line={"color": COLORS["blue"], "width": 3},
                marker={"size": 9, "color": COLORS["sky"], "line": {"width": 1, "color": "#ffffff"}},
                fill="tozeroy",
                fillcolor="rgba(95, 199, 223, 0.18)",
                name="Precipitación",
            )
        ]
    )
    fig.update_layout(title="Precipitación mensual del año seleccionado", yaxis_title="mm")
    return style_chart(fig)


def build_monthly_temperature_chart(year_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        [
            go.Scatter(
                x=year_df["month_name"],
                y=year_df["tmax_c"],
                mode="lines+markers",
                line={"color": COLORS["orange"], "width": 3},
                marker={"size": 8},
                name="Temp. máxima",
            ),
            go.Scatter(
                x=year_df["month_name"],
                y=year_df["tmin_c"],
                mode="lines+markers",
                line={"color": COLORS["sky"], "width": 3},
                marker={"size": 8},
                name="Temp. mínima",
            ),
        ]
    )
    fig.update_layout(title="Temperatura máxima y mínima mensual", yaxis_title="°C")
    return style_chart(fig)


def build_annual_precip_chart(annual_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        [
            go.Bar(
                x=annual_df["year"],
                y=annual_df["precipitation_total_mm"],
                marker={
                    "color": annual_df["precipitation_total_mm"],
                    "colorscale": [[0, COLORS["ocher"]], [0.5, COLORS["warm_yellow"]], [1, COLORS["orange"]]],
                    "line": {"color": "#ffffff", "width": 1},
                },
                name="Precipitación anual",
            )
        ]
    )
    fig.update_layout(title="Precipitación anual 2015–2024", yaxis_title="mm")
    return style_chart(fig)


def build_annual_temperature_chart(annual_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        [
            go.Scatter(
                x=annual_df["year"],
                y=annual_df["tmax_avg_c"],
                mode="lines+markers",
                line={"color": COLORS["orange"], "width": 3},
                marker={"size": 9},
                name="Temp. máxima promedio",
            ),
            go.Scatter(
                x=annual_df["year"],
                y=annual_df["tmin_avg_c"],
                mode="lines+markers",
                line={"color": COLORS["sky"], "width": 3},
                marker={"size": 9},
                name="Temp. mínima promedio",
            ),
        ]
    )
    fig.update_layout(title="Temperatura promedio anual 2015–2024", yaxis_title="°C")
    return style_chart(fig)


def station_card(station_row: pd.Series) -> str:
    return f"""
    <div class="info-card">
        <div class="section-label">Ficha de la estación</div>
        <h3>{station_row['station_display_name']}</h3>
        <p><strong>Estado:</strong> {station_row['state'].title()}</p>
        <p><strong>Municipio:</strong> {station_row['municipality'].title()}</p>
        <p><strong>Tipo de clima:</strong> {station_row['climate_type']}</p>
        <p><strong>Coordenadas:</strong> {station_row['lat']:.4f}, {station_row['lon']:.4f}</p>
        <p><strong>Altitud:</strong> {station_row['altitude_m']:.0f} m</p>
        <p><strong>Periodo:</strong> 2015–2024</p>
    </div>
    """


def popup_html(station_row: pd.Series) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif; min-width:240px; color:{COLORS['text']};">
        <div style="font-size:16px; font-weight:700; margin-bottom:8px; color:{COLORS['brown']};">{station_row['station_display_name']}</div>
        <div style="margin-bottom:4px;"><strong>Estado:</strong> {station_row['state'].title()}</div>
        <div style="margin-bottom:4px;"><strong>Clave:</strong> {int(station_row['station_id'])}</div>
        <div style="margin-bottom:4px;"><strong>Clima:</strong> {station_row['climate_type']}</div>
        <div><strong>Coordenadas:</strong> {station_row['lat']:.4f}, {station_row['lon']:.4f}</div>
    </div>
    """


def enrich_stations(stations: pd.DataFrame) -> pd.DataFrame:
    enriched = stations.copy()
    for station_name, values in STATION_REFERENCE.items():
        mask = enriched["station_display_name"] == station_name
        if mask.any():
            for key, value in values.items():
                enriched.loc[mask, key] = value
    enriched["station_id"] = pd.to_numeric(enriched["station_id"], errors="coerce")
    enriched["lat"] = pd.to_numeric(enriched["lat"], errors="coerce")
    enriched["lon"] = pd.to_numeric(enriched["lon"], errors="coerce")
    return enriched


def build_station_map(stations: pd.DataFrame, selected_station: str) -> folium.Map:
    selected_row = stations.loc[stations["station_display_name"] == selected_station].iloc[0]
    fmap = folium.Map(
        location=[float(selected_row["lat"]), float(selected_row["lon"])],
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=True,
        prefer_canvas=True,
    )

    mexico_bounds = [[14.0, -118.5], [33.8, -86.0]]
    fmap.fit_bounds(mexico_bounds)

    for _, row in stations.iterrows():
        is_selected = row["station_display_name"] == selected_station
        radius = 16 if is_selected else 12
        color = COLORS["orange"] if is_selected else COLORS["blue"]
        weight = 5 if is_selected else 3

        tooltip_text = row["station_display_name"]
        popup = folium.Popup(popup_html(row), max_width=320)
        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=radius,
            color="#ffffff",
            weight=weight,
            fill=True,
            fill_color=color,
            fill_opacity=0.95,
            tooltip=tooltip_text,
            popup=popup,
        ).add_to(fmap)

    return fmap


def climate_legend_html() -> str:
    items = [
        ("Muy árido", COLORS["ocher"]),
        ("Árido", "#f6ef93"),
        ("Semiárido", COLORS["soft_yellow"]),
        ("Semicálido", COLORS["warm_yellow"]),
        ("Cálido", COLORS["orange"]),
        ("Templado", COLORS["green"]),
        ("Semifrío", COLORS["sky"]),
        ("Frío", COLORS["deep_blue"]),
    ]
    swatches = "".join(
        f'<div class="legend-item"><span class="legend-swatch" style="background:{color};"></span><span>{label}</span></div>'
        for label, color in items
    )
    return f"""
    <div class="climate-legend">
        <div class="section-label">Referencia cromática</div>
        <div class="legend-grid">{swatches}</div>
    </div>
    """


st.markdown(
    f"""
    <style>
        .stApp {{
            background:
                radial-gradient(circle at top left, rgba(197,159,74,0.16), transparent 22%),
                radial-gradient(circle at top right, rgba(88,197,232,0.16), transparent 24%),
                linear-gradient(180deg, #f8f3e6 0%, {COLORS["paper"]} 100%);
            color: {COLORS["text"]};
        }}
        .block-container {{
            max-width: 1600px;
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }}
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #ebddb9 0%, #f7f1e2 100%);
            border-right: 1px solid rgba(155,106,47,0.14);
        }}
        h1, h2, h3 {{
            font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
            color: {COLORS["text"]};
        }}
        .map-shell {{
            background: rgba(255, 250, 240, 0.92);
            border: 1px solid rgba(155,106,47,0.10);
            border-radius: 1.2rem;
            padding: 1rem;
            box-shadow: 0 14px 28px rgba(114, 92, 54, 0.08);
            margin-bottom: 1rem;
        }}
        .map-helper {{
            color: {COLORS["muted"]};
            font-size: 0.96rem;
            margin: 0 0 0.8rem 0.1rem;
        }}
        .info-card {{
            background: linear-gradient(180deg, #fffaf0 0%, #f8efdc 100%);
            border: 1px solid rgba(155,106,47,0.14);
            border-radius: 1rem;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 12px 20px rgba(114, 92, 54, 0.08);
            min-height: 250px;
        }}
        .info-card p {{
            margin-bottom: 0.45rem;
        }}
        .section-label {{
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: {COLORS["brown"]};
            font-size: 0.74rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .climate-legend {{
            background: linear-gradient(180deg, #fffaf0 0%, #f8efdc 100%);
            border: 1px solid rgba(155,106,47,0.14);
            border-radius: 1rem;
            padding: 1rem 1.05rem;
            box-shadow: 0 12px 20px rgba(114, 92, 54, 0.08);
            margin-top: 1rem;
        }}
        .legend-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.55rem 0.9rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 0.55rem;
            color: {COLORS["text"]};
            font-size: 0.94rem;
        }}
        .legend-swatch {{
            width: 18px;
            height: 18px;
            border-radius: 0.3rem;
            border: 1px solid rgba(58,50,37,0.14);
            flex: 0 0 18px;
        }}
        .reference-card {{
            background: linear-gradient(180deg, #fffaf0 0%, #f8efdc 100%);
            border: 1px solid rgba(155,106,47,0.14);
            border-radius: 1rem;
            padding: 1rem 1.05rem;
            box-shadow: 0 12px 20px rgba(114, 92, 54, 0.08);
            margin-top: 1rem;
        }}
        div[data-testid="metric-container"] {{
            background: rgba(255, 250, 240, 0.92);
            border: 1px solid rgba(155,106,47,0.10);
            border-radius: 0.95rem;
            padding: 0.65rem 0.9rem;
            box-shadow: 0 8px 18px rgba(114, 92, 54, 0.06);
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


try:
    dataset, dataset_path = load_dataset()
    stations, stations_path = load_stations(dataset)
except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

stations = enrich_stations(stations)
reference_image_path = load_reference_image_path()

options = station_options(dataset)
years = sorted(dataset["year"].dropna().astype(int).unique().tolist())

if "selected_station" not in st.session_state or st.session_state["selected_station"] not in options:
    st.session_state["selected_station"] = options[0]
if "selected_year" not in st.session_state or st.session_state["selected_year"] not in years:
    st.session_state["selected_year"] = years[-1]

selected_station = st.session_state["selected_station"]

st.markdown("# Mapa interactivo de estaciones climáticas de México")

st.markdown('<div class="map-shell">', unsafe_allow_html=True)
st.markdown(
    '<div class="map-helper">Haz clic en un marcador para ver la información de la estación. La estación seleccionada se resalta en naranja.</div>',
    unsafe_allow_html=True,
)
map_result = st_folium(
    build_station_map(stations, selected_station),
    width=None,
    height=720,
    returned_objects=["last_object_clicked_tooltip"],
    key="mapa_estaciones",
)
st.markdown("</div>", unsafe_allow_html=True)

clicked_station = map_result.get("last_object_clicked_tooltip") if isinstance(map_result, dict) else None
if clicked_station and clicked_station in options and clicked_station != st.session_state["selected_station"]:
    st.session_state["selected_station"] = clicked_station
    st.rerun()

with st.sidebar:
    st.markdown("## Filtros")
    st.selectbox("Estación climatológica", options, key="selected_station")
    st.select_slider("Año", options=years, key="selected_year")
    st.markdown(climate_legend_html(), unsafe_allow_html=True)

station_df = dataset[dataset["station_display_name"] == st.session_state["selected_station"]].copy()
station_df = station_df.sort_values(["year", "month"])
year_df = station_df[station_df["year"] == st.session_state["selected_year"]].sort_values("month")
annual_df = build_annual_summary(station_df)
station_row = stations.loc[stations["station_display_name"] == st.session_state["selected_station"]].iloc[0]
annual_metrics = annual_df[annual_df["year"] == st.session_state["selected_year"]].iloc[0]

info_col, metrics_col = st.columns([0.95, 1.45], gap="large")
with info_col:
    st.markdown(station_card(station_row), unsafe_allow_html=True)
    if reference_image_path is not None:
        st.markdown('<div class="reference-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Mapa climático de referencia</div>', unsafe_allow_html=True)
        st.image(str(reference_image_path), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with metrics_col:
    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("Precipitación total anual", f"{annual_metrics['precipitation_total_mm']:.1f} mm")
    metric_col_2.metric("Temp. máxima promedio anual", f"{annual_metrics['tmax_avg_c']:.1f} °C")
    metric_col_3.metric("Temp. mínima promedio anual", f"{annual_metrics['tmin_avg_c']:.1f} °C")

chart_col_1, chart_col_2 = st.columns(2, gap="large")
with chart_col_1:
    st.plotly_chart(
        build_monthly_precip_chart(year_df),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )
with chart_col_2:
    st.plotly_chart(
        build_monthly_temperature_chart(year_df),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )

chart_col_3, chart_col_4 = st.columns(2, gap="large")
with chart_col_3:
    st.plotly_chart(
        build_annual_precip_chart(annual_df),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )
with chart_col_4:
    st.plotly_chart(
        build_annual_temperature_chart(annual_df),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )
