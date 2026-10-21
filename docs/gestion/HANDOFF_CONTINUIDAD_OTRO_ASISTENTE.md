# MotoSafe GBA — Estado completo del proyecto al 21/10/2026, para continuar con otro asistente

Este documento es un traspaso de contexto completo. Está pensado para pegarlo o subirlo a ChatGPT (u otro asistente) y que pueda seguir trabajando en el proyecto con el mismo nivel de rigor que se viene usando, hasta que vuelvas a tener tokens de Claude disponibles. Contiene: qué es el proyecto, cómo está el repo, qué se hizo en la última sesión larga, qué decisiones quedan pendientes de tu parte, y — más importante — las reglas de trabajo que hay que respetar para no romper la disciplina que sostiene todo el informe de tesis.

Si estás arrancando una sesión nueva con esto: pegá el documento completo como primer mensaje, decile al asistente que lea `docs/gestion/BACKLOG.md`, `docs/gestion/DECISIONES.md`, `docs/gestion/BITACORA.md` y `docs/gestion/MAPA_PENDIENTES.md` del repo antes de tocar nada, y que no asuma nada que no esté confirmado en esos archivos o en el código real.

**Regenerado 2026-10-21 (SES-153)**: la versión anterior había quedado parada en SES-147 (23/10 commits atrás); esta reescribe las cifras y el estado contra `BACKLOG.md` y `git log` reales de hoy, no copiados de la versión anterior.

---

## 1. Qué es el proyecto

MotoSafe GBA es el Proyecto Final de Ingeniería Informática (USAL) de Rodolfo Barrionuevo: un sistema de análisis y visualización de riesgo vial para motociclistas en el Gran Buenos Aires. Combina:

- **Backend** en FastAPI + PostgreSQL/PostGIS, con un modelo Random Forest entrenado sobre datos reales de siniestros (dataset oficial GCBA 2019-2025) que sirve predicciones de nivel de riesgo por zona (`/hotspots`) y por ruta.
- Capas adicionales de datos reales: delitos (GCBA), clima (Open-Meteo), prensa (scraping propio de notas de robos/choques con geocodificación), corredores de siniestralidad (clustering sobre siniestros de moto).
- **Frontend** en React + MapLibre GL: mapa con heatmap/hexágonos de riesgo, comparador de rutas (TomTom con tráfico en vivo), reporte colaborativo de incidentes, modo navegación/viaje.
- Toda la infraestructura corre en Docker Compose (desarrollo local de Rodo) y hay un despliegue documentado para producción (Render), **sin ningún servicio público desplegado todavía** (confirmado en SES-151: no hay cuenta ni despliegue real en ningún proveedor de hosting).

El trabajo entero se rige por una regla de fondo no negociable: **nada se declara hecho sin evidencia real verificada** (corridas reales contra el backend real, datos reales, tests reales pasando). Nunca se fabrica un resultado ni se asume que algo funciona sin probarlo. Esta disciplina es la columna vertebral de todo el proyecto y de la tesis — perderla rompe la credibilidad del trabajo completo.

## 2. Cómo está organizado el repo (lo que importa para gestión)

Carpeta `docs/gestion/` — el corazón del seguimiento:

