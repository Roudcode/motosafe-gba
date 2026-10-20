"""Cuanto se puede asegurar el nivel de riesgo de cada zona real de produccion.

No es un chequeo de generalizacion temporal (eso ya lo mide D02/A02): esto es
estabilidad del propio proceso de entrenamiento. Produccion entrena sobre el
100% del historico disponible (reentrenar_modelo.py, train_test_split simple,
sin recorte por anio) -- asi que la pregunta real es: si se vuelve a entrenar
el mismo modelo, con los mismos datos, pero con el azar propio del bootstrap
interno del Random Forest y de una remuestra con reemplazo del dataset
(bagging clasico, lo que hace cualquier reentrenamiento real no sea
bit-a-bit identico), ¿la zona X sigue cayendo en el mismo nivel de riesgo?

Se entrenan N modelos sobre N remuestras bootstrap del dataset COMPLETO
(mismo feature set que produccion: sin edad, con sexo e indice), se evalua
cada uno sobre la grilla de 336 escenarios de calibrar_umbrales_riesgo.py
para las 740 zonas reales, y se mide que tan seguido coinciden los N modelos
en el nivel asignado a cada zona-escenario.
"""
import time
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier

DATA = Path("data")
BACKEND = Path("backend")
CATEGORICAS = ["dia_semana", "comuna", "tipo_de_via_siniestro", "contraparte_siniestro", "sexo_victima", "lluvia"]
NUMERICAS_SIN_EDAD = ["hora", "temperatura", "humedad"]
COLUMNAS = NUMERICAS_SIN_EDAD + CATEGORICAS + ["indice_inseguridad"]
N_BOOTSTRAP = 10

HORAS = list(range(24))
DIAS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
CLIMAS = [
    {"lluvia": "NO", "temperatura": 17.6, "humedad": 72.1},
    {"lluvia": "SI", "temperatura": 17.6, "humedad": 72.1},
]


def cargar_base_completa():
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    motos["contraparte_siniestro"] = motos["contraparte_siniestro"].str.strip().str.upper()
    motos["tipo_de_via_siniestro"] = motos["tipo_de_via_siniestro"].str.strip().str.upper()
    fecha = pd.to_datetime(motos["fecha_siniestro"], errors="coerce")
    motos["dia_semana"] = fecha.dt.day_name()
    motos["hora"] = pd.to_datetime(motos["hora_siniestro"], format="%H:%M:%S", errors="coerce").dt.hour
    motos = motos.dropna(subset=["hora"]).copy()

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


def cargar_zonas_reales():
    zonas = pd.read_csv(BACKEND / "hotspots_contexto.csv")
    zonas["comuna_moda"] = zonas["comuna_moda"].astype(str)
    return zonas


def score_de_matriz(matriz, clases):
    clases = list(clases)
    return 2 * matriz[:, clases.index("MORTAL")] + matriz[:, clases.index("GRAVE")]


def predecir_grilla(rf, columnas_modelo, zonas):
    clases = rf.classes_.tolist()
    scores_por_escenario = []
    for hora in HORAS:
        for dia in DIAS:
            for clima in CLIMAS:
                filas = pd.DataFrame({
                    "hora": hora, "temperatura": clima["temperatura"], "humedad": clima["humedad"],
                    "dia_semana": dia, "comuna": zonas["comuna_moda"], "tipo_de_via_siniestro": zonas["tipo_via_moda"],
                    "contraparte_siniestro": zonas["contraparte_moda"], "sexo_victima": zonas["sexo_moda"],
                    "lluvia": clima["lluvia"], "indice_inseguridad": zonas["indice_inseguridad"],
                })
                codificada = pd.get_dummies(filas, columns=CATEGORICAS, dtype=float).reindex(columns=columnas_modelo, fill_value=0)
                matriz = rf.predict_proba(codificada)
                scores_por_escenario.append(score_de_matriz(matriz, clases))
    return np.array(scores_por_escenario)  # (336, 740)


def nivel_vectorizado(scores, p25, p75, p95):
    niveles = np.full(scores.shape, "bajo", dtype=object)
    niveles[scores >= p25] = "medio"
    niveles[scores >= p75] = "alto"
    niveles[scores >= p95] = "critico"
    return niveles


