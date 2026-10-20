"""Matriz de confusion real (conteos) de la variante sin_edad (produccion actual)
sobre la evaluacion temporal 2024, mismo pipeline que eval_calibracion.py /
split_interno_sin_edad.py pero con train<2023 / test=2024 (temporal, no split
aleatorio) para reemplazar la Tabla 4.3 del Capitulo 4, que todavia citaba la
variante con edad.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, classification_report, f1_score

DATA = Path("data")
CATEGORICAS = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
NUMERICAS_SIN_EDAD = ["hora", "temperatura", "humedad"]


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
    resumen = victimas.groupby("id_siniestro").agg(
        sexo_victima=("sexo_victima", lambda x: x.mode().iloc[0] if not x.mode().empty else "SD"),
    ).reset_index()
    base = motos.merge(resumen, on="id_siniestro", how="left")
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


base = cargar_base()
columnas = NUMERICAS_SIN_EDAD + CATEGORICAS + ["indice_inseguridad"]

train = base[base.anio_siniestro < 2023].copy()
test = base[base.anio_siniestro == 2024].copy()
print(f"n train={len(train)} n test={len(test)}")

x_train = pd.get_dummies(train[columnas], columns=CATEGORICAS, dtype=float)
x_test = pd.get_dummies(test[columnas], columns=CATEGORICAS, dtype=float).reindex(columns=x_train.columns, fill_value=0)

rf = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
    class_weight="balanced_subsample", random_state=42, n_jobs=-1)
rf.fit(x_train, train["gravedad_siniestro"])
pred = rf.predict(x_test)
y_test = test["gravedad_siniestro"].to_numpy()

clases = ["GRAVE", "LEVE", "MORTAL"]
cm = confusion_matrix(y_test, pred, labels=clases)
print("\nmatriz de confusion (filas=real, columnas=predicho), orden", clases)
print(cm)

print("\nf1 macro:", round(f1_score(y_test, pred, average="macro", zero_division=0), 4))
rep = classification_report(y_test, pred, output_dict=True, zero_division=0)
for c in clases:
    print(f"{c}: precision={round(rep[c]['precision'],4)} recall={round(rep[c]['recall'],4)} support={int(rep[c]['support'])}")

total_pred_grave = cm[:, 0].sum()
total_pred_mortal = cm[:, 2].sum()
print(f"\ntotal predicho GRAVE: {total_pred_grave}  de los cuales reales GRAVE: {cm[0,0]}")
print(f"total predicho MORTAL: {total_pred_mortal}  de los cuales reales MORTAL: {cm[2,2]}")
