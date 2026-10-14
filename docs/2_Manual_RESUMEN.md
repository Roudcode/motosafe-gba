# MotoSafe GBA — Manual de Operación

**Actualizado: 2026-10-13**, verificado contra los scripts reales del repositorio. Este documento es para *hacer*, no para entender el porqué (eso está en la Guía Completa). Comandos exactos, en orden, y qué hacer cuando algo falla.

---

## 1. Levantar todo desde cero — camino recomendado

**Orden importante: Docker siempre primero.**

### Paso 1 — Docker Desktop
Abrilo a mano (menú Inicio → "Docker Desktop" → clic). **No arranca solo con Windows.** Esperá a que la ventana diga "Engine running" — puede tardar 1-2 minutos.

### Paso 2 — Doble clic en `iniciar.bat`
En la carpeta del proyecto. Abre 5 pestañas (Windows Terminal) o 4 ventanas separadas: Docker, Backend, Frontend, Scraper de noticias y Túnel. El backend por sí solo instala dependencias, chequea el login (te pide crear usuario/contraseña la primera vez con `generar_password.py` si todavía no existe), aplica migraciones pendientes y recién después arranca. Si no querés correr el scraper cada vez, usá `iniciar_app.bat` en vez de `iniciar.bat`.

### Paso 3 — Iniciar sesión
La app pide usuario/contraseña (login activado por defecto). Usá lo que configuraste con `generar_password.py`.

### Paso 4 — Confirmar
Entrar a la URL que muestra la pestaña Frontend (normalmente `https://localhost:5173/`, certificado autofirmado — el navegador va a avisar, es esperado). El mapa tiene que cargar con hexágonos o puntos de colores reales y la leyenda con números (no "0 zonas registradas").

---

## 2. Levantar cada pieza a mano (si `iniciar.bat` falla y necesitás aislar el problema)

```powershell
# Base de datos
cd $HOME\Desktop\motosafe-gba
docker compose up -d
docker ps   # tiene que aparecer motosafe-db en "Up"

# Backend (otra terminal)
cd $HOME\Desktop\motosafe-gba\backend
venv312\Scripts\activate
python migrar.py
python run_dev.py   # esperar "Application startup complete."

# Frontend (otra terminal)
cd $HOME\Desktop\motosafe-gba\frontend
npm run dev
```

---

## 3. Levantar Jupyter (para seguir trabajando en el notebook)

En una terminal aparte (no reemplaza al backend ni al frontend):
```powershell
cd $HOME\Desktop\motosafe-gba\backend
venv312\Scripts\activate
cd ..\notebooks
jupyter notebook
```
Se abre el navegador. Abrir `01_eda_hotspots_moto.ipynb`.

---

## 4. Comandos de Git más usados

Guardar cambios y subirlos a GitHub:
```powershell
cd $HOME\Desktop\motosafe-gba
git add .
git commit -m "descripción corta de lo que cambiaste"
git push
```

Ver si hay algo sin guardar:
```powershell
git status
```

Ver el historial de commits:
```powershell
git log --oneline -10
```

---

## 5. Reentrenar o modificar el modelo

1. Levantar Jupyter (sección 3).
2. Abrir `01_eda_hotspots_moto.ipynb`, ir a las celdas del modelo final.
3. Si se reentrena con cambios, al final volver a guardar:
```python
joblib.dump(modelo_final, '../data/modelo_final.pkl')
joblib.dump(X3.columns.tolist(), '../data/columnas_modelo.pkl')
```
4. Copiar los archivos actualizados al backend:
```powershell
cd $HOME\Desktop\motosafe-gba
copy data\modelo_final.pkl backend\
copy data\columnas_modelo.pkl backend\
```
5. Reiniciar el backend (`Ctrl+C` en su pestaña, después `python run_dev.py` de nuevo) — el modelo no se recarga solo, porque el cambio está en el `.pkl`, no en el código.

---

## 6. Problemas que ya pasaron, y cómo se resuelven

