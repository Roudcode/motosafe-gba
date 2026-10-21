# A09 — muestra real de notas de prensa para etiquetado (2026-10-21, SES-146)

**Esto es solo exportación de datos reales, sin análisis ni curación.** El análisis de precisión queda
para Rodo, por separado, como pidió explícitamente ("eso lo hago yo después, separado de quien genera el
dato").

## Qué es

`muestra_calles.csv`: 50 notas reales de `reportes_prensa` (tabla real de la base de desarrollo local,
794 filas totales al momento de correr esto: 758 barrio, 21 calle, 15 interseccion).

- **Todas** las 36 filas reales con `nivel_precision` en `calle` (21) o `interseccion` (15) — son las que
  más interesa revisar para A09 (calidad del extractor en el caso más exigente).
- **14 filas de `barrio` sorteadas al azar** (semilla fija `20261021`, reproducible con el script) sobre
  las 759 reales de ese nivel, sin ningún criterio de selección manual, para llegar a 50 sin "elegir" cuáles
  entran.
- Total: 50, dentro del rango 40-60 pedido.

## Columnas

`id, titulo, descripcion_completa, query_extraida, nivel_precision, url` son las pedidas. Se agregó una
séptima, `descripcion_obtenida_en_vivo`, para no mezclar dato verificado con dato no verificado (ver
limitación abajo) — no reemplaza ninguna de las seis, solo marca el origen de `descripcion_completa` y
`query_extraida`.

- `id`, `titulo` (= `titular` de la tabla), `nivel_precision`, `url` (= `url_fuente`): salen directo de la
  base real, tal cual están guardados.
- `descripcion_completa` y `query_extraida`: **no están persistidas en la base** (`_evaluar_y_guardar` en
  `scrapear_noticias_robos.py` las calcula de paso y nunca las guarda). Se obtuvieron bajando cada URL en
  vivo con el mismo código real del scraper (`extraer_titulo_descripcion`, mismo `HEADERS_NAVEGADOR`, misma
  pausa `PAUSA_ENTRE_FETCHES_SEG`) y corriendo `extraer_ubicacion(titular_real, descripcion_bajada)` —
  exactamente la función que decide `query_extraida`, `nivel_precision` y el radio en producción.

## Limitación real y declarada

`descripcion_completa`/`query_extraida` reflejan el contenido de la página **hoy** (2026-10-21), no
necesariamente el que vio el scraper el día que guardó cada fila (un medio puede editar una nota después de
publicarla). Es una aproximación fiel pero no una reconstrucción exacta del momento del guardado original.
En esta corrida las 50 URLs respondieron igual (`descripcion_obtenida_en_vivo=True` en las 50); si alguna
vez una URL no responde, esa fila queda con `descripcion_completa`/`query_extraida` vacías en vez de
inventar contenido (el script no completa nada a mano).

`query_extraida` salió vacía en 2 de las 50 filas: son casos reales donde `extraer_ubicacion` sobre el
texto bajado hoy no encontró pista de ubicación utilizable — dato real, no error del script.

## Reproducir

`exportar_muestra.py`, corrido tal cual desde esta carpeta con el Python del venv del backend
(`backend/venv312/Scripts/python.exe`). Necesita `DATABASE_URL` real (se toma de `backend/.env`) y acceso
de red de salida a los sitios de prensa reales.
