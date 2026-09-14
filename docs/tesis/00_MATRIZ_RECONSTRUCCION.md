# Reconstrucción de la tesis MotoSafe GBA

Este documento reemplaza al texto anterior como guía de trabajo. La devolución docente recibida sobre la Entrega 4 obliga a no reutilizar afirmaciones no verificadas, entrevistas no documentadas, herramientas no usadas ni costos declarados como cero.

## Criterio de redacción

Cada sección debe diferenciar tres estados: implementación comprobada, plan de validación pendiente y supuesto económico. Ningún estado pendiente se presenta como resultado.

## Requisitos de la materia identificados

| Capítulo | Pedido de la cátedra | Evidencia disponible | Pendiente real |
|---|---|---|---|
| 1 Introducción | problema, objetivos, relevancia, barreras, hipótesis, enfoque y recursos | proyecto, backlog y documentación técnica | fijar título, hipótesis y alcance definitivo con Rodolfo |
| 2 Metodología | problema, delimitación, diseño, indicadores, técnicas, instrumentos, análisis y gestión | contrato del modelo, fichas de datos, bitácora, CI | declarar IA; decidir si habrá entrevistas o retirarlas; ejecutar evaluación temporal |
| 3 Literatura | antecedentes y conceptos que fundamenten las decisiones | fuentes iniciales, antecedente UTDT y documentos de datos | bibliografía primaria verificada y citas completas |
| 4 Marco tecnológico | arquitectura, software, hosting, base, UX, operación, pruebas y justificación de elecciones | React/Vite/MapLibre, FastAPI, PostgreSQL, modelo, GitHub, Docker, Render | capturas reales, diagrama final, migración cloud y pruebas de despliegue |
| 5 Justificación económica | inversión, costos, flujos, VAN, TIR y recupero | arquitectura de costos y cotización inicial de Render | escenario de usuarios, modelo de ingresos/financiación y supuestos aprobados |

## Hechos que sí pueden afirmarse hoy

- MotoSafe es una plataforma web React/Vite con MapLibre; usa una API FastAPI y PostgreSQL/PostGIS.
- El modelo actualmente guardado es Random Forest; estima gravedad condicionada a un siniestro, no probabilidad de que un viaje tenga un accidente.
- La evidencia auditada registra 23.343 hechos de motocicleta limpios, 740 hotspots y 243 corredores. Esos datos corresponden al universo histórico documentado y no prueban cobertura predictiva independiente de todo el GBA.
- La prensa multifluente registró una corrida real de 560 candidatas, 289 ubicadas y 267 nuevas almacenadas el 13 de septiembre de 2026.
- El repositorio contiene CI, migraciones versionadas, imágenes Docker y un Blueprint de Render; no se debe afirmar que ya existe un despliegue productivo hasta validar ese entorno.

## Contenido que se descarta del documento anterior

- Entrevistas, guía de preguntas, grabaciones y validación cualitativa: no están documentadas.
- Figma, wireframes previos y aplicación móvil: no forman parte de la implementación disponible.
- OpenWeatherMap: el sistema actual utiliza Open-Meteo.
- Cobertura predictiva validada del GBA y costo cero: no están sustentados.
- Métricas o resultados no reproducidos con el modelo actual.

## Fuentes internas de referencia

- `docs/modelo/CONTRATO_Y_EVALUACION.md`
- `docs/datos/FICHA_SINIESTROS_MOTO.md`
- `docs/riesgo/PROCEDENCIA_Y_COBERTURA.md`
- `docs/riesgo/INGESTA_PRENSA_MULTIFUENTE.md`
- `docs/operacion/DESPLIEGUE_MVP.md`
- `docs/entrega/MATRIZ_ACADEMICA_Y_DEMO.md`
- `docs/gestion/BITACORA.md`
