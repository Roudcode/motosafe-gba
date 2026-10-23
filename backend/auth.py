"""Autenticacion por sesion para cuando la app queda expuesta a internet
(Tailscale Funnel).

F11 (SES-165): dejo de ser un unico usuario fijo por variables de entorno.
Ahora hay una tabla `usuarios` real (email + password_hash con bcrypt +
email_verificado) y una tabla `codigos_auth` para los codigos de 6 digitos
de verificacion de cuenta y reseteo de contrasena (ver
migrations/005_usuarios.sql). El usuario viejo del .env
(AUTH_USERNAME/AUTH_PASSWORD_HASH) no se migro a la tabla nueva a proposito:
"rodo" es un nombre de usuario, no un email real, asi que no hay ninguna
casilla de correo legitima con la que migrarlo con integridad -- inventar una
(rodo@local, por ejemplo) crearia una cuenta fantasma sin un camino real de
reseteo de contrasena. Lo mas limpio es que Rodo se registre de cero con su
email real por el flujo nuevo, con una cuenta verdaderamente verificada desde
el dia uno. AUTH_USERNAME/AUTH_PASSWORD_HASH quedan sin usar por /auth/login
(que ahora busca en la tabla `usuarios`), pero no se borraron del .env ni se
rompio `generar_password.py` -- no hace falta para este cambio y podria servir
de referencia.

La sesion sigue siendo una cookie firmada (HMAC via itsdangerous), no un
token en base: el servidor no guarda estado de sesion en ningun lado, solo
verifica la firma y el vencimiento de lo que ya vino en la cookie. Lo unico
que cambio en el payload es que antes era {"usuario": AUTH_USERNAME} (fijo)
y ahora es {"usuario_id": <id real de la tabla usuarios>}. HttpOnly + Secure
+ SameSite=Lax siguen igual.
"""
import logging
import os
import re
import secrets
import threading
import time
from datetime import datetime, timedelta, timezone

import bcrypt
import psycopg2
from fastapi import APIRouter, HTTPException, Request, Response, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from pydantic import BaseModel

import email_service

logger = logging.getLogger("motosafe.auth")

# El login protege el acceso personal por Tailscale Funnel. El MVP publico
# (docker-compose.production.yml, render.yaml) corre sin login y lo apaga con
# AUTH_HABILITADO=false. Por defecto queda ACTIVADO: si en el .env local falta
# esta variable, la app expuesta por Funnel no queda abierta sin querer.
_VALORES_FALSOS = {"0", "false", "no", "off"}
AUTH_HABILITADO = os.getenv("AUTH_HABILITADO", "true").strip().lower() not in _VALORES_FALSOS

SESSION_SECRET = os.getenv("SESSION_SECRET", "").strip()
SESSION_COOKIE_NAME = "motosafe_session"
SESSION_MAX_AGE_SECONDS = int(os.getenv("SESSION_MAX_AGE_HOURS", "12")) * 3600
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if AUTH_HABILITADO and not SESSION_SECRET:
    raise RuntimeError(
        "Falta SESSION_SECRET en el .env. Genera uno con: "
        "python -c \"import secrets; print(secrets.token_hex(32))\" "
        "y pegalo en el .env."
    )
# DATABASE_URL NO se exige al importar (a diferencia de SESSION_SECRET): el
# job de CI "backend-sintaxis" corre toda la suite sin ninguna base
# levantada (ver .github/workflows/ci.yml, "tests sin base de datos") -- los
# endpoints que de verdad necesitan la tabla usuarios fallan recien al
# llamarse, con el error real de psycopg2, no al importar el modulo.

# Sin login no se firma ninguna cookie.
_serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="motosafe-session") if AUTH_HABILITADO else None

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LONGITUD_MINIMA_PASSWORD = 8
CODIGO_VIGENCIA_MINUTOS = 15
MAX_INTENTOS_CODIGO = 5


def _conn():
    return psycopg2.connect(DATABASE_URL)


def _normalizar_email(email: str) -> str:
    return email.strip().lower()


