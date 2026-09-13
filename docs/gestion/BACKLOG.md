# Backlog único — MotoSafe GBA

Actualizado: 2026-09-13. Rodo autorizó avanzar y verificar el bloque inicial de integridad, consistencia y recuperación. Los demás ítems siguen propuestos; esta lista no implica que las 63 propuestas estén implementadas.

63 ítems: 23 hallazgos y 40 oportunidades. Prioridad sugerida: P1 integridad/defensa, P2 consolidación, P3 evolución opcional. Esfuerzo relativo: S localizado, M varios componentes, L investigación/integración amplia. No son estimaciones de días. Los solapamientos se ejecutan juntos, no se suman como trabajos independientes.

Estados permitidos: propuesto → seleccionado → en curso → validado; alternativamente diferido o descartado con motivo. Para cambiar a validado, registrar evidencia y sesión en BITACORA. La prioridad no implica aprobación.

## Ejecución actual

| ID | Estado | Alcance real y evidencia |
|---|---|---|
| A05 | Validado parcialmente | El comparador calcula cobertura por trazado y por fuente. La recomendación exige 60% sobre siniestros y muestra inseguridad aparte; `sin datos` no equivale a 0%. Falta validación geográfica independiente. |
| A01 | Validado parcialmente | Contrato formal y etiquetas de interfaz dejan explícita la gravedad condicionada a un siniestro. Falta revisión con dirección académica y consistencia de todas las guías históricas. |
| A02 | En curso | Se incorporó evaluación temporal con selección y test separados, preprocesamiento ajustado sólo en train y salida reproducible. Falta ejecución real y evidencia resultante. |
| A03 | En curso | El protocolo mide faltantes por período, métricas por ausencia de edad y ablaciones demográficas. Falta ejecución y análisis de sus resultados, sin inferencias causales. |
| A04 | En curso | El protocolo calcula Brier, ECE, matriz de confusión e intervalos bootstrap. Falta evidencia real y una decisión explícita de costos/umbrales de alertas. |
| D01 | En curso | Se añadió ficha inicial del dataset de siniestros y contrato del modelo. Faltan fichas de todas las fuentes, licencia, procedencia primaria y versiones verificadas. |
| D02 | En curso | El evaluador calcula intervalo bootstrap descriptivo para F1. Faltan resultados reales y estabilidad por año/comuna con soporte suficiente. |
| A01 | Validado parcialmente | Contrato formal y etiquetas de interfaz dejan explícita la gravedad condicionada a un siniestro. Falta revisión con dirección académica y consistencia de todas las guías históricas. |
| A02 | En curso | Se incorporó evaluación temporal con selección y test separados, preprocesamiento ajustado sólo en train y salida reproducible. Falta ejecución real y evidencia resultante. |
| A03 | En curso | El protocolo mide faltantes por período, métricas por ausencia de edad y ablaciones demográficas. Falta ejecución y análisis de sus resultados, sin inferencias causales. |
| A04 | En curso | El protocolo calcula Brier, ECE, matriz de confusión e intervalos bootstrap. Falta evidencia real y una decisión explícita de costos/umbrales de alertas. |
| A06 | En curso | Los empates no se etiquetan automáticamente y la cobertura de inseguridad ya no sustituye la de siniestros. Se creó plantilla de rutas de referencia; faltan casos revisados y sensibilidad de pesos. |
| A07 | Validado parcialmente | Borrado con token privado de una sola entrega, UUID canónico, token no expuesto por GET y prueba de contrato. Quedan migración versionada, cuotas y política de votos. |
| A08 | Validado | Prensa externa pasa a nodos DOM con texto y solo enlaces `http(s)`; cubierto por revisión y build. |
| A09 | En curso | Límites de palabra, ambigüedades y pruebas de regresión. Hay plantilla/evaluador reproducible para precisión, recall, abstención y error geográfico; falta conjunto humano etiquetado y métricas reales. |
| A10 | En curso | Se eliminó la doble aplicación de lluvia y hotspots se actualizan cada cinco minutos. Se documentaron TTL y procedencia conocidos; faltan fechas de generación devueltas por backend. |
| A11 | En curso | Se documentaron unidad, procedencia, TTL y límites de cada capa; la tarjeta de ruta muestra cobertura separada por fuente. Faltan fechas diferenciadas visibles desde backend y distancia a segmentos. |
| D03 | En curso | Se agregó plantilla de rutas de referencia para cobertura parcial, empate, desvío y discordancia entre fuentes. Faltan casos independientes revisados. |
| D04 | En curso | Se definió la evidencia para variar radio/pesos; faltan corridas y reporte de sensibilidad real. |
| A12 | Validado parcialmente | Pool con máximo físico, espera acotada, rollback y prueba unitaria. `/health` reporta estado de DB sin secretos. Falta integración contra PostgreSQL real. |
| A13 | Validado | Límites de coordenadas/hora/edad y respuesta vacía de hotspots probados. |
| A14 | En curso | Se agregó `backend/migrar.py`, migración versionada y procedimiento de ejecución. Falta ejecutarla contra PostgreSQL aislado y retirar la compatibilidad DDL por request. |
| T04 | Validado parcialmente | `/health` informa servicio, disponibilidad de base y hora UTC sin datos personales. Faltan métricas de latencia/error por servicio y retención de logs. |
| T05 | Validado parcialmente | CI en GitHub valida lint, tests y build frontend, más sintaxis backend en Python 3.12. Falta corrida confirmada en GitHub e integración con PostgreSQL. |
| T06 | En curso | Procedimiento documentado de dump/restauración aislada; falta ejecutar y registrar un ensayo real. |
| A15 | Validado parcialmente | La primera carga se libera ante fallo de hotspots; las capas secundarias conservan caché, identifican cuáles fallaron, muestran última consulta y se reintentan sin recargar toda la página. Faltan estados de fecha de origen desde backend. |
| F08 | En curso | La actividad identifica reportes propios vigentes. Faltan contratos backend y pantalla para vencidos, retirados por consenso y desmentidos. |
| A16 | Validado parcialmente | Velocidad/ETA se limpian al detenerse y el progreso se proyecta sobre segmentos, evitando saltos entre vértices largos. Faltan trazas GPS reales de parada, giro, desvío, pérdida y llegada. |
| A18 | Validado parcialmente | Geocodificación exacta usa caché de cinco minutos y rechaza HTTP fallido explícitamente. Falta evaluar cuota/compatibilidad real del proveedor y persistencia controlada. |
| A17 | En curso | Se retiró la dependencia de autor de la capa de reportes del mapa; falta perfilado y separación incremental. |
| V10 | Validado parcialmente | La carga inicial no queda bloqueada; los fallos de capas enumeran la fuente y ofrecen reintento localizado sin simular éxito. Faltan mensajes específicos para sin datos y red del sistema. |
| A23 | En curso | Foco visible, zoom nativo y movimiento reducido están implementados; se agregó matriz QA. Falta ejecución real con teclado, zoom, temas y dispositivos. |
| G03 | Validado parcialmente | Matriz objetivo–evidencia–límite centralizada. Falta contrastarla con requisitos institucionales no presentes en el repositorio. |
| G04 | Validado parcialmente | Guion de demo y condiciones de reproducción documentados. Falta ensayo medido con servicios disponibles. |

