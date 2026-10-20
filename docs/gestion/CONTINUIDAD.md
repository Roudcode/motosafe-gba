# Continuidad del proyecto — leer primero

**Actualizado:** 2026-10-20. **Responsable de producto:** Rodo. **Estado:** catálogo A01–A24 mayormente cerrado o validado (ver "Ejecución actual" en BACKLOG.md para el detalle ítem por ítem); SES-116 cerró A04 y D02/A24, SES-117 a SES-123 completaron una serie de auditorías visuales (vertical de celular, design tokens, apartado de prensa, consistencia general). Infraestructura: Tailscale Funnel caído desde no se sabe cuándo entre el 12/10 y el 20/10, recuperación en curso con Rodo (ver última entrada de este archivo).

## Pedido actual de Rodo

Centralizar auditoría, documentación, decisiones y cambios para poder retomar con Claude. Rodo autorizó avanzar por bloques, con commit y push de cada entrega. El foco actual es ampliar y validar la ingesta multifluente de prensa sin confundirla con el modelo académico de gravedad.

## Punto de transferencia para otra IA

- **Base antes de trabajar con Codex:** `c24b8a7` (auditada como fotografía histórica).
- **Cambios de Codex entregados:** `d2fb3ec` en `main` (`feat: centralizar continuidad y reforzar integridad`). Incluye documentación, código y pruebas de SES-001 a SES-004.
- **Estado al cerrar esa entrega:** árbol de trabajo limpio; no se modificaron datasets ni el modelo.
- **Instrucción de arranque:** ejecutar `git status`, leer este archivo y luego `docs/README.md`, `BACKLOG.md`, `BITACORA.md` y `DECISIONES.md`. No asumir que A01–A23 están cerrados: el estado concreto está en la tabla «Ejecución actual» del backlog.

## Qué se hizo

**Corrección de continuidad del 13/09:** el registro del 11/09 anticipaba un backlog y dos documentos que aún no se habían escrito. Se completaron BACKLOG, PRIORIZACION y VALIDACION el 13/09. El estado descrito abajo corresponde ahora a los archivos existentes, no a una implementación de las mejoras.

1. Auditoría integral sobre commit `c24b8a7` y datos locales; informe y evidencias en `docs/assessment_2026-09-11/`.
2. Se creó el centro documental `docs/README.md` y la gestión compartida en esta carpeta.
3. Se amplió el catálogo a **63 ítems: 23 hallazgos y 40 oportunidades adicionales**. Hay dependencias y solapamientos explícitos; no representan 63 proyectos independientes.
4. Se prepararon paquetes de prioridad y protocolo de validación.
5. SES-004 implementó un primer bloque: token privado para borrar reportes, sanitización de prensa, validación de entradas, pool acotado, respuesta vacía de hotspots, correcciones de riesgo/ranking y recuperación de carga. No se modificaron el modelo ni los datasets.
6. SES-005 inició A14 con migraciones SQL versionadas y reforzó la advertencia de cobertura del comparador. La migración aún no fue ejecutada contra PostgreSQL real porque el intérprete base del `venv` local dejó de estar disponible.
7. SES-006 evitó que respuestas HTTP fallidas vacíen corredores, inseguridad, reportes y prensa como si fueran una respuesta sin datos. Se mantienen las cachés visibles; faltan estados específicos por capa.
8. SES-007 añadió un aviso visible cuando una capa secundaria no puede actualizarse y conserva información en caché. Los reintentos específicos por capa siguen pendientes.
9. SES-008 agregó un reintento global desde ese aviso; sigue pendiente separar reintentos y fechas por fuente.
10. SES-010 habilitó zoom nativo del navegador y foco visible; falta revisión visual accesible.
11. SES-020 agregó cobertura registrada por trazado para evitar que ausencia de zonas se presente como menor exposición.

## Estado técnico comprobado en la auditoría

