# -*- coding: utf-8 -*-
"""
Reclusteriza los siniestros de moto. Historial de parámetros (ver bitácora
de desarrollo en README.md para el detalle de cada barrido):

  1. eps=60m, min_samples=10 (DBSCAN)  -> 430 hotspots, 32.1% de cobertura.
  2. eps=100m, min_samples=12 (DBSCAN) -> 412 hotspots, 49.9% de cobertura,
     con post-filtro de fragmentos (ver historial en git de esta misma
     función para el detalle de esa versión).
  3. HDBSCAN (actual)                  -> 740 hotspots, 75.6% de cobertura.

Se pasó de DBSCAN a HDBSCAN porque DBSCAN usa un radio fijo (eps): para
cubrir zonas de densidad más baja hacía falta agrandar eps, pero eso
arriesgaba fusionar clusters en zonas densas (un "blob" que se come el
1-2% de todos los siniestros en una sola zona, inútil para priorizar).
HDBSCAN no usa un radio fijo, se adapta a la densidad local de cada zona,
así que puede encontrar clusters chicos y compactos en zonas de baja
densidad sin arriesgar ese efecto en las zonas densas.

Se comparó un barrido de min_cluster_size x min_samples chequeando en cada
combinación el tamaño del cluster más grande como % del total (mismo
chequeo de "riesgo de blob" que se usó para calibrar DBSCAN). Con
min_cluster_size=12 ((mismo piso que antes: todo hotspot mostrado tiene al
menos 12 siniestros reales, ahora garantizado nativamente por HDBSCAN, sin
necesitar post-filtro) y min_samples=3, el cluster más grande da 0.41% del
total — más chico que el 0.73% que daba la configuración DBSCAN anterior,
o sea que además de mejorar la cobertura, este resultado es más seguro.

Es la versión script, reproducible, de la sección 2 (clustering) del
notebook notebooks/01_eda_hotspots_moto.ipynb. Regenera:
  - data/motos_con_clusters.csv (motos_limpio.csv + columna cluster)
  - data/hotspots_moto_caba.csv (agregado por cluster: ubicación, cantidad,
    mortales, graves)

No toca el modelo entrenado ((modelo_final.pkl no depende del clustering,
ver notebooks/reentrenar_modelo.py) pero SI invalida hotspots_contexto.csv,
que depende de motos_con_clusters.csv — hay que correr reentrenar_modelo.py
después de este script para regenerarlo.

Uso:
    python notebooks/reclusterizar_hotspots.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"

MIN_CLUSTER_SIZE = 12
MIN_SAMPLES = 3


def main():
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    coords = motos[["latitud_siniestro", "longitud_siniestro"]].values
    coords_rad = np.radians(coords)

    hd = HDBSCAN(min_cluster_size=MIN_CLUSTER_SIZE, min_samples=MIN_SAMPLES, metric="haversine").fit(coords_rad)
    labels = hd.labels_.copy()

    # A diferencia de DBSCAN, HDBSCAN ya garantiza que todo cluster no ruido
    # tiene al menos MIN_CLUSTER_SIZE miembros: no hace falta post-filtro de
    # fragmentos. Solo queda renumerar 0..n-1 de forma contigua.
    ids_validos = sorted(set(labels) - {-1})
    remapeo = {cid: i for i, cid in enumerate(ids_validos)}
    labels = np.array([remapeo.get(l, -1) for l in labels])

    motos["cluster"] = labels
    n_clusters = len(ids_validos)
    n_ruido = int((labels == -1).sum())
    cobertura = 1 - n_ruido / len(motos)

    print(f"{n_clusters} hotspots encontrados (HDBSCAN, min_cluster_size={MIN_CLUSTER_SIZE}, min_samples={MIN_SAMPLES})")
    print(f"{n_ruido} siniestros aislados de {len(motos)} ({(1 - cobertura) * 100:.1f}%)")
    print(f"Cobertura: {cobertura * 100:.1f}%")

    motos.to_csv(DATA / "motos_con_clusters.csv", index=False)
    print(f"\nmotos_con_clusters.csv actualizado ({len(motos)} filas)")

    # --- Agregado por cluster para hotspots_moto_caba.csv ---
    con_cluster = motos[motos["cluster"] != -1].copy()
    agregado = con_cluster.groupby("cluster").agg(
        latitud=("latitud_siniestro", "mean"),
        longitud=("longitud_siniestro", "mean"),
        cantidad_siniestros=("id_siniestro", "count"),
        mortales=("gravedad_siniestro", lambda s: (s == "MORTAL").sum()),
        graves=("gravedad_siniestro", lambda s: (s == "GRAVE").sum()),
    ).reset_index()

    agregado.to_csv(DATA / "hotspots_moto_caba.csv", index=False)
    print(f"hotspots_moto_caba.csv actualizado ({len(agregado)} hotspots)")
    print("\nSiguiente paso: correr notebooks/reentrenar_modelo.py para regenerar")
    print("hotspots_contexto.csv (depende de motos_con_clusters.csv), y despues")
    print("'python cargar_hotspots.py' en backend/ para recargar la base.")


if __name__ == "__main__":
    main()
