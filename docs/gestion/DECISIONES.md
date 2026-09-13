# Registro de decisiones

Separar decisiones tomadas de recomendaciones. Una propuesta de Codex/Claude no equivale a aprobación de Rodo.

| ID | Fecha | Estado | Decisión y origen | Consecuencia |
| DEC-010 | 2026-09-13 | Vigente | Rodo autorizó ampliar la ingesta de prensa y pidió que motos sea un filtro, no la única categoría. | El tipo de hecho y `relacionado_moto` se guardan por separado. Fuentes sociales sólo se incorporan por API oficial, feed permitido o exportación autorizada. |
| DEC-009 | 2026-09-13 | Vigente | Rodo autorizó el bloque de riesgo. La cobertura para recomendar «menor exposición» se define sobre registros históricos de siniestros; la inseguridad se informa por separado. | Una fuente no completa artificialmente a la otra. Menos de 60% o fuente ausente impide la recomendación; el umbral queda sujeto a validación D03/D04. |
| DEC-008 | 2026-09-13 | Vigente | Para A01–A04, el score se define como gravedad condicional a un siniestro observado. Rodo autorizó completar el bloque académico; la definición se formalizó sin cambiar el uso productivo. | No se comunica como probabilidad de ocurrencia, seguridad de una ruta ni riesgo individual. La cobertura espacial se evalúa por separado. |
|---|---|---|---|---|
| DEC-001 | 2026-09-11 | Adoptada | Rodo solicita centralizar documentación, auditoría y futuros cambios para retomar con Claude. | `docs/README.md` es la entrada; `docs/gestion/` contiene continuidad, backlog, bitácora, decisiones y validación. |
| DEC-002 | 2026-09-11 | Adoptada, implementación documental | Preservar el assessment fechado y registrar evolución fuera de esa fotografía. | Correcciones en BACKLOG/BITACORA; nueva evidencia en carpetas fechadas. |
| DEC-003 | 2026-09-11 | Adoptada, implementación documental | Una única lista operativa con IDs estables; propuestas separadas de trabajo aprobado. | Backlog antiguo de README queda histórico, enlazado al nuevo. |
| DEC-004 | 2026-09-11 | Pendiente de selección | Consolidar integridad y metodología antes de ampliar prestaciones costosas. Recomendación del assessment. | Elegir paquetes de PRIORIZACION; no iniciar implementación general por esta fila. |
| DEC-005 | 2026-09-11 | Pendiente | Dirección visual propuesta: mapa protagonista, amarillo reservado a acciones, menos decoración, paneles por modo. | Validar con estados representativos y Rodo antes de un rediseño general. |
| DEC-006 | 2026-09-11 | Pendiente | Alcance de defensa centrado en CABA, distinguiendo ruteo GBA de cobertura de datos. | Alinear título, objetivos, interfaz y evaluación según decisión académica. |
| DEC-007 | 2026-09-13 | Adoptada | Rodo autorizó avanzar y corroborar el funcionamiento. Se inicia por integridad de reportes, contenido externo, entradas, actualización y recuperación, sin declarar cerrado el catálogo completo. | Se implementan y prueban cambios incrementales; los asuntos metodológicos A01–A04 siguen abiertos. |

## Plantilla

### DEC-XXX — Título

- Fecha / estado / autor de la decisión:
- Problema e IDs relacionados:
- Opciones consideradas:
- Decisión y motivo:
- Evidencia o instrucción de Rodo que la respalda:
- Efectos, límites y costo de mantenimiento:
- Qué queda pendiente y cuándo revisarla:

Si se revierte una decisión, conservar el registro y agregar una nueva que la sustituya.