- React + Vite + MapLibre; FastAPI + psycopg2/PostgreSQL/PostGIS. Documentos anteriores aún dicen Leaflet.
- Modelo guardado: Random Forest, 300 árboles, profundidad 12, mínimo cinco muestras por hoja, balanced_subsample, 55 columnas.
- 23.343 hechos de moto limpios; 23.338 filas para modelado; 740 hotspots viales; 243 corredores; inseguridad 633 general + 502 con moto.
- Datos históricos de CABA. Ruteo y prensa en GBA no equivalen a cobertura predictiva validada del conurbano.
- Última verificación local: backend 55 pruebas aprobadas en SES-004; SES-005 verificó sintaxis de `migrar.py` con Python alternativo y frontend 73 con `node node_modules/vitest/vitest.mjs run`, lint y build aprobados. El `venv` del backend ya no puede iniciar porque su Python base no existe en la ruta configurada. Build advierte un bundle JavaScript de 1,29 MB antes de gzip. No hubo E2E contra PostgreSQL, servicios de ruteo ni navegador.
- Métricas reconstruidas del pickle en el split declarado: macro-F1 0,378; GRAVE precision 0,111/recall 0,735; MORTAL precision 0,116/recall 0,482. **No son una nueva prueba independiente.**
- Navegador rechazó certificado HTTPS local. No hay certificación visual de esta revisión ni E2E con PostgreSQL/TomTom reales.
- SES-021 formalizó el contrato de gravedad condicionada y añadió un evaluador temporal que evita fuga de preprocesamiento, mide ablaciones, faltantes, calibración e incertidumbre. No modifica el modelo productivo. Se verificó su sintaxis con Python alternativo; no se generaron métricas nuevas porque el `venv` local depende de un intérprete base inexistente.
- SES-022 separó la cobertura de rutas por fuente: inseguridad no puede completar artificialmente cobertura de siniestros. La interfaz muestra ambos porcentajes y requiere cobertura histórica de siniestros para recomendar menor exposición. Se añadieron protocolos de evidencia para rutas y prensa; faltan casos humanos/externos y fechas de artefacto expuestas por backend.
- SES-023 añadió `/health`, dependencias declaradas, CI y guía operativa de migración/respaldo. No se ensayó PostgreSQL real porque el entorno local sigue sin intérprete Python funcional para el `venv` ni servicio de base confirmado.
- SES-024 reemplazó el reintento por recarga de página por reintentos independientes de corredores e inseguridad, conservando caché e indicando fuentes fallidas y última consulta. Los estados completos de reportes siguen pendientes de contrato backend.
- SES-025 corrigió el progreso GPS para medir sobre segmentos de ruta y no sólo vértices; las pruebas cubren avance intermedio continuo. Faltan trazas reales y perfilado de rendimiento.
- SES-031 amplió la ingesta de prensa: hechos `robo`, `inseguridad` y `choque` se clasifican por separado del atributo persistente `relacionado_moto`; la interfaz permite filtrar Motos sin ocultar el resto. Se añadieron dos RSS de búsqueda pública para ampliar el descubrimiento de medios locales. Falta ejecución real, conjunto humano etiquetado y deduplicación semántica.
- SES-032 conserva la fecha real de publicación de RSS y la usa en la vigencia, orden, ajustes de riesgo y antigüedad visible. Las fuentes sin fecha siguen usando la de ingesta. Falta extraer fecha de páginas/sitemaps y ejecutar contra PostgreSQL real.
- SES-033 elimina el sufijo editorial que Google Noticias agrega a sus titulares antes de comparar duplicados durante una corrida. Sigue pendiente deduplicación semántica validada con muestra humana.
- SES-034 imprime métricas de ingesta por fuente y el total asociado a motos para poder comparar aportes reales antes de sumar o retirar medios.
- SES-035 fija modo claro para nuevas instalaciones, corrige el popup de prensa que se cerraba por el tick del reloj y mejora el filtro de prensa con chips accesibles.
- SES-036 evita además el cierre por propagación del toque del mapa, extrae fecha editorial desde HTML/JSON-LD y amplía el descubrimiento agregado por zonas del GBA. Requiere corrida real para medir cuántas noticias nuevas aporta cada consulta.
- SES-037 refuerza la detención de eventos táctiles de los marcadores y agrega un actualizador por lotes para completar fechas editoriales de filas históricas.
- SES-038 corrige la causa real de cierre del popup: el array filtrado se regeneraba en cada tick. `iniciar.bat` abre Scraper como pestaña separada y lo ejecuta al levantar la app; requiere reparar Python para funcionar.
- SES-039 registró una corrida real que abortó por URL de agregador mayor a 500 caracteres. `url_fuente` se amplió a TEXT y las inserciones se aíslan por fila; hay que repetir la corrida y confirmar el resumen final.
- SES-040 confirmó la corrida completa: 560 candidatas, 289 ubicadas, 267 guardadas y 99 candidatas de motos. Las búsquedas agregadas aportaron 234 guardadas; se necesita revisión humana y deduplicación semántica antes de interpretar el volumen como incidencia.
- SES-041 muestra en el panel Prensa el total cargado y el visible según filtro. Las noticias de precisión barrial pueden seguir superpuestas hasta implementar agrupación visual.
- SES-042 agrupa las noticias cercanas con contador y permite abrir los puntos individuales al acercarse.
- SES-043 evita que las notas de una misma coordenada queden ocultas: el marcador de diario oscuro muestra su cantidad y abre una lista para elegir cada noticia. El color queda diferenciado de las zonas de riesgo.
- SES-044 prepara el MVP para no depender de la PC: Compose productivo separa web/API/PostGIS/scraper, aplica migraciones al arrancar y conserva secretos fuera de Git. Falta validar la composición con Docker/PostGIS, publicar HTTPS, programar el scraper en el proveedor y ensayar backup/restauración antes de llamarlo productivo.
- SES-045 agrega un Blueprint de Render para publicar rápido desde GitHub. Requiere que Rodo inicie sesión en Render, autorice el repositorio y cargue la clave privada de TomTom; la base gratuita propuesta es sólo de prueba y vence a los 30 días.
- SES-046 inició la reconstrucción de tesis: `docs/tesis/` contiene matriz de requisitos, declaración/registro de IA e índice propuesto hasta Capítulo 5. La entrega anterior se usa sólo para detectar contenido descartado; faltan fuentes primarias, supuestos económicos y evidencia final.
- SES-047 retiró los RSS de Google Noticias mediante DEC-011 porque su `robots.txt` restringe `/rss/`. La corrida directa del 2026-09-14 encontró 122 candidatas, ubicó 57 y guardó 4 filas nuevas; tuvo 20 candidatas relacionadas con moto. No es comparable con la corrida histórica de 560/289/267, que incluía 234 noticias del agregador. También se corrigió la estructura de tesis: Capítulo 3 pasa a ser Marco teórico y tecnológico, Capítulo 4 Arquitectura y diseño del sistema, y los capítulos 6, 7 y 8 permanecen separados.
- SES-048 resolvió la discrepancia de métricas: el pickle vigente es el modelo de 55 columnas actualizado el 2026-09-07, no el modelo previo de 66 columnas de Fase 4. Se reprodujo su split interno: F1 macro 0,3782; GRAVE precision/recall 0,1107/0,7346; MORTAL precision/recall 0,1159/0,4821. La evaluación temporal independiente sigue pendiente y no se debe afirmar desempeño futuro ni para GBA. Se creó el registro de actas de tutor vacío, sin inventar reuniones o aprobaciones.
- SES-049 entregó la primera versión de `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5.docx` (24 páginas). SES-050 la reescribió íntegramente contra los 11 PDF de clases de la cátedra: Capítulo 5 con supuestos económicos explícitos y VAN/TIR/recupero/sensibilidad, índice con páginas reales en dos pasadas, tres diagramas y corrección de la cifra de pruebas (80 frontend / 61 backend) contra el repositorio real (33 páginas). SES-051 hizo la revisión final: intentó de nuevo conseguir capturas reales (repositorio y proyecto de Claude, ambos sin imágenes de la aplicación) antes de reestructurar la sección de capturas pendientes; agregó una tabla única de supuestos y un escenario de sensibilidad combinado pesimista/base/optimista en el Capítulo 5; corrigió dos citas mal homologadas (WHO/W3C); y rediseñó los tres diagramas para distinguir implementado/preparado/pendiente. Resultado: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5_FINAL.docx` (35 páginas). Capturas reales, acta de tutor y evaluación temporal del modelo siguen pendientes; el commit y push del archivo quedan a cargo de Rodo porque `device_bash` sigue sin funcionar en este entorno.
- SES-052 preparó evidencia formal aún no aplicada: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` incorpora Resumen/Abstract preliminares, listas de figuras/tablas y Apéndice A de encuesta y prueba de tareas; el protocolo editable es `docs/tesis/03_INSTRUMENTOS_VALIDACION_USUARIOS.md`. G02 queda en curso: no hay participantes, encuestas, validación de usuarios ni capturas reales declaradas como hechas. La nueva versión requiere renderizado visual antes de reemplazar oficialmente al Word FINAL.
- SES-021 formalizó el contrato de gravedad condicionada y añadió un evaluador temporal que evita fuga de preprocesamiento, mide ablaciones, faltantes, calibración e incertidumbre. No modifica el modelo productivo. Se verificó su sintaxis con Python alternativo; no se generaron métricas nuevas porque el `venv` local depende de un intérprete base inexistente.

