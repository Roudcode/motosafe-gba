import pytest
from scrapear_noticias_robos import categoria_de, encontrar_localidad, extraer_fecha_publicacion, extraer_ubicacion, encontrar_zona, firma_titular, parsear_rss, relacionado_con_moto, zona_de_ubicacion


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


# --- A09: validación de zona del geocode (SES-069) ---------------------------
# Direcciones reales devueltas por Nominatim el 2026-10-06, ver
# docs/evidencias/2026-10-06/A09-geocodificacion/.
import scrapear_noticias_robos as scraper  # noqa: E402

CALLE_ECHEVERRIA_EN_MUNRO = {'road': 'Esteban Echeverría', 'suburb': 'Munro', 'state_district': 'Partido de Vicente López', 'state': 'Buenos Aires'}
PARTIDO_ECHEVERRIA = {'state_district': 'Partido de Esteban Echeverría', 'state': 'Buenos Aires'}
LOCALIDAD_MALVINAS_EN_BROWN = {'village': 'Malvinas Argentinas', 'town': 'Partido de Almirante Brown', 'state': 'Buenos Aires'}
PARTIDO_MALVINAS = {'state_district': 'Partido de Malvinas Argentinas', 'state': 'Buenos Aires'}
ESTACION_BELGRANO_EN_MONSERRAT = {'railway': 'Belgrano', 'suburb': 'Monserrat', 'city': 'Buenos Aires', 'state': 'Ciudad Autónoma de Buenos Aires'}
BARRIO_BELGRANO = {'suburb': 'Belgrano', 'city': 'Buenos Aires', 'state_district': 'Comuna 13', 'state': 'Ciudad Autónoma de Buenos Aires'}


def _nominatim_falso(monkeypatch, respuestas):
    """respuestas: lista de address dicts (o None) en el orden de las consultas."""
    pedidos = []

    def buscar(query, **extra):
        pedidos.append((query, extra))
        direccion = respuestas[len(pedidos) - 1]
        return None if direccion is None else {'lat': '-34.8', 'lon': '-58.4', 'address': direccion}

    monkeypatch.setattr(scraper, '_buscar_nominatim', buscar)
    return pedidos


def test_resultado_en_zona_rechaza_homonimos_de_otro_partido():
    assert not scraper.resultado_en_zona(CALLE_ECHEVERRIA_EN_MUNRO, 'Esteban Echeverría', 'Buenos Aires', True)
    assert scraper.resultado_en_zona(PARTIDO_ECHEVERRIA, 'Esteban Echeverría', 'Buenos Aires', True)
    assert not scraper.resultado_en_zona(LOCALIDAD_MALVINAS_EN_BROWN, 'Malvinas Argentinas', 'Buenos Aires', True)
    assert scraper.resultado_en_zona(PARTIDO_MALVINAS, 'Malvinas Argentinas', 'Buenos Aires', True)


def test_resultado_en_zona_acepta_variantes_reales_de_osm():
    # "General San Martín", "Partido del Pilar" y Quilmes solo con city.
    assert scraper.resultado_en_zona({'state_district': 'Partido de General San Martín'}, 'San Martín', 'Buenos Aires', True)
    assert scraper.resultado_en_zona({'town': 'Pilar', 'state_district': 'Partido del Pilar'}, 'Pilar', 'Buenos Aires', True)
    assert scraper.resultado_en_zona({'city': 'Quilmes', 'state': 'Buenos Aires'}, 'Quilmes', 'Buenos Aires', True)
    assert scraper.resultado_en_zona({'state_district': 'Partido de La Plata'}, 'City Bell', 'Buenos Aires', True)


def test_barrio_de_caba_exige_el_barrio_solo_en_nivel_barrio():
    assert not scraper.resultado_en_zona(ESTACION_BELGRANO_EN_MONSERRAT, 'Belgrano', 'CABA', True)
    assert scraper.resultado_en_zona(BARRIO_BELGRANO, 'Belgrano', 'CABA', True)
    # Una calle cerca del límite puede venir con el barrio vecino: alcanza con CABA.
    assert scraper.resultado_en_zona(ESTACION_BELGRANO_EN_MONSERRAT, 'Belgrano', 'CABA', False)
    assert not scraper.resultado_en_zona(PARTIDO_ECHEVERRIA, None, 'CABA', False)


