# Auditoría de desajustes silenciosos de comportamiento

Fecha: 23/10/2026. Código auditado: commit `ce941c13535c42583827646cc483c9a9f9ec3392` (corrección de cobertura de rutas ya incluida). Se inspeccionaron utilidades y tests del frontend, reglas de negocio de `backend/main.py`, deduplicación de `backend/scrapear_noticias_robos.py` y los puntos de consumo relevantes de `App.jsx` y `MapaMotoSafe.jsx`. Esta pasada busca **comportamiento del código**, no repite correcciones editoriales de las dos auditorías anteriores. No se cambió implementación.

Hashes SHA-256 de archivos clave: `frontend/src/utils/geoRiesgo.js` `19A85DA0B58A65CA2F466286CD1FA7B40126F26118030D3C43F3924D3A52F31E`; `frontend/src/App.jsx` `5BD1381003F7476C3F00532B399828E83D47C05392817333FDF9FB38C1D33250`; `backend/main.py` `65D26A15082D823E2DB475B1AEDAF0F80B9D090398AA9406848A5EF0FFD72B4F`; `backend/scrapear_noticias_robos.py` `55330724CD914284B311DC8B0244DDFA00AFC3D818360CF46256BE4B1B746988`. Si cambian, revalidar líneas y resultados.

## B01 — Reproducción independiente de H03: noticia vieja rejuvenecida

**Severidad: alta; ya registrado como H03 en `docs/assessment_2026-10-22/ASSESSMENT.md` y A09 en BACKLOG. No es un descubrimiento nuevo.** `backend/main.py:1096-1105` define `_FECHA_REFERENCIA_PRENSA_SQL`. El comentario dice que una fecha mal extraída o antigua no debe «dejar vigente una nota vieja». La expresión `CASE` acepta `publicado_en` solo si cae entre `creado_en - 30 días` y `creado_en + 1 día`; en cualquier otro caso usa `creado_en`. Por ello también convierte **una fecha editorial antigua válida** en fecha reciente.

**Caso reproducido en PostgreSQL aislado:** `publicado_en='2020-01-01'`, `creado_en='2026-10-23'` produce `fecha_referencia='2026-10-23'` con la expresión del código. Se ejecutó `SELECT CASE WHEN timestamp '2020-01-01' BETWEEN timestamp '2026-10-23' - interval '30 days' AND timestamp '2026-10-23' + interval '1 day' THEN timestamp '2020-01-01' ELSE timestamp '2026-10-23' END`; resultado `2026-10-23 00:00:00`. El contenedor PostGIS efímero se eliminó después. Es un caso de entrada sintético, no una afirmación de que exista hoy esa fila en producción.

**Efecto visible:** `listar_reportes_prensa` usa esa fecha para filtrar los 30 días (`backend/main.py:1110-1137`), y `_obtener_reportes_recientes_por_tipo` la usa para el ajuste de riesgo de siete días (`backend/main.py:1166-1210`). Una noticia antigua que el scraper vuelva a encontrar puede reaparecer en el mapa y subir un nivel de riesgo vial o de inseguridad como si fuese reciente. El resultado no emite error ni aviso de «fecha de ingesta usada».

## B02 — La navegación puede declarar llegada estando lejos del destino

**Severidad: alta.** `frontend/src/App.jsx:1294-1319` afirma que medir el recorrido sobre la polilínea hace coincidir el criterio con la tarjeta y exige estar «cerca de verdad». Sin embargo, `calcularProgresoRuta` proyecta el GPS al segmento y limita el parámetro de proyección al extremo (`frontend/src/utils/geoRiesgo.js:63-83`). En `App.jsx:1315-1321`, `Math.max(0, progresoUltimo - progresoGPS)` da cero cuando el GPS quedó **más allá** del último vértice. Si `pasoActual` ya está en el último paso `arrive`, se llama a `desactivarModoViaje('Llegaste a destino')`.

**Probe ejecutado:** polilínea `[-34.60,-58.40] → [-34.59,-58.40]`, último paso en `[-34.59,-58.40]`, GPS en `[-34.57,-58.40]`. `distanciaKm(GPS,destino)=2,2239 km`; ambos progresos proyectados `1,11195 km`; `faltanKm=0`, que pasa el umbral real de `0,03 km` (`App.jsx:96`). El probe que importa la función real queda en `PROBES_BUGS_REALES/probe_llegada.mjs`.

**Efecto visible:** desaparecen instrucciones y modo viaje con el mensaje «Llegaste a destino» aunque el GPS esté a más de 2 km. El caso requiere estar ya en el último paso; no se afirma que ocurra en toda navegación. La detección de desvío es otro efecto React y no impide que este cálculo de llegada devuelva cero.

## B03 — Reproducción independiente de H12: ventana temporal de duplicados incompleta

**Severidad: media; ya registrado como H12 en `docs/assessment_2026-10-22/ASSESSMENT.md` y A09 en BACKLOG. No es un descubrimiento nuevo.** `backend/scrapear_noticias_robos.py:720-748` y sus comentarios describen notas «cerca en el tiempo» dentro de `DIAS_VENTANA_DUPLICADO=5`. La consulta solo exige `COALESCE(publicado_en, creado_en) >= referencia - 5 días`; no hay `<= referencia + 5 días`. El filtro posterior verifica distancia y similitud, pero no fecha. Los tests existentes no cubren un candidato posterior a la noticia nueva.

