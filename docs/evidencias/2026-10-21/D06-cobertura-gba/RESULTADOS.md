# D06 — ampliar cobertura de GBA con fuentes comparables (investigación, sin tocar código) (2026-10-21, SES-155)

**Pregunta real que responde esta ficha**: hoy el modelo entrena y evalúa solo con datos de siniestros/delitos
de CABA (`docs/datos/FICHAS_FUENTES.md`, fuente "Siniestros viales (GCBA)" y "Delitos (GCBA)", ambas con
límite documentado "Solo CABA"), pero el producto se llama y se presenta como "MotoSafe **GBA**" (Gran
Buenos Aires, que incluye decenas de partidos de la Provincia de Buenos Aires fuera de la Ciudad). D06
pregunta si existe una fuente pública real de siniestros/delitos para esos partidos, estructuralmente
comparable a la de CABA -- no para usarla todavía, solo para confirmar si existe y bajo qué condiciones.

**No se descargó ningún archivo de datos al proyecto ni se tocó ningún script del pipeline.** Lo único que
se trajo fuera del proyecto (a una carpeta temporal de la sesión, no al repo) fue el PDF público del manual
de usuario de una de las bases, para poder leer su diccionario de variables real -- se describe más abajo,
en "Método".

## Resumen ejecutivo (la respuesta corta a D06)

**Sí existe una fuente real, con microdatos a nivel de hecho individual, que cubre los partidos de GBA (no
solo CABA) y es parcialmente comparable a la fuente actual de siniestros**: la base **SAT-MV (Sistema de
Alerta Temprana de Muertes Viales)** del SNIC, publicada por el Ministerio de Seguridad de la Nación en
`datos.gob.ar`. Tiene una limitación real importante: **solo cubre víctimas fatales**, no todas las
severidades como la fuente de CABA. Para delitos, la fuente nacional comparable más cercana (SNIC
Departamental) **solo tiene agregados por partido/mes, no hechos individuales con coordenadas** -- no es
comparable en granularidad a la fuente de delitos de CABA.

Ninguna de las fuentes provinciales (Provincia de Buenos Aires) ni municipales relevadas publica microdatos
de siniestros o delitos a nivel de hecho individual. Esto confirma, con evidencia real y no por
suposición, que la Provincia de Buenos Aires **no tiene un equivalente directo** al portal de datos abiertos
de CABA para esta temática.

## Qué se revisó, fuente por fuente (lo que pidió Rodo, en orden)

### 1. Portal de datos abiertos de la Provincia de Buenos Aires

**Verificado real**: `catalogo.datos.gba.gob.ar` ("Datos Abiertos PBA", CKAN v2.6.3). Se navegó directamente
a los organismos relevantes:

- **Ministerio de Seguridad** (PBA): **3 datasets publicados**, ninguno es de siniestros viales o delitos a
  nivel de hecho (se revisaron los 3 títulos exactos directamente en el organismo, no solo por búsqueda por
  palabra clave).
- **Ministerio de Transporte / Infraestructura** (bajo el cual está la Subsecretaría de Política y Seguridad
  Vial provincial): **1 dataset publicado**, tampoco es de siniestros a nivel de hecho.

**Conclusión real**: el catálogo oficial de datos abiertos de la Provincia de Buenos Aires **no tiene
microdatos de siniestros viales ni de delitos**, ni agregados por partido en formato de datos (CSV/XLSX)
dentro de ese catálogo.

### 2. ANSV (Agencia Nacional de Seguridad Vial)

**Verificado real**: búsquedas directas en `datos.gob.ar` por `ansv` (0 resultados) y por `seguridad vial`
(5 resultados, ninguno publicado por la ANSV ni con datos de siniestros vehiculares a nivel de hecho -- ver
tabla de la sección 2 más abajo). El dominio `argentina.gob.ar/seguridadvial/observatorio-vial` (ruta
esperada del Observatorio Vial de la ANSV) devuelve **404** al día de hoy.

**Conclusión real**: la ANSV, al día de hoy, **no tiene presencia como publicador de datasets abiertos** en
el portal nacional. Sus informes de siniestralidad (anuarios) existen pero no se encontró un dataset
descargable asociado a ellos en `datos.gob.ar`. Esto no descarta que existan en el sitio propio de la ANSV
fuera del catálogo nacional, pero no se encontró un enlace real a eso desde ningún dataset relevado.

### 3. Portales municipales de partidos de GBA

**Revisado por búsqueda** (La Matanza, Lomas de Zamora, Quilmes, San Isidro, Vicente López, Morón, entre
otros de primer/segundo cordón): no se encontró, para ninguno, un portal de datos abiertos propio con un
dataset de siniestros viales o delitos a nivel de hecho individual. Esto queda documentado como "no
encontrado con el esfuerzo razonable de esta sesión", no como "confirmado que no existe en ningún partido" --
un relevamiento exhaustivo de los ~40 partidos de GBA, uno por uno, excede el alcance de esta tarea de
investigación puntual.

