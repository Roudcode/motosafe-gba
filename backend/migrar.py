"""Aplica las migraciones SQL versionadas de MotoSafe GBA.

Uso desde la carpeta ``backend``::

    .\\venv\\Scripts\\python.exe migrar.py

Es seguro repetirlo: cada archivo se registra al terminar correctamente y no
se vuelve a ejecutar. No carga datasets ni borra tablas.
"""
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
MIGRACIONES_DIR = BASE_DIR / 'migrations'


def migraciones_disponibles():
    return sorted(MIGRACIONES_DIR.glob('[0-9][0-9][0-9]_*.sql'))


def aplicar_migraciones(database_url=None):
    """Aplica archivos pendientes y devuelve sus nombres, en orden."""
    url = database_url or os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL no está configurada')

    with psycopg2.connect(url) as conn:
        with conn.cursor() as cur:
            cur.execute('''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(255) PRIMARY KEY,
                    aplicado_en TIMESTAMPTZ NOT NULL DEFAULT now()
                )
            ''')
            cur.execute('SELECT version FROM schema_migrations')
            aplicadas = {fila[0] for fila in cur.fetchall()}

            pendientes = [archivo for archivo in migraciones_disponibles() if archivo.name not in aplicadas]
            for archivo in pendientes:
                cur.execute(archivo.read_text(encoding='utf-8'))
                cur.execute('INSERT INTO schema_migrations (version) VALUES (%s)', (archivo.name,))
    return [archivo.name for archivo in pendientes]


if __name__ == '__main__':
    load_dotenv(BASE_DIR / '.env')
    aplicadas = aplicar_migraciones()
    print('Migraciones aplicadas:' if aplicadas else 'No hay migraciones pendientes.')
    for nombre in aplicadas:
        print(f'- {nombre}')
