"""Config compartida de pytest.

Desde que el backend exige sesion para todo lo que no sea /health o
/auth/* (ver auth.py), los tests existentes -- que pegan directo a los
endpoints, no es eso lo que estan probando -- necesitan dos cosas antes de
que se importe main.py:

1. Las variables de entorno que auth.py exige al importarse (si no estan,
   tira RuntimeError y ningun test puede correr).
2. Una sesion "siempre valida" durante los tests, para no tener que hacer
   login en cada uno.
"""
import os
import secrets

os.environ.setdefault("AUTH_USERNAME", "test")
os.environ.setdefault("SESSION_SECRET", secrets.token_hex(32))

import bcrypt  # noqa: E402

os.environ.setdefault(
    "AUTH_PASSWORD_HASH",
    bcrypt.hashpw(b"clave-de-test-no-usar-en-produccion", bcrypt.gensalt()).decode("utf-8"),
)

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _sesion_siempre_valida(monkeypatch):
    import auth

    monkeypatch.setattr(auth, "sesion_valida", lambda request: True)
