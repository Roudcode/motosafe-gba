# V13 — marcadores diferenciados por origen y antigüedad (2026-10-22, SES-162)

Criterio de cierre: "Histórico/prensa/comunidad reconocibles sin confundir precisión con halo físico."
Depende de A11 (ya validado). Vive en `MapaMotoSafe.jsx`.

## Qué había antes (revisado en el código real)

- **Prensa**: ya tiene ícono propio por tipo de incidente (diario para "robo", auto con impacto para
  "choque") y un halo punteado cuyo tamaño escala con el nivel de precisión real (`radio_metros` →
  intersección/calle/barrio) -- con un comentario explícito del autor original: "Nunca se dibuja como si
  fuera un punto exacto cuando el texto de la noticia no lo era". Esta parte del criterio (precisión
  comunicada sin fingir exactitud) ya estaba resuelta, con intención documentada.
- **Hallazgo real**: histórico (hotspots de siniestros) y comunidad (reportes colaborativos) usan **la
  misma función** (`elementoCirculo`) para dibujarse -- círculo liso, mismo borde sólido, diferenciados solo
  por color y tamaño. A diferencia de prensa (que sí tiene ícono propio), estos dos **no son reconocibles
  entre sí por forma**, solo por color -- el mismo tipo de ambigüedad que V04 buscó (y no encontró) en la
  UI de paneles, pero acá sí aparece, en el mapa.
- Revisado también: `.cluster-bubble-inseguridad` (clusters de inseguridad) ya usa un recurso para esto --
  `border-radius: 28%; border-style: dashed` en vez del círculo sólido de los clusters de siniestros. Es el
  mismo tipo de necesidad que comunidad/histórico, resuelta ahí con borde punteado.

## Qué se cambió

Se extendió `elementoCirculo({ ... })` con un parámetro opcional `estiloBorde` (default `'solid'`, no
rompe ningún llamado existente) y se usó `estiloBorde: 'dashed'` **solo** en el marcador de reportes
colaborativos (`reportes.map(...)`) -- mismo recurso visual (borde punteado) que ya usa
`.cluster-bubble-inseguridad` para una distinción parecida, no un patrón nuevo. Los hotspots históricos
siguen con borde sólido, sin cambios.

## Qué no se tocó

- El halo de precisión de prensa (ya resuelto, con intención documentada -- no se tocó el tamaño ni el
  criterio de los tres niveles).
- Los marcadores de `origenPunto`/`destinoPunto`/`ubicacionReporte` (ruta y borrador de reporte en curso):
  son una categoría distinta (puntos de un flujo en curso, no histórico/prensa/comunidad ya publicados),
  fuera del alcance de este criterio.
- No se tocó el ícono de prensa ni su paleta.

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- no hay test de componente de `MapaMotoSafe.jsx` para estos
  marcadores hoy; cambio de un parámetro CSS inline con valor por defecto que preserva el comportamiento
  anterior en todos los demás llamados).
- `vite build`: compila sin errores.

## Actualización 2026-10-22 (SES-163)

Con sesión real disponible, no había ningún reporte colaborativo real cargado en la base de desarrollo para
ver el marcador con borde punteado en pantalla (confirmado: todos los marcadores visibles en el mapa real
eran de prensa, ninguno de `reportes`). No se fabricó un reporte falso para forzar la verificación visual
-- queda pendiente para cuando exista un reporte real, o si Rodo quiere crear uno de prueba él mismo. El
cambio en sí (parámetro `estiloBorde` con valor por defecto que preserva el comportamiento anterior) sigue
respaldado por lint/tests/build en verde.
