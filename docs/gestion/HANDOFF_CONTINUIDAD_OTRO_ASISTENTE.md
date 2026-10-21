# MotoSafe GBA — Estado completo del proyecto al 21/10/2026, para continuar con otro asistente

Este documento es un traspaso de contexto completo. Está pensado para pegarlo o subirlo a ChatGPT (u otro asistente) y que pueda seguir trabajando en el proyecto con el mismo nivel de rigor que se viene usando, hasta que vuelvas a tener tokens de Claude disponibles. Contiene: qué es el proyecto, cómo está el repo, qué se hizo en la última sesión larga, qué decisiones quedan pendientes de tu parte, y — más importante — las reglas de trabajo que hay que respetar para no romper la disciplina que sostiene todo el informe de tesis.

Si estás arrancando una sesión nueva con esto: pegá el documento completo como primer mensaje, decile al asistente que lea `docs/gestion/BACKLOG.md`, `docs/gestion/DECISIONES.md`, `docs/gestion/BITACORA.md` y `docs/gestion/MAPA_PENDIENTES.md` del repo antes de tocar nada, y que no asuma nada que no esté confirmado en esos archivos o en el código real.

---

## 1. Qué es el proyecto

MotoSafe GBA es el Proyecto Final de Ingeniería Informática (USAL) de Rodolfo Barrionuevo: un sistema de análisis y visualización de riesgo vial para motociclistas en el Gran Buenos Aires. Combina:

- **Backend** en FastAPI + PostgreSQL/PostGIS, con un modelo Random Forest entrenado sobre datos reales de siniestros (dataset oficial GCBA 2019-2025) que sirve predicciones de nivel de riesgo por zona (`/hotspots`) y por ruta.
- Capas adicionales de datos reales: delitos (GCBA), clima (Open-Meteo), prensa (scraping propio de notas de robos/choques con geocodificación), corredores de siniestralidad (clustering sobre siniestros de moto).
- **Frontend** en React + Leaflet: mapa con heatmap/hexágonos de riesgo, comparador de rutas (TomTom con tráfico en vivo), reporte colaborativo de incidentes, modo navegación/viaje.
- Toda la infraestructura corre en Docker Compose (desarrollo local de Rodo) y hay un despliegue documentado para producción (Render).

El trabajo entero se rige por una regla de fondo no negociable: **nada se declara hecho sin evidencia real verificada** (corridas reales contra el backend real, datos reales, tests reales pasando). Nunca se fabrica un resultado ni se asume que algo funciona sin probarlo. Esta disciplina es la columna vertebral de todo el proyecto y de la tesis — perderla rompe la credibilidad del trabajo completo.

## 2. Cómo está organizado el repo (lo que importa para gestión)

Carpeta `docs/gestion/` — el corazón del seguimiento:

- **`BACKLOG.md`**: lista única de 65 ítems (prefijos A=análisis/core, V=diseño/UX, F=funciones nuevas, D=datos/modelo, T=infraestructura/testing, G=gestión académica), cada uno con estado (`Validado` / `Validado parcialmente` / `En curso` / `No iniciado` / diferido / descartado) y la evidencia real que lo respalda, con links a `docs/evidencias/<fecha>/<ítem>/`.
- **`DECISIONES.md`**: registro formal de decisiones (DEC-001 a DEC-022 al momento de escribir esto), con plantilla fija (problema, opciones, decisión y motivo, evidencia, efectos/límites, qué queda pendiente). Cuando algo requiere tu criterio y no se puede resolver con más evidencia, se deja ahí como "pendiente de decisión de Rodo", **nunca se decide unilateralmente** si cambia el comportamiento del sistema en producción.
- **`BITACORA.md`**: diario de sesiones (SES-001 a SES-146 al momento de escribir esto), cada entrada documenta qué se hizo, qué se verificó y cómo.
- **`MAPA_PENDIENTES.md`** (nuevo, creado esta sesión): reorganiza los 65 ítems del backlog por área funcional real (core/modelo, lógica de negocio, base de datos/infraestructura, arquitectura frontend, diseño/UX, funciones nuevas, gestión académica) en vez de por prefijo de letra — pensado para decidir qué atacar a continuación.
- **`CONTINUIDAD.md`, `ACTAS_TUTOR.md`, `VALIDACION.md`, `PRIORIZACION.md`**: documentos de apoyo, menos centrales.

