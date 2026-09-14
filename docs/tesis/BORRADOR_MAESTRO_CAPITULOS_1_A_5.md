# MotoSafe GBA

## Plataforma web para consulta de información vial, contextual y colaborativa orientada a motociclistas

**Autor:** Rodolfo [completar apellido]

**Carrera e institución:** [completar]

**Fecha:** [completar]

## Estado del borrador

Este documento se redacta a partir de evidencia técnica disponible en el repositorio. Las secciones con resultados empíricos, costos finales o validaciones de despliegue se completarán sólo cuando exista evidencia verificable. No se incluyen entrevistas, prototipos Figma ni resultados de usuarios porque no están documentados.

## Capítulo 1 Introducción

### 1.1 Problema

Los motociclistas toman decisiones de circulación con información fragmentada. Los registros históricos de siniestros, los reportes de inseguridad, las condiciones meteorológicas, el estado de una ruta y las noticias locales suelen estar dispersos en fuentes distintas. Aun cuando existe información pública, no siempre está preparada para responder una pregunta práctica antes de iniciar un recorrido: qué antecedentes se conocen en una zona y qué cobertura tienen esos antecedentes.

MotoSafe GBA propone una plataforma web que reúne capas históricas, información contextual y reportes recientes sobre un mapa. El sistema no afirma que pueda anticipar la ocurrencia de un accidente durante un viaje. Su modelo estima la gravedad posible de un siniestro condicionado a que ese siniestro ocurra. Esta distinción limita el alcance de las recomendaciones y evita presentar la ausencia de datos como seguridad.

### 1.2 Objetivo general

Diseñar e implementar un MVP web que permita consultar, visualizar y comparar información de riesgo vial y contexto reciente para motociclistas, con trazabilidad de fuentes, cobertura y límites de interpretación.

### 1.3 Objetivos específicos

- Integrar datos históricos de siniestralidad de motociclistas y visualizar zonas de referencia.
- Implementar un modelo de clasificación de gravedad condicionado a la ocurrencia de un siniestro y documentar su alcance.
- Incorporar capas de inseguridad, noticias públicas, clima, rutas y reportes colaborativos sin equiparar sus procedencias ni su cobertura.
- Diseñar una interfaz cartográfica accesible en escritorio y móvil.
- Preparar una arquitectura reproducible con API, base PostgreSQL/PostGIS, scraper periódico y despliegue cloud.

### 1.4 Alcance y delimitación

El trabajo se concentra en un MVP web. La evidencia histórica del modelo se documenta principalmente para CABA; las capas y consultas de GBA amplían la utilidad de exploración, pero no constituyen una validación predictiva independiente del conurbano. El proyecto no incluye aplicación móvil nativa, gestión de flotas, autenticación de identidad ni garantía de seguridad para un trayecto.

### 1.5 Relevancia

La propuesta organiza información pública y reciente en una interfaz orientada a un usuario concreto. Su aporte no depende de prometer una predicción absoluta: consiste en hacer visibles procedencia, antigüedad, cobertura y límites de las fuentes antes de usar una ruta o interpretar una zona.

## Capítulo 2 Metodología y procedimientos

### 2.1 Diseño de trabajo

El proyecto combina desarrollo de software, análisis de datos históricos y evaluación técnica reproducible. La unidad principal del modelo es un registro de siniestro y la salida se interpreta como gravedad condicionada. La evaluación temporal, el tratamiento de faltantes, la calibración y la incertidumbre están definidos en el contrato del modelo; sus resultados definitivos se incorporarán únicamente después de ejecutar el protocolo sobre el entorno reproducible.

### 2.2 Datos e indicadores

La documentación interna registra 23.343 hechos limpios de motocicleta, 23.338 filas destinadas al modelado, 740 hotspots y 243 corredores. Los indicadores contemplados incluyen métricas de clasificación, cobertura por fuente sobre rutas, vigencia de las capas, calidad de la ingesta de prensa y resultados de pruebas funcionales. La ausencia de información se comunica como cobertura insuficiente y no como un valor bajo de riesgo.

### 2.3 Técnicas e instrumentos

Se utilizan datasets y servicios públicos documentados, scripts de procesamiento, pruebas automatizadas, control de versiones Git y verificaciones manuales de interfaz. No se declaran entrevistas ni encuestas en este trabajo hasta contar con protocolo, consentimiento y resultados registrados.

### 2.4 Uso de inteligencia artificial

Las herramientas de IA se emplearon para apoyar la auditoría de código, la organización documental, la elaboración de borradores y la revisión técnica. Las decisiones de alcance, selección de evidencia, fuentes, resultados y conclusiones corresponden al autor. El registro de trazabilidad se mantiene en `01_DECLARACION_IA_Y_REGISTRO.md` y deberá completarse con cada prompt utilizado para una sección final.

## Capítulo 3 Marco teórico y tecnológico

### 3.1 Ejes de revisión y estado del arte

La revisión bibliográfica debe cubrir seguridad vial de motociclistas, análisis geoespacial de siniestros, clasificación de gravedad, comunicación de incertidumbre, sistemas de información geográfica, datos colaborativos y gobernanza de fuentes públicas. Las fuentes se incorporarán en formato completo luego de verificarlas en su publicación primaria.

### 3.2 Brecha abordada

La brecha práctica que aborda MotoSafe no es la ausencia total de datos, sino la distancia entre fuentes dispersas y una consulta comprensible para un motociclista. El sistema integra capas con distinta naturaleza y por eso debe exponer su origen, fecha y cobertura en vez de convertirlas en una única medida sin explicación.

