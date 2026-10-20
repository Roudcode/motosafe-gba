# D02 — Aislando la causa de la inestabilidad temporal entre splits

Continuación directa de `docs/evidencias/2026-10-18/D02-estabilidad/README.md`,
que midió la diferencia (F1 macro 0,2859 en 2023→2024 contra 0,3689 en
2024→2025, intervalos de confianza que no se superponen) y dejó tres
hipótesis sin descartar: composición de siniestros, cambio real de patrón,
o el tamaño de entrenamiento más grande del segundo split (15.559 contra
11.644 filas).

Script: `notebooks/investigar_causa_d02.py` (variante `sin_edad`, sin
`indice_inseguridad` por la misma limitación ya documentada). Comando:

```
python notebooks/investigar_causa_d02.py --output docs/evidencias/2026-10-20/D02-causa
```

## Hipótesis descartada: el tamaño de entrenamiento no es la causa

Se re-corrió el split 2024→2025 submuestreando el set de entrenamiento
<2024 (15.559 filas) al mismo tamaño que <2023 (11.644 filas), con 10
semillas distintas. Si el tamaño explicara la brecha, el F1 macro sobre
2025 debería caer hacia 0,286. No cae: se mantiene en 0,380 de media
(desvío 0,0047, rango 0,373–0,388), incluso por encima del 0,369 del
entrenamiento con las 15.559 filas completas.

| Entrenamiento | Evaluación | F1 macro |
|---|---|---|
| <2023 completo (11.644 filas) | 2024 | 0,2859 |
| <2024 completo (15.559 filas) | 2025 | 0,3689 |
| <2024 submuestreado a 11.644 filas (10 corridas) | 2025 | 0,380 (media) |

Entrenar con menos datos de 2024 sigue generalizando mejor a 2025 que
entrenar con todos los datos de <2023 generaliza a 2024. El tamaño del
set de entrenamiento queda descartado como causa de la brecha.

## Dónde está realmente la diferencia: no en las clases críticas

El desglose por clase (ya disponible en los reportes de evaluación del
18/10) muestra que MORTAL es prácticamente estable entre splits y GRAVE
mejora poco; el salto de F1 macro está dominado por LEVE:

| Clase | F1 (2023→2024) | F1 (2024→2025) | Lectura |
|---|---|---|---|
| LEVE | 0,593 (recall 0,429) | 0,788 (recall 0,669) | domina el salto de F1 macro |
| GRAVE | 0,138 (recall 0,600, precisión 0,078) | 0,209 (recall 0,503, precisión 0,132) | mejora moderada, sobre todo en precisión |
| MORTAL | 0,126 (recall 0,558) | 0,110 (recall 0,594) | prácticamente estable |

La precisión en LEVE es casi idéntica en los dos splits (0,959 en
ambos); lo que cambia es cuántos LEVE reales el modelo logra recuperar
sin marcarlos como GRAVE o MORTAL por error. Esto es relevante para la
lectura del capítulo de resultados: la inestabilidad entre años **no**
golpea con la misma fuerza al desempeño en las clases que más importan
para una alerta preventiva (GRAVE/MORTAL); golpea sobre todo a qué tan
bien el modelo reconoce los casos leves, que es la clase mayoritaria y
la que más pesa en cualquier promedio no ponderado.

## Pista de composición no explicada todavía: completitud de edad por año

La variable `edad_desconocida` no se usa como feature en la variante
`sin_edad`, pero su proporción por año es una señal de calidad de datos
y vale registrarla:

| Partición | % edad_desconocida |
|---|---|
| Entrenamiento <2023 | 45,30% |
| **Evaluación 2024** | **12,13%** |
| Entrenamiento <2024 | 45,39% |
| Evaluación 2025 | 41,10% |

El año 2024, evaluado solo, tiene una completitud de edad muy superior
al resto de la serie (12% de faltantes contra 41-45% en todos los demás
cortes). 2025 vuelve a un nivel de faltantes parecido al histórico. Esto
no prueba causalidad sobre la brecha de F1 macro, pero es un indicio
concreto de que 2024 podría ser un año atípico en el propio proceso de
carga/registro de datos, no solo en el patrón de siniestralidad vial, y
abre una pista de investigación nueva y más barata que seguir antes de
dar la causa por indeterminada: revisar si otros campos del dataset
oficial (no solo edad) también muestran una completitud anómala
específicamente en 2024.

Las proporciones de clase (LEVE/GRAVE/MORTAL) por año no muestran una
diferencia grande entre evaluación 2024 y 2025 (92,4%/6,3%/1,3% contra
91,7%/7,6%/0,7%), así que la composición de clases tampoco explica la
brecha por sí sola.

## Conclusión para el Capítulo 8 / BACKLOG (D02)

De las tres hipótesis abiertas el 18/10, el tamaño de entrenamiento
queda descartado con evidencia cuantitativa. La brecha de F1 macro entre
splits no compromete de forma pareja a todas las clases: se concentra en
el reconocimiento de casos leves, mientras que el desempeño en MORTAL (la
clase de mayor costo si se la ignora) es estable entre años. Queda una
pista concreta y no resuelta todavía: la completitud de edad del año
2024 es anómala frente al resto de la serie, lo que sugiere revisar la
calidad del dato oficial año por año antes de seguir buscando la causa
en el modelo. D02 pasa de "sin evidencia para descartar ninguna
hipótesis" a "tamaño descartado, cambio real de patrón sigue como
hipótesis más plausible, con una pista de calidad de dato por año
todavía sin seguir".
