# V02 — unificar tamaños, espaciado, radios y sombras (2026-10-22, SES-162)

Criterio de cierre: "Tokens comunes y componentes coherentes en ambos temas." Dependencia explícita:
inventario de estilos real, para evitar un rediseño arbitrario.

## Inventario real (grep sobre `App.css`, no asumido)

Revisados todos los paneles flotantes principales (`.ruta-form`, `.ruta-resumen`, `.capas-panel`,
`.detalle-panel`, `.legend`): **ya usan, de forma consistente, los mismos tokens** --
`border-radius: var(--r-lg)`, `background: var(--surface-float)`, `border: 1px solid var(--border)`,
`box-shadow: var(--shadow-float)`, `backdrop-filter: blur(var(--surface-float-blur))`. No hay
inconsistencia real entre ellos. Los radios de 50% (avatares, dots, FABs circulares) son una familia
distinta a propósito (forma circular, no rectángulo redondeado) -- no es lo mismo que `--r-*`, no
correspondía unificarlos.

Las sombras de color (`box-shadow: 0 ... rgba(color,...)`) tampoco son inconsistencia: son un segundo nivel
deliberado, reservado para la acción principal de cada contexto (verde = iniciar viaje, amarillo = reportar,
azul = ruta seleccionada), distinto del `--shadow-float` neutro que usan los paneles. Confirmado revisando
cada uso: ninguno está fuera de ese patrón.

## Hallazgo real: dos colores repetidos sin token

`#FF3B3B` (3 lugares: `.capa-inseguridad-toggle.activa` ×2 propiedades, `.legend-inseguridad`) es,
literalmente, el mismo valor que ya existe como `--rojo` -- estaba escrito a mano en vez de referenciar la
variable. `#F2793B` (3 lugares: `.capa-toggle:hover`, `.capa-toggle.capas-con-cambios` ×2) es un naranja
**real y deliberadamente distinto** de `--naranja` (`#FF8C42`, el de nivel "alto" de la paleta de riesgo) --
usarlo en el botón de capas evita sugerir que el panel de capas está marcando un riesgo alto, pero no tenía
ninguna variable propia que lo documentara como intencional.

## Qué se cambió

- `#FF3B3B` → `var(--rojo)` en los 3 lugares (mismo valor exacto, cero cambio visual).
- Nuevo token `--naranja-capas: #F2793B` en `:root` (no se duplica en el bloque de tema claro porque `--rojo`
  tampoco se redefine ahí -- ambos colores de datos/acento quedan iguales en los dos temas, mismo criterio
  que ya declara el comentario existente sobre `--naranja`/`--rojo`/`--azul`). Reemplazados los 3 usos de
  `#F2793B` por `var(--naranja-capas)`, con un comentario explicando por qué es distinto de `--naranja` a
  propósito (para que la próxima sesión no lo "corrija" fusionándolo).

## Qué no se tocó

No se tocó ningún valor de `--sp-N` (espaciado) ni `--r-*` (radios) -- ya estaban unificados. No se
fusionaron `#14171A` y `#0B1620` (dos negros casi idénticos usados como texto sobre fondos de color
brillante, en lugares distintos): son dos colores preexistentes con origen distinto (`--bg`/`--inset` uno,
el contorno oscuro de V11 el otro) y fusionarlos sería un cambio de diseño, no una limpieza de token -- la
diferencia visual entre ambos es imperceptible, así que no hay beneficio real que justifique tocarlo sin que
Rodo lo pida.

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- es sustitución de valor CSS idéntico, no hay comportamiento que
  testear).
- `vite build`: compila sin errores.
- No se verificó en pantalla real (sin credencial de acceso a la app) -- pero al ser una sustitución de
  valores idénticos (`var(--rojo)` resuelve exactamente a `#FF3B3B`, `var(--naranja-capas)` a `#F2793B`), no
  hay render distinto que verificar: el riesgo de regresión visual es nulo por construcción.

## Actualización 2026-10-22 (SES-163) — decisión real sobre `#14171A`/`#0B1620`

Pedido explícito de Rodo, con el criterio delegado: "si no hay razón funcional real, unificalos; si la hay,
documentalo en el propio CSS". Revisados los 17 usos reales de ambos colores en `App.css` (texto sobre
fondos de acento): el patrón resultó **100% consistente, sin ninguna excepción** -- `#0B1620` (con un dejo
azulado) solo aparece sobre fondos fríos (`--verde`, `--azul`); `#14171A` (más neutro) solo sobre fondos
cálidos (`--amarillo`, `--naranja-capas`, `--rojo`). No es un accidente de sesiones distintas trabajando el
mismo día -- es una decisión real de armonía de color, repetida sin falla en cada botón de acción de la
app. **Decisión: no se fusionan.** Se documentó la razón directamente en `:root` de `App.css`, junto a los
demás tokens de color, para que ninguna sesión futura los "limpie" sin saber que es intencional.
