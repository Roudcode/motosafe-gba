# Mapa categorizado de pendientes — MotoSafe GBA

Reorganiza el contenido de `BACKLOG.md` (65 ítems en total, letras A/V/F/D/T/G) por área funcional real en vez de por el prefijo de letra, para decidir qué atacar antes de la entrega final. No agrega información nueva: cada estado viene tal cual figura hoy en `BACKLOG.md` (tabla "Ejecución actual", releída entera para esta regeneración). Se regenera a mano cuando cambie el backlog; no se mantiene en paralelo de forma automática. **Regenerado 2026-10-21 (SES-153)**: la versión anterior se había quedado en el estado de antes de SES-148 (T02 como "En curso", A20/A21/A05/V10 sin cerrar, D05 sin existir todavía).

Resumen numérico: de 65 ítems, **17 están Validado, 24 Validado parcialmente, 2 En curso y 22 No iniciado**. Los 22 no iniciados son casi todos del catálogo de diseño (V) y funciones nuevas (F) planteado al inicio del proyecto, no del núcleo que sostiene la tesis. Categorización hallazgo/oportunidad: A, D y T son hallazgos de la auditoría original; V y F son oportunidades/mejoras de producto; G es mixto (gestión académica, con piezas de ambos tipos) — mismo criterio ya usado en versiones anteriores de este documento.

---

## 1. Core — modelo y datos

La ciencia de datos de fondo: qué predice el sistema, con qué calidad, y de dónde salen los datos.

**Validado:** A01 (definición de gravedad vs. ocurrencia), A02 (evaluación temporal independiente), A04 (calibración y costos de falsas alertas), A10 (actualización de riesgo), A11 (procedencia e incertidumbre mostradas), A24 (confianza por zona frente al reentrenamiento).

**Validado parcialmente:**
- A03 (ablaciones edad/sexo) — medido y con una decisión real pendiente (DEC-022): sacar el sexo de la víctima como variable resuelve la inestabilidad entre años pero empeora las clases graves/mortales en el año más reciente. Te toca decidir.
- A09 (calidad del extractor de prensa) — falta el conjunto etiquetado para validar calles/intersecciones. Ya se exportó la muestra real (`docs/evidencias/2026-10-21/A09-muestra-etiquetado/`); el paso que sigue es que la etiquetes vos.
- D01 (fichas de dataset/modelo) — cerrado el diccionario de datos del publicador (confirmado que no existe) y los términos de Open-Meteo; TomTom sigue sin una frase explícita sobre el plan gratuito.
- D02 (estabilidad por año — causa ya identificada, mismo DEC-022 de arriba), D03 (rutas de referencia — 4 casos reales generados, falta tu revisión de criterio), D04 (sensibilidad de pesos/clustering — medido, sin decisión de ajuste todavía).
- A20 (limpieza geográfica común) — criterio unificado (`notebooks/limpieza_geografica_comun.py`), aplicado sin efecto real a siniestros y medido (sin aplicar) sobre delitos: 12 coordenadas rotas y ~12.500 duplicados exactos que hoy nadie filtra, queda tu decisión de aplicarlo.
- A21 (validar corredores y estabilidad espacial) — procedencia trazada, estabilidad espacial medida: los puntos que definen cada corredor son 100% deterministas, la polilínea de OSRM no lo es (límite de un tercero, no del pipeline).
- D05 (monitor de cambios en calidad de datos) — nuevo (`notebooks/monitor_calidad_datos.py`), corre antes de `promover_artefactos.py --confirmar`, verificado con datos reales regenerados y con un candidato alterado a propósito. Es solo un reporte, no bloquea nada.

**No iniciado:**
- D06 (ampliar cobertura GBA con fuentes comparables) — P3/L, disponibilidad de fuentes sin confirmar.

---

## 2. Lógica de negocio (backend / aplicación)

Reglas de la aplicación en sí: sesión, reportes, capas, rutas, migraciones.

**Validado:** A05 (cobertura del comparador — validación geográfica independiente real: una ruta en GBA profundo dio 0% de cobertura sin ningún badge de seguridad disfrazado, una ruta límite CABA/GBA dio cobertura intermedia real sin diluirse), A07 (borrado y protección de votos), A08 (escape de títulos externos), A12 (pool de conexiones y recuperación SQL), A13 (validación de entradas), A15 (carga/error/recuperación de capas — ya no queda nada pendiente de código), A18 (búsqueda compatible con proveedor), F08 (reportes con estado y gestión propios).

**Validado parcialmente:** A06 (dedup de capas y rankings), A14 (migraciones/consultas/cuotas), A16 (velocidad/ETA/progreso), A19 (pipeline canónico y notebook histórico seguro — los 3 pasos de red corridos contra servicios reales), A22 (entorno y artefactos reproducibles — CI confirmado en GitHub), A23 (accesibilidad y persistencia).

Nada en esta categoría está sin empezar.

---

## 3. Base de datos e infraestructura

