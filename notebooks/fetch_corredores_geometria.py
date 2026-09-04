# -*- coding: utf-8 -*-
"""
Toma data/corredores_candidatos.csv (generado sin red por
notebooks/identificar_corredores.py: agrupa siniestros por calle y elige los
dos puntos mas alejados de cada una) y para cada calle le pide a OSRM la ruta
real entre esos dos puntos. El resultado es la geometria real de la avenida
(la polilinea que efectivamente sigue las calles), no una linea recta entre
los extremos.

Se corre una sola vez (como fetch_clima_historico.py) y necesita red real,
por eso hay que correrlo desde tu maquina y no desde el entorno de Claude.

Uso:
    cd Desktop\\motosafe-gba
    backend\\venv\\Scripts\\activate
    python notebooks/fetch_corredores_geometria.py
"""
import json
import time
from pathlib import Path

import httpx
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ENTRADA = BASE_DIR / "data" / "corredores_candidatos.csv"
SALIDA = BASE_DIR / "data" / "corredores_riesgo.csv"

OSRM_URL = "https://router.project-osrm.org/route/v1/driving"

candidatos = pd.read_csv(ENTRADA)
print(f"{len(candidatos)} calles candidatas a procesar")

geometrias = []
fallidas = []

for i, fila in candidatos.iterrows():
    url = f"{OSRM_URL}/{fila['lng_a']},{fila['lat_a']};{fila['lng_b']},{fila['lat_b']}"
    try:
        r = httpx.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=10.0)
        r.raise_for_status()
        data = r.json()
        if data.get("code") != "Ok" or not data.get("routes"):
            raise ValueError(f"OSRM sin ruta (code={data.get('code')})")
        coords_lonlat = data["routes"][0]["geometry"]["coordinates"]
        # OSRM devuelve [lon, lat]; Leaflet espera [lat, lon]
        geometria = [[lat, lon] for lon, lat in coords_lonlat]
        geometrias.append(json.dumps(geometria))
    except Exception as e:
        # Si OSRM falla para esta calle puntual, se usa una linea recta entre
        # los dos extremos como respaldo (peor que la ruta real, pero mejor
        # que perder la calle del todo).
        geometrias.append(json.dumps([[fila['lat_a'], fila['lng_a']], [fila['lat_b'], fila['lng_b']]]))
        fallidas.append(fila['calle'])
        print(f"  [{i+1}/{len(candidatos)}] {fila['calle']}: fallo OSRM ({e}), uso linea recta")

    if (i + 1) % 20 == 0:
        print(f"  ... {i+1}/{len(candidatos)} procesadas")
    time.sleep(0.3)  # no golpear el servidor publico de OSRM sin pausas

candidatos["geometria"] = geometrias
candidatos.to_csv(SALIDA, index=False)
print(f"\nListo: {len(candidatos)} corredores guardados en {SALIDA}")
if fallidas:
    print(f"{len(fallidas)} calles usaron linea recta de respaldo (OSRM no pudo con ellas): {fallidas[:10]}{'...' if len(fallidas) > 10 else ''}")
