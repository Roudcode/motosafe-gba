# G04 — ensayo real de demo (2026-10-21, SES-146)

Corrida real de los 6 pasos del guion existente en `docs/entrega/MATRIZ_ACADEMICA_Y_DEMO.md`, tal cual está
escrito — no se reescribió el guion. Esto es la ejecución medida, no una revisión del guion en sí.

**Aclaración honesta sobre los tiempos**: no hubo un presentador humano narrando en esta corrida (la ejecutó
este agente, no Rodo). Los tiempos que siguen son tiempos reales del sistema (carga de datos, respuesta de
cada servicio), no tiempos de una exposición oral real — eso solo se puede medir con Rodo presentando en
vivo. Se declara así en vez de inventar una duración de "demo completa".

## Antes de la demo (registro pedido por el propio guion)

- **Versión / commit**: `cc290b8aa156357d6cf2bb3c396d8814d23b8c6b` (2026-10-21 13:13:30 +0000), rama `main`.
  `frontend/package.json` sin número de versión propio (`0.0.0`, no versionado por SemVer en este
  proyecto).
- **Backend**: `/health` → `estado: ok, base_datos: ok, version_sklearn_coincide: true`. Servido en modo
  dev (`npm run dev:http` del lado frontend; el backend corría ya antes de empezar esta sesión, fuera de mi
  control directo — ver nota más abajo).
- **Datos cargados** (vistos en vivo en la UI, no contados aparte): siniestros con cobertura 2019–2025
  (GCBA), 740 hotspots de riesgo, capa de prensa mostrando "424 de 424" notas en el momento de la corrida,
  nota más reciente de prensa a 58 min de antigüedad.
- **Servicios externos que respondieron en vivo durante esta corrida**: Nominatim (búsqueda de 2 direcciones
  reales, resultados en ambos casos), TomTom Routing (ruta real con tráfico, 3 alternativas), clima (ícono y
  temperatura real visibles, 16°C→17°C entre dos cargas, cambio real no simulado).
- **Fallos simulados**: uno solo, a propósito, en el paso 4 (ver abajo). No hubo ningún fallo no planeado
  de un servicio externo durante el resto de la corrida.

## Los 6 pasos

### 1. Abrir el mapa y explicar cobertura/fuentes antes de seleccionar una ruta

**Tiempo**: carga inicial completa (hotspots + corredores + inseguridad general/moto + reportes + prensa +
cobertura) en ~1-2s reales desde el primer request hasta mapa interactivo (8 pedidos reales en paralelo,
todos 200 OK, visto en `read_network_requests`). **Qué respondió en vivo**: backend propio (todos los
`/api/*`), tiles de mapa base. La leyenda de cobertura ("Siniestros 2019–2025 · GCBA") queda visible antes
de tocar nada, cumpliendo el orden que pide el guion (cobertura antes que ruta).

### 2. Buscar origen y destino, mostrar alternativas, tiempo, exposición y cobertura por fuente

**Tiempo**: búsqueda de dirección real → resultados en ~1,5s (Nominatim real); cálculo de ruta con 3
alternativas → ~2s (TomTom real, con tráfico). **Resultado real** (caso: Paraguay 1854 → Obelisco):
3 alternativas (7/10/11/12 min según tráfico), cada una con su nivel de exposición (alto/medio/bajo) y, al
abrir el detalle, cobertura por fuente separada (siniestros de moto y delitos de inseguridad listados
aparte, con distancia real a cada zona cruzada — "a 323 m", "a 102 m", etc.) y la nota de alcance
("La exposición compara zonas históricas registradas; no estima la probabilidad de un siniestro...").

### 3. Activar una capa de inseguridad y aclarar que no reemplaza siniestros

**Tiempo**: instantáneo (capa ya cargada, solo cambia el dibujo). Confirmado el texto real que ya trae la
UI, tal cual lo muestra el panel de capas: *"Es solo una capa visual: tu ruta y las alertas en viaje
siempre consideran la inseguridad, esté prendida o no esta vista."* — el guion puede citarlo literal en vez
de parafrasearlo.

