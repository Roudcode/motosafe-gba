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


class _ConexionFalsaPool:
    def __init__(self):
        self.closed = 0
        self.rollbacks = 0
        self.cerrada = False

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = 1
        self.cerrada = True


def test_raiz_responde_ok():
    r = client.get("/")
    assert r.status_code == 200
    assert "mensaje" in r.json()


def test_health_informa_estado_de_base_sin_exponer_configuracion():
    conexion = _mock_db([])
    with patch("main.psycopg2.connect", return_value=conexion):
        r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"
    assert r.json()["base_datos"] == "ok"
    assert "DATABASE_URL" not in r.text
    # Booleano sin versiones exactas: /health es público (ver A22).
    assert isinstance(r.json()["version_sklearn_coincide"], bool)
    assert main.sklearn.__version__ not in r.text


def test_metrics_registra_conteo_y_latencia_de_una_ruta_sin_exponer_configuracion():
    """Ver T04 en BACKLOG.md: /metrics agrega conteo, errores y latencia por
    ruta. No debe filtrar DATABASE_URL ni ningun otro secreto de config."""
    main._metricas_por_ruta.clear()
    r1 = client.get("/")
    assert r1.status_code == 200
    r2 = client.get("/metrics")
    assert r2.status_code == 200
    cuerpo = r2.json()
    assert "/" in cuerpo
    assert cuerpo["/"]["conteo"] >= 1
    assert cuerpo["/"]["errores_5xx"] == 0
    assert cuerpo["/"]["latencia_promedio_ms"] >= 0
    assert "DATABASE_URL" not in r2.text


def test_metrics_cuenta_error_4xx_de_una_ruta_invalida():
    main._metricas_por_ruta.clear()
    r1 = client.delete("/reportes/7", headers={"X-Report-Delete-Token": "corto"})
    assert r1.status_code == 422
    r2 = client.get("/metrics")
    ruta = "/reportes/{reporte_id}"
    assert ruta in r2.json()
    assert r2.json()[ruta]["errores_4xx"] >= 1


def test_pool_no_supera_el_maximo_y_reutiliza_conexion_limpia():
    primera, segunda = _ConexionFalsaPool(), _ConexionFalsaPool()
    pool = main._PoolConexiones(maxsize=2, timeout=0)
    with patch("main.psycopg2.connect", side_effect=[primera, segunda]) as conectar:
        assert pool.getconn() is primera
        assert pool.getconn() is segunda
        with pytest.raises(RuntimeError, match="agotado"):
            pool.getconn()
        pool.putconn(primera)
        assert pool.getconn() is primera
    assert conectar.call_count == 2
    assert primera.rollbacks == 1


def test_esquema_reportes_se_asegura_una_sola_vez_por_proceso():
    conexion = MagicMock()
    estado_anterior = main._esquema_reportes_listo
    main._esquema_reportes_listo = False
    try:
        with patch("main._asegurar_tabla_reportes") as reportes, patch("main._asegurar_tabla_confirmaciones") as confirmaciones:
            main._asegurar_esquema_reportes_una_vez(conexion)
            main._asegurar_esquema_reportes_una_vez(conexion)
        reportes.assert_called_once_with(conexion)
        confirmaciones.assert_called_once_with(conexion)
    finally:
        main._esquema_reportes_listo = estado_anterior


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


def _reloj_fijo(hora, minuto=0):
    """Clase datetime con .now() congelado a esa hora (martes 6/1/2026, fecha
    arbitraria sin relevancia), pensada para usarse con
    patch("main.datetime", _reloj_fijo(HORA)) en cualquier test que dependa
    de 'hora_actual' (siniestros/corredores via el modelo, o inseguridad via
    FRANJA_PICO_INSEGURIDAD) sin quedar atado a la hora real de Buenos Aires
    en el momento en que corre pytest. `hora` es en punto de referencia de
    ZONA_CABA (main pasa el tz al llamar .now(tz), esta clase solo fija el
    reloj, no reimplementa la conversion de zona)."""
    from datetime import datetime as datetime_real

    class _RelojFijoClase(datetime_real):
        @classmethod
        def now(cls, tz=None):
            return datetime_real(2026, 1, 6, hora, minuto, 0, tzinfo=tz)

    return _RelojFijoClase


