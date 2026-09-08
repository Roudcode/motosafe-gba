"""
Tests basicos del backend. Corren con pytest desde backend/:
    cd backend && pytest

No requieren la base de datos levantada: el endpoint /hotspots se prueba
mockeando psycopg2.connect, asi el test es rapido y no depende de Docker
estando corriendo. /predecir si usa el modelo real (modelo_final.pkl),
porque eso es justamente lo que queremos verificar.
"""
import json
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

import main

client = TestClient(main.app)


def test_raiz_responde_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert "mensaje" in r.json()


def test_predecir_devuelve_prediccion_valida():
    payload = {
        "hora": 20,
        "dia_semana": "Friday",
        "comuna": "1",
        "tipo_de_via": "AVENIDA",
        "contraparte": "AUTO",
        "edad_victima": 30,
        "sexo_victima": "M",
    }
    r = client.post("/predecir", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["prediccion"] in ("LEVE", "GRAVE", "MORTAL")
    assert set(data["probabilidades"].keys()) == {"LEVE", "GRAVE", "MORTAL"}
    # Las probabilidades tienen que sumar ~1 y ser todas >= 0
    assert abs(sum(data["probabilidades"].values()) - 1.0) < 0.01
    assert all(p >= 0 for p in data["probabilidades"].values())


def test_predecir_no_rompe_con_categoria_nunca_vista_en_entrenamiento():
    """
    El modelo se entrena con pd.get_dummies + reindex(fill_value=0): una categoria
    que el modelo nunca vio (comuna/via/contraparte inventadas) no debe tirar un
    error 500, tiene que devolver una prediccion igual (con esa columna en cero).
    Este test documenta ese comportamiento a proposito: no es un bug, pero hay que
    saber que pasa silenciosamente sin ningun aviso de "categoria desconocida".
    """
    payload = {
        "hora": 3,
        "dia_semana": "Blursday",
        "comuna": "ZONA-INEXISTENTE-999",
        "tipo_de_via": "VIA-INVENTADA",
        "contraparte": "OVNI",
        "edad_victima": 30,
        "sexo_victima": "M",
    }
    r = client.post("/predecir", json=payload)
    assert r.status_code == 200
    assert r.json()["prediccion"] in ("LEVE", "GRAVE", "MORTAL")


def _mock_db(filas):
    """Arma un mock de psycopg2.connect() que devuelve `filas` en fetchall()."""
    cursor = MagicMock()
    cursor.fetchall.return_value = filas
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    return conexion


def test_hotspots_con_contexto_propio_usa_el_modelo():
    """Cluster 0 SI tiene fila en hotspots_contexto.csv: contexto_estimado debe ser False."""
    fila_db = {
        "id": 1, "cluster": 0, "latitud": -34.6, "longitud": -58.4,
        "cantidad_siniestros": 50, "mortales": 1, "graves": 3, "nivel_riesgo": "bajo",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])):
        r = client.get("/hotspots")
    assert r.status_code == 200
    hotspot = r.json()[0]
    assert hotspot["nivel_riesgo"] in ("bajo", "medio", "alto", "critico")
    assert hotspot["contexto_estimado"] is False
    assert "prediccion_modelo" in hotspot


def test_hotspots_sin_contexto_propio_usa_perfil_generico_pero_no_rompe():
    """
    Cluster inexistente en hotspots_contexto.csv (99999): antes del fix, este caso se
    quedaba con el nivel_riesgo heuristico que traia la fila de la base, distinto del
    que calcula el modelo para el resto. Ahora tiene que pasar por el modelo igual,
    usando el contexto generico de la ciudad, y marcarse como contexto_estimado=True.
    """
    fila_db = {
        "id": 2, "cluster": 99999, "latitud": -34.6, "longitud": -58.4,
        "cantidad_siniestros": 10, "mortales": 0, "graves": 0, "nivel_riesgo": "bajo",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])):
        r = client.get("/hotspots")
    assert r.status_code == 200
    hotspot = r.json()[0]
    assert hotspot["nivel_riesgo"] in ("bajo", "medio", "alto", "critico")
    assert hotspot["contexto_estimado"] is True
    assert "prediccion_modelo" in hotspot


