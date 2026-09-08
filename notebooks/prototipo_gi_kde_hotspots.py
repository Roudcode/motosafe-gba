# -*- coding: utf-8 -*-
"""
PROTOTIPO exploratorio (no de produccion): prueba dos metodos mas, en las
mismas 3 capas con numero de referencia real, para completar la comparacion
metodologica antes de cerrar la decision de clustering:

  - Getis-Ord Gi* (hot spot analysis estadistico, el estandar en GIS/criminologia,
    ej. ArcGIS "Hot Spot Analysis"): en vez de agrupar por densidad o contar por
    grilla, calcula un z-score de significancia por celda (cuanto se desvia su
    vecindad de lo esperable por azar). Corre sobre la misma grilla H3 res9 ya
    usada, con pesos de contiguedad hexagonal (vecinos = grid_disk k=1).

  - KDE (Kernel Density Estimation) discretizado: rasteriza los puntos en una
    grilla fina (~100m), suaviza con un filtro gaussiano (equivalente a KDE
    pero O(grilla) en vez de O(n*m), viable para 400k+ puntos), y define
    hotspots como componentes conexas por encima de un percentil de densidad.

Referencia (ver bitacora / prototipo H3):
  - Siniestros de moto: 740 hotspots (HDBSCAN), 75.6% cobertura, cluster mayor 0.41%
  - Robos con moto:     502 hotspots (HDBSCAN), 74.3% cobertura, cluster mayor 0.79%
  - Delito general:     303 hotspots (DBSCAN),  29.2% cobertura, cluster mayor <3%
  - H3 percentil (delito general, el unico donde H3 mostro mejora real):
    ~277-557 hotspots, 33.3%-50.8% cobertura

No escribe ni modifica ningun CSV de produccion. Solo imprime resultados.
"""
from pathlib import Path

import h3
import numpy as np
import pandas as pd
from scipy import ndimage
from libpysal.weights import W
from esda.getisord import G_Local

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"
ANIOS_VENTANA = 3
RESOLUCION_H3 = 9

# ---------------------------------------------------------------------------
# Getis-Ord Gi*
# ---------------------------------------------------------------------------

def gi_star_hotspots(df, lat_col, lng_col, nombre, zscores_a_probar=(1.96, 2.58)):
    print(f"\n--- Getis-Ord Gi* | {nombre} ---", flush=True)
    d = df.copy()
    d["hex"] = d.apply(lambda r: h3.latlng_to_cell(r[lat_col], r[lng_col], RESOLUCION_H3), axis=1)
    conteo = d.groupby("hex").size()
    celdas = list(conteo.index)
    idx = {c: i for i, c in enumerate(celdas)}
    valores = conteo.values.astype(float)

    vecinos = {}
    for c in celdas:
        anillo = h3.grid_disk(c, 1)
        vs = [idx[v] for v in anillo if v != c and v in idx]
        vecinos[idx[c]] = vs
    islas = {i for i, vs in vecinos.items() if len(vs) == 0}
    if islas:
        print(f"  {len(islas)} celdas aisladas (sin vecinos ocupados) excluidas del calculo de Gi*", flush=True)

    w_dict = {
        i: [v for v in vs if v not in islas]
        for i, vs in vecinos.items() if i not in islas
    }
    w_dict = {i: vs for i, vs in w_dict.items() if len(vs) > 0}
    w = W(w_dict)
    w.transform = "B"

    ids_validos = list(w_dict.keys())
    valores_validos = valores[ids_validos]
    gi = G_Local(valores_validos, w, star=True, permutations=199)

    n_total = len(d)
    for z_umbral in zscores_a_probar:
        hot = gi.Zs >= z_umbral
        n_hot = int(hot.sum())
        cantidades_hot = valores_validos[hot]
        cobertura = cantidades_hot.sum() / n_total * 100
        cluster_mayor = (cantidades_hot.max() / n_total * 100) if n_hot else 0
        conf = "95%" if z_umbral < 2 else "99%"
        print(f"  z>={z_umbral} ({conf} confianza): {n_hot} celdas hotspot, "
              f"cobertura {cobertura:.1f}%, celda mayor {cluster_mayor:.2f}%", flush=True)


