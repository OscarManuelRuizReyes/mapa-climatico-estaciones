# Mapa interactivo de estaciones climáticas de México

Aplicación educativa en Streamlit para explorar estaciones climáticas seleccionadas de México, comparar precipitación y temperatura entre 2015 y 2024 y aprender sobre el ciclo del agua mediante actividades interactivas.

> Los datos son procesados con fines demostrativos y educativos. No deben utilizarse como validación climatológica oficial.

## Objetivo

Facilitar una lectura clara y accesible del clima de distintas regiones de México, combinando mapa, fotografías, gráficas, tablas y recursos didácticos para públicos escolares.

## Funcionalidades

- Mapa de México con estaciones, tipos de clima y selección interactiva.
- Comparación mensual y anual de precipitación y temperaturas.
- Filtros por estación y año, tabla detallada y descarga en CSV.
- Fotografías y explicaciones educativas de cada estación.
- `Reto del Agua` y `Viaje de una gotita` como recursos de aprendizaje.
- Fuente base OpenStreetMap, sin depender de una clave de CARTO.

## Tecnologías

- Python y Streamlit
- pandas
- Folium y streamlit-folium
- Plotly
- Pillow

## Estructura

```text
.
├── app.py                         # Aplicación principal
├── src/theme.py                   # Paleta y tipografía centralizadas
├── assets/logos/                  # Recursos institucionales para la interfaz
├── data/                          # Contenido de actividades educativas
├── Fotos/                         # Fotografías y recursos del ciclo del agua
├── Fuentes/                       # Datos y documentación fuente
│   └── branding/                  # Guía de identidad Talento CICY
├── docs/                          # Informes técnicos del proyecto
└── requirements.txt               # Dependencias de ejecución
```

## Instalación y ejecución

Se recomienda Python 3.10 o posterior.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La aplicación estará disponible normalmente en `http://localhost:8501`. Para detenerla, presiona `Ctrl+C` en la terminal donde se ejecuta.

## Datos y configuración

Los CSV utilizados por la aplicación están en `Fuentes/`. La carga remota de preguntas desde Google Sheets es opcional y mantiene un contenido local de respaldo. Las variables sensibles deben almacenarse en `.streamlit/secrets.toml`, archivo excluido de Git.

## Identidad visual

La interfaz adopta la guía de Talento CICY incluida en `Fuentes/branding/2026 Branding board TC.pdf`: azul `#005680`, verde `#7B8323` y Noto Sans como tipografía preferente. Los colores usados para representar series y categorías climáticas se conservan independientes de la paleta institucional.

## Autoría

- Dra. Yalina Montecelos Zamora
- Ing. Oscar Manuel Ruiz Reyes

Proyecto desarrollado con referencia institucional de Talento CICY y CICY.
