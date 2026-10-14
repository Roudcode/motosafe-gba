# MotoSafe GBA — Manual de Operación (explicado paso a paso)

**Actualizado: 2026-10-13.** Este manual describe el flujo de arranque vigente
hoy, verificado contra los scripts reales del repositorio (`iniciar.bat`,
`backend/_iniciar_backend.bat`). Las versiones anteriores de este documento
describían activar un `venv` genérico y correr `uvicorn` a mano en varias
terminales por separado — eso ya no es necesario, hay un lanzador único.
Se conserva la sección 2 ("cada pieza a mano") para quien quiera entender
o controlar cada pieza por separado, pero el camino recomendado es la
sección 1.

## Antes de empezar: qué es una terminal y cómo se usa

Una terminal (también llamada consola, o PowerShell en Windows) es una ventana donde le escribís órdenes a la computadora en forma de texto, en vez de hacer clic con el mouse. Cada línea que escribís se llama "comando". Apretás Enter, y la computadora ejecuta esa orden.

Cosas importantes para entenderla:
- La computadora siempre está "parada" en una carpeta específica. Si le pedís algo que está en otra carpeta sin decirle antes que se mueva ahí, no lo va a encontrar.
- El comando `cd` (de "change directory", cambiar de carpeta) es cómo le decís "movete a esta otra carpeta".
- Todo tiene que estar escrito exactamente bien — mayúsculas, espacios, barras — porque la computadora no adivina lo que quisiste decir.

En este proyecto vas a usar **varias terminales al mismo tiempo**, cada una corriendo una parte distinta del sistema, sin cerrarse entre sí.

---

## 1. Levantar todo desde cero (después de reiniciar la PC) — camino recomendado

Hoy existe un lanzador único en la raíz del proyecto: `iniciar.bat`. Hace todo lo que antes requería varias terminales manuales, en un solo doble clic.

### Paso 1 — Abrir Docker Desktop

**Qué es y por qué hace falta:** Docker Desktop es el programa que hace posible que tu base de datos exista y esté disponible. Sin él corriendo, nada de lo demás va a poder guardar ni leer datos.

**Cómo hacerlo:** andá al menú Inicio de Windows, escribí "Docker Desktop", y hacé clic para abrirlo. **Este programa no arranca solo con Windows** — hay que abrirlo a mano cada vez que reiniciás la PC (a menos que hayas activado la opción de que arranque automático en su configuración).

**Cómo saber si ya está listo:** en la ventana de Docker Desktop, abajo a la izquierda, tiene que decir **"Engine running"** en verde. Puede tardar entre 30 segundos y 2 minutos la primera vez después de un reinicio — no lo cierres ni intentes nada más mientras carga.

### Paso 2 — Doble clic en `iniciar.bat`

Con Docker ya listo, andá a la carpeta `$HOME\Desktop\motosafe-gba` y hacé doble clic en `iniciar.bat`. Si tenés instalado Windows Terminal (`wt`), abre **una sola ventana con 5 pestañas**: Docker, Backend, Frontend, Scraper de noticias y Túnel. Si no lo tenés instalado, abre lo mismo pero en 4 ventanas de consola separadas.

**Qué hace cada pestaña/ventana, en orden:**
- **Docker:** corre `docker compose up -d`, levanta la base de datos PostgreSQL/PostGIS de fondo.
- **Backend:** corre `backend\_iniciar_backend.bat`, que hace cuatro cosas en cadena, cada una dentro del entorno virtual del proyecto (`venv312`, no uno genérico):
  1. Instala/verifica las dependencias de Python exactas del `requirements.lock` (con verificación de hash — rápido si ya están instaladas, no reinstala de cero cada vez).
  2. **Chequea el login.** Si todavía no configuraste usuario/contraseña de acceso a la app (`AUTH_USERNAME`/`AUTH_PASSWORD_HASH` en `backend\.env`), el script se detiene y corre `generar_password.py`, que te pide un usuario y una contraseña y te devuelve las dos líneas para pegar en `backend\.env`. Guardás el archivo y volvés a ejecutar `iniciar.bat`.
  3. **Aplica las migraciones de base de datos pendientes** (`migrar.py`) — no hace nada si ya están aplicadas, así que es seguro correrlo siempre.
  4. Arranca el servidor en sí (`run_dev.py`, que a su vez levanta `uvicorn`).
