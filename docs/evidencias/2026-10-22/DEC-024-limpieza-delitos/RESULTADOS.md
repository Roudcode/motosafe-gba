# DEC-024 — aplicar la limpieza geográfica común a delitos_caba.csv y reentrenar lo que depende de ella (2026-10-22, SES-157)

Ejecución directa de una decisión ya tomada (DEC-024 en `docs/gestion/DECISIONES.md`, confirmada en el chat
el 2026-10-22: "Sí, aplicarlo"). A diferencia de DEC-022 (D02), acá no había trade-off real: A20 ya había
medido (sin aplicar) que lo que se excluye son datos objetivamente rotos o duplicados, sin ninguna
contrapartida negativa conocida.

## Qué consume realmente `delitos_caba.csv` (confirmado leyendo el código antes de tocar nada)

Dos scripts, cada uno con su propio punto de entrada al mismo CSV:

- `notebooks/identificar_hotspots_inseguridad.py` -- ya tenía un filtro manual de `(0,0)`, pero no
  `fuera_de_gba` ni `duplicado_exacto`.
- `notebooks/construir_indice_inseguridad.py` -- no filtraba coordenadas ni deduplicaba nada (agregaba
  directo por `comuna`).

Esto ya lo había confirmado A20 (`docs/evidencias/2026-10-21/A20-limpieza-geografica/RESULTADOS.md`); no
se volvió a medir de cero, se partió de ese hallazgo.

## Qué se tocó

- **`notebooks/identificar_hotspots_inseguridad.py`**: reemplazado el filtro manual de `(0,0)` por una
  llamada a `limpiar_coordenadas()` (mismo módulo común de A20, `notebooks/limpieza_geografica_comun.py`),
  en el mismo punto donde antes filtraba a mano.
- **`notebooks/construir_indice_inseguridad.py`**: agregada la misma llamada a `limpiar_coordenadas()`
  antes de agregar por `comuna` (antes no filtraba nada).
- Ningún cambio en el criterio en sí (`limpieza_geografica_comun.py` no se tocó) -- solo se conectaron los
  dos scripts al módulo que ya existía.

## Corrida real, en `data/` (nunca se tocó `backend/` directo)

### Paso rápido: `construir_indice_inseguridad.py`

```
[delitos_caba.csv] 1387622 filas de entrada -> 1340599 filas limpias
  (sin_coordenadas=27986, coordenada_cero=6500, fuera_de_gba=12, duplicado_exacto=12525)
Ventana usada: [2023, 2024, 2025] (433768 delitos de 1340332 totales)
```

Números idénticos a los que A20 ya había medido sin aplicar -- confirma que el código nuevo reproduce
exactamente lo que se había cuantificado antes.

`data/indice_inseguridad_comuna.csv` resultante, comparado contra el vigente en `backend/`:

| comuna | índice inseguridad (vigente → candidato) | índice inseguridad moto (vigente → candidato) |
|---|---|---|
| 1 | 1.0 → 1.0 | 1.0 → 1.0 |
| 2 | 0.0 → 0.0 | 0.09 → 0.091 |
| 3 | 0.384 → 0.386 | 0.454 → 0.455 |
| 4 | 0.52 → 0.519 | 0.751 → 0.752 |
| 5 | 0.087 → 0.088 | 0.304 → 0.304 |
| 6 | 0.006 → 0.006 | 0.192 → 0.193 |
| 7 | 0.367 → 0.369 | 0.322 → 0.323 |
| 8 | 0.235 → 0.229 | 0.073 → 0.073 |
| 9 | 0.146 → 0.145 | 0.234 → 0.235 |
| 10 | 0.042 → 0.042 | 0.0 → 0.0 |
| 11 | 0.055 → 0.056 | 0.079 → 0.08 |
| 12 | 0.07 → 0.07 | 0.031 → 0.032 |
| 13 | 0.175 → 0.174 | 0.29 → 0.289 |
| 14 | 0.426 → 0.43 | 0.566 → 0.568 |
| 15 | 0.213 → 0.211 | 0.34 → 0.342 |

Cambio máximo real: 0,006 en `indice_inseguridad` (comuna 8, 0.235→0.229) y 0,002 en `indice_inseguridad_moto`.
**Ningún cambio de orden relativo entre comunas** -- el ranking de riesgo por comuna es idéntico al vigente,
solo cambian los decimales. Esperado: el conteo crudo baja 0,56%-1,79% según la comuna (ya medido en A20),
pero al normalizarse min-max entre las 15 comunas, un movimiento parejo entre todas apenas mueve la escala.

Confirmado con `notebooks/monitor_calidad_datos.py --vigente backend --candidato data`: sin hallazgos de
esquema ni de faltantes (el reporte no compara valores de `indice_inseguridad_comuna.csv` directamente,
solo esquema/faltantes/geo -- la comparación de valores de arriba se hizo a mano, con `diff` real contra el
CSV vigente).

