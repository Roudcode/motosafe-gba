import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

df = pd.read_csv('../data/hotspots_moto_caba.csv')

def calcular_nivel(row):
    score = row['cantidad_siniestros'] + row['mortales'] * 5 + row['graves'] * 2
    if score >= 100:
        return 'critico'
    if score >= 60:
        return 'alto'
    if score >= 30:
        return 'medio'
    return 'bajo'

df['nivel_riesgo'] = df.apply(calcular_nivel, axis=1)

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
        row['nivel_riesgo'], row['longitud'], row['latitud']
    ))

conn.commit()
print(f"{len(df)} hotspots cargados en la base de datos")
cur.close()
conn.close()