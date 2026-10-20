# Confianza por zona: estabilidad del nivel de riesgo frente al reentrenamiento

Pedido directo de Rodo tras la discusión sobre qué tan fuerte puede ser la
afirmación de "esto es zona de riesgo" en la tesis: no quedarse en una
advertencia mejor redactada, sino agregar algo real a la herramienta que
permita sostener esa afirmación con evidencia. Esto es lo que se agregó.

## Qué mide y qué no mide

D02 (ver `docs/evidencias/2026-10-18/D02-estabilidad/`) ya mostró que el F1
del modelo no es estable de un año de evaluación a otro — eso es
generalización temporal, y sigue sin resolverse. Esto es otra cosa: cuánto
depende el nivel de riesgo asignado a una zona puntual del azar propio de
entrenar (una remuestra bootstrap distinta, el único factor no determinista
real de un reentrenamiento con los mismos datos e hiperparámetros). Si una
zona cae en 'alto' en 9 de 10 reentrenamientos posibles, esa clasificación es
sólida. Si cae en 'alto' en 5 de 10, el número que ve el usuario depende más
de qué modelo salió esta vez que de un patrón real en los datos de esa zona.

## Método

Se entrenaron 10 `RandomForestClassifier` con los hiperparámetros exactos de
producción (`n_estimators=300, max_depth=12, min_samples_leaf=5,
class_weight="balanced_subsample"`, `random_state` distinto por modelo), cada
uno sobre una remuestra bootstrap (con reemplazo) del dataset completo —
mismo universo que usa `reentrenar_modelo.py` en producción, sin recorte por
año. Cada uno de los 10 modelos se evaluó sobre la misma grilla de 336
escenarios (24 horas × 7 días × lluvia sí/no) que calibra
`UMBRALES_HOTSPOTS`, aplicada a las 740 zonas reales de
`backend/hotspots_contexto.csv`, calculando sus propios cortes p25/p75/p95 de
referencia y clasificando cada zona-escenario en bajo/medio/alto/crítico. Se
midió, para cada zona-escenario, qué fracción de los 10 modelos coincide con
el voto mayoritario, y se promedió esa fracción sobre los 336 escenarios para
obtener un número por zona.

Script: `notebooks/calcular_confianza_zonas.py`. Reescribe
`backend/hotspots_contexto.csv` agregando la columna `confianza_estabilidad`.

## Resultado real (740 zonas, 10 modelos bootstrap)

| Métrica | Valor |
|---|---|
| Acuerdo global entre los 10 modelos (media) | 84,9% |
| Acuerdo global (mediana) | 90,0% |
| Acuerdo por zona — mínimo | 52,6% |
| Acuerdo por zona — mediana | 83,8% |
| Acuerdo por zona — máximo | 100,0% |
| Zonas con acuerdo ≥ 90% | 224 de 740 (30,3%) |
| Zonas con acuerdo ≥ 80% | 545 de 740 (73,6%) |
| Zonas con acuerdo < 60% | 1 de 740 (0,1%) |

Acuerdo promedio agrupado por el nivel mayoritario asignado en cada
zona-escenario:

| Nivel | Zona-escenarios | Acuerdo promedio |
|---|---|---|
| bajo | 58.096 | 90,3% |
| medio | 132.977 | 85,3% |
| alto | 48.458 | 78,5% |
| crítico | 9.109 | 78,9% |

La inestabilidad no se reparte parejo: se concentra en 'alto' y 'crítico',
justo los niveles que importan más para una decisión de seguridad. Esto es
consistente con un experimento previo y metodológicamente más limitado (dos
modelos sobre ventanas temporales distintas, train<2023 vs train<2024, en vez
de 10 sobre bootstrap del dataset completo): ahí también 'crítico' salía como
el nivel menos estable (67,0% de acuerdo entre los dos modelos, contra 85,0%
de 'bajo'). Los dos métodos coinciden en la dirección del hallazgo aunque no
en el número exacto, porque miden fuentes de variabilidad distintas
(ventana temporal de entrenamiento vs. azar de muestreo del mismo
entrenamiento).

## Qué se construyó con esto (no solo el hallazgo)

1. **`notebooks/calcular_confianza_zonas.py`**: script reproducible que corre
   el experimento completo y actualiza `hotspots_contexto.csv`. Mismo patrón
   que `calibrar_umbrales_riesgo.py`: se corre una vez offline, no en cada
   request.
2. **`backend/hotspots_contexto.csv`**: columna nueva `confianza_estabilidad`
   (0 a 1) para cada una de las 740 zonas reales.
3. **`backend/main.py`**: el endpoint `/hotspots` expone
   `confianza_estabilidad` en cada hotspot devuelto, tomada directamente de
   `hotspots_contexto.csv` (sin costo de cómputo adicional por request, ya
   está precalculada). Es `None` cuando el hotspot no tiene fila propia en el
   CSV — no se inventa un número para un perfil genérico que no es una zona
   real. `nivel_riesgo` NO cambia: sigue siendo 100% el output de
   `modelo_final.pkl`, sin tocar su calibración. `confianza_estabilidad` es un
   dato adicional, no un reemplazo.
4. **`_HUELLA_UMBRALES_CALIBRADOS`** actualizada (`19401654e33717952769b8af
   10a349a55de4e8d064ed4bfde0a672b9241a4fff`): agregar la columna cambió los
   bytes de `hotspots_contexto.csv`, así que el hash que detecta
   desincronización tenía que recalcularse. Se verificó a mano que
   `UMBRALES_HOTSPOTS`/`UMBRALES_CORREDORES` en sí NO cambian (dependen del
   modelo y de las columnas de contexto que ya existían, no de la columna
   nueva); solo cambió el hash que vigila el archivo completo.
5. **Tests nuevos** en `backend/tests/test_main.py`:
   `test_hotspots_con_contexto_propio_incluye_confianza_estabilidad_valida`
   (el valor está en [0, 1] para una zona real) y
   `test_hotspots_sin_contexto_propio_confianza_estabilidad_es_none` (no se
   inventa un valor para un cluster sin fila propia). Un test preexistente
   (`test_hotspots_diferencia_niveles_entre_si_no_todos_iguales`) armaba su
   propio contexto falso sin la columna nueva y se actualizó para incluirla.
   Suite completa: 126/126 en verde.

## Qué significa esto para la tesis

Responde directo a la pregunta que quedó abierta: "¿puedo decir que esto es
zona de riesgo?". Ahora hay un número por zona que dice, con evidencia real,
cuánto puede sostenerse esa afirmación puntual. Para las 224 zonas con
acuerdo ≥ 90% (30,3% del total), la clasificación es robusta al azar de
reentrenar y se puede afirmar con bastante confianza. Para el resto, en
especial las que caen en 'alto'/'crítico' (que son justamente las que más se
usarían para alertar), la afirmación tiene que ir acompañada del número de
confianza — no es una limitación que se resuelve suavizando el texto, es una
medida real y ya construida en la herramienta que permite distinguir qué
zonas sí se pueden asegurar de las que no, en vez de tratarlas todas igual.

Lo que esto NO resuelve: la inestabilidad entre años de D02 (es un problema
distinto, de generalización temporal, no de varianza de entrenamiento) ni el
problema estructural de precisión baja en GRAVE (A04, es desbalance de
clases). `confianza_estabilidad` cuantifica una dimensión real y antes no
medida de cuánto se puede confiar en el número que ve el usuario — no
resuelve las otras limitaciones ya documentadas.