# Reloj por defecto para tests que solo necesitan "una hora cualquiera FUERA
# de las franjas pico de inseguridad" (ver FRANJA_PICO_INSEGURIDAD en
# main.py: general 17-21hs, moto 19-23hs) -- 11am no cae en ninguna de las
# dos, igual que ya se usaba de forma ad-hoc en
# test_hotspots_con_choque_reciente_cerca_sube_un_escalon.
_RelojFijo = _reloj_fijo(11)


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


def _mock_db_reportes(fetchone_valor=None, fetchall_valor=None, rowcount=0, conteo_previo_autor=0):
    """Mock de conexion/cursor para los endpoints de reportes colaborativos.
    A diferencia de _mock_db (que solo mockea fetchall para /hotspots), esta
    tabla usa fetchone (POST), fetchall (GET) y rowcount (DELETE).

    crear_reporte llama fetchone() dos veces: primero para el conteo de la
    cuota diaria por autor_id, despues para el RETURNING del INSERT. Con
    side_effect en vez de return_value, la primera llamada devuelve el
    conteo y la segunda la fila creada -- en los tests que no pasan por
    crear_reporte (GET/DELETE) simplemente no se consume el segundo valor."""
    cursor = MagicMock()
    cursor.fetchone.side_effect = [{"cantidad": conteo_previo_autor}, fetchone_valor]
    cursor.fetchall.return_value = fetchall_valor or []
    cursor.rowcount = rowcount
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    return conexion


def test_crear_reporte_devuelve_la_fila_creada():
    autor_id = "11111111-2222-4333-8444-555555555555"
    fila_creada = {
        "id": 1, "lat": -34.6, "lng": -58.4, "categoria": "pavimento",
        "creado_en": "2026-09-04T12:00:00+00:00",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchone_valor=fila_creada)):
        r = client.post("/reportes", json={
            "lat": -34.6, "lng": -58.4, "categoria": "pavimento", "autor_id": autor_id,
        })
    assert r.status_code == 201
    assert r.json()["categoria"] == "pavimento"
    assert len(r.json()["delete_token"]) >= 32


def test_crear_reporte_rechaza_coordenadas_fuera_del_mundo():
    autor_id = "11111111-2222-4333-8444-555555555555"
    r = client.post("/reportes", json={
        "lat": 999, "lng": -58.4, "categoria": "pavimento", "autor_id": autor_id,
    })
    assert r.status_code == 422


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


def test_crear_reporte_respeta_cuota_diaria_por_autor():
    """Ver CUOTA_REPORTES_POR_DIA_POR_AUTOR: el rate limit de /reportes es por
    IP y por minuto: no distingue dispositivos, ni frena volumen sostenido
    durante el dia. Esta cuota es la segunda barrera, por autor_id."""
    autor_id = "11111111-2222-4333-8444-555555555555"
    conteo_al_limite = main.CUOTA_REPORTES_POR_DIA_POR_AUTOR
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(conteo_previo_autor=conteo_al_limite)):
        r = client.post("/reportes", json={
            "lat": -34.6, "lng": -58.4, "categoria": "pavimento", "autor_id": autor_id,
        })
    assert r.status_code == 429
    assert str(conteo_al_limite) in r.json()["detail"]


def test_crear_reporte_permite_uno_menos_del_limite_de_la_cuota():
    autor_id = "11111111-2222-4333-8444-555555555555"
    fila_creada = {
        "id": 1, "lat": -34.6, "lng": -58.4, "categoria": "pavimento",
        "creado_en": "2026-09-04T12:00:00+00:00",
    }
    conteo_bajo_el_limite = main.CUOTA_REPORTES_POR_DIA_POR_AUTOR - 1
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(
        fetchone_valor=fila_creada, conteo_previo_autor=conteo_bajo_el_limite,
    )):
        r = client.post("/reportes", json={
            "lat": -34.6, "lng": -58.4, "categoria": "pavimento", "autor_id": autor_id,
        })
    assert r.status_code == 201


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


