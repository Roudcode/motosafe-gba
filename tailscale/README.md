# Publicar MotoSafe GBA por Tailscale Funnel

Esquema real de este proyecto (no el genérico de cualquier app):

```
Internet
  -> https://<nombre-pc>.<tailnet>.ts.net   (Tailscale Funnel, TLS real)
  -> https://127.0.0.1:5175                  (vite preview del build de produccion, TLS autofirmado)
       -> /api/*  proxeado internamente a  http://127.0.0.1:8000  (FastAPI)
       -> todo lo demas servido por Vite (la SPA de React)
```

Un solo puerto queda expuesto a internet: **5175**. El backend (8000) nunca
es alcanzable directo desde afuera -- solo Vite le pega, en la misma
máquina. Esto es el mismo patrón que ya usaban con `cloudflared` en
`iniciar_app.bat`, solo que Tailscale Funnel da una URL fija (no cambia en
cada reinicio) en vez de una aleatoria de `trycloudflare.com`.

## Qué cambié en el proyecto

- `backend/auth.py` (nuevo): login/logout por sesión, cookie firmada
  (HttpOnly + Secure + SameSite=Lax), vencimiento configurable, límite de
  intentos de login (5 cada 60s por IP).
- `backend/main.py`: un middleware exige esa cookie para **todo** excepto
  `/health` y `/auth/*`. Protege las 15 rutas existentes sin tocarlas una
  por una.
- `backend/generar_password.py` (nuevo): genera el hash bcrypt de tu
  contraseña para pegar en `.env` -- la contraseña en texto plano no queda
  guardada en ningún lado.
- `backend/run_dev.py`: ahora confía en `X-Forwarded-Proto` solo si el
  pedido viene de 127.0.0.1 (el proxy de Vite).
- `backend/requirements.txt` y `requirements.txt` (raíz): se agregó
  `passlib[bcrypt]` e `itsdangerous`.
- `backend/tests/conftest.py` (nuevo) y `backend/tests/test_auth.py`
  (nuevo): los 67 tests existentes siguen pasando igual (corren con una
  sesión simulada), y se suman 6 tests nuevos que prueban login, logout,
  bloqueo por intentos fallidos y que las rutas protegidas devuelven 401
  sin sesión. **Los 73 tests pasan.**
- `frontend/src/components/LoginGate.jsx` (nuevo) y `frontend/src/main.jsx`:
  pantalla de login antes de mostrar la app; botón "Salir" flotante una vez
  adentro.
- `.env.example` (raíz): documenta las variables nuevas.
- `backend/.env`: ya tiene un `SESSION_SECRET` generado al azar. Faltan
  `AUTH_USERNAME` y `AUTH_PASSWORD_HASH` (ver paso 1 abajo) y `PUBLIC_URL`
  (se completa solo al final, con la URL real).
- `tailscale/` (esta carpeta, nueva): los 6 scripts de control.

## Lo que falta que hagas vos (todo en la PC real, yo no tengo acceso a eso)

### 1. Generar tu contraseña

```
cd backend
venv312\Scripts\activate
pip install -r requirements.txt
python generar_password.py
```

Te va a pedir la contraseña dos veces y te va a imprimir dos líneas
(`AUTH_USERNAME=...` y `AUTH_PASSWORD_HASH=...`). Pegalas en `backend\.env`.

El login está activado por defecto (`AUTH_HABILITADO` ausente o `true`). No
pongas `AUTH_HABILITADO=false` en este `.env`: eso es solo para el MVP público
(`docker-compose.production.yml`, `render.yaml`), y con Funnel dejaría la app
abierta a internet.

### 2. Instalar Tailscale (si no lo tenés)

Descargar de https://tailscale.com/download/windows e iniciar sesión con
tu cuenta.

### 3. Habilitar Funnel para esta PC

Entrar a https://login.tailscale.com/admin/machines , abrir el dispositivo
de esta PC y habilitar **Funnel** (en algunos planes/tailnets es un toggle
directo; en otros hay que agregar el atributo `funnel` en la política de
ACL del tailnet -- la consola te indica cuál es tu caso).

### 4. Levantar todo

```
tailscale\iniciar_app_tailscale.bat
```

