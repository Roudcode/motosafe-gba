# Assessment integral — MotoSafe GBA

**Fecha:** 11 de septiembre de 2026. **Base revisada:** commit `c24b8a7` y archivos locales de datos y entorno. **Objeto:** evaluar implementación, datos, modelo, reproducibilidad, seguridad, experiencia de uso y evidencia para el proyecto final de Ingeniería. No se modificó el código de la aplicación.

## 1. Dictamen

MotoSafe tiene una implementación considerable y coherente como **prototipo de apoyo a decisiones**: integra datos oficiales, procesamiento geográfico, un modelo realmente serializado y utilizado por la API, reportes persistentes, noticias geolocalizadas, alternativas de ruta, tráfico y navegación. Hay decisiones razonadas, pruebas automatizadas y trabajo de interfaz. No es una maqueta con colores inventados.

Sin embargo, **no considero cerrada la parte práctica ni validada la promesa de recomendar rutas más seguras**. Los problemas principales no son agregar funcionalidades: son establecer qué estima cada indicador, corregir errores de integración y seguridad, y hacer que los resultados publicados correspondan al artefacto que se ejecuta.

Para una defensa académica, las mayores debilidades son la diferencia entre gravedad y probabilidad de ocurrencia, el uso del conjunto temporal para elegir configuraciones, la influencia de datos faltantes y el cambio entre entrenamiento individual e inferencia sobre perfiles promedio. Para uso público, sobresalen la autorización de borrado de reportes, el HTML de prensa sin escape y la interpretación de ausencia de cobertura como bajo riesgo.

**Decisión recomendada:** congelar nuevas funciones; cerrar primero los hallazgos P1 y consolidar una versión demostrable, reproducible y documentada. No hace falta rehacer toda la aplicación ni abandonar Random Forest o HDBSCAN. Sí hace falta revisar la justificación y el contrato de riesgo que conecta sus componentes.

### Estado por dimensión

| Dimensión | Evaluación |
|---|---|
| Implementación funcional | Avanzada; integración extensa, con fallos concretos de actualización, navegación y manejo de errores. |
| Datos | Volumen suficiente para experimentación; cobertura CABA, faltantes importantes y limpieza geográfica desigual entre pipelines. |
| Modelo | Carga y predice; utilidad operativa y calibración probabilística todavía no demostradas. |
| Clustering | Resultados cuantificados y mejora de asignación histórica; falta validación temporal/espacial de utilidad. |
| Seguridad | Insuficiente para exposición pública con reportes habilitados. |
| Reproducibilidad | Parcial: hay scripts, semillas y dependencias fijadas, pero el notebook y el arranque desde cero presentan obstáculos. |
| Calidad y pruebas | Buena base de pruebas unitarias; faltan integración con PostgreSQL y escenarios completos de usuario. |
| Documentación | Abundante y explicativa; desactualizada respecto de la implementación y los artefactos actuales. |
| Preparación de defensa | Buen material de base; requiere cerrar metodología, trazabilidad y evidencia de validación. |

No se asigna un porcentaje de avance: no hay una rúbrica institucional ni criterios de aceptación completos disponibles para calcularlo.

## 2. Alcance y método

Se inventariaron **84 archivos versionados**, y los archivos locales de `data/`. Se revisaron el código propio de backend y frontend, configuración, scripts de operación, scripts de análisis, notebook, pruebas y documentación. Se perfilaron íntegramente los **16 CSV** de `data/`, se inspeccionaron el modelo y sus columnas, y se compararon hashes de las copias de los artefactos. Se extrajo el contenido textual de los seis DOCX y se contrastaron sus afirmaciones técnicas con código y datos.

Los paquetes de `node_modules`, el entorno `venv`, cachés, objetos internos de Git y bundles generados se trataron como dependencias o productos de compilación: no se hizo revisión manual de cada línea de código de terceros. Se comprobaron versiones, compilación y avisos de npm. No se leyeron ni publicaron valores secretos de `.env`. Los recursos gráficos se inventariaron; no constituyen una auditoría de diseño visual. Los DOCX se revisaron por contenido, no mediante certificación de su maquetación página por página.

**Evidencia adjunta:**

- `inventario.csv`: archivo, tamaño y SHA-256 de los archivos versionados y datos locales.
- `evidencias.json`: perfiles de datos, modelo, métricas reconstruidas, verificaciones aisladas y texto extraído de DOCX.
- `auditar.py`: auditoría reproducible de solo lectura; no entrena, no ejecuta el scraper contra medios y no escribe en PostgreSQL. Las comprobaciones HTTP utilizan mocks donde interviene la base o el clima.

Se distinguen tres tipos de evidencia: **ejecutada**, cuando se reprodujo localmente; **estática**, cuando la conclusión deriva del código; y **pendiente**, cuando requiere servicios, dispositivos o nuevos experimentos. Un resultado con mocks no se presenta como una prueba real de TomTom o PostgreSQL.

### Comprobaciones ejecutadas

