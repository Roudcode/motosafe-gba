# Mapa categorizado de pendientes — MotoSafe GBA

Reorganiza el contenido de `BACKLOG.md` (65 ítems en total, letras A/V/F/D/T/G) por área funcional real en vez de por el prefijo de letra, para decidir qué atacar antes de la entrega final. No agrega información nueva: cada estado viene tal cual figura hoy en `BACKLOG.md`. Se regenera a mano cuando cambie el backlog; no se mantiene en paralelo de forma automática.

Resumen numérico: de 65 ítems, 17 están **Validado**, 22 **Validado parcialmente**, 3 **En curso** y 27 **No iniciado**. Los 27 no iniciados son casi todos del catálogo de diseño (V) y funciones nuevas (F) planteado al inicio del proyecto, no del núcleo que sostiene la tesis.

---

## 1. Core — modelo y datos

La ciencia de datos de fondo: qué predice el sistema, con qué calidad, y de dónde salen los datos.

**Validado:** A01 (definición de gravedad vs. ocurrencia), A02 (evaluación temporal independiente), A04 (calibración y costos de falsas alertas), A10 (actualización de riesgo), A11 (procedencia e incertidumbre mostradas), A24 (confianza por zona frente al reentrenamiento).

**Validado parcialmente:**
- A03 (ablaciones edad/sexo) — medido y con una decisión real pendiente (DEC-022): sacar el sexo de la víctima como variable resuelve la inestabilidad entre años pero empeora las clases graves/mortales en el año más reciente. Te toca decidir.
- A09 (calidad del extractor de prensa) — falta el conjunto etiquetado para validar calles/intersecciones. Es el único pendiente de A09 que sigue sin un plan concreto.
- D01 (fichas de dataset/modelo), D02 (estabilidad por año — causa ya identificada, mismo DEC-022 de arriba), D03 (rutas de referencia — 4 casos reales generados, falta tu revisión de criterio), D04 (sensibilidad de pesos/clustering — medido, sin decisión de ajuste todavía).

**No iniciado:**
- A20 (limpieza geográfica común entre algoritmos) — P2/M.
- A21 (validar corredores y estabilidad espacial) — P2/L, depende de A20.
- D05 (monitor de cambios en calidad de datos) — P3/M.
- D06 (ampliar cobertura GBA con fuentes comparables) — P3/L, disponibilidad de fuentes sin confirmar.

---

## 2. Lógica de negocio (backend / aplicación)

Reglas de la aplicación en sí: sesión, reportes, capas, rutas, migraciones.

**Validado:** A07 (borrado y protección de votos), A08 (escape de títulos externos), A12 (pool de conexiones y recuperación SQL), A13 (validación de entradas), A18 (búsqueda compatible con proveedor), F08 (reportes con estado y gestión propios).

**Validado parcialmente:** A05 (cobertura del comparador), A06 (dedup de capas y rankings), A14 (migraciones/consultas/cuotas), A15 (carga/error/recuperación de capas), A16 (velocidad/ETA/progreso), A19 (pipeline canónico y notebook histórico seguro), A22 (entorno y artefactos reproducibles), A23 (accesibilidad y persistencia).

Nada en esta categoría está sin empezar.

---

## 3. Base de datos e infraestructura

**Validado parcialmente:** T01 (integración real con base efímera), T04 (observabilidad sin datos personales), T05 (integración continua), T06 (backup y restauración ensayada).

**En curso:** T02 (E2E visual completo) — justo lo que le acabamos de pedir a Codex (modo dev, flujos en pantalla, móvil, teclado).

**No iniciado:** T03 (presupuesto de rendimiento móvil) — P2/M, depende de A17.

---

## 4. Arquitectura de código (frontend)

**En curso:** A17 (separar `App.jsx`) — las diez extracciones de JSX ya están hechas (2140→1959 líneas); lo que queda (los `useEffect` que calculan velocidad/ETA durante la navegación) es trabajo de otro tipo, nunca estuvo en el alcance original. Prácticamente cerrado.

---

## 5. Diseño y UX

**Validado:** V08 (panel de capas simplificado, QA visual real hecha).

**Validado parcialmente:** V10 (estados vacíos y errores con acción útil).

**No iniciado (12 de 14 ítems del catálogo):** V01 (jerarquía explorar/comparar/navegar), V02 (unificar tamaños/espaciado/sombras), V03 (tipografía y legibilidad), V04 (colores más semánticos), V05 (panel inferior móvil), V06 (tarjetas de rutas comparables), V07 (detalle de zona progresivo), V09 (atenuar decoración durante viaje), V11 (contraste sobre mapas claros/satélite), V12 (onboarding breve), V13 (marcadores diferenciados), V14 (pulir estados táctiles). Todos P2 o P3 -- ninguno bloquea la entrega, pero es la categoría con más ítems sin tocar.

---

## 6. Funciones nuevas (features)

**Validado:** F08 (ya contado en lógica de negocio, también es una feature).

**No iniciado (9 de 10 ítems):** F01 (preferencias tiempo vs. exposición), F02 (favoritos con nombres propios), F03 (recientes locales), F04 (explicar por qué cambia una ruta), F05 (preferencias de alertas), F06 (guía por voz), F07 (pantalla activa durante navegación), F09 (modo degradado sin red), F10 (compartir resumen de ruta). Mezcla de P2 y P3 -- ninguno es requisito de la cátedra, son mejoras de producto.

---

## 7. Gestión académica / tesis

**Validado parcialmente:** G02 (validación con usuarios — falta ampliar la muestra de 12 y variar el canal de reclutamiento), G03 (matriz objetivos–evidencias — falta contrastar con requisitos institucionales que no están en el repo), G04 (demo reproducible — falta el ensayo medido con los servicios realmente disponibles).

**En curso:** G05 (actas con el tutor) — de baja prioridad real: el tutor no pide un registro formal.

**No iniciado:** G01 (sincronizar guías, README y el Word de la tesis) — P2/M.

---

## Lectura para decidir qué sigue

Los 27 ítems "No iniciado" son, en su enorme mayoría (21 de 27), diseño (V) y funciones nuevas (F): el catálogo de mejoras de producto planteado al arrancar el proyecto, no material que la cátedra pida para aprobar. Nada de esa categoría bloquea la entrega. Lo que sí queda más cerca de bloquear o de pesar en la nota son, en orden de impacto real:

1. **A09** — conjunto etiquetado para validar calles/intersecciones (ya ofrecido: armarte una planilla corta de notas reales para etiquetar).
2. **G01** — sincronizar guías/README/Word con el estado real del proyecto, para que la documentación de entrega no quede desactualizada.
3. **G03/G04** — cerrar lo que depende de vos (requisitos institucionales, ensayo de demo).
4. **T02** — en curso con Codex ahora mismo.
5. **DEC-022** (D02/A03) — tu decisión sobre sacar o no el sexo de la víctima como variable del modelo.

Si alguno de los 27 "No iniciado" te importa para la entrega final igual, decímelo y lo subimos de prioridad acá; si no, vale la pena dejarlo explícitamente fuera de alcance (con una línea en `DECISIONES.md`, mismo criterio que ya usamos para otros recortes) en vez de que quede flotando como deuda sin decidir.
