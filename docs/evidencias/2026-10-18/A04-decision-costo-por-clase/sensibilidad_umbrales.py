"""Sensibilidad de los cortes de percentil (p25/p75/p95) del modelo sin_edad
(el que esta en produccion) para la decision de negocio pendiente de A04:
costo relativo de falsas alarmas por clase.

Mismo pipeline de carga y mismo split temporal que eval_calibracion.py
(train<2023, validacion=2023, test=2024). El score 2*P(MORTAL)+P(GRAVE) se
calcula igual que en produccion (calibrar_umbrales_riesgo.py / main.py).

La poblacion de referencia real de produccion es sintetica (hotspots_contexto
x 336 escenarios hora/dia/lluvia), no tiene gravedad real. Para poder medir
recall/precision reales por clase, los percentiles de corte se calculan sobre
el score de VALIDACION (2023, nunca usado para entrenar) y se aplican sobre
TEST (2024, nunca visto) -- mismo principio de no contaminar la evaluacion
que usa el resto del proyecto.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

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
validacion = base[base.anio_siniestro == 2023].copy()
test = base[base.anio_siniestro == 2024].copy()
print(f"filas: train={len(train)} validacion(ref. percentiles)={len(validacion)} test(evaluacion real)={len(test)}")

x_train = pd.get_dummies(train[columnas], columns=CATEGORICAS, dtype=float)
x_val = pd.get_dummies(validacion[columnas], columns=CATEGORICAS, dtype=float).reindex(columns=x_train.columns, fill_value=0)
x_test = pd.get_dummies(test[columnas], columns=CATEGORICAS, dtype=float).reindex(columns=x_train.columns, fill_value=0)

rf = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
    class_weight="balanced_subsample", random_state=42, n_jobs=-1)
rf.fit(x_train, train["gravedad_siniestro"])
clases = rf.classes_.tolist()
idx_mortal = clases.index("MORTAL")
idx_grave = clases.index("GRAVE")

proba_val = rf.predict_proba(x_val)
score_val = 2 * proba_val[:, idx_mortal] + proba_val[:, idx_grave]

proba_test = rf.predict_proba(x_test)
score_test = 2 * proba_test[:, idx_mortal] + proba_test[:, idx_grave]
y_test = test["gravedad_siniestro"].to_numpy()

es_grave = y_test == "GRAVE"
es_mortal = y_test == "MORTAL"
es_severo = es_grave | es_mortal

print(f"\nscore en test: min={score_test.min():.4f} max={score_test.max():.4f} mediana={np.median(score_test):.4f}")
print(f"total test: {len(y_test)}  GRAVE={es_grave.sum()}  MORTAL={es_mortal.sum()}  severo(GRAVE+MORTAL)={es_severo.sum()}")

print("\ncorte(pctl) | umbral(score) | %zonas marcadas 'alto o mas' | recall GRAVE | recall MORTAL | recall severo | precision severo")
cortes = [50, 60, 65, 70, 75, 80, 85, 90, 95]
for c in cortes:
    umbral = np.percentile(score_val, c)
    flag = score_test >= umbral
    pct_flag = flag.mean()
    recall_g = (flag & es_grave).sum() / es_grave.sum() if es_grave.sum() else float("nan")
    recall_m = (flag & es_mortal).sum() / es_mortal.sum() if es_mortal.sum() else float("nan")
    recall_s = (flag & es_severo).sum() / es_severo.sum() if es_severo.sum() else float("nan")
    precision_s = (flag & es_severo).sum() / flag.sum() if flag.sum() else float("nan")
    marca = "  <- p75 actual (medio/alto)" if c == 75 else ("  <- p95 actual (alto/critico)" if c == 95 else "")
    print(f"p{c:02d} | {umbral:.4f} | {pct_flag*100:5.1f}% | {recall_g*100:5.1f}% | {recall_m*100:5.1f}% | {recall_s*100:5.1f}% | {precision_s*100:5.1f}%{marca}")
