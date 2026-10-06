"""Re-geocodifica las filas de reportes_prensa ubicadas con el método anterior
a SES-069 (decisión de Rodo, 2026-10-06).

La tabla guarda solo el titular, no la descripción con que se ubicó cada nota,
y 232 filas vienen de Google Noticias, que no se vuelve a consultar (DEC-011).
Por eso no se descarga nada de los medios:

  1. zona: el punto viejo de una fila de nivel 'barrio' es el resultado de la
     consulta de zona del método anterior. Si coincide (al micrómetro) con el
     punto «anterior» de una de las 87 zonas medidas en
     ../A09-geocodificacion/resultado.json, se sabe qué zona era, y se usa el
     punto «nuevo» validado de esa misma zona.
  2. titular: si no coincide con ninguna zona, se re-extrae la ubicación solo
     del titular y se geocodifica con geocodificar_en_zona (con validación).
     Si el titular da menos precisión que la guardada (la fila era de calle o
     intersección, ubicada con una descripción que ya no está), no se pisa un
     punto preciso: se verifica por geocodificación inversa si el punto viejo
     cae en la zona del titular. Si cae, queda como está; si no, se mueve al
     punto de la zona y se baja a nivel 'barrio' (800 m).
  3. sin cambio: si nada de lo anterior da un punto, la fila queda como está.

Uso, desde la raíz del repo (DATABASE_URL de backend/.env):
    python docs/evidencias/2026-10-06/A09-regeocodificacion/regeocodificar_prensa.py            # simula
    python docs/evidencias/2026-10-06/A09-regeocodificacion/regeocodificar_prensa.py --aplicar  # actualiza
Escribe propuesta.csv con una fila por nota y el resumen por pantalla.
"""
import csv
import json
import math
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
sys.path.insert(0, str(RAIZ / 'backend'))
sys.path.insert(0, str(AQUI.parent / 'A09-geocodificacion'))
import medir_zonas  # noqa: E402  (caché de Nominatim y mismo pedido que el scraper)
import scrapear_noticias_robos as s  # noqa: E402

s._buscar_nominatim = medir_zonas.buscar_con_cache


def clave(lat, lng):
    return (round(lat, 6), round(lng, 6))


def distancia_m(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (*a, *b))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def zonas_medidas():
    """punto anterior -> (zona, punto nuevo, ¿el anterior estaba mal?)"""
    por_punto = {}
    for fila in json.loads((AQUI.parent / 'A09-geocodificacion' / 'resultado.json').read_text(encoding='utf-8')):
        anterior, nuevo = fila['anterior']['punto'], fila['nuevo']['punto']
        if anterior and nuevo:
            por_punto.setdefault(clave(*anterior), (fila['zona'], tuple(nuevo),
                                                    fila['anterior']['resultado'] != 'ok'))
    return por_punto


PRECISION = {'interseccion': 0, 'calle': 1, 'barrio': 2}


def _en_zona(punto, zona, localidad):
    partido_real, barrio_real = medir_zonas.donde_cae(punto)
    if localidad == 'CABA':
        return partido_real == 'caba' and (zona is None or barrio_real == medir_zonas.norm(zona))
    esperado = medir_zonas.norm(s.PARTIDO_DE_LOCALIDAD.get(zona, zona))
    return bool(partido_real) and partido_real.endswith(esperado)


def proponer(fila, por_punto):
    """(método, detalle, punto nuevo, ¿el anterior estaba en otra zona?, nivel, radio)"""
    viejo = (fila['lat'], fila['lng'])
    if fila['nivel_precision'] == 'barrio' and clave(*viejo) in por_punto:
        zona, nuevo, estaba_mal = por_punto[clave(*viejo)]
        return 'zona', zona, nuevo, estaba_mal, fila['nivel_precision'], fila['radio_metros']
    ubicacion = s.extraer_ubicacion(fila['titular'], '')
    if not ubicacion:
        return 'sin cambio', 'sin pista en el titular', None, None, None, None
    query, nivel, radio = ubicacion
    zona, localidad = s.encontrar_zona(fila['titular']) or (None, 'CABA')
    if PRECISION[nivel] > PRECISION[fila['nivel_precision']]:
        if _en_zona(viejo, zona, localidad):
            return 'sin cambio', f'punto preciso dentro de {zona or localidad}', None, None, None, None
        punto, motivo = s.geocodificar_en_zona(query, nivel, zona, localidad)
        if punto:
            return 'titular', f'fuera de {zona or localidad}, baja a barrio', punto, True, nivel, radio
        return 'sin cambio', f'titular: {motivo}', None, None, None, None
    punto, motivo = s.geocodificar_en_zona(query, nivel, zona, localidad)
    if punto:
        return 'titular', query, punto, None, nivel, radio
    return 'sin cambio', f'titular: {motivo}', None, None, None, None


