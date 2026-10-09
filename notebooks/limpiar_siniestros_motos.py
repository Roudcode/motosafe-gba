# -*- coding: utf-8 -*-
"""
Paso 0 del pipeline (A19): limpieza de data/siniestros_viales_hechos.csv y
filtro a siniestros de motociclistas con coordenadas validas. Es la version
no interactiva de la seccion 1 ("Carga y limpieza de los datos") del notebook
historico notebooks/01_eda_hotspots_moto.ipynb -- ver docs/modelo/PIPELINE_CANONICO.md.

Pasos (en el mismo orden que el notebook):
  1. Saca la fila con el error de exportacion de Excel ('#REF!') en
     modo_desplazamiento_victima.
  2. Normaliza a mayusculas sin espacios las columnas de texto que se usan
     para filtrar y modelar (modo_desplazamiento_victima, gravedad_siniestro,
     tipo_de_via_siniestro).
  3. Agrega la columna 'comuna' (entero) extraida de comuna_siniestro con una
     regex, para no depender del formato de texto exacto ("Comuna 8", etc.).
  4. Convierte latitud/longitud a numerico (coercion a NaN si no son validas)
     y descarta las filas sin coordenadas.
  5. Filtra a modo_desplazamiento_victima == 'MOTO'.

data/siniestros_viales_victimas.csv NO se usa aca: el notebook lo carga en
esta misma seccion pero nunca lo combina con 'hechos' antes de guardar
motos_limpio.csv (se vuelve a leer, limpio e independiente, en la seccion de
ablacion demografica -- A03). Mantenerlo fuera de este script no es una
simplificacion: es lo que el notebook historico efectivamente hace.

Entrada: data/siniestros_viales_hechos.csv
Salida: data/motos_limpio.csv

    python notebooks/limpiar_siniestros_motos.py
"""
import re
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ENTRADA = BASE_DIR / "data" / "siniestros_viales_hechos.csv"
SALIDA = BASE_DIR / "data" / "motos_limpio.csv"

COLUMNAS_TEXTO = ["modo_desplazamiento_victima", "gravedad_siniestro", "tipo_de_via_siniestro"]
VALOR_ERROR_EXCEL = "#¡REF!"


def normalizar_comuna(valor):
    if pd.isna(valor):
        return None
    match = re.search(r"\d+", str(valor))
    return int(match.group()) if match else None


def main():
    hechos = pd.read_csv(ENTRADA, encoding="utf-8-sig", sep=";", low_memory=False)
    print(f"Hechos: {hechos.shape}")

    hechos = hechos[hechos["modo_desplazamiento_victima"] != VALOR_ERROR_EXCEL].copy()
    for col in COLUMNAS_TEXTO:
        hechos[col] = hechos[col].str.strip().str.upper()

    hechos["comuna"] = hechos["comuna_siniestro"].apply(normalizar_comuna)

    hechos["latitud_siniestro"] = pd.to_numeric(hechos["latitud_siniestro"], errors="coerce")
    hechos["longitud_siniestro"] = pd.to_numeric(hechos["longitud_siniestro"], errors="coerce")
    hechos_geo = hechos.dropna(subset=["latitud_siniestro", "longitud_siniestro"]).copy()
    print(f"{len(hechos_geo)} de {len(hechos)} siniestros tienen coordenadas "
          f"({len(hechos_geo) / len(hechos) * 100:.1f}%)")

    motos = hechos_geo[hechos_geo["modo_desplazamiento_victima"] == "MOTO"].copy()
    print(f"{len(motos)} siniestros de motociclistas con coordenadas validas")
    print(motos["gravedad_siniestro"].value_counts())

    motos.to_csv(SALIDA, index=False)
    print(f"\nGuardado en {SALIDA}")


if __name__ == "__main__":
    main()
