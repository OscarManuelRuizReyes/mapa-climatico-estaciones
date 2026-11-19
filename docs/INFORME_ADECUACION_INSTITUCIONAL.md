# Informe de adecuación institucional

## Alcance aplicado

- Se incorporó la identidad visual de Talento CICY con azul `#005680`, verde `#7B8323` y Noto Sans como familia tipográfica preferente.
- Se agregó una cabecera institucional, un pie de autoría y estilos consistentes para navegación, tarjetas, formularios, tablas, mapa y gráficas.
- Se separaron los tokens visuales de los colores científicos para no cambiar la lectura de las variables climáticas.
- Se organizó la guía de marca en `Fuentes/branding/` y el logotipo de interfaz en `assets/logos/`.
- Se incorporaron desde la guía original el lockup `Ciencia y Tecnología | CICY` y un patrón halftone, organizado en `assets/branding/`, para detalles discretos del encabezado y cierre institucional.
- Se amplió la documentación de instalación, estructura, datos e identidad institucional.

## Integridad funcional

No se modificaron cálculos, datasets, coordenadas, filtros, selección de estaciones, marcadores, popups, descargas ni la navegación de las actividades educativas.

## Seguridad

La revisión no encontró credenciales ni rutas privadas en archivos rastreados. `.streamlit/secrets.toml` y `.env` permanecen excluidos por `.gitignore`; no se inspeccionó ni documentó su contenido.

## Candidatos de limpieza no eliminados

- `Fuentes/ProyectoCicy.code-workspace`: configuración local, ahora ignorada por Git.
- `Fotos/ciclo_agua/22029385.jpeg`, `59982735.jpeg` y `76647647464.png`: recursos locales no rastreados cuyo uso debe confirmarse antes de incorporarlos o eliminarlos.
- `Fuentes/image.jpeg`, `Fotos/59283752.png` y carpetas de reconstrucción del ciclo: se conservaron porque podrían servir como referencias o recursos históricos.