def test_borrar_reporte_requiere_token_privado():
    token = "x" * 32
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(rowcount=1)) as mock_connect:
        r = client.delete("/reportes/7", headers={"X-Report-Delete-Token": token})
    assert r.status_code == 200
    assert r.json() == {"eliminado": True}
    cursor_usado = mock_connect.return_value.cursor.return_value
    cursor_usado.execute.assert_any_call(
        "DELETE FROM reportes_colaborativos WHERE id = %s AND delete_token_hash = %s", (7, main._hash_delete_token(token))
    )


def test_borrar_reporte_no_acepta_un_token_de_otro_reporte():
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(rowcount=0)):
        r = client.delete("/reportes/7", headers={"X-Report-Delete-Token": "x" * 32})
    assert r.status_code == 404


def test_borrar_reporte_rechaza_token_corto():
    r = client.delete("/reportes/7", headers={"X-Report-Delete-Token": "corto"})
    assert r.status_code == 422


def test_listar_reportes_no_expone_autor_id():
    ahora = datetime.now(timezone.utc)
    fila = {
        "id": 1, "lat": -34.6, "lng": -58.4, "categoria": "robo",
        "autor_id": "identidad-interna", "creado_en": ahora,
        "confirmaciones": 0, "desmentidas": 0,
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchall_valor=[fila])):
        r = client.get("/reportes")
    assert r.status_code == 200
    assert "autor_id" not in r.json()[0]


def test_confirmar_reporte_devuelve_el_voto_creado():
    autor_original = "11111111-2222-4333-8444-555555555555"
    otro_autor = "99999999-8888-4777-8666-555555555555"
    reporte_existente = {"autor_id": autor_original}
    voto_creado = {"reporte_id": 1, "autor_id": otro_autor, "tipo": "confirma"}
    cursor = MagicMock()
    cursor.fetchone.side_effect = [reporte_existente, voto_creado]
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    with patch("main.psycopg2.connect", return_value=conexion):
        r = client.post("/reportes/1/confirmar", json={"autor_id": otro_autor, "tipo": "confirma"})
    assert r.status_code == 201
    assert r.json()["tipo"] == "confirma"


def test_confirmar_reporte_rechaza_votar_el_propio():
    autor_original = "11111111-2222-4333-8444-555555555555"
    cursor = MagicMock()
    cursor.fetchone.return_value = {"autor_id": autor_original}
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    with patch("main.psycopg2.connect", return_value=conexion):
        r = client.post("/reportes/1/confirmar", json={"autor_id": autor_original, "tipo": "desmiente"})
    assert r.status_code == 400


def test_confirmar_reporte_rechaza_reporte_inexistente():
    otro_autor = "99999999-8888-4777-8666-555555555555"
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    with patch("main.psycopg2.connect", return_value=conexion):
        r = client.post("/reportes/999/confirmar", json={"autor_id": otro_autor, "tipo": "confirma"})
    assert r.status_code == 404


def test_confirmar_reporte_rechaza_tipo_invalido():
    otro_autor = "99999999-8888-4777-8666-555555555555"
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes()):
        r = client.post("/reportes/1/confirmar", json={"autor_id": otro_autor, "tipo": "me-gusta"})
    assert r.status_code == 422


def test_predecir_rechaza_hora_y_edad_imposibles():
    payload = {
        "hora": 99, "dia_semana": "Friday", "comuna": "1", "tipo_de_via": "AVENIDA",
        "contraparte": "AUTO", "edad_victima": -2, "sexo_victima": "M",
    }
    assert client.post("/predecir", json=payload).status_code == 422


def test_hotspots_vacios_devuelve_lista_vacia():
    with patch("main.psycopg2.connect", return_value=_mock_db([])):
        r = client.get("/hotspots")
    assert r.status_code == 200
    assert r.json() == []


