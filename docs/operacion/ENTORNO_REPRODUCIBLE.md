# Entorno reproducible y artefactos del modelo (A22)

Actualizado: 2026-10-05 (SES-066). Evidencia: [docs/evidencias/2026-10-05/A22-entorno/](../evidencias/2026-10-05/A22-entorno/README.md).

## Regla

La API sirve un modelo serializado con `joblib` (`backend/modelo_final.pkl`). scikit-learn no garantiza que un pickle cargue igual en otra versión. Por eso:

1. `backend/requirements.txt` fija **versiones exactas** (`==`) de las dependencias directas y es el archivo que se edita a mano. `backend/requirements.lock` fija además todas las transitivas, con hashes SHA256, y es lo que instalan el Dockerfile, el CI y `backend\_iniciar_backend.bat` (`pip install --require-hashes -r requirements.lock`). Desde SES-068.
2. La versión de `scikit-learn` declarada ahí tiene que ser **la misma con la que se guardó el modelo**. `backend/tests/test_entorno.py` lee la versión del propio pickle y falla si no coincide.
3. `requirements.txt` de la raíz incluye el del backend y agrega solo dependencias de notebooks. Reentrenar o recalibrar usa la misma versión que sirve la API.
4. `notebooks/reentrenar_modelo.py` se niega a entrenar si el scikit-learn instalado no es el declarado.
5. `/health` devuelve `version_sklearn_coincide`: `false` significa que el servidor cargó el modelo con otra versión. El detalle de versiones sale solo en la consola al arrancar, no en la respuesta pública.

## Instalación limpia

Python 3.12 (el mismo que la imagen `python:3.12-slim`). Desde la raíz del repositorio, en Windows:

```
py -3.12 -m venv backend\venv312
backend\venv312\Scripts\activate
pip install --require-hashes -r requirements.lock
cd backend
python -m pytest -q
```

`backend\venv312` es el nombre que esperan `iniciar.bat`, `iniciar_app.bat`, `tareas.bat` y `backend\_iniciar_backend.bat`. Para solo la API alcanza `pip install --require-hashes -r backend/requirements.lock`. Los prototipos de clustering (`notebooks/prototipo_*.py`) necesitan además `pip install -r notebooks/requirements-prototipos.txt` (h3, folium, libpysal, esda).

### Regenerar los locks

Después de cambiar `backend/requirements.txt` o `requirements.txt`, con [uv](https://docs.astral.sh/uv/) en cualquier entorno de herramientas:

```
uv pip compile --universal --python-version 3.12 --generate-hashes --no-header backend/requirements.txt -o backend/requirements.lock
uv pip compile --universal --python-version 3.12 --generate-hashes --no-header requirements.txt -o requirements.lock
```

`--universal` resuelve para Windows y Linux a la vez (por ejemplo `colorama` en Windows y `uvloop` en Linux, ambos dependencias de `uvicorn[standard]`). `tests/test_entorno.py` falla si el lock del backend no coincide con las versiones directas o si algún paquete no tiene hash.

Verificado el 2026-10-05 en un venv nuevo con Python 3.12.10: `pip check` sin conflictos, 80 tests aprobados y sin `InconsistentVersionWarning`. La imagen Docker del backend, construida con las mismas versiones, también aprobó los 80 tests en Linux.

## Artefactos vigentes

| Archivo (`backend/`) | SHA256 | Origen |
|---|---|---|
| `modelo_final.pkl` | `d89d873df7695247f8138c26271918fff3bb80bc6a6c7a925b8829aabae0de7b` | `notebooks/reentrenar_modelo.py`, scikit-learn 1.7.2, commit `65d40dd` (SES-065) |
| `columnas_modelo.pkl` | `cb75764d39819bf973720ef977ec69242dc4b8aef7e32e0f7784ffe445c8a1a3` | mismo script, 53 columnas |
| `hotspots_contexto.csv` | `e00889a88fba62193845ff67e9a1b53facdfb757aa0d6de3af34cbf1232b8ebf` | mismo script |
| `indice_inseguridad_comuna.csv` | `98511c694160012bdf6f7be9e93226114d499d7e5cda821e8bdd010cbea0f4f6` | `notebooks/construir_indice_inseguridad.py` |

Los umbrales `UMBRALES_HOTSPOTS`/`UMBRALES_CORREDORES` de `backend/main.py` se reproducen exactamente con scikit-learn 1.7.2 corriendo `notebooks/calibrar_umbrales_riesgo.py` sobre estos artefactos. `_HUELLA_UMBRALES_CALIBRADOS` cubre los tres archivos de riesgo; esta tabla agrega `columnas_modelo.pkl` y la versión.

## Cambiar una versión o reentrenar

1. Editar `backend/requirements.txt` y crear un venv nuevo con él. No actualizar un venv existente para probar.
2. Si cambia scikit-learn: reentrenar con `notebooks/reentrenar_modelo.py` en ese venv, recalibrar umbrales con `notebooks/calibrar_umbrales_riesgo.py` y pegar valores y huella en `main.py`.
3. Correr `python -m pytest -q` en `backend/` y actualizar la tabla de hashes de arriba.
4. Para comparar predicciones entre dos versiones sin reentrenar: `docs/evidencias/2026-10-05/A22-entorno/comparar_versiones_sklearn.py`.

## Límites conocidos

- `notebooks/requirements-prototipos.txt` no tiene lock: son prototipos exploratorios. Se verificó corriendo `prototipo_gi_kde_hotspots.py` completo y comprobando las funciones h3 v4 de `prototipo_h3_hotspots.py`; este último no se ejecutó porque escribe archivos `_h3_preview` en `data/`.
- `geopandas` pasó de 1.0.1 a 1.2.0 porque libpysal 4.15 exige `>=1.1`; ningún script del repositorio lo importa. `seaborn` y `requests`, usados por el notebook histórico, quedaron declarados. No se ejecutó el notebook histórico.
