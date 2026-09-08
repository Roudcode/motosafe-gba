# -*- coding: utf-8 -*-
"""
PROTOTIPO exploratorio, no de produccion: genera hotspots usando H3 (binning
espacial fijo por hexagonos) en vez de clustering por densidad (DBSCAN/HDBSCAN),
para las 3 capas que ya tienen un numero de referencia real:

  - Siniestros de moto:    hoy 740 hotspots (HDBSCAN), 75.6% cobertura, cluster mayor 0.41%
  - Robos con moto:        hoy 502 hotspots (HDBSCAN), 74.3% cobertura, cluster mayor 0.79%
  - Delito general:        hoy 303 hotspots (DBSCAN),  29.2% cobertura, cluster mayor <3%

Motivacion (ver bitacora): calibrar HDBSCAN/DBSCAN requiere iterar a mano
(riesgo de "blob" si el parametro es muy laxo, cobertura baja si es muy
estricto), y en datasets grandes (delito general, 412 mil puntos) HDBSCAN
puede tardar horas o no terminar en una notebook comun. H3 no tiene ese
costo: es una grilla fija de hexagonos, contar delitos por celda es una
operacion lineal, sin arbol ni parametro de radio que ajustar por prueba y
error.

Este script NO pisa ningun CSV de produccion. Escribe versiones "_h3_preview"
al lado de los reales, con el mismo esquema de columnas, para poder
comparar. Tambien genera un mapa HTML (data/preview_h3_vs_produccion.html)
con ambas versiones superpuestas (con control de capas) para inspeccion
visual antes de decidir si migrar de verdad.

Uso:
    python notebooks/prototipo_h3_hotspots.py
"""
from pathlib import Path

import folium
import h3
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data"
ANIOS_VENTANA = 3

# Parametros elegidos del barrido exploratorio (ver bitacora): resolucion 9
# (~200m de lado, similar a una cuadra) balancea cobertura alta con una
# cantidad de zonas todavia razonable para mostrar en un mapa.
RESOLUCION = 9
MIN_POR_CELDA = {"siniestros_moto": 5, "robos_moto": 5, "delito_general": 8}


def _hotspots_h3(df, lat_col, lng_col, min_por_celda, columnas_extra=None):
    """Agrupa por celda H3, agrega columnas extra (moda de comuna/tipo, suma
    de mortales/graves) igual que hacen los scripts de produccion, y devuelve
    un DataFrame con el mismo tipo de columnas que los CSV reales."""
    df = df.copy()
    df["hex"] = df.apply(lambda r: h3.latlng_to_cell(r[lat_col], r[lng_col], RESOLUCION), axis=1)
    conteo = df.groupby("hex").size()
    celdas_validas = conteo[conteo >= min_por_celda].index

    filas = []
    for i, hex_id in enumerate(celdas_validas):
        grupo = df[df["hex"] == hex_id]
        lat, lng = h3.cell_to_latlng(hex_id)
        fila = {"cluster": i, "latitud": lat, "longitud": lng, "cantidad": len(grupo)}
        if columnas_extra:
            for nombre, col in columnas_extra.items():
                if col in grupo.columns:
                    fila[nombre] = grupo[col].mode().iloc[0] if not grupo[col].mode().empty else None
        filas.append(fila)
    resumen = pd.DataFrame(filas).sort_values("cantidad", ascending=False).reset_index(drop=True)
    resumen["cluster"] = range(len(resumen))

    n = len(df)
    cobertura = resumen["cantidad"].sum() / n * 100
    cluster_mayor = (resumen["cantidad"].max() / n * 100) if len(resumen) else 0
    print(f"  -> {len(resumen)} hotspots, cobertura {cobertura:.1f}%, cluster mayor {cluster_mayor:.2f}%")
    return resumen


def _agregar_al_mapa(mapa, df, nombre_capa, color, lat_col="latitud", lng_col="longitud", cantidad_col="cantidad"):
    capa = folium.FeatureGroup(name=nombre_capa, show=False)
    for _, fila in df.iterrows():
        folium.CircleMarker(
            location=[fila[lat_col], fila[lng_col]],
            radius=3 + min(fila[cantidad_col] ** 0.5, 12),
            color=color, fill=True, fill_opacity=0.5, weight=1,
            popup=f"{nombre_capa}: {fila[cantidad_col]}",
        ).add_to(capa)
    capa.add_to(mapa)