- **Frontend:** corre `npm run dev` dentro de `frontend\`, sirve la página del mapa.
- **Scraper:** corre `scrapear_noticias_robos.py --guardar` una vez, para traer noticias de prensa nuevas al abrir la app. (Si no lo querés correr cada vez, usá `iniciar_app.bat` en vez de `iniciar.bat` — es el mismo lanzador pero sin esta pestaña.)
- **Túnel:** corre `cloudflared tunnel --url https://localhost:5173 --no-tls-verify`, que expone la app detrás de una URL pública temporal (`*.trycloudflare.com`), visible en esa misma pestaña. Cambia cada vez que se reinicia — no es una dirección fija.

**Cómo saber si funcionó:** la pestaña de Frontend te muestra una dirección local, normalmente `https://localhost:5173/` (con certificado autofirmado del propio Vite — el navegador va a avisar que no es de confianza, es esperado en desarrollo). Abrí esa dirección, o la del túnel si querés probar desde el celular.

### Paso 3 — Iniciar sesión

La app pide usuario y contraseña la primera vez que la abrís (la misma pantalla de login que configuraste con `generar_password.py` en el paso anterior). Esto es así por defecto (`AUTH_HABILITADO=true` salvo que se desactive explícitamente) — protege que cualquiera con el link del túnel pueda entrar sin permiso.

### Paso 4 — Confirmar que todo está funcionando junto

Una vez logueado, tenés que ver el mapa cargado con hexágonos o puntos de colores (verde, amarillo, naranja, rojo) repartidos por la ciudad, y en la esquina de abajo a la izquierda una leyenda con números al lado de cada color. Si en cambio ves "0 zonas registradas" o un cartel de "sin conexión", andá a la sección de problemas de este mismo documento.

---

## 2. Levantar cada pieza a mano (si no querés usar `iniciar.bat`)

Útil para entender qué hace cada pieza por separado, o si `iniciar.bat` falla y necesitás aislar el problema.

### Base de datos

```powershell
cd $HOME\Desktop\motosafe-gba
docker compose up -d
docker ps
```

`docker ps` tiene que mostrar una fila con `motosafe-db` y "Up" en su estado.

### Backend (servidor de datos)

```powershell
cd $HOME\Desktop\motosafe-gba\backend
venv312\Scripts\activate
python migrar.py
python run_dev.py
```

`venv312\Scripts\activate` activa el entorno virtual del proyecto (no uno genérico llamado `venv` — ese nombre quedó de una versión anterior de este manual). `migrar.py` aplica las migraciones de base de datos pendientes antes de arrancar; `run_dev.py` levanta el servidor real. Tiene que aparecer **"Application startup complete."** Si el login todavía no está configurado, va a avisarlo — correr `python generar_password.py` primero y pegar las dos líneas que devuelve en `backend\.env`.

### Frontend (la parte visual)

```powershell
cd $HOME\Desktop\motosafe-gba\frontend
npm run dev
```

Te va a mostrar una dirección como `https://localhost:5173/`. Vite sirve con HTTPS y certificado autofirmado en este proyecto — el navegador va a marcarlo como no confiable, es esperado.

---

## 3. Levantar Jupyter (para trabajar en el análisis o el modelo)

Jupyter es un programa aparte que no reemplaza al backend ni al frontend — es para cuando querés seguir trabajando en el análisis de datos o en el modelo de Machine Learning, no para usar la aplicación en sí.

Abrí una **terminal nueva** (podés tener Docker, backend, frontend, y esta cuarta terminal, todas abiertas al mismo tiempo sin problema):

```powershell
cd $HOME\Desktop\motosafe-gba\backend
venv312\Scripts\activate
cd ..\notebooks
jupyter notebook
```

Esto abre una pestaña nueva en tu navegador con la interfaz de Jupyter. Hacé clic en el archivo `01_eda_hotspots_moto.ipynb` para abrir el notebook donde está todo el trabajo hecho.