| Comprobación | Resultado |
|---|---|
| Backend: `python -m pytest -q -p no:cacheprovider`, desde `backend/` | **45 pruebas aprobadas**, 14,54 s; 1.200 avisos de deprecación de joblib/NumPy. |
| Frontend: `npm run lint` | Aprobado. |
| Frontend: `npm run build` | Aprobado; aviso por tamaño del bundle. |
| Frontend: `npm test` | Falló el lanzador local: `vitest` no reconocido. |
| Frontend: `node node_modules/vitest/vitest.mjs run` | **71 pruebas aprobadas**, tres archivos, 935 ms. Confirma que la suite funciona, aunque el comando habitual requiere reparar la instalación local. |
| `npm audit --json` contra el registro npm | **0 vulnerabilidades reportadas**, 203 dependencias contabilizadas. Esto no cubre fallos del código propio ni dependencias Python. |
| Sintaxis de Python propio en backend/notebooks | 23 archivos `.py` parsean correctamente. |
| Sintaxis del notebook | Error de sintaxis en la quinta celda; además hay obstáculos de ejecución descritos abajo. |
| Cuatro pares de artefactos `data/`–`backend/` | Coinciden byte a byte. |
| Modelo guardado | Se deserializa y predice con el entorno instalado. |
| Frontend en navegador | Vite inició en `127.0.0.1:5173`; el navegador rechazó el certificado HTTPS local (`ERR_CERT_AUTHORITY_INVALID`). Sin validación visual completa. |

No se ejecutaron un reentrenamiento completo, los barridos costosos, una recarga de tablas, un recorrido GPS real, pruebas de carga ni un pentest. Tampoco se verificó disponibilidad actual de cada medio del scraper. El entorno de desarrollo HTTPS y la suite con mocks no acreditan un despliegue productivo.

## 3. Qué existe realmente

El frontend utiliza **React 19, Vite 8 y MapLibre GL 6**, no Leaflet. La API es FastAPI con acceso directo a PostgreSQL mediante psycopg2; PostGIS forma parte de la infraestructura, aunque buena parte del cálculo espacial se realiza en Python/JavaScript.

El backend expone hotspots viales, predicción puntual, corredores, dos capas de inseguridad, reportes colaborativos y de prensa, tiles de tráfico y rutas TomTom. El modelo es un **RandomForestClassifier de 300 árboles**, profundidad máxima 12, mínimo de cinco muestras por hoja y `class_weight='balanced_subsample'`. Tiene **55 columnas de entrada**. Los archivos finales están efectivamente integrados a la API.

El scraper configura **19 fuentes**, distribuidas entre varias estrategias de extracción. Contarlas no demuestra que las 19 estén entregando noticias válidas hoy. La implementación tiene más cobertura funcional que la descripción antigua de “16 fuentes”.

### Datos observados

| Archivo / conjunto | Cantidad actual | Observación |
|---|---:|---|
| Hechos viales originales | 65.818 | Datos hasta el 31/12/2025; 3.031 coordenadas no convertibles o ausentes. |
| Víctimas originales | 75.197 | Relación uno a muchos con hechos; 1.439 filas completamente repetidas, cuya semántica requiere revisar antes de eliminar. |
| Siniestros de moto limpios | 23.343 | 21.756 leves, 1.304 graves, 283 mortales. |
| Filas disponibles para modelado | 23.338 | Se excluyen cinco filas sin hora; 21.756 leves, 1.300 graves, 282 mortales. |
| Hotspots viales | 740 | Agrupan 17.651 registros; 5.692 quedan como ruido. |
| Contextos por hotspot | 740 | Sin nulos en el archivo final. |
| Corredores | 243 | Archivo de candidatos y archivo de geometrías con 243 filas cada uno. |
| Delitos originales | 1.387.622 | Años 2016–2025; distintas ventanas según procesamiento. |
| Hotspots de inseguridad general | 633 | Resultado actual HDBSCAN; documentación conserva 303/DBSCAN. |
| Hotspots de inseguridad con moto | 502 | Total inseguridad actual: **1.135**, no 805. |
| Índices de inseguridad | 15 | Una fila por comuna. |
| Clima horario | 67.296 | 01/01/2019–04/09/2026, sin nulos o duplicados en este archivo. |
| Prototipos H3 | 1.517 / 2.570 / 1.172 | Celdas viales / delito general / delito con moto; no son los hotspots servidos por la API. |

Los hotspots viales asignan el **75,62% de los registros históricos**; el mayor agrupa 95 siniestros, 0,41% del total. Es una medida de asignación de datos, no de porcentaje del territorio cubierto ni de precisión predictiva.

En delito general, 205.110 registros agrupados sobre 408.241 elegibles dan **50,24%**. El 49,8% que aparece en otros resultados usa un denominador distinto, que incluye coordenadas cero. Con moto: 11.707 sobre 15.759, **74,29%**. Deben compararse algoritmos usando exactamente el mismo universo y filtros.

## 4. Hallazgos prioritarios

**P1:** resolver antes de sostener resultados centrales o habilitar uso público. **P2:** resolver para una demo estable y un proceso reproducible. **P3:** mejora posterior. No se usa P0 porque no se acreditó una emergencia activa en un servicio público.

### A01 — P1 — La variable objetivo no es la probabilidad de sufrir un siniestro

**Evidencia estática:** `notebooks/reentrenar_modelo.py`, función `entrenar`; `backend/main.py`, inferencia de hotspots. El objetivo es `gravedad_siniestro` entre registros donde ya ocurrió un hecho. No hay viajes sin accidente, exposición vehicular ni kilómetros recorridos como denominador.

El modelo estima gravedad condicionada al contexto de un siniestro registrado. No estima directamente la probabilidad de que un motociclista choque al recorrer un tramo. El clustering incorpora concentración histórica, pero la cantidad de hechos no se convierte por eso en probabilidad de ocurrencia dentro del Random Forest.

