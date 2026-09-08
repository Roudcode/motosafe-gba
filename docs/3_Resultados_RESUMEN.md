# MotoSafe GBA — Resultados del Modelo Predictivo

Este documento reúne la metodología y los resultados del análisis de datos y el modelo de Machine Learning. Está escrito para poder usarse directamente como base de la sección de resultados de la tesis.

---

## 1. Fuente y preparación de los datos

**Fuente:** data.buenosaires.gob.ar, dataset "Siniestros viales" (Secretaría de Transporte, Observatorio de Movilidad y Seguridad Vial), dos archivos:
- **Hechos**: 65.818 siniestros, 2019–septiembre 2025, con coordenadas.
- **Víctimas**: 75.197 registros (relación 1 a N con hechos), con modo de desplazamiento, edad y sexo.

**Limpieza aplicada:**
- 1 fila con error de exportación de Excel (`#¡REF!`) descartada.
- Normalización de mayúsculas/minúsculas inconsistentes en columnas categóricas (`MOTO` vs `moto`, etc.).
- Normalización del campo comuna, que venía en dos formatos mezclados (`"Comuna 1"` y `"1"`).
- Filtrado a coordenadas válidas: 62.787 de 65.817 (95,4%).
- Filtrado a víctimas en moto: **23.343 siniestros** con coordenadas válidas — la base de trabajo.

---

## 2. Identificación de hotspots (DBSCAN, luego HDBSCAN)

**Primer intento (300m de radio, mínimo 10 casos):** fusionó casi toda la ciudad en un solo cluster de 23.068 puntos — efecto de "encadenamiento" típico de DBSCAN en zonas urbanas densas.

**Calibración DBSCAN (60 metros de radio, mínimo 10 casos por cluster):** 430 hotspots geográficamente coherentes, 67,9% de los siniestros clasificados como "aislados" (sin recurrencia puntual). Una vuelta posterior de barrido sistemático de parámetros (eps 40-120m x min_samples 6-15) mejoró esto a 412 hotspots con 49,9% de cobertura como mejor punto seguro (cluster más grande por debajo del umbral de "blob").

**Resultado final, en producción (HDBSCAN, min_cluster_size=12, min_samples=3):** se migró de DBSCAN a HDBSCAN porque este último se adapta a la densidad local de cada zona en vez de usar un radio fijo para toda la ciudad. **740 hotspots**, **75,6% de cobertura** de los siniestros históricos (24,4% quedan "aislados", casos demasiado dispersos como para formar zona compacta), con el cluster más grande ocupando apenas **0,41%** del total — más seguro incluso que la versión DBSCAN. Es la configuración vigente al momento de escribir esto.

**Hallazgo destacado:** el hotspot con más muertes (Donado, Saavedra — 4 mortales en 52 casos) no es el de mayor volumen (Av. Ricardo Balbín, Saavedra — 88 casos, 3 mortales). Confirma con datos reales que frecuencia y severidad son dimensiones distintas del riesgo. (Este hallazgo surgió durante la calibración DBSCAN y se sostiene igual en la migración a HDBSCAN.)

---

## 3. Modelo predictivo — variables utilizadas

**Variable objetivo:** gravedad del siniestro (`LEVE` / `GRAVE` / `MORTAL`).

**Distribución real (fuerte desbalance de clases):**
| Clase | Casos | % |
|---|---|---|
| LEVE | 21.756 | 93,2% |
| GRAVE | 1.304 | 5,6% |
| MORTAL | 283 | 1,2% |

**Variables predictoras, dos versiones:**

*Versión 1 (contexto):* hora, día de la semana, comuna, tipo de vía, contraparte del siniestro. 61 variables tras codificación (one-hot encoding).

*Versión 2 (contexto + víctima):* se agregan edad y sexo del motociclista, obtenidos del archivo de víctimas y unidos por `id_siniestro`. 66 variables.

**Limitación documentada:** edad disponible en 60% de los casos (14.088 de 23.338); el 40% restante se completó con la mediana (32 años) y se marcó con un indicador binario de "edad estimada" para que el modelo distinga entre dato real y estimado. Se filtraron edades imposibles (menores de 14 o mayores de 95 años) antes de imputar.

---

## 4. Comparación de modelos

Todos entrenados con `train_test_split` estratificado (80/20), `random_state=42`, y compensación de desbalance (`class_weight='balanced'` en Random Forest, `sample_weight` calculado con `compute_sample_weight` en XGBoost).

| # | Modelo | Variables | Recall MORTAL | Recall GRAVE | Precision GRAVE |
|---|---|---|---|---|---|
| 1 | Random Forest | Contexto (5 var.) | 0,39 | 0,12 | 0,09 |
| 2 | XGBoost | Contexto (5 var.) | 0,38 | 0,35 | 0,08 |
| **3** | **Random Forest** | **Contexto + edad/sexo** | **0,45** | **0,73** | 0,11 |
| 4 | XGBoost | Contexto + edad/sexo | 0,29 | 0,52 | 0,15 |

**Modelo elegido: #3 (Random Forest con edad/sexo), guardado en `modelo_final.pkl`.**

También se probó una versión binaria (LEVE vs. GRAVE+MORTAL combinadas) con el modelo #1: dio peor resultado (recall SERIO: 0,30) que el modelo de 3 clases — simplificar el problema no mejoró la detección de casos serios, en este caso específico.

---

## 5. Cómo se traduce la probabilidad del modelo en un nivel de riesgo (bajo/medio/alto/crítico)

