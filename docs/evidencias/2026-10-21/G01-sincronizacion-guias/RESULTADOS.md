# G01 — sincronizar guías internas con el estado real (2026-10-21)

Alcance: `docs/README.md`, `docs/gestion/CONTINUIDAD.md` y otras guías internas del repositorio. **El Word
de la tesis queda explícitamente fuera**, como pidió Rodo. `AGENTS.md` se revisó y no tenía ninguna cifra
ni afirmación técnica desactualizada (es un documento de proceso, sin números). `docs/gestion/
MAPA_PENDIENTES.md` y `docs/gestion/HANDOFF_CONTINUIDAD_OTRO_ASISTENTE.md` se revisaron y quedan señalados
pero sin editar -- ver "Qué se identificó pero no se tocó" al final.

## Criterio para no borrar menciones históricas legítimas

Revisado antes de tocar nada (mismo criterio ya discutido en una sesión anterior sobre un hallazgo
similar): un documento con formato de bitácora/traspaso (entradas fechadas, "Actualización AAAA-MM-DD —
SES-XXX: ...") describe correctamente lo que era cierto **en ese momento**. Eso no se corrige ni se borra
-- sería reescribir historia. Solo se corrige lo que un documento afirma como **estado vigente hoy** (un
resumen al tope del archivo, una cifra sin fecha, una lista de "lo que falta" que ya no es cierta). Aplicado
en la práctica: en `CONTINUIDAD.md`, decenas de entradas fechadas de sesiones pasadas (ej. "80 tests
frontend y 65 backend" de SES-058, "93 tests" de SES-114) **no se tocaron** -- son historia real de esa
fecha. Solo se corrigieron el resumen del tope del archivo y una lista de "problemas vigentes" sin fecha
que sí afirmaba algo falso sobre hoy (ver abajo).

## Correcciones reales, con antes/después

### `docs/README.md`

1. **Fecha de "Actualizado"**: `2026-10-20` → `2026-10-21`.
2. **Rango de IDs de hallazgos** (línea de convención, afirma una regla vigente, no historia):
   - Antes: *"mantener A01–A23 para los hallazgos"*
   - Después: *"mantener A01–A24 para los hallazgos"*
   - Motivo: A24 (confianza por zona) existe y está Validado desde SES-116; la convención decía A23 porque
     quedó escrita antes de que A24 se creara.
3. **Conteo de tests**, agregada una sección nueva `## Pruebas técnicas — 2026-10-21` (sin tocar la de
   `2026-10-13`, que queda como registro histórico de esa fecha, con una frase agregada aclarando que está
   superada):
   - Antes (única sección, sin fecha de verificación posterior): *"93 tests frontend... y 120 backend
     aprobados (11 skipped)"*.
   - Después (corrido de nuevo ahora mismo, no copiado): **96 tests frontend, 140 backend aprobados (11
     skipped)**.
   - Nota honesta: el pedido de Rodo mencionaba "136 passed" para el backend -- se verificó corriendo la
     suite en el momento (no se usó el número del pedido sin comprobarlo) y el resultado real es **140**,
     no 136. La diferencia es real: entre que se escribió el pedido y esta verificación se sumaron
     pruebas (T04/`consumir_metricas.py` en SES-150). Se documenta el número verificado ahora, no el que
     venía en el mensaje.

### `docs/gestion/BACKLOG.md`

4. **Conteo total de ítems** (encabezado, afirma un total vigente, no historia):
   - Antes: *"63 ítems: 23 hallazgos y 40 oportunidades"*.
   - Después: *"65 ítems: 24 hallazgos y 41 oportunidades"*.
   - Cómo se recontó: directo de las tablas reales del archivo, no estimado. La sección "## Hallazgos
     existentes" tiene 24 filas únicas (A01 a A24, confirmado listando cada ID). Las demás secciones
     ("Diseño visual", "Funcionalidades y producto", "Datos y valor científico", "Calidad técnica y
     operación", "Documentación...") suman 14+10+6+6+5 = 41 oportunidades (D01-D06, T01-T06, G01-G05,
     V01-V14, F01-F10). 24+41=65, y coincide con el conteo independiente de IDs únicos en toda la tabla
     "Ejecución actual" (también 65). Esta misma cifra de 65 ya aparecía correcta en
     `MAPA_PENDIENTES.md` y en `HANDOFF_CONTINUIDAD_OTRO_ASISTENTE.md` -- confirma que el encabezado de
     `BACKLOG.md` era el que había quedado atrás, no al revés.

### `docs/gestion/CONTINUIDAD.md`

5. **Lista de "problemas que deben permanecer visibles"** (afirma un estado vigente sin fecha):
   - Antes: *"A07, A09, A10, A12, A15 y A16 solo tienen correcciones parciales"*.
   - Después: *"A07, A10, A12 y A15 ya están Validados (sin pendiente de código); solo A09 y A16 siguen
     con correcciones parciales"*.
   - Verificado contra `BACKLOG.md` fila por fila: A07 Validado, A09 Validado parcialmente, A10 Validado,
     A12 Validado, A15 Validado, A16 Validado parcialmente. De los seis citados, cuatro ya estaban
     cerrados -- la frase original se había quedado con la lista completa de cuando los seis estaban
     parciales.
6. **Resumen del tope del archivo**: agregada una oración que actualiza la fecha (20/10 noche → 21/10) y
   apunta a la entrada nueva de abajo, sin borrar el resumen anterior (que sigue siendo cierto sobre lo que
   describía).
7. **Entrada nueva al final** (`## Actualización 2026-10-21 — SES-148 a SES-152`): resume en una sola
   entrada lo que cambió realmente desde la última entrada del archivo (SES-147) -- T02 cerrado, A22/T05
   con CI confirmado, T01/A19/T06/T03/A20/A21 avanzados, A05 validado, D05 nuevo, y esta misma pasada de
   G01. Sin esto, el archivo se quedaba parado en SES-147 mientras BACKLOG/BITACORA ya tenían cuatro
   sesiones más de trabajo real encima.

## Qué se identificó pero no se tocó

- **`docs/gestion/MAPA_PENDIENTES.md`**: su propio resumen numérico ("17 Validado, 22 Validado
  parcialmente, 3 En curso, 27 No iniciado") quedó desactualizado por el trabajo de esta sesión (T02 ya no
  está "En curso", D05 ya no está "No iniciado", etc.). El documento declara explícitamente su propio
  límite ("se regenera a mano cuando cambie el backlog; no se mantiene en paralelo de forma automática")
  -- no es un error no corregido, es un documento que ya avisa que necesita regenerarse y todavía no se
  hizo esa regeneración completa (recontar los 65 ítems uno por uno no entraba en el alcance de esta
  sesión). Queda señalado para una próxima pasada.
- **`docs/gestion/HANDOFF_CONTINUIDAD_OTRO_ASISTENTE.md`**: es una fotografía fechada ("Estado completo del
  proyecto al 21/10/2026") pensada para pegarse en otro asistente en un momento puntual, no un documento
  vivo que se vaya actualizando -- su "3 En curso (T02, A17, G05)" y "27 No iniciado" ya no reflejan el
  trabajo de esta sesión. Mismo criterio que arriba: señalado, no reescrito, porque regenerarlo
  completo es una tarea en sí misma (un traspaso de contexto nuevo), no una corrección puntual.
- **`Claude outputs/HANDOFF_MOTOSAFE_2026-10-21.md`**: todavía dice "React + Leaflet". No es una guía
  interna del repositorio -- está en `.gitignore` (`Claude outputs/`), es un artefacto local/efímero, fuera
  del alcance que pidió Rodo.
- **Menciones legítimamente históricas de "Leaflet"** encontradas y dejadas sin tocar: `docs/
  assessment_2026-09-11/ASSESSMENT.md` (auditoría fechada, conservada por decisión explícita del proyecto),
  `docs/gestion/BITACORA.md` (entradas de sesión, historia), raíz `README.md` línea 233 (sección fechada de
  "Tareas realizadas" de cuando se agregó tráfico de TomTom, de antes de la migración a MapLibre -- el
  propio README avisa arriba que "la auditoría identifica afirmaciones antiguas pendientes de actualizar en
  este documento" y que su backlog histórico se conserva como tal).

## Verificación

96/96 tests de frontend y 140 passed/11 skipped de backend confirmados corriendo las suites de nuevo al
cierre de esta sesión (no copiados de una corrida anterior). `git diff --stat` de los tres archivos
tocados: 3 archivos, cambios puntuales y acotados a las frases identificadas arriba, sin tocar ninguna
entrada fechada de historia.
