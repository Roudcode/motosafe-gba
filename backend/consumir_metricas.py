"""
T04 (BACKLOG) -- "falta retencion de logs y que esto se consuma desde algun
lado (hoy nadie mira /metrics salvo que se abra a mano)".

Este script pide /metrics al backend real (no toca el proceso de la API,
no agrega tareas en segundo plano dentro de main.py -- eso hubiera sido
mas riesgoso de verificar sin el servidor vivo) y guarda una foto con
fecha en un archivo JSONL local, recortando lo mas viejo que el periodo
de retencion.

Uso pensado: correrlo periodicamente (cron en Linux, Programador de
tareas en Windows) cada 15-30 minutos contra el backend real. Sin eso,
este script solo no resuelve nada por si mismo -- la parte que falta
(programar la ejecucion periodica en la maquina real de Rodo) necesita
el entorno real, no un sandbox.

    python consumir_metricas.py                       # una corrida
    python consumir_metricas.py --url http://127.0.0.1:8000/metrics
    python consumir_metricas.py --retencion-dias 14
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

RUTA_LOG_DEFECTO = Path(__file__).resolve().parent / "logs" / "metricas_historico.jsonl"
URL_DEFECTO = "http://127.0.0.1:8000/metrics"
RETENCION_DIAS_DEFECTO = 30


def pedir_metricas(url: str, timeout: float = 5.0) -> dict:
    """Pide /metrics al backend real. No inventa un resultado si falla --
    propaga el error para que quien programe la corrida (cron/Task
    Scheduler) lo vea en su propio log de ejecución."""
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def leer_snapshots(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    snapshots = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea:
            continue
        try:
            snapshots.append(json.loads(linea))
        except json.JSONDecodeError:
            # una línea corrupta (corte a mitad de escritura) no debe
            # tirar abajo la retención de todo el resto del archivo
            continue
    return snapshots


def recortar_por_retencion(snapshots: list[dict], retencion_dias: int, ahora: datetime) -> list[dict]:
    limite = ahora - timedelta(days=retencion_dias)
    conservados = []
    for s in snapshots:
        try:
            fecha = datetime.fromisoformat(s["capturado_en"])
        except (KeyError, ValueError):
            continue
        if fecha >= limite:
            conservados.append(s)
    return conservados


def escribir_snapshots(ruta: Path, snapshots: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    contenido = "\n".join(json.dumps(s, ensure_ascii=False) for s in snapshots)
    ruta.write_text(contenido + ("\n" if contenido else ""), encoding="utf-8")


def correr(url: str, ruta_log: Path, retencion_dias: int, ahora: datetime | None = None) -> dict:
    ahora = ahora or datetime.now(timezone.utc)
    metricas = pedir_metricas(url)
    snapshot = {"capturado_en": ahora.isoformat(), "metricas": metricas}

    existentes = leer_snapshots(ruta_log)
    existentes.append(snapshot)
    conservados = recortar_por_retencion(existentes, retencion_dias, ahora)
    escribir_snapshots(ruta_log, conservados)

    return {
        "snapshot_nuevo": snapshot,
        "total_conservados": len(conservados),
        "descartados_por_retencion": len(existentes) - len(conservados),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=URL_DEFECTO)
    parser.add_argument("--log", type=Path, default=RUTA_LOG_DEFECTO)
    parser.add_argument("--retencion-dias", type=int, default=RETENCION_DIAS_DEFECTO)
    args = parser.parse_args()

    try:
        resultado = correr(args.url, args.log, args.retencion_dias)
    except (urllib.error.URLError, TimeoutError) as e:
        print(f"No se pudo pedir {args.url}: {e}. ¿Está corriendo el backend?")
        raise SystemExit(1)

    print(json.dumps({
        "conteo_rutas": len(resultado["snapshot_nuevo"]["metricas"]),
        "total_conservados": resultado["total_conservados"],
        "descartados_por_retencion": resultado["descartados_por_retencion"],
        "log": str(args.log),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
