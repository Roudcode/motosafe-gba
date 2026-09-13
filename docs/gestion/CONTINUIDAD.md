# Continuidad del proyecto — leer primero

**Actualizado:** 2026-09-13. **Responsable de producto:** Rodo. **Estado:** implementación incremental del bloque inicial y verificación; el catálogo completo sigue sin estar cerrado.

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
- SES-021 formalizó el contrato de gravedad condicionada y añadió un evaluador temporal que evita fuga de preprocesamiento, mide ablaciones, faltantes, calibración e incertidumbre. No modifica el modelo productivo. Se verificó su sintaxis con Python alternativo; no se generaron métricas nuevas porque el `venv` local depende de un intérprete base inexistente.

## Problemas que deben permanecer visibles

El modelo estima gravedad condicionada a un siniestro, no ocurrencia por viaje. 2025 fue utilizado en selección de configuraciones. Los faltantes de demografía tienen asociación muy fuerte con la clase y se utilizan de forma diferente al inferir perfiles de zonas. Las rutas todavía pueden premiar falta de cobertura. A07, A09, A10, A12, A15 y A16 solo tienen correcciones parciales, detalladas en BACKLOG. El notebook histórico sigue sin ejecutarse de punta a punta.

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
