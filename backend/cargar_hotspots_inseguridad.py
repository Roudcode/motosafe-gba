# -*- coding: utf-8 -*-
"""
Carga los hotspots de inseguridad (data/hotspots_inseguridad_general.csv y
data/hotspots_inseguridad_moto.csv, generados por
notebooks/identificar_hotspots_inseguridad.py) en la tabla hotspots_inseguridad.

A diferencia de hotspots_riesgo/corredores_riesgo, esta capa NO pasa por el
modelo entrenado en cada request: no es una prediccion de severidad de un
siniestro (no aplica, esto es densidad de delitos), es densidad historica de
incidentes. El nivel de riesgo se calcula una sola vez aca, con percentiles
relativos (25/75/95, mismo criterio que se uso para corredores_riesgo cuando
los cortes absolutos resultaron demasiado gruesos) SOBRE CADA TIPO POR
SEPARADO -- general y moto tienen escalas de "cantidad_delitos" muy distintas
(hasta ~2500 en general, hasta ~70 en moto), mezclarlos haria que todo "moto"
caiga en el nivel mas bajo.

La tabla se autocrea (CREATE TABLE IF NOT EXISTS), igual que corredores_riesgo.

Uso:
    python cargar_hotspots_inseguridad.py
"""
import os

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def nivel_por_percentiles(cantidades):
    p25, p75, p95 = np.percentile(cantidades, [25, 75, 95])

    def nivel(c):
        if c >= p95:
            return 'critico'
        if c >= p75:
            return 'alto'
        if c >= p25:
            return 'medio'
        return 'bajo'

    return [nivel(c) for c in cantidades]


conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS hotspots_inseguridad (
        id SERIAL PRIMARY KEY,
        tipo VARCHAR(20) NOT NULL,
        cluster INTEGER NOT NULL,
        latitud DOUBLE PRECISION NOT NULL,
        longitud DOUBLE PRECISION NOT NULL,
        cantidad_delitos INTEGER NOT NULL,
        comuna_moda VARCHAR(10),
        tipo_delito_moda VARCHAR(50),
        nivel_riesgo VARCHAR(20) NOT NULL,
        ubicacion GEOGRAPHY(Point, 4326)
    )
""")

cur.execute("DELETE FROM hotspots_inseguridad")

total = 0
for tipo, archivo in [('general', '../data/hotspots_inseguridad_general.csv'), ('moto', '../data/hotspots_inseguridad_moto.csv')]:
    df = pd.read_csv(archivo)
    niveles = nivel_por_percentiles(df['cantidad_delitos'].to_numpy())

    for (_, row), nivel in zip(df.iterrows(), niveles):
        cur.execute("""
            INSERT INTO hotspots_inseguridad
                (tipo, cluster, latitud, longitud, cantidad_delitos, comuna_moda, tipo_delito_moda, nivel_riesgo, ubicacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """, (
            tipo, int(row['cluster']), float(row['latitud']), float(row['longitud']),
            int(row['cantidad_delitos']), str(row['comuna_moda']), row['tipo_delito_moda'], nivel,
            float(row['longitud']), float(row['latitud']),
        ))
    total += len(df)
    print(f"{tipo}: {len(df)} hotspots cargados")

conn.commit()
print(f"\n{total} hotspots de inseguridad cargados en total")
cur.close()
conn.close()
