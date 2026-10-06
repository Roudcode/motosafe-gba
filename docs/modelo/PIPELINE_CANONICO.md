# Pipeline canónico de datos, modelo y capas (A19)

Actualizado: 2026-10-06 (SES-077). Evidencia: [docs/evidencias/2026-10-06/A19-pipeline/](../evidencias/2026-10-06/A19-pipeline/README.md).

## Reglas

1. **El notebook `01_eda_hotspots_moto.ipynb` es exploración histórica.** Su primera celda de código desvía cualquier `to_csv`/`joblib.dump` hacia `data/` o `backend/` a `data/exploracion_notebook/`, así que «Run All» no puede pisar artefactos vigentes. No forma parte del pipeline.
2. **El pipeline son scripts no interactivos** en `notebooks/`, corridos en el orden de abajo con el entorno de `requirements.lock`, que fija scikit-learn igual que el modelo.
3. **Los scripts escriben candidatos en `data/`. Nada se publica solo.** `notebooks/promover_artefactos.py` muestra el manifiesto (SHA256 vigente contra candidato) y solo copia a `backend/` con `--confirmar`.

## Orden

| Paso | Script | Entrada | Salida (en `data/`) | Red |
|---|---|---|---|---|
| 0 | (notebook histórico, sección 1) | `siniestros_viales_hechos.csv`, `siniestros_viales_victimas.csv` | `motos_limpio.csv` | No |
| 1 | `fetch_delitos_caba.py` | Buenos Aires Data | `delitos_caba.csv` | Sí |
| 2 | `fetch_clima_historico.py` | Open-Meteo | `clima_historico.csv` | Sí |
| 3 | `construir_indice_inseguridad.py` | `delitos_caba.csv` | `indice_inseguridad_comuna.csv` | No |
| 4 | `identificar_hotspots_inseguridad.py` | `delitos_caba.csv` | `hotspots_inseguridad_general.csv`, `hotspots_inseguridad_moto.csv` | No |
| 5 | `reclusterizar_hotspots.py` | `motos_limpio.csv` | `motos_con_clusters.csv`, `hotspots_moto_caba.csv` | No |
| 6 | `identificar_corredores.py` | `motos_limpio.csv`, `siniestros_viales_victimas.csv` | `corredores_candidatos.csv` | No |
| 7 | `fetch_corredores_geometria.py` | `corredores_candidatos.csv` | `corredores_riesgo.csv` | Sí (OSRM público) |
| 8 | `reentrenar_modelo.py` | `motos_limpio.csv`, `motos_con_clusters.csv`, `clima_historico.csv`, `indice_inseguridad_comuna.csv` | `modelo_final.pkl`, `columnas_modelo.pkl`, `hotspots_contexto.csv` | No |
| 9 | `promover_artefactos.py`, después `--confirmar` | candidatos de `data/` | `backend/` (modelo, columnas, contexto, índice) | No |
| 10 | `calibrar_umbrales_riesgo.py` | artefactos de `backend/` | umbrales y huella para pegar en `backend/main.py` | No |
| 11 | `generar_metadatos_capas.py` | `motos_limpio.csv`, `delitos_caba.csv` | `backend/metadatos_capas.json` | No |
| 12 | `cargar_hotspots.py`, `cargar_corredores.py`, `cargar_hotspots_inseguridad.py` | CSV de capas | tablas de la base (recarga) | No |

En los pasos 4, 5 y 7 los CSV de capas quedan en `data/` y se versionan (SES-076). La API los toma de la base: en una base nueva los carga `cargar_datos_iniciales.py`, y en una existente se recargan con el paso 12.

## Límites

- **El paso 0 no tiene script.** `motos_limpio.csv` sale de la sección de limpieza del notebook histórico, que según el assessment no corre de punta a punta. Se trata como entrada congelada (hash en la evidencia). Escribir un script canónico de limpieza queda pendiente.
- Los pasos 1, 2 y 7 dependen de servicios externos y pueden devolver datos distintos con el tiempo.
