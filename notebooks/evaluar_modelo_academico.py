"""Evaluación temporal reproducible del modelo de gravedad, sin modificar producción.

Ejemplo:
  python notebooks/evaluar_modelo_academico.py --selection-year 2023 --test-year 2024 --output docs/evidencias/2026-09-13/A01-A04
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, classification_report, confusion_matrix, f1_score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CATEGORICAS = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
NUMERICAS = ["hora", "edad_victima", "edad_desconocida", "temperatura", "humedad"]


def cargar_base() -> pd.DataFrame:
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    motos["contraparte_siniestro"] = motos["contraparte_siniestro"].str.strip().str.upper()
    motos["tipo_de_via_siniestro"] = motos["tipo_de_via_siniestro"].str.strip().str.upper()
    fecha = pd.to_datetime(motos["fecha_siniestro"], errors="coerce")
    motos["anio_siniestro"] = fecha.dt.year
    motos["dia_semana"] = fecha.dt.day_name()
    motos["hora"] = pd.to_datetime(motos["hora_siniestro"], format="%H:%M:%S", errors="coerce").dt.hour
    motos = motos.dropna(subset=["hora", "anio_siniestro"]).copy()

    victimas = pd.read_csv(DATA / "siniestros_viales_victimas.csv", encoding="utf-8-sig", sep=";", low_memory=False)
    victimas["modo_desplazamiento_victima"] = victimas["modo_desplazamiento_victima"].str.strip().str.upper()
    victimas["sexo_victima"] = victimas["sexo_victima"].str.strip().str.upper()
    victimas = victimas[victimas["modo_desplazamiento_victima"] == "MOTO"].copy()
    victimas["edad_victima"] = pd.to_numeric(victimas["edad_victima"], errors="coerce")
    resumen = victimas.groupby("id_siniestro").agg(
        edad_victima=("edad_victima", "mean"),
        sexo_victima=("sexo_victima", lambda x: x.mode().iloc[0] if not x.mode().empty else "SD"),
    ).reset_index()
    base = motos.merge(resumen, on="id_siniestro", how="left")
    base.loc[(base["edad_victima"] < 14) | (base["edad_victima"] > 95), "edad_victima"] = np.nan
    base["edad_desconocida"] = base["edad_victima"].isna().astype(int)
    base["sexo_victima"] = base["sexo_victima"].fillna("SD")
    base["comuna"] = base["comuna"].astype("Int64").astype(str)
    base["fecha_siniestro_str"] = pd.to_datetime(base["fecha_siniestro"], errors="coerce").dt.date.astype(str)

    clima = pd.read_csv(DATA / "clima_historico.csv")
    clima["fecha"] = clima["fecha"].astype(str)
    base = base.merge(clima, left_on=["fecha_siniestro_str", "hora"], right_on=["fecha", "hora"], how="left")
    base = base.dropna(subset=["precipitacion", "temperatura", "humedad"]).copy()
    base["lluvia"] = np.where(base["precipitacion"] > 0.1, "SI", "NO")
    return base


def preparar(train: pd.DataFrame, objetivo: pd.DataFrame, columnas: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    train = train.copy(); objetivo = objetivo.copy()
    if "edad_victima" in columnas:
        mediana = train["edad_victima"].median()
        train["edad_victima"] = train["edad_victima"].fillna(mediana)
        objetivo["edad_victima"] = objetivo["edad_victima"].fillna(mediana)
    cat = [c for c in CATEGORICAS if c in columnas]
    x_train = pd.get_dummies(train[columnas], columns=cat, dtype=float)
    x_objetivo = pd.get_dummies(objetivo[columnas], columns=cat, dtype=float).reindex(columns=x_train.columns, fill_value=0)
    return x_train, x_objetivo


def ece(y: np.ndarray, probas: np.ndarray, clases: np.ndarray, bins: int = 10) -> float:
    total = 0.0
    for indice, clase in enumerate(clases):
        observado = (y == clase).astype(float)
        for grupo in np.array_split(np.argsort(probas[:, indice]), bins):
            if len(grupo):
                total += len(grupo) / (len(y) * len(clases)) * abs(observado[grupo].mean() - probas[grupo, indice].mean())
    return float(total)


def intervalo_f1(y: np.ndarray, pred: np.ndarray, repeticiones: int = 300) -> list[float]:
    """Intervalo bootstrap descriptivo; no convierte el resultado en inferencia causal."""
    rng = np.random.default_rng(42)
    muestras = []
    for _ in range(repeticiones):
        indice = rng.integers(0, len(y), len(y))
        muestras.append(f1_score(y[indice], pred[indice], average="macro", zero_division=0))
    return [float(x) for x in np.quantile(muestras, [0.025, 0.975])]


def medir(nombre: str, train: pd.DataFrame, validacion: pd.DataFrame, test: pd.DataFrame, columnas: list[str]) -> dict:
    x_train, x_val = preparar(train, validacion, columnas)
    _, x_test = preparar(train, test, columnas)
    modelo = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1)
    modelo.fit(x_train, train["gravedad_siniestro"])
    pred_val = modelo.predict(x_val)
    pred_test = modelo.predict(x_test)
    probas = modelo.predict_proba(x_test)
    clases = modelo.classes_
    y_test = test["gravedad_siniestro"].to_numpy()
    brier = {str(c): float(brier_score_loss((y_test == c).astype(int), probas[:, i])) for i, c in enumerate(clases)}
    grupos_faltante = {}
    for etiqueta, grupo in test.groupby("edad_desconocida"):
        # pred_test conserva el orden de test; se localiza con una máscara de posición.
        posiciones = np.flatnonzero(test["edad_desconocida"].to_numpy() == etiqueta)
        grupos_faltante[str(int(etiqueta))] = {
            "filas": int(len(grupo)),
            "f1_macro": float(f1_score(y_test[posiciones], pred_test[posiciones], average="macro", zero_division=0)),
        }
    return {
        "variante": nombre,
        "columnas": columnas,
        "f1_macro_seleccion": float(f1_score(validacion["gravedad_siniestro"], pred_val, average="macro", zero_division=0)),
        "f1_macro_evaluacion": float(f1_score(y_test, pred_test, average="macro", zero_division=0)),
        "reporte_evaluacion": classification_report(y_test, pred_test, output_dict=True, zero_division=0),
        "matriz_confusion": confusion_matrix(y_test, pred_test, labels=clases).tolist(),
        "clases": [str(c) for c in clases], "brier_por_clase": brier, "ece_multiclase": ece(y_test, probas, clases),
        "intervalo_bootstrap_f1_macro_95": intervalo_f1(y_test, pred_test),
        "metricas_por_edad_desconocida": grupos_faltante,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selection-year", type=int, required=True)
    parser.add_argument("--test-year", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.selection_year >= args.test_year:
        raise SystemExit("selection-year debe ser anterior a test-year")
    base = cargar_base()
    train = base[base.anio_siniestro < args.selection_year].copy()
    validacion = base[base.anio_siniestro == args.selection_year].copy()
    test = base[base.anio_siniestro == args.test_year].copy()
    if min(len(train), len(validacion), len(test)) == 0:
        raise SystemExit("No hay filas para una de las particiones temporales solicitadas")
    base_cols = NUMERICAS + CATEGORICAS
    variantes = {
        "base": base_cols,
        "sin_edad": [c for c in base_cols if c not in {"edad_victima", "edad_desconocida"}],
        "sin_demografia": [c for c in base_cols if c not in {"edad_victima", "edad_desconocida", "sexo_victima"}],
    }
    resultados = [medir(nombre, train, validacion, test, columnas) for nombre, columnas in variantes.items()]
    salida = {
        "protocolo": {"train_hasta": args.selection_year - 1, "seleccion": args.selection_year, "evaluacion_independiente": args.test_year,
            "indice_inseguridad": "excluido: no hay version temporalmente fechada"},
        "filas": {"train": len(train), "seleccion": len(validacion), "evaluacion": len(test)},
        "faltantes": {"edad_train": float(train.edad_desconocida.mean()), "edad_seleccion": float(validacion.edad_desconocida.mean()), "edad_evaluacion": float(test.edad_desconocida.mean())},
        "resultados": resultados,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "reporte_modelo_temporal.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame([{k: r[k] for k in ("variante", "f1_macro_seleccion", "f1_macro_evaluacion", "ece_multiclase")} for r in resultados]).to_csv(args.output / "resumen_modelo_temporal.csv", index=False)
    print(json.dumps(salida["filas"], ensure_ascii=False)); print(f"Evidencia escrita en {args.output}")


if __name__ == "__main__":
    main()
