"""
D02 -- aislar la causa de la inestabilidad temporal entre splits.

Evidencia previa (docs/evidencias/2026-10-18/D02-estabilidad/README.md) ya
midio que F1 macro evaluacion difiere entre 2023->2024 (0,2859) y 2024->2025
(0,3689), con intervalos de confianza que no se superponen, y nombro tres
hipotesis sin descartar ninguna: composicion de siniestros, cambio real de
patron, o el tamano de entrenamiento mas grande del segundo split
(15.559 contra 11.644 filas).

Este script ataca las dos hipotesis mas baratas de chequear sin reentrenar
el artefacto de produccion:

  (A) Composicion: compara la proporcion de clases (gravedad_siniestro),
      la tasa de edad_desconocida, y la distribucion de dia_semana/lluvia
      entre los dos anos de EVALUACION (2024 vs 2025) y entre los dos sets
      de ENTRENAMIENTO (<2023 vs <2024).

  (B) Tamano de entrenamiento: re-corre el split 2024->2025 pero con el
      set de entrenamiento submuestreado al mismo tamano que el split
      2023->2024 (11.644 filas), repetido con 10 semillas distintas, para
      ver si el F1 macro sobre 2025 cae hacia 0,286 (el tamano explicaria
      la brecha) o se mantiene cerca de 0,369 (el tamano no es la causa
      principal).

No modifica el artefacto de produccion ni ningun archivo del repositorio
salvo el reporte de salida indicado en --output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CATEGORICAS = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
NUMERICAS = ["hora", "edad_victima", "edad_desconocida", "temperatura", "humedad"]
COLUMNAS_SIN_EDAD = [c for c in (NUMERICAS + CATEGORICAS) if c not in {"edad_victima", "edad_desconocida"}]


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


def preparar(train: pd.DataFrame, objetivo: pd.DataFrame, columnas: list[str]):
    train = train.copy(); objetivo = objetivo.copy()
    cat = [c for c in CATEGORICAS if c in columnas]
    x_train = pd.get_dummies(train[columnas], columns=cat, dtype=float)
    x_objetivo = pd.get_dummies(objetivo[columnas], columns=cat, dtype=float).reindex(columns=x_train.columns, fill_value=0)
    return x_train, x_objetivo


def entrenar_evaluar(train: pd.DataFrame, test: pd.DataFrame, columnas: list[str], seed: int) -> float:
    x_train, x_test = preparar(train, test, columnas)
    modelo = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight="balanced_subsample", random_state=seed, n_jobs=-1)
    modelo.fit(x_train, train["gravedad_siniestro"])
    pred = modelo.predict(x_test)
    return float(f1_score(test["gravedad_siniestro"], pred, average="macro", zero_division=0))


def composicion(df: pd.DataFrame, etiqueta: str) -> dict:
    total = len(df)
    props_clase = (df["gravedad_siniestro"].value_counts(normalize=True) * 100).round(2).to_dict()
    conteo_clase = df["gravedad_siniestro"].value_counts().to_dict()
    return {
        "split": etiqueta,
        "filas": int(total),
        "proporcion_clase_pct": {str(k): float(v) for k, v in props_clase.items()},
        "conteo_clase": {str(k): int(v) for k, v in conteo_clase.items()},
        "pct_edad_desconocida": round(float(df["edad_desconocida"].mean()) * 100, 2),
        "pct_lluvia_si": round(float((df["lluvia"] == "SI").mean()) * 100, 2),
        "comunas_distintas": int(df["comuna"].nunique()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeticiones", type=int, default=10)
    args = parser.parse_args()

    base = cargar_base()

    train_2023 = base[base.anio_siniestro < 2023].copy()   # split 2023->2024
    test_2024 = base[base.anio_siniestro == 2024].copy()
    train_2024 = base[base.anio_siniestro < 2024].copy()   # split 2024->2025
    test_2025 = base[base.anio_siniestro == 2025].copy()

    # --- (A) composicion ---
    comp = [
        composicion(train_2023, "entrenamiento <2023 (split 2023->2024)"),
        composicion(test_2024, "evaluacion 2024 (split 2023->2024)"),
        composicion(train_2024, "entrenamiento <2024 (split 2024->2025)"),
        composicion(test_2025, "evaluacion 2025 (split 2024->2025)"),
    ]

    # --- (B) tamano de entrenamiento controlado ---
    n_chico = len(train_2023)  # 11.644, tamano del split mas corto
    n_grande = len(train_2024)
    rng = np.random.default_rng(123)

    f1_submuestreado = []
    for i in range(args.repeticiones):
        seed = int(rng.integers(0, 1_000_000))
        idx = rng.choice(n_grande, size=n_chico, replace=False)
        train_sub = train_2024.iloc[idx]
        f1 = entrenar_evaluar(train_sub, test_2025, COLUMNAS_SIN_EDAD, seed=seed)
        f1_submuestreado.append(f1)

    # referencias: full-size en cada split (deben reproducir aprox. los numeros
    # ya documentados en D02-estabilidad, con una semilla fija por separado)
    f1_full_2024_2025 = entrenar_evaluar(train_2024, test_2025, COLUMNAS_SIN_EDAD, seed=42)
    f1_full_2023_2024 = entrenar_evaluar(train_2023, test_2024, COLUMNAS_SIN_EDAD, seed=42)

    resultado_b = {
        "n_entrenamiento_chico_2023": n_chico,
        "n_entrenamiento_grande_2024": n_grande,
        "f1_macro_full_2023_train__test_2024": f1_full_2023_2024,
        "f1_macro_full_2024_train__test_2025": f1_full_2024_2025,
        "f1_macro_2024_train_submuestreado_a_tamano_2023__test_2025": {
            "repeticiones": args.repeticiones,
            "valores": f1_submuestreado,
            "media": float(np.mean(f1_submuestreado)),
            "desvio": float(np.std(f1_submuestreado)),
            "min": float(np.min(f1_submuestreado)),
            "max": float(np.max(f1_submuestreado)),
        },
    }

    salida = {"composicion": comp, "experimento_tamano_entrenamiento": resultado_b}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "reporte_causa_d02.json").write_text(json.dumps(salida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(resultado_b, ensure_ascii=False, indent=2))
    print(f"\nEvidencia completa en {args.output}/reporte_causa_d02.json")


if __name__ == "__main__":
    main()
