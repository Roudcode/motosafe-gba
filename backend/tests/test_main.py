"""
Tests basicos del backend. Corren con pytest desde backend/:
    cd backend && pytest

No requieren la base de datos levantada: el endpoint /hotspots se prueba
mockeando psycopg2.connect, asi el test es rapido y no depende de Docker
estando corriendo. /predecir si usa el modelo real (modelo_final.pkl),
porque eso es justamente lo que queremos verificar.
"""
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


def test_nivel_desde_probabilidades_umbrales():
    """Casos de borde de la funcion de umbrales, documentados en su docstring."""
    assert main.nivel_desde_probabilidades({"MORTAL": 0.25, "GRAVE": 0.0}) == "critico"
    assert main.nivel_desde_probabilidades({"MORTAL": 0.15, "GRAVE": 0.0}) == "alto"
    assert main.nivel_desde_probabilidades({"MORTAL": 0.0, "GRAVE": 0.45}) == "alto"
    assert main.nivel_desde_probabilidades({"MORTAL": 0.0, "GRAVE": 0.25}) == "medio"
    assert main.nivel_desde_probabilidades({"MORTAL": 0.0, "GRAVE": 0.0}) == "bajo"
