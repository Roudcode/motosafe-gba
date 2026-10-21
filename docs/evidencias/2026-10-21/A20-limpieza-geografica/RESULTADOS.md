# A20 — criterio de limpieza geográfica común (2026-10-21)

Desbloqueado porque el "diccionario de datos del publicador" del que dependía ya se confirmó que no
existe (`docs/datos/FICHAS_FUENTES.md`, actualización 2026-10-21) -- un límite real de la fuente, no algo
que haya que esperar.

## Qué consume realmente cada universo (revisado antes de tocar nada)

Universo de **siniestros de moto** (`data/motos_limpio.csv`): lo generan `limpiar_siniestros_motos.py`
(paso 0 del pipeline) y lo consumen `reclusterizar_hotspots.py` (hotspots de moto) e
`identificar_corredores.py` (corredores de riesgo).

Universo de **delitos de CABA** (`data/delitos_caba.csv`): lo consumen `construir_indice_inseguridad.py`
(índice por comuna) e `identificar_hotspots_inseguridad.py` (hotspots de inseguridad general/moto).

## Lo que ya existía, revisado antes de reescribir nada

`limpiar_siniestros_motos.py` (paso 0, A19/SES-112) ya limpia bastante: error de exportación de Excel,
normalización de texto, comuna, y **descarta coordenadas sin dato** -- pero no (0,0), ni fuera de GBA, ni
duplicados exactos.

`identificar_hotspots_inseguridad.py` ya tenía su propio filtro de (0,0) para `delitos_caba.csv` (comentario
real en el código: sin él, "un cluster entero... se cuela como un hotspot en el medio del Golfo de Guinea",
hallazgo de una validación cualitativa anterior) -- pero tampoco fuera de GBA ni duplicados.

`construir_indice_inseguridad.py` no filtra coordenadas (agrega por `comuna`, no por lat/lng) y no
deduplica nada.

**Conclusión antes de tocar código**: los dos universos NO usan el mismo criterio -- uno de los dos ya
excluye (0,0), el otro no; ninguno de los dos excluye fuera-de-GBA ni duplicados exactos. Esto es
exactamente lo que A20 pedía confirmar.

## Criterio común, nuevo módulo

`notebooks/limpieza_geografica_comun.py`: una función `limpiar_coordenadas(df, lat_col, lng_col, nombre)`
que aplica, en orden, y **contando cada motivo** (nunca un filtro silencioso): sin coordenadas → (0,0) →
fuera de un bounding box generoso de GBA → duplicado exacto (fila completa, conserva la primera).

## Medido contra los datos reales de hoy

### Lado siniestros de moto (`siniestros_viales_hechos.csv` → `motos_limpio.csv`)

`limpiar_siniestros_motos.py` se extendió para usar el módulo común en el mismo paso donde ya descartaba
coordenadas sin dato (no se reescribió desde cero). Corrido en una copia aislada (no sobre `data/` real) y
comparado:

```
[siniestros_viales_hechos.csv] 65817 filas de entrada -> 62787 filas limpias
  (sin_coordenadas=3030, coordenada_cero=0, fuera_de_gba=0, duplicado_exacto=0)
```

**0 filas adicionales excluidas.** El `motos_limpio.csv` resultante es **byte a byte idéntico** (mismo
SHA256) al vigente en el repo -- confirmado con `sha256sum` de ambos. El cambio a
`limpiar_siniestros_motos.py` queda aplicado en el repo (sin commitear) porque está probado que no altera
ningún dato real hoy; solo cierra la brecha para el día en que sí aparezca algún (0,0)/duplicado/absurdo en
una actualización futura del dataset.

### Lado delitos (`delitos_caba.csv`)

Medido con el módulo común directamente sobre el CSV real (sin modificar `identificar_hotspots_inseguridad.py`
ni `construir_indice_inseguridad.py` todavía -- ver por qué, abajo):

```
[delitos_caba.csv] 1387622 filas de entrada -> 1340599 filas limpias
  (sin_coordenadas=27986, coordenada_cero=6500, fuera_de_gba=12, duplicado_exacto=12525)
```

- `coordenada_cero` (6500): ya las excluye `identificar_hotspots_inseguridad.py` hoy -- confirma que ese
  filtro existente no es vacío, de verdad hace falta.
- `fuera_de_gba` (12), **nuevo, nadie lo filtra hoy**: coordenadas genuinamente rotas, no (0,0) -- algunas
  caen en otra provincia (lat/lng plausibles pero lejos de GBA), otras son errores de exportación
  evidentes (ej. longitud `5840982` o latitud `-3.459469e+17`, un número que no puede ser una coordenada).
- `duplicado_exacto` (12525 en todo el histórico), **nuevo, nadie lo filtra hoy**: filas idénticas en todas
  las columnas.

**Impacto real medido en el índice de inseguridad por comuna** (`construir_indice_inseguridad.py`, ventana
real de los últimos 3 años: 2023-2025): de los 438.073 delitos de esa ventana, **4.305 son duplicados
exactos** (~1%). Deduplicar baja el conteo crudo de cada comuna entre 0,56% y 1,79%, **sin ser parejo**
entre comunas (comuna 8: -1,79%; comuna 11: -0,56%) -- como el índice se normaliza min-max entre las 15
comunas, una diferencia no pareja puede mover levemente el orden relativo, aunque no se recalculó el CSV
final para confirmar si efectivamente cambia algún nivel de riesgo mostrado.

## Por qué no se tocó `identificar_hotspots_inseguridad.py` ni `construir_indice_inseguridad.py` todavía

A diferencia del lado de siniestros (donde el cambio resultó ser un no-op verificado), acá el criterio
común **sí cambiaría datos publicados**: `identificar_hotspots_inseguridad.py` corre HDBSCAN sobre el
dataset completo (~70 minutos documentados en el propio script -- no se volvió a correr en esta sesión) y
`construir_indice_inseguridad.py` alimenta `indice_inseguridad_comuna.csv`, que ya está promovido a
`backend/`. Cambiarlos de verdad implica reentrenar/republicar artefactos que hoy sirven producción, igual
que `promover_artefactos.py --confirmar` -- una decisión aparte, no algo para forzar sin que Rodo lo pida
(mismo criterio que ya aplicó A19 con `fetch_corredores_geometria.py`). Queda medido y cuantificado, listo
para que Rodo decida si vale la pena aplicarlo.

## Conclusión

Unificado el criterio en un módulo común, con cada exclusión contada (nunca silenciosa). Aplicado ya al
lado de siniestros (verificado sin efecto en los datos de hoy). Medido con precisión el efecto real en el
lado de delitos -- 12 coordenadas genuinamente rotas y ~12.500 duplicados exactos que hoy nadie filtra --
sin aplicarlo todavía a los scripts que generan artefactos ya publicados, porque esa aplicación es una
decisión de producto/modelo, no de limpieza de datos.
