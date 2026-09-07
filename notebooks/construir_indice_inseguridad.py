# -*- coding: utf-8 -*-
"""
Construye un indice de inseguridad por comuna a partir de data/delitos_caba.csv
(descargado antes por fetch_delitos_caba.py). No necesita red, es agregacion
pura sobre datos que ya estan en el repo.

Se usan los ULTIMOS 3 ANIOS completos disponibles (no el historico 2016-2025
entero) para que el indice refleje el nivel de inseguridad actual de cada
comuna, no un promedio de una decada que puede no representar la situacion de
hoy (se verifico que 2025 viene completo y parejo mes a mes, no truncado).

Se calculan dos indices, ambos normalizados 0-1 (min-max entre las 15 comunas):
  - indice_inseguridad: tasa de delitos totales por anio, por comuna.
  - indice_inseguridad_moto: tasa de delitos con uso_moto = SI por anio, por
    comuna (mas especifico para un producto de riesgo para motociclistas que
    el indice general).

Salida: data/indice_inseguridad_comuna.csv (comuna, delitos_promedio_anual,
delitos_moto_promedio_anual, indice_inseguridad, indice_inseguridad_moto).

Se corre una sola vez despues de fetch_delitos_caba.py, y de nuevo cuando se
actualice ese archivo (una vez por anio, cuando el GCBA publique el siguiente):

    python notebooks/construir_indice_inseguridad.py
"""
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
ENTRADA = BASE_DIR / "data" / "delitos_caba.csv"
SALIDA = BASE_DIR / "data" / "indice_inseguridad_comuna.csv"

ANIOS_VENTANA = 3  # ultimos N anios completos disponibles en el dataset


def normalizar_0_1(serie):
    minimo, maximo = serie.min(), serie.max()
    if maximo == minimo:
        return serie * 0
    return (serie - minimo) / (maximo - minimo)


def main():
    delitos = pd.read_csv(ENTRADA, low_memory=False)
    delitos = delitos.dropna(subset=["comuna"]).copy()
    delitos["comuna"] = delitos["comuna"].astype(int).astype(str)

    anio_max = delitos["anio_dataset"].max()
    anios_incluidos = list(range(anio_max - ANIOS_VENTANA + 1, anio_max + 1))
    ventana = delitos[delitos["anio_dataset"].isin(anios_incluidos)].copy()
    print(f"Ventana usada: {anios_incluidos} ({len(ventana)} delitos de {len(delitos)} totales)")

    total_por_comuna = ventana.groupby("comuna").size().rename("delitos_total_ventana")
    moto_por_comuna = (
        ventana[ventana["uso_moto"] == "SI"].groupby("comuna").size().rename("delitos_moto_total_ventana")
    )

    resumen = pd.DataFrame(index=[str(c) for c in range(1, 16)])
    resumen = resumen.join(total_por_comuna).join(moto_por_comuna).fillna(0)
    resumen.index.name = "comuna"
    resumen = resumen.reset_index()

    resumen["delitos_promedio_anual"] = (resumen["delitos_total_ventana"] / ANIOS_VENTANA).round(1)
    resumen["delitos_moto_promedio_anual"] = (resumen["delitos_moto_total_ventana"] / ANIOS_VENTANA).round(1)

    resumen["indice_inseguridad"] = normalizar_0_1(resumen["delitos_promedio_anual"]).round(3)
    resumen["indice_inseguridad_moto"] = normalizar_0_1(resumen["delitos_moto_promedio_anual"]).round(3)

    salida = resumen[[
        "comuna", "delitos_promedio_anual", "delitos_moto_promedio_anual",
        "indice_inseguridad", "indice_inseguridad_moto",
    ]].sort_values("comuna", key=lambda s: s.astype(int))

    salida.to_csv(SALIDA, index=False)
    print(f"\nGuardado en {SALIDA}:")
    print(salida.to_string(index=False))


if __name__ == "__main__":
    main()
