# -*- coding: utf-8 -*-
"""
Hotspots de inseguridad (robos, hurtos, lesiones, amenazas, homicidios), misma
metodologia que los hotspots de siniestros de moto (01_eda_hotspots_moto.ipynb,
seccion 2): DBSCAN con distancia haversine, eps=60m (~una cuadra). No usa el
indice de inseguridad por comuna (ese es demasiado grueso -- 15 valores -- para
andar como capa propia en el mapa); esto agrupa los delitos reales, punto por
punto, igual que se hizo con los siniestros.

Se corre sobre data/delitos_caba.csv (ya descargado por fetch_delitos_caba.py),
tomando la misma ventana de los ultimos 3 anios completos que usa el indice de
inseguridad (2023-2025), para que la capa refleje el presente y no un promedio
de una decada. No necesita red.

Dos variantes, con min_samples elegido empiricamente para cada una (mismo eps,
pero la densidad de datos es muy distinta y con un min_samples parejo una de
las dos termina en un "cluster gigante" que fusiona media ciudad -- el mismo
problema de "encadenamiento" que documenta 01_eda_hotspots_moto.ipynb con 300m
de radio, aca aparece por exceso de puntos en vez de exceso de radio):

  - GENERAL: todo delito salvo "Vialidad" (que es infraccion de transito, no
    inseguridad). min_samples=100 (los datos son ~18x mas densos que los
    siniestros de moto, así que el min_samples tambien escala) -> ~300
    hotspots, cluster mas grande <3% del total (chequeado, sin encadenamiento).

  - MOTO: delitos con uso_moto=SI (en la practica, 100% categoria Robo -- el
    GCBA no distingue si la moto fue el medio del robo o el objeto robado).
    min_samples=10, igual que los siniestros de moto (dataset mucho mas chico,
    ~16mil casos, no hace falta escalar el min_samples).

Salida: data/hotspots_inseguridad_general.csv y
data/hotspots_inseguridad_moto.csv (cluster, latitud, longitud,
cantidad_delitos, comuna_moda, tipo_delito_moda).

Uso:
    python notebooks/identificar_hotspots_inseguridad.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"

EPS_METROS = 60
EPS_RAD = EPS_METROS / 6371000
ANIOS_VENTANA = 3


def clusterizar(df, min_samples, etiqueta):
    coords_rad = np.radians(df[["latitud", "longitud"]].values)
    db = DBSCAN(eps=EPS_RAD, min_samples=min_samples, metric="haversine", algorithm="ball_tree").fit(coords_rad)
    df = df.copy()
    df["cluster"] = db.labels_

    n_clusters = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)
    n_ruido = int((db.labels_ == -1).sum())
    print(f"[{etiqueta}] {n_clusters} hotspots, {n_ruido} aislados de {len(df)} ({n_ruido/len(df)*100:.1f}%)")

    resumen = df[df["cluster"] != -1].groupby("cluster").agg(
        latitud=("latitud", "mean"),
        longitud=("longitud", "mean"),
        cantidad_delitos=("cluster", "count"),
        comuna_moda=("comuna", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        tipo_delito_moda=("tipo_delito", lambda x: x.mode().iloc[0] if not x.mode().empty else None),
    ).reset_index().sort_values("cantidad_delitos", ascending=False)

    tamano_mayor = resumen["cantidad_delitos"].max() if len(resumen) else 0
    if tamano_mayor / len(df) > 0.10:
        print(f"  ADVERTENCIA: el cluster mas grande tiene {tamano_mayor/len(df)*100:.1f}% del total -- "
              f"posible encadenamiento, revisar min_samples antes de usar esta salida.")
    return resumen


def main():
    delitos = pd.read_csv(DATA / "delitos_caba.csv", low_memory=False)
    delitos = delitos.dropna(subset=["latitud", "longitud"]).copy()

    anio_max = delitos["anio_dataset"].max()
    anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
    ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()
    print(f"Ventana usada: {anios_incluidos} ({len(ventana)} delitos con coordenadas)")

    general = ventana[ventana["tipo_delito"] != "Vialidad"].copy()
    resumen_general = clusterizar(general, min_samples=100, etiqueta="GENERAL")
    resumen_general.to_csv(DATA / "hotspots_inseguridad_general.csv", index=False)

    moto = ventana[ventana["uso_moto"] == "SI"].copy()
    resumen_moto = clusterizar(moto, min_samples=10, etiqueta="MOTO")
    resumen_moto.to_csv(DATA / "hotspots_inseguridad_moto.csv", index=False)

    print(f"\nGuardado: {len(resumen_general)} hotspots generales, {len(resumen_moto)} hotspots de robos con moto")


if __name__ == "__main__":
    main()
