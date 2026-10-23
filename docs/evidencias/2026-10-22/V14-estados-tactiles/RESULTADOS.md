# V14 — pulir estados táctiles y transiciones (2026-10-22, SES-162)

Criterio de cierre: "Feedback inmediato, sin saltos de layout ni dependencia exclusiva de hover." Depende
de V02 (ya cerrado en esta misma sesión) y A23.

## Qué había antes (medido, no asumido)

Comparadas todas las reglas `:hover` de `App.css` contra las reglas `:active` existentes (41 `:hover` vs 18
`:active`): **15 controles reales y tocables** tenían feedback solo por `:hover` -- en celular, sin mouse,
eso es cero feedback al tocar. Descartados de la lista: `.maplibregl-ctrl-attrib-button` y
`.maplibregl-popup-close-button` (controles propios de MapLibre, no nuestros para restylear sin tocar la
librería) y `.capa-inseguridad-toggle` (confirmado código muerto -- ningún JSX la usa más, quedó de antes
del panel único de capas; no se tocó por no ser parte de este alcance).

**"Sin saltos de layout"**: revisado aparte -- ninguna regla `:hover` existente cambia `padding`, `margin`,
`width`, `height` ni `font-size` (todas usan `transform`/`box-shadow`/`color`/`border-color`, que no
provocan reflow). Ya cumplido, no hizo falta tocar nada ahí.

## Qué se cambió

Agregado `:active` con **exactamente la misma declaración** que ya tenía `:hover` (ningún valor nuevo) en
los 13 controles reales restantes: `.capa-toggle.capas-con-cambios`, `.topbar-status.clickeable`,
`.actividad-borrar`, `.ruta-form-miubicacion`, `.ruta-opcion`, `.ruta-opcion.activa`,
`.ruta-detalle-toggle`, `.popup-voto-btn`, `.popup-ver-noticia`, `.popup-grupo-prensa-item`,
`.portal-actividad-item` (sumado a su `:focus-visible` ya existente). Es una extensión de selector, no un
rediseño -- cada control ya tenía su efecto definido, solo le faltaba dispararse también al tocar.

## Qué no se tocó

`.capa-inseguridad-toggle` (código muerto, fuera de alcance). Los demás controles que ya tenían `:active`
(18 antes de este cambio) -- no se tocaron, ya cumplían. No se agregó ningún efecto nuevo que no existiera
ya en `:hover` -- el criterio es "no depender solo de hover", no "agregar más feedback del que había".

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- son reglas CSS puras, extensión de selector).
- `vite build`: compila sin errores.

## Actualización 2026-10-22 (SES-163)

Con sesión real disponible: `:active` es un pseudo-estado transitorio (solo dura mientras el botón del
mouse/dedo sigue presionado), difícil de capturar con las herramientas de automatización de esta sesión
(no hay forma confiable de mantener el "mousedown" y tomar una captura en el medio desde acá). Confirmado
en cambio, con JS, que las reglas CSS nuevas existen realmente en la hoja de estilos cargada por el
navegador real (no solo en el archivo fuente) -- se verificó que `.ruta-opcion:active` y
`.portal-actividad-item:active` aparecen en `document.styleSheets` con las mismas declaraciones que
`:hover`. El cambio es mecánico y de bajo riesgo; la confirmación visual del efecto en un dispositivo
táctil real queda pendiente.