**Cómo se usa un notebook, en resumen:** el archivo está dividido en "celdas", cada una con un pedacito de código. Hacés clic en una celda y apretás `Shift + Enter` para ejecutar solo esa celda y pasar a la siguiente. El resultado de cada celda aparece justo debajo, antes de la próxima.

---

## 4. Comandos de Git más usados (guardar y respaldar cambios)

Git es el sistema que guarda el historial de tu proyecto. Cada vez que hacés cambios importantes y querés guardarlos de forma permanente (tanto en tu compu como en internet, en GitHub), usás esta secuencia:

```powershell
cd $HOME\Desktop\motosafe-gba
git add .
git commit -m "descripción corta de lo que cambiaste"
git push
```

**Qué hace cada línea:**
- `git add .`: le dice a Git "prepará todos los archivos que cambié para guardarlos" (el punto significa "todos, en esta carpeta y sus subcarpetas").
- `git commit -m "..."`: guarda esa "foto" del proyecto de forma permanente en tu computadora, con una etiqueta de texto que describe qué cambió. El texto entre comillas es libre, pero conviene que sea claro (por ejemplo: `"agrego el boton de compartir ruta"`).
- `git push`: manda esa foto guardada hacia GitHub, la copia en internet.

**Para ver si tenés cambios sin guardar:**
```powershell
git status
```
Si dice "nothing to commit, working tree clean", no hay nada pendiente.

**Para ver el historial de cambios guardados:**
```powershell
git log --oneline -10
```
Te muestra los últimos 10 cambios guardados, cada uno con su descripción.

---

## 5. Cómo reentrenar o modificar el modelo de Machine Learning

Si en algún momento querés cambiar algo del modelo (agregar una variable nueva, probar otro algoritmo, etc.):

1. Levantar Jupyter (sección 2 de este documento).
2. Abrir el notebook, ir a las celdas correspondientes al modelo, hacer los cambios.
3. Si el modelo se reentrena, hay que guardarlo de nuevo con estas dos líneas dentro de una celda del notebook:
```python
joblib.dump(modelo_final, '../data/modelo_final.pkl')
joblib.dump(X3.columns.tolist(), '../data/columnas_modelo.pkl')
```
4. Copiar los archivos actualizados a la carpeta donde el backend los necesita:
```powershell
cd $HOME\Desktop\motosafe-gba
copy data\modelo_final.pkl backend\
copy data\columnas_modelo.pkl backend\
```
5. Reiniciar el backend: ir a su terminal, apretar `Ctrl + C` (esto lo corta), y volver a escribir `uvicorn main:app --reload`. Esto es necesario porque, aunque el servidor se recarga solo cuando cambia el código (`main.py`), **no se entera solo si cambiás el archivo del modelo** — hay que reiniciarlo a mano para que cargue la versión nueva.

---

## 6. Problemas que ya pasaron durante esta sesión, y cómo se resuelven

Esta sección existe porque cada uno de estos errores ya ocurrió al menos una vez mientras se construía el proyecto. Si te aparece alguno, seguramente la solución está acá.

### "failed to connect to the docker API... npipe... El sistema no puede encontrar el archivo especificado"
**Por qué pasa:** Docker Desktop no está abierto, o está abierto pero todavía no terminó de cargar su "motor" interno.
**Solución:** abrir Docker Desktop a mano (menú Inicio) y esperar a que la ventana diga "Engine running" antes de tocar cualquier terminal.

### "uvicorn no se reconoce como nombre de un cmdlet, función, archivo de script..."
**Por qué pasa:** dos causas posibles.
- El entorno virtual de Python no está activado (el principio de la línea no dice `(venv312)`) → correr `venv312\Scripts\activate`.
- Estás parado en la carpeta equivocada. `run_dev.py` solo funciona si estás dentro de `backend/` → correr `cd backend` primero.

### "cd backend" dice que la ruta no existe
**Por qué pasa:** estás parado en tu carpeta de usuario general (`C:\Users\tunombre`), no en el proyecto.
**Solución:** empezar siempre escribiendo la ruta completa: `cd $HOME\Desktop\motosafe-gba\backend`.

