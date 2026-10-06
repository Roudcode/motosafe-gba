# A19 — Pipeline canónico y notebook histórico seguro (SES-077)

Fecha: 2026-10-06.

## Problema (assessment A19)

- El notebook `01_eda_hotspots_moto.ipynb` escribe con nombres fijos en `data/`: `motos_limpio`, `motos_con_clusters`, `hotspots_moto_caba` (clustering DBSCAN viejo), `modelo_final` y `hotspots_contexto`. Con «Run All» podía reemplazar artefactos vigentes por versiones antiguas.
- `reentrenar_modelo.py` copiaba directo a `backend/`, sin ningún paso de promoción.

## Cambios

1. **Guarda en el notebook:** una celda de aviso y otra de código al principio. Desvían `DataFrame.to_csv` y `joblib.dump` dirigidos a `data/` o `backend/` hacia `data/exploracion_notebook/`, que Git ignora. Se probó ejecutando el código de la celda desde `notebooks/`:
   - las escrituras a `data/hotspots_moto_caba.csv` y `backend/modelo_final.pkl` terminaron en `data/exploracion_notebook/`;
   - una escritura fuera de esas carpetas no se desvió;
   - re-ejecutar la celda no la envuelve dos veces;
   - los SHA256 de los vigentes no cambiaron.
2. **`reentrenar_modelo.py`** deja los candidatos en `data/` y ya no copia a `backend/`.
3. **`notebooks/promover_artefactos.py`:** muestra el manifiesto (SHA256 y fecha, vigente contra candidato). Con `--confirmar` copia lo que difiere, después de verificar que el modelo candidato use la versión de scikit-learn declarada.
4. **Orden canónico** en `docs/modelo/PIPELINE_CANONICO.md`.

## Prueba desde cero en una copia de trabajo

- Copia: clon limpio del repo en el scratchpad, con los scripts actuales y solo los **datos crudos** (`motos_limpio.csv`, `siniestros_viales_victimas.csv`, `clima_historico.csv`, `delitos_caba.csv`). Entorno: venv instalado desde `requirements.lock` (scikit-learn 1.7.2).
- Se corrieron en orden `construir_indice_inseguridad`, `reclusterizar_hotspots`, `reentrenar_modelo`, `identificar_corredores` e `identificar_hotspots_inseguridad`. El resultado está en `resultado_comparacion.txt`.
- **Los hashes de bytes dieron distintos, pero el contenido es idéntico.** En Windows, pandas escribe los CSV con CRLF y Git convierte fines de línea, así que el SHA256 no sirve para comparar. Se compararon con `comparar_contenido.py`:
  - CSV celda por celda;
  - modelo árbol por árbol: estructura, umbrales y valores de los 300 árboles.

| Artefacto | Resultado |
|---|---|
| `indice_inseguridad_comuna.csv` | mismo contenido |
| `motos_con_clusters.csv` | mismo contenido |
| `hotspots_moto_caba.csv` | mismo contenido |
| `hotspots_contexto.csv` | mismo contenido |
| `corredores_candidatos.csv` | mismo contenido |
| `modelo_final.pkl` | 300 árboles, 0 distintos: el mismo modelo |
| `hotspots_inseguridad_*.csv` | ver `resultado_comparacion.txt` |

- El `backend/` de la copia no cambió durante la corrida (verificado con `sha256sum -c`): reentrenar ya no publica solo.

## Límites

- `motos_limpio.csv` (paso 0) sale de la limpieza del notebook histórico y se usó como entrada congelada. Falta un script canónico de limpieza.
- No se corrieron los pasos con red (`fetch_*`, geometría de corredores por OSRM).
- El manifiesto de `promover_artefactos.py` normaliza los fines de línea de los CSV: con ese cambio, los CSV regenerados en la copia dan el mismo SHA256 que los vigentes. El pickle del modelo regenerado sigue difiriendo en bytes aunque los 300 árboles sean idénticos, así que aparece como «DIFIERE». Es deliberadamente conservador: antes de `--confirmar`, comparar con `comparar_contenido.py`.
