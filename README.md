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

Los CSV crudos de siniestralidad (`data/siniestros_viales_hechos.csv`, `data/siniestros_viales_victimas.csv`) no están en el repo por tamaño — se descargan de [data.buenosaires.gob.ar](https://data.buenosaires.gob.ar).

## Estructura

```
backend/        API FastAPI, modelo entrenado, tests
frontend/       App React (mapa, rutas, reportes)
notebooks/      Análisis exploratorio, clustering, entrenamiento del modelo
docs/           Documentación del proyecto (resultados, extensiones futuras)
```