### 4. Simular fallo de capa y mostrar caché + reintento

**Cómo se hizo, honestamente**: no se tocó el backend real (es un proceso que ya estaba corriendo antes de
esta sesión, fuera de mi control, y pararlo sin saber cómo lo levanta Rodo normalmente era un riesgo
innecesario). En cambio se registró un *service worker* temporal
(`frontend/public/_test_sw_g04.js`, borrado al terminar) que intercepta solo `/api/hotspots` y devuelve
503 a propósito — una forma real de cortar una capa a nivel de red del navegador, sin inventar nada en la
UI ni mockear React. Tras recargar con el service worker activo:

- Apareció el banner real: *"Sin conexión con el backend. Reintentando cada 5s."* con botón "Reintentar
  ahora".
- **El mapa siguió mostrando los hexágonos de riesgo** (288 bajo / 435 medio / 15 alto / 7 crítico) pese al
  corte — confirma que el caché de `localStorage` sostiene la vista aunque el backend esté caído, tal como
  describe A15/V10 en el backlog.
- Se desregistró el service worker y se recargó: la app volvió a pedir datos reales (temperatura pasó de
  16°C a 17°C real, confirmando que fue un pedido nuevo y no un dato repetido) y el banner desapareció solo,
  sin acción manual adicional.

### 5. Activar modo viaje y mostrar progreso continuo, ETA y salida

**Tiempo**: "Iniciar viaje" → tarjeta de maniobra visible en ~1-1,5s. Mostró maniobra real ("Doblá a la
derecha en Calle Rodriguez Peña", "LUEGO: Doblá a la izquierda en Calle Lavalle"), resumen "7 min · 1.7 km"
y botón "Salir" funcional (volvió a la vista de ruta normal). **Límite declarado, no nuevo**: sin GPS real
de dispositivo en este entorno no se pudo ver el progreso avanzar de verdad sobre una traza en movimiento
(A16 ya lo tiene pendiente); para la demo real con Rodo caminando/en moto esto sí se vería completo.

### 6. Cerrar con límites: gravedad condicionada, datos históricos CABA y fuentes recientes imperfectas

Paso narrativo, no una acción en la app — texto para decir en la demo, tomado literal de lo ya documentado
y vigente (no inventado para este cierre):

- *Gravedad condicionada*: "el contrato y las etiquetas de interfaz dejan explícita la gravedad condicionada
  a un siniestro" (A01, `BACKLOG.md`) — el sistema no predice si un siniestro va a ocurrir, solo qué tan
  grave tiende a ser *dado que* ocurre.
- *Datos históricos CABA*: "Datos históricos de CABA; no cobertura validada de todo GBA" (fila "Mapear
  contexto vial" de este mismo documento de matriz).
- *Fuentes recientes imperfectas*: "Scraper sin medición humana aún; reportes no son verificación oficial"
  (misma matriz) — y, con más detalle real si hace falta, la medición de precisión de A09 (0,84 precisión
  temática, 0,923 recall sobre 105 casos con juicio experto, evidencia en
  `docs/evidencias/2026-09-13/A09/`).

## Conclusión

Los 6 pasos del guion existente se ejecutaron tal cual están escritos contra el stack real, con servicios
externos reales (Nominatim, TomTom, clima) respondiendo en vivo. El paso 4 se verificó con un fallo real
simulado a nivel de red (no mockeado en React): el caché sostiene la vista y el reintento recupera sin
intervención manual más allá del botón. No se encontró ningún comportamiento roto o inesperado en esta
corrida. Falta, como ya dice el guion, el ensayo con Rodo narrando en vivo y cronometrando su propia
exposición — esto fue la verificación técnica de que cada paso *funciona*, no un ensayo de oratoria.