- **`BACKLOG.md`**: lista única de 65 ítems (prefijos A=análisis/core, V=diseño/UX, F=funciones nuevas, D=datos/modelo, T=infraestructura/testing, G=gestión académica), cada uno con estado (`Validado` / `Validado parcialmente` / `En curso` / `No iniciado` / diferido / descartado) y la evidencia real que lo respalda, con links a `docs/evidencias/<fecha>/<ítem>/`.
- **`DECISIONES.md`**: registro formal de decisiones (DEC-001 a DEC-022 al momento de escribir esto), con plantilla fija (problema, opciones, decisión y motivo, evidencia, efectos/límites, qué queda pendiente). Cuando algo requiere tu criterio y no se puede resolver con más evidencia, se deja ahí como "pendiente de decisión de Rodo", **nunca se decide unilateralmente** si cambia el comportamiento del sistema en producción.
- **`BITACORA.md`**: diario de sesiones (SES-001 a SES-153 al momento de escribir esto), cada entrada documenta qué se hizo, qué se verificó y cómo.
- **`MAPA_PENDIENTES.md`** (regenerado esta sesión, SES-153): reorganiza los 65 ítems del backlog por área funcional real (core/modelo, lógica de negocio, base de datos/infraestructura, arquitectura frontend, diseño/UX, funciones nuevas, gestión académica) en vez de por prefijo de letra — pensado para decidir qué atacar a continuación.
- **`CONTINUIDAD.md`, `ACTAS_TUTOR.md`, `VALIDACION.md`, `PRIORIZACION.md`**: documentos de apoyo, menos centrales.

Carpeta `docs/tesis/`: los capítulos de la tesis en `.docx`. Capítulos 1 a 6 en `MotoSafe_GBA_Capitulos_1_a_6.docx`, Capítulo 7 (`..._Capitulo_7_Presentacion_de_resultados.docx`) y Capítulo 8 (`..._Capitulo_8_Implicancias_Conclusiones_y_Recomendaciones.docx`) como archivos separados. **No es parte del alcance de G01** (sincronización de guías) — Rodo lo revisa directo.

Carpeta `docs/evidencias/<fecha>/<item>/`: toda la evidencia real (CSVs, scripts, READMEs/RESULTADOS.md) que respalda cada actualización de BACKLOG.md. Si algo no tiene su carpeta de evidencia correspondiente, no está verificado.

## 3. Resumen numérico del backlog (65 ítems, recontado directo de `BACKLOG.md` el 21/10/2026, SES-153)

- **17 Validado**
- **24 Validado parcialmente**
- **2 En curso** (A17, G05)
- **22 No iniciado** — de estos, 21 son del catálogo de diseño/UX (V, 12 ítems) y funciones nuevas (F, 9 ítems), planteado al inicio del proyecto como mejoras de producto; el resto es D06 (fuentes GBA comparables, disponibilidad sin confirmar). Ninguno bloquea la entrega académica. **A pedido explícito de Rodo, nada del catálogo V/F se toca sin que él lo pida primero** — son decisiones de producto/diseño que quiere tomar él antes.

Esta cifra reemplaza la "63 ítems: 23+40" que tenía `BACKLOG.md` hasta SES-152 (quedó vieja a medida que se agregaron A20/A21/A24/D05 y otros ítems nuevos) y la "27 No iniciado / 3 En curso" que tenía este mismo documento hasta su versión anterior — T02 y T03 ya no están ni "en curso" ni "no iniciado".

Lo que realmente pesa para la entrega, en orden de impacto (según el cierre de `MAPA_PENDIENTES.md`):

1. **A09** — falta el conjunto etiquetado para validar calles/intersecciones del extractor de prensa. Ya se exportó la muestra real; el paso que sigue es que vos la etiquetes.
2. **D03** — revisar con tu propio criterio si los 4 casos reales de ruta generados "están bien" (quien los generó explícitamente no evaluó eso).
3. **G02/G03** — ampliar la muestra de validación con usuarios (G02) y contrastar contra requisitos institucionales que no están en el repo (G03); dependen de vos.
4. **A20/D04** — tu decisión sobre si ajustar `UMBRAL_CRUCE_KM` del comparador de rutas a la luz de la sensibilidad real medida.
5. **DEC-022** — tu decisión sobre sacar o no `sexo_victima` como variable del modelo.

## 4. Qué se hizo desde el traspaso anterior (SES-147) — todo esto ya está commiteado salvo lo que se aclara al final

Commits reales desde entonces (`git log`, del más reciente al más viejo):