def main():
    t0 = time.time()
    base = cargar_base_completa()
    zonas = cargar_zonas_reales()
    n_zonas = len(zonas)
    print(f"filas totales: {len(base)}  zonas reales: {n_zonas}")

    todos_los_niveles = []  # lista de matrices (336, 740), una por modelo bootstrap
    rng = np.random.default_rng(42)
    for b in range(N_BOOTSTRAP):
        indices = rng.integers(0, len(base), len(base))
        muestra = base.iloc[indices]
        x_train = pd.get_dummies(muestra[COLUMNAS], columns=CATEGORICAS, dtype=float)
        rf = RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
            class_weight="balanced_subsample", random_state=b, n_jobs=-1)
        rf.fit(x_train, muestra["gravedad_siniestro"])
        scores = predecir_grilla(rf, x_train.columns, zonas)
        p25, p75, p95 = np.percentile(scores, [25, 75, 95])
        niveles = nivel_vectorizado(scores, p25, p75, p95)
        todos_los_niveles.append(niveles)
        print(f"  bootstrap {b+1}/{N_BOOTSTRAP} listo ({time.time()-t0:.0f}s acumulados)  p25={p25:.3f} p75={p75:.3f} p95={p95:.3f}")

    pila = np.stack(todos_los_niveles)  # (N_BOOTSTRAP, 336, 740)

    # Para cada (escenario, zona), el nivel mas votado entre los N modelos y
    # con que fraccion de los modelos coincide ese voto.
    niveles_posibles = ["bajo", "medio", "alto", "critico"]
    conteos = np.zeros((len(niveles_posibles),) + pila.shape[1:], dtype=int)
    for i, niv in enumerate(niveles_posibles):
        conteos[i] = (pila == niv).sum(axis=0)
    voto_mayoritario_idx = conteos.argmax(axis=0)
    acuerdo = conteos.max(axis=0) / N_BOOTSTRAP  # (336, 740): fraccion de modelos que coinciden con el voto mayoritario

    print(f"\n=== Acuerdo entre {N_BOOTSTRAP} modelos bootstrap sobre el mismo dataset completo ===")
    print(f"acuerdo global (todas las zonas x escenarios): media {acuerdo.mean()*100:.1f}%  mediana {np.median(acuerdo)*100:.1f}%")

    acuerdo_por_zona = acuerdo.mean(axis=0)  # promedio sobre los 336 escenarios, por zona
    print(f"\nacuerdo por zona: minimo {acuerdo_por_zona.min()*100:.1f}%  mediana {np.median(acuerdo_por_zona)*100:.1f}%  maximo {acuerdo_por_zona.max()*100:.1f}%")
    print(f"zonas con acuerdo >= 90%: {(acuerdo_por_zona >= 0.9).sum()} de {n_zonas} ({100*(acuerdo_por_zona >= 0.9).mean():.1f}%)")
    print(f"zonas con acuerdo >= 80%: {(acuerdo_por_zona >= 0.8).sum()} de {n_zonas} ({100*(acuerdo_por_zona >= 0.8).mean():.1f}%)")
    print(f"zonas con acuerdo < 60%: {(acuerdo_por_zona < 0.6).sum()} de {n_zonas} ({100*(acuerdo_por_zona < 0.6).mean():.1f}%)")

    nivel_mayoritario_por_zona_escenario = np.array(niveles_posibles)[voto_mayoritario_idx]  # (336, 740)
    # Agrupar el acuerdo segun el nivel mayoritario asignado, para ver si
    # 'critico' es mas o menos estable que 'bajo'.
    print("\nacuerdo promedio, agrupado por el nivel mayoritario asignado en ese zona-escenario:")
    for niv in niveles_posibles:
        mask = nivel_mayoritario_por_zona_escenario == niv
        if mask.sum():
            print(f"  {niv}: {mask.sum()} zona-escenario, acuerdo promedio {acuerdo[mask].mean()*100:.1f}%")

    zonas_out = zonas.copy()
    zonas_out["acuerdo_bootstrap_pct"] = acuerdo_por_zona
    zonas_out.to_csv("/tmp/scratch/zonas_confianza_bootstrap.csv", index=False)
    print(f"\ntotal: {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