### 4. Ministerio de Seguridad de la Provincia de Buenos Aires (delitos)

Ya cubierto en el punto 1 (el Ministerio de Seguridad de PBA publica solo 3 datasets en el catálogo
provincial, ninguno de delitos a nivel de hecho). La Subsecretaría de Política y Seguridad Vial provincial
(bajo Ministerio de Transporte, publicaciones en `publicaciones.transporte.gba.gob.ar`) tampoco publica
microdatos -- solo informes PDF/PPTX con conteos agregados por municipio (ej. "LA MATANZA 2861" siniestros en
2025), cuyos datos de origen (Superintendencia de Análisis Criminal, Ministerio de Seguridad PBA) no se
liberan como dataset descargable.

## La fuente real más prometedora: SNIC / SAT (Ministerio de Seguridad de la Nación)

Encontrada por búsqueda dirigida en `datos.gob.ar` (`q=estadisticas+criminales`), confirmada visitando cada
página de dataset real y leyendo su manual de usuario real (ver "Método" abajo).

### SAT-MV — Muertes viales (la más relevante para siniestros)

| Campo | Valor real verificado |
|---|---|
| Página | https://www.datos.gob.ar/dataset/muertes-viales-sistema-de-alerta-temprana-estadisticas-criminales-en-la-republica-argentina |
| Publicador | Ministerio de Seguridad Nacional, Dirección Nacional de Estadística Criminal |
| Licencia | Creative Commons Attribution 4.0 |
| Formatos | XLSX, CSV, DTA, SAV (microdatos) + PDF (informes y manual de usuario) |
| Actualización | Anual (declarada `R/P1Y`). Última modificación de la base: 02-12-2025 |
| Granularidad geográfica | **Hecho individual, con `latitud`/`longitud` geocodificadas** (método: librería `Nominatim` sobre OpenStreetMap, a partir de calle/altura/localidad/departamento/provincia reportados) + `departamento_id`/`departamento_nombre` -- el manual aclara explícitamente: *"Cada jurisdicción se divide en departamento, de Ciudad Autónoma de Buenos Aires corresponde a Comunas y en **Provincia de Buenos Aires corresponde a Partidos**"*. También trae `localidad_id`/`localidad_nombre`. |
| Cobertura temática | **Solo víctimas fatales** ("muertes en accidentes viales con víctimas fatales") -- no cubre heridos ni siniestros sin muertos. |
| Columnas relevantes para comparar con CABA | `fecha_hecho`, `anio`, `mes`, `hora_hecho`, `calle_nombre`, `calle_altura`, `calle_interseccion_nombre`, `tipo_lugar` (ruta nacional/provincial/etc.), `modo_produccion_hecho` (categórica), `clima_condicion`, `victima_clase` (conductor/acompañante/peatón/ciclista), **`victima_vehiculo`** con valor `6 = Motocicleta` (comparable directo al campo de modo de desplazamiento que ya usa la fuente de CABA), edad y sexo de víctimas e inculpados. |
| Tamaño real | 37.533 registros totales en la base (hechos + víctimas + inculpados combinados en formato largo, un registro por persona involucrada por hecho -- **no** es una fila por hecho; hay que filtrar por `tipo_persona` y contar `id_hecho` único para obtener cantidad de hechos, según indica el propio manual). |
| Dónde se verificó | Página real del dataset (`get_page_text` del navegador) + manual de usuario real (PDF público, descargado solo a una carpeta temporal fuera del repo para extraer el texto con `pdftotext`, ver "Método"). |

**Diferencia real importante con la fuente de CABA**: la fuente de CABA (`siniestros_viales_hechos.csv` /
`victimas.csv`) incluye siniestros de **todas las severidades**, no solo los que terminan en muerte. Usar
SAT-MV tal cual para "ampliar a GBA" **subrepresentaría sistemáticamente el riesgo real** si se la tratara
como equivalente a la fuente de CABA -- un partido con muchos heridos pero pocos muertos aparecería con
muy pocos casos. No es un defecto de la fuente, es un alcance distinto que hay que tener en cuenta en
cualquier evaluación futura (fuera del alcance de esta ficha, que es solo de relevamiento).

### SAT-HD — Homicidios dolosos (posible análogo parcial para delitos)

Misma estructura, mismo publicador, misma licencia (CC BY 4.0), mismo manual de usuario (formato), misma
granularidad geográfica (`departamento_id` = partido en PBA, con lat/long geocodificada). Cubre
**homicidios dolosos/femicidios únicamente** -- mucho más angosto que el dataset de "Delitos (GCBA)" que
hoy alimenta el modelo (que incluye robos, hurtos, lesiones, etc. con coordenadas). Página:
https://www.datos.gob.ar/dataset/homicidios-dolosos-sistema-de-alerta-temprana-estadisticas-criminales-en-la-republica-argentina

