# Ficha de referencia del modelo vigente

**Estado:** evidencia reproducida el 2026-09-14.
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
| Columnas de entrada | 55 |

El artefacto fue actualizado el 2026-09-07 y su última versión en Git corresponde a `9a592aa`. La configuración se encuentra en `notebooks/reentrenar_modelo.py`. Incluye hora, edad e indicador de edad desconocida, temperatura, humedad, índice general de inseguridad por comuna, día, comuna, tipo de vía, contraparte, sexo y lluvia, después de codificación one-hot.

## Métricas que pueden citarse

La evaluación se reprodujo cargando el pickle vigente, reconstruyendo sus 55 columnas y aplicando el split estratificado determinista definido por el entrenamiento: 80/20, `random_state=42`, estratificado por `gravedad_siniestro`. El conjunto de prueba tuvo 4.668 filas.

| Métrica | Resultado |
|---|---:|
| Accuracy | 0,6180 |
| F1 macro | 0,3782 |
| Recall GRAVE | 0,7346 |
| Precision GRAVE | 0,1107 |
| F1 GRAVE | 0,1924 |
| Recall MORTAL | 0,4821 |
| Precision MORTAL | 0,1159 |
| F1 MORTAL | 0,1869 |

Estas cifras describen la reproducción del artefacto actual sobre un split aleatorio interno. Sirven para documentar el estado técnico vigente y sus falsas alertas. No son una evaluación temporal independiente, no demuestran generalización futura y no deben presentarse como desempeño para GBA.

## Resolución de la discrepancia con Fase 4

Los valores anteriores de Fase 4, incluidos recalls aproximados de 0,45 para MORTAL y 0,73 para GRAVE, corresponden al modelo anterior de contexto más edad/sexo, de 66 columnas. Ese modelo no es el pickle que hoy carga el backend. La diferencia no es una contradicción de una misma ejecución: se modificaron datos de entrada y configuración entre el modelo anterior y el vigente.

Los comentarios históricos del script que mencionan un holdout de 2025 no sustituyen una evidencia guardada de esa corrida. El protocolo temporal de `notebooks/evaluar_modelo_academico.py` se ejecutó y archivó el 2026-09-15 (ver la sección siguiente); a partir de esta ficha, la tesis puede citar esos resultados como evaluación temporal independiente, no solo la tabla anterior como reconstrucción del split aleatorio interno.

## Evaluación temporal independiente (ejecutada el 2026-09-15)

Se ejecutó `notebooks/evaluar_modelo_academico.py --selection-year 2023 --test-year 2024 --output docs/evidencias/2026-09-15/A02-A03-A04`, sin tocar el artefacto en producción (`backend/modelo_final.pkl`) ni reentrenarlo: entrena un Random Forest con la misma configuración sobre los años anteriores a la selección, únicamente para reproducir el protocolo de partición temporal. Entrenamiento sobre 2019-2022 (11.644 filas), selección de variables sobre 2023 (3.915 filas) y evaluación independiente sobre 2024 (3.331 filas). El índice de inseguridad general se excluyó de esta corrida por no tener una versión fechada temporalmente disponible para el período evaluado.

| Variante | F1 macro (selección 2023) | F1 macro (evaluación 2024) | ECE multiclase |
|---|---:|---:|---:|
| Con edad y sexo (base) | 0,348 | 0,262 | 0,318 |
| Sin edad | 0,317 | 0,286 | 0,304 |
| Sin edad ni sexo | 0,407 | 0,362 | 0,307 |

Intervalo bootstrap 95% del F1 macro en evaluación, variante base: [0,244; 0,281]. La proporción de edad desconocida es 45% en entrenamiento y en selección, y 12% en el año de evaluación (2024): una diferencia real de completitud entre períodos, no un artefacto del script, y una limitación en sí misma para comparar años entre sí.

El desempeño cae de forma considerable respecto de la reconstrucción del split aleatorio interno (F1 macro 0,378 en la tabla anterior): la variante base pasa a F1 macro 0,262 al evaluar sobre un año completo posterior al de entrenamiento. La variante que excluye edad y sexo generaliza mejor entre años (F1 macro 0,362) que la que los incluye, a pesar de partir de menos información. Esto es evidencia real de que el modelo generaliza peor entre años de lo que sugiere un split aleatorio dentro del mismo período, y de que la demografía disponible en este dataset (edad con alta proporción de valores desconocidos, sexo) no aporta señal estable entre años, sino que la degrada levemente. El ECE se mantiene en un rango similar entre variantes (0,30-0,32): las probabilidades predichas no están bien calibradas en ninguna de las tres.

Evidencia completa (JSON con matrices de confusión, reporte de clasificación completo y desagregación por edad desconocida) archivada en `docs/evidencias/2026-09-15/A02-A03-A04/reporte_modelo_temporal.json` y `resumen_modelo_temporal.csv`.

## Redacción aprobada para la tesis

> El artefacto vigente es un Random Forest de 300 árboles que clasifica gravedad condicionada a la ocurrencia de un siniestro. En una reproducción del split estratificado interno de 80/20 obtuvo F1 macro de 0,378, recall de 0,735 para la clase GRAVE y 0,482 para MORTAL. Las precisiones de 0,111 y 0,116, respectivamente, muestran una tasa elevada de falsas alertas. Por ello, los resultados se interpretan como una señal exploratoria de gravedad y no como una probabilidad de ocurrencia, una garantía de seguridad vial ni una validación temporal para GBA.
>
> Una evaluación temporal independiente, entrenando hasta 2022 y evaluando sobre 2024, sitúa el F1 macro real en 0,262 (intervalo bootstrap 95%: [0,244; 0,281]), sensiblemente por debajo del 0,378 del split aleatorio interno. Esta caída confirma que el split aleatorio sobreestima la capacidad de generalización entre años y refuerza la lectura del modelo como señal exploratoria, no como validación temporal cerrada.

## Reproducción

Se ejecutó un script temporal que carga el artefacto, reconstruye la matriz desde `data/` y compara exactamente las 55 columnas almacenadas. No reentrenó ni sobrescribió datos, artefactos o el backend. La verificación imprimió 23.338 filas de modelado, 55 columnas y las métricas de esta ficha.
