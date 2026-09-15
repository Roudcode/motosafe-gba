from scrapear_noticias_robos import categoria_de, extraer_fecha_publicacion, extraer_ubicacion, encontrar_zona, firma_titular, parsear_rss, relacionado_con_moto


def test_categoria_no_confunde_subcadena_de_robo():
    assert categoria_de('El Concejo aprobo una ordenanza', '') is None
    assert categoria_de('Investigan un robo en Quilmes', '') == 'robo'


def test_excluye_san_martin_de_los_andes():
    assert encontrar_zona('Un hecho ocurrido en San Martin de los Andes') is None


def test_no_confunde_flores_con_el_barrio_y_prioriza_partido():
    assert encontrar_zona('Robaron flores en una casa de Quilmes') == ('Quilmes', 'Buenos Aires')


def test_interseccion_con_partido_no_caen_en_barrio_homonimo():
    ubicacion = extraer_ubicacion('Choque en San Martin y Belgrano, Moron', '')
    assert ubicacion == ('San Martin y Belgrano, Morón, Buenos Aires, Argentina', 'interseccion', 80)


def test_clasifica_inseguridad_y_moto_como_atributos_independientes():
    assert categoria_de('Balearon a un motociclista en Quilmes', '') == 'inseguridad'
    assert relacionado_con_moto('Motociclista herido en Quilmes', '') is True
    assert relacionado_con_moto('La moto de agua fue secuestrada', '') is False
    assert relacionado_con_moto('Un auto chocó en Quilmes', '') is False


def test_rss_conserva_fecha_de_publicacion():
    rss = b'''<?xml version="1.0"?><rss><channel><item>
        <title>Robo en Quilmes</title><link>https://ejemplo.test/nota</link>
        <description>Una noticia</description><pubDate>Sun, 13 Sep 2026 15:30:00 -0300</pubDate>
    </item></channel></rss>'''
    item = parsear_rss(rss)[0]
    assert item['publicado_en'].isoformat() == '2026-09-13T15:30:00-03:00'


def test_firma_conserva_titulo_editorial_de_fuente_directa():
    assert firma_titular('Robo de una moto en Quilmes - Diario Local', 'Diario Local') == 'robo de una moto en quilmes - diario local'


def test_html_conserva_fecha_editorial_y_no_inventa_una():
    assert extraer_fecha_publicacion('<meta property="article:published_time" content="2026-09-13T18:00:00-03:00">').isoformat() == '2026-09-13T18:00:00-03:00'
    assert extraer_fecha_publicacion('<html><title>Sin fecha</title></html>') is None


def test_reconoce_alias_de_localidad_no_oficial():
    # Confirmado con una corrida real evaluada a mano (A09, 2026-09-15): estos
    # nombres de uso cotidiano en la prensa no estan en PARTIDOS_GBA/BARRIOS_CABA
    # (que solo tienen el nombre oficial del partido) y antes de este alias
    # quedaban "[sin ubicar]" pese a ser un partido GBA inambiguo.
    assert encontrar_zona('Asaltaron a un joven para robarle la moto en Lomas') == ('Lomas de Zamora', 'Buenos Aires')
    assert encontrar_zona('Un hecho ocurrido en Monte Grande') == ('Esteban Echeverría', 'Buenos Aires')
    assert encontrar_zona('Un robo en Los Hornos') == ('La Plata', 'Buenos Aires')
    assert encontrar_zona('Un robo en Tolosa') == ('La Plata', 'Buenos Aires')
    assert encontrar_zona('Un tiroteo en Virrey del Pino') == ('La Matanza', 'Buenos Aires')


def test_alias_de_localidad_no_rompe_la_exclusion_de_otra_provincia():
    # Mismo chequeo que test_excluye_san_martin_de_los_andes pero para un
    # alias: si el alias aparece pegado a "de <otra provincia>", no debe
    # devolver el partido GBA de todas formas.
    assert encontrar_zona('Un hecho en Lomas de Mendoza') is None
