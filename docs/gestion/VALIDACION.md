# Protocolo de validación y entrega

Actualizado: 2026-09-13. **Este archivo define pruebas futuras; no afirma que ya se ejecutaron.**

## Registro por cambio

Guardar fecha, ID, commit/base, entorno, entradas, resultado esperado, observado y evidencia en `docs/evidencias/AAAA-MM-DD/ID/`. Usar datos sintéticos cuando haya ubicación/identidad personal. Una captura ilustra un estado; no demuestra por sí sola comportamiento funcional.

| Tipo de cambio | Comprobación mínima pertinente |
|---|---|
| Documentación | Referencias válidas, IDs consistentes, estados fieles y diff sin cambios accidentales. |
| API | Caso válido, límite/error afectado y regresión relevante; DB real aislada si cambia SQL/transacciones. |
| Reportes/identidad | Autor autorizado y tercero, UUID público, migración, error de red y consistencia UI-servidor. |
| Riesgo/rutas | Vacío, cobertura parcial, empate, capas fallidas, lluvia y cambio de hora; trazabilidad de fuentes. |
| UI | Estado antes/después, móvil y escritorio, teclado, foco, zoom, temas y contenido largo. |
| GPS | Traza de detención, giro entre fixes, pérdida de señal, desvío y llegada; distinguir simulación de prueba de campo. |
| ML/datos | Split/fechas/hashes, baseline, métricas por clase, incertidumbre, faltantes y evaluación independiente. |
| Operación | Arranque limpio, fallo de upstream/base, límites y recuperación; no usar datos productivos para pruebas destructivas. |

## Matriz visual propuesta

- Viewports: 360×800, 390×844, 844×390 y 1366×768; agregar dispositivo real representativo.
- Temas: claro y oscuro; fondos de mapa habituales.
- Estados: carga, error, sin datos, mapa denso, capas abiertas, resultados de búsqueda, teclado, tres rutas, reporte, navegación y pérdida de señal.
- Comprobar: acciones visibles, paneles sin superposición impeditiva, lectura del giro/ETA, foco visible, ampliación de texto y movimiento reducido.
- No solicitar ni cambiar permisos de GPS del usuario sin el alcance correspondiente; usar escenarios controlados y registrar la limitación.

## Condición para dar un ítem por validado

1. Cumple el criterio de BACKLOG y el alcance elegido.
2. Pasan los checks pertinentes; cualquier límite pendiente está explícito.
3. No se confunden mocks con servicios reales ni reconstrucción del split con evaluación independiente.
4. Se actualizaron BITACORA, CONTINUIDAD y guías afectadas; DECISIONES cuando hubo una elección nueva.
5. Se registró el commit o que aún no existe. No marcar publicado/desplegado por haber compilado.

Las pruebas históricas del 11/09 están en el assessment. No reutilizar su estado verde como evidencia automática para cambios posteriores.
