"""
D02 -- pista de completitud por anio, mas alla de edad_victima.

docs/evidencias/2026-10-20/D02-causa/README.md encontro que el porcentaje
de edad_desconocida en el anio de EVALUACION 2024 (12,13%) es muy inferior
al resto de la serie (41-45%), y dejo abierta la pregunta: ¿2024 es un
anio atipico solo en el registro de edad, o la anomalia de completitud es
mas amplia (otros campos del dataset oficial tambien mas completos ese
anio)? Esa pregunta importa porque, si es mas amplia, apunta a un cambio
en el proceso de carga/registro del dataset oficial en 2024 (una hipotesis
de calidad de dato), no a un cambio real en el patron de siniestralidad
vial (la hipotesis que D02 todavia no puede descartar ni confirmar).

Este script mide, para cada anio 2019-2025 y sobre el mismo universo de
siniestros de moto que usa el resto de D02 (motos_limpio.csv + victimas de
siniestros_viales_victimas.csv filtradas a modo_desplazamiento MOTO), el
porcentaje de valores faltantes o marcados como "SD" (sin dato) en seis
campos del dataset oficial, no solo edad: comuna, tipo de via, contraparte,
direccion normalizada, sexo de la victima y edad de la victima.

No modifica ningun archivo del repositorio salvo el reporte indicado en
--output.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def cargar_base() -> pd.DataFrame:
    motos = pd.read_csv(DATA / "motos_limpio.csv")
    motos["contraparte_siniestro"] = motos["contraparte_siniestro"].str.strip().str.upper()
    motos["tipo_de_via_siniestro"] = motos["tipo_de_via_siniestro"].str.strip().str.upper()

    victimas = pd.read_csv(DATA / "siniestros_viales_victimas.csv", encoding="utf-8-sig", sep=";", low_memory=False)
    victimas["modo_desplazamiento_victima"] = victimas["modo_desplazamiento_victima"].str.strip().str.upper()
    victimas["sexo_victima"] = victimas["sexo_victima"].str.strip().str.upper()
    victimas = victimas[victimas["modo_desplazamiento_victima"] == "MOTO"].copy()
    victimas["edad_victima"] = pd.to_numeric(victimas["edad_victima"], errors="coerce")
    resumen = victimas.groupby("id_siniestro").agg(
        edad_victima=("edad_victima", "mean"),
        sexo_victima=("sexo_victima", lambda x: x.mode().iloc[0] if not x.mode().empty else "SD"),
    ).reset_index()

    base = motos.merge(resumen, on="id_siniestro", how="left")
    base.loc[(base["edad_victima"] < 14) | (base["edad_victima"] > 95), "edad_victima"] = np.nan
    base["sexo_victima"] = base["sexo_victima"].fillna("SD")
    return base


def pct_faltante(serie: pd.Series, extra_sentinela: set[str] | None = None) -> float:
    """Porcentaje de valores nulos o que coinciden con un sentinela explicito
    de "sin dato" (ej. "SD"), sobre el total de filas de la serie."""
    faltante = serie.isna()
    if extra_sentinela:
        faltante = faltante | serie.astype(str).str.strip().str.upper().isin(extra_sentinela)
    return round(float(faltante.mean()) * 100, 2)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    base = cargar_base()
    anios = sorted(base["anio_siniestro"].dropna().unique())

    campos = {
        "comuna": {"sentinelas": None},
        "tipo_de_via_siniestro": {"sentinelas": {"SD"}},
        "contraparte_siniestro": {"sentinelas": {"SD"}},
        "direccion_normalizada_siniestro": {"sentinelas": None},
        "sexo_victima": {"sentinelas": {"SD"}},
        "edad_victima": {"sentinelas": None},
    }

    filas = []
    for anio in anios:
        sub = base[base["anio_siniestro"] == anio]
        fila = {"anio": int(anio), "filas": int(len(sub))}
        for campo, cfg in campos.items():
            fila[f"pct_faltante_{campo}"] = pct_faltante(sub[campo], cfg["sentinelas"])
        filas.append(fila)

    tabla = pd.DataFrame(filas)
    args.output.mkdir(parents=True, exist_ok=True)
    tabla.to_csv(args.output / "completitud_por_anio.csv", index=False)
    (args.output / "completitud_por_anio.json").write_text(
        json.dumps(filas, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(tabla.to_string(index=False))
    print(f"\nEvidencia completa en {args.output}")


if __name__ == "__main__":
    main()