def test_niveles_relativos_desde_matriz_clasifica_contra_cortes_fijos():
    """
    niveles_relativos_desde_matriz ya no recalcula percentiles sobre el lote de
    cada pedido (eso hacia que 'alto' significara cosas distintas segun la hora
    de la consulta, ver el comentario largo de la funcion en main.py) -- ahora
    compara la probabilidad de cada fila contra cortes fijos (UMBRALES_HOTSPOTS /
    UMBRALES_CORREDORES, calibrados offline). Este test verifica la logica de
    clasificacion en si, con cortes explicitos y scores elegidos a proposito
    justo en cada borde, independiente de cualquier lote real.
    """
    import numpy as np
    clases = ["GRAVE", "LEVE", "MORTAL"]
    cortes = {"p25": 0.4, "p75": 0.8, "p95": 1.2}

    def matriz_para_score(score):
        # score = 2*p_mortal + p_grave; con p_grave=0 y p_leve=1-p_mortal, alcanza
        # con variar p_mortal = score/2 para obtener el score deseado exacto.
        p_mortal = score / 2
        return np.array([[0.0, 1.0 - p_mortal, p_mortal]])

    casos = [
        (0.1, "bajo"),      # bien por debajo de p25
        (0.4, "medio"),     # exactamente en p25 -> ya no es bajo
        (0.7, "medio"),     # entre p25 y p75
        (0.8, "alto"),      # exactamente en p75 -> ya no es medio
        (1.0, "alto"),      # entre p75 y p95
        (1.2, "critico"),   # exactamente en p95 -> ya no es alto
        (1.6, "critico"),   # bien por encima de p95
    ]
    for score, esperado in casos:
        [nivel] = main.niveles_relativos_desde_matriz(matriz_para_score(score), clases, cortes)
        assert nivel == esperado, f"score={score} dio {nivel}, esperaba {esperado}"


def test_hotspots_diferencia_niveles_entre_si_no_todos_iguales():
    """
    Mismo sintoma que ya se documenta en /corredores, pero en el endpoint que
    de verdad alimenta el mapa y el score de riesgo de cada ruta: con cortes
    absolutos, ~86% de los 740 hotspots terminaba en 'alto'/'critico' (Bajo 6,
    Medio 98, Alto 568, Critico 68, confirmado en produccion), asi que casi
    cualquier ruta cruzaba una zona 'alto' sin importar que tan mejor fuera
    respecto de otra -- el score de riesgo se sentia constante. Este test
    verifica que con perfiles de zona bien distintos entre si, /hotspots
    realmente reparte en mas de un nivel.

    La hora se congela (11am, un horario diurno cualquiera) porque los cortes
    ahora son fijos (UMBRALES_HOTSPOTS, calibrados offline -- ver el comentario
    de niveles_relativos_desde_matriz en main.py) en vez de recalcularse sobre
    el lote de cada pedido: sin congelar la hora, este test dependeria de la
    hora real a la que corre pytest, verificado a mano que 11am reparte bien
    estos 8 perfiles entre varios niveles.
    """
    from datetime import datetime as datetime_real

    class _RelojFijo(datetime_real):
        @classmethod
        def now(cls, tz=None):
            return datetime_real(2026, 1, 6, 11, 0, 0, tzinfo=tz)  # martes 11am

    perfiles = [
        {"comuna_moda": str(i), "tipo_via_moda": tv, "contraparte_moda": cp, "sexo_moda": sx, "edad_promedio": edad}
        for i, (tv, cp, sx, edad) in enumerate([
            ("CALLE", "BICICLETA", "F", 20.0),
            ("CALLE", "PEATON", "F", 22.0),
            ("AVENIDA", "AUTO", "M", 30.0),
            ("AVENIDA", "AUTO", "M", 33.0),
            ("AVENIDA", "AUTO", "M", 35.0),
            ("AVENIDA", "CAMION", "M", 40.0),
            ("AV. GRAL. PAZ", "AUTO", "M", 45.0),
            ("AV. GRAL. PAZ", "CAMION", "M", 50.0),
        ], start=1)
    ]
    filas_db = [
        {
            "id": i, "cluster": i, "latitud": -34.6, "longitud": -58.4,
            "cantidad_siniestros": 50, "mortales": 1, "graves": 5, "nivel_riesgo": "bajo",
        }
        for i in range(1, len(perfiles) + 1)
    ]
    # Cada cluster necesita su propia fila en hotspots_contexto.csv para no caer
    # todos en el mismo perfil generico (que los volveria identicos a proposito,
    # sin poder probar nada) -- se parchea directo el contexto en cache.
    contexto_original = main.contexto_hotspots
    contexto_falso = contexto_original.copy() if hasattr(contexto_original, 'copy') else None
    import pandas as pd
    contexto_falso = pd.DataFrame([{"cluster": i, **perfiles[i - 1]} for i in range(1, len(perfiles) + 1)])
    with patch.object(main, "contexto_hotspots", contexto_falso):
        with patch("main.psycopg2.connect", return_value=_mock_db(filas_db)):
            with patch("main.datetime", _RelojFijo):
                r = client.get("/hotspots")
    assert r.status_code == 200
    hotspots = r.json()

    niveles_presentes = {h["nivel_riesgo"] for h in hotspots}
    assert len(niveles_presentes) >= 2, f"todos los hotspots quedaron en el mismo nivel: {niveles_presentes}"

    def score(h):
        p = h["prediccion_modelo"]
        return 2 * p.get("MORTAL", 0) + p.get("GRAVE", 0)

    orden_niveles = ["bajo", "medio", "alto", "critico"]
    mas_riesgoso = max(hotspots, key=score)
    menos_riesgoso = min(hotspots, key=score)
    assert orden_niveles.index(mas_riesgoso["nivel_riesgo"]) >= orden_niveles.index(menos_riesgoso["nivel_riesgo"])


