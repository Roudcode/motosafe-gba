# MotoSafe GBA — Centro de documentación

**Entrada única para Rodo, Claude y Codex. Actualizado: 2026-09-13.**

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
| [Guía detallada](1_Guia_DETALLADA.md) / [resumen](1_Guia_RESUMEN.md) | Explicación general; contiene información histórica desactualizada. Pendiente sincronizar con versión validada. |
| [Manual detallado](2_Manual_DETALLADO.md) / [resumen](2_Manual_RESUMEN.md) | Operación; no ejecutar Run All del notebook para recuperar errores sin resolver A19. |
| [Resultados detallados](3_Resultados_DETALLADO.md) / [resumen](3_Resultados_RESUMEN.md) | Resultados de versiones anteriores; no adjudicarlos automáticamente al modelo vigente. |
| [Extensión de inseguridad](9_Extension_Futura_Inseguridad.md) | Documento histórico; parte de su alcance ya está implementado. |
| DOCX homónimos de guías/manuales/resultados | Copias existentes; aún no regeneradas ni sincronizadas. Markdown será el texto editable de referencia para futuras actualizaciones. |
| [README raíz](../README.md) | Instalación e historia anterior. Su backlog antiguo se conserva como histórico; el operativo es BACKLOG.md. |

## Convención para todos los cambios futuros

- **Una tarea, un ID:** mantener A01–A23 para los hallazgos; V/F/D/T/G para mejoras adicionales. No crear una lista operativa paralela.
- **No confundir propuesta con aprobación ni con implementación.** La prioridad del backlog es recomendada hasta que Rodo decida el alcance.
- Cada cambio registra motivo, ID, archivos, pruebas, resultado, pendientes y commit si existe. Sin commit se indica explícitamente.
- Una decisión nueva entra en DECISIONES; una sesión/cambio en BITACORA; el resumen vigente en CONTINUIDAD.
- Evidencia nueva: `docs/evidencias/AAAA-MM-DD/ID/`. No sobrescribir la evidencia histórica ni guardar claves, ubicaciones personales o datos de usuarios reales.
- Las guías y resultados se actualizan cuando cambia el comportamiento que describen. Registrar si queda pendiente regenerar Word/PDF.
- No inventar sesiones, actas, aprobación del usuario, métricas o pruebas no realizadas. Conservar discrepancias y límites.

Centralizar significa mantener este índice y estos registros como punto de entrada. Los datos y el código conservan sus ubicaciones de ejecución; no se duplican dentro de documentación.
