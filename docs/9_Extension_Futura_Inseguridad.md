# 9. Extensión futura — capa de inseguridad (robos/delitos)

## 9.1 Contexto y alcance actual

MotoSafe GBA se acotó deliberadamente, en esta primera versión, a riesgo por **siniestralidad vial**. Inseguridad/delitos es un fenómeno relacionado pero de naturaleza distinta — otra fuente de datos, otro patrón espacial y temporal — y se identificó desde el inicio como una segunda pata del proyecto que requiere su propio desarrollo, no una extensión trivial del modelo de accidentes existente.

Esta sección documenta el trabajo de investigación ya realizado sobre la viabilidad de esa extensión: la fuente de datos identificada, su estructura real (verificada, no asumida), y el plan técnico de integración — para que sea el punto de partida directo de la siguiente etapa del proyecto.

## 9.2 Fuente de datos identificada

**Mapa del Delito de la Ciudad de Buenos Aires** (Ministerio Público Fiscal), publicado como dataset abierto en el mismo portal institucional que la fuente de siniestros viales:

- `https://data.buenosaires.gob.ar/dataset/delitos`
- Archivos anuales en CSV/XLSX. Se descargaron y verificaron los años 2022-2025 (588.856 registros); el portal indica disponibilidad histórica desde 2016, lo cual ampliaría considerablemente el volumen de entrenamiento si se decide incluir esos años.

Que la fuente sea del mismo organismo/portal que ya se usó para siniestros es una ventaja concreta: mismo tipo de licenciamiento, mismo criterio de calidad de dato, y una estructura de columnas lo suficientemente parecida como para reutilizar buena parte del código de limpieza ya escrito y probado.

## 9.3 Estructura real del dataset (verificada sobre 2022-2025)

Columnas: `id-mapa`, `anio`, `mes`, `dia`, `fecha`, `franja` (hora, 0-23), `tipo`, `subtipo`, `uso_arma`, `uso_moto`, `barrio`, `comuna`, `latitud`, `longitud`, `cantidad`.

Distribución por `tipo` (588.856 filas, 2022-2025):

| Tipo | Cantidad |
|---|---|
| Robo | 239.778 |
| Hurto | 229.283 |
| Vialidad | 42.945 |
| Lesiones | 40.729 |
| Amenazas | 35.785 |
| Homicidios | 336 |

Calidad de dato: ~2% de filas con coordenadas inválidas (0,0 o nulas) y un porcentaje similar sin comuna asignada — mismo tipo de limpieza (filtrado por `dropna`/coerción numérica) ya implementado para el dataset de siniestros, directamente reutilizable.

### Nota importante sobre `uso_moto` — corrección de interpretación

`uso_moto = "SI"` (20.856 casos, exclusivamente dentro de `tipo = "Robo"`) indica que **el delito fue cometido usando una motocicleta** — el patrón conocido como "motochorro". **No indica que la víctima estuviera en moto.**

Esto no invalida la relevancia para el proyecto — un motociclista convive directamente con el riesgo de motochorros (maniobras agresivas, invasión de carril, persecución) además del riesgo delictivo en sí — pero es un ángulo distinto al de "riesgo de ser asaltado mientras se circula en moto", y debe comunicarse con esa precisión. El dataset no tiene una categoría específica de "víctima motociclista"; dentro de `Robo`, los únicos subtipos son `Robo total` (236.457) y `Robo automotor` (3.321, sin distinguir moto de auto).

`uso_arma` (31.930 "SI" sobre el total) es la variable más cercana a un indicador de gravedad, análoga en función a `gravedad_siniestro` del dataset de accidentes.

## 9.4 Por qué no se integra en el mismo modelo/clustering de siniestros

Fusionar delitos y siniestros viales en un único score de "riesgo" mezclaría dos fenómenos con causas, patrones espaciales y patrones horarios distintos (un robo se concentra en esquinas de bajo tránsito y horarios nocturnos; un siniestro vial se concentra en arterias de alto tránsito) en un número único que perdería interpretabilidad — no sería posible explicar qué representa un "riesgo 0.6" compuesto por dos fenómenos de naturaleza diferente.

**Decisión de arquitectura**: dos capas de riesgo independientes y paralelas, no una fusionada. El usuario podría alternar entre "riesgo vial" (el actual) y "riesgo de inseguridad" (nuevo), o verlas superpuestas con codificación de color diferenciada.

## 9.5 Plan técnico de implementación (siguiente etapa)

Reutilizando el patrón de trabajo ya validado con siniestros:

1. **Limpieza**: normalización de texto, filtrado de coordenadas inválidas y comuna nula — mismo código base que `01_eda_hotspots_moto.ipynb` sección 1, adaptado a las columnas de delitos.
2. **Filtro de población de interés**: decidir el corte relevante para motociclistas — la opción más directa es `uso_moto == 'SI'` (motochorros, 20.856 casos en 2022-2025), eventualmente combinado con `tipo IN ('Robo', 'Hurto')` según qué se quiera capturar.
3. **Clustering (DBSCAN) independiente**: no reutilizar los parámetros de siniestros (eps=60m, min_samples=10) sin retuneo — el patrón espacial de delitos es distinto y probablemente requiera otro radio y otro mínimo de muestras. Repetir el proceso de prueba/ajuste documentado en la notebook actual (intento fallido → ajuste → validación visual).
4. **Decisión de modelado**: evaluar si `uso_arma` da una variable de severidad suficientemente informativa para un modelo predictivo tipo Random Forest (como con `gravedad_siniestro`), o si en una primera versión conviene mostrar únicamente densidad/frecuencia histórica por zona y franja horaria, sin modelo de clasificación — MVP de menor esfuerzo y sin el riesgo de un modelo mal calibrado.
5. **Backend**: nueva tabla en PostGIS (`delitos_riesgo` o similar) y un endpoint independiente (`GET /inseguridad` o un parámetro de capa en `/hotspots`), sin tocar la lógica actual de `nivel_desde_probabilidades` para siniestros viales.
6. **Frontend**: capa toggleable independiente en el mapa, con leyenda y paleta de color propia que no se confunda visualmente con el riesgo vial existente.

## 9.6 Estimación de esfuerzo

Reproducir el pipeline completo con modelo predictivo equivalente al de siniestros implica un volumen de trabajo comparable al ya invertido en esa primera etapa — no es una extensión de una tarde. Una versión acotada (limpieza + clustering + capa de frecuencia histórica, sin modelo predictivo) es sustancialmente más rápida de producir gracias a la reutilización directa del código de limpieza y clustering ya escrito, y sería el punto de entrada razonable para esta segunda etapa del proyecto.
