# MotoSafe GBA — Centro de documentación

**Entrada única para Rodo, Claude y Codex. Actualizado: 2026-10-21.**

## Para retomar el proyecto

1. Leer [CONTINUIDAD.md](gestion/CONTINUIDAD.md): estado comprobado, instrucciones y resumen para pasar a Claude.
2. Consultar [BACKLOG.md](gestion/BACKLOG.md): catálogo único de correcciones y oportunidades, con IDs, esfuerzo, dependencias y aceptación.
3. Leer [PRIORIZACION.md](gestion/PRIORIZACION.md): paquetes recomendados y decisiones pendientes.
4. Revisar [BITACORA.md](gestion/BITACORA.md) y [DECISIONES.md](gestion/DECISIONES.md): qué se hizo y qué se decidió realmente.
5. Usar [VALIDACION.md](gestion/VALIDACION.md) para registrar evidencia antes de cerrar cambios.

## Evidencia y documentación existente

| Documento | Función y estado |
|---|---|
| [Assessment integral 2026-09-11](assessment_2026-09-11/ASSESSMENT.md) | Diagnóstico histórico con 23 hallazgos. No actualizarlo como si fuera el estado futuro; registrar correcciones en backlog y bitácora. |
| [Evidencias](assessment_2026-09-11/evidencias.json), [inventario](assessment_2026-09-11/inventario.csv), [script](assessment_2026-09-11/auditar.py) | Resultados y mecanismo de reproducción de aquella revisión. |
| [Contrato y evaluación del modelo](modelo/CONTRATO_Y_EVALUACION.md) | Definición defendible del score, protocolo temporal y límites de faltantes/calibración. |
| [Ficha de siniestros con moto](datos/FICHA_SINIESTROS_MOTO.md) | Unidad de análisis, fuentes locales, transformaciones y límites de los datos. |
| [Cobertura y procedencia de capas](riesgo/PROCEDENCIA_Y_COBERTURA.md) | Fuentes, cobertura por trazado, TTL y protocolo de validación de rutas y prensa. |
| [Ingesta de prensa multifluente](riesgo/INGESTA_PRENSA_MULTIFUENTE.md) | Fuentes, clasificación de motos, límites de calidad y proceso para ampliar cobertura. |
| [Operación de backend y base](operacion/BACKEND_Y_BASE_DE_DATOS.md) | Migraciones, salud, CI, backup y límites de la validación con PostgreSQL. |
| [Entorno reproducible](operacion/ENTORNO_REPRODUCIBLE.md) | Versiones exactas, versión de scikit-learn del modelo, instalación limpia y hashes de artefactos. |
| [Despliegue del MVP](operacion/DESPLIEGUE_MVP.md) | Arquitectura cloud, contenedores, secretos, operación y criterios para declarar un despliegue productivo. |
| [QA de accesibilidad y visual](calidad/QA_ACCESIBILIDAD_VISUAL.md) | Matriz reproducible para teclado, zoom, temas, móvil, movimiento y red. |
| [Matriz académica y demo](entrega/MATRIZ_ACADEMICA_Y_DEMO.md) | Objetivos, evidencia, límites y guion reproducible de presentación. |
| [Actas y seguimiento con tutor](gestion/ACTAS_TUTOR.md) | Registro central de reuniones verificables; actualmente sin actas cargadas. |
| [Guía detallada](1_Guia_DETALLADA.md) / [resumen](1_Guia_RESUMEN.md) | Actualizada 2026-10-13: Fases 1-13 son la historia original (sin reescribir), Fases 14-17 agregan login, búsqueda con TomTom, portal de Actividad y hexágonos de cobertura. DOCX homónimos todavía sin regenerar. |
| [Manual detallado](2_Manual_DETALLADO.md) / [resumen](2_Manual_RESUMEN.md) | Actualizado 2026-10-13 contra los scripts reales (`iniciar.bat`, login, migraciones automáticas, `venv312`). No ejecutar Run All del notebook para recuperar errores sin resolver A19. |
| [Resultados detallados](3_Resultados_DETALLADO.md) / [resumen](3_Resultados_RESUMEN.md) | Resultados de versiones anteriores; no adjudicarlos automáticamente al modelo vigente. Sin cambios en esta ronda: el modelo no se tocó en SES-114/115. |
| [Extensión de inseguridad](9_Extension_Futura_Inseguridad.md) | Documento histórico de investigación, conservado sin reescribir; nota agregada 2026-10-13 al tope indicando que esta extensión ya está implementada y dónde. |
| DOCX homónimos de guías/manuales/resultados | Copias existentes; aún no regeneradas ni sincronizadas. Markdown será el texto editable de referencia para futuras actualizaciones. |
| [README raíz](../README.md) | Instalación e historia anterior. Su backlog antiguo se conserva como histórico; el operativo es BACKLOG.md. |

