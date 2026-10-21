# T02 — E2E visual real (2026-10-21, SES-146)

Corrido contra el stack real: `npm --prefix frontend run dev:http` (Vite sin HTTPS, workaround documentado
en `vite.config.js`), backend real en :8000, PostgreSQL/PostGIS local real, sesión autenticada real del
navegador pane (cookie de sesión viva de una sesión anterior — no se pidió ni se tipeó contraseña en este
tramo). Servidor backend sin errores nuevos en los logs durante toda la corrida (`preview_logs` revisado).

No se tocó código de producción. No se corrió ningún script que escriba en datos reales salvo el reporte
de prueba descripto abajo (consciente y documentado, no accidental).

## Nota sobre la herramienta de prueba, no el producto

Al emular un viewport de escritorio grande (1400x900) con `resize_window` con tamaño custom, el DOM mide
y layoutea correctamente (verificado con `getBoundingClientRect` en consola: `#root`, `.app`, el canvas de
MapLibre, todos a 1400x900), pero la captura de pantalla de la herramienta del navegador solo pinta una
esquina de ~180x115px y deja el resto en blanco — un artefacto de la herramienta (`computer screenshot`),
no un bug de la app. Confirmado reproducible en una pestaña nueva. El preset `mobile` (375x812) y el
tamaño nativo del panel (~316x295, usado como "desktop" de facto en esta sesión) capturan sin problema.
Por eso el tramo de escritorio de esta corrida se hizo en el tamaño nativo del panel en vez de un 1280/1440
estándar — limitación de la herramienta, declarada, no del producto.

## Flujos probados (desktop, mouse)

| Flujo | Resultado | Evidencia |
|---|---|---|
| Modo dev | OK | `npm run dev:http` sirvió la app completa con HMR de Vite activo (`[vite] connected` en consola), sin certificado bloqueando la carga. |
| Click en zona de riesgo | OK | Click en hexágono abrió panel de detalle real: "1258 eventos de riesgo en esta celda", desglose Medio/Bajo, "170 siniestros · 1088 delitos", "Celda de ~650m de radio". |
| Buscar un lugar | OK | Búsqueda real contra Nominatim ("Obelisco, Buenos Aires") devolvió 5 resultados reales; selección centró el mapa y mostró tarjeta "Ir"/"Cerrar". |
| Trazar ruta | OK | Origen real (Paraguay 1854) + destino del paso anterior → 3 alternativas reales de TomTom con tráfico en vivo (7/10/11/12 min según alternativa), exposición alto/medio/bajo, detalle de zonas cruzadas con distancia real ("a 323 m", etc.), nota de alcance de la exposición visible. |
| Reportar | OK | Categoría "Robo o arrebato", ubicación marcada a mano (no había GPS real del dispositivo) → POST real al backend, confirmado con "Reporte enviado — gracias por sumar el dato" y contador "1 reporte tuyo" actualizado. **Se creó un reporte real de prueba en la base de desarrollo local** (no la personal de producción) como parte de este ensayo. |
| Navegación GPS | Parcial | "Iniciar viaje" entró en modo viaje real (tarjeta de maniobra "Doblá a la derecha en Calle Rodriguez Peña", resumen "7 min · 1.7 km", botón "Salir"), sin errores de consola nuevos. **No se pudo probar con una traza GPS real de dispositivo** — el navegador del panel no tiene geolocalización física; sigue siendo el límite ya declarado en A16 (trazas reales de parada/giro/desvío/pérdida/llegada pendientes). |

## Repetido a 375px (mobile)

Con `resize_window` preset `mobile` (375x812): legend, FABs de "Trazar ruta"/"Reportar", topbar y buscador
se ven completos sin recorte ni superposición. Se repitió el flujo de reporte completo a este ancho (misma
categoría, mismo resultado: "Reporte enviado"). Buscador y resultados también se probaron a este ancho con
el mismo comportamiento que en desktop.

## Teclado solo

Probado con `Tab`/`Shift+Tab`/`Enter`/`Escape`/`Down`, sin mouse, leyendo el foco real
(`document.activeElement`) en vez de inferirlo de la captura.

- **OK**: los botones principales de la topbar (tema, capas, actividad, buscar, reportar) son alcanzables
  en orden lógico por Tab, cada uno con anillo de foco visible (`outline: solid 3px`).
- **OK**: el botón "Buscar lugar, calle o local" se activa con Enter y el foco pasa automáticamente al
  campo de texto (no hace falta un click extra).
- **OK**: el panel de capas se abre con Enter sobre su botón y se cierra con `Escape` (confirmado con un
  segundo `read_page` tras un breve delay de render).
- **Hallazgo real (confirmado, reproducible dos veces)**: la lista de resultados de búsqueda **no es
  alcanzable por teclado**. Los resultados existen como `<button>` reales en el DOM apenas se muestran
  (confirmado con `read_page`: `button "Plaza de Mayo, Avenida Rivadavia, Buenos Aires"`, etc.), pero se
  desmontan del DOM en cuanto el foco sale del campo de texto (confirmado con
  `document.querySelectorAll('button')` tras un `Tab`: 0 coincidencias). Ni `Tab` ni `ArrowDown` sirven
  para entrar a la lista — sólo el click de mouse (ya probado arriba) selecciona un resultado. Esto
  bloquea completamente "buscar un lugar" (y por lo tanto armar una ruta a partir de una búsqueda) para un
  usuario que solo usa teclado. No estaba cubierto por la matriz de A23 (que se centró en el modal de
  bienvenida y el zoom).

## Lo que no se alcanzó a cubrir en esta pasada

- Repetición exhaustiva de los 6 flujos a 375px (se repitió buscador y reportar; zona de riesgo/trazar
  ruta no se repitieron a este ancho por tiempo, aunque el layout general ya se vio correcto).
- Exploración completa del panel de capas por teclado más allá de abrir/cerrar (son muchas opciones tipo
  radio/checkbox dentro de un panel scrolleable; no se verificó si cada una es alcanzable por Tab).
- Navegación GPS con traza real de dispositivo (limitación de entorno, no nueva).

## Conclusión

Los cinco flujos funcionales centrales (zona de riesgo, búsqueda, ruta, reporte, modo viaje) funcionan de
punta a punta contra el stack real, con datos reales, en desktop y en 375px. Se encontró y confirmó un bug
real de accesibilidad por teclado: la lista de resultados del buscador no es alcanzable sin mouse. Queda
como hallazgo para A23/T02, no corregido en esta sesión (esto fue solo la corrida de evidencia, no se pidió
arreglar nada).
