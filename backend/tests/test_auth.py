"""Pruebas del circuito real de login/logout (auth.py).

A diferencia del resto de la suite, estos tests NO quieren el bypass
global de conftest.py (sesion_valida siempre True) -- es justamente el
circuito de autenticacion lo que se esta probando aca.
"""
import os

import pytest
from fastapi.testclient import TestClient

import auth
import main

CONTRASENA_TEST = "clave-de-test-no-usar-en-produccion"


@pytest.fixture(autouse=True)
def _sesion_siempre_valida():
    """Anula, solo en este archivo, el bypass autouse de conftest.py."""
    yield


@pytest.fixture(autouse=True)
def _limpiar_intentos_fallidos():
    auth._intentos_fallidos.clear()
    yield
    auth._intentos_fallidos.clear()


@pytest.fixture(autouse=True)
def _sin_base_real(monkeypatch):
    """/health y /metrics tocan la base. Sin esto, si Postgres esta levantado,
    dejan conexiones reales en main._pool_conexiones y los tests de
    test_main.py que mockean psycopg2.connect reciben esa conexion real del
    pool. Aca solo importa si el middleware deja pasar o no el pedido."""
    def _sin_base(*args, **kwargs):
        raise main.psycopg2.OperationalError("base deshabilitada en test_auth")

    monkeypatch.setattr(main.psycopg2, "connect", _sin_base)
    monkeypatch.setattr(main, "_pool_conexiones", main._PoolConexiones())


@pytest.fixture
def client():
    # base_url en https: la cookie de sesion se marca Secure (asi debe
    # ser, se expone por Tailscale Funnel siempre en https), y un
    # cliente de pruebas en http no la reenviaria de vuelta.
    return TestClient(main.app, base_url="https://testserver")


def test_endpoint_protegido_sin_sesion_devuelve_401(client):
    respuesta = client.get("/metrics")
    assert respuesta.status_code == 401


def test_health_no_requiere_sesion(client):
    respuesta = client.get("/health")
    assert respuesta.status_code != 401


def test_login_con_contrasena_incorrecta_falla(client):
    respuesta = client.post(
        "/auth/login",
        json={"username": os.environ["AUTH_USERNAME"], "password": "incorrecta"},
    )
    assert respuesta.status_code == 401


def test_login_correcto_habilita_endpoints_protegidos(client):
    respuesta = client.post(
        "/auth/login",
        json={"username": os.environ["AUTH_USERNAME"], "password": CONTRASENA_TEST},
    )
    assert respuesta.status_code == 200
    assert "motosafe_session" in respuesta.cookies

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["usuario"] == os.environ["AUTH_USERNAME"]

    metricas = client.get("/metrics")
    assert metricas.status_code != 401


def test_logout_invalida_la_sesion(client):
    client.post(
        "/auth/login",
        json={"username": os.environ["AUTH_USERNAME"], "password": CONTRASENA_TEST},
    )
    client.post("/auth/logout")
    respuesta = client.get("/auth/me")
    assert respuesta.status_code == 401


def test_bloqueo_tras_varios_intentos_fallidos(client):
    for _ in range(5):
        client.post(
            "/auth/login",
            json={"username": os.environ["AUTH_USERNAME"], "password": "mal"},
        )
    respuesta = client.post(
        "/auth/login",
        json={"username": os.environ["AUTH_USERNAME"], "password": CONTRASENA_TEST},
    )
    assert respuesta.status_code == 429
