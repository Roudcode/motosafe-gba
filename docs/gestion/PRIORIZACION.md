# Orden de avance propuesto

Actualizado: 2026-09-13. **Recomendación, no autorización para ejecutar todos los ítems.** El alcance y los estados viven en BACKLOG; esta página agrupa trabajo, no es otra lista de tareas.

## Primer bloque recomendado: una base confiable y visible

Objetivo: que la app no muestre éxito falso, no permita borrado ajeno y explique fallos claramente.

- **A08:** títulos de prensa seguros como texto.
- **A13:** entradas válidas y respuesta estable con base vacía.
- **A15 + V10:** primera carga, errores y reintento; comprobar HTTP antes de confirmar acciones.
- **A07:** separar identidad pública de autorización privada. Definir migración de reportes existentes antes de cambiar el contrato.

Orden interno: A08/A13 → A15/V10 → A07 con su contrato y migración revisados. A07 es prioritario para exposición pública; el orden no habilita publicar mientras esté abierto. Es un bloque transversal acotado, sin reentrenar ni cambiar toda la estética.

**Salida revisable:** casos antes/después, pruebas de regresión, pantalla de error útil y documentación por ID. Se puede dividir A07 en una entrega propia si su migración amplía el alcance.

## Segundo bloque: que el riesgo mostrado signifique lo que dice

A01/A05/A06/A10/A11 y V06/V07: cobertura explícita, etiquetas relativas honestas, actualización y un solo contrato de ajustes. A09 debe resolverse antes de presentar prensa como modificador confiable; hasta medirla, considerar mantenerla informativa como opción de diseño a decidir.

**Salida:** una ruta con cobertura parcial no se presenta como segura; base, ajuste, fecha y fuentes distinguibles. Este bloque mejora tanto funcionamiento como claridad visual.

## Tercer bloque: experiencia móvil y navegación

Validar visualmente la app primero. Luego A16/A17/A23, V01–V05/V08–V14 y F04/F05/F08. Probar primero una dirección visual en tres estados: explorar, comparar y navegar. Mantener colores de marca y capacidades útiles existentes.

**Salida:** comparación visual antes/después, teclado y orientación sin controles tapados, GPS detenido sin velocidad vieja, marcadores estables. Las propuestas visuales todavía no están validadas por capturas.

## Cuarto bloque: evidencia científica y reproducción

A02–A04/A19–A22, D01–D04, T01/T05/T06 y G01/G03/G04. Es la línea decisiva para la defensa. Si la fecha de presentación es cercana, esta línea debe adelantarse al pulido visual amplio; no hay una fecha límite informada para decidir ese ajuste.

**Salida:** evaluación reproducible, límites explícitos y documentación consistente con un artefacto identificado. No asegurar mejoras de métricas hasta realizar los experimentos.

## Evolución opcional

F01–F03/F06/F07/F09/F10, D05/D06 y resto de instrumentación según evidencia de uso. Voz, favoritos ampliados y caché pueden ser útiles, pero no corrigen automáticamente la validez del riesgo ni la cobertura.

## Cómo elegir sin hacer todo

| Si el objetivo inmediato es… | Elegir |
|---|---|
| Demo estable | Primer bloque, segundo bloque y QA móvil básica. |
| Defensa próxima | Primer bloque crítico + semántica del segundo + cuarto bloque antes de rediseño amplio. |
| Prueba con motociclistas | Primer/segundo bloque + navegación y accesibilidad + G02. |
| Publicación | Además: base, cuotas, recuperación, seguridad y operación validadas; no basta con hosting. |

No propongo una puntuación numérica artificial ni sumar esfuerzos como días. Al seleccionar un bloque, estimar tras revisar sus dependencias reales. Cerrar uno con evidencia antes de abrir múltiples frentes de implementación.
