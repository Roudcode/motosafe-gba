# MotoSafe GBA — evaluación UX para celular vertical

Fecha: 23/10/2026. Base: código de frontend en commit `f7ebdd4`, captura de producción `docs/tesis/capturas_prod/figura_4_7_viewport_movil.jpg` (375×812), evidencias visuales V05/V06/V09/V10–V14 y `docs/calidad/QA_ACCESIBILIDAD_VISUAL.md`. Se revisaron CSS y componentes de explorar, buscar, comparar rutas y navegar. **Es una revisión heurística sobre código y capturas existentes**, no una nueva sesión de uso con teléfono físico, teclado virtual o tráfico real. No se modificó la interfaz.

## Dictamen

La interfaz ya es utilizable en vertical y ha corregido varios problemas reales de superposición. No necesita cambiar de estética desde cero. Su límite principal es la **densidad simultánea**: en 375 px compiten topbar de dos filas, mapa con hexágonos y marcadores, leyenda inferior y dos acciones flotantes. Al abrir una tarea, el usuario cambia de foco entre varios elementos flotantes en vez de avanzar por una secuencia clara. Las propuestas de abajo son mejoras por etapa de uso; no están implementadas ni aprobadas.

## Recorrido móvil y oportunidades

| Prioridad | Momento | Evidencia observada | Mejora propuesta | Criterio de validación |
|---|---|---|---|---|
| P1 | Abrir y entender el mapa | Captura 375×812: hexágonos rojos/amarillos, marcadores de prensa, topbar de dos filas, leyenda y FABs ocupan a la vez la vista. `App.css:1409–1532` regula posiciones, pero no reduce información inicial. | Un inicio «Explorar» más sereno: mostrar una capa principal y un único acceso claro a capas; la leyenda compacta por defecto, con detalle a pedido. Conservar datos actuales al abrirla. | En 5 segundos, usuarios nuevos identifican qué están viendo y cómo buscar una ruta; mapa y acción principal siguen visibles a 360/375/390 px. |
| P1 | Buscar destino con teclado | V05 documenta que `RutaForm` no tiene límite vertical propio porque el desplegable absoluto se recortaba al añadir `overflow`. CSS usa `width:88vw` y sugerencias posicionadas. No hay prueba documentada con teclado virtual real. | Diseñar el formulario como una tarea móvil dedicada, con área de resultados y botón de acción adaptados al *visual viewport*; resolver la superposición del teclado junto con el desplegable, sin agregar un overflow que lo corte. | Probar en Android e iPhone físicos con teclado abierto, 360/390 px, texto largo y cinco sugerencias: destino, sugerencias, «Buscar ruta» y volver al mapa son accesibles sin scroll imposible. |
| P1 | Comparar rutas | V06 ya separa km/min y fija «Iniciar viaje». En móvil `.ruta-resumen` tiene ancho `min(300px,78vw)` y altura máxima `42vh`; hay prioridades «Rápida/Equilibrada/Menor exposición», tarjetas, cobertura y detalle interno en un espacio reducido. | Dar a las alternativas un resumen de una línea fuerte (tiempo, distancia y cobertura confiable o «sin datos») y reservar el cálculo/zonas para expansión. Evitar que «Menor exposición» parezca una garantía; cuando ninguna ruta alcanza cobertura, hacer visible esa condición antes del CTA. | Sin abrir detalles, alguien puede elegir una ruta y explicar por qué; el mapa aún muestra el trazado; se distingue «sin datos» de 0% y no se inicia por error una alternativa distinta. |
| P1 | Navegar | La captura V09 muestra una reducción real de decoración. En vertical, el CSS oculta la hora estimada de llegada (`.nav-resumen-mini-llegada {display:none}`) y fuerza el nombre de la calle a una línea (`-webkit-line-clamp:1`); las maniobras pueden ser largas. | Mantener giro, calle y distancia legibles como primera prioridad; permitir dos líneas a nombres largos o una expansión sencilla. Evaluar si el dato secundario más útil es ETA o kilómetros según pruebas con motociclistas detenidos. | Con tres instrucciones largas y sol directo simulado, el siguiente giro se lee sin tocar; no se confunde «7 min» con tiempo total inicial; el botón Salir queda accesible. |
| P2 | Capas y leyenda | La leyenda móvil mide 124 px y ofrece Todo/Siniestros/Delitos más cuatro niveles, con cada elemento interactivo de alrededor de 24 px en varias reglas (`App.css:1019–1039`). V14 añadió `:active` en controles, pero feedback no aumenta tamaño táctil. | Separar «qué capa veo» de «qué niveles filtro» en controles progresivos; mantener filtros con estado inequívoco y objetivos táctiles mayores, sin ampliar la leyenda permanentemente. | A 360 px, el usuario activa solo «alto» sin tocar «medio» ni arrastrar el mapa por accidente; puede restablecer filtros en un gesto claro. |
| P2 | Prensa sobre el mapa | En la captura móvil se mezclan iconos de noticia, burbujas numéricas y hexágonos. La vista de prensa ya dispone de filtro y listado/portal; el mapa solo no permite estimar cuántos eventos hay bajo cada punto agrupado. | Priorizar un conmutador «Mapa / Lista» dentro de Prensa en móvil y vincular cada elemento de lista con su punto y precisión geográfica. Mantener tipo, fecha editorial y radio de ubicación visibles antes de abrir la nota. | En un grupo de 9 noticias del mismo barrio, se pueden abrir las 9 individualmente desde móvil y regresar al mismo contexto, sin creer que 9 iconos son 9 ubicaciones exactas. |
| P2 | Reportar un hecho | El FAB «Reportar» comparte la esquina inferior con «Trazar ruta» y herramientas; en vertical el dedo tapa parte del mapa al buscar dónde marcar. | Iniciar un flujo en dos pasos: elegir tipo y ubicar/revisar punto; mostrar claramente alcance, vigencia y quién ve el reporte antes de enviar. Evitar acciones de reporte muy destacadas durante navegación activa. | Una persona puede enviar o cancelar sin confundir la ubicación de GPS, del mapa y del hecho; la confirmación muestra estado y forma de borrar/consultar. |
| P2 | Estados de error | Ya hay mensajes diferenciados de capas y reintentos (V10). En móvil, los banners pueden competir con controles que cambian de posición. | Mostrar un estado compacto junto a la capa afectada y una acción de reintento contextual; reservar alertas globales para pérdida de ruta/GPS/autenticación. | Cortar red, fallar solo clima, fallar solo prensa y fallar rutas: cada caso indica qué dato falta y qué puede seguir usándose sin tapar la acción principal. |

