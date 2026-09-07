# -*- coding: utf-8 -*-
"""
Barrido de HDBSCAN para los hotspots de inseguridad "GENERAL" (todo delito
salvo Vialidad), pendiente de evaluar desde la migracion de MOTO a HDBSCAN
(ver notebooks/identificar_hotspots_inseguridad.py).

Por que esto es un script aparte y no se corrio ya: el dataset GENERAL tiene
~412 mil puntos (vs. ~16mil de MOTO), y la construccion del arbol de
expansion minima que usa HDBSCAN por dentro no termino en 3 minutos en el
entorno de trabajo en la nube usado para evaluar MOTO, ni con distintos
parametros. Es un dataset grande de verdad: probablemente tarde varios
minutos incluso en una maquina normal, por eso conviene correrlo una vez,
sin apuro, en vez de iterar a mano.

Que hace: prueba una grilla chica de combinaciones min_cluster_size x
min_samples (escaladas a la densidad de GENERAL, ~18x mas denso que un
dataset tipico de siniestros), reportando para cada una cobertura y tamano
del cluster mas grande (mismo chequeo de "riesgo de blob" que en el resto
del proyecto). No escribe ningun CSV de salida -- es solo para decidir si
vale la pena migrar GENERAL de DBSCAN a HDBSCAN, y con que parametros, antes
de tocar notebooks/identificar_hotspots_inseguridad.py.

Uso (puede tardar bastante, dejarlo corriendo de fondo):
    python notebooks/sweep_hdbscan_inseguridad_general.py
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"

ANIOS_VENTANA = 3

# Punto de partida de referencia: DBSCAN (eps=60m, min_samples=100) da 303
# hotspots, 29.2% de cobertura, cluster mas grande <3% del total.
COMBINACIONES = [
    (100, 20), (100, 30), (150, 20), (150, 30),
    (200, 30), (200, 50), (300, 30), (300, 50),
    (500, 50), (500, 80),
]


def main():
    delitos = pd.read_csv(DATA / "delitos_caba.csv", low_memory=False)
    delitos = delitos.dropna(subset=["latitud", "longitud"]).copy()

    anio_max = delitos["anio_dataset"].max()
    anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
    ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()

    general = ventana[ventana["tipo_delito"] != "Vialidad"].copy()
    coords_rad = np.radians(general[["latitud", "longitud"]].values)
    n = len(general)
    print(f"GENERAL: {n} delitos (ventana {anios_incluidos})")
    print("Referencia DBSCAN actual: 303 hotspots, 29.2% cobertura, cluster mayor <3%\n")

    resultados = []
    for mcs, ms in COMBINACIONES:
        t0 = time.time()
        hd = HDBSCAN(
            min_cluster_size=mcs, min_samples=ms, metric="haversine", algorithm="ball_tree"
        ).fit(coords_rad)
        labels = hd.labels_
        n_clusters = len(set(labels) - {-1})
        n_ruido = int((labels == -1).sum())
        cobertura = (1 - n_ruido / n) * 100
        pct_mayor = (max(np.bincount(labels[labels != -1])) / n * 100) if n_clusters > 0 else 0
        dt = time.time() - t0
        resultados.append((mcs, ms, n_clusters, cobertura, pct_mayor, dt))
        print(
            f"mcs={mcs:4d} ms={ms:3d} -> {n_clusters:4d} hotspots, cobertura {cobertura:5.1f}%, "
            f"cluster_mayor {pct_mayor:5.2f}%, {dt:.1f}s",
            flush=True,
        )

    print("\nMejores (cluster_mayor < 3%, ordenados por cobertura):")
    buenos = [r for r in resultados if r[4] < 3.0]
    buenos.sort(key=lambda r: -r[3])
    for mcs, ms, n_clusters, cobertura, pct_mayor, dt in buenos[:5]:
        print(f"  min_cluster_size={mcs}, min_samples={ms} -> {n_clusters} hotspots, "
              f"{cobertura:.1f}% cobertura, cluster mayor {pct_mayor:.2f}%")


if __name__ == "__main__":
    main()
