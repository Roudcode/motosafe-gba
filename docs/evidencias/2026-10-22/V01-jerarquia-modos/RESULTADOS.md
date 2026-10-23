# V01 — jerarquía por modo: explorar, comparar, navegar (2026-10-22, SES-161)

Primera tarea del catálogo V que Rodo habilitó explícitamente para esta sesión (venía fuera de alcance en
V09/V10/V11/D06). Criterio de cierre: "En cada modo hay una acción principal y mapa visible; cambiar modo
conserva contexto."

## Qué había antes (revisado en el código real, no asumido)

No existe un estado `modo` explícito en `App.jsx`. El comportamiento real se arma con una combinación de
booleanos/longitudes ya existentes:

- `modoViaje` / `vistaNavegacion`: viaje en curso (con o sin cámara de navegación bloqueada).
- `rutasCalculadas.length > 0 && !modoViaje` (ya tenía nombre: `mostrandoOpcionesRuta`): alternativas de
  ruta calculadas, panel de comparación abierto.
- Ni lo anterior ni lo otro: exploración del mapa (incluye el formulario de ruta abierto, `rutaAbierta`,
  mientras se componen origen/destino).

**Hallazgo 1 (positivo, confirmado antes de tocar nada)**: estos tres estados ya son mutuamente excluyentes
por construcción -- `RutaForm` se cierra (`setRutaAbierta(false)`) en cuanto se calculan rutas con éxito;
`mostrandoOpcionesRuta` se apaga solo si `modoViaje` arranca; la leyenda (`LegendStack`) y el FAB de
reportar ya se ocultan mientras `mostrandoOpcionesRuta`/`panelRuta.montado` está activo (comentario propio
en el código: "no compiten por el mismo rincón de la pantalla"). El mapa (`mapa-wrapper`) se renderiza
siempre, sin condición -- ningún panel existente ocupa el 100% de la pantalla (se revisó el CSS de
`.ruta-form`, `.ruta-resumen` y `.detalle-panel`: todos son tarjetas flotantes con `max-height` acotado,
nunca `100vh`). "Mapa visible en los tres modos" ya se cumplía.

**Hallazgo 2 (real, el que motivó el cambio)**: el buscador (`SearchBar`, estado `busquedaAbierta`) es el
único panel flotante que **no** se cierra al entrar a modo "comparar"/edición de ruta. Su desplegable de
sugerencias solo se oculta con `!vistaNavegacion && abierto` -- nada lo apaga cuando se abre `RutaForm`
(`abrirPanelRuta()` cerraba actividad/stats/capas, pero no el buscador). Si alguien dejaba el buscador
abierto y después tocaba el botón de ruta, los dos paneles (`.ruta-form`, ambos anclados cerca de
`top: var(--y1)`) quedaban compitiendo por el mismo rincón superior de la pantalla -- el caso concreto de
"paneles acumulados" que el ítem pedía encontrar, no uno inventado.

## Qué se cambió

1. **`modoActual` explícito** (`App.jsx`): `modoViaje ? 'navegar' : mostrandoOpcionesRuta ? 'comparar' :
   'explorar'`. No cambia ningún comportamiento -- es la misma combinación de booleanos que ya regía todo,
   ahora con un nombre. Expuesto como `data-modo` en el `<div className="app">` raíz, para que cualquier
   regla CSS o test futuro pueda engancharse al modo sin repetir la combinación de estados en cada lugar.
2. **Corregido el hallazgo real**: `abrirPanelRuta()` ahora también llama `setBusquedaAbierta(false)`, en la
   misma línea que ya cerraba actividad/stats/capas. Una sola línea, mismo patrón ya existente.

## Qué no se tocó

Ningún flujo de navegación/viaje (V09 ya dejó ese trabajo fino hecho, según pidió Rodo explícitamente no
pisarlo). Ningún componente nuevo ni librería nueva. No se introdujo ningún sistema de tokens: `data-modo`
es un atributo plano, sin ninguna regla CSS nueva que dependa de él todavía (queda disponible para quien lo
necesite después, p. ej. V05).

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos específicos -- es un cambio estructural/CSS mínimo sobre lógica ya
  cubierta por los tests existentes de `riesgoRuta.js`/`CapaErrorBanners`, que no se tocaron).
- `vite build`: compila sin errores.
- **No se verificó en pantalla real**: la app exige sesión logueada (`AUTH_USERNAME`/`AUTH_PASSWORD_HASH` en
  `backend/.env`) y no se cuenta con la contraseña real -- por diseño, `generar_password.py` no la deja
  guardada en ningún archivo legible desde acá. Mismo tipo de limitación ya documentada en DEC-026 y en
  otras entradas del backlog sin acceso al stack logueado (ej. A17).

## Qué queda para una próxima sesión (si Rodo decide seguir)

`data-modo` queda como gancho disponible pero sin uso todavía -- si en el futuro se quiere dar una
identidad visual más fuerte a cada modo (por ejemplo, un color de acento de fondo sutil por modo), ya hay
dónde engancharlo sin otra refactorización. No se hizo ahora porque no era parte del criterio de cierre
("acción principal + mapa visible + conserva contexto" ya estaba cumplido) y hubiera sido agregar
decoración sin una necesidad real identificada -- justo lo que el criterio general de la sesión pide evitar.

## Actualización 2026-10-22 (SES-163) — confirmado real, con login real por primera vez

Con sesión real iniciada, se confirmó en el navegador real (no solo en código) los tres modos:

- **Explorar**: `document.querySelector('.app').getAttribute('data-modo')` → `"explorar"` al cargar la app.
- **Comparar**: trazada una ruta real (Paraguay 1854 → Avenida Maipú 1300, Vicente López, mismo caso real
  de D03/DEC-026) → `data-modo` pasó a `"comparar"` automáticamente, 3 alternativas reales calculadas.
- **Navegar**: tocado "Iniciar viaje" real → `data-modo` pasó a `"navegar"`, tarjeta de maniobra visible,
  mapa atenuado (V09), leyenda oculta, "Salir" disponible -- sin clutter, confirmado con una captura real.

**El hallazgo corregido (buscador compitiendo con `RutaForm`) también se confirmó real**: abierto el
buscador, tocado el botón de ruta -- `aria-expanded` del buscador pasó de `"true"` a `"false"` solo, sin
ninguna acción manual, y `RutaForm` se abrió limpio, sin superposición.

No se encontró ningún caso adicional de paneles acumulados al repasar los tres modos con el stack real. No
hizo falta ningún cambio de código más allá del ya hecho en SES-161.