### SNIC - Departamental (agregado, no a nivel de hecho)

| Campo | Valor real verificado |
|---|---|
| Página | https://www.datos.gob.ar/dataset/snic-departamental-estadisticas-criminales-en-la-republica-argentina-por-departamentos |
| Descripción real | "Hechos delictivos y víctimas por tipo de delito... **por departamentos**. Cantidades y tasas **desde 2014**." |
| Categorías de delito | Homicidios dolosos, Hurtos, Lesiones culposas, Lesiones dolosas, Otros delitos, Robos, Robos agravados, Tentativas de robo, Violaciones (lista real tomada de las palabras clave del dataset) |
| Granularidad | **Solo agregado por departamento/partido y mes** (hay un recurso "por departamentos y mes y sexo") -- **sin coordenadas, sin hecho individual**. |
| Licencia / actualización | CC BY 4.0; actualizado 01-06-2026, anual. |

**Uso realista**: podría servir en el futuro como una variable de contexto a nivel de partido (una tasa
departamental de delito), no como reemplazo del dataset de delitos geolocalizados de CABA -- la pérdida de
granularidad (de punto a partido completo) es real y significativa para un modelo que hoy usa hotspots de
alta resolución.

## Método (qué se verificó realmente y cómo)

1. Búsquedas reales en `www.datos.gob.ar` (`estadisticas+criminales`, `ansv`, `seguridad+vial`) navegando
   con el navegador integrado, leyendo el listado real de resultados (no solo el resumen de un buscador).
2. Cada página de dataset candidato se abrió y se leyó completa (`get_page_text`) para confirmar licencia,
   publicador, fecha de actualización y lista real de recursos -- no se infirió nada de un snippet de
   búsqueda.
3. Para confirmar las columnas reales y la granularidad geográfica exacta de SAT-MV (la fuente más
   prometedora), se abrió el enlace real del "Manual de usuario" (PDF público en
   `cloud-snic.minseg.gob.ar`). El navegador integrado no puede previsualizar ese PDF (fuerza una descarga),
   así que se usó `WebFetch` para traerlo -- esto dejó una copia del PDF en una carpeta temporal de
   herramientas de la sesión (fuera del repo del proyecto). Se extrajo su texto real con `pdftotext
   -layout` (herramienta ya presente en el entorno) a un archivo temporal en el scratchpad de la sesión, y
   se leyó ese texto con `Grep`/`Read` para confirmar el diccionario de variables real citado arriba. **No
   se guardó ningún archivo de datos ni el PDF dentro del repositorio del proyecto**, y no se tocó ningún
   script del pipeline.
4. El catálogo de la Provincia de Buenos Aires (`catalogo.datos.gba.gob.ar`) se navegó directamente por
   organismo (Ministerio de Seguridad, Ministerio de Transporte) para listar sus datasets reales, en vez de
   confiar en una búsqueda por palabra clave que podría no encontrar un título con otra redacción.
5. Los portales municipales se revisaron por búsqueda general; no se encontró ninguno con un dataset
   relevante, por lo que no se navegó a cada dominio municipal individualmente (ver limitación en la
   sección 3 arriba).

## Qué no se hizo (a propósito, por instrucción explícita)

- No se descargó ningún archivo de datos (XLSX/CSV/DTA/SAV) de SAT-MV, SAT-HD ni SNIC Departamental.
- No se tocó ningún script de `notebooks/` ni del pipeline del modelo.
- No se evaluó la calidad real de los datos de SAT-MV (completitud, consistencia, cobertura real por
  partido) -- sería el "paso 2" que esta ficha deja planteado para que Rodo decida si vale la pena, no algo
  que se haya hecho acá.
- No se relevó partido por partido los ~40 municipios de GBA uno por uno (ver limitación real documentada en
  la sección 3).

## Qué queda para que decida Rodo (si quiere avanzar)

Si en algún momento se quiere evaluar en serio ampliar a GBA, las dos fuentes reales con mejor chance son:

1. **SAT-MV** para siniestros -- pero habría que decidir explícitamente cómo tratar la diferencia de alcance
   (solo fatales vs. todas las severidades de CABA): ¿usar SAT-MV solo para un sub-modelo de "riesgo de
   muerte" en GBA, separado del modelo de severidad general de CABA? ¿o conseguir algún proxy adicional para
   heridos?
2. **SNIC Departamental** para una variable de contexto de delito a nivel de partido, sabiendo que es mucho
   menos granular que el dataset de delitos de CABA.

Ninguna decisión de incorporación se tomó ni se sugiere tomar en esta ficha -- es relevamiento, como pidió
Rodo explícitamente.
