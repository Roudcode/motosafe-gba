# MotoSafe GBA — Resultados del Modelo Predictivo (explicado desde cero)

Este documento explica, sin dar por sabido nada de Machine Learning, qué se hizo con los datos y cómo se llegó al modelo final. Está escrito para poder usarse tanto para entender el trabajo como base directa de la sección de resultados de la tesis.

**Nota de vigencia (actualizado 20/10/2026):** el 05/10/2026 se sacó la edad de la víctima del modelo en producción y cambió el mecanismo que traduce la predicción en nivel de riesgo (de cortes de probabilidad fijos a percentiles sobre un score relativo). Este documento ya refleja la variante vigente; donde algo quedó solo como evidencia histórica (por qué se eligió Random Forest sobre XGBoost, por ejemplo) se aclara explícitamente.

---

## 1. Conceptos de Machine Learning que hacen falta para entender el resto

### ¿Qué significa "entrenar" un modelo, en la práctica?

Imaginate que le mostrás a alguien 23.343 fichas, cada una describiendo un accidente real de moto (a qué hora fue, en qué tipo de calle, con qué chocó) y, al reverso de cada ficha, cómo terminó (leve, grave, o mortal). Después de mirar todas esas fichas, esa persona empieza a "intuir" patrones: por ejemplo, que los choques contra camiones de noche suelen ser más graves que los choques contra autos de día. Un modelo de Machine Learning hace algo parecido, pero de forma matemática y con mucha más precisión y volumen de lo que una persona podría procesar a mano.

### ¿Qué es "evaluar" un modelo, y por qué no alcanza con ver si "acertó mucho"?

Una vez entrenado, hay que comprobar qué tan bien predice, pero usando datos que **no vio durante el entrenamiento** — si lo evaluás con los mismos ejemplos que ya memorizó, no es una prueba real, es como corregir un examen con las respuestas ya dadas.

Acá aparece un problema importante en este proyecto en particular: de los 23.343 casos, el 93% son leves, el 5,6% graves, y solo el 1,2% mortales. Si un modelo fuera tan "vago" que simplemente dijera "todo es leve" sin analizar nada, acertaría el 93% de las veces — un número que suena bien pero que en realidad no sirve para nada, porque el objetivo real es detectar los casos graves y mortales, no los leves (que son fáciles de adivinar por ser la mayoría).

Por eso, en vez de medir "cuántas veces acertó en total" (a esto se le llama *accuracy*), se usan otras medidas más específicas:

- **Precisión**: de todas las veces que el modelo dijo "esto va a ser grave", ¿en cuántas realmente lo fue? (mide qué tan confiable es cuando alarma)
- **Recall (sensibilidad)**: de todos los casos que realmente fueron graves, ¿en cuántos el modelo se dio cuenta? (mide qué tan bueno es para no dejar pasar casos importantes)
- **F1**: combina precisión y recall en un solo número, útil para comparar modelos de un vistazo. El "F1 macro" promedia el F1 de las tres clases (leve/grave/mortal) por igual, sin dejar que la clase mayoritaria (leve) tape a las otras dos, que son justamente las que importan.

Para este proyecto, el **recall** sigue siendo la métrica más importante para GRAVE y MORTAL — en una app de seguridad, es mucho peor "no avisar" de un caso grave real que generar alguna falsa alarma de más. El F1 macro se usa para comparar variantes del modelo entre sí de forma resumida.

### ¿Qué son Random Forest y XGBoost?

Son dos algoritmos distintos, ambos populares para este tipo de tarea. Simplificando mucho: los dos construyen muchos "árboles de decisión" (una serie de preguntas encadenadas, tipo "¿es de noche? → sí → ¿fue en autopista? → sí → probablemente grave") y combinan las respuestas de todos esos árboles para dar una predicción final más confiable que un único árbol solo. Se diferencian en *cómo* construyen y combinan esos árboles — cada uno tiene ventajas según el tipo de datos. El modelo elegido para MotoSafe GBA es Random Forest (ver sección 4).