def test_monte_grande_ya_no_cae_en_munro(monkeypatch):
    # Caso real de SES-067: "Monte Grande: un detenido por el robo de un auto".
    query, nivel, _ = extraer_ubicacion('Monte Grande: un detenido por el robo de un auto', '')
    pedidos = _nominatim_falso(monkeypatch, [CALLE_ECHEVERRIA_EN_MUNRO, PARTIDO_ECHEVERRIA])
    assert scraper.geocodificar_en_zona(query, nivel, 'Esteban Echeverría', 'Buenos Aires') == ((-34.8, -58.4), 'ok')
    assert pedidos[0][1] == {'featureType': 'settlement'}
    assert pedidos[1][0] == 'Partido de Esteban Echeverría, Buenos Aires, Argentina'


def test_sin_resultado_dentro_de_la_zona_la_nota_no_se_ubica(monkeypatch):
    _nominatim_falso(monkeypatch, [LOCALIDAD_MALVINAS_EN_BROWN, CALLE_ECHEVERRIA_EN_MUNRO])
    assert scraper.geocodificar_en_zona('Malvinas Argentinas, Buenos Aires, Argentina', 'barrio',
                                        'Malvinas Argentinas', 'Buenos Aires') == (None, 'fuera_de_zona')


def test_calle_en_otro_partido_se_descarta(monkeypatch):
    pedidos = _nominatim_falso(monkeypatch, [CALLE_ECHEVERRIA_EN_MUNRO])
    assert scraper.geocodificar_en_zona('Rivadavia 100, Quilmes, Buenos Aires, Argentina', 'calle',
                                        'Quilmes', 'Buenos Aires') == (None, 'fuera_de_zona')
    assert len(pedidos) == 1 and pedidos[0][1] == {}


def test_sin_respuesta_de_nominatim_se_informa_como_vacio(monkeypatch):
    _nominatim_falso(monkeypatch, [None])
    assert scraper.geocodificar_en_zona('Caseros y Salta, Constitución, CABA, Argentina', 'interseccion',
                                        'Constitución', 'CABA') == (None, 'vacio')


def test_partido_que_solo_figura_en_display_name():
    # Caso real de la corrida de prueba de SES-069: "Almirante Brown 500".
    direccion = {'house_number': '500', 'road': 'Almirante Brown', 'town': 'Burzaco', 'state': 'Buenos Aires'}
    nombre = '500, Almirante Brown, Burzaco, Partido de Almirante Brown, Buenos Aires, B1852, Argentina'
    assert scraper.resultado_en_zona(direccion, 'Almirante Brown', 'Buenos Aires', False, nombre)
    assert not scraper.resultado_en_zona(direccion, 'Almirante Brown', 'Buenos Aires', False)


def test_nombre_de_partido_o_barrio_seguido_de_altura_es_una_calle():
    # Caso real de SES-069: la nota era de Grand Bourg (Malvinas Argentinas).
    texto = 'Detuvieron en Grand Bourg a Coco. El allanamiento fue en Almirante Brown al 500'
    assert encontrar_zona(texto) == ('Malvinas Argentinas', 'Buenos Aires')
    assert encontrar_zona('Robo en Belgrano al 1500, Quilmes') == ('Quilmes', 'Buenos Aires')
    assert encontrar_zona('Asalto en Belgrano al 1500') is None
    # Sin altura sigue siendo la zona.
    assert encontrar_zona('Detuvieron a un ladrón en Almirante Brown') == ('Almirante Brown', 'Buenos Aires')


def test_nota_ya_guardada_cuenta_como_ya_en_base_y_no_como_nueva(monkeypatch):
    """SES-082: ON CONFLICT (url_fuente) DO NOTHING deja rowcount en 0. Antes la
    nota se perdía en el conteo; ahora cuenta como 'ya en la base'."""
    from unittest.mock import MagicMock
    import scrapear_noticias_robos as scraper

    cur = MagicMock()
    cur.rowcount = 0  # el INSERT no insertó: la URL ya estaba
    contadores = {
        'candidatas': 0, 'candidatas_moto': 0, 'ubicadas': 0, 'guardadas': 0, 'ya_en_base': 0,
        'duplicadas': 0, 'fuera_de_zona': 0, 'firmas_vistas': set(), 'candidatas_por_tipo': {},
        'candidatas_por_fuente': {}, 'ubicadas_por_fuente': {}, 'guardadas_por_fuente': {},
    }
    monkeypatch.setattr(scraper, 'extraer_ubicacion', lambda t, d: ('Quilmes, Buenos Aires, Argentina', 'barrio', 800))
    monkeypatch.setattr(scraper, 'encontrar_zona', lambda t: ('Quilmes', 'Buenos Aires'))
    monkeypatch.setattr(scraper, 'geocodificar_en_zona', lambda *a: ((-34.72, -58.26), 'ok'))

    scraper._evaluar_y_guardar('Robaron a un jubilado en Quilmes', '', 'https://ejemplo.test/1', 'Fuente X', True, cur, contadores, None)

    assert contadores['ya_en_base'] == 1
    assert contadores['guardadas'] == 0


