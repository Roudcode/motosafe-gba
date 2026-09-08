# -*- coding: utf-8 -*-
"""
Barrido de HDBSCAN para los hotspots de inseguridad "GENERAL" (todo delito
salvo Vialidad), pendiente de evaluar desde la migracion de MOTO a HDBSCAN
(ver notebooks/identificar_hotspots_inseguridad.py).

Estrategia en dos pasos, pensada para no quemar 20+ minutos por combinacion
en una notebook comun:
  0) Prueba de humo (~5 mil puntos) para confirmar que el pipeline corre
     bien en esta maquina antes de ir a algo mas grande.
  1) Probar la grilla de parametros sobre una MUESTRA aleatoria (~80 mil
     puntos, ~20% del dataset real) -- suficiente para ver que combinacion
     da buena cobertura sin encadenamiento, en una fraccion del tiempo.
  2) Confirmar la mejor combinacion de la muestra corriendola una sola vez
     sobre el dataset COMPLETO (412 mil puntos), para tener el numero real
     antes de decidir si migrar notebooks/identificar_hotspots_inseguridad.py.

Las combinaciones se prueban de la mas liviana a la mas pesada
(min_cluster_size mas grande primero), para tener señal de progreso rapido
en vez de esperar la peor combinacion primero. NO se usa n_jobs=-1 (se probo
y se descarto: en Windows puede generar un deadlock entre el paralelismo de
sklearn y las librerias numericas de base, que deja el proceso colgado sin
usar CPU y sin imprimir nada mas -- justo el sintoma que se vio en la
primera corrida de esta version).

Uso:
    python notebooks/sweep_hdbscan_inseguridad_general.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"

ANIOS_VENTANA = 3
FRACCION_MUESTRA = 0.2
SEMILLA = 42

# Ordenadas de la mas liviana (min_cluster_size mas grande) a la mas pesada.
# Punto de partida de referencia: DBSCAN (eps=60m, min_samples=100) da 303
# hotspots, 29.2% de cobertura, cluster mas grande <3% del total.
COMBINACIONES = [
    (500, 80), (500, 50), (300, 50), (300, 30),
    (200, 50), (200, 30), (150, 30), (150, 20),
    (100, 30), (100, 20),
]


def _correr_grilla(coords_rad, n_total, etiqueta):
    print(f"\n--- Grilla sobre {etiqueta} ({len(coords_rad)} puntos) ---", flush=True)
    resultados = []
    for mcs, ms in COMBINACIONES:
        print(f"  probando mcs={mcs:4d} ms={ms:3d} ...", end=" ", flush=True)
        sys.stdout.flush()
        t0 = time.time()
        hd = HDBSCAN(
            min_cluster_size=mcs, min_samples=ms, metric="haversine",
            algorithm="ball_tree",
        ).fit(coords_rad)
        labels = hd.labels_
        n_clusters = len(set(labels) - {-1})
        n_ruido = int((labels == -1).sum())
        cobertura = (1 - n_ruido / len(coords_rad)) * 100
        pct_mayor = (max(np.bincount(labels[labels != -1])) / len(coords_rad) * 100) if n_clusters > 0 else 0
        dt = time.time() - t0
        resultados.append((mcs, ms, n_clusters, cobertura, pct_mayor, dt))
        print(
            f"{n_clusters:4d} hotspots, cobertura {cobertura:5.1f}%, "
            f"cluster_mayor {pct_mayor:5.2f}%, {dt:.1f}s",
            flush=True,
        )
    return resultados


def main():
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
    print("Referencia DBSCAN actual: 303 hotspots, 29.2% cobertura, cluster mayor <3%", flush=True)

    # Paso 0: prueba de humo con un puñado de puntos, para confirmar que HDBSCAN
    # corre sin problemas en esta maquina antes de ir a algo mas grande. Si esto
    # se cuelga tambien, el problema es del entorno (no del tamano del dataset).
    print("\n--- Prueba de humo (5000 puntos) ---", flush=True)
    humo = general.sample(n=min(5000, n), random_state=SEMILLA)
    coords_humo = np.radians(humo[["latitud", "longitud"]].values)
    t0 = time.time()
    HDBSCAN(min_cluster_size=30, min_samples=10, metric="haversine", algorithm="ball_tree").fit(coords_humo)
    print(f"  OK, {time.time()-t0:.1f}s -- el entorno anda bien, sigue la muestra grande.", flush=True)

    # Paso 1: muestra aleatoria (~20%) para probar la grilla rapido.
    print(f"\nArmando muestra del {int(FRACCION_MUESTRA*100)}% ...", flush=True)
    muestra = general.sample(frac=FRACCION_MUESTRA, random_state=SEMILLA)
    coords_muestra = np.radians(muestra[["latitud", "longitud"]].values)
    print(f"  {len(muestra)} puntos listos.", flush=True)
    resultados_muestra = _correr_grilla(coords_muestra, n, "MUESTRA (20%)")

    print("\nMejores en la muestra (cluster_mayor < 3%, ordenados por cobertura):")
    buenos = [r for r in resultados_muestra if r[4] < 3.0]
    buenos.sort(key=lambda r: -r[3])
    for mcs, ms, n_clusters, cobertura, pct_mayor, dt in buenos[:5]:
        print(f"  min_cluster_size={mcs}, min_samples={ms} -> {n_clusters} hotspots, "
              f"{cobertura:.1f}% cobertura, cluster mayor {pct_mayor:.2f}%")

    if not buenos:
        print("\nNinguna combinacion de la grilla se mantuvo bajo el 3% de cluster_mayor "
              "en la muestra -- no se confirma ninguna sobre el dataset completo.")
        return

    # Paso 2: confirmar la mejor combinacion de la muestra sobre el dataset COMPLETO.
    mejor_mcs, mejor_ms = buenos[0][0], buenos[0][1]
    print(f"\n--- Confirmando la mejor combinacion (mcs={mejor_mcs}, ms={mejor_ms}) "
          f"sobre el dataset COMPLETO ({n} puntos) ---")
    coords_completo = np.radians(general[["latitud", "longitud"]].values)
    t0 = time.time()
    hd = HDBSCAN(
        min_cluster_size=mejor_mcs, min_samples=mejor_ms, metric="haversine",
        algorithm="ball_tree",
    ).fit(coords_completo)
    labels = hd.labels_
    n_clusters = len(set(labels) - {-1})
    n_ruido = int((labels == -1).sum())
    cobertura = (1 - n_ruido / n) * 100
    pct_mayor = (max(np.bincount(labels[labels != -1])) / n * 100) if n_clusters > 0 else 0
    dt = time.time() - t0
    print(f"RESULTADO FINAL: {n_clusters} hotspots, cobertura {cobertura:.1f}%, "
          f"cluster mayor {pct_mayor:.2f}%, {dt:.1f}s")


if __name__ == "__main__":
    main()
