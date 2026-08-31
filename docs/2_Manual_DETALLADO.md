# MotoSafe GBA — Manual de Operación (explicado paso a paso)

## Antes de empezar: qué es una terminal y cómo se usa

Una terminal (también llamada consola, o PowerShell en Windows) es una ventana donde le escribís órdenes a la computadora en forma de texto, en vez de hacer clic con el mouse. Cada línea que escribís se llama "comando". Apretás Enter, y la computadora ejecuta esa orden.

Cosas importantes para entenderla:
- La computadora siempre está "parada" en una carpeta específica. Si le pedís algo que está en otra carpeta sin decirle antes que se mueva ahí, no lo va a encontrar.
- El comando `cd` (de "change directory", cambiar de carpeta) es cómo le decís "movete a esta otra carpeta".
- Todo tiene que estar escrito exactamente bien — mayúsculas, espacios, barras — porque la computadora no adivina lo que quisiste decir.

En este proyecto vas a usar **varias terminales al mismo tiempo**, cada una corriendo una parte distinta del sistema, sin cerrarse entre sí.

---

## 1. Levantar todo desde cero (después de reiniciar la PC)

El proyecto tiene tres piezas que tienen que estar corriendo al mismo tiempo, cada una en su propia terminal, para que la aplicación funcione completa. El orden importa.

### Paso 1 — Abrir Docker Desktop

**Qué es y por qué hace falta:** Docker Desktop es el programa que hace posible que tu base de datos exista y esté disponible. Sin él corriendo, nada de lo demás va a poder guardar ni leer datos.

**Cómo hacerlo:** andá al menú Inicio de Windows, escribí "Docker Desktop", y hacé clic para abrirlo. **Este programa no arranca solo con Windows** — hay que abrirlo a mano cada vez que reiniciás la PC (a menos que hayas activado la opción de que arranque automático en su configuración).

**Cómo saber si ya está listo:** en la ventana de Docker Desktop, abajo a la izquierda, tiene que decir **"Engine running"** en verde. Puede tardar entre 30 segundos y 2 minutos la primera vez después de un reinicio — no lo cierres ni intentes nada más mientras carga.

### Paso 2 — Levantar la base de datos

Con Docker ya listo, abrí una terminal (o usá la que tengas abierta) y escribí, línea por línea:

```powershell
cd $HOME\Desktop\motosafe-gba
docker compose up -d
docker ps
```

**Qué hace cada línea:**
- `cd $HOME\Desktop\motosafe-gba`: le dice a la terminal "movete a la carpeta del proyecto".
- `docker compose up -d`: lee un archivo llamado `docker-compose.yml` (que ya está preparado) y levanta la base de datos según esas instrucciones. El `-d` significa que se ejecuta "de fondo", sin ocupar la terminal.
- `docker ps`: muestra una lista de todo lo que Docker tiene corriendo en este momento. Tiene que aparecer una fila con el nombre `motosafe-db` y la palabra "Up" en su estado — eso confirma que la base de datos está viva y disponible.

### Paso 3 — Levantar el backend (el servidor de datos)

Abrí una **terminal nueva** (no reutilices la anterior, dejala corriendo Docker) y escribí:

```powershell
cd $HOME\Desktop\motosafe-gba\backend
.\venv\Scripts\activate
uvicorn main:app --reload
```

**Qué hace cada línea:**
- `cd ...\backend`: te movés a la carpeta donde vive el servidor de datos.
- `.\venv\Scripts\activate`: activa el "entorno virtual" de Python — una carpeta especial donde están instaladas todas las librerías que este proyecto necesita, separadas de cualquier otro programa Python que tengas en la PC. Si funcionó, vas a ver que el principio de la línea de comandos ahora empieza con `(venv)`.
- `uvicorn main:app --reload`: arranca el servidor de datos en sí. `main:app` le dice qué archivo de código correr (`main.py`, donde está escrita toda la lógica del servidor). `--reload` hace que, si modificás el código mientras el servidor está corriendo, se reinicie solo.

**Cómo saber si funcionó:** tiene que aparecer, entre otras líneas, el texto **"Application startup complete."** Si eso aparece, el servidor está listo y escuchando pedidos. **Dejá esta terminal abierta y no le escribas nada más** — mientras esté abierta, el servidor sigue funcionando; si la cerrás, se apaga.

### Paso 4 — Levantar el frontend (la parte visual)

Abrí **otra terminal nueva** (ya tenés dos abiertas: Docker/base de datos, y el backend; esta es la tercera):

```powershell
cd $HOME\Desktop\motosafe-gba\frontend
npm run dev
```

**Qué hace:** levanta un mini-servidor que te sirve la página web del mapa en tu navegador, y va actualizándola automáticamente cada vez que se modifica el código visual.

**Cómo saber si funcionó:** la terminal te va a mostrar una dirección web, normalmente `http://localhost:5173/`. Copiá esa dirección (o hacele clic si tu terminal lo permite) y pegala en el navegador. **Dejá esta terminal abierta también.**

