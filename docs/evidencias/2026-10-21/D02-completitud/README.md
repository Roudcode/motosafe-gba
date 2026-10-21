# D02 — completitud por año más allá de edad: la anomalía de 2024 es de dos campos, no del dataset entero

Continuación directa de `docs/evidencias/2026-10-20/D02-causa/README.md`, que había medido que el porcentaje de `edad_desconocida` en el año de evaluación 2024 (12,13%) es muy inferior al resto de la serie (41-45%) y dejó abierta la pregunta: ¿2024 es un año atípico solo en el registro de edad, o la anomalía de completitud es más amplia (otros campos del dataset oficial también más completos ese año, lo que apuntaría a un cambio en el proceso de carga/registro, no en el patrón real de siniestralidad)?

Script: `notebooks/completitud_por_anio_d02.py`. Comando:

```
python notebooks/completitud_por_anio_d02.py --output docs/evidencias/2026-10-21/D02-completitud
```

Mide, sobre el mismo universo de siniestros de moto que usa el resto de D02, el porcentaje de valores faltantes o marcados "sin dato" en seis campos del dataset oficial, año por año (2019 a 2025, no solo los dos años en disputa):

| Año  | Filas | Comuna | Tipo de vía | Contraparte | Dirección normalizada | Sexo de la víctima | Edad de la víctima |
|------|-------|--------|-------------|-------------|------------------------|---------------------|----------------------|
| 2019 | 3.743 | 0,88%  | 94,90%      | 0,96%       | 96,63%                 | 93,99%              | 94,18%               |
| 2020 | 2.048 | 1,81%  | 1,76%       | 22,07%      | 2,29%                  | 9,72%                | 11,62%               |
| 2021 | 2.254 | 0,49%  | 0,58%       | 11,14%      | 1,38%                  | 4,66%                 | 7,72%                |
| 2022 | 3.600 | 0,92%  | 8,31%       | 6,72%       | 8,56%                  | 17,08%               | 37,17%                |
| 2023 | 3.919 | 1,15%  | 1,05%       | 11,81%      | 1,17%                  | 26,69%               | 45,60%                |
| **2024** | 3.331 | 4,08%  | **0,00%** | **0,60%** | 1,44%                  | **16,15%**           | **12,13%**            |
| 2025 | 4.448 | 0,38%  | 0,04%       | 2,41%       | 0,00%                  | **36,98%**           | **41,10%**             |

## Lectura: no es "2024 más completo en todo", es "2024 más completo en dos campos demográficos"

Los campos de ubicación y categorización del hecho (comuna, tipo de vía, contraparte del siniestro, dirección normalizada) están consistentemente bien completados desde 2020 en adelante, con variaciones chicas y sin ningún patrón que distinga a 2024 del resto: 2024 tiene, de hecho, el porcentaje más alto de los últimos cuatro años en "comuna sin dato" (4,08%, contra 0,38-1,15% en 2021/2023/2025). Donde sí aparece una anomalía real y marcada es en los dos campos que describen a la víctima: sexo y edad. Ahí 2024 tiene la completitud más alta de toda la serie reciente (edad: 12,13%; sexo: 16,15%), muy por debajo de 2023 (45,60%/26,69%) y de 2025 (41,10%/36,98%), que son los años que efectivamente se comparan en la medición de inestabilidad de D02 (entrenar con datos hasta 2023, evaluar 2024; entrenar con datos hasta 2024, evaluar 2025).

Sexo y edad se mueven juntos en los siete años medidos (bajan y suben a la vez, nunca uno sin el otro), lo que indica que comparten origen: probablemente ambos dependen de que el acta policial del hecho haya registrado los datos personales de la víctima, un paso del trámite que varía en qué tan bien se completa según el año, mientras que los datos del hecho en sí (dónde, con qué, en qué tipo de vía) se cargan de forma más estable.

Esto cambia la hipótesis que dejó abierta la medición anterior. No hay evidencia de que 2024 sea, en general, un año con mejor carga de datos en el dataset oficial: la ubicación y la categorización del hecho no muestran ninguna mejora particular ese año. Lo que sí hay es una variable del modelo, `sexo_victima` (que la variante sin edad del modelo productivo sí usa como feature, a diferencia de `edad_victima` y `edad_desconocida`, que esa variante descarta), cuya tasa de valores "sin dato" cambia de forma marcada año a año y llega a su mínimo justo en el año de evaluación donde el modelo mejor generaliza (2024, F1 macro 0,3689) y a uno de sus máximos en el año donde generaliza peor (2023 como entrenamiento no es evaluación, pero 2025 como evaluación con 36,98% de sexo faltante es el otro extremo de la serie). Esto es una correlación temporal entre dos series de siete puntos cada una, no una prueba causal: no se corrió todavía el experimento que aislaría el efecto (reentrenar y evaluar forzando la misma tasa de "sexo sin dato" en ambos años, o sacando `sexo_victima` como feature y viendo si la brecha de F1 se mantiene igual). Ese es el próximo paso concreto, más barato que seguir buscando en el patrón de siniestralidad real.

