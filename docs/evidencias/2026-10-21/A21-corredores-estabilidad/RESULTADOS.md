# A21 — procedencia y estabilidad espacial real de los corredores de riesgo (2026-10-21)

Depende de A20 (universo limpio y común), corrido justo antes en esta misma sesión. El universo real de
siniestros de moto (`motos_limpio.csv`) no cambió con el criterio común de A20 (0 filas adicionales
excluidas, hash idéntico) -- así que los corredores de este ítem corren sobre exactamente los mismos datos
de entrada de siempre, ya "limpios y comunes" según lo que mide A20.

## Procedencia

`data/corredores_riesgo.csv` (columnas: `cantidad_siniestros, mortales, graves, comuna_moda,
tipo_via_moda, contraparte_moda, edad_promedio, sexo_moda, calle, tramo, tramos_totales, lat_a, lng_a,
lat_b, lng_b, geometria`) sale de dos pasos reales, en este orden (`docs/modelo/PIPELINE_CANONICO.md`):

1. `identificar_corredores.py` (sin red): agrupa `motos_limpio.csv` por calle (regex sobre
   `direccion_normalizada_siniestro`), filtra calles con ≥30 siniestros (`UMBRAL_MIN_SINIESTROS`), parte
   cada una en hasta 8 tramos (`MAX_TRAMOS_POR_CALLE`) de ~40 siniestros cada uno
   (`SINIESTROS_POR_TRAMO_OBJETIVO`), y para cada tramo calcula el contexto real (comuna/tipo de vía/
   contraparte más frecuentes, edad promedio, sexo más frecuente) agregando las filas reales que caen en
   ese tramo -- y los dos puntos más alejados entre sí dentro del tramo (`lat_a/lng_a/lat_b/lng_b`), que
   definen sus extremos.
2. `fetch_corredores_geometria.py` (con red, OSRM público): toma esos mismos extremos y les pide a OSRM la
   polilínea real de la calle entre ambos puntos (columna `geometria`).

Cada columna de `corredores_riesgo.csv` traza a una agregación real sobre siniestros reales -- no hay
ningún valor inventado ni un valor por defecto que no venga de una fila real del dataset.

## Estabilidad espacial: dos preguntas distintas, medidas por separado

### 1. Los puntos que definen cada corredor (paso 1, sin red)

**100% deterministas**, medido de verdad: se corrió `identificar_corredores.py` dos veces seguidas, en una
copia aislada, con exactamente el mismo `motos_limpio.csv`/`siniestros_viales_victimas.csv` de entrada.
`corredores_candidatos.csv` salió **byte a byte idéntico** (mismo SHA256) en ambas corridas -- ningún
origen de no-determinismo real (no hay `random`/muestreo; el `sort_values` y el `groupby` de pandas, con
los mismos datos de entrada, dan el mismo resultado corrida tras corrida). Esto responde la parte de
"estabilidad espacial" que de verdad depende del pipeline propio: con los mismos datos de entrada, los
extremos de cada corredor (y por lo tanto su `comuna_moda`/`tipo_via_moda`/etc.) no cambian nunca entre
corridas.

### 2. La geometría que dibuja OSRM entre esos mismos extremos (paso 2, con red)

**No es estable**, ya medido con datos reales en SES-149 (A19): corriendo `fetch_corredores_geometria.py`
dos veces contra el servidor demo público de OSRM, con los **mismos 243 extremos** de entrada (confirmado
comparando `lat_a/lng_a/lat_b/lng_b` entre ambas corridas, exactamente iguales), **103 de 243 (42,4%)**
polilíneas salieron distintas -- OSRM elige caminos distintos entre los mismos dos puntos según cuándo se
le pregunte. Es un límite conocido y ya declarado del servidor demo (sin garantías de reproducibilidad,
`FICHAS_FUENTES.md`), **no un defecto del pipeline propio** -- el dato que sí es responsabilidad de este
proyecto (los extremos de cada corredor) es perfectamente estable; el que no lo es (el trazado visual
exacto entre esos extremos) depende de un tercero fuera de control del proyecto.

## Qué significa "estabilidad espacial" en la práctica, con esto medido

Separar las dos preguntas cambia la conclusión: si "estabilidad espacial" se hubiera medido solo mirando
la columna `geometria`, la conclusión habría sido "los corredores son inestables" -- engañoso, porque lo
que define un corredor como entidad de riesgo (qué calle, qué tramo, qué contexto de siniestros, dónde
empieza y termina) es 100% estable; solo el dibujo exacto de la polilínea sobre el mapa varía. Para el
modelo y para `/corredores`, lo que importa es el score de riesgo del tramo (que sale de
`cantidad_siniestros`/`mortales`/`graves`/contexto, todos estables) -- la polilínea es solo la
representación visual de "qué calle es", y aunque tome un camino ligeramente distinto entre los mismos dos
puntos, sigue identificando la misma avenida real.

## Qué no se cubrió

- No se midió la estabilidad temporal (si `motos_limpio.csv` cambia con una actualización real del dataset
  de siniestros, si los mismos corredores siguen apareciendo) -- eso es una pregunta distinta, más cercana
  a D02 (estabilidad entre años) que a esta estabilidad de pipeline con datos fijos.
- No se re-descargó la geometría de los 243 corredores una tercera vez para ver si el 42,4% de cambio se
  mantiene parejo o varía -- la medición de SES-149 ya es la evidencia real disponible, no se repitió por
  no agregar nada nuevo al hallazgo.

## Conclusión

Procedencia de `corredores_riesgo.csv` es clara y trazable a datos reales en cada columna. Estabilidad
espacial, medida por partes: los puntos que definen cada corredor son perfectamente estables entre
corridas del pipeline propio (hash idéntico, 0 variación); la polilínea exacta que dibuja OSRM entre esos
puntos no lo es (42,4% de cambio medido), pero es un límite conocido de un servicio externo, no del
pipeline del proyecto, y no afecta el score de riesgo ni la identidad del corredor.