def test_predecir_devuelve_clima_usado():
    """El modelo ahora usa clima como variable real: la respuesta tiene que reportar
    qué clima se usó (en vivo o fallback), no solo la predicción."""
    payload = {
        "hora": 20,
        "dia_semana": "Friday",
        "comuna": "1",
        "tipo_de_via": "AVENIDA",
        "contraparte": "AUTO",
        "edad_victima": 30,
        "sexo_victima": "M",
    }
    r = client.post("/predecir", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "clima_usado" in data
    assert set(data["clima_usado"].keys()) == {"lluvia", "temperatura", "humedad"}
    assert data["clima_usado"]["lluvia"] in ("SI", "NO")


def test_predecir_acepta_clima_explicito_para_simular_escenarios():
    """Si se pasa clima explícito (ej. 'y si llueve'), se usa ese en vez del clima
    en vivo, y la respuesta lo refleja tal cual se mandó."""
    payload = {
        "hora": 20,
        "dia_semana": "Friday",
        "comuna": "1",
        "tipo_de_via": "AVENIDA",
        "contraparte": "AUTO",
        "edad_victima": 30,
        "sexo_victima": "M",
        "lluvia": "SI",
        "temperatura": 12.0,
        "humedad": 90.0,
    }
    r = client.post("/predecir", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["clima_usado"] == {"lluvia": "SI", "temperatura": 12.0, "humedad": 90.0}


def test_hotspots_incluye_clima_en_cada_hotspot():
    fila_db = {
        "id": 1, "cluster": 0, "latitud": -34.6, "longitud": -58.4,
        "cantidad_siniestros": 50, "mortales": 1, "graves": 3, "nivel_riesgo": "bajo",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])):
        r = client.get("/hotspots")
    assert r.status_code == 200
    hotspot = r.json()[0]
    assert "clima" in hotspot
    assert set(hotspot["clima"].keys()) == {"lluvia", "temperatura", "humedad"}


def test_obtener_clima_actual_usa_fallback_historico_si_la_api_falla_y_no_hay_cache():
    """Degradación controlada, primer nivel: sin cache todavía y la API no responde
    (timeout, host caído, lo que sea) -> promedio histórico usado en el entrenamiento,
    nunca una excepción hacia el caller."""
    main._cache_clima['datos'] = None
    main._cache_clima['timestamp'] = 0.0
    with patch("main.httpx.get", side_effect=Exception("timeout simulado")):
        clima = main.obtener_clima_actual()
    assert clima == main._CLIMA_FALLBACK


def test_obtener_clima_actual_usa_ultimo_cache_si_la_api_falla_pero_hay_dato_previo():
    """Degradación controlada, segundo nivel: si ya hay un dato en cache (aunque esté
    vencido) y la API falla, se prefiere ese dato por sobre el promedio histórico."""
    dato_previo = {"lluvia": "SI", "temperatura": 15.0, "humedad": 88.0}
    main._cache_clima['datos'] = dato_previo
    main._cache_clima['timestamp'] = 0.0  # vencido a propósito (hace mucho tiempo)
    with patch("main.httpx.get", side_effect=Exception("timeout simulado")):
        clima = main.obtener_clima_actual()
    assert clima == dato_previo
    main._cache_clima['datos'] = None
    main._cache_clima['timestamp'] = 0.0


