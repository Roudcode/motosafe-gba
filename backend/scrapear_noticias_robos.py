# -*- coding: utf-8 -*-
"""
Scraper de noticias de robos/asaltos en el GBA, para la tabla reportes_prensa
(ver backend/main.py, _asegurar_tabla_prensa). NO es en vivo -- pensado para
correr unas pocas veces por dia (a mano, o con el Programador de Tareas de
Windows), nunca en cada request. Ver la nota larga en main.py sobre por que
esto es una fuente separada de reportes_colaborativos y por que no alimenta
la alerta de proximidad del frontend.

Fuentes (v2 -- ver mas abajo por que se cambiaron):
  - Infobae: sitemap de la categoria policiales (XML, una <loc> por nota).
  - La Nación: listado de la sección /seguridad/ (HTML, se extraen los links
    a notas).
Clarin quedo afuera por ahora: su feed de policiales devuelve bloqueo (probado
con fetch generico) y necesita headers de navegador real para confirmar si es
un bloqueo real o solo del cliente usado para probar -- pendiente de validar
a mano si se quiere sumar.

Por que no se usa el RSS general de portada (v1 de este script): probado en
una corrida real, 183 items entre las dos fuentes (83 + 100) y 0 candidatas de
robo -- el RSS de portada mezcla politica, espectaculos, deportes, etc., y la
nota de policiales que sí sale publicada rara vez llega a portada. La
categoria/seccion dedicada trae contenido muchísimo más denso en esto, y
además el slug de la URL de cada nota ya suele traer el barrio o partido
("...-asaltaron-a-un-hombre-en-boedo-...", "...-robo-en-san-isidro-..."), lo
que permite un pre-filtro barato antes de bajar la nota completa.

El problema real de esta fuente no es conseguir noticias, es que una noticia
de robo casi nunca trae una direccion exacta ("en la esquina de X y Y"), la
mayoria solo menciona el barrio o el partido ("un hombre fue asaltado en
Villa Urquiza"). Por eso la ubicacion se resuelve en TRES niveles de
precision, de mas a menos exacto (ver extraer_ubicacion), y cada reporte
guarda con que nivel salio (nivel_precision + radio_metros) para que el
frontend lo pinte distinto -- un pin puntual si hay interseccion, un circulo
mas grande si solo se pudo ubicar el barrio. Nunca se inventa una precision
que el texto no tiene.

Pipeline por fuente:
  1. Bajar el sitemap/listado -> lista de URLs de notas.
  2. Pre-filtrar por el SLUG de la URL (palabra clave + gazetteer sobre el
     slug con guiones cambiados por espacios) -- esto evita bajar decenas de
     notas irrelevantes solo para descartarlas.
  3. Para cada URL que pasa el pre-filtro, bajar la nota completa y sacar
     titulo + descripcion (title/og:description del HTML) -- ni el sitemap ni
     el listado de sección traen esto, solo la pagina de la nota.
  4. Sobre ese titulo+descripcion real corre el mismo pipeline de siempre:
     es_candidata (confirma el pre-filtro con texto completo, no solo el
     slug) -> extraer_ubicacion -> geocodificar_nominatim -> guardar.

Modo de uso:
    python scrapear_noticias_robos.py            # dry-run: solo imprime que
                                                  # encontraria, no toca la base
    python scrapear_noticias_robos.py --guardar  # inserta de verdad

Corré primero SIN --guardar y mirá la salida a ojo antes de guardar nada --
la calidad de la geocodificacion depende de que tan literal sea el texto de
cada nota, y conviene chequear un par de casos reales antes de confiar en el
pipeline entero.
"""
import html
import os
import re
import sys
import time
import unicodedata
import xml.etree.ElementTree as ET

import httpx
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

# Nominatim exige un User-Agent que identifique la app (su politica de uso
# prohibe el default generico de las librerias HTTP) y pide no pasar de 1
# pedido por segundo -- ver el sleep en geocodificar_nominatim. Mismo host y
# mismo estilo de bbox que ya usa el frontend (ver geoRiesgo.js:geocodificar),
# para que un "San Martín, Vicente López" no termine resolviendo en Uruguay.
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "MotoSafeGBA-tesis-USAL/1.0 (proyecto academico, contacto en README del repo)"
BBOX_GBA = "-59.5,-33.9,-57.8,-35.3"
PAUSA_ENTRE_GEOCODES_SEG = 1.1

