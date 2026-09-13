"""Mide resultados del extractor contra una muestra humana etiquetada.

No llama a Internet, no toca la base y no produce métricas si faltan etiquetas.
Uso: python backend/evaluar_extractor_prensa.py ruta/a/prensa_etiquetada.csv
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path


def si(valor: str) -> bool:
    return valor.strip().lower() in {"si", "sí", "true", "1"}


def main(path: Path) -> None:
    with path.open(encoding="utf-8", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
    revisadas = [f for f in filas if f.get("esperado_incidente", "").strip()]
    if not revisadas:
        raise SystemExit("No hay filas revisadas: completar esperado_incidente antes de medir.")

    positivos = [f for f in revisadas if f["esperado_incidente"].strip().lower() not in {"no", "ninguno", "irrelevante"}]
    detectados = [f for f in revisadas if f.get("extraido_incidente", "").strip().lower() not in {"", "no", "ninguno", "irrelevante"}]
    verdaderos = [f for f in positivos if f.get("extraido_incidente", "").strip().lower() == f["esperado_incidente"].strip().lower()]
    precision = len(verdaderos) / len(detectados) if detectados else 0.0
    recall = len(verdaderos) / len(positivos) if positivos else 0.0
    abstenciones = sum(not f.get("extraido_incidente", "").strip() for f in revisadas)
    errores = [float(f["error_geografico_m"]) for f in revisadas if f.get("error_geografico_m", "").strip()]
    print(f"Filas revisadas: {len(revisadas)}")
    print(f"Precisión de incidente: {precision:.3f}")
    print(f"Recall de incidente: {recall:.3f}")
    print(f"Abstenciones: {abstenciones}/{len(revisadas)}")
    if errores:
        print(f"Error geográfico medio (m): {sum(errores) / len(errores):.1f}")
    else:
        print("Error geográfico: sin pares revisados con distancia.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python backend/evaluar_extractor_prensa.py archivo.csv")
    main(Path(sys.argv[1]))
