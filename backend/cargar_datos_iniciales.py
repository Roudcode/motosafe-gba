"""Carga inicial de las capas de datos al arrancar el contenedor.

Corre en entrypoint.sh después de migrar.py. Para cada capa (hotspots de
siniestros, corredores, hotspots de inseguridad) carga los CSV de
MOTOSAFE_DATA_DIR solo si la tabla no existe o está vacía: si ya tiene datos no
la toca, así que reiniciar el contenedor no recarga nada. Prensa no entra acá:
la llena el scraper.

Los CSV no se copian a la imagen. En docker-compose.production.yml se montan
desde data/ del repositorio en /data (solo lectura). Si el directorio no está,
se avisa y la API arranca igual (las capas responden error hasta cargarlas).

Uso local, desde backend/:
    python cargar_datos_iniciales.py            # usa ../data
"""
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

import cargar_corredores
import cargar_hotspots
import cargar_hotspots_inseguridad

# Clave fija para pg_advisory_xact_lock, distinta de la de migrar.py.
_LOCK_CARGA_INICIAL = 72_011_051

CAPAS = (
    ('hotspots_riesgo', cargar_hotspots, ('hotspots_moto_caba.csv',)),
    ('corredores_riesgo', cargar_corredores, ('corredores_riesgo.csv',)),
    ('hotspots_inseguridad', cargar_hotspots_inseguridad,
     ('hotspots_inseguridad_general.csv', 'hotspots_inseguridad_moto.csv')),
)


def _filas(cur, tabla):
    cur.execute('SELECT to_regclass(%s)', (tabla,))
    if cur.fetchone()[0] is None:
        return 0
    cur.execute(f'SELECT count(*) FROM {tabla}')
    return cur.fetchone()[0]


def cargar_si_vacias(database_url, dir_datos):
    """Devuelve {tabla: 'cargada N' | 'ya tenía N' | 'sin CSV'}. Cada capa va en
    su propia transacción, con un lock para que dos procesos no carguen a la vez."""
    dir_datos = Path(dir_datos)
    resultado = {}
    with psycopg2.connect(database_url) as conn:
        for tabla, modulo, archivos in CAPAS:
            with conn.cursor() as cur:
                cur.execute('SELECT pg_advisory_xact_lock(%s)', (_LOCK_CARGA_INICIAL,))
                existentes = _filas(cur, tabla)
                if existentes:
                    resultado[tabla] = f'ya tenía {existentes}'
                elif not all((dir_datos / a).is_file() for a in archivos):
                    resultado[tabla] = 'sin CSV'
                else:
                    resultado[tabla] = f'cargada {modulo.cargar(cur, dir_datos)}'
            conn.commit()
    return resultado


if __name__ == '__main__':
    load_dotenv(Path(__file__).resolve().parent / '.env')
    dir_datos = os.getenv('MOTOSAFE_DATA_DIR') or cargar_hotspots.DIR_DATOS_POR_DEFECTO
    resultado = cargar_si_vacias(os.environ['DATABASE_URL'], dir_datos)
    for tabla, estado in resultado.items():
        print(f'[carga inicial] {tabla}: {estado}')
    if any(estado == 'sin CSV' for estado in resultado.values()):
        print(f'[carga inicial] AVISO: faltan CSV en {dir_datos}; esas capas responden error '
              'hasta cargarlas (montar data/ en MOTOSAFE_DATA_DIR).', file=sys.stderr)
