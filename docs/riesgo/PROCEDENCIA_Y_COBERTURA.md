# Cobertura, procedencia y límites de las capas de riesgo

**Ítems:** A05, A06, A09, A10, A11, D03, D04.  
**Estado:** implementación inicial de cobertura por fuente; validación externa pendiente.

## Qué muestra el comparador

Para cada alternativa se muestrean hasta 120 vértices de su trazado. Se informa
por separado la proporción cercana a registros de **siniestros** y de
**inseguridad**. Una fuente ausente se muestra como `sin datos`, que es
distinto de `0%`: el primero no permite concluir nada y el segundo indica que
la fuente disponible no tuvo registros próximos bajo el radio configurado.

La recomendación «menor exposición» exige al menos 60% de cobertura del eje
histórico de siniestros. Registros de inseguridad no reemplazan esa cobertura:
ambas capas tienen procedencia, unidad y significado distintos. El resultado
compara alternativas del mismo pedido; no estima siniestralidad por viaje.

## Procedencia y actualización

| Capa | Procedencia | Unidad | Actualización / TTL | Límite visible |
|---|---|---|---|---|
| Hotspots | Siniestros históricos procesados en CABA | Punto/cluster | Backend consulta cada 5 min desde el cliente | No cubre ni predice automáticamente GBA. |
| Corredores | Corredores offline derivados de siniestros | Geometría de calle | Carga al iniciar; cache local de última respuesta | Período visible en la leyenda (siniestros 2019–2025, desde `/capas/cobertura`); fecha de generación del archivo en el tooltip. |
| Inseguridad | Delitos GCBA procesados, general o con moto | Punto/cluster | Carga al iniciar; cache local de última respuesta | No equivale a gravedad vial. Nivel base por percentil fijo, ajustado por franja horaria y reportes recientes (ver más abajo). |
| Prensa | Noticias filtradas y geocodificadas | Hecho puntual aproximado | Cliente consulta cada 10 min; vigencia de 30 días | Puede ser ambiguo, incompleto o tener ubicación aproximada. |
| Reportes comunitarios | Personas usuarias | Hecho puntual | Consulta cada 30 s; vigencia por categoría | No son verificados automáticamente. |

La aplicación conserva la última respuesta local cuando una actualización
falla. Esa persistencia no debe presentarse como fecha de origen del dato. Para
cerrar A10/A11 falta devolver desde backend la fecha de generación de cada
artefacto y mostrarla en la interfaz.

### Período de cobertura visible (A10/A11/A15, SES-075)

Decisión de Rodo: la interfaz muestra el **período que cubren los datos** de cada capa, porque es lo que sirve para juzgar la vigencia del riesgo. La fecha de generación del archivo queda como dato secundario en un tooltip. `GET /capas/cobertura` lo sirve desde `backend/metadatos_capas.json`, que genera `notebooks/generar_metadatos_capas.py` a partir de `data/` (no versionado), y suma prensa de forma dinámica:

| Capa | Período (datos de 2026-10-06) | Registros | Archivo de la capa |
|---|---|---|---|
| Hotspots y corredores | 2019-01-01 a 2025-12-31 | 23.343 siniestros con moto | 2026-09-07 / 2026-09-04 |
| Inseguridad general | 2023-01-01 a 2025-12-31 (últimos 3 años del dataset) | 447.938 delitos | 2026-09-09 |
| Inseguridad con moto | 2023-01-01 a 2025-12-31 | 15.792 delitos | 2026-09-09 |
| Prensa | últimos 30 días + fecha de la nota más reciente en la base | dinámico | — |

Hay que regenerar el JSON cada vez que se regeneran las capas.

### Factores dinámicos por capa

Qué tan en vivo está cada capa de riesgo, de un vistazo (no reemplaza los
comentarios de código citados en cada fila, los resume):

