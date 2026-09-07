# MotoSafe GBA

Mapa de riesgo para motociclistas en CABA, construido sobre un modelo de Machine Learning (Random Forest) entrenado con datos reales de siniestralidad vial (2019-2025, data.buenosaires.gob.ar). Proyecto Final de Ingeniería en Informática — Universidad del Salvador.

Backend en FastAPI + PostgreSQL/PostGIS, frontend en React + Leaflet. El detalle de la metodología (limpieza de datos, clustering DBSCAN, comparación de modelos, umbrales de riesgo) está documentado en `notebooks/01_eda_hotspots_moto.ipynb` y en `docs/`.

## Requisitos

- Docker (para PostgreSQL/PostGIS)
- Python 3.10+ y `venv`
- Node 18+ y npm

## Puesta en marcha

### 1. Base de datos

```
docker compose up -d
```

Levanta PostgreSQL con PostGIS en `localhost:5432` (ver credenciales en `docker-compose.yml`).

### 2. Backend

```
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac
pip install -r ../requirements.txt
```

Copiar `.env.example` a `.env` en `backend/` (o en la raíz, según corresponda) y completar `DATABASE_URL` si difiere del default de `docker-compose.yml`.

Cargar los hotspots en la base (una sola vez, o cada vez que se regeneren los datos):

```
python cargar_hotspots.py
```

Cargar los corredores de riesgo (calles completas, como Av. Gral. Paz o Av. Rivadavia,
en vez de zonas puntuales — ver Capítulo 4 de la tesis, sección de corredores):

```
python cargar_corredores.py
```

Requiere que exista `data/corredores_riesgo.csv`. Ese archivo se genera en dos pasos
porque el segundo necesita internet real:

1. `python notebooks/identificar_corredores.py` — agrupa los siniestros por calle
   (sin red, ya viene corrido, genera `data/corredores_candidatos.csv`).
2. `python notebooks/fetch_corredores_geometria.py` — le pide a OSRM la geometría real
   de cada calle candidata y genera `data/corredores_riesgo.csv`.

Cargar los hotspots de inseguridad (delitos reales del GCBA — robos, hurtos, lesiones,
etc. — no siniestros de moto; dos capas independientes, "general" y "con moto"):

```
python cargar_hotspots_inseguridad.py
```

Requiere `data/hotspots_inseguridad_general.csv` y `data/hotspots_inseguridad_moto.csv`.
Se generan en dos pasos, ninguno necesita red (parten de `data/delitos_caba.csv`, que sí
la necesita — ver más abajo):

1. `python notebooks/fetch_delitos_caba.py` — descarga el dataset de Delitos de CABA
   (data.buenosaires.gob.ar, un CSV por año 2016-2025) y genera `data/delitos_caba.csv`.
   Necesita internet real, se corre una sola vez y de nuevo cuando el GCBA publique el
   año siguiente.
2. `python notebooks/identificar_hotspots_inseguridad.py` — agrupa los delitos por
   densidad geográfica (DBSCAN, misma metodología que los hotspots de moto) y genera
   los dos CSV de arriba.

Igual que `corredores_riesgo`, la tabla `hotspots_inseguridad` se autocrea al correr
`cargar_hotspots_inseguridad.py`, no hace falta crearla a mano. A diferencia de
`/hotspots` y `/corredores`, `GET /hotspots-inseguridad` no pasa por el modelo
entrenado ni depende del clima: el nivel de riesgo es densidad histórica de delitos,
calculado una sola vez al cargar la tabla.

Levantar la API:

```
uvicorn main:app --reload
```

Queda en `http://localhost:8000`. `GET /hotspots` devuelve las 412 zonas con el nivel de riesgo recalculado en vivo por el modelo.

Correr los tests:

```
pytest
```

### 3. Frontend

```
cd frontend
npm install
npm run dev
```

Queda en `http://localhost:5173`. Necesita el backend corriendo en `localhost:8000` (CORS ya configurado para `localhost:5173`/`5174`).

## Artefactos del modelo

`backend/modelo_final.pkl`, `backend/columnas_modelo.pkl` y `backend/hotspots_contexto.csv` están versionados en el repo (son necesarios para que el backend arranque) aunque el resto de `data/` no lo está — son copias generadas por la notebook, no se regeneran solas. Si se reentrena el modelo o se recalculan los hotspots, hay que volver a correr `notebooks/01_eda_hotspots_moto.ipynb` de punta a punta y copiar los artefactos resultantes a `backend/`.

`data/corredores_riesgo.csv` (y por lo tanto la tabla `corredores_riesgo`) no está
versionado por el mismo motivo que el resto de `data/`. A diferencia de los hotspots,
la tabla de corredores se crea sola (`CREATE TABLE IF NOT EXISTS`) al correr
`cargar_corredores.py`, no hace falta crearla a mano.