def test_obtener_clima_actual_usa_cache_vigente_sin_llamar_a_la_api():
    """Dentro de la ventana de 10 minutos no se debe llamar a la API de nuevo."""
    dato_cacheado = {"lluvia": "NO", "temperatura": 20.0, "humedad": 60.0}
    main._cache_clima['datos'] = dato_cacheado
    main._cache_clima['timestamp'] = time.monotonic()
    with patch("main.httpx.get") as mock_get:
        clima = main.obtener_clima_actual()
    mock_get.assert_not_called()
    assert clima == dato_cacheado
    main._cache_clima['datos'] = None
    main._cache_clima['timestamp'] = 0.0


def test_obtener_clima_actual_parsea_bien_una_respuesta_exitosa_de_open_meteo():
    """Camino feliz: la API responde ok, se cachea y se devuelve el dato parseado."""
    main._cache_clima['datos'] = None
    main._cache_clima['timestamp'] = 0.0
    respuesta_mock = MagicMock()
    respuesta_mock.json.return_value = {
        "current": {"precipitation": 0.5, "temperature_2m": 22.3, "relative_humidity_2m": 65}
    }
    respuesta_mock.raise_for_status.return_value = None
    with patch("main.httpx.get", return_value=respuesta_mock):
        clima = main.obtener_clima_actual()
    assert clima == {"lluvia": "SI", "temperatura": 22.3, "humedad": 65.0}
    main._cache_clima['datos'] = None
    main._cache_clima['timestamp'] = 0.0


def _mock_db_reportes(fetchone_valor=None, fetchall_valor=None, rowcount=0):
    """Mock de conexion/cursor para los endpoints de reportes colaborativos.
    A diferencia de _mock_db (que solo mockea fetchall para /hotspots), esta
    tabla usa fetchone (POST), fetchall (GET) y rowcount (DELETE)."""
    cursor = MagicMock()
    cursor.fetchone.return_value = fetchone_valor
    cursor.fetchall.return_value = fetchall_valor or []
    cursor.rowcount = rowcount
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    return conexion


def test_crear_reporte_devuelve_la_fila_creada():
    autor_id = "11111111-2222-4333-8444-555555555555"
    fila_creada = {
        "id": 1, "lat": -34.6, "lng": -58.4, "categoria": "pavimento",
        "autor_id": autor_id, "creado_en": "2026-09-04T12:00:00+00:00",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchone_valor=fila_creada)):
        r = client.post("/reportes", json={
            "lat": -34.6, "lng": -58.4, "categoria": "pavimento", "autor_id": autor_id,
        })
    assert r.status_code == 201
    assert r.json()["categoria"] == "pavimento"


def test_crear_reporte_rechaza_categoria_invalida():
    autor_id = "11111111-2222-4333-8444-555555555555"
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes()):
        r = client.post("/reportes", json={
            "lat": -34.6, "lng": -58.4, "categoria": "categoria-inventada", "autor_id": autor_id,
        })
    assert r.status_code == 422


def test_crear_reporte_rechaza_autor_id_no_uuid():
    """autor_id ya no acepta cualquier string -- ver ReporteNuevo.validar_autor_id."""
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes()):
        r = client.post("/reportes", json={
            "lat": -34.6, "lng": -58.4, "categoria": "pavimento", "autor_id": "dispositivo-abc",
        })
    assert r.status_code == 422


def test_listar_reportes_excluye_los_vencidos_segun_su_categoria():
    """Un 'corte' vence a las 12hs; uno de hace 2 dias no debe aparecer en la
    respuesta aunque siga en la base. Un 'pavimento' de la misma antiguedad
    (vence a los 30 dias) si tiene que aparecer."""
    ahora = datetime.now(timezone.utc)
    corte_vencido = {
        "id": 1, "lat": -34.6, "lng": -58.4, "categoria": "corte",
        "autor_id": "a", "creado_en": ahora - timedelta(days=2),
    }
    pavimento_vigente = {
        "id": 2, "lat": -34.6, "lng": -58.4, "categoria": "pavimento",
        "autor_id": "b", "creado_en": ahora - timedelta(days=2),
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchall_valor=[pavimento_vigente, corte_vencido])):
        r = client.get("/reportes")
    assert r.status_code == 200
    ids = [f["id"] for f in r.json()]
    assert ids == [2]