| Capa | Hora | Clima en vivo | Prensa reciente |
|---|---|---|---|
| Hotspots (siniestros) | Sí, feature del modelo entrenado | Sí, feature del modelo entrenado (lluvia, temperatura, humedad de Open-Meteo) | Sí, ajuste visible por choques cercanos reportados en los últimos días |
| Corredores (siniestros) | Sí, feature del modelo entrenado | Sí, feature del modelo entrenado | Sí, ajuste visible por choques cercanos a cualquier punto del trazado |
| Inseguridad (general/moto) | Sí, ajuste visible por franja horaria calibrada según subtipo (no pasa por un modelo: el nivel base es un percentil fijo) | No | Sí, ajuste visible por robos/hechos de inseguridad cercanos |

Los reportes comunitarios (robo, choque, pavimento, iluminación) se muestran
como capa propia en el mapa, con su propio timer de vigencia por categoría y
su propio mecanismo de retiro por consenso de desmentidas. No modifican el
`nivel_riesgo` de ninguna de las tres capas de la tabla: ese ajuste solo lo
dispara `reportes_prensa` (noticias scrapeadas), no un reporte de usuario.

El badge de clima de la interfaz toma el mismo objeto `clima` que ya viajó en
la respuesta de `/hotspots` y que el modelo ya usó para calcular ese
`nivel_riesgo` (antes era un fetch aparte del navegador a Open-Meteo con
parámetros distintos, que podía mostrar una temperatura distinta a la que
realmente influyó en el nivel mostrado).

### Ajuste dinámico de inseguridad (franja horaria)

Hotspots y corredores incorporan la hora como variable del modelo entrenado:
el nivel de riesgo que devuelven ya varía según la hora de la consulta.
Inseguridad era, hasta esta revisión, la única capa sin componente horario:
el nivel salía de un percentil fijo (bajo/medio/alto/crítico calculado una
sola vez sobre `cantidad_delitos`, ver `cargar_hotspots_inseguridad.py`) y no
cambiaba entre las 4am y las 20hs, a pesar de que el propio dataset de
Delitos del GCBA muestra picos horarios reales y distintos por subtipo
(19-23hs para robos con moto, 17-21hs para delito general; columna
`franja_horaria`, antes perdida por un alias incompleto en
`fetch_delitos_caba.py`).

`/hotspots-inseguridad` sube ahora el nivel un escalón cuando la hora de
Buenos Aires de la consulta cae en la franja pico calibrada para el subtipo
pedido (`FRANJA_PICO_INSEGURIDAD` en `backend/main.py`), sin reentrenar nada
ni tocar el percentil base: mismo criterio que el ajuste ya existente por
reportes de prensa recientes de esta misma capa, con el que se apila (tope
en `crítico`). Cada fila devuelve `ajustado_por_horario` y
`motivo_ajuste_horario` para que quede explícito en la interfaz y en la
evaluación cuándo el nivel mostrado no es el percentil crudo. El cálculo vive
únicamente en el backend — la versión anterior (frontend, por
`FRANJA_PICO_INSEGURIDAD_GENERAL/_MOTO` en `constants.js`) se retiró para
evitar una doble calibración y el riesgo de doble ajuste sobre la misma
zona.

No sustituye a un modelo de predicción de delito (horizonte distinto al de
siniestralidad vial, exigiría su propia evaluación académica); es el mismo
principio que ya se aplica a siniestros, usando un dato horario real que
estaba en el dataset pero sin usar.

## Validación pendiente y reproducible

`docs/evidencias/2026-09-13/A09/prensa_etiquetada.csv` es la plantilla para un
conjunto revisado por persona. Ejecutar:

```powershell
python backend/evaluar_extractor_prensa.py docs/evidencias/2026-09-13/A09/prensa_etiquetada.csv
```

El script entrega precisión, recall, abstenciones y error geográfico sólo si
se completan etiquetas reales. No usar pruebas sintéticas como métrica de
calidad de prensa.

Las rutas de referencia se registran en
`docs/evidencias/2026-09-13/D03/rutas_referencia.csv`. Deben contener casos
con cobertura parcial, empate, desvío y fuentes discordantes antes de ajustar
el radio de 60% o los pesos de ranking.
