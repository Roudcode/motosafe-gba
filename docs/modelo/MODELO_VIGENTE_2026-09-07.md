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

Los comentarios históricos del script que mencionan un holdout de 2025 no sustituyen una evidencia guardada de esa corrida. Hasta ejecutar y archivar el protocolo temporal de `notebooks/evaluar_modelo_academico.py`, la tesis debe citar exclusivamente la tabla anterior como evaluación interna reproducida y declarar pendiente la validación temporal.

## Redacción aprobada para la tesis

> El artefacto vigente es un Random Forest de 300 árboles que clasifica gravedad condicionada a la ocurrencia de un siniestro. En una reproducción del split estratificado interno de 80/20 obtuvo F1 macro de 0,378, recall de 0,735 para la clase GRAVE y 0,482 para MORTAL. Las precisiones de 0,111 y 0,116, respectivamente, muestran una tasa elevada de falsas alertas. Por ello, los resultados se interpretan como una señal exploratoria de gravedad y no como una probabilidad de ocurrencia, una garantía de seguridad vial ni una validación temporal para GBA.

## Reproducción

Se ejecutó un script temporal que carga el artefacto, reconstruye la matriz desde `data/` y compara exactamente las 55 columnas almacenadas. No reentrenó ni sobrescribió datos, artefactos o el backend. La verificación imprimió 23.338 filas de modelado, 55 columnas y las métricas de esta ficha.