```
0f8c0cb  SES-152: A05 validado con casos reales en pantalla, D05 monitor de calidad de datos nuevo, G01 sincroniza guías internas
ad65860  SES-151: T06 ensayado con volumen real en local, T03 línea base de rendimiento móvil, A20 criterio de limpieza geográfica común, A21 procedencia y estabilidad espacial de corredores
d2afd69  SES-149: T02 confirmación visual, A22/T05 CI confirmado, T01 rol mínimo, A19 pasos de red reales; T06 pendiente por decisión de Rodo
e4981a4  Cierra cuatro pendientes chicos sin necesitar el stack real (A06, A15, D01, T04)
bcfe8a7  DEC-022: aclara que la variante intermedia propuesta ya está implementada en la opción A
63528d3  T02: corrige el bug real de accesibilidad por teclado del buscador (SES-146)
94e93ad  Corrige el handoff: el frontend usa MapLibre GL, no Leaflet
3116569  Prepara etiquetado humano de prensa sin asignar resultados
```

**T02 cerrado**: el bug real de accesibilidad por teclado que había quedado documentado sin arreglar (la lista de resultados del buscador se desmontaba del DOM con el blur del input, sin mirar adónde iba el foco) se corrigió de verdad (`SearchBar.jsx`) y se confirmó visualmente en navegador real, en desktop y 375px, con `document.activeElement` real, no inferido. T02 pasa a Validado.

**A22/T05 — CI confirmado**: `gh auth login` corrido con autorización explícita de Rodo (completó él mismo el código de un solo uso en su navegador, sin que se le pidiera ni se viera su contraseña). Primera corrida de CI en GitHub confirmada limpia: lint/test/build del frontend, `py_compile` + `pip install --require-hashes` + pytest del backend contra un `postgis/postgis:16-3.4` real de servicio.

**T01 — permisos mínimos reales**: contra un PostGIS descartable (nunca `motosafe-db`), encontrado iterando fallos reales el conjunto mínimo de privilegios que necesita el rol que conecta el backend (sin dueño, sin superusuario): `CONNECT` + `USAGE` en schema + `SELECT/INSERT/UPDATE/DELETE` en tablas + `USAGE` en secuencias.

**A19 — pasos de red reales**: los 3 pasos con red del pipeline canónico (delitos CABA, clima Open-Meteo, geometría de corredores vía OSRM) corridos contra los servicios reales de hoy, en una copia de trabajo aislada. Delitos idéntico al vigente; clima con un hallazgo real (Open-Meteo revisa después las fechas más recientes); corredores con 42,4% de polilíneas distintas entre corridas (límite real del servidor demo de OSRM, no del pipeline propio).

**T06 — backup/restauración con volumen real, en local**: confirmado que no hay ningún despliegue público real (no hay producción que arriesgar). Ensayado con la composición real de producción (`docker-compose.production.yml`) y un volumen Docker **nombrado y persistente de verdad**. Reinicio real sin `-v`: el volumen sobrevivió completo. `pg_dump`/`pg_restore` reales sobre una instancia nueva: hashes idénticos, API real funcionando sobre la copia.

**T03 — línea base real de rendimiento móvil**: primera medición real a 375px (carga inicial, renders de `App`/`MapaMotoSafe`, memoria), con un presupuesto propuesto a partir de la medición (no inventado de antemano). Declarado explícito: es optimista respecto de un celular real con red real (sin throttling todavía).

**A20 — criterio común de limpieza geográfica**: nuevo `notebooks/limpieza_geografica_comun.py`. Aplicado sin efecto real a `limpiar_siniestros_motos.py` (verificado con hash idéntico al CSV vigente). Medido (sin aplicar) sobre `delitos_caba.csv`: 12 coordenadas genuinamente rotas y ~12.500 duplicados exactos que hoy nadie filtra.