Los CSV crudos de siniestralidad (`data/siniestros_viales_hechos.csv`, `data/siniestros_viales_victimas.csv`) no están en el repo por tamaño — se descargan de [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar).

## Estructura

```
backend/        API FastAPI, modelo entrenado, tests
frontend/       App React (mapa, rutas, reportes)
notebooks/      Análisis exploratorio, clustering, entrenamiento del modelo
docs/           Documentación del proyecto (resultados, extensiones futuras)
```


## Bitácora de desarrollo

> Registro semanal exigido por la cátedra a partir de la Entrega 2 (criterio
> "Registro del Proceso" del Proyecto Final). Arranca en esta entrada: el
> desarrollo previo a esta fecha está documentado igual, paso a paso, en el
> historial de commits de Git (`git log`), pero no en este formato narrativo.
> De acá en adelante, cada sesión de trabajo relevante suma una entrada.

### 07/09/2026 — Inseguridad (delitos) integrada de punta a punta, y rediseño del panel de capas

**Tareas realizadas**
- Descarga y normalización de 10 años de delitos de CABA (`fetch_delitos_caba.py`, 1.387.622 registros, data.buenosaires.gob.ar).
- Índice de inseguridad por comuna (`construir_indice_inseguridad.py`), sumado como variable numérica al modelo Random Forest y reentrenado (`reentrenar_modelo.py`), validado contra dos variantes descartadas antes de adoptar la definitiva.
- Clustering DBSCAN de hotspots de inseguridad, dos variantes (`identificar_hotspots_inseguridad.py`): delito general (303 zonas) y robos con moto (132 zonas), calibrado con `min_samples` distinto para cada uno.
- Endpoint `GET /hotspots-inseguridad` y tabla `hotspots_inseguridad` (`cargar_hotspots_inseguridad.py`).
- Capa de inseguridad en el mapa, primero como toggle independiente y después integrada de verdad al motor de ruteo y a las alertas en viaje (antes solo afectaban a los siniestros de moto).
- Reportes colaborativos con antigüedad relativa ("hace 12 min") y opacidad que decae según la vigencia de cada categoría.
- Panel único de "Capas del mapa" reemplazando dos botones que ciclaban estados sin mostrar las opciones de entrada.
- Diferenciación visual completa de la capa de inseguridad: paleta violeta/magenta propia, forma de cluster distinta (squircle punteado), agrupamiento por zoom propio, atenuación del fondo cuando está activa.
- Corrección de un choque de paneles (el de Capas tapaba el de detalle de zona).

**Decisiones de diseño y su justificación**
- No fusionar siniestros y delito en un score único inventado: no hay base empírica para ponderar uno contra el otro. Sí es válido sumarlos, porque los dos ya están normalizados a la misma escala ordinal (percentiles calculados dentro de cada dataset por separado), no son magnitudes crudas distintas.
- Se descartó la variante del modelo que sumaba `indice_inseguridad_moto` como columna aparte: perdía recall en MORTAL, que es la prioridad explícita del proyecto por sobre precision en GRAVE (ver `nivel_desde_probabilidades` en `backend/main.py`).
- Paleta y forma de cluster distintas para inseguridad en vez de reusar las de siniestros, después de que una primera versión (mismos colores, mismo estilo de punto) generó confusión visual real, reportada por el usuario.
- Panel único de capas en vez de dos botones que ciclaban estados: ciclar no es descubrible (hay que tocar para enterarte de qué opciones existen); un panel con todas las opciones visibles de entrada sí lo es.

**Obstáculos encontrados y cómo se resolvieron**
- `data.buenosaires.gob.ar` está bloqueado por el firewall del entorno de trabajo en la nube usado en esta sesión: el script de descarga se armó para correrlo a mano desde la PC, no de forma automática.
- El panel de Capas nuevo tapaba el panel de detalle de zona (mismo rincón de pantalla, mayor prioridad de apilado): se resolvió cerrando el panel de Capas automáticamente al abrir cualquier otro panel de esa zona de la pantalla, siguiendo el mismo patrón que ya usaba el resto de la app.
- DBSCAN con el mismo radio que ya funcionaba para siniestros de moto (60m) volvía a encadenar todo en un cluster gigante al aplicarlo a delito general, por la distinta densidad de puntos entre datasets; se recalibró `min_samples` por separado para cada uno (10 para moto, 100 para delito general), verificado con barridos empíricos.

