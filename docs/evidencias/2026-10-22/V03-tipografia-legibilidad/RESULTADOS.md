# V03 — mejorar tipografía y legibilidad de datos clave (2026-10-22, SES-162)

Criterio de cierre: "Calle, giro y ETA legibles con texto ampliado sin ocultar acciones." Foco en
`NavegacionManiobra.jsx` (calle + giro) y `NavegacionResumen.jsx` (ETA), los paneles que se ven durante el
viaje.

## Qué había antes (revisado en el código real)

- **Calle/giro** (`.navegacion-texto strong`, el texto de "Dobló a la derecha en Av. Corrientes"):
  `--fs-xl` (19px), con `-webkit-line-clamp: 2` -- ya es de los tamaños más grandes de la escala (`--fs-2xs`
  a `--fs-3xl`, 10px a 36px). No es el caso que necesita texto ampliado.
- **ETA** (`.viaje-tiempo`, la tira mínima de navegación `NavegacionResumen.jsx`): el número de minutos
  restantes (`.viaje-tiempo strong`) ya está en `--fs-2xl` (26px, el escalón más grande salvo `--fs-3xl`).
  **Hallazgo real**: la línea de abajo (`.viaje-tiempo span`) trae la distancia restante **y la hora real de
  llegada** ("4.2 km · llegás 14:32") -- el dato que el criterio de cierre llama "ETA" -- en `--fs-sm`
  (12px), el mismo tamaño que cualquier texto secundario genérico de la app. Es información que alguien
  quiere leer de un vistazo manejando, no un dato decorativo.
- Revisado también el preview del próximo giro (`.navegacion-luego-texto`, "Luego: ..."): también en
  `--fs-sm` (12px) -- consistente con el resto de texto secundario, no es un caso aislado, así que no se
  tocó (es intencionalmente más chico que el giro actual, correcto por jerarquía).

## Qué se cambió

`.viaje-tiempo span` sube un escalón: `--fs-sm` (12px) → `--fs-base` (14px). Sigue siendo claramente más
chico que el número principal (26px), así que la jerarquía (minutos > resto) no se pierde -- solo deja de
estar en el escalón mínimo de la escala para un dato que el propio criterio de cierre nombra explícitamente.

## Por qué no se tocó más

- No hay ningún botón de acción dentro de `NavegacionManiobra`/`NavegacionResumen` que quede oculto al
  agrandar texto -- "Salir" vive en la misma tira (`nav-resumen-mini`), nunca se solapa con estos textos.
  El riesgo que anticipaba la dependencia de V03 ("puede aumentar alto de paneles") no se materializó para
  este cambio puntual: una sola línea, `white-space: nowrap` + elipsis ya la protege de desbordar en
  pantallas angostas.
- **Hallazgo aparte, documentado pero no corregido** (no es un bug de legibilidad real, es deuda técnica):
  existen dos reglas `.navegacion-distancia` en `App.css` (línea ~440, `--fs-md`, con un comentario que la
  describe como la versión "de reposo"; línea ~1770, `--fs-2xl`, sin ninguna clase ni selector que las
  distinga). Al tener el mismo selector y especificidad, la segunda regla (más abajo en el archivo) siempre
  gana en cascada -- la primera es código muerto, nunca se renderiza. No afecta la legibilidad real hoy (el
  tamaño que sí se aplica es el grande), así que no se tocó para no ampliar el alcance de esta sesión sin
  que Rodo lo pida -- queda señalado para una limpieza aparte.

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- cambio de un valor de tamaño de fuente, sin lógica).
- `vite build`: compila sin errores.

## Actualización 2026-10-22 (SES-163) — confirmado real

Con sesión real, trazada una ruta e iniciado el viaje real: `getComputedStyle` sobre `.viaje-tiempo span`
(el texto con distancia + hora de llegada) confirmó `font-size: 14px` (`--fs-base`), el valor nuevo -- antes
del cambio hubiera dado `12px` (`--fs-sm`). Confirmado en pantalla real (ver captura del modo navegar en la
evidencia de V01) que el texto se lee claramente, sin acercarse al tamaño del número principal (26px).