## Hallazgos existentes

La evidencia y el diagnóstico completo están en [ASSESSMENT.md](../assessment_2026-09-11/ASSESSMENT.md). Los IDs conservan exactamente su significado.

| ID | Mejora / beneficio | P / esfuerzo | Dependencia | Criterio de cierre resumido |
|---|---|---|---|---|
| A01 | Definir gravedad frente a ocurrencia: promesa defendible | P1/M | Decisión de alcance | Objetivo, etiquetas y evaluación describen la misma variable. |
| A02 | Evaluación temporal independiente | P1/L | A01 | Selección y evaluación separadas; preprocesamiento y datos disponibles por fecha. |
| A03 | Medir efecto de faltantes y perfiles agregados | P1/L | A02 | Ablaciones y métricas de la unidad servida, sin conclusiones causales infundadas. |
| A04 | Calibración y costos de falsas alertas | P1/L | A02–A03 | Curvas/métricas independientes y significado explícito del score. |
| A05 | Cobertura desconocida distinta de riesgo bajo | P1/M | A01 | Ruta sin datos no recibe recomendación de seguridad. |
| A06 | Evitar duplicación de capas y corregir rankings | P1/M | A05 | Empates, pesos y etiquetas relativos probados; fuentes solapadas declaradas. |
| A07 | Autorizar borrado y proteger votos | P1/M | Política de identidad | UUID público no permite borrar; credencial privada y normalización verificadas. |
| A08 | Escape de títulos externos | P1/S | Ninguna | Marcado externo se muestra como texto; enlaces con protocolos permitidos. |
| A09 | Calidad del extractor de prensa | P1/L | Conjunto etiquetado | Casos ambiguos generan abstención; precisión y error geográfico medidos. |
| A10 | Actualizar riesgo y unificar ajustes | P1/M | A01 | Fecha/TTL reales; lluvia no duplicada; categorías separadas. |
| A11 | Mostrar procedencia e incertidumbre | P2/M | A09–A10 | Motivos conservados; fechas diferenciadas y distancia a segmentos. |
| A12 | Pool acotado y recuperación SQL | P2/M | PostgreSQL de prueba | Límite real y recuperación tras excepción demostrados. |
| A13 | Validación de entradas y tabla vacía | P2/S | Ninguna | Valores imposibles rechazados; vacío sin error del modelo. |
| A14 | Migraciones, consultas y cuotas | P2/L | A12 | Base nueva reproducible, consultas acotadas y límites de recursos. |
| A15 | Carga, error y recuperación consistentes | P2/M | A13 | Primera visita sin backend ofrece salida; 500 no simula éxito. |
| A16 | Velocidad, ETA y progreso fiables | P2/M | Trazas GPS | Detención, giro omitido y llegada probados; rápida usa duración declarada. |
| A17 | Reducir recreación de mapa y separar responsabilidades | P2/M | Perfilado | Marcadores estables y listeners liberados; mejora medida. |
| A18 | Búsqueda compatible con proveedor | P2/M | Decisión de proveedor | Servicio admite el flujo; caché y cuotas documentadas. |
| A19 | Pipeline canónico y notebook histórico seguro | P2/M | A22 | Ejecución documentada no sobrescribe inadvertidamente artefactos vigentes. |
| A20 | Limpieza geográfica común | P2/M | Diccionario de datos | Algoritmos comparan mismo universo; ceros/absurdos excluidos con registro. |
| A21 | Validar corredores y estabilidad espacial | P2/L | A20 | Geometría con procedencia y persistencia temporal comprobada. |
| A22 | Entorno y artefactos reproducibles | P2/M | Ninguna | Instalación limpia, hashes, versiones y restauración documentadas. |
| A23 | Accesibilidad y persistencia robusta | P2/M | Matriz visual | Teclado/foco/zoom y almacenamiento fallido probados. |

