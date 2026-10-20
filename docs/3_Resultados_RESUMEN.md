# MotoSafe GBA — Resultados del Modelo Predictivo

Este documento reúne la metodología y los resultados del análisis de datos y el modelo de Machine Learning. Está escrito para poder usarse directamente como base de la sección de resultados de la tesis.

**Nota de vigencia (actualizado 20/10/2026):** el modelo en producción cambió el 05/10/2026 (se sacó la edad de la víctima como variable) y el mecanismo de nivel de riesgo cambió de cortes de probabilidad fijos a percentiles sobre un score relativo. Este documento refleja la variante vigente. La comparación original de algoritmos (sección 4) se conserva porque sigue siendo la evidencia real de por qué se eligió Random Forest sobre XGBoost, aclarando en qué deja de aplicar a la variante de demografía elegida después.

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
- Filtrado a víctimas en moto: **23.343 siniestros** con coordenadas válidas, de los cuales 23.338 con hora válida — la base de trabajo para el modelo.

---

## 2. Identificación de hotspots (DBSCAN, luego HDBSCAN)

**Primer intento (300m de radio, mínimo 10 casos):** fusionó casi toda la ciudad en un solo cluster de 23.068 puntos — efecto de "encadenamiento" típico de DBSCAN en zonas urbanas densas.

**Calibración DBSCAN (60 metros de radio, mínimo 10 casos por cluster):** 430 hotspots geográficamente coherentes, 67,9% de los siniestros clasificados como "aislados" (sin recurrencia puntual). Una vuelta posterior de barrido sistemático de parámetros (eps 40-120m x min_samples 6-15) mejoró esto a 412 hotspots con 49,9% de cobertura como mejor punto seguro (cluster más grande por debajo del umbral de "blob").

**Resultado final, en producción (HDBSCAN, `min_cluster_size=12, min_samples=3`):** se migró de DBSCAN a HDBSCAN porque este último se adapta a la densidad local de cada zona en vez de usar un radio fijo para toda la ciudad. **740 hotspots de siniestros de moto**, **75,6% de cobertura** de los siniestros históricos (24,4% quedan "aislados", casos demasiado dispersos como para formar zona compacta), con el cluster más grande ocupando apenas **0,41%** del total — más seguro incluso que la versión DBSCAN. Es la configuración vigente al momento de escribir esto.

**Clustering aparte, de inseguridad general (delito, no siniestros viales):** HDBSCAN con `min_cluster_size=150, min_samples=20` sobre los delitos reales del GCBA, dando **633 hotspots, 50,2% de cobertura** — es un clustering distinto, no debe confundirse con el de siniestros de moto de arriba.

**Hallazgo destacado:** el hotspot con más muertes (Donado, Saavedra — 4 mortales en 52 casos) no es el de mayor volumen (Av. Ricardo Balbín, Saavedra — 88 casos, 3 mortales). Confirma con datos reales que frecuencia y severidad son dimensiones distintas del riesgo. (Este hallazgo surgió durante la calibración DBSCAN y se sostiene igual en la migración a HDBSCAN.)

---

## 3. Modelo predictivo — variables utilizadas

**Variable objetivo:** gravedad del siniestro (`LEVE` / `GRAVE` / `MORTAL`), **condicionada a que el siniestro ya ocurrió** — el modelo no estima la probabilidad de tener un siniestro por viaje, solo qué tan grave sería dado que ocurre.

**Distribución real (fuerte desbalance de clases):**
| Clase | Casos | % |
|---|---|---|
| LEVE | 21.756 | 93,2% |
| GRAVE | 1.304 | 5,6% |
| MORTAL | 283 | 1,2% |

**Variables del modelo vigente (53 columnas tras codificación one-hot):** hora del siniestro, temperatura y humedad (clima histórico vía Open-Meteo), índice general de inseguridad por comuna, día de la semana, comuna, tipo de vía, contraparte del siniestro, sexo de la víctima y lluvia. **No incluye edad de la víctima ni el indicador de edad desconocida** — se sacaron el 05/10/2026 (ver sección 6).

**Limitación documentada sobre la demografía que sí queda (sexo):** la edad estaba disponible en el 60% de los casos en el período de entrenamiento/selección, con una brecha real entre períodos (45% de edad desconocida en 2019-2023, 12% en 2024) — una de las razones por las que la variable dejó de usarse, además de su efecto en la generalización entre años (sección 6).

---

## 4. Comparación de modelos (evidencia histórica de la elección de algoritmo, Fase 4 del proyecto)

