# MotoSafe GBA — Manual de Operación

Este documento es para *hacer*, no para entender el porqué (eso está en la Guía Completa). Comandos exactos, en orden, y qué hacer cuando algo falla.

---

## 1. Levantar todo desde cero (después de reiniciar la PC)

**Orden importante: Docker siempre primero.**

### Paso 1 — Docker Desktop
Abrilo a mano (menú Inicio → "Docker Desktop" → clic). **No arranca solo con Windows.** Esperá a que la ventana diga "Engine running" — puede tardar 1-2 minutos.

### Paso 2 — Base de datos
```powershell
cd $HOME\Desktop\motosafe-gba
docker compose up -d
docker ps
```
Tiene que aparecer `motosafe-db` en estado "Up".

### Paso 3 — Backend (terminal nueva)
```powershell
cd $HOME\Desktop\motosafe-gba\backend
.\venv\Scripts\activate
uvicorn main:app --reload
```
Esperar a `Application startup complete.` **Dejar esta terminal abierta, no tocarla más.**

### Paso 4 — Frontend (otra terminal nueva)
```powershell
cd $HOME\Desktop\motosafe-gba\frontend
npm run dev
```
Da una URL (normalmente `http://localhost:5173/`). **Dejar esta terminal abierta también.**

### Paso 5 — Confirmar
Entrar a la URL del paso 4. El mapa tiene que cargar con puntos de colores reales y la leyenda con números (no "0 zonas registradas").

---

## 2. Levantar Jupyter (para seguir trabajando en el notebook)

En una **tercera terminal** (no reemplaza al backend ni al frontend):
```powershell
cd $HOME\Desktop\motosafe-gba\backend
.\venv\Scripts\activate
cd ..\notebooks
jupyter notebook
```
Se abre el navegador. Abrir `01_eda_hotspots_moto.ipynb`.

---

## 3. Comandos de Git más usados

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

## 4. Reentrenar o modificar el modelo

1. Levantar Jupyter (sección 2).
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
5. Reiniciar el backend (`Ctrl+C` en su terminal, después `uvicorn main:app --reload` de nuevo) — el modelo no se recarga solo aunque `--reload` esté activo, porque el cambio está en el `.pkl`, no en `main.py`.

---

## 5. Problemas que ya pasaron, y cómo se resuelven

### "failed to connect to the docker API... npipe"
Docker Desktop no está abierto (o no terminó de cargar). Abrilo a mano y esperá a "Engine running" antes de tocar cualquier terminal.

### "uvicorn no se reconoce como nombre de un cmdlet..."
Dos causas posibles:
- El venv no está activado (el prompt no dice `(venv)` al principio) → `.\venv\Scripts\activate`
- Estás parado en la carpeta equivocada (tiene que ser `backend/`, no la raíz del proyecto) → `cd backend`

### "cd backend" dice que la ruta no existe
Estás parado en tu carpeta de usuario (`C:\Users\tunombre`), no en el proyecto. Empezá siempre con:
```powershell
cd $HOME\Desktop\motosafe-gba\backend
```

### El frontend muestra "Sin conexión con el backend"
El backend intentó conectarse a la base de datos antes de que Docker terminara de levantar. Solución: confirmar `docker ps` muestra `motosafe-db` en "Up", después ir a la terminal del backend, `Ctrl+C`, y `uvicorn main:app --reload` de nuevo.

### El mapa muestra "0 zonas registradas" aunque el backend funciona
Puede ser un bug de React donde algo no se recalcula (pasó una vez con `useMemo` sin la dependencia correcta). Revisar la consola del navegador (F12 → Console) buscando errores en rojo. Si no hay errores, probar `Ctrl+Shift+R` (refresco fuerte).

### `git add / commit / push` con `&&` entre comandos da error
En PowerShell no se usa `&&` para encadenar comandos como en bash/cmd. Poner cada comando en su propia línea, o separarlos con `;`.

### Falta alguna librería de Python al ejecutar una celda (`ModuleNotFoundError`)
```powershell
cd $HOME\Desktop\motosafe-gba\backend
.\venv\Scripts\activate
pip install nombre-de-la-libreria
```
Después, en Jupyter: **Kernel → Restart Kernel and Run All Cells** (instalar solo no alcanza, el kernel ya cargado no ve la librería nueva hasta reiniciar).

### Jupyter tira error de que una variable "no está definida" (`NameError`)
El kernel se reinició y las celdas de arriba no se volvieron a ejecutar. Ir a **Run → Run All Cells** (o **Kernel → Restart Kernel and Run All Cells**) para correr todo el notebook de punta a punta en orden.

---

## 6. Rutas importantes, para no perderse

| Qué | Dónde |
|---|---|
| Proyecto completo | `C:\Users\<usuario>\Desktop\motosafe-gba\` |
| Backend / API | `...\motosafe-gba\backend\main.py` |
| Frontend / interfaz | `...\motosafe-gba\frontend\src\App.jsx` |
| Notebook de análisis | `...\motosafe-gba\notebooks\01_eda_hotspots_moto.ipynb` |
| Datos (no en GitHub) | `...\motosafe-gba\data\` |
| API corriendo | http://localhost:8000 (docs interactivas en http://localhost:8000/docs) |
| App corriendo | http://localhost:5173 |
| Repo en GitHub | https://github.com/Roudcode/motosafe-gba (privado) |