def test_listar_reportes_retira_por_consenso_de_desmentidas():
    """Un reporte con 3 desmentidas y 0 confirmaciones se retira antes de tiempo,
    aunque su vigencia por categoria todavia no haya vencido."""
    ahora = datetime.now(timezone.utc)
    robo_desmentido = {
        "id": 1, "lat": -34.6, "lng": -58.4, "categoria": "robo",
        "autor_id": "a", "creado_en": ahora - timedelta(hours=1),
        "confirmaciones": 0, "desmentidas": 3,
    }
    robo_confirmado = {
        "id": 2, "lat": -34.6, "lng": -58.4, "categoria": "robo",
        "autor_id": "b", "creado_en": ahora - timedelta(hours=1),
        "confirmaciones": 3, "desmentidas": 2,
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchall_valor=[robo_confirmado, robo_desmentido])):
        r = client.get("/reportes")
    ids = [f["id"] for f in r.json()]
    assert ids == [2]


def test_listar_reportes_prensa_excluye_los_de_mas_de_un_mes():
    """A diferencia de /reportes, aca no hay categorias con vigencia distinta --
    todo vence a los 30 dias fijo (ver VIGENCIA_HORAS_PRENSA)."""
    ahora = datetime.now(timezone.utc)
    nota_vigente = {
        "id": 1, "lat": -34.6, "lng": -58.4, "nivel_precision": "barrio", "radio_metros": 800,
        "titular": "Asaltaron a un jubilado en Flores", "url_fuente": "https://ejemplo.com/1",
        "fuente": "La Nación", "creado_en": ahora - timedelta(days=10),
    }
    nota_vencida = {
        "id": 2, "lat": -34.6, "lng": -58.4, "nivel_precision": "barrio", "radio_metros": 800,
        "titular": "Robo en Palermo", "url_fuente": "https://ejemplo.com/2",
        "fuente": "Infobae", "creado_en": ahora - timedelta(days=45),
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchall_valor=[nota_vigente, nota_vencida])):
        r = client.get("/reportes-prensa")
    assert r.status_code == 200
    ids = [f["id"] for f in r.json()]
    assert ids == [1]


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
    # Hora congelada a las 11am (fuera de las dos franjas pico, ver
    # FRANJA_PICO_INSEGURIDAD en main.py) para que este test no dependa de la
    # hora real de Buenos Aires en el momento en que corre pytest -- sin
    # esto, el mismo test fallaria de forma intermitente solo entre las
    # 17-21hs, que es justo cuando el ajuste tiene que activarse (ver los
    # tests dedicados mas abajo para ese comportamiento).
    with patch("main.datetime", _RelojFijo):
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
    assert datos[0]["ajustado_por_horario"] is False


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


# --- Ajuste de riesgo por reportes de prensa recientes (ver el comentario
# largo de _ajuste_por_reportes_recientes en main.py) --------------------
#
# Estos tests patchean main._obtener_reportes_recientes_por_tipo directo en
# vez de sumar filas falsas a _mock_db/_mock_db_reportes a proposito: esa
# funcion cachea su resultado en un dict a nivel de modulo
# (_cache_reportes_recientes) que persiste entre tests dentro de la misma
# corrida de pytest, asi que depender del mock de la conexion de base
# haria estos tests fragiles frente al orden en que corren. Patchear la
# funcion en si es determinista y evita ademas que los tests existentes de
# /hotspots, /corredores y /hotspots-inseguridad (que NO patchean esto)
# necesiten tocarse: sin el patch, esa funcion cae en su propio manejo
# defensivo de filas con forma inesperada (ver el try/except por fila) y
# devuelve lista vacia, o sea "sin ajuste" -- el comportamiento de antes.

def test_reportes_prensa_incluye_tipo_incidente():
    ahora = datetime.now(timezone.utc)
    nota_choque = {
        "id": 1, "lat": -34.6, "lng": -58.4, "nivel_precision": "barrio", "radio_metros": 800,
        "titular": "Choque múltiple en la Panamericana", "url_fuente": "https://ejemplo.com/1",
        "fuente": "TN", "tipo_incidente": "choque", "creado_en": ahora - timedelta(days=1),
    }
    with patch("main.psycopg2.connect", return_value=_mock_db_reportes(fetchall_valor=[nota_choque])):
        r = client.get("/reportes-prensa")
    assert r.status_code == 200
    assert r.json()[0]["tipo_incidente"] == "choque"


