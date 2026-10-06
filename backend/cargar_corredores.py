# -*- coding: utf-8 -*-
"""
Carga data/corredores_riesgo.csv (generado por notebooks/identificar_corredores.py
+ notebooks/fetch_corredores_geometria.py) a la tabla corredores_riesgo en
Postgres. Mismo patron que cargar_hotspots.py: se corre una vez, o cada vez que
se regeneren los datos.

La tabla se crea sola si no existe. `cargar` la usa tambien
cargar_datos_iniciales.py al arrancar el contenedor.
"""
import json
import os
from pathlib import Path

import pandas as pd
import psycopg2
from dotenv import load_dotenv

DIR_DATOS_POR_DEFECTO = Path(__file__).resolve().parent.parent / 'data'
MENSAJE = '{total} corredores de riesgo cargados en la base de datos'


def cargar(cur, dir_datos=DIR_DATOS_POR_DEFECTO):
    """Crea la tabla si falta, la vacía y la carga desde corredores_riesgo.csv.
    No hace commit: lo decide quien llama. Devuelve la cantidad cargada."""
    df = pd.read_csv(Path(dir_datos) / 'corredores_riesgo.csv')
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