### ¿Qué significa que el modelo "no generaliza bien entre años"?

Entrenar y evaluar con datos mezclados de todos los años (una práctica común pero optimista) puede esconder un problema: si el modelo aprendió algo que solo valía para un año puntual (una moda pasajera en los datos, no un patrón real y estable), va a parecer mucho mejor de lo que en realidad es útil hacia adelante. Por eso este proyecto usa, además del split aleatorio normal, una **evaluación temporal independiente**: entrena con años anteriores, define configuraciones con un año intermedio, y recién evalúa el resultado final sobre un año posterior que nunca tocó antes — simulando lo más parecido posible a usar el modelo "en el futuro real". Esto se explica con más detalle en la sección 7.

---

## 2. De dónde salieron los datos, y cómo se prepararon

**Fuente:** el portal de datos abiertos del Gobierno de la Ciudad de Buenos Aires (data.buenosaires.gob.ar), dataset "Siniestros viales", de la Secretaría de Transporte. Son datos públicos y oficiales, no encuestas ni estimaciones — cada registro corresponde a un siniestro real reportado a las autoridades.

Se descargaron dos archivos:
- **"Hechos"**: 65.818 siniestros ocurridos entre 2019 y septiembre de 2025, con su ubicación geográfica exacta.
- **"Víctimas"**: 75.197 registros de personas afectadas (un mismo siniestro puede tener más de una víctima, por eso hay más filas de víctimas que de hechos).

### La limpieza necesaria (cualquier dato real del mundo tiene errores)

- Se encontró una fila con basura de un error de exportación de Excel (`#¡REF!`) — se descartó.
- Varias columnas de texto tenían la misma categoría escrita de formas distintas (por ejemplo "MOTO" y "moto" contadas como cosas separadas) — se unificó todo a mayúsculas.
- La columna de "comuna" venía a veces como `"Comuna 1"` y otras veces solo como `"1"` — se normalizó a un único formato numérico.
- Se descartaron los registros sin coordenadas geográficas válidas (quedaron 62.787 de 65.817, el 95,4%).
- Al filtrar específicamente los casos de motociclistas con coordenadas válidas, quedó la base de 23.343 siniestros; descartando además 5 filas con hora inválida, la base de trabajo definitiva para el modelo quedó en **23.338 siniestros**.

---

## 3. Encontrar los "puntos calientes" (clustering: DBSCAN, luego HDBSCAN)

### El problema que resuelve

Con más de 23 mil puntos dispersos por el mapa, no todos representan el mismo tipo de información. Algunos son casos aislados (mala suerte puntual, sin patrón), y otros se repiten una y otra vez en el mismo lugar exacto — esos últimos son los que realmente importa identificar, porque señalan un problema estructural del lugar (mal diseño de la esquina, falta de semáforo, etc.), no un accidente casual.

### Cómo se hizo

Se usó un algoritmo llamado **DBSCAN**, que agrupa puntos que están muy cerca entre sí en el espacio. Hay que decirle dos cosas: qué tan cerca tienen que estar los puntos para considerarse "del mismo grupo" (el radio), y cuántos puntos mínimo hacen falta para que se considere un grupo real y no ruido.

**Primer intento (radio de 300 metros):** salió mal — casi todos los 23.343 puntos terminaron agrupados en un único cluster gigante que cubría gran parte de la ciudad. Esto pasa porque, en una ciudad con calles muy densas, cualquier punto tiene otro punto cerca a 300 metros, y esa cercanía se va "encadenando" hasta unir zonas que en realidad no tienen nada que ver entre sí.

**Ajuste DBSCAN (radio de 60 metros, mínimo 10 casos):** dio un resultado mucho más razonable — 430 zonas de riesgo bien definidas, cada una correspondiendo realmente a una esquina o tramo de calle específico con historial repetido de siniestros. El 67,9% de los 23.343 siniestros quedó clasificado como "caso aislado" (sin patrón geográfico repetido) — un número esperable y realista, no un error. Una vuelta posterior de barrido sistemático de parámetros llevó esto a 412 zonas con 49,9% de cobertura como mejor punto seguro.

