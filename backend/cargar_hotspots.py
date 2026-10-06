import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

DIR_DATOS_POR_DEFECTO = Path(__file__).resolve().parent.parent / 'data'
MENSAJE = '{total} hotspots cargados en la base de datos (nivel_riesgo real se calcula en vivo en /hotspots)'

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


def cargar(cur, dir_datos=DIR_DATOS_POR_DEFECTO):
    """Crea la tabla si falta, la vacía y la carga desde hotspots_moto_caba.csv.
    No hace commit. Devuelve la cantidad cargada."""
    df = pd.read_csv(Path(dir_datos) / 'hotspots_moto_caba.csv')
    # Igual que corredores_riesgo y hotspots_inseguridad: la tabla se autocrea. Antes
    # se asumía creada a mano y una base nueva fallaba con "relation does not exist"
    # (E2E de SES-068). Esquema copiado del de la base de desarrollo existente.
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hotspots_riesgo (
            id SERIAL PRIMARY KEY,
            cluster INTEGER,
            latitud DOUBLE PRECISION,
            longitud DOUBLE PRECISION,
            cantidad_siniestros INTEGER,
            mortales INTEGER,
            graves INTEGER,
            nivel_riesgo VARCHAR(20),
            ubicacion GEOMETRY(Point, 4326)
        )
    """)
    cur.execute("DELETE FROM hotspots_riesgo")

    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO hotspots_riesgo (cluster, latitud, longitud, cantidad_siniestros, mortales, graves, nivel_riesgo, ubicacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
        """, (
            # latitud/longitud se castean a float nativo de Python: pandas las trae
            # como np.float64, y psycopg2 arma el literal SQL con repr() del valor.
            # Numpy >= 2.0 cambio el repr() de sus escalares (antes "-34.5", ahora
            # "np.float64(-34.5)"), lo que rompia el INSERT con un valor no casteado.
            int(row['cluster']), float(row['latitud']), float(row['longitud']),
            int(row['cantidad_siniestros']), int(row['mortales']), int(row['graves']),
            NIVEL_PLACEHOLDER, float(row['longitud']), float(row['latitud'])
        ))
    return len(df)


if __name__ == '__main__':
    load_dotenv()
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cur = conn.cursor()
    total = cargar(cur)
    conn.commit()
    print(MENSAJE.format(total=total))
    cur.close()
    conn.close()