# Cada fuente sabe bajar su listado de URLs (sitemap XML o pagina HTML de
# sección) -- el resto del pipeline (prefiltro de slug, fetch de la nota,
# extraccion de titulo/descripcion, ubicacion, geocode) es identico para las
# dos, ver main().
FUENTES_SITEMAP = [
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/sitemap2/category/sociedad/policiales/"),
]
FUENTES_SECCION = [
    ("La Nación", "https://www.lanacion.com.ar/seguridad/", "https://www.lanacion.com.ar"),
]

# Tope de notas a evaluar por fuente y por corrida -- un sitemap de categoria
# o un listado de sección puede traer cientos de URLs viejas, y no tiene
# sentido (ni es amable con el sitio) bajarlas todas en cada corrida cuando
# alcanza con las mas recientes para una fuente que se corre varias veces por
# dia.
MAX_URLS_POR_FUENTE = 40
PAUSA_ENTRE_FETCHES_SEG = 0.5

# Palabras que hacen candidata a una noticia (titulo + descripcion, sin
# acentos ni mayusculas -- ver normalizar). No filtra por "moto" a proposito:
# un robo a pie en una esquina es igual de util para el mapa que uno con moto
# de por medio, el eje de esta capa es inseguridad en general, no siniestros.
PALABRAS_CLAVE_ROBO = [
    'robo', 'robaron', 'robar', 'asalto', 'asaltaron', 'asaltar',
    'arrebato', 'arrebataron', 'motochorro', 'motochorros', 'entradera',
    'entraderas', 'atracador', 'atracadores', 'ladrones', 'ladron',
    'delincuentes armados', 'asaltantes',
]

# Los 48 barrios oficiales de CABA + los partidos del GBA con mas poblacion/
# siniestralidad -- gazetteer para ubicar la noticia cuando no hay calle, y
# para acotar el geocode de una calle ambigua (ver extraer_ubicacion). Lista
# publica y estable (division administrativa oficial), no requiere scraping
# propio.
BARRIOS_CABA = [
    'Agronomía', 'Almagro', 'Balvanera', 'Barracas', 'Belgrano', 'Boedo',
    'Caballito', 'Chacarita', 'Coghlan', 'Colegiales', 'Constitución',
    'Flores', 'Floresta', 'La Boca', 'La Paternal', 'Liniers', 'Mataderos',
    'Monte Castro', 'Monserrat', 'Nueva Pompeya', 'Núñez', 'Palermo',
    'Parque Avellaneda', 'Parque Chacabuco', 'Parque Chas', 'Parque Patricios',
    'Puerto Madero', 'Recoleta', 'Retiro', 'Saavedra', 'San Cristóbal',
    'San Nicolás', 'San Telmo', 'Vélez Sarsfield', 'Versalles', 'Villa Crespo',
    'Villa del Parque', 'Villa Devoto', 'Villa General Mitre', 'Villa Lugano',
    'Villa Luro', 'Villa Ortúzar', 'Villa Pueyrredón', 'Villa Real',
    'Villa Riachuelo', 'Villa Santa Rita', 'Villa Soldati', 'Villa Urquiza',
]
PARTIDOS_GBA = [
    'La Matanza', 'San Isidro', 'Vicente López', 'Tigre', 'Quilmes',
    'Avellaneda', 'Lanús', 'Lomas de Zamora', 'Morón', 'Tres de Febrero',
    'San Martín', 'Merlo', 'Moreno', 'José C. Paz', 'Malvinas Argentinas',
    'San Miguel', 'Hurlingham', 'Ituzaingó', 'Esteban Echeverría', 'Ezeiza',
    'Almirante Brown', 'Berazategui', 'Florencio Varela', 'San Fernando',
    'Escobar', 'Pilar',
]
_RE_CALLE = r"[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ'.]{2,}(?:\s(?:de\s)?[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ'.]{1,}){0,3}"
RE_INTERSECCION = re.compile(rf"({_RE_CALLE})\s(?:y|esquina)\s({_RE_CALLE})")
RE_ALTURA = re.compile(rf"({_RE_CALLE})\s+al\s+(\d{{2,5}})")


def normalizar(texto):
    """Sin acentos y en minuscula, para que el matching de palabras clave no
    dependa de que la fuente haya escrito bien los tildes (pasa seguido en
    titulares)."""
    sin_acentos = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return sin_acentos.lower()


