import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

df = pd.read_csv('../data/hotspots_moto_caba.csv')

# nivel_riesgo se inserta como placeholder fijo ('bajo') porque la columna es NOT NULL,
# pero NUNCA se usa como tal: el endpoint GET /hotspots (main.py) recalcula el nivel
# real de cada hotspot en cada pedido, en vivo, a partir del modelo entrenado
# (Random Forest, modelo_final.pkl) — no de una fórmula heurística sobre este CSV.
# Antes acá se calculaba un nivel_riesgo con una fórmula propia (cantidad +
# mortales*5 + graves*2), lo cual generaba dos criterios de "riesgo" distintos
# conviviendo en el sistema: si un hotspot no tenía contexto en hotspots_contexto.csv,
# el backend se quedaba con este valor heurístico en vez del valor del modelo, sin
# avisar. Se eliminó esa fórmula para que exista una sola fuente de verdad (el modelo).
NIVEL_PLACEHOLDER = 'bajo'

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

cur.execute("DELETE FROM hotspots_riesgo")

for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO hotspots_riesgo (cluster, latitud, longitud, cantidad_siniestros, mortales, graves, nivel_riesgo, ubicacion)
        VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
    """, (
        int(row['cluster']), row['latitud'], row['longitud'],
        int(row['cantidad_siniestros']), int(row['mortales']), int(row['graves']),
        NIVEL_PLACEHOLDER, row['longitud'], row['latitud']
    ))

conn.commit()
print(f"{len(df)} hotspots cargados en la base de datos (nivel_riesgo real se calcula en vivo en /hotspots)")
cur.close()
conn.close()