### El frontend muestra "Sin conexión con el backend"
**Por qué pasa:** el servidor de datos (backend) intentó conectarse a la base de datos en un momento en que Docker todavía no había terminado de levantarla.
**Solución:** confirmar con `docker ps` que `motosafe-db` diga "Up". Después, ir a la terminal/pestaña donde corre el backend, apretar `Ctrl + C`, y volver a correr `python run_dev.py` (o cerrar y reabrir `iniciar.bat`).

### El mapa muestra "0 zonas registradas" aunque el backend parece andar bien
**Por qué pasa:** puede ser un error en el código de la parte visual donde algo no se actualiza correctamente cuando llegan datos nuevos.
**Solución:** abrir las herramientas de desarrollador del navegador (tecla `F12`), ir a la pestaña "Console", y buscar algún mensaje en rojo (error). Si no hay ningún error visible, probar un refresco fuerte de la página con `Ctrl + Shift + R`.

### Al ejecutar `git add`, `git commit` y `git push` juntos con `&&` entre ellos, da error de sintaxis
**Por qué pasa:** `&&` para unir comandos en una sola línea es una sintaxis de otros sistemas (bash, cmd), pero PowerShell (la terminal de Windows) no la reconoce de la misma forma.
**Solución:** escribir cada comando en su propia línea, uno abajo del otro, en vez de todos juntos con `&&`.

### Al ejecutar una celda del notebook, aparece "ModuleNotFoundError: No module named '...'"
**Por qué pasa:** falta instalar esa librería específica de Python en el entorno virtual.
**Solución:**
```powershell
cd $HOME\Desktop\motosafe-gba\backend
venv312\Scripts\activate
pip install nombre-de-la-libreria
```
Después, en Jupyter, ir al menú **Kernel → Restart Kernel and Run All Cells**. Instalar la librería sola no alcanza — el "kernel" (el proceso de Python que ya está corriendo dentro del notebook) no se entera de la librería nueva hasta que se reinicia.

### Jupyter tira "NameError: name '...' is not defined"
**Por qué pasa:** el kernel se reinició (por ejemplo, después de instalar una librería nueva), y las celdas de arriba, que definían esa variable, no se volvieron a ejecutar.
**Solución:** ir al menú **Run → Run All Cells** (o **Kernel → Restart Kernel and Run All Cells**), para que todo el notebook se ejecute de punta a punta, en orden, desde el principio.

---

## 7. Mapa de rutas del proyecto, para no perderte

| Qué buscás | Dónde está |
|---|---|
| La carpeta completa del proyecto | `C:\Users\<tu usuario>\Desktop\motosafe-gba\` |
| El código del servidor de datos | `...\motosafe-gba\backend\main.py` |
| El código de la parte visual | `...\motosafe-gba\frontend\src\App.jsx` |
| El notebook con todo el análisis | `...\motosafe-gba\notebooks\01_eda_hotspots_moto.ipynb` |
| Los datos (CSV, no se suben a GitHub) | `...\motosafe-gba\data\` |
| El lanzador único (todo junto) | `...\motosafe-gba\iniciar.bat` (con scraper) / `iniciar_app.bat` (sin scraper) |
| La aplicación funcionando en el navegador | https://localhost:5173 (certificado autofirmado, esperado) |
| El servidor de datos, para probarlo directo | http://localhost:8000/docs |
| URL pública temporal (túnel Cloudflare) | la pestaña "Tunel" de `iniciar.bat` muestra un link `*.trycloudflare.com` nuevo cada vez que se levanta — no es fijo |
| El respaldo en internet del proyecto | https://github.com/Roudcode/motosafe-gba (repositorio privado) |

**Nota sobre acceso público:** además del túnel de Cloudflare de arriba (el que usa `iniciar.bat` hoy), el repositorio tiene una carpeta `tailscale/` con otro mecanismo de túnel (Tailscale Funnel) y un script de vigilancia automática, documentado en sesiones anteriores de BITACORA.md. No se pudo confirmar con certeza, solo leyendo el repositorio, cuál de los dos mecanismos es el que está activo en este momento — es una pregunta para Rodo, no algo para asumir en una entrega académica.
