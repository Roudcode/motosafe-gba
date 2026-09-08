# MotoSafe GBA — Resultados del Modelo Predictivo (explicado desde cero)

Este documento explica, sin dar por sabido nada de Machine Learning, qué se hizo con los datos y cómo se llegó al modelo final. Está escrito para poder usarse tanto para entender el trabajo como base directa de la sección de resultados de la tesis.

---

## 1. Conceptos de Machine Learning que hacen falta para entender el resto

### ¿Qué significa "entrenar" un modelo, en la práctica?

Imaginate que le mostrás a alguien 23.343 fichas, cada una describiendo un accidente real de moto (a qué hora fue, en qué tipo de calle, con qué chocó, qué edad tenía el motociclista) y, al reverso de cada ficha, cómo terminó (leve, grave, o mortal). Después de mirar todas esas fichas, esa persona empieza a "intuir" patrones: por ejemplo, que los choques contra camiones de noche suelen ser más graves que los choques contra autos de día. Un modelo de Machine Learning hace algo parecido, pero de forma matemática y con mucha más precisión y volumen de lo que una persona podría procesar a mano.

### ¿Qué es "evaluar" un modelo, y por qué no alcanza con ver si "acertó mucho"?

Una vez entrenado, hay que comprobar qué tan bien predice, pero usando datos que **no vio durante el entrenamiento** — si lo evaluás con los mismos ejemplos que ya memorizó, no es una prueba real, es como corregir un examen con las respuestas ya dadas.

Acá aparece un problema importante en este proyecto en particular: de los 23.343 casos, el 93% son leves, el 5,6% graves, y solo el 1,2% mortales. Si un modelo fuera tan "vago" que simplemente dijera "todo es leve" sin analizar nada, acertaría el 93% de las veces — un número que suena bien pero que en realidad no sirve para nada, porque el objetivo real es detectar los casos graves y mortales, no los leves (que son fáciles de adivinar por ser la mayoría).

Por eso, en vez de medir "cuántas veces acertó en total" (a esto se le llama *accuracy*), se usan otras dos medidas más específicas:

- **Precisión**: de todas las veces que el modelo dijo "esto va a ser grave", ¿en cuántas realmente lo fue? (mide qué tan confiable es cuando alarma)
- **Recall (sensibilidad)**: de todos los casos que realmente fueron graves, ¿en cuántos el modelo se dio cuenta? (mide qué tan bueno es para no dejar pasar casos importantes)

Para este proyecto, el **recall** es la métrica más importante — en una app de seguridad, es mucho peor "no avisar" de un caso grave real que generar alguna falsa alarma de más.

### ¿Qué son Random Forest y XGBoost?

Son dos algoritmos distintos, ambos populares para este tipo de tarea. Simplificando mucho: los dos construyen muchos "árboles de decisión" (una serie de preguntas encadenadas, tipo "¿es de noche? → sí → ¿fue en autopista? → sí → probablemente grave") y combinan las respuestas de todos esos árboles para dar una predicción final más confiable que un único árbol solo. Se diferencian en *cómo* construyen y combinan esos árboles — cada uno tiene ventajas según el tipo de datos.

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
- Al filtrar específicamente los casos de motociclistas con coordenadas válidas, quedó la base de trabajo definitiva: **23.343 siniestros**.

---

## 3. Encontrar los "puntos calientes" (clustering: DBSCAN, luego HDBSCAN)

### El problema que resuelve

Con 23.343 puntos dispersos por el mapa, no todos representan el mismo tipo de información. Algunos son casos aislados (mala suerte puntual, sin patrón), y otros se repiten una y otra vez en el mismo lugar exacto — esos últimos son los que realmente importa identificar, porque señalan un problema estructural del lugar (mal diseño de la esquina, falta de semáforo, etc.), no un accidente casual.

### Cómo se hizo