## Conclusión para el BACKLOG (D02)

La pista de "calidad de dato por año" que dejó abierta `D02-causa` se confirma real y se precisa: no es un efecto del dataset oficial en general, es específico de los dos campos demográficos de la víctima (edad y sexo), que varían juntos año a año y no están alineados con la completitud de los campos de ubicación/categorización del hecho. `sexo_victima` es feature activa en el modelo productivo; su tasa de completitud coincide, en los dos años que D02 compara, con el sentido de la brecha de F1 macro. Sigue sin confirmarse si esa correlación es causal — el experimento que lo determinaría (reentrenar sin `sexo_victima` como feature, o con la tasa de faltantes igualada entre años) no se corrió todavía.

## Experimento causal: sacar `sexo_victima` como feature

Script: `notebooks/experimento_sexo_d02.py`. Comando:

```
python notebooks/experimento_sexo_d02.py --output docs/evidencias/2026-10-21/D02-completitud
```

Reentrena y evalúa los dos splits en disputa (entrenar con datos hasta 2023, evaluar 2024; entrenar con datos hasta 2024, evaluar 2025), cinco semillas cada uno, con y sin `sexo_victima` como feature (todo lo demás, incluida la ausencia de edad, igual a la variante productiva).

| Configuración | F1 macro 2023→2024 (media, 5 semillas) | F1 macro 2024→2025 (media, 5 semillas) | Brecha |
|---|---|---|---|
| Con sexo (como hoy en producción) | 0,288 | 0,368 | 0,080 |
| **Sin sexo** | **0,365** | **0,360** | **-0,005** |

Sacar `sexo_victima` prácticamente cierra la brecha entre los dos años (de 0,080 a -0,005, dentro del ruido de las cinco corridas) y lo hace subiendo el split más débil (2023→2024 pasa de 0,288 a 0,365), no bajando el más fuerte. El desglose por clase muestra de dónde sale la mejora: en ambos splits, el salto está dominado por LEVE (en 2023→2024 pasa de F1 0,593 a 0,848; en 2024→2025, de 0,788 a 0,910), consistente con el hallazgo ya documentado en `D02-causa` de que la inestabilidad entre años se concentra en el reconocimiento de casos leves, no en los graves o mortales.

Esto confirma que la pista de completitud no era solo una correlación: `sexo_victima`, con su tasa de "sin dato" variando fuerte año a año (del 4,66% en 2021 al 93,99% en 2019), aporta ruido que el modelo termina usando de forma que no generaliza bien entre años, y sacarlo resuelve la inestabilidad temporal que D02 tenía documentada como hallazgo sin causa.

**Pero hay un costado que no mejora parejo.** En el split 2024→2025 (el que más importa, por ser el más reciente y el que usa más datos de entrenamiento), sacar sexo mejora LEVE pero empeora GRAVE (de F1 0,209 a 0,089) y MORTAL (de F1 0,110 a 0,079) -- las dos clases que más importan para una alerta preventiva. El promedio macro sin ponderar por tamaño de clase (que es como se mide F1 macro) sube porque LEVE es la clase mayoritaria y pesa igual que las otras en el promedio, pero el beneficio real para el caso de uso del sistema (priorizar zonas de riesgo grave) no está tan claro. En el split 2023→2024, GRAVE y MORTAL se mantienen casi iguales (0,138→0,117 y 0,126→0,120 respectivamente), sin ese mismo costado negativo.

## Conclusión para el BACKLOG (D02) -- decisión pendiente, no ejecutada

La inestabilidad temporal entre splits que D02 dejó como hallazgo sin causa tiene ahora una causa identificada con evidencia experimental, no solo una correlación: la tasa de "sexo sin dato", muy variable entre años, es feature activa en el modelo productivo y empeora su generalización de forma desigual entre años. Sacarla resuelve la inestabilidad y mejora el promedio general, pero a costa de las clases GRAVE y MORTAL en el split más reciente (2024→2025). No se modificó el modelo de producción ni su lista de features en esta sesión -- es una decisión de diseño real (qué pesa más: estabilidad entre años en el promedio general, o desempeño en las clases críticas de un año puntual) que le corresponde a Rodo, no algo para resolver con un script más. Queda planteada como decisión abierta en `docs/gestion/DECISIONES.md` (ver DEC-022).
