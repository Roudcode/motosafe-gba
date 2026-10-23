# V04 — colores más semánticos, menos acentos simultáneos (2026-10-22, SES-161)

Criterio de cierre: "Riesgo, selección y acción diferenciados por texto/forma además de color." V11 (ya
validado) midió y corrigió contraste real de la paleta de riesgo contra el mapa -- **no se tocó esa paleta
acá**, a propósito, como pidió Rodo explícitamente. Lo que pide V04 es otra cosa: que el significado de un
color no dependa solo del color.

## Dónde se buscó (los tres lugares que pidió Rodo, no otros)

### 1. Leyenda (`LegendStack.jsx`)

Cada nivel de riesgo (siniestros e inseguridad) ya se muestra como `<span class="legend-swatch">` (el color)
**+ `val.label` (texto: "Bajo"/"Medio"/"Alto"/"Crítico") + un contador numérico** en la misma fila. El color
nunca es la única señal -- el texto ya está ahí. Revisado el código real: así fue desde que existe el
componente, no es un hallazgo nuevo.

### 2. Tarjetas de ruta (`RutaResumenPanel.jsx`)

- El estado "seleccionada" de una tarjeta (`.ruta-opcion.activa`) no es solo un cambio de color: cambia
  borde (azul) **+ fondo tintado + sombra con elevación** (`box-shadow`), el mismo lenguaje de profundidad
  que ya usa el resto de la UI flotante -- hay una señal de forma (elevación) además del color.
- La línea de exposición de cada ruta (`<span class="ruta-opcion-riesgo nivel-X">`) siempre trae **texto
  explícito** ("exposición bajo/medio/alto/crítico entre alternativas", "cobertura registrada insuficiente",
  "sin zonas registradas cerca") -- nunca solo un color. La palabra del nivel ("bajo" vs. "crítico") ya es,
  por sí misma, una señal no-color.
- Los badges (`rápida`, `menor exposición`, `equilibrada`, `rápida y menor exposición`) ya combinan ícono
  propio (`Zap`, `ShieldCheck`, `Scale`) + texto + color -- nunca solo color, y cada badge usa un ícono
  distinto del de los demás.

### 3. Controles de capas (`CapasPanel.jsx`)

Cada opción (`.capas-opcion`) ya trae un **radio que cambia de forma** (círculo vacío → círculo relleno,
`.capas-opcion.activa .capas-opcion-radio { background: var(--azul) }`), un ícono propio por opción
(`op.Icon`), un rótulo y una descripción corta -- cuatro señales no-color antes de llegar al color del
borde. El estado activo no depende del color para leerse.

## Conclusión real: no se encontró un caso real de ambigüedad en los tres lugares pedidos

Revisando los tres a fondo, **todos ya combinan color con texto y/o ícono y/o forma** -- no hay ningún lugar
donde nivel de riesgo, selección de ruta o un control activo dependan solo del color para distinguirse entre
sí. Además, los colores de riesgo (verde/amarillo/naranja/rojo) y el color de selección/acción (azul) ni
siquiera comparten tono -- no hay superposición de hue entre "esto es riesgoso" y "esto está
seleccionado/activo", que es justamente el tipo de confusión que el criterio de cierre busca evitar.

Por instrucción explícita de Rodo ("no inventes casos hipotéticos"), no se forzó ningún cambio de código.
Esto se documenta como el resultado real de la revisión, no como un ítem sin trabajar: se citó cada caso
revisado, con el código real que lo respalda, en vez de asumir que faltaba algo.

## Verificación

No aplica un verificación de tests/lint/build porque no se modificó ningún archivo de código para este
ítem -- la "verificación" es la cita directa del código fuente de arriba, revisado línea por línea en
`LegendStack.jsx`, `RutaResumenPanel.jsx`, `CapasPanel.jsx` y las reglas CSS correspondientes de `App.css`.

## Qué no se tocó

La paleta de colores de riesgo (V11, ya cerrado). Ningún componente nuevo.

## Actualización 2026-10-22 (SES-163)

Con sesión real disponible, se confirmó en pantalla (claro y oscuro) que la leyenda, las tarjetas de ruta y
el panel de capas siguen leyéndose igual que lo revisado en código -- sin cambios de este ítem, nada que
reverificar puntualmente más allá de la revisión visual general de la sesión (ver REPASO_FINAL.md).