## Qué conservar

- La elección de modo Explorar/Comparar/Navegar (V01), con una acción principal distinta en cada uno.
- MapLibre, colores de riesgo con texto y diferenciación de fuentes; revisar densidad de visualización antes de cambiar paleta.
- Botón «Iniciar viaje» fijo fuera del área de scroll, correcciones de foco y `:active`, y safe areas del CSS.
- Detalle progresivo y explicación de cobertura. La dificultad para interpretar cobertura también aparece en la prueba de 12 motociclistas descrita en la tesis; esa muestra es pequeña y por conveniencia.

## Orden de prueba recomendado

1. **Móvil físico vertical con teclado**: buscar origen/destino y cinco sugerencias; 360/375/390 px y zoom de texto del sistema.
2. **Comparación de tres rutas**: cobertura baja, sin datos y tiempo similar; medir si entiende «menor exposición» antes de tocar detalle.
3. **Mapa denso de prensa**: grupo de 9 noticias y filtros por moto/robo; medir descubrimiento de todas las notas.
4. **Navegación estacionado y en simulación segura**: instrucciones largas, pérdida GPS, desvío y llegada; evaluar lectura, no interacción mientras conduce.
5. **Tema claro/oscuro y sol directo**: contraste real en teléfono, objetivos táctiles, VoiceOver/TalkBack y fuente ampliada.

Para cada escenario, registrar modelo de teléfono, navegador, tamaño lógico, orientación, teclado, captura y resultado. No atribuir a esta auditoría una validación en dispositivo físico que no se hizo.

## Relación con el backlog

Usar los IDs existentes: V01 para jerarquía por modo; V03 tipografía; V05 teclado/panel móvil; V06 comparación; V08 capas; V09 navegación; V10 estados; V13 prensa; V14 tactilidad; A23 accesibilidad visual; T02 pruebas E2E. Este documento aporta prioridades y criterios nuevos sobre esos mismos ítems. No abre un catálogo paralelo ni autoriza cambios de producto.
