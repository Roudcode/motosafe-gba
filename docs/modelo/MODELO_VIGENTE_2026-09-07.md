# Ficha de referencia del modelo vigente

**Estado:** evidencia reproducida el 2026-10-05, tras el cambio de variante de demografía (ver más abajo).
**Artefacto:** `backend/modelo_final.pkl`.
**Propósito:** evitar que la tesis mezcle resultados de modelos anteriores con el artefacto que usa la aplicación.

## Identidad del artefacto

El modelo vigente es un `RandomForestClassifier` entrenado sobre 23.338 registros de siniestros con motocicleta que pudieron cruzarse con clima histórico. Sus hiperparámetros son:

| Parámetro | Valor |
|---|---:|
| `n_estimators` | 300 |
| `max_depth` | 12 |
| `min_samples_leaf` | 5 |
| `class_weight` | `balanced_subsample` |
| `random_state` | 42 |
| Columnas de entrada | 53 |

El artefacto fue actualizado el 2026-10-05 (reentrenado desde la variante que excluye edad, ver sección siguiente). La configuración se encuentra en `notebooks/reentrenar_modelo.py`. Incluye hora, temperatura, humedad, índice general de inseguridad por comuna, día, comuna, tipo de vía, contraparte, sexo y lluvia, después de codificación one-hot. Ya no incluye edad de la víctima ni el indicador de edad desconocida.

## Cambio de demografía (2026-10-05): por qué se sacó la edad

Hasta el 2026-09-07, el artefacto en producción incluía edad y sexo de la víctima (55 columnas). La evaluación temporal independiente (sección más abajo) mostró que esa era la peor de las tres variantes posibles en generalización entre años: F1 macro 0,262 en evaluación 2024, contra 0,286 sin edad y 0,362 sin demografía completa. Sostener la variante que peor generaliza solo porque ya estaba en producción no tenía justificación, así que se retrenó con la variante sin edad (con sexo e índice de inseguridad), que mejora la generalización sin perder recall de GRAVE/MORTAL (a diferencia de sacar también el sexo, que hunde el recall de GRAVE a 0,17 en evaluación temporal — ver `docs/evidencias/2026-10-05/A02-A04-recalibracion/README.md`).

Consecuencia directa: los umbrales de percentil (`UMBRALES_HOTSPOTS`/`UMBRALES_CORREDORES` en `backend/main.py`) se recalibraron contra el nuevo modelo con `calibrar_umbrales_riesgo.py`, y el artefacto quedó con huella SHA256 verificable en `/health` (`umbrales_riesgo_actualizados`, ver `_huella_artefactos_riesgo` en `backend/main.py`).

## Métricas que pueden citarse (modelo vigente, sin edad)

La evaluación se reprodujo re-ejecutando `notebooks/reentrenar_modelo.py`, que aplica el split estratificado determinista definido por el entrenamiento: 80/20, `random_state=42`, estratificado por `gravedad_siniestro`. El conjunto de prueba tuvo 4.668 filas.

| Métrica | Resultado |
|---|---:|
| Accuracy | 0,63 |
| F1 macro | 0,37 |
| Recall GRAVE | 0,62 |
| Precision GRAVE | 0,10 |
| F1 GRAVE | 0,18 |
| Recall MORTAL | 0,52 |
| Precision MORTAL | 0,11 |
| F1 MORTAL | 0,18 |

Estas cifras describen la reproducción del artefacto actual sobre un split aleatorio interno. Sirven para documentar el estado técnico vigente y sus falsas alertas. No son una evaluación temporal independiente, no demuestran generalización futura y no deben presentarse como desempeño para GBA.

Para contexto, la variante con edad (ya fuera de producción) obtenía en el mismo split interno: F1 macro 0,38, recall GRAVE 0,73, recall MORTAL 0,48. El split aleatorio interno es sistemáticamente más optimista que la evaluación temporal (ver más abajo) para las tres variantes por igual; la comparación entre variantes dentro de este mismo split no cambia la decisión de sacar la edad, que se tomó sobre la evaluación temporal, no sobre este split.

## Evaluación temporal independiente (ejecutada el 2026-09-15, confirma la decisión del 2026-10-05)

Se ejecutó `notebooks/evaluar_modelo_academico.py --selection-year 2023 --test-year 2024 --output docs/evidencias/2026-09-15/A02-A03-A04`, sin tocar el artefacto en producción ni reentrenarlo: entrena un Random Forest con la misma configuración sobre los años anteriores a la selección, únicamente para reproducir el protocolo de partición temporal. Entrenamiento sobre 2019-2022 (11.644 filas), selección de variables sobre 2023 (3.915 filas) y evaluación independiente sobre 2024 (3.331 filas). El índice de inseguridad general se excluyó de esta corrida particular por no tener una versión fechada temporalmente disponible para el período evaluado (la corrida de `eval_calibracion.py` del 2026-10-05, en el evidencias del mismo día, sí lo incluye y confirma la misma conclusión).

