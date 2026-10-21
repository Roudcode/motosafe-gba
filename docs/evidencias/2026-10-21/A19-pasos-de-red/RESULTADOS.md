# A19 — pasos con red del pipeline canónico contra servicios reales (2026-10-21, SES-149)

Faltaban específicamente los tres pasos con red de `docs/modelo/PIPELINE_CANONICO.md` (1, 2 y 7), corridos
contra los servicios reales -- no contra ninguna copia ya descargada. Se corrieron en una **copia de
trabajo aislada** (fuera del repo, en el scratchpad de la sesión:
`.../scratchpad/A19-copia-trabajo/{notebooks,data}/`), copiando los tres scripts tal cual y, para el paso
7, el `corredores_candidatos.csv` real como única entrada (los tres scripts resuelven su ruta de salida
como `Path(__file__).resolve().parent.parent / "data" / ...`, así que al vivir en la copia escriben ahí, no
en el `data/` real del repo). **No se corrió `promover_artefactos.py --confirmar`** ni se tocó ningún
archivo de `data/` real -- eso es una decisión aparte, como pidió Rodo.

## Paso 1 — `fetch_delitos_caba.py` (Buenos Aires Data)

Primera corrida: el recurso de 2020 devolvió `502 Bad Gateway` real del servidor (hallazgo real, no
simulado). Reintentado a los pocos minutos: `curl` manual al mismo recurso dio `200`, y una segunda corrida
completa del script trajo los 10 años sin error. **Confirmado transitorio, no un link roto.**

- **1.387.622 delitos** descargados (2016-2025).
- **Idéntico byte a byte** al `data/delitos_caba.csv` vigente: mismo recuento de filas (1.387.623 con
  encabezado) y mismo SHA256 (`5125e4da...`). El dataset de Buenos Aires Data no cambió desde la última
  vez que se generó el CSV vigente.

## Paso 2 — `fetch_clima_historico.py` (Open-Meteo)

- **68.425 filas** (vs 67.297 del vigente): la diferencia son 1.128 filas nuevas, el rango de fechas que
  pasó entre que se generó el CSV vigente (hasta 2026-09-04) y hoy (hasta 2026-10-21) -- el script usa
  `date.today()` como fin, así que es exactamente el comportamiento esperado, no un error.
- **Hallazgo real**: las primeras 67.200 líneas son idénticas, pero las últimas ~13-14 horas del archivo
  vigente (2026-09-04, horas 9 a 21) **cambiaron levemente** en la nueva descarga (ej. temperatura 8.9°C →
  9.1°C, humedad 78% → 77%). El archivo histórico de Open-Meteo no es 100% inmutable para las fechas más
  recientes al momento de una descarga: se revisa/afina después, consistente con que esos puntos todavía no
  tenían el reanálisis completo cuando se bajaron la primera vez. Es un límite real a declarar (ya lo
  insinúa D01 sobre Open-Meteo, pero no con este detalle concreto): reentrenar con clima recién descargado
  puede traer micro-diferencias en los días más recientes del rango anterior, no solo filas nuevas.

## Paso 7 — `fetch_corredores_geometria.py` (OSRM público)

243/243 calles candidatas resueltas sin ningún fallo (pausa real de 1,1s entre pedidos, ~4-5 minutos de
corrida).

- **Hallazgo real, medido**: de las 243 geometrías, **140 (57,6%) salieron idénticas** al
  `data/corredores_riesgo.csv` vigente y **103 (42,4%) cambiaron**, con los mismos puntos de origen/destino
  en ambos casos (confirmado comparando `lat_a/lng_a/lat_b/lng_b`: exactamente iguales). Ejemplo: "Av.
  Pueyrredón" tramo 2, mismos extremos, polilínea de 868 caracteres codificados en la corrida anterior vs
  1406 en esta -- OSRM eligió un camino distinto entre los mismos dos puntos. Esto confirma con datos reales
  el límite que ya declara `FICHAS_FUENTES.md` sobre el servidor demo de OSRM (sin garantía de
  reproducibilidad): la geometría de un corredor no es estable entre corridas, aunque los puntos que definen
  cada tramo (que sí vienen de `identificar_corredores.py`, sin red) no cambian.

## Conclusión

Los tres pasos de red corren limpio contra los servicios reales de hoy. Delitos: sin cambios. Clima: datos
nuevos esperados más una revisión real y acotada de los últimos días del rango anterior. Corredores: la
geometría de más del 40% de las calles cambia entre corridas reales de OSRM aunque los extremos no cambien
-- un límite real y medido, no antes cuantificado, que vale la pena agregar a D01/`FICHAS_FUENTES.md` si
Rodo lo considera relevante para el informe.

No se promovió nada a `backend/` ni se tocó `data/` real -- los tres CSV generados quedan solo en la copia
de trabajo del scratchpad de esta sesión (no versionada, se pierde al cerrar la sesión salvo que se pida
conservarla).