### "failed to connect to the docker API... npipe"
Docker Desktop no está abierto (o no terminó de cargar). Abrilo a mano y esperá a "Engine running" antes de tocar cualquier terminal.

### "uvicorn no se reconoce..." o el backend no arranca
Dos causas posibles:
- El venv no está activado (el prompt no dice `(venv312)` al principio) → `venv312\Scripts\activate`
- Estás parado en la carpeta equivocada (tiene que ser `backend/`, no la raíz del proyecto) → `cd backend`

### El backend se detiene pidiendo usuario/contraseña
Todavía no configuraste el login. Correr `python generar_password.py`, pegar las dos líneas que devuelve (`AUTH_USERNAME`/`AUTH_PASSWORD_HASH`) en `backend\.env`, guardar y volver a arrancar.

### "cd backend" dice que la ruta no existe
Estás parado en tu carpeta de usuario (`C:\Users\tunombre`), no en el proyecto. Empezá siempre con:
```powershell
cd $HOME\Desktop\motosafe-gba\backend
```

### El frontend muestra "Sin conexión con el backend"
El backend intentó conectarse a la base de datos antes de que Docker terminara de levantar. Solución: confirmar `docker ps` muestra `motosafe-db` en "Up", después ir a la pestaña del backend, `Ctrl+C`, y `python run_dev.py` de nuevo.

### El mapa muestra "0 zonas registradas" aunque el backend funciona
Puede ser un bug de React donde algo no se recalcula. Revisar la consola del navegador (F12 → Console) buscando errores en rojo. Si no hay errores, probar `Ctrl+Shift+R` (refresco fuerte).

### `git add / commit / push` con `&&` entre comandos da error
En PowerShell no se usa `&&` para encadenar comandos como en bash/cmd. Poner cada comando en su propia línea, o separarlos con `;`.

### Falta alguna librería de Python al ejecutar una celda (`ModuleNotFoundError`)
```powershell
cd $HOME\Desktop\motosafe-gba\backend
venv312\Scripts\activate
pip install nombre-de-la-libreria
```
Después, en Jupyter: **Kernel → Restart Kernel and Run All Cells** (instalar solo no alcanza, el kernel ya cargado no ve la librería nueva hasta reiniciar).

### Jupyter tira error de que una variable "no está definida" (`NameError`)
El kernel se reinició y las celdas de arriba no se volvieron a ejecutar. Ir a **Run → Run All Cells** (o **Kernel → Restart Kernel and Run All Cells**) para correr todo el notebook de punta a punta en orden.

---

## 7. Rutas importantes, para no perderse

| Qué | Dónde |
|---|---|
| Proyecto completo | `C:\Users\<usuario>\Desktop\motosafe-gba\` |
| Lanzador único (todo junto) | `...\motosafe-gba\iniciar.bat` (con scraper) / `iniciar_app.bat` (sin scraper) |
| Backend / API | `...\motosafe-gba\backend\main.py` |
| Frontend / interfaz | `...\motosafe-gba\frontend\src\App.jsx` |
| Notebook de análisis | `...\motosafe-gba\notebooks\01_eda_hotspots_moto.ipynb` |
| Datos (no en GitHub) | `...\motosafe-gba\data\` |
| API corriendo | http://localhost:8000 (docs interactivas en http://localhost:8000/docs) |
| App corriendo | https://localhost:5173 |
| URL pública temporal | pestaña "Tunel" de `iniciar.bat` (`*.trycloudflare.com`, cambia cada vez) |
| Repo en GitHub | https://github.com/Roudcode/motosafe-gba (privado) |

**Nota:** además del túnel de Cloudflare de arriba, existe en el repo una carpeta `tailscale/` con otro mecanismo de acceso público (Tailscale Funnel) documentado en sesiones anteriores de BITACORA.md. Cuál de los dos está activo en un momento dado es algo que solo Rodo puede confirmar — no se infiere solo leyendo el código.
