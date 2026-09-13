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
