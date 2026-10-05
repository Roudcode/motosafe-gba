# Continuidad del proyecto — leer primero

**Actualizado:** 2026-10-05. **Responsable de producto:** Rodo. **Estado:** implementación incremental del bloque inicial y verificación; el catálogo completo sigue sin estar cerrado.

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
