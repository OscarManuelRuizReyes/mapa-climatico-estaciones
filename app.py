import base64
import html
import io
import json
from pathlib import Path
from typing import Optional

import folium
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image, ImageOps
from streamlit.errors import StreamlitSecretNotFoundError
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Mapa interactivo de estaciones climáticas de México",
    layout="wide",
    initial_sidebar_state="expanded",
)


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "Fuentes"
QUIZ_DATA_PATH = BASE_DIR / "data" / "preguntas_reto_agua.json"
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
COLORS = {
    "paper": "#f4eddc",
    "card": "#fff9ee",
    "sand": "#efe3c6",
    "brown": "#b79247",
    "ocher": "#c59f4a",
    "soft_yellow": "#ece94b",
    "warm_yellow": "#f3c04b",
    "orange": "#ff8b4b",
    "green": "#7eb86d",
    "sky": "#58c5e8",
    "blue": "#4a89e8",
    "deep_blue": "#5570a6",
    "text": "#3a3225",
    "muted": "#6f6554",
    "success_bg": "#e8f6ea",
    "success_text": "#2f7d42",
    "error_bg": "#fde9e4",
    "error_text": "#a24c34",
}
STATION_IMAGE_FILES = {
    15062: "toluca.jpg",
    10048: "durango.jpeg",
    1008: "tepezala.jpeg",
    2034: "mexicalo.jpg",
    11070: "guanajuato.jpg",
    4024: "campeche.jpeg",
    31097: "yucatan.jpeg",
}
STATION_PLACE_DESCRIPTIONS = {
    15062: "Esta estación representa un clima frío de alta montaña. Se ubica a gran altitud, por eso las temperaturas se mantienen bajas durante buena parte del año. Es útil para mostrar que en México también existen zonas donde puede hacer mucho frío.",
    10048: "Esta estación representa un clima semifrío de sierra. La altitud ayuda a que el ambiente sea fresco durante gran parte del año, con temperaturas más bajas que en las zonas cálidas del país.",
    1008: "Esta estación representa un clima árido. En este tipo de lugar llueve poco y el paisaje suele tener vegetación adaptada a la falta de agua, como matorrales y plantas resistentes.",
    2034: "Esta estación representa un clima muy árido. Es una zona con muy poca lluvia y temperaturas muy altas en parte del año. Sirve para explicar los ambientes secos y calurosos.",
    11070: "Esta estación representa un clima semiárido. No es tan seco como un desierto, pero la lluvia es limitada y el paisaje puede tener vegetación baja, pastizales y matorrales.",
    4024: "Esta estación representa un clima cálido húmedo. Es un lugar con temperaturas altas y mucha lluvia, por lo que suele haber ríos, humedad y vegetación abundante.",
    31097: "Esta estación representa un clima cálido subhúmedo. Hace calor durante gran parte del año, pero la lluvia se concentra más en ciertos meses, por eso hay temporada de lluvias y temporada más seca.",
}
DEFAULT_GOOGLE_SHEET_ID = "1MHYx1jypG_-rCEyFyvGIO5ZvqnUSGK2bAwgl50HbJ58"
DEFAULT_GOOGLE_SHEET_PREGUNTAS_GID = "445447247"
DEFAULT_GOOGLE_SHEET_APRENDIZAJES_GID = "56937761"
DEFAULT_QUIZ_PAYLOAD = {
    "final_summary": [
        "El Sol impulsa la evaporación.",
        "El vapor se condensa y forma gotas.",
        "El agua regresa como precipitación.",
        "La infiltración ayuda a recargar los acuíferos.",
        "Muy poca lluvia puede producir sequías.",
        "Mucha lluvia en poco tiempo puede provocar inundaciones.",
    ],
    "questions": [
        {
            "id": 1,
            "iconos": "☀️ 💧",
            "pregunta": "¿Por qué el Sol ayuda al ciclo del agua?",
            "opciones": {
                "A": "Porque hace que el agua desaparezca para siempre.",
                "B": "Porque calienta el agua y favorece la evaporación.",
                "C": "Porque detiene la lluvia.",
                "D": "Porque enfría las nubes.",
            },
            "respuestas_correctas": ["B"],
            "explicacion": "El calor del Sol transforma parte del agua líquida en vapor. Ese proceso se llama evaporación.",
            "permite_multiple": False,
        },
        {
            "id": 2,
            "iconos": "☁️ ❄️",
            "pregunta": "¿Qué ocurre cuando el vapor de agua toca una superficie más fría?",
            "opciones": {
                "A": "Se convierte en gotas pequeñas.",
                "B": "Se vuelve arena.",
                "C": "Desaparece.",
                "D": "Se convierte en fuego.",
            },
            "respuestas_correctas": ["A"],
            "explicacion": "Cuando el vapor se enfría, se condensa y forma pequeñas gotas de agua.",
            "permite_multiple": False,
        },
        {
            "id": 3,
            "iconos": "🌧️ ☁️",
            "pregunta": "¿Qué pasa cuando las gotas en las nubes se hacen grandes y pesadas?",
            "opciones": {
                "A": "Suben más al cielo.",
                "B": "Se quedan quietas para siempre.",
                "C": "Caen como precipitación.",
                "D": "Se convierten en piedras.",
            },
            "respuestas_correctas": ["C"],
            "explicacion": "Cuando las gotas crecen demasiado, caen como lluvia u otra forma de precipitación.",
            "permite_multiple": False,
        },
        {
            "id": 4,
            "iconos": "🌱 💧",
            "pregunta": "¿Qué ocurre cuando parte del agua de lluvia entra al suelo?",
            "opciones": {
                "A": "Se llama infiltración.",
                "B": "Se convierte en humo.",
                "C": "Sale volando.",
                "D": "Hace que el Sol se apague.",
            },
            "respuestas_correctas": ["A"],
            "explicacion": "La infiltración ocurre cuando el agua entra al suelo y ayuda a recargar el agua subterránea.",
            "permite_multiple": False,
        },
        {
            "id": 5,
            "iconos": "☀️ 🌵",
            "pregunta": "¿Qué puede ocurrir si durante muchos meses llueve mucho menos de lo normal?",
            "opciones": {
                "A": "Una sequía.",
                "B": "Un arcoíris permanente.",
                "C": "Más nieve en la playa.",
                "D": "Que el mar desaparezca en un día.",
            },
            "respuestas_correctas": ["A"],
            "explicacion": "Cuando pasa mucho tiempo con poca lluvia, puede aparecer una sequía.",
            "permite_multiple": False,
        },
        {
            "id": 6,
            "iconos": "🌧️ 🌊",
            "pregunta": "¿Qué puede ocurrir si llueve demasiado en poco tiempo?",
            "opciones": {
                "A": "Una inundación.",
                "B": "Que todas las plantas se congelen.",
                "C": "Que desaparezcan las nubes.",
                "D": "Que el agua deje de moverse.",
            },
            "respuestas_correctas": ["A"],
            "explicacion": "La lluvia intensa en poco tiempo puede hacer que el agua se acumule y provoque inundaciones.",
            "permite_multiple": False,
        },
        {
            "id": 7,
            "iconos": "⚠️ 💧",
            "pregunta": "¿Cuáles eventos están relacionados con cambios extremos en el ciclo del agua?",
            "opciones": {
                "A": "Sequías.",
                "B": "Inundaciones.",
                "C": "Sombras de los árboles.",
                "D": "Piedras redondas.",
            },
            "respuestas_correctas": ["A", "B"],
            "explicacion": "Las sequías y las inundaciones pueden aparecer cuando cambia mucho la cantidad de lluvia en una región.",
            "permite_multiple": True,
        },
    ],
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
        "temperatura_media_anual",
        "temperatura_maxima_promedio",
        "temperatura_minima_promedio",
        "precipitacion_anual_promedio",
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

    if "date_month" in df.columns:
        df["date_month"] = pd.to_datetime(df["date_month"], errors="coerce")
    if "month_name" in df.columns:
        df["month_name"] = pd.Categorical(df["month_name"], categories=MONTH_ORDER, ordered=True)
    df["station_label"] = df.get("station_display_name", df.get("station_name")).fillna(df.get("station_name"))
    return df, dataset_path


@st.cache_data(show_spinner=False)
def load_stations(dataset: pd.DataFrame) -> tuple[pd.DataFrame, Optional[Path]]:
    stations_path = find_first_existing_path(["estaciones_demo_clima_2015_2024.csv"])
    if stations_path is not None:
        stations = pd.read_csv(stations_path, encoding="utf-8-sig")
    else:
        stations = dataset.drop_duplicates(subset=["station_label"]).copy()
        stations_path = None

    for column in (
        "lat",
        "lon",
        "altitude_m",
        "temperatura_media_anual",
        "temperatura_maxima_promedio",
        "temperatura_minima_promedio",
        "precipitacion_anual_promedio",
    ):
        if column in stations.columns:
            stations[column] = pd.to_numeric(stations[column], errors="coerce")
    stations["station_label"] = stations.get("station_display_name", stations.get("station_name")).fillna(
        stations.get("station_name")
    )
    return stations, stations_path


def normalize_quiz_payload(payload: object) -> dict:
    if not isinstance(payload, dict):
        payload = {}

    final_summary = payload.get("final_summary", DEFAULT_QUIZ_PAYLOAD["final_summary"])
    if not isinstance(final_summary, list) or not final_summary:
        final_summary = DEFAULT_QUIZ_PAYLOAD["final_summary"]

    raw_questions = payload.get("questions", DEFAULT_QUIZ_PAYLOAD["questions"])
    questions = []
    for fallback_index, raw in enumerate(raw_questions, start=1):
        if not isinstance(raw, dict):
            continue
        options = raw.get("opciones", {})
        if not isinstance(options, dict) or not options:
            options = {"A": "Opción A", "B": "Opción B"}
        normalized_options = {}
        for letter, text in options.items():
            letter_text = str(letter).strip()[:1].upper() or "A"
            normalized_options[letter_text] = str(text)

        correct_answers = raw.get("respuestas_correctas", [])
        if not isinstance(correct_answers, list):
            correct_answers = []
        correct_answers = [str(value).strip()[:1].upper() for value in correct_answers if str(value).strip()]
        valid_letters = list(normalized_options.keys())
        correct_answers = [letter for letter in correct_answers if letter in valid_letters] or [valid_letters[0]]

        questions.append(
            {
                "id": int(raw.get("id", fallback_index)),
                "iconos": str(raw.get("iconos", "💧")),
                "pregunta": str(raw.get("pregunta", "Pregunta sin texto")),
                "opciones": normalized_options,
                "respuestas_correctas": correct_answers,
                "explicacion": str(raw.get("explicacion", "")),
                "permite_multiple": bool(raw.get("permite_multiple", len(correct_answers) > 1)),
            }
        )

    questions = sorted(questions, key=lambda item: item["id"])
    return {"final_summary": [str(item) for item in final_summary], "questions": questions}


def load_quiz_payload_from_local() -> dict:
    if not QUIZ_DATA_PATH.exists():
        save_quiz_payload(DEFAULT_QUIZ_PAYLOAD)
    with QUIZ_DATA_PATH.open("r", encoding="utf-8") as file:
        return normalize_quiz_payload(json.load(file))


def save_quiz_payload(payload: dict) -> None:
    QUIZ_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with QUIZ_DATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(normalize_quiz_payload(payload), file, ensure_ascii=False, indent=2)


def parse_truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "si", "sí", "yes", "y"}


