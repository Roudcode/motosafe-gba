# A09 — medición de duplicación semántica entre fuentes de prensa

## Contexto

El extractor de prensa (`backend/scrapear_noticias_robos.py`) dedupe hoy de
dos formas, ninguna semántica:

1. **Dentro de una corrida**: `firma_titular` compara título normalizado +
   categoría, pero solo contra lo visto en la misma ejecución del script
   (`contadores['firmas_vistas']`, un set que se descarta al terminar).
2. **Entre corridas**: `ON CONFLICT (url_fuente) DO NOTHING` en el INSERT,
   que dedupe solo por URL exacta.

Ninguna de las dos detecta el caso real: el mismo incidente cubierto por
dos medios distintos, con URL y título distintos. Eso ya estaba señalado
como pendiente en el backlog ("Persisten deduplicación semántica... sin
conjunto etiquetado") pero sin medir cuánto pesa en la práctica.

`firma_titular` documenta explícitamente la decisión de no intentar esto:
"dos titulares parecidos pueden describir incidentes distintos" — una
decisión de diseño deliberada para evitar falsos merges, no un olvido.

## Qué se midió

Sobre `docs/evidencias/2026-10-06/A09-regeocodificacion/propuesta.csv`
(450 filas reales de `reportes_prensa`, snapshot del 2026-10-06, 20
fuentes distintas incluyendo medios directos y agregadores de Google
Noticias retirados por DEC-011), se calculó similitud de título por
Jaccard de tokens (sin stopwords) para todo par de filas con **fuente
distinta** (101.025 pares posibles sobre 450 filas).

Script: `medir_similitud.py`. Salida completa: `pares_detectados.txt`.

## Resultado

| Umbral Jaccard | Pares cross-fuente detectados |
|---|---|
| ≥ 0.70 | 9 |
| ≥ 0.60 | 13 |
| ≥ 0.50 | 18 |
| ≥ 0.45 | 24 |
| ≥ 0.30 | 97 |

A partir de jacc ≥ 0.70 los pares son duplicados reales e inequívocos del
mismo incidente contado por dos fuentes (ej.: "Detuvieron a un joven en
Ensenada que estuvo prófugo seis años por balear a otro hombre en un
robo", en `0221` y en `Google Noticias La Plata - 0221`). Varios de estos
son agregador-de-Google-Noticias reflejando a su fuente directa (retirado
hacia adelante por DEC-011, pero estas filas históricas no se borraron).

Entre jacc 0.45 y 0.70 aparecen duplicados reales entre medios
genuinamente independientes, sin relación de agregador (ej.: "La
Matanza termina su peor semana de violencia..." en Infobae vs. "La
Matanza: hubo más de un asesinato por día en la última semana" en Diario
Conurbano, jacc 0.50; o el caso del jubilado de Moreno que mató a un
asaltante, cubierto por Primer Plano Online y Minutouno, jacc 0.73).

Por debajo de jacc ~0.45 el método empieza a mostrar falsos positivos
claros: pares que comparten tema y partido (ej. "La Matanza" + "policía"
+ "robo") pero describen hechos distintos. Ejemplo en el límite (jacc
0.44-0.45): un policía de la Ciudad asesinado en Merlo vs. un comisario
bonaerense asesinado en La Matanza — mismo patrón narrativo, incidentes
distintos.

## Lectura

El problema es real pero acotado: ~2% de los pares cross-fuente (9 de
450 filas) son duplicados inequívocos a umbral conservador, y la
duplicación infla el conteo de exposición en esas zonas puntuales, no de
forma generalizada. No es ruido masivo, pero tampoco es cero.

## Por qué no se implementó un dedup automático esta sesión

`firma_titular` ya declara por escrito que evitar duplicación semántica
fue una decisión consciente para no arriesgar falsos merges (perder un
incidente real distinto por error pesa más, para una app de seguridad,
que contar dos veces uno repetido). La medición de arriba confirma que
ese riesgo es real: el margen entre "duplicado seguro" (jacc ≥ 0.70) y
"falso positivo seguro" (jacc ≤ 0.45) es angosto y depende del par
concreto, no solo del umbral.

Cambiar el comportamiento de inserción de producción (saltear filas en
`_evaluar_y_guardar`) sin la posibilidad de revisar en vivo contra la
base real de este entorno es un riesgo que no corresponde asumir
unilateralmente. La medición queda como evidencia para decidir con Rodo
el camino: auto-descarte a un umbral conservador (≥0.70, con el costo de
dejar pasar los duplicados de 0.45-0.70), marcar-para-revisión sin
descartar (agregar columna o reporte aparte, sin tocar el flujo de
guardado), o dejarlo como está y aceptar la inflación acotada medida
arriba.

## Validación de calles sin conjunto etiquetado

El otro pendiente de A09 ("validación de calles sin conjunto
etiquetado") no se abordó esta sesión: requiere armar un conjunto de
casos reales con calle + partido esperado, en la misma línea que
`prensa_etiquetada.csv`, y no hay uno armado todavía para este aspecto
puntual. Queda sin medir, no se inventó una muestra para no repetir el
error que esta skill evita (no fabricar evidencia).

## Implementación (SES-130, mismo día)

Rodo decidió el camino: automatizar sin revisión humana, pero sin
descartar ninguna fila (variante de la opción 2 del README original,
sacando el paso de revisión manual).

Diseño final en `backend/scrapear_noticias_robos.py`
(`_detectar_duplicado_semantico`): antes de insertar una nota nueva, se
busca entre las filas ya guardadas del mismo `tipo_incidente` (no ya
marcadas como duplicado de otra) **la intersección de tres señales**, no
el título solo:

1. **Tiempo**: publicadas dentro de los últimos `DIAS_VENTANA_DUPLICADO`
   = 5 días una de la otra.
2. **Espacio**: a menos de `RADIO_DUPLICADO_METROS` = 1500 m (mismo punto
   geocodificado, no solo mismo partido).
3. **Título**: similitud Jaccard de tokens ≥ `UMBRAL_DUPLICADO_SEMANTICO`
   = 0,70 — el umbral más conservador medido arriba, no un punto medio,
   justamente porque acá no hay humano revisando antes de actuar.

Si las tres se cumplen, la fila nueva se guarda igual (nunca se pierde el
dato crudo) pero queda marcada con `duplicado_de_id` apuntando a la
original (columna agregada en
`backend/migrations/004_duplicados_prensa.sql`, con el mismo patrón de
seguridad en `_asegurar_tabla`). `_FILTRO_FUENTES_PRENSA_SQL` en
`backend/main.py` excluye las filas marcadas de `/reportes-prensa` y del
ajuste de riesgo por reportes recientes — mismo mecanismo que ya usa para
las filas viejas de Google Noticias (no se borra nada, se deja de
contar).

Verificado con 5 pruebas nuevas en `backend/tests/test_scrapear_noticias_robos.py`,
usando los mismos casos reales de esta medición: el par de Moreno (jacc
0,73, dos medios independientes) se detecta y marca; el par límite de
Merlo/La Matanza (jacc 0,44) se rechaza correctamente aunque comparta
partido y tema; el mismo par de Moreno a más de 1500 m se rechaza aunque
el título coincida. 127/127 pruebas de backend en verde (sin contar
`test_integracion_postgres.py`, que necesita una base real, y
`test_run_dev.py`, que falla por falta de `uvicorn` en este entorno —
ninguna de las dos relacionada con este cambio).

**Lo que no se pudo verificar esta sesión**: el filtro de ventana de
días y de `duplicado_de_id IS NULL` vive en el `WHERE` de la consulta SQL
real, no en código Python — no hay forma de probarlo sin una base
Postgres real, inalcanzable desde este entorno. Tampoco se corrió el
scraper contra la base de producción para medir cuántas filas reales
quedarían marcadas con esta lógica. Falta aplicar la migración
(`backend/migrar.py`) y correr el scraper real contra la base para
confirmar en vivo.

## Corrección (SES-133, misma noche): el umbral de título solo era insuficiente en producción real

La primera corrida real con `--guardar` (Rodo/Codex, mismo día) guardó 51 filas nuevas, 0 marcadas como duplicado semántico. Antes de aceptar ese número, Codex verificó un caso concreto del propio log: el tiroteo de Villa Pueyrredón, cubierto por Clarín, TN, Minutouno y La Nación el mismo día, con coordenadas geocodificadas prácticamente idénticas entre sí. Ninguna quedó marcada.

Calculado con la propia `_tokens_similitud`: el par más parecido de los seis (Clarín vs. TN) dio jaccard 0,467, muy por debajo del umbral de 0,70. Los otros cinco pares, más bajo todavía. No es un bug: es exactamente el trade-off medido antes de implementar (por debajo de jacc ~0,45 el método empieza a confundir hechos distintos), aplicado de forma pareja sin distinguir qué tan fuerte era la otra señal disponible -- la coordenada.

La corrección no fue bajar el umbral de título en general (eso reabre el riesgo de falso merge ya medido). Fue reconocer que la cercanía geográfica no es una señal binaria "adentro o afuera del radio de 1500m": una coincidencia **casi exacta** de coordenadas, cuando además ambas notas se geocodificaron a nivel preciso (`calle`/`interseccion`, radio ≤150m -- no al centroide vago de `barrio`, radio 800m, que varias notas sin dirección pueden compartir por coincidencia sin ser el mismo hecho), es mucha más evidencia que "está cerca" y alcanza con mucha menos superposición de título.

Implementado como un umbral graduado en `_detectar_duplicado_semantico`: con coordenada casi exacta (≤300m, provisional) y geocodificación precisa en ambas notas, el umbral de título baja a 0,15; en cualquier otro caso se mantiene el 0,70 de siempre. El radio de 300m es provisional -- Rodo le pidió a Codex una lista de grupos reales de la base (notas de distinta fuente geocodificadas al mismo punto) para calibrarlo con datos en vez de a ojo; queda pendiente ajustarlo cuando esa lista esté.

7 pruebas nuevas con el caso real de Villa Pueyrredón (título ficticio pero jaccard calibrado igual al par real medido, 0,385) y su contraparte de guarda (mismo par, pero con geocodificación vaga en vez de precisa, para confirmar que la coincidencia precisa no se activa sin eso). 129/129 pruebas de backend en verde.

**Sin verificar todavía**: si este ajuste efectivamente captura el caso de Villa Pueyrredón contra la base real (no se volvió a correr el scraper después de este cambio) ni el radio de 300m contra los grupos reales que Codex todavía no trajo.

## Segunda corrección (misma noche, DEC-019): Villa Pueyrredón no se resuelve -- el guard de precisión lo excluye por diseño

Codex midió contra la base real de producción (no contra una muestra ficticia): de toda `reportes_prensa`, solo 36 filas tienen `radio_metros≤150` (nivel `calle`/`interseccion`, el gate de precisión que exige la corrección anterior). El resto (745 filas) está a nivel `barrio` (radio 800, centroide compartido).

Dos hallazgos que cambian la conclusión anterior:

**Villa Pueyrredón tiene `radio_metros=800` en las 4 filas.** El caso que motivó todo este trabajo fue geocodificado a nivel `barrio`, no `calle`/`interseccion`. El guard de precisión de la corrección anterior (exige `radio_metros≤150` en ambas filas) lo excluye por diseño -- no importa qué radio de distancia se use, nunca iba a pasar por esa rama. El mecanismo implementado nunca resolvió el caso que lo motivó; eso no se había verificado contra el dato real de esa fila hasta ahora.

**Dentro de las 36 filas de precisión real, el único grupo multi-fuente es José C. Paz** (Infobae ×2, Minutouno), coordenada idéntica hasta el 7º decimal, radio 80m en las tres. Midiendo el jaccard real entre los títulos de las dos notas de Infobae -- confirmadas como el mismo hecho por la coordenada idéntica -- da **0,0**. Cero palabras en común. El umbral de 0,15 fijado en la corrección anterior tampoco hubiera detectado este caso real.

Los dos únicos pares de fuente distinta dentro de esas 36 filas que NO son el mismo hecho están a 963m y 1.319m. No hay un solo caso real medido entre 1m y ~960m: la señal de distancia es binaria (0m = mismo hecho confirmado, ~960m+ = hechos distintos confirmados), sin zona gris con datos.

**Corrección aplicada**: `RADIO_COINCIDENCIA_PRECISA_METROS` bajó de 300 (estimado) a 100 (dato real, con margen de sobra contra los 963m conocidos). `UMBRAL_DUPLICADO_SEMANTICO_COORDENADA_PRECISA` bajó de 0,15 a 0,0: dentro de la rama de coincidencia precisa, el título no aporta nada que la geografía+tiempo+categoría no aporte ya -- medido contra el único caso real disponible (José C. Paz), exigir superposición de título solo generaba un falso negativo sin evitar ningún falso positivo medido.

**Lo que queda abierto, de nuevo**: Villa Pueyrredón y cualquier duplicado geocodificado a nivel `barrio` siguen sin una solución automática. La coordenada a ese nivel es un centroide que cualquier nota de la zona comparte por default, no evidencia de "mismo lugar exacto" -- usarla ahí reabriría el riesgo de falso merge medido en SES-129. No hay, por ahora, una señal confiable para esos casos sin el paso de revisión humana que Rodo ya descartó explícitamente.

2 pruebas nuevas con el caso real exacto de José C. Paz (detecta) y de los dos falsos positivos confirmados a 963m (no detecta). 34/34 pruebas del scraper, 131/131 de todo el backend.

Documentado en DEC-019 (`docs/gestion/DECISIONES.md`).

**Sin verificar todavía**: si 100m y 0,0 son suficientes contra una muestra más grande (la actual son 36 filas, un solo grupo multi-fuente real); confirmar contra una corrida real posterior que José C. Paz (o un caso equivalente futuro) efectivamente queda marcado.

## Diagnóstico de la geocodificación (21/10, DEC-020): por qué Villa Pueyrredón no es nivel calle

Antes de diseñar una señal nueva para el caso barrio, se probó si el problema era más simple: el extractor perdiéndose una calle que el texto sí menciona. Codex hizo fetch en vivo de las 4 URLs reales y corrió `extraer_ubicacion`/`zona_de_ubicacion` contra el título y la descripción real de cada nota, sin tocar código.

Resultado mixto. Minutouno, Clarín y TN son genuinamente vagas ("una plaza", "una plazoleta"), sin calle ni intersección que extraer. La Nación nombra una plaza y una estación por su nombre propio ("plaza Nunca Más", "estación del ferrocarril Mitre"), que los patrones actuales (`RE_INTERSECCION`, `RE_ALTURA`) no cubren -- buscan calle+calle o calle+altura, no landmarks con nombre propio.

No se construye esa capacidad de reconocimiento de landmarks todavía: aunque existiera, solo mejoraría 1 de las 4 filas, y el guard de precisión de DEC-019 exige precisión en ambas filas de un par -- el caso real seguiría sin detectarse. El dato real confirma algo más general y más importante: mejorar la geocodificación no es una solución general al problema de dedup a nivel barrio, porque buena parte de la cobertura policial real simplemente no da ubicación precisa, con ningún patrón de extracción posible.

Detalle completo en DEC-020 (`docs/gestion/DECISIONES.md`).