Carpeta `docs/tesis/`: los capítulos de la tesis en `.docx`. Capítulos 1 a 6 en `MotoSafe_GBA_Capitulos_1_a_6.docx`, Capítulo 7 (`..._Capitulo_7_Presentacion_de_resultados.docx`) y Capítulo 8 (`..._Capitulo_8_Implicancias_Conclusiones_y_Recomendaciones.docx`) como archivos separados.

Carpeta `docs/evidencias/<fecha>/<item>/`: toda la evidencia real (CSVs, scripts, READMEs/RESULTADOS.md) que respalda cada actualización de BACKLOG.md. Si algo no tiene su carpeta de evidencia correspondiente, no está verificado.

## 3. Resumen numérico del backlog (65 ítems, al 21/10/2026)

- **17 Validado**
- **22 Validado parcialmente**
- **3 En curso** (T02, A17, G05)
- **27 No iniciado** — de estos, 21 son del catálogo de diseño/UX (V) y funciones nuevas (F), planteado al inicio del proyecto como mejoras de producto. Ninguno bloquea la entrega académica. El resto son D05/D06 (core) y G01/T03 (infra/gestión).

Lo que realmente pesa para la entrega, en orden de impacto (según el cierre de `MAPA_PENDIENTES.md`):

1. **A09** — falta el conjunto etiquetado para validar calles/intersecciones del extractor de prensa. Ya se exportó la muestra real (ver sección 5) — el paso que sigue es que vos la etiquetes.
2. **G01** — sincronizar guías/README/Word de la tesis con el estado real del proyecto (no iniciado).
3. **G03/G04** — G04 (ensayo cronometrado de demo) ya se corrió esta sesión; G03 (matriz objetivos-evidencias contra requisitos institucionales) sigue dependiendo de vos.
4. **T02** — en curso, con un hallazgo real de accesibilidad por teclado (ver sección 4).
5. **DEC-022** — tu decisión sobre sacar o no `sexo_victima` como variable del modelo (ver sección 6).

## 4. Qué se hizo en la última sesión larga (21/10/2026) — todo esto ya está commiteado

Commits de esta sesión, en orden (`git log` real):

```
98f18e9  Leyenda de nivel de riesgo colapsable + buscador reducido a una lupa (SES-141)
b4c122b  Mueve el disparador de búsqueda a la topbar (SES-141)
a243061  Cap 7: agrega los resultados reales del comparador de rutas (SES-142)
4839365  D02: identifica causalmente la fuente de la inestabilidad temporal (SES-143)
44f5a39  Cap 8: cierra el pendiente de completitud por año de D02 (SES-144)
5c2e77d  Confirma verificación visual en vivo de la leyenda colapsable y el buscador en topbar (SES-145)
cc290b8  Agrega mapa categorizado de pendientes por area funcional
4f500ae  Verificación independiente de corrida T02/G04/A09: E2E visual real, ensayo cronometrado de demo y muestra real de prensa para etiquetado (SES-146)
```

**UI (frontend)**: la leyenda "Nivel de riesgo" ahora es colapsable (botón con flecha, estado persistido en `localStorage`), y el buscador se movió de estar siempre visible a un botón en la topbar junto a los otros íconos (tema/capas/actividad) que lo abre/cierra. Verificado en pantalla real y en mobile por Rodo, confirmado OK.

**Tesis — Capítulo 7**: se agregó la sección 7.6 "Resultados del comparador de rutas" con los 4 casos reales (D03) y el análisis de sensibilidad (D04), renumerando la síntesis final a 7.7.

**Tesis — Capítulo 8**: se actualizó el párrafo de la sección 8.3 que hablaba de "seguir la pista de completitud por año" (D02) con el hallazgo causal real, explicado en prosa sin jerga sin explicar.

**D02 (estabilidad temporal del modelo) — hallazgo causal**: se confirmó que `sexo_victima` es la causa de la inestabilidad entre splits temporales (no solo correlación). Sacarla como feature casi cierra la brecha entre años, pero empeora GRAVE y MORTAL en el split más reciente. Esto generó **DEC-022**, pendiente de tu decisión (ver sección 6).

**`MAPA_PENDIENTES.md`**: remapeo completo de los 65 ítems por área funcional, a pedido tuyo.

**T02/G04/A09 encadenados (vía Codex, verificado independientemente por Claude antes de commitear)**:

- **T02**: los 5 flujos centrales (zona de riesgo, buscar lugar, trazar ruta, reportar, modo viaje) funcionan de punta a punta en desktop y 375px contra el stack real. **Hallazgo real confirmado dos veces con `document.activeElement`**: la lista de resultados del buscador se desmonta en cuanto el foco sale del campo de texto, así que no es alcanzable por `Tab`/`ArrowDown` — bloquea "buscar un lugar" para quien usa solo teclado. No está arreglado, solo documentado — es un bug real pendiente.
- **G04**: los 6 pasos del guion de demo (`docs/entrega/MATRIZ_ACADEMICA_Y_DEMO.md`) corridos de punta a punta contra servicios reales (Nominatim, TomTom con tráfico, clima), cronometrados. El paso de "simular fallo de capa" cortó `/api/hotspots` a nivel de red real (con un service worker de prueba, borrado al terminar) sin tocar el backend que ya estaba corriendo — confirmado el banner de reintento, el caché sosteniendo el mapa, y la recuperación real al reconectar.
- **A09**: exportada una muestra real de 50 notas de prensa (36 de nivel calle/intersección completas + 14 de barrio sorteadas al azar con semilla fija, sin curar) a `docs/evidencias/2026-10-21/A09-muestra-etiquetado/muestra_calles.csv`, con título, descripción completa y la ubicación que extrae el sistema hoy. Es solo exportación — el análisis de precisión te queda a vos (ver sección 5).

Verificación que yo (Claude) hice antes de commitear, no solo el self-report de Codex: re-corrí la suite de tests del frontend (`node node_modules/vitest/vitest.mjs run` → **93/93 en verde**), `eslint src/` limpio, `git status` confirmando que no se tocó código de producción, y cada afirmación de los tres `RESULTADOS.md`/`README.md` cruzada contra el CSV real y el diff real de `BACKLOG.md`/`BITACORA.md`.

## 5. Lo que te queda pendiente a VOS (no al asistente)

1. **Etiquetar la muestra de A09** (`docs/evidencias/2026-10-21/A09-muestra-etiquetado/muestra_calles.csv`, 50 filas): para cada nota, juzgar si `query_extraida` (lo que el sistema extrajo como ubicación) es correcto contra el texto real de la noticia. Esto cierra el único pendiente de A09 que no tiene plan todavía (validación de calles/intersecciones sin conjunto etiquetado, abierto desde SES-073).
2. **DEC-022**: decidir si (A) dejás `sexo_victima` como está en el modelo productivo, (B) la sacás, o (C) pedís explorar una variante intermedia (categoría "sin dato" explícita en vez de sacar la variable entera) antes de elegir entre A y B. El trade-off real: sacarla cierra la brecha entre años (F1 macro 0,288→0,365 en el split más débil) pero empeora GRAVE (0,209→0,089) y MORTAL (0,110→0,079) en el split más reciente.
3. **D04**: decidir si conviene ajustar `UMBRAL_CRUCE_KM` del comparador de rutas a la luz de la sensibilidad medida (varía la cobertura y en un caso cambia cuál ruta aparece como de menor riesgo).
4. **D03**: revisar con tu propio criterio si los 4 casos reales de ruta generados "están bien" — quien generó los datos (el agente) explícitamente no evaluó eso.
5. **El bug de accesibilidad por teclado en el buscador** (hallazgo de T02): decidir si se arregla ahora o se prioriza después. Es un bug real, chico en alcance (vive en `frontend/src/components/SearchBar.jsx`, el patrón `onBlur` + `setTimeout(150)` que desmonta la lista de sugerencias sin importar adónde fue el foco), pero nadie lo arregló todavía.
6. **Los 27 ítems "No iniciado"** del backlog (mayormente V/diseño y F/funciones nuevas): decidir si alguno te importa para la entrega final o si se deja explícitamente fuera de alcance con una línea en `DECISIONES.md` (mismo criterio ya usado para otros recortes), en vez de dejarlos flotando como deuda sin decidir.

## 6. Reglas de trabajo — leer antes de seguir con cualquier asistente

Estas reglas sostienen la credibilidad de todo el proyecto. Cualquier asistente que continúe (ChatGPT incluido) debería seguirlas:

- **Nunca fabricar resultados.** Si algo no se pudo probar, se documenta explícitamente como "no verificado", nunca se inventa un resultado plausible. Esto se aplicó literalmente en cada sesión (ver BITACORA.md) y es la regla más importante de todas.
- **Verificar antes de confiar en un self-report.** Cuando otra herramienta/agente (Codex, u otro asistente) dice "ya lo hice, 93/93 tests en verde", hay que correr los tests de nuevo, leer el diff real, cruzar contra los archivos de evidencia — nunca aceptar el reporte tal cual. Esta sesión se hizo exactamente así con el lote T02/G04/A09 antes de commitear.
- **Las decisiones que cambian el modelo o el comportamiento productivo nunca se toman solas.** Si una medición abre una disyuntiva real (ejemplo: DEC-022), se documenta con números reales y se deja pendiente de tu decisión explícita en `DECISIONES.md`, nunca se resuelve unilateralmente.
- **Nunca pasar ni tipear tu contraseña real** en ningún chat, de ningún asistente. Si una tarea necesita tu sesión autenticada contra el backend real, entrás vos mismo en la pantalla de login.
- **Estilo de la tesis** (ya aplicado en todos los capítulos existentes): sin fechas puntuales en la prosa, sin códigos internos de seguimiento (A09, DEC-022, SES-146, etc. — eso se explica en lenguaje llano), con la jerga técnica explicada la primera vez que aparece sin volverse un manual, documentos que no crecen de más, y contexto autocontenido para un lector que no conoce el sistema de seguimiento interno.
- **Principio de versionado del informe** (DEC-016): los capítulos de tesis y documentos de gestión se mantienen al día — cuando un avance deja desactualizado un capítulo anterior, se corrige directamente en el texto, sin nota de versión fechada. Lo que preserva la historia es la bitácora, no el capítulo.
- **Para cambiar `BACKLOG.md`**: solo pasa a "Validado" cuando no queda nada pendiente de código ni de decisión para ese ítem; "Validado parcialmente" si queda algo real sin cerrar.
- **Convención de commits de este repo**: mensajes descriptivos en español, sin emojis, con el detalle real de qué se verificó (no solo qué se hizo).

## 7. Cómo retomar con otro asistente (ChatGPT u otro)

1. Dale este documento completo como contexto inicial.
2. Pedile que lea (si tiene acceso al repo) `docs/gestion/BACKLOG.md`, `docs/gestion/DECISIONES.md` (al menos las últimas 5-6 decisiones), `docs/gestion/MAPA_PENDIENTES.md` completo y las últimas 10-15 entradas de `docs/gestion/BITACORA.md` antes de proponer cualquier paso.
3. Si no tiene acceso directo al repo (por ejemplo, estás en el chat web de ChatGPT sin conexión a tus archivos), subile los archivos de `docs/gestion/` y los capítulos de tesis que correspondan a lo que vayas a trabajar.
4. Priorizá, según la lista de la sección 5, qué querés resolver primero — lo más barato y de mayor impacto es etiquetar la muestra de A09 (es trabajo tuyo de lectura, no de código) y decidir DEC-022 (es una decisión, no una tarea técnica).
5. Cuando vuelvas a Claude con tokens disponibles, contale qué avanzaste con el otro asistente (qué decisiones tomaste, qué código cambió si cambió algo) para que se pueda verificar y seguir la misma disciplina de siempre.

## 8. Dónde está todo (rutas reales en el repo)

- Backlog: `docs/gestion/BACKLOG.md`
- Decisiones: `docs/gestion/DECISIONES.md`
- Bitácora: `docs/gestion/BITACORA.md`
- Mapa de pendientes por área: `docs/gestion/MAPA_PENDIENTES.md`
- Muestra de A09 para etiquetar: `docs/evidencias/2026-10-21/A09-muestra-etiquetado/muestra_calles.csv` (y su `README.md`)
- Evidencia D02/causalidad: `docs/evidencias/2026-10-21/D02-completitud/README.md`
- Evidencia D04/sensibilidad: `docs/evidencias/2026-10-21/D04/`
- Evidencia T02 (E2E visual + bug de teclado): `docs/evidencias/2026-10-21/T02-E2E-visual/RESULTADOS.md`
- Evidencia G04 (ensayo de demo): `docs/evidencias/2026-10-21/G04-ensayo-demo/RESULTADOS.md`
- Capítulos de tesis: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_6.docx`, `..._Capitulo_7_Presentacion_de_resultados.docx`, `..._Capitulo_8_Implicancias_Conclusiones_y_Recomendaciones.docx`
- Guion de demo: `docs/entrega/MATRIZ_ACADEMICA_Y_DEMO.md`

---

*Último commit al momento de escribir esto: `4f500ae`. Todo lo descripto en la sección 4 ya está commiteado en el repo (nada pendiente de commitear de esta sesión).*