def main():
    aplicar = '--aplicar' in sys.argv
    load_dotenv(RAIZ / 'backend' / '.env')
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute('SELECT id, lat, lng, nivel_precision, radio_metros, titular, fuente FROM reportes_prensa ORDER BY id')
    filas = [dict(zip(('id', 'lat', 'lng', 'nivel_precision', 'radio_metros', 'titular', 'fuente'), r))
             for r in cur.fetchall()]
    por_punto = zonas_medidas()

    salida, actualizaciones = [], []
    for fila in filas:
        metodo, detalle, nuevo, estaba_mal, nivel, radio = proponer(fila, por_punto)
        dist = distancia_m((fila['lat'], fila['lng']), nuevo) if nuevo else None
        cambia = dist is not None and dist > 1
        salida.append({
            'id': fila['id'], 'fuente': fila['fuente'], 'nivel': fila['nivel_precision'], 'titular': fila['titular'][:120],
            'metodo': metodo, 'detalle': detalle, 'lat_anterior': fila['lat'], 'lng_anterior': fila['lng'],
            'lat_nueva': nuevo[0] if nuevo else '', 'lng_nueva': nuevo[1] if nuevo else '',
            'distancia_m': round(dist) if dist is not None else '', 'cambia': cambia,
            'anterior_en_otro_partido': '' if estaba_mal is None else estaba_mal,
            'nivel_nuevo': nivel if cambia else '',
        })
        if cambia:
            actualizaciones.append((nuevo[0], nuevo[1], nivel, radio, fila['id'], fila['lat'], fila['lng']))

    with (AQUI / 'propuesta.csv').open('w', encoding='utf-8', newline='') as f:
        escritor = csv.DictWriter(f, fieldnames=list(salida[0]))
        escritor.writeheader()
        escritor.writerows(salida)

    cambian = [x for x in salida if x['cambia']]
    print(f'filas: {len(salida)}')
    for metodo in ('zona', 'titular', 'sin cambio'):
        print(f'  método {metodo}: {sum(x["metodo"] == metodo for x in salida)}')
    print(f'cambian de ubicación: {len(cambian)}')
    print(f'  corrigen una zona que caía en otro partido o barrio: {sum(x["anterior_en_otro_partido"] is True for x in cambian)}')
    print(f'  misma zona, otro punto representativo: {sum(x["anterior_en_otro_partido"] is False for x in cambian)}')
    print(f'  re-extraídas del titular: {sum(x["metodo"] == "titular" for x in cambian)}'
          f' (de ellas, bajan a nivel barrio por estar fuera de su zona: '
          f'{sum("baja a barrio" in x["detalle"] for x in cambian)})')
    for umbral in (1_000, 5_000, 20_000):
        print(f'  desplazamiento > {umbral // 1000} km: {sum(x["distancia_m"] > umbral for x in cambian)}')

    if aplicar:
        actualizadas = 0
        for lat, lng, nivel, radio, id_, lat_viejo, lng_viejo in actualizaciones:
            # Solo si la fila sigue con las coordenadas leídas (por si el scraper la tocó).
            cur.execute('UPDATE reportes_prensa SET lat = %s, lng = %s, nivel_precision = %s, radio_metros = %s '
                        'WHERE id = %s AND lat = %s AND lng = %s',
                        (lat, lng, nivel, radio, id_, lat_viejo, lng_viejo))
            actualizadas += cur.rowcount
        conn.commit()
        print(f'APLICADO: {actualizadas} filas actualizadas en una transacción')
    conn.close()


if __name__ == '__main__':
    main()