**Resultado final, en producción:** se migró de DBSCAN a HDBSCAN, un algoritmo que no usa un radio fijo sino que se adapta a la densidad local de cada zona (una esquina con siniestros muy pegados entre sí y una avenida con siniestros más dispersos pueden formar zonas igual de válidas, cada una con su propia escala). Con `min_cluster_size=12, min_samples=3` se llegó a **740 zonas de riesgo de siniestros de moto**, con **75,6% de cobertura** de los siniestros históricos (24,4% quedan "aislados") y el cluster más grande ocupando apenas **0,41%** del total — más seguro incluso que la mejor versión con DBSCAN. Esta es la configuración vigente para siniestros de moto.

**Un clustering aparte, para la capa de inseguridad general** (delito reportado por el GCBA, no siniestros viales): con `min_cluster_size=150, min_samples=20` se llegó a **633 hotspots, 50,2% de cobertura**. Es un clustering independiente del anterior — comparten el algoritmo (HDBSCAN) pero no los parámetros ni los datos de entrada, y no deben confundirse al leer las dos cifras.

**Un hallazgo concreto que salió de este análisis:** el punto con más muertes registradas (una calle en el barrio de Saavedra, con 4 casos mortales sobre 52 siniestros totales) no es el punto con más siniestros en total (una avenida, también en Saavedra, con 88 siniestros pero solo 3 mortales). Esto demuestra con datos reales algo importante: la cantidad de siniestros y la gravedad de esos siniestros son dos cosas distintas, y un sistema que solo mire "cuántos siniestros hubo" sin mirar "qué tan graves fueron" se perdería justamente el punto más peligroso de los dos.

---

## 4. Entrenamiento y comparación de modelos (origen de la elección de algoritmo)

### Variable que se busca predecir

La gravedad del siniestro, con tres posibles resultados: LEVE, GRAVE, o MORTAL — **condicionada a que el siniestro ya ocurrió**. Esto es importante aclararlo: el modelo no calcula la probabilidad de que una persona tenga un accidente en un viaje o tramo dado, solo qué tan grave tendería a ser si ocurriera uno en ese contexto.

### El desbalance de clases, en números concretos

| Resultado | Cantidad de casos | Porcentaje |
|---|---|---|
| LEVE | 21.756 | 93,2% |
| GRAVE | 1.304 | 5,6% |
| MORTAL | 283 | 1,2% |

### La comparación original que definió el algoritmo

Para decidir entre Random Forest y XGBoost, y entre usar solo contexto (hora, día, comuna, tipo de vía, contraparte) o sumar también edad y sexo de la víctima, se entrenaron y compararon cuatro combinaciones, todas dejando un 20% de los datos aparte para evaluar después (el "conjunto de prueba"), con una técnica para compensar el desbalance de clases:

| # | Algoritmo | Variables usadas | Recall en MORTAL | Recall en GRAVE |
|---|---|---|---|---|
| 1 | Random Forest | Solo contexto | 0,39 | 0,12 |
| 2 | XGBoost | Solo contexto | 0,38 | 0,35 |
| 3 | Random Forest | Contexto + edad/sexo | 0,45 | 0,73 |
| 4 | XGBoost | Contexto + edad/sexo | 0,29 | 0,52 |

Esta comparación (hecha con un artefacto de 66 columnas, que incluía edad) dejó dos conclusiones que **siguen vigentes**: Random Forest se comporta mejor que XGBoost con este dataset (la mejora de sumar demografía no se sostuvo al cambiar de algoritmo), y una versión simplificada a dos categorías ("leve" vs. "serio" combinando grave+mortal) dio peor resultado (recall de "serio": 0,30) que separar en tres clases — simplificar el problema no ayudó.

