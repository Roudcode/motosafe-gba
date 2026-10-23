"""Pruebas de auth.py que NO necesitan una base de datos real.

F11 (SES-165): el login ahora busca el usuario en la tabla `usuarios` real
(ver auth.py) -- a diferencia del mecanismo viejo (un usuario fijo por
variable de entorno), hasta un login con credenciales inventadas necesita
que esa tabla exista de verdad (si no, psycopg2 tira "relation does not
exist", no un 401 limpio). Por eso TODO lo que llama a /auth/login,
/auth/registro o cualquier otro endpoint que toque la tabla usuarios vive en
test_integracion_postgres.py (gateado por MOTOSAFE_TEST_DATABASE_URL, con
una base desechable ya migrada) -- nunca acá. Lo que queda en este archivo es
justamente lo que no depende de eso: login deshabilitado (AUTH_HABILITADO=
false, ni siquiera llega a tocar la base) y el middleware de sesión sobre
endpoints que no son de auth.

A diferencia del resto de la suite, estos tests NO quieren el bypass
global de conftest.py (sesion_valida siempre True) -- es justamente el
circuito de autenticacion lo que se esta probando aca.
"""
import os

import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(autouse=True)
def _sesion_siempre_valida():
    """Anula, solo en este archivo, el bypass autouse de conftest.py."""
    yield


@pytest.fixture(autouse=True)
def _sin_base_real(monkeypatch):
    """/health y /metrics tocan la base. Sin esto, si Postgres esta levantado,
    dejan conexiones reales en main._pool_conexiones y los tests de
    test_main.py que mockean psycopg2.connect reciben esa conexion real del
    pool. Aca solo importa si el middleware deja pasar o no el pedido -- los
    tests de este archivo no llaman a ningun endpoint de auth.py que toque
    la base (esos viven en test_integracion_postgres.py)."""
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


def _correr_sin_auth(codigo):
    """Importa main en un proceso nuevo, sin AUTH_*/SESSION_SECRET: auth.py
    lee las variables al importarse y en este proceso ya quedo importado con
    las de conftest.py."""
    import subprocess
    import sys

    entorno = {k: v for k, v in os.environ.items() if not k.startswith(("AUTH_", "SESSION_"))}
    # Vacias y no ausentes: main.py llama a load_dotenv(), que completaria las
    # ausentes con un backend/.env local; dotenv no pisa variables existentes.
    entorno.update(AUTH_USERNAME="", AUTH_PASSWORD_HASH="", SESSION_SECRET="")
    entorno["AUTH_HABILITADO"] = "false"
    # Sin base: los endpoints probados no la necesitan para decidir el 401/404.
    entorno["DATABASE_URL"] = "postgresql://nadie:nada@127.0.0.1:1/ninguna"
    return subprocess.run(
        [sys.executable, "-W", "ignore", "-c", codigo],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=entorno, capture_output=True, text=True, timeout=120,
    )


def test_sin_login_la_app_arranca_sin_variables_de_auth_y_no_exige_sesion():
    resultado = _correr_sin_auth(
        "from fastapi.testclient import TestClient\n"
        "import main\n"
        "c = TestClient(main.app)\n"
        "print(c.get('/auth/me').json())\n"
        "print(c.get('/').status_code)\n"
        "print(c.post('/auth/login', json={'email': 'x@x.com', 'password': 'y'}).status_code)\n"
        "print(c.post('/auth/registro', json={'email': 'x@x.com', 'nombre_usuario': 'x', 'password': 'y'}).status_code)\n"
    )
    assert resultado.returncode == 0, resultado.stderr
    me, raiz, login, registro = resultado.stdout.strip().splitlines()[-4:]
    assert me == "{'usuario': None, 'auth_habilitado': False}"
    assert raiz == "200"
    assert login == "404"
    assert registro == "404"


def test_con_login_activado_por_defecto_faltan_variables_y_no_arranca():
    # F11 (SES-165): ya no hace falta AUTH_USERNAME/AUTH_PASSWORD_HASH (el
    # login ahora busca en la tabla usuarios) -- lo que sigue siendo
    # obligatorio con AUTH_HABILITADO por defecto es SESSION_SECRET.
    resultado = _correr_sin_auth("import os; os.environ.pop('AUTH_HABILITADO'); import main")
    assert resultado.returncode != 0
    assert "SESSION_SECRET" in resultado.stderr
