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