## Diseño visual y experiencia

V01–V14 son propuestas de diseño basadas en componentes y CSS revisados. **No son defectos visuales confirmados mediante capturas.** Conservar marca, temas, áreas seguras, capas y navegación ya existentes; validar antes/después antes de reemplazar soluciones actuales.

| ID | Propuesta y valor | P / esfuerzo | Dependencia / tradeoff | Aceptación |
|---|---|---|---|---|
| V01 | Jerarquía por modo: explorar, comparar, navegar | P2/M | A15; evita acumular paneles | En cada modo hay una acción principal y mapa visible; cambiar modo conserva contexto. |
| V02 | Unificar tamaños, espaciado, radios y sombras | P2/M | Inventario de estilos; evita rediseño arbitrario | Tokens comunes y componentes coherentes en ambos temas. |
| V03 | Mejorar tipografía y legibilidad de datos clave | P2/S | A23; puede aumentar alto de paneles | Calle, giro y ETA legibles con texto ampliado sin ocultar acciones. |
| V04 | Colores más semánticos, menos acentos simultáneos | P2/M | A01/A06 | Riesgo, selección y acción diferenciados por texto/forma además de color. |
| V05 | Panel inferior móvil con alturas controladas | P2/M | V01; propuesta frente a paneles flotantes | A 360/390 px, teclado abierto y paisaje no tapa controles esenciales. |
| V06 | Tarjetas de rutas comparables | P2/M | A05/A06/A16 | Tiempo, distancia, cobertura y ejes separados; selección visible sin promesa absoluta. |
| V07 | Detalle de zona con explicación progresiva | P2/M | A11 | Primero conclusión y fecha; fuente y método ampliables sin saturar. |
| V08 | Simplificar panel de capas | P2/S | Capas ya existen | Diferencia fondo/overlay y visualización/cálculo; estado seleccionado accesible. |
| V09 | Atenuar decoración y animación durante viaje | P2/S | A23; preservar alertas relevantes | Ruta y maniobra dominan; movimiento reducido respeta preferencias. |
| V10 | Estados vacíos y errores con acción útil | P2/S | A15 | Mensajes distinguen sin datos, sin red y fallo; ofrecen reintento adecuado. |
| V11 | Revisar contraste sobre mapas claros/satélite | P2/M | QA visual pendiente | Ruta, etiquetas y puntos distinguibles en fondos representativos. |
| V12 | Onboarding breve y ayuda reabrible | P2/S | A01/A05 | Explica cobertura y colores sin cifras rígidas; usuario puede volver a leerlo. |
| V13 | Marcadores diferenciados por origen y antigüedad | P2/M | A11 | Histórico/prensa/comunidad reconocibles sin confundir precisión con halo físico. |
| V14 | Pulir estados táctiles y transiciones | P3/S | V02/A23 | Feedback inmediato, sin saltos de layout ni dependencia exclusiva de hover. |

