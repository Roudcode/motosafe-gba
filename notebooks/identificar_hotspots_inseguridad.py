# -*- coding: utf-8 -*-
"""
Hotspots de inseguridad (robos, hurtos, lesiones, amenazas, homicidios).

Dos variantes, con metodologia distinta para cada una desde la migracion a
HDBSCAN de los siniestros de moto (ver README.md, bitacora, "De DBSCAN a
HDBSCAN"):

  - MOTO: delitos con uso_moto=SI (en la practica, 100% categoria Robo -- el
    GCBA no distingue si la moto fue el medio del robo o el objeto robado).
    Se evaluo un barrido de min_cluster_size x min_samples con HDBSCAN, igual
    criterio que se uso para los siniestros de moto (mismo chequeo de "riesgo
    de blob": tamano del cluster mas grande como % del total). Con
    min_cluster_size=12 (mismo piso que siniestros: todo hotspot mostrado
    tiene al menos 12 casos reales) y min_samples=2, el resultado fue 502
    hotspots, cobertura del 74.3% -- un salto enorme frente al 14.1% que daba
    la calibracion anterior con DBSCAN (eps=60m, min_samples=10), con el
    cluster mas grande en 0.79% del total (mas seguro que el <3% que toleraba
    la version DBSCAN). El dataset de robos con moto (~16mil casos) es de
    tamano similar al de siniestros de moto (~23mil), lo que explica que la
    misma metodologia haya dado una mejora comparable.

  - GENERAL: todo delito salvo "Vialidad" (que es infraccion de transito, no
    inseguridad). Migrado a HDBSCAN (min_cluster_size=150, min_samples=20).
    El barrido inicial (notebooks/sweep_hdbscan_inseguridad_general.py) se
    corrio sobre una muestra del 20% por el timeout que daba HDBSCAN en el
    entorno de trabajo en la nube sobre el dataset completo (mas de 411 mil
    puntos); ahi esta combinacion ya ganaba claro (90 hotspots, 42.8%
    cobertura, cluster mayor 1.73% vs. 303 hotspots/29.2%/<3% de DBSCAN).
    Se confirmo despues sobre el dataset COMPLETO en la maquina local
    (notebooks/confirmar_hdbscan_general_completo.py, 71.7 minutos de
    corrida): 633 hotspots, cobertura 50.2%, cluster mas grande 0.63% del
    total (ver data/../sweep_log_confirmacion.txt). Gana en las tres metricas
    a la vez frente a DBSCAN, por eso queda como decision final.

Se corre sobre data/delitos_caba.csv (ya descargado por fetch_delitos_caba.py),
tomando la misma ventana de los ultimos 3 anios completos que usa el indice de
inseguridad (2023-2025), para que la capa refleje el presente y no un promedio
de una decada. No necesita red.

Salida: data/hotspots_inseguridad_general.csv y
data/hotspots_inseguridad_moto.csv (cluster, latitud, longitud,
cantidad_delitos, comuna_moda, tipo_delito_moda).

Uso:
    python notebooks/identificar_hotspots_inseguridad.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, HDBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"

EPS_METROS = 60
EPS_RAD = EPS_METROS / 6371000
ANIOS_VENTANA = 3

# MOTO (HDBSCAN) -- ver docstring de arriba para el resultado del barrido.
MOTO_MIN_CLUSTER_SIZE = 12
MOTO_MIN_SAMPLES = 2

# GENERAL (HDBSCAN) -- ver docstring de arriba para el resultado de la
# confirmacion sobre el dataset completo.
GENERAL_MIN_CLUSTER_SIZE = 150
GENERAL_MIN_SAMPLES = 20


def _resumir(df, labels, etiqueta):
    df = df.copy()
    df["cluster"] = labels

    n_clusters = len(set(labels) - {-1})
    n_ruido = int((labels == -1).sum())
    print(f"[{etiqueta}] {n_clusters} hotspots, {n_ruido} aislados de {len(df)} ({n_ruido/len(df)*100:.1f}%)")

    resumen = df[df["cluster"] != -1].groupby("cluster").agg(
        latitud=("latitud", "mean"),
        longitud=("longitud", "mean"),
        cantidad_delitos=("cluster", "count"),
        comuna_moda=("comuna", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        tipo_delito_moda=("tipo_delito", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
    ).reset_index().sort_values("cantidad_delitos", ascending=False)

    tamano_mayor = resumen["cantidad_delitos"].max() if len(resumen) else 0
    if tamano_mayor / len(df) > 0.03:
        print(f"  ADVERTENCIA: el cluster mas grande tiene {tamano_mayor/len(df)*100:.1f}% del total -- "
              f"posible encadenamiento, revisar parametros antes de usar esta salida.")
    return resumen


def clusterizar_dbscan(df, min_samples, etiqueta):
    coords_rad = np.radians(df[["latitud", "longitud"]].values)
    db = DBSCAN(eps=EPS_RAD, min_samples=min_samples, metric="haversine", algorithm="ball_tree").fit(coords_rad)
    return _resumir(df, db.labels_, etiqueta)


def clusterizar_hdbscan(df, min_cluster_size, min_samples, etiqueta):
    coords_rad = np.radians(df[["latitud", "longitud"]].values)
    hd = HDBSCAN(
        min_cluster_size=min_cluster_size, min_samples=min_samples, metric="haversine", algorithm="ball_tree"
    ).fit(coords_rad)
    # A diferencia de DBSCAN, HDBSCAN ya garantiza que todo cluster no ruido
    # tiene al menos min_cluster_size miembros: no hace falta post-filtro.
    return _resumir(df, hd.labels_, etiqueta)


def main():
    delitos = pd.read_csv(DATA / "delitos_caba.csv", low_memory=False)
    delitos = delitos.dropna(subset=["latitud", "longitud"]).copy()
    # (0,0) es un valor centinela de GPS invalido, no un null real -- dropna no lo
    # agarra. Sin este filtro, un cluster entero de casos con coordenada rota
    # (~3463 en el dataset actual, tipo "Lesiones") se cuela como un "hotspot" en
    # el medio del Golfo de Guinea. Encontrado en la validacion cualitativa.
    delitos = delitos[(delitos["latitud"] != 0) | (delitos["longitud"] != 0)].copy()

    anio_max = delitos["anio_dataset"].max()
    anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
    ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()
    print(f"Ventana usada: {anios_incluidos} ({len(ventana)} delitos con coordenadas)")

    general = ventana[ventana["tipo_delito"] != "Vialidad"].copy()
    print("GENERAL (HDBSCAN): puede tardar bastante sobre el dataset completo "
          "(~70 min en la confirmacion previa) -- no es que se colgo.")
    resumen_general = clusterizar_hdbscan(
        general, min_cluster_size=GENERAL_MIN_CLUSTER_SIZE, min_samples=GENERAL_MIN_SAMPLES, etiqueta="GENERAL"
    )
    resumen_general.to_csv(DATA / "hotspots_inseguridad_general.csv", index=False)

    moto = ventana[ventana["uso_moto"] == "SI"].copy()
    resumen_moto = clusterizar_hdbscan(
        moto, min_cluster_size=MOTO_MIN_CLUSTER_SIZE, min_samples=MOTO_MIN_SAMPLES, etiqueta="MOTO"
    )
    resumen_moto.to_csv(DATA / "hotspots_inseguridad_moto.csv", index=False)

    print(f"\nGuardado: {len(resumen_general)} hotspots generales, {len(resumen_moto)} hotspots de robos con moto")


if __name__ == "__main__":
    main()