**Lo que esta comparación ya NO describe:** la variante #3, con edad y sexo, dejó de estar en producción el 05/10/2026. No fue porque el recall de esta tabla estuviera mal medido, sino porque una evaluación posterior (sección 7) mostró que esa variante era la que peor generalizaba entre años distintos — un problema que esta comparación, al usar un único split aleatorio, no podía ver.

### El modelo que hoy usa la aplicación

Es Random Forest (por la comparación de arriba), pero con sexo e índice de inseguridad como demografía/contexto — sin edad. Está guardado como `modelo_final.pkl` y tiene 53 columnas de entrada (no 66, que era el artefacto de esta comparación).

---

## 5. Cómo se traduce la predicción del modelo en un nivel de riesgo (bajo/medio/alto/crítico)

### El mecanismo vigente

El modelo entrenado predice probabilidades por clase (LEVE/GRAVE/MORTAL), no un nivel de riesgo directamente. El backend combina esas probabilidades en un único número, llamado score: `score = 2×P(MORTAL) + P(GRAVE)` — a MORTAL se le da el doble de peso que a GRAVE, porque es la clase que más importa no dejar pasar.

Ese score no se compara contra un valor fijo (como "score ≥ 0,5 es alto"), sino contra **percentiles calculados una sola vez sobre una población de referencia**: p25, p75 y p95. Esto es distinto de calcular los percentiles sobre cada lote de pedidos que llegan en el momento — si se hiciera así, la escala se iría deformando con el tiempo, porque "alto" dejaría de significar siempre lo mismo.

| Corte | Nivel resultante |
|---|---|
| score ≥ percentil 95 | Crítico |
| score ≥ percentil 75 | Alto |
| score ≥ percentil 25 | Medio |
| Ninguno de los anteriores | Bajo |

### Por qué el corte está puesto justo ahí (y no en otro percentil)

El 18/10/2026 se midió, sobre la variante vigente, qué pasaría con cortes alternativos (percentil 50 a percentil 95), usando el año 2023 como población de referencia para calcular los percentiles y el año 2024 como prueba real, nunca usado para ajustar nada:

| Corte | % de combinaciones zona-hora marcadas "alto o más" | Recall GRAVE | Recall MORTAL |
|---|---:|---:|---:|
| p50 | 60,2% | 74,8% | 83,7% |
| p75 (vigente, medio→alto) | 32,4% | 48,1% | 74,4% |
| p95 (vigente, alto→crítico) | 7,7% | 11,9% | 55,8% |

El recall de MORTAL se mantiene casi plano entre p50 y p75 (83,7% baja solo a 74,4%), mientras que el de GRAVE cae de forma gradual y sostenida en todo el rango (74,8% a 11,9%) — GRAVE es más difícil de separar de LEVE con las variables disponibles, así que el modelo no lo "encuentra" de golpe en ningún corte puntual, lo va perdiendo de a poco a medida que el corte se exige más estricto.

**La conclusión práctica:** el corte vigente (p75/p95) prioriza no perder señal de MORTAL — en ese punto todavía conserva la mayor parte de su recall posible — a costa de un recall más bajo en GRAVE (48,1%). Es una decisión consciente de costo relativo por clase, documentada con números: se acepta avisar menos sobre "graves" para no dejar de avisar sobre "mortales". Si se usara un corte más laxo (p50), casi dos tercios de las combinaciones zona-hora del mapa quedarían marcadas "alto o más", lo que vaciaría de valor la señal para quien lo use.

### Qué pasa cuando falta el contexto propio de un hotspot

Cada hotspot necesita, para pasar por el modelo, un perfil típico de esa zona (comuna, tipo de vía, contraparte y sexo mayoritario de sus víctimas históricas), calculado una sola vez y guardado en `hotspots_contexto.csv`. Si un hotspot no tiene fila propia en ese archivo, el backend usa el perfil promedio de toda la ciudad como entrada al mismo modelo, y la respuesta de la API lo marca explícitamente con `contexto_estimado: true`, para que la limitación quede trazable en vez de oculta.