**Próximos pasos**
- Actualizar la tesis formal (Capítulos 3, 4 y 6) con todo este contenido — se pospuso a propósito hasta terminar el desarrollo, para no reescribir dos veces.
- Evaluar si conviene declustering dependiente de zoom más agresivo también en la vista de clusters de siniestros.
- Seguir esta bitácora semana a semana de acá en más.

### 07/09/2026 (continuación) — Tests de frontend, y mejoras al modelo entrenado y al clustering de hotspots

**Tareas realizadas**
- Se armó una base de tests automatizados para el frontend (Vitest), que hasta ahora tenía cero: se extrajo de `App.jsx` a un módulo propio (`utils/riesgoRuta.js`) la unificación de siniestros e inseguridad y el cálculo de score por ruta, y se sumaron 31 tests entre ese módulo y `utils/tiempo.js`.
- Push de 18 commits que habían quedado sin subir a GitHub (hechos en sesiones anteriores) — quedó confirmado que el problema era falta de `git push`, no un problema en los commits.
- Barrido sistemático de parámetros de DBSCAN para el clustering de siniestros de moto (60 combinaciones de radio x mínimo de siniestros por zona, en vez de los dos intentos manuales originales). Se adoptó radio=100m, mínimo=12 siniestros, con un post-filtro que descarta clusters "fragmento" (un artefacto conocido de cómo sklearn asigna puntos límite en su implementación greedy, verificado empíricamente antes de decidir el filtro). Resultado: 412 hotspots (antes 430), cobertura de siniestros del 49.9% (antes 32.1%).
- Validación temporal real del modelo (`notebooks/validar_temporal.py`): entrenar con 2019-2024 y testear contra 2025 completo (año nunca visto), en vez de solo el split aleatorio 80/20 de siempre. Reveló que el recall reportado con split aleatorio es optimista: contra datos realmente futuros, el recall de GRAVE cae de 0.60 a 0.52 y el de MORTAL de 0.41 a 0.34.
- Tuning de hiperparámetros del Random Forest (`notebooks/tuning_rf.py`, `notebooks/tuning_rf2.py`), evaluado siempre contra el holdout temporal de 2025 y no solo contra cross-validation. Se adoptó una configuración (`class_weight="balanced_subsample"`, hojas mínimas de 5, 300 árboles) que sube el recall de GRAVE a 0.65-0.73 y de MORTAL a 0.48-0.56, a cambio de una accuracy general más baja.
- Reentrenamiento del modelo final y regeneración de todos los artefactos derivados (`hotspots_moto_caba.csv`, `motos_con_clusters.csv`, `hotspots_contexto.csv`, `modelo_final.pkl`) con los nuevos parámetros.

**Decisiones de diseño y su justificación**
- Se descartó la configuración que la búsqueda automática por cross-validation marcó como "mejor" (mejor f1_macro dentro del período de entrenamiento): al probarla contra el holdout real de 2025, el recall de GRAVE se derrumbaba de 0.52 a 0.07. Es sobreajuste — la métrica de validación cruzada no es un proxy confiable de generalización a datos futuros, hay que medir contra un holdout temporal real.
- Se priorizó recall de casos graves/mortales por sobre accuracy general en la configuración final del modelo: en una app de seguridad vial, perderse un caso grave pesa más que una falsa alarma de más. Es una decisión de producto, documentada como tal (no una que un benchmark ciego hubiera tomado).
- Se aceptó una cobertura de hotspots del 49.9% en vez de perseguir un número más alto: subir el radio de búsqueda más allá de 100m empieza a fusionar zonas distintas en una sola (verificado en el barrido — a partir de ~120m con pocos mínimos de siniestros, un solo cluster se comía hasta el 12.76% de todos los siniestros), repitiendo el problema del primer intento fallido de clustering.

**Obstáculos encontrados y cómo se resolvieron**
- Los clusters con menos miembros que el mínimo configurado no eran un bug: se verificó con `BallTree` que el core point de esos clusters sí tiene suficientes vecinos reales, pero la mayoría ya habían sido tomados por un cluster vecino más grande procesado antes por el orden de asignación greedy de `sklearn`. Se resolvió con un post-filtro explícito que descarta esos fragmentos como ruido.
- No hay acceso a la base de datos Postgres del usuario desde este entorno de trabajo en la nube: la carga real de los nuevos hotspots a la base (`cargar_hotspots.py`) y la verificación visual en el mapa quedan pendientes de que el usuario las corra en su propia máquina.

**Próximos pasos**
- Actualizar la tesis formal con estos hallazgos (validación temporal, trade-off de recall vs. accuracy, barrido de clustering) cuando llegue el momento de retomarla.

### 07/09/2026 (continuación 2) — De DBSCAN a HDBSCAN para los hotspots de siniestro: 412 → 740 zonas, 49.9% → 75.6% de cobertura