**Consecuencia:** afirmar “esta ruta reduce tu probabilidad de accidente” excede la evidencia. También son insuficientes las conclusiones causales sobre edad, clima o comuna basadas exclusivamente en importancias del modelo.

**Cierre:** definir formalmente el objetivo, presentar la salida como indicador de gravedad/concentración histórica según corresponda y validar por separado la utilidad de ordenar rutas. Para estimar incidencia harían falta datos y diseño adicionales.

### A02 — P1 — El conjunto temporal dejó de ser una prueba final independiente

**Evidencia estática:** `tuning_rf2.py` compara seis configuraciones directamente contra 2025; `reentrenar_modelo.py` documenta esa selección y guarda un modelo con split aleatorio 80/20. `validar_temporal.py` todavía utiliza 200 árboles y `balanced`, distinto del artefacto actual de 300 árboles y `balanced_subsample`.

Seleccionar hiperparámetros observando resultados de 2025 convierte ese período en validación. Llamarlo “nunca visto” para una evaluación final induce a error. A esto se suma la imputación de edad antes de dividir y un índice agregado de inseguridad de años recientes aplicado retrospectivamente a filas antiguas. Este último es contexto disponible hoy, pero no era necesariamente información disponible al predecir en la fecha histórica.

**Cierre:** un único pipeline con preprocesamiento ajustado en entrenamiento; selección interna temporal; evaluación exterior intacta o validación temporal anidada; features con fecha de disponibilidad; configuración y hash del modelo asociados al informe. Separar claramente evaluación retrospectiva de simulación prospectiva. Véase la [guía oficial de scikit-learn sobre fuga de información](https://scikit-learn.org/stable/common_pitfalls.html).

### A03 — P1 — La señal de datos faltantes es muy fuerte y cambia en inferencia

**Evidencia ejecutada:** la edad está ausente en 9.271/21.756 leves (**42,61%**), 15/1.300 graves (**1,15%**) y 8/282 mortales (**2,84%**). `sexo_victima_SD` aparece en 7.655 leves, diez graves y un mortal. Las dos mayores importancias individuales del modelo son `edad_desconocida` (0,1171) y `sexo_victima_SD` (0,0979).

Esto es evidencia de asociación con el mecanismo de registro; no prueba por sí solo una fuga directa del target. Sí impide atribuir sin más la mejora a “quién conduce”. Las importancias por impureza tampoco equivalen a efectos causales.

**Evidencia estática:** `backend/main.py:399` y `:986` fijan `edad_desconocida=0` y utilizan perfiles agregados por zona. Entrenar sobre víctimas individuales y consultar luego una edad promedio con sexo/contraparte modal no garantiza conservar el comportamiento evaluado.

**Cierre:** ablación con/sin indicadores de faltantes y demografía, métricas separadas por disponibilidad y año, y evaluación de la unidad realmente servida: hotspot/perfil agregado. Definir explícitamente qué significa un perfil genérico.

### A04 — P1 — Los porcentajes de clase y los percentiles de riesgo no están calibrados como probabilidad operativa

El modelo usa ponderación de clases. `predict_proba` no acredita por sí solo calibración respecto de las frecuencias reales. Los cortes sobre `2*p(MORTAL)+p(GRAVE)` generan categorías del indicador; **calibrar esos cortes por percentiles no es calibrar probabilidades**. Los corredores tienen su propia referencia, lo que también requiere explicitar qué es comparable entre capas.

**Cierre:** evaluar curvas de calibración y métricas probabilísticas sobre datos independientes, justificar costos de error y medir carga de falsas alertas. No presentar el score ponderado como una probabilidad, ya que puede superar uno. La [documentación oficial de calibración de scikit-learn](https://scikit-learn.org/stable/modules/calibration.html) distingue estas cuestiones.

### A05 — P1 — Falta de cobertura puede convertirse en una ruta “segura”

**Evidencia estática:** `frontend/src/utils/riesgoRuta.js`, `calcularRutasConScore`; `App.jsx:1609`. Una ruta sin zonas cruzadas recibe score cero y nivel bajo. Las capas históricas verificadas son de CABA; poder trazar rutas o mostrar noticias del conurbano no aporta automáticamente cobertura histórica equivalente.

Además, las noticias o reportes fuera de los hotspots existentes no crean por sí mismos nuevas zonas históricas puntuadas. Es posible favorecer una alternativa porque recorre territorio sin datos. El problema también aparece si una capa no cargó correctamente.

**Cierre:** máscara de cobertura por fuente, estado “sin datos suficientes”, porcentaje de trayecto evaluado y exclusión de recomendaciones de seguridad cuando la comparación no tiene cobertura equivalente.

### A06 — P1 — El score mezcla capas solapadas y las etiquetas relativas pueden ocultar riesgo

`unificarZonasInseguridad` suma delito general y delito con moto aunque esta última población se solape con la primera. Ser capas distintas no las vuelve evidencia independiente. Usar categorías ordinales comunes tampoco demuestra que los pesos 1/2/3/5 sean comparables entre tipos de riesgo.

En `nivelRelativoEnLote`, tres scores iguales y positivos reciben todos nivel bajo: `indexOf` devuelve el primer puesto para los tres. La mejor alternativa de un conjunto muy riesgoso también puede etiquetarse como baja. La interfaz muestra “segura” o “recomendada” sin que esa categoría sea una medida absoluta validada.

**Cierre:** evitar duplicación o declarar y validar su ponderación; separar riesgo vial e inseguridad; distinguir “menor score entre estas alternativas” de “riesgo bajo”; definir empates y cobertura. Medir sensibilidad de la recomendación ante cambios razonables de pesos y radios.

### A07 — P1 — Cualquiera que lee reportes puede obtener la credencial usada para borrarlos

**Evidencia estática directa:** `backend/main.py:648` devuelve `autor_id`; `:683–695` autoriza el DELETE únicamente mediante ese mismo UUID. Validar su formato no demuestra titularidad. No hace falta adivinarlo: está en la respuesta pública.

Los votos tampoco acreditan personas independientes: se pueden generar nuevos UUID, y las representaciones textuales equivalentes de un UUID no se normalizan antes de utilizarlas como identidad. Esto debilita tanto el bloqueo de autovoto como el criterio de ocultar un reporte por desmentidas.

**Cierre:** separar identificador público de una credencial privada verificable por servidor para borrar; normalizar UUID; definir una política de abuso para votos. Es posible conservar el alcance sin cuentas de usuario, pero no usar un identificador expuesto como autorización.

### A08 — P1 — HTML externo de prensa se inserta sin escape

**Evidencia estática:** `frontend/src/components/MapaMotoSafe.jsx:800–803` interpola `rep.fuente` y `rep.titular` en `.setHTML`. El scraper procesa contenido externo y decodifica entidades HTML. Existe una vía de inyección de contenido y potencial XSS almacenado si llega marcado malicioso al título. No se explotó contra datos reales.

**Cierre:** crear nodos y asignar `textContent`/`setDOMContent`, o sanitizar con una política explícita si realmente se requiere HTML. Validar protocolos de enlaces. Agregar un caso con título que contenga marcado y verificar que se vea como texto.

### A09 — P1 — La extracción geográfica y temática produce falsos positivos reproducibles

**Evidencia ejecutada con textos sintéticos, sin geocodificación externa:**

| Entrada | Resultado del extractor |
|---|---|
| “Robaron en San Martin de los Andes” | San Martín, Buenos Aires. |
| “Robaron flores en una casa de Quilmes” | Flores, CABA. |
| “Choque en San Martin y Belgrano, Moron” | Intersección ubicada en Belgrano, CABA, precisión de 80 m. |
| “Aprobo el examen en Palermo” | Categoría robo por coincidencia de subcadena. |

No se deduce de estos ejemplos una tasa global de error; sí prueban fallos de las reglas actuales. Como las noticias pueden elevar niveles de riesgo, una ubicación equivocada ya no es solo un marcador incorrecto.

**Cierre:** respetar localidad explícita antes que nombres ambiguos, límites de palabra, detección de lugares homónimos, abstención ante ambigüedad y un conjunto manual de titulares etiquetados. Medir precisión temática y error geográfico por nivel declarado antes de usar prensa para modificar riesgo.

### A10 — P1 — Riesgo “en vivo” sin actualización periódica exitosa y lluvia contada dos veces

**Evidencia estática:** `App.jsx:361–490` carga hotspots al montar y solo reintenta cada cinco segundos cuando hubo error. Tras éxito no refresca periódicamente esas predicciones. Corredores, inseguridad y clima del frontend también se cargan una vez. Reportes cada 30 segundos y prensa cada diez minutos sí se actualizan.

El backend ya incluye lluvia en la inferencia y `geoRiesgo.js:111–122` vuelve a subir un nivel por lluvia. Cualquier categoría de reporte cercano también eleva el riesgo vial, incluidos robos. No hay evidencia de validación de esa composición.

**Cierre:** definir un contrato único de riesgo base y ajustes; calcular lluvia en un solo lugar o justificar empíricamente ambos efectos; separar categorías; devolver fecha de cálculo, fuentes y motivos. Refrescar según un TTL explícito y mostrar datos vencidos como tales.

### A11 — P2 — La explicación del ajuste de prensa se pierde y su incertidumbre no se propaga

`App.jsx:369–381` descarta `ajustado_por_reciente` y `motivo_ajuste` al mapear hotspots. El usuario puede ver un nivel modificado por noticias como si fuera únicamente resultado del modelo.

`backend/main.py:813` selecciona noticias por `creado_en` y aplica un radio fijo de 600 m; no toma `radio_metros` ni `nivel_precision` para ese cálculo. La fecha de incorporación no necesariamente es la del incidente. El ajuste de corredores utiliza vértices, no distancia a segmentos; puede omitir un hecho próximo al medio de un tramo. También elige el mayor recuento local por vértice, no la unión de reportes ni necesariamente el más reciente de todo el corredor.

**Cierre:** conservar procedencia y fechas; distinguir publicación/incorporación/incidente; usar incertidumbre para aceptar o abstenerse de ajustar; distancia a segmento y deduplicación por noticia. El halo visual en píxeles es una convención documentada: no debe interpretarse como un radio geográfico exacto.

### A12 — P2 — El pool no limita conexiones simultáneas y no restablece transacciones

**Evidencia ejecutada:** un pool `maxsize=2` permitió cinco préstamos consecutivos abriendo cinco conexiones. `backend/main.py:38–58` limita la cola de conexiones libres, no el total prestado. El comentario que promete diez simultáneas es incorrecto.

`putconn` no hace rollback ni descarta una conexión con transacción abortada. Los lectores realizan SELECT y devuelven conexiones sin cierre explícito de transacción; ante una excepción pueden reutilizar estado inválido.

**Cierre:** pool con límite real, timeout de adquisición, rollback garantizado y cierre en el ciclo de vida de la app. Probar agotamiento, excepción SQL y recuperación con PostgreSQL real. Mantener una implementación para no cambiar mocks no es una justificación suficiente de su corrección.

### A13 — P2 — Entrada inválida y base vacía no se manejan consistentemente

**Evidencia ejecutada:** `/predecir` aceptó hora 99 y edad −50 con HTTP 200. `ReporteNuevo` aceptó latitud/longitud 999. Con tabla de hotspots vacía, el endpoint llega al modelo y falla con una matriz de cero muestras; corredores sí contempla vacío.

**Cierre:** límites numéricos y geográficos en la API, política explícita para categorías desconocidas y contrato estable de ausencia de datos. Comprobar que un reporte inválido no pueda interrumpir el renderizado del mapa.

### A14 — P2 — Operación de base y protección de recursos incompletas

Se ejecuta DDL de aseguramiento de tablas y ALTER en caminos de consulta; eso agrega trabajo y posibles bloqueos. Hay lecturas de reportes completas con filtrado temporal posterior en Python, sin una estrategia clara de índices y paginación. Los loaders reemplazan datos, pero no existe una migración integral versionada que prepare todas las tablas desde cero; `cargar_hotspots.py` supone `hotspots_riesgo` existente.

El rate limiting es útil pero parcial: `/corredores` y `/trafico/tiles/{z}/{x}/{y}.png` tienen costo y no reciben la misma protección. Tampoco hay validación completa de coordenadas de tiles. Los límites en memoria deben revisarse cuando haya múltiples procesos y proxy inverso.

**Cierre:** migraciones, consultas acotadas e índices medidos; protección de endpoints costosos; límites de upstream; readiness real y métricas de errores/latencia. No basta con que `/` conteste para acreditar disponibilidad de base y artefactos.

### A15 — P2 — Primera carga puede quedar bloqueada indefinidamente

**Evidencia estática:** `primeraVezListo` pasa a verdadero solo al cargar hotspots correctamente o disponer de caché. `LoadingScreen` permanece encima con z-index 2000, por sobre el aviso de backend. Un usuario nuevo con backend caído puede quedar en “Calculando riesgo en vivo” sin salida útil.

Los fetch principales no tienen timeout explícito; una respuesta HTTP fallida de reportes se transforma en `[]`, borrando visualmente los reportes previos, aunque el comentario prometa conservarlos. El DELETE actualiza la interfaz sin comprobar `r.ok`. Los votos incrementan contadores optimistas sin representar correctamente cambios de voto o fallos hasta el siguiente refresco.

**Cierre:** estados separados de carga/error/vacío/datos vencidos, reintento visible y verificaciones HTTP consistentes. Probar primera visita sin backend, 500 posterior y recuperación.

### A16 — P2 — Velocidad y elección de ruta rápida pueden ser engañosas

**Evidencia estática:** `App.jsx:657` solo actualiza velocidad si es mayor a 0,5 m/s; si el vehículo se detiene conserva la lectura anterior. Una rama sin heading ni brújula retorna antes de actualizar velocidad. Eso también afecta la ETA calculada a partir de velocidad instantánea.

`idxMasRapida` usa `min` sin tráfico aunque la respuesta contiene `eta_trafico`. Es una decisión explícita en README, pero la etiqueta “rápida” no comunica esa distinción. El avance de instrucciones basado en proximidad a un punto puede perder maniobras entre fixes; el progreso por vértice más cercano también necesita validación en curvas, bucles y calles paralelas.

**Cierre:** representar velocidad cero/desconocida, comparar duración acorde a la etiqueta y usar progreso sobre segmentos con tolerancia a precisión GPS. Reproducir trazas grabadas: detenido, giro omitido, desvío, retorno y llegada. No se verificó conducción real durante esta auditoría.

### A17 — P2 — Recreación innecesaria de marcadores y deuda de componentes

`App.jsx` concentra aproximadamente 1.875 líneas; `MapaMotoSafe.jsx`, 1.040; `backend/main.py`, 1.350. El tamaño no demuestra un fallo por sí solo, pero mezcla responsabilidades y dificulta probar flujos.

`votarReporte` se crea en cada render y se pasa al mapa. Su efecto de reportes depende de ese callback (`MapaMotoSafe.jsx:780`), por lo que puede destruir/recrear marcadores aunque los reportes no cambien. El contador de segundos provoca renders frecuentes del padre. Los listeners de capas de ruta tampoco tienen una retirada simétrica clara al retirar capas.

**Cierre:** estabilizar callbacks, separar efectos y liberar listeners; medir con profiler. Extraer carga de datos, reportes, rutas y navegación según responsabilidades. El build produce JS de **1.284,74 kB** (354,63 kB gzip) y CSS de 123,53 kB; evaluar carga diferida del mapa/paneles después de corregir comportamiento.

### A18 — P2 — Autocompletado incompatible con el servicio público Nominatim

`useSugerenciasDireccion.js` lanza búsquedas mientras se escribe con debounce de 400 ms. La [política oficial del servicio público Nominatim](https://operations.osmfoundation.org/policies/nominatim/) prohíbe el autocompletado y establece límites para el uso agregado de la aplicación. Debounce y AbortController son útiles para UX, pero no resuelven esa incompatibilidad.

**Cierre:** proveedor que admita autocompletado, instancia propia o búsqueda explícita compatible con el servicio elegido. Centralizar caché y presupuesto de consultas; revisar también geocodificación periódica del scraper. No se hizo una evaluación legal general de proveedores.

### A19 — P2 — El notebook no constituye un pipeline ejecutable de punta a punta

**Evidencia ejecutada/estática:** quinta celda con `print(...)hechos_geo = ...` concatenado; la siguiente intenta convertir coordenadas `SD` mediante `astype(float)`; otra celda contiene `fi` aislado. La corrección posterior de coordenadas no salva una ejecución que ya se detuvo antes.

Además conserva entrenamiento y clustering anteriores que escriben los mismos nombres de artefactos. Arreglar únicamente la sintaxis y seguir el “Run All” del manual puede reemplazar resultados HDBSCAN/modelo final por versiones antiguas.

**Cierre:** marcar el notebook histórico como exploración no publicadora o actualizarlo; pipeline canónico no interactivo; salidas por versión y promoción explícita al backend. Arranque desde cero en una copia de trabajo y comparación de manifiestos, sin sobrescribir el modelo vigente.

### A20 — P2 — Limpieza y comparación geográfica no son uniformes

En delitos hay 27.986 coordenadas ausentes, 6.500 pares cero/cero y doce coordenadas adicionales fuera de un bounding box amplio del área. Algunos valores son desproporcionados respecto de coordenadas terrestres. Los centroides de producción inspeccionados permanecen dentro del área, por lo que no se atribuye automáticamente el problema al mapa servido.

Sí hay impacto concreto en el preview H3 general: una celda próxima al origen geográfico acumula **3.463 hechos**. Ese pipeline no elimina ceros igual que los otros; las comparaciones H3/Gi*/KDE/HDBSCAN no parten siempre de idénticos registros.

**Cierre:** validación geográfica compartida antes de cualquier método, reporte de exclusiones y denominador único. No eliminar automáticamente filas repetidas de delitos o víctimas sin reconstruir la semántica e identificadores originales.

### A21 — P2 — Corredores y clustering necesitan validación de interpretación

`fetch_corredores_geometria.py` pide geometría OSRM entre extremos; una ruta entre extremos puede desviarse de la avenida nominal. El fallback recto no queda inequívocamente distinguido como geometría estimada en el producto.

La mejora de cobertura y el control del cluster máximo son buenos criterios exploratorios, pero no prueban que todos los clusters representen peligro persistente. “Ruido” de HDBSCAN no significa que esos siniestros sean aleatorios o carezcan de patrón. Cantidad por cluster tampoco es densidad sin normalizar área, ni riesgo individual sin exposición.

**Cierre:** verificar corredores sobre red vial, guardar fuente/calidad de geometría; estabilidad temporal y de parámetros de clustering; revisar muestras y validar persistencia fuera del período utilizado para construirlos.

### A22 — P2 — Reproducibilidad del entorno y despliegue incompletos

`requirements.txt` fija varias dependencias directas pero no todo el entorno científico observado; `h3` no está instalado pese a existir un prototipo que lo requiere. El entorno actual presenta avisos de incompatibilidad futura entre joblib y NumPy 2.5.2. El README recomienda Node 18, mientras el Vite instalado requiere `^20.19.0 || >=22.12.0`.

Hay artefactos copiados correctamente hoy, pero no un manifiesto de ejecución con hashes de entradas, commit, configuración, split y métricas que explique de manera verificable su procedencia. La persistencia de pickle exige mantener compatibilidad y cargar únicamente artefactos confiables.

Docker Compose prepara base de desarrollo; no equivale a empaquetar backend y frontend para producción. Los scripts de inicio/túnel y la configuración Vite sirven a desarrollo. Antes de hosting se necesitan configuración de red, secretos, backup/restauración, proceso supervisado y HTTPS válidos para ese despliegue.

**Cierre:** instalación limpia reproducible, dependencias de experimentación separadas, migraciones completas, manifiesto y prueba de restauración. Se ejecutó auditoría npm; **no se completó escaneo de vulnerabilidades Python**, por lo que no se afirma que estén libres de avisos.

### A23 — P2/P3 — Accesibilidad y estados persistidos requieren pruebas específicas

Las sugerencias usan `onMouseDown` en botones y no una activación equivalente de teclado. Hay controles basados en divs, diálogos sin gestión completa de foco y estados visuales sin semántica equivalente. La página restringe zoom, y no se encontró tratamiento de movimiento reducido. Son observaciones de código, no un certificado de incumplimiento obtenido mediante auditoría instrumental.

Hay trabajo positivo en áreas seguras, orientación, temas y algunos targets de 44 px. Debe verificarse con teclado, lector de pantalla, texto ampliado y dispositivos reales. Varias escrituras directas en localStorage pueden lanzar excepciones aunque exista un wrapper defensivo; los valores JSON válidos tampoco se validan siempre por estructura.

**Cierre:** controles semánticos, activación por teclado, foco y zoom; esquema para datos persistidos y fallback ante almacenamiento no disponible. El manifest por sí solo no acredita navegación offline: no hay un service worker que resuelva caché integral de aplicación/mapa.

## 5. Qué dicen las métricas del artefacto guardado

Se reconstruyó el split estratificado 80/20 con semilla 42 que declara el script, sobre las 23.338 filas actuales, y se aplicó **el modelo guardado sin reentrenarlo** a las 4.668 filas de esa partición.

**Límite importante:** es una reconstrucción del split declarado, no una prueba independiente ni una certificación de qué filas vio originalmente ese pickle. Sirve para contrastar el artefacto con su pipeline actual; no corrige los problemas metodológicos A02/A03.

| Clase | Precision | Recall | F1 | Casos |
|---|---:|---:|---:|---:|
| GRAVE | 0,111 | 0,735 | 0,192 | 260 |
| LEVE | 0,984 | 0,613 | 0,755 | 4.352 |
| MORTAL | 0,116 | 0,482 | 0,187 | 56 |
| Macro | 0,404 | 0,610 | **0,378** | 4.668 |

Accuracy: **0,618**. La clase mayoritaria representa alrededor del 93,2%; por eso accuracy aislada es una mala medida de utilidad para este caso. Tampoco sería correcto rechazar el modelo solo por perder contra esa referencia en accuracy: la referencia no detectaría graves ni mortales.

Matriz de confusión, filas reales y columnas predichas:

| Real / predicha | GRAVE | LEVE | MORTAL |
|---|---:|---:|---:|
| GRAVE | 191 | 37 | 32 |
| LEVE | 1.511 | 2.667 | 174 |
| MORTAL | 23 | 6 | 27 |

El modelo recupera una proporción relevante de graves, pero aproximadamente **nueve de cada diez predicciones GRAVE o MORTAL no pertenecen a esa clase específica** en esta reconstrucción. Algunas confusiones son entre grave y mortal, no todas falsas alarmas de cualquier severidad. La utilidad de alertar depende de frecuencia de avisos, costo de error y habituación del usuario, que no se midieron.

No hay evidencia suficiente para decir que el modelo está “validado para GBA”, que reduce incidentes o que sus porcentajes sean probabilidades calibradas de un viaje. Sí hay una base experimental medible sobre la cual continuar.

## 6. Documentación y defensa académica

La documentación tiene valor: explica decisiones, reconoce baja precisión y cobertura CABA, describe limitaciones y conserva una bitácora extensa. **Sí existe backlog**, al final del README. No corresponde afirmar que falta por completo la gestión del proyecto.

El problema es su sincronización. Deben corregirse o fecharse como históricos:

| Afirmación/documentación | Estado actual comprobado |
|---|---|
| Leaflet / react-leaflet-cluster | MapLibre GL. |
| 805 hotspots de inseguridad; general DBSCAN pendiente | 1.135; general 633/HDBSCAN en los archivos y script actuales. |
| 66 columnas del modelo final | 55 columnas del pickle actual. |
| Modelo #3 histórico y métricas asociadas | Configuración final distinta; publicar métricas y hash de cada versión. |
| Cortes de `nivel_desde_probabilidades` | La implementación vigente utiliza otro mecanismo de score/cortes. |
| Datos hasta septiembre de 2025 | Los archivos revisados incluyen diciembre de 2025. |
| 23.343 filas entrenadas | 23.338 disponibles tras excluir hora faltante. |
| Temporal 2025 “nunca visto” | Se utilizó para comparar configuraciones. |
| Inseguridad como extensión futura en `docs/9...` | Ya integrada; redefinir qué queda efectivamente como futuro. |
| “Quién aporta más” confirmado | Requiere separar efecto demográfico del mecanismo de faltantes. |
| “Run All” como recuperación universal | Notebook actual no ejecutable y con salidas históricas superpuestas. |

No se encontraron en esta carpeta los capítulos formales completos de tesis, reglamento institucional, actas ni `claude/bitacora-motosafe.md`. La ausencia local no demuestra que no existan en otra ubicación. Sin esos materiales no puede certificarse cumplimiento formal de todos los objetivos de la carrera.

### Evidencias mínimas para la defensa

1. Matriz objetivo–requisito–implementación–prueba–resultado–limitación.
2. Diagrama de arquitectura actualizado y diccionario de datos, incluida semántica oficial de `uso_moto`: no equiparar automáticamente participación de una moto con robo a motociclistas.
3. Pipeline canónico, manifiesto de artefactos y demostración de reconstrucción desde datos disponibles.
4. Informe de evaluación temporal/espacial con configuración exacta, baseline, intervalos de incertidumbre y ablaciones.
5. Explicación de cada score y evidencia de sensibilidad/validación de rutas; separar algoritmo de predicción y reglas de negocio.
6. Protocolo de pruebas de usuario y navegación con resultados observados, incluyendo fallos y cobertura limitada.
7. Backlog depurado con prioridad, responsable, aceptación y evidencia; mantener el historial real sin fabricar actas retrospectivas.

## 7. Cobertura por archivo y subsistema

El inventario adjunto enumera cada archivo y su hash. Esta tabla indica el tratamiento y los hallazgos asociados; evita confundir inventariar un binario con revisar manualmente su implementación.

| Archivos / conjunto | Revisión y conclusión |
|---|---|
| `backend/main.py` | Endpoints, validación, SQL, pool, inferencia, caché, ajustes, contratos y servicios; A01–A04, A07, A11–A14. |
| `backend/scrapear_noticias_robos.py` | Estrategias, clasificación, ubicación, persistencia y fechas; ejemplos aislados A09/A11. Sin scraping completo. |
| `backend/cargar_hotspots.py`, `cargar_corredores.py`, `cargar_hotspots_inseguridad.py` | Lecturas, reemplazo de tablas y contratos; A14/A22. No se ejecutaron escrituras. |
| `backend/tests/test_main.py`, `tests/__init__.py` | Lectura y ejecución: 45 pruebas; mocks no acreditan integración real. |
| Cuatro artefactos de `backend/` | Deserialización/perfilado y comparación con copias de `data/`; parámetros y métricas en JSON. |
| `frontend/src/App.jsx` | Estado, fetch, rutas, GPS, reportes, persistencia y composición; A05–A06, A10–A11, A15–A17, A23. |
| `MapaMotoSafe.jsx` | Fuentes/capas, marcadores, eventos, navegación, popups; A08/A17. |
| `CapasPanel`, `LoadingScreen`, `Onboarding`, `ThemeToggle` | Flujos, semántica y ciclo de vida; A15/A23. |
| `geoRiesgo`, `riesgoRuta`, `tiempo`, `storage`, `ui`, `constants` | Fórmulas, unidades, reglas, formatos, geocodificación y configuración; A05–A06, A10, A16/A18/A23. |
| Dos hooks y tres archivos `.test.js` | Actualización/debounce y cobertura de funciones puras; 71 pruebas aprobadas. |
| `App.css`, `index.css`, `main.jsx`, `index.html`, manifest, SVG/PNG | Código de estilo/entrada y metadatos revisados; assets inventariados. Sin QA visual completa por certificado. |
| `package.json`, lockfile, ESLint, Vite, README y ejemplos frontend | Build/lint, versiones, auditoría npm, configuración de desarrollo; A18/A22. |
| `01_eda_hotspots_moto.ipynb` | Celdas, narrativa y salidas; parseo de código y obstáculos Run All; A19. |
| `reentrenar_modelo`, `validar_temporal`, `tuning_rf`, `tuning_rf2`, `calibrar_umbrales_riesgo` | Objetivo, splits, selección, features y traducción de scores; A01–A04. |
| `reclusterizar_hotspots`, `identificar_hotspots_inseguridad`, `sweep_hdbscan_inseguridad_general`, `confirmar_hdbscan_general_completo` | Parámetros, filtros y evidencia de resultados; A20/A21. Sin repetir barridos. |
| `identificar_corredores`, `fetch_corredores_geometria` | Agrupación de hechos y trazado de avenidas; A21. |
| `fetch_delitos_caba`, `fetch_clima_historico`, `construir_indice_inseguridad` | Ingesta, ventanas, unión y agregación; A02/A20/A22. |
| `prototipo_h3_hotspots`, `prototipo_gi_kde_hotspots` | Comparabilidad, preprocesamiento, dependencias y previews; A20/A22. |
| `data/` | Los 16 CSV completos perfilados; binarios y HTML inventariados; no se regeneraron datos. |
| Siete Markdown y seis DOCX en `docs/` | Contenido contrastado; inconsistencias en sección 6. No se certifica layout de Word. |
| README raíz, requirements, Compose, ejemplos, gitignore y tres BAT | Instalación, operación, bitácora y backlog; A14/A22. No se abrió un túnel público. |
| Logs de barridos | Contrastados con scripts y CSV; no equivalen a un registro completo de experimentos. |

## 8. Plan de cierre propuesto

### Bloque 1 — Integridad del producto

Cerrar A05–A10: cobertura desconocida, semántica de rutas, borrado/votos, escape de prensa, geolocalización y composición de ajustes. Mientras no se mida la calidad de prensa, no debería elevar silenciosamente un nivel presentado como predicción.

**Aceptación:** no hay borrado usando un identificador público; títulos externos son texto; rutas sin cobertura no reciben recomendación de seguridad; score base y ajustes tienen fuente/fecha; lluvia no se duplica sin validación; falsos positivos geográficos de esta auditoría son casos de regresión.

### Bloque 2 — Estabilidad y reproducción

Cerrar A12–A19/A22: base vacía, validación, pool, migraciones, carga inicial, errores HTTP, velocidad, proveedor de búsqueda y notebook. Consolidar scripts de construcción y registrar hashes.

**Aceptación:** una instalación limpia carga datos y sirve la demo mediante pasos documentados; una caída temporal no bloquea permanentemente la UI; conexiones no superan el límite; la recuperación SQL funciona; tests de integración reales pasan; recorrido GPS reproducido conserva progreso correcto.

### Bloque 3 — Validación del aporte académico

Cerrar A01–A04/A20/A21: objetivo formal, evaluación temporal independiente, tratamiento de faltantes, calibración y validación geográfica. Escribir resultados según lo medido, incluso si la mejora es modesta.

**Aceptación:** informe generado por una ejecución identificable, con métricas por clase y período, intervalos, baseline, ablaciones, cobertura y límites. No reutilizar cifras históricas como si describieran la versión vigente.

### Bloque 4 — Documentación final y demostración

Actualizar guías/manuales/resultados y backlog; preparar guion de demo con casos exitosos y degradados; verificar accesibilidad y pantallas reales. Asociar los objetivos académicos al código y a las pruebas disponibles.

**Aceptación:** no hay contradicciones entre README, DOCX, API, modelo y cifras de datos; otra persona puede reproducir la demostración y explicar qué significa cada color sin depender de la memoria del autor.

## 9. Conclusión profesional

El mayor valor de MotoSafe está en la integración construida y en la posibilidad de convertirla en una evaluación experimental honesta. Su mayor riesgo actual es que una interfaz convincente haga parecer más concluyentes resultados que todavía son exploratorios.

La prioridad es **consolidar y validar lo existente**. Con los problemas de autorización, cobertura, actualización y trazabilidad resueltos, más una metodología ajustada al verdadero objetivo del modelo, el proyecto puede presentar un aporte de ingeniería defendible. El estado revisado todavía no justifica afirmar que la aplicación está terminada, que fue validada integralmente en GBA o que demuestra reducción de riesgo en circulación.
