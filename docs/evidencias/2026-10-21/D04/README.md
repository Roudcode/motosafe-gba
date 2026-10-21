# D04 — sensibilidad real de pesos/umbral y clustering de corredores (2026-10-21, SES-140)

Ver el asiento completo en `docs/gestion/BITACORA.md` (SES-140) para el contexto y las conclusiones.

## Archivos

- `hotspots_trim.json`, `insgGeneral_trim.json`, `insgMoto_trim.json`: datasets reales completos (740/633/502 filas) exportados desde `localStorage` de una sesión real autenticada de la app (mismos datos que `/hotspots` y `/hotspots-inseguridad?tipo=general|moto` devolvieron en ese momento), recortados a `[id, lat, lng, nivel]`.
- `rutas_coords.json`: coordenadas reales (muestreadas cada 4 puntos) de las 3 alternativas de cada uno de los 4 casos de ruta de D03, obtenidas de `/rutas` (TomTom real) contra las mismas direcciones geocodificadas en `docs/evidencias/2026-09-13/D03/rutas_referencia.csv`.
- `sensibilidad_pesos.py` / `salida_sensibilidad_pesos.txt`: replica la lógica real de `frontend/src/utils/riesgoRuta.js` y `geoRiesgo.js` en Python y la corre contra los datos de arriba, variando `PESO_RIESGO` y `UMBRAL_CRUCE_KM`.
- `sensibilidad_corredores.py` / `salida_sensibilidad_corredores.txt`: replica la lógica real de `notebooks/identificar_corredores.py` (sin tocar `data/corredores_candidatos.csv`) contra `data/motos_limpio.csv` y `data/siniestros_viales_victimas.csv` reales, variando `UMBRAL_MIN_SINIESTROS`, `SINIESTROS_POR_TRAMO_OBJETIVO` y `MAX_TRAMOS_POR_CALLE`.

Para reproducir: correr cualquiera de los dos scripts `.py` tal cual desde esta carpeta (usan rutas relativas al repo).