### 3.3 Criterios de selección tecnológica

La selección tecnológica se evalúa según cinco criterios: capacidad para representar información geográfica; compatibilidad con un servicio web mantenible; persistencia de geometrías y consultas espaciales; trazabilidad de datos y pruebas; y costo de una eventual operación sostenida. La selección no prueba por sí misma la validez de las estimaciones de riesgo: aporta los medios para presentar, consultar y auditar fuentes heterogéneas.

### 3.4 Tecnologías seleccionadas

La interfaz utiliza React y Vite para construir una aplicación web de una sola página. MapLibre representa el mapa y las capas sin depender de un proveedor cerrado de interfaz cartográfica. El backend utiliza FastAPI para exponer los recursos del sistema y PostgreSQL con PostGIS para persistir reportes, noticias y geometrías. El procesamiento de los datos históricos y el modelo usan Python, pandas y scikit-learn. TomTom es un servicio externo de búsqueda y ruteo; su disponibilidad, cuota y costo deben mantenerse separados de los datos propios del sistema.

### 3.5 Operación y alternativas de despliegue

Docker y Compose describen una arquitectura reproducible con servicios diferenciados para interfaz, API, base y proceso periódico de ingesta. Render fue configurado como alternativa de despliegue, con una base gratuita sólo apta para demostración temporal; al momento de este borrador no existe un despliegue cloud validado. La elección de proveedor, los backups, los secretos, el dominio y los límites de APIs se retoman como costos y riesgos en capítulos posteriores.

## Capítulo 4 Arquitectura y diseño del sistema

### 4.1 Alcance y arquitectura de contexto

MotoSafe utiliza un frontend React/Vite con MapLibre, una API FastAPI y PostgreSQL/PostGIS. El backend carga el modelo Random Forest y los artefactos de contexto necesarios para servir hotspots y consultas. La base conserva reportes colaborativos y noticias. Un scraper independiente consulta fuentes periodísticas directas y registra noticias candidatas que cumplen criterios de clasificación y ubicación.

### 4.2 Modelo de datos y flujos principales

El diseño separa registros históricos, artefactos del modelo, capas derivadas, rutas, reportes colaborativos y noticias. Cada noticia conserva fuente, URL, categoría, relación explícita con motos, fecha editorial cuando está disponible, fecha de ingesta y precisión geográfica. Esta separación evita que una nota se interprete como dato oficial de siniestralidad o que una fuente de inseguridad complete artificialmente la cobertura histórica de una ruta.

El flujo histórico procesa datos de siniestros, genera artefactos y publica consultas de referencia. El flujo de prensa descubre notas en medios directos, aplica clasificación textual y geocodificación acotada, deduplica de manera conservadora e inserta filas aisladas. La capa de prensa no alimenta el modelo de gravedad. El diseño debe explicitar que su cobertura depende de fuentes autorizadas y es limitada: la corrida histórica que incorporaba Google Noticias no es comparable con las corridas posteriores a su retiro por la restricción de `robots.txt`.

### 4.3 Interfaz, API, seguridad y calidad

La interfaz comunica capas, filtros, antigüedad, cobertura y estados de falla sin presentar el silencio de una fuente como ausencia de riesgo. La API expone recursos de consulta y un endpoint de salud. El diseño incorpora validación de entradas, limitación de peticiones, tratamiento de contenido externo, secretos fuera del repositorio y migraciones versionadas. Las pruebas automatizadas, el control de versiones y la revisión visual son evidencia parcial de calidad; no reemplazan pruebas de usuarios, E2E con todos los servicios externos ni validación metodológica del modelo.

### 4.4 Operación y despliegue previsto

El repositorio incorpora migraciones versionadas, endpoint `/health`, CI, imágenes Docker y un Blueprint para Render. La arquitectura objetivo separa web, API, base y scraper programado. Al momento de esta redacción, el despliegue cloud está preparado pero no debe describirse como validado hasta completar la publicación, migrar datos y registrar pruebas de operación.

### 4.5 Limitaciones técnicas y evolución

El frontend cuenta con lint, build y pruebas Vitest; el backend cuenta con pruebas pytest y validación sintáctica. Los resultados de pruebas, límites del modelo, cobertura de rutas, precisión de prensa y estados de red se documentan en el backlog y la bitácora. Una prueba verde no sustituye la validación de datos, rutas o comportamiento real de usuarios.

## Capítulo 5 Justificación económica

### 5.1 Enfoque

La evaluación económica se realizará mediante escenarios separados de demo académica, piloto público y operación sostenida. Cada escenario debe explicitar inversión inicial, costo de infraestructura, consumo de APIs, almacenamiento, monitoreo, respaldo y soporte. No corresponde describir el proyecto como costo cero porque su operación utiliza cómputo, servicios externos y persistencia de datos.

### 5.2 Base de costos actual

La cotización inicial observada en Render para API y web fue de USD 14 mensuales, más el tiempo efectivo de ejecución del cron del scraper. La base gratuita propuesta para pruebas vence a los 30 días y no equivale a operación permanente. El análisis final incorporará dominio, servicio de mapas/ruteo, base persistente, backups y escenarios de demanda con fuentes fechadas.

### 5.3 Flujo de fondos

Antes de calcular VAN, TIR y período de recupero, Rodolfo debe aprobar el horizonte temporal, tasa de descuento, fuente de financiación o ingreso, usuarios previstos y supuestos de adopción. Los cálculos se presentarán sobre un mismo flujo, con análisis de sensibilidad y sin convertir estimaciones en resultados observados.