def test_nivel_subido_un_escalon_topa_en_critico():
    assert main._nivel_subido_un_escalon("bajo") == "medio"
    assert main._nivel_subido_un_escalon("medio") == "alto"
    assert main._nivel_subido_un_escalon("alto") == "critico"
    assert main._nivel_subido_un_escalon("critico") == "critico"
    assert main._nivel_subido_un_escalon("valor-no-reconocido") == "valor-no-reconocido"


def test_hotspots_sin_reportes_recientes_no_se_ajusta():
    fila_db = {
        "id": 1, "cluster": 0, "latitud": -34.6, "longitud": -58.4,
        "cantidad_siniestros": 50, "mortales": 1, "graves": 3, "nivel_riesgo": "bajo",
    }
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=[]):
        r = client.get("/hotspots")
    hotspot = r.json()[0]
    assert hotspot["ajustado_por_reciente"] is False
    assert hotspot["motivo_ajuste"] is None


def test_hotspots_con_choque_reciente_cerca_sube_un_escalon():
    """Un hotspot a ~50m de un choque reportado hace 2 días tiene que subir
    su nivel_riesgo un escalón (relativo al que calcula el modelo para ese
    mismo contexto) y quedar marcado como ajustado. No se asume un nivel
    absoluto fijo ("bajo", "medio", etc.): el modelo real (no uno de prueba)
    puede dar cualquiera de los cuatro para este contexto sintético según la
    hora/clima -- lo que hay que verificar es que el ajuste sube EXACTAMENTE
    un escalón respecto de lo que el modelo daría sin él, no un valor
    absoluto adivinado. La hora se congela (mismo patrón que
    test_hotspots_diferencia_niveles_entre_si_no_todos_iguales) para que las
    dos llamadas (con y sin reporte cercano) usen el mismo contexto horario
    y sean comparables entre sí."""
    fila_db = {
        "id": 1, "cluster": 0, "latitud": -34.6000, "longitud": -58.4000,
        "cantidad_siniestros": 50, "mortales": 1, "graves": 3, "nivel_riesgo": "bajo",
    }
    reporte_cercano = [{"lat": -34.6003, "lng": -58.4000, "titular": "Choque en Palermo"}]

    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main.datetime", _RelojFijo), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=[]):
        r_sin_ajuste = client.get("/hotspots")
    nivel_base = r_sin_ajuste.json()[0]["nivel_riesgo"]

    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main.datetime", _RelojFijo), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=reporte_cercano):
        r_con_ajuste = client.get("/hotspots")
    hotspot = r_con_ajuste.json()[0]

    assert hotspot["ajustado_por_reciente"] is True
    assert hotspot["nivel_riesgo"] == main._nivel_subido_un_escalon(nivel_base)
    assert "Choque en Palermo" in hotspot["motivo_ajuste"]


def test_hotspots_con_choque_reciente_lejos_no_se_ajusta():
    fila_db = {
        "id": 1, "cluster": 0, "latitud": -34.6000, "longitud": -58.4000,
        "cantidad_siniestros": 50, "mortales": 1, "graves": 3, "nivel_riesgo": "bajo",
    }
    reporte_lejano = [{"lat": -34.9, "lng": -58.9, "titular": "Choque en La Matanza"}]
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=reporte_lejano):
        r = client.get("/hotspots")
    hotspot = r.json()[0]
    assert hotspot["ajustado_por_reciente"] is False
    # No se ajusta -> nivel_riesgo tiene que ser el mismo que sin reporte alguno
    # (no un valor absoluto adivinado, ver la nota larga del test anterior).
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=[]):
        r_sin_reportes = client.get("/hotspots")
    assert hotspot["nivel_riesgo"] == r_sin_reportes.json()[0]["nivel_riesgo"]