def test_localidad_del_gba_se_ubica_por_su_nombre_dentro_del_partido(monkeypatch):
    # Caso real del dry-run 2026-10-06: notas de Punta Lara (Ensenada) y de
    # Nordelta (Tigre) quedaban sin ubicar. Se geocodifican por la localidad.
    query, nivel, radio = extraer_ubicacion('Murió un bebé de 10 días en un choque en Punta Lara', '')
    assert (query, nivel, radio) == ('Punta Lara, Ensenada, Buenos Aires, Argentina', 'barrio', 800)
    pedidos = _nominatim_falso(monkeypatch, [PARTIDO_ECHEVERRIA])
    assert scraper.geocodificar_en_zona(query, nivel, 'Ensenada', 'Buenos Aires') == (None, 'fuera_de_zona')
    assert len(pedidos) == 1 and pedidos[0][1] == {'featureType': 'settlement'}


def test_localidad_sin_resultado_no_cae_al_centro_del_partido(monkeypatch):
    query, nivel, _ = extraer_ubicacion('Ataque de perros en Nordelta', '')
    pedidos = _nominatim_falso(monkeypatch, [None, PARTIDO_ECHEVERRIA])
    assert scraper.geocodificar_en_zona(query, nivel, 'Tigre', 'Buenos Aires') == (None, 'vacio')
    assert len(pedidos) == 1


def test_localidad_solo_si_no_hay_partido_ni_barrio_y_no_como_calle():
    # Una avenida Canning en CABA no es la localidad de Ezeiza.
    assert encontrar_localidad('Robo en Av. Canning al 500') is None
    assert encontrar_localidad('Robo en Canning, Ezeiza') == ('Canning', 'Ezeiza')
    # Si hay barrio de CABA en el texto, manda la zona que ya se resolvia antes.
    assert zona_de_ubicacion('Robo en Av. Canning, en Palermo') == ('Palermo', 'CABA')
    assert zona_de_ubicacion('Un hecho sin zona') == (None, 'CABA')


class _RespuestaFalsa:
    def __init__(self, status, datos=None):
        self.status_code = status
        self._datos = datos or []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)

    def json(self):
        return self._datos


def _nominatim_con_red_falsa(monkeypatch, respuestas):
    monkeypatch.setattr(scraper, '_cache_nominatim', {})
    monkeypatch.setattr(scraper, '_nominatim_bloqueado', False)
    monkeypatch.setattr(scraper.time, 'sleep', lambda s: None)
    pedidos = []

    def get(url, params, headers, timeout):
        pedidos.append(params['q'])
        return respuestas.pop(0)

    monkeypatch.setattr(scraper.httpx, 'get', get)
    return pedidos


def test_consulta_repetida_en_la_corrida_no_vuelve_a_pedir(monkeypatch):
    pedidos = _nominatim_con_red_falsa(monkeypatch, [_RespuestaFalsa(200, [PARTIDO_ECHEVERRIA])])
    scraper._buscar_nominatim('Quilmes, Buenos Aires, Argentina')
    scraper._buscar_nominatim('Quilmes, Buenos Aires, Argentina')
    assert len(pedidos) == 1


def test_un_429_corta_los_pedidos_del_resto_de_la_corrida(monkeypatch):
    pedidos = _nominatim_con_red_falsa(monkeypatch, [_RespuestaFalsa(429)])
    with pytest.raises(scraper.NominatimBloqueado):
        scraper._buscar_nominatim('Punta Lara, Ensenada, Buenos Aires, Argentina')
    with pytest.raises(scraper.NominatimBloqueado):
        scraper._buscar_nominatim('Nordelta, Tigre, Buenos Aires, Argentina')
    assert len(pedidos) == 1