Se usó un algoritmo llamado **DBSCAN**, que agrupa puntos que están muy cerca entre sí en el espacio. Hay que decirle dos cosas: qué tan cerca tienen que estar los puntos para considerarse "del mismo grupo" (el radio), y cuántos puntos mínimo hacen falta para que se considere un grupo real y no ruido.

**Primer intento (radio de 300 metros):** salió mal — casi todos los 23.343 puntos terminaron agrupados en un único cluster gigante que cubría gran parte de la ciudad. Esto pasa porque, en una ciudad con calles muy densas, cualquier punto tiene otro punto cerca a 300 metros, y esa cercanía se va "encadenando" hasta unir zonas que en realidad no tienen nada que ver entre sí.

**Ajuste DBSCAN (radio de 60 metros, mínimo 10 casos):** dio un resultado mucho más razonable — 430 zonas de riesgo bien definidas, cada una correspondiendo realmente a una esquina o tramo de calle específico con historial repetido de siniestros. El 67,9% de los 23.343 siniestros quedó clasificado como "caso aislado" (sin patrón geográfico repetido) — un número esperable y realista, no un error. Una vuelta posterior de barrido sistemático de parámetros llevó esto a 412 zonas con 49,9% de cobertura como mejor punto seguro.

**Resultado final, en producción:** se migró de DBSCAN a HDBSCAN, un algoritmo que no usa un radio fijo sino que se adapta a la densidad local de cada zona (una esquina con siniestros muy pegados entre sí y una avenida con siniestros más dispersos pueden formar zonas igual de válidas, cada una con su propia escala). Con `min_cluster_size=12, min_samples=3` se llegó a **740 zonas de riesgo**, con **75,6% de cobertura** de los siniestros históricos (24,4% quedan "aislados") y el cluster más grande ocupando apenas **0,41%** del total — más seguro incluso que la mejor versión con DBSCAN. Esta es la configuración vigente.

**Un hallazgo concreto que salió de este análisis:** el punto con más muertes registradas (una calle en el barrio de Saavedra, con 4 casos mortales sobre 52 siniestros totales) no es el punto con más siniestros en total (una avenida, también en Saavedra, con 88 siniestros pero solo 3 mortales). Esto demuestra con datos reales algo importante: la cantidad de siniestros y la gravedad de esos siniestros son dos cosas distintas, y un sistema que solo mire "cuántos siniestros hubo" sin mirar "qué tan graves fueron" se perdería justamente el punto más peligroso de los dos.

---

## 4. Entrenamiento y comparación de modelos

### Variable que se busca predecir

La gravedad del siniestro, con tres posibles resultados: LEVE, GRAVE, o MORTAL.

### El desbalance de clases, en números concretos

| Resultado | Cantidad de casos | Porcentaje |
|---|---|---|
| LEVE | 21.756 | 93,2% |
| GRAVE | 1.304 | 5,6% |
| MORTAL | 283 | 1,2% |

### Información que se le dio al modelo (variables predictoras)

**Primera versión ("contexto del lugar y momento"):** hora del siniestro, día de la semana, comuna, tipo de vía, y con qué contraparte chocó (auto, camión, otra moto, etc.). En total, después de convertir las categorías de texto en un formato que el modelo pueda procesar (técnica llamada "codificación one-hot"), esto se convierte en 61 columnas de datos.

**Segunda versión ("contexto + datos de la víctima"):** se agregaron la edad y el sexo del motociclista, obtenidos cruzando el archivo de "hechos" con el de "víctimas". Con esto, la matriz de datos crece a 66 columnas.

**Un problema real que hubo que resolver:** la edad de la víctima solo estaba disponible en el 60% de los casos (14.088 de 23.338). En vez de descartar el 40% restante (perdiendo información valiosa), se completó ese dato faltante con el valor promedio (32 años), y se agregó una columna extra que marca "esta edad es una estimación, no un dato real" — para que el modelo pueda distinguir entre información confiable e información completada. Además, se descartaron edades imposibles para un conductor de moto (menores de 14 años, mayores de 95 años), que eran errores de carga del dataset original.