def test_corredores_con_choque_cerca_de_un_vertice_se_ajusta():
    fila_db = {
        "id": 1, "calle": "PAZ, GRAL. AV.", "geometria": json.dumps([[-34.6, -58.5], [-34.5, -58.46]]),
        "cantidad_siniestros": 1119, "mortales": 23, "graves": 70,
        "comuna_moda": "12", "tipo_via_moda": "AV. GRAL. PAZ", "contraparte_moda": "AUTO",
        "edad_promedio": 34.3, "sexo_moda": "M",
    }
    reporte_cercano_al_segundo_vertice = [{"lat": -34.5003, "lng": -58.46, "titular": "Choque en Av. Gral. Paz"}]
    with patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=reporte_cercano_al_segundo_vertice):
        r = client.get("/corredores")
    corredor = r.json()[0]
    assert corredor["ajustado_por_reciente"] is True
    assert "Choque en Av. Gral. Paz" in corredor["motivo_ajuste"]


def test_hotspots_inseguridad_con_robo_reciente_cerca_se_ajusta():
    # Hora fija FUERA de la franja pico para aislar el efecto del ajuste por
    # reporte reciente del de franja horaria (ver los tests dedicados a cada
    # uno mas abajo, y el de abajo de todo que prueba que se apilan).
    fila_db = {
        "id": 1, "cluster": 5, "latitud": -34.6, "longitud": -58.4,
        "cantidad_delitos": 120, "comuna_moda": "1", "tipo_delito_moda": "Robo",
        "nivel_riesgo": "alto",
    }
    reporte_cercano = [{"lat": -34.6002, "lng": -58.4001, "titular": "Robo en Retiro"}]
    with patch("main.datetime", _RelojFijo), \
         patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=reporte_cercano):
        r = client.get("/hotspots-inseguridad")
    hotspot = r.json()[0]
    assert hotspot["ajustado_por_reciente"] is True
    assert hotspot["ajustado_por_horario"] is False
    assert hotspot["nivel_riesgo"] == "critico"  # alto -> critico (un escalon, por el reporte)
    assert "Robo en Retiro" in hotspot["motivo_ajuste"]


# --- Ajuste de riesgo por franja horaria (solo /hotspots-inseguridad, ver
# FRANJA_PICO_INSEGURIDAD y _aplicar_ajuste_horario en main.py) -----------

def test_hotspots_inseguridad_en_franja_pico_general_sube_un_escalon():
    fila_db = {
        "id": 1, "cluster": 5, "latitud": -34.6, "longitud": -58.4,
        "cantidad_delitos": 120, "comuna_moda": "1", "tipo_delito_moda": "Robo",
        "nivel_riesgo": "medio",
    }
    with patch("main.datetime", _reloj_fijo(18)), \
         patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=[]):
        r = client.get("/hotspots-inseguridad")  # tipo=general por default
    hotspot = r.json()[0]
    assert hotspot["ajustado_por_horario"] is True
    assert hotspot["nivel_riesgo"] == "alto"  # medio -> alto, 18hs cae en 17-21hs
    assert "18hs" in hotspot["motivo_ajuste_horario"]


def test_hotspots_inseguridad_fuera_de_franja_pico_no_se_ajusta_por_horario():
    fila_db = {
        "id": 1, "cluster": 5, "latitud": -34.6, "longitud": -58.4,
        "cantidad_delitos": 120, "comuna_moda": "1", "tipo_delito_moda": "Robo",
        "nivel_riesgo": "medio",
    }
    with patch("main.datetime", _reloj_fijo(11)), \
         patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=[]):
        r = client.get("/hotspots-inseguridad")
    hotspot = r.json()[0]
    assert hotspot["ajustado_por_horario"] is False
    assert hotspot["motivo_ajuste_horario"] is None
    assert hotspot["nivel_riesgo"] == "medio"  # sin cambios


