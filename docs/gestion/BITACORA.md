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
- Límite: PostgreSQL y Python no están disponibles en esta terminal para validación backend real.

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
