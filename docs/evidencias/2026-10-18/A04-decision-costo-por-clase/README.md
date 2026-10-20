# Decisión de costo relativo por clase (cierre de A04)

Evidencia real para el Capítulo 4 (A04) y el Capítulo 7. Protocolo: mismo split
temporal que `eval_calibracion.py` (entrenamiento 2019-2022, evaluación 2024),
sobre la variante sin edad (con sexo e índice de inseguridad) que está en
producción desde el 05/10/2026.

`split_interno_sin_edad.py` reproduce el split aleatorio interno (80/20,
estratificado) de esa misma variante, para tener el par honesto "inflado vs.
real" del modelo que corre hoy, en vez de citar el del modelo viejo (con edad).

`sensibilidad_umbrales.py` responde la pregunta que quedaba abierta en A04:
qué costo relativo se le asigna a una falsa alarma frente a un caso grave o
mortal no detectado. Entrena el mismo modelo sobre train<2023, calcula los
percentiles de corte sobre el score (`2*P(MORTAL)+P(GRAVE)`) usando 2023 como
población de referencia (nunca entrenada, nunca evaluada), y mide sobre 2024
qué recall/precisión real resulta de cada corte posible.

## Resultado 1: números actualizados del modelo en producción

| | Split aleatorio interno | Evaluación temporal (2024, real) |
|---|---|---|
| F1 macro | 0,368 | 0,3032 |
| Recall / Precisión GRAVE | 0,604 / 0,098 | 0,600 / 0,084 |
| Recall / Precisión MORTAL | 0,464 / 0,105 | 0,512 / 0,072 |

Reemplaza los números de la variante con edad (F1 macro 0,378 / 0,262) que
quedaron citados en el Capítulo 4 (Tabla 4.1) y en el borrador original del
Capítulo 7 antes del retrain del 05/10/2026.

Matriz de confusión de la evaluación temporal (filas = real, columnas = predicho):

| Real / Predicho | GRAVE | LEVE | MORTAL |
|---|---|---|---|
| GRAVE (n=210) | 126 | 54 | 30 |
| LEVE (n=3.078) | 1.360 | 1.464 | 254 |
| MORTAL (n=43) | 15 | 6 | 22 |

Nota de reproducibilidad: estas cifras salen de correr `eval_calibracion.py`
de nuevo en esta sesión (mismo código, mismo `random_state=42`) para obtener
los conteos de la matriz, que `resultado_calibracion.json` no guarda. El
resultado (F1 macro 0,3032) difiere en el tercer decimal del guardado en ese
JSON en su momento (0,3045); con un RandomForestClassifier de 300 árboles,
una corrida nueva no siempre reproduce el valor exacto bit a bit aunque la
semilla y el código sean los mismos (depende de versión de librerías y orden
de paralelización interna). La diferencia es mínima y no cambia ninguna
conclusión; se deja esta nota en vez de mezclar silenciosamente dos corridas
distintas en el mismo informe.

## Resultado 2: sensibilidad del corte de percentil (p25/p75/p95)

Percentiles calculados sobre el score de 2023 (población de referencia),
aplicados sobre 2024 (test real, nunca usado para calibrar nada):

| Corte | Umbral score | % zona-hora marcado "alto o más" | Recall GRAVE | Recall MORTAL | Recall severo | Precisión severo |
|---|---|---|---|---|---|---|
| p50 | 0,672 | 60,2% | 74,8% | 83,7% | 76,3% | 9,6% |
| p60 | 0,712 | 49,4% | 64,3% | 83,7% | 67,6% | 10,4% |
| p65 | 0,733 | 43,0% | 56,7% | 83,7% | 61,3% | 10,8% |
| p70 | 0,754 | 37,2% | 52,4% | 81,4% | 57,3% | 11,7% |
| **p75 (vigente, medio→alto)** | 0,778 | 32,4% | 48,1% | 74,4% | 52,6% | 12,3% |
| p80 | 0,807 | 26,8% | 42,9% | 74,4% | 48,2% | 13,6% |
| p85 | 0,853 | 21,0% | 34,3% | 72,1% | 40,7% | 14,7% |
| p90 | 0,952 | 13,7% | 22,4% | 65,1% | 29,6% | 16,4% |
| **p95 (vigente, alto→crítico)** | 1,131 | 7,7% | 11,9% | 55,8% | 19,4% | 19,1% |

El recall de MORTAL se mantiene casi plano entre p50 y p75 (83,7% a 74,4%),
mientras que el de GRAVE cae de forma gradual y sostenida en todo el rango
(74,8% en p50 a 11,9% en p95), porque GRAVE es más difícil de separar de LEVE
con las features disponibles: no hay un corte donde el modelo "encuentre" de
golpe a los GRAVE, los va perdiendo de a poco.

**Conclusión**: el corte vigente (p75/p95) pondera implícitamente el costo de
un MORTAL no detectado muy por encima del costo de una falsa alarma, y lo hace
en un punto eficiente: MORTAL todavía está cerca de su recall máximo en p75
(74,4% contra 83,7% en p50), así que no hay mucho para ganar ahí bajando el
corte. Lo que sí se pierde bajando el corte es volumen de alarmas sin sentido:
en p50, el 60% de las combinaciones zona-hora quedarían marcadas como "alto o
más", lo que vacía de valor la señal para quien usa el mapa. El recall más
bajo de GRAVE (48,1% en el corte vigente) es la consecuencia aceptada de esa
decisión, no un defecto sin revisar. Se cierra A04 con esta evidencia: la
decisión de negocio sobre costo relativo por clase queda tomada y documentada
con números, no a criterio implícito.
