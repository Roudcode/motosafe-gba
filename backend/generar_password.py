"""Genera el AUTH_PASSWORD_HASH para pegar en el .env.

No guarda ni envia la contrasena a ningun lado: pide una contrasena por
consola, calcula su hash con bcrypt (que ya incluye una salt aleatoria
propia por hash) y lo imprime en pantalla. El valor impreso es lo unico
que va al .env -- la contrasena en texto plano no queda guardada en
ningun archivo.

Uso (parado en la carpeta backend, con el venv activado):
    python generar_password.py
"""
import getpass

import bcrypt


def main() -> None:
    password = getpass.getpass("Elegi la contrasena para entrar a MotoSafe GBA: ")
    confirmacion = getpass.getpass("Repetila: ")
    if password != confirmacion:
        print("No coinciden. Corre el script de nuevo.")
        return
    if len(password) < 4:
        print("Usa al menos 4 caracteres.")
        return
    if len(password.encode("utf-8")) > 72:
        print("Demasiado larga (bcrypt limita a 72 bytes). Usa una mas corta.")
        return
    hash_generado = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    print("\nListo. Pega estas dos lineas en tu .env (backend/.env):\n")
    print(f"AUTH_USERNAME=rodo")
    print(f"AUTH_PASSWORD_HASH={hash_generado}")
    print("\n(podes cambiar 'rodo' por el usuario que quieras)")


if __name__ == "__main__":
    main()