## Convención para todos los cambios futuros

- **Una tarea, un ID:** mantener A01–A24 para los hallazgos; V/F/D/T/G para mejoras adicionales. No crear una lista operativa paralela.
- **No confundir propuesta con aprobación ni con implementación.** La prioridad del backlog es recomendada hasta que Rodo decida el alcance.
- Cada cambio registra motivo, ID, archivos, pruebas, resultado, pendientes y commit si existe. Sin commit se indica explícitamente.
- Una decisión nueva entra en DECISIONES; una sesión/cambio en BITACORA; el resumen vigente en CONTINUIDAD.
- Evidencia nueva: `docs/evidencias/AAAA-MM-DD/ID/`. No sobrescribir la evidencia histórica ni guardar claves, ubicaciones personales o datos de usuarios reales.
- Las guías y resultados se actualizan cuando cambia el comportamiento que describen. Registrar si queda pendiente regenerar Word/PDF.
- No inventar sesiones, actas, aprobación del usuario, métricas o pruebas no realizadas. Conservar discrepancias y límites.

Centralizar significa mantener este índice y estos registros como punto de entrada. Los datos y el código conservan sus ubicaciones de ejecución; no se duplican dentro de documentación.

## Pruebas técnicas — 2026-10-21

- Estado actual (G01, corrido de nuevo al cerrar esta sesión, no copiado de una entrada anterior): **96 tests frontend** (`node node_modules/vitest/vitest.mjs run`) y **140 backend aprobados (11 skipped**, de integración con PostgreSQL real no levantada en esta verificación), lint y build sin errores. Detalle de cada tanda que llevó de 93/120 a 96/140 en SES-148 (teclado del buscador) y SES-150 (`consumir_metricas.py`) en [BITACORA.md](gestion/BITACORA.md).
- E2E real contra el stack levantado (PostgreSQL/PostGIS, backend, frontend, navegador integrado) corrido varias veces esta misma semana: confirmación visual del buscador por teclado (SES-149), T01 contra un PostGIS descartable con un rol de permisos mínimos (SES-149), T06 contra la composición real de producción con volumen persistente (SES-151), A05 con rutas reales en pantalla (SES-152). No hay todavía E2E en un dispositivo físico real ni con throttling de red/CPU (ver T03 en BACKLOG.md).

## Pruebas técnicas — 2026-10-13

- Estado de esa fecha: 93 tests frontend (`node node_modules/vitest/vitest.mjs run`) y 120 backend aprobados (11 skipped, de integración con PostgreSQL real no levantada en esa verificación), lint y build sin errores. Verificado en el navegador en los dos temas (claro/oscuro) y en un viewport de celular real (375×812). Detalle de cada tanda de SES-114/SES-115 en [BITACORA.md](gestion/BITACORA.md). Conservado como registro histórico de esa fecha; ver la entrada de arriba para el estado vigente.
- No hubo E2E contra PostgreSQL real ni dispositivo físico en esa verificación puntual; sí hubo pasadas anteriores con PostGIS descartable (ver SES-070, SES-112, SES-113 en BITACORA) y con el navegador integrado de Claude Code actuando sobre la app real corriendo en local.

## Pruebas técnicas — 2026-09-15

- [Pruebas actuales y límites](evidencias/2026-09-15/G02-T02/PRUEBAS.md): 80 tests frontend y 65 backend aprobados; navegador bloqueado por certificado. Conservado como registro histórico de esa fecha; ver la entrada de arriba para el estado vigente.

## Auditoría vigente de cierre (22/10/2026)

[Assessment integral nuevo](assessment_2026-10-22/ASSESSMENT.md): revisión de HEAD 1c4b8ef más cambios locales de Claude, 11 P1 y 7 P2, con reproducciones SQL/API y cobertura. No sustituye el assessment histórico de septiembre. Frontend 108/108; backend con PostGIS aislado 157 aprobadas y 3 fallidas. Leer antes de asumir que los ítems validados históricamente siguen cerrados.
