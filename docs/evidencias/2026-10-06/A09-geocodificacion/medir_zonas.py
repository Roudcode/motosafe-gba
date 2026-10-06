"""A09 — ¿La ubicación por zona del scraper cae en la zona pedida?

Para cada partido del GBA, alias de localidad y barrio de CABA del gazetteer de
backend/scrapear_noticias_robos.py, ubica la zona con dos métodos:

  anterior -> la consulta que armaba extraer_ubicacion (nivel 'barrio') con el
              geocode sin validar (comportamiento hasta SES-068).
  nuevo    -> geocodificar_en_zona (SES-069): featureType=settlement, validación
              de partido/barrio y reintento "Partido de X"; None = se abstiene.

La verificación es independiente del código evaluado: cada punto se pasa por
geocodificación inversa de Nominatim (/reverse, zoom 14) y se mira en qué
partido o barrio cae realmente.

Uso, desde la raíz del repo:
    python docs/evidencias/2026-10-06/A09-geocodificacion/medir_zonas.py
Las respuestas quedan en cache_nominatim.json para no repetir pedidos; el
detalle, en resultado.json.
"""
import json
import sys
import time
import unicodedata
from pathlib import Path

import httpx

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parents[3] / 'backend'))
import scrapear_noticias_robos as s  # noqa: E402

CACHE = AQUI / 'cache_nominatim.json'
cache = json.loads(CACHE.read_text(encoding='utf-8')) if CACHE.exists() else {}
REVERSE_URL = s.NOMINATIM_URL.replace('/search', '/reverse')


def norm(texto):
    texto = unicodedata.normalize('NFKD', texto or '').encode('ascii', 'ignore').decode().lower().strip()
    for prefijo in ('partido del ', 'partido de '):
        texto = texto.removeprefix(prefijo)
    return texto


def pedir(url, params):
    clave = json.dumps({'url': url, **params}, sort_keys=True)
    if clave not in cache:
        r = httpx.get(url, params={**params, 'format': 'json', 'addressdetails': 1},
                      headers={'User-Agent': s.USER_AGENT, 'Accept-Language': 'es'}, timeout=15)
        time.sleep(s.PAUSA_ENTRE_GEOCODES_SEG)
        r.raise_for_status()
        cache[clave] = r.json()
        CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding='utf-8')
    return cache[clave]


def buscar_con_cache(query, **extra):
    datos = pedir(s.NOMINATIM_URL, {'q': query, 'viewbox': s.BBOX_GBA, 'bounded': 1, 'limit': 1, **extra})
    return datos[0] if datos else None


s._buscar_nominatim = buscar_con_cache  # mismo pedido que el scraper, con caché


def donde_cae(punto):
    """Partido (o 'caba') y barrio según geocodificación inversa del punto."""
    respuesta = pedir(REVERSE_URL, {'lat': punto[0], 'lon': punto[1], 'zoom': 14})
    a = respuesta.get('address', {})
    if 'autonoma de buenos aires' in norm(a.get('state')):
        return 'caba', norm(a.get('suburb'))
    # En algunas zonas (p. ej. Adrogué) OSM no pone el partido en address, pero
    # sí aparece en display_name: "Adrogué, Partido de Almirante Brown, ...".
    for parte in respuesta.get('display_name', '').split(', '):
        if parte.lower().startswith('partido'):
            return norm(parte), None
    for clave in ('state_district', 'county'):
        if a.get(clave):
            return norm(a[clave]), None
    for clave in ('town', 'city'):
        if (a.get(clave) or '').lower().startswith('partido'):
            return norm(a[clave]), None
    return norm(a.get('city') or a.get('town')) or None, None


def anterior(zona, tipo, partido):
    localidad = 'CABA' if tipo == 'barrio' else 'Buenos Aires'
    nombre = partido if tipo == 'alias' else zona  # encontrar_zona devuelve el partido del alias
    r = buscar_con_cache(f'{nombre}, {localidad}, Argentina')
    return (float(r['lat']), float(r['lon'])) if r else None


def nuevo(zona, tipo, partido):
    localidad = 'CABA' if tipo == 'barrio' else 'Buenos Aires'
    nombre = partido if tipo == 'alias' else zona
    return s.geocodificar_en_zona(f'{nombre}, {localidad}, Argentina', 'barrio', nombre, localidad)[0]


def zonas():
    for p in s.PARTIDOS_GBA:
        yield p, 'partido', s.PARTIDO_DE_LOCALIDAD.get(p, p)
    for alias, partido in s.ALIAS_LOCALIDAD_PARTIDO.items():
        yield alias, 'alias', partido
    for b in s.BARRIOS_CABA:
        yield b, 'barrio', None


def evaluar(punto, zona, tipo, partido):
    if punto is None:
        return 'abstiene'
    partido_real, barrio_real = donde_cae(punto)
    if tipo == 'barrio':
        return 'ok' if partido_real == 'caba' and barrio_real == norm(zona) else f'mal ({partido_real}/{barrio_real})'
    return 'ok' if partido_real and partido_real.endswith(norm(partido)) else f'mal ({partido_real})'


def main():
    filas = []
    for zona, tipo, partido in zonas():
        fila = {'zona': zona, 'tipo': tipo, 'partido_esperado': partido}
        for nombre, metodo in (('anterior', anterior), ('nuevo', nuevo)):
            punto = metodo(zona, tipo, partido)
            fila[nombre] = {'punto': punto, 'resultado': evaluar(punto, zona, tipo, partido)}
        filas.append(fila)
        print(f"{zona:22} {tipo:8} anterior={fila['anterior']['resultado']:34} nuevo={fila['nuevo']['resultado']}")
    (AQUI / 'resultado.json').write_text(json.dumps(filas, ensure_ascii=False, indent=1), encoding='utf-8')
    print()
    for tipo in ('partido', 'alias', 'barrio'):
        sub = [f for f in filas if f['tipo'] == tipo]
        for nombre in ('anterior', 'nuevo'):
            res = [f[nombre]['resultado'] for f in sub]
            print(f"{tipo:8} {nombre:9} ok {res.count('ok')}/{len(sub)}, mal {sum(r.startswith('mal') for r in res)}, "
                  f"se abstiene {res.count('abstiene')}")


if __name__ == '__main__':
    main()
