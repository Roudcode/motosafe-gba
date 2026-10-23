# V06 — tarjetas de rutas comparables (2026-10-22, SES-161)

Criterio de cierre: "Tiempo, distancia, cobertura y ejes separados; selección visible sin promesa
absoluta." Vive en `RutaResumenPanel.jsx` y los datos ya calculados en `riesgoRuta.js` (incluido
`brechaCoberturaEnRecomendada` de DEC-026, ya cerrado).

## Qué había antes (revisado en el componente real)

Ya existe una estructura de tarjeta por ruta (`.ruta-opcion`, un botón por alternativa), no una lista
corrida de números -- eso ya estaba resuelto. Dentro de cada tarjeta:

1. **Hallazgo real 1**: tiempo y distancia se mostraban como un solo texto corrido, `{r.km} km · {r.min}
   min`, sin separación visual real entre los dos ejes -- mismo peso tipográfico, unidos por un punto medio.
2. **Ya resuelto de antes, confirmado**: cobertura por fuente (siniestros/inseguridad) y el desglose
   (cantidad de zonas por eje + puntaje) ya están en líneas separadas de la de tiempo/distancia y de la de
   exposición, detrás del toggle "Ver cómo se calcula" (progresivo, no amontonado) -- ejes ya diferenciados
   ahí.
3. **Selección visible sin promesa absoluta, ya cumplido**: la tarjeta seleccionada se marca con
   borde+sombra (ver V04), pero el texto nunca dice "esta es la segura" -- dice "exposición bajo/medio/alto
   entre alternativas" (comparativo, no categórico) o "cobertura registrada insuficiente"/"sin zonas
   registradas cerca" (hedge explícito). El aviso de DEC-026 (`brechaCoberturaRecomendada`, ya implementado
   esta semana) ya refuerza exactamente este punto cuando corresponde: avisa cuando la recomendación de
   "menor exposición" depende de una fuente con cobertura parcial, sin opacarlo ni competir con el resto del
   panel (mismo patrón visual `ruta-cobertura-aviso`, debajo de la lista de tarjetas). No hizo falta tocarlo
   de nuevo -- ya cumple lo que pide este criterio.

## Qué se cambió

Solo el hallazgo real 1: tiempo y distancia pasan a dos `<span class="ruta-opcion-stat">` con ícono propio
cada uno (`Route` para distancia, `Clock` para tiempo, mismo patrón de ícono+texto que ya usa el resto del
panel -- badges, desglose, cobertura con tráfico), en vez de un texto corrido. El contenedor
(`.ruta-opcion-datos`) pasa a `display: flex` con `gap`, así que el ícono de tráfico en vivo (ya existía)
también queda como un tercer "stat" separado, en vez de pegado con un "·" a mano.

## Qué no se tocó

No se cambió qué datos se muestran, ni cuándo (la cobertura por fuente y el desglose siguen detrás del
mismo toggle de antes). No se cambió el score, el umbral de "cobertura registrada insuficiente" (0,6) ni
nada de `riesgoRuta.js`. No se introdujo ningún componente de tarjeta nuevo -- es el mismo `.ruta-opcion`
de siempre, con una sub-estructura nueva adentro de una sola línea.

## Verificación

- `eslint src/`: limpio.
- `vitest run`: 108/108 (sin tests nuevos -- cambio de marcado/CSS puro sobre una línea que ningún test
  existente verificaba por contenido textual exacto; se revisó que ningún test de `RutaResumenPanel`
  dependiera del texto anterior y no hay ninguno, el panel no tiene test de componente propio todavía).
- `vite build`: compila sin errores.
- **No se verificó en pantalla real** (mismo motivo que V01/V04: sin credencial de acceso a la app desde
  acá). Queda pendiente la captura antes/después que pidió Rodo explícitamente -- no se pudo producir sin
  poder levantar el stack logueado.

## Actualización 2026-10-22 (SES-163) — captura real conseguida

Con sesión real, trazada una ruta real (Paraguay 1854 → Avenida Maipú 1300, Vicente López -- mismo caso 2
de D03/DEC-026). Confirmado con JS sobre el DOM real: `.ruta-opcion-stat` renderiza "16.6 km" y "21 min"
como elementos separados (no un texto corrido), y el aviso de DEC-026 se disparó solo (sin forzarlo) con los
valores reales: "cobertura parcial de inseguridad (56%, contra 85% de la otra fuente)" -- confirma que
`brechaCoberturaEnRecomendada` funciona de punta a punta con datos reales, no solo en los tests unitarios.
Captura real en [`tarjetas_km_min_separados.jpg`](tarjetas_km_min_separados.jpg): las tres tarjetas de ruta,
cada una con distancia y tiempo en su propio ícono, badges de "rápida"/"menor exposición", y el aviso de
cobertura parcial visible debajo de la lista. Queda cubierto el pendiente de captura real.