# ---------------------------------------------------------------------------
# KDE discretizado (grilla + filtro gaussiano + componentes conexas)
# ---------------------------------------------------------------------------

def kde_hotspots(df, lat_col, lng_col, nombre, percentiles=(90, 95, 97)):
    print(f"\n--- KDE (grilla + gaussiano) | {nombre} ---", flush=True)
    lat = df[lat_col].values
    lng = df[lng_col].values
    n_total = len(df)

    bin_lat = 100 / 111000
    bin_lng = 100 / 91500

    lat_bins = np.arange(lat.min() - bin_lat, lat.max() + bin_lat, bin_lat)
    lng_bins = np.arange(lng.min() - bin_lng, lng.max() + bin_lng, bin_lng)

    hist, lat_edges, lng_edges = np.histogram2d(lat, lng, bins=[lat_bins, lng_bins])
    suavizado = ndimage.gaussian_filter(hist, sigma=2.0)

    lat_idx = np.clip(np.digitize(lat, lat_edges) - 1, 0, suavizado.shape[0] - 1)
    lng_idx = np.clip(np.digitize(lng, lng_edges) - 1, 0, suavizado.shape[1] - 1)

    estructura = np.ones((3, 3))
    for p in percentiles:
        umbral = np.percentile(suavizado[suavizado > 0], p)
        mascara = suavizado >= umbral
        etiquetas, n_hot = ndimage.label(mascara, structure=estructura)

        etiqueta_por_punto = etiquetas[lat_idx, lng_idx]
        en_hotspot = etiqueta_por_punto > 0
        cobertura = en_hotspot.sum() / n_total * 100

        if n_hot:
            conteos_por_cluster = np.bincount(etiqueta_por_punto[en_hotspot])
            cluster_mayor = conteos_por_cluster.max() / n_total * 100
        else:
            cluster_mayor = 0

        print(f"  percentil {p}: {n_hot} hotspots, cobertura {cobertura:.1f}%, cluster mayor {cluster_mayor:.2f}%", flush=True)


def main():
    print("=== Siniestros de moto (ref: HDBSCAN 740 hotspots, 75.6% cob., 0.41% mayor) ===", flush=True)
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    gi_star_hotspots(motos, "latitud_siniestro", "longitud_siniestro", "Siniestros de moto")
    kde_hotspots(motos, "latitud_siniestro", "longitud_siniestro", "Siniestros de moto")

    delitos = pd.read_csv(DATA / "delitos_caba.csv", low_memory=False)
    delitos = delitos.dropna(subset=["latitud", "longitud"]).copy()
    delitos = delitos[(delitos["latitud"].between(-34.75, -34.50)) & (delitos["longitud"].between(-58.55, -58.33))].copy()
    anio_max = delitos["anio_dataset"].max()
    anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
    ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()

    print("\n=== Robos con moto (ref: HDBSCAN 502 hotspots, 74.3% cob., 0.79% mayor) ===", flush=True)
    moto_delitos = ventana[ventana["uso_moto"] == "SI"].copy()
    gi_star_hotspots(moto_delitos, "latitud", "longitud", "Robos con moto")
    kde_hotspots(moto_delitos, "latitud", "longitud", "Robos con moto")

    print("\n=== Delito general (ref: DBSCAN 303 hotspots, 29.2% cob., <3% mayor; "
          "H3 percentil 33.3%-50.8% cob.) ===", flush=True)
    general = ventana[ventana["tipo_delito"] != "Vialidad"].copy()
    gi_star_hotspots(general, "latitud", "longitud", "Delito general")
    kde_hotspots(general, "latitud", "longitud", "Delito general")


if __name__ == "__main__":
    main()
