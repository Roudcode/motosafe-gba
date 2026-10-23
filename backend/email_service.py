"""Envio de mails reales por Gmail SMTP (cuenta dedicada, no personal) para
el sistema de usuarios: codigo de verificacion al registrarse y codigo de
reseteo de contrasena. Texto plano, sin plantillas HTML -- un codigo de 6
digitos no necesita diseno.

Si SMTP_USER/SMTP_PASSWORD no estan puestas en el .env, el backend arranca
igual (no rompe el arranque), pero mandar un mail real falla con un error
claro en el log -- nunca en silencio. Para desarrollo local sin esas
variables, enviar_codigo imprime el codigo por consola como fallback (ver
_FALLBACK_CONSOLA), para no bloquear el resto del flujo mientras no esten
configuradas.
"""
import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("motosafe.email")

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "").strip()
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "").strip()

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
    """El mail no se pudo mandar de verdad (SMTP sin configurar o falla real)."""


def _fallback_consola(destinatario: str, tipo: str, codigo: str) -> None:
    logger.warning(
        "SMTP_USER/SMTP_PASSWORD no configuradas -- no se mandó mail real. "
        "Código de %s para %s (solo consola, desarrollo): %s",
        tipo, destinatario, codigo,
    )


def enviar_codigo(destinatario: str, tipo: str, codigo: str) -> bool:
    """Manda el mail real. Si falta configuración SMTP, cae al fallback de
    consola (no bloquea el flujo) pero deja bien claro en el log que no se
    mandó nada de verdad -- y se lo dice también a quien llamó esta función
    (H13, assessment 2026-10-22: antes el fallback devolvía silenciosamente
    como si hubiera mandado el mail, y el registro respondía `mail_enviado:
    true` sin haber mandado nada real). Devuelve True solo si de verdad se
    mandó por SMTP; False si usó el fallback de consola (no es un error:
    nunca se levanta ErrorEnvioMail por falta de configuración, solo por una
    falla real de un SMTP ya configurado)."""
    if tipo not in _ASUNTOS:
        raise ValueError(f"Tipo de código desconocido: {tipo}")

    if not SMTP_USER or not SMTP_PASSWORD:
        _fallback_consola(destinatario, tipo, codigo)
        return False

    mensaje = EmailMessage()
    mensaje["Subject"] = _ASUNTOS[tipo]
    mensaje["From"] = SMTP_USER
    mensaje["To"] = destinatario
    mensaje.set_content(_CUERPOS[tipo].format(codigo=codigo))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as servidor:
            servidor.starttls()
            servidor.login(SMTP_USER, SMTP_PASSWORD)
            servidor.send_message(mensaje)
    except Exception as exc:  # noqa: BLE001 -- se relanza con contexto, no se traga
        logger.error("Falló el envío real de mail (%s) a %s: %s", tipo, destinatario, exc)
        raise ErrorEnvioMail(f"No se pudo enviar el mail de {tipo}") from exc
    return True