def es_candidata(titulo, descripcion):
    texto = normalizar(f"{titulo} {descripcion}")
    return any(normalizar(palabra) in texto for palabra in PALABRAS_CLAVE_ROBO)


def encontrar_zona(texto):
    """Primer barrio/partido del gazetteer que aparece en el texto, como
    (nombre, "CABA" o "Buenos Aires"), o None. Se usa tanto como fallback de
    ubicacion (nivel 'barrio') como para acotar el geocode de una calle
    ambigua (nivel 'interseccion'/'calle') -- en el GBA hay calles "San
    Martín" en decenas de partidos distintos, sin esta pista Nominatim puede
    resolver cualquiera de ellas.

    Devuelve tambien la localidad correcta (CABA para un barrio, "Buenos
    Aires" para un partido) porque son cosas distintas -- San Isidro NO es
    CABA, es otro partido del GBA. Pegarle "CABA, Argentina" a una zona que
    en realidad es un partido geocodifica mal o no encuentra nada."""
    texto_norm = normalizar(texto)
    for zona in BARRIOS_CABA:
        if normalizar(zona) in texto_norm:
            return zona, 'CABA'
    for zona in PARTIDOS_GBA:
        if normalizar(zona) in texto_norm:
            return zona, 'Buenos Aires'
    return None


def extraer_ubicacion(titulo, descripcion):
    """
    Devuelve (query_nominatim, nivel_precision, radio_metros) o None si no hay
    ninguna pista de ubicacion en el texto (en ese caso, la nota se descarta --
    mejor pocos reportes bien ubicados que muchos tirados al azar).

    Tres niveles, de mas a menos precision:
      1. 'interseccion' (calle Y calle / calle ESQUINA calle) -- el mas exacto,
         pero el menos frecuente: la mayoria de las notas no llega a este detalle.
      2. 'calle' (calle AL altura, ej. "Rivadavia al 4500") -- precision de
         cuadra, bastante mas comun que la interseccion.
      3. 'barrio' -- solo se pudo ubicar la zona mencionada, sin calle. Es el
         caso mas comun. El radio grande (800m) es a proposito: es mentira
         mostrar esto como si fuera un punto exacto.
    """
    texto = f"{titulo}. {descripcion}"
    zona_encontrada = encontrar_zona(texto)
    # Sin pista de zona en el texto, se asume CABA como default (no GBA en
    # general) porque en la practica las notas con detalle de calle suelen
    # ser de la Ciudad -- un sesgo conocido, no una certeza, pero mejor eso
    # que geocodificar sin ninguna localidad y arriesgar un resultado fuera
    # de la region entera.
    zona, localidad = zona_encontrada if zona_encontrada else (None, 'CABA')
    sufijo_zona = f", {zona}" if zona else ""

    m = RE_INTERSECCION.search(texto)
    if m:
        return (f"{m.group(1)} y {m.group(2)}{sufijo_zona}, {localidad}, Argentina", 'interseccion', 80)

    m = RE_ALTURA.search(texto)
    if m:
        return (f"{m.group(1)} {m.group(2)}{sufijo_zona}, {localidad}, Argentina", 'calle', 150)

    if zona:
        return (f"{zona}, {localidad}, Argentina", 'barrio', 800)

    return None


def geocodificar_nominatim(query):
    """Mismo geocoder y mismo bbox que el frontend (geoRiesgo.js), pero desde
    Python: User-Agent identificado (exigido por la politica de uso de
    Nominatim) y una pausa fija entre pedidos (tambien exigida, max 1/seg).
    No cachea entre corridas -- el volumen esperado (unas pocas notas por
    corrida, unas pocas corridas por dia) esta lejos de necesitarlo."""
    resp = httpx.get(
        NOMINATIM_URL,
        params={"format": "json", "q": query, "viewbox": BBOX_GBA, "bounded": 1, "limit": 1},
        headers={"User-Agent": USER_AGENT, "Accept-Language": "es"},
        timeout=10,
    )
    time.sleep(PAUSA_ENTRE_GEOCODES_SEG)
    resp.raise_for_status()
    datos = resp.json()
    if not datos:
        return None
    return float(datos[0]['lat']), float(datos[0]['lon'])


