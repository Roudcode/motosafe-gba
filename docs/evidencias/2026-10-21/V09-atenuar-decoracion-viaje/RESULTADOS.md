# V09 — atenuar decoración y animación durante el viaje (2026-10-21, SES-154)

Mismo criterio ya usado en A23/V10: medible/objetivo (qué compite visualmente, no una decisión de diseño
nueva). Alcance acotado a lo que compite sin aportar información durante un viaje en curso -- sin tocar la
ruta trazada, la tarjeta de maniobra, el velocímetro ni alertas reales.

## Qué se encontró (listado antes de tocar nada, como pidió Rodo)

Revisado `frontend/src/App.jsx`, `MapaMotoSafe.jsx` y `App.css` buscando qué queda visible y animado
durante `vistaNavegacion`:

1. **Ya resuelto de antes, confirmado funcionando**: casi toda la topbar (tema, capas, actividad, buscar,
   clima) ya se oculta con `!vistaNavegacion &&...`. El fondo del mapa (hexágonos, clusters, mapa de calor,
   corredores) ya se atenúa a opacidad 0,1 vía `atenuarFondo` (`App.jsx:1584`) -- aplicado de forma
   consistente a todas las capas GL de `MapaMotoSafe.jsx`. Los marcadores HTML de hotspots/corredores en
   nivel "crítico" (clase `capa-fondo-nav`) también se atenúan a 0,15 vía `.mapa-en-navegacion
   .capa-fondo-nav` en `App.css`. El puck de posición (`puck-navegacion`, pulso propio) y las zonas
   realmente cruzadas por la ruta siguen a opacidad plena -- correcto, son información real de navegación,
   no decoración.
2. **Hallazgo real 1**: los marcadores de notas de prensa (`marker-prensa-wrapper`, `marker-prensa-grupo`)
   **no** llevaban la clase `capa-fondo-nav` -- quedaban a opacidad plena (1) durante toda la navegación,
   a diferencia de los hotspots/corredores de fondo que sí se atenúan. Una noticia vieja en el mapa competía
   visualmente con la ruta igual que si la navegación no estuviera activa.
3. **Hallazgo real 2**: el punto del estado en la topbar (`.topbar-status.viaje .status-dot`) pulsa
   continuamente (`pulse-report 1.4s infinite`) durante **todo** el "modo viaje", incluida la navegación a
   pantalla completa -- un parpadeo de fondo que no agrega información (el texto de al lado ya dice la
   ruta/ETA) y queda ahí compitiendo con la tarjeta de maniobra.
4. **Revisado y descartado como hallazgo**: los marcadores de reportes comunitarios recientes
   (`pulse-marker-report` en `reportes`) son alertas reales de seguridad (ver también el banner
   `alertaReporte` ya existente en `App.jsx`) -- no se tocaron, a propósito. El marcador de "dónde va a
   quedar el reporte" (`ubicacionReporte`) solo aparece mientras se compone un reporte nuevo, no durante
   navegación en curso -- tampoco se tocó.

## Implementación

- `MapaMotoSafe.jsx`: `marker-prensa-wrapper` y `marker-prensa-grupo` ahora llevan también la clase
  `capa-fondo-nav` -- se atenúan igual que hotspots/corredores (0,15 de opacidad) durante la navegación, con
  la misma transición de 0,4s que ya existía, sin tocar su comportamiento fuera de navegación.
- `App.jsx`: el `topbar-status` ahora recibe un modificador `nav-activa` cuando `vistaNavegacion` es real
  (no solo `modoViaje`, para no apagar el punto en un caminar con el modo activo pero sin la cámara de
  navegación bloqueada, donde no compite con nada).
- `App.css`: `.topbar-status.viaje.nav-activa .status-dot { animation: none; opacity: 0.6; }` -- apaga el
  pulso solo en navegación activa, deja el punto visible (más tenue) en vez de ocultarlo del todo.

Ninguna animación nueva: solo se atenúa/apaga lo que ya existía. `prefers-reduced-motion` no necesita
ningún cambio -- la regla global `*, *::before, *::after { animation-duration: 0.01ms !important; ... }`
en `App.css` ya cubre cualquier animación existente o futura, y lo que se tocó acá es "apagar" o "reusar"
una clase ya atenuada, no agregar un `@keyframes` nuevo.

## Verificación

**Antes de tocar nada**: confirmado con el navegador real que los marcadores de prensa quedaban a opacidad
`1` durante la navegación (`getComputedStyle`).

**Real, con un viaje en curso** (stack real levantado, sesión real logueada, ruta real Paraguay 1854 →
Obelisco, modo viaje iniciado de verdad):

```
mapaEnNavegacion: true
opacidad de marcadores de prensa: 0.15   (antes: 1)
clase del topbar-status: "topbar-status  viaje  nav-activa"
animación del punto de estado: "none"    (antes: "pulse-report")
```

Captura real: [`navegacion_atenuada.jpg`](navegacion_atenuada.jpg) -- la tarjeta de maniobra ("Dobló a la
derecha...") y el resumen de navegación ("7 min · 1.2 km · Salir") quedan como lo más prominente en
pantalla, con el fondo del mapa visiblemente apagado.

Al salir del viaje (`Salir`), confirmado que los marcadores de prensa vuelven a opacidad `1` con una
transición suave (`0.4s`), sin quedar "pegados" en el estado atenuado.

96/96 → **101/101** tests de frontend en verde (sin tests nuevos específicos de V09 -- es un cambio de
clases CSS puro, verificado en pantalla real; los 5 tests nuevos de esta sesión son de V10, ya cerrado
antes). Eslint limpio.

## Qué no se tocó

Nada de la ruta trazada, la tarjeta de maniobra, el velocímetro, el puck de posición, ni los banners de
alerta real (`alertaReporte`, `CapaErrorBanners`). Nada del resto del catálogo V.