Todos entrenados con `train_test_split` estratificado (80/20), `random_state=42`, y compensación de desbalance (`class_weight='balanced'` en Random Forest, `sample_weight` calculado con `compute_sample_weight` en XGBoost). Esta comparación se hizo con un artefacto de 66 columnas (incluía edad), ya reemplazado — se conserva porque sigue siendo la evidencia real de por qué se descartó XGBoost, no porque describa el modelo vigente.

| # | Modelo | Variables | Recall MORTAL | Recall GRAVE | Precisión GRAVE |
|---|---|---|---|---|---|
| 1 | Random Forest | Contexto (5 var.) | 0,39 | 0,12 | 0,09 |
| 2 | XGBoost | Contexto (5 var.) | 0,38 | 0,35 | 0,08 |
| 3 | Random Forest | Contexto + edad/sexo | 0,45 | 0,73 | 0,11 |
| 4 | XGBoost | Contexto + edad/sexo | 0,29 | 0,52 | 0,15 |

**Lo que esta comparación sostiene todavía:** Random Forest sobre XGBoost (la mejora de sumar demografía no se sostuvo al cambiar de algoritmo) y la arquitectura de clase (`class_weight` balanceado, 3 clases en vez de una versión binaria simplificada, que dio peor resultado: recall 0,30 de "serio" combinado, por debajo del recall MORTAL de la versión de 3 clases).

**Lo que esta comparación ya NO sostiene:** la fila #3 (con edad/sexo) no es la variante vigente. El 05/10/2026 se retiró la edad por motivos de generalización entre años (ver sección 6) — la demografía que queda en producción es solo sexo, no edad+sexo.

---

## 5. Cómo se traduce la predicción del modelo en un nivel de riesgo (bajo/medio/alto/crítico)

**Mecanismo vigente, distinto del original:** el modelo devuelve probabilidades por clase (LEVE/GRAVE/MORTAL). El backend calcula un score continuo por hotspot, `score = 2×P(MORTAL) + P(GRAVE)`, y lo compara contra percentiles fijos (`p25`, `p75`, `p95`) calculados una sola vez sobre una población de referencia — no contra umbrales de probabilidad absolutos como en versiones anteriores del sistema, ni contra percentiles recalculados sobre cada lote de pedidos (lo que distorsionaría la escala con el tiempo).

| Corte | Nivel |
|---|---|
| score ≥ p95 | Crítico |
| score ≥ p75 | Alto |
| score ≥ p25 | Medio |
| resto | Bajo |

**Por qué se pondera el doble a MORTAL que a GRAVE en el score:** una medición de sensibilidad (18/10/2026, sobre la variante vigente) comparó qué pasaría con cortes de percentil alternativos (p50 a p95) usando 2023 como población de referencia y 2024 como test real, nunca usado para calibrar nada. El recall de MORTAL se mantiene casi plano entre p50 y p75 (83,7% → 74,4%), mientras que el de GRAVE cae de forma gradual en todo el rango (74,8% → 11,9%) — GRAVE es más difícil de separar de LEVE con las variables disponibles, así que no hay un corte donde el modelo "encuentre" de golpe a los graves, los va perdiendo de a poco. El corte vigente (p75 para "alto", p95 para "crítico") queda en un punto donde MORTAL todavía conserva la mayor parte de su recall posible, a costa de un recall más bajo en GRAVE (48,1%) — una decisión de costo relativo por clase explícita, no un valor arbitrario: se acepta perder más señal de GRAVE para no perder señal de MORTAL.

**Cobertura de contexto:** para calcular estas probabilidades, cada hotspot necesita un perfil típico (comuna, tipo de vía, contraparte, sexo mayoritario de las víctimas históricas de esa zona), guardado en `hotspots_contexto.csv`. Si un hotspot no tiene ese perfil propio, el backend usa el perfil promedio de toda la ciudad y lo marca explícitamente con `contexto_estimado: true` en la respuesta de la API.

---

## 6. Por qué se sacó la edad del modelo (cambio del 05/10/2026)

Una evaluación temporal independiente (entrenando 2019-2022, seleccionando configuración sobre 2023, evaluando sobre 2024 como año nunca visto) mostró que la variante con edad y sexo era la que **peor generalizaba** de tres variantes posibles entre años: F1 macro 0,262 en evaluación 2024, contra 0,286 sin edad y 0,362 sin demografía completa. Sostener la variante que peor generaliza solo porque ya estaba en producción no tenía justificación.

Se descartó también sacar el sexo (la variante de mejor F1 global, 0,362): hundía el recall de GRAVE a 0,17 en evaluación temporal, porque el modelo pierde una señal real para distinguir GRAVE de LEVE. La variante elegida (sin edad, con sexo e índice de inseguridad) mejora la generalización sin sacrificar esa detección.

