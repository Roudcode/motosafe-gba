"""
A09 -- exportar una muestra real de notas de prensa para que Rodo la etiquete
despues, por separado (este script SOLO exporta, no analiza ni juzga precision).

Fuente real: la tabla `reportes_prensa` de la base de desarrollo local real
(misma base que usa la app en esta sesion). Columnas persistidas: id, titular,
nivel_precision, url_fuente -- NO persiste `descripcion` ni el `query_extraida`
que arma `extraer_ubicacion` (son valores de paso dentro de
`_evaluar_y_guardar`, nunca se guardan en la tabla).

Para completar esas dos columnas sin inventar nada, se reusa el codigo real
del scraper (`extraer_titulo_descripcion`, `extraer_ubicacion`) y se vuelve a
bajar cada URL en vivo (son notas de prensa publicas, mismo User-Agent y pausa
entre pedidos que ya usa `scrapear_noticias_robos.py`). Limitacion real y
declarada: el contenido de la pagina HOY puede no ser exactamente el que vio
el scraper el dia que la guardo (un medio puede editar la nota); por eso se
guarda `descripcion_obtenida_en_vivo` para separar lo verificado de lo no
verificado, y si una URL ya no responde, la fila queda con esas dos columnas
vacias en vez de inventar contenido.

Muestra: TODAS las filas con nivel_precision in (calle, interseccion) --son
las que mas rinden para validar el extractor-- mas una muestra aleatoria
(semilla fija, reproducible) de nivel barrio hasta completar el rango pedido
(40-60). Sin curar: no se excluye ninguna fila a mano.
"""
import csv
import os
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "backend"))

import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent.parent.parent / "backend" / ".env")

from scrapear_noticias_robos import (  # noqa: E402
    HEADERS_NAVEGADOR,
    PAUSA_ENTRE_FETCHES_SEG,
    extraer_titulo_descripcion,
    extraer_ubicacion,
)

SEMILLA = 20261021
TOTAL_OBJETIVO = 50
SALIDA = Path(__file__).resolve().parent / "muestra_calles.csv"

conn = psycopg2.connect(os.environ["DATABASE_URL"])
cur = conn.cursor()
cur.execute("""
    SELECT id, titular, url_fuente, nivel_precision
    FROM reportes_prensa
    WHERE nivel_precision IN ('calle', 'interseccion')
    ORDER BY id
""")
filas_precision = cur.fetchall()

cur.execute("""
    SELECT id, titular, url_fuente, nivel_precision
    FROM reportes_prensa
    WHERE nivel_precision = 'barrio'
    ORDER BY id
""")
filas_barrio_todas = cur.fetchall()
conn.close()

faltan = max(0, TOTAL_OBJETIVO - len(filas_precision))
rng = random.Random(SEMILLA)
muestra_barrio = rng.sample(filas_barrio_todas, min(faltan, len(filas_barrio_todas)))

filas = filas_precision + muestra_barrio
print(f"calle/interseccion reales: {len(filas_precision)}")
print(f"barrio sorteadas (semilla {SEMILLA}): {len(muestra_barrio)} de {len(filas_barrio_todas)} totales")
print(f"total exportado: {len(filas)}")

resultados = []
ok, fallidas = 0, 0
for idx, (id_, titular, url, nivel) in enumerate(filas, 1):
    descripcion = ""
    query_extraida = ""
    obtenida_en_vivo = False
    try:
        resp = httpx.get(url, headers=HEADERS_NAVEGADOR, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        _titulo_actual, descripcion = extraer_titulo_descripcion(resp.text)
        ubicacion = extraer_ubicacion(titular, descripcion)
        if ubicacion is not None:
            query_extraida = ubicacion[0]
        obtenida_en_vivo = True
        ok += 1
        print(f"[{idx}/{len(filas)}] ok id={id_} ({nivel})")
    except Exception as err:
        fallidas += 1
        print(f"[{idx}/{len(filas)}] FALLO id={id_} ({nivel}): {type(err).__name__}: {err}")
    resultados.append({
        "id": id_,
        "titulo": titular,
        "descripcion_completa": descripcion,
        "query_extraida": query_extraida,
        "nivel_precision": nivel,
        "url": url,
        "descripcion_obtenida_en_vivo": obtenida_en_vivo,
    })
    time.sleep(PAUSA_ENTRE_FETCHES_SEG)

with open(SALIDA, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=[
        "id", "titulo", "descripcion_completa", "query_extraida",
        "nivel_precision", "url", "descripcion_obtenida_en_vivo",
    ])
    w.writeheader()
    w.writerows(resultados)

print(f"\nOK: {ok}  FALLIDAS (sin descripcion/query, URL no respondio igual que en el scrape original): {fallidas}")
print(f"Escrito: {SALIDA}")