**Probe ejecutado contra la función real:** noticia entrante de `2026-01-01`, misma categoría, coordenada exacta y título que una fila candidata simulada con id 7. El cursor registra límite inferior `2025-12-27` y ninguna condición superior; `_detectar_duplicado_semantico` devuelve `7`. Si esa fila candidata en la base fue publicada, por ejemplo, el `2026-01-20`, la consulta también la entregaría: está a 19 días, fuera de la ventana anunciada. El probe con cursor falso verifica la rama Python y la SQL emitida; **no se ejecutó un INSERT de este caso en la base real**. Archivo: `PROBES_BUGS_REALES/probe_dedupe_future.py`.

**Efecto visible:** la noticia anterior puede quedar marcada `duplicado_de_id=7`; la API filtra esa fila en `_FILTRO_FUENTES_PRENSA_SQL` (`backend/main.py:1091`), por lo que no aparece en la capa de prensa ni se considera para el ajuste de riesgo. Solo se materializa si la noticia antigua se ingesta después de una posterior suficientemente similar y cercana, algo posible en backfills o sitemaps desordenados.

## B04 — «Índice de riesgo del mapa visible» se calcula con zonas fuera del mapa y filtros

**Severidad: media.** En `frontend/src/App.jsx:1528-1533`, `indiceRiesgo` suma el peso de **todas** las `zonasAjustadas`; su `useMemo` depende solo de ese array. En `App.jsx:1366-1371`, `zonasFiltradas` sí aplica niveles y búsqueda, y el mapa además tiene viewport propio. Pero `App.jsx:1770-1771` etiqueta el número «Índice de riesgo del mapa visible (0-100)».

**Caso concreto por cálculo de la implementación:** con dos zonas ajustadas, una `bajo` de peso 1 y otra `critico` de peso 5 (`frontend/src/constants.js:21`), el índice es `(1+5)/(2×5)×100=60`. Si el usuario apaga «crítico» o hace zoom hasta ver solo la zona baja, `zonasAjustadas` no cambia y el número sigue en 60. El código no lee `zonasFiltradas`, `nivelesActivos` ni límites del mapa para ese número. Este caso se verificó por las dependencias y la fórmula, no mediante captura de navegador.

**Efecto visible:** estadística que dice medir el mapa visible puede permanecer roja/60 después de ocultar la zona crítica. Es un desajuste entre dato y etiqueta de UI; no cambia el score de rutas.

## B05 — Búsqueda que pasa de cero a una zona no dispara el vuelo al cargarse datos

**Severidad: media-baja, dependiente de secuencia.** `frontend/src/App.jsx:1374-1384` comenta que el vuelo se dispara al teclear si hay una sola coincidencia. El efecto lee `zonasFiltradas.length`, pero declara solo `[busqueda]` como dependencia y desactiva explícitamente `react-hooks/exhaustive-deps`. `zonasFiltradas` depende de `zonasAjustadas` y `nivelesActivos` (`App.jsx:1366-1371`).

**Caso concreto:** usuario escribe una búsqueda de al menos tres caracteres cuando las zonas todavía no cargaron: el efecto ve cero coincidencias. Llega el fetch y `zonasFiltradas` pasa a una coincidencia, mientras `busqueda` permanece igual. React vuelve a renderizar, pero el efecto no se vuelve a ejecutar; no hay `setVuelo` ni `setZonaResaltada`. Lo mismo puede ocurrir al cambiar filtros hasta dejar una coincidencia. Es una reproducción por secuencia de estados/dependencias React; no se hizo un E2E de ese flujo.

**Efecto visible:** resultado único en el mapa sin el centrado/resaltado automático prometido por el comentario. El siguiente cambio de texto sí vuelve a dispararlo.

## Observación condicionada, de menor prioridad

`backend/main.py:458-463` declara que el hash de artefactos detecta umbrales desincronizados y `/health` lo expone; si `_huella_artefactos_riesgo()` lanza `OSError`, asigna `UMBRALES_RIESGO_ACTUALIZADOS=True`. Una ausencia/permisos de lectura de algún artefacto se presenta como «actualizado». No se simuló el arranque con ese fallo, y el modelo faltante probablemente cause además problemas de carga; queda como fallo de observabilidad **condicionado**, no como incidencia productiva confirmada.

## Balance y límites

**Hallazgos nuevos de esta pasada: B02, B04 y B05.** B01 y B03 son reproducciones propias de H03/H12 ya abiertos; se documentan aquí para dejar completa la evidencia del contraste solicitado, pero no se cuentan ni se priorizan como problemas nuevos. Ninguno de estos cinco es la corrección de cobertura de `ce941c1`.

Se verificó el arreglo de cobertura de `ce941c1`: `coberturaRegistrada` usa solo `coberturaPorFuente[i]?.siniestro ?? null`. No se volvió a reportar como bug. Las utilidades de `storage.js`, `hexBin.js` y `tiempo.js` no ofrecieron otro desajuste de negocio con impacto confirmado en esta pasada. Las dependencias de los `useMemo` relevantes para rutas y progreso sí cubren sus variables leídas; B05 es un `useEffect`, no un `useMemo`.

Comandos ejecutados: `npm.cmd test -- --run` en `frontend` (**109 aprobados**); `python -m pytest -q tests/test_scrapear_noticias_robos.py tests/test_main.py` con `backend/venv312` (**118 aprobados**, una advertencia de dependencia); probe Node de llegada; probe Python de deduplicación; consulta SQL en PostGIS efímero. No se corrieron lint, build, E2E ni pruebas de carga en esta sesión. La suite en verde demuestra que estos casos no están cubiertos por los tests actuales; no demuestra que cada disparador ya ocurrió en producción.

No se proponen parches aquí. Los B01–B05 son localizadores de esta auditoría, no un segundo backlog; el seguimiento y las decisiones pertenecen a `docs/gestion/BACKLOG.md` y `DECISIONES.md`.