def test_borrar_mis_reportes_solo_afecta_al_autor_pedido():
    autor_id = "11111111-2222-4333-8444-555555555555"
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(rowcount=3)) as mock_connect:
        r = client.request("DELETE", "/reportes", params={"autor_id": autor_id})
    assert r.status_code == 200
    assert r.json() == {"eliminados": 3}
    cursor_usado = mock_connect.return_value.cursor.return_value
    cursor_usado.execute.assert_any_call(
        "DELETE FROM reportes_colaborativos WHERE autor_id = %s", (autor_id,)
    )


def test_borrar_mis_reportes_rechaza_autor_id_no_uuid():
    r = client.request("DELETE", "/reportes", params={"autor_id": "dispositivo-abc"})
    assert r.status_code == 422


def test_corredores_devuelve_nivel_de_riesgo_y_geometria_parseada():
    fila_db = {
        "id": 1, "calle": "PAZ, GRAL. AV.", "geometria": json.dumps([[-34.6, -58.5], [-34.5, -58.46]]),
        "cantidad_siniestros": 1119, "mortales": 23, "graves": 70,
        "comuna_moda": "12", "tipo_via_moda": "AV. GRAL. PAZ", "contraparte_moda": "AUTO",
        "edad_promedio": 34.3, "sexo_moda": "M",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])):
        r = client.get("/corredores")
    assert r.status_code == 200
    corredor = r.json()[0]
    assert corredor["nivel_riesgo"] in ("bajo", "medio", "alto", "critico")
    assert "prediccion_modelo" in corredor
    assert corredor["geometria"] == [[-34.6, -58.5], [-34.5, -58.46]]


def test_corredores_devuelve_lista_vacia_sin_reventar_si_no_hay_datos():
    with patch("main.psycopg2.connect", return_value=_mock_db([])):
        r = client.get("/corredores")
    assert r.status_code == 200
    assert r.json() == []


def test_corredores_diferencia_niveles_entre_si_no_todos_iguales():
    """
    Los corredores son, por construccion, solo avenidas transitadas (>=30
    siniestros): su riesgo absoluto cae en un rango distinto al de los 740
    hotspots puntuales, por eso tienen su propia poblacion de referencia
    (UMBRALES_CORREDORES). Este test verifica que, con corredores de perfiles
    bien distintos, aparecen al menos dos niveles, y el de mayor probabilidad
    de MORTAL/GRAVE no termina en un nivel mas bajo que el de menor probabilidad.

    Hora congelada (11am) por el mismo motivo que en el test analogo de
    /hotspots: los cortes ahora son fijos, no se recalculan sobre el lote de
    este pedido, asi que sin congelar la hora el test dependeria de a que hora
    real corre pytest.
    """
    from datetime import datetime as datetime_real

    class _RelojFijo(datetime_real):
        @classmethod
        def now(cls, tz=None):
            return datetime_real(2026, 1, 6, 11, 0, 0, tzinfo=tz)  # martes 11am

    perfiles = [
        {"comuna_moda": str(i), "tipo_via_moda": tv, "contraparte_moda": cp, "sexo_moda": sx, "edad_promedio": edad}
        for i, (tv, cp, sx, edad) in enumerate([
            ("CALLE", "BICICLETA", "F", 20.0),
            ("CALLE", "PEATON", "F", 22.0),
            ("AVENIDA", "AUTO", "M", 30.0),
            ("AVENIDA", "AUTO", "M", 33.0),
            ("AVENIDA", "AUTO", "M", 35.0),
            ("AVENIDA", "CAMION", "M", 40.0),
            ("AV. GRAL. PAZ", "AUTO", "M", 45.0),
            ("AV. GRAL. PAZ", "CAMION", "M", 50.0),
        ], start=1)
    ]
    filas_db = [
        {
            "id": i, "calle": f"CALLE {i}", "geometria": json.dumps([[-34.6, -58.5], [-34.5, -58.46]]),
            "cantidad_siniestros": 50, "mortales": 1, "graves": 5, **perfil,
        }
        for i, perfil in enumerate(perfiles, start=1)
    ]
    with patch("main.psycopg2.connect", return_value=_mock_db(filas_db)):
        with patch("main.datetime", _RelojFijo):
            r = client.get("/corredores")
    assert r.status_code == 200
    corredores = r.json()

    niveles_presentes = {c["nivel_riesgo"] for c in corredores}
    assert len(niveles_presentes) >= 2, f"todos los corredores quedaron en el mismo nivel: {niveles_presentes}"

    def score(c):
        p = c["prediccion_modelo"]
        return 2 * p.get("MORTAL", 0) + p.get("GRAVE", 0)

    orden_niveles = ["bajo", "medio", "alto", "critico"]
    mas_riesgoso = max(corredores, key=score)
    menos_riesgoso = min(corredores, key=score)
    assert orden_niveles.index(mas_riesgoso["nivel_riesgo"]) >= orden_niveles.index(menos_riesgoso["nivel_riesgo"])


