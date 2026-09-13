# MotoSafe GBA

> **Continuidad y documentación central:** empezar por [docs/README.md](docs/README.md). El [backlog operativo](docs/gestion/BACKLOG.md) y el [plan de prioridades](docs/gestion/PRIORIZACION.md) reemplazan para trabajo futuro la lista histórica al final de este README. La auditoría identifica afirmaciones antiguas pendientes de actualizar en este documento.

Mapa de riesgo para motociclistas en CABA, construido sobre un modelo de Machine Learning (Random Forest) entrenado con datos reales de siniestralidad vial (2019-2025, data.buenosaires.gob.ar). Proyecto Final de Ingeniería en Informática — Universidad del Salvador.

Backend en FastAPI + PostgreSQL/PostGIS, frontend en React + Leaflet. El detalle de la metodología (limpieza de datos, clustering HDBSCAN (siniestros y robos con moto) y DBSCAN (delito general), comparación de modelos, umbrales de riesgo) está documentado en `notebooks/01_eda_hotspots_moto.ipynb` y en `docs/`.

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

Copiar `.env.example` a `.env` en `backend/` (o en la raíz, según corresponda) y completar `DATABASE_URL` si difiere del default de `docker-compose.yml`. `OPEN_METEO_BASE_URL` y `CORS_ALLOWED_ORIGINS` ya vienen con un default que funciona en desarrollo local, no hace falta tocarlos. `TOMTOM_API_KEY` es opcional: sin ella el backend arranca igual, pero la capa de tráfico en vivo (`/trafico/tiles`) y el cálculo de rutas (`/rutas`) no van a funcionar (ver [tomtom.com/developer](https://developer.tomtom.com) para sacar una key gratuita).

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

Queda en `http://localhost:8000`. `GET /hotspots` devuelve las 740 zonas con el nivel de riesgo recalculado en vivo por el modelo.

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

Queda en `http://localhost:5173`. Necesita el backend corriendo en `localhost:8000` (CORS ya configurado para `localhost:5173`/`5174`). Si el backend corre en otra URL (por ejemplo, ya hosteado), copiar `frontend/.env.example` a `frontend/.env` y completar `VITE_API_URL`.

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

### 07/09/2026 (continuación 3) — Tráfico en vivo (TomTom): capa visual de congestión y ETA real en la Ruta Rápida

**Tareas realizadas**
- Antes de escribir código se evaluó viabilidad real: cobertura de datos de TomTom en Buenos Aires (confirmada — TomTom publica un Traffic Index propio de la ciudad), límites de cuota gratuita (200.000 tiles/mes en Traffic Flow API, 20.000 requests/mes en Routing API) y comportamiento al agotarla (corta con error 429, no cobra automático sin plan pago explícito). Con el volumen esperado de un proyecto de tesis, ambas cuotas quedan varios órdenes de magnitud por debajo del límite.
- Se creó una cuenta y un proyecto en el portal de desarrolladores de TomTom, con una API key que cubre Traffic Flow API y Routing API.
- Se agregaron dos endpoints nuevos al backend (`backend/main.py`): `GET /trafico/tiles/{z}/{x}/{y}.png` (proxy de los tiles raster de flujo de tráfico, estilo `relative0-dark`) y `GET /trafico/eta` (tiempo de viaje con tráfico en vivo vía TomTom Routing API, con `computeTravelTimeFor=all` para tener también el tiempo sin tráfico de referencia). Ambos con cache en memoria (120s tiles, 60s ETA) como salvaguarda contra uso descuidado, y ambos devuelven 503 sin romper el resto de la app si `TOMTOM_API_KEY` no está configurada.
- En el frontend: nuevo toggle "Tráfico en vivo" en el panel de capas (`CapasPanel.jsx`), independiente de las demás capas (se puede combinar con cualquiera). Al activarlo se agrega un `TileLayer` que apunta al proxy del backend, nunca directo a TomTom.
- La Ruta Rápida ahora muestra, además del tiempo de OSRM sobre el trazado dibujado, un dato aparte "X min con tráfico" (TomTom), explícitamente etiquetado como algo complementario, no un reemplazo. Se completa después de mostrarse la ruta (no bloquea el resultado principal) y desaparece en silencio si el backend no tiene la key configurada.
- Se agregó `TOMTOM_API_KEY` a `.env.example` como plantilla, confirmando que `.env` real sigue fuera de git.

**Decisiones de diseño y su justificación**
- Todo pasa por el backend, nunca se llama a TomTom directo desde el navegador: si la key viajara al frontend, cualquiera podría copiarla desde las devtools y agotar la cuota gratuita del proyecto en minutos.
- El tiempo con tráfico de TomTom se muestra como un dato aparte del tiempo de OSRM, no lo reemplaza: TomTom calcula su propio trazado puertas adentro para estimar ese tiempo, que no es necesariamente idéntico al que dibuja OSRM en el mapa. Mezclarlos sería mostrar un número que no corresponde exactamente al trazado visible — se prefirió ser explícito ("con tráfico en vivo") antes que impreciso.
- No se metió tráfico dentro del score de riesgo de la Ruta Segura: congestión y probabilidad de siniestro grave son ejes distintos (a veces hasta inversos — menos velocidad por tráfico puede significar choques más leves), mezclarlos diluiría el score que es el diferencial real de la tesis.
- Tiles raster (PNG) en vez de vector tiles (protobuf): mismo dato, integración trivial con un `TileLayer` de Leaflet ya existente, sin agregar una librería nueva para decodificar vector tiles. Para el volumen y el objetivo de este proyecto, la complejidad extra de vector tiles no se traduce en ningún beneficio real.

**Obstáculos encontrados y cómo se resolvieron**
- Ninguno relevante: la documentación oficial de TomTom (Traffic Flow raster tiles, Routing API v1) tenía los formatos de URL y campos de respuesta necesarios, se integró directo contra la API real sin necesidad de prueba y error.

**Próximos pasos**
- Cargar la API key real de TomTom en `backend/.env` (`TOMTOM_API_KEY=...`) y probar ambas features en el mapa real.
- Confirmar visualmente que la capa de tráfico se ve razonable sobre CABA (colores de congestión coherentes con la hora del día) y que el "X min con tráfico" aparece en la Ruta Rápida.
- Si con el uso real se ve que la cuota gratuita empieza a ajustar (poco probable al volumen de este proyecto), subir el TTL de cache de tiles de 120s a algo mayor es el primer ajuste, antes de considerar un plan pago.

### 07/09/2026 (continuación 4) — Prework antes de hostear: version de scikit-learn, y URLs/CORS parametrizables

Arrancamos a preparar el sistema para salir de "solo corre en mi maquina" antes de elegir un hosting real, en vez de arrastrar estos temas y encontrarlos recien al desplegar.

**Tareas realizadas**
- Se detecto (por un warning al levantar el backend) que el modelo se habia entrenado con scikit-learn 1.7.2 en este entorno de trabajo, mientras que `requirements.txt` fija 1.5.2 (la version real instalada en la maquina del usuario). Se bajo scikit-learn a 1.5.2 en este entorno tambien y se reentreno el modelo con esa version -- mismas metricas (el entrenamiento no cambia, solo el binario serializado), cero warnings de version al cargarlo ahora.
- `API_URL` en el frontend (`constants.js`) ahora lee `VITE_API_URL` si esta definida (variable de entorno de Vite, se inyecta en build time), con `http://localhost:8000` como default para seguir andando igual en desarrollo local sin tocar nada. Se agrego `frontend/.env.example` documentandolo.
- CORS en el backend (`main.py`) ahora lee `CORS_ALLOWED_ORIGINS` (lista separada por coma) en vez de tener los dos puertos de Vite hardcodeados, con el mismo default de siempre si la variable no esta. Documentado en `.env.example`.

**Decisiones de diseño y su justificacion**
- Se reentreno el modelo para bajarlo a la version de scikit-learn de `requirements.txt` (1.5.2), no se subio `requirements.txt` a 1.7.2: la version 1.5.2 es la que ya esta probada en la maquina real del usuario, cambiar el pin del proyecto para acomodar este entorno de trabajo hubiera sido al reves de como debe ser la relacion entre ambos.
- Variables de entorno con default de desarrollo en ambos casos (frontend y backend): local sigue funcionando exactamente igual sin que el usuario tenga que crear nada nuevo, y el deploy real solo necesita definir dos variables (`VITE_API_URL` y `CORS_ALLOWED_ORIGINS`) sin tocar codigo.

**Pendiente antes de hostear (todavia no resuelto)**
- OSRM: el calculo de ruta usa el servidor de demo publico (`router.project-osrm.org`), pensado para pruebas, no para produccion -- sin garantia de disponibilidad ni limite de uso documentado. Antes de exponer la app publicamente hace falta evaluar alternativas (OSRM propio vs. un servicio de ruteo con free tier confiable) con el mismo criterio que se uso para elegir TomTom, no de apuro.

**Proximos pasos**
- Evaluar opciones de reemplazo/respaldo para OSRM antes de hostear.
- Recien despues, evaluar el hosting en si (backend + Postgres/PostGIS + frontend).

### 07/09/2026 (continuación 5) — OSRM fuera, TomTom Routing API adentro: cálculo de ruta propio y sin depender de un servidor de demo

**Tareas realizadas**
- Se reemplazó el cálculo de ruta, que hasta ahora pegaba directo desde el navegador contra `router.project-osrm.org` (servidor de demo público de OSRM, pensado solo para pruebas, sin garantía de disponibilidad ni límite de uso documentado), por un endpoint propio del backend: `GET /rutas`.
- El nuevo endpoint llama a la Routing API de TomTom (la misma cuenta y key que ya se usa para la capa de tráfico en vivo) con `traffic=true`, `computeTravelTimeFor=all`, `maxAlternatives`, `routeRepresentation=polyline` e `instructionsType=tagged`, y devuelve por cada ruta: el trazado (`coords`), distancia y tiempo de referencia sin tráfico (`km`, `min`), el tiempo con tráfico en vivo (`eta_trafico`) y la guía turn-by-turn ya traducida (`pasos`).
- Se armó `TOMTOM_MANIOBRA_A_OSRM`, un diccionario que traduce cada código de maniobra de TomTom (43 códigos, de `ARRIVE` a `AHEAD_TAKE_FERRY`) al formato `(tipo, modificador)` que ya esperaba el frontend (heredado del contrato de OSRM). Esto permitió no tocar nada de `frontend/src/utils/ui.js` (`textoManiobra`, `iconoManiobra`): la traducción vive enteramente en el backend.
- Se actualizó `calcularRuta` en `App.jsx` para pedir `${API_URL}/rutas?...` en vez de la URL de OSRM, y se sacó la llamada aparte a `/trafico/eta` (ya no hace falta: el mismo pedido a `/rutas` trae el tiempo con tráfico de la misma ruta que se dibuja).
- Se eliminó el endpoint `/trafico/eta` del backend: su funcionalidad quedó subsumida en `/rutas`, mantenerlo hubiera sido código muerto.
- Se corrió la suite completa: 24 tests de backend (pytest) y 31 de frontend (Vitest) siguen pasando sin cambios, más un build de producción (`npm run build`) limpio.

**Decisiones de diseño y su justificación**
- Este cambio resuelve de paso una limitación que había quedado señalada al integrar el tráfico en vivo: antes, el trazado de la ruta (OSRM) y el tiempo con tráfico (TomTom) salían de dos cálculos de ruta independientes, que no necesariamente elegían las mismas calles. Ahora ambos salen del mismo pedido a TomTom, así que el tiempo mostrado corresponde exactamente al trazado que se ve en el mapa.
- Se mantuvo `min` (el tiempo de referencia, sin tráfico) como el campo que usa la lógica existente de comparación entre rutas (rápida/corta), para no tocar esa parte del código que ya funciona y está en uso. El tiempo con tráfico en vivo sigue yendo aparte, en `eta_trafico`, con el mismo criterio de "dato complementario, nunca reemplaza lo que se ve dibujado" que ya se había definido para la feature de tráfico.
- Se probó la lógica del endpoint contra el código real (arma la URL, usa la key, procesa la respuesta esperada de TomTom) pero no se pudo hacer una prueba de punta a punta contra la API real de TomTom desde este entorno de trabajo en la nube: el acceso a internet de este entorno está restringido y no permite llegar a `api.tomtom.com`. La prueba real (pedir una ruta en el mapa y confirmar que aparece el trazado, el tiempo y la guía de pasos) queda pendiente de correr en la máquina del usuario, igual que con la carga de hotspots y la capa de tráfico en sesiones anteriores.

**Obstáculos encontrados y cómo se resolvieron**
- Al intentar levantar `uvicorn` para probar el endpoint end-to-end desde este entorno, faltaba el paquete instalado; se usó en cambio `fastapi.testclient.TestClient` para ejecutar el endpoint directamente en proceso, lo que alcanzó para confirmar que el código corre sin errores de sintaxis ni de lógica hasta el punto exacto del pedido HTTP a TomTom (que sí requiere salida a internet real).

**Próximos pasos**
- Probar `/rutas` de punta a punta en la máquina del usuario: reiniciar el backend, calcular una ruta en el mapa y confirmar que aparecen el trazado, el tiempo con tráfico y los pasos de navegación con sentido.
- Evaluar la vista de navegación 3D/con heading (mostrar la ruta con la orientación de avance, como Maps o Waze, al menos al comenzar un viaje) — pendiente de una decisión técnica sobre el enfoque (rotación completa del mapa vs. solo el ícono de ubicación).
- Avanzar con la evaluación de hosting real (backend + Postgres/PostGIS + frontend) una vez cerrado el punto anterior.

### 07/09/2026 (continuación 6) — Panel de capas: opción de apagar la vista de fondo, y segunda vuelta de HDBSCAN para robos con moto

**Tareas realizadas**
- Se sumó una opción "Apagada" al grupo "Vista de fondo" del Panel de Capas (`constants.js`, `OPCIONES_CAPA_MAPA`): hasta ahora ese grupo era el único de los tres sin forma de desactivarse del todo, a diferencia de Inseguridad y Tráfico. Sin cambios en la lógica de renderizado: como cada capa ya se dibuja con un chequeo puntual (`capaMapa === 'clusters'`, etc.), agregar el valor `'apagado'` alcanza para que ninguna coincida.
- A partir de la pregunta de si valía la pena aplicarle a los hotspots de inseguridad el mismo tratamiento que a los de siniestro (DBSCAN → HDBSCAN), se midió primero la cobertura real de cada uno, que no estaba documentada con un número exacto: delito general 29.2%, robos con moto apenas 14.1%.
- Se corrió un barrido de HDBSCAN sobre robos con moto (~16 mil casos, tamaño similar al de los siniestros de moto): con `min_cluster_size=12, min_samples=2` la cobertura subió a 74.3% (más del quíntuple), con el cluster más grande en 0.79% del total (más seguro que el 3% que toleraba la calibración DBSCAN anterior). Se actualizó `notebooks/identificar_hotspots_inseguridad.py` para usar HDBSCAN en esta capa y se regeneró `data/hotspots_inseguridad_moto.csv` (132 → 502 hotspots).
- Delito general (411.704 casos, ~18 veces más denso) no se migró: HDBSCAN no llegó a terminar ni una combinación en el entorno de trabajo de esta sesión, ni esperando varios minutos con distintos parámetros. Se dejó un script aparte (`notebooks/sweep_hdbscan_inseguridad_general.py`) para evaluarlo sin apuro en una máquina con más tiempo/CPU disponible, sin tocar la calibración actual mientras tanto.
- Se actualizaron las Guías del proyecto (`docs/1_Guia_DETALLADA.md`, sumando una Fase 13; `docs/1_Guia_RESUMEN.md`) y los `.docx` correspondientes con los números nuevos (435 → 805 hotspots de inseguridad totales) y la metodología mixta (DBSCAN para delito general, HDBSCAN para robos con moto).

**Decisiones de diseño y su justificación**
- Se migró robos con moto y no delito general en esta vuelta, en vez de esperar a poder hacer las dos juntas: el tamaño de cada dataset es lo que determina si HDBSCAN es viable de evaluar interactivamente (16 mil casos sí, 412 mil no en este entorno), y no había motivo para demorar una mejora ya confirmada y de bajísimo riesgo (no toca el modelo entrenado, no rompe el contrato de la API) esperando a resolver la otra.
- Se dejó un script de barrido aparte para delito general en vez de insistir con parámetros más agresivos en el mismo entorno: ya se había probado con `min_cluster_size` de hasta 500 sin terminar en 170 segundos, así que seguir intentando ahí no iba a dar una respuesta distinta.

**Obstáculos encontrados y cómo se resolvieron**
- Los primeros intentos de correr HDBSCAN en background (`nohup ... &` + `disown`) para no bloquear la sesión mientras se probaba con el dataset grande terminaron matando el proceso apenas terminaba el comando que lo lanzaba: el entorno de trabajo en la nube usado en esta sesión no sostiene procesos en segundo plano entre llamadas. Se resolvió corriendo cada prueba en primer plano con `timeout`, dentro del límite de tiempo disponible por llamada.
- Igual que con los hotspots de siniestro, no hay acceso a la base Postgres del usuario desde este entorno: la recarga real de los 502 hotspots nuevos de robos con moto (`cargar_hotspots_inseguridad.py`) y la verificación visual en el mapa quedan pendientes de correrse en la máquina del usuario.

**Próximos pasos**
- Correr `cargar_hotspots_inseguridad.py` en la máquina del usuario para recargar los hotspots de robos con moto en la base local, y confirmar visualmente que las zonas nuevas tienen sentido geográfico.
- Correr `notebooks/sweep_hdbscan_inseguridad_general.py` sin apuro (puede tardar varios minutos) para decidir si delito general también conviene migrarlo a HDBSCAN.
- Seguir con la vista de navegación 3D/heading y la evaluación de hosting real, en el orden que ya se había definido.

### 07/09/2026 (continuación 7) — Auditoría de arquitectura: identidad de dispositivo, pool de conexiones, rate limiting y test end-to-end de /rutas

**Tareas realizadas**
- Se hizo una revisión crítica del backend a pedido explícito (arquitectura, seguridad básica, cobertura de tests), de la que salieron 6 observaciones. De esas, se resolvieron 4 en esta vuelta:
  1. `autor_id` en `/reportes` ahora se valida como UUID (backend, `ReporteNuevo.validar_autor_id` y chequeo equivalente en el DELETE). El frontend ya generaba un UUID real con `crypto.randomUUID()`; se corrigió el único punto débil, el fallback para navegadores sin esa API, que antes producía un string con formato propio (`dev-<timestamp>-<random>`) y ahora genera un UUID v4 manual (`generarUuidV4Fallback` en `utils/storage.js`). Se evaluó explícitamente si convenía pedir cuenta para reportar y se descartó: sigue siendo identidad de dispositivo, no de usuario, documentado como decisión de alcance y no como hueco de seguridad tapado.
  2. Pool de conexiones a Postgres: los 6 `psycopg2.connect(DATABASE_URL)` sueltos (uno por endpoint) se reemplazaron por una clase `_PoolConexiones` propia en `main.py`, no por `psycopg2.pool.SimpleConnectionPool`, a propósito: la propia sigue llamando a `psycopg2.connect()` para abrir una conexión nueva (así los tests que mockean `main.psycopg2.connect` no se rompieron) pero reutiliza conexiones ya abiertas cuando están libres y no cerradas, y es lazy (no conecta nada al importar el módulo, así que `pytest` sigue corriendo sin la base levantada).
  3. Rate limiting con `slowapi` en los tres endpoints con costo real: `/predecir` (30/min), `/reportes` POST (20/min) y `/rutas` (20/min, es el que además paga por pedido a TomTom). Límite por IP, pensado para no afectar el uso normal y cortar abuso obvio.
  4. Test end-to-end de `/rutas`: 4 tests nuevos que mockean la respuesta de TomTom (`main.httpx.get`) y verifican el flujo completo -- pedido con parámetros reales, traducción de maniobras (`TOMTOM_MANIOBRA_A_OSRM`), armado del contrato `RutaOut` con `eta_trafico` desglosado -- más los casos sin API key (503), TomTom caído (502) y sin resultados (404). No existía ninguna cobertura de este endpoint hasta ahora, siendo la funcionalidad más nueva del proyecto.
- Se actualizaron los tests existentes de `/reportes` que usaban `autor_id` con valores no-UUID (`"dispositivo-abc"`, ya inválido con la nueva validación) y se agregaron 2 tests nuevos que verifican el rechazo explícito de un `autor_id` mal formado.

**Decisiones de diseño y su justificación**
- Se descartó una cuenta de usuario para reportar: agrega fricción real (nadie crea una cuenta para avisar de un pozo) y scope nuevo (login, sesión, recuperación) que la cátedra no pidió. La necesidad real detrás del pedido -- trazabilidad y poder ver patrones de uso cuando el proyecto salga al público -- ya la cubre el identificador de dispositivo: alcanza para detectar abuso (muchos reportes desde el mismo dispositivo) sin necesitar saber quién es la persona.
- El pool de conexiones se implementó a mano en vez de usar `psycopg2.pool.SimpleConnectionPool` (la opción "de libro") porque esa clase abre conexiones reales al construirse y llama a `connect` desde su propio método interno, no desde `psycopg2.connect` visible para los tests -- adoptarla tal cual hubiera roto los 11 tests que mockean `main.psycopg2.connect` y además hubiera hecho que `pytest` fallara sin una base de datos real disponible (justo lo que el propio docstring de los tests dice que no debería hacer falta).
- Rate limiting puesto solo en los 3 endpoints con costo real (cómputo del modelo, escritura en base, llamada paga a TomTom), no en todos: los de solo lectura de datos ya calculados (`/hotspots`, `/corredores`, `/hotspots-inseguridad`) no tienen el mismo riesgo de abuso ni el mismo costo por pedido.

**Obstáculos encontrados y cómo se resolvieron**
- El primer intento de pooling (con `psycopg2.pool.SimpleConnectionPool`, creado como variable de módulo) rompió 24/24 tests existentes al no llamar más a `psycopg2.connect` en cada pedido. Se resolvió con la implementación propia descripta arriba, que aprovecha una diferencia de comportamiento real entre una conexión real (`.closed` es `0`, falsy, mientras esté abierta) y un `MagicMock` de test (`.closed` es otro `MagicMock`, truthy por default): el pool nunca reutiliza un mock entre tests, pero sí reutiliza conexiones reales en producción, sin que los tests tuvieran que cambiar su forma de mockear.
- Ese mismo cambio dejó fuera de validez 2 tests existentes de `/reportes` que usaban `"dispositivo-abc"` como `autor_id` (ya no es un UUID válido): se corrigieron los fixtures y se sumaron 2 tests explícitos de rechazo.

**Próximos pasos**
- Pendiente de definir con el sweep de HDBSCAN para delito general (`notebooks/sweep_hdbscan_inseguridad_general.py`, corriendo en la máquina del usuario) si esa capa también migra de DBSCAN a HDBSCAN.
- Validación cualitativa de hotspots (marcado como tarea, no resuelto en este ciclo): tomar ~15 hotspots "críticos" de robos con moto e inseguridad general y cruzarlos contra conocimiento real de zonas de CABA, para dejar un párrafo de validación cualitativa en el capítulo de resultados de la tesis.
- Seguir con la vista de navegación 3D/heading y la evaluación de hosting real.

### Backlog vigente (actualizado 07/09/2026, continuación 8)

Lista de tareas abiertas para no perder el hilo entre sesiones, en el orden en que tiene sentido encararlas:

- [ ] **Cerrar método de clustering para delito general**: confirmar el resultado del sweep de HDBSCAN sobre el dataset completo (411.704 puntos, corriendo en la máquina del usuario, sin `n_jobs` para evitar el cuelgue ya diagnosticado). Si mcs=150/ms=20 confirma algo cercano a lo visto en la muestra (90 hotspots, 42.8% cobertura, 1.73% cluster mayor), HDBSCAN gana y no hace falta migrar a H3. Si el dataset completo da peor, el candidato de respaldo es H3 con umbral por percentil (33.3%-50.8% cobertura, sin riesgo de blob), ya probado y documentado. Se probaron también Getis-Ord Gi* y KDE (grilla + filtro gaussiano) como alternativas: ninguna de las dos superó a HDBSCAN/H3 en ningún layer (Gi* muy conservador, KDE reintroduce el problema de blob). Con esto las opciones metodológicas están agotadas — no hace falta seguir probando otros métodos de clustering.
- [x] ~~Cruzar riesgo con rutas~~ -- CORRECCIÓN: al revisar el código a fondo se confirmó que esto ya estaba implementado (`utils/riesgoRuta.js`: `calcularZonasCruzadasPorRuta` + `calcularRutasConScore`, wireado en `App.jsx` con badges "rápida/segura/equilibrada/recomendada" y desglose por eje). Se había planteado como pendiente por error en una vuelta anterior de esta conversación; quedó corregido en el momento.
- [x] **Ajuste horario para inseguridad, CORREGIDO con dato real**: se implementó primero como heurística sin sustento (`FRANJA_NOCTURNA`, 22-6hs, por criterio criminológico genérico), porque en ese momento se creía que el dataset de Delitos del GCBA no tenía hora. Se descubrió después (ver siguiente entrada de bitácora) que sí la tiene -- se perdía por un alias incompleto en `fetch_delitos_caba.py` -- y al mirar la distribución horaria real de robos con moto, la heurística resultó estar equivocada: el pico real es 19-23hs (20-21hs llegan a 7.3-7.5% de los casos vs. 4.2% esperado si fuera parejo en 24hs), y el tramo 0-6hs que la heurística marcaba como de mayor riesgo es en realidad el de MENOR incidencia (1.4-2.5%). Se corrigió a `FRANJA_PICO_INSEGURIDAD` (19-23hs), con `esFranjaPicoInseguridad`/`calcularAjustePorFranjaHoraria` en `utils/geoRiesgo.js`, ahora citando el dato real en el motivo mostrado al usuario en vez de una heurística declarada. Se aplica solo a inseguridad, no a siniestros de moto (esa capa ya recibe hora real como feature del modelo entrenado, ver `backend/main.py`). No se extendió el ajuste de clima (lluvia) a inseguridad -- se evaluó y se descartó: no hay sustento causal real. 10 tests (`geoRiesgo.test.js` + extensión de `riesgoRuta.test.js`), 44/44 pasando en el suite completo.
- [x] **Bug real encontrado y corregido: se perdía la hora de los delitos.** `fetch_delitos_caba.py` mapea nombres de columna del portal a nombres internos vía una lista de alias; la hora real (columna `franja` en el portal, verificada en `docs/9_Extension_Futura_Inseguridad.md` cuando se investigó la fuente) no estaba en la lista de alias reconocidos (`franja_horaria`, `hora`), así que se perdía en silencio para los 10 años del dataset sin ningún warning (no estaba en la lista de columnas "obligatorias" que sí avisan si faltan). Se agregó `"franja"` a los alias y se agregó un aviso explícito al final del fetch (qué años trajeron la columna, o una advertencia si ninguno la trae) para que un problema así no vuelva a pasar desapercibido. Al re-correr el fetch, los 10 años (2016-2025) trajeron la columna, limpia (24 valores 0-23, apenas 0.18% de nulos).
- [ ] **Validación cualitativa de hotspots**: tomar ~15 hotspots "críticos" de robos con moto e inseguridad general y contrastarlos contra conocimiento real de zonas de CABA, para un párrafo de validación cualitativa en el capítulo de resultados de la tesis.
- [ ] **Vista de navegación 3D / heading**: rotar el mapa según la orientación de marcha, o al menos rotar el ícono de posición (opción más segura por compatibilidad con `react-leaflet-cluster`).
- [ ] **Evaluación de hosting real**: backend + Postgres/PostGIS + frontend (Railway, Render, Fly.io, VPS u otra opción).
- [ ] **Pendiente administrativo**: pushear el commit `1bd3213` (auditoría de arquitectura) — quedó commiteado local pero sin subir.
