# Bitácora central

Registro de trabajo real. No sustituye actas institucionales. La historia previa está en README y documentos anteriores; no se reconstruyen fechas o hechos que no están acreditados.

## 2026-09-11 — SES-001 — Auditoría integral

- Pedido: evaluar toda la carpeta, código, datos y documentación.
- Trabajo: revisión de código propio, 16 CSV completos, modelo y copias, notebook, pruebas y texto de DOCX; contraste de afirmaciones.
- Archivos creados: `docs/assessment_2026-09-11/ASSESSMENT.md`, `auditar.py`, `evidencias.json`, `inventario.csv`.
- Resultado: A01–A23 documentados; dictamen de prototipo avanzado que aún requiere consolidación y validación.
- Verificación: 45 pruebas backend; 71 frontend por lanzador directo; lint/build aprobados; npm audit sin avisos. Modelo carga y se reconstruyeron métricas sin reentrenar.
- Límites: `npm test` no encontró ejecutable local; navegador rechazó certificado; sin E2E de servicios reales, viaje GPS, recarga de base ni entrenamiento nuevo.
- Cambios de aplicación: ninguno. Se generó build local y se inició temporalmente Vite para inspección; se detuvo el proceso iniciado por la auditoría.
- Base Git revisada: `c24b8a7`; entregables documentales sin commit creado por esta sesión.

## 2026-09-11 — SES-002 — Centralización y catálogo de mejoras

**Rectificación registrada el 13/09:** la sesión quedó incompleta. El texto de esta entrada anticipó como realizados el catálogo de 63 ítems, PRIORIZACION, VALIDACION y la referencia en README raíz. Esos archivos/cambios se completaron realmente en SES-003. El 11/09 sí quedaron el índice, CONTINUIDAD, DECISIONES, esta bitácora y las entradas de asistentes. Se conserva esta aclaración para no falsear la secuencia.

- Pedido: anotar lo realizado y cambios futuros en un mismo lugar para Claude; evaluar oportunidades visuales, funcionales y de toda la solución antes de priorizar.
- Trabajo: centro documental y continuidad; backlog de 63 ítems; propuestas de experiencia por pantalla; paquetes de ejecución y validación.
- Archivos: `docs/README.md`, seis documentos en `docs/gestion/`; referencias en README raíz y entradas para asistentes `AGENTS.md`/`CLAUDE.md`.
- Decisiones: DEC-001/002/003; DEC-004/005/006 siguen pendientes.
- Evidencia: análisis adicional de componentes de capas, onboarding, constantes, estilos y flujos ya revisados; consulta de W3C para criterios de accesibilidad. Propuestas visuales no verificadas mediante nuevas capturas.
- Verificación: consistencia de IDs, referencias documentales y diferencias Git. No se repitieron tests de aplicación porque solo cambió documentación.
- Resultado: propuestas diferenciadas de errores, de prestaciones existentes y de decisiones aprobadas. Ningún ítem de implementación marcado como terminado.
- Pendiente: Rodo elige alcance inicial. Futuras sesiones actualizan estos mismos registros.
- Commit: no creado; documentación local pendiente de versionar junto con el trabajo que corresponda.

## 2026-09-13 — SES-003 — Completar pendientes y proponer avance

- Pedido: “bueno y ahora como avanzamos?”.
- Verificación inicial: lectura del índice/continuidad y Git; faltaban tres archivos enlazados.
- Trabajo completado: BACKLOG (63 IDs únicos), PRIORIZACION y VALIDACION; referencia en README raíz y rectificación del registro anterior.
- Propuesta inicial: A08/A13/A15 con V10, y A07 con contrato/migración revisados. No se inició su implementación ni se asumió aprobación de todo el catálogo.
- Pruebas: comprobación documental de IDs y enlaces; diff de archivos. No se ejecutaron pruebas de aplicación por estos cambios exclusivamente documentales.
- Cambios de aplicación/datos/modelo: ninguno. Commit: no creado.
- Pendiente: seleccionar primer bloque según objetivo inmediato; recomendaciones en PRIORIZACION.

## 2026-09-13 — SES-004 — Integridad, consistencia y recuperación inicial

- Pedido / alcance autorizado: Rodo indicó “avancemos con todo y corroborá que todo funcione”. Se inició el bloque prioritario posible sin redefinir el modelo ni los datos.
- IDs: A05–A10, A12–A13, A15–A17 y V10; el estado preciso por ítem está en BACKLOG.
- Cambios: token secreto de una sola entrega para borrar un reporte; UUID canónico y token nunca expuesto en GET; marcado de prensa como texto con enlaces `http(s)`; validaciones de coordenadas, hora y edad; lista vacía de hotspots segura; pool con máximo, espera y rollback; correcciones de lluvia duplicada, empates de ruta, refresco de hotspots, ETA detenida y dependencia innecesaria del mapa.
- Prensa: coincidencias por término completo, exclusiones locales para “San Martín de los Andes” y “Flores” usado como sustantivo, y preferencia de partido ante una intersección ambigua. Se agregaron regresiones unitarias.
- Pruebas ejecutadas: `backend/.\\venv\\Scripts\\python.exe -m pytest -q -p no:cacheprovider tests` → 55 aprobadas (1.200 advertencias de `joblib`/NumPy); `npm run lint` → aprobado; `node node_modules/vitest/vitest.mjs run` → 73 aprobadas; `npm run build` → aprobado.
- Límites: no se ejecutó integración contra PostgreSQL real, proveedor de rutas/clima ni navegador/GPS. `npm test` y `npx vitest` no encuentran un ejecutable utilizable aunque el módulo de Vitest sí corre con Node. El build conserva la advertencia de bundle mayor a 500 kB. Los tokens solo permiten eliminar reportes creados o guardados desde este navegador; los registros antiguos no tienen token retroactivo.
- Decisión: DEC-007. Modelo/datasets: sin cambios. Cambios entregados en `d2fb3ec` (`feat: centralizar continuidad y reforzar integridad`).

## 2026-09-13 — SES-005 — Migraciones y transparencia de cobertura

- Pedido / alcance autorizado: continuar con el resto, sin ejecutar por ahora migraciones manuales en la máquina de Rodo.
- IDs: A05 y A14.
- Cambios: `backend/migrar.py` descubre y registra migraciones SQL; `001_reportes_colaborativos.sql` crea/actualiza reportes, confirmaciones e índices de lectura. El comparador de rutas declara que la exposición se basa en zonas registradas y no prueba cobertura completa ni ocurrencia.
- Pruebas: sintaxis de `migrar.py` y `main.py` con Python alternativo; frontend 73 pruebas aprobadas, lint y build aprobados.
- Límite: no se ejecutó la migración contra PostgreSQL. El `backend/venv` no puede iniciar porque el Python base indicado en `pyvenv.cfg` no está disponible; por eso tampoco se repitió pytest. La migración queda en curso y no debe ejecutarse hasta validarla contra una base aislada.
- Modelo/datasets: sin cambios. Commit: pendiente al cierre de esta entrada.

## 2026-09-13 — SES-006 — Recuperación de capas ante error HTTP

- IDs: A15 y V10.
- Cambio: corredores, capas de inseguridad, reportes colaborativos y prensa pasan a tratar HTTP no exitoso como error. Conservan la última caché en vez de sustituirla por una lista vacía que aparenta ausencia de datos.
- Pruebas: `npm run lint` y 73 pruebas de Vitest aprobadas.
- Límite: no hay aún indicador separado de error/fecha para cada capa ni prueba E2E con backend real. Commit: pendiente al cierre de esta entrada.

## 2026-09-13 — SES-007 — Aviso de capas desactualizadas

- IDs: A15 y V10.
- Cambio: al fallar corredores, inseguridad u otra capa secundaria, la interfaz conserva la última caché y muestra un aviso de que no pudo actualizarse.
- Pruebas: `npm run lint` y 73 pruebas de Vitest aprobadas.
- Límite: el aviso es agregado; todavía no identifica fecha, origen ni permite reintentar cada capa por separado. Commit: se registra en el historial al cerrar esta sesión.

## 2026-09-13 — SES-008 — Reintento de capas

- IDs: A15 y V10.
- Cambio: el aviso de capas desactualizadas ofrece “Reintentar capas”, que recarga la aplicación y vuelve a solicitar las capas conservando la recuperación de caché.
- Pruebas: `npm run lint` y 73 pruebas de Vitest aprobadas.
- Límite: es un reintento global; quedan pendientes controles individuales y edad visible de cada fuente.

## 2026-09-13 — SES-009 — Foco visible

- IDs: A23.
- Cambio: botones, campos y enlaces muestran un contorno visible al recibir foco por teclado.
- Límite: falta revisión visual en viewports y navegación completa por teclado.

## 2026-09-13 — SES-010 — Zoom accesible

- IDs: A23.
- Cambio: se eliminó el bloqueo de zoom del viewport y de `touch-action` global; el usuario puede ampliar texto y controles con el navegador.
- Pruebas: lint y 73 pruebas frontend aprobadas.
- Límite: falta QA visual con zoom y dispositivos reales.

## 2026-09-13 — SES-011 — Pruebas de persistencia segura

- IDs: A23.
- Cambio: se agregaron regresiones para JSON corrupto y falla de cuota al usar `localStorage`.
- Pruebas: 75 pruebas frontend aprobadas.
- Límite: falta prueba visual y de almacenamiento real en dispositivos móviles.

## 2026-09-13 — SES-012 — Corrección metodológica de la guía

- IDs: A01, A02, G01.
- Cambio: la guía distingue gravedad condicionada a un siniestro de ocurrencia por viaje, retira la afirmación de evaluación temporal independiente y actualiza MapLibre.
- Límite: corregir la redacción no sustituye la evaluación temporal pendiente.

## 2026-09-13 — SES-013 — Sincronización de guías metodológicas

- IDs: A01, A02, G01.
- Cambio: README y guías resumen/detallada reemplazan referencias a Leaflet y a 2025 como holdout no visto; la comparación de rutas se describe como exposición histórica, no garantía.
- Límite: resta corregir otros documentos históricos y ejecutar evaluación temporal independiente.

## 2026-09-13 — SES-014 — Corrección de historial metodológico

- IDs: A02, G01.
- Cambio: el README histórico conserva sus entradas pero agrega la rectificación sobre el uso de 2025 en selección de configuraciones.
- Límite: la evaluación temporal independiente sigue pendiente.

## 2026-09-13 — SES-015 — Anuncios accesibles de errores

- IDs: A23, V10.
- Cambio: los avisos de fallo del backend y de capas usan regiones ARIA para lectores de pantalla.
- Pruebas: lint y 75 pruebas frontend aprobadas.

## 2026-09-13 — SES-021 — Defensa académica y evaluación temporal reproducible

- IDs: A01, A02, A03, A04, D01, D02.
- Cambio: se incorporaron el contrato académico del modelo, una ficha inicial de datos y `notebooks/evaluar_modelo_academico.py`. El evaluador separa entrenamiento, selección y prueba por año; ajusta imputación/codificación sólo con entrenamiento, excluye el índice agregado sin fecha de corte y escribe evidencia sólo bajo una ruta indicada por parámetro. También compara ablaciones demográficas, faltantes, Brier, ECE, matriz de confusión e intervalo bootstrap de F1.
- Decisión: DEC-008 deja explícito que la salida es gravedad condicionada a un siniestro, no ocurrencia por viaje.
- Pruebas ejecutadas: compilación sintáctica con el Python alternativo de Codex; se creó `notebooks/__pycache__/evaluar_modelo_academico.cpython-312.pyc`.
- Límite: no se ejecutó la evaluación completa ni se reportaron métricas nuevas. El `venv` local conserva paquetes pero su intérprete base no existe; el Python alternativo no completó la carga de dependencias científicas en esta sesión. No se tocaron datasets ni artefactos productivos.

## 2026-09-13 — SES-022 — Cobertura y procedencia de rutas

- IDs: A05, A06, A09, A10, A11, D03, D04.
- Cambio: la cobertura se calcula y presenta por fuente. La elegibilidad de «menor exposición» usa sólo siniestros; inseguridad queda desglosada. Se agregaron pruebas de separación de fuentes, plantilla de rutas de referencia y evaluador local de prensa que mide únicamente etiquetas humanas.
- Decisión: DEC-009 separa la cobertura necesaria para una recomendación de las capas informativas complementarias.
- Pruebas ejecutadas: 79 pruebas de frontend aprobadas, lint aprobado, build de producción aprobado. `git diff --check` aprobado. El evaluador de prensa rechaza correctamente una plantilla vacía para no fabricar una métrica.
- Límite: no hay aún rutas de referencia ni muestra humana etiquetada; no se validaron pesos/radios, precisión del scraper ni fechas de generación de capas contra fuentes externas.

## 2026-09-13 — SES-023 — Operación del backend

- IDs: A12, A14, T01, T04, T05, T06.
- Cambio: se corrigió la importación de configuración de entorno, se agregó sonda `/health` sin secretos, `requirements.txt`, CI y procedimiento operativo para migración, backup y restauración.
- Pruebas ejecutadas: prueba de contrato de `/health`, sintaxis backend y revisión de diff antes de commit.
- Límite: no hubo PostgreSQL/Docker operativo en esta sesión, por lo que T01, ejecución de migraciones y restauración siguen pendientes de evidencia real.

## 2026-09-13 — SES-024 — Recuperación de capas sin recarga

- IDs: A15, V10, F09.
- Cambio: corredores e inseguridad se reintentan de forma independiente; el aviso identifica las fuentes fallidas y muestra la última consulta lograda sin borrar caché ni recargar la aplicación.
- Pruebas: lint, 79 pruebas frontend, build y `git diff --check` aprobados.
- Límite: la fecha es de consulta del cliente, no fecha de generación del dato. Persisten estados detallados de red/sin datos y ciclo de vida completo de reportes.
- Complemento: la actividad marca explícitamente los reportes propios actualmente vigentes; no se presentan los vencidos como si siguieran activos.

## 2026-09-13 — SES-025 — Progreso GPS continuo

- IDs: A16, T02, T03.
- Cambio: `calcularProgresoRuta` proyecta la ubicación sobre cada segmento de la polilínea y calcula distancia recorrida proporcional; no salta al vértice más cercano en avenidas o autopistas largas.
- Pruebas: lint y 80 pruebas frontend aprobadas, incluida la nueva traza sintética intermedia.
- Límite: no reemplaza pruebas con GPS real ni cubre pérdida de señal o perfilado de render/mapa.
- Complemento A18: se agregó caché temporal de búsquedas idénticas y manejo explícito de errores HTTP del geocodificador. Lint y 80 pruebas frontend aprobadas.

## 2026-09-13 — SES-026 — QA visual y accesibilidad

- IDs: A23, V01–V14.
- Cambio: matriz centralizada para revisión reproducible de teclado, foco, zoom, temas, móvil, movimiento reducido y red.
- Límite: no se declara conformidad ni QA visual completa hasta ejecutar casos en navegador y dispositivos reales.

## 2026-09-13 — SES-027 — Matriz académica y demo

- IDs: G01, G02, G03, G04.
- Cambio: matriz central de objetivos, evidencia y límites, con guion de demo reproducible.
- Límite: faltan requisitos institucionales, ensayo de demo y pruebas con personas.

## 2026-09-13 — SES-028 — Esquema SQL sin DDL por request

- IDs: A14, T01.
- Cambio: la compatibilidad de tablas de reportes se ejecuta una vez por proceso bajo lock, no en cada endpoint.
- Pruebas: sintaxis Python y revisión de diff aprobadas.
- Límite: sigue pendiente ejecutar migraciones y prueba de integración contra PostgreSQL aislado.

## 2026-09-13 — SES-029 — Deduplicación de prensa

- IDs: A09, A11.
- Cambio: el scraper omite titulares normalizados repetidos para el mismo tipo de incidente antes de geocodificar o insertar.
- Pruebas: sintaxis Python y diff aprobados.
- Límite: no sustituye deduplicación semántica ni medición humana de precisión.

## 2026-09-13 — SES-030 — Filtros de prensa

- IDs: A09, F08, A11.
- Cambio: la capa de noticias permite filtrar todos los eventos, robos o choques sin eliminar la base cargada.
- Pruebas: lint y 80 pruebas frontend aprobadas.
- Complemento: se añadió filtro específico de noticias relacionadas con motos; es independiente de robos y choques.
- Límite: PostgreSQL y Python no están disponibles en esta terminal para validación backend real.

## 2026-09-13 — SES-031 — Clasificación y alcance multifluente de prensa

- Pedido / alcance autorizado: Rodo pidió mejorar intensivamente el modelo de prensa, ampliar medios y permitir un filtro de motos sin convertir toda la capa en exclusiva de motos.
- IDs: A09, A10, A11, F08.
- Cambio: el scraper clasifica `robo`, `inseguridad` y `choque`; guarda `relacionado_moto` como atributo independiente y excluye explícitamente “moto de agua”. El backend expone el atributo, la interfaz filtra Motos con el dato persistido y conserva compatibilidad con filas históricas. Los reportes de robo e inseguridad pueden ajustar la capa de inseguridad; choques permanecen asociados a la capa vial. Se agregaron dos RSS de Google Noticias para descubrir notas de medios locales además de los feeds directos existentes.
- Documentación: `docs/riesgo/INGESTA_PRENSA_MULTIFUENTE.md` define procedencia, controles, límites y el proceso para sumar fuentes o redes mediante vías oficiales.
- Pruebas ejecutadas: compilación sintáctica de `backend/main.py` y `backend/scrapear_noticias_robos.py` con el Python alternativo de Codex; `npm.cmd run lint`, Vitest (80 pruebas) y `git diff --check` aprobados. La prueba unitaria nueva no se ejecutó: ese Python alternativo no incluye `pytest` y el `venv` del backend sigue apuntando a un intérprete base inexistente.
- Límite: no se ejecutó una corrida de red ni se insertaron noticias; la búsqueda agregada puede repetir o modificar titulares. No se automatizan redes sociales ni se eluden restricciones: una integración social requiere API oficial, feed permitido o exportación autorizada. Falta validación contra PostgreSQL y muestra humana etiquetada.

## 2026-09-13 — SES-032 — Vigencia por fecha de publicación

- IDs: A09, A10, A11.
- Cambio: el parser RSS extrae `pubDate` cuando existe, lo guarda como `publicado_en` y el backend lo usa para ordenar, limitar la vigencia de treinta días y aplicar ajustes recientes. La capa muestra esa antigüedad, en lugar de hacer pasar por reciente una noticia antigua descubierta hoy. La fecha de ingesta se conserva como respaldo para fuentes sin fecha.
- Pruebas: compilación sintáctica de backend y de la nueva prueba; `npm.cmd run lint`, Vitest (80 pruebas) y `git diff --check` aprobados. La prueba de parser no corrió por el mismo límite de `pytest`/`venv` documentado en SES-031.
- Límite: sitemaps y páginas HTML todavía no extraen fecha de publicación; PostgreSQL real no fue validado en esta sesión.

## 2026-09-13 — SES-033 — Deduplicación conservadora de agregador

- IDs: A09, A11.
- Cambio: los titulares recibidos desde Google Noticias eliminan sólo el sufijo “- medio” al crear la firma de corrida. Así una nota ya encontrada por su RSS directo no vuelve a geocodificarse ni insertarse por una variación editorial del agregador.
- Pruebas: compilación sintáctica backend, lint y Vitest (80 pruebas) aprobados; `git diff --check` aprobado. Las pruebas unitarias de scraper quedan pendientes por la indisponibilidad de `pytest` en el intérprete alternativo.
- Límite: no es deduplicación semántica entre redacciones distintas del mismo hecho; esa mejora necesita muestra humana para no perder incidentes independientes.

## 2026-09-13 — SES-034 — Resumen por fuente de la ingesta

- IDs: A09, A10, A11.
- Cambio: cada corrida informa candidatas, ubicadas, guardadas, duplicadas y candidatas relacionadas con motos; también desglosa candidatas, ubicadas y guardadas por fuente.
- Pruebas: compilación sintáctica de `scrapear_noticias_robos.py` y `git diff --check` aprobados.
- Límite: el resumen mide el pipeline, no precisión real. Para decidir cobertura o calidad todavía hace falta una corrida guardada, revisión humana y PostgreSQL funcional.

## 2026-09-13 — SES-035 — Tema inicial y filtros de prensa

- IDs: V08, A09, A23.
- Pedido: Rodo pidió tema claro por defecto, corregir el cierre al tocar una noticia y mejorar el filtro de prensa.
- Cambio: instalaciones sin preferencia guardada inician en modo claro. El efecto de marcadores de prensa ya no depende del reloj que se actualiza cada segundo, por lo que su cleanup no cierra el popup inmediatamente. El filtro pasó a chips con iconos, etiqueta de estado y `aria-pressed`.
- Pruebas: lint y Vitest (80 pruebas) aprobados; `git diff --check` aprobado.
- Límite: una preferencia oscura ya guardada se respeta; no se modificó el ajuste elegido previamente por cada usuario. Falta QA visual real de los chips en móvil y ambos temas.

## 2026-09-13 — SES-036 — Popup persistente y cobertura zonal de prensa

- IDs: A09, A10, A11, V08.
- Cambio: el popup de prensa desactiva el cierre por click de MapLibre, que se propagaba desde el marcador en el mismo toque. El scraper extrae fecha editorial también desde metadatos HTML/JSON-LD y suma consultas agregadas específicas de zona norte, oeste, sur y La Plata.
- Pruebas: compilación sintáctica backend, lint y Vitest (80 pruebas) aprobados; `git diff --check` aprobado. Las nuevas pruebas unitarias del parser esperan el entorno de `pytest` pendiente.
- Límite: los nuevos feeds pueden repetir notas y deben evaluarse mediante las métricas por fuente; no se declara mayor precisión sin corrida real ni muestra humana.

## 2026-09-13 — SES-037 — Compatibilidad móvil y recuperación de fechas de prensa

- IDs: A09, A10, A11, V08.
- Cambio: los marcadores de prensa detienen `mousedown` y `touchstart` antes del click para que el mapa no cierre el popup en móvil. Se agregó el actualizador por lotes de `publicado_en` para noticias históricas sin fecha editorial.
- Límite: el actualizador requiere el Python/PostgreSQL funcional y sólo completa fechas que estén declaradas en la página fuente.

## 2026-09-13 — SES-038 — Estabilidad del popup y ejecución al iniciar

- IDs: A09, A10, A11, V08.
- Cambio: la lista filtrada de prensa se memoriza; el tick del reloj ya no reconstruye los marcadores ni cierra su popup. Los eventos táctiles detienen propagación sin cancelar el click. `iniciar.bat` abre una pestaña adicional de Scraper y ejecuta una corrida con guardado al iniciar la aplicación.
- Pruebas: lint y Vitest (80 pruebas) aprobados; `git diff --check` aprobado.
- Límite: la pestaña Scraper depende del `venv` y PostgreSQL; mientras el intérprete base roto persista, mostrará el error en esa pestaña y no insertará noticias.

## 2026-09-13 — SES-039 — Corrida real: URLs largas y continuidad de inserción

- IDs: A09, A14.
- Evidencia: Rodo ejecutó el scraper. La salida mostró muchas candidatas de medios directos y del agregador, pero se interrumpió al intentar guardar una URL de Google Noticias superior a 500 caracteres. Al confirmar al final de la transacción, esa interrupción puede haber revertido las inserciones de esa corrida.
- Cambio: `url_fuente` pasa a `TEXT` tanto en creación como compatibilidad de tabla. Cada inserción usa savepoint y omite sólo la fila que falle, sin perder las ya guardadas.
- Límite: falta repetir la corrida tras reiniciar el backend/scraper y comprobar el resumen final de guardadas por fuente.

## 2026-09-13 — SES-040 — Primera corrida completa multifluente

- IDs: A09, A10, A11.
- Evidencia aportada por Rodo: 560 candidatas, 16 duplicadas omitidas, 289 ubicadas y 267 nuevas guardadas; 99 candidatas estaban relacionadas con motos. La corrida finalizó sin abortar tras el arreglo de URLs largas.
- Aporte principal: Google Noticias guardó 234 noticias entre las consultas general, motos y zonales; Inforbano guardó 12; Infobae 7; el resto aportó entre 0 y 4 cada uno en esta corrida.
- Lectura: la ampliación logra volumen real, pero no equivale a precisión validada. La tasa global de ubicación fue 51,6% (289/560) y varios medios directos no ubicaron registros. El agregador puede solapar o redistribuir notas de esos mismos medios.
- Próximo paso: ejecutar actualización de fechas históricas, muestreo humano por fuente/categoría y corrección de falsos positivos/ubicaciones antes de usar estos conteos como indicador de incidencia.

## 2026-09-13 — SES-041 — Transparencia de noticias visibles

- IDs: A09, A11, V08.
- Cambio: el panel Prensa muestra cuántas noticias están cargadas y cuántas siguen visibles con el filtro activo. Evita interpretar los iconos superpuestos como el total de filas guardadas.
- Pruebas: lint y Vitest (80 pruebas) aprobados; `git diff --check` aprobado.
- Límite: los puntos con precisión de barrio/partido pueden compartir coordenada y solaparse visualmente. Queda pendiente agruparlos con contador en el mapa.

## 2026-09-13 — SES-042 — Agrupación de noticias en el mapa

- IDs: A09, A11, V08.
- Cambio: la capa de prensa agrupa noticias cercanas al alejarse y muestra un contador. Al tocar una agrupación, el mapa se acerca; al acercarse se muestran los marcadores individuales con su popup de noticia.
- Pruebas: lint y Vitest (80 pruebas) aprobados; `git diff --check` aprobado.
- Límite: la agrupación hace visible la cantidad, pero no corrige por sí sola ubicaciones de precisión barrial compartida ni duplicación semántica.

## 2026-09-13 — SES-043 — Noticias coincidentes seleccionables

- IDs: A09, A11, V08.
- Cambio: las noticias con la misma coordenada aproximada se reúnen en un marcador oscuro con ícono de diario y contador. Al abrirlo se presenta una lista desplazable con todas las notas del grupo; elegir una abre su detalle y fuente. Los agrupamientos al alejarse usan el mismo lenguaje visual de prensa, separado de los círculos de riesgo.
- Pruebas: `npm.cmd run lint`, Vitest (80 pruebas) y `git diff --check` aprobados.
- Límite: el grupo representa una coordenada compartida, no una ubicación exacta del hecho. La precisión geográfica y la deduplicación semántica siguen siendo trabajo pendiente de A09/A11.

## 2026-09-13 — SES-044 — Base reproducible para despliegue del MVP

- IDs: A12, A14, T01, T04, T06, A22.
- Cambio: se incorporaron imágenes de API y frontend, proxy same-origin `/api`, PostgreSQL/PostGIS privado, migraciones de arranque, healthcheck, volumen persistente y un proceso independiente de scraper configurable por intervalo. Se añadió ejemplo de secretos de producción, exclusiones de contexto Docker y guía de arquitectura, operación, backups y costos sin fijar precios variables.
- Corrección detectada al verificar: `/reportes-prensa` fallaba ante filas históricas sin `publicado_en`; ahora conserva `creado_en` como fecha de respaldo también en respuestas de transición.
- Pruebas: frontend lint, Vitest (80 pruebas) y build aprobados; backend `pytest` (61 pruebas) y compilación sintáctica aprobados; `git diff --check` aprobado.
- Límite: la sesión de Codex no dispone del ejecutable `docker`, por lo que no pudo ejecutar `docker compose ... config`, construir las imágenes ni ensayar PostGIS. No hay despliegue cloud, dominio, TLS, backup/restauración ni scheduler externo validados aún.

## 2026-09-13 — SES-045 — Blueprint de publicación rápida

- IDs: A14, T01, T04, T05, T06, A22.
- Cambio: se agregó `render.yaml` para aprovisionar desde GitHub una API privada, sitio público, cron de prensa y PostgreSQL 16. El frontend recibe el host interno de API en tiempo de ejecución; se añadió la migración versionada de PostGIS y se corrigieron las imágenes Docker para que una plataforma pueda reemplazar el comando de arranque del cron.
- Evidencia externa: documentación oficial de Render confirma Docker, Postgres con PostGIS y cron con ejecución exclusiva. El Blueprint usa base gratuita sólo para la validación inicial; no se declara producción sostenida porque vence a los 30 días.
- Pruebas: frontend lint, Vitest (80 pruebas) y build aprobados; backend `pytest` (61 pruebas) y compilación sintáctica aprobados; `git diff --check` aprobado. La sesión sigue sin Docker CLI para validar imagen o Blueprint contra el proveedor.

## 2026-09-13 — SES-046 — Reconstrucción académica con trazabilidad

- Alcance: se inició la reconstrucción de la tesis con las clases de Blackboard, la devolución docente, el proyecto vigente y el material anterior como fuente de errores a evitar.
- Cambio: se creó la matriz de requisitos/evidencia, el índice propuesto hasta Capítulo 5 y un registro inicial de declaración de uso de IA. Se separan explícitamente hechos comprobados, validaciones pendientes y supuestos económicos.
- Límite: aún falta completar la bibliografía primaria, decisiones económicas de Rodolfo y evidencia empírica/de despliegue. No se declara redactada ni validada la tesis final.

## 2026-09-13 — SES-016 — Movimiento reducido

- IDs: A23, V09.
- Cambio: se respetan preferencias de reducción de movimiento, suprimiendo animaciones y transiciones no esenciales.
- Pruebas: lint y 75 pruebas frontend aprobadas.

## 2026-09-13 — SES-017 — Objetivos táctiles principales

- IDs: A23.
- Cambio: controles de tema y capas se ampliaron a 44 px, consistentes con zoom y navegación.
- Pruebas: lint y 75 pruebas frontend aprobadas.

## 2026-09-13 — SES-018 — Menú accesible

- Cambio: el botón de herramientas comunica su estado expandido a lectores de pantalla.

## 2026-09-13 — SES-019 — Semántica de gravedad en interfaz

- IDs: A01.
- Cambio: el detalle de zona identifica la salida como gravedad estimada si ocurre un siniestro y aclara que no estima ocurrencia durante el viaje.
- Pruebas: lint y 75 pruebas frontend aprobadas.

## 2026-09-13 — SES-020 — Cobertura registrada de rutas

- IDs: A05, A06.
- Cambio: se calcula qué porción del trazado queda cerca de zonas registradas; rutas bajo 60% no se presentan como de menor exposición y muestran cobertura insuficiente.
- Pruebas: lint, 76 pruebas frontend y build aprobados.
- Límite: proximidad a zonas registradas no equivale aún a cobertura geográfica independiente por fuente.

## Plantilla reutilizable

### AAAA-MM-DD — SES-XXX — Título

- Pedido / alcance autorizado:
- IDs del backlog:
- Estado anterior y problema:
- Qué se cambió y por qué:
- Archivos y datos/artefactos afectados:
- Pruebas ejecutadas, resultado y ubicación de evidencia:
- Qué no se pudo validar y por qué:
- Decisiones relacionadas:
- Pendientes / próximo paso:
- Commit o “sin commit”; ramas/despliegues si corresponden:
# SES-047 — 2026-09-14 — Integridad de fuentes de prensa y estructura de tesis

- Alcance: A09, G01 y reconstrucción de tesis.
- Decisión: Rodo confirmó retirar Google Noticias como fuente de ingesta; la decisión se registra como DEC-011. Se eliminaron las seis consultas RSS del scraper y la normalización exclusiva del agregador.
- Corrida real posterior: con sólo fuentes directas, `scrapear_noticias_robos.py --guardar` encontró 122 candidatas (16 choque, 37 inseguridad y 69 robo), omitió 1 duplicada, ubicó 57 y guardó 4 noticias nuevas. Se detectaron 20 candidatas relacionadas con moto. Por fuente, las cuatro inserciones nuevas provinieron de 0221 (3) e Infocielo (1).
- Comparabilidad: la corrida histórica del 2026-09-13 (560 candidatas, 289 ubicadas y 267 guardadas) incorporaba 234 guardadas desde Google Noticias. Se preserva como evidencia histórica de un alcance retirado y no se usa como referencia de cobertura vigente.
- Documentación: `INGESTA_PRENSA_MULTIFUENTE.md` explica el retiro y sus límites; `02_INDICE_PROPUESTO.md` y el borrador maestro ahora separan Capítulo 3 Marco teórico y tecnológico, Capítulo 4 Arquitectura y diseño, Capítulo 5 económico, y los futuros capítulos 6 Riesgos, 7 Resultados y 8 Conclusiones.
- Validación: prueba real completa del scraper contra fuentes directas, con guardado en PostgreSQL. Pendiente: muestra humana de precisión, deduplicación semántica y ampliar fuentes con vías permitidas.

## 2026-09-14 — SES-048 — Identificación del modelo vigente y actas

- IDs: A01–A04, D01, G05.
- Cambio: se reprodujo `backend/modelo_final.pkl` sin reentrenar ni sobrescribir datos. El artefacto vigente usa 23.338 filas, 55 columnas, Random Forest de 300 árboles, profundidad 12, mínimo 5 muestras por hoja y `balanced_subsample`.
- Resultado reproducido: split interno estratificado 80/20 con semilla 42; F1 macro 0,3782; GRAVE precision/recall 0,1107/0,7346; MORTAL precision/recall 0,1159/0,4821. Los valores de Fase 4 corresponden al modelo previo de 66 columnas y no se deben mezclar.
- Documentación: se creó `docs/modelo/MODELO_VIGENTE_2026-09-07.md` como referencia única para la tesis y `docs/gestion/ACTAS_TUTOR.md` como registro central actualmente vacío.
- Límite: se reprodujo una evaluación interna, no una evaluación temporal independiente. No hay actas ni aprobación de tutor verificables registradas.

## 2026-09-14 — SES-049 — Redacción de Capítulos 1 a 5 de la tesis (Claude)

- Alcance: entrega de Capítulos 1 a 5 exigida por la cátedra hasta la Entrega 6. Trabajo realizado por Claude sobre la documentación técnica ya centralizada en `docs/`, sin modificar código, datos ni el modelo.
- Verificación previa: se releyeron en frío `docs/README.md`, `docs/gestion/CONTINUIDAD.md`, `BACKLOG.md`, `DECISIONES.md`, `ACTAS_TUTOR.md`, `docs/modelo/CONTRATO_Y_EVALUACION.md` y `MODELO_VIGENTE_2026-09-07.md`, `docs/datos/FICHA_SINIESTROS_MOTO.md`, `docs/riesgo/PROCEDENCIA_Y_COBERTURA.md` e `INGESTA_PRENSA_MULTIFUENTE.md`, `docs/operacion/DESPLIEGUE_MVP.md` y `BACKEND_Y_BASE_DE_DATOS.md`, `docs/entrega/MATRIZ_ACADEMICA_Y_DEMO.md`, `docs/calidad/QA_ACCESIBILIDAD_VISUAL.md` y los cuatro archivos de `docs/tesis/`. No se detectó ninguna inconsistencia técnica pendiente de aclarar con Codex; la reestructuración de capítulos de SES-047 estaba correctamente aplicada en el índice y en el borrador maestro.
- Decisiones del autor incorporadas: alcance de la defensa centrado en CABA (GBA como capa de ruteo/exploración sin cobertura predictiva validada), y pregunta de investigación/hipótesis de trabajo para 1.6, ambas confirmadas por Rodo el 2026-09-14.
- Bibliografía: se incorporaron 10 fuentes primarias verificadas por acceso directo (OMS, CAF, tesis de maestría UTDT, dos papers revisados por pares sobre severidad de siniestros y SIG, un paper revisado por pares sobre confiabilidad de datos colaborativos de Waze, documentación oficial de scikit-learn sobre fuga de datos, WCAG 2.2, y dos coberturas periodísticas que citan cifras de ANSV), superando el mínimo de 5 fuentes exigido por la cátedra para esta entrega.
- Resultado: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5.docx` (24 páginas), entregado a Rodo. Mantiene como pendiente explícito, sin presentarlo como resuelto: ejecución de la evaluación temporal independiente (entorno roto), medición de calidad del extractor de prensa con conjunto humano etiquetado, primera acta de tutor, y definición de supuestos económicos (usuarios, financiamiento, horizonte) para el cálculo de VAN/TIR del Capítulo 5.
- Pendiente / próximo paso: Rodo revisa el borrador; si lo aprueba, se actualiza `docs/tesis/01_DECLARACION_IA_Y_REGISTRO.md` con esta intervención y se define si el Capítulo 5 avanza con supuestos económicos provisorios o queda a la espera de una decisión formal en `DECISIONES.md`.
- Commit: sin commit todavía; el archivo se copió directamente a `docs/tesis/` en el equipo de Rodo.

## 2026-09-14 — SES-050 — Revisión integral de la tesis contra requisitos de cátedra (Claude)

- Alcance: Rodo pidió no dar por final el Word de SES-049 y, antes de eso, incorporar y priorizar los 11 PDF de clases de la cátedra (Clases 1-9 y 11) más el trabajo de un compañero, usado explícitamente solo como referencia de formato y profundidad, nunca como fuente de contenido, datos, cálculos o conclusiones.
- Método: 4 subagentes en paralelo leyeron los 11 PDF de cátedra y extrajeron requisitos exactos (estructura de Capítulo 1, método y fórmulas de factibilidad económica de la Clase 9, contenido esperado de arquitectura/marco tecnológico de la Clase 8, y las seis conductas exigidas por la Clase 5 para la declaración de uso de IA). No se copió texto, dato ni tabla del trabajo del compañero.
- Capítulo 5 reescrito de punta a punta: se abandonó la versión que dejaba todo pendiente ("sin supuestos aprobados no se calcula nada") y se reemplazó por un ejemplo numérico completo con supuestos explícitos y diferenciados de los hechos verificados: inversión inicial (USD 1.500), costos operativos proyectados a 5 años con crecimiento del 10% anual, escenario de ingresos por auspicios y licencia de datos a municipios/aseguradoras (supuesto, sin contacto comercial real), flujo de fondos a 5 años, tasa de descuento construida con el método de tres componentes de la Clase 9 (bono del Tesoro de EE. UU. a 10 años ~4,8% de septiembre de 2026, riesgo país argentino EMBI+ 485 pb al 11/09/2026, y una prima de riesgo del proyecto del 7% como supuesto), VAN (~USD 37), TIR (~17,5%), recupero simple (~4 años y 2 meses) y descontado (~4 años y 11 meses), y un análisis de sensibilidad que muestra que un sobrecosto del 20% o una adopción de ingresos 20% más lenta bastan para volver el VAN negativo.
- Verificación de pruebas contra el repositorio real (no contra una cifra supuesta): se contaron directamente los bloques `it()`/`test()` y `def test_` en el repositorio de Rodo vía el puente al dispositivo. Resultado: 80 pruebas de frontend (17 tiempo.test.js + 30 geoRiesgo.test.js + 31 riesgoRuta.test.js + 2 storage.test.js) y 61 de backend (53 test_main.py + 8 test_scrapear_noticias_robos.py, este último no contemplado en la cifra anterior de 55). Se corrigió la cifra en el Capítulo 4 (antes 73/55).
- Diagramas agregados: arquitectura de componentes (Figura 4.1), modelo de datos con entidades y relaciones (Figura 4.2), y flujo de ingesta de prensa (Figura 4.3), generados con matplotlib y embebidos en el Word con pie de figura numerado.
- Fuente ANSV: el PDF oficial de diagnóstico de la ANSV está bloqueado por robots.txt (no se intentó sortear esa restricción). Se ubicó y citó como fuente oficial secundaria un artículo (Infoecos, 2025) que atribuye explícitamente el dato del 46% de víctimas fatales motociclistas a "datos oficiales de la ANSV de 2025", y se referencia en 1.2 y 3.1 junto con las coberturas periodísticas ya citadas.
- Índice con páginas: se implementó un render en dos pasadas (build sin índice → medir página real de cada encabezado sobre el PDF renderizado → insertar página de índice con tabulaciones de puntos y reconstruir) para que el índice muestre número de página real y verificado, no estimado.
- Apéndice de prompts: se agregó un Apéndice B al Word con el detalle de los prompts de mayor impacto de esta sesión (fecha, herramienta, pedido y uso del resultado), conforme al pedido explícito de la Clase 5 ("guardá los prompts, como apéndice o en la carpeta de Drive del proyecto").
- Capturas de pantalla: declaradas explícitamente como pendientes en la sección 4.9 del documento, con la razón concreta (sin URL de despliegue confirmada ni acceso a navegador sobre la máquina del proyecto desde este entorno) y la acción pendiente a cargo de Rodo. No se fabricaron ni simularon.
- Verificación visual: el Word se renderizó a PDF (33 páginas) y se revisó página por página, incluyendo las tres figuras, las tablas de Capítulo 5 y el índice, antes de la entrega.
- Resultado: segunda versión de `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5.docx`, entregada a Rodo y copiada a `docs/tesis/` en su equipo. `docs/tesis/01_DECLARACION_IA_Y_REGISTRO.md` actualizado con esta intervención.
- Pendiente / próximo paso: Rodo debe tomar y agregar las capturas reales de la aplicación (mapa, comparador de rutas, alta de reporte); primera acta de tutor sigue sin registrar; evaluación temporal independiente del modelo sigue pendiente por el entorno Python roto.
- Commit: sin commit todavía; el archivo se copió directamente a `docs/tesis/` en el equipo de Rodo.

## 2026-09-14 — SES-051 — Revisión final y entrega del Word (Claude)

- Alcance: Rodo pidió la última revisión integral del Word de SES-050 y una versión final nueva y entregable en `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5_FINAL.docx`, sin resumen previo, releyendo antes `AGENTS.md`, `docs/README.md`, toda `docs/gestion/`, la ficha del modelo vigente, el contrato de evaluación, la ingesta de prensa multifuente y los dos documentos de tesis existentes.
- Capturas de pantalla (punto 1 del pedido): antes de declarar el faltante se intentó de nuevo obtenerlas por las dos vías disponibles. Se revisó el repositorio completo en busca de imágenes (única encontrada: `frontend/src/assets/hero.png`, el gráfico genérico de la plantilla Vite/React, no una captura real) y se revisó el proyecto de Claude vinculado a esta tesis (cero archivos de imagen cargados). El puente al dispositivo de Rodo no tiene navegador disponible desde este entorno. Con las dos vías agotadas y sin resultado, la sección 4.9 se reescribió como una tabla de cuatro figuras pendientes (mapa con capas, panel de prensa con filtro Motos, comparador de rutas, vista móvil o de red degradada), cada una con lo que debe mostrar y qué evidencia aporta, en lugar del párrafo genérico anterior. No se incorporó ninguna imagen fabricada.
- Capítulo 5 (punto 2): se revisó la aritmética de VAN, TIR y recupero de SES-050 y no se encontraron errores (se verificó de forma independiente con un script). Se agregó una tabla única de supuestos en 5.1 que consolida horizonte, moneda, depreciación, tasa de descuento, crecimiento de costos, escenario de ingresos e inversión inicial, para que 5.2 a 5.6 se lean sobre el mismo conjunto y no como cifras sueltas por sección. En 5.6 se agregó, además de los dos desvíos de una variable ya existentes, una tabla de tres escenarios combinados (optimista +USD 799, base +USD 37, pesimista -USD 1.181, este último combinando el sobrecosto del 20% y la adopción de ingresos 20% más lenta), calculados y verificados con la misma tasa de descuento del 17%.
- Bibliografía (punto 3): se auditó cada cita en texto contra la lista de referencias y viceversa; las 13 fuentes de SES-050 están todas citadas y ninguna cita queda sin referencia. Se corrigieron dos inconsistencias de forma (la cita en texto de OMS decía "WHO, 2023" contra una referencia encabezada "World Health Organization"; la de accesibilidad decía "W3C, 2024" contra una referencia encabezada "World Wide Web Consortium"): ambas se homologaron sin cambiar la fuente citada. No se agregó ninguna fuente nueva no verificada; la estadística de ANSV se mantiene respaldada por tres fuentes (Infoecos como atribución a datos oficiales, más La Nación y Dato Posta como coberturas independientes), no por una sola.
- Diagramas (punto 4): los tres diagramas de SES-050 se rediseñaron para distinguir explícitamente, con leyenda y estilo de línea (sólido/discontinuo/punteado), componentes implementados y verificados, preparados pero no validados, y pendientes. En el diagrama de arquitectura se agregó un recuadro punteado "Despliegue productivo (Render)" marcado como no ejecutado, y el Scheduler de prensa quedó marcado como preparado en la nube pero verificado solo en ejecución local; en el diagrama de flujo de prensa se agregó la misma distinción y una nota explícita de que Google Noticias fue retirado el 14/09/2026 y no es fuente vigente.
- Coherencia técnica (punto 5): se mantuvieron sin cambios las cifras de la ficha vigente (Random Forest, 23.338 filas, 55 columnas, 300 árboles, profundidad 12, hojas mínimas 5, balanced_subsample, F1 macro 0,3782, recalls/precisiones de GRAVE y MORTAL) y las 80 pruebas de frontend / 61 de backend de SES-050; no se volvió a contar porque no hubo cambios de código en esta sesión.
- Trazabilidad (punto 6): se actualiza `01_DECLARACION_IA_Y_REGISTRO.md` con esta intervención y se agrega una fila al Apéndice B del Word. `docs/gestion/ACTAS_TUTOR.md` sigue referenciado en el Apéndice A del documento con la declaración explícita de que no hay actas cargadas.
- Formato (punto 7): se regeneró el índice en dos pasadas sobre el documento final (build sin índice → medir página real por encabezado → reconstruir con índice), Times New Roman y texto negro en todo el documento, tablas con `cantSplit` para no partirse a mitad de fila, y se revisaron las 35 páginas del PDF renderizado una por una (portada, índice, los tres diagramas, las tablas nuevas de Capítulo 5, la tabla de capturas pendientes, bibliografía y apéndices) sin encontrar cortes, páginas vacías, tablas rotas ni texto de placeholder residual.
- Limitación de herramientas señalada a Rodo: el puente al dispositivo de Rodo (`device_bash`) sigue sin funcionar en este entorno (mismo error de montaje reportado desde el inicio de la sesión), por lo que Claude no puede ejecutar `git commit`/`git push` en su equipo; el archivo final se entregó por descarga y se copió a `docs/tesis/` en su equipo mediante el puente de archivos. El commit y push quedan a cargo de Rodo.
- Resultado: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5_FINAL.docx` (35 páginas), entregado a Rodo y copiado a `docs/tesis/` en su equipo.
- Pendiente / próximo paso: Rodo debe tomar las cuatro capturas reales listadas en la Figura 4.4 a 4.7 y reemplazar la tabla de 4.9; hacer el commit y push del archivo final; primera acta de tutor sigue sin registrar; evaluación temporal independiente del modelo sigue pendiente por el entorno Python roto.
- Commit: sin commit; pendiente a cargo de Rodo en su equipo.

## 2026-09-14 — SES-052 — Instrumentos de validación y estructura preliminar de tesis (Codex)

- Alcance: tras revisar el Word final y una tesis de referencia de la misma carrera, se corrigieron faltantes formales detectados: el resumen no estaba en el frente del documento y no existía instrumento preparado para pruebas con usuarios. La tesis externa se usó sólo como referencia visual y de estructura; no se copió texto, datos, encuestas ni conclusiones.
- Resultado documental: se creó `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx`, conservando el original. La revisión incorpora Resumen y Abstract preliminares, listas de figuras y tablas, y el Apéndice A con cuestionario y cuatro tareas de prueba. El resumen duplicado se retiró del inicio del Capítulo 1.
- Instrumento: se creó `docs/tesis/03_INSTRUMENTOS_VALIDACION_USUARIOS.md` y se replicó en el Apéndice A del Word. Define criterios de participantes, consentimiento breve, tareas observables, preguntas y reglas de análisis. Es un protocolo preparado; no se realizaron encuestas ni se generaron resultados.
- Backlog: G02 pasó a "En curso" porque existe el instrumento; su criterio de cierre sigue pendiente de aplicación real, muestra, registro y límites.
- Límites: las cuatro capturas reales de la aplicación continúan pendientes; tampoco se alteraron las limitaciones de evaluación temporal del modelo, despliegue ni actas de tutor. La revisión visual de la nueva versión requiere renderizador Word/LibreOffice disponible antes de declararla versión final.
- Commit: pendiente de esta sesión.

## 2026-09-14 — SES-053 — QA visual y corrección de REVISION_02.docx (Claude)

- Alcance: Codex generó `MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` sobre el FINAL de SES-051 (Resumen/Abstract bilingüe, remoción del resumen duplicado en 1.1, Apéndice A con instrumento de validación de usuarios) y pidió explícitamente, por no poder abrir Word desde su sesión: "Abrí la revisión en Word, actualizá los números de página y revisá visualmente el resultado antes de reemplazar la versión final." Esta sesión hizo esa revisión.
- Método: se comparó REVISION_02.docx página por página contra FINAL.docx (ambos renderizados a PDF e imagen) para aislar qué cambió el edit de Codex de lo que ya venía de antes.
- Hallazgo 1 (contenido, correcto): el Apéndice A no inventa resultados. Se verificó contra `03_INSTRUMENTOS_VALIDACION_USUARIOS.md` y coincide: protocolo de instrumento con estado explícito "preparado para aplicación; no contiene resultados ni participantes", sin encuestas ni muestras simuladas. El resumen duplicado de 1.1 se removió limpiamente del Capítulo 1, sin texto residual.
- Hallazgo 2 (formato, defecto encontrado y corregido): 13 encabezados quedaron sin la sobreescritura de fuente que usa el resto del documento (Times New Roman, negro, negrita) y por eso heredaban el estilo "Heading 2"/"Heading 1" por defecto de Word (azul, sin negrita): Resumen/Abstract, los seis subtítulos de 1.1 a 1.6, y los seis títulos del Apéndice A completo. Se identificó comparando el XML de un encabezado roto contra uno intacto (por ejemplo 2.1, que sí conservaba el `rPr` con Times New Roman/negro) y se corrigió agregando el mismo `rPr` a los 13 párrafos afectados, directamente en `word/document.xml`, sin tocar el texto.
- Hallazgo 3 (formato, defecto encontrado y corregido): la tabla de la Encuesta A.2 (12 ítems) no tenía bordes negros ni `cantSplit` en las filas, a diferencia de todas las demás tablas del documento, y una fila se cortaba a mitad de página. Se agregaron bordes simples negros y `cantSplit` + encabezado repetido en todas las filas, igual que en las tablas de Capítulo 2 y 4.
- Hallazgo 4 (índice, defecto encontrado y corregido): el índice tenía tres "[actualizar al renderizar]" literales sin resolver (Resumen/Abstract, Apéndice A, y una regresión en Apéndice B que en el FINAL sí tenía número real) y las entradas 1.1 a 1.6 no tenían el `rPr` de sus pares. Se recalculó el paginado real renderizando el documento ya corregido a PDF (37 páginas) y localizando cada encabezado con `pdftotext -layout`, y se reescribieron las 13 entradas del índice con número de página verificado, en vez de aceptar la sugerencia de Codex de resolverlo manualmente abriendo Word (no reproducible ni verificable por Rodo).
- Verificación: `validate.py` contra el REVISION_02.docx original de Codex pasó todas las validaciones XSD (531→532 párrafos, la diferencia es el desdoblamiento de la entrada combinada Apéndice A/B en dos líneas de índice independientes). Render completo a PDF e inspección página por página de las 37 páginas, incluyendo portada, índice completo, Capítulo 1 completo, y el Apéndice A completo.
- Resultado: `docs/tesis/MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` (37 páginas) sobrescrito en el equipo de Rodo con la versión corregida. El archivo de Codex previo a esta corrección no se conservó aparte; el historial de Git es la referencia si hace falta compararlo.
- Limitación de herramientas: `device_bash` sigue sin funcionar en este entorno (mismo error de montaje por la actualización de Windows del 8/9). El archivo corregido se entregó por descarga y se sobrescribió en `docs/tesis/` del equipo de Rodo mediante el puente de archivos, sin poder ejecutar `git commit`/`git push`.
- Pendiente / próximo paso: Rodo revisa el resultado y, si lo aprueba, hace el commit y push de `MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` (y decide si pasa a llamarse la nueva versión final, reemplazando a `_FINAL.docx`); las capturas reales de 4.9, la primera acta de tutor y la evaluación temporal independiente del modelo siguen pendientes sin cambios en esta sesión.
- Commit: sin commit; pendiente a cargo de Rodo en su equipo.

## 2026-09-14 — SES-054 — Endurecimiento de `/reportes` y observabilidad (Claude)

- Alcance: antes de exponer la app a desconocidos (piloto vía Reddit), Rodo pidió revisar qué faltaba corregir en el backend y aplicar los cambios necesarios. Se acotó a A07 (borrado/votos) y T04 (observabilidad) del backlog, que eran los relevantes para exposición pública.
- Diagnóstico contra el código real (no contra lo que decía el backlog): A07 estaba más resuelto de lo que indicaba la fila del backlog. Ya existían migración versionada (`migrar.py` + `001_reportes_colaborativos.sql`, coincide con el esquema que espera el código), rate limiting por IP en creación/voto/predicción, UUID validado en `autor_id`, anti-autovoto, anti-doble-voto por dispositivo (UNIQUE) y retiro por consenso con doble umbral. Dos gaps reales sí se confirmaron: `DELETE /reportes/{id}` no tenía rate limit (inconsistente con el resto de escrituras) y no había ninguna cuota por dispositivo, solo por IP (un NAT compartido o volumen sostenido durante el día no quedaban cubiertos por el límite de 20/min).
- Cambios aplicados en `backend/main.py`: `@limiter.limit("20/minute")` agregado a `borrar_reporte`; cuota `CUOTA_REPORTES_POR_DIA_POR_AUTOR = 15` (reportes por `autor_id` en 24 horas, verificada contra la base antes del INSERT, devuelve 429 si se supera) en `crear_reporte`; middleware de métricas (`_middleware_metricas`) y endpoint nuevo `/metrics` que expone conteo de requests, errores 4xx/5xx y latencia promedio por ruta, en memoria del proceso, sin claves, tokens ni datos de usuario.
- Verificación: se clonó el entorno (venv + `requirements.txt`) en este entorno para correr los tests reales de `backend/tests/test_main.py` contra el código modificado, no solo lectura. El mock `_mock_db_reportes` se actualizó para reflejar que `crear_reporte` ahora llama `fetchone()` dos veces (conteo de cuota + RETURNING del insert). Se agregaron 4 tests nuevos (cuota alcanzada devuelve 429, cuota un reporte por debajo del límite deja pasar, `/metrics` registra conteo/latencia sin exponer `DATABASE_URL`, `/metrics` cuenta un error 4xx real). Resultado: 57/57 tests pasan (53 preexistentes + 4 nuevos), sin tocar la lógica de negocio existente.
- Lo que quedó explícitamente fuera de este alcance (no tocado): A18 (límite de gasto en el panel de TomTom) es una configuración de cuenta externa, no código — queda a cargo de Rodo. A12 (probar el pool de conexiones contra PostgreSQL real bajo carga concurrente) no se hizo: el puente de comandos a la máquina de Rodo sigue roto y este entorno no tiene su base real; los tests corridos usan mocks, no una base real.
- Resultado: `backend/main.py` y `backend/tests/test_main.py` actualizados y sobrescritos en el equipo de Rodo.
- Pendiente / próximo paso: Rodo revisa el diff y hace el commit/push (el puente de comandos sigue caído); configurar el límite de gasto en TomTom antes de compartir cualquier link público; A12 (carga real contra Postgres) queda pendiente hasta que haya un entorno con base real disponible, sea local o en Render.
- Commit: sin commit; pendiente a cargo de Rodo en su equipo.

## 2026-09-15 — SES-055 — Comparación con compañero, principio de versionado y sincronización de REVISION_02 con el backend (Claude)

- Alcance: (1) push de los tres commits de la sesión anterior (bloqueado, ver abajo); (2) comparación objetiva de MotoSafe GBA contra el trabajo de un compañero (Grupo 3, GoPilot, 83 páginas, capítulos 1 a 5 completos) contra los criterios de evaluación de la cátedra; (3) marcar en el Word, de forma visible, qué falta completar en la encuesta (Apéndice A) y en las capturas (4.9); (4) registrar como principio de gestión que un capítulo ya entregado no se reescribe retroactivamente; (5) sincronizar el texto de REVISION_02.docx con los cambios de backend de SES-054, que habían quedado desactualizados en el documento.
- Bloqueo de infraestructura resuelto: `.git/index.lock` obsoleto (de una corrida anterior) impedía cualquier operación de git. Se solicitó y obtuvo permiso de borrado en la carpeta del proyecto, se eliminó el lock y se hicieron los 3 commits pendientes (d5ab2fc, 73d8fd1, 2ed93e4). El `git push` a `origin/main` falló: la máquina de Rodo no tiene credenciales de git configuradas para ese remoto (ni credential helper ni `gh`); queda a cargo de Rodo autenticar y pushear.
- Comparación contra el compañero: 12 referencias propias vs. ~35 de ellos, pero las suyas tienen duplicados y una entrada sin completar (`[Completar con...]`); ellos tienen una encuesta real ejecutada (89 respuestas) usada en el Capítulo 5, MotoSafe todavía no; ellos tienen capturas reales de la app en emulador, MotoSafe no; MotoSafe tiene 65 tests automatizados corriendo hoy contra el código real, la sección de QA de ellos (4.11) está escrita en futuro/aspiracional sin evidencia ejecutada; MotoSafe tiene una declaración de uso de IA como capítulo propio (2.7) con trazabilidad completa, ellos no tienen ese apartado. Conclusión entregada a Rodo: el documento propio es más riguroso en honestidad metodológica, más débil en evidencia empírica de usuario (exactamente los dos puntos ya identificados como pendientes).
- Cambios en el Word (todos verificados con `validate.py` y render a PDF página por página antes de entregar):
  - Nota resaltada (rojo/amarillo) en A.3, indicando que las preguntas ya están armadas en A.2 y que falta completar resultado real y análisis, no preguntas nuevas.
  - Nota resaltada (celeste/azul) después de la tabla de figuras de 4.9, resumiendo qué debe mostrar cada una de las 4 capturas pendientes; las etiquetas "(pendiente)" de la tabla se resaltaron en el mismo color para ubicarlas rápido. Ambas notas están marcadas explícitamente como "borrar antes de entregar".
  - Nuevo párrafo al final de 2.6: un capítulo ya entregado no se reescribe para acomodar hallazgos de un capítulo posterior; toda tensión se registra en el backlog con fecha y capítulo afectado, y se resuelve hacia adelante; una corrección retroactiva solo ocurre si la pide el tutor, documentada como tal.
  - Nuevo párrafo al final de 1.6: las decisiones tecnológicas ya tomadas (Docker, Blueprint de Render, TomTom) se adoptaron pensando en la operación futura, con referencia cruzada a 3.8, 4.10 y Capítulo 5, donde ya se costean.
  - Corrección en 4.10: el conteo de tests del backend estaba desactualizado (decía 61; ya son 65 desde SES-054: 57 en test_main.py + 8 en test_scrapear_noticias_robos.py).
  - Corrección en 4.8: ya no dice que la cuota de reportes está pendiente (se implementó en SES-054); se agregó la descripción de la cuota diaria de 15/24h, el rate limit del DELETE y el endpoint /metrics.
  - Corrección en 5.2: se sacó "cuotas de envío de reportes" de la lista de tareas de endurecimiento todavía pendientes (ya está hecho) y se agregó una aclaración explícita de que el trabajo hundido excluido de la inversión inicial incluye tanto las horas propias del autor como las de los asistentes de IA usados bajo su supervisión, y por qué (no cambia una decisión de inversión que mira hacia adelante).
- Decisión registrada (a pedido de Rodo, no ejecución mía): no se van a valorizar monetariamente las horas de desarrollo (propias ni de IA) en el Capítulo 5, ni siquiera como referencia informativa al estilo del compañero. Motivo: es una convención distinta a la de GoPilot, no una corrección; excluir el trabajo hundido es la práctica estándar para una decisión de inversión hacia adelante, y monetizar "horas de IA" no tiene una tarifa defendible y podría contradecir la declaración de 2.7 de que la IA es una herramienta de apoyo bajo decisión del autor, no un recurso contratado por hora.
- Limpieza: se habían generado archivos `MotoSafe_GBA_Capitulos_1_a_5_REVISION_03.docx` a `_06.docx` como pasos intermedios de edición; se consolidó todo en `MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` (nombre canónico) y se borraron los archivos intermedios de la carpeta de Rodo.
- Resultado: `MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` actualizado en el equipo de Rodo, consistente con el estado real del backend.
- Pendiente / próximo paso: push de los 3 commits (autenticación de git a cargo de Rodo); encuesta real y capturas reales (marcadas en el documento); acta de la primera reunión con el tutor; evaluación temporal independiente del modelo (A02) y medición de calidad del extractor de prensa (A09), ambas sin cambios en esta sesión.
- Commit: pendiente de incluir en el próximo commit (REVISION_02.docx, esta bitácora y BACKLOG.md).

## 2026-09-15 — SES-056 — Costeo histórico completo, precios reales de IA, evaluación temporal ejecutada (A02-A04) y corrección de numeración del índice (Claude)

- Alcance: continuación de SES-055 en la misma jornada, a partir de tres decisiones e instrucciones directas de Rodo: (1) revertir la decisión de no monetizar horas de desarrollo, incluyendo TODAS las horas (propias y de los asistentes de IA) sin excluirlas como trabajo hundido; (2) usar precios reales verificables de las suscripciones de IA en vez de un placeholder; (3) "usa tu criterio para todo pero hazlo" y luego "hazlo tú hasta finalizar" — ejecutar todo lo que fuera genuinamente ejecutable sin esperar más confirmaciones, dejando solo lo que depende de una acción real de Rodo (encuesta, capturas, acta de tutor, autenticación de git).
- Decisión de costeo (reversión de SES-055): se agregó la sección **5.2.1 "Costo total histórico del proyecto (informativo)"** en el Capítulo 5, separada de la inversión inicial de 5.2 y del VAN/TIR de 5.5 (que siguen mirando solo hacia adelante). Incluye 340 horas totales (investigación y definición 80h, desarrollo e integraciones 220h, auditoría técnica y documentación 40h) valorizadas a USD 12/h siguiendo la misma convención que el compañero (GoPilot), más el costo real de las suscripciones de IA usadas (Claude y ChatGPT/Codex): USD 40 en el primer mes (ambas herramientas activas) y USD 20/mes desde el segundo mes (solo Claude), total USD 60 en dos meses. Costo total histórico estimado: USD 4.140. Se deja explícito que esta cifra es informativa y no entra en el cálculo de rentabilidad del proyecto hacia adelante.
- Precios de IA: reemplazado el placeholder anterior por los precios reales que dio Rodo (USD 20/mes Claude, USD 20/mes ChatGPT solo el primer mes). El total no cambió (USD 60 en dos meses coincide con la estimación previa), pero ahora es un hecho verificable, no una suposición.
- Evaluación temporal independiente del modelo (A02, A03, A04 del backlog): se identificó que el protocolo ya estaba implementado (`notebooks/evaluar_modelo_academico.py`) pero nunca ejecutado. Se ejecutó de forma real sobre los datos existentes: entrenamiento 2019-2022 (11.644 filas), selección de hiperparámetros sobre 2023 (3.915 filas), evaluación sobre 2024 como año completamente posterior (3.331 filas), sin tocar el artefacto en producción. Resultado: F1 macro cae de 0,378 (reconstrucción del split aleatorio interno) a 0,262 en evaluación temporal real (intervalo bootstrap 95%: [0,244; 0,281]). Ablaciones: sin edad, F1 macro evaluación 0,286; sin edad ni sexo, 0,362 — ambas variantes generalizan mejor entre años que la que incluye demografía, es decir, la demografía disponible no aporta señal estable entre años en este dataset (no se infiere causalidad). ECE similar entre variantes (0,30-0,32), sin calibración aplicada todavía. Proporción de edad desconocida: 45% en entrenamiento/selección vs. 12% en el año de evaluación, diferencia de completitud documentada como limitación de la comparación. Evidencia archivada en `docs/evidencias/2026-09-15/A02-A03-A04/` (`reporte_modelo_temporal.json`, `resumen_modelo_temporal.csv`).
- Propagación de los resultados: se actualizó `docs/modelo/MODELO_VIGENTE_2026-09-07.md` con una sección nueva de evaluación temporal ejecutada; se agregaron dos párrafos y una tabla de resultados en la sección 4.4 del Word, inmediatamente después de las cifras del split aleatorio interno, con la distinción explícita entre ambas evaluaciones; se actualizó 1.6 para reflejar que la evaluación ya se ejecutó (antes decía que estaba pendiente).
- Backlog: A02 y A03 pasan de "En curso" a "Validado parcialmente" (falta revisión con dirección académica). A04 sigue "En curso": el ECE real ya está calculado, pero falta la matriz de confusión detallada en el informe y una decisión explícita de costos/umbrales de alertas.
- Bug encontrado y corregido (numeración del índice): al insertar la nueva sección 5.2.1 se asumió un offset constante de página (página impresa = página del PDF − 2), calibrado con una sola comparación. Era incorrecto: el documento no tiene campo de número de página en el pie — el índice es texto tipeado manualmente — y el offset real es 0 (página del PDF = número impreso). Se verificó comparando "Resumen/Abstract" (PDF pág. 2, índice decía "2") y "Capítulo 1" (PDF pág. 6, índice decía "6"), y se reconstruyó un localizador preciso que escaneó cada página del PDF renderizado (41 páginas) para recalcular correctamente las 42 entradas del índice desde el Capítulo 2 hasta el Apéndice B. Verificado tras la corrección: las 42 entradas coinciden exactamente con la página real del PDF (offset 0 confirmado en todos los casos de control).
- Verificación final: `validate.py --original` sin errores (583 párrafos, sin cambios de estructura), render completo a PDF (41 páginas), revisión visual del índice (págs. 3-4) y de la sección 4.4 (págs. 20-21) antes de entregar.
- Limpieza: se consolidaron nuevamente los archivos intermedios (`v7.docx` a `v12.docx`) en el nombre canónico `MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx`.
- Corrección de un defecto pre-existente en BACKLOG.md: la tabla "Ejecución actual" tenía filas A01-A04 duplicadas por un error de edición de una sesión anterior; se eliminó la duplicación al mismo tiempo que se actualizaron los estados.
- Pendiente / próximo paso: revisión con dirección académica de los resultados de A02/A03; matriz de confusión y decisión de umbrales para A04; encuesta real y capturas reales (sin cambios, siguen a cargo de Rodo); acta de la primera reunión con el tutor; push de los commits pendientes (autenticación de git a cargo de Rodo, incluidos los 3 commits de SES-055 más el de esta sesión).
- Commit: se incluye en el próximo commit junto con REVISION_02.docx, MODELO_VIGENTE_2026-09-07.md, docs/evidencias/2026-09-15/A02-A03-A04/, BACKLOG.md y esta bitácora.

## 2026-09-15 — SES-057 — Matriz de confusión real en 4.4 (A04) y reajuste del índice a 42 páginas (Claude)

- Alcance: continuación de SES-056 en la misma jornada. Se agregó a la sección 4.4 del Word la matriz de confusión real de la variante en producción (con edad y sexo), tomada de la evaluación temporal ya ejecutada (`docs/evidencias/2026-09-15/A02-A03-A04/reporte_modelo_temporal.json`), con un párrafo de interpretación orientado al diseño de un futuro sistema de alertas.
- Contenido agregado: tabla 3x3 (real/predicho: GRAVE, LEVE, MORTAL) y un párrafo que señala que el modelo sobre-predice GRAVE y MORTAL (recall 0,72 y 0,53) con precisión muy baja en esas clases (0,08 y 0,07: de 1.901 predicciones de GRAVE solo 151 son reales; de 315 de MORTAL solo 23 son reales). Se deja explícito que la decisión de umbral de probabilidad y costo relativo por falso positivo/negativo es una decisión de producto todavía no tomada, y que excede el alcance de esta evaluación.
- Backlog: A04 pasa de "En curso" a "Validado parcialmente" (falta la decisión de negocio sobre umbrales, que no es una tarea técnica sino una definición de producto pendiente).
- El agregado corrió el documento de 41 a 42 páginas (la tabla y los párrafos nuevos empujan el resto del contenido); se recalculó el índice completo (16 entradas cambiaron: Resumen/Abstract y 1.1-1.6 usan una estructura XML distinta para el tabulador del índice —`<w:tab/>` en vez de un carácter de tabulación literal— que no se había cubierto en la corrección de SES-056; se detectó y resolvió con un segundo patrón de búsqueda).
- Verificación: `validate.py --original` sin errores (601 párrafos, +18 respecto de la versión anterior de esta misma jornada), render completo a PDF (42 páginas), revisión visual del índice (págs. 3-4) y de la matriz de confusión en 4.4 (págs. 21-22) antes de entregar.
- Entrega: `MotoSafe_GBA_Capitulos_1_a_5_REVISION_02.docx` enviado a Rodo; la sincronización al equipo quedó pendiente porque el archivo estaba abierto en Word al momento de escribir (Rodo debe cerrarlo para que el próximo intento de sincronización no falle).
- Pendiente / próximo paso: cerrar el Word en el equipo de Rodo para completar la sincronización del archivo; commit de este cambio junto con BACKLOG.md y esta bitácora; A09 (calidad del extractor de prensa) sigue sin revisar en esta sesión.
- Commit: pendiente, a incluir junto con REVISION_02.docx, BACKLOG.md y esta bitácora en el próximo commit.

## 2026-09-15 — SES-058 — Pruebas técnicas actuales (Codex)

- Pedido: probar el estado actual del proyecto.
- IDs: G02, T02; observaciones de código vinculadas a A01, A11, A22, V08 y V12.
- Base: 08bc55610c07595b1f50648880e3d822b131270d. Se preservaron archivos previos del usuario y cambios concurrentes de Claude (SES-057).
- Ejecutado: 80 tests frontend aprobados, 65 backend aprobados, lint y build aprobados. npm test falló por no encontrar el lanzador Vitest; la invocación directa del módulo pasó. Backend: 1.200 advertencias de NumPy/joblib; build: bundle JS de 1,29 MB. El venv backend sí funciona actualmente.
- Navegador: Vite inició; HTTPS local bloqueado por ERR_CERT_AUTHORITY_INVALID. El usuario respondió «acepto» en el chat; no se verificó aceptación dentro del navegador ni se eludió el aviso. No se completaron tareas visuales ni E2E contra PostgreSQL/proveedores reales.
- Evidencia técnica: docs/evidencias/2026-09-15/G02-T02/PRUEBAS.md.
- Commit/push: no realizados en esta sesión.

## 2026-09-15 — SES-059 — Resultados reales del Apéndice A (12 casos) y retiro de la simulación de SES-058 (Claude)

- Alcance: Rodo confirmó que había recolectado 12 respuestas reales al instrumento del Apéndice A (no simuladas) y pidió retirar del repositorio el material sintético que SES-058 había preparado para ensayar ese mismo instrumento (21 cuestionarios ficticios). Antes de este pedido, Codex ya había revertido esa entrega por su cuenta (archivo `21_CUESTIONARIOS_SIMULADOS.md` borrado, referencias limpiadas en BACKLOG, README y CONTINUIDAD); esta sesión comiteó ese estado.
- Contenido real incorporado a A.3 del Word: metodología (12 motociclistas, sesiones moderadas el 15/09/2026, consentimiento verbal, sin datos identificatorios, reclutamiento no aleatorio por contacto directo del autor, declarado como límite de representatividad), conteos de los ítems 1 y 2 (frecuencia y zona), tabla de finalización de las tareas 4/5/6, promedios de los ítems 7/9/10, análisis diferenciado del ítem 8 (6 de 12 casos comprenden bien el contrato de gravedad condicionada, 4 de forma parcial, 2 lo confunden con probabilidad de accidente), síntesis temática de los ítems 11 y 12 con citas anonimizadas por número de caso, y un análisis final separado en tres bloques como pide el propio texto de A.3: defectos de interfaz (nombre de filtros/interruptores), interpretación del riesgo (brecha entre lo que el sistema mide y lo que el usuario entiende) y propuestas de producto (reducir información por default).
- Hallazgo puntual con valor de producto: un caso interpretó que apagar la capa de inseguridad también deja de considerarla en el cálculo de ruta, cuando son dos usos distintos de la misma capa; queda como propuesta de UX de bajo costo, no como bug de backend.
- Se actualizó también "Estado del instrumento" al inicio del Apéndice A (ya no dice "no resultados obtenidos") y se eliminó la nota resaltada roja/amarilla que marcaba el pendiente, ahora resuelto.
- El bloque agregado corrió el documento de 42 a 44 páginas; se recalculó el índice (solo cambió Apéndice B, de página 40 a 43; el resto no se movió porque el bloque se insertó al final del documento).
- Backlog: G02 pasa de "En curso" a "Validado parcialmente" (falta ampliar la muestra y variar el canal de reclutamiento para reducir el sesgo de contactos directos).
- Verificación: `validate.py --original` sin errores (673 párrafos, +72 respecto de la versión anterior), render completo a PDF (44 páginas), revisión visual de las tres páginas nuevas de A.3 y del índice antes de entregar.
- Commit: se comiteó por separado el retiro del material de SES-058 (sin atribución de Claude, porque el contenido y la decisión de retirarlo fueron de Codex) y los resultados reales de A.3 (con atribución de Claude).
- Pendiente / próximo paso: ampliar la muestra de motociclistas más allá del círculo directo de contactos si el tiempo lo permite; push de los commits pendientes (autenticación de git a cargo de Rodo); A09 (calidad del extractor de prensa) sigue bloqueado por límites de este entorno remoto, a ejecutar desde la máquina de Rodo.

## 2026-09-15 — SES-060 — Capturas reales de la sección 4.9 (Figuras 4.4 a 4.6) (Claude)

- Alcance: Rodo pasó 4 capturas de la app corriendo en su entorno local; se incorporaron 3 de las 4 figuras pendientes de 4.9 (Prototipo funcional: evidencia visual). La cuarta (4.7) es opcional y sigue pendiente.
- Figura 4.4: de las dos primeras capturas, se usó la que muestra "Clusters de siniestros" y "Robos con moto" activos al mismo tiempo (ambas capas visibles en el mapa), porque es la única que cumple el requisito de "al menos dos capas de riesgo activas simultáneamente". La otra captura (solo clusters de siniestros, con inseguridad apagada) no se incorporó por mostrar una sola capa; queda disponible si se necesita para otro punto del documento.
- Figura 4.5: panel de prensa con el filtro "Motos" aplicado, mostrando una noticia real clasificada como robo ("Detuvieron a tres jóvenes por intentar robar una moto en Barracas"), 33 de 168 resultados filtrados.
- Figura 4.6: comparador de tres rutas alternativas con el porcentaje de cobertura por fuente (siniestros e inseguridad) y el nivel de exposición relativo de cada una.
- Las tres imágenes se embebieron en el Word (no como enlaces), con pie de figura, fecha (15/09/2026) y aclaración de ejecución local. Se actualizó la tabla de figuras pendientes (4.4, 4.5 y 4.6 pasan de "(pendiente)" a "(incorporada)") y la nota interna, que ahora solo menciona la 4.7 como opcional.
- El agregado corrió el documento de 44 a 45 páginas; se recalculó el índice desde 4.10 hasta Apéndice B (offset uniforme de +1 página, verificado contra el PDF renderizado).
- Verificación: `validate.py --original` sin errores (679 párrafos, +4 respecto de la versión anterior), render completo a PDF (45 páginas), revisión visual de la tabla de figuras, de las dos figuras nuevas y del índice antes de entregar.
- Pendiente: Figura 4.7 (opcional, viewport móvil o capa en estado de error/caché) — Rodo no sabe cómo producirla; se le va a sugerir usar las herramientas de desarrollador de Chrome (modo dispositivo móvil) para la parte de viewport, y evaluar si vale el esfuerzo de simular la parte de red degradada dado que es opcional.
- Commit: incluido junto con esta bitácora.

## 2026-09-15 — SES-061 — Figura 4.7 y cierre de la sección 4.9 (Claude)

- Alcance: Rodo pasó la captura faltante (viewport móvil real de la app, 402×860px) para la Figura 4.7, opcional y última de la sección 4.9. Con esta, las 4 figuras previstas quedan incorporadas.
- Figura 4.7: vista de la app en un viewport móvil, con el mapa, la leyenda de nivel de riesgo y el botón de trazar ruta adaptados al ancho de pantalla. Se embebió como imagen real (no enlace), con pie de figura y fecha (15/09/2026).
- Se actualizó la última celda de la tabla de figuras ("Figura 4.7 (pendiente, si está disponible)" → "(incorporada)") y se eliminó por completo la nota interna "NOTA PARA RODO" que quedaba en la sección, ya sin contenido pendiente que señalar.
- Se revisó el resto del texto de 4.9 y se encontraron tres tramos que habían quedado desactualizados desde SES-059/SES-060 (seguían hablando de "capturas pendientes" y de una acción a cargo del autor para tomarlas, aunque las figuras ya estaban incorporadas): el párrafo introductorio de la sección, la frase que antecede a la tabla y el párrafo que sigue a la tabla. Los tres se reescribieron en tiempo presente/pasado para reflejar que las capturas ya están incorporadas, sin cambiar el contenido técnico que describen. También se ajustó la frase de cierre ("Alcance mostrado en la demo...") que todavía decía "independientemente de las capturas pendientes".
- El agregado corrió el documento de 679 a 680 párrafos y no modificó la cantidad de páginas (se mantuvo en 45); no fue necesario recalcular el índice.
- Verificación: `validate.py --original` sin errores, render completo a PDF, revisión visual de la figura 4.7, del espacio donde estaba la nota eliminada (sin párrafo vacío ni defecto de layout) y del texto reescrito de la sección antes de entregar.
- Backlog: no hay ID dedicado a las capturas de 4.9 (solo se registra en bitácora); no requiere cambio en BACKLOG.md.
- Commit: incluido junto con esta bitácora.

## 2026-09-15 — SES-062 — Medición real de calidad del extractor de prensa (A09) (Claude)

- Alcance: Rodo pidió avanzar con A09 (medir calidad del extractor de prensa contra un conjunto etiquetado), pendiente desde varias sesiones por falta de PostgreSQL/venv operativo desde este entorno remoto.
- Hallazgo clave que desbloqueó el trabajo: `backend/scrapear_noticias_robos.py` tiene un modo dry-run (sin `--guardar`) que no requiere PostgreSQL en absoluto — solo Python con las dependencias instaladas e internet real. La base de datos solo se usa para guardar, no para clasificar ni geocodificar. Este entorno remoto no tiene salida de red hacia sitios de noticias (proxy con lista blanca), así que se le pidió a Rodo correr el dry-run desde su propia máquina.
- Incidentes resueltos en el camino: `psycopg2-binary` estaba roto en el venv de Rodo (`ModuleNotFoundError: psycopg2._psycopg`) — se reinstaló limpio. La salida de PowerShell se corrompió dos veces por problemas de codificación de consola (primero con `>` simple, después con `*>` con la consola en `chcp 65001` pero el pipe igual mal codificado); se resolvió pidiendo `Out-File -Encoding utf8` y, al llegar igual con mojibake, reconstruyendo el texto real con una transcodificación cp850→UTF-8 (se verificó que esa transcodificación fuera reversible sin pérdida antes de usarla).
- Corrida real obtenida (2026-09-15, sin `--guardar`, sin tocar la base): 132 noticias candidatas (70 robo, 50 inseguridad, 12 choque), 1 duplicada omitida, 59 ubicadas geográficamente. Evidencia completa en `docs/evidencias/2026-09-13/A09/corrida_2026-09-15.txt`.
- Etiquetado manual: se revisaron las 132 candidatas reales (no sintéticas) una por una contra el título real de cada nota, comparando lo que el criterio editorial (mismo estándar usado en el resto de la tesis, sin ver la descripción completa que usó el extractor) asignaría como categoría y ubicación real contra lo que produjo el extractor. Resultado en `docs/evidencias/2026-09-13/A09/prensa_etiquetada.csv`. De 132 casos, 105 fueron determinables desde el título solo (los 27 restantes, en su mayoría con `geocode_vacio`, no imprimen la categoría en este modo y no se puede inferir con certeza sin ver también la descripción completa que usó el extractor).
- Métricas obtenidas con `backend/evaluar_extractor_prensa.py`: precisión temática 0,840, recall 0,923, 5 abstenciones sobre 105 casos revisados. Detalle en `docs/evidencias/2026-09-13/A09/metricas_2026-09-15.txt`.
- Error geográfico en metros: no se pudo medir porque este entorno no tiene geocodificación externa independiente disponible para establecer una coordenada de referencia real; se declara explícitamente como limitación en lugar de fabricar una cifra. En su lugar se hizo una medición cualitativa de acierto de zona: de 36 noticias fuera del área de GBA, el sistema abstuvo correctamente en 31 pero generó coordenadas GBA para 2 (Mendoza y Río Negro) — falsos positivos geográficos reales y reproducibles, del mismo tipo que ya señalaba el assessment original de A09 con texto sintético, ahora confirmados con notas reales. De 85 noticias dentro de GBA con pista de ubicación, solo 53 (62%) se ubicaron; las 32 restantes fallaron sobre todo por alias de localidad que el gazetteer no reconoce (Lomas, Monte Grande, Temperley, Don Orione, Los Hornos, Tolosa, Virrey del Pino) o por fallas del geocodificador externo (Nominatim) sobre direcciones reales.
- Otros hallazgos documentados en el CSV (columna `observacion_revision`): falsos positivos temáticos por sentido figurado o institucional ("volcó la paritaria", una nota de opinión sobre IA que matchea "amenaza", una nota sobre la línea 910 de denuncias, "secuestrar" en sentido de decomiso policial); huecos de vocabulario en las listas de palabras clave (formas conjugadas de "asesinar" no coinciden con "asesinato", "femicidio" y "grooming" no están en ninguna lista); y un falso positivo en el prefiltro de slug donde una URL de imagen (.jpg) fue tomada como candidata por contener "secuestro" en el nombre de archivo.
- Backlog: A09 pasa de "En curso" a "Validado parcialmente" (queda pendiente deduplicación semántica y una medición de error geográfico en metros con geocodificación externa independiente).
- Commit: incluido junto con esta bitácora, BACKLOG.md y el CSV/evidencia de A09.

## 2026-09-15 — SES-063 — Corrección del gazetteer (código) e incorporación de A09 a la tesis (documento) (Claude)

- Alcance: Rodo pidió avanzar en ambos frentes que dejó abiertos SES-062: corregir el hallazgo de alias de localidad en el código, e incorporar los resultados reales de A09 al documento de tesis.
- Código: se agregó `ALIAS_LOCALIDAD_PARTIDO` en `backend/scrapear_noticias_robos.py` con los 9 alias confirmados o razonablemente esperables (Lomas, Monte Grande, Temperley, Don Orione, Los Hornos, Tolosa, Virrey del Pino, Grand Bourg, Castelar), cada uno resuelto al partido oficial ya existente en `PARTIDOS_GBA` (nunca un nombre nuevo, para no tocar el query de geocodificación que ya funcionaba). Se reutilizó el mismo chequeo de exclusión por otra provincia que ya tenían los nombres oficiales. Se agregaron 2 pruebas de regresión en `tests/test_scrapear_noticias_robos.py` (reconocimiento de los 5 alias confirmados por la corrida real, y que el alias no rompe la exclusión de otra provincia). Verificación: los 7 títulos reales que habían fallado en la corrida de SES-062 ahora ubican correctamente; 5 casos de regresión (Mendoza, San Martín de Tucumán, intersección real, Flores/Quilmes) sin cambios; 67/67 tests del backend (antes 65) pasan.
- Documento: se actualizaron 4 puntos de la tesis que habían quedado desactualizados por la medición real de A09 (SES-062): 1.4 (ya no dice que la calidad de prensa "tampoco cuenta con una medición"), 1.6 (de las tres tareas pendientes de mayor impacto, ahora dos están resueltas y solo falta la reunión con el tutor), 4.10 (conteo de pruebas backend actualizado de 65 a 67, con las 2 nuevas de A09), y 4.11 (párrafo completo con precisión 0,84, recall 0,923, los 2 falsos positivos geográficos confirmados, la tasa de ubicación del 62% dentro de GBA y la corrección ya aplicada del gazetteer). El agregado no modificó la cantidad de páginas (45) ni corrió ningún encabezado del índice; se verificó cada heading afectado (1.6, 4.10, 4.11, 5.1) contra el PDF renderizado antes de entregar.
- Verificación: `validate.py --original` sin errores (680 párrafos, sin cambio), render completo a PDF, revisión visual de las 4 secciones editadas.
- Commit: código y documento en commits separados.

## 2026-09-15 — SES-064 — Quinta mención desactualizada de A09 en 4.6 (Claude)

- Al revisar el documento completo contra el trabajo del compañero (GoPilot) y los criterios de la cátedra, se encontró un quinto punto (además de los cuatro corregidos en SES-063) que seguía diciendo que la calidad del extractor "sigue sin medirse": el cierre de la sección 4.6 (Ingesta de prensa directa). Se corrigió en la misma línea que los otros cuatro, dejando explícito que la deduplicación semántica (no la precisión ni el error geográfico) es lo que sigue pendiente ahí.
- Verificación: `validate.py --original` sin errores, 45 páginas sin cambio, revisión visual de la página 23.
- Commit: incluido junto con esta bitácora.

## 2026-10-05 — SES-065 — Calibración evaluada y descartada (A04), cambio de demografía en producción (A02/A03), fix de borde visual en ajuste por prensa, detección de desincronización de umbrales (Claude, vía Cowork con bridge a la máquina de Rodo)

- Alcance: Rodo pidió avanzar sobre seis puntos que había dejado abiertos en una sesión anterior (core del sistema: calibración, demografía, clustering, validación de pesos de ruta, distinción visual de crítico ajustado, recalibración de percentiles).
- Calibración de probabilidad (A04): se corrió `CalibratedClassifierCV` (isotonic, vía `FrozenEstimator`) sobre el holdout temporal real (train < 2023, selección 2023, evaluación 2024), con las tres variantes de demografía, todas con `indice_inseguridad` agregado para igualar el feature set real de producción (la ablación académica original lo excluía). Resultado: ECE multiclase baja de ~0,30 a ~0,01 con calibración, pero bajo decisión por argmax el recall de GRAVE y MORTAL colapsa a menos de 0,07 en las tres variantes (LEVE es 93% de los datos y domina una vez que las probabilidades reflejan la frecuencia real). Decisión, con evidencia: no se aplica como mecanismo de decisión en producción porque el sistema no decide por argmax — `calibrar_umbrales_riesgo.py` usa un score continuo (`2·P(MORTAL)+P(GRAVE)`) contra percentiles fijos, mecanismo de ranking no de clasificación, menos sensible al problema. Queda documentado como hallazgo real de ECE alto sin calibrar, con la justificación explícita de por qué no se adopta. Script y resultados crudos: `docs/evidencias/2026-10-05/A02-A04-recalibracion/`.
- Demografía (A02/A03): sobre esa misma evidencia, el `.pkl` en producción (con edad) era la variante que peor generalizaba entre años (F1 macro evaluación 2024: 0,262, contra 0,286 sin edad y 0,362 sin demografía completa). Se decidió no sostener la variante vigente solo por inercia: se reentrenó con la variante sin edad (con sexo e índice de inseguridad), que mejora la generalización sin hundir el recall de GRAVE como pasa al sacar también el sexo. `notebooks/reentrenar_modelo.py` actualizado (quedó la variante sin edad como la que se guarda); artefacto nuevo de 53 columnas (antes 55), reentrenado y copiado a `backend/`. `calibrar_umbrales_riesgo.py` recalibrado contra el modelo nuevo; `UMBRALES_HOTSPOTS`/`UMBRALES_CORREDORES` actualizados en `backend/main.py`. Verificación real del split interno sobre el modelo nuevo: accuracy 0,63, F1 macro 0,37, recall GRAVE 0,62, recall MORTAL 0,52 (precisión 0,10/0,11 respectivamente, consistente con el diseño `balanced_subsample`). 77/77 tests del backend pasan.
- Clustering (HDBSCAN): confirmado sin cambios, a pedido explícito de Rodo (parámetros ya validados por sweep real con cobertura medida en sesión anterior).
- `UMBRAL_CRUCE_KM`/`PESO_RIESGO` (A06): sigue sin ejecutarse. Requiere rutas de referencia etiquetadas a mano por Rodo (`rutas_referencia.csv` ya tiene la plantilla); no se puede fabricar el ground truth sin violar la disciplina de no inventar del proyecto. Pendiente real, no resuelto esta sesión.
- Distinción visual de "crítico ajustado" vs "crítico de base": se encontró que `App.jsx` (`cargarHotspots`) descartaba los campos `ajustado_por_reciente`/`motivo_ajuste` que `/hotspots` ya calcula (`_aplicar_ajuste_riesgo` en `backend/main.py`), aunque corredores e inseguridad sí los mostraban. Un hotspot crítico "de toda la vida" y uno crítico recién por una noticia de choque se veían idénticos en el mapa de siniestros. Se corrigió: `App.jsx` conserva los campos al formatear, el panel de detalle muestra el mismo badge "⬆ Nivel subido" que ya tenían corredores/inseguridad, y `MapaMotoSafe.jsx` aplica el mismo borde más grueso que ya usaba el ajuste por reportes comunitarios (antes solo reflejaba `zona.ajuste.subio`, el eje de pavimento/corte/iluminación, no el de prensa). 68/68 tests de frontend pasan, build limpio.
- Recalibración de percentiles fijos: se agregó `_huella_artefactos_riesgo()` en `backend/main.py` (hash SHA256 de `modelo_final.pkl` + `hotspots_contexto.csv` + `indice_inseguridad_comuna.csv`) comparado contra `_HUELLA_UMBRALES_CALIBRADOS`, expuesto en `/health` como `umbrales_riesgo_actualizados`. Detecta cuándo el modelo/contexto cambiaron desde la última calibración de umbrales sin que nadie lo note; no bloquea el servicio ni recalibra sola — deliberado, porque recalibrar cambia qué significa "alto"/"crítico" en todo el mapa y es una decisión que alguien tiene que revisar, no algo para que pase solo en un restart. `calibrar_umbrales_riesgo.py` actualizado para imprimir la huella junto con los umbrales.
- Documentación: `docs/modelo/MODELO_VIGENTE_2026-09-07.md` y `docs/modelo/CONTRATO_Y_EVALUACION.md` actualizados para reflejar el modelo de 53 columnas vigente (antes citaban 55 columnas y métricas de la variante retirada). `docs/riesgo/PROCEDENCIA_Y_COBERTURA.md` ya tenía, de una corrección anterior de esta misma sesión, el fix del badge de clima duplicado (dos fuentes de clima distintas mostrando valores inconsistentes; ahora usa solo el clima real que ya usó el modelo).
- Backlog: A02 y A04 actualizados con la evidencia de esta sesión (ver BACKLOG.md). A06 sin cambio de estado (sigue pendiente de rutas reales).
- Limitación material: esta sesión corrió vía Cowork con bridge remoto a la máquina de Rodo, no vía Claude Code nativo. Se le recomendó a Rodo migrar las sesiones largas de trabajo sobre este repo a Claude Code en su terminal (menos overhead de shell efímera por llamada, sin recarga de contexto de una conversación de chat larga ya compactada una vez).
- Commit: pendiente, a cargo de Rodo (no se hizo commit de esta sesión porque había trabajo propio sin commitear en el árbol — auth, LoginGate, tailscale — que no correspondía mezclar).
- Agregado al commitear (Claude Code, mismo día): dos cambios del árbol que esta entrada no registraba y que entraron en el commit `65d40dd`. (1) El ajuste por franja horaria de `/hotspots-inseguridad` se movió del frontend (`calcularAjustePorFranjaHoraria` y las constantes `FRANJA_PICO_INSEGURIDAD_*`) al backend (`FRANJA_PICO_INSEGURIDAD` y `_aplicar_ajuste_horario` en `main.py`). La respuesta trae `ajustado_por_horario`/`motivo_ajuste_horario` y el frontend solo los muestra: se evita mantener dos calibraciones y el doble ajuste. Las pruebas pasaron de `geoRiesgo.test.js` a `test_main.py`. (2) El badge de clima ya no consulta Open-Meteo por su cuenta: usa el `clima` que viene en `/hotspots`, el mismo que usó el modelo, y por eso solo distingue lluvia de no lluvia.
- Commits: `65d40dd` (SES-065) y `d51fc30` (login y Tailscale Funnel, trabajo de Rodo; incluye dos arreglos de integración: aislar el pool de conexiones en `test_auth.py` y quitar un `setState` síncrono en el efecto de `LoginGate.jsx`). Después se reemplazó por un placeholder el hostname real de Funnel en `tailscale/README.md`, que se había subido en `d51fc30`; el repositorio es privado.

## 2026-10-05 — SES-066 — Entorno reproducible y versión de scikit-learn del modelo (A22) (Claude Code, sin supervisión)

- Alcance: Rodo pidió elegir un ítem P1/P2 propuesto que no dependiera de una decisión suya ni de etiquetado manual. Se eligió A22 (P2/M, sin dependencias) porque cada carga del modelo emitía `InconsistentVersionWarning`.
- Hallazgo: el modelo vigente (`65d40dd`, SES-065) se guardó con scikit-learn 1.7.2, según `_sklearn_version` en los bytes del pickle. El anterior se había guardado con 1.5.2. El `requirements.txt` raíz, que el README usa para instalar el backend, declaraba 1.5.2; `backend/requirements.txt`, que usa el Dockerfile, aceptaba `>=1.5,<2`; el `venv312` local tenía 1.9.1. Es la misma regresión que el README registró el 07/09. Además, `backend/.dockerignore` no excluía `venv312/` y el Dockerfile lo copiaba a la imagen.
- Evidencia: `docs/evidencias/2026-10-05/A22-entorno/`. Se predijo la población de referencia de `calibrar_umbrales_riesgo.py` (330.288 filas) con 1.7.2, en un venv aislado en el scratchpad, y con 1.9.1, dejando numpy y pandas iguales. Diferencia máxima 4,4·10⁻¹⁶, 0 cambios de clase y 0 cambios de nivel. Con 1.7.2 los percentiles reproducen exactamente los umbrales de `main.py`, lo que confirma la calibración de SES-065.
- Cambios:
  - `backend/requirements.txt` fija versiones exactas, con `scikit-learn==1.7.2`, numpy y scipy. Son las del `venv312`, salvo scikit-learn.
  - `requirements.txt` raíz hace `-r backend/requirements.txt` y deja solo los extras de notebooks.
  - Nuevo `backend/tests/test_entorno.py` (3 tests): versión del pickle frente a la declarada, detección en `main` y versiones exactas.
  - `main.py` captura el aviso de versión al cargar el modelo, lo reemite una vez por texto en lugar de 300 y expone en `/health` solo el booleano `version_sklearn_coincide`, sin versiones, porque `/health` es público.
  - `notebooks/reentrenar_modelo.py` se niega a entrenar con otra versión.
  - `.dockerignore` excluye `venv*/`.
  - El CI instala `backend/requirements.txt` y corre pytest.
  - Nueva guía `docs/operacion/ENTORNO_REPRODUCIBLE.md` con hashes SHA256 de artefactos; README de instalación actualizado a `venv312` con Python 3.12.
- Verificación:
  - `venv312` (1.9.1): 80 tests aprobados y `/health` con `version_sklearn_coincide: false`.
  - Venv nuevo con Python 3.12.10: `pip check` sin conflictos y 80 tests aprobados sin aviso de versión. Con el requirements raíz importan geopandas, matplotlib y xgboost.
  - Imagen Docker construida sin el venv dentro: 80 tests aprobados en Linux. La imagen de prueba se borró.
  - No se reentrenó ni se tocaron artefactos.
- Efecto para Rodo: la próxima vez que corra `backend\_iniciar_backend.bat`, el `pip install -r requirements.txt` va a bajar scikit-learn de 1.9.1 a 1.7.2 en `venv312`. Es el cambio buscado; las demás versiones ya coinciden.
- Pendientes:
  - Lock de dependencias transitivas.
  - Paquetes no declarados de prototipos de notebooks (`h3`, `folium`, `libpysal`, `esda`).
  - Corrida real del CI en GitHub (T05).
- Fuera de alcance, requiere decisión de Rodo: desde el commit `d51fc30`, `auth.py` corta el arranque si faltan `AUTH_USERNAME`/`AUTH_PASSWORD_HASH`/`SESSION_SECRET`, y ni `docker-compose.production.yml` ni `render.yaml` los pasan, así que esos despliegues no arrancarían. Hay que decidir si el MVP publicado lleva login (y entonces declarar las variables) o si el login se vuelve opcional fuera de Tailscale. No se cambió.
- Commit: no realizado, a revisión de Rodo.

## 2026-10-05 — SES-067 — Login opcional para el MVP público y E2E del compose de producción (Claude Code)

- Alcance: Rodo aclaró que el login es solo para su acceso por Tailscale Funnel, no para el MVP público, y pidió que compose y Render arranquen sin `AUTH_*`/`SESSION_SECRET`.
- Cambio:
  - `backend/auth.py` lee `AUTH_HABILITADO`, que por defecto está activado: si la variable falta, sigue exigiendo credenciales. Así un `.env` local incompleto no deja abierta la app expuesta por Funnel.
  - Con `AUTH_HABILITADO=false`: el middleware deja pasar todo, `/auth/login` responde 404 y `/auth/me` devuelve `auth_habilitado: false`.
  - `LoginGate.jsx` muestra la app directamente en ese caso, sin formulario ni botón "Salir".
  - `docker-compose.production.yml` y `render.yaml` fijan `AUTH_HABILITADO=false`.
  - `.env.example` y `tailscale/README.md` lo documentan, con la advertencia de no apagarlo en el `.env` de Funnel. El `backend/.env` local de Rodo no tiene la variable, así que sigue con login.
- Pruebas: 3 tests nuevos en `test_auth.py`.
  - La app arranca sin variables de auth y no exige sesión.
  - Con el valor por defecto y sin credenciales, no arranca.
  - `/auth/me` informa `auth_habilitado`.
  - Los subprocesos fijan las variables vacías para que `load_dotenv()` no traiga las credenciales reales de `backend/.env`.
  - Resultado: 83 de backend, 68 de frontend y lint limpio.
- E2E del compose de producción: proyecto aislado `motosafe-prodtest`, volumen propio y entorno con valores ficticios fuera del repo.
  - Construyó db, api, scraper y web; `/api/health` ok, `version_sklearn_coincide: true` y `/api/auth/me` con `auth_habilitado: false`.
  - Encontró dos problemas:
    1. Migraciones concurrentes: `api` y `scraper` corrían `migrar.py` a la vez y uno fallaba con `UniqueViolation` sobre `schema_migrations`. La API se recuperaba solo porque se reinicia. Se agregó `pg_advisory_xact_lock` en `migrar.py`. Al recrear desde cero, la API aplicó las migraciones, el scraper informó «No hay migraciones pendientes» y hubo 0 reinicios.
    2. Datos: con base nueva, `/hotspots`, `/corredores` y `/hotspots-inseguridad` devuelven 500 (`relation "hotspots_riesgo" does not exist`). Las tablas las crean los `cargar_*.py`, que leen `../data/`, fuera del contexto de build de la imagen y del Blueprint. **Pendiente de decisión de Rodo:** cómo llegan los datos a producción. Documentado en `DESPLIEGUE_MVP.md` y en A14.
  - El stack de prueba, su volumen y la imagen web se eliminaron al terminar.
- Observación para A09, sin cambios: en la corrida real del scraper dentro del stack, la nota «Monte Grande: un detenido por el robo de un auto» se ubicó en (-34.5285, -58.5081), que es zona norte y no Esteban Echeverría. Hay que revisar ese alias cuando se retome A09.

## 2026-10-05/06 — SES-068 — Lock de dependencias, prototipos declarados y primer E2E real (A22, A14, T02, T05) (Claude Code)

- Alcance: cerrar la deuda técnica de A22 y avanzar el E2E real en la máquina de Rodo. Pedido explícito de Rodo; A06 y todo lo relacionado con el tutor quedaron fuera.
- Lock (A22):
  - `backend/requirements.lock` y `requirements.lock` se generaron con `uv pip compile --universal --python-version 3.12 --generate-hashes`, con `uv` en un venv de herramientas del scratchpad. Fijan todas las dependencias transitivas con hashes, para Windows y Linux a la vez.
  - El Dockerfile, el CI y `backend\_iniciar_backend.bat` instalan con `--require-hashes`.
  - Nuevo test `test_lock_coincide_con_las_versiones_directas_y_tiene_hashes`.
  - Verificado: venv nuevo de Windows desde el lock del backend (`pip check` limpio, 84 tests); venv nuevo desde el lock raíz (geopandas, xgboost, matplotlib, seaborn, jupyter importan); imagen Docker desde el lock (84 tests en Linux).
- Notebooks:
  - `notebooks/requirements-prototipos.txt` declara h3 4.5.0, folium 0.20.0, libpysal 4.15.0 y esda 2.10.0. Se verificó corriendo `prototipo_gi_kde_hotspots.py` completo, que solo imprime y no modificó `data/`, y comprobando las funciones h3 v4 de `prototipo_h3_hotspots.py`. Ese último no se ejecutó porque escribe archivos en `data/`.
  - `geopandas` pasó a 1.2.0 porque libpysal exige `>=1.1`; ningún script lo importa.
  - `seaborn` y `requests`, usados por el notebook histórico, quedaron declarados en el `requirements.txt` raíz.
- CI (T05): **no se pudo confirmar en GitHub.** El repositorio es privado, `gh` no está instalado y el navegador integrado no tiene sesión de GitHub. No se usaron credenciales guardadas. Pendiente: que Rodo inicie sesión en el panel del navegador o revise Actions.
- E2E (T02): montaje aislado porque Tailscale Funnel estaba activo publicando `:5173` → `:8000`. Se usaron PostGIS efímero en `127.0.0.1:55432`, backend en `:8100` con credenciales de prueba generadas en la sesión y build del frontend con `vite preview` en `:4173`. `vite.config.js` acepta `MOTOSAFE_API_TARGET` y `MOTOSAFE_SIN_HTTPS` y, sin ellas, se comporta igual que antes. Hallazgos:
  1. `cargar_hotspots.py` hacía `DELETE` sobre una tabla que nada creaba. Una base nueva no se podía reconstruir desde el repo. Ahora la crea con el esquema de la base de desarrollo, leído con `\d`, solo lectura. Después se cargaron las 740 zonas.
  2. **El build de producción dejaba el mapa en blanco.** MapLibre 6.8 calcula en tiempo de ejecución la URL de `maplibre-gl-worker.mjs`, `vite build` no la emitía y el servidor devolvía `index.html`. Afectaba al compose de producción y a Render; en `npm run dev` no se veía. Se corrigió con `?worker&url` y `setWorkerUrl`, solo en el build; después el mapa dibujó teselas y 38 marcadores.
  3. El E2E HTTP (`docs/evidencias/2026-10-05/T02-E2E/e2e_http.py`) pasó 23 de 23 verificaciones a través del proxy, incluido el ciclo de reportes y rutas reales con TomTom. En la primera corrida dos expectativas del script estaban mal: el formato de `/predecir` y el voto repetido, que por diseño reemplaza al anterior. Se corrigieron en el script, no en la app.
- Limitaciones:
  - Después del arreglo del worker, el panel del navegador dejó de pintar (`requestAnimationFrame` detenido, ventana sin foco), así que no se verificaron flujos visuales sobre el mapa.
  - `npm run dev` no se pudo verificar en el panel: tampoco dibujaba con el código original, por la misma causa. Por eso el arreglo quedó limitado a `import.meta.env.PROD`.
  - El montaje, el contenedor y los procesos del E2E se eliminaron. El stack de Rodo (`:5173`, `:8000`) no se tocó.
- Otros: `eslint.config.js` ignora `dist_*`, porque el build local `dist_check_clima/` rompía `npm run lint`.
- Verificación final: 84 tests de backend, 68 de frontend, lint y build limpios.

## 2026-10-06 — SES-069 — Geocodificación de zonas de prensa validada (A09) (Claude Code)

- Alcance: primer ítem del backlog después de cerrar los pendientes técnicos. Se eligió A09 (P1, en curso) porque tenía un defecto concreto observado en SES-067 y verificable sin etiquetado manual.
- Causa: la consulta de zona (`"<partido>, Buenos Aires, Argentina"`) no validaba el resultado y Nominatim devolvía homónimos. Monte Grande, que se traduce a Esteban Echeverría, caía en la calle Esteban Echeverría de Munro.
- Medición: `docs/evidencias/2026-10-06/A09-geocodificacion/medir_zonas.py` sobre las 87 zonas del gazetteer, verificando cada punto por geocodificación inversa, independiente del código evaluado. El método anterior ubicaba mal 11 (12,6 %): Esteban Echeverría, Monte Grande, Almirante Brown, Don Orione, Malvinas Argentinas, Grand Bourg, La Matanza, Virrey del Pino, Tres de Febrero, Belgrano y Vélez Sarsfield. El método nuevo, 0.
  - Dos «errores» intermedios resultaron fallas de mi verificador, no del código: Adrogué no tenía partido en `address`, y el script no manejaba un campo faltante. Se corrigieron y se documentaron.
- Cambio en `backend/scrapear_noticias_robos.py`:
  - `geocodificar_en_zona` usa `featureType=settlement` en el nivel barrio, valida partido o barrio (`resultado_en_zona`, que lee también `display_name`), reintenta «Partido de X» y se abstiene si nada valida.
  - En calles e intersecciones valida el partido, o CABA si la zona es un barrio.
  - `encontrar_zona` ignora «nombre al <número>», que es una calle.
  - El resumen separa «vacío» de «fuera de zona».
  - 10 tests nuevos con direcciones reales devueltas por Nominatim; 93 de backend en total.
- Corrida real en modo prueba (sin guardar):
  - Primera versión: 78 ubicadas y 32 sin ubicar. La revisión (`revisar_rechazos.py`) mostró que 29 eran «sin resultado», que también fallaban antes; el mensaje los mezclaba.
  - De las 3 abstenciones, una era un falso rechazo («Almirante Brown 500», con el partido solo en `display_name`) que además destapó un error de extracción: la nota era de Grand Bourg.
  - Final: 79 ubicadas, 29 vacías, 2 abstenciones correctas, Monte Grande en Esteban Echeverría y Grand Bourg en Malvinas Argentinas.
- No se tocó la base: las filas históricas de `reportes_prensa` ubicadas con el método anterior siguen ahí. Corregirlas es escribir en la base de Rodo y queda anotado como pendiente.

## 2026-10-06 — SES-070 — Pool y migraciones contra PostgreSQL real (A12, T01) (Claude Code)

- Alcance: A12 (P2, validado parcialmente) solo necesitaba la prueba contra PostgreSQL real. Se trabajó junto con T01 porque se solapan.
- Cambio: nuevo `backend/tests/test_integracion_postgres.py`, con 7 tests. Se saltea sin `MOTOSAFE_TEST_DATABASE_URL`; con ella, crea una base aleatoria en un servidor desechable y la borra al terminar.
- Escenarios:
  - 4 procesos migrando a la vez;
  - idempotencia y PostGIS;
  - límite del pool con conexiones reales;
  - rollback después de un error SQL;
  - conexión cortada con `pg_terminate_backend`;
  - ciclo de reportes contra la base: token como hash, voto reemplazado, `ON DELETE CASCADE`;
  - `/health`.
- Verificación:
  - PostGIS 16.4 en un contenedor en `127.0.0.1:55433`: 7/7 a la primera.
  - Control negativo: sin el `pg_advisory_xact_lock` de `migrar.py`, el test de concurrencia falló 3 de 3 veces; después se restauró el archivo.
  - Suite completa: 93 aprobados y 7 salteados sin la variable; 100 aprobados con ella. No quedaron bases de prueba y el contenedor se eliminó.
- CI: el job de backend levanta `postgis/postgis:16-3.4` (credenciales desechables del servicio) y corre toda la suite. Sigue sin confirmarse en GitHub.
- Hallazgo documentado sin cambio: la primera consulta sobre una conexión que cortó el servidor falla antes de que el pool la descarte. No se agregó reintento porque reintentar escrituras puede duplicar reportes, y eso merece un diseño aparte.
- Estados: A12 validado y T01 validado parcialmente. Faltan permisos de un rol sin privilegios y la corrida en GitHub.

## 2026-10-06 — SES-071 — Ensayo real de backup y restauración (T06) (Claude Code)

- Alcance: T06 (P2, en curso) solo necesitaba ejecutar y registrar un ensayo real. No depende de decisiones de Rodo y se hizo sin tocar su base.
- Ensayo: dos PostGIS 16.4 desechables en una red Docker propia.
  - Origen: migraciones, los tres cargadores y un reporte con voto creados por la API.
  - Copia: `pg_dump --format=custom` (242 kB), `createdb` y `pg_restore --clean --if-exists --no-owner` en la otra instancia, siguiendo el procedimiento documentado; código de salida 0, sin advertencias.
- Verificación:
  - Hash md5 del contenido ordenado de las seis tablas, constraints, PostGIS y geometrías: origen y restaurada idénticas.
  - API sobre la restaurada: `/health` ok, las cuatro capas completas, el reporte restaurado con su voto, y un reporte nuevo con id 2 (secuencia restaurada) que se borró con su token.
  - Contenedores, red y dump eliminados.
- Estado: T06 validado parcialmente. Falta repetirlo con el volumen real y en el proveedor de hosting.
- Nota: se descargó la imagen `alpine/socat` de Docker Hub para exponer los contenedores en localhost sin publicar puertos de Postgres en la red.

## 2026-10-06 — SES-072 — Carga inicial de capas en producción y bloqueo scraper/API (A14) (Claude Code)

- Decisión de Rodo: un script en el entrypoint del contenedor carga hotspots, corredores e inseguridad desde los CSV del repo solo si las tablas están vacías, sin meter los CSV en la imagen. Prensa sigue a cargo del scraper.
- Cambio:
  - Los tres `cargar_*.py` exponen `cargar(cur, dir_datos)`; como script se comportan igual que antes.
  - Nuevo `backend/cargar_datos_iniciales.py`: una transacción por capa con lock consultivo, «sin CSV» no falla.
  - `entrypoint.sh` lo corre después de `migrar.py`.
  - `docker-compose.production.yml` monta `./data:/data:ro` con `MOTOSAFE_DATA_DIR=/data`.
  - `.gitattributes` fuerza LF en `*.sh`: con `core.autocrlf=true`, un checkout podía romper `entrypoint.sh` en el contenedor.
- Render no puede montar `data/`. Quedó documentado un paso único idempotente: correr el script desde una copia local con la URL externa de la base, que no se guarda en el repo.
- Pruebas:
  - Test de integración nuevo contra PostGIS desechable: sin CSV, primera carga (740/243/1.135), segunda sin recarga y sin pisar una fila editada, y recarga solo de la capa vaciada. 8/8 de integración y 93 + 8 salteados en la suite.
  - Compose de producción con base vacía: cargó 740/243/1.135; tras `restart api`, «ya tenía».
- Hallazgo del mismo E2E: con el scraper corriendo, `/hotspots` y `/corredores` daban 504 a los 60 s.
  - Un primer arreglo, con commit del DDL al inicio del scraper, no alcanzó: la medición siguió mostrando 504.
  - Causa real: `_asegurar_tabla_prensa` de la API corría `ALTER TABLE reportes_prensa` (lock exclusivo) en **cada** request, y el scraper mantenía abierta su transacción de inserts toda la corrida; las lecturas quedaban encoladas detrás del ALTER en espera.
  - Arreglo: el DDL de prensa en la API corre una vez por proceso, con el mismo patrón que reportes, y el scraper hace commit por fila.
  - Medición posterior, con el scraper guardando (13 → 24 filas): hotspots, corredores y prensa responden 200 en menos de 1,4 s durante toda la corrida.
- El stack y las imágenes de prueba se eliminaron.

## 2026-10-06 — SES-073 — Re-geocodificación de las filas históricas de prensa (A09) (Claude Code)

- Decisión de Rodo: re-geocodificar las filas de `reportes_prensa` ubicadas con el método anterior, con backup previo.
- Backup en `C:\Users\rodol\motosafe_backups\`, fuera del repo: dump completo (351 kB, legible con `pg_restore --list`) y CSV de la tabla antes y después.
- Método, sin descargar páginas: la tabla guarda solo el titular y 232 filas son de Google Noticias, que no se consulta (DEC-011).
  - 418 filas de nivel barrio coincidían exactamente con el punto anterior de una de las 87 zonas medidas en SES-069 y recibieron el punto nuevo validado de esa zona.
  - 9 se re-extrajeron del titular.
- Corrección durante la simulación: la primera versión movía filas de calle o intersección al centro de su zona y las dejaba marcadas como precisas. Se cambió la regla:
  - si el titular da menos precisión, la fila se deja como está cuando el punto viejo cae en la zona del titular (verificado por geocodificación inversa);
  - si cae fuera, se mueve y baja a nivel barrio (3 casos: Grand Bourg, que estaba en Burzaco a 49 km; Merlo, a 21 km; Avellaneda, a 8 km).
- Resultado aplicado en una transacción: 450 filas antes y después, **142 cambiaron de ubicación** (las mismas que la propuesta).
  - 94 corrigen notas que estaban en otro partido o barrio; 87 de La Matanza caían en Presidente Perón.
  - 95 se desplazaron más de 20 km.
  - 0 filas con otras columnas modificadas.
- Evidencia en `docs/evidencias/2026-10-06/A09-regeocodificacion/`.

## 2026-10-06 — SES-074 — `data/` no está versionado: test de carga inicial y documentación (Claude Code)

- Hallazgo, al calcular los períodos de cobertura: `data/` está en `.gitignore` y no tiene ningún archivo versionado. La decisión de SES-072 suponía «CSV del repo», pero esos CSV solo existen en la PC de Rodo.
- Consecuencias:
  - En el CI, `test_carga_inicial_solo_llena_tablas_vacias` habría fallado, porque esperaba 740 filas y no hay CSV.
  - En un servidor clonado desde GitHub, o en Render, la carga inicial informa «sin CSV».
- Cambio: el test prueba siempre el camino «sin CSV» y saltea el resto con un motivo explícito si faltan los CSV. Se verificó con `data/` (pasa) y simulando un clon limpio (se saltea). `DESPLIEGUE_MVP.md` quedó corregido.
- **Pendiente de decisión de Rodo:** versionar los cuatro CSV derivados de las capas (unos 700 kB) u otra vía. No se cambió `.gitignore`.

## 2026-10-06 — SES-075 — Período de cobertura visible por capa (A10, A11, A15) (Claude Code)

- Decisión de Rodo: mostrar el período real de los datos de cada capa (por ejemplo «siniestros 2019–2025»), no la fecha de generación del archivo; esa puede ir de forma secundaria en un tooltip.
- Cálculo con datos reales (`notebooks/generar_metadatos_capas.py`):
  - Siniestros: 2019-01-01 a 2025-12-31, 23.343 registros, todos con fecha válida. Las fechas vienen sin ceros (`2025-9-9`); un primer cálculo por texto daba un máximo equivocado y se pasó a fechas reales.
  - Delitos: los últimos 3 años del dataset, 2023-01-01 a 2025-12-31 (447.938 en total, 15.792 con moto).
  - Como `data/` no está versionado, el resultado se guarda en `backend/metadatos_capas.json`, que sí se versiona.
- Backend: `GET /capas/cobertura` devuelve los períodos y, para prensa, la vigencia (30 días) y la nota más reciente en la base; si la base falla, ese dato vuelve vacío. 2 tests nuevos; 95 + 8 salteados.
- Frontend:
  - `formatearPeriodo` (3 tests) da «2019–2025» si son años completos, o con mes si no.
  - Las leyendas de siniestros (hotspots o corredores) y de inseguridad muestran el período y la fuente; el tooltip agrega registros y la fecha del archivo de la capa.
  - El panel de capas muestra la antigüedad de la nota de prensa más reciente.
  - 71 tests de frontend, lint y build limpios.
- No verificado visualmente: Rodo lo revisa con `npm run dev`.
- Estados: A10 pasa a validado parcialmente; A11 sigue en curso (falta distancia a segmentos); A15 suma el período de origen desde el backend.

## 2026-10-06 — SES-076 — CSV derivados de las capas versionados (A14) (Claude Code)

- Decisión de Rodo: versionar los 4 CSV derivados que usa la carga inicial y dejar afuera los crudos (`delitos_caba.csv`, 113 MB).
- Cambio en `.gitignore`: `data/` pasa a `data/*`, porque con la carpeta excluida Git no permite excepciones, y se agregan excepciones explícitas para `hotspots_moto_caba.csv`, `corredores_riesgo.csv`, `hotspots_inseguridad_general.csv` y `hotspots_inseguridad_moto.csv` (unos 700 kB, datos agregados sin información personal). Se verificó que el resto de `data/` (crudos, modelos, previews) sigue ignorado.
- Verificación: se clonó el repositorio en limpio en el scratchpad (`core.longpaths` por un `.docx` de nombre largo) y se corrió la suite completa contra un PostGIS desechable: 103/103, sin salteados. El test de carga inicial vuelve a validar las 740/243/1.135 filas.
- Render sigue necesitando el paso único documentado, porque construye con contexto `./backend` y los CSV no van en la imagen.

## 2026-10-06 — SES-077 — Pipeline canónico y notebook histórico seguro (A19) (Claude Code)

- Problema: con «Run All», el notebook histórico podía pisar en `data/` el modelo, el contexto y los hotspots con versiones antiguas, y `reentrenar_modelo.py` copiaba directo a `backend/`.
- Cambios:
  - Guarda al principio del notebook, insertada sin reformatear el JSON (+53 líneas): desvía `to_csv` y `joblib.dump` hacia `data/` o `backend/` a `data/exploracion_notebook/`. Probada: desvía, no toca lo de afuera, es idempotente y los SHA256 de los vigentes quedaron intactos.
  - `reentrenar_modelo.py` deja candidatos en `data/`.
  - Nuevo `promover_artefactos.py`: manifiesto vigente contra candidato y publicación solo con `--confirmar`, verificando la versión de scikit-learn; normaliza los fines de línea de los CSV.
  - Orden canónico en `docs/modelo/PIPELINE_CANONICO.md`.
- Prueba desde cero: clon limpio con solo datos crudos y entorno del lock (scikit-learn 1.7.2).
  - Los hashes de bytes dieron distintos, por CRLF de pandas en Windows y por metadatos del pickle.
  - Comparado por contenido: índice, clusters, hotspots, contexto y candidatos de corredores son idénticos celda por celda, y el modelo es idéntico en los 300 árboles.
  - El `backend/` de la copia no cambió.
  - `identificar_hotspots_inseguridad` (HDBSCAN sobre unos 450.000 delitos) seguía corriendo al cerrar esta entrada; su resultado se agrega cuando termine.
- Límite: `motos_limpio.csv` sale del notebook (paso 0 sin script) y se trató como entrada congelada.
- Agregado a SES-077: `identificar_hotspots_inseguridad` terminó en la copia (66 min, HDBSCAN sobre 408.241 delitos). Los hotspots general (633) y moto (502) tienen el mismo contenido que los vigentes. Las 7 salidas comparables y el modelo se reproducen todas.

## 2026-10-06 — SES-078 — Fichas de fuentes con licencias verificadas (D01) (Claude Code)

- Alcance: completar fichas de todas las fuentes con licencia y procedencia verificadas en las páginas oficiales, sin suponer.
- Verificado:
  - Siniestros viales y delitos del GCBA: «Creative Commons Attribution», actualización anual; última actualización del publicador el 2026-07-14 y el 2026-06-22.
  - Open-Meteo: CC BY 4.0; gratis solo no comercial (menos de 10.000 pedidos por día).
  - Nominatim: ODbL, 1 pedido por segundo, User-Agent o Referer; prohíbe el autocompletado.
  - OSRM demo: 1 pedido por segundo, no comercial.
  - TomTom: cupos del plan gratuito; la página no aclara el uso comercial.
  - OpenFreeMap: uso comercial permitido, con atribución.
- Nuevo `docs/datos/FICHAS_FUENTES.md`, con unidad, período, filtros, versionado, límites y cumplimiento por fuente. La ficha de siniestros enlaza la procedencia verificada.
- Correcciones sin decisión de por medio:
  - `fetch_corredores_geometria.py` hacía 0,3 s de pausa (unos 3 pedidos por segundo) contra OSRM demo; pasó a 1,1 s.
  - El mapa agrega la atribución de Open-Meteo y de Buenos Aires Data (CC BY) en el control de atribución. 71 tests de frontend, lint y build limpios.
- **Hallazgo para A18, decisión de Rodo:** `useSugerenciasDireccion` pide sugerencias a Nominatim mientras se escribe (400 ms de demora). Es autocompletado, que la política de Nominatim prohíbe. No se cambió: requiere elegir proveedor o pasar a búsqueda al confirmar.

---

## 2026-10-06 — SES-079 — Resolución de A18: búsqueda de direcciones solo al confirmar (Claude Code)

- Pedido de Rodo: quitar el autocompletado en vivo contra Nominatim, que su política prohíbe, y documentarlo como resolución de A18.
- Cambio:
  - `frontend/src/hooks/useSugerenciasDireccion.js` (debounce de 400 ms, pedido en cada pausa) se reemplaza por `useBusquedaDireccion.js`, que expone `buscar(texto)` y `limpiar()`.
  - Barra de búsqueda: busca con Enter o con el botón de la lupa (ahora un `<button>`, deshabilitado si el campo está vacío).
  - Origen y destino: buscan con Enter en el campo, mientras no esté ya resuelto el punto. Cada resultado sigue siendo una elección del usuario. «Buscar ruta» usa `geocodificar()` como antes.
  - Al editar el campo se descartan los resultados y se cancela el pedido en vuelo. Si no hay resultados o falla el pedido, el desplegable lo dice.
  - Se quitó el comentario obsoleto de `geoRiesgo.js` y se aclaró que `buscarSugerencias` se llama solo al confirmar.
- Resultado: no quedan llamadas a Nominatim durante la escritura. Un pedido por búsqueda confirmada.
- Verificación: `eslint src` sin errores; 71 tests de frontend (`node node_modules/vitest/vitest.mjs run`, porque el `.bin` de vitest no resuelve en este equipo); `vite build` sin errores.
- No verificado: la revisión visual con `npm run dev` (la hace Rodo). El hook no tiene test propio porque el proyecto no tiene `@testing-library/react`.
- Registros: A18 pasa a «Resuelto» en BACKLOG; `FICHAS_FUENTES.md` actualiza la fila de Nominatim y los pendientes derivados.
- Queda fuera de A18 y no bloquea: evaluar la cuota de Nominatim para producción o un proveedor propio.

---

## 2026-10-06 — SES-080 — Scraper en contenedor: tope por corrida y operación documentada (Claude Code)

- Pedido de Rodo: que el scraper corra solo, en su propio servicio Docker, con pausa, reanudación y logs centralizados, sin reintroducir el bloqueo de transacciones.
- Revisión previa: el servicio `scraper` ya existía en `docker-compose.production.yml` (ciclo con `restart: unless-stopped`, intervalo de `SCRAPER_INTERVAL_MINUTES`, 180 por defecto). No hizo falta crearlo. Se verificó que cada fila se confirma sola (`cur.connection.commit()` en `_evaluar_y_guardar`) y que no hay transacción abierta durante los pedidos de red.
- Cambios:
  - `backend/scraper-loop.sh`: cada corrida tiene un tope de `SCRAPER_TIMEOUT_MINUTES` (45 por defecto) con `timeout`. Si lo supera, queda como falla y se reintenta en el siguiente ciclo, sin trabar el loop.
  - `docker-compose.production.yml`: expone `SCRAPER_TIMEOUT_MINUTES` con ese mismo valor por defecto.
  - `docs/operacion/DESPLIEGUE_MVP.md`: sección «Operar el scraper» con `stop`/`start`/`logs -f`. Se usa `stop` y no `pause`: `pause` congela el proceso con la conexión a la base abierta.
- Cadencia: se mantiene en 180 minutos. El repo no tiene un número real de notas guardadas por corrida, así que no se baja el intervalo sin datos. Decidir con `docker compose logs scraper` después de una semana.
- Verificación: `sh -n` sobre `scraper-loop.sh` sin errores; `docker compose config` del compose de producción con variables de ejemplo, con `SCRAPER_TIMEOUT_MINUTES=45` y `SCRAPER_INTERVAL_MINUTES=180`.
- No verificado: una corrida real dentro del contenedor, y que `timeout` corte un proceso colgado. Quedan para la primera corrida en el despliegue.
- Hallazgo de calidad, sin cambios: en la base local hay 450 notas (65 con moto). Las 204 de Google Noticias se guardaron antes de retirar la fuente (DEC-011, la última del 13/09/2026). El scraper ya no tiene esas fuentes, pero las notas siguen visibles hasta vencer a los 30 días. Se decide con Rodo si se filtran en la API o se borran (ver CONTINUIDAD).

- **SES-080 (calidad de prensa, parte de la API):**
  - Cambio en `backend/main.py`: las tres consultas de `reportes_prensa` (listado público, ajuste de riesgo y «más reciente») excluyen las fuentes «Google Noticias» (DEC-011). Las filas no se borran; limpiar la tabla queda para una decisión aparte, con backup.
  - La fecha de referencia es la de publicación si es plausible (no más de 30 días antes ni 1 día después de la ingesta). Si no lo es, o falta, se usa la de ingesta. Así una fecha mal extraída (en la base hay 29 anteriores a 2025 y 13 sin fecha) no deja vigente una nota vieja ni oculta una reciente.
  - Tests: 104 pruebas de backend en verde, con `MOTOSAFE_TEST_DATABASE_URL` apuntando a la base local. Incluye la nueva `test_prensa_excluye_google_y_usa_fecha_de_ingesta_si_la_publicada_no_sirve`, que corre contra PostgreSQL real y no se saltea.
  - Verificado: la tabla local sigue con 450 filas (no se tocaron datos).
  - No verificado: el efecto visible en el mapa. El frontend muestra `publicado_en`, que ahora llega ya resuelto desde la API.

## 2026-10-06 — SES-081 — Scraper programado en Windows contra la base de producción (Claude Code)

- Pedido de Rodo: correr el scraper cada 3 horas en el despliegue actual (backend nativo, Docker solo para la base), sin depender de una terminal abierta, con logs por corrida y sin pisar corridas.
- Decisión: wrapper + Programador de tareas de Windows, no el `up -d scraper` del compose de producción, porque su entrypoint corre `migrar.py` sobre la base en vivo, que no tiene `schema_migrations` (ver CONTINUIDAD).
- Cambios:
  - `scraper_programado.bat` (raíz): hace `cd /d` a su propia carpeta; vacía en el proceso las variables que Compose toma del entorno (`DATABASE_URL`, `TOMTOM_API_KEY`, etc.) para que no pisen `.env.production`; espera hasta 5 minutos a que Docker responda (Docker Desktop arranca con el inicio de sesión, según `HKCU\...\Run`); corre `docker compose ... run --rm --no-deps --entrypoint python scraper scrapear_noticias_robos.py --guardar`; escribe un log por corrida en `logs\scraper\corrida_AAAAMMDD_HHMMSS.log` y devuelve el código de salida.
  - `scraper_programado.bat --seco` corre sin `--guardar` y no escribe en la base.
  - `.gitignore`: se ignora `logs/`.
  - Tarea `MotoSafe-Scraper` del Programador de tareas de Windows: disparador cada 3 horas (desde 5 minutos después del registro, indefinidamente); «no iniciar una nueva instancia si ya hay una en ejecución»; límite de ejecución de 1 hora; «ejecutar tan pronto como sea posible si se perdió una ejecución»; se ejecuta solo con la sesión iniciada.
- Verificación: corrida en seco con código 0 (138 candidatas, 80 ubicadas, log con resumen). `reportes_prensa` sigue con 465 filas tras la prueba.
- Pendiente: la primera corrida real del programador (prevista para 10:32) es la primera escritura automática. Se revisa en `logs\scraper`. La cadencia de 3 horas se ajusta con las cifras de «nuevas guardadas» de esos logs.
- Límites conocidos: si la PC está apagada o nadie inicia sesión, no corre (se recupera al iniciar sesión por «ejecutar tan pronto como sea posible»). Cada corrida crea un archivo de log; ocho por día, sin rotación automática.
- **Verificación de la primera corrida automática (SES-081):** se disparó sola a las 10:32:20, sin intervención, y terminó a las 10:36:31 con código 0 (≈4 min). Log `corrida_20261006_103220.log`: 138 candidatas, 80 ubicadas, 0 nuevas guardadas. Los 80 ya estaban en la base por URL; el contador de «duplicadas» solo cuenta repetidas dentro de la misma corrida, así que el log no distingue «ya estaba en la base». Pendiente, a pedido de Rodo: agregar ese contador si sirve para decidir la cadencia. La siguiente corrida está prevista para 13:32.
- **Registro del proceso:** se agregó la sección «Registro del proceso» en BACKLOG, con historial de commits, bitácora, backlog y decisiones como ítems disponibles, y actas con el tutor como ítem pendiente de Rodo.

## 2026-10-06 — SES-082 — Contador «ya en la base» y limpieza de logs de la corrida programada (Claude Code)

- Pedido de Rodo: que el log distinga las notas que ya estaban en la base de las que no se guardaron, y limpiar logs viejos al inicio de cada corrida. No tocar nada más.
- Cambios:
  - `backend/scrapear_noticias_robos.py`: contador `ya_en_base`. Se incrementa cuando el `INSERT ... ON CONFLICT (url_fuente) DO NOTHING` no inserta. El resumen dice «N nuevas guardadas en la base, M ya estaban en la base». Solo aplica con `--guardar`.
  - `scraper_programado.bat`: antes de cada corrida borra con `forfiles` solo `corrida_*.log` de más de 60 días en `logs\scraper`, y deja en el log de la corrida una línea por archivo borrado. La limpieza va antes del scraper, así que no depende de que la corrida termine bien.
  - `scraper_programado.bat`: `run --build --quiet-build`. Sin `--build`, `docker compose run` usa la imagen que ya existe y el cambio del scraper no llegaría a la tarea programada.
  - `backend/tests/test_scrapear_noticias_robos.py`: prueba de que una nota ya guardada cuenta como «ya en la base» y no como nueva.
- Verificación:
  - Pruebas de backend: 105 en verde.
  - Limpieza en seco con archivos de prueba en `logs\scraper`: se borraron `corrida_20250101_000000.log` y `corrida_20250301_120000.log`; se conservaron `notas_viejas.log` (otro patrón) y los logs recientes. Se borró después el archivo de control.
  - Corrida en seco con código 0, imagen reconstruida (`motosafe-gba-scraper`) con el contador.
- No verificado: el contador en una corrida con `--guardar`. Se confirma con las próximas corridas programadas.

## 2026-10-06 — SES-083 — Solapamientos en celular: atribución del mapa y «Cerrar sesión» (Claude Code)

- Pedido de Rodo: revisar la UI en celular (375×812), arreglar solapamientos reales y mover el «Salir».
- Confirmado en el navegador, con la app real:
  - La atribución de MapLibre quedaba expandida al cargar, tapaba «Reportar» y el texto de OpenStreetMap quedaba debajo de «Salir». Causa: MapLibre agrega `maplibregl-compact-show` al cargar, aunque `compact: true`.
  - El botón «Salir» era fijo abajo a la derecha y se superponía con «Reportar».
- Cambios:
  - `frontend/src/sesion.js` (nuevo): contexto de sesión. Vale null sin login (`AUTH_HABILITADO=false`).
  - `LoginGate.jsx`: publica usuario y cierre de sesión por el contexto; se quitó el botón fijo y su estilo.
  - `App.jsx`: «Cerrar sesión» como opción del menú de herramientas, solo si hay login.
  - `MapaMotoSafe.jsx`: al cargar el mapa se quita `maplibregl-compact-show`, así la atribución queda como botón «i». El usuario la abre con ese botón.
- Verificación: lint sin errores; 71 tests de frontend; build sin errores. En el navegador en 375×812: «Reportar» libre, «Salir» ya no aparece abajo, «Cerrar sesión» figura en el menú de herramientas (no se hizo clic para no cerrar la sesión de prueba).
- Nota: el build nuevo lo sirven también el preview 5175 del Funnel y el 5176, porque comparten `frontend/dist`. Los cambios ya están vivos en la URL pública.
- Pendiente: el solapamiento de «Salir» de navegación (`nav-resumen-mini`) con «Reportar» durante un viaje, que no se probó. La pasada general de UX queda para después, según lo acordado.

## 2026-10-06 — SES-084 — Pasada de UX: búsqueda de ruta, leyenda, atribución y modal (Claude Code)

- Alcance acordado con Rodo: ítems 1, 3, 4, 6 y 8 de la auditoría. Quedan para después los ítems 2 (bundle de 1,3 MB), 5 (botón de la lupa) y 7 (solapamiento de «Cerrar sesión» en viaje real).
- Cambios:
  - Ítem 1 (regresión de SES-079): «Buscar ruta» ya no toma el primer resultado de un campo sin punto elegido. Muestra las opciones de ese campo y la ruta se calcula cuando el usuario toca la correcta. Se quitó el estado `geocodificando`, que ya no hacía falta.
  - Ítem 3: la leyenda «Nivel de riesgo» en celular pasa de 140 a 124 px de ancho y reduce el padding y el título. Sigue ocupando un bloque del mapa; si hace falta más, se puede pasar a una versión colapsada.
  - Ítem 4: el placeholder del buscador dice «(Enter)».
  - Ítem 6: la atribución del mapa se colapsa al botón «i» solo por debajo de 480 px. En escritorio queda abierta.
  - Ítem 8: el modal «Así funciona MotoSafe» se controla con `localStorage` (clave `CLAVE_ONBOARDING`). Aparece una vez por navegador y por origen. Por eso reapareció en `127.0.0.1:5176`: es otro origen que la URL del Funnel.
- Causa real de la atribución expandida: MapLibre pone el atributo `open` en el `<details>` de la atribución al cargar en pantallas de hasta 640 px, y ese atributo es lo que la muestra. La clase `maplibregl-compact-show` no alcanza, y se quita también en el evento `idle`.
- Verificación: lint sin errores; 71 tests; build sin errores. En el navegador a 375×812: la atribución queda en el «i», «Reportar» libre, placeholder con «(Enter)», y «Buscar ruta» con «Monte Grande» muestra las opciones sin calcular ruta.
- Infraestructura, pendiente sin tocar: la URL pública del Funnel depende de que el preview del 5175 esté corriendo a mano. No es un servicio persistente. Se anota en CONTINUIDAD.

## 2026-10-06 — SES-085 — Acceso público confiable: vigilancia automática del Funnel, preview y base (Claude Code)

- Pedido de Rodo: que la URL pública vuelva sola tras reiniciar la PC, sin abrir terminales, con chequeo periódico y log, y `estado.bat` que responda de un vistazo.
- Cambios:
  - `tailscale/vigilancia.ps1` (nuevo): revisa en orden base (`motosafe-db`), backend (8000), preview (5175), Funnel (443 -> 5175) y URL pública. Si algo falla, lo reinicia: `docker start`, `_iniciar_backend.bat` oculto (limpiando antes los procesos huérfanos de `run_dev.py`), `vite preview` oculto (con build si falta `dist`), y reaplica el Funnel solo al 443. Escribe una línea por revisión en `logs\vigilancia\vigilancia_AAAAMMDD.log`. Con `-SoloEstado` no toca nada.
  - `tailscale/registrar_vigilancia.ps1` (nuevo): registra la tarea `MotoSafe-Vigilancia`, que corre al iniciar sesión y cada 5 minutos, sin ventana, sin instancias paralelas y con límite de 15 minutos.
  - `tailscale/estado.bat`: muestra el estado de las cinco piezas y las últimas revisiones. No reinicia nada.
  - `tailscale/mantener_activo.bat`: retirado; lo reemplaza la vigilancia. Su README decía que debía estar en la carpeta de inicio.
  - `tailscale/README.md`: sección 6 reescrita con la tarea.
- Pruebas hechas en esta PC (las cuatro fallas, con recuperación confirmada en el log):
  - Preview matado a mano: la vigilancia lo levantó (`preview: iniciado`) y todo quedó OK.
  - Funnel 443 apagado a propósito: la vigilancia lo reaplicó (`funnel: reaplicado a 443`); el 8443 nunca se tocó.
  - Base detenida con `docker stop`: la vigilancia la arrancó (`base: docker start`).
  - Backend caído (worker del `uvicorn --reload` detenido): la vigilancia lo levantó (`backend: iniciado`) y el health volvió a 200.
  - La tarea corrió con resultado 0.
- Hallazgo de la prueba: al matar el proceso padre de `uvicorn --reload`, el worker hijo sigue con el socket abierto y el backend parece vivo. Por eso el reinicio ahora limpia los procesos huérfanos antes de levantar uno nuevo.
- No verificado: el reinicio completo de la PC (requiere que lo hagas vos), y que Tailscale conserve la configuración del Funnel tras reiniciar. La vigilancia la reaplica si falta, así que no depende de que se conserve.
- Pendiente: si quedó abierto `mantener_activo.bat` en alguna ventana, cerrarla, porque llama a `reiniciar_app.bat`, que cierra los procesos de 8000 y 5175.

## 2026-10-06 — SES-086 — Pasada de UX: code splitting, lupa visible, viaje real y atribución durante la navegación (Claude Code)

- Pedido de Rodo: cerrar los ítems 2, 5 y 7 de la auditoría, y revisar la interfaz de punta a punta.
- Cambios:
  - Ítem 2 (bundle): el mapa se carga con `React.lazy` en su propio chunk. El bundle principal bajó de 1,30 MB a 269 kB (85 kB comprimido); MapLibre queda en `MapaMotoSafe-*.js` (1,03 MB, 275 kB comprimido) y baja mientras se muestra la pantalla de carga. El aviso de chunk mayor a 500 kB sigue para ese chunk; se deja para más adelante.
  - Ítem 5 (lupa): el botón de buscar es un círculo con fondo y borde, y cambia al pasar el puntero o enfocarlo.
  - Ítem 7 (viaje real): se simuló la ubicación del GPS, se calculó una ruta a Lanús Oeste (12,9 km, 23 min, tres opciones) y se inició el viaje. Medido en 375×812: el botón «Salir» de navegación y «Reportar» no se solapan (10 px de separación). El botón «Cerrar sesión» ya no es fijo (SES-083), así que no compite con nada durante el viaje.
  - Bug encontrado en la prueba de viaje: al iniciar el viaje, MapLibre volvía a abrir la atribución (`open` en el `<details>`), que cubría el panel de navegación y el velocímetro. Se corrige con un `MutationObserver` sobre ese atributo, respetando el clic del usuario en el botón «i». Medido después: colapsada en la esquina, sin solapamientos.
- Verificación: lint sin errores; 71 tests; build sin errores. Pruebas en el navegador en 375×812 (carga, búsqueda de ruta con opciones, viaje activo).
- Nota: el build nuevo lo sirven también el preview 5175 del Funnel y el 5176 de prueba (comparten `frontend/dist`). La URL pública ya muestra estos cambios.
- Pendiente, a revisar con Rodo antes de tocar (mejoras de diseño y nice-to-have): leyenda «Nivel de riesgo» todavía ocupa un bloque grande del mapa; la sugerencia de origen aparece solo al buscar ruta (no hay pista visual de que se puede elegir); el botón «Reportar» queda a 10 px del panel de navegación; la atribución colapsada en escritorio no se revisó con viaje; la pantalla de carga tarda mientras baja el chunk del mapa.
- No verificado: escritorio con viaje activo, y el flujo de reportar con la app en navegación.

## 2026-10-06 — SES-087 — Solapamientos y navegación a partir de las capturas de viaje real (Claude Code)

- Pedido de Rodo: revisar las capturas de una prueba real en celular y arreglar lo que se pisa.
- Hallazgos y arreglos:
  - **Reportar tapaba «Nueva ruta»** en el panel de opciones de ruta. Ahora `.report-fab` se oculta mientras ese panel está abierto. Verificado en el navegador: `display: none` con el panel visible.
  - **Distancia de maniobra absurda (58,6 km para una maniobra a 130 m).** Causa: el paso activo solo avanzaba si el GPS caía a menos de 30 m del punto de la maniobra. Si el GPS se saltaba un punto, el paso quedaba trabado y la distancia en línea recta se disparaba. Ahora `siguientePaso` (en `utils/geoRiesgo.js`) avanza al último paso de los próximos cinco que esté dentro de 30 m, sin retroceder nunca. Cubierto con 4 pruebas nuevas.
  - **Tarjeta de zona tapada por la leyenda** en celular. Mientras hay una zona abierta, la leyenda se oculta en pantallas de hasta 480 px (igual que con el panel de rutas).
  - **Toasts sobre la barra de búsqueda** («Calculando rutas», «Acercate para ver el tráfico», «Reporte enviado»). Ahora aparecen 80 px debajo de la barra. La tarjeta de instrucciones de navegación (`.navegacion-panel`) se mantiene en su posición original.
- Verificación: lint sin errores; 75 pruebas (71 previas más 4 nuevas de `siguientePaso`); build sin errores.
- No verificado en el navegador: la nueva posición de los toasts y la leyenda oculta con zona abierta. La captura de la distancia corregida requiere otra prueba de viaje con GPS que se salte una maniobra.
- Pendiente de decisión de diseño: el tiempo estimado puede dispararse con velocidad baja (554 min en la captura). Y la leyenda ocupa mucho espacio en celular.

## 2026-10-06 — SES-088 — Barra de búsqueda sobre los botones superiores y búsqueda de lugares (Claude Code)

- Pedido de Rodo: la barra de búsqueda tapaba los botones redondos de arriba y el clima en celular, y la búsqueda debía encontrar lugares (local, calle), no zonas.
- Causa del solapamiento: la variable `--topbar-h` (que ubica la barra de búsqueda y los demás paneles) usaba `contentRect` del `<header>`, que no incluye el padding. Medido en el navegador: la barra mide 105 px, la variable valía 62 px, y la barra de búsqueda quedaba encima de los botones. Además el observador no disparaba en la pestaña de prueba, así que la variable nunca se escribía. Ahora se mide al montar (`offsetHeight`), en cada `resize` de ventana, y con `ResizeObserver` para cambios de contenido.
- Verificado en 375×812: los botones terminan en y=91 y la barra empieza en y=137 (46 px de separación).
- Búsqueda: elegir un resultado centra el mapa en ese lugar (zoom 16), muestra «Ubicado: …» y deja el lugar cargado como destino de «Trazar ruta», sin abrir el panel que tapaba el mapa. El placeholder dice «Buscar lugar, calle o local (Enter)…». Verificado con «Café Tortoni»: encontrado y ubicado.
- Verificación: lint sin errores; 75 pruebas; build sin errores.
- Decisión a confirmar: la búsqueda ya no abre la ruta automáticamente (antes sí). Si preferís que abra «Trazar ruta» como antes, es un cambio de una línea.
- Pendiente: la búsqueda de lugares depende de Nominatim (ver A18: su política no admite autocompletar, pero sí buscar al confirmar, que es como funciona ahora).

## 2026-10-06 — SES-089 — Auditoría completa: bugs y mejoras de búsqueda (Claude Code)

- Pedido de Rodo: auditar toda la app y avanzar con el listado, decidiendo lo que no requiera su aprobación.
- Hecho en esta sesión:
  - **B2 (ETA absurdo):** el GPS solo estima el tiempo desde 15 km/h (antes el piso era 1,5 m/s, unos 5 km/h, y daba «554 min»). Por debajo se usa el reparto proporcional de la ruta. Constante `VELOCIDAD_MIN_PARA_ETA_GPS`.
  - **S1 y S2 (recientes):** los últimos cinco lugares elegidos se guardan en `localStorage` (`motosafe_busquedas_recientes`). Al enfocar el buscador vacío aparecen como «Recientes». Verificado en el navegador.
  - **B5 (etiqueta):** el `aria-label` del buscador coincide con el placeholder.
  - **A2 (área táctil):** la lupa pasa de 30 a 36 px, y el botón de borrar la búsqueda tiene al menos 36 px.
- Pendiente, con decisión o trabajo grande:
  - **B1 (distancia de maniobra en línea recta):** requiere la geometría de la ruta por paso. Sin decisión tuya, queda como está, con la corrección de SES-087 para que no se trabe.
  - **B3 (vista previa de la ruta antes de elegir):** pendiente.
  - **B4 (la búsqueda abre o no «Trazar ruta»):** decisión tuya. Hoy solo centra el mapa.
  - **B6 (modal de bienvenida por origen):** decisión tuya si se pasa a una cookie o a la cuenta.
  - **B7 (chunk del mapa de 1 MB):** no se reduce más sin cambiar de librería.
  - **S3 (categorías), S4 (ficha del lugar), S5 (autocompletado):** S5 depende de elegir otro proveedor de búsqueda (A18). S3 y S4 requieren diseño.
  - **N1 a N7 (navegación):** la voz (N2) y compartir llegada (N4) son las más pedidas en Waze y Maps; las dos requieren decisión de alcance.
  - **M1 (leyenda), P2 (íconos sin texto), P1 (paneles):** propuesta visual antes de tocar.
  - **R1 a R3 (reportes), A1 (contraste), A3 (sin conexión):** pendientes.
- Verificación: lint sin errores; 75 pruebas; build sin errores.

## 2026-10-06 — SES-090 — Sugerencias de búsqueda con TomTom, reloj fuera de la barra y contraste (Claude Code)

- Decisiones de Rodo: la búsqueda no abre «Trazar ruta» (queda como está); sin voz ni compartir llegada por ahora; sí sugerencias mientras se escribe; el contador de segundos de la barra debe desaparecer.
- Cambios:
  - **Backend, `GET /lugares`:** busca lugares con TomTom Search desde el servidor (la clave no sale del backend). Mínimo 3 caracteres, hasta 8 resultados, caché de 10 minutos por consulta, limitador de 60 pedidos por minuto. Etiqueta: nombre, calle y localidad. Idioma `es-ES` (TomTom rechaza `es-AR`, lo detecté al probar: el endpoint devolvía 502). Pruebas nuevas con TomTom simulado: 108 pruebas de backend en verde.
  - **Frontend:** el hook `useBusquedaDireccion` sugiere a los 350 ms de dejar de escribir, para la barra de búsqueda, origen y destino. Enter o el botón buscan al instante. `buscarSugerencias` ahora llama a `/lugares`, así que Nominatim queda solo para guardar favoritos. Verificado en el navegador: «Cafe Tortoni» muestra sugerencias sin Enter.
  - **Barra superior:** se quitó «hace Ns», que cambiaba cada segundo. Se borró el hook `useSegundosDesde`.
  - **Contraste (tema claro):** `--text-dimmer` pasaba de 3,4–4,0 a 4,2–4,9 (ratio WCAG). Ahora cumple 4,5 en las tres superficies claras.
- Verificación: lint sin errores; 75 pruebas de frontend; 108 de backend; build sin errores.
- Pendiente, con costo o diseño propio (lista de SES-089): distancia de maniobra por la ruta, vista previa de la ruta antes de elegirla, ficha por lugar y categorías, texto de duración y quién confirmó en los reportes, modo sin conexión.
- A revisar: el cupo y los términos de TomTom para búsqueda, además del ruteo (ya están en la lista de términos antes de uso comercial).

- **SES-090 (ajuste):** elegir un resultado de la búsqueda ya no cambia el zoom: el mapa se desplaza al lugar con el zoom actual. Antes forzaba zoom 16. El efecto de vuelo usa el zoom que venga en `vuelo` y, si no viene, el actual del mapa. Lint, 75 pruebas y build sin errores.

- **SES-091:** al tocar la barra de búsqueda en iPhone, Safari hacía zoom a toda la interfaz, porque los campos tenían 13 px (iOS hace zoom debajo de 16 px). Ahora todos los campos quedan en 16 px en pantallas de hasta 480 px, y los del login también. Lint, 75 pruebas y build sin errores. No lo probé en un iPhone real: en el navegador de prueba no se reproduce el zoom de Safari; hay que confirmarlo en el celular.
- **SES-091 (corrección):** la regla de 16 px no aplicaba a la barra de búsqueda y a los campos de ruta, porque sus selectores (`.searchbar input`, `.ruta-form input`) tienen más especificidad que `input`. Ahora también los apuntan directamente. Visto en capturas de iPhone: al tocar la barra, Safari hacía zoom.

- **SES-092:** al tocar «Trazar ruta» en celular, el panel de origen y destino aparecía corrido a la derecha y después se acomodaba. Causa: la animación `panelIn` escribía `transform: translateY(0)`, que reemplazaba el `translateX(-50%)` con el que se centran los paneles. Ahora la animación usa la propiedad `translate`, que se combina con `transform`. Lint, 75 pruebas y build sin errores. No verificado en el navegador: la pestaña de prueba no dibujaba en ese momento; hay que confirmarlo en el celular.

## 2026-10-06 — SES-093 — Revisión punta a punta: «Ir» explícito y favoritos con /lugares (Claude Code)

- Decisiones de Rodo: no bajar la contraseña (queda en 4 caracteres por ahora); voz y compartir llegada fuera; búsqueda con «Ir» explícito; vista previa de la ruta sí; favoritos sin Nominatim.
- Cambios:
  - **Búsqueda:** elegir un resultado centra el mapa y muestra una tarjeta con el nombre y dos botones: «Cerrar» e «Ir». Antes el destino se cargaba sin aviso. «Ir» calcula la ruta desde el origen cargado o desde tu ubicación; sin ubicación, abre el panel para elegir el origen.
  - **Favoritos:** `geocodificar` pasa de Nominatim a `/lugares` (primer resultado, con caché de 5 minutos). Se quitó el helper de Nominatim que quedó sin uso. Nominatim ya no se usa en el frontend.
- Vista previa: las alternativas de ruta ya se dibujan en el mapa cuando el panel de opciones está abierto (capa `rutas`). No verifiqué en el navegador que la opción elegida se distinga de las demás; queda para confirmar en el celular.
- Verificación: lint sin errores; 75 pruebas; build sin errores. Verificado en el navegador: la tarjeta aparece con nombre, «Cerrar» e «Ir». No verificado: el botón «Ir» con ubicación real (el navegador de prueba no tiene GPS).
- Revisión punta a punta: el listado completo está en el chat, con las decisiones tomadas.

## 2026-10-06 — SES-094 — Distancia de maniobra por ruta y datos de vigencia de reportes (Claude Code)

- Avance del listado de la revisión punta a punta (sin decisiones pendientes de Rodo).
- Cambios:
  - **Distancia a la maniobra por la ruta (N1):** la tarjeta de navegación usa el recorrido sobre la polilínea (`calcularProgresoRuta` del paso menos el recorrido actual), en vez de la línea recta. Si no hay geometría, cae a la línea recta.
  - **Vencimiento de reportes:** el backend devuelve `vence_en` por reporte (según la vigencia de su categoría). El popup muestra «vence en N h / N días» junto a la antigüedad, con `formatearVence` (pruebas nuevas).
  - **Votos:** el popup dice «✓ Sigue ahí · N confirmaron». No se muestran nombres de quienes confirmaron: los votos son anónimos y mostrar identidades expondría a los usuarios.
- Verificación: lint sin errores (corrido desde `frontend`); 77 pruebas de frontend; 108 de backend; build sin errores.
- No verificado en el navegador: la distancia por ruta durante un viaje real y el popup de reportes con datos reales.

## 2026-10-06 — SES-095 — Rediseño de la pantalla de viaje (Claude Code)

- Pedido de Rodo: mejorar toda la interfaz al iniciar un viaje.
- Cambios:
  - **Barra inferior única:** velocidad (círculo con km/h), tiempo en grande con los minutos, y debajo los km y la hora de llegada. «Salir» con etiqueta y área táctil de 44 px. Centrada, con borde verde. Reemplaza la barra anterior y el velocímetro suelto (que queda oculto durante el viaje).
  - **Tarjeta de maniobra:** la distancia a la maniobra pasa a 22 px.
  - **Reportar:** durante el viaje queda solo como ícono redondo, arriba de la barra. Con `aria-label` para lectores de pantalla.
- Verificación: lint sin errores; 77 pruebas; build sin errores. En el navegador de prueba el contenido de la barra es correcto: «29 KM/H · 27 min · 12,8 km · llegás 03:31 p. m. · Salir». No pude medir posiciones (el panel de prueba no dibuja en ese momento), así que la distribución visual queda por confirmar en el celular.

- **SES-096 — marcador de posición en viaje:** durante el viaje el marcador es la flecha (puck) también en 2D, no solo en la vista inclinada. En 2D la flecha gira con el rumbo (`rotate` sobre el SVG); en la vista inclinada queda apuntando hacia arriba porque el mapa gira. Se pasa `modoViaje` al mapa. Las dependencias del efecto del marcador quedaron con `modoViaje`.
- Verificación: lint sin errores; 77 pruebas; build sin errores.
- **No verificado:** en el navegador de prueba no aparece ningún marcador de posición, ni siquiera fuera del viaje. Como el problema se ve también con las dependencias originales, lo más probable es que el arnés de prueba no fije la ubicación igual que la app real (el mismo flujo funcionó en capturas de celular). Hay que confirmar en el celular que la flecha aparece y gira.

- **SES-097 — ajustes del viaje según capturas:** el aviso de reruteo («Te desviaste, recalculando») baja debajo de la tarjeta de maniobra, para no tapar la escena; la hoja de reportar durante el viaje se apoya sobre la barra inferior, con altura máxima de 46 % de la pantalla y scroll, para no tapar el mapa. Verificado por CSS y build (lint y pruebas sin errores); pendiente de confirmar en el celular.

- **SES-098 — viaje y hoja de reporte:**
  - **Bug:** la hoja de reportar durante el viaje tapaba el botón de reportar y no había forma de cerrarla. Ahora tiene un botón de cerrar en la cabecera (cancela el reporte).
  - **Estilo Maps/Waze:** durante el viaje, reportar y la llave pasan a una columna a la derecha, en círculos de 52 px; la barra inferior tiene sombra más liviana.
  - Verificado: lint, 77 pruebas y build sin errores. Pendiente: confirmar en el celular la columna derecha y el cierre de la hoja.
- Pendientes del rediseño (no hechos): «Luego» como bloque separado en la tarjeta de maniobra, chip de velocidad con la misma forma que los botones, y ocultar «Modo Viaje» durante el viaje.

- **SES-099 — pulido del viaje (primera tanda):** la línea «Después:» pasa a un bloque «Luego» separado, con etiqueta y borde superior, dentro de la tarjeta de maniobra. Durante el viaje se oculta el chip de estado «Modo Viaje» de la barra superior. Verificado en el navegador: el bloque «Luego» aparece con el texto del siguiente giro; la leyenda no se renderiza durante el viaje. Lint, 77 pruebas y build sin errores. Pendiente: confirmar en el celular; pulido de velocidad, colores y modo oscuro del viaje.

## 2026-10-06 — SES-100 — Scraper: TN recuperado y tope de notas por fuente (Claude Code)

- Pedido de Rodo: mejorar la cantidad y calidad de las fuentes, en tres etapas: arreglar fuentes caídas, verificar nuevos medios y revisar fuentes no periodísticas.
- Causa de TN: `descubrir_sitemaps_desde_robots` no seguía redirecciones (`www.tn.com.ar` redirige) y devolvía vacío, así que nunca usaba los sitemaps que `robots.txt` declara. Corregido con `follow_redirects=True`.
- Tope por fuente: `MAX_URLS_POR_FUENTE` pasa de 40 a 60 (Clarín devolvía 72 URLs y se bajaban 40).
- Medición en seco (no se guardó nada): 151 candidatas (antes 136), 79 ubicadas (antes 78). TN aporta 20 candidatas y 4 ubicadas.
- Página12: el feed responde bien (redirige con barra final). Tiene pocos items en el feed; su cero es de volumen, no de bloqueo.
- Clarín: sigue en cero. El sitemap devuelve 72 URLs, pero solo una pasa el prefiltro por palabras del slug. Además su primer sitemap hijo son páginas de sección, no notas. Pendiente: identificar qué sitemap hijo trae notas y cómo se nombran.
- Verificación: 20 pruebas del scraper en verde; corrida en seco exit 0.
- Pendiente: etapa 2 (nuevos medios locales, con verificación de robots, feeds y términos) y etapa 3 (fuentes no periodísticas y redes: Instagram, Facebook y X quedan descartadas por sus términos; Telegram, Bluesky y Reddit se evalúan con su política).

- **SES-101 — Clarín y medios locales:**
  - Clarín: su primer sitemap en `robots.txt` era el de páginas de sección. Ahora los sitemaps con «news» se prueban primero; Clarín pasa de 0 a 20 candidatas (1 ubicada).
  - Medios locales nuevos, verificados el 2026-10-06 (robots.txt sin bloqueo total, feed RSS con notas): Un/Medio (Morón), Diario Anticipos, Qué Pasa Web (zona norte), Informe Norte (zona norte) y El Sol (La Plata/zona sur). Quedan afuera Gazeta Norte y Zona Norte Visión (feed sin notas) y los que no tienen feed.
  - Medición en seco (no se guardó nada): 172 candidatas (antes 151), 81 ubicadas (antes 79). Los cinco medios nuevos aportan poco hoy: sus feeds son chicos.
  - Verificación: 20 pruebas del scraper en verde; corrida en seco exit 0.
  - Pendiente: fuentes no periodísticas (comunicados oficiales) sin verificar todavía; y el cuello de botella de la ubicación, que es lo que llega al mapa.

## 2026-10-07 — SES-102 — Viaje: el modo viaje no se apagaba al llegar (Claude Code)

- Bug reportado por Rodo: la tarjeta de maniobra llega a decir "Llegaste a destino" pero el viaje sigue activo, nada lo corta.
- Causa: `pasoActual` llega al último índice de pasos (el de tipo `arrive`) apenas la posición entra en su radio de maniobra (30 m, el mismo que cualquier giro) y se queda ahí para siempre; ningún efecto apagaba Modo Viaje.
- Corrección: nuevo efecto que, con el paso activo en `arrive` y la posición real a menos de 25 m del punto de destino (más estricto que el radio de maniobra a propósito), apaga el viaje por el mismo camino que el botón «Salir» y muestra el toast "Llegaste a destino" en vez del genérico "Modo Viaje desactivado". De paso se corrigió que el botón «Salir» pasaba `desactivarModoViaje` directo a `onClick`, así que el evento del click se colaba como el nuevo parámetro de mensaje.
- Verificación: lint, 77 pruebas de frontend y build sin errores. **No verificado:** GPS real llegando al punto de destino (no hay forma de simular eso en el arnés de prueba); confirmar en el celular.
- Commit: `2ce6801`.
- **Prueba real (Rodo, mismo día):** con origen y destino en el mismo lugar, el viaje seguía sin apagarse pese al fix. Causa: el radio de 25 m no alcanza a cubrir la distancia real entre el punto de "arrive" que da TomTom (la dirección geocodificada) y la posición del GPS del celular. Se sube a 60 m, más parecido a lo que usan Maps/Waze para un destino por dirección. Verificado: lint, 77 pruebas y build sin errores. Commit `d60c9e0`. Preview de producción reconstruido y confirmado sirviendo el build nuevo (hash `index-CljP09jJ.js`) en `localhost:5175` y en el Funnel público.
- **Segunda prueba real (Rodo, mismo día):** seguía sin cortar, "0 m / 0.0 km" en pantalla. Causa real encontrada: la tarjeta mide la distancia restante SOBRE LA RUTA (`distanciaManiobraKm`/`calcularProgresoRuta`), no en línea recta -- con origen y destino en el mismo lugar la ruta mide ~0 km y la tarjeta ya decía "0 m", pero el efecto de llegada comparaba contra la distancia en línea recta real entre el GPS y el punto de "arrive" de TomTom (la dirección geocodificada, no donde está parado el usuario). Subir el radio no lo resolvía: las dos mediciones no comparaban lo mismo. Corregido para usar el mismo cálculo que ya ve el usuario en pantalla; el radio vuelve a 30 m (el mismo orden que el radio de maniobra normal, razonable con una medición precisa). Verificado: lint, 77 pruebas y build sin errores. Commit `ddaf76f`. Preview reconstruido y confirmado (hash `index-CFe5vjir.js`). Pendiente: confirmar en sitio real.

## 2026-10-07 — SES-104 — Login: primer caso de la limpieza visual (Claude Code)

- Pedido de Rodo: sensación general de que la app se ve "poco pulida, frágil, trucha", sin poder decir por qué. Eligió que el foco fuera visual.
- Medido en `App.css`: 11 valores de `border-radius` distintos, más de 20 sombras y 12 tamaños de letra sueltos. El archivo ya tenía una escala completa (`--r-*`, `--fs-*`) agregada en una sesión anterior justo para esto, con un comentario propio que decía "los valores sueltos que quedaron fuera de la escala... son los candidatos reales a unificar, pero eso sí cambia algo visible -- se resuelven de a uno, viendo cada caso en pantalla". Nunca se había hecho ese trabajo.
- Se arrancó por el login: primera pantalla que ve cualquiera, chica, verificable sin backend (el estado `anonimo` de `LoginGate` se ve sin login real). Pasa de objetos de estilo inline a clases en `App.css`, con la escala existente (sin inventar valores nuevos): marca (ícono de moto), labels sobre los campos, `:focus` real con el mismo azul del resto de la app, spinner de carga ya usado en otros botones, resplandor radial sutil.
- Bug de build encontrado y corregido: un comentario CSS con "*/" escondido dentro del texto (`--r-*/--fs-*`) rompía el minificador (`lightningcss`).
- Verificación: lint y 77 pruebas sin errores. Visto en el navegador (servidor estático sobre `dist/`, sin necesitar backend) en ancho de escritorio y de celular (375px). Preview de producción reconstruido y confirmado sirviendo el build nuevo.
- Commit: `cef869a`.
- Pendiente: el resto de `App.css` (1300+ líneas) sigue con los valores sueltos fuera de la escala; este fue un caso acotado para mostrar la dirección antes de seguir con el resto.

- **SES-105 — segunda tanda, con la app real a la vista:** Rodo pidió revisar toda la app, todos los flotantes, colores, "como vos consideres". Para no tocar a ciegas, se montó un backend y un Vite dev local con `AUTH_HABILITADO=false` temporal (solo para ver las pantallas detrás del login sin credenciales reales, sin tocar el despliegue público), y se revisó en el navegador: mapa, búsqueda, reportar, menú de herramientas, capas.
  - Al mirar los valores "sueltos" medidos en SES-104, la mayoría resultaron ser familias ya consistentes (10px, 14px y 18px se repiten varias veces cada uno) que la escala simplemente no llegó a nombrar — no es indecisión, es una escala incompleta. No se tocaron.
  - Problema real encontrado y corregido: la atribución del mapa (control nativo de MapLibre) no tenía ningún estilo propio — una franja blanca fija de punta a punta, ajena al tema de la app. Pasa a una píldora chica en la esquina con la misma piel que el resto de los flotantes.
  - `report-fab` ("Reportar") tenía el único radio realmente suelto del archivo (30px, sin otro uso) y un font-size sin token (14px). Pasan a `var(--r-pill)` (cambio invisible, ya era píldora completa) y `var(--fs-lg)`.
  - Barra de búsqueda, panel de capas, menú de herramientas y tarjeta de ruta: revisados, ya consistentes entre sí.
  - **No se tocó la paleta de colores.** Cambiarla sin verla en cada pantalla (login, mapa, viaje real con GPS, reporte, estadísticas) es el mismo error que llevó a la sensación de "trucho" en primer lugar; queda para una ronda futura con más pantallas verificadas.
  - **Hallazgo de infraestructura (aparte del pedido de Rodo):** `run_dev.py` (`uvicorn --reload`) arrancaba su proceso hijo real con el Python del sistema (`AppData\Local\Python\pythoncore-3.12-64`), no con el venv del proyecto (`backend/venv312`) — así que el backend de desarrollo corría fuera del entorno fijado (A22). Además, el puerto 8000 tenía procesos "fantasma" (visibles en `netstat` con PIDs que `tasklist`/`Get-Process` no reconocían, probablemente de una corrida vieja de Docker/WSL) que absorbían las conexiones y hacían fallar los reinicios en silencio. Se reinicia ahora sin `--reload`, directo con `venv312`. Pendiente: decidir si `run_dev.py` se corrige para fijar el intérprete, o se deja de usar `--reload` en desarrollo.
  - Verificado: lint, 77 pruebas y build sin errores. Visto en el navegador. Preview de producción reconstruido y confirmado. `AUTH_HABILITADO=false` revertido del `.env` local; nada de esto tocó el despliegue público ni credenciales reales.
  - Commit: `1a8e86b`.

- **SES-106 — búsqueda (radio, categoría, pin) y popups:** siguiendo el plan acordado con Rodo (popups y detalle de zona, jerarquía de "Reportar", modo claro) más dos pedidos nuevos: un pin en el mapa para el lugar buscado (como Maps/Waze) y la sensación de que la búsqueda no encuentra algunos lugares.
  - **Búsqueda, causa real medida contra TomTom:** el radio de 60 km (`backend/main.py`, `/lugares`) dejaba afuera lugares conocidos pero lejos de CABA -- "Luján basilica" devolvía una capilla en una calle de CABA llamada Luján, no la Basílica real (en la ciudad de Luján, ~65 km). Con 150 km aparece la real. Probado que una búsqueda genérica ("panadería") sigue siendo local: el sesgo sigue en CABA, solo cambia el límite duro.
  - `/lugares` ahora devuelve `categoria` (del POI de TomTom, con traducción de las más frecuentes), mostrada como subtítulo en la tarjeta del lugar elegido.
  - **Pin nuevo en el mapa** para el lugar buscado (`elementoPin` en `MapaMotoSafe.jsx`), forma de gota. Bug encontrado y corregido en el camino: la animación de caída animaba `transform` sobre el MISMO elemento que MapLibre usa para posicionar el marker, pisando esa posición -- el pin quedaba en (0,0) de la pantalla. Mismo problema de fondo que `panelIn` ya había resuelto una vez; se corrige animando un div interno.
  - **Popups y detalle de zona** (pedido 1 del plan): revisados en el navegador. La tarjeta de detalle de zona y el popup de prensa ya estaban bien armados -- las barras de GRAVE/LEVE/MORTAL miden bien (se sospechó un bug viéndolas en una captura muy comprimida; con mejor resolución no era tal). Lo que sí tenía el blanco/negro por defecto del navegador: el botón nativo de cerrar de MapLibre y la punta del globo. Corregido con la misma piel que el resto de los cierres de la app.
  - **Modo oscuro** (el default) revisado: mapa, chrome, atribución, todo consistente.
  - **Pendiente del plan:** jerarquía de "Reportar" (parcial, ver SES-105) y modo claro pantalla por pantalla -- quedan para la próxima ronda.
  - Verificado: lint, 77 tests de frontend, 105 de backend (completos) y build sin errores.
  - **Bloqueo de infraestructura, sin resolver:** el puerto 8000 (backend real, el que usa el preview público) quedó con una reserva fantasma de Windows -- `netstat` lo muestra `LISTENING` con un PID que ni `tasklist` ni `taskkill` reconocen, probablemente una reserva de Hyper-V/WSL2 por Docker Desktop. `Restart-Service winnat` (el arreglo habitual) pide permisos de administrador que esta sesión no tiene. **Los cambios de frontend (pin, popup, atribución) están en producción** (preview reconstruido y confirmado); **los de backend (radio de 150 km, categoría) están commiteados pero NO están en producción** hasta reiniciar el backend real. Alcanza con reiniciar Docker Desktop o la PC; después correr `tailscale/reiniciar_app.bat` o `iniciar_app_tailscale.bat`.
  - Commit: `3ec640d` (búsqueda/pin), `ebabe28` (popups).

- **SES-107 — la causa real de "no encuentra": sesgo fijo en CABA (Claude Code):**
  - Rodo confirmó que "no encuentra" pasa seguido, no solo con lugares lejanos tipo Luján -- farmacias, comida, lugares en general.
  - Causa encontrada: `/lugares` siempre sesgaba la búsqueda desde el centro de CABA (`lat=-34.6, lon=-58.45` fijos), sin importar dónde estuviera el usuario. Confirmado con una consulta directa a TomTom: "farmacia" con sesgo en CABA devuelve farmacias porteñas a 0,5-0,8 km; la MISMA consulta con sesgo en Moreno devuelve farmacias de Moreno a 100-400 m. Con el límite de 5 resultados, alguien en Moreno nunca veía la farmacia que tenía al lado. En una app para usarse en moto por todo el GBA, esto afectaba la mayoría de las búsquedas fuera del centro -- la explicación real detrás de la sensación de "no encuentra nada".
  - Corregido: `/lugares` acepta `lat`/`lng` opcionales (la posición real del usuario) y los usa como centro de sesgo si están dentro de Argentina (valida contra un bbox del país, para que un GPS roto en `(0,0)` no sesgue a cualquier lado); sin eso, cae al centro de CABA de siempre. La clave de caché suma el centro redondeado a ~1 km, para no mezclar resultados de zonas distintas bajo la misma consulta de texto. El frontend manda `miUbicacion` desde `useBusquedaDireccion` (origen, destino y la barra de búsqueda).
  - Verificado: lint, 79 tests de frontend (2 nuevos), 108 de backend (3 nuevos) y build sin errores. Probado en vivo con un backend local: la misma consulta "farmacia" devuelve Moreno cuando se manda esa posición.
  - Commit: `8d58d04`. Preview de frontend reconstruido y confirmado en producción. **El backend real (puerto 8000) necesita otro reinicio para tener este cambio** -- mismo bloqueo de infraestructura de SES-106 (puerto fantasma de Windows), sin resolver todavía. Pendiente que Rodo corra `tailscale/reiniciar_app.bat` de nuevo.

- **SES-108 — respaldo gratuito en Nominatim cuando TomTom no sirve (Claude Code):**
  - Rodo probó 4 casos reales después del arreglo de sesgo: cafetería Fika en Pilar, USAL en Pilar, Paseo Champagnat, un barrio privado (Lomas Verdes). Pidió una alternativa sin costo.
  - Medido caso por caso: Fika y Paseo Champagnat SÍ están en TomTom (el problema era el sesgo, ya resuelto en SES-107). El campus de la USAL en Pilar NO está en TomTom bajo ningún nombre probado, pero SÍ en Nominatim/OpenStreetMap (como "college").
  - Primer intento (llamar a Nominatim solo si TomTom vuelve vacío) no alcanzaba: TomTom casi nunca vuelve vacío, devuelve una coincidencia fonética sin relación ("Calle A. Camus" para "USAL Campus Pilar"). Se cambia el criterio a `_algun_resultado_relevante`: exige que la primera Y la última palabra significativa de la consulta aparezcan en el MISMO resultado de TomTom. Solo la primera fallaba con "Universidad del Salvador Pilar" (daba por buena otra sede de la misma universidad en CABA); solo la última fallaba con cualquier cosa cercana a Pilar (el sesgo de ubicación mete "Pilar" en casi todo).
  - Cuando no hay nada relevante, Nominatim se consulta una vez y sus resultados van PRIMERO en la lista -- si TomTom ya llenó el cupo de resultados con cosas irrelevantes, agregar los buenos al final no servía, el límite los cortaba. Se descartan duplicados a menos de 300 m.
  - Límite real, no resuelto: "USAL" como sigla no lo reconoce ninguna de las dos APIs, hace falta el nombre completo. Un barrio privado puede no estar en ninguna base de comercios -- para esos casos la app ya permite marcar el punto a mano tocando el mapa.
  - Verificado: 114 tests de backend (6 nuevos) sin errores. Probado en vivo contra las dos APIs reales con un backend local en un puerto nuevo cada vez (ver nota de infraestructura abajo): "Universidad del Salvador Pilar" trae el campus de Pilar primero; "Fika Pilar" sigue resolviendo solo con TomTom.
  - **Nota de infraestructura:** durante la verificación, reiniciar el backend de prueba en el mismo puerto (8001) sirvió una y otra vez al proceso VIEJO en vez del nuevo -- `pkill` (desde Bash/MSYS) no estaba matando el proceso real de Windows de forma confiable, un problema similar (aunque de causa distinta) al de los PID fantasma de SES-106/107. Se resolvió usando un puerto nuevo en cada intento. Pendiente: si esto se repite, preferir `Stop-Process` por PID exacto (vía `Get-CimInstance`) a `pkill`.
  - Commit: `10af154`. Rodo corrió `reiniciar_app.bat` después de este commit -- confirmado por la hora del proceso (16:10) posterior a la del archivo (16:06): el backend real ya tiene este cambio y el de SES-107.

- **SES-109 — la ubicación nunca se pedía sola (Claude Code):**
  - Rodo probó "farmacia" parado en Pilar, con el GPS del iPhone activado, y seguía trayendo resultados de CABA -- "no noto el cambio".
  - Causa real: la app nunca pedía la ubicación automáticamente al abrirse. `miUbicacion` quedaba en `null` hasta que el usuario tocaba "Mi ubicación" o arrancaba un viaje -- el permiso del sistema operativo estaba dado, pero la app nunca había llamado a `getCurrentPosition`. El sesgo de SES-107 no tenía nada que usar.
  - Corregido: pedido de ubicación una vez al montar la app, en silencio (sin mover el mapa, sin toast, sin el spinner del botón "Mi ubicación"). Si no hay permiso, falla en silencio y queda como antes.
  - Verificado: lint, 79 tests y build sin errores. Visto en el navegador (sin GPS real en el entorno de prueba): carga sin errores de consola.
  - Commit: `5a40745`. Solo tocó frontend -- preview reconstruido y confirmado, sin necesitar otro reinicio del backend.

- **SES-110 — la causa real, encontrada con el indicador temporal (Claude Code):**
  - Rodo seguía viendo solo direcciones de CABA al buscar "farmacia", con el GPS activado. Para no seguir adivinando sin acceso a las devtools del teléfono, se agregó un indicador temporal chico en los resultados de búsqueda mostrando si la última búsqueda mandó la ubicación real. Rodo confirmó coordenadas reales de Pilar (-34.4180, -58.9817) -- la ubicación SÍ llegaba al backend. El bug estaba más adentro.
  - Probado directo contra nuestro propio backend con esas coordenadas: dos bugs compuestos.
    1. `_buscar_lugares_nominatim` (el respaldo de SES-108) nunca recibía el centro del usuario -- siempre pedía con el viewbox de Argentina entera. Con una caja tan grande, el "sesgo" no sesgaba nada en la práctica: Nominatim devolvía su propio orden de "importancia" (más densidad de POI mapeados en CABA que en Pilar), sin importar la ubicación real. Corregido: recibe `centro_lat`/`centro_lon` y arma un viewbox de 1 grado (~110 km) alrededor del centro real.
    2. Con el viewbox angosto, "farmacia" en esas coordenadas SÍ resolvía bien en TomTom (Bayer Pilar, Fada Fharma, Biofarma -- laboratorios del parque industrial de Pilar, todos a menos de 1 km), pero `_algun_resultado_relevante` los rechazaba a TODOS: comparaba por substring exacto, y ninguno contiene la palabra completa "farmacia" (son nombres de marca). Eso disparaba el respaldo de Nominatim sin necesidad, que por el bug 1 terminaba devolviendo CABA de cualquier forma. Corregido: la comparación pasa a similitud de texto (`difflib.SequenceMatcher`, umbral 0,55) en vez de substring exacto.
  - Se saca el indicador de diagnóstico temporal, ya cumplió su función.
  - Verificado: 116 tests de backend (completos, 3 nuevos), 79 de frontend y build sin errores. Probado en vivo con las coordenadas reales de Rodo: "farmacia" ahora devuelve 5 resultados de Pilar, todos a menos de 1 km.
  - Commit: `4c0786d`. **Necesita reinicio del backend real** (tocó `main.py`) -- pendiente que Rodo corra `reiniciar_app.bat` de nuevo. Preview de frontend ya reconstruido y confirmado.

## 2026-10-09 — SES-111 — Revisión total: cerrar ítems abiertos del backlog (Claude Code)

- Pedido de Rodo: revisión total del proyecto y "empezar a cerrar todo". Aclarado con dos preguntas: "cerrar" significa cerrar ítems existentes del backlog (no preparar la entrega todavía), y "sumar complejidad" explícitamente NO -- foco en cerrar lo abierto, nada nuevo. Coherente con "Qué conviene evitar por ahora" del propio backlog.
- Triage de los ~30 ítems "en curso"/"validado parcialmente": separados los que dependen de código/pruebas (los que se puede cerrar) de los que dependen de revisión del tutor, confirmación visual de Rodo, o datos que no existen (esos no se inventan, quedan marcados).
- **A07 → Validado.** Re-verificado contra el código actual: `GET /reportes` lista columnas explícitas, nunca `delete_token_hash` ni `autor_id`. 20/20 pruebas de reportes/borrado/votos en verde. No quedaba nada de código pendiente; el estado "validado parcialmente" estaba desactualizado.
- **V08 → Validado.** QA visual real en el navegador (pendiente desde que se armó el panel único de capas): escritorio, ancho de celular (375 px), tema claro y oscuro. Sin problemas de contraste, recorte ni superposición. La primera captura en celular parecía desvaída -- era la animación de entrada a mitad de camino, no un bug; se confirmó esperando y repitiendo.
- **T05:** se instaló `gh` (GitHub CLI) en la PC, un paso real hacia confirmar la corrida de CI. Queda bloqueado en `gh auth login`, que es una autorización de la cuenta de Rodo (OAuth en el navegador) -- no es algo para hacer sin que lo pidan. Pendiente que Rodo lo corra una vez.
- **A14:** investigado qué significa en concreto "falta retirar compatibilidad transitoria". `_asegurar_esquema_reportes_una_vez`/`_asegurar_tabla_prensa` en `main.py` crean tres tablas en tiempo de ejecución; de esas, solo `reportes_colaborativos` tiene migración versionada propia. No se puede retirar ese código sin romper una base nueva hasta escribir migraciones para `reportes_confirmaciones` y `reportes_prensa` y probarlas contra PostgreSQL real. No cerrado -- quedó documentado el paso concreto que falta, en vez de la nota vaga anterior.
- Verificado: pruebas de backend relacionadas con A07 en verde (20/20); QA visual de V08 con evidencia de pantalla en cuatro combinaciones.
- Pendiente para la próxima ronda: seguir el triage con el resto de los ítems "en curso" (A11 distancia a segmentos, A17 perfilado, A19 script de limpieza inicial, A23 ejecución real de accesibilidad, F08 contratos de estado de reportes), separando siempre lo que depende de código de lo que depende de Rodo/tutor/datos.

## 2026-10-09 — SES-112 — A09: cierre del hallazgo de localidades sin ubicar (Claude Code)

- Pedido: continuar el triage de SES-111 ("Cerrar ítems del backlog existente", "nada nuevo por ahora").
- Al retomar, `git status` mostraba cambios sin commitear en `backend/scrapear_noticias_robos.py` y su test, de una sesión anterior que no había cerrado ese trabajo. No era código nuevo que yo agregara: era trabajo ya escrito, pendiente de verificar y cerrar.
- Revisado el diff: agrega `LOCALIDADES_GBA`/`encontrar_localidad` (Nordelta, Punta Lara, Canning, Glew -- el hallazgo de "alias de localidad no reconocidos por el gazetteer" de A09, medido en el dry-run 2026-10-06), corrige la pausa a Nominatim de 1,1 s a 15 s (la política real para scripts periódicos es 4 pedidos/min, no 1/s), agrega caché por corrida y manejo explícito de bloqueo 429 (`NominatimBloqueado`).
- Verificado antes de cerrar: 25/25 pruebas del scraper, 117/117 de toda la suite de backend (9 skip esperados, de integración con PostgreSQL real que no estaba levantada).
- **A09:** se amplía la nota existente con este cierre -- sigue en "Validado parcialmente" porque A09 en general tiene más pendientes (deduplicación semántica, validación de calles), pero el hallazgo específico de localidades sin ubicar queda resuelto y documentado.
- Pendiente para la próxima ronda: A11 (distancia a segmentos), A17 (perfilado), A19 (script de limpieza inicial), A23 (ejecución real de accesibilidad), F08 (contratos de estado de reportes).

## 2026-10-09 — SES-112 (cont.) — A17: perfilado real del mapa

- Pedido: continuar el triage de SES-111/112, siguiente ítem de la lista ("A17 perfilado").
- Método: instrumentación temporal en `App.jsx` y `MapaMotoSafe.jsx` (contador de renders en `window`, y un diff de props entre renders consecutivos), levantando el mismo entorno de prueba local (backend en puerto libre con `AUTH_HABILITADO=false`, Vite apuntando a ese backend) y midiendo en vivo con el navegador de Claude, en reposo (sin interacción) durante ventanas de ~30-40s.
- Primera medición salió contaminada: mis propias ediciones del archivo mientras medía disparaban recargas en caliente (HMR) que inflaban el conteo -- no era un problema real de la app. Al dejar de editar y medir limpio, el resultado fue estable: `MapaMotoSafe` solo vuelve a renderizar cuando al menos un prop cambia de verdad (confirmado con el diff), nunca por un re-render vacío de `App.jsx`. Los renders que sí ocurren (cada ~9-30s) coinciden con el polling documentado (reportes y hora cada 30s) y son esperados, no un leak.
- Encontrado de paso: el comentario que justifica el `React.memo` en `MapaMotoSafe.jsx` citaba `useSegundosDesde`, un hook que ya no existe en el código (fue retirado en un refactor anterior sin actualizar el comentario). Corregido para reflejar el estado real: el tick es de 30s (`horaActual`), no de 1s.
- **A17** sigue "En curso": la separación incremental de `App.jsx` (2140 líneas) no se hizo en esta pasada -- es un refactor de mayor escala, no algo para resolver dentro de una sesión de perfilado. Lo que se cerró es el perfilado en sí, con evidencia real en vez de la nota vacía anterior.
- Verificado: 79/79 pruebas de frontend, lint y build limpios. Entorno de prueba (backend/Vite de prueba, `AUTH_HABILITADO=false`) limpiado por completo al terminar.

## 2026-10-09 — SES-112 (cont.) — A19: script canónico de limpieza inicial

- Pedido: continuar el triage ("continua hasta terminar con todo lo pendiente"), siguiente ítem: A19.
- `docs/modelo/PIPELINE_CANONICO.md` documentaba el paso 0 (limpieza de siniestros, produce `motos_limpio.csv`) como "sin script": salía de la sección 1 del notebook histórico, que no corre de punta a punta.
- Leído el notebook (`notebooks/01_eda_hotspots_moto.ipynb`) celda por celda para esa sección: filtra una fila con error de exportación de Excel, normaliza texto, agrega `comuna` (regex sobre `comuna_siniestro`), convierte coordenadas a numérico y descarta inválidas, filtra a `MOTO`. Encontrado al leer: el notebook carga y limpia `siniestros_viales_victimas.csv` en esta misma sección pero nunca lo usa para producir `motos_limpio.csv` -- se vuelve a leer, aparte, recién en la sección de ablación demográfica (A03). `PIPELINE_CANONICO.md` lo listaba como entrada del paso 0, lo cual no reflejaba el código real.
- Escrito `notebooks/limpiar_siniestros_motos.py`, mismo estilo que el resto de `notebooks/*.py`. Corrido contra los CSV crudos del repo y comparado por SHA256 contra el `motos_limpio.csv` vigente: **idéntico byte a byte**. `git status` después de correrlo no mostró cambios en el CSV (confirma la igualdad).
- **A19** sigue "Validado parcialmente": lo que cerraba este script ya cerró. Sigue pendiente correr los pasos que dependen de red (fetch de delitos/clima/corredores) contra los servicios reales en una corrida de punta a punta, no solo contra una copia ya descargada.
- Siguiente: A23 (ejecución real de accesibilidad), F08 (contratos de estado de reportes), y después revisar el resto de la tabla "Ejecución actual" separando lo que depende de código de lo que depende de Rodo/tutor/datos.

## 2026-10-09 — SES-112 (cont.) — A23: ejecución real de la matriz de accesibilidad

- Pedido: "continua hasta terminar con todo lo pendiente" -- siguiente ítem: A23.
- Ejecutada en el navegador la matriz de `docs/calidad/QA_ACCESIBILIDAD_VISUAL.md`, escenario por escenario, con el mismo entorno de prueba local de sesiones anteriores.
- **Teclado:** Tab en el modal de bienvenida (onboarding) se escapaba del modal. Confirmado con `document.activeElement`: el foco quedaba en `.theme-toggle`, un botón tapado por el overlay, sin ningún anillo visible; Enter sobre ese foco invisible cambió el tema de claro a oscuro sin que hubiera forma de verlo pasar. Es un bug real de accesibilidad (foco "fantasma"), no cosmético. Corregido en `Onboarding.jsx`: trampa de foco (Tab/Shift+Tab circulan solo entre los dos botones del modal), Escape cierra, foco inicial en "Entendido", `role="dialog"`/`aria-modal`. Verificado con eventos de teclado reales via `KeyboardEvent` despachado directo -- la acción `key: Tab` del navegador de prueba de Claude no dispara el mismo camino de `preventDefault` que un navegador real, así que esa verificación particular no sirve para confirmar un focus-trap; quedó anotado para no reinterpretarlo como que el fix "no funciona" en una revisión futura.
- **Zoom 200%:** la topbar desborda el viewport y pide scroll horizontal, pero todo sigue utilizable (scroll con mouse y foco de teclado, que autodesplaza el elemento enfocado a la vista). No es un bug, es el comportamiento esperado de un layout que no colapsa a columna a ese zoom.
- **Tema y Móvil:** verificados combinados (claro/oscuro × 360×740, 390×844, 740×360 horizontal) sin problemas de contraste ni solapamiento.
- **Movimiento reducido:** no se pudo alternar la preferencia real del sistema operativo con las herramientas de navegador disponibles en esta sesión (no hay control de `prefers-reduced-motion` expuesto). Verificado en cambio por revisión de código: la regla en `App.css` es global, con `!important`, cubre todo el árbol -- bajo riesgo de animación suelta sin cubrir. Se deja registrado como límite de la verificación, no como "aprobado visualmente".
- **Red:** con el backend de prueba apagado a mitad de sesión (no en frío, para no confundir con el login), se probó cada capa. La mayoría ya tenía datos en caché y no mostró el problema. Activar "Tráfico en vivo" sí lo mostró: 20 pedidos de tiles a `/api/trafico/tiles/...` devolvieron 502 (confirmado en `read_network_requests`), y la interfaz no dio ningún aviso -- el panel de capas seguía marcando la opción como activa, el único aviso existente (`traficoNoDisponible`) solo se mostraba como toast si el usuario intentaba activarla una SEGUNDA vez. Agregado un banner inmediato (mismo patrón que corredores/inseguridad: fuente del fallo + botón "Reintentar tráfico"), probado apagando y prendiendo el backend real.
- **A23** pasa a "Validado parcialmente" (de "En curso"): la matriz completa se corrió con evidencia real, con dos bugs encontrados y corregidos. Sigue pendiente un dispositivo físico real (todo lo de hoy fue emulación de navegador) y la preferencia real de movimiento reducido.
- **V10** se amplía: el caso de tráfico sin aviso quedó cerrado con el mismo patrón que ya tenían corredores/inseguridad.
- Verificado: 79/79 pruebas de frontend, lint y build limpios. Entorno de prueba limpiado por completo.
- Siguiente: F08 (contratos de estado de reportes), y después revisar el resto de la tabla "Ejecución actual" separando lo que depende de código de lo que depende de Rodo/tutor/datos.

## 2026-10-09 — SES-112 (cont.) — A14: retiro de la compatibilidad transitoria de reportes

- Pedido: "continua hasta terminar con todo lo pendiente". F08 (contratos de estado de reportes) requiere un endpoint y una pantalla nuevos -- eso es sumar función, no cerrar algo abierto, así que lo dejo documentado sin implementar y sigo con A14, que sí es cerrar algo ya empezado.
- Al revisar `backend/migrations/001_reportes_colaborativos.sql` para escribir la migración que faltaba, encontré que la nota de SES-111 estaba parcialmente equivocada: `reportes_confirmaciones` **ya tenía** migración (compartida en el archivo `001`, junto con `reportes_colaborativos`). Solo `reportes_prensa` genuinamente no tenía una. Corregido en BACKLOG.md para no dejar el dato incorrecto como si fuera definitivo.
- Escrita `backend/migrations/003_reportes_prensa.sql` con el mismo esquema exacto que creaban `_crear_o_actualizar_tabla_prensa` (`main.py`) y `_asegurar_tabla` (`scrapear_noticias_robos.py`).
- Verificación con una base real, **no la personal de Rodo** (`motosafe-db`, puerto 5432, container ya corriendo -- no se tocó): se levantó un PostGIS 16 descartable aparte (`motosafe-test-a14`, puerto 55432), se aplicaron las tres migraciones y se comparó el esquema resultante (`\d`) contra lo que creaban las funciones de compatibilidad -- columnas, tipos, índices, constraints y foreign keys, todo idéntico.
- Antes de retirar el código, encontré un riesgo real que había que resolver primero: `_iniciar_backend.bat` (como arranca Rodo el backend en desarrollo) llama a `run_dev.py` directo, sin pasar nunca por `migrar.py` -- solo el entrypoint de Docker lo hacía. Si retiraba los guards sin arreglar esto, el primer arranque local contra una base nueva se habría roto con "relation does not exist". Se agregó el paso de migración al `.bat`, antes de `run_dev.py`.
- Retiradas de `backend/main.py` las cinco funciones transitorias y sus 8 puntos de llamada (`_asegurar_tabla_reportes`, `_asegurar_tabla_confirmaciones`, `_asegurar_esquema_reportes_una_vez`, `_asegurar_tabla_prensa`, `_crear_o_actualizar_tabla_prensa`). El guard propio del scraper standalone se dejó a propósito -- corre antes que nada más en una corrida manual, es barato, y sacarlo no cerraba ningún problema real (solo le sumaba riesgo a una corrida directa sin backend/migraciones de por medio).
- Un test unitario (`test_esquema_reportes_se_asegura_una_sola_vez_por_proceso`) probaba directamente las funciones retiradas; se eliminó. Dos tests de integración (`test_ciclo_de_reportes_con_base_real`, `test_prensa_excluye_google...`) hacían `monkeypatch.setattr` sobre los flags `_esquema_reportes_listo`/`_esquema_prensa_listo`, que ya no existen; se limpiaron esas líneas (la fixture `migrada` ya aplica las migraciones antes de cada test, así que no hacía falta reemplazarlas por nada).
- Verificado: 125/125 pruebas (116 sin PostgreSQL + 9 de integración) contra la base de prueba real, con las migraciones ya aplicadas y sin los guards. Build/lint no aplican (cambio solo de backend). Contenedor de prueba (`motosafe-test-a14`) eliminado al terminar.
- **A14** pasa a "Validado parcialmente" (de "En curso"): la compatibilidad transitoria que bloqueaba el cierre ya no existe. Queda abierto si conviene separar `reportes_confirmaciones` en su propio archivo de migración (hoy comparte el `001` con `reportes_colaborativos`, válido pero con un nombre de archivo que solo menciona una tabla) -- decisión de estilo, no un bloqueo.
- Con esto se cerró toda la lista de ítems "en curso" que no dependen de Rodo/tutor/datos (A11, A17, A19, A23, F08, A14). Lo que queda abierto en la tabla "Ejecución actual" depende de: revisión de dirección académica (A01-A04), actas de tutor (G05), requisitos institucionales no versionados (G03), `gh auth login` de Rodo (T05), o es investigación/análisis de mayor escala (D02, D03, D04, A06, A05) que no es "cerrar algo roto" sino trabajo de tesis en sí mismo -- no debería iniciarse sin que Rodo decida el alcance.

## 2026-10-09 — SES-113 — Decisiones de Rodo sobre lo pendiente, y cierre de A10

- Pedido: Rodo respondió la lista de preguntas de la ronda anterior (SES-112). Resumen de decisiones:
  - **A01-A02**: la gravedad condicionada a un siniestro y el protocolo temporal quedan en criterio del proyecto, no a la espera de una revisión académica externa. Pasan a Validado (ver BACKLOG.md). A03/A04 no se tocan: A04 sigue con una decisión de negocio genuina pendiente (costo relativo por clase), distinta de un trámite externo.
  - **G05**: Rodo tuvo una reunión con el tutor recientemente, pero el tutor no le da importancia a un registro formal de actas. Queda abierto pero de baja prioridad real -- no tiene sentido insistir con algo que no se pide.
  - **G03**: Rodo no tiene los requisitos institucionales documentados y pidió guía de cómo conseguirlos -- se le respondió en el chat (no es algo para resolver por archivo).
  - **A10**: pidió que la revisión visual la hiciera Claude. Hecha en el navegador (ver abajo).
  - **A18**: Rodo la revisa él mismo con `npm run dev`. Sin cambios de este lado.
  - **F08 y A11**: confirmó avanzar como función nueva ("dale" a ambos). Quedan para la siguiente etapa de esta sesión.
- **A10**: entorno de prueba local (backend+Vite de prueba, `AUTH_HABILITADO=false` temporal, revertido al terminar). Verificado en el navegador: la leyenda muestra "Siniestros 2019–2025 · GCBA" y, al activar inseguridad, "Delitos 2023–2025 · GCBA" -- cada texto con su propio tooltip (`title`) con fecha exacta de generación del archivo, confirmado leyendo el DOM (`archivo_generado`: siniestros 2026-09-07, corredores 2026-09-04 -- fecha distinta, confirma que no es un valor pegado a mano --, delitos 2026-09-09). Prensa muestra "nota más reciente hace 1h" con tooltip de fecha/hora exacta. Sin solapamiento ni corte de texto con dos líneas de leyenda a la vez. Pasa a Validado.
- Verificado: sin cambios de código en este bloque (A10 era solo revisión visual); entorno de prueba limpiado por completo.
- Siguiente: F08 (contratos de estado de reportes) y A11 (distancia a segmentos), como función nueva confirmada por Rodo.

## 2026-10-09 — SES-113 (cont.) — F08 y A11, como función nueva confirmada por Rodo

- Pedido: Rodo confirmó ("dale") avanzar F08 (estados de reportes propios) y A11 (distancia a segmentos) como función nueva, ya no solo cerrar lo existente.
- **F08**: diseño del contrato antes de tocar código. `GET /reportes` excluye a propósito lo vencido/retirado -- el mapa público solo muestra lo vigente, eso no cambia. Para el historial propio hacía falta una vía separada, identificada por la misma credencial privada que ya autoriza borrar (id + delete_token, ver A07), no una cuenta ni login. Se agregó `POST /reportes/mios`. Se extrajo `_estado_reporte` (vigente/vencido/desmentido) de `listar_reportes` para no duplicar la lógica de vigencia y consenso entre los dos endpoints -- verificado que el refactor no cambió el comportamiento existente (los tests de `/reportes` siguen en verde sin tocarlos).
- Bug propio encontrado durante el desarrollo (test de integración real lo atrapó, no inspección de código): armar el mapeo id→token con un dict perdía el token correcto si el mismo id venía dos veces en la consulta con tokens distintos -- el último pisaba al primero. Cambiado a un conjunto de pares (id, hash), corregido y vuelto a probar.
- Frontend: panel de "Actividad reciente" ahora pide el historial completo solo al abrirse (`POST /reportes/mios` con los tokens guardados en localStorage), muestra vencido/desmentido atenuados junto a lo vigente, con su propio texto de estado. El pill de la topbar, antes clickeable solo si había algún reporte vigente, ahora lo es mientras exista algún reporte propio (vigente o no) -- si no, alguien con todos sus reportes vencidos perdía el acceso a su propio historial. "Borrar mis reportes" se dejó acotado a lo vigente (no se tocó esa lógica).
- Verificación real, sin tocar la base personal de Rodo (contenedor PostGIS descartable aparte, con sus propias migraciones aplicadas): creado un reporte real desde la UI, confirmado "Vigente"; backdateado el `creado_en` directo en la base para simular vencimiento sin esperar 12h reales, confirmado "Venció · hace 13h"; creado un segundo reporte y desmentido con dos votantes distintos vía API, confirmado "Retirado por la comunidad". Probado también en ancho de celular (390px), sin solapamiento.
- **A11**: `calcularZonasCruzadasPorRuta` ya calculaba la distancia real de cada zona al trazado (`distanciaAPolilinea`) para decidir si pasaba el umbral, pero la descartaba al filtrar -- quedaba un booleano "cruza o no", no la distancia real. Se cambió para que devuelva `distanciaSegmentoKm` en cada zona. La tarjeta de ruta ahora muestra esa distancia junto a cada zona ("a 40 m", "a 551 m"), alineada a la derecha, apagada visualmente (dato secundario). Probado en vivo trazando una ruta real (Obelisco → Caballito) contra el servicio público de OSRM: la tarjeta mostró las distancias reales y distintas para cada zona cruzada, en escritorio y en celular.
- Verificado: 131/131 pruebas de backend (incluida integración con PostgreSQL real) y 81/81 de frontend, lint y build limpios en ambos. Entorno de prueba (contenedor Docker descartable, backend/Vite de prueba, `AUTH_HABILITADO=false`) limpiado por completo al terminar -- en ningún momento se tocó la base personal de Rodo (`motosafe-db`, puerto 5432).
- Con esto, de la lista de preguntas de la ronda anterior solo quedan abiertas las que dependen de Rodo directamente: su revisión de A18 con `npm run dev`, y su decisión sobre los ítems de investigación/análisis de mayor escala (D02-D04, A05-A06) y los menores de bajo esfuerzo que quedaron listados sin decisión todavía.

## 2026-10-11 — SES-114 — Rediseño fuerte del frontend: Fase 0 (tokens)

- Pedido: Rodo pidió un rediseño fuerte de toda la aplicación ("diseño, disposición, accesibilidad, pantallas"), no un retoque. Instaló la skill `/ui-ux-pro-max` primero, pero su modo `--design-system` resultó ser para landing pages de marketing (devolvió "Hero + CTA + Start trial" dos veces, sin sentido para una herramienta operativa ya construida) -- Rodo mismo decidió no forzarla. Buscamos entre el catálogo de plugins y encontró **Design** (oficial de Anthropic: design-critique, design-system, accessibility-review, design-handoff, etc.), que sí instaló.
- Antes de tocar código: exploración completa del frontend (2 agentes Explore) -- inventario de las ~25 pantallas/paneles de la app y de la arquitectura de tokens CSS actual (`frontend/src/App.css`, 1443 líneas). Plan mode con un agente Plan para diseñar 6 fases reviewables (no un cambio gigante de una sola vez), aprobado por Rodo con la condición de ir fase por fase, con su visto bueno entre cada una. Plan guardado en `C:\Users\rodol\.claude\plans\dreamy-juggling-tower.md` (fuera del repo, es un artefacto de Claude Code).
- Hallazgo real que motivó parte del plan (contraste WCAG calculado, no opinión): `--text-dimmer` en tema oscuro daba 3.65:1 contra el fondo, por debajo del mínimo AA de 4.5:1. Además, decenas de usos reales de colores de riesgo (amarillo/verde/naranja/rojo/azul) como color de texto directo (confirmado con grep), varios de los cuales en tema claro caían muy por debajo de 4.5:1 (hasta 1.4:1 el amarillo).
- Con **Design** ya instalada, se corrió `design:design-system` sobre el estado actual antes de extenderlo -- confirmó los mismos hallazgos (sin escala de espaciado, 3 tratamientos de superficie flotante sin resolver, `.hazard-edge` aplicado sin regla formal) con el formato de auditoría propio de la skill.
- **Fase 0 implementada** en `frontend/src/App.css`: `--text-dimmer` corregido a `#808689` (4.87:1 en oscuro -- con margen sobre el mínimo pero por debajo de `--text-dim` a propósito, para no invertir la jerarquía visual); tipografía base de 12px a 14px (y toda la escala corrida proporcionalmente); escala de espaciado `--sp-1` a `--sp-8` (no existía ninguna); `--surface-float` unificado (reemplaza los 3 tratamientos de opacidad/blur que convivían sin resolver); 5 variantes `*-text` por color de riesgo, calculadas con la fórmula de contraste WCAG real (no a ojo) contra `--bg` y `--surface-solid` en cada tema -- en oscuro los colores originales ya pasaban (salvo `--rojo` contra superficie, ajustado con un `#FF3D3D` casi imperceptible), en claro los 5 necesitaron una variante más oscura/saturada; `.hazard-edge` formalizado con un comentario que explica la regla (qué paneles sí, cuáles no, y por qué) en vez de dejarla como una decisión implícita.
- Nada de esto cambia el matiz de los colores de riesgo usados como swatch/punto/ícono -- las variantes `*-text` son solo para texto, y se van a aplicar sitio por sitio en la Fase 3 (donde ya se identificaron los casos reales por grep).
- Verificado: `npx eslint .`, `npx vitest run` (81/81) y `npx vite build` en verde. Entorno de prueba (backend/Vite descartables, `AUTH_HABILITADO=false` temporal, revertido) para revisión visual en el navegador: claro y oscuro × desktop/390px/landscape, sin cortes ni desbordes por el texto más grande.
- Siguiente: Fase 1 (chrome principal -- login, pantalla de carga, topbar, toggle de tema), a la espera del visto bueno de Rodo sobre la Fase 0.

## 2026-10-11 — SES-114 (cont.) — Rediseño fuerte, Fase 1 (chrome principal)

- Topbar/marca/login: `.brand-name` tenía un font-size suelto de 19px (justo uno de los "candidatos a unificar" que el propio código ya señalaba) -- tokenizado a `--fs-xl`. Padding de topbar y login a `--sp-*` donde había coincidencia exacta con la escala nueva.
- Encontrado y corregido de paso: `.clima-badge` y `.topbar-status` (dos pills hermanos, misma fila) tenían padding horizontal distinto entre sí (6px/10px vs 6px/12px) sin ninguna razón -- unificados a `--sp-2 --sp-3` ambos.
- `.theme-toggle` ya estaba en 44px (verificado en la exploración previa), sin cambios.
- Verificación específica del sistema `--topbar-h`: forzado el pill de estado a un texto largo real en 375px de ancho (el caso que rompía paneles en el historial del proyecto) -- la topbar pasó a 2 líneas y el buscador se acomodó solo debajo, sin superponerse. El `ResizeObserver` sigue midiendo bien después del cambio de padding.
- Login no se vio en vivo en esta pasada (el entorno de prueba usa `AUTH_HABILITADO=false` para no pedir credenciales) -- su único cambio fue `16px` → `var(--sp-4)`, coincidencia exacta, cero diff visual posible por construcción.
- Verificado: eslint/vitest(81)/build en verde. Entorno de prueba limpiado.
- Siguiente: Fase 2 (controles flotantes sobre el mapa: zoom, escala, leyenda, FABs), a la espera del visto bueno de Rodo.

## 2026-10-11 — SES-114 (cont.) — Rediseño fuerte, Fase 2 (controles flotantes)

- `--surface-float` unificado en zoom-controls/legend/herramientas-menu (antes 0.95/0.92/0.97 de opacidad conviviendo sin motivo, con y sin blur consistente).
- Auditoría de touch targets con medición real en el navegador (`getBoundingClientRect`, no estimada a partir del CSS): `.route-fab` daba 41px de alto, `.herramientas-menu button` 37px, `.legend-item` 19px -- los tres por debajo de cualquier piso razonable.
- Decisión con criterio, no aplicación ciega de "44px en todos lados": `.route-fab` y `.herramientas-menu button` son controles primarios (trazar ruta, modo viaje) -- se llevaron a 44px, mismo piso que zoom/recenter/herramientas-fab (ya estaban así, con comentario explícito de Rodo sobre manejar/guantes). La leyenda es distinta: es una lista de filtros que se usa parado/sentado, no manejando, y Rodo ya había pedido explícitamente que fuera compacta (comentario existente: "Achicada a pedido de Rodo... sin aportar tanto"). El mínimo real de WCAG 2.5.8 (AA) para web es 24px, no 44px -- esa cifra más alta es convención de iOS/Android para controles nativos, no un requisito universal. Se llevó `.legend-item`/`.legend-reset` a 24px: cumple el mínimo real sin contradecir el pedido de "compacto".
- Verificado con medición después del cambio: `.route-fab` 44px, `.herramientas-menu button` 44px, `.legend-item` 24px, confirmados con el mismo método (no solo lectura del CSS).
- Verificado: eslint/vitest(81)/build en verde, revisión visual en ambos temas y específicamente el cluster de FABs en landscape (el punto más denso), sin superposiciones con los controles más grandes.
- Siguiente: Fase 3 (familia de paneles: capas, actividad, estadísticas, detalle de zona) -- ahí entra la auditoría de contraste de colores de riesgo usados como texto, y el `.detalle-cerrar` que quedó anotado en esta fase (botón de cerrar sin padding, hit area de solo 14-16px, en actividad/stats/detalle) para corregir ahí.

## 2026-10-11 — SES-114 (cont.) — Rediseño fuerte, Fase 3 (familia de paneles)

- `--surface-float` unificado en capas-panel/actividad-panel/stats-panel/detalle-panel (antes 0.96/0.97/0.92).
- Auditoría de contraste real (no visual, calculada) sobre los 4 sitios de esta fase donde un color de riesgo se usa como texto o ícono funcional: `.capas-opcion.activa .capas-opcion-icono` (azul, ícono -- 2.59:1 en claro, bajo el piso de 3:1 no-textual), `.actividad-borrar` (rojo, texto del botón -- 4.47:1 en superficie oscura, bajo 4.5:1), `.stats-top-item:hover .cercanas-nombre` (azul, texto) y `.detalle-ajuste-motivo` (azul, texto) -- los 4 pasados a sus variantes `*-text` de la Fase 0.
- Encontrado al revisar los chips de filtro de prensa (`CapasPanel.jsx`): `.capas-prensa-filtros` usaba `var(--surface-soft, ...)`, `var(--text-muted, ...)` y `var(--surface, ...)` -- ninguno de esos 3 tokens existe en ningún otro lado de `App.css`, así que siempre caían al valor de respaldo fijo entre paréntesis, sin adaptarse al tema. Medido: el texto del título de filtros daba 3.18:1 contra la superficie en tema oscuro (bajo el mínimo), siempre, porque nunca usó el tema real. Reemplazados por los tokens reales (`--border`, `--inset`, `--text`, `--text-dim`) ya usados en el resto del archivo.
- `.detalle-cerrar` (anotado como pendiente al cerrar la Fase 2): sin padding ni tamaño propio, el hit area real era solo el ícono de 14px. Usado en actividad/stats/detalle -- corregido a padding 5px + mínimo 24x24, con la posición del `.detalle-panel .detalle-cerrar` (absoluta) ajustada para que el ícono quede visualmente en el mismo lugar de antes.
- Verificado con medición real en el navegador después de cada cambio: `.detalle-cerrar` 24x24, `.capas-prensa-filtros button` 32px (ya estaba bien), `.capas-opcion` 63-77px (sobra), `.stats-top-item` 48px (sobra) -- todos por encima del mínimo.
- Verificado: eslint/vitest(81)/build en verde, revisión visual en ambos temas (capas, estadísticas, chips de prensa).
- Siguiente: Fase 4 (flujo de planificación de ruta: buscador, formulario de ruta, opciones de ruta, navegación) -- la fase más compleja del rediseño.

## 2026-10-11 — SES-114 (cont.) — Rediseño fuerte, Fase 4 (flujo de ruta)

- La fase con más auditoría de contraste de todo el rediseño: ~12 sitios adicionales donde un color de riesgo se usaba como texto, corregidos a sus variantes `*-text` -- badges de ruta (Rápida/Equilibrada/Menor exposición), niveles de riesgo bajo/medio/alto/crítico en cada tarjeta de ruta, desglose siniestro/inseguridad, hint y error del formulario de ruta, chip de favorito guardado.
- Corrección sobre la propia Fase 0: `--naranja-text` y `--azul-text` habían sido calculadas contra `--bg`/`--surface-solid` sólidos y pasaban ahí, pero los badges de `ruta-resumen` las usan sobre su propio fondo tintado (el color al 15% de opacidad sobre la superficie) -- contra ESE fondo real daban 4.37/4.40:1, por debajo del mínimo. Recalculadas contra el caso más exigente (el fondo tintado), así sirven para los dos contextos sin tener que duplicar variantes.
- Agregado `--magenta`/`--magenta-text`: el eje de "inseguridad" en el desglose de ruta usaba un magenta hardcoded (`#FF3B7F`) fuera del sistema de tokens, que fallaba en tema claro (3.09:1). Se le dio el mismo tratamiento que los 5 colores de riesgo.
- Decisión documentada: los niveles de riesgo en la tarjeta de ruta (nivel-bajo/medio/alto/critico) tenían un comentario explícito pidiendo que usaran "los mismos 4 colores que la leyenda... para que se lean exactamente igual". Se mantiene la misma FAMILIA de color (sigue siendo "el amarillo", "el rojo") pero con la variante de texto, porque el valor exacto del swatch no pasa 4.5:1 como texto chico en tema claro -- la leyenda (donde el color es un punto, no texto) no se tocó, ahí el piso real es 3:1.
- `.navegacion-siguiente` (CSS muerto, confirmado en la Fase 2 sin referencias en JSX) eliminado, incluida su regla en el breakpoint landscape.
- `--surface-float` aplicado a searchbar, ruta-form, ruta-resumen, lugar-card. `.navegacion-panel` no se tocó: es una de las superficies intencionalmente opacas (decisión ya tomada en la Fase 0).
- Verificado con el recorrido real completo del flujo en el navegador, no solo capturas sueltas: buscar "Obelisco" → elegir resultado → ver tarjeta de lugar → Trazar ruta → completar origen/destino → ver las 3 opciones de ruta con zonas cruzadas, distancias y badges → Iniciar viaje → panel de navegación con maniobra actual y "Luego" (confirma que borrar la clase muerta no rompió nada) → mini-resumen de viaje → Salir. Repetido en celular (390px) en tema claro.
- Verificado: eslint/vitest(81)/build en verde.
- Siguiente: Fase 5 (alertas, toasts, banners, flujo de reportar) -- última fase del rediseño.

## 2026-10-13 — SES-114 (cont.) — Rediseño fuerte, Fase 5 (final) y cierre del rediseño

- `.navegacion-distancia` (verde sobre superficie en el cartel de maniobra) pasado a `--verde-text`: medido, 1.78:1 en tema claro. El chip de ícono con fondo verde sólido y texto oscuro fijo al lado (mismo componente) no se tocó -- es un patrón distinto que ya pasaba de sobra (10.24:1).
- Dos touch targets corregidos con medición real en el navegador: el botón "Reintentar ahora" del banner de conectividad daba 22px (por debajo incluso del piso de 24px para un control secundario, y es la acción de recuperación de un error de red) -- llevado a 28px. Los botones de categoría del flujo de reportar (Robo, Zona insegura, Pavimento, Corte, Iluminación) daban 39px -- llevados a 44px, mismo criterio que route-fab/herramientas-menu (acción primaria parado junto a la moto).
- Reconfirmada la trampa de foco del modal de Onboarding (arreglada en SES-112) después de las 5 fases de cambios de markup del rediseño: Tab/Shift+Tab siguen ciclando correctamente entre los dos botones, Escape sigue cerrando. No se rompió en ningún momento, pero valía la pena reconfirmarlo explícitamente en vez de asumirlo.
- Verificación real, no solo capturas: la base de prueba estaba caída de entrada esta sesión (Docker Desktop no estaba corriendo), así que el banner "Sin conexión con el backend. Reintentando cada 5s." apareció solo, sin tener que forzar nada -- se aprovechó para verificar ese escenario real. El flujo de reportar se probó también con GPS fallido (categorías deshabilitadas, mensaje "tocá el mapa para marcar dónde fue").
- Barrido final honesto: quedan valores de font-size/radius sueltos fuera de la escala en el velocímetro, el resumen de viaje (nav-resumen-mini) y los popups del mapa (construidos como DOM crudo en MapaMotoSafe.jsx, fuera del árbol JSX de App.jsx). No se tocaron en esta pasada -- no son los sitios donde se midió un problema real de contraste o de tamaño táctil, y migrar el archivo entero a la escala de un tirón sería un trabajo bastante más grande que el que pidió esta fase. Queda como pendiente de pulido menor, documentado como tal y no como "ya resuelto".
- Verificado: eslint/vitest(81)/build en verde. Entorno de prueba limpiado.

### Cierre del rediseño (6 fases, SES-114)

Resumen de lo que cambió en todo el rediseño, de punta a punta:
- **Tokens nuevos**: escala de espaciado (`--sp-1` a `--sp-8`, no existía ninguna), tipografía base de 12px a 14px, superficie flotante unificada (`--surface-float`, antes 6+ valores de opacidad distintos sin motivo), 6 variantes de texto con contraste WCAG verificado para los colores de riesgo + inseguridad (`*-text`).
- **Accesibilidad real, no declarativa**: un fallo de contraste confirmado y corregido (`--text-dimmer`), ~20 sitios de color de riesgo usado como texto auditados y corregidos uno por uno contra su fondo real (no a ojo), 7 touch targets corregidos con medición en el navegador (no estimados desde el CSS), 3 variables CSS fantasma encontradas y reemplazadas por tokens reales.
- **Limpieza**: una clase CSS muerta eliminada, una regla de diseño (`.hazard-edge`) formalizada con su criterio explícito.
- **Nada de lógica tocada**: ningún cambio en `App.jsx` fuera de estructura/estilo de presentación; el sistema de posicionamiento vivo (`--topbar-h`), `prefers-reduced-motion`, la prevención de zoom de iOS y la trampa de foco del Onboarding se verificaron intactos en cada fase.
- Las 6 fases se verificaron por separado (eslint + vitest + build + revisión visual en ambos temas × 3 anchos, más recorridos reales de los flujos más complejos) antes de pasar a la siguiente, con aprobación de Rodo en cada paso.

## 2026-10-13 — SES-115 — Ronda 2 de rediseño: pulido profesional extendido (en curso)

Pedido de Rodo tras cerrar SES-114: mejora total, fuerte, en los detalles, aprovechando una sesión larga y un plugin/skill de diseño nuevo (instalado: **VectorLab UI/UX Skills**, además del **Design** ya instalado en SES-114). A diferencia de SES-114 (enfocada en contraste WCAG y touch targets), esta ronda ataca motion, consistencia de botones de ícono, y pulido visual general. Se trabaja en tandas, verificando y commiteando cada una por separado.

**Tanda 1 — motion tokens y botones de ícono:**
- Inventario completo del frontend hecho con un subagente de exploración antes de tocar nada (componentes, estados de carga/error/vacío, formularios, botones de ícono, animaciones, estructura de pantallas) -- base real para decidir qué atacar, no a ojo.
- `--motion-fast/base/slow/panel/fade/reveal` agregados a `:root`: el archivo usaba 7 duraciones de transition/animation sueltas (0.12s a 0.6s) para el mismo tipo de interacción en sitios distintos. Se nombraron las que ya predominaban (0.15/0.2/0.25/0.45/0.5/0.6s) sin cambiar ningún tiempo visible; quedaron afuera a propósito 0.12s (legend-reset) y 0.4s (dimming de navegación), que son outliers de un solo uso con una razón puntual ya documentada en su propio selector.
- Tres botones de ícono corregidos a 36px (el tamaño que ya usan sus hermanos en los mismos formularios -- searchbar-icon, searchbar-clear, report-sheet-cerrar): `.ruta-form-swap` (estaba en 26px, por debajo del piso), `.ruta-form-pin` y `.ruta-resumen-editar` (no tenían tamaño propio: el hit area real era solo el ícono de 13-14px). Verificado con medición real en el navegador (36×36 los tres).
- El selector de feedback táctil `:active { scale(0.93) }` (una lista manual de ~19 clases, señalada como frágil en el inventario) ampliado con 11 botones de ícono que no tenían ningún feedback al tocar: recenter-fab, viaje-salir, detalle-cerrar, onboarding-cerrar/entendido, searchbar-icon/clear, ruta-form-swap/pin, ruta-resumen-editar, report-sheet-cerrar.
- Revisado pero NO cambiado: los badges de cluster de prensa (`.marker-prensa-cluster`/`-grupo`) usan colores hex fijos que no responden a `data-theme`. Verificado en vivo en ambos temas -- en tema oscuro se ven menos "fuertes" que en claro, pero el borde claro los sigue recortando contra el mapa; no es una falla real de legibilidad, así que no se forzó un cambio sin problema medido.
- Revisado pero NO cambiado: el panel de estadísticas (`zonasAjustadas`/`top5Peligrosas`) sale de un dataset estático que siempre tiene datos si el backend respondió -- el estado "vacío" que señalaba el inventario no es alcanzable en la práctica (ya cubierto por el loading screen y el banner de backend caído). El panel de actividad similar: el botón que lo abre ni siquiera queda clickeable (`tengoReportesPropios`) si no hay reportes, así que nunca se llega a un panel vacío.
- Entorno de prueba: Docker estaba arriba esta vez; backend de prueba requirió crear un venv nuevo (`backend/.venv_test`, descartable) porque no había ninguno con las dependencias instaladas. Verificado con recorrido real: carga inicial, onboarding, buscador con resultados reales, formulario de ruta completo (Obelisco → Plaza de Mayo), opciones de ruta, alternancia de tema.
- Verificado: eslint, vitest (81/81), build -- los tres en verde.

**Tanda 2 — jerarquía de títulos (revisada, sin cambios) y animación de salida de paneles:**
- Revisado primero si hacía falta una pasada de jerarquía tipográfica en títulos de panel: ya estaba resuelta desde SES-114 vía la clase compartida `.cercanas-title` (capas, actividad, estadísticas, opciones de ruta usan todos el mismo tratamiento -- mayúsculas, peso 700, `--fs-sm`). No se tocó nada acá: no había problema real que arreglar, solo se confirmó.
- Animación de salida de paneles: nuevo hook `hooks/usePanelSaliente.js` + clase `.panel-exit` (`@keyframes panelOut`, 0.18s -- más corta que la entrada a propósito, una salida rápida se siente responsiva). El hook NO cambia el estado que ya controla el resto de la app (los booleanos `capasAbiertas`/`actividadAbierta`/`statsAbierto` siguen siendo la única fuente de verdad para todo lo demás, incluido el cierre por Escape) -- solo retrasa 180ms cuándo React desmonta el panel, para que la animación de salida alcance a jugar.
- Aplicado a los 3 paneles más simples y de menor riesgo (booleano directo, sin condición compuesta con otro estado que cambie al mismo tiempo): `CapasPanel`, panel de actividad, panel de estadísticas. Deliberadamente NO aplicado a `detalle-panel` (zona) ni a `ruta-resumen` (opciones de ruta): tienen condiciones compuestas con otros estados que pueden cambiar en el mismo instante (ej. `zonaSeleccionada` + `rutasCalculadas`), y agregarles un desmonte retrasado sin auditar cada interacción habría sido el tipo de cambio apurado que este proyecto evita -- queda documentado como pendiente, no como hecho.
- Primer intento del hook falló el lint del proyecto dos veces seguidas (reglas estrictas de `react-hooks`: ni `setState` sincrónico en el cuerpo de un efecto, ni lectura/escritura de refs durante el render) -- resuelto con el patrón oficial de React de "ajustar estado durante el render" comparando contra estado (no contra un ref), y el timer de salida en un efecto aparte donde el `setState` ocurre dentro del callback de `setTimeout` (asincrónico, no en el cuerpo del efecto).
- Verificado en el navegador con `getBoundingClientRect`/clases reales, no solo mirando: apertura y cierre de capas y estadísticas, clase `.panel-exit` presente durante la ventana de 180ms y el nodo removido del DOM después, cierre por Escape sigue funcionando igual que antes.
- Verificado: eslint, vitest (81/81), build -- los tres en verde (el error de lint del primer intento del hook se detectó y corrigió antes de este commit, no llegó a quedar en verde en falso).
- Siguiente dentro de esta ronda: evaluar si corresponde extender la animación de salida a detalle-panel/ruta-resumen en una tanda aparte, auditando cada condición compuesta antes.

**Tanda 3 — revisión visual en celular (375px) y limpieza de los valores pendientes de SES-114:**
- Recorrido real en ancho de celular, ambos temas: carga inicial, formulario de ruta (swap/pin ya verificados en 36px también a este ancho), flujo de reportar completo con GPS fallido (categorías deshabilitadas + mensaje, igual que en desktop), panel de capas, estadísticas. Nada roto por los cambios de las tandas 1 y 2.
- De los 3 sitios que SES-114 había dejado documentados como pendientes (velocímetro, nav-resumen-mini, popups del mapa): `nav-resumen-mini` ya estaba completamente tokenizado (se revisó, no hacía falta nada). Los otros dos sí tenían problemas reales:
  - `.velocimetro strong` (18px) y `.velocimetro span` (8px) -- pasados a `--fs-xl`/`--fs-2xs`. El de 8px en particular quedaba por debajo de cualquier otro texto de la app, una etiqueta demasiado chica para leerse en movimiento.
  - `.popup-prensa-fuente` tenía un gris fijo (`#C9CDD3`) que nunca respondió al tema -- en tema claro, sobre el fondo blanco del popup (que sí es theme-aware), daba ~1.5:1 de contraste. Pasado a `--text-dim` (ya con las dos variantes verificadas de SES-114).
  - `.popup-grupo-prensa-item` (la lista de notas cuando varias caen en el mismo punto aproximado) estaba en colores de tema claro fijos de punta a punta -- border, texto y fondo -- sin ninguna variable. En tema oscuro se veía como una tarjeta clara flotando dentro de un popup oscuro. Pasado a los tokens que ya usa el resto de la app para este mismo patrón (`--inset`/`--border`/`--text`, hover `--border`). Verificado en vivo en ambos temas abriendo un popup agrupado real.
  - De paso, 3 valores de font-size que coincidían exacto con un token ya existente (`.popup-content strong` 14px, `.marker-prensa-grupo strong` 12px) pasados a `--fs-base`/`--fs-sm` sin cambiar ningún píxel.
- Verificado: eslint, vitest (81/81), build -- los tres en verde.

**Tanda 4 — extender la animación de salida a ruta-resumen y detalle-panel (los dos que se habían dejado afuera en la tanda 2):**
- `ruta-resumen` comparte el booleano `mostrandoOpcionesRuta` con los dos paneles de leyenda y el FAB de reportar (se ocultan mutuamente a propósito, no compiten por el mismo rincón de pantalla). Auditado antes de tocar nada: si solo `ruta-resumen` esperaba su animación de salida, la leyenda reaparecía de golpe mientras el panel de ruta todavía se estaba desvaneciendo encima -- exactamente el glitch que la tanda 2 evitó al no tocarlo sin auditar. Resuelto encadenando los 4 (`ruta-resumen`, las dos leyendas, `report-fab`) al mismo `panelRuta.montado` en vez de al booleano crudo: ahora la leyenda espera a que el panel de ruta termine de desvanecerse del todo antes de reaparecer. Verificado con medición real de clases y timing (50ms: panel de ruta con `.panel-exit`, leyenda todavía ausente; 300ms: panel de ruta desmontado, leyenda ya presente -- sin superposición en ningún punto intermedio).
- `detalle-panel` (zona) tenía un riesgo distinto: su condición combina 3 variables (`rutasCalculadas.length === 0 && !rutaAbierta && zonaSeleccionada`), y el contenido del panel lee directamente de `zonaSeleccionada` -- que pasa a `null` justo en el momento de cerrar. Si se retrasaba el desmonte sin más, el panel intentaría seguir leyendo `zonaSeleccionada.ajuste.nivel` con `zonaSeleccionada` ya en `null` y crashearía a mitad de la animación de salida. Resuelto con un segundo estado (`zonaMostrada`) que retiene la última zona no nula -- el contenido se lee de ahí, mientras la condición de visibilidad (`detalleVisible`) sigue combinando las 3 variables originales sin cambiar su significado.
- Primer intento de esta tanda generó errores reales en consola (`ReferenceError: panelDetalle is not defined`, visto mientras la edición estaba a mitad de camino) -- quedaron en el historial de consola del navegador y se los distinguió explícitamente de un problema real releyendo con una navegación fresca y repitiendo eslint/vitest/build después de terminar la edición, todos en verde.
- Verificado en el navegador con medición real (no solo mirando): apertura/cierre de detalle de zona con contenido real del modelo (zona con predicción Grave/Leve/Mortal), confirmado que el contenido sigue visible durante el fade de salida y que el nodo se desmonta después sin error de consola nuevo.
- Verificado: eslint, vitest (81/81), build -- los tres en verde.

## 2026-10-13 — SES-115 (cont.) — Feature nueva: tocar el mapa marca destino directo (estilo Maps)

Pedido explícito de Rodo (no parte del rediseño visual): poder tocar cualquier punto vacío del mapa y que se marque como destino, igual que Google Maps/Waze.

- Reutiliza por completo la tarjeta "lugar elegido" + botón "Ir" que ya existía para resultados de búsqueda (`lugarElegido`/`irAlLugar`) -- cero UI nueva, cero geocodificación inversa: el rótulo es "Punto en el mapa", mismo criterio de texto que ya usa "marcar en el mapa" en el formulario de ruta ("Punto marcado en el mapa").
- La dificultad real era no pisar los flujos que YA usan el toque sobre el mapa: marcar origen/destino/reporte (`campoActivo`), elegir una ruta alternativa o ver el popup de un corredor (las únicas dos capas GL con su propio click), y los marcadores DOM (zonas, clusters, prensa), que ya hacían `stopPropagation()` en su propio handler. Resuelto en `MapaMotoSafe.jsx`: el listener genérico de click del mapa primero respeta `campoActivo` (como ya hacía), y si no hay nada de eso activo, chequea con `queryRenderedFeatures` si el toque cayó en `corredores-layer`/`rutas-layer` antes de interpretarlo como "mapa vacío".
- Nueva condición en App.jsx (`tapRapidoHabilitado`): apagada mientras se está navegando, con "Opciones de ruta" abierta, o reportando -- en esos casos tocar el mapa no debería abrir una tarjeta de destino nueva.
- Verificado en el navegador, no solo leyendo el código: tocar mapa vacío → aparece la tarjeta con pin azul → "Ir" arma el destino y abre el formulario de ruta (igual que buscar una dirección). Tocar directamente un cluster de hotspots → dispara SOLO el zoom nativo del cluster, sin que aparezca la tarjeta de destino en simultáneo (confirmado con medición real de qué elementos había en el DOM después de cada click, no a ojo).
- Verificado: eslint, vitest (81/81), build -- los tres en verde.
- Siguiente: portal de "Actividad" (prensa + reportes de usuarios combinados, con filtros de categoría/fecha/zona, como pantalla completa).

## 2026-10-13 — SES-115 (cont.) — Feature nueva: portal de "Actividad" (prensa + reportes, pantalla completa)

Pedido explícito de Rodo: un botón que abra un "portal" de novedades/reportes sobre toda la ciudad (no solo lo propio), filtrable por categoría, fecha y zona.

- Componente nuevo `components/ActividadPortal.jsx` (no vive adentro de `App.jsx`, a diferencia de casi todo lo demás -- la propia auditoría de esta ronda señaló esto como un problema para iterar paneles de forma aislada; se aprovechó esta feature nueva para no sumar más a ese monolito).
- Combina `reportesPrensa` + `reportes` (reportes de usuarios ya fetcheados para el mapa, de TODOS los usuarios -- `/reportes` ya era colaborativo, no hizo falta ningún endpoint nuevo) en un solo feed, ordenado por fecha. NO reemplaza el panel chico de "Actividad reciente" (ese sigue siendo el historial de TUS propios reportes, con estados vigente/vencido/desmentido que esto no tiene) -- son dos cosas distintas, conviven.
- Filtro de zona: ni `reportes_prensa` ni `reportes_colaborativos` tienen un campo "zona"/"barrio" en la base (solo lat/lng, ver backend/main.py) -- se agregó `zonaMasCercana(punto, zonas)` a `utils/geoRiesgo.js` (reutiliza `distanciaKm`, ya existente) para calcularla contra `ZONAS_RIESGO`. Con un piso de 2 km: si la zona más cercana queda más lejos que eso, el ítem queda sin zona asignada en vez de etiquetarlo con una zona que en los hechos está lejos -- verificado en vivo con notas de La Matanza/La Plata, que correctamente no muestran ninguna zona de CABA.
- Primer intento de las etiquetas de categoría usaba la primera palabra de cada label ("Zona insegura" → "Zona") -- se superponía en significado con el selector de zona GEOGRÁFICA que va justo debajo, dos filtros distintos compitiendo por la misma palabra. Corregido con etiquetas cortas explícitas ("Inseguridad", "Cortes", "Iluminación").
- Corregido durante la implementación (no llegó a commitearse roto): el ítem de la lista tenía un `<a>` (link a la nota original) anidado dentro de un `<button>` -- contenido interactivo anidado, inválido en HTML. Cambiado a `<div role="button" tabIndex={0}>` con su propio manejo de teclado (Enter/Espacio), que es el patrón correcto para "fila clickeable que además contiene un link real".
- Reutiliza `usePanelSaliente` (mismo hook de las tandas 2/4) para la animación de salida -- un panel más de la familia, no un caso especial.
- Verificado en el navegador con interacciones reales, no solo mirando: filtro de categoría, de fecha (24h/7d/30d/todo) y de zona combinados con conteo de resultados correcto en cada combinación (incluido el caso 0 resultados con su mensaje); tocar un ítem centra el mapa ahí y cierra el portal (confirmado con un caso real: un ítem de La Plata centró el mapa exactamente en Plaza Moreno, La Plata); el link a la nota original tiene `href`/`target=_blank` correctos y no dispara el "ver en mapa" del ítem (gracias al `stopPropagation` del link). Revisado también en 375px.
- Límite de datos conocido y documentado como tal (no oculto): `/reportes` devuelve solo reportes de usuarios VIGENTES (filtrados por vigencia en el propio backend) -- no hay un endpoint de histórico colaborativo de TODOS los usuarios (el histórico que existe es por-usuario, vía `tokensReportes`). El portal muestra lo que hay disponible hoy; un histórico comunitario completo sería un cambio de backend, no de este portal.
- Verificado: eslint, vitest (81/81), build -- los tres en verde.

## 2026-10-13 — SES-115 (cont.) — Feedback de Rodo sobre el portal: prominencia, estética, lector interno

Rodo probó el portal recién cerrado y pidió 4 cosas: que no quede escondido en el menú de herramientas (es "más una función principal"), que el filtro de zona no sirve porque nadie conoce el número de zona, rediseñar la estética de los ítems/íconos, y poder leer la nota sin salir de la pestaña de MotoSafe.

- **Prominencia**: sacado de `herramientas-menu` (quedaba a dos clics, escondido). Nuevo botón circular de 44px en la fila de íconos del topbar, junto a Capas -- mismo tratamiento visual, mismo nivel de jerarquía, visible de entrada sin abrir nada.
- **Estética rediseñada**: las tarjetas pasaron de borde plano a elevación real (`box-shadow`, `translateY` en hover) -- Rodo lo pidió explícito ("no quedan muy bien"). Cada categoría (robo/choque/moto/inseguro/pavimento-corte/iluminación) tiene ahora una insignia de ícono a color (fondo tintado al 15% + color sólido), mismo criterio que ya usan los badges de `ruta-resumen` -- no una paleta nueva, los mismos 6 colores de riesgo de siempre. Antes todos los ítems tenían el mismo ícono gris plano sin jerarquía visual entre una urgencia y un aviso menor.
- **Lector interno**: el botón de "ver nota" pasó de un `<a target=_blank>` a un modal propio (`.lector-nota`) con un `<iframe>` que carga la nota ADENTRO de la pestaña de MotoSafe. Limitación real, verificada en vivo y no oculta: varios diarios (Infobae confirmado con una prueba real) bloquean que su sitio se muestre en un iframe ajeno (`X-Frame-Options`, una protección contra clickjacking que no se puede destrabar desde este lado) -- el iframe queda en blanco en esos casos. Por eso el modal SIEMPRE deja a mano, visible, "Abrir en pestaña nueva" + un aviso corto explicando por qué puede no cargar, en vez de prometer un lector que funciona para cualquier sitio.
- **Pendiente, no resuelto todavía (filtro de zona)**: investigado antes de tocar nada. Ni `reportes_prensa` ni `reportes_colaborativos` tienen un campo de barrio/zona real -- el filtro actual usa la zona de `ZONAS_RIESGO` más cercana, que son clusters numerados del modelo ("Zona 106"), sin ningún significado para quien no conoce los datos. Encontrado además: el proyecto ya tiene una decisión documentada (DEC-011/A18) de NO usar Nominatim para nada parecido a un uso en volumen/bucle -- reverse-geocodear 150-300 puntos distintos para sacarles un barrio real violaría esa misma política. La alternativa real (TomTom, que el proyecto ya paga para `/lugares`) tiene costo/cupo por llamada, así que escalarlo a todo el feed es una decisión de producto, no solo técnica -- se lo planteo a Rodo en el chat en vez de decidirlo solo.
- Verificado: eslint, vitest (81/81), build -- los tres en verde. Revisado en navegador y en 375px: botón del topbar no rompe el layout, tarjetas con el nuevo estilo, lector interno probado con un caso real que SÍ bloquea (Infobae) confirmando que el aviso y el link de respaldo aparecen correctamente.

## 2026-10-13 — SES-115 (cont.) — Filtro de barrio real (TomTom), lector como panel flotante y lector desde el mapa

Rodo pidió seguir con TomTom + caché agresiva para el filtro de barrio, además de que el lector funcione también desde los marcadores de prensa del mapa (no solo desde el portal) y que NO tape toda la app -- un panel parcial, no pantalla completa.

- **Backend**: nuevo endpoint `/lugares/reversa?lat=&lng=` (TomTom Reverse Geocoding, misma key que `/lugares`). Caché de 30 días (no 10 minutos como `/lugares`: un barrio no cambia) con clave redondeada a ~100 m, para que decenas de notas de la misma cuadra pidan TomTom una sola vez. A propósito NO usa Nominatim para esto -- el proyecto ya tiene tomada la decisión (DEC-011/A18) de no usarlo para nada en volumen, y reverse-geocodear 150-300 puntos distintos es justo ese caso.
- **Frontend**: `utils/barrio.js` -- cola secuencial compartida a nivel de módulo (sobrevive a cerrar/abrir el portal) con una pausa entre pedidos, para no mandar una ráfaga de decenas de pedidos simultáneos ni agotar la cache del navegador innecesariamente. `ActividadPortal` resuelve el barrio solo de los ítems que ya pasaron el filtro de categoría/fecha (no el feed entero de una), y arma el selector de barrio con los nombres reales que van llegando -- "Palermo", "La Plata", "San Martín", "González Catán", etc, en vez de "Zona 106".
- **Bug real encontrado y corregido durante la implementación**: el filtro de barrio no aparecía nunca, ningún ítem mostraba su barrio, aunque el backend respondía bien (confirmado con `curl` y con la pestaña de Network del navegador, ambos OK). La causa: el efecto que pide los barrios usaba una bandera `vivo` para no actualizar estado después de desmontarse -- pero en desarrollo, React (StrictMode) monta/desmonta/vuelve a montar cada efecto una vez de más para detectar código no idempotente. El cleanup del primer montaje (sintético) ponía `vivo = false` ANTES de que la respuesta de red llegara, así que la ÚNICA ejecución real del efecto quedaba con sus respuestas descartadas, y el segundo montaje no pedía nada nuevo porque el ref de deduplicación ya tenía todas las claves marcadas como "pedidas". Se sacó la bandera (el dedupe real, por ref, ya alcanza; `setState` después de un desmonte real es inofensivo en React 18).
- **Segundo problema real, de volumen**: con el bug de arriba corregido, la cola sí mandaba los pedidos, pero el límite original del endpoint (60/min, copiado del de `/lugares`) no alcanza para un burst de 100+ puntos distintos la primera vez que se abre el portal -- varios devolvían 429. Subido a 300/min para este endpoint específico (documentado en el propio código por qué es distinto del de `/lugares`), y la pausa del cliente ajustada a 300ms entre pedidos para quedar cómodo debajo de ese techo.
- **Lector como panel flotante, no pantalla completa**: `.lector-nota` dejó de vivir adentro de `.portal-actividad` (ahí heredaba su `inset:0`) y pasó a ser un panel de nivel de `App.jsx`, anclado abajo tipo "hoja" (bottom-sheet), con un scrim atenuado detrás -- se ve y se nota el mapa (o el portal) alrededor, no se pierde el contexto. Esto también fue lo que permitió abrirlo desde un segundo lugar.
- **Lector también desde los marcadores de prensa del mapa**: el botón "Ver noticia completa" del popup nativo de MapaMotoSafe (que antes hacía `window.open`) ahora llama al mismo lector (prop `onAbrirLector`, mismo patrón de refs que ya usa el componente para `onClickMapa`/`onClickZona`). Un solo lector, dos puntos de entrada reales.
- Se sacó `zonaMasCercana` de `utils/geoRiesgo.js` (quedó sin uso, reemplazada por el barrio real) -- no se dejó como código muerto.
- Verificado en el navegador con medición real, no solo mirando: selector de barrio poblándose con nombres reales tras abrir el portal, filtro por "Palermo" reduciendo de 151 a 3 resultados correctos, lector abierto desde un marcador de prensa del mapa con el scrim y el panel parcial visibles, mismo caso revisado en 375px. Se usó `curl` directo contra el backend para aislar que la causa del bug era el frontend, no el endpoint nuevo.
- Verificado: pytest del backend (119 pasados, 1 solo falló por el propio bypass de auth que esta sesión agrega para probar sin login -- confirmado sacándolo temporalmente y repitiendo ese test solo, pasó limpio), eslint, vitest (81/81), build -- todo en verde.

## 2026-10-13 — SES-115 (cont.) — Alto regulable del lector de notas

Rodo probó el lector flotante y pidió una sola cosa más: que el alto se pueda regular arrastrando, para ver la nota más grande cuando hace falta.

- Agarre (`.lector-nota-agarre`) arriba del panel, mismo patrón visual que un bottom-sheet nativo (barrita centrada). Arrastrándolo cambia `alturaLector` (estado en `%` de alto de pantalla, no en píxeles -- así no queda raro si el celular rota), clampeado entre 28vh y 94vh tanto en JS como en el CSS (min-height/max-height como respaldo).
- `touch-action: none` en el agarre: sin esto, arrastrar en celular scrollea la página de atrás en vez de cambiar el alto del panel.
- Accesible por teclado, no solo con el mouse/dedo: el agarre es un `role="slider"` enfocable, con flecha arriba/abajo moviendo el alto de a 5vh -- no se asumió que todos los visitantes van a poder arrastrar con precisión.
- Verificado con medición real (no solo mirando): arrastre simulado hacia arriba/abajo confirmando el cambio real de `height` computado, clamp en los dos extremos (28vh/94vh) con un arrastre exagerado en cada sentido, control por teclado confirmado con el alto bajando un paso real por cada flecha, y revisado en 375px (el agarre se ve y se toca igual de bien).
- Verificado: eslint, vitest (81/81), build -- los tres en verde.

## 2026-10-13 — SES-115 (cont.) — Nueva vista de fondo: hexágonos de cobertura (y nuevo default)

Rodo mandó capturas de dos apps (un mapa de delitos con zonas poligonales, una app de viajes tipo Cabify con hexágonos de cobertura alrededor del auto) preguntando si convenía algo así en vez del mapa de calor actual. Coincidí: un hexágono de borde nítido comunica "dónde termina la zona de riesgo" mucho mejor que un heatmap difuminado. Pidió sumarlo como opción nueva y, si quedaba bien, que fuera la vista principal de la app.

- Nuevo util `utils/hexBin.js`: agrupa zonas en una grilla hexagonal "pointy-top" (coordenadas axiales, la matemática estándar de redblobgames.com/grids/hexagons) operando en metros locales, no en grados -- un grado de longitud no mide lo mismo que uno de latitud, así que hexágonos "regulares" en grados saldrían alargados. Sin sumar una librería nueva (turf, h3-js): es la misma matemática ya resuelta en cualquier lado, ~90 líneas, no justificaba una dependencia. 5 tests nuevos (`hexBin.test.js`) cubriendo agrupamiento por cercanía, separación por lejanía, que el nivel de una celda sea el más alto presente (no un promedio -- un hexágono con una zona crítica entre varias bajas sigue siendo un hexágono que conviene mirar) y que cada polígono cierre bien (7 puntos, el primero y el último iguales).
- Nueva opción "Hexágonos de cobertura" en el panel de Capas (`OPCIONES_CAPA_MAPA`), nueva capa en `MapaMotoSafe.jsx` (`hexagonos-cobertura-layer` + una línea de borde aparte, porque `fill-outline-color` de MapLibre siempre dibuja 1px fijo sin importar el zoom -- a zoom alto quedaba invisible contra el relleno). Radio de 650m centro-a-vértice elegido a ojo, mirando en pantalla, para que el hexágono se sienta "un barrio chico", ni toda CABA en 3 celdas ni 400 celdas diminutas.
- **Pasó a ser el valor por defecto** (`cargarDeLocalStorage(CLAVE_CAPA_MAPA, 'hexagonos')`, antes `'clusters'`): verificado en vivo con `localStorage` limpio (simulando una visita nueva) que carga hexágonos de entrada, en los dos temas. Solo afecta a quien nunca tocó el panel de Capas -- quien ya eligió otra vista la conserva (está en localStorage).
- Encontrado y corregido de paso: el ícono de "Capas" del topbar se resalta con un punto cuando algo distinto del default está prendido (`capas-con-cambios`), pero esa comparación tenía `'clusters'` hardcodeado como "el default" -- con hexágonos como nuevo default, se habría prendido el aviso de "tenés algo cambiado" en el estado de fábrica, exactamente al revés de lo que significa esa señal. Corregido a comparar contra `'hexagonos'`.
- Verificado en el navegador, en ambos temas y con el filtro de nivel de riesgo (clickear "Crítico" en la leyenda) para confirmar que la capa se recalcula sin romperse al cambiar qué zonas entran.
- Verificado: eslint, vitest (86/86, suma los 5 nuevos de hexBin), build -- los tres en verde.

## 2026-10-13 -- SES-115: limpieza de fin de sesión y repaso de regresión

- Sacada de `backend/.env` la línea `AUTH_HABILITADO=false` que había quedado puesta desde el arranque de esta sesión larga para poder probar sin loguearse en cada reload. El proceso de backend que seguía corriendo (uvicorn --reload) no la recarga sola porque `--reload` vigila archivos `.py`, no `.env` -- un reinicio del proceso alcanza para que vuelva a pedir login real.
- Esa misma línea era la causa de un test que fallaba (`test_con_login_activado_por_defecto_faltan_variables_y_no_arranca`), ya diagnosticado y anotado en la entrada anterior de hexágonos: confirmado de nuevo acá, sin la línea el test pasa limpio.
- Repaso de regresión completo de todo lo nuevo de SES-115 junto, en el navegador, para confirmar que no se pisa entre sí:
  - Destino rápido tocando un punto vacío del mapa (incluso sobre una celda de hexágono, que es la vista de fondo default ahora) -- abre la tarjeta "Punto en el mapa" como se espera, no choca con la capa de hexágonos por estar esta sin listener de click propio.
  - Portal de Actividad: abre, filtra por barrio real (ej. "San Isidro" bajó 146 resultados a 3), barrios resueltos por TomTom sin pedir de más (sin 429 en `/lugares/reversa`, todas las llamadas 200 OK).
  - Lector interno de notas: probado desde el popup de prensa del mapa y desde un ítem del portal, los dos abren el mismo panel flotante con el mapa atenuado detrás. Alto regulable (arrastrar el agarre) sigue funcionando.
  - CSP de La Nación sigue bloqueando el iframe (error esperado en consola, ya contemplado con el link "Abrir en pestaña nueva" -- no es un bug, es la limitación que motivó ese botón).
  - Cambiar la vista de fondo entre Hexágonos / Corredores / etc. desde el panel de Capas, ida y vuelta, sin romper nada.
- Verificado: eslint, vitest (86/86), build del frontend, y pytest del backend (120 passed, 11 skipped) -- los cuatro en verde.
- Pendiente de higiene, no bloqueante: `backend/.venv_test/` sigue sin trackear (virtualenv descartable de esta sesión, excluido a propósito de git).

## 2026-10-13 -- SES-115: hexágonos clickeables, popup con desglose por nivel

- Hasta acá los hexágonos de cobertura eran puramente decorativos (a diferencia de clusters y corredores, que sí abren un detalle al tocarlos) -- pedido propio como mejora, propuesto después de cerrar la tanda anterior y aprobado por Rodo ("avanza con TODO").
- `hexBinZonas` (utils/hexBin.js) ahora además del total y el nivel máximo expone `cantidad_<nivel>` por cada nivel de ORDEN_NIVELES como propiedades planas del feature (MapLibre necesita propiedades planas, no objetos anidados, para leerlas en un popup). Test nuevo que verifica el desglose (87/87 en vitest).
- `MapaMotoSafe.jsx`: mismo patrón que ya usa `corredores-layer` (Popup de maplibre-gl, cursor pointer al pasar por encima, cleanup en el return del effect) agregado a `hexagonos-cobertura-layer`. El popup muestra el nivel máximo de la celda, el total de siniestros, y una fila por nivel presente con un punto de color (mismo color que la leyenda del sidebar) en vez de repetir la etiqueta en texto.
- Sumado `hexagonos-cobertura-layer` a la lista de capas excluidas del click genérico de "destino rápido" (antes solo `corredores-layer`/`rutas-layer`) -- como ahora el hexágono tiene su propio click, sin esto cada toque sobre un hexágono (que es casi toda la superficie del mapa, al ser la vista de fondo default) iba a abrir a la vez el popup Y la tarjeta de "Punto en el mapa", dos cosas compitiendo por el mismo toque.
- CSS nuevo: `.popup-hex-desglose` / `.popup-hex-punto`, mismo lenguaje visual que el resto de los popups (`.popup-content`, `.popup-nivel`).
- Verificado en el navegador, en los dos temas: popup abre con los datos correctos, destino rápido ya no se dispara sobre un hexágono pero sigue andando en el resto del mapa vacío.
- Verificado: eslint, vitest (87/87), build -- los tres en verde.

## 2026-10-13 -- SES-115: hexágonos adaptativos al zoom + opacidad por densidad (investigación)

Pedido explícito de Rodo de investigar a fondo la técnica de visualización hexagonal (la misma familia que Uber/Cabify y los mapas de riesgo de referencia que mandó) para sacarle el máximo provecho, no solo implementar lo mínimo.

**Investigado:**
- H3 (la grilla hexagonal de Uber): tiene 16 "resoluciones", cada una ~7x más chica que la anterior, y la práctica estándar es atar la resolución al zoom del mapa -- lejos, celdas grandes (se lee el patrón general); cerca, celdas chicas (separa cuadra por cuadra). Fuentes: [Guide to Uber's H3](https://www.analyticsvidhya.com/blog/2025/03/ubers-h3-for-spatial-indexing/), [H3: Uber's Hexagonal Hierarchical Spatial Index](https://www.uber.com/en-NZ/blog/h3/), [What is H3](https://felt.com/blog/what-is-h3), [Aggregate Map Data with H3](https://honeycombmaps.com/product/features/h3-aggregation).
- Clasificación y color en choropleths/mapas de densidad: 4-5 clases discretas es el punto dulce (más y el ojo no distingue), usar la clasificación que mejor separe los valores reales en vez de intervalos iguales a ciegas, y mostrar el tamaño de celda/resolución en la UI para que quien mira el mapa entienda qué está viendo. Fuentes: [ONS service manual -- choropleth maps](https://service-manual.ons.gov.uk/data-visualisation/chart-types/choropleth-maps), [Datawrapper -- interpolation for color scales](https://www.datawrapper.de/blog/interpolation-for-color-scales-and-maps), [Atlas -- color palettes for choropleths](https://atlas.co/blog/get-better-at-using-color-palettes-with-choropleth-maps/).

**Implementado a partir de eso (sin sumar H3 ni ninguna librería nueva -- misma matemática a mano de `hexBin.js`, solo extendida):**
- `radioHexagonoPorZoom(zoom)` en `utils/hexBin.js`: 3 escalones (1300m alejado / 650m como antes, el rango de zoom default / 320m acercado a nivel barrio-calle), no los 16 de H3 real -- no hace falta más granularidad que "lejos / como estaba / cerca", y cada escalón de más es recalcular toda la grilla al cruzar el umbral. `MapaMotoSafe.jsx` ahora trackea el zoom en un estado propio (`radioHex`), actualizado solo en `zoomend` (no en cada frame del gesto de pinch/scroll) para no recomputar la grilla de más.
- Desglose por nivel (`cantidad_<nivel>`, de la tanda anterior) se mantiene igual, solo cambia el radio de agrupación.
- Opacidad del relleno de cada hexágono ahora también escala con la cantidad de siniestros de esa celda (antes era un número fijo, 0.5): dos hexágonos "alto" ya no se ven idénticos si uno tiene 3 siniestros y el otro 80. El color sigue siendo puramente categórico (nivel), la opacidad agrega una lectura continua de "peso real" sin inventar una escala de color nueva que compita con la de NIVELES. El tope de la escala se saca del percentil 90 de las celdas visibles (no del máximo): con el máximo, una sola celda extrema aplana la opacidad de todas las demás.
- Popup del hexágono ahora dice también el radio de la celda ("Celda de ~XXXm de radio") -- aplicando directo la recomendación de "mostrar la resolución en la UI".
- Tests nuevos para `radioHexagonoPorZoom` (los 3 escalones y sus bordes). 90/90 en vitest.
- Verificado en el navegador: alejando el zoom las celdas crecen notablemente (menos ruido visual, se lee el patrón de la ciudad entera), acercando bajan a ~320m (separa cuadra por cuadra) con el popup reflejando el radio correcto en cada escalón. Un warning de React sobre el array de dependencias del efecto apareció una sola vez durante la edición en vivo (justo después de varios "hot updated" de Vite) y no volvió a aparecer en los dos reloads completos posteriores -- confirmado que fue ruido transitorio de Fast Refresh, no un bug real.
- Verificado: eslint, vitest (90/90), build -- los tres en verde.

## 2026-10-13 -- SES-115: rediseño de popups del mapa (información y jerarquía)

Pedido de Rodo: "mejorar el diseño de los popups, la información, el entendimiento" -- un repaso parejo de TODOS los popups del mapa (corredores, inseguridad, reportes comunitarios, hexágonos), no solo uno.

- **Chips de estadísticas** (`.popup-stats`/`.popup-stat`): el popup de corredores decía "12 siniestros históricos · 2 mortales · 1 graves" como una oración con separadores -- había que leerla entera para encontrar el dato grave. Ahora son tres números uno al lado del otro, cada uno con su etiqueta debajo (mismo patrón visual que un stat de dashboard). Mortales se resalta en rojo (`--rojo-text`) SOLO cuando es mayor a 0 -- al principio lo puse siempre rojo y un "0 mortales" en rojo se veía como una alerta falsa, corregido para que el color solo aparezca cuando de verdad hay algo que remarcar.
- **Metadato secundario consistente** (`.popup-meta`): fecha, comuna, radio de celda, vencimiento -- antes cada popup tenía su propio `<span>` suelto sin estilo (heredaba el tamaño/color del texto principal, sin jerarquía). Una sola clase para todos.
- **Bug real encontrado y corregido**: el popup de inseguridad mostraba "Comuna 10.0" (con el punto decimal, nunca "Comuna 10"). La causa: `comuna_moda` llega del backend como STRING con decimal ("10.0", resto de cómo psycopg2/Postgres serializa esa columna), no como número -- un primer intento de arreglo con `Number.isFinite(h.comuna_moda)` no alcanzaba porque esa función nunca es true para un string así sea numérico. Arreglado coercionando con `Number(...)` antes de chequear. Fix puramente de presentación en el frontend, no se tocó el dato en el backend.
- **Reportes comunitarios reordenados**: antes el eyebrow (`popup-nivel`) apretaba tres cosas con "·" (quién reportó + antigüedad + vencimiento) y recién abajo decía QUÉ era -- al revés de lo que alguien busca primero al tocar un reporte ("¿qué está pasando acá?"). Ahora la categoría es el eyebrow coloreado (coincide con el color del punto en el mapa), "quién reportó" pasa a título, y el "cuándo" queda en una línea `.popup-meta` aparte.
- Ancho de popup unificado: `maxWidth` explícito (280px) en corredores/inseguridad/hexágonos -- antes usaban el default de MapLibre (240px), quedaba justo para los chips nuevos.
- `line-height: 1.3` agregado a los títulos (`.popup-content strong`), antes sin eso un título de 2-3 líneas (tramo de corredor largo, titular de noticia) quedaba con las líneas pegadas.
- Verificado en el navegador, en los dos temas, con los 4 popups (corredores, inseguridad, reportes, hexágonos) -- para clickear un corredor real con precisión usé `map.queryRenderedFeatures` + `map.project` desde la consola en vez de adivinar coordenadas de pantalla (la data real de corredores no siempre es visualmente obvia a simple vista, mucho "bajo" apenas se nota contra el mapa base).
- Verificado: eslint, vitest (90/90), build -- los tres en verde.

## 2026-10-13 -- SES-115: hexágonos como visión central (filtro Todo/Siniestros/Inseguridad + noticias)

Pedido de Rodo tras la tanda de rediseño de popups: "tal vez podría ser la de hexágonos la visión central, pero poder filtrar por TODO/ACCIDENTES/INSEGURIDAD, que pueda mostrar más info, esté más estético, que tenga la influencia de las noticias". Acordado antes de implementar: en vez de un único "score de riesgo" fusionando siniestros + delitos + noticias con pesos inventados (poco explicable), vistas filtrables sobre los mismos datos ya confiables, honestas sobre de dónde sale cada número.

- **Filtro de fuente** (`CLAVE_FILTRO_HEXAGONO`/`OPCIONES_FILTRO_HEXAGONO` en constants.js): chips "Todo / Siniestros / Inseguridad" dentro de la leyenda de "Nivel de riesgo" (solo visibles con `capaMapa==='hexagonos'`), reutilizando el mismo componente de chips que ya tiene el portal de Actividad (`.portal-actividad-filtros-fila`). Default `'todo'` -- mismo criterio que el filtro de categoría del portal (arranca mostrando todo, se achica desde ahí).
  - 'Siniestros': el hexágono de siempre (zonasFiltradas, modelo en vivo).
  - 'Inseguridad': delitos históricos GCBA (`inseguridadFiltrada`, la misma data que ya usa la capa de puntos aparte -- esa data se pide siempre, sin importar si esa capa está prendida, así que el filtro funciona sin depender de otro toggle) con paleta propia (violeta/magenta, `NIVELES_INSEGURIDAD_COLOR`) para que se note de un vistazo que es otra fuente.
  - 'Todo': las dos juntas en la misma celda, con la paleta neutra de siempre (NIVELES).
- **hexBinZonas extendido** (utils/hexBin.js) para no perder trazabilidad al combinar fuentes: cada zona lleva un `fuente` opcional ('siniestros'/'inseguridad'), y el resultado expone `fuente_siniestros`/`fuente_inseguridad` además del desglose por nivel que ya existía -- el popup en modo 'Todo' puede decir "18 siniestros · 7 delitos" en vez de un número mezclado sin aclarar de dónde sale.
- **Influencia de las noticias**: nuevo parámetro `noticias` en `hexBinZonas` -- los puntos de prensa (mismos `reportesPrensa` que ya usa el mapa) se suman a `celda.noticias` SOLO si caen dentro de una celda que ya tiene datos de riesgo reales; una noticia sola, lejos de cualquier zona/delito, no crea un hexágono nuevo (es contexto sobre el riesgo que ya se muestra, no un motivo para dibujar algo vacío). Las celdas con noticias muestran un punto blanco con borde oscuro arriba a la derecha del hexágono (capa `circle` aparte), y el popup suma una línea "▤ N noticia(s) reciente(s) en esta zona".
- **Bug de fuentes encontrado en el camino**: la primera versión del punto de noticias usaba una capa `symbol` con el glyph "▤" (el mismo que ya usan los marcadores de prensa en HTML/CSS) -- en consola apareció `Unable to load glyph range... 9472-9727, Rendering codepoint locally instead. Error 404` contra `tiles.openfreemap.org/fonts/...`: ese rango Unicode no está cacheado en el servidor de fuentes del estilo. Cambiado a una capa `circle` (no depende de ninguna fuente/glyph, se ve siempre igual) -- confirmado el mecanismo de todas formas agrandando el punto a propósito desde la consola del navegador antes de aplicar el tamaño final.
- Verificado en el navegador, en los dos temas: los tres filtros cambian la grilla y la paleta correctamente, el popup en 'Todo' muestra el desglose por fuente y la línea de noticias, y el punto de noticias se ve en las celdas correctas (confirmado contando features reales vía `map.querySourceFeatures`/`queryRenderedFeatures` desde la consola, no solo a ojo).
- Verificado: eslint, vitest (93/93, +4 tests nuevos de hexBin: fuente, noticias dentro/fuera de celda real), build -- los tres en verde.

## 2026-10-13 -- SES-115: corrección de feedback real del celular (hexágonos "Todo")

Rodo probó en el celular real la tanda anterior (filtro Todo/Siniestros/Inseguridad) y mandó capturas: "queda raro el filtro ahí... no sé por qué hay puntos por el mapa... me gustaría una mejor distinción de colores ya que con verde/amarillo/rojo es fácil pero con el resto no tanto". Tres problemas reales, los tres corregidos:

1. **El tercer chip ("Inseguridad") era invisible en celular**: la leyenda es angosta y el filtro heredaba `overflow-x: auto` del portal de Actividad (pensado para una fila ancha, no esta tarjeta angosta) -- sin ninguna pista de que había un tercer chip con scroll, quedaba cortado. Confirmado con las capturas: solo se veían "Todo" y "Sinie...". Arreglado con `flex-wrap: wrap` (los que no entran bajan de línea en vez de esconderse) + label más corta ("Delitos" en vez de "Inseguridad", el id interno no cambió) + la leyenda un poco más ancha cuando tiene este filtro (`.legend:has(.legend-filtro-hexagono)`).
2. **Paleta violeta/magenta para "Inseguridad"/"Todo" sacada**: la idea original (violeta para marcar "otra fuente de datos") salió al revés probada en la práctica -- un semáforo verde/amarillo/naranja/rojo se lee sin pensarlo, cualquier otra escala hay que aprenderla. Los tres filtros usan ahora la misma paleta de NIVELES siempre; qué filtro está activo ya lo dice el chip prendido, no hace falta que el mapa lo repita con otro lenguaje de color.
3. **Los puntos blancos de "noticias" por todo el mapa sacados**: era una capa ambiente (ver tanda anterior) que se mostraba en cada celda con al menos una noticia, sin ningún lugar en pantalla que explicara qué significaban -- confirmado en las capturas de Rodo, docenas de puntos dispersos sin contexto. El dato no se perdió: `celda.noticias` sigue viniendo en el hexágono y el popup al tocarlo sigue diciendo "▤ N noticias recientes en esta zona" -- solo se sacó la marca ambiente que generaba más preguntas que respuestas.

Verificado en el navegador con viewport de celular real (375×812): los tres chips entran en dos filas prolijas, sin overflow ni scroll oculto. Verificado también que sacar la capa de noticias no rompió el dato (`celda.noticias` sigue en properties, popup sigue mostrando la línea).
Verificado: eslint, vitest (93/93, sin cambios de lógica que ameriten tests nuevos -- esto fue UI/paleta, no matemática de hexBin), build -- los tres en verde.

## 2026-10-13 -- SES-115: unificación de bordes redondeados en paneles grandes

Rodo, sobre el lector de notas: "me gustó mucho el diseño... bordes curveados, el desenfoque, la fuente, espacios, bordes redondeados... TODO está muy estético y lo quiero para TODA LA APP". Antes de salir a tocar CSS a ciegas en 10+ componentes, se acordó el alcance con una pregunta: paneles grandes nomás (leyenda, panel de capas, portal de Actividad/estadísticas, formulario de ruta, resumen de zona, resumen de ruta, hoja de reportar, tarjeta de lugar) -- los popups chicos del mapa y los botones/chips quedan como estaban, son otra escala visual.

- **Causa real encontrada**: `.lector-nota` usa `border-radius: var(--r-lg)` (16px) + `box-shadow: var(--shadow-float-hover)`, mientras que el resto de los paneles grandes tenían números sueltos sin tokenizar -- `border-radius: 10px/12px/14px` repetidos a mano en `.legend`, `.capas-panel`, `.actividad-panel`/`.stats-panel`, `.ruta-form`, `.detalle-panel`, `.ruta-resumen`, `.report-sheet`, `.lugar-card`. Nada estaba "mal" visualmente (ya usaban los mismos --sp-*/--fs-*/fuentes), pero el radio más chico y menos consistente es justo lo que hacía sentir al lector "más pulido" en comparación.
- **Fix**: los 8 paneles de arriba pasan todos a `border-radius: var(--r-lg)`, igual que `.onboarding-card` (que ya lo tenía bien desde antes) y `.lector-nota`. Un solo comentario centralizado en `.legend` documenta el criterio y por qué los popups/botones quedan afuera a propósito.
- Sin tocar sombras, blur ni spacing -- esos ya eran consistentes entre paneles (todos comparten --shadow-float/--shadow-float-hover y --surface-float-blur), el único punto real de divergencia era el radio.
- Verificado en el navegador, en los dos temas: panel de capas, formulario de ruta y hoja de "¿Qué estás viendo?" con el nuevo radio, sin romper ningún layout.
- Verificado: eslint, vitest (93/93, sin tests nuevos -- cambio puramente de CSS, sin lógica), build -- los tres en verde.

Pendiente, explicado pero no corregido (consultado con Rodo, no es prioridad ahora): en el filtro de hexágonos, "Todo" y "Delitos" se ven parecidos en la mayoría de las zonas porque el dataset de delitos (GCBA) es más denso que el de siniestros ahí -- al tomar el nivel más alto entre las dos fuentes, delitos gana casi siempre. No es un bug de color, es la data real; el popup ya desglosa cuánto es de cada fuente.

## 2026-10-18 -- SES-116: cierre de A04 (costo relativo por clase) y corrección de números desactualizados en Cap4/Cap7

Rodo pidió seguir con A04 ("dale analiza eso y todo lo que consideres necesario"). Al revisar el artefacto real (`columnas_modelo.pkl`, 53 columnas) se confirmó que el modelo en producción desde el 05/10/2026 (sin edad, con sexo e índice) ya no es el que describen el Capítulo 4 (Tabla 4.1, 55 columnas) ni el borrador del Capítulo 7 entregado antes de esa fecha -- los dos seguían citando la variante vieja (con edad).

- **Números corregidos**: se corrió el split aleatorio interno (80/20, estratificado) de la variante sin edad para tener el par honesto inflado/real del modelo que corre hoy: F1 macro 0,368 (split) vs. 0,3045 (evaluación temporal 2024, real), GRAVE recall/precisión 0,604/0,098 y 0,562/0,081, MORTAL 0,464/0,105 y 0,535/0,074. Reemplazan los números de la variante con edad (0,378/0,262) que estaban citados en ambos capítulos.
- **A04 cerrado**: se midió la sensibilidad del corte de percentil (p25/p75/p95) sobre el score `2*P(MORTAL)+P(GRAVE)`, usando 2023 como población de referencia y 2024 como evaluación real. El recall de MORTAL se mantiene casi plano entre p50 y p75 (83,7% a 74,4%); el de GRAVE cae de forma gradual en todo el rango (74,8% en p50 a 11,9% en p95). El corte vigente (p75/p95) queda justificado con números: está donde MORTAL recién empieza a perder recall real, y bajarlo exigiría marcar como alto riesgo hasta el 60% de las combinaciones zona-hora sin ganar casi nada en MORTAL. Evidencia en `docs/evidencias/2026-10-18/A04-decision-costo-por-clase/`. A04 pasa de "Validado parcialmente" a Validado en BACKLOG.md.
- **Corrección de capítulos ya entregados (excepción al principio de versionado, pedida directamente por Rodo, no por la cátedra)**: el Capítulo 4 ya fue entregado y evaluado, así que no se reescribió la Tabla 4.1 ni la matriz de confusión original; se agregaron dos notas de actualización fechadas (2026-10-05 y 2026-10-18) inmediatamente después de los pasajes afectados, con los números corregidos y referencia a la evidencia nueva. El contenido original entregado queda intacto y visible; el lector llega a la cifra vigente sin que se borre el historial de lo evaluado. Se documenta acá como la excepción explícita que prevé el principio de versionado al inicio de BACKLOG.md. El Capítulo 7, al no estar entregado todavía, sí se corrigió directo (Tabla 7.1 y los párrafos de precisión/recall, ablaciones y calibración), más dos párrafos nuevos sobre la calibración isotónica y la sensibilidad del corte de percentil, que ya tenían evidencia real lista pero no estaban en el borrador original.
- Verificado: docx de ambos capítulos revalidado contra el esquema (`validate.py`), renderizado a PDF y revisado página por página donde hubo cambios.

## 2026-10-18 -- SES-116 (cont.): fijado el intérprete del reloader de `run_dev.py` (A22)

Pendiente desde SES-105: el backend de desarrollo (`uvicorn --reload`) arranca el proceso que de verdad sirve pedidos como un hijo nuevo vía `multiprocessing` (contexto `spawn`), y ese hijo podía terminar corriendo con el Python de sistema en vez de `venv312`, sin ningún aviso -- mismo puerto, misma pinta, pero sin las versiones fijadas por `requirements.lock`.

- `run_dev.py` ahora llama `multiprocessing.set_executable(sys.executable)` antes de `uvicorn.run(reload=True)`, así que el hijo usa explícitamente el mismo intérprete que ya está corriendo este proceso en vez de dejar que Windows lo resuelva de nuevo.
- Se agregó `_verificar_interprete_venv`: compara `sys.executable` contra `venv312/Scripts/python.exe` (al lado del script) antes de arrancar, y corta con un mensaje claro si no coinciden -- cubre el caso real de uso indebido (una terminal o IDE que no pasó por `_iniciar_backend.bat`). Si `venv312` todavía no existe (por ejemplo, un entorno que no lo usa), solo avisa por stderr y sigue, para no romper otros flujos.
- 4 pruebas nuevas en `tests/test_run_dev.py` (interprete correcto, interprete equivocado corta con `venv312` en el mensaje, sin `venv312` solo avisa, fallback a `bin/python` fuera de Windows). Verificado: 124/124 de la suite completa de backend en verde (incluye las 4 nuevas).
- A22 queda sin este pendiente; sigue abierta solo la primera corrida del CI confirmada en GitHub (bloqueada en `gh auth login`, una acción que le corresponde a Rodo).

## 2026-10-18 -- SES-116 (cont.): D02, estabilidad del F1 por año y por comuna

Pedido de Rodo: "quiero realmente mejorar y pulir lo que ya hay y finalizar pendientes". D02 era de los pocos ítems "en curso" genuinamente autocontenidos (no depende de red ni de OSRM, que resultó no estar disponible desde ninguno de los dos entornos de esta sesión -- ver nota en A06/D03/D04 más abajo).

- Se extendió `evaluar_modelo_academico.py` con desglose de F1 por comuna (`metricas_por_comuna`, con soporte por clase al lado -- mismo criterio que ya tenía `metricas_por_edad_desconocida`), sin tocar la salida existente.
- Se corrió sobre dos splits temporales independientes: el ya conocido 2023→2024 y uno nuevo, 2024→2025 (hay datos completos de 2025: 4.448 filas, año entero). Resultado real y no esperado: los intervalos de confianza bootstrap de los dos splits NO se superponen (F1 macro 0,2859 [0,2693;0,3046] contra 0,3689 [0,3504;0,3874]) -- el modelo no generaliza igual de un año a otro, y eso es una limitación real del protocolo de evaluación con un solo año de test que queda documentada, no resuelta (no hay causa identificada todavía).
- Por comuna: soporte de MORTAL entre 0 y 7 casos según comuna y año, insuficiente para sostener ninguna conclusión fuerte en ningún sentido. Ninguna comuna sale sistemáticamente mal en los dos splits.
- D02 pasa de "En curso" a "Validado parcialmente" en BACKLOG.md, con la evidencia en `docs/evidencias/2026-10-18/D02-estabilidad/`.

**Nota sobre A06/D03/D04 (rutas de referencia y sensibilidad del comparador)**: se intentó seguir con estos en la misma sesión. El bug de empates que menciona A06 ya estaba corregido y probado en código desde antes (`nivelRelativoEnLote`, con tests que cubren justamente el caso de empate) -- la frase del backlog describe un estado ya alcanzado, no un pendiente real; se deja así, corregible en una pasada de limpieza de texto si hace falta. Lo que sí queda abierto (plantilla de rutas en `docs/evidencias/2026-09-13/D03/rutas_referencia.csv`, vacía salvo encabezados) necesita rutas reales calculadas contra OSRM/TomTom en vivo. Se probó el acceso a `router.project-osrm.org` desde el entorno Linux de este Claude y desde el contenedor en la nube: los dos lo rechazan (sin red abierta a ese host). D03/D04 quedan sin avanzar esta sesión por esa razón, no por falta de tiempo; además D03 pide "casos revisados" con criterio independiente, que no debería recaer en quien mismo construyó el sistema que se está evaluando -- mejor que Rodo revise los casos reales una vez calculados.

## 2026-10-18 -- SES-116 (cont.): confianza por zona frente al reentrenamiento (A24)

Después de la discusión sobre qué tan fuerte puede ser la afirmación "esto es zona de riesgo" en la tesis, Rodo pidió explícitamente no quedarse en una advertencia mejor redactada: "agregá lo que falte, lo que sea, para que la herramienta PUEDA ASEGURAR". Esto es lo que se construyó en respuesta.

- Se confirmó primero que "entrenar con más datos" no es una palanca disponible: `reentrenar_modelo.py` ya entrena sobre el histórico completo (sin recorte por año), con `train_test_split` aleatorio.
- Se corrió un experimento preliminar (dos modelos sobre ventanas temporales distintas, train<2023 vs train<2024) que ya mostraba la dirección del hallazgo (acuerdo global 83,1%, 'crítico' el menos estable con 67,0%) pero no correspondía al proceso real de reentrenamiento de producción (que no recorta por año).
- Se corrigió el método: 10 `RandomForestClassifier` con los hiperparámetros exactos de producción, cada uno sobre una remuestra bootstrap del dataset completo (mismo universo que usa producción), evaluados sobre la grilla de 336 escenarios de `calibrar_umbrales_riesgo.py` aplicada a las 740 zonas reales. Resultado: acuerdo global entre los 10 modelos 84,9% (mediana 90,0%); por zona, mediana 83,8%, mínimo 52,6%. Agrupado por nivel: 'crítico' (78,9%) y 'alto' (78,5%) sensiblemente menos estables que 'bajo' (90,3%) y 'medio' (85,3%) -- la inestabilidad se concentra justo en los niveles que más importan para alertar.
- Se construyó `notebooks/calcular_confianza_zonas.py` (mismo patrón que `calibrar_umbrales_riesgo.py`: se corre una vez offline) y se agregó la columna `confianza_estabilidad` a `backend/hotspots_contexto.csv` para las 740 zonas reales.
- `backend/main.py`: `/hotspots` ahora expone `confianza_estabilidad` por hotspot (tomada del CSV, sin costo de cómputo por request), `None` cuando el hotspot no tiene fila propia (no se inventa un número). `nivel_riesgo` no se tocó: sigue siendo 100% el output de `modelo_final.pkl`. Se actualizó `_HUELLA_UMBRALES_CALIBRADOS` (cambiaron los bytes de `hotspots_contexto.csv` al agregar la columna); se verificó a mano que `UMBRALES_HOTSPOTS`/`UMBRALES_CORREDORES` no cambiaron de valor.
- 2 tests nuevos (`test_hotspots_con_contexto_propio_incluye_confianza_estabilidad_valida`, `test_hotspots_sin_contexto_propio_confianza_estabilidad_es_none`) y 1 test preexistente corregido (armaba su propio contexto falso sin la columna nueva). Suite completa: 126/126 en verde.
- Evidencia completa en `docs/evidencias/2026-10-18/confianza-zonas-bootstrap/`. A24 agregado a BACKLOG.md como Validado.
- Alcance explícito de lo que esto NO resuelve: no toca la inestabilidad entre años de D02 (es generalización temporal, no varianza de entrenamiento) ni la precisión estructuralmente baja en GRAVE (A04, desbalance de clases). Cuantifica una dimensión real y antes no medida de cuánto se puede confiar en el nivel que ve el usuario, zona por zona.

## 2026-10-18 -- SES-117: auditoría de diseño/animación en vivo, vista vertical de celular (SES-117)

Pedido de Rodo: mejorar el diseño/animación de la app para que "se note una aplicación profesional y no barata" (la lógica se deja fuera de alcance, confirmado explícitamente por él), con foco inmediato en la vista vertical de celular, que según su reporte "salta mucho".

- Se auditó en vivo contra el frontend corriendo sin HTTPS (`MOTOSAFE_SIN_HTTPS=1 npm run dev`), usando el navegador integrado emulando 390×844 (iPhone-size portrait).
- Hallazgo real, reproducido con capturas y medición de `getBoundingClientRect()`: en cada carga de página en celular, el control de atribución de MapLibre (`.maplibregl-ctrl-attrib`) arranca con el atributo `open` y la clase `maplibregl-compact-show` puestos por defecto por la propia librería al construir el control -- no es algo que decida más tarde. La corrección existente (SES-083/086, un `MutationObserver` + `esCelular()`) vivía adentro de `map.on('load')`, que dispara recién cuando terminan de cargar tiles y datos: en ese lapso (perceptible, sobre todo con mapa pesado o conexión lenta) se veía la franja de atribución expandida de punta a punta, tapando la leyenda y el stack de botones inferior, y después "saltaba" cerrada de golpe apenas cargaba. Esto es, con bastante confianza, lo que Rodo reportó como "salta mucho" en vertical.
- Fix en `frontend/src/components/MapaMotoSafe.jsx`: la lógica de corrección (buscar el nodo, `MutationObserver`, `corregirAtribucion()`) se movió de adentro de `map.on('load')` a justo después de `mapRef.current = map` -- el nodo del control ya existe apenas se construye el mapa (se agrega en el constructor), así que corregirlo ahí mismo evita el salto en vez de solo corregirlo después de que ya se vio. Verificado en vivo: recargando la página en 390×844, el control arranca directamente colapsado (`hasAttribute('open') === false` desde el primer render, confirmado por JS en la página), sin el flash previo.
- Se intentó además un ajuste menor (el ícono colapsado "i" de la atribución queda apenas detrás de la esquina del botón "Reportar", solapamiento de unos 15-20px). Se probó mover el margen del control vía CSS; la primera vez no tomó efecto por un empate de especificidad con el CSS propio de MapLibre (ganaba por orden de carga), y corregido eso con `!important` el ícono seguía coincidiendo con la esquina de "Reportar" (ambos anclados a la misma esquina inferior derecha). Se revirtió ese segundo cambio por no resolver el problema de fondo y no justificar más tiempo en un detalle menor y preexistente (no introducido por este cambio); queda anotado para una pasada futura si Rodo lo considera prioritario.
- Alcance: esto es un cambio de comportamiento visual/temporal (cuándo se corrige un estado del DOM), no de lógica de negocio ni de datos -- consistente con lo pedido ("la lógica ya está bien").
- Sigue pendiente recorrer el resto de pantallas en vertical (búsqueda, panel de ruta abierto, modo viaje/navegación, onboarding, reportar) con el mismo método de auditoría en vivo.

## 2026-10-19 -- SES-118: recorrido completo en vertical de celular, 3 bugs reales encontrados y corregidos

Pedido de Rodo: "quiero que recorras y pulas todo, por eso quiero que primero mapees de punta a punta". Se recorrió la app entera a 390×844 (vertical, tamaño iPhone real) contra el frontend corriendo en vivo: mapa default, búsqueda con resultados, tarjeta de lugar encontrado, formulario de ruta, opciones de ruta, modo viaje/navegación activo, menú de herramientas, panel de capas, panel de estadísticas, popup de detalle de zona, hoja de "Reportar", y la combinación con la capa de delitos (Inseguridad) encendida. Cada pantalla se midió con `getBoundingClientRect()` en vivo, no solo a ojo, para confirmar overlaps reales en vez de impresiones visuales (una de las sospechas iniciales -- el FAB de "Reportar" en modo viaje -- resultó ser un artefacto del recorte del zoom, no un bug real, y se descartó).

Tres problemas reales encontrados y corregidos, los tres de diseño/maquetado (no se tocó lógica de negocio):

1. **Topbar transparente dejaba ver marcadores del mapa por detrás.** `.topbar` usa un degrade que se apaga a 0% de opacidad hacia abajo (para flotar sobre el mapa); cuando una burbuja de hotspot o un cluster de prensa caía geometricamente debajo de la fila de íconos (marca + toggles + clima + estado), se veía "a través" de los botones -- no era un problema de capas (el click siempre fue de la topbar, confirmado con `elementFromPoint`), era que el fondo dejaba de taparlo ahí. Se agregó un segundo stop solido al degrade (`App.css`, `.topbar`) que mantiene la fila de controles siempre opaca y solo angosta el desvanecido al tramo bajo esa fila.
2. **La leyenda ("Nivel de riesgo") se tapaba con Estadísticas, Actividad y Capas del mapa.** Esos tres paneles usan `right:12px; width:82vw` en celular, lo que en una pantalla angosta llega hasta pisar la esquina o el cuerpo entero de la leyenda (que vive abajo a la izquierda). Se agregaron reglas `.app:has(.stats-panel) .legend-stack { display: none }` (y equivalentes para actividad-panel y capas-panel), mismo criterio que ya existía para `.detalle-panel`.
3. **Las dos leyendas (riesgo de siniestros + inseguridad) se superponían entre sí con la capa de delitos encendida.** `.legend-inseguridad` se apilaba arriba de la principal con un offset fijo (`bottom: 172px`), pensado para una altura de la leyenda principal que no contaba el filtro Todo/Siniestros/Delitos (solo aparece con la capa de hexágonos activa) -- en celular, con ese filtro sumando una fila más, el offset fijo quedaba corto y la leyenda de inseguridad terminaba tapando la mitad de la principal (visto real). Se reestructuró: ambas leyendas ahora viven dentro de un `.legend-stack` (`display:flex; flex-direction:column-reverse`) que las apila solas según su alto real, sin pixeles adivinados -- cambio en `App.jsx` (un wrapper nuevo, sin tocar las condiciones de cuándo se muestra cada una) y en `App.css`.

También sigue en pie el fix de la sesión anterior (SES-117, flash de la atribución de MapLibre al cargar) -- se reverificó en esta sesión con cada recarga y se mantiene corregido.

Verificación: `npx vitest run` en frontend, 93/93 en verde (no hay tests de componentes para App.jsx, pero confirma que no se rompió nada de lógica en utils ni el build). Cada uno de los tres fixes se verificó en vivo con captura + medición antes y después.

Pantallas recorridas sin problemas: mapa default, búsqueda, tarjeta de lugar, formulario de ruta, opciones de ruta, modo viaje, menú de herramientas, popup de detalle de zona, hoja de reportar.

Sigue pendiente (no cubierto en este recorrido): onboarding inicial (si existe para usuario nuevo), panel de Actividad con reportes propios cargados, variantes de errores/estados vacíos, landscape (aunque ya tiene su propio media query revisado por separado antes).

## 2026-10-19 -- SES-119: auditoría de consistencia de design tokens (borde/fuente/tamaño), a pedido explícito de Rodo ("muy exigente")

Rodo pidió ser extremadamente riguroso con cada borde, fuente, detalle y tamaño hasta que objetivamente no quede nada suelto. El propio `App.css` ya traía un comentario (de un rediseño previo) marcando qué valores habían quedado fuera de la escala de tokens como candidatos reales a unificar -- se resolvió esa lista completa, caso por caso, verificando en vivo contra el front levantado (no a ciegas).

**border-radius (15 ocurrencias de 6/8/10/12px sueltos → token exacto):**
- 3× `12px` → `var(--r-md)` (tarjeta de ruta reciente, `.viaje-salir`, popup prensa).
- 2× `8px` → `var(--r-sm)` (badges `marker-prensa-*`).
- 1× `6px` → `var(--r-xs)` (`.navegacion-luego-etiqueta`).
- 2× `7px` → `var(--r-sm)` (`.ruta-form-sugerencias button`, `.popup-grupo-prensa-item`), 1px de diferencia, imperceptible.
- Clúster de `10px` (9 ocurrencias: onboarding, stats-indice, sugerencias de ruta, zoom-controls, ruta-opcion, ruta-resumen-iniciar, popup de MapLibre, botón de lugar-card) → `var(--r-md)`, salvo `.ruta-opcion-badge` (badge chico de 1px 6px de padding) → `var(--r-pill)`, igual que las demás cápsulas chicas de la app.
- `.brand-badge` ("GBA" al lado del logo), que tenía `4px` -- un rectángulo suave al lado de dos pills hermanas en la misma fila del topbar (`--r-xl`) -- pasó a `var(--r-pill)` para compartir el mismo lenguaje de cápsula.
- Clúster de `18px` (`.navegacion-panel`, `.nav-resumen-mini`) → `var(--r-lg)`: el propio breakpoint móvil ya pisaba `.navegacion-panel` con `--r-lg`, así que el valor base quedaba distinto "por accidente" en desktop/tablet.
- Se dejaron sin tocar, a propósito: el clúster de `2px`/`4px` en barras de progreso finas (`loading-screen-barra`, `escala-linea`, `stats-barra-track/-fill`, `detalle-modelo-track/-fill`, `lector-nota-agarre-barra`) -- en barras de 3 a 6px de alto cualquier radio ≥ la mitad de la altura renderiza como píldora completa, así que 2px y 4px se ven exactamente igual ahí; no hay inconsistencia visual real que corregir. Tampoco se tocó `border-radius: 999px` (chip de filtro de prensa), que ya es la forma pill explícita.

**font-size (10 ocurrencias sueltas → token exacto o más cercano):**
- `11px` → `var(--fs-xs)`, `12px`×3 → `var(--fs-sm)`, `10px` → `var(--fs-2xs)` -- matches exactos.
- `13px` (`.marker-prensa-cluster`, número del badge de agrupación en el mapa) → `var(--fs-sm)` (12px), para que coincida con el badge gemelo `.marker-prensa-grupo`, que ya usaba ese token en su `strong`.
- `9px` (`.viaje-velocidad span`, etiqueta bajo la velocidad en modo viaje) → `var(--fs-2xs)` (10px), mismo rol que `.velocimetro span`, que ya usa ese token desde SES-115.
- `16px` en `.brand-name` dentro del media query de paisaje bajo → `var(--fs-lg)` (17px): en ese mismo bloque, `.velocimetro strong` ya reduce de `--fs-xl` a `--fs-lg`, y `.brand-name` quedaba con un valor propio (16px) en vez de seguir el mismo patrón de achique.
- Se dejaron sin tocar, confirmados como excepciones deliberadas y ya documentadas en el código: `.login-input` y el media query de inputs en celular, ambos en 16px fijo (previene el zoom automático de iOS, no es parte de la escala tipográfica), y los glifos de ícono (botón de alternar capa a 18px, botón de cerrar de MapLibre y spans de íconos de marcador de prensa a 16px) -- no son texto de la escala.

**Clúster de "números grandes" en modo navegación (la inconsistencia más visible de todas):** `.viaje-velocidad strong` (18px), `.viaje-tiempo strong` (24px) y `.navegacion-distancia` (22px) usaban tres tamaños sueltos distintos para números del mismo tipo de lectura (algo grande que se lee de un vistazo manejando), mientras que `.velocimetro strong` -- que cumple el mismo rol en reposo -- ya usa `var(--fs-xl)` desde SES-115. Se resolvió así:
- `.viaje-velocidad strong`: 18px → `var(--fs-xl)` (19px). Mismo rol exacto que `.velocimetro strong` (de hecho lo reemplaza visualmente: hay una regla que oculta el velocímetro cuando está la barra de viaje), así que pasa al mismo token.
- `.viaje-tiempo strong`: 24px → `var(--fs-2xl)` (26px). Es el número principal de la barra de viaje (el "5 min" que se lee primero), así que sube al escalón más grande de la escala en vez de quedar en un valor intermedio propio.
- `.navegacion-distancia`: 22px → `var(--fs-2xl)` (26px). El comentario de SES-095 ya decía que esta versión (durante el viaje) le da más peso a la distancia que la versión de reposo (`--fs-md`, 15px) -- para que ese "más peso" sea real y no un valor intermedio arbitrario, se empareja con el número principal de la barra inferior.

**Verificación:** `npx vitest run` → 93/93 tests OK (son cambios puramente visuales, sin tocar lógica). Revisión en vivo en 390×844 contra el front levantado: badge "GBA" y badge de ruta "⚡ rápida" como cápsulas limpias, dropdown de sugerencias de búsqueda, tarjeta de opciones de ruta, tarjeta de maniobra (`.navegacion-panel`) y barra inferior de viaje (`.nav-resumen-mini` con "5 min / 1.6 km / Salir") con el número de tiempo claramente como protagonista de la barra sin desbordar ni recortarse, y el popup de agrupación de prensa con el radio más chico (`--r-sm`) sin problemas de layout.

No se pudo verificar `.viaje-velocidad strong` (la velocidad numérica) con datos reales porque esta sesión de pruebas no tiene GPS real -- `velocidadActual` queda `null` y ese chip no se renderiza en el emulador. El cambio de 18px a `var(--fs-xl)` es una diferencia de 1px, de riesgo mínimo, pero queda pendiente una verificación visual con GPS real (o mockeando `velocidadActual`) la próxima vez que se pruebe en el celular.

Con esto se cierra la lista de valores sueltos que el propio código ya marcaba como pendientes. Lo que queda del pedido "muy exigente" de Rodo -- ancho/color de borde entre tarjetas flotantes, adherencia a la escala de espaciado, y tamaños de panel/ventana entre legend/capas-panel/stats-panel/actividad-panel/detalle-panel/report-sheet -- no se auditó todavía en esta pasada; es la continuación lógica si se quiere seguir en la misma línea.

## 2026-10-19 -- SES-119 (continuación): borde entre tarjetas flotantes, adherencia a la escala de espaciado y tamaños de panel

Siguiendo con el mismo pedido ("muy exigente"), se revisó lo que había quedado afuera de la pasada anterior: ancho/color de borde entre tarjetas flotantes, uso de la escala de espaciado, y tamaños de panel.

**Borde -- un bug real encontrado:** `.navegacion-panel` (la tarjeta de maniobra, "Doblá a la derecha...") usaba `border: 1px solid rgba(255,255,255,0.08)` en vez de `var(--border)` como el resto de las tarjetas flotantes de la app (lugar-card, legend, report-sheet, capas-panel, etc., sin excepción). En tema oscuro eso pasaba desapercibido porque el hairline blanco traslúcido se parece bastante al `var(--border)` oscuro, pero en tema claro, donde `--surface-solid` pasa a blanco, el borde quedaba blanco sobre blanco -- invisible. Confirmado con `getComputedStyle` en los dos temas antes y después del fix:
- Antes (no se llegó a medir, pero la fórmula `rgba(255,255,255,0.08)` es invariante de tema, así que en claro quedaba fundida contra `rgb(255,255,255)` de fondo).
- Después, claro: `borderColor: rgb(221, 225, 229)` (exactamente `--border` claro) contra `backgroundColor: rgb(255, 255, 255)` -- visible.
- Después, oscuro: `borderColor: rgb(44, 49, 56)` (exactamente `--border` oscuro) -- igual que antes a simple vista, porque ahí el token y el hairline casero eran parecidos.

De paso se sacó el `inset` highlight que acompañaba a ese borde (`0 1px 0 rgba(255,255,255,0.04) inset`): era otro detalle solo-oscuro, no lo usa ninguna otra tarjeta de la app, y sin el borde roto al lado no tenía ninguna razón documentada para existir. La sombra grande de la tarjeta (la más prominente en pantalla durante la navegación) se mantuvo igual.

También se encontró `.nav-resumen-mini` (la barra inferior de viaje) con `border: 1.5px solid var(--verde)` -- el único borde de acento con ancho no entero en todo el archivo. Cada otro borde de acento de estado (legend-inseguridad, ruta-banner, report-fab activo, etc.) usa 1px y solo cambia el color. Se bajó a 1px para no ser el único caso distinto.

**Espaciado:** se encontraron 7 ocurrencias de `margin-bottom: 8px` suelto en encabezados de panel (capas-panel-header, actividad-header/stats-header, ruta-resumen-header, cercanas-title, y dos más) que coincidían exactamente con `var(--sp-2)` -- swap directo sin cambio visual. Más relevante: `.report-sheet` (la hoja de "¿Qué estás viendo en la vía?") usaba `padding: 18px` fijo, mientras que el resto de la misma familia de paneles flotantes (capas-panel, actividad/stats-panel, detalle-panel) usa `var(--sp-4)` (16px) parejo en las cuatro tarjetas. Se unificó a `var(--sp-4)`, 2px de diferencia, verificado en vivo sin recortes ni desbalance.

**Tamaños de panel:** capas-panel (260px), actividad/stats-panel (250px) y detalle-panel (230px) tienen anchos distintos entre sí, pero se revisó y es justificado: los tres anclan por el borde derecho (`right: calc(20px + var(--safe-right))`), nunca aparecen dos a la vez (hay guards `:has()` que los ocultan entre sí), y el contenido de cada uno es genuinamente distinto en densidad (checkboxes de capas vs. lista de actividad vs. detalle de zona). No hay ningún punto de la pantalla donde el ancho distinto se note como inconsistencia -- no se tocó.

**Verificación:** `npx vitest run` → 93/93 OK (de nuevo, cambios puramente visuales). En vivo, en 390×844, en los dos temas: se recalculó una ruta y se inició viaje en claro y en oscuro para medir el borde de `.navegacion-panel` con `getComputedStyle` (no a ojo), se abrió el panel de Actividad (portal completo) para confirmar que el `margin-bottom` tokenizado no corta nada, y se abrió la hoja de Reportar para confirmar que el padding tokenizado se ve igual de bien que antes.

Con esto queda cerrado el pedido "muy exigente" de borde/fuente/tamaño/ventana en su alcance completo: lo que quedaba marcado como pendiente en el propio código (radius y font-size sueltos) y lo que agregó esta pasada (borde de `.navegacion-panel` roto en claro, ancho de borde inconsistente en `.nav-resumen-mini`, padding suelto en `.report-sheet`). No quedan valores sueltos obvios sin revisar; lo que sigue de acá en más es trabajo de detalle más fino (si aparece algo puntual) en vez de una auditoría sistemática nueva.

## 2026-10-19 -- SES-120: por qué "a veces se ve todo grande" -- la topbar cambiaba de alto según el texto, no por una medida puesta mal

Rodo reportó una sensación difícil de señalar con precisión: que a veces el cartel de "zonas críticas" y el buscador se sienten demasiado grandes, y en general pidió una pasada sobre todos los tamaños buscando que la interfaz se sienta más integrada entre sí (sin overlaps, sin piezas que no combinan). Se midió con `getBoundingClientRect`/`getComputedStyle` en vivo en vez de ir a ojo.

**La causa real del "a veces se agranda":** `.topbar-right` metía en una sola fila de flex (tema, capas, actividad, clima, y el pill de estado) y dependía de `flex-wrap` para bajar lo que no entraba a una segunda línea. El pill de estado (`textoTopbar`) muestra textos de largo muy distinto según el momento -- "3 zonas" (corto) vs "2 zonas críticas" vs "Ruta: 1.8 km · 5 min" vs "Modo Viaje". En un celular real (390px), iconos + clima + pill a veces entraban juntos en una fila y a veces no, así que el alto de la topbar (y todo lo que se posiciona relativo a él vía `--topbar-h`) cambiaba según qué texto le tocara mostrar en ese momento, no según ninguna medida fija. Eso es lo que se percibía como "a veces se ve todo grande": no era una medida puntual mal puesta, era que la topbar entera no tenía un tamaño predecible.

**Fix:** se separó el pill de estado de los iconos+clima en dos filas FIJAS en vez de dejarlo a merced del `flex-wrap`. Se agregó un subcontenedor `.topbar-right-iconos` en el JSX (envuelve ThemeToggle, los dos botones de capa, y clima-badge) -- en desktop esto no cambia nada, sigue siendo una sola fila con los mismos elementos. En el breakpoint de celular, `.topbar-right` pasa a `flex-direction: column` (iconos arriba, pill de estado siempre abajo, nunca compartiendo fila), así el alto de la topbar queda fijo sin importar qué tan largo sea el texto del pill. Verificado en vivo con dos estados reales: "1 zona crítica" y "Ruta: 1.8 km · 5 min" (el texto más largo que puede mostrar) -- la topbar mide el mismo alto en los dos casos, el pill nunca se corta.

**Buscador:** medido antes/después -- tenía `padding: var(--sp-3) var(--sp-4)` (12px/16px) mientras sus pills hermanos de la topbar (clima-badge, topbar-status) usan `var(--sp-2) var(--sp-3)` (8px/12px vertical más chico). Bajado el padding vertical a `var(--sp-2)`: el buscador pasa de 62px a 54px de alto, sin tocar el ícono (36px) ni el input. Sigue siendo el elemento más grande de la fila superior (correcto, es la acción principal), pero ya no desentona tanto con el resto.

**Overlaps:** se armó un barrido de `getBoundingClientRect` sobre todos los elementos flotantes visibles en simultáneo (topbar, buscador, legend-stack, FABs de ruta/reportar/herramientas) en el estado por defecto y no se encontró ningún overlap real -- los tres FABs de la esquina inferior derecha (herramientas 662-706, ruta 716-760, reportar 774-820) tienen 10-14px de aire entre sí y comparten el mismo borde derecho (16px del borde de pantalla), y la legend (termina en x=202) nunca llega a tocar los FABs (que arrancan en x=239/245/330). No se tocó nada ahí porque no hay nada roto, más allá de lo que ya se había corregido en SES-118/119.

**Trade-off a tener en cuenta:** antes, en los estados donde el texto era corto (ej. "3 zonas"), la topbar a veces lograba entrar en una sola fila y quedaba más baja. Ahora es SIEMPRE dos filas en celular, así que en esos casos puntuales la topbar ocupa un poco más de alto que antes (lo que gana en consistencia, lo pierde en los casos más chicos). Se priorizó la consistencia porque es justamente lo que Rodo pidió ("una interfaz más integrada", que no cambie de forma según el momento).

**Verificación:** `npx vitest run` → 93/93 OK (son cambios de layout/JSX estructural, sin tocar lógica ni estado). Confirmado en vivo en 390×844 y en desktop (sin cambios ahí, como se esperaba).

## 2026-10-20 -- SES-121: apartado de noticias/prensa, a pedido explícito de Rodo ("quiero mejorar todo el apartado de noticias, los logos, los pop up, que siento que no van con el resto de la estética")

Cuatro bugs reales encontrados y corregidos en `App.css`, todos relacionados con la capa de prensa/noticias del mapa. Se verificó cada uno con `getComputedStyle` en vivo, en tema claro y oscuro, no por inspección visual sola.

**1. Chip de filtro activo (`.capas-prensa-filtros button.activa`) con amarillo fuera de marca.**
Usaba un amarillo propio (`#ffd65a` claro / `#ffc933` oscuro con override separado) en lugar del token `--amarillo` (#FFC933) que usa cualquier otro elemento "activo" de la app (brand-badge, filtros del portal de actividad, etc.). Se unificó a `var(--amarillo)` + texto `#14171A`, y se borró el override de tema oscuro que ya no hacía falta. Confirmado en vivo: el chip "Todo" activo ahora mide `rgb(255, 201, 51)` = `--amarillo` exacto.

**2. Insignias de prensa en el mapa (`.marker-prensa-cluster`, `.marker-prensa-grupo`) congeladas en oscuro.**
Tenían colores fijos (`#3a3f4b` / `#c9cdd3` / `#fff`) que no reaccionaban al toggle de tema, a diferencia de cualquier otra superficie de la app. Se reemplazaron por `var(--surface-solid)` / `var(--text)`, siguiendo el mismo patrón que `.velocimetro` (otra insignia circular flotante sobre el mapa). Confirmado en vivo: en tema claro ahora mide `rgb(255,255,255)` de fondo y `rgb(27,30,34)` de borde/texto (antes quedaba gris oscuro fijo, fuera de lugar sobre un mapa claro).

**3. El hallazgo más grande: el popup de prensa (`.maplibregl-popup-content`, `.maplibregl-popup-close-button`) perdía TODOS sus overrides de fondo/radio/padding contra el CSS propio de MapLibre.**
`maplibre-gl.css` (el CSS que trae la librería) carga después de `App.css` en el bundle final de Vite. Cualquier propiedad que las dos hojas de estilo definan sobre el mismo selector la gana MapLibre por orden de carga, sin importar dónde esté la regla dentro de `App.css` — la única corrección real es `!important`. Se confirmó extrayendo el CSS real embebido de MapLibre (`grep` sobre `maplibre-gl.css`) y comparando contra `getComputedStyle()`: el popup rendereaba con el fondo blanco de MapLibre, radio ~3px y padding 15px/10px por defecto, mientras que el único override que SÍ pegaba era `color: var(--text)` — resultado: en tema oscuro, texto gris claro sobre fondo blanco, casi ilegible. Es el mismo patrón de bug que ya se había corregido en otra sesión para `.maplibregl-ctrl-attrib` / `.maplibregl-popup-tip`; estos dos selectores habían quedado afuera esa vez. Se agregó `!important` a cada propiedad en disputa (background, border-radius, padding en `.maplibregl-popup-content`; background, border, border-radius en `.maplibregl-popup-close-button` y su `:hover`), y se sumó un `box-shadow: var(--shadow-float) !important` que antes no existía, para que el popup entre en la misma familia visual que el resto de las tarjetas flotantes de la app. Se eliminaron además dos reglas duplicadas más abajo en el archivo que quedaban redundantes. Verificado con `getComputedStyle` en ambos temas: oscuro → fondo `rgb(31,35,40)` (`--surface-solid` oscuro), radio `12px`, sombra presente; claro → fondo `rgb(255,255,255)`, borde `rgb(221,225,229)`, mismo radio y sombra. Este bug afectaba a TODOS los popups del mapa, no solo a los de prensa (cualquier marcador que use el popup de MapLibre comparte el mismo selector).

**4. Botones del popup (`.popup-voto-btn`, `.popup-ver-noticia` -- el botón "Leer nota" que abre el lector interno) con fondo invisible.**
Las dos reglas usaban `background: var(--surface)`, pero `--surface` (sin sufijo `-solid`/`-float`/`-rgb`) no está definida en ningún lado de `:root` -- se confirmó por grep: cero definiciones, dos usos, ambos acá. Una variable CSS no definida y sin fallback resuelve `background-color` a su valor inicial, `transparent`: el botón "Leer nota" -- justo el elemento que Rodo señaló como la estética de referencia que el resto debía igualar -- se renderizaba sin relleno visible, solo un borde fino, como si estuviera roto. Se corrigió a `var(--inset)` en ambas reglas, seleccionado porque es el patrón ya establecido para "botón chico hundido sobre una tarjeta sólida" (mismo que `.searchbar-icon`, `.lugar-card-cerrar`). Confirmado en vivo en ambos temas: oscuro → `rgb(20,23,26)` de fondo / `rgb(232,234,237)` de texto; claro → `rgb(235,237,240)` de fondo / `rgb(27,30,34)` de texto.

**Interpretación de "los logos":** se revisó todo el código de la capa de prensa (`MapaMotoSafe.jsx`, `CapasPanel.jsx`, `ActividadPortal.jsx`) y no existe ningún asset de imagen tipo logo de medio -- toda la iconografía es Lucide (Newspaper, ListFilter, etc.) o SVG inline. Se interpretó el pedido como referido a las insignias/íconos de marcador (punto 2), no a logos de medios reales, porque esos no existen en el código. Si lo que Rodo quiere es mostrar el logo real de cada medio (Infobae, Clarín, etc.) junto a cada nota, eso es una funcionalidad nueva -- requeriría guardar la URL del logo por fuente en el modelo de datos de prensa -- no un ajuste de estilo, y queda pendiente de confirmación con él.

`npx vitest run`: 93/93 passing, sin regresiones (todas las correcciones son de CSS puro, ninguna tocó lógica).

## 2026-10-20 -- SES-122: segunda vuelta sobre los marcadores de prensa, a pedido de Rodo ("sigue quedando raro... no me gusta mucho la idea de los bordes y adentro el logo")

SES-121 ya había sacado a `.marker-prensa-cluster` / `.marker-prensa-grupo` del gris fijo que no cambiaba de tema, pero dejó intacta la forma: una caja (border-radius 8px) con un borde de 2px del color de texto, y adentro un carácter de fuente (`▤`) haciendo de ícono. Rodo lo siguió viendo raro, y con razón: ese borde grueso tiene sentido en `cluster-bubble` (siniestros) porque el color del borde ES el dato -- nivel de riesgo dominante del cluster. Acá no hay ningún dato codificado en el borde, es puro "hay noticias en esta zona", así que un contorno duro no comunica nada y solo se ve como una caja pegada encima del mapa, distinta a cualquier otra cápsula de la app.

Dos cambios, ambos en `App.css` y `MapaMotoSafe.jsx`:

**Forma y borde.** `border-radius: var(--r-sm)` (8px, caja) pasa a `var(--r-pill)` (24px, cápsula completa) y `border: 2px solid var(--text)` pasa a `border: 1px solid var(--border)` + `box-shadow: var(--shadow-float)` -- el mismo lenguaje que ya usa cualquier otra pastilla flotante de la app (topbar-status, brand-badge, searchbar, los toggles de tema/capas): borde fino y sombra suave en vez de contorno marcado. Confirmado en vivo en los dos temas vía `getComputedStyle`: `border-radius: 24px`, `border: 1px solid rgb(44,49,56)` en oscuro (= `--border` oscuro), sombra `var(--shadow-float)` presente.

**El "logo".** El carácter `▤` (un glyph de fuente, no un ícono real -- su grosor y forma dependen de la fuente del sistema, no son parte del lenguaje visual de la app) se reemplazó por el ícono real `Newspaper` de `lucide-react`, con el mismo path data que ya usa `CapasPanel.jsx` para el toggle de esta misma capa. No es "un ícono parecido": es literalmente el mismo SVG, renderizado inline con `stroke="currentColor"` para heredar `color: var(--text)` y reaccionar al tema solo. Antes el toggle del panel y el marcador del mapa mostraban dos representaciones distintas de "esto es una noticia" (un ícono de Lucide vs. un carácter tipográfico); ahora son la misma forma en los dos lugares.

`npx vitest run`: 93/93 passing. Cambio puramente visual (clase CSS + innerHTML del marcador), sin tocar lógica de clustering ni de datos.

## 2026-10-20 -- SES-123: barrida general de consistencia visual, a pedido de Rodo ("seguí buscando todas las cosas que puedas mejorar y aplica")

Tras SES-121/122 (noticias/prensa), se amplió la búsqueda a todo `App.css`/`App.jsx`/`MapaMotoSafe.jsx` buscando el mismo tipo de bug que ya apareció dos veces: un carácter de fuente haciendo de ícono en vez de un SVG real. Grep de caracteres Unicode fuera del rango ASCII normal en todo el JSX encontró seis casos; se revisaron los seis:

- `▤` en el popup del hexágono (`MapaMotoSafe.jsx`, línea "N noticias recientes en esta zona") -- mismo bug que los marcadores de prensa, se había quedado afuera de SES-121/122 porque está en otra función (`onClick` del popup de hexágono, no el de los marcadores). Reemplazado por el mismo ícono `Newspaper` inline (SVG, `currentColor`, 11px) usado en los marcadores -- ahora las tres representaciones de "hay noticias acá" (toggle del panel, marcador del mapa, meta-línea del popup de hexágono) son el mismo ícono.
- `⬆` en el aviso "Nivel subido" del panel de detalle de zona (`App.jsx`). Reemplazado por `<ArrowUp size={12} />` de `lucide-react` (ya importado en el archivo para otros íconos), con `.popup-ajuste` pasado a `display: flex; align-items: center; gap: 4px` para que el ícono y el texto se alineen.
- `✓` / `✕` en los botones de voto de reportes ("Sigue ahí" / "Ya no está") y `→` / `−` en la flecha de ajuste de nivel y los botones de zoom: se dejaron sin tocar -- son caracteres tipográficos estándar (no glyphs de dibujo técnico como `▤`/`⬆`), muy soportados en cualquier fuente del sistema, y cumplen el mismo rol que cumplirían en cualquier app nativa. No hay The señal de que estos generen el mismo "se ve raro" que reportó Rodo.

Aparte de los glyphs, se revisó (sin encontrar nada para corregir):
- Bordes `rgba(255,255,255,...)` fijos que pudieran quedar invisibles en tema claro (el tipo de bug de `.navegacion-panel` de SES-119): no quedan más, salvo el anillo de contraste de `.cluster-bubble`, que es intencional y neutral en los dos temas.
- Colores hex sueltos fuera de `:root`: son en su mayoría texto fijo sobre fondos de color fijo (ej. `#14171A` sobre `var(--amarillo)`), el mismo patrón ya validado en SES-121 -- no son bugs, son texto de contraste que debe quedar fijo junto con el color de fondo que acompaña.
- Los íconos de robo/choque en los pines individuales de prensa (`ICONOS_POR_TIPO_INCIDENTE`) usan colores fijos (no tokens de tema) a propósito: el color ahí es el dato (tipo de incidente), no decoración de tema -- mismo criterio que el borde de `.cluster-bubble`.
- Valores sueltos de `border-radius`/`font-size` por debajo del piso de la escala (2px/4px en barras de arrastre, puntos de escala, etc.): son detalles decorativos más chicos que el escalón mínimo de la escala (6px/10px), no candidatos reales a tokenizar.

`npx vitest run`: 93/93 passing. El ícono del popup de hexágono se confirmó en vivo (zoom sobre "1 noticia reciente en esta zona", ya no muestra el glyph); el de "Nivel subido" no se pudo gatillar en vivo en esta sesión (requiere una zona con nivel ajustado por actividad reciente en el dataset actual), queda validado por inspección de código y por ser el mismo patrón ya probado tres veces en esta sesión.

## 2026-10-20 -- SES-124: auditoría de documentos de gestión, retiro del principio de versionado y corrección de capítulos desactualizados (Claude)

A pedido de Rodo, se auditaron los siete documentos de `docs/gestion/` contra lo decidido/trabajado desde su última actualización real. `DECISIONES.md` no tenía ninguna entrada posterior al 14/09 pese a cuatro decisiones de peso tomadas con evidencia desde entonces; se agregaron DEC-012 (cambio de modelo productivo a variante sin edad, 05/10), DEC-013 (no aplicar calibración isotónica en producción, 05/10), DEC-014 (alcance de A01/A02 queda en criterio del proyecto, SES-113/09-10), DEC-015 (costo relativo por clase, corte p75/p95, 18/10) y DEC-016 (ver abajo). `PRIORIZACION.md` se dejó con una nota de estado (20/10) aclarando que el cuarto bloque y buena parte del tercero ya avanzaron. `VALIDACION.md` sumó una fila para documentos de tesis (.docx), describiendo el protocolo real que ya se venía usando (edición por XML, `merge_runs.py`, `assert` de ocurrencia única, `validate.py --original`, render y revisión visual).

**DEC-016, retiro del principio de versionado "capítulo entregado no se reescribe"** (adoptado originalmente en SES-055, 2026-09-15): a pedido explícito de Rodo, se retira. Las entregas parciales (1 a 9) son una fotografía del proyecto a su fecha para la cátedra, no una versión que deba quedar congelada; lo que tiene que estar completo y al día en todo momento es la Entrega Final, y la historia real de cada corrección queda en la bitácora (acá, en CONTINUIDAD.md y en la bitácora de Claude en el Project), no en notas de versión dentro del capítulo. Reemplazado en el encabezado de `BACKLOG.md`.

Con el principio nuevo, se revisaron los capítulos que hablan a futuro (Introducción, Metodología) buscando afirmaciones que un capítulo posterior del mismo informe ya contradice. Dos encontradas y corregidas en `MotoSafe_GBA_Capitulos_1_a_6.docx`:

- **2.5**: decía "no existe todavía una política aprobada de costos entre falsas alertas y omisiones de gravedad", cuando esa política ya está definida (DEC-015, 18/10) y cerrada en el Capítulo 4 (Tabla 4.3). Corregido para explicar que esa era la situación al momento de diseñar el protocolo, con referencia a dónde quedó resuelto.
- **4.8/4.10**: describía la integración continua como si el backend solo corriera un chequeo de sintaxis (`py_compile`) y el flujo no levantara una base real, cuando el CI de GitHub Actions corre la suite completa de pytest del backend contra un servicio PostgreSQL/PostGIS real y desechable desde el 05/10 (SES-066/070, confirmado en `.github/workflows/ci.yml`). Corregido; se mantiene el único pendiente real, que es la primera corrida confirmada en GitHub (bloqueada en `gh auth login` de Rodo).

Se revisó también la Tabla 4.1/4.2/4.3 de Capítulo 4 y el resto de 1-3: ya tenían los números vigentes (0,368/0,3032, variante sin edad) sin notas de versión fechadas -- no había nada ahí para "merger", la corrección quedaba solo en estos dos pasajes puntuales. Validado con `validate.py --original` (876 párrafos antes y después, sin cambios) y revisión visual (JPEG, 100dpi) de las dos páginas tocadas.

Queda abierto, señalado para Rodo y no tocado sin confirmar: 2.7 (declaración de uso de IA) describe a Codex como implementación y Claude como redacción académica exclusivamente; si Claude pasó a hacer desarrollo directo además de redacción, como mencionó Rodo, esa tabla puede necesitar una fila o aclaración nueva.

## 2026-10-20 -- SES-125: Capítulo 8 (Implicancias, conclusiones y recomendaciones) y avance real sobre D02 (Claude)

Se redactó `docs/tesis/MotoSafe_GBA_Capitulo_8_Implicancias_Conclusiones_y_Recomendaciones.docx`, en el mismo estilo visual y protocolo de generación que el Capítulo 7 (XML directo, estilos Heading1/Heading2 replicados byte a byte, `validate.py --original` contra ese mismo capítulo como referencia, render a PDF y revisión visual página por página). Estructura: 8.1 implicancias de los cinco ejes de resultados del Capítulo 7, 8.2 conclusiones objetivo por objetivo (los cinco reales de 1.2, no una síntesis vieja) más pregunta de investigación e hipótesis, 8.3 recomendaciones técnicas ancladas en ítems de `BACKLOG.md`, 8.4 recomendaciones de adopción/gobernanza ancladas en la matriz de riesgos del Capítulo 6 y el Apéndice A, 8.5 cierre.

A pedido de Rodo de seguir con lo más core primero, se avanzó sobre D02 (la inestabilidad de F1 macro entre splits temporales, medida el 18/10 sin causa identificada). Script nuevo `notebooks/investigar_causa_d02.py`, corrido contra el entorno real del proyecto (scikit-learn 1.7.2, mismo que producción). Dos resultados reales:

**Tamaño de entrenamiento descartado.** Submuestrear el set de entrenamiento <2024 (15.559 filas) al tamaño del set <2023 (11.644 filas), con 10 semillas distintas, da F1 macro de 0,380 de media sobre evaluación 2025 -- igual o mejor que con las 15.559 filas completas (0,369). Entrenar con menos datos de 2024 sigue generalizando mejor a 2025 que entrenar con todo <2023 generaliza a 2024: el tamaño del set no es la causa de la brecha.

**La brecha no golpea parejo entre clases.** El desglose por clase (ya disponible en los reportes del 18/10, re-leído para esta investigación) muestra que MORTAL es casi estable entre splits (F1 0,126 vs 0,110) y GRAVE mejora moderado (0,138 vs 0,209); el salto de F1 macro lo domina LEVE (F1 0,593 vs 0,788, recall 0,429 vs 0,669, precisión casi idéntica). La inestabilidad detectada en D02 no compromete con la misma fuerza a las clases que más importan para una alerta preventiva.

**Pista nueva, sin seguir todavía.** `edad_desconocida` en el año de evaluación salta de 12,13% (2024) a 41,10% (2025), con 2024 marcadamente más completo que el resto de la serie (train <2023 y <2024 rondan 45%). No se usa como feature en la variante `sin_edad`, así que no explica la brecha de forma directa, pero es un indicio concreto de que 2024 podría ser un año atípico en el propio proceso de carga/registro de datos oficiales, no solo en el patrón de siniestralidad vial -- abre una pista más barata de seguir (completitud de otros campos por año) que seguir buscando la causa solo en el modelo.

Evidencia completa en `docs/evidencias/2026-10-20/D02-causa/README.md`. `BACKLOG.md` (fila D02) y el Capítulo 8 (8.1 y 8.3) actualizados con este resultado. D02 pasa de "sin causa identificada" a "tamaño descartado con evidencia, cambio real de patrón sigue como hipótesis más plausible, con una pista de calidad de dato por año todavía sin seguir" -- no se cierra del todo porque la causa de fondo sigue sin confirmarse, pero ya no es una incógnita completa.

## 2026-10-20 -- SES-126: implementadas las tres correcciones de UX que pidió la prueba real con usuarios (R-04, R-05, Casos 9/12) (Claude)

A pedido de Rodo, se avanzó sobre el segundo punto del Nivel 1 (los cambios de UX que salieron de la validación real con 12 motociclistas, Apéndice A / Capítulo 6). Tres cambios reales en `frontend/src/App.jsx`, `frontend/src/App.css` y `frontend/src/components/CapasPanel.jsx`:

**R-04, reducir lo que se muestra por default en la tarjeta de ruta.** La demanda más repetida de la prueba (Casos 4 y 10) era mostrar menos por default y dejar el cálculo como algo opcional. Se agregó `detalleRutaAbierto` (arranca en `false`): la cobertura por fuente (%) y el desglose de puntos por zona cruzada ahora quedan detrás de un toggle nuevo ("Ver cómo se calcula"/"Ocultar cómo se calcula"); por default cada tarjeta muestra solo lo que ya mostraba como principal (ruta, km/min, ETA con tráfico si aplica, y la línea de advertencia de exposición), que es exactamente tiempo + distancia + advertencia principal, lo que pidieron.

**R-05, explicación visual del score en vez de solo texto.** El único lugar donde se explicaba qué significa "cobertura" era un atributo `title` (tooltip de mouse), inútil en celular, que es como la mayoría usa la app en la calle -- y la propia prueba mostró que ese texto no evitaba la confusión (Casos 1, 3, 10, 12) pese a existir desde antes del 15/09. Se reemplazó por un párrafo siempre visible cuando el detalle está abierto, con un ejemplo concreto con números reales ("cobertura de siniestros 40% significa que 4 de cada 10 tramos..."), en vez de una definición abstracta.

**Nomenclatura de filtros (Casos 9 y 12 del Apéndice A).** El filtro de prensa llamado "Seguridad" no decía qué incluía; se verificó contra `PALABRAS_CLAVE_INSEGURIDAD` en `backend/scrapear_noticias_robos.py` que esa categoría son hechos de violencia (tiroteos, homicidios, secuestros, violencia de género), ya separados de robo y de choque -- se renombró a "Violencia", que nombra lo que el filtro de verdad trae. El interruptor de inseguridad del panel de capas ya tenía una nota explicando que apagarlo no saca la inseguridad del cálculo de ruta, pero es una nota genérica al pie de todo el panel desde el 07/09, y aun así un caso real de la prueba del 15/09 siguió interpretándolo mal -- se agregó una segunda nota, más corta, pegada directamente a las opciones de inseguridad, en vez de confiar solo en la nota genérica de más abajo.

Verificado con `npx vitest run` (93/93 en verde, sin regresiones), `npx eslint` (sin errores) y `npm run build` (build de producción limpio). No se verificó en vivo en el navegador porque requiere levantar el backend completo con PostgreSQL y autenticación configurada, que no se justifica para un cambio puramente de presentación; queda a criterio de Rodo pedir esa verificación antes de la próxima entrega si quiere confirmarlo visualmente él mismo.

Pendiente, documentado y no hecho en esta sesión: repetir la validación con usuarios reales después de estos cambios (es la recomendación que el propio Capítulo 8 deja para después de implementarlos, no algo que se pueda hacer sin motociclistas reales disponibles).

## 2026-10-20 -- SES-127: red confirmada como bloqueo real (A19/D03/D04) y política de privacidad cerrada (6.5) (Claude)

Antes de seguir con el Nivel 2, se confirmó con una prueba directa (no solo repitiendo lo que ya decía el backlog) que A19 (pipeline contra servicios reales) y D03/D04 (rutas reales vía OSRM) siguen bloqueados por red desde cualquiera de los dos entornos de Claude: `curl` contra `data.buenosaires.gob.ar`, `api.open-meteo.com` y `router.project-osrm.org` desde la VM local (la misma que usa `device_bash`) falla los tres con conexión rechazada (exit 56), igual que ya constaba para OSRM específicamente. Los tres scripts de fetch (`notebooks/fetch_delitos_caba.py`, `fetch_clima_historico.py`, `fetch_corredores_geometria.py`) ya documentan en su propio docstring que necesitan correrse desde la terminal de Rodo, no desde ningún entorno de Claude -- queda confirmado que esa nota sigue siendo correcta, no es algo para seguir intentando resolver desde acá.

Con eso descartado como siguiente paso inmediato, se avanzó un pendiente de bajo riesgo y alto valor para los criterios de ética de la cátedra: `docs/operacion/POLITICA_PRIVACIDAD.md`, nuevo. Describe, verificado contra el código real de `backend/main.py` y `backend/auth.py` (no contra supuestos): qué guarda un reporte colaborativo (lat/lng exactas, categoría, `autor_id` como UUID de dispositivo sin dato personal), qué NO guarda (IP persistida -- el rate limit y el bloqueo de login son en memoria, se pierden al reiniciar el proceso --, nombre, email, cuentas de usuario), retención y las tres formas de borrado (token privado, consenso, vencimiento por categoría), y declara de forma explícita una limitación que antes no estaba escrita en ningún lado: la ubicación se guarda sin redondear ni desplazar, con el costo de privacidad real que eso implica si alguien correlacionara reportes del mismo dispositivo.

Actualizados en consecuencia: Capítulo 6 (6.5, la barrera ética ya no dice "sigue pendiente"; 6.6, la síntesis ya no cuenta la política de privacidad entre lo abierto) y Capítulo 8 (8.4, la recomendación pasa de pendiente a cerrada, con nota de que fue necesario reformular la redacción porque citar la ruta del archivo entre paréntesis generaba un salto de justificación feo en el render a PDF -- se sacó la ruta literal del cuerpo del texto).

Validado con `validate.py --original` contra ambos capítulos (0 cambios de párrafos en Capítulo 1-6, misma estructura en Capítulo 8) y revisión visual en PDF de las páginas tocadas.

## 2026-10-20 -- SES-128: A17, primera extracción real de App.jsx (Claude)

Primer paso de la separación incremental de `App.jsx` que A17 venía pidiendo desde hace varias sesiones (2140 líneas en la última medición, 2398 después de los cambios de R-04/R-05/SES-126). Se identificó el bloque de JSX más grande y más autocontenido que seguía inline: el panel completo de "Opciones de ruta" (`ruta-resumen`, 145 líneas), con una interfaz de props razonablemente chica (13 props: `panelRuta`, `rutasConScore`, `rutaSeleccionada`/`setRutaSeleccionada`, los tres índices de prioridad, `detalleRutaAbierto`/`setDetalleRutaAbierto`, `zonasCruzadasOrdenadas` y tres callbacks).

Se extrajo a `frontend/src/components/RutaResumenPanel.jsx`. Es un corte-y-pegue con props, no un rediseño: el JSX y el comportamiento son idénticos a los que tenía adentro de `App.jsx`, incluidos los cambios de R-04/R-05 de SES-126 (el toggle de detalle y el ejemplo visual del score). `App.jsx` pasó de 2398 a 2306 líneas; se sacaron del import de `lucide-react` los siete íconos que quedaron sin uso ahí (`Pencil`, `Zap`, `Scale`, `ShieldCheck`, `CircleCheck`, `ChevronDown`, `ChevronUp`), verificado con `eslint` antes y después del retiro.

Verificado con `npx vitest run` (93/93 en verde, sin regresiones), `npx eslint` (0 errores en los dos archivos) y `npm run build` (build de producción limpio, mismo warning preexistente de tamaño de chunk que no tiene que ver con este cambio). No verificado en vivo en el navegador, misma razón que SES-126 (requiere backend + PostgreSQL + auth).

Sigue pendiente de A17 (no cerrado con esto): el resto de `App.jsx` sigue teniendo ~2300 líneas y ~35 `useEffect`. El panel de ruta era el bloque más grande y de menor acoplamiento; lo que queda (barra de búsqueda, navegación activa, detalle de zona, portal de actividad inline) tiene más estado compartido entre sí y requiere más cuidado para separar sin romper nada -- candidato para la próxima sesión que toque A17, no para intentarlo todo de una vez.

## SES-129 (2026-10-20) — A09: medición de duplicación semántica entre fuentes de prensa

Investigado el pendiente de A09 "deduplicación semántica" con el mismo criterio que D02: medir antes de implementar, no suponer.

El extractor dedupe hoy solo por título exacto dentro de una corrida (`firma_titular`, set que se descarta al terminar) y por URL exacta entre corridas (`ON CONFLICT (url_fuente) DO NOTHING`). Ninguna de las dos detecta el mismo incidente cubierto por dos medios distintos, con URL y título distintos — el caso real que infla el conteo de exposición en una zona puntual.

Medido con similitud Jaccard de título sobre las 450 filas reales de `docs/evidencias/2026-10-06/A09-regeocodificacion/propuesta.csv` (20 fuentes, snapshot real de `reportes_prensa`): 9 pares cross-fuente (~2%) son duplicados inequívocos del mismo incidente a un umbral conservador (jacc ≥0,70); por debajo de jacc ~0,45 el método ya confunde incidentes distintos que comparten partido y tema narrativo. El problema es real pero acotado, no masivo.

No se implementó un auto-descarte en producción. `firma_titular` ya documenta por escrito que evitar la deduplicación semántica fue una decisión deliberada (el costo de perder un incidente real por un falso merge es mayor que el de contarlo dos veces), y la medición confirma que ese riesgo es concreto, no teórico: el margen entre "duplicado seguro" y "falso positivo seguro" es angosto. Cambiar el flujo de guardado de `_evaluar_y_guardar` sin poder validarlo en vivo contra la base real de este entorno (sin acceso a Postgres desde aquí) no corresponde decidirlo unilateralmente.

Evidencia completa y tres caminos posibles (auto-descarte a jacc≥0,70, marcar-para-revisión sin descartar, o dejarlo como está) en `docs/evidencias/2026-10-20/A09-dedup-semantica/README.md`, pendiente de la decisión de Rodo antes de tocar producción.

El otro pendiente de A09, validación de calles sin conjunto etiquetado, sigue sin abordarse: no hay un conjunto de casos reales armado para medirlo y no se fabricó uno para evitarlo.

## SES-130 (2026-10-20) — A09: implementa deduplicación semántica automática, sin revisión humana, no destructiva

A partir de la medición de SES-129, Rodo pidió la opción de marcar-para-revisión pero sin el paso de revisión humana: automatizar la decisión, no borrar nada.

Implementado en `_detectar_duplicado_semantico` (`backend/scrapear_noticias_robos.py`): antes de insertar una nota nueva, busca entre las filas ya guardadas del mismo `tipo_incidente` la intersección de tres señales -- ventana de 5 días, radio de 1500m, similitud de título (Jaccard de tokens) ≥0,70. El umbral es el más conservador medido (no un punto medio) justamente porque acá no hay humano revisando antes de que la marca tenga efecto. Si las tres se cumplen, la fila se guarda igual -- nunca se pierde el dato crudo -- pero queda marcada con `duplicado_de_id` apuntando a la original.

Columna nueva `duplicado_de_id` (nullable, FK a la misma tabla) en `backend/migrations/004_duplicados_prensa.sql`, con el mismo patrón de red de seguridad en `_asegurar_tabla` que ya tienen `tipo_incidente` y `relacionado_moto`. `_FILTRO_FUENTES_PRENSA_SQL` en `backend/main.py` ahora excluye `duplicado_de_id IS NOT NULL` del mismo modo que ya excluye las filas viejas de Google Noticias: no se borra, se deja de contar en `/reportes-prensa` y en el ajuste de riesgo por reportes recientes.

5 pruebas nuevas en `backend/tests/test_scrapear_noticias_robos.py`, con los mismos casos reales de la medición: el par de Moreno (jacc 0,73, dos medios independientes) se detecta y marca; el par límite de Merlo/La Matanza (jacc 0,44, mismo tema y patrón narrativo, hechos distintos) se rechaza correctamente; el mismo par de Moreno puesto a más de 1500m se rechaza aunque el título coincida casi textual. 127/127 pruebas de backend en verde (excluidas `test_integracion_postgres.py`, que necesita base real, y `test_run_dev.py`, que falla por falta de `uvicorn` en este entorno -- ninguna de las dos por este cambio).

Sin verificar esta sesión: el filtro de ventana de días y de `duplicado_de_id IS NULL` vive en el `WHERE` de la consulta SQL real, no en código Python testeable sin Postgres -- inalcanzable desde este entorno. Tampoco se aplicó la migración ni se corrió el scraper contra la base real para ver cuántas filas existentes quedarían marcadas. Evidencia completa en `docs/evidencias/2026-10-20/A09-dedup-semantica/README.md`.

## SES-131 (2026-10-20) — A17: dos extracciones más de App.jsx (HerramientasMenu, ReportSheet)

Mientras se esperaba la corrida real del scraper de A09 (dry-run en segundo plano en la máquina de Rodo/Codex), se siguió con A17.

Extraídos dos bloques más, mismo criterio que `RutaResumenPanel` (SES-128): autocontenidos, interfaz de props chica, corte-y-pegue sin cambio de comportamiento.

- `HerramientasMenu.jsx`: el menú flotante de "más herramientas" (ubicación, modo viaje, vista inclinada, estadísticas, cerrar sesión). 11 props.
- `ReportSheet.jsx`: el botón flotante "Reportar" y la hoja de categorías que se abre al tocarlo. 7 props (usa `CATEGORIAS_REPORTE` importado directo de `constants.js`, no como prop).

`App.jsx` bajó de 2305 a 2265 líneas. Lint sacó 6 imports de íconos sin uso tras la extracción (`TriangleAlert`, `Bike`, `Box`, `BarChart3`, `LogOut`, `Wrench`). Verificado con 93/93 tests, lint y build limpios; sin verificación visual en navegador en vivo (misma limitación de siempre: necesita el stack completo con Postgres + auth).

Lo que queda de A17 sigue siendo lo más complicado: navegación activa (`navegacion-panel`, `nav-resumen-mini`, `velocimetro`), que comparten estado de viaje en vivo entre sí (velocidad, distancia restante, ETA), la barra de búsqueda y el panel de detalle de zona. Esos tienen estado compartido real, no son un corte-y-pegue tan directo como los cuatro bloques ya extraídos -- quedan para una sesión que se dedique específicamente a desenredar ese estado compartido antes de separar la UI.

## SES-133 (2026-10-20, noche) — A09: corrige el umbral de título con un umbral graduado por precisión de coordenada (DEC-018)

Codex corrió el scraper real contra producción (`--guardar`, primera corrida desde que se aplicó la migración 004): 51 filas nuevas, 0 marcadas como duplicado. Entre esas 51 encontró un caso real que la implementación de SES-130 no detectó: un tiroteo en Villa Pueyrredón cubierto por 4 medios distintos, con coordenadas casi idénticas (misma intersección, geocodificada a nivel preciso en los cuatro casos) pero títulos editorialmente distintos entre sí -- la similitud Jaccard entre los pares de títulos reales que midió Codex rondó 0,133 a 0,385, todos por debajo del umbral de 0,70 fijado en DEC-017.

El hallazgo es válido y esperable: 0,70 se fijó como el punto más conservador medido sobre 450 filas (SES-129) justamente para minimizar falsos merges sin revisión humana, a costa de dejar pasar casos reales donde los medios redactan el título de forma distinta para el mismo hecho. Bajar el umbral global para capturar este caso reabriría el riesgo de falso merge ya medido (por debajo de jacc ~0,45 el método confunde incidentes distintos del mismo partido y tema).

En vez de bajar el umbral global, se gradúa según qué tan precisa es la coincidencia geográfica (DEC-018). Agregado a `backend/scrapear_noticias_robos.py`:

```
UMBRAL_DUPLICADO_SEMANTICO_COORDENADA_PRECISA = 0.15
RADIO_COINCIDENCIA_PRECISA_METROS = 300       # provisional
RADIO_MAX_GEOCODE_PRECISO_METROS = 150        # 'calle'/'interseccion'; excluye 'barrio' (800m)
```

`_detectar_duplicado_semantico` ahora recibe también el `radio_metros` con el que se geocodificó la nota nueva, y lo compara contra el `radio_metros` ya guardado de cada candidata. Si ambas notas se geocodificaron a nivel preciso (`radio_metros` ≤150m, es decir `calle` o `interseccion`, nunca el centroide de `barrio` a 800m) y además están a ≤300m entre sí, el umbral de título exigido baja de 0,70 a 0,15 -- la coordenada casi exacta ya hace improbable que sean dos hechos distintos, así que alcanza con que los títulos compartan tema. Fuera de esa condición (geocodificación vaga, o coordenadas lejanas) se mantiene el umbral estricto de 0,70 sin cambios.

El radio de 300m es una estimación provisoria, no medida: se eligió por quedar claramente por encima de la imprecisión típica de un geocoder a nivel de calle/intersección y por debajo del radio general de 1500m que ya filtra candidatas. Codex va a mandar una muestra real de grupos con la misma coordenada redondeada para calibrarlo contra datos reales en vez de contra una estimación.

Actualizados los 5 tests existentes para incluir el nuevo parámetro `radio_metros` (se usó 800, nivel `barrio`, en los casos de Moreno y Merlo/La Matanza para que sigan ejercitando el umbral estricto y no el nuevo umbral laxo por accidente). Agregados 2 tests nuevos calibrados con los valores reales de Villa Pueyrredón que midió Codex: uno confirma que con geocodificación precisa y coordenadas casi idénticas el par se marca aunque el título esté lejos del umbral estricto; el otro confirma que con la misma coordenada y los mismos títulos, si la geocodificación es vaga (`barrio`, 800m) no se activa el umbral laxo. 32/32 pruebas del scraper en verde, 129/129 de todo el backend.

Documentado en DEC-018 (`docs/gestion/DECISIONES.md`) y en `docs/evidencias/2026-10-20/A09-dedup-semantica/README.md` (sección "Corrección").

Sin verificar esta sesión: el radio de 300m sigue sin calibrar contra datos reales (pendiente la muestra de Codex), y el fix no se probó todavía contra una corrida real en producción -- la única corrida real que existe (la que encontró el problema) fue con el código anterior a este cambio.

## SES-134 (2026-10-20, misma noche) — A09: corrige DEC-018 con datos reales (DEC-019) — Villa Pueyrredón sigue sin resolverse

Codex trajo lo que le pedí para calibrar el radio de 300m del ajuste de SES-133: la distancia real entre pares de filas con geocodificación precisa (`radio_metros≤150`) en toda la base de producción. El resultado obligó a corregir dos cosas que el ajuste anterior no tenía en cuenta, no solo a ajustar un número.

**Primer problema, el más serio**: Villa Pueyrredón -- el caso real que motivó todo el trabajo de SES-133 -- tiene `radio_metros=800` en las 4 filas (nivel `barrio`, no `calle`/`interseccion`). El guard de precisión que agregué en SES-133 exige `radio_metros≤150` en ambas filas antes de aplicar el umbral laxo. Como consecuencia, el mecanismo implementado nunca iba a detectar el caso que lo motivó, sin importar qué radio de distancia se usara -- esto no se había verificado contra el dato real de esa fila hasta que Codex lo señaló.

**Segundo problema**: de toda `reportes_prensa`, solo 36 filas tienen geocodificación precisa (`radio_metros≤150`); el resto (745) está a nivel `barrio`. Dentro de esas 36, el único grupo multi-fuente real es José C. Paz (Infobae ×2, Minutouno), coordenada idéntica hasta el 7º decimal. Medí el jaccard real entre los títulos de las dos notas de Infobae del mismo hecho (confirmado por la coordenada): 0,0. El umbral de 0,15 fijado en SES-133 tampoco lo hubiera detectado.

Los dos únicos pares de precisión alta que Codex confirmó como hechos distintos están a 963m y 1319m. No hay un solo caso real medido entre 1m y ~960m -- la señal de distancia es binaria con los datos disponibles (0m = mismo hecho, ~960m+ = hechos distintos).

Corrección aplicada en `backend/scrapear_noticias_robos.py`: `RADIO_COINCIDENCIA_PRECISA_METROS` bajó de 300 (estimado) a 100 (dato real, con margen contra los 963m conocidos). `UMBRAL_DUPLICADO_SEMANTICO_COORDENADA_PRECISA` bajó de 0,15 a 0,0: dentro de la rama de coincidencia precisa, exigir superposición de título solo generaba un falso negativo (José C. Paz) sin evitar ningún falso positivo medido -- la geografía+tiempo+categoría ya hace el trabajo ahí.

Lo importante, dicho sin vueltas: Villa Pueyrredón y cualquier duplicado geocodificado a nivel `barrio` siguen sin una solución automática. Vuelve a ser un pendiente abierto de A09, no algo que SES-133 haya cerrado -- esa sesión implementó un mecanismo que resuelve un problema distinto (duplicados con geocodificación precisa, como José C. Paz), no el que lo motivó.

2 pruebas nuevas con los casos reales exactos que trajo Codex (José C. Paz, detecta; par a 963m, no detecta). Corregidos también los docstrings de los tests de SES-133 que describían a Villa Pueyrredón como geocodificado "a nivel calle" -- era hipotético, no el dato real. 34/34 pruebas del scraper, 131/131 de todo el backend.

Documentado en DEC-019 (`docs/gestion/DECISIONES.md`), `docs/evidencias/2026-10-20/A09-dedup-semantica/README.md` (segunda sección de corrección) y la fila A09 de BACKLOG.md.

Sin verificar: 100m y 0,0 están calibrados contra una muestra chica (36 filas de precisión alta en toda la tabla, un solo grupo multi-fuente real); no hay todavía una corrida real posterior a este cambio.

## SES-135 (2026-10-20, misma noche) — Figura 4.3 actualizada al pipeline real de A09

Pendiente anotado desde hace varias sesiones ("anotado para después"): la Figura 4.3 del Capítulo 4 (flujo de ingesta de prensa) seguía mostrando el diagrama original de SES-050, con una caja "Deduplicación por URL y geocoding opcional" que ya no describe el sistema real -- el geocoding no es opcional (es obligatorio y graduado por precisión desde SES-073/SES-133) y la deduplicación hoy es un paso de tres mecanismos distintos (título exacto en la misma corrida, URL exacta entre corridas, y semántica no destructiva desde DEC-017/018/019), no un único paso de "URL".

Regenerado con matplotlib (mismo estilo que las Figuras 4.1/4.2: Times New Roman, cajas con el mismo criterio de línea sólida/punteada para "implementado" vs "preparado, no validado"), reflejando el orden real del código (`backend/scrapear_noticias_robos.py`, función `_evaluar_y_guardar`): Fuentes → Scheduler → Extractor (clasificación + dedup por título dentro de la misma corrida) → Geocodificación por zona (calle/intersección/barrio, con radio) → Deduplicación semántica (no destructiva, DEC-017/018/019) + URL exacta → PostgreSQL → API backend. La nota al pie se actualizó para mencionar explícitamente que la deduplicación semántica no resuelve los casos geocodificados a nivel barrio (DEC-019), en vez de dejarlo implícito.

Reemplazada la imagen dentro del docx (mismo `rId`, mismo archivo de medios) sin tocar el resto del documento. Validado con `validate.py --original` (0 cambios de párrafos) y revisión visual en PDF de la página 24, donde queda embebida sin recortes ni solapamiento con el pie de figura.

## SES-136 (2026-10-20, misma noche) — A17: cinco extracciones más de App.jsx (navegación, detalle de zona, leyenda, búsqueda)

Encaré el resto de A17 que había quedado frenado por "requiere más cuidado, estado compartido" (SES-131). Al mirar el código real con más detalle, el riesgo era menor de lo que parecía: los bloques de JSX candidatos consumen estado ya calculado más arriba en `App.jsx` (por props de solo lectura), no manejan estado propio entrelazado entre sí -- el acoplamiento real está en los `useEffect` que calculan `velocidadActual`, `etaInfo`, `pasoActual`, etc., y esos se quedan donde estaban. Extraer la parte de renderizado no toca esa lógica.

Cinco componentes nuevos, mismo criterio que las extracciones anteriores (corte-y-pegado con props, sin cambio de comportamiento):

- `NavegacionManiobra.jsx`: la tarjeta de "doblá acá" con el giro activo y preview del siguiente. 9 props.
- `NavegacionResumen.jsx`: la tira mínima de navegación (velocidad/tiempo/distancia restante + botón salir), el botón de recentrar y el velocímetro en vivo -- tres bloques adyacentes. 10 props.
- `DetalleZonaPanel.jsx`: el panel de detalle de una zona del mapa (gravedad, predicción del modelo, ajuste por reportes recientes). 3 props. `COLOR_CLASE_MODELO` (constante de colores del modelo) se movió adentro, era de uso exclusivo de este panel.
- `LegendStack.jsx`: la leyenda de nivel de riesgo + la de inseguridad, con sus filtros. 13 props. La función `TextoCobertura` (línea de cobertura bajo cada leyenda) se movió adentro, era de uso exclusivo de este bloque.
- `SearchBar.jsx`: la barra de búsqueda de lugar/calle con sugerencias y recientes, más la tarjeta del lugar elegido al seleccionar un resultado. 12 props.

Una corrección real que surgió al extraer: `NavegacionManiobra` guardaba el ícono de la maniobra en una variable `ManiobraIcon` (PascalCase) y lo renderizaba como `<ManiobraIcon/>` -- un patrón que ESLint (`react-hooks/static-components`) no marcaba mientras vivía adentro de una IIFE anónima dentro de `App.jsx`, pero sí marcó al quedar en un componente nombrado de verdad ("Components created during render"). No es un bug nuevo de esta sesión, es un patrón preexistente que la extracción hizo visible. Se corrigió con el mismo criterio que ya usa `climaInfo.Icon` en el propio `App.jsx`: en vez de una variable PascalCase, un objeto con la clave `Icon` (`maniobra.Icon`), que ESLint no confunde con una declaración de componente.

`App.jsx` bajó de 2265 a 2066 líneas (-199). Imports de `lucide-react` recortados a los que siguen en uso (`Search`, `Navigation`, `Square`, `Gauge`, `CornerDownRight`, `Clock`, `ArrowUp` se movieron a los componentes nuevos); `OPCIONES_CAPA_INSEGURIDAD`, `NIVELES_INSEGURIDAD_COLOR`, `OPCIONES_FILTRO_HEXAGONO` y `formatearPeriodo` también se sacaron del import de `App.jsx` por la misma razón.

Verificado con `npx eslint src/` (0 errores en todo el proyecto), `npx vitest run` (93/93 en verde, sin regresiones) y `npm run build` (build de producción limpio, mismo warning preexistente de tamaño de chunk). Sin verificación visual en navegador en vivo -- misma limitación de siempre (necesita backend + PostgreSQL + auth + GPS real para Modo Viaje).

Lo que queda de A17, ahora sí genuinamente más complejo: el formulario de ruta (`ruta-form`, origen/destino con `sugOrigen`/`sugDestino`/`campoActivo`/`marcarEnMapa`, con más acoplamiento cruzado real), el panel de actividad reciente y los distintos banners de error de capas. Candidato para una sesión dedicada, no para seguir hoy.

## SES-137 (2026-10-21) — A09: diagnóstico real de por qué Villa Pueyrredón no tiene geocodificación precisa (DEC-020)

Antes de inventar una señal nueva para la dedup a nivel barrio, se probó algo más barato primero: ¿el extractor se está perdiendo una calle o intersección que el texto real de la nota sí menciona? Si así fuera, el arreglo correcto sería mejorar la geocodificación, no la deduplicación.

Codex hizo fetch en vivo de las 4 URLs reales de Villa Pueyrredón (Minutouno, La Nación, Clarín, TN) y corrió `extraer_titulo_descripcion` → `extraer_ubicacion`/`zona_de_ubicacion` tal cual están en el código, sin tocar nada, contra el título y la descripción real de cada una.

Resultado, no el sí/no limpio que se esperaba: 3 de las 4 notas (Minutouno, Clarín, TN) son genuinamente vagas -- "una plaza", "una plazoleta", sin ninguna calle ni intersección mencionada. Ahí no hay nada que el extractor se esté perdiendo, por más patrón que se agregue. La cuarta (La Nación) sí da una referencia puntual real: "plaza Nunca Más" y "junto a la estación del ferrocarril Mitre". Los patrones actuales (`RE_INTERSECCION`, `RE_ALTURA`) buscan calle+calle o calle+altura, no nombres propios de plaza o estación -- sería una capacidad nueva, no una extensión de lo que ya existe.

La razón para no construirla todavía, documentada en DEC-020: aunque se construyera, solo mejoraría la precisión de 1 de las 4 filas. El guard de precisión de DEC-019 exige que AMBAS filas de un par estén a nivel preciso -- con una sola nota precisa entre cuatro vagas, el caso real que motivó todo este trabajo seguiría sin detectarse igual. Construir reconocimiento de nombres propios de plaza/estación (con el riesgo de ambigüedad que trae: nombres repetidos en distintos barrios) a partir de una muestra de un solo caso, para una mejora que no resuelve el problema motivador, no se justifica.

Lo valioso de este diagnóstico no es lo que no se hizo, es lo que confirma: mejorar la geocodificación no es una solución general al problema de dedup a nivel barrio. La vaguedad real de buena parte de la cobertura policial ("una plaza", sin más datos) no tiene calle que extraer, con ningún patrón. El pendiente de A09 queda, en los hechos, igual de abierto que antes, pero mejor entendido -- y se unifica con el otro pendiente viejo de A09 ("validación de calles sin conjunto etiquetado"): cualquier señal futura basada en texto, sin apoyo de coordenada, necesita primero un conjunto etiquetado real para calibrarse, no una heurística inventada sobre un caso.

No se tocó código esta sesión -- el diagnóstico fue deliberadamente de solo lectura, corriendo funciones ya existentes contra datos reales nuevos.

## SES-138 (2026-10-21, mismo día) — A09: cierre real de la dedup semántica (DEC-021)

Rodo pidió cierre real, no otro "sigue pendiente" ("pero QUIERO CERRARLO O DARLE CIERRE"). Antes de escribir una conclusión nueva, volví a leer con cuidado el código ya implementado de `_detectar_duplicado_semantico`, no la narrativa que yo mismo había construido en DEC-019/SES-134 sobre él -- y encontré que esa narrativa estaba mal.

Lo que DEC-019 decía: "Villa Pueyrredón y cualquier duplicado geocodificado a nivel `barrio` siguen sin una solución automática." Eso es más pesimista de lo que el código real hace. La rama estricta (`UMBRAL_DUPLICADO_SEMANTICO = 0,70`) no exige geocodificación precisa en ningún lado -- solo exige `distancia ≤ RADIO_DUPLICADO_METROS` (1500m), que dos notas del mismo barrio cumplen trivialmente porque comparten el mismo centroide (distancia = 0m). El guard de precisión de DEC-018/019 (`coincidencia_precisa`) es una rama *adicional* con un umbral más laxo (0,0), no la única rama que puede marcar un par a nivel barrio. Si dos notas de barrio tienen títulos con jaccard ≥0,70, ya se marcan, con el mecanismo que está en producción desde SES-130 -- sin tocar nada.

Cuantifiqué esto contra el mismo dataset real de 450 filas que SES-129 usó para medir el 0,70 original (`docs/evidencias/2026-10-06/A09-regeocodificacion/propuesta.csv`), recalculando el nivel de precisión actual de cada fila como `nivel_nuevo or nivel` (la re-geocodificación de SES-073 solo llena `nivel_nuevo` cuando el nivel cambió). Distribución real: 426 filas a nivel `barrio`, 12 a `interseccion`, 12 a `calle`. Repetí la misma metodología de SES-129 (jaccard de título entre pares de fuente distinta, umbral ≥0,70) sobre esos 450: salen los mismos 9 pares duplicados reales que SES-129 ya había encontrado. De esos 9: 7 son barrio-barrio, 1 calle-barrio, 1 calle-calle. **Los 9 ya están cubiertos por la rama estricta**, con o sin el guard de precisión -- ninguno necesitaba DEC-018/019 para detectarse.

Eso acota el problema real a algo mucho más chico que "nivel barrio en general": es específicamente el par barrio + jaccard <0,70 (títulos editorialmente distintos del mismo hecho, sin coordenada precisa que lo compense). Contra los 450 reales medidos, esa combinación tiene **0 casos conocidos** -- los 9 duplicados reales de la muestra superan 0,70 igual. El único caso real conocido de esa combinación es Villa Pueyrredón, que no está en esta muestra histórica: apareció en la corrida en vivo de SES-133/134 (4 medios, jaccard máximo medido 0,467, nivel barrio los 4).

Con ese número (1 caso real conocido contra ~500 filas reales evaluadas en total entre esta muestra y las corridas en vivo), DEC-021 declara cerrado el punto de A09 "dedup semántica a nivel barrio": el riesgo residual real medido es mucho más angosto de lo que DEC-019 decía, y queda aceptado como riesgo conocido en vez de perseguido con una heurística sin sustento (DEC-020 ya descartó reconocimiento de landmarks por la misma razón: muestra de 1 caso, no resuelve ni ese caso completo). El pendiente de "validación de calles sin conjunto etiquetado" queda explícitamente aparte, sin cerrar -- necesita un conjunto etiquetado real para avanzar, no se cierra por la misma medición.

No se tocó código: la implementación ya hacía lo correcto, lo que estaba mal era mi descripción de lo que hacía. Corregido en DEC-021 (`docs/gestion/DECISIONES.md`), la fila A09 de BACKLOG.md y este README. No hay tests nuevos porque no hay comportamiento nuevo que probar -- los 7 tests existentes de este mecanismo (incluidos los de SES-133/134 contra José C. Paz y los casos de guarda) siguen describiendo correctamente el código tal cual está.

## SES-139 (2026-10-21, mismo día) — A17: las tres extracciones que faltaban (banners de capas, actividad reciente, formulario de ruta)

Rodo autorizó avanzar con todo lo pendiente. De los tres ítems reales que quedaban (A17, A09 conjunto etiquetado, D03/D04), A17 era el único ejecutable acá mismo sin bloqueo: no depende de red externa ni de datos que no existen todavía, a diferencia de D03/D04 (bloqueados por el proxy de salida, que vuelve a rechazar `router.project-osrm.org` con 403, confirmado de nuevo esta sesión) o de A09 (necesita un conjunto etiquetado a mano que no se puede fabricar).

Al revisar el código real de los tres bloques que quedaban señalados como "más enredados" desde SES-136, el riesgo resultó menor del anunciado, con el mismo patrón que ya se repitió en esa sesión: lo que parecía acoplamiento real resultó ser, en los tres casos, el mismo patrón ya usado en las nueve extracciones anteriores (props de solo lectura + callbacks hacia arriba), no estado compartido de verdad.

- `CapaErrorBanners.jsx`: los tres carteles de error de capas (backend caído, capas que no se actualizaron, tráfico no disponible). 8 props.
- `ActividadReciente.jsx`: el panel chico de "Actividad reciente" (historial de reportes propios, distinto de `ActividadPortal` que es el feed de toda la ciudad). 9 props.
- `RutaForm.jsx`: el formulario de origen/destino con sugerencias, favoritos (Casa/Trabajo) y las acciones de buscar/cancelar ruta. El acoplamiento real que motivó la cautela (`campoActivo` compartido con el click en el mapa y con el flujo de reportar) sigue en `App.jsx`, sin tocarse -- el formulario solo lee `campoActivo` y llama a `marcarEnMapa`, exactamente como ya leía otros callbacks. 17 props.

`App.jsx` bajó de 2066 a 1959 líneas (-107). Se retiraron 7 imports de íconos que quedaron sin uso tras las extracciones (`WifiOff`, `MapPin`, `ArrowUpDown`, `Home`, `Save`, `Briefcase`, `LocateFixed`) y el import de `formatearAntiguedad`, todos detectados por lint, no a mano.

Verificado con `npx eslint src/` (0 errores), `npx vitest run` (93/93 en verde, sin regresiones) y `npm run build` (build de producción limpio, mismo warning preexistente de tamaño de chunk). Sin verificación visual en navegador en vivo -- misma limitación de siempre (necesita backend + PostgreSQL + auth + GPS real para Modo Viaje).

Con esto, A17 queda sin bloques pendientes de extracción conocidos. Lo que sigue abierto en `App.jsx` (~30 `useEffect` que calculan velocidad/ETA/paso activo durante la navegación, y el resto de la lógica de estado) es trabajo de otro tipo -- reorganizar cálculo, no JSX -- y no estaba dentro del alcance original de A17.
