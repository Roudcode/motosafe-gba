# -*- coding: utf-8 -*-
"""
Scraper de noticias de robos/asaltos en el GBA, para la tabla reportes_prensa
(ver backend/main.py, _asegurar_tabla_prensa). NO es en vivo -- pensado para
correr unas pocas veces por dia (a mano, o con el Programador de Tareas de
Windows), nunca en cada request. Ver la nota larga en main.py sobre por que
esto es una fuente separada de reportes_colaborativos y por que no alimenta
la alerta de proximidad del frontend.

Categorias (v5): cada nota se clasifica en 'robo' o 'choque' segun que lista
de palabras clave matchea primero (ver CATEGORIAS_PALABRAS_CLAVE), y esa
categoria viaja hasta la base (columna tipo_incidente) y hasta el frontend,
que la muestra con un icono propio por tipo. El backend tambien la usa para
ajustar -- de forma visible, sin tocar la calibracion del modelo entrenado
-- el nivel de riesgo de /hotspots y /corredores (con choques recientes) y
de /hotspots-inseguridad (con robos recientes). Ver _ajuste_por_reportes_recientes
en main.py.

Fuentes (v4):
  - Infobae: sitemap de la categoria policiales (XML, una <loc> por nota).
  - La Nación: listado de la sección /seguridad/ (HTML, se extraen los links
    a notas).
  - Página12: RSS de la sección Sociedad (no tienen RSS de policiales
    dedicado -- mas diluido que Infobae/La Nacion, pero mucho mas acotado
    que un RSS de portada general).
  - Diario Popular / 0221: dos medios regionales (Diario Popular cubre GBA
    en general, 0221 cubre La Plata/Berisso/Ensenada) que corren sobre la
    misma plataforma de CMS -- mismo patron de sitemap en robots.txt
    (sitemap-news.xml) y de URL (segmento /policiales/ en la ruta). A
    diferencia de Infobae, ese sitemap NO viene ya filtrado por categoria
    (trae política, deportes, etc. mezclado), así que se filtra primero por
    el segmento /policiales/ de la URL (barato, antes que el prefiltro de
    slug de siempre) -- ver FUENTES_SITEMAP_SECCIONADO. Se probaron por
    tener foco geografico mas chico que Infobae/La Nacion/Página12 y por
    eso mismo mas propensos a mencionar la calle exacta, no solo el barrio.
  - Clarín / TN: bloquearon el acceso "normal" tanto en una prueba de Rodo
    como en una prueba independiente hecha para este cambio (mismo
    resultado con clientes distintos, asi que no es un problema puntual de
    un cliente). En vez de descartarlas, se prueban varios metodos en
    cascada con headers de navegador real (ver HEADERS_NAVEGADOR y
    descubrir_urls_multiestrategia): sitemap(s) declarados en robots.txt
    (siguiendo un nivel de indice si hace falta, ver
    extraer_urls_sitemap_recursivo), sitemap "adivinado" en la raiz
    (/sitemap.xml, convencion muy comun que no siempre se declara en
    robots.txt), sitemap estilo Arc Publishing (por si tambien corren sobre
    Arc como Infobae/La Nacion), y por ultimo scrapear la seccion de
    policiales directo. Si ninguno funciona en la practica, el script lo
    dice explicitamente en la salida y sigue con las demas fuentes -- no es
    un error, es que esa fuente sigue bloqueada.

Fuentes nuevas (v6) -- misma logica que arriba, ahora apuntada a llenar el
agujero geografico real que tenia esta lista: hasta v5 la cobertura era
CABA-generica (Infobae/La Nacion/Pagina12) + La Plata/Berisso/Ensenada
(0221) + GBA sin discriminar (Diario Popular), pero zona norte y zona
oeste del conurbano no tenian NINGUNA fuente propia -- toda nota de esa
zona dependia de que un medio nacional se dignara a cubrirla. Se
investigaron mas de 25 medios chicos/regionales del GBA (busqueda amplia
por zona: norte, oeste, sur, La Plata, y agencias que cubren varios
partidos a la vez) y a cada uno se le probo primero si tenia un FEED RSS
de la categoria policiales/seguridad ya armado (algo que Infobae/Pagina12
no ofrecen pero WordPress y Blogger si, de fabrica, con solo agregarle
/feed/ o el patron propio de Blogger a la URL de la categoria) -- eso es
categoricamente mejor que sitemap: trae titulo+descripcion sin bajar cada
nota (como FUENTES_RSS de siempre), y ya viene acotado a la categoria
correcta sin depender de que el segmento de la URL diga "policiales".
Encontrados y confirmados funcionando (con items reales, no solo XML
valido vacio -- varios "casi funcionan" pero el feed esta vacio, se
descartaron esos, ver mas abajo):
  - Diario Conurbano (Lomas de Zamora / conurbano sur en general):
    RSS de /policiales/feed/.
  - Infocielo (provincia en general, tono mas politico-judicial que
    policial puro pero cubre GBA ancho): RSS de
    /judiciales-y-policiales/feed/.
  - Primer Plano Online (La Matanza, Moron, Merlo, Ituzaingo, Hurlingham,
    Tres de Febrero, San Martin -- zona oeste amplia): RSS de
    /noticias/policiales/feed/.
  - Zona Norte Diario (San Isidro, Vicente Lopez, Tigre, San Fernando):
    ojo, su categoria policial se llama "seguridad", no "policiales" --
    RSS de /SECCIONES/informacion-general/seguridad/feed/.
  - Periodico Para Todos (Vicente Lopez, San Isidro, San Fernando, Tigre,
    Malvinas Argentinas, Jose C. Paz -- otra fuente de zona norte,
    biblioteca de notas mas chica que Zona Norte Diario pero misma zona,
    asi que suma en vez de solapar del todo): RSS de
    /secciones/policiales/feed/.
  - Zona Sur Diario (Avellaneda, Lanus, Quilmes, Berazategui): corre sobre
    Blogger, no WordPress -- el feed no es /categoria/feed/ sino el patron
    propio de Blogger para busqueda por etiqueta:
    /feeds/posts/default/-/Policiales?alt=rss.
  - Zona Oeste Diario (Moron, Ituzaingo, Hurlingham, La Matanza, Merlo,
    Malvinas Argentinas): mismo caso, tambien Blogger, mismo patron de
    feed por etiqueta.

Ademas se suman fuentes sin RSS de categoria pero con sitemap general
abierto (mismo patron que Diario Popular/0221 en FUENTES_SITEMAP_SECCIONADO
-- sitemap sin discriminar + filtro por segmento /policiales/ de la URL):
  - El Dia (La Plata): confirmado que sus notas de policiales llevan el
    segmento /policiales/ en la URL real (ej.
    ".../policiales/a-la-buena-de-dios-...-policiales_1789137000").
  - Minutouno (nacional, pero con volumen real de notas de GBA): a
    diferencia de los anteriores, ahi el crimen esta mezclado dentro de la
    seccion "sociedad" (no tiene una seccion policial propia) -- se agrega
    igual con segmento "sociedad" a sabiendas de que el filtro de segmento
    va a dejar pasar mucho mas volumen no-policial hacia el prefiltro de
    slug de siempre (el propio prefiltro de palabra clave se encarga de
    descartar el resto, a costa de mas requests desperdiciados que con un
    segmento realmente acotado).

Correcciones v6.1 (a partir de la primer corrida real de Rodo con las
fuentes de v6, no de una prueba propia -- documentado para no repetir el
mismo error de diagnostico):
  - Infocielo devolvia 403 Forbidden con el USER_AGENT identificado de
    siempre, pero la MISMA url de feed respondio bien con headers de
    navegador real -- mismo sintoma que Clarín/TN (bloqueo por User-Agent,
    no por bot detection mas sofisticado), asi que ahora FUENTES_RSS
    soporta un cuarto elemento opcional por tupla (headers), e Infocielo lo
    usa con HEADERS_NAVEGADOR en vez del USER_AGENT identificado.
  - El Diario Sur, Inforbano e Infosur Diario dieron "0 caen en
    /policiales/" en la corrida real -- dos causas DISTINTAS, no una sola:
    (a) El Diario Sur no tiene segmento de categoria en la URL, tiene
    segmento de LOCALIDAD (esteban-echeverria, alte-brown, provinciales...)
    -- el supuesto de que seguian la misma convencion que Diario Popular/
    0221 era simplemente incorrecto; (b) Inforbano e Infosur Diario
    apuntaban a un sitemap INDICE (sitemap_index.xml / sitemap.xml que a su
    vez lista sitemaps hijos), y el codigo de FUENTES_SITEMAP_SECCIONADO
    llamaba a extraer_urls_sitemap (NO la version recursiva) -- eso hizo
    que se filtraran por /policiales/ los NOMBRES DE ARCHIVO de los
    sitemaps hijos (post-sitemap3.xml, category-sitemap.xml...) en vez de
    URLs de notas reales, que por supuesto no calzan con ningun segmento.
    Se corrigen las dos cosas distinto: las tres fuentes se mueven de
    FUENTES_SITEMAP_SECCIONADO a FUENTES_SITEMAP (sin segmento, prefiltro
    de slug directo sobre el sitemap completo -- ver la nota en esa lista
    sobre por que esto es viable con volumen chico), Y ADEMAS main() ahora
    usa extraer_urls_sitemap_recursivo (la misma funcion que ya resolvia
    este problema para Clarín) para TODAS las fuentes de tipo sitemap, no
    solo las de FUENTES_MULTIESTRATEGIA -- asi que si alguna fuente mas el
    dia de mañana resulta apuntar a un indice sin que se sepa de antemano,
    el script baja un nivel solo en vez de tratar nombres de archivo como
    si fueran notas.

Correcciones v6.2 (segunda corrida real de Rodo con v6.1, 11/09):
  - El Diario Sur e Infosur Diario: confirmados funcionando (el fix de
    v6.1 resolvio ambos casos). Inforbano seguia en 0, por una causa
    DISTINTA de la de v6.1: su indice de sitemaps (WordPress/Yoast) mezcla
    post-sitemapN.xml (articulos reales, 38 archivos) con page-sitemap,
    tdb_templates-sitemap, category-sitemap, post_tag-sitemapN (uno por
    tag/categoria/autor, no por fecha) y author-sitemap -- en ORDEN
    INVERSO, el presupuesto de intentos se gastaba entero en
    author-sitemap y post_tag-sitemapN sin llegar nunca a un post-sitemap
    real (858 URLs bajadas, 0 candidatas, ninguna era una nota). Se
    agregaron esos tipos a _SITEMAP_TIPOS_IRRELEVANTES para que se
    prueben de ultimos -- fix generalizable a cualquier sitio WordPress
    con Yoast SEO, no especifico de Inforbano.
  - Infocielo: SIGUE devolviendo 403 aun con HEADERS_NAVEGADOR (la prueba
    de v6.1 que decia que funcionaba con headers de navegador no se
    reprodujo en la corrida real de Rodo). Se trata como fuente bloqueada,
    mismo estado que Clarín (parcial) y TN (total) -- no vale la pena
    seguir iterando con mas headers sin poder inspeccionar la respuesta
    real del WAF: puede ser un bloqueo de infraestructura (Cloudflare o
    similar) que no distingue por User-Agent sino por huella de cliente
    HTTP completa, y ahi headers no alcanzan. Documentado como limitacion
    explicita de la tesis junto con TN, no como bug pendiente de arreglar.

Probados y DESCARTADOS en esta ronda (para no repetir la busqueda):
  - Diario Anticipos, Moron Digital, Vivi el Oeste, Infosur Diario (el feed
    de categoria, no el sitemap -- ese si se usa, ver arriba): todos
    devuelven un feed RSS con la estructura valida pero CERO items (canal
    vacio) o un 404 directo -- no es que esten bloqueados, es que la
    convencion de URL de feed que se probo no es la que usan.
  - Agencia Zona Norte, Zona Norte Vision: no tienen feed RSS de ninguna
    categoria (se confirmo bajando el HTML de la portada), y sus URLs de
    nota son solo un ID numerico sin segmento de sección
    (zonanortevision.com.ar/427920/) -- no hay forma barata de acotar por
    URL antes de bajar cada nota, exactamente el problema que ya se
    documento mas arriba con el RSS de portada general de Infobae/La
    Nacion (demasiado diluido).
  - SM Noticias: mismo problema de URL sin segmento
    (smnoticias.com/noticias/285484).
  - La Urbe Digital, La Buena Info: bloquean explicitamente a bots de IA
    (ClaudeBot, GPTBot, etc.) en su robots.txt vía Content-Signal
    ("ai-train=no"/Disallow general para esos user-agents puntuales) -- a
    diferencia del resto de esta lista, que solo restringe /wp-admin/ o
    nada, esta es una señal explicita de la fuente que conviene respetar
    aunque el User-Agent que usa este script no sea ninguno de los
    listados por nombre.
  - 24con: su robots.txt tiene "Allow: /" seguido de un "Disallow: /"
    general mas abajo -- configuracion contradictoria, se prefiere no
    interpretarla y descartar la fuente antes que arriesgar un acceso que
    el sitio no queria permitir.
  - InfoCielo (La Plata) [ya descartado en v4, se mantiene la nota]: tiene
    su sitemap partido en 475 archivos "post-sitemapN.xml" sin orden
    cronologico confiable por numero (se verifico: el archivo con el
    numero mas alto no es el mas reciente, tiene notas de 2024) y sin
    sitemap de noticias dedicado -- filtrar esto bien exigiria bajar y
    ordenar por <lastmod> los 475 archivos en cada corrida, demasiado
    costoso para el beneficio. NOTA v6: si tiene RSS de categoria
    (/judiciales-y-policiales/feed/) -- se agrega por esa via en vez del
    sitemap, ver arriba.
  - Diario Crónica (diariocronica.com.ar) [ya descartado en v4, se
    mantiene la nota]: es de Comodoro Rivadavia, Chubut, no tiene nada que
    ver con GBA -- se descarta por region, no por tecnica. (No confundir
    con "Crónica" a secas, cronica.com.ar, que si es de Buenos Aires --
    esa se evaluo aparte y no se agrego todavia por falta de RSS/sitemap
    declarado, queda como candidato para una proxima ronda via scrape de
    listado, mismo metodo que La Nacion.)

Redes sociales (Instagram, Twitter/X, Facebook, Telegram): evaluadas y
descartadas a proposito para este scraper. No tienen RSS/sitemap publico,
exigen login para casi cualquier busqueda util, y su anti-bot esta pensado
especificamente para frenar este tipo de acceso automatizado -- un script
que corre unas pocas veces por dia se rompe con el primer cambio de HTML o
bloqueo de IP, y usar una cuenta propia para saltear el login arriesga que
se la suspendan. Ademas no se encontro un canal publico de Telegram real y activo
especifico de robos en el GBA (se buscó; el unico resultado real que aparecio
es de Mexico, no sirve) -- no tiene sentido escribir codigo apuntando a una
fuente que no esta confirmada. Queda como limitacion/trabajo futuro explicito
para la tesis, no como algo pendiente de este script.

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
# extraccion de titulo/descripcion, ubicacion, geocode) es identico para
# todas, ver main() y _procesar_url.
FUENTES_SITEMAP = [
    ("Infobae", "https://www.infobae.com/arc/outboundfeeds/sitemap2/category/sociedad/policiales/"),
    # v6 -- estas tres NO tienen ningun segmento de categoria en la URL (a
    # diferencia de Infobae, cuyo sitemap ya viene acotado a la categoria de
    # origen): El Diario Sur usa un segmento de LOCALIDAD
    # (esteban-echeverria, alte-brown, provinciales...), Inforbano e Infosur
    # Diario usan slugs planos sin categoria ni localidad
    # (/2016/06/29/asesinaron-a-.../ o directo /el-titulo-como-slug/). Se
    # probo primero como FUENTES_SITEMAP_SECCIONADO con segmento
    # "policiales" y dio 0 candidatas en una corrida real (correcto: el
    # segmento no existe) -- van aca en cambio, con el prefiltro de slug de
    # siempre corriendo sobre el sitemap COMPLETO (no acotado por
    # categoria), igual que Infobae pero sin el filtro extra. El volumen es
    # chico (sitios regionales, no cientos de notas por dia) asi que el
    # costo de bajar de mas es bajo.
    ("El Diario Sur", "https://www.eldiariosur.com/sitemap.xml"),
    ("Inforbano", "https://inforbano.com.ar/sitemap_index.xml"),
    ("Infosur Diario", "https://infosurdiario.com.ar/sitemap.xml"),
]
FUENTES_SECCION = [
    ("La Nación", "https://www.lanacion.com.ar/seguridad/", "https://www.lanacion.com.ar", "seguridad"),
]
# RSS que ya trae titulo+descripcion (no hace falta bajar cada nota
# completa como con sitemap/seccion) -- reservado para fuentes cuyo feed
# ya viene acotado a una sección razonable, nunca portada general (ver la
# nota larga al principio del archivo sobre por que el RSS de portada de
# Infobae/La Nacion resulto inutil para esto).
FUENTES_RSS = [
    ("Página12", "https://www.pagina12.com.ar/arc/outboundfeeds/rss/secciones/sociedad/notas"),
    # v6 -- ver la nota larga al principio del archivo ("Fuentes nuevas v6")
    # para el detalle de por que cada una de estas se agrega por RSS de
    # categoria en vez de sitemap, y que otras se probaron y no tenian feed.
    ("Diario Conurbano", "https://diarioconurbano.com.ar/policiales/feed/"),
    # Bloquea el USER_AGENT identificado con 403 (confirmado en una corrida
    # real) pero no headers de navegador -- ver "Correcciones v6.1" arriba.
    # Tercer elemento opcional de la tupla: "navegador" pide HEADERS_NAVEGADOR
    # en vez del USER_AGENT identificado de siempre (ver el loop de
    # FUENTES_RSS en main()).
    ("Infocielo", "https://www.infocielo.com/judiciales-y-policiales/feed/", "navegador"),
    ("Primer Plano Online", "https://primerplanoonline.com.ar/noticias/policiales/feed/"),
    ("Zona Norte Diario", "https://www.zonanortediario.com.ar/SECCIONES/informacion-general/seguridad/feed/"),
    ("Periódico Para Todos", "https://periodicoparatodos.com.ar/secciones/policiales/feed/"),
    # Estas dos corren sobre Blogger (no WordPress) -- el feed de categoria
    # no es /policiales/feed/ sino el patron propio de Blogger para buscar
    # por etiqueta ("label"). parsear_rss les sirve igual (Blogger devuelve
    # RSS 2.0 real con ?alt=rss, no un Atom disfrazado).
    ("Zona Sur Diario", "https://www.zonasurdiario.com.ar/feeds/posts/default/-/Policiales?alt=rss"),
    ("Zona Oeste Diario", "https://www.zonaoestediario.com.ar/feeds/posts/default/-/Policiales?alt=rss"),
]
# Sitemap general (mezcla todas las secciones) + segmento de URL a filtrar
# antes de aplicar el prefiltro de slug de siempre -- ver la nota larga al
# principio del archivo sobre Diario Popular / 0221 y por que hace falta
# este filtro extra que Infobae no necesita (su sitemap ya viene acotado a
# la categoria policiales de origen).
FUENTES_SITEMAP_SECCIONADO = [
    ("Diario Popular", "https://www.diariopopular.com.ar/sitemap-news.xml", "policiales"),
    ("0221", "https://www.0221.com.ar/sitemap-news.xml", "policiales"),
    # v6 -- ver la nota larga al principio del archivo ("Fuentes nuevas v6").
    # El Día: segmento /policiales/ confirmado en una URL de nota real.
    ("El Día", "https://www.eldia.com/news_1.xml", "policiales"),
    # Minutouno: el crimen no tiene seccion propia, vive dentro de
    # "sociedad" -- este filtro deja pasar mucho mas volumen no-policial
    # que las demas fuentes de esta lista (el prefiltro de slug de siempre
    # se encarga del resto, a costa de mas requests desperdiciados).
    ("Minutouno", "https://www.minutouno.com/sitemap-news.xml", "sociedad"),
]

# Headers "de navegador real": tanto una prueba de Rodo como una prueba
# independiente hecha para este cambio (clientes distintos, mismo
# resultado) chocaron con bloqueo al pedirle Clarín/TN con un User-Agent
# identificado como bot. No hay garantia de que esto lo resuelva -- puede
# ser un bloqueo de infraestructura (Cloudflare o similar), no solo un
# check de User-Agent -- por eso descubrir_urls_multiestrategia prueba
# varios metodos en cascada en vez de apostar a uno solo. Con Infobae/La
# Nación/Página12 no hace falta disimular (no bloquean), ahi se sigue
# usando el USER_AGENT identificado de siempre.
HEADERS_NAVEGADOR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "es-AR,es;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com/",
}
# (dominio, [rutas de sección a probar como ultimo recurso]) -- ver
# descubrir_urls_multiestrategia para el resto de los metodos que se
# prueban antes de llegar a scrapear la sección directo.
FUENTES_MULTIESTRATEGIA = [
    ("Clarín", "https://www.clarin.com", ["https://www.clarin.com/policiales/"]),
    ("TN", "https://www.tn.com.ar", ["https://www.tn.com.ar/policiales/"]),
]

# Tope de notas a evaluar por fuente y por corrida -- un sitemap de categoria
# o un listado de sección puede traer cientos de URLs viejas, y no tiene
# sentido (ni es amable con el sitio) bajarlas todas en cada corrida cuando
# alcanza con las mas recientes para una fuente que se corre varias veces por
# dia.
MAX_URLS_POR_FUENTE = 40
PAUSA_ENTRE_FETCHES_SEG = 0.5

# Palabras que hacen candidata a una noticia, agrupadas por CATEGORIA (titulo +
# descripcion, sin acentos ni mayusculas -- ver normalizar). v5 suma 'choque'
# junto a 'robo' porque el frontend ahora distingue una capa de incidentes
# recientes por tipo (icono/emoji propio por categoria, ver
# frontend/src/components/MapaMotoSafe.jsx) y el backend usa el tipo para
# ajustar el nivel de riesgo mostrado (ver _ajuste_por_reportes_recientes en
# main.py: los choques recientes ajustan el riesgo de siniestro vial de
# /hotspots y /corredores, los robos recientes ajustan la capa de densidad de
# delito de /hotspots-inseguridad -- cada categoria pega en el modelo que le
# corresponde semanticamente).
#
# CATEGORIAS_PALABRAS_CLAVE es un dict ORDENADO a proposito: categoria_de()
# devuelve la PRIMERA que matchea, asi que el orden es una prioridad
# explicita. 'robo' va primero porque en una nota que menciona ambas cosas
# (ej. "chocó escapando de un asalto") el hecho central para esta tesis
# (inseguridad, no trafico) es el robo.
#
# No se filtra por "moto" a proposito en ninguna de las dos: un robo a pie o
# un choque de auto en una esquina son igual de utiles para el mapa que uno
# con moto de por medio, el eje de esta capa es inseguridad/siniestralidad en
# general, no exclusivamente motociclistas.
PALABRAS_CLAVE_ROBO = [
    'robo', 'robaron', 'robar', 'asalto', 'asaltaron', 'asaltar',
    'arrebato', 'arrebataron', 'motochorro', 'motochorros', 'entradera',
    'entraderas', 'atracador', 'atracadores', 'ladrones', 'ladron',
    'delincuentes armados', 'asaltantes',
]
PALABRAS_CLAVE_CHOQUE = [
    'choque', 'choco', 'chocaron', 'colision', 'colisiono', 'colisionaron',
    'volco', 'volcaron', 'atropello', 'atropellaron', 'atropellar',
    'siniestro vial', 'despiste', 'despisto', 'accidente de transito',
    'accidente vial', 'embistio', 'embistieron',
]
CATEGORIAS_PALABRAS_CLAVE = {
    'robo': PALABRAS_CLAVE_ROBO,
    'choque': PALABRAS_CLAVE_CHOQUE,
}

# Los 48 barrios oficiales de CABA + los partidos del GBA con mas poblacion/
# siniestralidad -- gazetteer para ubicar la noticia cuando no hay calle, y
# para acotar el geocode de una calle ambigua (ver extraer_ubicacion). Lista
# publica y estable (division administrativa oficial), no requiere scraping
# propio.
#
# La Plata, Berisso y Ensenada se agregaron en v4 junto con la fuente 0221
# (ver FUENTES_SITEMAP_SECCIONADO): sin esto, esa fuente entera resolvia
# "[sin ubicar]" en todas sus notas -- 0221 cubre especificamente esa zona
# y casi nunca la nombra como "GBA" a secas, siempre por el partido/
# localidad puntual. City Bell no es un partido en si (es una localidad
# dentro del partido de La Plata) pero se la agrega igual porque Nominatim
# la reconoce como lugar propio y aparecio repetida en notas reales de
# 0221 sin mencionar "La Plata" en el mismo parrafo.
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
    # Gran La Plata -- ver el comentario arriba de BARRIOS_CABA. City Bell
    # antes de La Plata a proposito: si el texto menciona ambos, gana la
    # localidad mas especifica (encontrar_zona devuelve el primer match).
    'City Bell', 'La Plata', 'Berisso', 'Ensenada',
]
_RE_CALLE = r"[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ'.]{2,}(?:\s(?:de\s)?[A-ZÁÉÍÓÚÑ][\wÁÉÍÓÚÑáéíóúñ'.]{1,}){0,3}"
RE_INTERSECCION = re.compile(rf"({_RE_CALLE})\s(?:y|esquina)\s({_RE_CALLE})")
RE_ALTURA = re.compile(rf"({_RE_CALLE})\s+al\s+(\d{{2,5}})")

# Nombres de partido/barrio del GBA que TAMBIEN son nombre de una ciudad en
# otra provincia (ambiguedad real del espanol: "San Martin" es un partido
# del GBA pero tambien una ciudad de Tucuman/Mendoza/San Juan). Si el
# gazetteer matchea "San Martín" y ESE MISMO MATCH viene seguido de "de
# <provincia>" (ver _es_de_otra_provincia), se descarta ese match e se
# sigue buscando otro -- visto en un caso real: "un ex jugador de San
# Martín de Tucumán" resolvia como si fuera el partido de GBA.
#
# v3 hacia este chequeo sobre el TEXTO COMPLETO de la nota (cualquier
# mencion de la provincia en cualquier parte, no solo pegada al match)
# y descartaba la nota entera -- eso causo una regresion real: varias de
# estas provincias (Córdoba, Santa Fe, Jujuy, Entre Ríos, Salta) son
# TAMBIEN nombres de avenidas comunes en el GBA, asi que una nota que
# mencionaba, por ejemplo, la ciudad de Córdoba en un parrafo aparte
# (nada que ver con la ubicacion del robo) terminaba descartando una
# direccion en Av. Córdoba real y bien ubicada ("La Matanza" paso de
# ubicarse correctamente a "[sin ubicar]"). v4 localiza el chequeo:
# solo descarta el match puntual que tiene la provincia pegada al lado,
# no la nota entera.
PROVINCIAS_NO_GBA = [
    'Tucumán', 'Mendoza', 'San Juan', 'Córdoba', 'Salta', 'Santa Fe',
    'Mar del Plata', 'Rosario', 'Neuquén', 'Chaco', 'Misiones', 'Jujuy',
    'Corrientes', 'Entre Ríos', 'La Rioja', 'Catamarca', 'Formosa',
    'Santiago del Estero', 'Chubut', 'Río Negro', 'Santa Cruz', 'Tierra del Fuego',
]

# Algunos nombres del gazetteer tambien son palabras comunes. Solo se acepta
# el barrio cuando el texto lo presenta como lugar; asi "robaron flores en
# Quilmes" no genera un falso punto en Flores, CABA.
BARRIOS_AMBIGUOS = {'Flores'}

# "San Martin de los Andes" no sigue el patron "de <provincia>" anterior,
# pero tampoco refiere al partido bonaerense. Se conserva como exclusion local
# al match para no descartar otra ubicacion valida que aparezca en la nota.
CONTINUACIONES_FUERA_GBA = [' de los andes']


def normalizar(texto):
    """Sin acentos y en minuscula, para que el matching de palabras clave no
    dependa de que la fuente haya escrito bien los tildes (pasa seguido en
    titulares)."""
    sin_acentos = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return sin_acentos.lower()


def es_candidata(titulo, descripcion):
    """True si matchea CUALQUIER categoria -- se usa para el prefiltro barato
    de slug (antes de bajar la nota completa), donde todavia no hace falta
    saber DE QUE categoria se trata, solo si vale la pena bajarla."""
    return categoria_de(titulo, descripcion) is not None


def categoria_de(titulo, descripcion):
    """Devuelve 'robo', 'choque', o None si no matchea ninguna categoria --
    ver CATEGORIAS_PALABRAS_CLAVE (el orden del dict es la prioridad cuando
    una nota menciona palabras de mas de una categoria)."""
    texto = normalizar(f"{titulo} {descripcion}")
    for categoria, palabras in CATEGORIAS_PALABRAS_CLAVE.items():
        if any(_contiene_termino(texto, palabra) for palabra in palabras):
            return categoria
    return None


def _contiene_termino(texto_norm, termino):
    """Busca una palabra o frase completa, sin confundir subcadenas.

    Por ejemplo, ``robo`` debe encontrar "robo" y "robo," pero no
    "aprobo". El mismo criterio se usa sobre slugs, que previamente se
    normalizan reemplazando sus guiones por espacios.
    """
    termino_norm = normalizar(termino)
    return re.search(rf'(?<!\w){re.escape(termino_norm)}(?!\w)', texto_norm) is not None


def _es_de_otra_provincia(texto_norm, zona, pos_match):
    """True si el match de `zona` en texto_norm (que termina en pos_match)
    esta seguido de cerca por " de <provincia>" -- ej. "san martin de
    tucuman". Ventana chica (40 caracteres) a proposito: la idea es
    detectar la frase pegada al nombre ("San Martín de Tucumán"), no
    cualquier mencion de la provincia en el resto del articulo (ver el
    comentario largo sobre PROVINCIAS_NO_GBA)."""
    resto = texto_norm[pos_match:pos_match + 40]
    return (
        any(resto.startswith(f" de {normalizar(p)}") for p in PROVINCIAS_NO_GBA)
        or any(resto.startswith(continuacion) for continuacion in CONTINUACIONES_FUERA_GBA)
    )


def _es_barrio_ambiguo_en_contexto(texto_norm, zona, inicio):
    """Exige una pista linguistica de lugar para barrios de nombre comun."""
    if zona not in BARRIOS_AMBIGUOS:
        return False
    fin = inicio + len(normalizar(zona))
    contexto = texto_norm[max(0, inicio - 14):min(len(texto_norm), fin + 14)]
    zona_norm = normalizar(zona)
    return not any(pista in contexto for pista in (
        f'en {zona_norm}', f'de {zona_norm}', f'barrio {zona_norm}',
        f'{zona_norm}, caba', f'{zona_norm} caba', f'{zona_norm} (caba',
    ))


def _oraciones(texto):
    """Divide en oraciones por punto seguido de espacio. Evita un bug real
    encontrado en un dry-run: _RE_CALLE permite un punto DENTRO de una
    palabra (para abreviaturas como "Av." o "Gral."), pero eso tambien deja
    que el patron de interseccion "lea de mas" y le pegue la primera
    palabra de la oracion siguiente a una calle real -- caso real visto:
    un bar llamado "Sol y Verde" en una nota, seguido de ". El dueño..."
    se leyo como si "Sol y Verde. El" fuera una sola interseccion. Buscar
    calles oracion por oracion (en vez de sobre el texto completo) corta
    ese cruce de raiz."""
    return re.split(r'(?<=[a-záéíóúñ0-9])\.\s+', texto)


def encontrar_zona(texto):
    """Primer partido o barrio válido del gazetteer, como
    (nombre, "CABA" o "Buenos Aires"), o None. Los partidos se revisan antes
    que los barrios para desambiguar calles homónimas. Se usa tanto como fallback de
    ubicacion (nivel 'barrio') como para acotar el geocode de una calle
    ambigua (nivel 'interseccion'/'calle') -- en el GBA hay calles "San
    Martín" en decenas de partidos distintos, sin esta pista Nominatim puede
    resolver cualquiera de ellas.

    Devuelve tambien la localidad correcta (CABA para un barrio, "Buenos
    Aires" para un partido) porque son cosas distintas -- San Isidro NO es
    CABA, es otro partido del GBA. Pegarle "CABA, Argentina" a una zona que
    en realidad es un partido geocodifica mal o no encuentra nada.

    Si el primer match de una zona ambigua (San Martín, y en general
    cualquiera de PARTIDOS_GBA/BARRIOS_CABA) viene pegado a "de <otra
    provincia>", se descarta ESE match puntual y se sigue buscando --
    nunca se descarta la nota entera por esto (ver el comentario largo
    sobre PROVINCIAS_NO_GBA, incluye el caso real de la regresion que
    este chequeo localizado vino a arreglar)."""
    texto_norm = normalizar(texto)

    # Si una nota nombra un partido y un barrio de CABA, el partido es una
    # referencia administrativa mas precisa para acotar una calle. Tambien
    # resuelve casos como "San Martin y Belgrano, Moron", donde Belgrano es
    # una calle y no el barrio porteno.
    for zona in PARTIDOS_GBA:
        zona_norm = normalizar(zona)
        for match in re.finditer(rf'(?<!\w){re.escape(zona_norm)}(?!\w)', texto_norm):
            pos = match.start()
            if not _es_de_otra_provincia(texto_norm, zona, pos + len(zona_norm)):
                return zona, 'Buenos Aires'
    for zona in BARRIOS_CABA:
        zona_norm = normalizar(zona)
        for match in re.finditer(rf'(?<!\w){re.escape(zona_norm)}(?!\w)', texto_norm):
            pos = match.start()
            if (
                not _es_de_otra_provincia(texto_norm, zona, pos + len(zona_norm))
                and not _es_barrio_ambiguo_en_contexto(texto_norm, zona, pos)
            ):
                return zona, 'CABA'
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

    # El chequeo de ambiguedad con otra provincia (San Martín de Tucumán,
    # etc.) vive DENTRO de encontrar_zona, localizado al match puntual --
    # ver ahi y el comentario largo sobre PROVINCIAS_NO_GBA.
    zona_encontrada = encontrar_zona(texto)
    # Sin pista de zona en el texto, se asume CABA como default (no GBA en
    # general) porque en la practica las notas con detalle de calle suelen
    # ser de la Ciudad -- un sesgo conocido, no una certeza, pero mejor eso
    # que geocodificar sin ninguna localidad y arriesgar un resultado fuera
    # de la region entera.
    zona, localidad = zona_encontrada if zona_encontrada else (None, 'CABA')
    sufijo_zona = f", {zona}" if zona else ""

    # Oracion por oracion (ver _oraciones) para que una calle real nunca se
    # pegue con la primera palabra de la oracion siguiente.
    for oracion in _oraciones(texto):
        m = RE_INTERSECCION.search(oracion)
        if m:
            return (f"{m.group(1)} y {m.group(2)}{sufijo_zona}, {localidad}, Argentina", 'interseccion', 80)

    for oracion in _oraciones(texto):
        m = RE_ALTURA.search(oracion)
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


def _es_sitemap_index(xml_bytes):
    """True si la raiz del XML es <sitemapindex> (apunta a otros sitemaps)
    en vez de <urlset> (apunta a notas). ET guarda el namespace pegado al
    tag (ej. '{http://www.sitemaps.org/schemas/sitemap/0.9}sitemapindex'),
    por eso el endswith en vez de comparar el tag entero."""
    raiz = ET.fromstring(xml_bytes)
    return raiz.tag.endswith('sitemapindex')


# Sub-sitemaps que casi seguro NO tienen notas de policiales -- visto en un
# dry-run real con Clarín: robots.txt declara sitemaps/index.xml, que no es
# un indice de UN nivel sino de DOS (index.xml -> un indice por TIPO de
# contenido -- index_recipes.xml, index_galleries.xml, presumiblemente uno
# de articulos tambien -- y cada uno de esos es a su vez un indice con ~45
# sitemaps hijos, uno por tanda). Con el presupuesto de recursion agotandose
# en tipos irrelevantes (recetas, galerias de fotos) antes de llegar al de
# articulos, el resultado terminaba siendo URLs de recetas/fotos que nunca
# iban a pasar el filtro de palabras clave. Estas palabras deprorizan (no
# descartan del todo, por si acaso) esos sub-sitemaps para que se prueben
# de ultimos, no de primeros.
#
# Correccion real (corrida de Rodo, 11/09, sobre Inforbano): un indice de
# WordPress/Yoast tipico no es una sola lista cronologica de notas -- mezcla
# post-sitemapN.xml (los articulos reales) con page-sitemap, tdb_templates-
# sitemap, category-sitemap, post_tag-sitemapN (uno por CADA tag/categoria/
# autor del sitio, no por fecha). Inforbano tiene 38 post-sitemap pero
# TERMINAN el listado del indice, y el orden inverso + el presupuesto de
# `intentos_restantes` (5 en el primer nivel) se gastaban entero en
# author-sitemap y post_tag-sitemap sin llegar nunca a un post-sitemap real:
# 858 URLs bajadas, 0 candidatas, porque ninguna era una nota. Se agregan
# estos tipos a la lista de deprorizados.
_SITEMAP_TIPOS_IRRELEVANTES = (
    'recipe', 'receta', 'galer', 'video', 'audio', 'podcast',
    'post_tag', 'category-sitemap', 'author-sitemap', 'page-sitemap', 'tdb_templates',
)


def extraer_urls_sitemap_recursivo(url_sitemap, headers, intentos_restantes=6):
    """Como extraer_urls_sitemap, pero baja niveles si el sitemap resulta
    ser un INDICE de sitemaps en vez de un listado de notas (puede haber
    mas de un nivel de indice, ver _SITEMAP_TIPOS_IRRELEVANTES). Sin esto,
    extraer_urls_sitemap devuelve las URLs de sitemap como si fueran notas,
    y ninguna pasa el prefiltro de slug (0 candidatas aunque el fetch
    "funcionó").

    Prueba los sitemaps hijos EN ORDEN INVERSO (el ultimo listado suele ser
    el mas reciente en los generadores mas comunes) salvo que el nombre
    sugiera un tipo de contenido irrelevante (esos se prueban al final) y
    ACUMULA los que resuelvan a un <urlset> real, hasta juntar
    MAX_URLS_POR_FUENTE URLs o agotar `intentos_restantes` -- un solo
    sitemap hijo puede traer pocas notas, asi que sumar mas de uno mejora
    las chances sin tener que bajarlos todos. `intentos_restantes` topea
    tanto la recursion (por si un indice apunta a otro indice, y a otro)
    como cuantos sitemaps se prueban en total, para no terminar bajando
    decenas de archivos en una sola corrida."""
    if intentos_restantes <= 0:
        return []
    try:
        # timeout mas alto que el resto del script (15s) -- un indice de
        # sitemaps grande (Inforbano: dio ReadTimeout real en una corrida
        # de Rodo el 11/09) puede tardar mas que una nota individual.
        resp = httpx.get(url_sitemap, headers=headers, timeout=25, follow_redirects=True)
        resp.raise_for_status()
    except Exception as err:
        print(f"    [sitemap] {url_sitemap} -> {type(err).__name__}: {err}")
        return []
    try:
        if _es_sitemap_index(resp.content):
            hijos = extraer_urls_sitemap(resp.content)
            print(f"    [sitemap] {url_sitemap} -> es un índice con {len(hijos)} sitemaps hijos, acumulando desde el más reciente")
            relevantes = [h for h in reversed(hijos) if not any(t in h.lower() for t in _SITEMAP_TIPOS_IRRELEVANTES)]
            deprorizados = [h for h in reversed(hijos) if any(t in h.lower() for t in _SITEMAP_TIPOS_IRRELEVANTES)]
            acumuladas = []
            restantes = intentos_restantes - 1
            for url_hijo in relevantes + deprorizados:
                if restantes <= 0 or len(acumuladas) >= MAX_URLS_POR_FUENTE:
                    break
                urls = extraer_urls_sitemap_recursivo(url_hijo, headers, restantes)
                restantes -= 1
                for u in urls:
                    if u not in acumuladas:
                        acumuladas.append(u)
            return acumuladas
        return extraer_urls_sitemap(resp.content)
    except ET.ParseError:
        print(f"    [sitemap] {url_sitemap} -> respondió pero no es XML válido")
        return []


def filtrar_por_segmento(urls, segmento):
    """Se queda solo con las URLs cuya ruta contiene /{segmento}/ -- para
    sitemaps que mezclan todas las secciones del sitio (Diario Popular,
    0221: ver FUENTES_SITEMAP_SECCIONADO) en vez de venir ya acotados a una
    categoria como el de Infobae. Barato y anterior al prefiltro de slug
    de siempre, asi no se le corre el filtro de palabra clave a notas de
    deportes o espectaculos que nunca van a matchear."""
    segmento_norm = f"/{segmento}/"
    return [u for u in urls if segmento_norm in u]


def extraer_urls_seccion(html_text, dominio, segmento):
    """Listado HTML de una sección (no XML) -- se buscan directamente los
    href que caen bajo ese segmento de ruta (ej. 'seguridad', 'policiales').

    El dominio en el href es OPCIONAL a proposito: probado contra la pagina
    real, La Nacion sirve estos links como ruta relativa (href="/seguridad/
    ...") en vez de URL absoluta -- exigir el dominio completo en el regex
    hacia que nunca matchee nada.

    No se exige un sufijo de CMS especifico (la v1 de esta funcion exigia
    "-nidNNNNNNN" al final, propio de La Nación) para que la misma funcion
    sirva tambien para Clarín/TN, cuyo formato de slug no se conoce de
    antemano (ver descubrir_urls_multiestrategia). En cambio se exige un
    slug "largo" (>= 12 caracteres) para no matchear links de navegacion
    cortos (paginación, "Inicio", etc.) que tambien caen bajo la sección."""
    patron = re.compile(rf'href="(?:{re.escape(dominio)})?(/{re.escape(segmento)}/[a-z0-9][a-z0-9\-]{{12,}}/?)"', re.IGNORECASE)
    vistos = []
    for path in patron.findall(html_text):
        url = dominio + path
        if url not in vistos:
            vistos.append(url)
    return vistos


def parsear_rss(xml_bytes):
    """RSS 2.0 sin namespace para los campos que importan (title/link/
    description). Reservado para fuentes de FUENTES_RSS, cuyo feed ya viene
    acotado a una sección razonable -- no para portada general (ver la nota
    larga al principio del archivo sobre Infobae/La Nación v1)."""
    raiz = ET.fromstring(xml_bytes)
    items = []
    for item in raiz.findall('./channel/item'):
        titulo = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        descripcion = re.sub(r'<[^>]+>', ' ', item.findtext('description') or '').strip()
        if titulo and link:
            items.append({'titulo': titulo, 'link': link, 'descripcion': html.unescape(descripcion)})
    return items


def descubrir_sitemaps_desde_robots(dominio):
    """Lee robots.txt y devuelve las URLs listadas en lineas "Sitemap:" --
    forma estandar (sirve para cualquier CMS, no solo Arc Publishing) de
    encontrar el sitemap de un sitio sin adivinar la ruta a ciegas."""
    try:
        resp = httpx.get(f"{dominio}/robots.txt", headers=HEADERS_NAVEGADOR, timeout=10)
        resp.raise_for_status()
    except Exception:
        return []
    return [
        linea.split(':', 1)[1].strip()
        for linea in resp.text.splitlines()
        if linea.lower().startswith('sitemap:')
    ]


def descubrir_urls_multiestrategia(nombre_fuente, dominio, rutas_seccion):
    """Para fuentes que devolvieron bloqueo con el acceso "normal" (Clarín,
    TN -- ver HEADERS_NAVEGADOR): en vez de apostar a un solo metodo, se
    prueban varios en cascada. Se detiene en el primero que devuelva al
    menos una URL de nota, e imprime cual funciono para que quede
    documentado que metodo hizo falta -- asi la próxima vez no hay que
    volver a adivinar.

    Orden de intentos:
      1. Sitemap(s) declarados en robots.txt (estandar, cualquier CMS) --
         si alguno resulta ser un INDICE de sitemaps en vez de notas
         directas, se baja un nivel mas solo, hasta encontrar uno con
         notas (ver extraer_urls_sitemap_recursivo; caso real: Clarín).
      2. Sitemap "adivinado" en la raiz del dominio (/sitemap.xml) --
         convencion muy comun que no siempre se declara en robots.txt.
      3. Sitemap estilo Arc Publishing (.../arc/outboundfeeds/sitemap2/
         category/policiales/), por si tambien corren sobre Arc como
         Infobae/La Nación.
      4. Scrapear directamente el HTML de la(s) ruta(s) de sección dadas.

    Si ninguno funciona, devuelve [] y lo dice explicitamente: no es un bug
    del script, es que la fuente sigue bloqueada -- no tiene sentido
    reintentar en cada corrida algo que ya se sabe que no entra."""
    intentos_sitemap = [('sitemap (robots.txt)', sm) for sm in descubrir_sitemaps_desde_robots(dominio)]
    intentos_sitemap.append(('sitemap adivinado', f"{dominio}/sitemap.xml"))
    intentos_sitemap.append(('sitemap Arc Publishing', f"{dominio}/arc/outboundfeeds/sitemap2/category/policiales/"))

    for metodo, url in intentos_sitemap:
        urls = extraer_urls_sitemap_recursivo(url, HEADERS_NAVEGADOR)
        if urls:
            print(f"  Funcionó: {metodo} ({url}) -- {len(urls)} URLs")
            return urls
        print(f"  [{metodo}] {url} -> sin notas reconocibles")

    for ruta in rutas_seccion:
        try:
            resp = httpx.get(ruta, headers=HEADERS_NAVEGADOR, timeout=15, follow_redirects=True)
            resp.raise_for_status()
        except Exception as err:
            print(f"  [scrape de sección] {ruta} -> {type(err).__name__}: {err}")
            continue
        segmento = ruta.rstrip('/').rsplit('/', 1)[-1]
        urls = extraer_urls_seccion(resp.text, dominio, segmento)
        if urls:
            print(f"  Funcionó: scrape de sección ({ruta}) -- {len(urls)} URLs")
            return urls
        print(f"  [scrape de sección] {ruta} -> respondió pero 0 notas reconocibles")

    print(f"  Ningún método funcionó para {nombre_fuente} -- sigue bloqueada, no se agrega nada esta corrida")
    return []


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
    titulo = re.sub(
        r'\s*[-|]\s*(Infobae|LA NACION|La Nación|Clarín|TN|Página ?12|Diario Popular|0221'
        r'|El Día|El Diario Sur|Inforbano|Infosur Diario|Minutouno(?:\.com)?)\.?\s*$',
        '', titulo, flags=re.IGNORECASE,
    ).strip()

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
            tipo_incidente VARCHAR(20) NOT NULL DEFAULT 'robo',
            publicado_en TIMESTAMPTZ,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    # ALTER para bases que ya tenian la tabla creada antes de v5 (sin esta
    # columna) -- CREATE TABLE IF NOT EXISTS no la agrega si la tabla ya
    # existe. Mismo patron que usa main.py (_asegurar_tabla_prensa) del lado
    # del backend, para que correr cualquiera de los dos primero deje la
    # tabla en el mismo estado.
    cur.execute("ALTER TABLE reportes_prensa ADD COLUMN IF NOT EXISTS tipo_incidente VARCHAR(20) NOT NULL DEFAULT 'robo'")


def _evaluar_y_guardar(titulo, descripcion, url, nombre_fuente, guardar, cur, contadores):
    """Cola comun del pipeline a partir de titulo+descripcion ya conocidos,
    vengan de un RSS directo (ya los trae) o de bajar y parsear una nota
    individual (ver _procesar_url): categoria_de -> ubicacion -> geocode ->
    guardar. Devuelve nada, solo imprime y actualiza contadores (dict
    mutable, para no volver todo global ni devolver una tupla de numeros de
    cada llamada) -- contadores['candidatas_por_tipo'] es un dict aparte con
    el desglose por categoria, para que la salida final diga cuanto de cada
    tipo se encontro, no solo un total mezclado."""
    if not titulo:
        return
    categoria = categoria_de(titulo, descripcion)
    if categoria is None:
        return
    contadores['candidatas'] += 1
    contadores['candidatas_por_tipo'][categoria] = contadores['candidatas_por_tipo'].get(categoria, 0) + 1

    ubicacion = extraer_ubicacion(titulo, descripcion)
    if ubicacion is None:
        print(f"  [sin ubicar] ({categoria}) {titulo}")
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
    print(f"  [{categoria}, {nivel}, r={radio}m] ({lat:.5f}, {lng:.5f}) -- {titulo}")

    if guardar:
        cur.execute("""
            INSERT INTO reportes_prensa (lat, lng, nivel_precision, radio_metros, titular, url_fuente, fuente, tipo_incidente, publicado_en)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (url_fuente) DO NOTHING
        """, (lat, lng, nivel, radio, titulo, url, nombre_fuente, categoria, None))
        if cur.rowcount > 0:
            contadores['guardadas'] += 1


def _procesar_url(url, nombre_fuente, guardar, cur, contadores, headers=None):
    """Para fuentes sin titulo/descripcion de entrada (sitemap, listado de
    sección, multi-estrategia): bajar la nota completa, sacarlos, y delegar
    en _evaluar_y_guardar. `headers` permite pasar HEADERS_NAVEGADOR para
    las fuentes que bloquean el USER_AGENT identificado (Clarín/TN)."""
    headers = headers or {"User-Agent": USER_AGENT}
    try:
        resp = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        titulo, descripcion = extraer_titulo_descripcion(resp.text)
    except Exception as err:
        print(f"  [error al bajar la nota: {err}] {url}")
        return
    finally:
        time.sleep(PAUSA_ENTRE_FETCHES_SEG)
    _evaluar_y_guardar(titulo, descripcion, url, nombre_fuente, guardar, cur, contadores)


def main():
    guardar = '--guardar' in sys.argv
    conn = cur = None
    if guardar:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        _asegurar_tabla(cur)

    contadores = {'candidatas': 0, 'ubicadas': 0, 'guardadas': 0, 'candidatas_por_tipo': {}}

    for nombre_fuente, url_sitemap in FUENTES_SITEMAP:
        print(f"\n=== {nombre_fuente} (sitemap: {url_sitemap}) ===")
        # extraer_urls_sitemap_recursivo, ver la misma nota en el loop de
        # FUENTES_SITEMAP_SECCIONADO mas abajo ("Correcciones v6.1").
        urls = extraer_urls_sitemap_recursivo(url_sitemap, {"User-Agent": USER_AGENT})
        if not urls:
            print("  ERROR al bajar/parsear el sitemap (0 URLs -- ver el detalle de intentos arriba si los hubo)")
            continue
        print(f"  {len(urls)} URLs en el sitemap")

        candidatas_slug = [u for u in urls if es_candidata(slug_a_texto(u), '')][:MAX_URLS_POR_FUENTE]
        print(f"  {len(candidatas_slug)} pasan el prefiltro de slug (se bajan completas)")
        for url in candidatas_slug:
            _procesar_url(url, nombre_fuente, guardar, cur, contadores)

    for nombre_fuente, url_seccion, dominio, segmento in FUENTES_SECCION:
        print(f"\n=== {nombre_fuente} (sección: {url_seccion}) ===")
        try:
            resp = httpx.get(url_seccion, headers={"User-Agent": USER_AGENT}, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            urls = extraer_urls_seccion(resp.text, dominio, segmento)
        except Exception as err:
            print(f"  ERROR al bajar/parsear la sección: {err}")
            continue
        print(f"  {len(urls)} notas en el listado")

        candidatas_slug = [u for u in urls if es_candidata(slug_a_texto(u), '')][:MAX_URLS_POR_FUENTE]
        print(f"  {len(candidatas_slug)} pasan el prefiltro de slug (se bajan completas)")
        for url in candidatas_slug:
            _procesar_url(url, nombre_fuente, guardar, cur, contadores)

    for fuente_rss in FUENTES_RSS:
        # Tupla de 2 (nombre, url) o de 3 (nombre, url, "navegador") -- ver
        # la nota "Correcciones v6.1" sobre Infocielo, que necesita
        # HEADERS_NAVEGADOR en vez del USER_AGENT identificado de siempre.
        nombre_fuente, url_rss = fuente_rss[0], fuente_rss[1]
        headers_rss = HEADERS_NAVEGADOR if len(fuente_rss) > 2 and fuente_rss[2] == "navegador" else {"User-Agent": USER_AGENT}
        print(f"\n=== {nombre_fuente} (RSS: {url_rss}) ===")
        try:
            resp = httpx.get(url_rss, headers=headers_rss, timeout=15, follow_redirects=True)
            resp.raise_for_status()
            items = parsear_rss(resp.content)
        except Exception as err:
            print(f"  ERROR al bajar/parsear el RSS: {err}")
            continue
        print(f"  {len(items)} items en el feed")
        for item in items:
            _evaluar_y_guardar(item['titulo'], item['descripcion'], item['link'], nombre_fuente, guardar, cur, contadores)

    for nombre_fuente, url_sitemap, segmento in FUENTES_SITEMAP_SECCIONADO:
        print(f"\n=== {nombre_fuente} (sitemap seccionado: {url_sitemap}) ===")
        # extraer_urls_sitemap_recursivo (no la version plana) -- ver
        # "Correcciones v6.1": Inforbano/Infosur apuntaban a un sitemap
        # INDICE y la version plana trataba nombres de archivo de sitemaps
        # hijos como si fueran notas. Con la version recursiva, una fuente
        # que ya viene como urlset directo (Diario Popular, 0221, El Dia,
        # Minutouno) no cambia de comportamiento -- devuelve lo mismo en el
        # primer nivel.
        urls = extraer_urls_sitemap_recursivo(url_sitemap, {"User-Agent": USER_AGENT})
        if not urls:
            print("  ERROR al bajar/parsear el sitemap (0 URLs -- ver el detalle de intentos arriba si los hubo)")
            continue
        print(f"  {len(urls)} URLs en el sitemap")
        urls_seccion = filtrar_por_segmento(urls, segmento)
        print(f"  {len(urls_seccion)} caen en /{segmento}/")

        candidatas_slug = [u for u in urls_seccion if es_candidata(slug_a_texto(u), '')][:MAX_URLS_POR_FUENTE]
        print(f"  {len(candidatas_slug)} pasan el prefiltro de slug (se bajan completas)")
        for url in candidatas_slug:
            _procesar_url(url, nombre_fuente, guardar, cur, contadores)

    for nombre_fuente, dominio, rutas_seccion in FUENTES_MULTIESTRATEGIA:
        print(f"\n=== {nombre_fuente} (multi-estrategia) ===")
        urls = descubrir_urls_multiestrategia(nombre_fuente, dominio, rutas_seccion)
        if not urls:
            continue
        candidatas_slug = [u for u in urls if es_candidata(slug_a_texto(u), '')][:MAX_URLS_POR_FUENTE]
        print(f"  {len(candidatas_slug)} pasan el prefiltro de slug (se bajan completas)")
        for url in candidatas_slug:
            _procesar_url(url, nombre_fuente, guardar, cur, contadores, headers=HEADERS_NAVEGADOR)

    if guardar:
        conn.commit()
        cur.close()
        conn.close()

    desglose = ", ".join(f"{cant} {tipo}" for tipo, cant in sorted(contadores['candidatas_por_tipo'].items()))
    print(f"\n{contadores['candidatas']} noticias candidatas ({desglose}), {contadores['ubicadas']} pudieron ubicarse"
          + (f", {contadores['guardadas']} nuevas guardadas en la base" if guardar
             else " (dry-run, no se guardo nada -- corré con --guardar para insertar)"))


if __name__ == "__main__":
    main()