def test_indice_inseguridad_por_comuna_cargado_y_diferenciado():
    """
    El indice de inseguridad (data/delitos_caba.csv del GCBA, ver
    notebooks/construir_indice_inseguridad.py) se carga una sola vez al arrancar
    y se usa como variable numerica del modelo (ver notebooks/reentrenar_modelo.py).
    Las 15 comunas de CABA tienen que estar presentes, con valores distintos entre
    si (no todas con el mismo indice, que seria indicio de que el join fallo y
    todo cayo al promedio de respaldo).
    """
    assert len(main.INDICE_INSEGURIDAD_POR_COMUNA) == 15
    valores = set(main.INDICE_INSEGURIDAD_POR_COMUNA.values())
    assert len(valores) > 1, "todas las comunas tienen el mismo indice, el join no diferencio nada"
    assert all(0.0 <= v <= 1.0 for v in valores)

    # Comuna inexistente: no debe reventar, cae al promedio de todas las comunas.
    generico = main.indice_inseguridad_de("comuna-que-no-existe")
    assert 0.0 <= generico <= 1.0


def test_predecir_usa_el_indice_de_inseguridad_de_la_comuna():
    """
    Dos comunas con indice de inseguridad bien distinto (la mas alta vs. la mas
    baja del dataset real) tienen que darle al modelo un input distinto en esa
    columna — se verifica llamando directo a indice_inseguridad_de, que es lo que
    alimenta /hotspots, /predecir y /corredores.
    """
    comuna_mas_insegura = max(main.INDICE_INSEGURIDAD_POR_COMUNA, key=main.INDICE_INSEGURIDAD_POR_COMUNA.get)
    comuna_mas_segura = min(main.INDICE_INSEGURIDAD_POR_COMUNA, key=main.INDICE_INSEGURIDAD_POR_COMUNA.get)
    assert main.indice_inseguridad_de(comuna_mas_insegura) > main.indice_inseguridad_de(comuna_mas_segura)

    payload_base = {
        "hora": 20, "dia_semana": "Friday", "tipo_de_via": "AVENIDA", "contraparte": "AUTO",
        "lluvia": "NO", "temperatura": 18.0, "humedad": 60.0,
    }
    r_insegura = client.post("/predecir", json={**payload_base, "comuna": comuna_mas_insegura})
    r_segura = client.post("/predecir", json={**payload_base, "comuna": comuna_mas_segura})
    assert r_insegura.status_code == 200
    assert r_segura.status_code == 200


def test_hotspots_inseguridad_devuelve_lo_que_hay_en_la_base():
    filas_db = [
        {
            "id": 1, "cluster": 5, "latitud": -34.6, "longitud": -58.4,
            "cantidad_delitos": 120, "comuna_moda": "1", "tipo_delito_moda": "Robo",
            "nivel_riesgo": "alto",
        },
    ]
    with patch("main.psycopg2.connect", return_value=_mock_db(filas_db)):
        r = client.get("/hotspots-inseguridad")
    assert r.status_code == 200
    datos = r.json()
    assert len(datos) == 1
    assert datos[0]["nivel_riesgo"] == "alto"
    assert datos[0]["cantidad_delitos"] == 120


