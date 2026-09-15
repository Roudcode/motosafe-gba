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
