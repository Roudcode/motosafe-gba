"""Completa fechas editoriales de noticias ya guardadas.

Uso: python actualizar_fechas_prensa.py [--limite 100]
Sólo actualiza `publicado_en` cuando la página original declara una fecha;
no vuelve a clasificar, geocodificar ni insertar noticias.
"""
import argparse
import time

import httpx
import psycopg2

from scrapear_noticias_robos import DATABASE_URL, USER_AGENT, _asegurar_tabla, extraer_fecha_publicacion


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limite', type=int, default=100)
    args = parser.parse_args()
    limite = max(1, min(args.limite, 500))

    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            _asegurar_tabla(cur)
            cur.execute("""
                SELECT id, url_fuente FROM reportes_prensa
                WHERE publicado_en IS NULL
                ORDER BY creado_en DESC
                LIMIT %s
            """, (limite,))
            filas = cur.fetchall()
            actualizadas = 0
            for noticia_id, url in filas:
                try:
                    respuesta = httpx.get(url, headers={'User-Agent': USER_AGENT}, timeout=15, follow_redirects=True)
                    respuesta.raise_for_status()
                    fecha = extraer_fecha_publicacion(respuesta.text)
                    if fecha:
                        cur.execute('UPDATE reportes_prensa SET publicado_en = %s WHERE id = %s', (fecha, noticia_id))
                        actualizadas += 1
                except httpx.HTTPError:
                    pass
                time.sleep(0.5)
    print(f'Revisadas: {len(filas)}. Fechas editoriales completadas: {actualizadas}.')


if __name__ == '__main__':
    main()