**A21 — procedencia y estabilidad de corredores**: los puntos que definen cada corredor son 100% deterministas (verificado con hash idéntico corriendo el pipeline dos veces); la polilínea que dibuja OSRM entre esos mismos puntos no lo es (límite de un tercero, no del pipeline propio).

**A05 — validación geográfica independiente real**: una ruta íntegra en GBA profundo (Moreno) dio 0% de cobertura en las tres alternativas, sin ningún badge de seguridad disfrazado; una ruta límite real (CABA → Tigre, cruzando la frontera) dio cobertura intermedia real (45-57%), confirmando que el cálculo por trazado no se diluye. A05 pasa a Validado.

**D05 — monitor de calidad de datos, nuevo**: `notebooks/monitor_calidad_datos.py`, corre antes de `promover_artefactos.py --confirmar` sin bloquear nada. Verificado con datos reales regenerados ("sin cambios relevantes") y con un candidato alterado a propósito (detectado, con una corrección real de umbral hecha en el momento: un criterio solo porcentual no alcanzaba a detectar un salto real en un dataset de 1,39M de filas).

**G01 — sincronización de guías**: `docs/README.md`, `docs/gestion/BACKLOG.md` y `docs/gestion/CONTINUIDAD.md` corregidos contra el estado real (fechas, rango de IDs, conteo de tests verificado corriendo las suites de nuevo, conteo total del backlog recontado). El Word de la tesis queda fuera de este alcance.

### Sin commitear todavía (esta misma sesión, SES-153, pendiente de tu revisión)

- **`MAPA_PENDIENTES.md` y este mismo documento**, regenerados con el estado real de hoy (tareas 1 y 2 de esta sesión).
- **V10 cerrado**: el último hueco que quedaba (una capa real que responde 200 con lista vacía no tenía mensaje distinto de un fallo) se cerró. Confirmado en el código real que `/corredores` (con un `if not resultado: return []` explícito) y `/hotspots-inseguridad` pueden responder legítimamente vacío; `/hotspots` queda afuera a propósito porque hoy siempre trae datos reales. Nuevo aviso en `CapaErrorBanners.jsx`, mismo patrón visual, sin ícono de alerta ni botón de reintento. Verificado con 5 tests de componente nuevos y confirmado en pantalla real simulando la respuesta vacía con un service worker temporal (borrado al terminar). V10 pasa a Validado.

Verificación al cierre de esta sesión: **101/101 tests de frontend** (96 anteriores + 5 nuevos de V10) y **140 passed/11 skipped de backend**, corridos de nuevo, no copiados de una entrada anterior.

## 5. Lo que te queda pendiente a VOS (no al asistente)

1. **Etiquetar la muestra de A09** (`docs/evidencias/2026-10-21/A09-muestra-etiquetado/muestra_calles.csv`, 50 filas): para cada nota, juzgar si `query_extraida` (lo que el sistema extrajo como ubicación) es correcto contra el texto real de la noticia.
2. **D03**: revisar con tu propio criterio si los 4 casos reales de ruta generados "están bien" — quien generó los datos explícitamente no evaluó eso.
3. **DEC-022**: decidir si (A) dejás `sexo_victima` como está en el modelo productivo, (B) la sacás, o (C) una variante intermedia (ya implementada en la opción A, ver DEC-022 en `DECISIONES.md`). El trade-off real: sacarla cierra la brecha entre años pero empeora GRAVE/MORTAL en el split más reciente.
4. **UMBRAL_CRUCE_KM / A20**: decidir si conviene ajustar el umbral de cruce del comparador de rutas a la luz de la sensibilidad real medida (D04), y si vale la pena aplicar el criterio de limpieza geográfica de A20 a `identificar_hotspots_inseguridad.py`/`construir_indice_inseguridad.py` (cambiaría artefactos ya publicados — republicarlos es tu decisión, no algo para forzar sin que lo pidas).
5. **G02/G03**: ampliar la muestra de validación con usuarios reales (G02) y contrastar la matriz de objetivos contra requisitos institucionales que no están en el repo (G03).
6. **Los 22 ítems "No iniciado"** del backlog (mayormente V/diseño y F/funciones nuevas): decidir si alguno te importa para la entrega final o si se deja explícitamente fuera de alcance con una línea en `DECISIONES.md`, en vez de dejarlos flotando como deuda sin decidir.