def _validar_email(email: str) -> str:
    email = _normalizar_email(email)
    if not EMAIL_REGEX.match(email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email inválido.")
    return email


LONGITUD_MINIMA_NOMBRE_USUARIO = 2
LONGITUD_MAXIMA_NOMBRE_USUARIO = 50


def _validar_nombre_usuario(nombre: str) -> str:
    nombre = nombre.strip()
    if not (LONGITUD_MINIMA_NOMBRE_USUARIO <= len(nombre) <= LONGITUD_MAXIMA_NOMBRE_USUARIO):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El nombre de usuario tiene que tener entre {LONGITUD_MINIMA_NOMBRE_USUARIO} y {LONGITUD_MAXIMA_NOMBRE_USUARIO} caracteres.",
        )
    return nombre


def _validar_password(password: str) -> None:
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La contraseña tiene que tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres.",
        )


def _hashear_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verificar_password(password: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hash_guardado.encode("utf-8"))
    except ValueError:
        return False


def _generar_codigo() -> str:
    # H04 (assessment 2026-10-22, SES-168): random.randint no es criptografico
    # -- un codigo de acceso tiene que generarse con secrets (CSPRNG).
    return f"{secrets.randbelow(1_000_000):06d}"


def _crear_codigo(cur, usuario_id: int, tipo: str) -> str:
    # H04 (assessment 2026-10-22, SES-168): un codigo anterior sin usar seguia
    # valido despues de pedir uno nuevo (reenviar-codigo/olvide-password) --
    # quien tuviera el mail viejo podia usarlo igual mientras no venciera.
    # Invalidarlo (marcarlo usado, no borrarlo, para no perder el registro de
    # intentos) antes de insertar el nuevo deja uno solo vigente por usuario y
    # tipo.
    cur.execute(
        """UPDATE codigos_auth SET usado_en = now()
           WHERE usuario_id = %s AND tipo = %s AND usado_en IS NULL""",
        (usuario_id, tipo),
    )
    codigo = _generar_codigo()
    expira = datetime.now(timezone.utc) + timedelta(minutes=CODIGO_VIGENCIA_MINUTOS)
    cur.execute(
        "INSERT INTO codigos_auth (usuario_id, codigo, tipo, expira_en) VALUES (%s, %s, %s, %s)",
        (usuario_id, codigo, tipo, expira),
    )
    return codigo


def _codigo_vigente(cur, usuario_id: int, tipo: str):
    """Devuelve (id, codigo, expira_en, intentos_fallidos) del codigo mas
    reciente sin usar de ese tipo, o None si no hay ninguno. FOR UPDATE (H04,
    assessment 2026-10-22, SES-168): sin el lock, dos pedidos concurrentes con
    el mismo codigo correcto podian leer la fila "sin usar" los dos antes de
    que cualquiera la marcara usada, y los dos pasaban. Con el lock, el
    segundo espera el commit del primero y ya la encuentra usada."""
    cur.execute(
        """SELECT id, codigo, expira_en, intentos_fallidos FROM codigos_auth
           WHERE usuario_id = %s AND tipo = %s AND usado_en IS NULL
           ORDER BY creado_en DESC LIMIT 1 FOR UPDATE""",
        (usuario_id, tipo),
    )
    return cur.fetchone()


router = APIRouter()

# --- Limitador de intentos por IP, en memoria -------------------------------
# Generalizado (SES-165) para que lo use login y, con el mismo patron, el
# reenvio de codigo y el pedido de reset -- por accion, para que agotar el
# limite de una no bloquee a las otras. Mismo criterio de antes: 5 intentos en
# 60 segundos por (ip, accion).
MAX_INTENTOS = 5
VENTANA_SEGUNDOS = 60
_intentos_fallidos: dict[str, list[float]] = {}
_lock_intentos = threading.Lock()


def _clave_limite(ip: str, accion: str) -> str:
    return f"{accion}:{ip}"


def _ip_bloqueada(ip: str, accion: str = "login") -> bool:
    clave = _clave_limite(ip, accion)
    ahora = time.time()
    with _lock_intentos:
        vigentes = [t for t in _intentos_fallidos.get(clave, []) if ahora - t < VENTANA_SEGUNDOS]
        _intentos_fallidos[clave] = vigentes
        return len(vigentes) >= MAX_INTENTOS


def _registrar_intento_fallido(ip: str, accion: str = "login") -> None:
    with _lock_intentos:
        _intentos_fallidos.setdefault(_clave_limite(ip, accion), []).append(time.time())


