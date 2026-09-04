"""
Descarga el clima historico (precipitacion, temperatura, humedad) para CABA,
hora por hora, desde 2019-01-01 hasta hoy, usando la API de archivo historico
de Open-Meteo (gratis, sin clave). Se corre UNA vez para generar
data/clima_historico.csv, que despues se une a los siniestros para reentrenar
el modelo con clima como variable real.

Importante: este script necesita salir a internet (api.open-meteo.com). Si lo
corres desde una terminal con acceso restringido no va a andar; correlo desde
una terminal normal (PowerShell / cmd / la terminal de tu editor), parado en
la carpeta del proyecto:

    python notebooks/fetch_clima_historico.py
"""
import sys
import time
from datetime import date
from pathlib import Path

import pandas as pd
import httpx

LAT, LON = -34.61, -58.44  # punto central de CABA, ver notebook: los siniestros caen en ese entorno
TIMEZONE = "America/Argentina/Buenos_Aires"
INICIO = date(2019, 1, 1)
FIN = date.today()
SALIDA = Path(__file__).resolve().parent.parent / "data" / "clima_historico.csv"


def descargar_anio(anio_inicio, anio_fin):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": anio_inicio.isoformat(),
        "end_date": anio_fin.isoformat(),
        "hourly": "precipitation,temperature_2m,relative_humidity_2m",
        "timezone": TIMEZONE,
    }
    resp = httpx.get(url, params=params, timeout=60)
    resp.raise_for_status()
    datos = resp.json()["hourly"]
    return pd.DataFrame({
        "fecha_hora": datos["time"],
        "precipitacion": datos["precipitation"],
        "temperatura": datos["temperature_2m"],
        "humedad": datos["relative_humidity_2m"],
    })


def main():
    bloques = []
    anio = INICIO.year
    while anio <= FIN.year:
        desde = date(anio, 1, 1) if anio > INICIO.year else INICIO
        hasta = date(anio, 12, 31) if anio < FIN.year else FIN
        print(f"Descargando {desde} a {hasta}...", file=sys.stderr)
        bloques.append(descargar_anio(desde, hasta))
        anio += 1
        time.sleep(1)  # no hace falta apurar, es una corrida unica

    clima = pd.concat(bloques, ignore_index=True)
    clima["fecha_hora"] = pd.to_datetime(clima["fecha_hora"])
    clima["fecha"] = clima["fecha_hora"].dt.date.astype(str)
    clima["hora"] = clima["fecha_hora"].dt.hour
    clima = clima[["fecha", "hora", "precipitacion", "temperatura", "humedad"]]
    clima.to_csv(SALIDA, index=False)
    print(f"Listo: {len(clima)} filas guardadas en {SALIDA}", file=sys.stderr)


if __name__ == "__main__":
    main()