## Problemas que deben permanecer visibles

El modelo estima gravedad condicionada a un siniestro, no ocurrencia por viaje. 2025 fue utilizado en selección de configuraciones. Los faltantes de demografía tienen asociación muy fuerte con la clase y se utilizan de forma diferente al inferir perfiles de zonas. Las rutas todavía pueden premiar falta de cobertura. A07, A09, A10, A12, A15 y A16 solo tienen correcciones parciales, detalladas en BACKLOG. El notebook histórico sigue sin ejecutarse de punta a punta.

**Antes de hacer público el repositorio:** el hostname real de Tailscale Funnel quedó en el historial de Git (commit `d51fc30`, `tailscale/README.md`). Antes de cambiar la visibilidad, rotarlo en Tailscale (renombrar la máquina o el tailnet), porque el valor viejo sigue en el historial aunque el archivo actual tenga un placeholder.

Ver A01–A23 en el assessment. No dar por resuelto un hallazgo porque existan tests verdes que no prueban ese escenario.

## Cómo continuar

1. Consultar `git status` y estos registros antes de editar; puede haber trabajo local sin commit. El punto de transferencia conocido de Codex es `d2fb3ec`.
2. Elegir con el alcance autorizado un paquete de PRIORIZACION. La preferencia actual es entender y priorizar; no hacer todas las propuestas automáticamente.
3. Enlazar cada trabajo a un ID de BACKLOG. Usar los criterios de aceptación y VALIDACION.
4. Al terminar, actualizar backlog, bitácora, decisiones si corresponde y este resumen. Registrar también intentos fallidos o limitaciones materiales.
5. Preservar el assessment como evidencia histórica. No reentrenar, recargar tablas o ejecutar el notebook histórico solo para “poner al día” la documentación.

## Mensaje listo para compartir con Claude

> Continuamos MotoSafe GBA. Toda la documentación de continuidad está centralizada en `docs/README.md`. Leé primero `docs/gestion/CONTINUIDAD.md`, después `BACKLOG.md`, `PRIORIZACION.md`, `BITACORA.md` y `DECISIONES.md` de esa carpeta. Codex hizo una auditoría integral con evidencias en `docs/assessment_2026-09-11/` y elaboró 63 ítems entre problemas y mejoras. Rodo autorizó un primer bloque, registrado como SES-004; consultá el estado por ID porque solo algunos están validados o en curso. Persisten problemas metodológicos A01–A04 y de cobertura. Conservá los IDs y registrá cada cambio y prueba en el centro documental; no abras otro backlog. Verificá código y Git antes de asumir que el estado sigue igual.

## Material no disponible aquí

No se encontraron los capítulos formales completos de tesis, el reglamento, actas ni una bitácora anterior en `claude/`. Si se incorporan después, agregarlos al índice y contrastarlos; no inferir cumplimiento institucional de su ausencia local.

## Actualización 2026-09-15 — SES-058 (Codex): pruebas técnicas


Verificación actual: 80 tests frontend, 65 backend, lint y build aprobados. El venv backend funciona en esta sesión, a diferencia del límite histórico consignado arriba. npm no encontró el lanzador Vitest; su módulo directo pasó. Persisten advertencias de bundle grande y deprecación NumPy/joblib. Navegador bloqueado por certificado HTTPS local: T02 sigue sin E2E. La respuesta «acepto» en el chat no acredita aceptación dentro del navegador. [Pruebas y límites](../evidencias/2026-09-15/G02-T02/PRUEBAS.md). Sin commit/push de esta sesión; se preservó el trabajo concurrente de Claude.

## Actualización 2026-10-05 — SES-065 (Claude, vía Cowork)

Calibración de probabilidad evaluada sobre el holdout temporal real y descartada para decisión en producción, con evidencia (ECE baja de 0,30 a 0,01 pero recall GRAVE/MORTAL colapsa bajo argmax; el sistema no decide por argmax). Modelo productivo cambiado a la variante sin edad (53 columnas), reentrenado, umbrales de percentil recalibrados, huella SHA256 verificable en `/health`. Fix de borde visual para distinguir crítico ajustado por prensa de crítico de base (antes el frontend descartaba el campo que el backend ya calculaba). Detalle completo en BITACORA.md, SES-065. `UMBRAL_CRUCE_KM`/`PESO_RIESGO` (A06) sigue pendiente de rutas de referencia reales de Rodo. Sin commit de esta sesión (ver motivo en BITACORA).

## Actualización 2026-10-05 — SES-066 (Claude Code): A22 entorno reproducible

