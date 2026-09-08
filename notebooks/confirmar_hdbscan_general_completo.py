# -*- coding: utf-8 -*-
"""
Confirma directamente sobre el dataset COMPLETO de delito general (sin
repetir el barrido sobre la muestra, ya hecho en sweep_hdbscan_inseguridad_general.py)
la combinacion que gano ahi: min_cluster_size=150, min_samples=20
-> en la muestra del 20% dio 90 hotspots, 42.8% cobertura, cluster mayor 1.73%.

Uso:
    python notebooks/confirmar_hdbscan_general_completo.py
"""
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"
ANIOS_VENTANA = 3
MCS, MS = 150, 20

print("Cargando delitos_caba.csv ...", flush=True)
t0 = time.time()
delitos = pd.read_csv(DATA / "delitos_caba.csv", low_memory=False)
delitos = delitos.dropna(subset=["latitud", "longitud"]).copy()
print(f"  {len(delitos)} filas cargadas en {time.time()-t0:.1f}s", flush=True)

anio_max = delitos["anio_dataset"].max()
anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()
general = ventana[ventana["tipo_delito"] != "Vialidad"].copy()
n = len(general)
print(f"GENERAL: {n} delitos (ventana {anios_incluidos})", flush=True)
print(f"Referencia DBSCAN actual: 303 hotspots, 29.2% cobertura, cluster mayor <3%", flush=True)
print(f"Referencia muestra 20% con mcs={MCS}, ms={MS}: 90 hotspots, 42.8% cobertura, cluster mayor 1.73%", flush=True)

print(f"\n--- Corriendo mcs={MCS}, ms={MS} sobre el dataset COMPLETO ({n} puntos) ---", flush=True)
print("(esto no imprime nada mas hasta terminar, puede tardar bastante -- no es que se colgo)", flush=True)
coords = np.radians(general[["latitud", "longitud"]].values)
t0 = time.time()
hd = HDBSCAN(min_cluster_size=MCS, min_samples=MS, metric="haversine", algorithm="ball_tree").fit(coords)
labels = hd.labels_
n_clusters = len(set(labels) - {-1})
n_ruido = int((labels == -1).sum())
cobertura = (1 - n_ruido / n) * 100
pct_mayor = (max(np.bincount(labels[labels != -1])) / n * 100) if n_clusters > 0 else 0
dt = time.time() - t0
print(f"\nRESULTADO FINAL: {n_clusters} hotspots, cobertura {cobertura:.1f}%, "
      f"cluster mayor {pct_mayor:.2f}%, {dt:.1f}s", flush=True)
