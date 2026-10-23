# V05 — panel inferior móvil con alturas controladas (2026-10-22, SES-162)

Criterio de cierre: "A 360/390 px, teclado abierto y paisaje no tapa controles esenciales." Depende de V01
(ya cerrado en SES-161).

## Qué había antes (revisado en `App.css` real, no asumido)

La app ya tiene un tratamiento de mobile/landscape bastante maduro, más de lo que anticipaba el ítem:

- Un `@media` de ancho angosto con `max-height` propio en casi todos los paneles flotantes
  (`.ruta-resumen`, `.detalle-panel`, `.actividad-panel`, `.stats-panel`), reducción de padding, y ocultado
  cruzado de la leyenda cuando cualquiera de esos paneles está abierto (`.app:has(.detalle-panel)
  .legend-stack { display: none }` y equivalentes) para que no compitan por el mismo rincón -- comentarios
  reales en el código citan capturas concretas de Rodo que motivaron cada ajuste (SES-087, SES-117).
- Un `@media (orientation: landscape) and (max-height: 500px)` **dedicado**, pensado explícitamente para
  "un celular apaisado en un soporte de moto" (según su propio comentario) -- topbar más baja, paneles con
  `max-height: calc(100vh - 70px)`.
- "Iniciar viaje" en el panel de rutas vive fuera del área que scrollea (`ruta-resumen-scroll`), fijo abajo
  del panel, así que nunca queda oculto por contenido largo -- ya resuelto de antes.

**Conclusión real**: el ancho (360/390px) y el paisaje ya están cubiertos con una solución medida y
documentada, no genérica. Lo único que el criterio de cierre nombra y que no tiene ningún tratamiento
visible en el código es **"teclado abierto"**.

## Lo que se evaluó para "teclado abierto" y por qué no se tocó

`RutaForm` (`.ruta-form`, origen/destino/favoritos) es el único panel flotante sin `max-height` propio --
todos los demás (`.capas-panel`, `.ruta-resumen`, `.detalle-panel`) sí lo tienen. En teoría, con el teclado
virtual abierto (el viewport visible se achica bastante en un celular), un formulario con varios campos +
una lista de sugerencias abierta podría superar el alto visible.

Se intentó un ajuste directo (mismo patrón que `.capas-panel`: `max-height` + `overflow-y: auto` sobre
`.ruta-form`), pero se revirtió antes de dejarlo: `.ruta-form-sugerencias` (el desplegable de sugerencias
de dirección) es `position: absolute` dentro de un ancestro `position: relative` que vive DENTRO de
`.ruta-form` -- agregarle `overflow-y: auto` al formulario convierte a `.ruta-form` en un contenedor de
scroll, y el desplegable (que hoy se superpone libremente por fuera del formulario cuando hace falta)
pasaría a recortarse en el borde del formulario en vez de superponerse. Sin poder probarlo en un navegador
real con teclado virtual, aplicar ese cambio a ciegas corría el riesgo de cambiar un problema hipotético
("el formulario no tiene tope de alto") por uno real y peor (el desplegable de sugerencias, que sí se usa
todo el tiempo, quedaría cortado). Se prefirió no tocar nada antes que romper algo que funciona hoy sin
poder verificarlo.

## Qué no se tocó

Ningún archivo de código para este ítem -- se revirtió el único intento. No se tocó nada del tratamiento
mobile/landscape existente, que ya cumple la mayor parte del criterio de cierre.

## Verificación

- `eslint src/` / `vitest run` (108/108) / `vite build`: verificados sin cambios pendientes, ya que no quedó
  ningún cambio de código de este ítem.
- No se verificó en pantalla real con teclado virtual abierto (sin acceso al stack logueado desde acá) --
  es, de los siete ítems de esta sesión, el que más necesita esa verificación real y menos se pudo avanzar
  sin ella.

## Actualización 2026-10-22 (SES-163) — confirmado real y corregido de fondo

Con login real disponible (ver nota de acceso al final de la bitácora de esta sesión), se reprodujo el
problema con una emulación real de teclado virtual en el navegador: viewport angosto (390px) con la altura
reducida a 400px (simulando el espacio que deja un teclado real en un celular). **Confirmado con una medida
real** (`getBoundingClientRect` sobre el desplegable de sugerencias real, con datos reales): el desplegable
llegaba a `bottom: 494` en un viewport de 400px de alto, y `document.body.scrollHeight` no era mayor que
`window.innerHeight` -- es decir, no había ningún scroll disponible para alcanzar la parte cortada. Era un
bug real, no hipotético.

**Corregido de fondo, no descartado**: en vez de agregarle scroll a `.ruta-form` (el intento anterior, que
sí recortaba el desplegable), se implementó el patrón correcto para este caso -- un "flip" de apertura,
igual al que usa cualquier select/popover nativo. Nuevo hook `useAbrirArriba` en `RutaForm.jsx`: después de
montarse, cada desplegable de sugerencias mide con `getBoundingClientRect()` si le entra hacia abajo contra
`window.visualViewport.height` (que sí refleja el achique real del teclado en los navegadores que lo
soportan); si no entra, se le agrega la clase `arriba` (`top: auto; bottom: calc(100% + 4px)` en `App.css`)
y se abre hacia arriba del campo en su lugar. Recalcula en cada apertura y con los eventos de
`resize`/`visualViewport.resize` (cubre el momento real en que aparece/desaparece el teclado).

**Verificado real, antes y después**:
- Antes del fix: desplegable con `bottom: 494` en un viewport de 400px -- cortado, sin clase `arriba`.
- Después del fix: mismo viewport de 400px, mismo desplegable -- clase `ruta-form-sugerencias arriba`
  agregada automáticamente, `top: 21, bottom: 201`, completamente dentro de los 400px visibles. Captura real
  en [`sugerencias_flip_arriba.jpg`](sugerencias_flip_arriba.jpg): las tres sugerencias, el campo, los
  botones "Guardar como Casa/Trabajo" y "Buscar ruta" todos visibles a la vez.
- Confirmado que el comportamiento normal (viewport alto, sin teclado) no cambió: en 390×844 el mismo
  desplegable sigue abriendo hacia abajo (`bottom: 494 < 844`), sin la clase `arriba`.

108/108 tests de frontend, lint y build en verde después del cambio. El resto del tratamiento mobile/
landscape (ya maduro, descrito arriba) no se tocó.

### Nota de acceso real para esta sesión

Se generó una contraseña de prueba local (`backend/.env`, `AUTH_PASSWORD_HASH` recalculado con bcrypt
directo, sin el flujo interactivo de `generar_password.py`) para poder loguearse de verdad -- no es un
secreto de producción (T06 ya confirmó que no hay ningún despliegue público). El backend de desarrollo se
reinició para que tomara el `.env` nuevo. Detalle completo de la decisión (restaurar o dejar la contraseña
de prueba) en el asiento de bitácora de esta sesión.