Dirección propuesta: mapa protagonista; marca amarilla para acciones concretas; superficies de panel uniformes; un solo panel principal por tarea; detalle secundario expandible. No se propone agregar efectos 3D decorativos: ya hay navegación orientada y primero debe validarse su utilidad.

## Funcionalidades y producto

Funciones opcionales deben justificar mantenimiento, datos y compatibilidad. Favoritos, reportes, capas, vibración y navegación ya existen: se mejora su comportamiento.

| ID | Propuesta y valor | P / esfuerzo | Dependencia / tradeoff | Aceptación |
|---|---|---|---|---|
| F01 | Preferencias explícitas entre tiempo y exposición histórica | P3/L | A04–A06; pesos necesitan validación | Usuario comprende compromiso y ningún ajuste inventa cobertura. |
| F02 | Lista y edición de favoritos con nombres propios | P3/M | A23; hoy Casa/Trabajo | Crear/renombrar/borrar sin perder coordenadas; almacenamiento validado. |
| F03 | Recientes locales y restauración de búsqueda | P3/S | A18/A23; privacidad | Historial acotado y borrable; no se envía a servidor por defecto. |
| F04 | Explicación de por qué cambia una ruta | P2/M | A10/A16 | Distingue desvío, tráfico y cambio de datos; evita recalcular en bucle. |
| F05 | Preferencias de alertas y límite de repetición | P2/M | A04/A16 | Alerta relevante no se repite por ruido GPS; audio/vibración opcionales. |
| F06 | Guía por voz opcional | P3/M | A16/F05; compatibilidad móvil | Ensayo de voces/permisos y fallback visual; sin dependencia obligatoria. |
| F07 | Mantener pantalla activa durante navegación | P3/S | Compatibilidad/permisos por verificar | Liberar al salir y mostrar fallback cuando no esté disponible. |
| F08 | Reportes con estado y gestión propios | P2/M | A07/A15 | Distingue enviado, vigente, desmentido y vencido; confirmación del servidor. |
| F09 | Modo degradado para pérdida de red | P2/L | A05/A10/A22; caché de mapas depende del proveedor | Datos guardados fechados; ruta existente consultable sin prometer ruteo offline. |
| F10 | Compartir resumen de ruta con cobertura y fecha | P3/M | A05/A06; privacidad de origen | Vista previa y elección del usuario; receptor conoce vigencia y límites. |

## Datos y valor científico