### Los cuatro modelos entrenados y comparados

Todos entrenados dejando un 20% de los datos aparte, sin usar para entrenar, exclusivamente para evaluar después (esto se llama "conjunto de prueba"). Además, se usó una técnica para compensar el desbalance de clases (que el modelo no ignore los pocos casos mortales solo porque son pocos).

| # | Algoritmo | Variables usadas | Recall en MORTAL | Recall en GRAVE |
|---|---|---|---|---|
| 1 | Random Forest | Solo contexto | 0,39 (detecta 39 de cada 100 mortales reales) | 0,12 (detecta 12 de cada 100 graves reales) |
| 2 | XGBoost | Solo contexto | 0,38 | 0,35 |
| **3** | **Random Forest** | **Contexto + edad/sexo** | **0,45** | **0,73** |
| 4 | XGBoost | Contexto + edad/sexo | 0,29 | 0,52 |

### El modelo elegido: el #3

Es el que mejor detecta tanto los casos graves como los mortales, con una mejora grande y consistente respecto a las otras versiones (no solo en un número aislado). Es el que quedó guardado como `modelo_final.pkl`, y es el que hoy usa la aplicación en producción.

### Un experimento adicional: ¿simplificar el problema mejora los resultados?

Se probó también combinar "grave" y "mortal" en una sola categoría llamada "serio" (dejando solo dos posibilidades: leve o serio), pensando que quizás el problema era demasiado difícil con tres categorías separadas. El resultado fue peor (recall de "serio": 0,30) que el mejor modelo de tres categorías — es decir, simplificar el problema en este caso **no ayudó**, contradiciendo la intuición inicial. Es un resultado válido para documentar tal como salió, no algo que haya que ocultar por no ser el esperado.

---

## 5. Cómo se traduce la probabilidad del modelo en un nivel de riesgo (bajo/medio/alto/crítico)

El modelo entrenado predice probabilidades por clase (LEVE/GRAVE/MORTAL), no un nivel de riesgo categórico. La función `nivel_desde_probabilidades()` en `backend/main.py` hace esa traducción, con los siguientes cortes:

| Condición | Nivel resultante |
|---|---|
| p(MORTAL) ≥ 0.20 | Crítico |
| p(MORTAL) ≥ 0.10 **o** p(GRAVE) ≥ 0.40 | Alto |
| p(GRAVE) ≥ 0.20 | Medio |
| Ninguna de las anteriores | Bajo |

**Justificación de la asimetría entre los umbrales de MORTAL y GRAVE.** Como se detalla en la sección de comparación de modelos, el modelo elegido tiene una precisión baja para la clase GRAVE (0.11, y no supera 0.15 en ninguna de las cuatro versiones evaluadas): produce bastantes falsos positivos de "grave" sobre casos que en la realidad fueron leves. Esa limitación se acepta de forma consciente porque, en un sistema de alerta de seguridad vial, es preferible sobre-alertar que dejar pasar un caso serio sin avisar. Esa misma lógica se traslada al diseño de los umbrales: como la señal de GRAVE es más ruidosa, se le exige una probabilidad acumulada más alta (0.40, o 0.20 para el nivel intermedio) que a MORTAL (0.10-0.20) para que el sistema escale el nivel de riesgo mostrado en el mapa. No es un ajuste arbitrario de constantes: es la misma decisión de "priorizar recall sobre precisión" que ya se justificó al elegir el modelo, aplicada también en la capa de presentación.

