from scrapear_noticias_robos import categoria_de, extraer_ubicacion, encontrar_zona, relacionado_con_moto


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