**Tareas realizadas**
- A partir de la pregunta directa de si se podía conseguir más zonas y cubrir más siniestros, se evaluó `sklearn.cluster.HDBSCAN` como alternativa a DBSCAN para el clustering de siniestros de moto (no para los hotspots de inseguridad, que siguen con DBSCAN sin cambios).
- Un primer barrido en grilla con `cluster_selection_epsilon` fijo tardó más de 120 segundos sin terminar ni una combinación; se abandonó ese parámetro y se probaron combinaciones sueltas de `min_cluster_size` x `min_samples` sin él, cada una en 17-23 segundos.
- Se aplicó a cada combinación el mismo chequeo de "riesgo de blob" usado para calibrar DBSCAN (tamaño del cluster más grande como % del total). Con `min_cluster_size=12` (mismo piso de 12 siniestros reales por zona que antes, ya garantizado de forma nativa por HDBSCAN) y `min_samples=3`, el resultado fue 740 hotspots, cobertura del 75.6% (antes 412 hotspots, 49.9%), con el cluster más grande en 0.41% del total — más chico que el 0.73% de la versión DBSCAN, es decir, mejor cobertura y a la vez más seguro.
- Se reescribió `notebooks/reclusterizar_hotspots.py` para usar HDBSCAN. El post-filtro de fragmentos que hacía falta con DBSCAN se eliminó: HDBSCAN garantiza nativamente que ningún cluster resultante tenga menos de `min_cluster_size` miembros, así que ya no hace falta ese paso.
- Se regeneraron `motos_con_clusters.csv`, `hotspots_moto_caba.csv`, `hotspots_contexto.csv` y `modelo_final.pkl` (el modelo no cambió de configuración, solo se reentrenó con las mismas variables — el clustering no es un input del modelo, solo de los hotspots que se despliegan en el mapa). Los 24 tests de backend siguen pasando.
- Se actualizaron los comentarios en código (`backend/main.py`, `backend/tests/test_main.py`, `notebooks/identificar_corredores.py`) y ambas Guías (RESUMEN y DETALLADA) con los números y el método nuevo.

**Decisiones de diseño y su justificación**
- Se eligió HDBSCAN sobre seguir ajustando DBSCAN porque el problema de fondo de DBSCAN es que usa un radio fijo (eps) para toda la ciudad: agrandarlo para cubrir zonas de baja densidad arriesga fusionar clusters en zonas densas (el efecto "blob" ya descartado en la calibración anterior). HDBSCAN se adapta a la densidad local de cada zona, así que puede encontrar zonas chicas y compactas donde hay pocos siniestros dispersos sin arriesgar ese efecto donde los siniestros están muy concentrados.
- Se descartó la grilla de búsqueda con `cluster_selection_epsilon` fijo (no terminó en 120 segundos) en vez de forzarla con timeouts más largos: los llamados simples sin ese parámetro ya daban resultados sólidos en menos de 25 segundos cada uno, así que insistir con la versión más lenta no aportaba nada que la más simple no diera.
- Se mantiene el trade-off de cobertura vs. precisión geográfica como una decisión consciente, no un objetivo de "llegar al 100%": el 24.4% de siniestros que quedan aislados corresponde a casos genuinamente dispersos, sin vecinos cercanos suficientes como para formar una zona compacta bajo ningún parámetro razonable — forzar más cobertura ahí significaría volver a arriesgar el efecto "blob" que ya se descartó dos veces.

**Obstáculos encontrados y cómo se resolvieron**
- El paquete `hdbscan` de PyPI (standalone) no está instalado; se usó `sklearn.cluster.HDBSCAN` (parte de scikit-learn 1.7.2, ya instalado), que expone la misma funcionalidad sin agregar una dependencia nueva.
- Igual que con la carga de hotspots de la sesión anterior, este entorno de trabajo en la nube no tiene acceso a la base Postgres del usuario: la recarga real de los 740 hotspots nuevos (`cargar_hotspots.py`) y la verificación visual en el mapa quedan pendientes de correrse en la máquina del usuario.

**Próximos pasos**
- Correr `cargar_hotspots.py` (opción 2 de `tareas.bat`) para recargar los 740 hotspots nuevos en la base local, y confirmar visualmente en el mapa que las zonas nuevas tienen sentido geográfico (no hay clusters alargados ni fusionados).
- Actualizar la tesis formal con este hallazgo (cambio de algoritmo de clustering, cobertura final) cuando llegue el momento de retomarla.
- Evaluar si vale la pena repetir esta misma comparación DBSCAN vs. HDBSCAN para los hotspots de inseguridad (delito general y robos con moto), que todavía usan la calibración manual original con DBSCAN.