El modelo vigente se guardó con scikit-learn 1.7.2, pero se declaraba 1.5.2 y el venv local tenía 1.9.1. Se fijaron versiones exactas en `backend/requirements.txt`, que el `requirements.txt` raíz ahora incluye. Un test compara la versión del pickle con la declarada, `/health` expone `version_sklearn_coincide` y el reentrenamiento se niega con otra versión. Predicciones entre 1.7.2 y 1.9.1 sin cambios de nivel (330.288 filas). La instalación limpia y la imagen Docker aprobaron 80 tests. Guía: `docs/operacion/ENTORNO_REPRODUCIBLE.md`. Sin commit, a revisión de Rodo.

**Pendiente de decisión de Rodo:** `docker-compose.production.yml` y `render.yaml` no pasan las variables `AUTH_*`/`SESSION_SECRET`, que `auth.py` exige desde `d51fc30`. Esos despliegues no arrancan hasta decidir si el MVP publicado lleva login.

## Actualización 2026-10-05 — SES-067: login opcional y compose de producción

El MVP público corre sin login (`AUTH_HABILITADO=false` en compose y Render). Por defecto el login sigue activado, como el acceso por Funnel. El compose de producción se levantó de verdad: arranca sano y se corrigió la carrera de migraciones. **Pendiente de decisión de Rodo:** en producción las capas de datos dan 500 con base nueva porque nada carga `hotspots_riesgo` y las demás tablas (ver `docs/operacion/DESPLIEGUE_MVP.md`).

## Actualización 2026-10-06 — SES-068: lock, prototipos y primer E2E real

Dependencias transitivas fijadas con hashes (`backend/requirements.lock`, `requirements.lock`) e instaladas con `--require-hashes` en Docker, CI y el lanzador local. Prototipos de notebooks declarados. El primer E2E real, aislado de Funnel y de la base personal, pasó 23/23 verificaciones HTTP. Corrigió dos fallas: el mapa en blanco en el build de producción (worker de MapLibre) y `cargar_hotspots.py` sin crear su tabla. **Pendiente de Rodo:** confirmar la primera corrida del CI en GitHub (repo privado, sin `gh` ni sesión en el navegador integrado). **Pendiente técnico:** E2E visual de los flujos del mapa con la ventana en primer plano.

## Actualización 2026-10-06 — SES-069: A09 geocodificación de zonas

El scraper valida que el geocode caiga en la zona que nombra la nota y se abstiene si no es así. Sobre las 87 zonas del gazetteer, el método anterior ubicaba mal 11 y el nuevo ninguna (verificado por geocodificación inversa). La corrida real ubicó 79 de 132 candidatas, contra 78 antes. **Pendiente de decisión de Rodo:** si se re-geocodifican las filas históricas de `reportes_prensa`, porque implica escribir en su base.

## Actualización 2026-10-06 — SES-070: A12/T01 contra PostgreSQL real

Tests de integración contra un PostGIS desechable: migraciones concurrentes, límites y recuperación del pool, y ciclo de reportes. Pasan 7/7, con control negativo. A12 queda validado. El CI levanta PostGIS y los corre; falta confirmarlo en GitHub.

## Actualización 2026-10-06 — SES-071: T06 backup ensayado

Backup y restauración ensayados entre dos PostGIS desechables con el procedimiento documentado: copia idéntica y API funcionando sobre ella. Falta repetirlo con el volumen real y en el hosting.

## Actualización 2026-10-06 — SES-072: carga inicial en producción

Las capas se cargan solas al arrancar el contenedor si la base está vacía (CSV montados, no en la imagen). En Render hay un paso único documentado en `DESPLIEGUE_MVP.md`. Se corrigió además un bloqueo que dejaba `/hotspots` y `/corredores` en 504 mientras corría el scraper.

## Actualización 2026-10-06 — SES-073: prensa histórica re-geocodificada