| Variante | F1 macro (selección 2023) | F1 macro (evaluación 2024) | ECE multiclase |
|---|---:|---:|---:|
| Con edad y sexo (variante retirada) | 0,348 | 0,262 | 0,318 |
| Sin edad (variante vigente desde 2026-10-05) | 0,317 | 0,286 | 0,304 |
| Sin edad ni sexo | 0,407 | 0,362 | 0,307 |

Intervalo bootstrap 95% del F1 macro en evaluación, variante con edad y sexo: [0,244; 0,281]. La proporción de edad desconocida es 45% en entrenamiento y en selección, y 12% en el año de evaluación (2024): una diferencia real de completitud entre períodos, no un artefacto del script, y una limitación en sí misma para comparar años entre sí.

El desempeño cae de forma considerable respecto de la reconstrucción del split aleatorio interno: la variante con edad y sexo pasaba de F1 macro 0,38 (split interno) a 0,262 (evaluación temporal). La variante que excluye edad generaliza mejor entre años a pesar de partir de menos información, y es la que terminó en producción. Sacar también el sexo generaliza todavía mejor en F1 macro global, pero a costa de hundir el recall de GRAVE (ver evidencia del 2026-10-05): no se adoptó por esa razón, no por desconocer la cifra más alta de F1.

Evidencia completa de esta corrida (JSON con matrices de confusión, reporte de clasificación completo y desagregación por edad desconocida) archivada en `docs/evidencias/2026-09-15/A02-A03-A04/reporte_modelo_temporal.json` y `resumen_modelo_temporal.csv`. La evidencia que agrega calibración de probabilidad y confirma la elección final de demografía está en `docs/evidencias/2026-10-05/A02-A04-recalibracion/`.

## Redacción aprobada para la tesis

> El artefacto vigente es un Random Forest de 300 árboles que clasifica gravedad condicionada a la ocurrencia de un siniestro, usando sexo pero no edad de la víctima como feature demográfico. En una reproducción del split estratificado interno de 80/20 obtuvo F1 macro de 0,37, recall de 0,62 para la clase GRAVE y 0,52 para MORTAL. Las precisiones de 0,10 y 0,11, respectivamente, muestran una tasa elevada de falsas alertas, consistente con un diseño que prioriza no dejar pasar casos graves (`class_weight='balanced_subsample'`) a costa de sobrealertar. Por ello, los resultados se interpretan como una señal exploratoria de gravedad y no como una probabilidad de ocurrencia, una garantía de seguridad vial ni una validación temporal para GBA.
>
> Una evaluación temporal independiente, entrenando hasta 2022 y evaluando sobre 2024, sitúa el F1 macro de esta variante en 0,286, por debajo del split aleatorio interno pero por encima de la variante que incluía edad (0,262, intervalo bootstrap 95%: [0,244; 0,281]). Esta diferencia fue el criterio real para retirar la edad del modelo en producción el 2026-10-05: la variante con más features demográficos no era la que mejor generalizaba entre años, y sostenerla solo porque ya estaba en producción no tenía respaldo empírico.
>
> Se evaluó además calibración de probabilidad (`CalibratedClassifierCV`, isotonic) sobre el mismo holdout temporal: mejora el ECE multiclase de 0,30 a 0,01, pero bajo decisión por argmax hunde el recall de GRAVE y MORTAL a menos de 0,07 (la clase mayoritaria LEVE domina una vez que las probabilidades reflejan la frecuencia real). No se adoptó como mecanismo de decisión en producción por esa razón: el sistema clasifica por percentiles de un score continuo, no por argmax, y ese mecanismo es menos sensible a la falta de calibración absoluta.

## Reproducción

Se reprodujo re-ejecutando `notebooks/reentrenar_modelo.py` sobre los datos actuales en `data/`, con `random_state=42` fijo (determinístico: la huella SHA256 de los artefactos resultantes coincide exactamente con la ya calibrada en `backend/main.py`, `_HUELLA_UMBRALES_CALIBRADOS`). No se modificó el protocolo de entrenamiento, solo el conjunto de columnas usado (sin edad). La corrida imprimió 23.338 filas de modelado, 53 columnas y las métricas de esta ficha.