### Paso 5 — Confirmar que todo está funcionando junto

En el navegador, con la dirección del paso 4 abierta, tenés que ver el mapa cargado con puntos de colores (verde, amarillo, naranja, rojo) repartidos por la ciudad, y en la esquina de abajo a la izquierda una leyenda con números al lado de cada color. Si en cambio ves "0 zonas registradas" o un cartel de "sin conexión", andá a la sección de problemas de este mismo documento.

---

## 2. Levantar Jupyter (para trabajar en el análisis o el modelo)

Jupyter es un programa aparte que no reemplaza al backend ni al frontend — es para cuando querés seguir trabajando en el análisis de datos o en el modelo de Machine Learning, no para usar la aplicación en sí.

Abrí una **terminal nueva** (podés tener Docker, backend, frontend, y esta cuarta terminal, todas abiertas al mismo tiempo sin problema):

```powershell
cd $HOME\Desktop\motosafe-gba\backend
.\venv\Scripts\activate
cd ..\notebooks
jupyter notebook
```

Esto abre una pestaña nueva en tu navegador con la interfaz de Jupyter. Hacé clic en el archivo `01_eda_hotspots_moto.ipynb` para abrir el notebook donde está todo el trabajo hecho.

**Cómo se usa un notebook, en resumen:** el archivo está dividido en "celdas", cada una con un pedacito de código. Hacés clic en una celda y apretás `Shift + Enter` para ejecutar solo esa celda y pasar a la siguiente. El resultado de cada celda aparece justo debajo, antes de la próxima.

---

## 3. Comandos de Git más usados (guardar y respaldar cambios)

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

## 4. Cómo reentrenar o modificar el modelo de Machine Learning

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

## 5. Problemas que ya pasaron durante esta sesión, y cómo se resuelven

Esta sección existe porque cada uno de estos errores ya ocurrió al menos una vez mientras se construía el proyecto. Si te aparece alguno, seguramente la solución está acá.

### "failed to connect to the docker API... npipe... El sistema no puede encontrar el archivo especificado"
**Por qué pasa:** Docker Desktop no está abierto, o está abierto pero todavía no terminó de cargar su "motor" interno.
**Solución:** abrir Docker Desktop a mano (menú Inicio) y esperar a que la ventana diga "Engine running" antes de tocar cualquier terminal.

### "uvicorn no se reconoce como nombre de un cmdlet, función, archivo de script..."
**Por qué pasa:** dos causas posibles.
- El entorno virtual de Python no está activado (el principio de la línea no dice `(venv)`) → correr `.\venv\Scripts\activate`.
- Estás parado en la carpeta equivocada. `uvicorn` solo funciona si estás dentro de `backend/` → correr `cd backend` primero.

### "cd backend" dice que la ruta no existe
**Por qué pasa:** estás parado en tu carpeta de usuario general (`C:\Users\tunombre`), no en el proyecto.
**Solución:** empezar siempre escribiendo la ruta completa: `cd $HOME\Desktop\motosafe-gba\backend`.

### El frontend muestra "Sin conexión con el backend"
**Por qué pasa:** el servidor de datos (backend) intentó conectarse a la base de datos en un momento en que Docker todavía no había terminado de levantarla.
**Solución:** confirmar con `docker ps` que `motosafe-db` diga "Up". Después, ir a la terminal donde corre `uvicorn`, apretar `Ctrl + C`, y volver a escribir `uvicorn main:app --reload`.

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
.\venv\Scripts\activate
pip install nombre-de-la-libreria
```
Después, en Jupyter, ir al menú **Kernel → Restart Kernel and Run All Cells**. Instalar la librería sola no alcanza — el "kernel" (el proceso de Python que ya está corriendo dentro del notebook) no se entera de la librería nueva hasta que se reinicia.

### Jupyter tira "NameError: name '...' is not defined"
**Por qué pasa:** el kernel se reinició (por ejemplo, después de instalar una librería nueva), y las celdas de arriba, que definían esa variable, no se volvieron a ejecutar.
**Solución:** ir al menú **Run → Run All Cells** (o **Kernel → Restart Kernel and Run All Cells**), para que todo el notebook se ejecute de punta a punta, en orden, desde el principio.

---

## 6. Mapa de rutas del proyecto, para no perderte

| Qué buscás | Dónde está |
|---|---|
| La carpeta completa del proyecto | `C:\Users\<tu usuario>\Desktop\motosafe-gba\` |
| El código del servidor de datos | `...\motosafe-gba\backend\main.py` |
| El código de la parte visual | `...\motosafe-gba\frontend\src\App.jsx` |
| El notebook con todo el análisis | `...\motosafe-gba\notebooks\01_eda_hotspots_moto.ipynb` |
| Los datos (CSV, no se suben a GitHub) | `...\motosafe-gba\data\` |
| La aplicación funcionando en el navegador | http://localhost:5173 |
| El servidor de datos, para probarlo directo | http://localhost:8000/docs |
| El respaldo en internet del proyecto | https://github.com/Roudcode/motosafe-gba (repositorio privado) |
