# A22 — Versión de scikit-learn del modelo frente al entorno (SES-066)

Fecha: 2026-10-05. Sesión: SES-066 (Claude Code, máquina de Rodo).

## Hallazgo

| Dónde | scikit-learn |
|---|---|
| `modelo_final.pkl` vigente (SES-065, commit `65d40dd`), leído de `_sklearn_version` en los bytes del pickle | 1.7.2 |
| `modelo_final.pkl` anterior (commit `c15e53e`) | 1.5.2 |
| `requirements.txt` raíz (usado por el README para instalar el backend) | `==1.5.2` |
| `backend/requirements.txt` (Dockerfile) | `>=1.5,<2`, sin versión exacta |
| `backend/venv312` local | 1.9.1 |

Tres versiones distintas convivían: la de entrenamiento, la declarada y la instalada. Cada carga del modelo emitía `InconsistentVersionWarning`. El README ya registraba el mismo problema el 07/09; se había corregido reentrenando y volvió con SES-065, que entrenó en otro entorno.

Otro hallazgo: `backend/.dockerignore` excluía `venv/` pero no `venv312/`, así que `COPY . ./` del Dockerfile metía el venv de Windows en la imagen.

## Comparación de predicciones 1.7.2 frente a 1.9.1

`comparar_versiones_sklearn.py` recorre la población de referencia de `notebooks/calibrar_umbrales_riesgo.py` (740 hotspots y 243 corredores en 336 escenarios de hora, día y lluvia) con el mismo modelo, numpy 2.5.3 y pandas 2.3.3, cambiando solo scikit-learn. Resultado en `resultado_comparacion.txt`:

- 248.640 predicciones de hotspots y 81.648 de corredores.
- Diferencia máxima de probabilidad: 4,4·10⁻¹⁶ (redondeo de punto flotante); no son idénticas bit a bit.
- 0 filas cambian de clase más probable y 0 filas cambian de nivel bajo/medio/alto/crítico contra los cortes de `main.py`.
- Con 1.7.2 los percentiles reproducen exactamente `UMBRALES_HOTSPOTS`/`UMBRALES_CORREDORES`. Con 1.9.1 el p75 de corredores difiere en el último decimal (`…744` frente a `…745`).

Conclusión: hoy 1.9.1 no cambia nada visible, pero eso se comprobó para esta combinación y no se puede asumir para versiones futuras. La versión de entrenamiento queda fijada.

## Cambios

- `backend/requirements.txt` con versiones exactas, `scikit-learn==1.7.2`.
- `requirements.txt` raíz incluye el del backend.
- Test `backend/tests/test_entorno.py`.
- Campo `version_sklearn_coincide` en `/health`.
- Control previo en `notebooks/reentrenar_modelo.py`.
- `venv*/` en `.dockerignore`.
- pytest en CI.
- Guía en `docs/operacion/ENTORNO_REPRODUCIBLE.md`.

## Verificación

- `venv312` (1.9.1): 80 tests aprobados; `/health` informa `version_sklearn_coincide: false`. El control de reentrenamiento se niega a correr.
- Venv nuevo con Python 3.12.10 desde `backend/requirements.txt`: `pip check` sin conflictos y 80 tests aprobados, sin `InconsistentVersionWarning`. Con el `requirements.txt` raíz se instalan e importan geopandas 1.0.1, matplotlib 3.9.2 y xgboost 2.1.1 con numpy 2.5.3.
- Imagen Docker del backend (`python:3.12-slim`): construida con las versiones fijadas, sin `venv312` dentro; 80 tests aprobados en Linux montando `tests/`.
- No se reentrenó el modelo ni se modificaron artefactos.

## Reproducir

```
<python con sklearn 1.7.2> comparar_versiones_sklearn.py generar a.npz
<python con sklearn 1.9.1> comparar_versiones_sklearn.py generar b.npz
python comparar_versiones_sklearn.py comparar a.npz b.npz
```