El modelo no devuelve "bajo/medio/alto/crítico" directamente: devuelve una probabilidad para cada clase (LEVE/GRAVE/MORTAL). El backend (`nivel_desde_probabilidades` en `main.py`) traduce esas probabilidades a un nivel con estos cortes:

| Condición | Nivel |
|---|---|
| p(MORTAL) ≥ 0.20 | Crítico |
| p(MORTAL) ≥ 0.10 o p(GRAVE) ≥ 0.40 | Alto |
| p(GRAVE) ≥ 0.20 | Medio |
| resto | Bajo |

**Por qué el umbral de MORTAL es más bajo que el de GRAVE:** como se documentó en la sección anterior, la precisión de GRAVE se mantiene baja (0.08–0.15) en las cuatro versiones probadas — el modelo genera bastantes falsas alarmas de "grave". Frente a esa limitación, se decidió priorizar no perder señal de MORTAL aun a costa de más falsos positivos: alcanza con menos probabilidad acumulada de MORTAL que de GRAVE para escalar el nivel de riesgo mostrado en el mapa. Es una decisión de diseño explícita, no un valor arbitrario, coherente con el criterio de "mejor sobre-alertar que no alertar" en seguridad vial.

**Cobertura de contexto:** para calcular estas probabilidades, cada uno de los 740 hotspots necesita un perfil típico (comuna, tipo de vía, contraparte, edad/sexo promedio de las víctimas históricas de esa zona), guardado en `hotspots_contexto.csv`. Si un hotspot no tiene ese perfil propio, el backend usa el perfil promedio de toda la ciudad en su lugar y lo marca explícitamente con `contexto_estimado: true` en la respuesta de la API — así queda trazable cuáles predicciones se basan en el historial específico de la zona y cuáles en un perfil genérico, en vez de mostrar un nivel de riesgo calculado con un criterio distinto sin aviso.

## 6. Por qué el modelo #3 es el elegido

- **Mejora sustancial y consistente** en las dos clases más importantes (detectar graves y mortales), no solo en una métrica aislada.
- Confirma la hipótesis de que **"quién" (edad, sexo de la víctima) aporta más información que "dónde y cuándo" solamente**.
- La mejora **no se sostuvo al cambiar de algoritmo** (XGBoost con las mismas variables nuevas empeoró) — evidencia de que la combinación específica algoritmo+variables importa, no cualquier receta genérica.

---

## 7. Importancia de variables (modelo base, sin edad/sexo)

| Variable | Importancia relativa |
|---|---|
| Hora del siniestro | 0,182 (la más influyente, con diferencia) |
| Contraparte = AUTO | 0,099 |
| Contraparte = CAMIÓN | 0,085 |
| Tipo de vía = AUTOPISTA | 0,068 |
| Contraparte = OBJETO FIJO | 0,055 |
| Día de la semana (cualquiera) | 0,017 – 0,021 cada uno (aporte marginal, casi parejo) |

**Conclusión citable:** el momento del día y el tipo de vehículo contraparte predicen la gravedad mucho mejor que el día de la semana o la comuna — contraintuitivo respecto a la hipótesis inicial de que "el fin de semana es más peligroso".

---

## 8. Limitaciones honestas del modelo, para declarar en la tesis

1. **Precisión de GRAVE se mantiene baja en todas las versiones** (máximo 0,15) — el modelo genera bastantes falsas alarmas de "grave" sobre casos que en realidad fueron leves. Aceptable en un contexto de seguridad (mejor sobre-alertar que no alertar), pero es una limitación real a declarar.
2. **40% de las edades son estimadas**, no reales — impacta la calidad de la señal que aporta esa variable.
3. **Faltan variables con probable alto poder predictivo** que el dataset del gobierno no incluye: velocidad del vehículo, uso de casco, presencia de alcohol, condición de la vía (mojada/seca), iluminación real del lugar y momento.
4. **El modelo se entrenó y evaluó sobre CABA exclusivamente** — no hay validación sobre datos del conurbano bonaerense.
5. En el uso actual en producción (API `/hotspots`), el contexto de "hora" y "día" es el mismo para las 740 zonas en cada consulta (el momento actual real), por lo que la variación de riesgo entre zonas refleja mayormente su perfil histórico (comuna, vía, contraparte típica) más que un patrón horario específico de cada lugar.

---

## 9. Archivos generados (ubicados en `data/` y copiados a `backend/`)

| Archivo | Contenido |
|---|---|
| `motos_limpio.csv` | 23.343 siniestros de moto, limpios |
| `motos_con_clusters.csv` | Los mismos, con el hotspot (cluster) asignado |
| `hotspots_moto_caba.csv` | Resumen de los 740 hotspots (ubicación, cantidad, gravedad) |
| `hotspots_contexto.csv` | Comuna/vía/contraparte/edad/sexo típicos por hotspot (usado en producción) |
| `modelo_random_forest.pkl` | Modelo #1 (contexto solo) |
| `modelo_xgboost.pkl` | Modelo #2 |
| `modelo_random_forest_v2.pkl` | Modelo #3, primera versión (comuna sin limpiar) |
| `modelo_xgboost_v2.pkl` (no guardado explícitamente, descartado) | Modelo #4 |
| **`modelo_final.pkl`** | **El modelo #3 definitivo, en producción** (comuna limpia) |
| `columnas_modelo.pkl` | Orden exacto de las 66 columnas que el modelo espera |
