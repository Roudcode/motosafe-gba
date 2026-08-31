# MotoSafe GBA — Guía Completa del Proyecto

Este documento explica qué es el proyecto, cómo está armado hoy, y qué de todo lo que ves funcionando es real y qué sigue siendo una simplificación. Es el documento para entender el panorama completo, no para ejecutar comandos (eso está en el Manual de Operación).

---

## 1. Qué es MotoSafe GBA, en una frase

Una aplicación que muestra en un mapa qué tan riesgoso es circular en moto por distintas zonas de CABA, combinando un modelo de Machine Learning entrenado con datos reales de siniestros, clima en tiempo real, y reportes de los propios usuarios.

**Estado real a esta altura:** ya no es una maqueta. El mapa muestra predicciones calculadas en vivo por un modelo entrenado con 23.343 siniestros reales — no una regla inventada.

---

## 2. El diagrama completo, actualizado

```
┌──────────────────┐
│   TU NAVEGADOR     │
│  (localhost:5173)  │
└──────────────────┘
          │
          ▼
┌──────────────────┐        ┌───────────────────┐        ┌──────────────────┐
│  Frontend React     │ ──── │   Backend FastAPI    │ ──── │  PostgreSQL +      │
│  (Vite + Leaflet)   │      │   (localhost:8000)   │      │  PostGIS (Docker)  │
└──────────────────┘        └───────────────────┘        │  tabla:            │
          │                            │                    │  hotspots_riesgo   │
          │                            ▼                    │  (430 filas)       │
          ▼                  ┌───────────────────┐        └──────────────────┘
   Open-Meteo API            │  Modelo entrenado    │
   (clima real)               │  (Random Forest,      │
          │                    │  modelo_final.pkl)    │
          ▼                  └───────────────────┘
   OSRM (rutas reales)                  ▲
          │                            │
          ▼                  ┌───────────────────┐
   Nominatim (direcciones)   │  hotspots_contexto.csv │
                              │  (comuna/vía/contra-   │
                              │  parte típica por zona)│
                              └───────────────────┘
```

**Cómo funciona un pedido al mapa, de punta a punta:**
1. El frontend le pide `/hotspots` al backend.
2. El backend trae los 430 hotspots de la base de datos (PostGIS).
3. Para cada uno, arma el contexto típico de esa zona (desde `hotspots_contexto.csv`: comuna, tipo de vía, contraparte más común, edad/sexo promedio) más la hora y el día **actuales**.
4. Le pasa ese contexto al modelo entrenado (`modelo_final.pkl`), que devuelve una probabilidad de leve/grave/mortal.
5. El backend traduce esa probabilidad a un nivel (bajo/medio/alto/crítico) y se lo manda al frontend.
6. El frontend pinta el mapa con esos niveles reales.

---

## 3. Qué es 100% real, y qué sigue siendo simplificación

### Real, con datos y procesamiento genuinos:
- Los 65.818 siniestros de CABA descargados de data.buenosaires.gob.ar (2019-2025).
- Los 23.343 casos de motociclistas, limpios, con coordenadas válidas.
- Los 430 hotspots, identificados con DBSCAN calibrado correctamente (no el primer intento fallido con 300m, que fusionaba toda la ciudad).
- El modelo Random Forest, entrenado con esos 23.343 casos, evaluado con F1-score y matriz de confusión (no accuracy, que hubiera mentido por el desbalance de clases).
- Las predicciones que ves en el mapa: son la salida real del modelo, no un número fijo.
- El clima (Open-Meteo) y las rutas (OSRM): servicios externos reales, no simulados.

### Simplificación consciente, documentada:
- **La hora y el día son iguales para las 430 zonas en cada pedido** (la hora actual del servidor). Esto significa que buena parte de la variación de riesgo entre zonas viene de su comuna/vía/contraparte típica, no de un patrón horario propio de cada lugar. Es una limitación real, no un error.
- **40% de las edades de víctimas son estimadas** (mediana), no datos reales — el dataset original solo tiene edad para el 60% de los casos de moto.
- **El "quién" que usa el backend para predecir es el promedio histórico de cada zona**, no la persona real que está mirando el mapa en ese momento.
- **Reportes y filtros del usuario viven en su propio navegador** (localStorage), no en una base de datos compartida — no hay componente colaborativo real todavía entre usuarios distintos.
- **Alcance geográfico: solo CABA.** El conurbano bonaerense no tiene un dataset geolocalizado equivalente disponible públicamente (se buscó y no se encontró).

