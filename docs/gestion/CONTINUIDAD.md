# Continuidad del proyecto — leer primero

**Actualizado:** 2026-09-13. **Responsable de producto:** Rodo. **Estado:** implementación incremental del bloque inicial y verificación; el catálogo completo sigue sin estar cerrado.

## Pedido actual de Rodo

Centralizar auditoría, documentación, decisiones y cambios para poder retomar con Claude. Luego Rodo autorizó avanzar y corroborar que funcione; se inició un bloque de integridad, consistencia y recuperación.

## Qué se hizo

**Corrección de continuidad del 13/09:** el registro del 11/09 anticipaba un backlog y dos documentos que aún no se habían escrito. Se completaron BACKLOG, PRIORIZACION y VALIDACION el 13/09. El estado descrito abajo corresponde ahora a los archivos existentes, no a una implementación de las mejoras.

1. Auditoría integral sobre commit `c24b8a7` y datos locales; informe y evidencias en `docs/assessment_2026-09-11/`.
2. Se creó el centro documental `docs/README.md` y la gestión compartida en esta carpeta.
3. Se amplió el catálogo a **63 ítems: 23 hallazgos y 40 oportunidades adicionales**. Hay dependencias y solapamientos explícitos; no representan 63 proyectos independientes.
4. Se prepararon paquetes de prioridad y protocolo de validación.
5. SES-004 implementó un primer bloque: token privado para borrar reportes, sanitización de prensa, validación de entradas, pool acotado, respuesta vacía de hotspots, correcciones de riesgo/ranking y recuperación de carga. No se modificaron el modelo ni los datasets.

## Estado técnico comprobado en la auditoría

- React + Vite + MapLibre; FastAPI + psycopg2/PostgreSQL/PostGIS. Documentos anteriores aún dicen Leaflet.
- Modelo guardado: Random Forest, 300 árboles, profundidad 12, mínimo cinco muestras por hoja, balanced_subsample, 55 columnas.
- 23.343 hechos de moto limpios; 23.338 filas para modelado; 740 hotspots viales; 243 corredores; inseguridad 633 general + 502 con moto.
- Datos históricos de CABA. Ruteo y prensa en GBA no equivalen a cobertura predictiva validada del conurbano.
- Última verificación local (SES-004): backend 55 pruebas aprobadas; frontend 73 con `node node_modules/vitest/vitest.mjs run`; lint y build aprobados. `npm test` sigue sin poder invocar Vitest por el binario local. Build advierte un bundle JavaScript de 1,29 MB antes de gzip. No hubo E2E contra PostgreSQL, servicios de ruteo ni navegador.
- Métricas reconstruidas del pickle en el split declarado: macro-F1 0,378; GRAVE precision 0,111/recall 0,735; MORTAL precision 0,116/recall 0,482. **No son una nueva prueba independiente.**
- Navegador rechazó certificado HTTPS local. No hay certificación visual de esta revisión ni E2E con PostgreSQL/TomTom reales.

## Problemas que deben permanecer visibles

El modelo estima gravedad condicionada a un siniestro, no ocurrencia por viaje. 2025 fue utilizado en selección de configuraciones. Los faltantes de demografía tienen asociación muy fuerte con la clase y se utilizan de forma diferente al inferir perfiles de zonas. Las rutas todavía pueden premiar falta de cobertura. A07, A09, A10, A12, A15 y A16 solo tienen correcciones parciales, detalladas en BACKLOG. El notebook histórico sigue sin ejecutarse de punta a punta.

Ver A01–A23 en el assessment. No dar por resuelto un hallazgo porque existan tests verdes que no prueban ese escenario.

## Cómo continuar

1. Consultar `git status` y estos registros antes de editar; puede haber trabajo local sin commit.
2. Elegir con el alcance autorizado un paquete de PRIORIZACION. La preferencia actual es entender y priorizar; no hacer todas las propuestas automáticamente.
3. Enlazar cada trabajo a un ID de BACKLOG. Usar los criterios de aceptación y VALIDACION.
4. Al terminar, actualizar backlog, bitácora, decisiones si corresponde y este resumen. Registrar también intentos fallidos o limitaciones materiales.
5. Preservar el assessment como evidencia histórica. No reentrenar, recargar tablas o ejecutar el notebook histórico solo para “poner al día” la documentación.

## Mensaje listo para compartir con Claude

> Continuamos MotoSafe GBA. Toda la documentación de continuidad está centralizada en `docs/README.md`. Leé primero `docs/gestion/CONTINUIDAD.md`, después `BACKLOG.md`, `PRIORIZACION.md`, `BITACORA.md` y `DECISIONES.md` de esa carpeta. Codex hizo una auditoría integral con evidencias en `docs/assessment_2026-09-11/` y elaboró 63 ítems entre problemas y mejoras. Rodo autorizó un primer bloque, registrado como SES-004; consultá el estado por ID porque solo algunos están validados o en curso. Persisten problemas metodológicos A01–A04 y de cobertura. Conservá los IDs y registrá cada cambio y prueba en el centro documental; no abras otro backlog. Verificá código y Git antes de asumir que el estado sigue igual.

## Material no disponible aquí

No se encontraron los capítulos formales completos de tesis, el reglamento, actas ni una bitácora anterior en `claude/`. Si se incorporan después, agregarlos al índice y contrastarlos; no inferir cumplimiento institucional de su ausencia local.