Esto corre como `iniciar_app.bat` de siempre pero reemplaza la pestaña de
`cloudflared` por `iniciar_funnel.bat`. Al terminar, la URL pública queda
en `tailscale\public_url.txt` -- pegala como `PUBLIC_URL` en `backend\.env`.

### 5. Confirmar que arrancó bien

```
tailscale\estado.bat
```

Debería mostrar `HTTP 200` para el backend local, el frontend local y la
URL pública. Pasame el contenido de `tailscale\public_url.txt` y desde acá
hago un pedido real a esa URL para confirmar que responde desde afuera de
tu red, no solo en tu WiFi.

### 6. Dejarla corriendo siempre (arranque de Windows)

No lo hice yo porque es una configuración persistente del sistema que te
corresponde aprobar a vos directamente en tu PC, pero es un paso de 30
segundos:

1. `Win + R` -> escribí `shell:startup` -> Enter (abre tu carpeta de
   inicio de Windows).
2. Arrastrá ahí un acceso directo a `tailscale\iniciar_app_tailscale.bat`
   y otro a `tailscale\mantener_activo.bat`.

Con eso, cada vez que prendés la PC y iniciás sesión, la app se levanta
sola y el watchdog la vigila (reinicia backend+frontend+funnel si el
backend deja de responder, sin duplicar procesos: antes de relanzar,
identifica y cierra puntualmente el PID que tenga ocupado el puerto 8000 o
5175, no mata procesos al voleo).

## Comandos sueltos, por si los necesitás directo

```
tailscale funnel --bg https+insecure://127.0.0.1:5175    equivale a iniciar_funnel.bat
tailscale funnel status                                    equivale a estado.bat (parte Tailscale)
tailscale funnel 443 off                                   equivale a detener_funnel.bat
```

Si alguno de estos tira error de sintaxis, es porque tu versión de
Tailscale usa otra forma del comando -- corré `tailscale funnel --help` y
pasame el output, te doy el comando exacto para tu versión.

## Acceso privado alternativo (si algún día todos tus dispositivos tienen Tailscale instalado)

Si en vez de acceso público desde cualquier lado te alcanza con acceder
solo desde tus propios dispositivos (los que vos agregues a tu tailnet),
`tailscale serve` hace lo mismo que Funnel pero sin salir a internet
público -- ni vos necesitás usuario/contraseña en ese caso, porque
Tailscale ya autenticó el dispositivo:

```
tailscale serve --bg https+insecure://127.0.0.1:5175
```

Esto NO reemplaza el login que ya quedó armado (es una capa aparte) pero
sí evita que la URL sea alcanzable desde cualquier IP de internet.

## Varios proyectos en la misma PC (ej: MotoSafe + Nexo)

Tailscale Funnel es por **dispositivo**, no por app: esta PC tiene un solo
nombre público (`<tu-hostname>.ts.net`). Si dos proyectos
corren `tailscale funnel --bg ...` sin especificar un puerto público
distinto, el segundo pisa al primero -- quedan mapeados al mismo puerto
público (443 por default) y el último comando gana.

La solución: Tailscale Funnel admite hasta 3 puertos públicos por
dispositivo (443, 8443 y 10000), cada uno con su propia URL:

- **MotoSafe**: `--https=443` -> `https://<tu-hostname>.ts.net`
  (puerto fijado explícito en `iniciar_funnel.bat`, no es el default
  implícito).
- **Nexo** (u otro proyecto): `--https=8443` -> algo como
  `tailscale funnel --bg --https=8443 localhost:<puerto-de-nexo>`, URL
  resultante `https://<tu-hostname>.ts.net:8443`.

Confirmar que ambos coexisten con `tailscale funnel status` -- tiene que
listar las dos entradas, una por puerto. `tailscale\detener_funnel.bat` y
`tailscale\reiniciar_app.bat` de ESTE proyecto solo tocan el puerto 443
(`tailscale funnel 443 off`), nunca el 8443 de otro proyecto.

## Por qué no se tocó `iniciar_app.bat` original

Para no romper lo que ya funciona con `cloudflared` sin que lo revises
vos primero. `iniciar_app_tailscale.bat` es un archivo aparte; cuando
confirmes que Tailscale Funnel te sirve mejor (URL fija, no cambia en
cada reinicio), podés simplemente empezar a usar siempre este y dejar de
usar el viejo.
