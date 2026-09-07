# -*- coding: utf-8 -*-
"""
Descarga el dataset de delitos de CABA (Mapa del Delito, data.buenosaires.gob.ar),
un CSV por anio desde 2016 hasta el mas reciente disponible, y los concatena en
un solo archivo: data/delitos_caba.csv.

Se corre UNA vez (igual que fetch_clima_historico.py y fetch_corredores_geometria.py)
y necesita internet real, por eso hay que correrlo desde tu maquina y no desde el
entorno de Claude:

    cd Desktop\\motosafe-gba
    backend\\venv\\Scripts\\activate
    python notebooks/fetch_delitos_caba.py

El dataset no tiene API en vivo (se actualiza una vez por anio), asi que esto se
corre una sola vez ahora y de nuevo, a mano, cuando el GCBA publique el anio
siguiente -- no hace falta automatizarlo como el clima.

Los nombres de columna del portal pueden variar levemente entre anios (mayus/
minus, con o sin tilde, "tipo_delito" vs "tipo"). El script normaliza los
nombres esperados y avisa por stderr si algun anio no trae una columna clave,
en vez de fallar en silencio con datos incompletos.
"""
import sys
import time
import unicodedata
from pathlib import Path

import httpx
import pandas as pd

SALIDA = Path(__file__).resolve().parent.parent / "data" / "delitos_caba.csv"

# URLs de descarga directa (recurso CSV) por anio, tomadas de
# https://data.buenosaires.gob.ar/dataset/delitos
RECURSOS_CSV = {
    2016: "https://data.buenosaires.gob.ar/dataset/delitos/resource/97ff15b0-fbd5-4064-8856-48798f8347e9/download",
    2017: "https://data.buenosaires.gob.ar/dataset/delitos/resource/217cf8ce-d4bc-477e-ab5a-173e9393478d/download",
    2018: "https://data.buenosaires.gob.ar/dataset/delitos/resource/d4c82cef-3783-4da1-9e47-02df3ebba9e2/download",
    2019: "https://data.buenosaires.gob.ar/dataset/delitos/resource/51ba3181-fabe-4b5f-8cd4-6dfcb24b0d67/download",
    2020: "https://data.buenosaires.gob.ar/dataset/delitos/resource/3f5fe778-bc8c-48ef-96fe-99aa62943152/download",
    2021: "https://data.buenosaires.gob.ar/dataset/delitos/resource/3a691e3e-6df9-412b-a300-6c611733c2c2/download",
    2022: "https://data.buenosaires.gob.ar/dataset/delitos/resource/3fbc3808-14c7-4559-8ba5-f68e919fee40/download",
    2023: "https://data.buenosaires.gob.ar/dataset/delitos/resource/dbec0c29-1ada-40df-b13c-75cf3013ca42/download",
    2024: "https://data.buenosaires.gob.ar/dataset/delitos/resource/49f58c2e-21d7-4766-84e0-4bb753d28478/download",
    2025: "https://data.buenosaires.gob.ar/dataset/delitos/resource/66c0f0f6-e682-403d-abbe-47227d1966fe/download",
}

# Alias posibles (normalizados: minuscula, sin tilde) para cada columna que
# necesitamos, porque el portal no siempre usa el mismo nombre de un anio a otro.
ALIAS = {
    "comuna": ["comuna"],
    "barrio": ["barrio"],
    "latitud": ["latitud", "lat"],
    "longitud": ["longitud", "long", "lon"],
    "fecha": ["fecha"],
    "franja_horaria": ["franja_horaria", "hora"],
    "tipo_delito": ["tipo_delito", "tipo", "tipo_uso"],
    "subtipo_delito": ["subtipo_delito", "subtipo"],
    "uso_moto": ["uso_moto", "moto"],
    "cantidad_victimas": ["cantidad_victimas", "victimas"],
}


def normalizar(texto):
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto


def mapear_columnas(df, anio):
    columnas_normalizadas = {normalizar(c): c for c in df.columns}
    mapeo = {}
    faltantes = []
    for destino, alias in ALIAS.items():
        encontrada = None
        for a in alias:
            if a in columnas_normalizadas:
                encontrada = columnas_normalizadas[a]
                break
        if encontrada:
            mapeo[encontrada] = destino
        elif destino in ("comuna", "latitud", "longitud", "fecha", "tipo_delito"):
            faltantes.append(destino)
    if faltantes:
        print(
            f"  [{anio}] ADVERTENCIA: no se encontraron las columnas {faltantes} "
            f"(columnas reales del archivo: {list(df.columns)})",
            file=sys.stderr,
        )
    return mapeo


def descargar_anio(anio, url):
    print(f"Descargando {anio}...", file=sys.stderr)
    resp = httpx.get(url, timeout=60, follow_redirects=True)
    resp.raise_for_status()
    from io import BytesIO
    df = pd.read_csv(BytesIO(resp.content), sep=None, engine="python")
    mapeo = mapear_columnas(df, anio)
    df = df.rename(columns=mapeo)
    df["anio_dataset"] = anio
    columnas_utiles = [c for c in ALIAS.keys() if c in df.columns] + ["anio_dataset"]
    return df[columnas_utiles]


def main():
    bloques = []
    for anio, url in RECURSOS_CSV.items():
        try:
            bloques.append(descargar_anio(anio, url))
        except Exception as e:
            print(f"  [{anio}] fallo la descarga: {e}", file=sys.stderr)
        time.sleep(1)

    if not bloques:
        print("No se pudo descargar ningun anio, no se genero salida.", file=sys.stderr)
        sys.exit(1)

    completo = pd.concat(bloques, ignore_index=True)
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    completo.to_csv(SALIDA, index=False)
    print(f"\nListo: {len(completo)} delitos guardados en {SALIDA}", file=sys.stderr)
    print(completo["anio_dataset"].value_counts().sort_index(), file=sys.stderr)


if __name__ == "__main__":
    main()