### Paso lento: `identificar_hotspots_inseguridad.py` (HDBSCAN, ~70 min reales)

```
[delitos_caba.csv] 1387622 filas de entrada -> 1340599 filas limpias
  (sin_coordenadas=27986, coordenada_cero=6500, fuera_de_gba=12, duplicado_exacto=12525)
Ventana usada: [2023, 2024, 2025] (433808 delitos con coordenadas)
GENERAL (HDBSCAN): puede tardar bastante sobre el dataset completo (~70 min en la confirmacion previa) -- no es que se colgo.
[GENERAL] 619 hotspots, 200291 aislados de 403993 (49.6%)
[MOTO] 502 hotspots, 4050 aislados de 15745 (25.7%)
Guardado: 619 hotspots generales, 502 hotspots de robos con moto
```

(La ventana de esta corrida, 433.808, difiere levemente de la del índice, 433.768 -- distinto filtro previo:
`construir_indice_inseguridad.py` descarta antes las filas sin `comuna`, `identificar_hotspots_inseguridad.py`
no necesita `comuna` para clusterizar. Diferencia esperada entre los dos scripts, no un error.)

Comparado contra lo que había en `data/` antes de este cambio (copiado a este mismo directorio de evidencia
como `*_antes.csv`):

| | Antes (sin limpieza) | Después (DEC-024) | Cobertura |
|---|---|---|---|
| GENERAL | 633 hotspots | **619 hotspots** (-14, -2,2%) | 50,2% → 49,6%* |
| MOTO | 502 hotspots | **502 hotspots** (mismo total) | 74,3% → 74,3% |

\*La cobertura de GENERAL se calcula sobre el total de delitos de la ventana, que también bajó (duplicados
y filas rotas excluidas) -- el pequeño cambio de 50,2% a 49,6% es consistente con eso, no un cambio de
metodología.

`diff` línea por línea contra el `_antes.csv`: GENERAL cambia en 1254 líneas (de 634, la mayoría por
pequeños corrimientos de `cantidad_delitos`/coordenadas de centroide al perder algunos duplicados de cada
cluster), MOTO en 158 líneas de 503 -- cambios chicos y acotados (ej. un cluster que tenía 63 casos pasa a
62, otro de 39 pasa a 38), no una reestructuración del mapa de hotspots. Ningún cluster nuevo aparece de la
nada ni desaparece un hotspot grande -- el efecto es justamente el esperado de sacar duplicados exactos y
un puñado de coordenadas rotas, no un cambio de metodología.

## Qué queda en `data/`, listo para que Rodo decida la promoción

- `data/indice_inseguridad_comuna.csv` -- nuevo, con la limpieza aplicada. **No promovido** a `backend/`
  (eso requiere `notebooks/promover_artefactos.py --confirmar`, no corrido en esta sesión).
- `data/hotspots_inseguridad_general.csv` / `data/hotspots_inseguridad_moto.csv` -- nuevos, con la limpieza
  aplicada. Estos no pasan por `promover_artefactos.py` (no están en su lista `ARTEFACTOS`) -- se cargan
  directo a la base real con `backend/cargar_hotspots_inseguridad.py`, que **tampoco se corrió** en esta
  sesión. La tabla `hotspots_inseguridad` de la base real sigue con los datos de antes hasta que alguien
  corra ese script a propósito.

## Verificación

- Conteos de exclusión idénticos entre esta corrida y la medición previa de A20 (sin aplicar) -- confirma
  que el código nuevo no introdujo ninguna diferencia de criterio.
- `indice_inseguridad_comuna.csv`: sin cambios de orden relativo entre comunas, cambio máximo 0,006 en el
  índice normalizado.
- `hotspots_inseguridad_{general,moto}.csv`: cambios acotados y explicables enteramente por las exclusiones
  medidas (ninguna reestructuración de clusters).
- `monitor_calidad_datos.py --vigente backend --candidato data`: sin hallazgos de esquema/faltantes nuevos
  más allá de lo esperado.
- Tests de Python no aplica (estos notebooks no tienen suite propia, igual que el resto del pipeline de
  modelo/datos -- se verifican por reproducción real, como ya es el criterio establecido para A19/A20).

## Qué no se hizo (a propósito, por instrucción explícita)

- **No se corrió `promover_artefactos.py --confirmar`**: `data/indice_inseguridad_comuna.csv` queda
  generado y verificado, pero `backend/indice_inseguridad_comuna.csv` sigue siendo el de antes.
- **No se corrió `cargar_hotspots_inseguridad.py`**: la tabla `hotspots_inseguridad` de la base real no se
  tocó.
- No se sobrescribió nada directamente en `backend/`.

Rodo decide el momento de promover con los números reales de esta ficha como referencia.