def _limpiar_intentos(ip: str, accion: str = "login") -> None:
    with _lock_intentos:
        _intentos_fallidos.pop(_clave_limite(ip, accion), None)


def _ip_de(request: Request) -> str:
    return request.client.host if request.client else "desconocida"


def _rechazar_si_bloqueada(request: Request, accion: str) -> None:
    if _ip_bloqueada(_ip_de(request), accion):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos. Esperá un minuto y volvé a intentar.",
        )


class LoginBody(BaseModel):
    # El campo se sigue llamando "email" por compatibilidad con el frontend y
    # los tests existentes, pero desde SES-169 también acepta el nombre de
    # usuario -- login() prueba ambos contra la misma fila (ver más abajo).
    email: str
    password: str


class RegistroBody(BaseModel):
    email: str
    password: str
    nombre_usuario: str


class VerificarCodigoBody(BaseModel):
    email: str
    codigo: str


class ReenviarCodigoBody(BaseModel):
    email: str


class OlvidePasswordBody(BaseModel):
    email: str


class ResetearPasswordBody(BaseModel):
    email: str
    codigo: str
    password_nueva: str


def _crear_cookie_sesion(response: Response, usuario_id: int, sesion_version: int) -> None:
    # H05 (assessment 2026-10-22, SES-168): la cookie lleva la version de
    # sesion vigente al momento de loguearse, para poder revocarla despues
    # (ver _usuario_id_de_sesion y resetear_password).
    token = _serializer.dumps({"usuario_id": usuario_id, "sesion_version": sesion_version})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_MAX_AGE_SECONDS,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


