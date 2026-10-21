# D05 — monitor de cambios en calidad de datos (2026-10-21)

Desbloqueado: A20 (`notebooks/limpieza_geografica_comun.py`, SES-151) y A22 (entorno reproducible) ya
estaban cerrados. El pipeline canónico ya separa candidatos en `data/` de lo publicado en `backend/` --
`promover_artefactos.py --confirmar` es el único paso que publica. D05 agrega un chequeo de calidad que
corre **antes** de esa decisión, nunca en lugar de ella.

## Qué hace, y qué NO hace

`notebooks/monitor_calidad_datos.py --vigente <carpeta> --candidato <carpeta>` compara los archivos
conocidos presentes en ambas carpetas y reporta tres cosas, siempre con números reales:

1. **Esquema**: columnas nuevas/desaparecidas y cambios de tipo en cada CSV; features nuevas/desaparecidas
   en `columnas_modelo.pkl` (el esquema que espera el modelo).
2. **Faltantes**: por columna, si la proporción de nulos cambió ≥5 puntos porcentuales.
3. **Limpieza geográfica** (reusa `limpieza_geografica_comun.py` de A20): para `motos_limpio.csv` y
   `delitos_caba.csv`, si la proporción de coordenada_cero/fuera_de_gba/duplicado_exacto saltó ≥1 punto
   porcentual **o** ≥100 filas en términos absolutos (ver "hallazgo real" abajo -- el umbral solo
   porcentual no alcanza en datasets grandes).

**Es solo un reporte.** No se invoca desde `promover_artefactos.py` ni desde ningún paso automático; no
bloquea nada; la decisión de correr `--confirmar` sigue siendo de Rodo, como pidió explícitamente.

## Ensayo 1 — datos reales de hoy, pipeline regenerado, se espera "sin cambios relevantes"

Se regeneró de verdad `motos_limpio.csv` (con `limpiar_siniestros_motos.py`, el mismo real de A20) y se
reusó el `delitos_caba.csv` real re-descargado en A19 (SES-149) -- ambos en una copia de trabajo aislada,
comparados contra los archivos reales de hoy (`data/motos_limpio.csv`, `backend/hotspots_contexto.csv`,
`backend/indice_inseguridad_comuna.csv`, `backend/columnas_modelo.pkl`, y un `delitos_caba.csv` de
referencia):

```
[motos_limpio.csv (vigente)] 23343 filas -> 23343 limpias (sin_coordenadas=0, coordenada_cero=0, fuera_de_gba=0, duplicado_exacto=0)
[motos_limpio.csv (candidato)] 23343 filas -> 23343 limpias (sin_coordenadas=0, coordenada_cero=0, fuera_de_gba=0, duplicado_exacto=0)
[delitos_caba.csv (vigente)] 1387622 filas -> 1340599 limpias (...)
[delitos_caba.csv (candidato)] 1387622 filas -> 1340599 limpias (idéntico)

Sin cambios relevantes.
```

**Confirmado**: con datos reales, regenerados de verdad, el monitor da exactamente "Sin cambios
relevantes", tal como se esperaba.

Nota aparte, honesta: al comparar `backend/` (vigente) contra `data/` (candidato) tal cual hoy -- la
comparación que de verdad importa antes de un `--confirmar` real -- el monitor marca `motos_limpio.csv` y
`delitos_caba.csv` como "solo existe en candidato". Es correcto (esos dos archivos son intermedios del
pipeline, nunca viven en `backend/`), pero hace que el reporte nunca diga "sin cambios relevantes" al
100% en esa comparación particular -- es ruido estructural, no un hallazgo real, y queda declarado en vez
de disimulado.

## Ensayo 2 — candidato alterado a propósito, se espera que el monitor lo detecte

Se armó un `delitos_caba.csv` alterado a mano sobre la copia regenerada real: se le sacó la columna
`comuna`, se vaciaron a propósito el 10% de los valores de `tipo_delito`, y se pusieron 3000 coordenadas
reales en `(0,0)` (antes tenían lat/lng reales). Corrido contra el mismo "vigente" del ensayo 1:

```
[delitos_caba.csv] ESQUEMA distinto:
  columnas desaparecidas: ['comuna']
[delitos_caba.csv] FALTANTES cambiaron >= 5.0 pp:
  'tipo_delito': 0.0% -> 10.0% (+10.0 pp)
[delitos_caba.csv] LIMPIEZA GEOGRAFICA, saltos >= 1.0 pp o >= 100 filas:
  coordenada_cero: 0.468% -> 0.684% (+0.215 pp, +2985 filas)
  duplicado_exacto: 0.903% -> 0.758% (-0.145 pp, -2013 filas)

Hay cambios para revisar antes de promover...
```

**Las tres alteraciones se detectaron**, con números reales y descriptivos (qué columna, cuánto cambiaron
los faltantes, cuántas filas de más/menos en cada motivo geográfico).

### Hallazgo real durante el propio ensayo (corregido en el momento)

La primera versión del script usaba solo un umbral porcentual (1 punto porcentual) para el salto
geográfico. Con las 3000 coordenadas inyectadas en `(0,0)`, el salto real fue de solo **+0,215 puntos
porcentuales** sobre 1,39 millones de filas -- **por debajo del umbral y sin reportarse**, pese a ser 3000
filas reales con un problema real. Corregido agregando un segundo criterio (≥100 filas de diferencia
absoluta, además del umbral porcentual): con eso, el salto de +2985 filas se detecta aunque sea chico en
porcentaje. Esto es exactamente el tipo de cosa que D05 pedía evitar -- un filtro que "parece" seguro pero
no lo es en la práctica, medido y corregido antes de cerrar la sesión, no dejado como está.

También se observó, de forma secundaria, que `duplicado_exacto` bajó (-2013 filas): esperable, porque
`coordenada_cero` se excluye ANTES que `duplicado_exacto` en `limpieza_geografica_comun.py` -- varias de
las 3000 filas alteradas habrían contado como duplicados entre sí si no hubieran sido excluidas primero
por ser (0,0). No es un error del monitor, es el orden de exclusión correcto (A20) reflejándose en el
reporte.

## Qué no se cubrió

- No se probó con un candidato de `hotspots_contexto.csv`/`indice_inseguridad_comuna.csv`/
  `columnas_modelo.pkl` alterado a propósito (solo se alteró `delitos_caba.csv`) -- el mecanismo de
  comparación es el mismo código para los tres, así que no se consideró necesario repetir el ensayo en
  cada archivo.
- `modelo_final.pkl` no se compara en absoluto (es un modelo completo, no un esquema comparable fila a
  fila) -- fuera de alcance de D05, que pide esquema/faltantes/geografía, no equivalencia de modelos.

## Conclusión

El monitor corre antes de la promoción, nunca la bloquea, y reporta con números reales tanto el caso "sin
cambios" (verificado con datos reales regenerados) como el caso "hay cambios" (verificado con un candidato
alterado a propósito, incluida una corrección real hecha en el momento sobre un umbral que no alcanzaba).
Queda en `notebooks/monitor_calidad_datos.py`, sin invocarse desde ningún paso automático.
