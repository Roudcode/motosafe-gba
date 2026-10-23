# Auditoría de correspondencia entre tesis y proyecto MotoSafe GBA

Fecha: 23 de octubre de 2026. Alcance: `MotoSafe_GBA_Capitulos_1_a_8_FINAL.docx`, contrastado con código, artefactos, pruebas, evidencias del repositorio y fuentes externas seleccionadas. No se modificó el Word ni el comportamiento del sistema.

## Dictamen

**El documento representa buena parte del proyecto, pero todavía no está listo para entregarse como descripción final consistente.** Hay discrepancias cuantitativas reproducibles, conclusiones metodológicas más fuertes que la evidencia y secciones que describen versiones distintas del sistema. Se identifican 27 observaciones, no 27 fallas de ejecución. Algunas requieren corregir texto; otras requieren evidencia o una decisión de Rodolfo antes de cambiar software o modelo.

Lo más importante: fijar una única versión evaluada del modelo, limitar las conclusiones sobre predicción y rutas, actualizar arquitectura y privacidad tras incorporar cuentas y nube, y distinguir evidencia histórica de verificación actual. La aritmética económica sí se reproduce; las reservas económicas se refieren a supuestos y costos omitidos.

## Versión auditada y método

- Commit de código de referencia: `c45ea283b3f36b09c0757e88d572bb26040d4f08`.
- SHA-256 del último Word contrastado: `a16357c0d449fe77f971a9e8297081c81f509be47ce668188e7dbc17d6166253`.
- SHA-256 del modelo inspeccionado: `d89d873df7695247f8138c26271918fff3bb80bc6a6c7a925b8829aabae0de7b`.
- El Word cambió externamente durante la auditoría. Se volvió a extraer y contrastar el texto al cierre. Se retiraron observaciones que ya estaban corregidas: alcance con autenticación, papel de Claude en backend/nube, alternativas de despliegue y suma mensual USD 32.
- Los identificadores Pxxxx corresponden al orden de párrafos del cuerpo del DOCX, contando párrafos vacíos. Se dan además secciones, tablas o frases para localizarlos con Buscar. No son números de página.
- Se leyó el texto, tablas y diagramas; se inspeccionaron las siete imágenes incorporadas. Una versión intermedia se exportó con Word en modo lectura a un PDF de 75 páginas y se revisaron páginas seleccionadas. **No se certifica revisión visual completa de todas las páginas de la última versión.**
- No se accedió a cuentas de usuarios ni se escribieron datos de producción. La comprobación pública se limitó al frontend y `/health`. El estado de consola OAuth y la última ejecución remota de CI no quedaron verificados independientemente.

### Comprobaciones ejecutadas

| Comprobación | Resultado y alcance |
|---|---|
| Backend, suite normal | 135 aprobadas, 33 omitidas por requerir PostgreSQL |
| Integración PostgreSQL | 33 aprobadas en contenedor PostGIS efímero aislado, luego eliminado |
| Total backend | 168 pruebas aprobadas entre ambas ejecuciones complementarias |
| Frontend | 108 aprobadas en 7 archivos |
| Sitio público | HTTP 200 en `https://motosafe-web.onrender.com` |
| Salud pública | `estado=ok`, `base_datos=ok`, flags de umbrales y sklearn verdaderos al consultar |
| Modelo guardado | Configuración y predicciones reconstruidas; resultados adjuntos en `VERIFICACIONES.json` |
| Rutas | Probes sobre la lógica real y repetición de sensibilidad D04 |
| Economía | VAN, TIR y escenarios recalculados |

Estas pruebas no equivalen a una certificación de seguridad, una prueba de carga o una validación de exactitud predictiva. Para ejecutar frontend hubo que reparar dependencias locales tras un fallo EPERM; no se modificaron package.json ni el lockfile. No se afirma haber repetido lint, build o todos los E2E en esta auditoría.

## Observaciones de prioridad alta

### AT-01 — Las métricas publicadas no reproducen el artefacto actual

**Dónde:** tabla 4.2, tabla 4.3, capítulos 7 y 8; P0130 y P0351. **Evidencia:** pickle, columnas guardadas, `notebooks/reentrenar_modelo.py`, script adjunto `verificar_modelo_y_costos.py` y `VERIFICACIONES.json`.

La reconstrucción del split estratificado 80/20, semilla 42, con el modelo guardado arroja población 23.338, entrenamiento 18.670 y prueba 4.668. No deben presentarse 18.670 como universo completo.