---

## 6. Por qué se sacó la edad del modelo (cambio del 05/10/2026)

Hasta esa fecha, el modelo en producción incluía edad y sexo de la víctima (55 columnas). Una evaluación temporal independiente — entrenando con 2019-2022, definiendo configuraciones con 2023, y evaluando recién sobre 2024 como año nunca visto — mostró algo que la comparación de la sección 4 no podía ver con un único split aleatorio: de tres variantes posibles, la que incluía edad era la que **peor generalizaba** entre años (F1 macro 0,262 en evaluación 2024), por debajo de sacar la edad (0,286) y de sacar también el sexo (0,362).

¿Por qué no se sacó también el sexo, si daba el F1 más alto de las tres? Porque esa variante hundía el recall de GRAVE a 0,17 en evaluación temporal — el modelo perdía una señal real para distinguir "grave" de "leve". La variante elegida (sin edad, con sexo e índice de inseguridad) mejora la generalización entre años sin sacrificar esa detección, un balance mejor que elegir solo por el número más alto de una métrica resumida.

**Un intento adicional que se descartó: calibrar las probabilidades.** Se probó una técnica llamada calibración isotónica, que ajusta las probabilidades del modelo para que reflejen honestamente la frecuencia real de cada clase (hoy el modelo está "mal calibrado": dice, por ejemplo, 40% de probabilidad de GRAVE en casos donde en la realidad esa probabilidad es mucho más baja, para poder tener más recall). La calibración funciona para ese objetivo — el error de calibración baja de 0,30 a 0,01 — pero, si se usara esa probabilidad calibrada para decidir directamente la clase más probable, el recall de GRAVE y MORTAL se hunde a menos de 0,07, porque la clase mayoritaria (LEVE, 93% de los casos) termina ganando casi siempre una vez que las probabilidades son honestas. No se adoptó para producción: el sistema no decide por "cuál es la clase más probable", decide por el score de percentiles de la sección 5, un mecanismo de orden relativo entre zonas que no se beneficia de la misma manera de que las probabilidades absolutas estén bien calibradas.

---

## 7. Qué tan bien funciona en realidad: el par honesto split interno / evaluación temporal

### Por qué hacen falta dos números, no uno

Evaluar con un split aleatorio simple (mezclar todos los años y separar 80%/20% al azar) tiende a dar un resultado optimista, porque dentro de un mismo año hay patrones que se repiten (la misma esquina conflictiva, el mismo tipo de choque de moda) que el modelo puede estar memorizando en vez de aprendiendo algo que valga para el futuro. Por eso este proyecto reporta siempre dos cifras por métrica: la del split aleatorio interno (más alta, pero menos realista) y la de una evaluación temporal independiente, donde el modelo se entrena con años anteriores y se evalúa sobre un año posterior que nunca tocó — la cifra que de verdad dice cuánto se puede confiar en el modelo hacia adelante.

### Los números del modelo vigente (sin edad)

| Métrica | Split aleatorio interno (80/20) | Evaluación temporal (2024, real) |
|---|---:|---:|
| F1 macro | 0,368 | 0,3032 |
| Recall / Precisión GRAVE | 0,604 / 0,098 | 0,600 / 0,084 |
| Recall / Precisión MORTAL | 0,464 / 0,105 | 0,512 / 0,072 |

Matriz de confusión de la evaluación temporal (filas = lo que realmente pasó, columnas = lo que predijo el modelo):

| Real / Predicho | GRAVE | LEVE | MORTAL |
|---|---:|---:|---:|
| GRAVE (210 casos reales) | 126 | 54 | 30 |
| LEVE (3.078 casos reales) | 1.360 | 1.464 | 254 |
| MORTAL (43 casos reales) | 15 | 6 | 22 |