---

## 4. El stack completo, y para qué sirve cada pieza

| Pieza | Qué es | Para qué sirve acá |
|---|---|---|
| Docker Desktop | Corre "cajas" (contenedores) con software preinstalado | Levanta PostgreSQL sin instalarlo directo en Windows |
| PostgreSQL + PostGIS | Base de datos con soporte geoespacial | Guarda los 430 hotspots con sus coordenadas |
| Python 3.12 | Lenguaje del backend y del análisis de datos | Todo el EDA, el modelo, y la API |
| FastAPI | Framework para construir APIs en Python | Sirve `/hotspots` y `/predecir` |
| scikit-learn | Librería de Machine Learning | Entrena y ejecuta el Random Forest |
| pandas | Manipulación de tablas de datos | Limpieza, transformación, todo el EDA |
| Jupyter | Entorno de código interactivo por celdas | Donde se hizo todo el análisis y entrenamiento |
| React + Vite | Librería/herramienta para la interfaz visual | El mapa y toda la UI |
| Leaflet + react-leaflet-cluster | Librería de mapas y agrupamiento de puntos | El mapa en sí, con los 430 puntos agrupados |
| Git + GitHub | Control de versiones y respaldo remoto | Historial del proyecto, respaldo fuera de tu PC |

---

## 5. Estructura de carpetas, actualizada

```
motosafe-gba/
├── backend/
│   ├── venv/                    → librerías Python de este proyecto
│   ├── main.py                  → la API (endpoints /hotspots, /predecir)
│   ├── cargar_hotspots.py       → script que cargó los 430 hotspots a la base
│   ├── modelo_final.pkl         → el modelo entrenado (Random Forest)
│   ├── columnas_modelo.pkl      → el orden de columnas que el modelo necesita
│   └── hotspots_contexto.csv    → comuna/vía/contraparte típica por zona
├── frontend/
│   └── src/
│       ├── App.jsx              → toda la lógica e interfaz
│       └── App.css              → estilos
├── notebooks/
│   └── 01_eda_hotspots_moto.ipynb  → todo el análisis: limpieza, clustering, modelos
├── data/                        → CSV pesados, NO se suben a GitHub
│   ├── motos_limpio.csv
│   ├── motos_con_clusters.csv
│   ├── hotspots_moto_caba.csv
│   ├── hotspots_contexto.csv
│   ├── modelo_final.pkl (copia)
│   └── siniestros_viales_hechos.csv / victimas.csv (los originales del gobierno)
├── docker-compose.yml
├── requirements.txt
└── .gitignore
```

---

## 6. Glosario rápido

| Término | Qué significa |
|---|---|
| Endpoint | Una dirección de la API a la que le pedís algo puntual (`/hotspots`, `/predecir`) |
| DBSCAN | Algoritmo que agrupa puntos geográficos cercanos — así se armaron los 430 hotspots |
| Random Forest | Algoritmo de Machine Learning que combina muchos "árboles de decisión" |
| F1-score / recall | Métricas para medir qué tan bien predice un modelo, mejores que "accuracy" cuando hay pocas muestras de una clase (acá, pocos casos mortales) |
| One-hot encoding | Convertir una categoría de texto ("AUTO", "MOTO") en columnas de 0/1 que un modelo pueda usar |
| Hardcodeado | Un valor escrito fijo en el código en vez de venir de una base de datos o cálculo real |
| localStorage | Memoria del propio navegador — lo que se guarda ahí no viaja a ningún servidor |

---

## 7. Lo que falta, con honestidad

1. **Conurbano bonaerense** — sigue sin resolverse. Alcance real: CABA.
2. **Persistencia compartida** de reportes y clima en la base de datos (hoy es solo local del navegador de cada usuario).
3. **La limitación de "hora/día iguales para todas las zonas"** — se podría refinar pidiéndole al modelo predicciones por franja horaria específica en vez de solo "ahora".
4. Documentado, no resuelto: el modelo predice mejor "leve" que "grave"/"mortal" por separado — es una limitación real de las variables disponibles (falta velocidad, uso de casco, alcohol — datos que el dataset del gobierno no tiene).
