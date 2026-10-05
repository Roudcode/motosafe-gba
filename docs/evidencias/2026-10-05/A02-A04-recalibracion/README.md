# Calibración de probabilidad y elección de demografía como feature

Evidencia real para el Capítulo 4 (A02/A04). Protocolo: `evaluar_modelo_academico.py`
(train < 2023, selección = 2023, evaluación independiente = 2024, nunca vista en
entrenamiento), con `indice_inseguridad` agregado a las tres variantes para igualar
el feature set real de producción (la ablación académica original lo excluía).

`eval_calibracion.py` reproduce esas tres variantes y les suma `CalibratedClassifierCV`
(isotonic, vía `FrozenEstimator`) ajustado sobre el holdout 2023, evaluado sobre 2024.
`resultado_calibracion.json` tiene los números crudos.

## Resultado 1: por qué la demografía cambió en producción

| Variante | F1 macro sin calibrar (2024) |
|---|---|
| Producción vieja (edad + sexo + índice) | 0.263 |
| Sin edad (sexo + índice) | 0.305 |
| Sin demografía (solo contexto + índice) | 0.361 |

La variante que estaba en producción era la que peor generalizaba de las tres entre
2023 y 2024. Sin edad mejora F1 macro un 16% y mantiene recall GRAVE/MORTAL razonable
(0.56/0.53); sin demografía gana más F1 pero porque el recall de GRAVE se desploma a
0.17 (el modelo deja de distinguir GRAVE de LEVE sin tener sexo como señal). Se optó
por sin edad, con sexo e índice: mejor generalización que la variante vieja sin sacrificar
la detección de GRAVE. Retrain ejecutado (`reentrenar_modelo.py`), modelo y umbrales
nuevos ya en `backend/main.py`.

## Resultado 2: por qué la calibración de probabilidad no se adoptó en producción

Con la variante elegida (sin edad), calibración isotonic sobre el holdout 2023-2024:

| | Sin calibrar | Calibrado (isotonic) |
|---|---|---|
| ECE multiclase | 0.296 | 0.014 |
| Recall GRAVE | 0.562 | 0.029 |
| Recall MORTAL | 0.535 | 0.070 |
| Precisión GRAVE | 0.081 | 0.316 |
| Precisión MORTAL | 0.074 | 0.600 |

La calibración isotonic funciona: el ECE baja de 0.30 a 0.014, las probabilidades que
devuelve el modelo pasan a ser honestas frente a la frecuencia real. Pero bajo
`.predict()` (argmax), ese mismo ajuste hunde el recall de GRAVE y MORTAL a casi cero,
porque LEVE es el 93% de los datos y una probabilidad bien calibrada favorece casi
siempre a la clase mayoritaria. Eso contradice el diseño de seguridad del sistema
(`class_weight='balanced_subsample'` existe justamente para inflar el recall de las
clases minoritarias a costa de precisión: mejor marcar de más un GRAVE/MORTAL que
dejarlo pasar como LEVE).

Por suerte, producción no decide con `.predict()`: `calibrar_umbrales_riesgo.py` usa
un score continuo (`2*P(MORTAL) + P(GRAVE)`) clasificado contra percentiles fijos
(p25/p75/p95) de una población de referencia. Es un mecanismo de ranking, no de
clasificación — mucho menos sensible a que las probabilidades absolutas estén mal
calibradas, porque lo que importa es el orden relativo entre zonas, no el valor
absoluto de cada una.

**Conclusión para la tesis**: la calibración de probabilidad es evidencia real de que
el modelo sin calibrar tiene ECE alto (0.30) — hallazgo legítimo para A04 — pero no se
adopta como mecanismo de decisión en producción, con esta justificación explícita
documentada, no por omisión.
