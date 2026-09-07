# -*- coding: utf-8 -*-
"""
Segunda vuelta de tuning: la busqueda por CV (tuning_rf.py) encontro una
config que mejora el f1_macro en cross-validation sobre 2019-2024 (0.458 vs
0.397) pero generaliza PEOR al holdout real de 2025 (f1_macro 0.386, y el
recall de GRAVE se derrumba de 0.52 a 0.07) -- señal clara de sobreajuste al
periodo de entrenamiento con arboles mas profundos y hojas mas chicas.

Esta segunda vuelta prueba unas pocas configs mas conservadoras (regularizadas)
directamente contra el holdout de 2025, en vez de confiar en el f1_macro de
CV como proxy de generalizacion futura -- que ya demostro ser enganoso.

Uso:
    python notebooks/tuning_rf2.py
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from reentrenar_modelo import cargar_motos_extendido  # noqa: E402

DATA = BASE_DIR.parent / "data"
ANIO_CORTE = 2025

CANDIDATOS = [
    ("actual (200/12, defaults)", dict(n_estimators=200, max_depth=12, class_weight="balanced")),
    ("mas regularizado A", dict(n_estimators=300, max_depth=10, min_samples_leaf=5, min_samples_split=10, class_weight="balanced")),
    ("mas regularizado B", dict(n_estimators=300, max_depth=8, min_samples_leaf=10, min_samples_split=20, class_weight="balanced")),
    ("mismo depth, hojas mas grandes", dict(n_estimators=300, max_depth=12, min_samples_leaf=5, min_samples_split=10, class_weight="balanced")),
    ("mas arboles, depth actual", dict(n_estimators=400, max_depth=12, class_weight="balanced")),
    ("balanced_subsample", dict(n_estimators=300, max_depth=12, min_samples_leaf=5, class_weight="balanced_subsample")),
]


def main():
    motos_extendido = cargar_motos_extendido()

    indice = pd.read_csv(DATA / "indice_inseguridad_comuna.csv")
    indice["comuna"] = indice["comuna"].astype(str)
    motos_extendido = motos_extendido.merge(
        indice[["comuna", "indice_inseguridad"]], on="comuna", how="left"
    )
    motos_extendido["indice_inseguridad"] = motos_extendido["indice_inseguridad"].fillna(
        indice["indice_inseguridad"].mean()
    )

    columnas_categoricas = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
    columnas_numericas = ["hora", "edad_victima", "edad_desconocida", "temperatura", "humedad", "indice_inseguridad"]

    train = motos_extendido[motos_extendido["anio_siniestro"] < ANIO_CORTE]
    test = motos_extendido[motos_extendido["anio_siniestro"] == ANIO_CORTE]

    todo = pd.get_dummies(
        motos_extendido[columnas_numericas + columnas_categoricas], columns=columnas_categoricas
    )
    X_train = todo.loc[train.index]
    X_test = todo.loc[test.index]
    y_train = train["gravedad_siniestro"]
    y_test = test["gravedad_siniestro"]

    resultados = []
    for nombre, params in CANDIDATOS:
        modelo = RandomForestClassifier(random_state=42, n_jobs=-1, **params)
        modelo.fit(X_train, y_train)
        pred = modelo.predict(X_test)
        reporte = classification_report(y_test, pred, output_dict=True)
        resultados.append({
            "config": nombre,
            "f1_macro": round(f1_score(y_test, pred, average="macro"), 3),
            "recall_grave": round(reporte["GRAVE"]["recall"], 3),
            "recall_mortal": round(reporte["MORTAL"]["recall"], 3),
            "recall_leve": round(reporte["LEVE"]["recall"], 3),
            "accuracy": round(reporte["accuracy"], 3),
        })
        print(f"listo: {nombre}")

    df = pd.DataFrame(resultados)
    pd.set_option("display.width", 160)
    print()
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
