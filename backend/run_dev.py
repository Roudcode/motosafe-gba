"""Arranque de desarrollo del backend, equivalente a:
    uvicorn main:app --reload --reload-exclude "venv/*"
pero sin pasar el "*" por la linea de comandos de Windows, donde el
lanzador de uvicorn.exe lo expande como wildcard de archivos incluso
entre comillas (bug del launcher de pip en Windows) y rompe el arranque.

proxy_headers=True + forwarded_allow_ips=127.0.0.1: el backend solo recibe
trafico del proxy de Vite (ver frontend/vite.config.js), que corre en la
misma maquina. Con esto, uvicorn confia en los headers X-Forwarded-Proto /
X-Forwarded-For que ponga ese proxy -- pero solo si el pedido entro desde
127.0.0.1, nunca de otro origen -- y request.url.scheme queda "https" como
corresponde cuando el acceso real es por Tailscale Funnel.

A22 (SES-105): reload=True hace que uvicorn arranque el proceso que de verdad
sirve pedidos como un hijo nuevo (multiprocessing, contexto "spawn"), no en
este mismo proceso. En Windows, ese contexto resuelve el interprete a usar
por su cuenta y no siempre coincide con el que ya esta corriendo este script
-- si _iniciar_backend.bat activo venv312 pero algo mas (un IDE, una terminal
vieja, un acceso directo) dejo "python" apuntando al interprete del sistema
antes de llegar aca, el proceso padre arranca bien con venv312 pero el hijo
que de verdad atiende pedidos puede terminar en el Python de sistema, sin que
nada lo avise: mismo puerto, misma pinta, pero sin las versiones fijadas que
garantiza requirements.lock (ver docs/operacion/ENTORNO_REPRODUCIBLE.md). Dos
guardas para que esto falle fuerte en vez de quedar en silencio:
1) multiprocessing.set_executable fija explicitamente el interprete que va a
   usar cualquier hijo que este proceso spawee, en vez de dejar que Windows lo
   vuelva a resolver por su cuenta.
2) _verificar_interprete_venv confirma, antes de arrancar, que el proceso
   actual corre con el Python de venv312 (al lado de este archivo) y no con
   otro -- si no, corta con un mensaje claro en vez de levantar el backend
   contra un entorno sin fijar.
"""
import multiprocessing
import sys
from pathlib import Path

import uvicorn


def _python_venv312_esperado():
    base = Path(__file__).resolve().parent / "venv312"
    scripts = base / "Scripts" / "python.exe"  # Windows
    posix = base / "bin" / "python"  # por si alguna vez se usa fuera de Windows
    return scripts if scripts.exists() else posix


def _verificar_interprete_venv():
    esperado = _python_venv312_esperado()
    actual = Path(sys.executable).resolve()
    if not esperado.exists():
        print(f"AVISO: no se encontro venv312 en {esperado.parent.parent} -- "
              f"se sigue sin verificar el interprete.", file=sys.stderr)
        return
    if actual != esperado.resolve():
        sys.exit(
            "Este backend de desarrollo tiene que correr con el Python de venv312, "
            f"no con {actual}.\nUsa _iniciar_backend.bat (activa venv312 antes de "
            "llamar a este script), no 'python run_dev.py' suelto desde otra terminal "
            "o IDE con otro interprete configurado."
        )


if __name__ == "__main__":
    _verificar_interprete_venv()
    multiprocessing.set_executable(sys.executable)
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=["venv/*"],
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1",
    )