## 6. Reglas de trabajo — leer antes de seguir con cualquier asistente

Estas reglas sostienen la credibilidad de todo el proyecto. Cualquier asistente que continúe (ChatGPT incluido) debería seguirlas:

- **Nunca fabricar resultados.** Si algo no se pudo probar, se documenta explícitamente como "no verificado", nunca se inventa un resultado plausible. Esto se aplicó literalmente en cada sesión (ver BITACORA.md) y es la regla más importante de todas.
- **Verificar antes de confiar en un self-report.** Cuando otra herramienta/agente (Codex, u otro asistente) dice "ya lo hice, X/X tests en verde", hay que correr los tests de nuevo, leer el diff real, cruzar contra los archivos de evidencia — nunca aceptar el reporte tal cual.
- **Antes de escribir en `BITACORA.md`, confirmar el número de sesión libre.** Buscar `## SES-` en el archivo y arrancar desde el siguiente número, no asumirlo — puede haber trabajo de otra sesión/asistente de por medio. Tampoco reatribuir un asiento anterior a un asistente específico sin confirmarlo primero.
- **Las decisiones que cambian el modelo o el comportamiento productivo nunca se toman solas.** Si una medición abre una disyuntiva real (ejemplo: DEC-022), se documenta con números reales y se deja pendiente de tu decisión explícita en `DECISIONES.md`, nunca se resuelve unilateralmente.
- **Nunca pasar ni tipear tu contraseña real** en ningún chat, de ningún asistente. Si una tarea necesita tu sesión autenticada contra el backend real, entrás vos mismo en la pantalla de login.
- **El catálogo V (diseño/UX) y F (funciones nuevas) no se toca sin que Rodo lo pida explícitamente** — son decisiones de producto que él quiere tomar antes de pedirlas. Si una tarea puntual (como V10) hace dudar si cruza a una decisión de diseño más grande, parar y preguntar en vez de decidir.
- **Una mención histórica fechada (una entrada de BITACORA/CONTINUIDAD, un assessment fechado) no se corrige ni se borra** — describe correctamente lo que era cierto en su momento. Solo se corrige lo que un documento afirma como estado vigente hoy sin serlo (criterio usado en G01).
- **No crear ninguna cuenta en ningún proveedor de hosting, ni ingresar ningún dato de pago**, bajo ninguna circunstancia, para ningún agente de IA actuando en nombre de Rodo.
- **Estilo de la tesis** (ya aplicado en todos los capítulos existentes): sin fechas puntuales en la prosa, sin códigos internos de seguimiento (A09, DEC-022, SES-146, etc. — eso se explica en lenguaje llano), con la jerga técnica explicada la primera vez que aparece sin volverse un manual, documentos que no crecen de más, y contexto autocontenido para un lector que no conoce el sistema de seguimiento interno.
- **Principio de versionado del informe** (DEC-016): los capítulos de tesis y documentos de gestión se mantienen al día — cuando un avance deja desactualizado un capítulo anterior, se corrige directamente en el texto, sin nota de versión fechada. Lo que preserva la historia es la bitácora, no el capítulo.
- **Para cambiar `BACKLOG.md`**: solo pasa a "Validado" cuando no queda nada pendiente de código ni de decisión para ese ítem; "Validado parcialmente" si queda algo real sin cerrar.
- **Convención de commits de este repo**: mensajes descriptivos en español, sin emojis, con el detalle real de qué se verificó (no solo qué se hizo).

## 7. Cómo retomar con otro asistente (ChatGPT u otro)

