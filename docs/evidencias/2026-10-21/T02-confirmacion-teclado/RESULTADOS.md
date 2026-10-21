# T02 — confirmación visual real del arreglo de teclado del buscador (2026-10-21, SES-149)

Confirma en navegador real (no solo el test de componente) el arreglo del commit `63528d3`
(`frontend/src/components/SearchBar.jsx`): el cierre por pérdida de foco se movió del input al
contenedor (`onBlur` + `e.relatedTarget`), y los botones de resultado pasaron de `onMouseDown` a
`onClick`.

Corrido contra el stack real: `npm --prefix frontend run dev:http`, backend real en :8000, sesión
autenticada ya viva del navegador pane (no se pidió ni se tipeó contraseña). Verificación de foco hecha
leyendo `document.activeElement` real desde la consola del navegador (equivalente a mirarlo en devtools),
no infiriéndolo de una captura de pantalla.

## Desktop

1. Abrí el buscador, escribí "Plaza de Mayo, Buenos Aires", Enter → resultados reales de Nominatim.
2. `Tab` desde el input → foco real en el botón "Limpiar búsqueda" (`cls: searchbar-clear`).
3. `Tab` de nuevo → foco real en el primer botón de resultado: `tag: BUTTON, text: "Rooftop Plaza de
   Mayo, Avenida de Mayo 560, Buenos Aires", outline: solid 3px` — confirmado con
   `document.activeElement`, anillo de foco visible.
4. `Enter` sobre ese botón → seleccionó el resultado, centró el mapa con un pin real y mostró la tarjeta
   "Ir"/"Cerrar" con "Rooftop Plaza de Mayo... Important tourist attraction".

## Viewport móvil (375x812)

Repetido igual con "Obelisco, Buenos Aires": `Tab` x2 desde el input llegó a
`BUTTON "Obelisco, Avenida Juan Bautista Justo, Buenos Aires"` con `outline: solid 3px`, y `Enter` lo
seleccionó y centró el mapa, mostrando la misma tarjeta de confirmación. Mismo comportamiento que en
desktop, sin diferencias.

## Resultado

El hallazgo real de SES-146 (la lista de resultados no era alcanzable por teclado porque se desmontaba del
DOM en cuanto el foco salía del input) está corregido y confirmado visualmente en los dos tamaños pedidos.
Esto era lo único que le faltaba a T02 en este punto: no se tocó código de producción en esta sesión, solo
se verificó el commit ya hecho.

Suite completa verificada aparte: 96/96 tests de frontend en verde
(`node node_modules/vitest/vitest.mjs run`, 6 archivos de test incluido el nuevo `SearchBar.test.jsx`).
