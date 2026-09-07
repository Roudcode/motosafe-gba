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

Queda en `http://localhost:8000`. `GET /hotspots` devuelve las 430 zonas con el nivel de riesgo recalculado en vivo por el modelo.

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