**Validado:** T02 (E2E visual completo — el hallazgo de teclado del buscador se corrigió de verdad y se confirmó en navegador real, en desktop y 375px; no quedan pendientes de código conocidos, salvo repetir el resto de los 6 flujos a 375px, una nota menor).

**Validado parcialmente:** T01 (integración real con base efímera — conjunto mínimo real de permisos de un rol sin privilegios de dueño, encontrado iterando fallos reales), T03 (presupuesto de rendimiento móvil — primera línea base real medida, objetivo propuesto a partir de la medición), T04 (observabilidad sin datos personales — historial con retención real), T05 (integración continua — primera corrida de CI en GitHub confirmada limpia), T06 (backup y restauración — ensayado con la composición real de producción y un volumen Docker nombrado persistente, en local; falta un proveedor de hosting real, que genuinamente no existe todavía).

**No iniciado:** ninguno.

---

## 4. Arquitectura de código (frontend)

**En curso:** A17 (separar `App.jsx`) — las extracciones de JSX ya están hechas (2140→1959 líneas); lo que queda (los `useEffect` que calculan velocidad/ETA durante la navegación) es trabajo de otro tipo, nunca estuvo en el alcance original. Prácticamente cerrado.

---

## 5. Diseño y UX

**Validado:** V08 (panel de capas simplificado, QA visual real hecha), V10 (estados vacíos y errores con acción útil — cerrado el último hueco: aviso específico para una capa que responde 200 con lista vacía, distinto del aviso de fallo, verificado con tests de componente y en pantalla real).

**No iniciado (12 de 14 ítems del catálogo):** V01 (jerarquía explorar/comparar/navegar), V02 (unificar tamaños/espaciado/sombras), V03 (tipografía y legibilidad), V04 (colores más semánticos), V05 (panel inferior móvil), V06 (tarjetas de rutas comparables), V07 (detalle de zona progresivo), V09 (atenuar decoración durante viaje), V11 (contraste sobre mapas claros/satélite), V12 (onboarding breve), V13 (marcadores diferenciados), V14 (pulir estados táctiles). Todos P2 o P3 -- ninguno bloquea la entrega, pero sigue siendo la categoría con más ítems sin tocar. **A pedido explícito de Rodo, nada de esta lista se toca sin que él lo pida primero.**

---

## 6. Funciones nuevas (features)

**Validado:** F08 (ya contado en lógica de negocio, también es una feature).

**No iniciado (9 de 10 ítems):** F01 (preferencias tiempo vs. exposición), F02 (favoritos con nombres propios), F03 (recientes locales), F04 (explicar por qué cambia una ruta), F05 (preferencias de alertas), F06 (guía por voz), F07 (pantalla activa durante navegación), F09 (modo degradado sin red), F10 (compartir resumen de ruta). Mezcla de P2 y P3 -- ninguno es requisito de la cátedra, son mejoras de producto. **Mismo criterio que V: no se tocan salvo pedido explícito.**

---

## 7. Gestión académica / tesis

**Validado parcialmente:** G01 (sincronizar guías, README y Word — `docs/README.md`/`BACKLOG.md`/`CONTINUIDAD.md` sincronizados con el estado real; el Word de la tesis queda fuera, lo revisa Rodo directo), G02 (validación con usuarios — falta ampliar la muestra de 12 y variar el canal de reclutamiento), G03 (matriz objetivos–evidencias — falta contrastar con requisitos institucionales que no están en el repo), G04 (demo reproducible — ensayo real cronometrado ya corrido contra servicios reales, incluido un fallo de capa simulado de verdad).

**En curso:** G05 (actas con el tutor) — de baja prioridad real: el tutor no pide un registro formal.

**No iniciado:** ninguno.

---

## Lectura para decidir qué sigue

Los 22 ítems "No iniciado" son, en su enorme mayoría (21 de 22), diseño (V) y funciones nuevas (F): el catálogo de mejoras de producto planteado al arrancar el proyecto, no material que la cátedra pida para aprobar. Nada de esa categoría bloquea la entrega. Lo que sí queda más cerca de bloquear o de pesar en la nota son, en orden de impacto real:

1. **A09** — conjunto etiquetado para validar calles/intersecciones (ya exportada la muestra real; el paso que sigue es tu revisión).
2. **D03** — revisión de criterio de los 4 casos reales de ruta que ya se generaron.
3. **G02/G03/G04** — cerrar lo que depende de vos (ampliar muestra de usuarios, requisitos institucionales; G04 ya tiene el ensayo real corrido, falta tu revisión).
4. **A20/A06 (DEC vinculado a `UMBRAL_CRUCE_KM`)** — decisión sobre si ajustar el umbral de cruce a la luz de lo medido en D04/A20.
5. **DEC-022** (D02/A03) — tu decisión sobre sacar o no el sexo de la víctima como variable del modelo.

Si alguno de los 22 "No iniciado" te importa para la entrega final igual, decímelo y lo subimos de prioridad acá; si no, vale la pena dejarlo explícitamente fuera de alcance (con una línea en `DECISIONES.md`, mismo criterio que ya usamos para otros recortes) en vez de que quede flotando como deuda sin decidir.
