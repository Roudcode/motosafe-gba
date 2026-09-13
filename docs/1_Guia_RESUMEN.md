# MotoSafe GBA — Guía Completa del Proyecto

Este documento explica qué es el proyecto, cómo está armado hoy, y qué de todo lo que ves funcionando es real y qué sigue siendo una simplificación. Es el documento para entender el panorama completo, no para ejecutar comandos (eso está en el Manual de Operación).

---

## 1. Qué es MotoSafe GBA, en una frase

Una aplicación que muestra exposición histórica registrada en zonas de CABA. El modelo clasifica la gravedad esperable **si ocurre un siniestro**; no estima la probabilidad de sufrir uno durante un viaje. Se complementa con clima actual, reportes y una capa histórica de inseguridad.

**Estado real a esta altura:** ya no es una maqueta. El mapa muestra predicciones calculadas en vivo por un modelo entrenado con 23.343 siniestros reales (que ahora también incluye el índice de inseguridad de cada comuna como variable) — no una regla inventada. Además de los hotspots puntuales, la app tiene una vista de corredores (avenidas completas con score de riesgo) y una capa de inseguridad histórica con sus propios hotspots (delito general y robos con moto, calculados con DBSCAN; los de siniestros usan HDBSCAN, ver más abajo).

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
│  (Vite + MapLibre)  │      │   (localhost:8000)   │      │  PostGIS (Docker)  │
└──────────────────┘        └───────────────────┘        │  tabla:            │
          │                            │                    │  hotspots_riesgo   │
          │                            ▼                    │  (740 filas)       │
          ▼                  ┌───────────────────┐        └──────────────────┘
   Open-Meteo API            │  Modelo entrenado    │
   (clima real)               │  (Random Forest,      │
          │                    │  modelo_final.pkl)    │
          ▼                  └───────────────────┘
   Nominatim (direcciones)              ▲
          │                            │
          ▼                  ┌───────────────────┐
   Backend → TomTom          │  hotspots_contexto.csv │
   (rutas + tráfico vivo)    │  (comuna/vía/contra-   │
                              │  parte típica por zona)│
                              └───────────────────┘
