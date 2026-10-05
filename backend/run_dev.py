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
"""
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=["venv/*"],
        proxy_headers=True,
        forwarded_allow_ips="127.0.0.1",
    )
