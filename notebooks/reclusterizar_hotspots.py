# -*- coding: utf-8 -*-
"""
Reclusteriza los siniestros de moto con parámetros ajustados tras un barrido
de eps (radio) x min_samples sobre motos_limpio.csv (ver bitácora de
desarrollo en README.md para el detalle del barrido y la justificación).

Parámetros anteriores: eps=60m, min_samples=10 -> 430 hotspots, 32.1% de
cobertura (siniestros que caen dentro de algún hotspot).
Parámetros nuevos:      eps=100m, min_samples=12 -> ~50% de cobertura, con
un post-filtro que descarta clusters "fragmento" (con menos de min_samples
miembros, un artefacto conocido de cómo sklearn asigna puntos límite en su
implementación greedy) para que la promesa "todo hotspot mostrado tiene al
menos min_samples siniestros reales" se cumpla siempre, sin excepciones.

Es la versión script, reproducible, de la sección 2 (clustering) del
notebook notebooks/01_eda_hotspots_moto.ipynb. Regenera:
  - data/motos_con_clusters.csv (motos_limpio.csv + columna cluster)
  - data/hotspots_moto_caba.csv (agregado por cluster: ubicación, cantidad,
    mortales, graves)

No toca el modelo entrenado (modelo_final.pkl no depende del clustering,
ver notebooks/reentrenar_modelo.py) pero SÍ invalida hotspots_contexto.csv,
que depende de motos_con_clusters.csv — hay que correr reentrenar_modelo.py
después de este script para regenerarlo.

Uso:
    python notebooks/reclusterizar_hotspots.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"

EPS_METROS = 100
MIN_SAMPLES = 12


def main():
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    coords = motos[["latitud_siniestro", "longitud_siniestro"]].values
    coords_rad = np.radians(coords)
    eps_rad = EPS_METROS / 6371000

    db = DBSCAN(eps=eps_rad, min_samples=MIN_SAMPLES, metric="haversine").fit(coords_rad)
    labels = db.labels_.copy()

    # Post-filtro: clusters con menos de MIN_SAMPLES miembros son fragmentos
    # del orden greedy de asignación de sklearn (un core point real, pero la
    # mayoría de sus vecinos ya fueron tomados por un cluster vecino más
    # grande procesado antes) — se tratan como ruido, no como hotspots.
    tamanos = pd.Series(labels)[pd.Series(labels) != -1].value_counts()
    fragmentos = set(tamanos[tamanos < MIN_SAMPLES].index)
    labels = np.array([-1 if l in fragmentos else l for l in labels])

    # Renumerar clusters 0..n-1 de forma contigua (después de descartar
    # fragmentos, los ids originales de DBSCAN quedan con huecos).
    ids_validos = sorted(set(labels) - {-1})
    remapeo = {cid: i for i, cid in enumerate(ids_validos)}
    labels = np.array([remapeo.get(l, -1) for l in labels])

    motos["cluster"] = labels
    n_clusters = len(ids_validos)
    n_ruido = int((labels == -1).sum())
    cobertura = 1 - n_ruido / len(motos)

    print(f"{n_clusters} hotspots encontrados (eps={EPS_METROS}m, min_samples={MIN_SAMPLES})")
    print(f"{n_ruido} siniestros aislados de {len(motos)} ({(1 - cobertura) * 100:.1f}%)")
    print(f"Cobertura: {cobertura * 100:.1f}%")
    print(f"Fragmentos descartados por el post-filtro: {len(fragmentos)}")

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
