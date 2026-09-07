# -*- coding: utf-8 -*-
"""
Valida el modelo con un split temporal (entrena con 2019-2024, testea contra
2025 entero) en vez del split aleatorio 80/20 que usa reentrenar_modelo.py.

El split aleatorio responde "el modelo aprendio el patron dentro de estos
datos?" pero no responde la pregunta que en realidad importa para produccion:
"el modelo generalizaria a siniestros que todavia no pasaron?" -- que es
exactamente la pregunta que ya esta escrita, sin responder con evidencia, en
el FAQ de la Guia del proyecto ("el modelo va a seguir prediciendo bien para
siempre?").

No reemplaza el modelo en produccion (modelo_final.pkl no se toca): esto es
una validacion adicional para reportar en la tesis y saber con evidencia real
que tan bien generaliza el enfoque a datos futuros.

Uso:
    python notebooks/validar_temporal.py
"""
import sys
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
from reentrenar_modelo import cargar_motos_extendido  # noqa: E402

DATA = BASE_DIR.parent / "data"
ANIO_CORTE = 2025  # 2019-2024 para entrenar, 2025 (ano completo) para testear


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
    print(f"Train (2019-{ANIO_CORTE - 1}): {len(train)} siniestros")
    print(f"Test  ({ANIO_CORTE}):      {len(test)} siniestros")
    print()

    # get_dummies sobre train+test juntos para que las columnas one-hot
    # coincidan (una categoria que solo aparece en test no puede generar una
    # columna que el modelo entrenado no conoce).
    todo = pd.get_dummies(
        motos_extendido[columnas_numericas + columnas_categoricas], columns=columnas_categoricas
    )
    X_train = todo.loc[train.index]
    X_test = todo.loc[test.index]
    y_train = train["gravedad_siniestro"]
    y_test = test["gravedad_siniestro"]

    modelo = RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1
    )
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)

    print(f"--- Validacion temporal: entrenado con {ANIO_CORTE - 1} y anios anteriores, testeado contra {ANIO_CORTE} ---")
    print(classification_report(y_test, y_pred))

    print("--- Para comparar: el mismo modelo con split aleatorio 80/20 (todos los anios mezclados) ---")
    from sklearn.model_selection import train_test_split
    X_rand_train, X_rand_test, y_rand_train, y_rand_test = train_test_split(
        todo, motos_extendido["gravedad_siniestro"], test_size=0.2, random_state=42,
        stratify=motos_extendido["gravedad_siniestro"]
    )
    modelo_rand = RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42, n_jobs=-1
    )
    modelo_rand.fit(X_rand_train, y_rand_train)
    y_rand_pred = modelo_rand.predict(X_rand_test)
    print(classification_report(y_rand_test, y_rand_pred))


if __name__ == "__main__":
    main()