def test_hotspots_inseguridad_moto_usa_su_propia_franja_distinta_de_general():
    # 22hs: dentro de la franja pico de MOTO (19-23hs) pero fuera de la de
    # GENERAL (17-21hs) -- si el endpoint usara una sola franja compartida
    # para los dos tipos (lo que la distribucion real del dataset de
    # Delitos del GCBA contradice, ver el comentario de FRANJA_PICO_INSEGURIDAD),
    # este test fallaria. Cada llamada usa su propio dict de fixture (no uno
    # compartido): _aplicar_ajuste_horario muta la fila in-place, asi que
    # reutilizar el mismo dict entre las dos llamadas haria que el ajuste de
    # la primera (moto) contaminara el resultado de la segunda (general).
    fila_moto = {
        "id": 1, "cluster": 5, "latitud": -34.6, "longitud": -58.4,
        "cantidad_delitos": 40, "comuna_moda": "1", "tipo_delito_moda": "Robo",
        "nivel_riesgo": "medio",
    }
    fila_general = dict(fila_moto)
    with patch("main.datetime", _reloj_fijo(22)), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=[]):
        with patch("main.psycopg2.connect", return_value=_mock_db([fila_moto])):
            r_moto = client.get("/hotspots-inseguridad?tipo=moto")
        with patch("main.psycopg2.connect", return_value=_mock_db([fila_general])):
            r_general = client.get("/hotspots-inseguridad?tipo=general")
    assert r_moto.json()[0]["ajustado_por_horario"] is True
    assert r_moto.json()[0]["nivel_riesgo"] == "alto"
    assert r_general.json()[0]["ajustado_por_horario"] is False
    assert r_general.json()[0]["nivel_riesgo"] == "medio"


def test_hotspots_inseguridad_ajuste_horario_y_reciente_se_apilan():
    """En franja pico Y con un reporte reciente cerca, los dos ajustes se
    suman: dos escalones, no uno. Arranca en 'bajo' (dos escalones libres
    antes de topar en 'critico') para que el test pueda distinguir "se
    aplico un ajuste" de "se aplicaron los dos"."""
    fila_db = {
        "id": 1, "cluster": 5, "latitud": -34.6, "longitud": -58.4,
        "cantidad_delitos": 120, "comuna_moda": "1", "tipo_delito_moda": "Robo",
        "nivel_riesgo": "bajo",
    }
    reporte_cercano = [{"lat": -34.6002, "lng": -58.4001, "titular": "Robo en Retiro"}]
    with patch("main.datetime", _reloj_fijo(18)), \
         patch("main.psycopg2.connect", return_value=_mock_db([fila_db])), \
         patch("main._obtener_reportes_recientes_por_tipo", return_value=reporte_cercano):
        r = client.get("/hotspots-inseguridad")
    hotspot = r.json()[0]
    assert hotspot["ajustado_por_reciente"] is True
    assert hotspot["ajustado_por_horario"] is True
    assert hotspot["nivel_riesgo"] == "alto"  # bajo -> medio (reciente) -> alto (horario)


def test_vertices_de_geometria_maneja_formatos_invalidos_sin_reventar():
    assert main._vertices_de_geometria(None) == []
    assert main._vertices_de_geometria([]) == []
    assert main._vertices_de_geometria("no-es-una-lista") == []
    assert main._vertices_de_geometria([[-34.6, -58.5], [-34.5, -58.46]]) == [(-34.6, -58.5), (-34.5, -58.46)]


def test_cobertura_capas_informa_periodo_real_y_prensa():
    """A10/A11/A15: período de los datos de cada capa, no fecha del archivo."""
    cursor = MagicMock()
    cursor.fetchone.return_value = (datetime(2026, 10, 5, 21, 30, tzinfo=timezone.utc),)
    conexion = MagicMock()
    conexion.cursor.return_value = cursor
    with patch("main.psycopg2.connect", return_value=conexion):
        r = client.get("/capas/cobertura")
    assert r.status_code == 200
    datos = r.json()
    for capa in ('hotspots', 'corredores', 'inseguridad_general', 'inseguridad_moto'):
        assert datos[capa]['desde'] <= datos[capa]['hasta']
        assert datos[capa]['fuente']
    assert datos['prensa'] == {'vigencia_dias': 30, 'mas_reciente': '2026-10-05T21:30:00+00:00'}


def test_cobertura_capas_no_falla_sin_base():
    with patch("main.psycopg2.connect", side_effect=main.psycopg2.OperationalError("sin base")):
        r = client.get("/capas/cobertura")
    assert r.status_code == 200
    assert r.json()['prensa']['mas_reciente'] is None
    assert 'hotspots' in r.json()