def extraer_urls_sitemap(xml_bytes):
    """Sitemap XML estandar (protocolo sitemaps.org) -- viene con namespace,
    por eso se itera por elem.tag.endswith('loc') en vez de buscar './/loc'
    a secas (ElementTree exige el namespace completo si no). Solo interesan
    las URLs; lastmod no se usa porque la vigencia de reportes_prensa ya se
    filtra en main.py por creado_en (fecha en que ESTE script encontro la
    nota), no por la fecha de publicacion de la fuente."""
    raiz = ET.fromstring(xml_bytes)
    return [elem.text.strip() for elem in raiz.iter() if elem.tag.endswith('loc') and elem.text]


def extraer_urls_seccion(html_text, dominio):
    """Listado HTML de una secion (no XML) -- se buscan directamente los
    href que apuntan a una nota de esa misma sección. El patron de La Nacion
    (".../seguridad/...-nidNNNNNNN/") es estable: el "nid" (news id) al
    final del slug es parte de su CMS y no un detalle de una nota puntual.

    El dominio en el href es OPCIONAL a proposito: probado contra la pagina
    real, La Nacion sirve estos links como ruta relativa (href="/seguridad/
    ...") en vez de URL absoluta -- exigir el dominio completo en el regex
    (como en la v1 de esta funcion) hacia que nunca matchee nada."""
    patron = re.compile(rf'href="(?:{re.escape(dominio)})?(/seguridad/[^"?#]+-nid\d+/?)"')
    vistos = []
    for path in patron.findall(html_text):
        url = dominio + path
        if url not in vistos:
            vistos.append(url)
    return vistos


def slug_a_texto(url):
    """Convierte el slug de la URL en texto plano para poder correrle el
    mismo filtro de palabras clave y el mismo gazetteer que se usa sobre
    titulo/descripcion, sin tener que bajar la nota completa todavia. Ni el
    sitemap de Infobae ni el listado de sección de La Nación traen titulo o
    descripcion -- eso solo está en la página de cada nota, y bajar las
    ~40 notas de cada corrida solo para descartar la mayoría por palabra
    clave sería un pedido de más por nada (y mas riesgo de rate-limit del
    lado del sitio)."""
    path = re.sub(r'^https?://[^/]+', '', url)
    slug = path.rstrip('/').rsplit('/', 1)[-1]
    slug = re.sub(r'-nid\d+$', '', slug)  # "nid" de La Nación al final del slug
    return slug.replace('-', ' ')


def _meta_content(html_text, atributo, valor):
    """Busca <meta ... content="..."> por nombre/propiedad (og:description,
    description), sin asumir el orden de los atributos -- distintos CMS
    escriben "property antes de content" o al revés."""
    patron = re.compile(
        rf'<meta[^>]+(?:{atributo}=["\']{re.escape(valor)}["\'][^>]*content=["\']([^"\']*)["\']'
        rf'|content=["\']([^"\']*)["\'][^>]*{atributo}=["\']{re.escape(valor)}["\'])',
        re.IGNORECASE,
    )
    m = patron.search(html_text)
    if not m:
        return None
    return m.group(1) or m.group(2)


def extraer_titulo_descripcion(html_text):
    """El sitemap y el listado de sección no traen titulo/descripcion (a
    diferencia del RSS) -- hay que bajar la nota entera y sacarlos del
    <title> y del meta og:description (con description a secas de
    respaldo). html.unescape porque estos campos suelen venir con entidades
    (&amp;, &quot;, etc)."""
    m_title = re.search(r'<title[^>]*>(.*?)</title>', html_text, re.IGNORECASE | re.DOTALL)
    titulo = html.unescape(m_title.group(1)).strip() if m_title else ''
    # el <title> de estos sitios trae el nombre del medio pegado al final
    titulo = re.sub(r'\s*[-|]\s*(Infobae|LA NACION|La Nación).*$', '', titulo, flags=re.IGNORECASE).strip()

    descripcion = _meta_content(html_text, 'property', 'og:description')
    if descripcion is None:
        descripcion = _meta_content(html_text, 'name', 'description')
    descripcion = html.unescape(descripcion).strip() if descripcion else ''

    return titulo, descripcion


