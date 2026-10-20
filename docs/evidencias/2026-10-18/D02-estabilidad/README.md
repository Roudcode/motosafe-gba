# D02 — Estabilidad del F1 por año y por comuna

Evidencia real para el Capítulo 4 (A02/D02). Protocolo: `evaluar_modelo_academico.py`
(el mismo evaluador de A02, con el IC bootstrap descriptivo que ya tenía),
ahora corrido sobre DOS pares de años independientes en vez de uno solo, y
extendido con desglose de F1 por comuna. No incluye `indice_inseguridad`
(esa variable no tiene versión fechada reconstruible año por año, misma
limitación ya documentada en el Capítulo 4); es la variante `sin_edad` sin
índice, no la que corre en producción hoy.

Comando:
```
python notebooks/evaluar_modelo_academico.py --selection-year 2023 --test-year 2024 --output docs/evidencias/2026-10-18/D02-estabilidad/split_2023_2024
python notebooks/evaluar_modelo_academico.py --selection-year 2024 --test-year 2025 --output docs/evidencias/2026-10-18/D02-estabilidad/split_2024_2025
```

## Resultado 1: el F1 macro NO es estable entre años (hallazgo real, no esperado)

| Split temporal | Entrenamiento | Selección | Evaluación | F1 macro evaluación | IC bootstrap 95% | ECE |
|---|---|---|---|---|---|---|
| 2023 → 2024 | <2023 (11.644) | 2023 (3.915) | 2024 (3.331) | 0,2859 | [0,2693; 0,3046] | 0,3039 |
| 2024 → 2025 | <2024 (15.559) | 2024 (3.331) | 2025 (4.448) | 0,3689 | [0,3504; 0,3874] | 0,2056 |

Los dos intervalos de confianza NO se superponen: la diferencia entre evaluar
contra 2024 o contra 2025 es real, no ruido de muestreo. Esto es un hallazgo
en sí mismo, no un defecto de la medición: significa que una sola evaluación
temporal (como la que cita el Capítulo 4, train<2023/test=2024) puede no
representar bien cómo va a rendir el modelo el año siguiente. El ECE también
baja de 0,30 a 0,21 entre splits, en la misma dirección (2025 es un año donde
el modelo generaliza mejor en los dos sentidos). No hay una causa identificada
todavía para esta diferencia entre años (podría ser composición de siniestros,
cambios reales en el patrón vial, o el año de entrenamiento más largo del
segundo split, 15.559 contra 11.644 filas); queda señalado como limitación
real del protocolo de evaluación con un solo año de test, no resuelto.

## Resultado 2: el F1 por comuna varía, pero está confundido con soporte chico

| Comuna | F1 (2023→2024) | GRAVE/MORTAL (2023→2024) | F1 (2024→2025) | GRAVE/MORTAL (2024→2025) |
|---|---|---|---|---|
| 1 | 0,271 | 19 / 5 | 0,356 | 22 / 2 |
| 2 | 0,265 | 5 / 1 | 0,479 | 12 / 1 |
| 3 | 0,316 | 11 / 1 | 0,443 | 20 / 2 |
| 4 | 0,294 | 16 / 3 | 0,370 | 28 / 6 |
| 5 | 0,242 | 12 / 0 | 0,374 | 18 / 2 |
| 6 | 0,234 | 8 / 2 | 0,306 | 10 / 0 |
| 7 | 0,285 | 14 / 5 | 0,360 | 23 / 1 |
| 8 | 0,388 | 12 / 4 | 0,420 | 21 / 6 |
| 9 | 0,404 | 13 / 5 | 0,383 | 35 / 1 |
| 10 | 0,257 | 9 / 7 | 0,366 | 18 / 4 |
| 11 | 0,218 | 9 / 2 | 0,293 | 29 / 0 |
| 12 | 0,184 | 16 / 1 | 0,307 | 20 / 4 |
| 13 | 0,302 | 21 / 3 | 0,292 | 19 / 1 |
| 14 | 0,283 | 19 / 2 | 0,361 | 31 / 1 |
| 15 | 0,265 | 16 / 2 | 0,397 | 27 / 1 |

El soporte de MORTAL por comuna va de 0 a 7 casos según el año: con esos
tamaños, el F1 de una sola comuna puede moverse mucho de un año a otro sin
que eso implique que el modelo "funciona peor" ahí (comuna 11 pasa de 0,218 a
0,293; comuna 9 baja de 0,404 a 0,383 pese a más que duplicar el soporte de
GRAVE). No hay ninguna comuna con F1 consistentemente mala en los dos splits
que justifique tratarla como un caso aparte; la variación observada es
compatible con ruido de muestreo dado el soporte, no con una falla geográfica
sistemática del modelo. Esto hay que decirlo con la misma cautela en los dos
sentidos: ni "las comunas rinden igual" (no se puede afirmar por falta de
significancia) ni "esta comuna anda mal" (el soporte no alcanza para
sostenerlo). La fila `<NA>` corresponde a siniestros sin comuna cargada en el
dataset original; su F1 alto (0,556 y 0,463) se apoya en muestras chicas
(136 y 17 filas) y no es representativo de nada geográfico.

## Conclusión para el Capítulo 4 / BACKLOG (D02)

El resultado de estabilidad temporal (Resultado 1) es lo suficientemente real
y sustancial como para citarse en el informe como limitación explícita del
protocolo de evaluación, no solo como evidencia de respaldo técnico. El
resultado por comuna (Resultado 2) no muestra una falla geográfica real, con
la salvedad honesta de que el soporte por comuna y clase es demasiado chico
para una conclusión fuerte en cualquier dirección.