```

**Cómo funciona un pedido al mapa, de punta a punta:**
1. El frontend le pide `/hotspots` al backend.
2. El backend trae los 740 hotspots de la base de datos (PostGIS).
3. Para cada uno, arma el contexto típico de esa zona (desde `hotspots_contexto.csv`: comuna, tipo de vía, contraparte más común, edad/sexo promedio) más la hora y el día **actuales**.
4. Le pasa ese contexto al modelo entrenado (`modelo_final.pkl`), que devuelve una probabilidad de leve/grave/mortal.
5. El backend traduce esa probabilidad a un nivel (bajo/medio/alto/crítico) y se lo manda al frontend.
6. El frontend pinta el mapa con esos niveles reales.

---

## 3. Qué es 100% real, y qué sigue siendo simplificación

### Real, con datos y procesamiento genuinos:
- Los 65.818 siniestros de CABA descargados de data.buenosaires.gob.ar (2019-2025).
- Los 23.343 casos de motociclistas, limpios, con coordenadas válidas.
- Los 740 hotspots, identificados con HDBSCAN (min_cluster_size=12, min_samples=3) tras evaluar también DBSCAN con un barrido sistemático de parámetros (eps 40-120m x min_samples 6-15, que llegó a 412 hotspots/49.9% de cobertura como mejor punto seguro). HDBSCAN no usa un radio fijo, así que se adapta a la densidad local de cada zona en vez de forzar un único radio para toda la ciudad, y esto permitió llegar al 75.6% de cobertura de los siniestros históricos sin arriesgar el efecto de "blob" (el cluster más grande queda en 0.41% del total, más seguro incluso que el 0.73% de la versión DBSCAN).
- El modelo Random Forest, entrenado con esos 23.343 casos y evaluado con F1-score y matriz de confusión. La evaluación temporal independiente sigue pendiente: 2025 intervino en selección de configuraciones, por lo que no debe presentarse como test completamente no visto.
- Las predicciones que ves en el mapa: son la salida real del modelo, no un número fijo.
- El clima (Open-Meteo), la geocodificación de direcciones (Nominatim) y el cálculo de rutas con tráfico en vivo (TomTom, vía el backend): servicios externos reales, no simulados.
- Los 805 hotspots de inseguridad (303 de delito general con DBSCAN + 502 de robos con moto con HDBSCAN, tras una segunda calibración que llevó su cobertura de 14.1% a 74.3%), sobre delitos reales descargados de data.buenosaires.gob.ar.
- El score de ruta compara exposición histórica registrada de siniestros e inseguridad, con desglose visible. No debe llamarse una garantía de ruta más segura.

### Simplificación consciente, documentada:
- **La hora y el día son iguales para las 740 zonas en cada pedido** (la hora actual del servidor). Esto significa que buena parte de la variación de riesgo entre zonas viene de su comuna/vía/contraparte típica, no de un patrón horario propio de cada lugar. Es una limitación real, no un error.
- **El mapa no estima ocurrencia por viaje ni cobertura completa:** sus etiquetas comparan exposición histórica en las zonas disponibles. Una ruta fuera de la cobertura comparable no puede interpretarse como más segura.
- **40% de las edades de víctimas son estimadas** (mediana), no datos reales — el dataset original solo tiene edad para el 60% de los casos de moto.
- **El "quién" que usa el backend para predecir es el promedio histórico de cada zona**, no la persona real que está mirando el mapa en ese momento.
- **Los reportes ahora son colaborativos de verdad**: se guardan en la base (tabla `reportes_colaborativos`) y los ve cualquier usuario, no solo quien los creó. Cada categoría tiene su propia vigencia (un corte vence en 12hs, un pozo en el pavimento en 30 días) — pasado ese tiempo dejan de aparecer en el mapa aunque sigan en la base como histórico.
- **Los filtros de nivel, favoritos y tema siguen viviendo en el navegador de cada usuario** (localStorage) — eso sí es preferencia individual, no dato colaborativo, y no tendría sentido compartirlo entre usuarios distintos.
- **Alcance geográfico: solo CABA.** El conurbano bonaerense no tiene un dataset geolocalizado equivalente disponible públicamente (se buscó y no se encontró).
- **La cobertura de hotspots de siniestro es del 75.6%, no del 100%**: casi un cuarto de los siniestros históricos (24.4%) caen fuera de cualquier hotspot ("aislados"), casos demasiado dispersos como para formar una zona compacta. Es una mejora real frente al 49.9% de la calibración anterior con DBSCAN, lograda al pasar a HDBSCAN (que se adapta a la densidad local en vez de usar un radio fijo), pero seguir subiendo la cobertura sin límite empieza a arriesgar el mismo efecto de "blob" que se descartó al calibrar DBSCAN — es un trade-off consciente entre cobertura y precisión geográfica, no una limitación que se pueda simplemente subir a cero.
- **El modelo prioriza recall de casos graves/mortales por sobre accuracy general, a propósito**: la configuración elegida (`class_weight="balanced_subsample"`, hojas mínimas de 5) detecta más casos graves y mortales que una configuración estándar, a cambio de generar más falsas alarmas en casos leves y una accuracy general más baja. Es la decisión correcta para una app de seguridad vial (perderse un caso grave es peor que una falsa alarma), pero es una decisión de producto explícita, no la que un benchmark ciego hubiera elegido.
- **El índice de inseguridad es histórico y anual, no en vivo**: se calcula una vez sobre los últimos 3 años completos de delitos por comuna, y se actualiza a mano cuando el GCBA publica el año siguiente — a diferencia del clima o de la hora, que sí son en vivo en cada predicción. Esto está explícito en la interfaz (panel de Capas) para que no se confunda con un dato en tiempo real.
- **Siniestros e inseguridad no se fusionan en un único número inventado**: se suman porque ambos ya están en la misma escala ordinal (percentiles calculados dentro de cada dataset por separado), pero se muestran siempre desglosados — no hay una ponderación arbitraria entre "cuánto pesa un choque contra cuánto pesa un robo", porque no hay datos que la justifiquen.

---

## 4. El stack completo, y para qué sirve cada pieza

| Pieza | Qué es | Para qué sirve acá |
|---|---|---|
| Docker Desktop | Corre "cajas" (contenedores) con software preinstalado | Levanta PostgreSQL sin instalarlo directo en Windows |
| PostgreSQL + PostGIS | Base de datos con soporte geoespacial | Guarda los 740 hotspots con sus coordenadas |
| Python 3.12 | Lenguaje del backend y del análisis de datos | Todo el EDA, el modelo, y la API |
| FastAPI | Framework para construir APIs en Python | Sirve `/hotspots` y `/predecir` |
| scikit-learn | Librería de Machine Learning | Entrena y ejecuta el Random Forest |
| pandas | Manipulación de tablas de datos | Limpieza, transformación, todo el EDA |
| Jupyter | Entorno de código interactivo por celdas | Donde se hizo todo el análisis y entrenamiento |
| React + Vite | Librería/herramienta para la interfaz visual | El mapa y toda la UI |
| MapLibre GL | Librería de mapas vectoriales | El mapa, sus capas y la navegación visual |
| Git + GitHub | Control de versiones y respaldo remoto | Historial del proyecto, respaldo fuera de tu PC |

---

## 5. Estructura de carpetas, actualizada

```
motosafe-gba/
├── backend/
│   ├── venv/                        → librerías Python de este proyecto
│   ├── main.py                      → la API (hotspots, corredores, hotspots-inseguridad, predecir, reportes)
│   ├── cargar_hotspots.py           → script que cargó los 740 hotspots a la base
│   ├── cargar_corredores.py         → carga la tabla de corredores de riesgo
│   ├── cargar_hotspots_inseguridad.py → carga la tabla de hotspots de inseguridad
│   ├── modelo_final.pkl             → el modelo entrenado (Random Forest, con índice de inseguridad)
│   ├── columnas_modelo.pkl          → el orden de columnas que el modelo necesita
│   ├── hotspots_contexto.csv        → comuna/vía/contraparte típica por zona
│   ├── indice_inseguridad_comuna.csv → índice de inseguridad por comuna (0-1)
│   └── tests/test_main.py           → 24 tests de la API
├── frontend/
│   └── src/
│       ├── App.jsx                  → lógica e interfaz principal
│       ├── App.css                  → estilos
│       ├── constants.js             → umbrales, paletas, catálogos fijos
│       ├── components/              → CapasPanel, CapaCalor, Onboarding, etc.
│       └── utils/                   → geoRiesgo.js, tiempo.js, ui.js
├── notebooks/
│   ├── 01_eda_hotspots_moto.ipynb   → limpieza, clustering y modelos originales
│   ├── fetch_delitos_caba.py        → descarga delitos de CABA (correr a mano, necesita internet real)
│   ├── construir_indice_inseguridad.py → arma el índice de inseguridad por comuna
│   ├── identificar_hotspots_inseguridad.py → DBSCAN sobre delitos (general y con moto)
│   └── reentrenar_modelo.py         → reproduce el entrenamiento sumando el índice de inseguridad
├── data/                            → CSV pesados, NO se suben a GitHub
│   ├── motos_limpio.csv / motos_con_clusters.csv / hotspots_moto_caba.csv
│   ├── delitos_caba.csv             → 1.387.622 delitos, 2016-2025
│   ├── hotspots_inseguridad_general.csv / _moto.csv
│   ├── indice_inseguridad_comuna.csv
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
| HDBSCAN | Algoritmo que agrupa puntos geográficos cercanos adaptándose a la densidad local — así se armaron los 740 hotspots de siniestro (los de inseguridad siguen con DBSCAN, un radio fijo) |
| Random Forest | Algoritmo de Machine Learning que combina muchos "árboles de decisión" |
| F1-score / recall | Métricas para medir qué tan bien predice un modelo, mejores que "accuracy" cuando hay pocas muestras de una clase (acá, pocos casos mortales) |
| One-hot encoding | Convertir una categoría de texto ("AUTO", "MOTO") en columnas de 0/1 que un modelo pueda usar |
| Hardcodeado | Un valor escrito fijo en el código en vez de venir de una base de datos o cálculo real |
| localStorage | Memoria del propio navegador — lo que se guarda ahí no viaja a ningún servidor |
| Índice de inseguridad | Número (0-1) por comuna, calculado sobre los últimos 3 años de delitos del GCBA; entra al modelo como una variable numérica más |
| Hotspot de inseguridad | Zona con delitos concentrados, encontrada con DBSCAN sobre el dataset de delitos (igual método que los hotspots de siniestros, dataset distinto) |
| Score de ruta / desglose | El puntaje de riesgo de una ruta trazada, que suma siniestros e inseguridad cruzados pero siempre muestra cuánto aporta cada eje por separado |
| Percentil (para nivel de riesgo) | El nivel bajo/medio/alto/crítico de cada zona no es un umbral fijo, es relativo: se calcula según en qué percentil (25/75/95) cae esa zona dentro de su propio dataset |

---

## 7. Lo que falta, con honestidad

1. **Conurbano bonaerense** — sigue sin resolverse. Alcance real: CABA, tanto para siniestros como para inseguridad.
2. **La limitación de "hora/día iguales para todas las zonas"** — se podría refinar pidiéndole al modelo predicciones por franja horaria específica en vez de solo "ahora".
3. Documentado, no resuelto: el modelo predice mejor "leve" que "grave"/"mortal" por separado — es una limitación real de las variables disponibles (falta velocidad, uso de casco, alcohol — datos que el dataset del gobierno no tiene).
4. **El índice de inseguridad se actualiza a mano, una vez al año** — no hay una API en vivo del GCBA para delitos, así que no se puede automatizar como el clima.
5. **La capa de inseguridad general y la de robos con moto son excluyentes en el mapa** (no se pueden ver juntas): se decidió así porque se superponen bastante y mostrarlas a la vez solo duplicaría puntos sobre el mismo hecho, pero no está evaluado a fondo si convendría una tercera vista combinada.