| Métrica | Word | Reconstrucción actual |
|---|---:|---:|
| Accuracy | 0,6262 | 0,631320 |
| F1 macro | 0,368 | 0,373769 |
| Recall GRAVE interno | 0,604 | 0,619231 |
| Recall MORTAL interno | 0,464 | 0,517857 |
| F1 temporal con índice | 0,3032 | 0,3045 en repetición del script temporal |

La matriz temporal reproducida, orden GRAVE/LEVE/MORTAL, es `[[118,63,29],[1332,1488,258],[14,6,23]]`; el Word usa `[[126,54,30],[1360,1464,254],[15,6,22]]`. El ensayo temporal entrena 11.644 casos y evalúa 3.331, y no es el mismo ajuste del pickle de producción. Repetir con los dos índices disponibles no recuperó exactamente la matriz publicada.

**Corrección:** conservar resultados históricos si se identifican sus artefactos; agregar manifiesto con hashes de datos, índice, columnas, modelo, script y partición. No reemplazar números silenciosamente ni llamar a un reentrenamiento experimental «el modelo vigente». Esto demuestra falta de reproducción exacta, no fabricación de resultados.

### AT-02 — «Temporal» no garantiza independencia real

**Dónde:** evaluación temporal del capítulo 4 y conclusiones 7–8. **Evidencia:** comentarios de selección en `notebooks/reentrenar_modelo.py`, constructor del índice y ensayos temporales.

Hay selección de configuración apoyada en resultados de 2025 y selección de demografía apoyada en 2024. Además, el índice construido con 2023–2025 puede aportar información posterior a observaciones de entrenamiento o evaluación. Ordenar las filas cronológicamente no elimina estas dos vías de contaminación.

**Corrección:** describir las evaluaciones como retrospectivas con reutilización para selección; reservar otro período realmente intacto o reconstruir cada variable según información disponible a su fecha. La decisión sobre cambiar el modelo no se toma en esta auditoría.

### AT-03 — Interpretación excesiva de las diferencias entre evaluaciones

**Dónde:** comparación interna/temporal y discusión D02. **Evidencia:** `docs/evidencias/2026-10-18/D02-estabilidad/README.md` y protocolos de los experimentos.

Una caída entre split aleatorio y temporal es compatible con cambio de distribución y otras causas; no prueba por sí sola fuga de datos. D02 compara variantes sin índice, mientras otra tabla sí lo incorpora: no son intercambiables. Incluso usando las cifras publicadas, `0,368 − 0,3032 = 0,0648`: **6,48 puntos porcentuales**, no ocho.

**Corrección:** separar protocolos y causas demostradas de hipótesis; identificar datos, variables y años en cada tabla. No atribuir toda diferencia a una sola causa no aislada experimentalmente.

### AT-04 — La hipótesis cambia entre introducción y resultados

**Dónde:** 1.5/P0040, 7/P0318, 7.7/P0344 y 8.2/P0365.

La introducción plantea utilidad y defendibilidad de una interfaz con trazabilidad frente a un score único. El capítulo 7 evalúa otra hipótesis: existencia de patrones espaciales y temporales. El capítulo 8 vuelve a la primera y afirma sostenerla. Encontrar clusters o mostrar una interfaz no demuestra superioridad frente a otra interfaz; no se encontró un ensayo comparativo que aísle ese efecto.

**Corrección:** una sola pregunta e hipótesis operacionalizadas, con indicadores y límites. Presentar el aporte de trazabilidad como resultado de diseño y evidencia exploratoria de utilidad, salvo contar con comparación válida.

### AT-05 — Clasificar gravedad de siniestros no valida el ranking de zonas

**Dónde:** P0351 y conclusiones sobre priorización relativa y umbrales. **Evidencia:** unidad de observación del entrenamiento, matrices de confusión y generación de hotspots.

La precisión/recall medidos por siniestro no validan automáticamente el ordenamiento de zonas ni la seguridad de una ruta. La tabla de costo por clase y la estabilidad bootstrap tampoco aportan verdad de terreno sobre incidencia futura por zona. Falta exposición —viajes, tránsito o kilómetros— para interpretar frecuencia como riesgo por viaje.

**Corrección:** explicitar el salto de unidad siniestro→zona→ruta y tratar el ranking como heurística informativa no validada como probabilidad ni reducción de siniestros. Separar umbrales de visualización de calibración probabilística.

### AT-06 — La cobertura de ruta no es porcentaje de kilómetros