def test_hotspots_inseguridad_acepta_tipo_moto():
    with patch("main.psycopg2.connect", return_value=_mock_db([])):
        r_general = client.get("/hotspots-inseguridad")
        r_moto = client.get("/hotspots-inseguridad?tipo=moto")
        r_invalido = client.get("/hotspots-inseguridad?tipo=lo-que-sea")
    assert r_general.status_code == 200
    assert r_moto.status_code == 200
    assert r_invalido.status_code == 422  # Literal["general", "moto"] rechaza cualquier otro valor


def _fake_respuesta_tomtom(travel_seg=600, sin_trafico_seg=480, largo_m=3200):
    """Arma una respuesta minima pero realista de la Routing API de TomTom (una sola
    ruta, dos puntos, una instruccion de giro), suficiente para probar el mapeo
    completo que hace calcular_rutas sin depender del servicio real."""
    respuesta = MagicMock()
    respuesta.raise_for_status.return_value = None
    respuesta.json.return_value = {
        "routes": [
            {
                "summary": {
                    "lengthInMeters": largo_m,
                    "travelTimeInSeconds": travel_seg,
                    "noTrafficTravelTimeInSeconds": sin_trafico_seg,
                },
                "legs": [
                    {
                        "points": [
                            {"latitude": -34.60, "longitude": -58.45},
                            {"latitude": -34.61, "longitude": -58.44},
                        ]
                    }
                ],
                "guidance": {
                    "instructions": [
                        {
                            "maneuver": "TURN_LEFT",
                            "street": "Av. Corrientes",
                            "point": {"latitude": -34.605, "longitude": -58.445},
                        }
                    ]
                },
            }
        ]
    }
    return respuesta


def test_calcular_rutas_devuelve_ruta_bien_formada_con_eta_de_trafico():
    """Flujo completo de /rutas: pedido -> TomTom (mockeado) -> traduccion de
    maniobras -> contrato RutaOut que espera el frontend (coords, km, min,
    eta_trafico desglosado, pasos con tipo/modificador ya traducidos de TomTom
    a la convencion heredada de OSRM)."""
    with patch("main.TOMTOM_API_KEY", "clave-de-prueba"), \
         patch("main.httpx.get", return_value=_fake_respuesta_tomtom()) as mock_get:
        r = client.get("/rutas", params={
            "origen_lat": -34.60, "origen_lng": -58.45,
            "destino_lat": -34.61, "destino_lng": -58.44,
        })
    assert r.status_code == 200
    mock_get.assert_called_once()
    rutas = r.json()
    assert len(rutas) == 1
    ruta = rutas[0]

    assert ruta["coords"] == [[-34.60, -58.45], [-34.61, -58.44]]
    assert ruta["km"] == 3.2
    # "min" usa el tiempo SIN trafico (referencia), no el tiempo con trafico en vivo.
    assert ruta["min"] == 8

    assert ruta["eta_trafico"] == {
        "con_trafico_min": 10, "sin_trafico_min": 8, "diferencia_min": 2,
    }

    assert len(ruta["pasos"]) == 1
    paso = ruta["pasos"][0]
    assert paso["tipo"] == "turn"
    assert paso["modificador"] == "left"
    assert paso["calle"] == "Av. Corrientes"


def test_calcular_rutas_sin_api_key_devuelve_503():
    with patch("main.TOMTOM_API_KEY", None):
        r = client.get("/rutas", params={
            "origen_lat": -34.60, "origen_lng": -58.45,
            "destino_lat": -34.61, "destino_lng": -58.44,
        })
    assert r.status_code == 503


def test_calcular_rutas_si_tomtom_falla_devuelve_502():
    import httpx as httpx_real
    with patch("main.TOMTOM_API_KEY", "clave-de-prueba"), \
         patch("main.httpx.get", side_effect=httpx_real.ConnectError("timeout simulado")):
        r = client.get("/rutas", params={
            "origen_lat": -34.60, "origen_lng": -58.45,
            "destino_lat": -34.61, "destino_lng": -58.44,
        })
    assert r.status_code == 502


def test_calcular_rutas_sin_resultados_devuelve_404():
    respuesta = MagicMock()
    respuesta.raise_for_status.return_value = None
    respuesta.json.return_value = {"routes": []}
    with patch("main.TOMTOM_API_KEY", "clave-de-prueba"), \
         patch("main.httpx.get", return_value=respuesta):
        r = client.get("/rutas", params={
            "origen_lat": -34.60, "origen_lng": -58.45,
            "destino_lat": -34.61, "destino_lng": -58.44,
        })
    assert r.status_code == 404