**Qué pasa cuando falta el contexto propio de un hotspot.** Cada uno de los 740 hotspots necesita, para pasar por el modelo, un perfil típico de esa zona (comuna, tipo de vía, contraparte y edad/sexo promedio de sus víctimas históricas), calculado una sola vez y guardado en `hotspots_contexto.csv`. En una primera versión del sistema, cuando un hotspot no tenía fila propia en ese archivo, el backend se quedaba con un nivel de riesgo calculado con una fórmula completamente distinta (una heurística simple sobre cantidad de siniestros, mortales y graves, usada solo para poblar la base de datos inicialmente) — es decir, convivían dos criterios de "riesgo" distintos en el mismo mapa sin que el usuario (ni el jurado revisando el código) pudiera distinguir cuál se estaba usando en cada punto. Se corrigió para que el modelo sea la única fuente de verdad: si falta el contexto propio del hotspot, se usa el perfil promedio de toda la ciudad como entrada al mismo modelo, y la respuesta de la API marca ese caso explícitamente con `contexto_estimado: true`, de forma que la limitación quede documentada y trazable en vez de oculta.

## 6. Qué variables importan más para predecir la gravedad

Analizando el modelo base (sin edad/sexo, para entender primero el peso de las variables de contexto), se encontró:

| Variable | Peso relativo en la predicción |
|---|---|
| Hora del siniestro | La más influyente, con bastante diferencia sobre el resto |
| Contraparte = AUTO | Segunda más influyente |
| Contraparte = CAMIÓN | Tercera |
| Tipo de vía = AUTOPISTA | Cuarta |
| Contraparte = OBJETO FIJO | Quinta |
| Día de la semana (cualquiera) | Aporte bajo, muy parejo entre todos los días |

**Conclusión, con implicancia práctica:** la hora del día y el tipo de vehículo con el que se choca predicen mucho mejor la gravedad que el día de la semana. Esto va en contra de una hipótesis intuitiva ("los fines de semana es más peligroso"), y es exactamente el tipo de hallazgo que vale la pena reportar tal cual salió, aunque no confirme lo que se esperaba de entrada.

---

## 7. Limitaciones del modelo, para declarar con honestidad

1. **La precisión al predecir "grave" se mantiene baja en todas las versiones probadas** (nunca supera 0,15) — el modelo genera bastantes falsas alarmas de "esto va a ser grave" sobre casos que en realidad terminaron siendo leves. En un contexto de seguridad vial, sobre-alertar es preferible a no alertar, pero es una limitación real que hay que reconocer, no ocultar.
2. **El 40% de las edades usadas para entrenar son estimadas**, no reales.
3. **Faltan variables que probablemente tendrían mucho peso predictivo** y que el dataset del gobierno no incluye: velocidad al momento del choque, uso de casco, presencia de alcohol, estado del pavimento (mojado o seco), y nivel real de iluminación del lugar en ese momento específico.
4. **El modelo se entrenó y evaluó exclusivamente con datos de CABA** — no hay ninguna validación de cómo se comportaría con datos del conurbano bonaerense.
5. **En el uso actual dentro de la aplicación**, la hora y el día que recibe el modelo son siempre los del momento real de la consulta, pero el resto del contexto (contraparte, edad, sexo) usa el "perfil típico histórico" de cada zona, no la situación específica de la persona que está mirando el mapa en ese momento — es una aproximación razonable, pero conviene tenerla presente y declarada.

---

## 8. Archivos que quedaron generados (en la carpeta `data/`, y copiados a `backend/` los que la aplicación usa en vivo)

| Archivo | Qué contiene |
|---|---|
| `motos_limpio.csv` | Los 23.343 siniestros de moto, ya limpios |
| `motos_con_clusters.csv` | Los mismos datos, con el número de zona (cluster) asignado a cada uno |
| `hotspots_moto_caba.csv` | Resumen de las 740 zonas: ubicación, cantidad de siniestros, gravedad |
| `hotspots_contexto.csv` | Comuna, tipo de vía, contraparte, edad y sexo típicos de cada una de las 740 zonas |
| `modelo_final.pkl` | El modelo #3 (el elegido), listo para usarse — este es el que corre en la aplicación real |
| `columnas_modelo.pkl` | El orden exacto de las 66 columnas que el modelo necesita para poder predecir correctamente |