Con backup previo en `C:\Users\rodol\motosafe_backups\`, 142 de las 450 notas cambiaron de ubicación; 94 estaban en otro partido o barrio (87 de La Matanza caían en Presidente Perón). Las filas precisas que estaban dentro de su zona no se tocaron.

## Actualización 2026-10-06 — SES-075: período de cobertura por capa

Las leyendas muestran el período real de los datos (siniestros 2019–2025, delitos 2023–2025) desde `/capas/cobertura`, con la fecha de generación del archivo en el tooltip. El JSON de metadatos se regenera con `notebooks/generar_metadatos_capas.py` cada vez que cambian las capas. Pendiente: la revisión visual de Rodo.

## Actualización 2026-10-06 — SES-076: CSV de capas versionados

Los 4 CSV derivados de las capas están en el repo y los crudos siguen afuera. Un clon limpio carga las capas solo; en Render sigue el paso único documentado.

## Actualización 2026-10-06 — SES-077: A19 pipeline canónico

El notebook histórico ya no puede pisar artefactos vigentes y publicar en `backend/` requiere `promover_artefactos.py --confirmar`. Orden del pipeline en `docs/modelo/PIPELINE_CANONICO.md`. Corrido desde cero en una copia, reproduce el mismo contenido y el mismo modelo. Falta un script para la limpieza inicial.

## Actualización 2026-10-06 — SES-078: D01 fichas de fuentes

`docs/datos/FICHAS_FUENTES.md` reúne licencia y política verificadas de cada fuente. **Pendiente de decisión de Rodo (A18):** el buscador autocompleta contra Nominatim y su política lo prohíbe; hay que elegir otro proveedor o buscar recién al confirmar.

## Actualización 2026-10-06 — SES-079: A18 resuelto (búsqueda solo al confirmar)

El buscador de direcciones ya no autocompleta contra Nominatim. Busca con Enter o con el botón de la barra, y origen/destino buscan con Enter; no hay pedidos mientras se escribe. Esto cierra el pendiente de decisión de A18 registrado en SES-078. Verificado con lint, 71 tests y build. Falta la revisión visual con `npm run dev` (la hace Rodo).

## Actualización 2026-10-06 — SES-080: scraper en contenedor y hallazgos de calidad

El scraper corre como servicio `scraper` del compose de producción, con tope por corrida (`SCRAPER_TIMEOUT_MINUTES`, 45 min) y operación documentada en `DESPLIEGUE_MVP.md` (`stop`/`start`/`logs`). No se rehizo desde cero porque ya existía.

**Calidad de los datos, pendiente de decisión de Rodo:**
- Las 204 notas de Google Noticias (retiradas por DEC-011) siguen en la base y se muestran hasta vencer a los 30 días. Opciones: (a) filtrar `fuente` que empieza con «Google» en la API, lo que oculta solo las vigentes y es reversible; (b) borrarlas, que es irreversible. Recomiendo (a).
- 29 notas tienen fecha anterior a 2025 y 13 no tienen fecha. Son fechas mal extraídas o ausentes. Recomiendo que la API las use por fecha de ingesta y no por la fecha de publicación cuando la publicada sea anterior a la ventana de 30 días.
- De las 450 notas, 426 están ubicadas solo a nivel barrio. Eso es esperable: mejorar la precisión depende de que el titular tenga una dirección.

**Actualización SES-080 (segunda parte):** la API ya no devuelve las notas de Google Noticias y usa la fecha de ingesta cuando la de publicación no es plausible. Las filas de la base no se tocaron. Si más adelante se decide limpiar la tabla, va con backup aparte.

## Actualización 2026-10-06 — SES-081: scraper programado en Windows

El scraper corre cada 3 horas con la tarea `MotoSafe-Scraper` del Programador de tareas, que ejecuta `scraper_programado.bat` contra la misma base que usa el backend nativo (`motosafe-db`, mismo proyecto y servicio que el compose de producción). Los logs quedan en `logs\scraper`, uno por corrida, y la cifra de «nuevas guardadas» de cada una sirve para decidir la cadencia. Docker Desktop arranca con el inicio de sesión; el `.bat` espera a que responda antes de correr.

No se usa `up -d scraper` del compose de producción hasta reconciliar `schema_migrations` con la base real. Ese entrypoint corre `migrar.py` sobre la base en vivo.

**Actualización SES-082:** la corrida programada ahora informa cuántas notas ya estaban en la base, y limpia `corrida_*.log` de más de 60 días antes de cada ejecución. Rodo decide la cadencia de 180 minutos con 3 o 4 corridas completas que incluyan el contador nuevo.

**Actualización SES-083:** en celular, la atribución del mapa se colapsa al botón «i» y el «Salir» pasó al menú de herramientas. El build nuevo está publicado en el Funnel. Pendiente: revisar el solapamiento de «Salir» durante la navegación y la pasada general de UX.

**Actualización SES-084:** pasada de UX sobre la búsqueda de ruta, la leyenda, la atribución y el modal de bienvenida. Pendientes: ítems 2, 5 y 7 de la auditoría (bundle, lupa y «Cerrar sesión» en viaje real). **Infraestructura:** la URL pública del Funnel depende de que el preview del 5175 siga vivo a mano; no es un servicio persistente.

**Actualización SES-085:** la URL pública se vigila sola cada 5 minutos con la tarea `MotoSafe-Vigilancia` (`tailscale\vigilancia.ps1`). Reinicia base, backend, preview y Funnel si fallan, y deja log en `logs\vigilancia`. `tailscale\estado.bat` muestra el estado sin reiniciar nada. Probado: preview, Funnel, base y backend. Falta confirmar un reinicio completo de la PC. El pendiente de infraestructura del preview queda resuelto por la vigilancia.

**Actualización SES-086:** cerrados los ítems 2 (code splitting: bundle principal de 269 kB), 5 (lupa visible) y 7 (viaje real probado en celular). Corregida la atribución que volvía a abrirse durante la navegación. Pendiente de revisar con Rodo: mejoras de diseño (leyenda, pista de la elección de origen, separación de «Reportar») y el chequeo en escritorio durante un viaje.

**Actualización SES-087:** corregidos a partir de capturas reales: «Reportar» tapaba «Nueva ruta», el paso de navegación quedaba trabado cuando el GPS se saltaba una maniobra, la leyenda tapaba la zona abierta y los toasts cubrían la búsqueda. Pendiente: confirmar en un viaje real la distancia de la maniobra y la posición de los toasts; decidir sobre el tiempo estimado y el tamaño de la leyenda.

**Actualización SES-088:** la barra de búsqueda ya no tapa los botones de arriba (la altura de la barra superior se medía mal). La búsqueda centra el mapa en el lugar elegido y lo deja como destino. Decisión pendiente: si la búsqueda debe abrir «Trazar ruta» directamente, como antes.

**Actualización SES-089:** auditoría completa en BITACORA. Cerrados: ETA absurdo, recientes en la búsqueda, etiqueta del buscador y áreas táctiles. Pendientes con decisión de Rodo: si la búsqueda abre «Trazar ruta», voz y compartir llegada, propuesta visual de leyenda e íconos, y el proveedor de búsqueda (A18).

**Actualización SES-090:** sugerencias de búsqueda mientras se escribe, vía TomTom desde el backend (`/lugares`). Sin contador de segundos en la barra. Contraste del texto secundario corregido. Pendientes: distancia de maniobra por ruta, vista previa de la ruta, fichas de lugares, datos de reportes y modo sin conexión. Revisar cupo y términos de TomTom para búsqueda.

**Actualización SES-100:** TN vuelve a aportar (corrección de redirección en robots.txt) y el tope por fuente sube a 60. Clarín sigue en cero: falta identificar el sitemap de notas. Pendientes: nuevos medios verificados y fuentes no periodísticas.

**Resumen de sesiones SES-091 a SES-101 (detalle en BITACORA):**
- **SES-091/092:** zoom de iOS al tocar campos (16 px) y animación de paneles centrados (`translate` en vez de `transform`). Pendiente confirmar en iPhone.
- **SES-093:** búsqueda con tarjeta «Ir» explícito; favoritos geocodificados con `/lugares` (sin Nominatim).
- **SES-094:** distancia a la maniobra medida por la ruta; vencimiento visible en reportes.
- **SES-095 a SES-099:** rediseño de la pantalla de viaje (barra única, flecha como marcador en 2D y 3D, bloque «Luego», hoja de reporte cerrable, columna de botones a la derecha). Pendiente confirmar en celular.
- **SES-100/101:** scraper: TN recuperado (redirección en robots.txt), tope de 60 notas por fuente, sitemaps de noticias primero (Clarín), cinco medios locales verificados (Un/Medio, Diario Anticipos, Qué Pasa Web, Informe Norte, El Sol). En seco: 172 candidatas y 81 ubicadas.

**Próximo foco:** mejorar la extracción de ubicación de las notas ya recopiladas (qué notas quedan sin ubicar y por qué). Pendientes abiertos: confirmar el viaje y el zoom de iOS en celular; fuentes no periodísticas sin verificar; TomTom (cupo y términos antes de uso comercial).

## Actualización 2026-10-13 — SES-102 a SES-113: viaje, limpieza visual inicial, búsqueda de lugares y triage de cierre del backlog

**Resumen (detalle completo en BITACORA):**
- **SES-102:** el modo viaje no se apagaba al llegar a destino. Tres correcciones sucesivas sobre pruebas reales de Rodo hasta encontrar la causa de fondo: la tarjeta mide distancia restante sobre la ruta, no en línea recta, y el efecto de llegada comparaba contra una medición distinta a la que el usuario ve en pantalla.
- **SES-104/105:** arranca la limpieza visual a partir del login (Rodo: sensación de "poco pulido, trucho", sin poder decir por qué). Medidos 11 valores de border-radius, 20+ sombras y 12 tamaños de letra sueltos pese a que ya existía una escala de tokens sin aplicar. Atribución del mapa y "Reportar" pasan a la escala.
- **SES-106 a SES-110:** la búsqueda de lugares "no encuentra" tenía cinco causas reales encadenadas, cada una encontrada y corregida con evidencia (no conjetura): radio de búsqueda corto (60 a 150 km), sesgo de búsqueda fijo en el centro de CABA en vez de la ubicación real del usuario, la app nunca pedía esa ubicación al abrirse, el respaldo en Nominatim no recibía el centro real (viewbox del país entero), y la comparación de relevancia usaba substring exacto en vez de similitud de texto. Verificado en cada paso con la ubicación real de Rodo en Pilar.
- **SES-111/112:** triage explícito de cierre del backlog existente (Rodo: "cerrar lo abierto", "sumar complejidad" no). Cerrados o avanzados con evidencia real: A07 y V08 (validados), A09 (localidades del GBA sin ubicar), A17 (perfilado real del mapa, sin memory leak), A19 (script canónico limpiar_siniestros_motos.py, verificado byte a byte contra el CSV vigente), A23 (matriz de accesibilidad completa, encontró y corrigió un foco fantasma real en el modal de bienvenida y un aviso de red faltante en tráfico), A14 (retirada la compatibilidad transitoria de reportes, con migración 003_reportes_prensa.sql nueva, verificada contra PostgreSQL real aparte de la base personal de Rodo).
- **SES-113:** Rodo decidió sobre lo pendiente del triage: A01/A02 pasan a Validado (criterio del proyecto, no a la espera de una revisión académica externa separada); A10 validado con revisión visual real. F08 (estados propios de reportes: vigente/vencido/retirado, vía la misma credencial privada que ya autoriza borrar) y A11 (distancia real de cada zona cruzada al trazado de la ruta, no solo "cruza sí/no") implementados como función nueva, confirmados por Rodo.

## Actualización 2026-10-11/13 — SES-114: rediseño fuerte del frontend en 6 fases

Pedido explícito de Rodo ("diseño, disposición, accesibilidad, pantallas", no un retoque), planificado en 6 fases revisables con aprobación entre cada una. Resultado de punta a punta: escala de espaciado nueva (--sp-1 a --sp-8, no existía ninguna), tipografía base de 12px a 14px, superficie flotante unificada (--surface-float, antes 6+ valores de opacidad sin motivo), 6 variantes de texto con contraste WCAG calculado (no a ojo) para los colores de riesgo e inseguridad. Accesibilidad real, no declarativa: un fallo de contraste confirmado y corregido (--text-dimmer), ~20 sitios de color-como-texto auditados contra su fondo real, 7 touch targets corregidos con medición en el navegador, 3 variables CSS fantasma (nunca definidas, siempre caían al valor de respaldo) reemplazadas por tokens reales, el foco fantasma del onboarding reconfirmado sin regresión tras las 5 fases de cambios de markup. Detalle fase por fase en BITACORA.

## Actualización 2026-10-13 — SES-115: ronda 2 de rediseño, portal de Actividad y hexágonos de cobertura como visión central (sesión en curso)

- **Features nuevas:** tocar un punto vacío del mapa marca destino directo (estilo Maps/Waze); portal de "Actividad" a pantalla completa (prensa + reportes comunitarios combinados, filtrable por categoría/fecha/barrio real vía reverse geocoding de TomTom con caché agresiva); lector interno de noticias (panel flotante de alto regulable arrastrando, abre desde el portal y desde los marcadores de prensa del mapa, con "Abrir en pestaña nueva" como salida honesta para los sitios que bloquean iframes).
- **Nueva vista de fondo — hexágonos de cobertura:** grilla hexagonal armada a mano (sin sumar librería, mismo criterio de dependencias del proyecto), con radio que se ajusta en escalones según el zoom (inspirado en cómo H3/Uber cambian de resolución), opacidad del relleno que escala con la densidad real de la celda, y popup con desglose por nivel al tocar un hexágono. Pasó a ser la vista de fondo por defecto (antes clusters), con la elección de quien ya usaba otra vista preservada en localStorage.
- **Filtro Todo/Siniestros/Inseguridad dentro de la vista de hexágonos:** arma la grilla con el modelo de siniestros, los delitos históricos del GCBA (misma fuente que ya usa la capa de puntos aparte, pedida siempre sin depender de que esa capa esté prendida) o ambas combinadas, con el nivel más alto de cualquiera de las dos por celda y un desglose explícito de cuánto es de cada fuente en el popup. Decisión explícita, acordada con Rodo antes de implementar: vistas filtrables y trazables en vez de un único "score" inventado que mezcle predicción de modelo, histórico de delitos y una noticia puntual con pesos arbitrarios. Las celdas con noticias de prensa recientes encima lo muestran en el popup, sin crear un hexágono nuevo solo por una noticia si no hay datos de riesgo reales ahí.
- **Rediseño de los 4 tipos de popup del mapa** (corredores, inseguridad, reportes comunitarios, hexágonos): chips de estadísticas en vez de oraciones largas con separadores, metadato secundario con un estilo único en vez de que cada uno reinventara el suyo, reportes comunitarios reordenados (qué pasó primero, quién/cuándo después). Bug real encontrado y corregido: el popup de inseguridad mostraba "Comuna 10.0" porque comuna_moda llega del backend como string con decimal, no número.
- **Corrección a partir de feedback real de celular** (capturas de Rodo sobre la tanda anterior): sacada la paleta violeta/magenta que tenía el filtro de inseguridad, en la práctica costaba más leerla que el semáforo verde/amarillo/naranja/rojo que ya usa el resto del mapa, así que los tres filtros quedaron con la misma paleta; sacada la capa ambiente de puntos blancos de "hay noticias acá" (confundía sin ningún lugar en pantalla que lo explicara; el dato sigue disponible en el popup); chips de filtro corregidos para no quedar cortados sin aviso en celular angosto (pasan a envolver en dos filas en vez de un scroll horizontal oculto).
- **Diseño:** bordes redondeados de los paneles grandes (leyenda, panel de capas, portal de Actividad/estadísticas, formulario de ruta, resumen de zona/ruta, hoja de reportar, tarjeta de lugar) unificados a --r-lg (16px), era la diferencia real, medida en el CSS, que hacía sentir al lector de notas "más pulido" que el resto de la app (que tenía 10/12/14px sueltos repetidos a mano en cada panel). Alcance acordado con Rodo antes de tocar código: paneles grandes nomás, los popups chicos del mapa y los botones/chips quedan con su escala propia a propósito.
- **Pendiente explicado, no bloqueante:** en el filtro de hexágonos, "Todo" y "Delitos" se ven parecidos en la mayoría de las zonas porque el dataset de delitos del GCBA es más denso que el de siniestros ahí; no es un bug de color, es la data real, el popup ya desglosa cuánto es de cada fuente.
- Verificado en cada tanda de esta sesión (detalle puntual en BITACORA): eslint, vitest frontend (81 al empezar la sesión, 93 al cierre de esta entrada, con tests nuevos para cada pieza de lógica agregada en hexBin.js), build, y pytest backend (120 passed, 11 skipped, sin cambios de backend en esta sesión más allá del repaso de regresión inicial). Probado en el navegador en los dos temas y con un viewport de celular real (375×812) para los hallazgos de feedback.

## Actualización 2026-10-18 — SES-116: cierre de A04, corrección de números Cap4/Cap7, intérprete de `run_dev.py`, estabilidad por año (D02) y confianza por zona (A24)

- **A04 cerrado**: el modelo en producción desde el 05/10 (sin edad, con sexo e índice) no es el que describían el Capítulo 4 (Tabla 4.1) ni el borrador del Capítulo 7 — los dos citaban la variante vieja (con edad). Números honestos corregidos: F1 macro 0,368 (split) vs. 0,3045 (evaluación temporal 2024, real); GRAVE 0,604/0,098 y 0,562/0,081; MORTAL 0,464/0,105 y 0,535/0,074. Sensibilidad del corte de percentil medida (p25 a p95): el corte vigente (p75/p95) queda justificado porque es donde MORTAL empieza a perder recall real. Evidencia en `docs/evidencias/2026-10-18/A04-decision-costo-por-clase/`.
- **Corrección de capítulos**: Capítulo 4 (ya entregado) no se reescribió — se agregaron notas de actualización fechadas (2026-10-05 y 2026-10-18) después de los pasajes afectados, dejando intacto lo evaluado. El Capítulo 7, al no estar entregado todavía, se corrigió directo (Tabla 7.1, precisión/recall, ablaciones, calibración, más dos párrafos nuevos sobre calibración isotónica y sensibilidad del corte). **Nota de esta revisión (20/10): el borrador de Capítulo 7 que describe esta entrada no se encontró como archivo en el repositorio ni en el historial de Git al auditar la carpeta `docs/tesis/` — solo existe el consolidado de Capítulos 1 a 6. Queda pendiente confirmar con Rodo/Codex dónde vive ese borrador antes de dar por buena esta entrada.**
- **A22 (run_dev.py)**: el reloader de desarrollo podía correr el proceso hijo con el Python de sistema en vez de `venv312`, sin aviso. Fijado con `multiprocessing.set_executable` + verificación explícita del intérprete. 4 tests nuevos, 124/124 en verde.
- **D02 (estabilidad del modelo)**: comparados dos splits temporales independientes (2023→2024 y 2024→2025); los intervalos de confianza bootstrap NO se superponen (F1 macro 0,2859 vs. 0,3689) — el modelo no generaliza igual de un año a otro. Limitación real documentada, no resuelta. D02 pasa a "Validado parcialmente".
- **A24 (confianza por zona)**: 10 Random Forest sobre remuestras bootstrap del dataset completo para medir cuánto cambia el nivel de riesgo de cada zona al reentrenar. Acuerdo global 84,9%; por zona, mediana 83,8%, mínimo 52,6%; los niveles "crítico" y "alto" son los menos estables (78-79% vs. 85-90% de "bajo"/"medio"). `/hotspots` ahora expone `confianza_estabilidad` por zona. 2 tests nuevos, suite completa 126/126.
- D03/D04 (rutas de referencia contra OSRM) siguen sin avanzar: el host de OSRM está bloqueado tanto desde el entorno de este Claude como desde el contenedor en la nube.

## Actualización 2026-10-18/19 — SES-117/118: auditoría visual en vertical de celular (3 bugs reales corregidos)

Pedido de Rodo: pulir diseño/animación sin tocar lógica, arrancando por la vista vertical de celular ("salta mucho"). SES-117: la atribución de MapLibre arrancaba abierta en cada carga porque la corrección vivía dentro de `map.on('load')`, que dispara tarde — movida a justo después de crear el mapa, ya no hay flash. SES-118: recorrida la app completa a 390×844 con medición real (`getBoundingClientRect`), tres bugs encontrados y corregidos: la topbar transparente dejaba ver marcadores por detrás (degradé con stop sólido agregado), la leyenda se tapaba con Estadísticas/Actividad/Capas (reglas `:has()` para ocultarla cuando corresponde), y las dos leyendas (riesgo + inseguridad) se superponían entre sí con un offset fijo mal calculado (reestructuradas en un `.legend-stack` que se apila sola). `npx vitest run` 93/93 en verde en ambas sesiones.

## Actualización 2026-10-19 — SES-119: auditoría exhaustiva de design tokens, a pedido explícito de Rodo ("muy exigente")

Resueltos todos los valores sueltos de `border-radius` y `font-size` que el propio código ya marcaba como pendientes (15 + 10 ocurrencias, mapeadas a los tokens `--r-*`/`--fs-*` existentes), más el clúster de "números grandes" en modo navegación (velocidad, tiempo, distancia) que usaba tres tamaños distintos para el mismo rol — unificados contra `--fs-xl`/`--fs-2xl`. En la continuación de la misma sesión: `.navegacion-panel` tenía un borde hardcodeado que quedaba invisible (blanco sobre blanco) en tema claro — corregido a `var(--border)`; `.nav-resumen-mini` era el único borde de acento con ancho no entero (1.5px); `.report-sheet` tenía padding fijo distinto al resto de paneles flotantes de su misma familia. Verificado con `getComputedStyle` en los dos temas, no a ojo. `npx vitest run` 93/93 en ambas partes.

## Actualización 2026-10-19 — SES-120: por qué "a veces se ve todo grande" (topbar de alto variable)

La topbar en celular metía iconos + clima + pill de estado en una sola fila con `flex-wrap`, y el pill de estado muestra textos de largo muy distinto ("3 zonas" vs. "Ruta: 1.8 km · 5 min") — eso hacía que el alto de la topbar cambiara según el momento, lo que se percibía como "a veces se ve todo grande". Corregido separando iconos (fila fija arriba) del pill de estado (fila fija abajo) en celular. De paso, el buscador bajó de 62px a 54px de alto para no desentonar con sus pills hermanos de la topbar. Barrido de overlaps sobre todos los elementos flotantes: ninguno real. `npx vitest run` 93/93.

## Actualización 2026-10-20 — SES-121/122/123: rediseño del apartado de prensa/noticias y barrida general de consistencia visual

A pedido explícito de Rodo sobre el apartado de noticias ("los logos, los pop up, que siento que no van con el resto de la estética"):
- Chip de filtro activo con amarillo fuera de marca, unificado a `var(--amarillo)`.
- Insignias de prensa en el mapa con colores fijos que no reaccionaban al tema, pasadas a `var(--surface-solid)`/`var(--text)`.
- **Hallazgo grande**: el popup de MapLibre (todos los popups del mapa, no solo prensa) perdía sus overrides de fondo/radio/padding contra el CSS propio de la librería por orden de carga en el bundle. Corregido con `!important` en las propiedades en disputa, igual que ya se había hecho antes para la atribución — estos dos selectores habían quedado afuera esa vez.
- Botones "Leer nota"/voto con `var(--surface)`, una variable CSS nunca definida en `:root` (resuelve a `transparent`) — corregidos a `var(--inset)`.
- SES-122, segunda vuelta sobre el mismo apartado: la caja con borde grueso de los marcadores de prensa no comunicaba ningún dato (a diferencia del borde de `cluster-bubble`, donde el color sí es el nivel de riesgo) — pasada a cápsula con borde fino + sombra, y el carácter de fuente `▤` reemplazado por el ícono real `Newspaper` de lucide-react.
- SES-123, barrida general: grep de caracteres Unicode fuera de ASCII en todo el JSX encontró 6 casos; 2 eran el mismo bug (glyph de fuente haciendo de ícono) en el popup de hexágonos y en el aviso "Nivel subido" — reemplazados por SVG real; los otros 4 (✓/✕/→/−) son caracteres tipográficos estándar sin problema, se dejaron.
- `npx vitest run` 93/93 en las tres sesiones. Todos los cambios son CSS/JSX puro, sin tocar lógica de datos ni de negocio.

## Actualización 2026-10-20 — Infraestructura: Tailscale Funnel caído, vigilancia sin correr desde el 11/10

Al intentar acceder a la URL pública desde el celular, se confirmó (con conexión real al navegador del escritorio, no solo leyendo archivos de estado) que el Funnel no responde en ninguno de sus dos endpoints. Causa identificada: la tarea programada `MotoSafe-Vigilancia` no corrió ni una vez entre el 12/10 y el 20/10 (el último log es del 11/10 23:21, todo OK); en el medio la PC se reinició al menos una vez, lo que probablemente tumbó Docker Desktop y/o la tarea programada sin que nada la reiniciara sola. Se le indicó a Rodo el procedimiento de recuperación (abrir Docker Desktop, esperar que esté estable, correr `tailscale\reiniciar_app.bat`, confirmar con `tailscale\estado.bat`) y re-registrar la vigilancia con `registrar_vigilancia.ps1` para que esto no vuelva a pasar en silencio. **Pendiente de confirmación de Rodo que quedó resuelto.**