def get_google_sheet_settings() -> tuple[str, str, str]:
    try:
        sheet_id = st.secrets.get("GOOGLE_SHEET_ID", DEFAULT_GOOGLE_SHEET_ID)
        preguntas_gid = st.secrets.get("GOOGLE_SHEET_PREGUNTAS_GID", DEFAULT_GOOGLE_SHEET_PREGUNTAS_GID)
        aprendizajes_gid = st.secrets.get("GOOGLE_SHEET_APRENDIZAJES_GID", DEFAULT_GOOGLE_SHEET_APRENDIZAJES_GID)
    except StreamlitSecretNotFoundError:
        sheet_id = DEFAULT_GOOGLE_SHEET_ID
        preguntas_gid = DEFAULT_GOOGLE_SHEET_PREGUNTAS_GID
        aprendizajes_gid = DEFAULT_GOOGLE_SHEET_APRENDIZAJES_GID
    return str(sheet_id), str(preguntas_gid), str(aprendizajes_gid)


def build_google_sheet_csv_url(sheet_id: str, gid: str) -> str:
    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


@st.cache_data(ttl=60, show_spinner=False)
def load_quiz_payload_from_google_sheets(sheet_id: str, preguntas_gid: str, aprendizajes_gid: str) -> dict:
    preguntas_df = pd.read_csv(build_google_sheet_csv_url(sheet_id, preguntas_gid))
    aprendizajes_df = pd.read_csv(build_google_sheet_csv_url(sheet_id, aprendizajes_gid))

    preguntas_df = preguntas_df[preguntas_df["activa"].map(parse_truthy)].copy()
    preguntas_df["orden"] = pd.to_numeric(preguntas_df["orden"], errors="coerce")
    preguntas_df["id"] = pd.to_numeric(preguntas_df["id"], errors="coerce")
    preguntas_df = preguntas_df.sort_values(["orden", "id"], na_position="last")

    questions = []
    for fallback_index, row in enumerate(preguntas_df.to_dict(orient="records"), start=1):
        options = {
            "A": str(row.get("opcion_a", "")).strip(),
            "B": str(row.get("opcion_b", "")).strip(),
            "C": str(row.get("opcion_c", "")).strip(),
            "D": str(row.get("opcion_d", "")).strip(),
        }
        options = {letter: text for letter, text in options.items() if text and text.lower() != "nan"}
        raw_answers = str(row.get("respuestas_correctas", ""))
        correct_answers = [
            answer.strip().upper()
            for answer in raw_answers.split(",")
            if answer.strip()
        ]

        questions.append(
            {
                "id": int(row["id"]) if pd.notna(row.get("id")) else fallback_index,
                "iconos": str(row.get("iconos", "💧")),
                "pregunta": str(row.get("pregunta", "Pregunta sin texto")),
                "opciones": options or {"A": "Opción A", "B": "Opción B"},
                "respuestas_correctas": correct_answers,
                "explicacion": str(row.get("explicacion", "")),
                "permite_multiple": parse_truthy(row.get("permite_multiple", False)),
            }
        )

    aprendizajes_df = aprendizajes_df[aprendizajes_df["activo"].map(parse_truthy)].copy()
    aprendizajes_df["orden"] = pd.to_numeric(aprendizajes_df["orden"], errors="coerce")
    aprendizajes_df = aprendizajes_df.sort_values("orden", na_position="last")
    final_summary = []
    for row in aprendizajes_df.to_dict(orient="records"):
        icono = str(row.get("icono", "")).strip()
        texto = str(row.get("texto", "")).strip()
        if texto and texto.lower() != "nan":
            final_summary.append(f"{icono} {texto}".strip())

    return normalize_quiz_payload(
        {
            "final_summary": final_summary or DEFAULT_QUIZ_PAYLOAD["final_summary"],
            "questions": questions or DEFAULT_QUIZ_PAYLOAD["questions"],
        }
    )


