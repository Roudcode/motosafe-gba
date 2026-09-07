# -*- coding: utf-8 -*-
"""
Busqueda de hiperparametros para el Random Forest, usando SOLO el set de
entrenamiento temporal (2019-2024) para la busqueda (RandomizedSearchCV con
StratifiedKFold), y el anio 2025 completo -- nunca visto durante la busqueda
-- como holdout final para reportar el resultado real. Evita el problema de
"tunear contra el mismo split que despues se reporta como resultado", que
inflaria artificialmente el numero final.

Uso:
    python notebooks/tuning_rf.py
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from reentrenar_modelo import cargar_motos_extendido  # noqa: E402

DATA = BASE_DIR.parent / "data"
ANIO_CORTE = 2025


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

    param_dist = {
        "n_estimators": [150, 200, 300, 400],
        "max_depth": [8, 10, 12, 16, 20, None],
        "min_samples_leaf": [1, 2, 4, 8],
        "min_samples_split": [2, 5, 10],
        "max_features": ["sqrt", "log2", 0.5],
    }

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    busqueda = RandomizedSearchCV(
        RandomForestClassifier(class_weight="balanced", random_state=42, n_jobs=-1),
        param_distributions=param_dist,
        n_iter=12,
        scoring="f1_macro",  # promedia igual las 3 clases, no se deja dominar por LEVE
        cv=cv,
        random_state=42,
        n_jobs=1,  # el RF ya usa los 2 cores, no paralelizar tambien la busqueda
        verbose=1,
    )
    busqueda.fit(X_train, y_train)

    print("\nMejores hiperparametros encontrados (por f1_macro en CV sobre 2019-2024):")
    print(busqueda.best_params_)
    print(f"f1_macro en CV: {busqueda.best_score_:.3f}")

    modelo_base = RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1
    )
    modelo_base.fit(X_train, y_train)
    pred_base = modelo_base.predict(X_test)

    mejor_modelo = busqueda.best_estimator_
    pred_mejor = mejor_modelo.predict(X_test)

    print("\n=== Holdout 2025 (nunca visto durante la busqueda) ===")
    print("\n--- Config actual (200 arboles, max_depth 12) ---")
    print(classification_report(y_test, pred_base))
    print(f"f1_macro: {f1_score(y_test, pred_base, average='macro'):.3f}")

    print("\n--- Config encontrada por la busqueda ---")
    print(classification_report(y_test, pred_mejor))
    print(f"f1_macro: {f1_score(y_test, pred_mejor, average='macro'):.3f}")


if __name__ == "__main__":
    main()