**Dónde:** explicación y resultados del comparador. **Evidencia:** `frontend/src/utils/riesgoRuta.js` y probe adjunto.

La implementación calcula proporciones sobre vértices muestreados, hasta 120, no longitud cubierta ponderada por distancia. «44% de ruta» no permite concluir «44% de kilómetros». El probe también reproduce que, ante cobertura vial `null` y cobertura de inseguridad 0,9, puede devolverse cobertura registrada 0,9 por fallback combinado. Eso no sostiene una afirmación general de que el umbral de cobertura se aplica siempre exclusivamente a siniestros.

**Corrección:** describir exactamente el estimador y su fallback; o proponer, con aprobación, cálculo por longitud y una política explícita para ausencia de cada capa. No cambiar comportamiento para hacerlo coincidir con el documento sin decisión.

### AT-07 — Ranking, etiquetas y sensibilidad no coinciden con lo afirmado

**Dónde:** método y resultados de rutas, análisis D04. **Evidencia:** `riesgoRuta.js`, `probe_rutas.mjs` y `sensibilidad_reproducida.txt`.

La cercanía selecciona zonas dentro del radio; no aplica necesariamente una ponderación continua por distancia. El score suma pesos ordinales. Las etiquetas dependen del conjunto de alternativas: `[10,11,12]` produce bajo/medio/alto; `[10,11,16]`, bajo/medio/crítico. No son categorías absolutas comparables entre búsquedas sin más explicación.

En el caso 2 de sensibilidad, base: Ruta 1=196, Ruta 2=194, Ruta 3=182. Con peso crítico 8: Ruta 1=199, Ruta 2=200, Ruta 3=185. La mejor permanece, pero **Ruta 1 y Ruta 2 intercambian orden**. Por tanto, «no cambia el orden» es incorrecto; «no cambia la ganadora en estos casos» es más acotado y defendible.

**Corrección:** actualizar fórmulas y conclusiones con la lógica real, distinguiendo ganador, ranking completo y etiquetas.

### AT-08 — Privacidad desactualizada después de incorporar cuentas

**Dónde:** privacidad del capítulo 4 y P0378. **Evidencia:** `backend/auth.py`, migraciones de usuarios y política de privacidad del repositorio.

El sistema ya almacena email, nombre de usuario, hash de contraseña y datos de verificación/sesión. La descripción de reportes mediante UUID puede ser correcta para esa tabla, pero no describe la totalidad del tratamiento de datos. El texto presenta la política como resuelta y enfatiza «qué no guarda: nombre, email» sin integrar adecuadamente el subsistema de cuentas.

**Corrección:** separar datos de cuenta, reporte y registros técnicos; documentar finalidad, vínculo, retención, acceso y borrado. No calificar un UUID persistente con coordenadas exactas como anonimato garantizado.

### AT-09 — El diagrama de arquitectura quedó atrás del despliegue y la autenticación

**Dónde:** figura 4.1 y explicación de arquitectura. **Evidencia:** imagen incorporada, nginx, backend de autenticación, SES-170 y comprobación pública.

Texto, figura y operación no describen una única versión: deben reflejar frontend y API en Render, PostgreSQL en Supabase, scraper en GitHub Actions y correo vía Gmail API. El flujo navegador→proxy `/api`→API y las direcciones de solicitud/respuesta deben quedar inequívocos; el dibujo actual no representa de forma completa estos componentes y relaciones.

**Corrección:** redibujar desde la configuración efectiva, marcando qué es comprobado hoy, qué es histórico y qué es propuesta. Que `/health` responda no verifica por sí solo todos los servicios del diagrama.

### AT-14 — La validación de prensa mezcla evidencia de distinta naturaleza

**Dónde:** calidad del clasificador/extractor de prensa. **Evidencia:** A09, CSV etiquetado, `docs/evidencias/2026-09-13/A09/metricas_2026-09-15.txt` y SES-062.

Hay 132 registros de partida, 105 evaluables y 27 excluidos; deben declararse también las abstenciones y el denominador usado. El registro de intervención de IA en etiquetado no permite presentar sin más el conjunto como referencia humana independiente. No se encontró identificación suficiente del anotador/revisor para sostener esa independencia. La clasificación temática, extracción de calles, precisión geográfica y deduplicación son tareas distintas; una métrica de la primera no valida las demás.

**Corrección:** explicar cómo se etiquetó y revisó, reportar exclusiones, desacuerdos y tareas medidas. Conservar como no verificada la exactitud geográfica que no tiene conjunto de referencia.

