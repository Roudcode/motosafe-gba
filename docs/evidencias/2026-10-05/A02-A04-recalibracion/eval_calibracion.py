"""Evaluacion temporal con indice_inseguridad (igual feature set que produccion)
y calibracion isotonica, para decidir demografia + calibracion con evidencia real.
No toca produccion -- solo lee data/, escribe a /tmp.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.metrics import brier_score_loss, classification_report, f1_score

ROOT = Path.cwd()
DATA = ROOT / "data"
CATEGORICAS = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
NUMERICAS = ["hora", "edad_victima", "edad_desconocida", "temperatura", "humedad"]

def cargar_base():
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

    indice = pd.read_csv(DATA / "indice_inseguridad_comuna.csv")
    indice["comuna"] = indice["comuna"].astype(str)
    base = base.merge(indice[["comuna", "indice_inseguridad"]], on="comuna", how="left")
    base["indice_inseguridad"] = base["indice_inseguridad"].fillna(indice["indice_inseguridad"].mean())
    return base

def preparar(train, objetivo, columnas):
    train = train.copy(); objetivo = objetivo.copy()
    if "edad_victima" in columnas:
        mediana = train["edad_victima"].median()
        train["edad_victima"] = train["edad_victima"].fillna(mediana)
        objetivo["edad_victima"] = objetivo["edad_victima"].fillna(mediana)
    cat = [c for c in CATEGORICAS if c in columnas]
    x_train = pd.get_dummies(train[columnas], columns=cat, dtype=float)
    x_obj = pd.get_dummies(objetivo[columnas], columns=cat, dtype=float).reindex(columns=x_train.columns, fill_value=0)
    return x_train, x_obj

def ece(y, probas, clases, bins=10):
    total = 0.0
    for i, clase in enumerate(clases):
        observado = (y == clase).astype(float)
        for grupo in np.array_split(np.argsort(probas[:, i]), bins):
            if len(grupo):
                total += len(grupo) / (len(y) * len(clases)) * abs(observado[grupo].mean() - probas[grupo, i].mean())
    return float(total)

def metricas_clase(y_test, pred, clases):
    rep = classification_report(y_test, pred, output_dict=True, zero_division=0)
    return {c: {"precision": round(rep.get(c, {}).get("precision", 0), 3), "recall": round(rep.get(c, {}).get("recall", 0), 3)} for c in clases}

def medir(nombre, train, validacion, test, columnas):
    x_train, x_val = preparar(train, validacion, columnas)
    _, x_test = preparar(train, test, columnas)
    rf = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1)
    rf.fit(x_train, train["gravedad_siniestro"])
    clases = rf.classes_.tolist()
    y_test = test["gravedad_siniestro"].to_numpy()

    pred_sin = rf.predict(x_test)
    probas_sin = rf.predict_proba(x_test)
    brier_sin = {c: round(float(brier_score_loss((y_test == c).astype(int), probas_sin[:, i])), 4) for i, c in enumerate(clases)}

    # Calibracion isotonica: el calibrador se ajusta sobre el anio de SELECCION
    # (2023), nunca visto en entrenamiento ni en el anio de evaluacion (2024).
    cal = CalibratedClassifierCV(FrozenEstimator(rf), method="isotonic")
    cal.fit(x_val, validacion["gravedad_siniestro"])
    pred_cal = cal.predict(x_test)
    probas_cal = cal.predict_proba(x_test)
    clases_cal = cal.classes_.tolist()
    brier_cal = {c: round(float(brier_score_loss((y_test == c).astype(int), probas_cal[:, i])), 4) for i, c in enumerate(clases_cal)}

    return {
        "variante": nombre,
        "sin_calibrar": {
            "f1_macro": round(f1_score(y_test, pred_sin, average="macro", zero_division=0), 4),
            "por_clase": metricas_clase(y_test, pred_sin, clases),
            "brier": brier_sin,
            "ece": round(ece(y_test, probas_sin, clases), 4),
        },
        "calibrado_isotonic": {
            "f1_macro": round(f1_score(y_test, pred_cal, average="macro", zero_division=0), 4),
            "por_clase": metricas_clase(y_test, pred_cal, clases_cal),
            "brier": brier_cal,
            "ece": round(ece(y_test, probas_cal, clases_cal), 4),
        },
    }

def main():
    base = cargar_base()
    train = base[base.anio_siniestro < 2023].copy()
    validacion = base[base.anio_siniestro == 2023].copy()
    test = base[base.anio_siniestro == 2024].copy()
    print(f"filas: train={len(train)} seleccion/calibracion={len(validacion)} evaluacion={len(test)}")

    base_cols = NUMERICAS + CATEGORICAS + ["indice_inseguridad"]
    variantes = {
        "produccion_actual (con edad+sexo+indice)": base_cols,
        "sin_edad (con sexo+indice)": [c for c in base_cols if c not in {"edad_victima", "edad_desconocida"}],
        "sin_demografia (solo contexto+indice)": [c for c in base_cols if c not in {"edad_victima", "edad_desconocida", "sexo_victima"}],
    }
    resultados = [medir(n, train, validacion, test, c) for n, c in variantes.items()]
    Path("/tmp/resultado_calibracion.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2))
    for r in resultados:
        print(f"\n=== {r['variante']} ===")
        print(f"  sin calibrar:  F1 macro={r['sin_calibrar']['f1_macro']}  ECE={r['sin_calibrar']['ece']}  GRAVE={r['sin_calibrar']['por_clase'].get('GRAVE')}  MORTAL={r['sin_calibrar']['por_clase'].get('MORTAL')}")
        print(f"  calibrado:     F1 macro={r['calibrado_isotonic']['f1_macro']}  ECE={r['calibrado_isotonic']['ece']}  GRAVE={r['calibrado_isotonic']['por_clase'].get('GRAVE')}  MORTAL={r['calibrado_isotonic']['por_clase'].get('MORTAL')}")

if __name__ == "__main__":
    main()
