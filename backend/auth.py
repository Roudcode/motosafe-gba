"""Autenticacion por sesion para cuando la app queda expuesta a internet
(Tailscale Funnel). Pensada para un solo usuario (uso personal): el
usuario y el hash de la contrasena viven en variables de entorno, nunca
en el repo ni en la base de datos -- no hace falta una tabla ni
migraciones para esto.

La sesion es una cookie firmada (HMAC via itsdangerous), no un token en
base: el servidor no guarda estado de sesion en ningun lado, solo verifica
la firma y el vencimiento de lo que ya vino en la cookie. HttpOnly +
Secure + SameSite=Lax evitan que JavaScript del lado del cliente la lea y
que viaje en pedidos cross-site.
"""
import os
import threading
import time

import bcrypt
from fastapi import APIRouter, HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

# El login protege el acceso personal por Tailscale Funnel. El MVP publico
# (docker-compose.production.yml, render.yaml) corre sin login y lo apaga con
# AUTH_HABILITADO=false. Por defecto queda ACTIVADO: si en el .env local falta
# esta variable, la app expuesta por Funnel no queda abierta sin querer.
_VALORES_FALSOS = {"0", "false", "no", "off"}
AUTH_HABILITADO = os.getenv("AUTH_HABILITADO", "true").strip().lower() not in _VALORES_FALSOS

AUTH_USERNAME = os.getenv("AUTH_USERNAME", "").strip()
AUTH_PASSWORD_HASH = os.getenv("AUTH_PASSWORD_HASH", "").strip()
SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
SESSION_COOKIE_NAME = "motosafe_session"
SESSION_MAX_AGE_SECONDS = int(os.getenv("SESSION_MAX_AGE_HOURS", "12")) * 3600

if AUTH_HABILITADO and (not AUTH_USERNAME or not AUTH_PASSWORD_HASH):
    raise RuntimeError(
        "Falta AUTH_USERNAME y/o AUTH_PASSWORD_HASH en el .env. Corre "
        "'python generar_password.py' en la carpeta backend para crearlos "
        "antes de levantar el servidor (o AUTH_HABILITADO=false si es un "
        "despliegue publico sin login)."
    )
if AUTH_HABILITADO and not SESSION_SECRET:
    raise RuntimeError(
        "Falta SESSION_SECRET en el .env. Genera uno con: "
        "python -c \"import secrets; print(secrets.token_hex(32))\" "
        "y pegalo en el .env."
    )

# Sin login no se firma ninguna cookie.
_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="motosafe-session") if AUTH_HABILITADO else None


def _verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except ValueError:
        # Hash guardado con formato invalido/corrupto en el .env.
        return False

router = APIRouter()

# --- Limitador de intentos de login, en memoria -----------------------------
# Un solo usuario real, asi que no hace falta nada mas sofisticado que esto:
# por IP, si hay 5 intentos fallidos en 60 segundos, se bloquea esa IP por el
# resto de esa ventana. Se reinicia el conteo apenas hay un login correcto.
MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 60
_intentos_fallidos: dict[str, list[float]] = {}
_lock_intentos = threading.Lock()


def _ip_bloqueada(ip: str) -> bool:
    ahora = time.time()
    with _lock_intentos:
        vigentes = [t for t in _intentos_fallidos.get(ip, []) if ahora - t < VENTANA_SEGUNDOS]
        _intentos_fallidos[ip] = vigentes
        return len(vigentes) >= MAX_INTENTOS


def _registrar_intento_fallido(ip: str) -> None:
    with _lock_intentos:
        _intentos_fallidos.setdefault(ip, []).append(time.time())


def _limpiar_intentos(ip: str) -> None:
    with _lock_intentos:
        _intentos_fallidos.pop(ip, None)


class LoginBody(BaseModel):
    username: str
    password: str


def _crear_cookie_sesion(response: Response) -> None:
    token = _serializer.dumps({"usuario": AUTH_USERNAME})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


def sesion_valida(request: Request) -> bool:
    if not AUTH_HABILITADO:
        return True
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return False
    try:
        _serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return False
    return True


@router.post("/auth/login")
def login(body: LoginBody, request: Request, response: Response):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login deshabilitado")
    ip = request.client.host if request.client else "desconocida"
    if _ip_bloqueada(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Esperá un minuto y volvé a intentar.",
        )
    if body.username != AUTH_USERNAME or not _verificar_password(body.password, AUTH_PASSWORD_HASH):
        _registrar_intento_fallido(ip)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")
    _limpiar_intentos(ip)
    _crear_cookie_sesion(response)
    return {"ok": True}


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"ok": True}


@router.get("/auth/me")
def me(request: Request):
    # auth_habilitado le dice al frontend si tiene que mostrar login y "Salir".
    if not AUTH_HABILITADO:
        return {"usuario": None, "auth_habilitado": False}
    if not sesion_valida(request):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    return {"usuario": AUTH_USERNAME, "auth_habilitado": True}