def _asegurar_tabla(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reportes_prensa (
            id SERIAL PRIMARY KEY,
            lat DOUBLE PRECISION NOT NULL,
            lng DOUBLE PRECISION NOT NULL,
            nivel_precision VARCHAR(20) NOT NULL,
            radio_metros INTEGER NOT NULL,
            titular TEXT NOT NULL,
            url_fuente VARCHAR(500) NOT NULL UNIQUE,
            fuente VARCHAR(50) NOT NULL,
            publicado_en TIMESTAMPTZ,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)


def _procesar_url(url, nombre_fuente, guardar, cur, contadores):
    """Pipeline comun a cualquier fuente para una URL de nota individual:
    fetch de la nota completa -> titulo/descripcion reales -> es_candidata
    (confirma el prefiltro de slug con texto completo) -> ubicacion ->
    geocode -> guardar. Devuelve nada, solo imprime y actualiza contadores
    (dict mutable, para no volver todo global ni devolver una tupla de 3
    numeros de cada llamada)."""
    try:
        resp = httpx.get(url, headers={"User-Agent": USER_AGENT}, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        titulo, descripcion = extraer_titulo_descripcion(resp.text)
    except Exception as err:
        print(f"  [error al bajar la nota: {err}] {url}")
        return
    finally:
        time.sleep(PAUSA_ENTRE_FETCHES_SEG)

    if not titulo or not es_candidata(titulo, descripcion):
        return
    contadores['candidatas'] += 1

    ubicacion = extraer_ubicacion(titulo, descripcion)
    if ubicacion is None:
        print(f"  [sin ubicar] {titulo}")
        return
    query, nivel, radio = ubicacion
    try:
        punto = geocodificar_nominatim(query)
    except Exception as err:
        print(f"  [error geocode: {err}] {titulo}")
        return
    if punto is None:
        print(f"  [geocode vacio -- query: \"{query}\"] {titulo}")
        return
    contadores['ubicadas'] += 1
    lat, lng = punto
    print(f"  [{nivel}, r={radio}m] ({lat:.5f}, {lng:.5f}) -- {titulo}")

    if guardar:
        cur.execute("""
            INSERT INTO reportes_prensa (lat, lng, nivel_precision, radio_metros, titular, url_fuente, fuente, publicado_en)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url_fuente) DO NOTHING
        """, (lat, lng, nivel, radio, titulo, url, nombre_fuente, None))
        if cur.rowcount > 0:
            contadores['guardadas'] += 1


def main():
    guardar = '--guardar' in sys.argv
    conn = cur = None
    if guardar:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        _asegurar_tabla(cur)

    contadores = {'candidatas': 0, 'ubicadas': 0, 'guardadas': 0}

    for nombre_fuente, url_sitemap in FUENTES_SITEMAP:
        print(f"\n=== {nombre_fuente} (sitemap: {url_sitemap}) ===")
        try:
            resp = httpx.get(url_sitemap, headers={"User-Agent": USER_AGENT}, timeout=15)
            resp.raise_for_status()
            urls = extraer_urls_sitemap(resp.content)
        except Exception as err:
            print(f"  ERROR al bajar/parsear el sitemap: {err}")
            continue
        print(f"  {len(urls)} URLs en el sitemap")

        candidatas_slug = [u for u in urls if es_candidata(slug_a_texto(u), '')][:MAX_URLS_POR_FUENTE]
        print(f"  {len(candidatas_slug)} pasan el prefiltro de slug (se bajan completas)")
        for url in candidatas_slug:
            _procesar_url(url, nombre_fuente, guardar, cur, contadores)

    for nombre_fuente, url_seccion, dominio in FUENTES_SECCION:
        print(f"\n=== {nombre_fuente} (sección: {url_seccion}) ===")
        try:
            resp = httpx.get(url_seccion, headers={"User-Agent": USER_AGENT}, timeout=15)
            resp.raise_for_status()
            urls = extraer_urls_seccion(resp.text, dominio)
        except Exception as err:
            print(f"  ERROR al bajar/parsear la sección: {err}")
            continue
        print(f"  {len(urls)} notas en el listado")

        candidatas_slug = [u for u in urls if es_candidata(slug_a_texto(u), '')][:MAX_URLS_POR_FUENTE]
        print(f"  {len(candidatas_slug)} pasan el prefiltro de slug (se bajan completas)")
        for url in candidatas_slug:
            _procesar_url(url, nombre_fuente, guardar, cur, contadores)

    if guardar:
        conn.commit()
        cur.close()
        conn.close()

    print(f"\n{contadores['candidatas']} noticias candidatas, {contadores['ubicadas']} pudieron ubicarse"
          + (f", {contadores['guardadas']} nuevas guardadas en la base" if guardar
             else " (dry-run, no se guardo nada -- corré con --guardar para insertar)"))


if __name__ == "__main__":
    main()