Leyendo la fila de MORTAL: de 43 casos mortales reales en 2024, el modelo marcó 22 correctamente como MORTAL y 15 como GRAVE (ambos son "alerta seria"), y solo 6 pasaron completamente desapercibidos como LEVE — consistente con el diseño de priorizar no dejar pasar casos serios, aunque a costa de muchas falsas alarmas (la columna de GRAVE predicho tiene 1.360 casos que en realidad fueron LEVE).

### Una limitación adicional, medida el 18/10/2026: el modelo no generaliza igual de un año a otro

Se corrió el mismo protocolo de evaluación temporal con dos pares de años distintos (2023→2024 y 2024→2025). Los intervalos de confianza del F1 macro de ambos splits **no se superponen** — es decir, el desempeño del modelo no es estable entre un período y el siguiente. Esto es una limitación real del dataset y del enfoque (pocos años de historia, eventos poco frecuentes en las clases minoritarias), que queda documentada tal como se midió, no resuelta.

---

## 8. Limitaciones del modelo, para declarar con honestidad

1. **La precisión al predecir "grave" y "mortal" se mantiene baja** (0,08 a 0,11, tanto en split interno como en evaluación temporal) — el modelo genera bastantes falsas alarmas sobre casos que en realidad terminaron siendo leves. Es una consecuencia aceptada de la decisión de costo relativo por clase (sección 5), no un error sin revisar, pero sigue siendo una limitación real que hay que reconocer.
2. **El modelo no generaliza igual entre años**: dos evaluaciones temporales con pares de años distintos dan intervalos de confianza que no se superponen.
3. **Faltan variables que probablemente tendrían mucho peso predictivo** y que el dataset del gobierno no incluye: velocidad al momento del choque, uso de casco, presencia de alcohol, estado del pavimento (mojado o seco), y nivel real de iluminación del lugar en ese momento específico.
4. **El modelo se entrenó y evaluó exclusivamente con datos de CABA** — no hay ninguna validación de cómo se comportaría con datos del conurbano bonaerense.
5. **Las probabilidades del modelo no están calibradas** (error de calibración 0,30, alto) — se evaluó calibrarlas y se descartó por el motivo de la sección 6. El mecanismo de decisión (percentiles de un score relativo) es menos sensible a esto que decidir por "la clase más probable", pero conviene tenerlo presente si alguna vez se quisiera comunicar una probabilidad puntual al usuario en vez de un nivel relativo.
6. **En el uso actual dentro de la aplicación**, la hora y el día que recibe el modelo son siempre los del momento real de la consulta, pero el resto del contexto (comuna, vía, contraparte, sexo) usa el "perfil típico histórico" de cada zona, no la situación específica de la persona que está mirando el mapa en ese momento — es una aproximación razonable, pero conviene tenerla presente y declarada.

---

## 9. Archivos que quedaron generados (en la carpeta `data/`, y copiados a `backend/` los que la aplicación usa en vivo)

| Archivo | Qué contiene |
|---|---|
| `motos_limpio.csv` | Los 23.343 siniestros de moto, ya limpios |
| `motos_con_clusters.csv` | Los mismos datos, con el número de zona (cluster) asignado a cada uno |
| `hotspots_moto_caba.csv` | Resumen de las 740 zonas de siniestros de moto: ubicación, cantidad, gravedad |
| `hotspots_contexto.csv` | Comuna, tipo de vía, contraparte y sexo típicos de cada zona |
| `modelo_final.pkl` | **El modelo vigente**: Random Forest sin edad, con sexo e índice de inseguridad, 53 columnas, reentrenado el 05/10/2026 — el que corre en la aplicación real |
| `columnas_modelo.pkl` | El orden exacto de las 53 columnas que el modelo necesita para poder predecir correctamente |

Los artefactos de la comparación original de algoritmos (sección 4: `modelo_random_forest.pkl`, `modelo_xgboost.pkl`, y las versiones de 66 columnas con edad) quedan como evidencia histórica de esa comparación — no son los que usa la aplicación hoy.
