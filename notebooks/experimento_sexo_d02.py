"""
D02 -- experimento causal sobre la pista de docs/evidencias/2026-10-21/D02-completitud:
¿la tasa de "sexo_victima sin dato" (que varia fuerte por anio y es feature
activa en la variante sin_edad del modelo productivo) explica parte de la
brecha de F1 macro entre el split 2023->2024 (0,2859) y el split
2024->2025 (0,3689), o la brecha se mantiene igual si se la saca?

Reentrena y evalua los mismos dos splits ya medidos, pero sacando
sexo_victima del conjunto de columnas (ademas de edad_victima y
edad_desconocida, que la variante productiva ya no usa). Si la brecha se
achica de forma marcada al sacar sexo_victima, es evidencia de que la
variable aporta al efecto; si se mantiene igual, queda descartada como
causa y la pista vuelve a quedar abierta sobre el patron real.

No modifica el artefacto de produccion ni ningun archivo del repositorio
salvo el reporte indicado en --output.
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
COLUMNAS_SIN_EDAD_NI_SEXO = [c for c in COLUMNAS_SIN_EDAD if c != "sexo_victima"]


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


def entrenar_evaluar(train: pd.DataFrame, test: pd.DataFrame, columnas: list[str], seed: int) -> dict:
    x_train, x_test = preparar(train, test, columnas)
    modelo = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight="balanced_subsample", random_state=seed, n_jobs=-1)
    modelo.fit(x_train, train["gravedad_siniestro"])
    pred = modelo.predict(x_test)
    f1_macro = float(f1_score(test["gravedad_siniestro"], pred, average="macro", zero_division=0))
    f1_por_clase = f1_score(test["gravedad_siniestro"], pred, average=None, zero_division=0,
                             labels=sorted(test["gravedad_siniestro"].unique()))
    return {
        "f1_macro": f1_macro,
        "f1_por_clase": dict(zip(sorted(test["gravedad_siniestro"].unique()), [float(v) for v in f1_por_clase])),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeticiones", type=int, default=5)
    args = parser.parse_args()

    base = cargar_base()
    train_2023 = base[base.anio_siniestro < 2023].copy()
    test_2024 = base[base.anio_siniestro == 2024].copy()
    train_2024 = base[base.anio_siniestro < 2024].copy()
    test_2025 = base[base.anio_siniestro == 2025].copy()

    resultado = {}
    for nombre, columnas in [("con_sexo", COLUMNAS_SIN_EDAD), ("sin_sexo", COLUMNAS_SIN_EDAD_NI_SEXO)]:
        corridas_2024 = []
        corridas_2025 = []
        for i in range(args.repeticiones):
            seed = 42 + i
            corridas_2024.append(entrenar_evaluar(train_2023, test_2024, columnas, seed=seed))
            corridas_2025.append(entrenar_evaluar(train_2024, test_2025, columnas, seed=seed))
        f1_2024 = [r["f1_macro"] for r in corridas_2024]
        f1_2025 = [r["f1_macro"] for r in corridas_2025]
        resultado[nombre] = {
            "columnas": columnas,
            "split_2023_a_2024": {
                "f1_macro_media": float(np.mean(f1_2024)), "f1_macro_valores": f1_2024,
                "f1_por_clase_primera_corrida": corridas_2024[0]["f1_por_clase"],
            },
            "split_2024_a_2025": {
                "f1_macro_media": float(np.mean(f1_2025)), "f1_macro_valores": f1_2025,
                "f1_por_clase_primera_corrida": corridas_2025[0]["f1_por_clase"],
            },
            "brecha_f1_macro_media": float(np.mean(f1_2025) - np.mean(f1_2024)),
        }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "experimento_sexo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: {"brecha_f1_macro_media": v["brecha_f1_macro_media"],
                           "f1_2023_2024": v["split_2023_a_2024"]["f1_macro_media"],
                           "f1_2024_2025": v["split_2024_a_2025"]["f1_macro_media"]}
                       for k, v in resultado.items()}, ensure_ascii=False, indent=2))
    print(f"\nEvidencia completa en {args.output}/experimento_sexo.json")


if __name__ == "__main__":
    main()
