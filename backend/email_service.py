"""Envio de mails reales para el sistema de usuarios: codigo de verificacion
al registrarse y codigo de reseteo de contrasena. Texto plano, sin plantillas
HTML -- un codigo de 6 digitos no necesita diseno.

SES-169: manda por la API HTTP de Gmail (OAuth2, refresh token de larga
duracion), no por SMTP -- Render bloquea el trafico saliente a los puertos
SMTP (25/465/587) en el plan gratis desde sep/2025, y Gmail API usa HTTPS
normal (443), que no esta bloqueado. La cuenta sigue siendo la dedicada
motosafe.noreply@gmail.com; GMAIL_CLIENT_ID/GMAIL_CLIENT_SECRET/
GMAIL_REFRESH_TOKEN se generaron una sola vez con un proyecto de Google Cloud
(scope gmail.send) y un flujo OAuth local -- ver SES-169 en BITACORA.md para
el procedimiento completo si hay que regenerarlos (p.ej. si se revoca el
acceso).

Si las credenciales no estan en el .env, el backend arranca igual (no rompe
el arranque), pero mandar un mail real falla con un error claro en el log --
nunca en silencio. Para desarrollo o despliegues sin esas variables,
enviar_codigo imprime el codigo por consola como fallback (ver
_FALLBACK_CONSOLA), para no bloquear el resto del flujo mientras no esten
configuradas.
"""
import base64
import logging
import os
from email.message import EmailMessage

import httpx

logger = logging.getLogger("motosafe.email")

GMAIL_CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "").strip()
GMAIL_CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "").strip()
GMAIL_REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN", "").strip()
# Remitente real: la cuenta dedicada que autorizo el refresh token de arriba.
GMAIL_REMITENTE = os.getenv("GMAIL_REMITENTE", "motosafe.noreply@gmail.com").strip()

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_ENVIAR_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"

_ASUNTOS = {
    "verificacion": "Tu código de verificación de MotoSafe GBA",
    "reset_password": "Tu código para restablecer tu contraseña de MotoSafe GBA",
}

_CUERPOS = {
    "verificacion": (
        "Tu código de verificación de MotoSafe GBA es: {codigo}\n\n"
        "Vence en 15 minutos. Si no creaste una cuenta en MotoSafe GBA, podés "
        "ignorar este mensaje.\n"
    ),
    "reset_password": (
        "Tu código para restablecer tu contraseña de MotoSafe GBA es: {codigo}\n\n"
        "Vence en 15 minutos. Si no pediste restablecer tu contraseña, podés "
        "ignorar este mensaje -- tu contraseña actual sigue siendo válida.\n"
    ),
}


class ErrorEnvioMail(Exception):
    """El mail no se pudo mandar de verdad (credenciales sin configurar o falla real)."""


def _fallback_consola(destinatario: str, tipo: str, codigo: str) -> None:
    logger.warning(
        "GMAIL_CLIENT_ID/SECRET/REFRESH_TOKEN no configuradas -- no se mandó mail real. "
        "Código de %s para %s (solo consola, desarrollo): %s",
        tipo, destinatario, codigo,
    )


def _obtener_access_token() -> str:
    respuesta = httpx.post(
        _TOKEN_URL,
        data={
            "client_id": GMAIL_CLIENT_ID,
            "client_secret": GMAIL_CLIENT_SECRET,
            "refresh_token": GMAIL_REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    respuesta.raise_for_status()
    return respuesta.json()["access_token"]


def _armar_mensaje_codificado(destinatario: str, tipo: str, codigo: str) -> str:
    mensaje = EmailMessage()
    mensaje["Subject"] = _ASUNTOS[tipo]
    mensaje["From"] = GMAIL_REMITENTE
    mensaje["To"] = destinatario
    mensaje.set_content(_CUERPOS[tipo].format(codigo=codigo))
    return base64.urlsafe_b64encode(mensaje.as_bytes()).decode("ascii")


def enviar_codigo(destinatario: str, tipo: str, codigo: str) -> bool:
    """Manda el mail real por la Gmail API. Si falta configuración, cae al
    fallback de consola (no bloquea el flujo) pero deja bien claro en el log
    que no se mandó nada de verdad -- y se lo dice también a quien llamó esta
    función (H13, assessment 2026-10-22: antes el fallback devolvía
    silenciosamente como si hubiera mandado el mail). Devuelve True solo si
    de verdad se mandó; False si usó el fallback de consola (no es un error:
    nunca se levanta ErrorEnvioMail por falta de configuración, solo por una
    falla real con credenciales ya configuradas)."""
    if tipo not in _ASUNTOS:
        raise ValueError(f"Tipo de código desconocido: {tipo}")

    if not (GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN):
        _fallback_consola(destinatario, tipo, codigo)
        return False

    try:
        access_token = _obtener_access_token()
        crudo = _armar_mensaje_codificado(destinatario, tipo, codigo)
        respuesta = httpx.post(
            _ENVIAR_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            json={"raw": crudo},
            timeout=10,
        )
        respuesta.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("Falló el envío real de mail (%s) a %s: %s", tipo, destinatario, exc)
        raise ErrorEnvioMail(f"No se pudo enviar el mail de {tipo}") from exc
    return True