| ID | Propuesta y valor | P / esfuerzo | Dependencia / tradeoff | Aceptación |
|---|---|---|---|---|
| D01 | Ficha de cada dataset y modelo | P2/M | A01/A22 | Fuente, licencia, fechas, unidad, filtros, versiones y límites documentados. |
| D02 | Intervalos y estabilidad por año/comuna | P2/L | A02/A03; muestras mortales pequeñas | Incertidumbre publicada; no inferir igualdad por ausencia de significancia. |
| D03 | Conjunto de rutas de referencia | P2/L | A05/A06/A21 | Casos de cobertura parcial, empate y desvío etiquetados con criterio independiente. |
| D04 | Sensibilidad a radios, pesos y clustering | P2/L | A20/A21 | Reportar cuánto cambia ranking y cobertura al variar parámetros razonables. |
| D05 | Monitor de cambios en calidad de datos | P3/M | A20/A22 | Detecta cambios de esquema, faltantes y coordenadas antes de publicar artefactos. |
| D06 | Ampliar cobertura GBA con fuentes comparables | P3/L | D01/A02; disponibilidad no confirmada | Fuente verificable y evaluación separada; no extrapolar silenciosamente desde CABA. |

## Calidad técnica y operación

| ID | Propuesta y valor | P / esfuerzo | Dependencia / tradeoff | Aceptación |
|---|---|---|---|---|
| T01 | Integración real con base efímera | P2/M | A12/A14 | Esquema, permisos, transacciones y recuperación probados sin tocar base personal. |
| T02 | E2E de flujos de usuario | P2/M | A15/certificado local | Buscar/comparar/reportar/recuperar fallo reproducibles; upstream controlado. |
| T03 | Presupuesto de rendimiento móvil | P2/M | A17 | Línea base de carga, renders y memoria; objetivo acordado y medido. |
| T04 | Observabilidad sin datos personales innecesarios | P2/M | A14 | Errores por servicio, edad de datos y latencia; logs sin claves ni GPS personal. |
| T05 | Integración continua y manifiesto de entrega | P2/M | A22/T01 | Lint/tests/build automáticos; release asociada a hashes y documentación. |
| T06 | Backup y restauración ensayada | P2/M | A14/A22 | Restauración en entorno aislado y procedimiento actualizado. |

## Documentación, investigación de uso y alcance

| ID | Propuesta y valor | P / esfuerzo | Dependencia / tradeoff | Aceptación |
|---|---|---|---|---|
| G01 | Sincronizar guías, README y Word | P2/M | A01/A22/D01 | Cifras/tecnologías vigentes; versiones históricas identificadas; Word renderizado al regenerar. |
| G02 | Pruebas con usuarios mediante tareas concretas | P2/M | V01/V06 | Registrar errores y comprensión, no solo opiniones; muestra y límites explícitos. |
| G03 | Matriz objetivos académicos–evidencias | P2/M | Documentación institucional | Cada objetivo tiene implementación, prueba y límite; vacíos visibles. |
| G04 | Demo reproducible con escenarios preparados | P2/M | A19/A22/T02 | Guion, datos de prueba, fallos simulados y tiempos medidos; demo identificada como tal. |

## Qué conviene evitar por ahora

- Reescritura total o migrar framework solo por tamaño de archivos: A17 propone separación incremental.
- Agregar deep learning/LLM sin baseline ni problema medido: no resuelve A01–A04.
- Login/red social/gamificación por defecto: agrega fricción y puede incentivar reportes sin calidad; A07 no requiere necesariamente cuentas.
- App nativa, ruteo completamente offline o expansión GBA como requisito inmediato: investigar costo y necesidad antes.
- Prometer que un botón “segura” o una estética profesional demuestra reducción de riesgo.

## Referencia de accesibilidad

Usar [WCAG 2.2](https://www.w3.org/TR/WCAG22/) como referencia para contraste, teclado, foco y tamaño de objetivos. Su criterio AA de tamaño mínimo contempla 24 píxeles CSS y excepciones; proponer 44 px para controles principales del producto es una decisión de diseño, no afirmar que todo objetivo inferior incumple automáticamente. Ver [explicación oficial de tamaño mínimo](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum). La conformidad requiere evaluación, no solo inspección CSS.