def main():
    mapa = folium.Map(location=[-34.61, -58.44], zoom_start=12, tiles="OpenStreetMap")

    # --- 1) Siniestros de moto ---
    print("\n=== Siniestros de moto ===")
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    h3_moto = _hotspots_h3(motos, "latitud_siniestro", "longitud_siniestro", MIN_POR_CELDA["siniestros_moto"])
    h3_moto.rename(columns={"cantidad": "cantidad_siniestros"}).to_csv(
        DATA / "hotspots_moto_caba_h3_preview.csv", index=False
    )
    prod_moto = pd.read_csv(DATA / "hotspots_moto_caba.csv")
    _agregar_al_mapa(mapa, prod_moto.rename(columns={"cantidad_siniestros": "cantidad"}),
                      "Siniestros moto - PRODUCCION (HDBSCAN)", "orange")
    _agregar_al_mapa(mapa, h3_moto.rename(columns={"cantidad_siniestros": "cantidad"}) if "cantidad_siniestros" in h3_moto else h3_moto,
                      "Siniestros moto - H3 (preview)", "red")

    # --- 2) Robos y delito general (mismo dataset base) ---
    delitos = pd.read_csv(DATA / "delitos_caba.csv", low_memory=False)
    delitos = delitos.dropna(subset=["latitud", "longitud"]).copy()
    anio_max = delitos["anio_dataset"].max()
    anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
    ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()

    print("\n=== Robos con moto ===")
    moto_delitos = ventana[ventana["uso_moto"] == "SI"].copy()
    h3_robos = _hotspots_h3(
        moto_delitos, "latitud", "longitud", MIN_POR_CELDA["robos_moto"],
        columnas_extra={"comuna_moda": "comuna", "tipo_delito_moda": "tipo_delito"},
    )
    h3_robos.rename(columns={"cantidad": "cantidad_delitos"}).to_csv(
        DATA / "hotspots_inseguridad_moto_h3_preview.csv", index=False
    )
    prod_robos = pd.read_csv(DATA / "hotspots_inseguridad_moto.csv")
    _agregar_al_mapa(mapa, prod_robos.rename(columns={"cantidad_delitos": "cantidad"}),
                      "Robos con moto - PRODUCCION (HDBSCAN)", "cyan")
    _agregar_al_mapa(mapa, h3_robos.rename(columns={"cantidad_delitos": "cantidad"}),
                      "Robos con moto - H3 (preview)", "blue")

    print("\n=== Delito general ===")
    general = ventana[ventana["tipo_delito"] != "Vialidad"].copy()
    h3_general = _hotspots_h3(
        general, "latitud", "longitud", MIN_POR_CELDA["delito_general"],
        columnas_extra={"comuna_moda": "comuna", "tipo_delito_moda": "tipo_delito"},
    )
    h3_general.rename(columns={"cantidad": "cantidad_delitos"}).to_csv(
        DATA / "hotspots_inseguridad_general_h3_preview.csv", index=False
    )
    prod_general = pd.read_csv(DATA / "hotspots_inseguridad_general.csv")
    _agregar_al_mapa(mapa, prod_general.rename(columns={"cantidad_delitos": "cantidad"}),
                      "Delito general - PRODUCCION (DBSCAN)", "yellow")
    _agregar_al_mapa(mapa, h3_general.rename(columns={"cantidad_delitos": "cantidad"}),
                      "Delito general - H3 (preview)", "lime")

    folium.LayerControl(collapsed=False).add_to(mapa)
    salida = DATA / "preview_h3_vs_produccion.html"
    mapa.save(str(salida))
    print(f"\nMapa comparativo guardado en {salida}")
    print("Abrilo en el navegador y activa/desactiva capas para comparar produccion vs. H3.")


if __name__ == "__main__":
    main()
