# -*- coding: utf-8 -*-
"""
Carga data/corredores_riesgo.csv (generado por notebooks/identificar_corredores.py
+ notebooks/fetch_corredores_geometria.py) a la tabla corredores_riesgo en
Postgres. Mismo patron que cargar_hotspots.py: se corre una vez, o cada vez que
se regeneren los datos.

A diferencia de hotspots_riesgo (que se asume ya creada a mano), esta tabla se
crea sola si no existe, para no repetir el problema de que el repo no arranque
limpio sin un paso manual documentado en ningun lado.
"""
import json
import os

import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

df = pd.read_csv('../data/corredores_riesgo.csv')

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS corredores_riesgo (
        id SERIAL PRIMARY KEY,
        calle VARCHAR(200) NOT NULL,
        tramo INTEGER NOT NULL DEFAULT 1,
        tramos_totales INTEGER NOT NULL DEFAULT 1,
        geometria TEXT NOT NULL,
        cantidad_siniestros INTEGER NOT NULL,
        mortales INTEGER NOT NULL,
        graves INTEGER NOT NULL,
        comuna_moda VARCHAR(10),
        tipo_via_moda VARCHAR(50),
        contraparte_moda VARCHAR(50),
        edad_promedio REAL,
        sexo_moda VARCHAR(5)
    )
""")
cur.execute("DELETE FROM corredores_riesgo")

for _, row in df.iterrows():
    # geometria ya viene como JSON (lista de [lat, lng]) desde fetch_corredores_geometria.py;
    # se valida que parsee antes de insertar, para no guardar filas rotas.
    geometria = json.loads(row['geometria'])
    cur.execute("""
        INSERT INTO corredores_riesgo
            (calle, tramo, tramos_totales, geometria, cantidad_siniestros, mortales, graves,
             comuna_moda, tipo_via_moda, contraparte_moda, edad_promedio, sexo_moda)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        row['calle'], int(row['tramo']), int(row['tramos_totales']),
        json.dumps(geometria), int(row['cantidad_siniestros']),
        int(row['mortales']), int(row['graves']),
        str(row['comuna_moda']), row['tipo_via_moda'], row['contraparte_moda'],
        float(row['edad_promedio']), row['sexo_moda'],
    ))

conn.commit()
print(f"{len(df)} corredores de riesgo cargados en la base de datos")
cur.close()
conn.close()
