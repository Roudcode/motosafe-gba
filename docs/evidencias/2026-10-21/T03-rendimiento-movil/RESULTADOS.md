# T03 — línea base real de rendimiento móvil (2026-10-21)

Dependía de A17 (separar `App.jsx`), prácticamente cerrado (bajó de 2140 a 1959 líneas en sucesivas
extracciones -- hoy 1981 con dos líneas de instrumentación temporal ya revertidas, sin bloques de
extracción pendientes conocidos). Medido con el stack real en modo dev (`npm run dev:http`), viewport móvil
emulado de 375x812.

## Método

No se usó React DevTools Profiler (no disponible como extensión en este navegador de panel). En su lugar,
mismo criterio que SES-112 para el perfilado anterior: una línea de instrumentación temporal
(`window.__renderCountApp++` / `window.__renderCountMapa++` al principio de `App()` y de
`MapaMotoSafeInner()`), leída con `performance.now()`/`performance.memory` desde la consola real del
navegador, **revertida con `Edit` antes de cerrar la sesión** (confirmado con `git diff` vacío sobre los
dos archivos). Carga inicial medida con la Navigation/Paint Timing API real del navegador
(`performance.getEntriesByType('navigation'|'paint')`), no inventada.

**Limitación honesta**: esto corrió contra el servidor de desarrollo de Vite (sin minificar, con
`React.StrictMode` que en desarrollo duplica el montaje/efectos de cada componente -- ya documentado en
A17), en el navegador del panel de Claude (no un celular real, sin throttling de red ni CPU). Los números
de abajo son una línea base real pero **optimista** respecto a producción real en un celular real con red
real: sirven para detectar regresiones futuras (compararse contra sí misma), no como una promesa de
experiencia en campo.

## Carga inicial (navegación fresca, 375px)

| Métrica | Valor real |
|---|---|
| DOM interactivo | 35,5 ms |
| DOMContentLoaded | 189,7 ms |
| First Contentful Paint | 272 ms |
| Load event | 195,1 ms |
| Renders de `App` hasta este punto | 30 |
| Renders de `MapaMotoSafe` hasta este punto | 24 |
| Memoria JS usada | ~64 MB (de ~104 MB de heap total) |

Los 30/24 renders iniciales (antes de cualquier interacción) salen de las ~8 cargas de datos en paralelo
(hotspots, corredores, inseguridad general/moto, reportes, prensa, cobertura, clima) más el doble montaje
de `StrictMode` en desarrollo -- no es un número comparable 1:1 con producción, donde `StrictMode` no
duplica nada.

## Sesión de uso típica (buscar, trazar ruta, modo viaje)

Medido en secuencia continua, mismo viewport, sin recargar la página:

| Tramo | Duración | Δ renders `App` | Δ renders `MapaMotoSafe` |
|---|---|---|---|
| Reposo tras la carga (sin interactuar) | 10 s | 0 | 0 |
| Buscar "Plaza Once" → elegir destino → armar ruta (origen real) → calcular → iniciar viaje | ~75 s (incluye tiempos de red reales de Nominatim/TomTom) | +60 | +58 |
| **Modo viaje activo, en reposo** (sin tocar nada, tarjeta de maniobra visible) | 60 s | **+16 (16/min)** | **+12 (12/min)** |
| Tras "Salir" del viaje, mapa quieto | 60 s | **+10 (10/min)** | **+10 (10/min)** |

Memoria al final (~4 minutos de sesión, tras buscar, trazar ruta y un ciclo completo de modo viaje): ~61 MB
usados de ~67 MB de heap total -- en el mismo orden que al inicio (~64 MB), sin indicio de crecimiento
sostenido en esta sesión corta. No se midió una sesión larga (30+ minutos) que pudiera revelar una fuga
lenta.

## Objetivo propuesto (con la medición real como referencia)

- **Renders en reposo (sin modo viaje activo)**: no superar **15 renders/min** de `App` fuera de
  interacción del usuario. Medido: 10/min. El margen cubre el polling ya conocido y documentado (reportes y
  hora cada 30s, hotspots cada 5 min) sin dejar pasar una regresión que agregue un intervalo nuevo sin
  querer.
- **Renders en reposo durante modo viaje activo**: no superar **22 renders/min** de `App`. Medido: 16/min
  -- el margen cubre el cálculo de velocidad/ETA/paso actual, que es más frecuente por diseño mientras se
  navega.
- **Tiempo a interactivo (dev local, sin red real)**: no superar **500 ms** de `domInteractive` ni **600
  ms** de First Contentful Paint en este mismo entorno de referencia (servidor dev local, sin throttling).
  Medido: 35,5 ms / 272 ms -- el objetivo deja margen generoso porque el número de hoy depende de que la
  máquina y la red locales estén descargadas; sirve como alarma temprana ante una regresión real (un
  bundle que creció mucho, un efecto que bloquea el render inicial), no como el número que vería un usuario
  real.
- **No se propone** todavía un objetivo de tiempo de carga en una red móvil real/throttled ni en un
  dispositivo físico real -- no se midió ninguna de las dos cosas en esta sesión (el navegador del panel no
  tiene throttling de red ni de CPU disponible, y no había un dispositivo real a mano). Queda como el
  siguiente paso real de T03, no resuelto acá.

## Conclusión

Primera línea base real y medida (no inventada) para T03, en el mismo entorno que viene usándose para
verificación visual en esta sesión de trabajo. El presupuesto propuesto es una alarma de regresión contra
esta misma línea base, no una garantía de experiencia en un celular real -- eso necesita throttling de red
real o un dispositivo físico, que quedan pendientes.