def _usuario_id_de_sesion(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None
    try:
        datos = _serializer.loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None
    usuario_id = datos.get("usuario_id")
    sesion_version = datos.get("sesion_version")
    if usuario_id is None or sesion_version is None:
        # Cookie de antes de H05 (sin version): no hay con que compararla, se
        # trata como invalida en vez de confiar ciegamente en la firma.
        return None

    # H05 (assessment 2026-10-22, SES-168): antes la cookie firmada alcanzaba
    # por si sola -- cambiar la contraseña (o un futuro "cerrar sesion en
    # todos lados") no invalidaba las que ya estaban circulando, porque nunca
    # se comparaban contra nada en la base. Esta consulta por pedido tiene un
    # costo (un round-trip extra a la base en cada endpoint protegido), pero
    # es el precio de que la revocacion sea real y no solo hasta que venza el
    # Max-Age de 12hs.
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT sesion_version FROM usuarios WHERE id = %s", (usuario_id,))
        fila = cur.fetchone()
    if not fila or fila[0] != sesion_version:
        return None
    return usuario_id


def sesion_valida(request: Request) -> bool:
    if not AUTH_HABILITADO:
        return True
    return _usuario_id_de_sesion(request) is not None


@router.post("/auth/registro", status_code=status.HTTP_201_CREATED)
def registro(body: RegistroBody, request: Request):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Registro deshabilitado")
    # H07 (assessment 2026-10-22, SES-168): no tenia ningun limite -- a
    # diferencia de login/reenviar/olvide/resetear, que ya lo usaban desde
    # F11. Cuenta cada pedido (no solo los que terminan en 409), mismo
    # criterio que reenviar-codigo/olvide-password: lo que hay que frenar acá
    # es el volumen de cuentas/mails que se pueden generar por IP, no
    # distinguir intentos "legitimos" de otros.
    _rechazar_si_bloqueada(request, "registro")
    _registrar_intento_fallido(_ip_de(request), "registro")
    email = _validar_email(body.email)
    _validar_password(body.password)
    nombre_usuario = _validar_nombre_usuario(body.nombre_usuario)
    password_hash = _hashear_password(body.password)

    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese email ya está registrado.")
        cur.execute("SELECT id FROM usuarios WHERE nombre_usuario = %s", (nombre_usuario,))
        if cur.fetchone():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ese nombre de usuario ya está en uso.")
        cur.execute(
            "INSERT INTO usuarios (email, password_hash, nombre_usuario, email_verificado) VALUES (%s, %s, %s, false) RETURNING id",
            (email, password_hash, nombre_usuario),
        )
        usuario_id = cur.fetchone()[0]
        codigo = _crear_codigo(cur, usuario_id, "verificacion")
        conn.commit()

    # H13 (assessment 2026-10-22, SES-168): enviar_codigo ahora devuelve si
    # de verdad mando el mail por SMTP (True) o cayo al fallback de consola
    # (False) -- antes, el fallback no levantaba excepcion y esta funcion
    # respondia `mail_enviado: true` sin haber mandado nada real.
    try:
        mail_enviado = email_service.enviar_codigo(email, "verificacion", codigo)
    except email_service.ErrorEnvioMail:
        # La cuenta ya quedo creada (no se revierte): el usuario puede pedir
        # que se lo reenvien. No se inventa que el mail "se mando" si fallo.
        mail_enviado = False

    return {"ok": True, "mail_enviado": mail_enviado}


@router.post("/auth/login")
def login(body: LoginBody, request: Request, response: Response):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Login deshabilitado")
    _rechazar_si_bloqueada(request, "login")
    # SES-169: el mismo campo ahora sirve para email o nombre de usuario -- el
    # email se compara normalizado (minúsculas, como en registro), el nombre
    # de usuario tal cual se escribió (es case-sensitive desde que se creó,
    # ver _validar_nombre_usuario/índice único de la migración 006).
    identificador = body.email.strip()
    ip = _ip_de(request)

    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT id, password_hash, email_verificado, sesion_version, email FROM usuarios
               WHERE email = %s OR nombre_usuario = %s""",
            (_normalizar_email(identificador), identificador),
        )
        fila = cur.fetchone()

    if not fila or not _verificar_password(body.password, fila[1]):
        _registrar_intento_fallido(ip, "login")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")

    usuario_id, _hash, email_verificado, sesion_version, email_real = fila
    if not email_verificado:
        # Contraseña correcta pero cuenta sin confirmar: no cuenta como intento
        # fallido de fuerza bruta (la credencial era correcta), y el mensaje
        # tiene que decir qué hacer, no ser un 401 generico. X-Email (SES-169):
        # si se logueó con nombre de usuario, el frontend necesita el email
        # real para reenviar-codigo/verificar-codigo (que solo aceptan email).
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirmá tu cuenta con el código que te mandamos a tu correo.",
            headers={"X-Requiere-Verificacion": "true", "X-Email": email_real},
        )

    _limpiar_intentos(ip, "login")
    _crear_cookie_sesion(response, usuario_id, sesion_version)
    return {"ok": True}


@router.post("/auth/verificar-codigo")
def verificar_codigo(body: VerificarCodigoBody):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deshabilitado")
    email = _normalizar_email(body.email)

    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, email_verificado FROM usuarios WHERE email = %s", (email,))
        fila = cur.fetchone()
        if not fila:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido o vencido.")
        usuario_id, ya_verificado = fila
        if ya_verificado:
            return {"ok": True, "ya_verificado": True}

        codigo_fila = _codigo_vigente(cur, usuario_id, "verificacion")
        if not codigo_fila:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido o vencido.")
        codigo_id, codigo_real, expira_en, intentos = codigo_fila

        if intentos >= MAX_INTENTOS_CODIGO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Demasiados intentos. Pedí un código nuevo.")
        if expira_en < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código venció. Pedí uno nuevo.")
        if body.codigo.strip() != codigo_real:
            cur.execute("UPDATE codigos_auth SET intentos_fallidos = intentos_fallidos + 1 WHERE id = %s", (codigo_id,))
            conn.commit()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código incorrecto.")

        cur.execute("UPDATE codigos_auth SET usado_en = now() WHERE id = %s", (codigo_id,))
        cur.execute("UPDATE usuarios SET email_verificado = true WHERE id = %s", (usuario_id,))
        conn.commit()

    return {"ok": True}


@router.post("/auth/reenviar-codigo")
def reenviar_codigo(body: ReenviarCodigoBody, request: Request):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deshabilitado")
    _rechazar_si_bloqueada(request, "reenviar")
    _registrar_intento_fallido(_ip_de(request), "reenviar")  # cuenta cada pedido, no solo los fallidos -- es lo que hay que limitar acá
    email = _normalizar_email(body.email)
    mensaje_generico = {"ok": True, "mensaje": "Si el email está registrado y pendiente de verificar, te mandamos un código nuevo."}

    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, email_verificado FROM usuarios WHERE email = %s", (email,))
        fila = cur.fetchone()
        if not fila or fila[1]:
            return mensaje_generico
        usuario_id = fila[0]
        codigo = _crear_codigo(cur, usuario_id, "verificacion")
        conn.commit()

    try:
        if not email_service.enviar_codigo(email, "verificacion", codigo):
            logger.warning("Reenvío de código de verificación a %s sin SMTP configurado (fallback consola).", email)
    except email_service.ErrorEnvioMail:
        logger.error("No se pudo reenviar el código de verificación a %s", email)

    return mensaje_generico


@router.post("/auth/olvide-password")
def olvide_password(body: OlvidePasswordBody, request: Request):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deshabilitado")
    _rechazar_si_bloqueada(request, "olvide")
    _registrar_intento_fallido(_ip_de(request), "olvide")
    email = _normalizar_email(body.email)
    # Misma respuesta exista o no la cuenta -- no filtra qué emails están registrados.
    mensaje_generico = {"ok": True, "mensaje": "Si el email está registrado, te mandamos un código para restablecer tu contraseña."}

    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        fila = cur.fetchone()
        if not fila:
            return mensaje_generico
        usuario_id = fila[0]
        codigo = _crear_codigo(cur, usuario_id, "reset_password")
        conn.commit()

    try:
        if not email_service.enviar_codigo(email, "reset_password", codigo):
            logger.warning("Código de reseteo para %s sin SMTP configurado (fallback consola).", email)
    except email_service.ErrorEnvioMail:
        logger.error("No se pudo enviar el código de reseteo a %s", email)

    return mensaje_generico


@router.post("/auth/resetear-password")
def resetear_password(body: ResetearPasswordBody, request: Request):
    if not AUTH_HABILITADO:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deshabilitado")
    _rechazar_si_bloqueada(request, "resetear")
    email = _normalizar_email(body.email)
    _validar_password(body.password_nueva)

    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        fila = cur.fetchone()
        if not fila:
            _registrar_intento_fallido(_ip_de(request), "resetear")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido o vencido.")
        usuario_id = fila[0]

        codigo_fila = _codigo_vigente(cur, usuario_id, "reset_password")
        if not codigo_fila:
            _registrar_intento_fallido(_ip_de(request), "resetear")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código inválido o vencido.")
        codigo_id, codigo_real, expira_en, intentos = codigo_fila

        if intentos >= MAX_INTENTOS_CODIGO:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Demasiados intentos. Pedí un código nuevo.")
        if expira_en < datetime.now(timezone.utc):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El código venció. Pedí uno nuevo.")
        if body.codigo.strip() != codigo_real:
            cur.execute("UPDATE codigos_auth SET intentos_fallidos = intentos_fallidos + 1 WHERE id = %s", (codigo_id,))
            conn.commit()
            _registrar_intento_fallido(_ip_de(request), "resetear")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Código incorrecto.")

        nuevo_hash = _hashear_password(body.password_nueva)
        # H05 (assessment 2026-10-22, SES-168): incrementar sesion_version
        # invalida cualquier cookie emitida antes de este reset (ver
        # _usuario_id_de_sesion) -- quien la haya copiado antes de ahora deja
        # de poder usarla, sin esperar a que venza el Max-Age de 12hs.
        cur.execute(
            "UPDATE usuarios SET password_hash = %s, sesion_version = sesion_version + 1 WHERE id = %s",
            (nuevo_hash, usuario_id),
        )
        cur.execute("UPDATE codigos_auth SET usado_en = now() WHERE id = %s", (codigo_id,))
        conn.commit()

    _limpiar_intentos(_ip_de(request), "resetear")
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
    usuario_id = _usuario_id_de_sesion(request)
    if usuario_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    with _conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT email, nombre_usuario FROM usuarios WHERE id = %s", (usuario_id,))
        fila = cur.fetchone()
    if not fila:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    # "usuario" se mantiene como el email (ya lo consumía el resto del código);
    # "nombre_usuario" es el nombre a mostrar (F11, SES-166 -- Rodo pidió esto
    # después de probar el registro real: "que tenga nombre de usuario no solo mail").
    return {"usuario": fila[0], "nombre_usuario": fila[1], "auth_habilitado": True}
