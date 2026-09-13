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
