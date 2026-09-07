# -*- coding: utf-8 -*-
"""
Reentrena el modelo final (Random Forest) sumando el indice de inseguridad por
comuna (data/indice_inseguridad_comuna.csv, generado por
construir_indice_inseguridad.py a partir del dataset de delitos de CABA) como
dos variables numericas nuevas: indice_inseguridad e indice_inseguridad_moto.

Es la version script, reproducible, del pipeline que vive en
notebooks/01_eda_hotspots_moto.ipynb (secciones 4, 5, 5.1 y 6 — desde que se
carga motos_limpio.csv hasta que se guarda modelo_final.pkl y
hotspots_contexto.csv). No repite el clustering DBSCAN ni la limpieza inicial
de datos: parte de motos_limpio.csv y motos_con_clusters.csv, que ya estan en
el repo y no cambian con este agregado.

No necesita red (motos_limpio.csv, siniestros_viales_victimas.csv,
clima_historico.csv, indice_inseguridad_comuna.csv ya estan todos en data/).

Uso:
    python notebooks/reentrenar_modelo.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"
BACKEND = BASE_DIR / "backend"


def cargar_motos_extendido():
    """Reproduce motos_extendido tal como queda al final de la seccion 4 del
    notebook (motos_limpio + edad/sexo de victima + clima), justo antes de
    codificar variables y entrenar."""
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    motos["contraparte_siniestro"] = motos["contraparte_siniestro"].str.strip().str.upper()
    motos["tipo_de_via_siniestro"] = motos["tipo_de_via_siniestro"].str.strip().str.upper()
    motos["hora"] = pd.to_datetime(motos["hora_siniestro"], format="%H:%M:%S").dt.hour
    motos["dia_semana"] = pd.to_datetime(motos["fecha_siniestro"]).dt.day_name()
    motos_modelo = motos.dropna(subset=["hora"]).copy()

    victimas = pd.read_csv(
        DATA / "siniestros_viales_victimas.csv", encoding="utf-8-sig", sep=";", low_memory=False
    )
    victimas["modo_desplazamiento_victima"] = victimas["modo_desplazamiento_victima"].str.strip().str.upper()
    victimas["sexo_victima"] = victimas["sexo_victima"].str.strip().str.upper()
    victimas_moto = victimas[victimas["modo_desplazamiento_victima"] == "MOTO"].copy()
    victimas_moto["edad_victima"] = pd.to_numeric(victimas_moto["edad_victima"], errors="coerce")
    resumen_victima = victimas_moto.groupby("id_siniestro").agg(
        edad_victima=("edad_victima", "mean"),
        sexo_victima=("sexo_victima", lambda x: x.mode().iloc[0] if not x.mode().empty else "SD"),
    ).reset_index()

    motos_extendido = motos_modelo.merge(resumen_victima, on="id_siniestro", how="left")
    motos_extendido.loc[
        (motos_extendido["edad_victima"] < 14) | (motos_extendido["edad_victima"] > 95), "edad_victima"
    ] = None
    motos_extendido["edad_desconocida"] = motos_extendido["edad_victima"].isna().astype(int)
    mediana_edad = motos_extendido["edad_victima"].median()
    motos_extendido["edad_victima"] = motos_extendido["edad_victima"].fillna(mediana_edad)
    motos_extendido["sexo_victima"] = motos_extendido["sexo_victima"].fillna("SD")
    motos_extendido["comuna"] = motos_extendido["comuna"].astype("Int64").astype(str)

    clima = pd.read_csv(DATA / "clima_historico.csv")
    clima["fecha"] = clima["fecha"].astype(str)
    motos_extendido["fecha_siniestro_str"] = pd.to_datetime(motos_extendido["fecha_siniestro"]).dt.date.astype(str)
    filas_antes = len(motos_extendido)
    motos_extendido = motos_extendido.merge(
        clima, left_on=["fecha_siniestro_str", "hora"], right_on=["fecha", "hora"], how="left"
    )
    sin_clima = motos_extendido["precipitacion"].isna().sum()
    motos_extendido = motos_extendido.dropna(subset=["precipitacion", "temperatura", "humedad"]).copy()
    motos_extendido["lluvia"] = (motos_extendido["precipitacion"] > 0.1).map({True: "SI", False: "NO"})
    print(f"Siniestros antes del cruce con clima: {filas_antes}")
    print(f"Sin clima disponible (descartados): {sin_clima}")
    print(f"Siniestros con clima real: {len(motos_extendido)}")
    return motos_extendido


def entrenar(motos_extendido, columnas_categoricas, columnas_numericas, etiqueta):
    X = pd.get_dummies(motos_extendido[columnas_numericas + columnas_categoricas], columns=columnas_categoricas)
    y = motos_extendido["gravedad_siniestro"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    # Config elegida tras comparar 6 variantes contra un holdout temporal real
    # (2025, nunca visto durante la busqueda) en vez de solo cross-validation:
    # la busqueda automatica por CV encontro una config "mejor" en el propio
    # periodo de entrenamiento que en realidad sobreajustaba (recall de GRAVE
    # se derrumbaba de 0.52 a 0.07 en el holdout). De las variantes probadas
    # directamente contra el holdout, esta (balanced_subsample, hojas minimas
    # de 5) es la que mejor equilibra recall de los casos graves/mortales
    # -- que es lo que mas importa en una app de seguridad vial -- sin hundir
    # tanto la accuracy general como las variantes mas agresivas. Contra el
    # holdout de 2025: recall GRAVE 0.52->0.65, MORTAL 0.34->0.56, a cambio de
    # accuracy general 0.71->0.64 (ver notebooks/tuning_rf2.py para el detalle
    # y las otras 5 variantes comparadas).
    modelo = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=5,
        class_weight="balanced_subsample", random_state=42, n_jobs=-1
    )
    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)
    print(f"\n--- {etiqueta} ---")
    print(classification_report(y_test, y_pred))
    return modelo, X


def main():
    motos_extendido = cargar_motos_extendido()

    indice = pd.read_csv(DATA / "indice_inseguridad_comuna.csv")
    indice["comuna"] = indice["comuna"].astype(str)
    motos_extendido = motos_extendido.merge(
        indice[["comuna", "indice_inseguridad", "indice_inseguridad_moto"]], on="comuna", how="left"
    )
    faltantes = motos_extendido["indice_inseguridad"].isna().sum()
    if faltantes:
        print(f"ADVERTENCIA: {faltantes} filas sin comuna reconocida en el indice, se completan con el promedio")
        motos_extendido["indice_inseguridad"] = motos_extendido["indice_inseguridad"].fillna(
            indice["indice_inseguridad"].mean()
        )
        motos_extendido["indice_inseguridad_moto"] = motos_extendido["indice_inseguridad_moto"].fillna(
            indice["indice_inseguridad_moto"].mean()
        )

    columnas_categoricas = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
    columnas_numericas_sin_indice = ["hora", "edad_victima", "edad_desconocida", "temperatura", "humedad"]
    # Se probaron 3 variantes offline antes de decidir (ver commit): con ambos
    # indices, solo el de moto, y solo el general. El general solo fue el que
    # mejoro el recall de MORTAL (0.38 -> 0.41) sin hundir tanto el de GRAVE como
    # las otras dos variantes (0.65 -> 0.60, contra 0.65 -> 0.55 con ambos indices).
    # Se descarta indice_inseguridad_moto como feature del modelo (empeoraba MORTAL
    # solo o en combinacion), pero se lo deja en indice_inseguridad_comuna.csv como
    # dato informativo, no es necesario tirarlo.
    columnas_numericas_con_indice = columnas_numericas_sin_indice + ["indice_inseguridad"]

    _, _ = entrenar(motos_extendido, columnas_categoricas, columnas_numericas_sin_indice, "SIN indice de inseguridad (modelo anterior)")
    modelo_final, X_final = entrenar(motos_extendido, columnas_categoricas, columnas_numericas_con_indice, "CON indice de inseguridad (modelo nuevo)")

    joblib.dump(modelo_final, DATA / "modelo_final.pkl")
    joblib.dump(X_final.columns.tolist(), DATA / "columnas_modelo.pkl")
    print(f"\nModelo final guardado en {DATA / 'modelo_final.pkl'} ({len(X_final.columns)} columnas)")

    # --- Contexto por hotspot (igual que la seccion 6 del notebook), mas el indice
    # de inseguridad de la comuna de cada hotspot, para que /hotspots pueda armar
    # la fila completa sin tener que hacer el join en cada request.
    motos_clusters = pd.read_csv(DATA / "motos_con_clusters.csv")
    base_clusters = motos_clusters[motos_clusters["cluster"] != -1][
        ["id_siniestro", "cluster", "comuna", "tipo_de_via_siniestro"]
    ]
    contexto_por_cluster = base_clusters.merge(
        motos_extendido[["id_siniestro", "edad_victima", "sexo_victima", "contraparte_siniestro"]],
        on="id_siniestro", how="left",
    ).groupby("cluster").agg(
        comuna_moda=("comuna", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        tipo_via_moda=("tipo_de_via_siniestro", lambda x: x.mode().iloc[0] if not x.mode().empty else "AVENIDA"),
        contraparte_moda=("contraparte_siniestro", lambda x: x.mode().iloc[0] if not x.mode().empty else "AUTO"),
        edad_promedio=("edad_victima", lambda x: x.mean() if x.notna().any() else 32.0),
        sexo_moda=("sexo_victima", lambda x: x.mode().iloc[0] if not x.mode().empty else "SD"),
    ).reset_index()
    contexto_por_cluster["comuna_moda"] = contexto_por_cluster["comuna_moda"].astype("Int64").astype(str)
    contexto_por_cluster["edad_promedio"] = contexto_por_cluster["edad_promedio"].round(1)

    contexto_por_cluster = contexto_por_cluster.merge(
        indice[["comuna", "indice_inseguridad", "indice_inseguridad_moto"]],
        left_on="comuna_moda", right_on="comuna", how="left",
    ).drop(columns=["comuna"])
    contexto_por_cluster["indice_inseguridad"] = contexto_por_cluster["indice_inseguridad"].fillna(indice["indice_inseguridad"].mean())
    contexto_por_cluster["indice_inseguridad_moto"] = contexto_por_cluster["indice_inseguridad_moto"].fillna(indice["indice_inseguridad_moto"].mean())

    contexto_por_cluster.to_csv(DATA / "hotspots_contexto.csv", index=False)
    print(f"hotspots_contexto.csv actualizado ({len(contexto_por_cluster)} clusters, con indice de inseguridad)")

    # --- Copiar artefactos a backend/, que es de donde los sirve main.py ---
    for archivo in ["modelo_final.pkl", "columnas_modelo.pkl", "hotspots_contexto.csv"]:
        (BACKEND / archivo).write_bytes((DATA / archivo).read_bytes())
    (BACKEND / "indice_inseguridad_comuna.csv").write_bytes((DATA / "indice_inseguridad_comuna.csv").read_bytes())
    print("\nArtefactos copiados a backend/: modelo_final.pkl, columnas_modelo.pkl, hotspots_contexto.csv, indice_inseguridad_comuna.csv")


if __name__ == "__main__":
    main()