**Calibración de probabilidad, evaluada y descartada:** se probó `CalibratedClassifierCV` (isotonic) sobre la variante elegida. Baja el ECE multiclase de 0,30 a 0,01 (probabilidades honestas frente a la frecuencia real), pero bajo decisión por argmax hunde el recall de GRAVE y MORTAL a menos de 0,07, porque la clase mayoritaria (LEVE, 93%) domina una vez que las probabilidades reflejan la frecuencia real. No se adoptó: el sistema no decide por argmax, decide por el score de percentiles de la sección 5, que es mucho menos sensible a que las probabilidades absolutas estén mal calibradas — lo que importa ahí es el orden relativo entre zonas, no el valor absoluto de cada una.

---

## 7. Métricas del modelo vigente (par honesto: split interno vs. evaluación temporal real)

| Métrica | Split aleatorio interno (80/20) | Evaluación temporal (2024, real) |
|---|---:|---:|
| F1 macro | 0,368 | 0,3032 |
| Recall / Precisión GRAVE | 0,604 / 0,098 | 0,600 / 0,084 |
| Recall / Precisión MORTAL | 0,464 / 0,105 | 0,512 / 0,072 |

**Para la tesis se citan siempre ambas cifras de cada par, nunca solo la más favorable.** El split interno está sistemáticamente inflado porque mezcla información de años distintos sin la separación temporal estricta; la evaluación temporal (entrenar con años anteriores, evaluar sobre un año completamente posterior) es la cifra honesta de cuánto generaliza el modelo hacia adelante.

Matriz de confusión de la evaluación temporal (filas = real, columnas = predicho):

| Real / Predicho | GRAVE | LEVE | MORTAL |
|---|---:|---:|---:|
| GRAVE (n=210) | 126 | 54 | 30 |
| LEVE (n=3.078) | 1.360 | 1.464 | 254 |
| MORTAL (n=43) | 15 | 6 | 22 |

**Estabilidad entre años (D02, 18/10/2026):** los intervalos de confianza de dos splits temporales independientes no se superponen — el modelo no generaliza igual de un año a otro. Es una limitación real de este dataset y este enfoque, documentada, no resuelta.

---

## 8. Limitaciones honestas del modelo, para declarar en la tesis

1. **Precisión de GRAVE y MORTAL se mantiene baja** (0,08–0,11) tanto en split interno como en evaluación temporal — el modelo genera bastantes falsas alarmas sobre casos que en realidad fueron leves. Aceptable en un contexto de seguridad (mejor sobre-alertar que no alertar, decisión explícita de costo relativo por clase), pero es una limitación real a declarar.
2. **El modelo no generaliza igual entre años** (D02): dos evaluaciones temporales con splits distintos no dan intervalos de confianza superpuestos.
3. **Faltan variables con probable alto poder predictivo** que el dataset del gobierno no incluye: velocidad del vehículo, uso de casco, presencia de alcohol, condición de la vía (mojada/seca), iluminación real del lugar y momento.
4. **El modelo se entrenó y evaluó sobre CABA exclusivamente** — no hay validación sobre datos del conurbano bonaerense.
5. **La calibración de probabilidad no está aplicada**: el ECE sin calibrar es 0,30 (alto). Se evaluó aplicarla y se descartó por el motivo de la sección 6 — las probabilidades absolutas no son una medida de confianza bien calibrada, aunque el mecanismo de decisión (percentiles de un score relativo) sea menos sensible a eso.
6. En el uso actual en producción (API `/hotspots`), el contexto de "hora" y "día" es el mismo para todas las zonas en cada consulta (el momento actual real), por lo que la variación de riesgo entre zonas refleja mayormente su perfil histórico (comuna, vía, contraparte típica) más que un patrón horario específico de cada lugar.

---

## 9. Archivos generados (ubicados en `data/` y copiados a `backend/`)

| Archivo | Contenido |
|---|---|
| `motos_limpio.csv` | 23.343 siniestros de moto, limpios |
| `motos_con_clusters.csv` | Los mismos, con el hotspot (cluster) asignado |
| `hotspots_moto_caba.csv` | Resumen de los 740 hotspots de siniestros de moto (ubicación, cantidad, gravedad) |
| `hotspots_contexto.csv` | Comuna/vía/contraparte/sexo típicos por hotspot (usado en producción) |
| **`modelo_final.pkl`** | **El modelo vigente** (Random Forest, sin edad, con sexo e índice de inseguridad, 53 columnas; reentrenado el 05/10/2026) |
| `columnas_modelo.pkl` | Orden exacto de las 53 columnas que el modelo espera |

Los artefactos de la comparación original de algoritmos (sección 4: `modelo_random_forest.pkl`, `modelo_xgboost.pkl`, las versiones con 66 columnas) quedan como evidencia histórica de esa comparación, no como artefactos en uso.