1. Dale este documento completo como contexto inicial.
2. Pedile que lea (si tiene acceso al repo) `docs/gestion/BACKLOG.md`, `docs/gestion/DECISIONES.md` (al menos las últimas 5-6 decisiones), `docs/gestion/MAPA_PENDIENTES.md` completo y las últimas 10-15 entradas de `docs/gestion/BITACORA.md` antes de proponer cualquier paso.
3. Si no tiene acceso directo al repo (por ejemplo, estás en el chat web de ChatGPT sin conexión a tus archivos), subile los archivos de `docs/gestion/` y los capítulos de tesis que correspondan a lo que vayas a trabajar.
4. Priorizá, según la lista de la sección 5, qué querés resolver primero — lo más barato y de mayor impacto sigue siendo etiquetar la muestra de A09 (es trabajo tuyo de lectura, no de código) y decidir DEC-022 (es una decisión, no una tarea técnica).
5. Cuando vuelvas a Claude con tokens disponibles, contale qué avanzaste con el otro asistente (qué decisiones tomaste, qué código cambió si cambió algo) para que se pueda verificar y seguir la misma disciplina de siempre.

## 8. Dónde está todo (rutas reales en el repo)

- Backlog: `docs/gestion/BACKLOG.md`
- Decisiones: `docs/gestion/DECISIONES.md`
- Bitácora: `docs/gestion/BITACORA.md`
- Mapa de pendientes por área: `docs/gestion/MAPA_PENDIENTES.md`
- Muestra de A09 para etiquetar: `docs/evidencias/2026-10-21/A09-muestra-etiquetado/muestra_calles.csv` (y su `README.md`)
- Evidencia T02 (confirmación visual real): `docs/evidencias/2026-10-21/T02-confirmacion-teclado/RESULTADOS.md`
- Evidencia T01 (permisos mínimos): `docs/evidencias/2026-10-21/T01-rol-sin-dueno/RESULTADOS.md`
- Evidencia A19 (pasos de red reales): `docs/evidencias/2026-10-21/A19-pasos-de-red/RESULTADOS.md`
- Evidencia T06 (volumen real en local): `docs/evidencias/2026-10-21/T06-backup-volumen-real/RESULTADOS.md`
- Evidencia T03 (línea base de rendimiento): `docs/evidencias/2026-10-21/T03-rendimiento-movil/RESULTADOS.md`
- Evidencia A20 (limpieza geográfica): `docs/evidencias/2026-10-21/A20-limpieza-geografica/RESULTADOS.md`
- Evidencia A21 (estabilidad de corredores): `docs/evidencias/2026-10-21/A21-corredores-estabilidad/RESULTADOS.md`
- Evidencia A05 (validación geográfica): `docs/evidencias/2026-10-21/A05-cobertura-desconocida/RESULTADOS.md`
- Evidencia D05 (monitor de calidad de datos): `docs/evidencias/2026-10-21/D05-monitor-calidad-datos/RESULTADOS.md`
- Evidencia G01 (sincronización de guías): `docs/evidencias/2026-10-21/G01-sincronizacion-guias/RESULTADOS.md`
- Evidencia V10 (aviso de capa sin datos): `docs/evidencias/2026-10-21/V10-mensaje-sin-datos/RESULTADOS.md`
- Capítulos de tesis: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_6.docx`, `..._Capitulo_7_Presentacion_de_resultados.docx`, `..._Capitulo_8_Implicancias_Conclusiones_y_Recomendaciones.docx`
- Guion de demo: `docs/entrega/MATRIZ_ACADEMICA_Y_DEMO.md`

---

*Último commit al momento de escribir esto: `0f8c0cb` (SES-152). Lo descripto en la sección 4 bajo "sin commitear todavía" (V10, este documento y `MAPA_PENDIENTES.md`) queda a tu revisión antes de commitear, como siempre.*