### AT-17 — La aritmética económica cierra; la cobertura de costos necesita revisión

**Dónde:** capítulo 5. **Evidencia:** recálculo adjunto y condiciones oficiales de servicios.

Con flujos `[-5640,-620,518,2450,4575,6992]` y tasa 17%, el VAN es USD 1.368,78 y la TIR 22,9864%. Se reproducen escenarios: costos +20%=USD 898,61; ingresos −20%=−USD 503,14; optimista=USD 3.240,70; combinado pesimista=−USD 973,30. No hay motivo para reemplazarlos por las cifras antiguas de otras versiones.

El escenario con ingresos debe contemplar condiciones comerciales: [Open-Meteo](https://open-meteo.com/en/pricing) distingue API gratuita no comercial y suscripción comercial. No basta presupuestar uso gratuito académico si se proyecta explotación comercial. También deben explicitarse mantenimiento, soporte, impuestos/comisiones aplicables, backups y horas de operación, aunque se excluyan justificadamente. Un costo constante adicional de unos USD 35,65 mensuales durante los cinco años consume todo el VAN base con esos supuestos.

**Corrección:** registrar fecha de tarifas, carácter académico/comercial, límites y disparadores de cambio de plan. Diferenciar factibilidad del ejemplo económico y rentabilidad demostrada.

### AT-19 — El correo puede depender de un OAuth de prueba que vence

**Dónde:** autenticación y riesgos operativos. **Evidencia:** Gmail API en código y configuración «Prueba» relatada en SES-170; [documentación oficial Google OAuth](https://developers.google.com/identity/protocols/oauth2#expiration).

En aplicaciones externas con estado Testing, los refresh tokens expiran a los siete días salvo la excepción de scopes básicos de identidad. `gmail.send` no es ese caso básico. La consola actual no se inspeccionó: **es un riesgo condicionado a que ese estado siga vigente**, no afirmación de que el correo esté fallando.

**Corrección:** verificar estado, alcance y fecha del token fuera del chat, documentar renovación/publicación y una prueba de continuidad. Un correo que llegó una vez no valida funcionamiento sostenido del registro o recuperación.

## Otras discrepancias que deben corregirse

### AT-10 — Modelo de datos y nombres de interfaces incompletos

**Dónde:** figura 4.2 y descripción de API. **Evidencia:** migraciones 005–007, `backend/auth.py`, rutas de `backend/main.py`.

Faltan entidades/campos de usuarios, códigos, versiones de sesión y deduplicación. Donde aparece `prensa_noticia` o `/noticias`, contrastar con `reportes_prensa` y `/reportes-prensa`. El pie «esquema real ... tal como están hoy» exige correspondencia exacta. Actualizar diagrama, claves y cardinalidades; distinguir un esquema conceptual de uno físico.

### AT-11 — Recuentos de pruebas y pendientes se contradicen

**Dónde:** capítulo 7, seguridad/pool P0147 y tablas de validación. El Word publica 67 backend +80 frontend =147. Esta auditoría ejecutó 168 backend y108 frontend; no son las cifras de septiembre ni de un futuro plan. PostgreSQL aislado sí fue probado. Esto tampoco demuestra carga productiva, disponibilidad continua o concurrencia ilimitada. Fechar cifras y distinguir integración de carga.

### AT-12 — Recomendaciones finales contienen tareas históricas ya avanzadas

**Dónde:** 8.3–8.4 y P0383. **Evidencia:** DEC-022 a DEC-026, SES-170, código y endpoint público.

No es coherente describir toda ejecución contra servicios reales como pendiente cuando ya existen despliegue público y registro de corridas. La auditoría confirmó web y salud, no la última corrida remota; conservar ese matiz. También hay textos antiguos sobre decisiones y tamaño de App.jsx: se contaron 2.010 líneas, no 2.066. Revisar cada pendiente contra su ID y fecha, sin convertir registros ajenos en validación propia.

### AT-13 — Resultados de clustering mezclan versiones y complementos

**Dónde:** P0135, 7.2/P0327 y P0353. **Evidencia:** CSV actuales y `docs/evidencias/2026-10-22/DEC-024-limpieza-delitos/RESULTADOS.md`.

Se describen a la vez 633 y619 hotspots generales como resultado final. Los archivos inspeccionados contienen740 viales,619 generales,502 de moto y243 corredores. La evidencia de limpieza informa200.291 puntos aislados sobre403.993:49,6% es fracción aislada; cobertura asignada es aproximadamente50,4%, su complemento. No intercambiar ambos. No se repitió el clustering completo; esta observación contrasta artefactos y aritmética de evidencia guardada.

### AT-15 — La caída de noticias guardadas no mide por sí sola pérdida de cobertura

**Dónde:** comparación de corridas de prensa. La corrida de267 nuevas y la posterior de4 nuevas usan una base con estado diferente; deduplicación y registros previos afectan el número insertado. 122 candidatas/57 ubicadas/4 nuevas no es un experimento controlado de ablación del agregador. Mantener ambas como históricas, con fuentes y estado inicial; no inferir una caída proporcional de recall o calidad.

### AT-16 — Las filas de Google Noticias no siguen expuestas como dice el cierre

**Dónde:** P0373. **Evidencia:** filtro de `/reportes-prensa` en `backend/main.py`, que excluye fuentes que comienzan por `Google Noticias` y filas marcadas como duplicadas.

Conservar filas en base no significa mostrarlas. Reemplazar «siguen visibles hasta vencer» por la política efectiva de exclusión/retención; purgar datos históricos es una decisión distinta y no se ejecutó.

### AT-18 — Presupuesto de escalamiento sin carga derivada y migración incompleta

**Dónde:** escenarios de usuarios y alternativas del capítulo 5. No basta multiplicar usuarios si no se derivan sesiones, solicitudes, geocodificación, rutas, mapa, almacenamiento y concurrencia. [Supabase](https://supabase.com/pricing) publica límites y pausado del plan gratuito; [Cloudflare Pages](https://developers.cloudflare.com/pages/platform/limits/) también tiene límites. Gratis no equivale a capacidad ilimitada.

Además, pasar el frontend actual a hosting estático elimina el nginx que hoy hace proxy de `/api`. Debe resolverse el destino de API, cookies y CORS. Presupuestar alternativa como propuesta con trabajo de migración, no como sustitución inmediata equivalente.

### AT-20 — La matriz de riesgos conserva condiciones de otra infraestructura

**Dónde:** capítulo 6. Revisar riesgos ligados a vencimiento de base gratuita de Render frente a la base actual en Supabase, incompatibilidad sklearn frente a controles ya incorporados, y dependencia local frente al despliegue público. Mantener el riesgo residual y fecha de mitigación; no borrar historia ni declarar eliminación absoluta. Añadir dependencia OAuth y bloqueos de feeds desde IP de Actions relatados en SES-170.

### AT-21 — Estructura editorial todavía de entrega parcial

**Dónde:** portada P0007/P0009, índice, bibliografía/apéndices y encabezados. La portada dice «Capítulos 1 a5 — Entrega parcial» y septiembre aunque el documento llega a8. Bibliografía y apéndices aparecen antes de capítulos7–8. El índice conserva contenido/instrucciones de actualización en su estado guardado; existe campo TOC, por lo que no debe confundirse con ausencia de índice. El estilo de encabezado de capítulo2 requiere homologación.

**Corrección:** portada final fechada, ocho capítulos consecutivos, referencias y anexos al cierre, actualización de campos y revisión del PDF exportado de la versión definitiva.

### AT-22 — Trazabilidad de IA y de evidencias incompleta para el documento final

**Dónde:** tabla2.1, declaración y apéndice de prompts. Parte del registro sigue restringida a capítulos1–5. Extender a6–8, diagramas, análisis y revisiones. Una afirmación general de revisión/aprobación por el autor no sustituye registro concreto. Las ediciones concurrentes quitaron fechas de varias evidencias; conservar en anexos fecha, versión y protocolo aunque se aligere el cuerpo. No atribuir aprobación nueva por esta auditoría.

### AT-23 — Las doce sesiones con usuarios necesitan respaldo recuperable

**Dónde:** apéndice A y capítulo7. El Word contiene resumen y casos, y SES-059 registra que el autor declaró reales las respuestas. No se localizó un registro primario independiente de las doce sesiones con fecha, versión, tareas y respuestas que permita reproducir la agregación. Eso es **evidencia primaria no localizada**, no demostración de entrevistas inventadas.

**Corrección:** vincular registros anonimizados existentes; si no existen, declarar el límite y no reconstruir respuestas ni consentimientos retrospectivamente. Separar una observación de muestra por conveniencia de inferencia poblacional.

### AT-24 — Bibliografía con una fecha errónea y verificación parcial

**Dónde:** cita/referencia Infoecos. La [nota consultada](https://infoecos.com.ar/index.php/los-usuarios-de-motos-representaron-el-46-de-las-victimas-fatales-por-siniestros-viales-en-argentina/) se publicó el12 de mayo de2026 y cita datos2025; no corresponde usar2025 como año de publicación de la noticia.

Se corroboraron también referencias seleccionadas como Camacho Onoa2025 en UTDT e Islam y colaboradores2022; no se auditó exitosamente cada fuente completa: algunas respuestas fueron bloqueadas/inaccesibles. No declarar toda bibliografía verificada por esta revisión. Completar fuente primaria, fecha y URL de documentación técnica que sostiene decisiones, y marcar una noticia como fuente secundaria aunque cite ANSV.

### AT-25 — Las capturas no prueban todos los estados que se les atribuyen

**Dónde:** figuras4.4–4.7. Hay capturas reales, no están pendientes todas. Sin embargo, la figura4.6 muestra insuficiencia de cobertura, no necesariamente la distinción nulo frente a cero; una vista móvil en4.7 no prueba por sí misma modo degradado o pérdida de red. Vincular cada afirmación a la captura o prueba que efectivamente la demuestra. CONTINUIDAD es registro de gestión, no reemplazo de procedimiento operativo ante una caída.

### AT-26 — El84,9% de estabilidad está explicado como otro estadístico

**Dónde:** P0352. **Evidencia:** `docs/evidencias/2026-10-18/confianza-zonas-bootstrap/README.md`.

La medida se construye a partir de proporción de votos de la clase mayoritaria y agregación sobre escenarios. No equivale a afirmar que los diez modelos coinciden unánimemente en84,9% de las740 zonas, ni es exactitud frente a realidad. Definir denominador, agregación y336 escenarios; mantener explícita la diferencia entre estabilidad y validez.

### AT-27 — Varias precisiones operativas cambian el significado del texto

**Dónde:** operación, seguridad y actualización del capítulo4.

- Refresco de frontend cada cinco minutos no es reentrenamiento ni actualización completa de fuentes.
- `/health` no informa «únicamente» estado, base y hora: también flags de umbrales y versión sklearn.
- Cookie firmada sin tabla de sesiones no implica ausencia de estado: se consulta versión de sesión asociada al usuario.
- Cuenta verificada por email no equivale a identidad civil comprobada; UUID tampoco garantiza una persona única ni evita por sí solo votos múltiples.
- Cron configurado no prueba éxito de cada corrida; distinguir programación, logs de una corrida y monitoreo sostenido.

Corregir estas descripciones sin prometer garantías que la implementación no proporciona.

## Qué sí coincide y conviene conservar

El stack React/MapLibre/FastAPI/PostgreSQL, el contrato de gravedad condicionada al siniestro y la delimitación académica a CABA están representados. La configuración actual tiene300 árboles, profundidad12, mínimo5 por hoja, balanceo por submuestra,53 columnas y sexo pero no edad. Hay implementaciones reales de cuentas, migraciones, prensa directa y controles operativos; no son solo propuestas. Existen resumen bilingüe, capturas y discusión de limitaciones. Las pruebas ejecutadas dan evidencia funcional y las cuentas financieras se reproducen.

No corresponde volver a afirmar que falta todo el desarrollo, que no hay capturas o que no hay despliegue. Tampoco corresponde concluir que aprobar pruebas demuestra eficacia predictiva o productiva a escala.

## Orden recomendado de cierre

1. **G01, coherencia académica:** fijar versión y manifiesto del modelo; corregir AT-01 aAT-05 yAT-26. Acordar qué evaluación se cita antes de reescribir resultados.
2. **G01 con referencias aA05/A06:** describir cobertura, ranking y sensibilidad realmente implementados, AT-06 yAT-07. Cualquier modificación del algoritmo requiere decisión explícita.
3. **G01:** sincronizar arquitectura, esquema, privacidad, operación y riesgos con cuentas y nube, AT-08 aAT-12,AT-16,AT-19,AT-20 yAT-27.
4. **G01/A09/G02:** cerrar trazabilidad de muestras de prensa y usuarios; preservar límites donde falta evidencia. No inventar datos para completar anexos.
5. **G01:** corregir supuestos económicos, bibliografía y armado editorial; generar el Word/PDF final y revisar página por página.

Los códigos AT identifican observaciones de esta fotografía histórica. **No constituyen otro backlog**: el seguimiento operativo permanece en `docs/gestion/BACKLOG.md`. No se promovió un modelo, alteró la base o tomó una decisión de producción como parte de esta auditoría.