def load_quiz_payload() -> tuple[dict, Optional[str]]:
    sheet_id, preguntas_gid, aprendizajes_gid = get_google_sheet_settings()
    try:
        return load_quiz_payload_from_google_sheets(sheet_id, preguntas_gid, aprendizajes_gid), None
    except Exception:
        return load_quiz_payload_from_local(), (
            "No se pudieron cargar las preguntas desde Google Sheets. Se usó la versión local."
        )


def station_options(dataset: pd.DataFrame) -> list[str]:
    return sorted(dataset["station_label"].dropna().unique().tolist())


def safe_climate_color(value: object) -> str:
    return value if isinstance(value, str) and value.strip() else COLORS["blue"]


@st.cache_data(show_spinner=False)
def load_station_image_uri(station_id: int) -> Optional[str]:
    image_name = STATION_IMAGE_FILES.get(int(station_id))
    if not image_name:
        return None

    image_path = BASE_DIR / "Fotos" / image_name
    if not image_path.exists():
        return None

    with Image.open(image_path) as image:
        fitted = ImageOps.fit(image.convert("RGB"), (1400, 820), method=Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        fitted.save(buffer, format="JPEG", quality=90)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


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
        template="plotly_white",
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


def build_rainfall_comparison_chart(annual_df: pd.DataFrame) -> go.Figure:
    comparison = annual_df.copy()
    average_rainfall = comparison["precipitation_total_mm"].mean()
    comparison["difference_from_average"] = comparison["precipitation_total_mm"] - average_rainfall
    comparison["classification"] = comparison["precipitation_total_mm"].apply(
        lambda value: "Más lluvia que el promedio" if value >= average_rainfall else "Menos lluvia que el promedio"
    )
    comparison["bar_color"] = comparison["classification"].map(
        {
            "Más lluvia que el promedio": COLORS["blue"],
            "Menos lluvia que el promedio": COLORS["ocher"],
        }
    )
    comparison["signal_text"] = comparison["classification"].map(
        {
            "Más lluvia que el promedio": "Posible año muy lluvioso",
            "Menos lluvia que el promedio": "Posible año seco",
        }
    )

    fig = go.Figure(
        [
            go.Bar(
                x=comparison["year"],
                y=comparison["precipitation_total_mm"],
                marker={"color": comparison["bar_color"], "line": {"color": "#ffffff", "width": 1}},
                customdata=comparison[
                    ["difference_from_average", "classification", "signal_text", "precipitation_total_mm"]
                ].to_numpy(),
                hovertemplate=(
                    "<b>Año %{x}</b><br>"
                    "Precipitación anual: %{customdata[3]:.1f} mm<br>"
                    "Diferencia contra el promedio: %{customdata[0]:+.1f} mm<br>"
                    "Clasificación: %{customdata[1]}<br>"
                    "Señal visual: %{customdata[2]}<extra></extra>"
                ),
                name="Lluvia anual",
            )
        ]
    )
    fig.add_hline(
        y=average_rainfall,
        line_color=COLORS["orange"],
        line_width=3,
        line_dash="dash",
        annotation_text="Promedio anual",
        annotation_position="top left",
        annotation_font_color=COLORS["orange"],
    )
    fig.update_layout(
        title="",
        xaxis_title="Año",
        yaxis_title="Precipitación anual total (mm)",
        margin={"t": 20, "l": 40, "r": 30, "b": 40},
    )
    return style_chart(fig)


def build_detailed_table(station_df: pd.DataFrame, selected_year: int, scope: str) -> pd.DataFrame:
    filtered = station_df.copy()
    if scope == "Mostrar solo año seleccionado":
        filtered = filtered[filtered["year"] == selected_year]

    filtered = filtered.sort_values(["year", "month"]).copy()
    filtered["precipitation_mm"] = pd.to_numeric(filtered["precipitation_mm"], errors="coerce").round(1)
    filtered["tmax_c"] = pd.to_numeric(filtered["tmax_c"], errors="coerce").round(1)
    filtered["tmin_c"] = pd.to_numeric(filtered["tmin_c"], errors="coerce").round(1)
    filtered["demo_generated"] = filtered["demo_generated"].map(
        lambda value: "Sí" if str(value).lower() == "true" else "No"
    )

    table = filtered[
        [
            "year",
            "month_name",
            "precipitation_mm",
            "tmax_c",
            "tmin_c",
            "data_status",
            "precip_source",
            "tmax_source",
            "tmin_source",
            "demo_generated",
        ]
    ].rename(
        columns={
            "year": "Año",
            "month_name": "Mes",
            "precipitation_mm": "Precipitación mensual (mm)",
            "tmax_c": "Temperatura máxima promedio (°C)",
            "tmin_c": "Temperatura mínima promedio (°C)",
            "data_status": "Estado del dato",
            "precip_source": "Fuente precipitación",
            "tmax_source": "Fuente Tmax",
            "tmin_source": "Fuente Tmin",
            "demo_generated": "Dato generado",
        }
    )
    return table


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
        <div class="section-label">Clima del lugar seleccionado</div>
        <h3>{station_row['tipo_clima_didactico']}</h3>
        <p class="kid-message">{station_row['mensaje_para_ninos']}</p>
        <p class="climate-text">{station_row['explicacion_clima']}</p>
        <p><strong>Estación:</strong> {station_row['station_label']}</p>
        <p><strong>Ubicación:</strong> {station_row['municipality'].title()}, {station_row['state'].title()}</p>
        <p><strong>Descripción corta:</strong> {station_row['descripcion_corta']}</p>
        <div class="climate-metrics">
            <div><span>Altitud</span><strong>{station_row['altitude_m']:.0f} m</strong></div>
            <div><span>Temp. media anual</span><strong>{station_row['temperatura_media_anual']:.1f} °C</strong></div>
            <div><span>Temp. máxima prom.</span><strong>{station_row['temperatura_maxima_promedio']:.1f} °C</strong></div>
            <div><span>Temp. mínima prom.</span><strong>{station_row['temperatura_minima_promedio']:.1f} °C</strong></div>
            <div><span>Lluvia anual prom.</span><strong>{station_row['precipitacion_anual_promedio']:.1f} mm</strong></div>
        </div>
    </div>
    """


def popup_html(station_row: pd.Series) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif; min-width:240px; color:{COLORS['text']};">
        <div style="font-size:16px; font-weight:700; margin-bottom:8px; color:{COLORS['brown']};">{station_row['station_label']}</div>
        <div style="margin-bottom:4px;"><strong>Estado:</strong> {station_row['state'].title()}</div>
        <div style="margin-bottom:4px;"><strong>Municipio:</strong> {station_row['municipality'].title()}</div>
        <div style="margin-bottom:4px;"><strong>Clave:</strong> {int(station_row['station_id'])}</div>
        <div style="margin-bottom:4px;"><strong>Clima:</strong> {station_row['tipo_clima_didactico']}</div>
        <div style="margin-bottom:4px;"><strong>Altitud:</strong> {station_row['altitude_m']:.0f} m</div>
        <div style="margin-bottom:4px;"><strong>Temp. media anual:</strong> {station_row['temperatura_media_anual']:.1f} °C</div>
        <div><strong>Precipitación anual prom.:</strong> {station_row['precipitacion_anual_promedio']:.1f} mm</div>
    </div>
    """


def build_station_map(stations: pd.DataFrame, selected_station: str) -> folium.Map:
    selected_row = stations.loc[stations["station_label"] == selected_station].iloc[0]
    fmap = folium.Map(
        location=[float(selected_row["lat"]), float(selected_row["lon"])],
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=False,
        prefer_canvas=True,
    )

    mexico_bounds = [[14.0, -118.5], [33.8, -86.0]]
    fmap.fit_bounds(mexico_bounds)

    for _, row in stations.iterrows():
        is_selected = row["station_label"] == selected_station
        radius = 16 if is_selected else 11
        climate_color = safe_climate_color(row.get("color_clima"))
        weight = 6 if is_selected else 3

        popup = folium.Popup(popup_html(row), max_width=320)
        if is_selected:
            folium.CircleMarker(
                location=[float(row["lat"]), float(row["lon"])],
                radius=22,
                color=climate_color,
                weight=1,
                fill=True,
                fill_color=climate_color,
                fill_opacity=0.18,
                opacity=0.35,
            ).add_to(fmap)
        folium.CircleMarker(
            location=[float(row["lat"]), float(row["lon"])],
            radius=radius,
            color="#ffffff",
            weight=weight,
            fill=True,
            fill_color=climate_color,
            fill_opacity=0.95,
            tooltip=row["station_label"],
            popup=popup,
        ).add_to(fmap)

    return fmap


def climate_legend_html(stations: pd.DataFrame) -> str:
    items = (
        stations[["tipo_clima_didactico", "color_clima"]]
        .dropna()
        .drop_duplicates()
        .sort_values("tipo_clima_didactico")
        .values.tolist()
    )
    swatches = "".join(
        f'<div class="legend-item"><span class="legend-swatch" style="background:{safe_climate_color(color)};"></span><span>{label}</span></div>'
        for label, color in items
    )
    return f"""
    <div class="climate-legend">
        <div class="section-label">Tipos de clima representados</div>
        <p class="legend-note">Estaciones seleccionadas con distintos climas de México.</p>
        <div class="legend-grid">{swatches}</div>
    </div>
    """


def option_review_cards(question: dict, selected_answers: list[str]) -> str:
    cards = []
    selected_set = set(selected_answers)
    correct_set = set(question["respuestas_correctas"])

    for letter, text in question["opciones"].items():
        classes = ["quiz-option-review"]
        if letter in correct_set:
            classes.append("correct")
        elif letter in selected_set:
            classes.append("incorrect")
        cards.append(
            (
                f'<div class="{" ".join(classes)}">'
                f'<span class="quiz-option-letter">{letter}</span>'
                f'<div class="quiz-option-text">{html.escape(text)}</div>'
                "</div>"
            )
        )
    return '<div class="quiz-option-review-grid">' + "".join(cards) + "</div>"


def evaluate_question(question: dict, selected_answers: list[str]) -> bool:
    normalized = sorted({answer.upper() for answer in selected_answers})
    expected = sorted({answer.upper() for answer in question["respuestas_correctas"]})
    return normalized == expected


def reset_quiz_progress() -> None:
    st.session_state["quiz_started"] = False
    st.session_state["quiz_finished"] = False
    st.session_state["quiz_current_index"] = 0
    st.session_state["quiz_checked"] = False
    st.session_state["quiz_results"] = {}


def ensure_quiz_state() -> None:
    defaults = {
        "quiz_started": False,
        "quiz_finished": False,
        "quiz_current_index": 0,
        "quiz_checked": False,
        "quiz_results": {},
        "quiz_admin_open": False,
        "quiz_admin_authenticated": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_quiz_admin_credentials() -> tuple[Optional[str], Optional[str]]:
    try:
        admin_user = st.secrets.get("QUIZ_ADMIN_USER")
        admin_password = st.secrets.get("QUIZ_ADMIN_PASSWORD")
    except StreamlitSecretNotFoundError:
        admin_user = None
        admin_password = None
    return admin_user, admin_password


def render_quiz_admin(payload: dict) -> None:
    st.markdown('<div class="quiz-admin-toggle-wrap">', unsafe_allow_html=True)
    if st.button("⚙️", key="quiz_admin_toggle", help="Acceso administrador"):
        st.session_state["quiz_admin_open"] = not st.session_state.get("quiz_admin_open", False)
    st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state.get("quiz_admin_open", False):
        return

    st.markdown('<div class="quiz-admin-card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">Modo administrador</div>', unsafe_allow_html=True)
    st.info("Para editar permanentemente, modifica el Google Sheet.")

    admin_user, admin_password = get_quiz_admin_credentials()

    if not st.session_state.get("quiz_admin_authenticated", False):
        auth_col_1, auth_col_2, auth_col_3 = st.columns([1, 1, 0.45], gap="small")
        username = auth_col_1.text_input(
            "Usuario",
            key="quiz_admin_user_input",
            placeholder="usuario",
            label_visibility="collapsed",
        )
        password = auth_col_2.text_input(
            "Contraseña",
            key="quiz_admin_password_input",
            type="password",
            placeholder="contraseña",
            label_visibility="collapsed",
        )
        access_clicked = auth_col_3.button("Entrar", key="quiz_admin_login_button")

        if access_clicked:
            if not admin_user or not admin_password:
                st.warning("Configura `QUIZ_ADMIN_USER` y `QUIZ_ADMIN_PASSWORD` en `.streamlit/secrets.toml` o en los secretos de Streamlit Cloud.")
            elif username == admin_user and password == admin_password:
                st.session_state["quiz_admin_authenticated"] = True
                st.success("Modo administrador activado.")
                st.rerun()
            else:
                st.error("Credenciales incorrectas.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    st.success("Modo administrador activo.")
    summary_text = st.text_area(
        "Resumen final",
        value="\n".join(payload["final_summary"]),
        height=150,
        key="quiz_summary_text",
        help="Escribe una idea por línea para el bloque final.",
    )
    if st.button("Guardar bloque final", key="quiz_save_summary"):
        st.warning("Para editar permanentemente, modifica el Google Sheet.")

    st.markdown("### Preguntas")
    question_labels = [f"{question['id']}. {question['pregunta']}" for question in payload["questions"]]
    selected_label = st.selectbox(
        "Selecciona una pregunta",
        question_labels,
        key="quiz_admin_selected_question",
    )
    selected_index = question_labels.index(selected_label)
    question = payload["questions"][selected_index]

    iconos = st.text_input("Íconos", value=question["iconos"], key=f"edit_iconos_{question['id']}")
    pregunta = st.text_area("Pregunta", value=question["pregunta"], key=f"edit_pregunta_{question['id']}", height=90)
    permite_multiple = st.checkbox(
        "Permitir varias respuestas",
        value=question["permite_multiple"],
        key=f"edit_multiple_{question['id']}",
    )

    edited_options = {}
    for letter in sorted(question["opciones"].keys()):
        edited_options[letter] = st.text_input(
            f"Opción {letter}",
            value=question["opciones"][letter],
            key=f"edit_option_{question['id']}_{letter}",
        )

    correct_answers = st.multiselect(
        "Respuestas correctas",
        sorted(edited_options.keys()),
        default=question["respuestas_correctas"],
        key=f"edit_correct_{question['id']}",
    )
    explicacion = st.text_area(
        "Explicación",
        value=question["explicacion"],
        key=f"edit_exp_{question['id']}",
        height=100,
    )

    action_col_1, action_col_2, action_col_3, action_col_4 = st.columns(4)
    if action_col_1.button("Guardar pregunta", key=f"save_question_{question['id']}"):
        st.warning("Para editar permanentemente, modifica el Google Sheet.")

    if action_col_2.button("Subir", key=f"move_up_{question['id']}", disabled=selected_index == 0):
        st.warning("Para editar permanentemente, modifica el Google Sheet.")

    if action_col_3.button(
        "Bajar",
        key=f"move_down_{question['id']}",
        disabled=selected_index == len(payload["questions"]) - 1,
    ):
        st.warning("Para editar permanentemente, modifica el Google Sheet.")

    if action_col_4.button("Eliminar", key=f"delete_question_{question['id']}"):
        st.warning("Para editar permanentemente, modifica el Google Sheet.")

    if st.button("Agregar pregunta nueva", key="quiz_add_question"):
        st.warning("Para editar permanentemente, modifica el Google Sheet.")

    if st.button("Cerrar modo administrador", key="quiz_admin_close"):
        st.session_state["quiz_admin_authenticated"] = False
        st.session_state["quiz_admin_open"] = False
        st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_quiz_view() -> None:
    ensure_quiz_state()
    payload, loading_warning = load_quiz_payload()
    questions = payload["questions"]
    total_questions = len(questions)

    st.markdown("# Reto del Agua")
    st.markdown(
        "Descubre cómo viaja el agua y qué ocurre cuando llueve demasiado o muy poco."
    )
    if loading_warning:
        st.caption(loading_warning)

    if not st.session_state["quiz_started"] and not st.session_state["quiz_finished"]:
        st.markdown(
            f"""
            <div class="quiz-hero">
                <div class="quiz-hero-top">
                    <div>
                        <div class="section-label">Misión: seguir las pistas del agua</div>
                        <h3>Prepárate para descubrir cómo viaja el agua por el cielo, las nubes, la lluvia y el suelo.</h3>
                        <p class="quiz-hero-copy">Responde preguntas sobre evaporación, condensación, precipitación, infiltración, sequías e inundaciones.</p>
                    </div>
                    <div class="quiz-hero-icons">☀️ 💧 ☁️ 🌧️</div>
                </div>
                <div class="quiz-hero-stats">
                    <div class="quiz-hero-pill"><strong>{total_questions}</strong><span>preguntas</span></div>
                    <div class="quiz-hero-pill"><strong>Sin reloj</strong><span>responde con calma</span></div>
                    <div class="quiz-hero-pill"><strong>Juego visual</strong><span>aprende mientras exploras</span></div>
                </div>
                <div class="quiz-hero-note-card">
                    <span class="quiz-hero-note-icon">💡</span>
                    <p>En algunas preguntas puede haber más de una respuesta correcta.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Comenzar reto", key="quiz_start_button", width="stretch"):
            st.session_state["quiz_started"] = True
            st.session_state["quiz_finished"] = False
            st.session_state["quiz_current_index"] = 0
            st.session_state["quiz_checked"] = False
            st.session_state["quiz_results"] = {}
            st.rerun()
        render_quiz_admin(payload)
        return

    if st.session_state["quiz_finished"]:
        score = sum(1 for value in st.session_state["quiz_results"].values() if value)
        st.markdown(
            f"""
            <div class="quiz-finish-card">
                <div class="section-label">¡Reto completado!</div>
                <h2>Resultado: {score} de {total_questions}</h2>
                <div class="quiz-summary-title">Lo que descubrimos:</div>
                <ul class="quiz-summary-list">
                    {''.join(f"<li>{html.escape(item)}</li>" for item in payload['final_summary'])}
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Jugar otra vez", key="quiz_restart_button", width="stretch"):
            reset_quiz_progress()
            st.rerun()
        render_quiz_admin(payload)
        return

    current_index = st.session_state["quiz_current_index"]
    current_question = questions[current_index]
    progress_text = f"Pregunta {current_index + 1} de {total_questions}"
    progress_percent = ((current_index + 1) / total_questions) * 100

    st.markdown(
        f"""
        <div class="quiz-question-shell">
            <div class="quiz-question-card">
                <div class="quiz-question-top">
                    <div class="section-label">{progress_text}</div>
                    <div class="quiz-icons">{html.escape(current_question['iconos'])}</div>
                </div>
                <h2>{html.escape(current_question['pregunta'])}</h2>
            </div>
            <div class="quiz-progress-shell">
                <div class="quiz-progress-track">
                    <div class="quiz-progress-fill" style="width: {progress_percent:.1f}%;"></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="quiz-subprompt">Selecciona tu respuesta y luego presiona Revisar.</div>',
        unsafe_allow_html=True,
    )

    option_letters = list(current_question["opciones"].keys())
    widget_key = f"quiz_answer_{current_question['id']}"
    if current_question["permite_multiple"]:
        st.markdown(
            '<div class="quiz-answer-label">Elige una o varias respuestas</div>',
            unsafe_allow_html=True,
        )
        selected = []
        for letter in option_letters:
            checkbox_key = f"{widget_key}_{letter}"
            checked = st.checkbox(
                f"{letter}. {current_question['opciones'][letter]}",
                key=checkbox_key,
                disabled=st.session_state["quiz_checked"],
            )
            if checked:
                selected.append(letter)
    else:
        single_value = st.radio(
            "Selecciona una respuesta",
            option_letters,
            format_func=lambda letter: f"{letter}. {current_question['opciones'][letter]}",
            key=widget_key,
            label_visibility="collapsed",
            disabled=st.session_state["quiz_checked"],
        )
        selected = [single_value] if single_value else []

    review_disabled = len(selected) == 0
    if not st.session_state["quiz_checked"]:
        if st.button(
            "Revisar",
            key=f"review_{current_question['id']}",
            disabled=review_disabled,
            width="content",
        ):
            is_correct = evaluate_question(current_question, selected)
            results = dict(st.session_state["quiz_results"])
            results[current_question["id"]] = is_correct
            st.session_state["quiz_results"] = results
            st.session_state["quiz_checked"] = True
            st.rerun()
    else:
        is_correct = st.session_state["quiz_results"].get(current_question["id"], False)
        if is_correct:
            st.success("Muy bien. Esa respuesta es correcta.")
        else:
            st.error("Casi. Vamos a revisar la explicación.")

        st.markdown(option_review_cards(current_question, selected), unsafe_allow_html=True)
        st.info(current_question["explicacion"])

        next_label = "Terminar reto" if current_index == total_questions - 1 else "Siguiente"
        if st.button(next_label, key=f"next_{current_question['id']}", width="stretch"):
            st.session_state["quiz_checked"] = False
            if current_index == total_questions - 1:
                st.session_state["quiz_finished"] = True
            else:
                st.session_state["quiz_current_index"] = current_index + 1
            st.rerun()

    render_quiz_admin(payload)


def render_map_sidebar(stations: pd.DataFrame, options: list[str], years: list[int]) -> None:
    with st.sidebar:
        st.markdown("---")
        st.markdown("## Filtros")
        st.selectbox("Estación climatológica", options, key="selected_station")
        st.select_slider("Año", options=years, key="selected_year")
        st.markdown(climate_legend_html(stations), unsafe_allow_html=True)


def render_map_view(dataset: pd.DataFrame, stations: pd.DataFrame) -> None:
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
        '<div class="map-helper">Haz clic en un marcador para ver la información de la estación. La estación seleccionada conserva su color climático y se resalta con un halo.</div>',
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

    render_map_sidebar(stations, options, years)

    station_df = dataset[dataset["station_label"] == st.session_state["selected_station"]].copy()
    station_df = station_df.sort_values(["year", "month"])
    year_df = station_df[station_df["year"] == st.session_state["selected_year"]].sort_values("month")
    annual_df = build_annual_summary(station_df)
    station_row = stations.loc[stations["station_label"] == st.session_state["selected_station"]].iloc[0]
    annual_metrics = annual_df[annual_df["year"] == st.session_state["selected_year"]].iloc[0]
    station_image_uri = load_station_image_uri(int(station_row["station_id"]))
    station_place_text = STATION_PLACE_DESCRIPTIONS.get(
        int(station_row["station_id"]),
        "Esta estación ayuda a explicar cómo cambia el clima en distintas regiones de México.",
    )

    info_col, image_col = st.columns([0.95, 1.15], gap="large")
    with info_col:
        st.markdown("## Clima del lugar seleccionado")
        st.markdown(station_card(station_row), unsafe_allow_html=True)
    with image_col:
        st.markdown('<div class="photo-card">', unsafe_allow_html=True)
        st.markdown('<div class="section-label">Así se ve este clima</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="photo-label">{station_row["tipo_clima_didactico"]}</div>',
            unsafe_allow_html=True,
        )
        if station_image_uri:
            st.markdown(
                f'<div class="photo-frame"><img src="{station_image_uri}" alt="{station_row["station_label"]}"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div class="photo-frame"><div class="photo-placeholder">Imagen no disponible</div></div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="photo-description">{station_place_text}</div>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

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

    st.markdown("## ¿Qué años llovió más o menos de lo normal?")
    st.caption(
        "Comparamos la lluvia de cada año con el promedio de la estación. Las barras azules muestran años más lluviosos y las barras naranja muestran años con menos lluvia."
    )
    st.plotly_chart(
        build_rainfall_comparison_chart(annual_df),
        use_container_width=True,
        config={"displayModeBar": False, "responsive": True},
    )
    st.caption(
        "Esta gráfica es una comparación visual inicial. Los años por encima del promedio pueden indicar años más lluviosos, y los años por debajo pueden indicar años más secos."
    )

    st.markdown("## Tabla detallada de datos mensuales")
    table_scope = st.radio(
        "Alcance de la tabla",
        ["Mostrar solo año seleccionado", "Mostrar todos los años de la estación"],
        horizontal=True,
    )
    detailed_table = build_detailed_table(station_df, st.session_state["selected_year"], table_scope)
    st.dataframe(detailed_table, width="stretch", hide_index=True)
    st.download_button(
        "Descargar tabla de la estación seleccionada",
        data=detailed_table.to_csv(index=False).encode("utf-8-sig"),
        file_name="datos_detallados_estacion_seleccionada.csv",
        mime="text/csv",
    )
    st.caption("La tabla reúne los valores mensuales disponibles para la estación elegida.")


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
        .map-shell,
        .info-card,
        .climate-legend,
        .photo-card,
        .quiz-hero,
        .quiz-question-shell,
        .quiz-question-card,
        .quiz-finish-card,
        .quiz-admin-card {{
            background: rgba(255, 250, 240, 0.92);
            border: 1px solid rgba(155,106,47,0.10);
            border-radius: 1.2rem;
            box-shadow: 0 14px 28px rgba(114, 92, 54, 0.08);
            overflow: hidden;
        }}
        .map-shell {{
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .map-helper {{
            color: {COLORS["muted"]};
            font-size: 0.96rem;
            margin: 0 0 0.8rem 0.1rem;
            overflow-wrap: anywhere;
        }}
        .info-card,
        .photo-card,
        .climate-legend,
        .quiz-hero,
        .quiz-question-shell,
        .quiz-question-card,
        .quiz-finish-card,
        .quiz-admin-card {{
            padding: 1.1rem 1.2rem;
        }}
        .info-card *,
        .photo-card *,
        .climate-legend *,
        .quiz-hero *,
        .quiz-question-shell *,
        .quiz-question-card *,
        .quiz-finish-card *,
        .quiz-admin-card * {{
            overflow-wrap: anywhere;
            word-break: break-word;
        }}
        .info-card p {{
            margin-bottom: 0.45rem;
        }}
        .kid-message {{
            font-size: 1.18rem;
            font-weight: 700;
            color: {COLORS["brown"]};
            margin: 0.35rem 0 0.75rem 0;
        }}
        .climate-text {{
            color: {COLORS["muted"]};
            line-height: 1.5;
            margin-bottom: 0.95rem;
        }}
        .climate-metrics {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.7rem;
            margin-top: 1rem;
        }}
        .climate-metrics div {{
            background: rgba(255,255,255,0.52);
            border: 1px solid rgba(155,106,47,0.08);
            border-radius: 0.8rem;
            padding: 0.7rem 0.8rem;
        }}
        .climate-metrics span {{
            display: block;
            color: {COLORS["muted"]};
            font-size: 0.8rem;
            margin-bottom: 0.18rem;
        }}
        .climate-metrics strong {{
            color: {COLORS["text"]};
            font-size: 0.98rem;
        }}
        .section-label {{
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: {COLORS["brown"]};
            font-size: 0.74rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .legend-note {{
            color: {COLORS["muted"]};
            font-size: 0.9rem;
            margin: 0 0 0.7rem 0;
        }}
        .legend-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 0.6rem;
        }}
        .legend-item {{
            display: flex;
            align-items: flex-start;
            gap: 0.55rem;
            color: {COLORS["text"]};
            font-size: 0.94rem;
            line-height: 1.3;
            min-width: 0;
        }}
        .legend-swatch {{
            width: 18px;
            height: 18px;
            border-radius: 0.3rem;
            border: 1px solid rgba(58,50,37,0.14);
            flex: 0 0 18px;
            margin-top: 0.1rem;
        }}
        .photo-frame {{
            width: 100%;
            height: 390px;
            border-radius: 0.95rem;
            overflow: hidden;
            background: linear-gradient(180deg, #e9e5db 0%, #dcd6c7 100%);
            border: 1px solid rgba(155,106,47,0.10);
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.9rem;
        }}
        .photo-frame img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}
        .photo-placeholder {{
            color: {COLORS["muted"]};
            font-size: 1.05rem;
            font-weight: 600;
        }}
        .photo-label {{
            display: inline-block;
            background: rgba(255,255,255,0.72);
            color: {COLORS["brown"]};
            border: 1px solid rgba(155,106,47,0.12);
            border-radius: 999px;
            padding: 0.25rem 0.7rem;
            font-size: 0.82rem;
            font-weight: 700;
            margin-bottom: 0.7rem;
            max-width: 100%;
        }}
        .photo-description {{
            color: {COLORS["muted"]};
            line-height: 1.55;
            margin-top: 0.5rem;
        }}
        div[data-testid="metric-container"] {{
            background: rgba(255, 250, 240, 0.92);
            border: 1px solid rgba(155,106,47,0.10);
            border-radius: 0.95rem;
            padding: 0.65rem 0.9rem;
            box-shadow: 0 8px 18px rgba(114, 92, 54, 0.06);
        }}
        .quiz-hero h3,
        .quiz-question-card h2,
        .quiz-finish-card h2 {{
            margin-top: 0.25rem;
            margin-bottom: 0.4rem;
        }}
        .quiz-hero {{
            padding: 1.3rem 1.35rem;
            background:
                radial-gradient(circle at top right, rgba(88,197,232,0.14), transparent 26%),
                radial-gradient(circle at bottom left, rgba(217,121,37,0.12), transparent 24%),
                linear-gradient(180deg, #fffaf1 0%, #fffdf9 100%);
            border: 1px solid rgba(217,121,37,0.10);
            margin-bottom: 0.75rem;
        }}
        .quiz-hero-top {{
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.4rem;
        }}
        .quiz-hero h3 {{
            font-size: clamp(1.6rem, 2.2vw, 2.6rem);
            line-height: 1.18;
            margin: 0.35rem 0 0.65rem 0;
        }}
        .quiz-hero-copy {{
            color: {COLORS["muted"]};
            font-size: 1.05rem;
            line-height: 1.6;
            max-width: 56rem;
            margin: 0;
        }}
        .quiz-hero-icons {{
            font-size: clamp(2rem, 3vw, 3.2rem);
            letter-spacing: 0.15rem;
            white-space: nowrap;
            padding-top: 0.35rem;
        }}
        .quiz-hero-stats {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.9rem;
            margin-top: 1rem;
        }}
        .quiz-hero-pill {{
            background: rgba(255,255,255,0.86);
            border: 1px solid rgba(155,106,47,0.10);
            border-radius: 1.1rem;
            padding: 0.95rem 1rem;
            box-shadow: 0 10px 20px rgba(114, 92, 54, 0.05);
        }}
        .quiz-hero-pill strong {{
            display: block;
            color: {COLORS["text"]};
            font-size: 1.05rem;
            margin-bottom: 0.15rem;
        }}
        .quiz-hero-pill span {{
            color: {COLORS["muted"]};
            font-size: 0.93rem;
        }}
        .quiz-hero-note-card {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
            background: rgba(255, 248, 231, 0.95);
            border: 1px solid rgba(217,121,37,0.14);
            border-radius: 1rem;
            padding: 0.9rem 1rem;
            margin-top: 1rem;
        }}
        .quiz-hero-note-card p {{
            margin: 0;
            color: {COLORS["text"]};
            font-weight: 600;
        }}
        .quiz-hero-note-icon {{
            font-size: 1.4rem;
            line-height: 1;
        }}
        .quiz-question-shell {{
            padding: 0.9rem 1rem 1.1rem 1rem;
            margin-bottom: 0.85rem;
            background: rgba(255, 252, 245, 0.94);
        }}
        .quiz-question-card {{
            padding: 1.1rem 1.25rem 1.45rem 1.25rem;
            border: 1px solid rgba(217,121,37,0.10);
            background: linear-gradient(180deg, #fffaf1 0%, #fffdf8 100%);
        }}
        .quiz-question-card h2 {{
            font-size: clamp(2rem, 3.2vw, 4.1rem);
            line-height: 1.12;
            margin-top: 1rem;
            margin-bottom: 0.2rem;
        }}
        .quiz-hero-meta,
        .quiz-hero-note,
        .quiz-summary-title {{
            color: {COLORS["muted"]};
        }}
        .quiz-icons {{
            font-size: clamp(2rem, 2.4vw, 3rem);
        }}
        .quiz-question-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1rem;
        }}
        .quiz-progress-shell {{
            padding: 0.9rem 0.1rem 0 0.1rem;
        }}
        .quiz-progress-track {{
            width: 100%;
            height: 16px;
            border-radius: 999px;
            background: rgba(255,255,255,0.96);
            overflow: hidden;
            border: 1px solid rgba(155,106,47,0.08);
        }}
        .quiz-progress-fill {{
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, #d97925 0%, #f1b04a 100%);
            box-shadow: 0 4px 10px rgba(217,121,37,0.18);
        }}
        .quiz-subprompt {{
            color: {COLORS["text"]};
            font-size: 1rem;
            margin: 0.2rem 0 0.8rem 0.1rem;
            font-weight: 600;
        }}
        .quiz-answer-label {{
            color: {COLORS["muted"]};
            font-size: 0.98rem;
            margin: 0.1rem 0 0.8rem 0.1rem;
        }}
        div[data-testid="stRadio"] > div {{
            gap: 0.85rem;
        }}
        div[data-testid="stRadio"] label {{
            background: #eef7fd;
            border: 4px solid #b7def5;
            border-radius: 1.5rem;
            padding: 1.05rem 1.2rem;
            min-height: 88px;
            align-items: center;
            transition: all 0.2s ease;
        }}
        div[data-testid="stRadio"] label:hover {{
            transform: translateY(-1px);
            box-shadow: 0 10px 24px rgba(90, 177, 224, 0.12);
            border-color: #8ecded;
        }}
        div[data-testid="stRadio"] label:has(input:checked) {{
            background: #dff1fc;
            border-color: #69b9e6;
            box-shadow: 0 10px 26px rgba(90, 177, 224, 0.18);
        }}
        div[data-testid="stRadio"] label p {{
            font-size: clamp(1.25rem, 1.5vw, 1.7rem);
            line-height: 1.35;
            font-weight: 600;
            color: #17395c;
        }}
        div[data-testid="stRadio"] label > div:first-child {{
            margin-right: 0.75rem;
        }}
        div[data-testid="stCheckbox"] {{
            margin-bottom: 0.85rem;
        }}
        div[data-testid="stCheckbox"] label {{
            background: #eef7fd;
            border: 4px solid #b7def5;
            border-radius: 1.5rem;
            padding: 1.05rem 1.2rem;
            min-height: 88px;
            align-items: center;
        }}
        div[data-testid="stCheckbox"] label:has(input:checked) {{
            background: #dff1fc;
            border-color: #69b9e6;
            box-shadow: 0 10px 26px rgba(90, 177, 224, 0.18);
        }}
        div[data-testid="stCheckbox"] label p {{
            font-size: clamp(1.25rem, 1.5vw, 1.7rem);
            line-height: 1.35;
            font-weight: 600;
            color: #17395c;
        }}
        div[data-testid="stButton"] > button[kind="secondary"] {{
            border-radius: 1rem;
        }}
        div[data-testid="stButton"] > button {{
            font-weight: 700;
        }}
        .quiz-option-review-grid {{
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 1rem 0;
        }}
        .quiz-option-review {{
            display: flex;
            align-items: flex-start;
            gap: 0.8rem;
            padding: 0.9rem 1rem;
            border-radius: 1rem;
            border: 1px solid rgba(155,106,47,0.12);
            background: rgba(255,255,255,0.66);
        }}
        .quiz-option-review.correct {{
            background: {COLORS["success_bg"]};
            border-color: rgba(47,125,66,0.25);
            color: {COLORS["success_text"]};
        }}
        .quiz-option-review.incorrect {{
            background: {COLORS["error_bg"]};
            border-color: rgba(162,76,52,0.22);
            color: {COLORS["error_text"]};
        }}
        .quiz-option-letter {{
            width: 34px;
            height: 34px;
            border-radius: 999px;
            background: rgba(255,255,255,0.82);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            flex: 0 0 34px;
        }}
        .quiz-summary-list {{
            margin-top: 0.5rem;
            padding-left: 1.2rem;
            line-height: 1.7;
        }}
        .quiz-admin-toggle-wrap {{
            margin-top: 1.5rem;
            display: flex;
            justify-content: flex-end;
        }}
        .quiz-admin-card input {{
            background: rgba(255,255,255,0.94);
        }}
        @media (max-width: 960px) {{
            .climate-metrics,
            .quiz-option-review-grid,
            .quiz-hero-stats {{
                grid-template-columns: 1fr;
            }}
            .quiz-hero-top,
            .quiz-question-top {{
                align-items: flex-start;
                flex-direction: column;
            }}
            .quiz-hero-icons {{
                white-space: normal;
            }}
            .quiz-question-card h2 {{
                font-size: 2rem;
            }}
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


with st.sidebar:
    st.markdown("## Navegación")
    current_view = st.selectbox(
        "Ir a sección",
        ["Mapa climático", "Reto del Agua"],
        key="current_view",
    )


if current_view == "Mapa climático":
    render_map_view(dataset, stations)
else:
    render_quiz_view()
