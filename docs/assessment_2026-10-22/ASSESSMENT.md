# Assessment integral de MotoSafe GBA — 22/10/2026

## Dictamen

**No recomiendo cerrar la versión como lista para producción sin resolver los P1 de este informe.** Hay avances reales, pruebas útiles y separación de responsabilidades; también hay fallas reproducibles que alteran la recomendación de rutas, la actualidad de las noticias y la recuperación de cuentas. Que una pantalla funcione en una demo no prueba estos casos límite.

Se auditó **HEAD `1c4b8ef` más el árbol de trabajo local**, incluidos F11 y los cambios visuales/operativos todavía sin commit. No se corrigió código productivo, no se reentrenó, no se cambió un umbral ni se escribió en la base personal. El assessment del 11/09 sigue siendo histórico.

**Resumen: 11 hallazgos P1, 7 P2. Ningún P0 demostrado.** P1 significa corregir antes de abrir el MVP a usuarios externos o de sostener la afirmación académica afectada; no significa que se haya observado un ataque en producción. P2 significa consolidación necesaria o falla con alcance más acotado. Los ejemplos fabricados para las pruebas están identificados como sintéticos: no son siniestros, noticias ni usuarios reales.

## Alcance y evidencia

Revisión transversal de backend, frontend, autenticación, persistencia, migraciones, scraper, uso de proveedores, modelo/pipeline, ranking, cachés, publicación, CI y continuidad documental. Se inspeccionaron los caminos críticos y sus pruebas. `inventario.json` identifica archivos propios de código/configuración y sus hashes; **inventariar no equivale a revisar manualmente cada línea**.

No incluye una nueva campaña de UX/GPS con motociclistas, un pentest desde Internet, una corrida masiva del scraper, un reentrenamiento completo, revisión página por página del Word, auditoría de todas las licencias ni certificación de ausencia de vulnerabilidades en dependencias. No se hicieron cambios para “hacer pasar” pruebas.

| Verificación ejecutada | Resultado de esta sesión |
|---|---|
| Frontend, Vitest | **108 aprobadas**, 7 archivos. Primer intento limitado por ENOENT de caché del sandbox; repetición fuera de él aprobada. |
| ESLint | Exit 0, sin errores. |
| Build Vite, salida separada | Exit 0. Chunk de mapa 1.037,98 kB (277,28 kB gzip); worker 487,10 kB. Advertencia de tamaño, no fallo. |
| Backend completo con PostgreSQL/PostGIS real aislado | **157 aprobadas, 3 fallidas**, 160 ejecutadas, 30,90 s. |
| Reproducciones backend propias | API real con TestClient + SQL real en base desechable; correo/proveedores simulados. `probe_backend.py` y `resultado_backend.json`. |
| Reproducción cobertura | Funciones reales importadas desde el frontend, misma geometría con distinta densidad de vértices. `probe_cobertura.mjs` y `resultado_cobertura.txt`. |
| Modelo cargado | RandomForestClassifier, 300 árboles, profundidad 12, hoja mínima 5, balanced_subsample, **53 columnas**, GRAVE/LEVE/MORTAL. Huella de umbrales y versión sklearn coinciden. No se recalcularon métricas predictivas. |
| Infraestructura local | Docker mostró el contenedor personal con puerto PostgreSQL publicado en todas las interfaces. Pruebas hechas en OTRO contenedor, puerto local 55439. |

El primer intento de pytest dentro del sandbox no produjo resultados y se interrumpió; no cuenta como prueba aprobada. La corrida válida fue la externa contra el contenedor desechable.

## Hallazgos prioritarios

### H01 — P1: la cobertura depende de cómo se dibuja la polilínea, no de la longitud cubierta

- **Código:** `frontend/src/utils/riesgoRuta.js:88–119`; consumo en `App.jsx:1392–1434`; explicación en `RutaResumenPanel.jsx` (“4 de cada 10 tramos”). Relacionado: A05/D03/D04.
- **Reproducción:** mismo segmento recto de 11,119 km y un hotspot inicial con radio de 600 m. Con dos vértices: 50%; con 100 vértices en los primeros 110 m y el mismo extremo final: **99,01%**. Aproximadamente sólo **5,40% de la longitud** está dentro del radio. La segunda representación supera el gate de 60% sin cambiar el recorrido.
- **Impacto:** una ruta casi totalmente fuera de cobertura puede habilitar la etiqueta “menor exposición”. La validación previa con dos destinos reales no prueba invariancia geométrica.
- **Corrección propuesta:** medir unión de intervalos cubiertos por longitud, o muestrear a distancia constante con error acotado; mantener fuentes separadas. El radio de DEC-023 no necesita cambiar para arreglar esto.
- **Aceptación:** densificar/simplificar una misma ruta no cambia significativamente la cobertura; tramo largo descubierto no queda diluido por vértices urbanos densos. Acordar tolerancia y medirla con rutas reales.

### H02 — P1: sin datos de siniestros, inseguridad puede habilitar la recomendación

- **Código:** `riesgoRuta.js:188`, `coberturaPorFuente[i]?.siniestro ?? coberturaPorRuta[i] ?? 0`. Relacionado: A05/DEC-009.
- **Reproducción:** fuente siniestros `null`, inseguridad `1`, cobertura combinada `1` → `coberturaRegistrada=1`. El gate de `App.jsx` sólo revisa este número.
- **Impacto:** una primera carga fallida o vacía de siniestros puede recomendar “menor exposición” usando solamente delitos. Contradice el contrato explícito de que una fuente no reemplaza a la otra.
- **Corrección/aceptación:** conservar `null` como indisponibilidad y bloquear esa recomendación; probar falta, vacío y error de cada capa por separado. No basta con agregar un aviso general.

### H03 — P1: noticias antiguas se rejuvenecen y modifican el riesgo actual

- **Código:** `backend/main.py:1093`, `listar_reportes_prensa`, `_obtener_reportes_recientes_por_tipo`. Relacionado: A09/A10/A11.
- **Causa:** si `publicado_en` es anterior a `creado_en - 30 días`, el CASE lo reemplaza por la fecha de ingesta, incluso cuando la fecha editorial es válida. Además lo devuelve bajo el nombre `publicado_en`.
- **Reproducción SQL/API:** noticia sintética publicada hace **dos años**, incorporada hoy → aparece en `/reportes-prensa` y en el conjunto que aumenta el riesgo por hechos de los últimos siete días.
- **Impacto:** no es sólo una fecha mal mostrada: afecta colores y ranking. Los sitemaps pueden devolver archivos históricos legítimos.
- **Corrección:** separar fecha editorial, fecha de ingesta, referencia temporal y estado de confianza. Una fecha antigua válida debe expirar; una fecha inválida o desconocida debe declararse y no tratarse automáticamente como hecho reciente para ajustar riesgo.
- **Aceptación:** caso antiguo, sin fecha, fecha futura y fecha editorial reciente, tanto en listado como en ajuste. Medir cuántas filas reales cambiarían antes de adoptar la política con Rodo.

### H04 — P1: los códigos de recuperación anteriores vuelven a ser utilizables

- **Código:** `backend/auth.py:140`, `_crear_codigo`, `resetear_password`. Relacionado: F11.
- **Causa:** se busca el último código **sin usar**. Generar uno nuevo no invalida los anteriores, y consumirlo vuelve a dejar al anterior como candidato.
- **Reproducción:** dos códigos no vencidos, viejo y nuevo. Reset con el nuevo → 200; luego reset con el viejo → **200**. Cambia efectivamente la contraseña otra vez.
- **Impacto:** pedir/usar un código nuevo no elimina el poder de un código anterior comprometido. Tampoco hay bloqueo transaccional de la lectura para garantizar un único consumo concurrente.
- **Corrección/aceptación:** invalidar todos los códigos previos del tipo y consumir el vigente de forma atómica. Ningún código anterior ni dos requests concurrentes deben completar dos reseteos. Usar `secrets` en lugar de `random` para generar secretos; no se demostró predicción del generador en esta auditoría.

### H05 — P1: cambiar contraseña o cerrar sesión no revoca una cookie copiada

- **Código:** `auth.py`, `_crear_cookie_sesion`, `_usuario_id_de_sesion`, `sesion_valida`, `resetear_password`, `logout`. Relacionado: F11/A07.
- **Reproducción:** cookie emitida antes del reset sigue obteniendo **200 en `/auth/me`** después de cambiar la contraseña y después del logout del navegador original.
- **Impacto:** la recuperación de cuenta no expulsa a alguien que ya obtuvo una sesión. Firma/HttpOnly/Secure protegen otros aspectos, no la revocación. La sesión dura por defecto 12 horas.
- **Corrección/aceptación:** versión de sesión por usuario o sesiones revocables; reset incrementa/invalida; definir si logout revoca una o todas. Probar también cuenta borrada/deshabilitada contra rutas protegidas, porque `sesion_valida` hoy sólo verifica payload firmado.

### H06 — P1: una misma cuenta puede fabricar el consenso que oculta reportes

- **Código:** `backend/main.py:795,835–882`; autor y voto dependen de UUID aportado por el cliente. Relacionado: A07/F08/F11.
- **Reproducción:** una única sesión crea un reporte y lo desmiente tres veces cambiando el UUID; las tres respuestas son **201** y el reporte desaparece del listado vigente.
- **Impacto:** el control de “no votar lo propio” y “usuarios distintos” no es efectivo frente a un cliente modificado. La cuota diaria por autor también admite UUID nuevos. El token privado de borrado sí sigue siendo una protección distinta y no se encontró aquí un bypass de ese token.
- **Corrección:** decidir cómo vincular reportes/votos a la identidad autenticada y cómo operar si se mantiene modo anónimo. No convertir silenciosamente un identificador de dispositivo en garantía de personas distintas.
- **Aceptación:** cambiar UUID desde una sesión no aumenta votos ni reinicia cuota; sesiones distintas siguen una política explícita contra abuso. Requiere decisión de Rodo por cambiar reglas del sistema.

### H07 — P1: registro público sin límite y proxy de tráfico sin protección de cuota

- **Código:** `auth.py:261` y `main.py:1557–1596`. Relacionado: F11/A13/A14/T04.
- **Evidencia:** registro no usa limitador; ocho registros desde la misma IP fueron **201**. Se simuló hashing/correo en esta comprobación para no consumir recursos ni enviar spam. En producción cada alta calcula bcrypt, escribe SQL y puede enviar SMTP. El proxy de tráfico no tiene límite ni validación de z/x/y: `/trafico/tiles/99/-1/-1.png` alcanzó el upstream simulado.
- **Impacto:** saturación de registro/envío de correo y consumo de cuota de TomTom mediante misses de caché. No se ejecutó una carga abusiva ni se cuantificó costo real.
- **Corrección/aceptación:** límites por acción/identidad/IP y globales, rangos válidos, presupuesto de proveedor, backpressure y respuestas 429. Probar detrás del proxy real: la identidad IP no puede asumirse correcta sólo por test directo.

### H08 — P1: la búsqueda automática vuelve a consultar Nominatim público

- **Código:** `useBusquedaDireccion.js` (350 ms mientras se escribe), `main.py:1920–1949` y `_buscar_lugares_nominatim`.
- **Evidencia estática:** si TomTom devuelve vacío o resultados irrelevantes, `/lugares` consulta automáticamente `nominatim.openstreetmap.org/search`. No distingue consulta confirmada de autocompletado ni tiene limitador global de 1 request/s para ese proveedor.
- **Impacto:** riesgo de bloqueo del geocodificador y regresión de A18, que figuraba validado. El proxy backend no convierte autocompletado en búsqueda manual.
- **Fuente primaria consultada el 22/10/2026:** [política oficial de Nominatim](https://operations.osmfoundation.org/policies/nominatim/), que prohíbe autocompletado y establece un máximo agregado por aplicación de una consulta por segundo. Las tareas periódicas tienen restricciones adicionales. No se enviaron consultas de prueba a Nominatim.
- **Corrección/aceptación:** mantener sugerencias exclusivamente en un proveedor que las admita; fallback público sólo con confirmación explícita y regulación global compatible, o servicio propio/contratado. La pausa de 15 s del scraper no regula las llamadas del frontend.

### H09 — P1: el Blueprint de Render no lleva las capas históricas ni el sistema de cuentas

- **Código/configuración:** `render.yaml` usa `dockerContext: ./backend`; `backend/Dockerfile` copia sólo ese contexto; carga inicial busca CSV fuera del contexto; no hay volumen, descarga ni seed en el Blueprint. `AUTH_HABILITADO=false` en Render y Compose productivo; SMTP y SESSION_SECRET tampoco se suministran allí.
- **Impacto:** un despliegue limpio siguiendo ese archivo no reproduce el sistema local: las capas históricas no se cargan y F11 queda deshabilitado. La carga inicial avisa “sin CSV” pero permite arrancar; `/health` no comprueba tablas/población de capas.
- **Nivel de evidencia:** configuración y caminos de carga revisados; el test SQL real confirma el modo “sin CSV”. **No se desplegó Render** ni se sostiene que una instancia ya desplegada tenga este fallo.
- **Corrección/aceptación:** empaquetar/sembrar los derivados con manifiesto y hashes, decidir autenticación de producción y configurar secretos fuera de Git. Ensayo desde checkout limpio + base vacía: login según política y conteos/datos correctos de todas las capas. Revisar plan/costos vigentes antes de contratar; no se verificaron precios en esta auditoría.

### H10 — P1 académico: el año de evaluación ya participó en decisiones posteriores

- **Evidencia:** `DEC-012` y `MODELO_VIGENTE_2026-09-07.md:24,47–69` justifican elegir sin edad por resultados de evaluación 2024; DEC-015 elige/sostiene umbrales usando sensibilidad reportada sobre 2024. `reentrenar_modelo.py:115–130` describe comparación de configuraciones contra 2025. `eval_calibracion.py` además cruza el índice actual por comuna, sin reconstruirlo a la fecha de cada partición; `construir_indice_inseguridad.py` usa los últimos tres años disponibles.
- **Consecuencia:** la separación cronológica de filas puede ser real y los cálculos seguir siendo correctos; **eso no convierte los resultados reutilizados para elegir en una estimación final independiente de selección**. Tampoco demuestra un escenario prospectivo con features disponibles en aquel momento. No se cuantificó optimismo ni se declaró inválido todo el trabajo previo.
- **Corrección:** identificar resultados como evaluación retrospectiva/exploratoria; congelar configuración y protocolo antes de una nueva evaluación no consultada (o validación anidada temporal). Para la feature de delitos usar versiones históricas o excluirla y reportar el alcance. Conservar las decisiones y los números anteriores con su verdadero papel.
- **Aceptación:** trazabilidad separada entrenamiento/selección/evaluación, fecha de disponibilidad de cada predictor y métricas de la configuración congelada. Sin prometer independencia de un año ya usado para decidir.

### H11 — P1 condicionado a la red: PostgreSQL local escucha fuera de localhost con credencial de desarrollo en Compose

- **Evidencia:** `docker-compose.yml` publica `5432:5432`, con credencial de desarrollo fija; `docker ps` mostró **0.0.0.0:5432 y [::]:5432** en el contenedor personal. No se publica la contraseña en este informe.
- **Impacto:** la base puede quedar accesible a otros equipos si el firewall/ruteo lo permite, especialmente en Wi-Fi no confiable. No se probó acceso desde Internet ni desde otro equipo y no se afirma compromiso.
- **Corrección/aceptación:** vincular a 127.0.0.1 si sólo la usa el backend local, revisar firewall y privilegios, separar secretos. Verificar desde otro equipo que no se pueda conectar. Cualquier rotación debe coordinarse con Rodo; no se realizó.

## Hallazgos P2

| ID | Hallazgo y evidencia | Consecuencia / cierre propuesto | Backlog |
|---|---|---|---|
| H12 | Dedup de prensa sólo filtra fecha `>= referencia - 5 días`, sin cota superior (`scrapear_noticias_robos.py:734–741`). Nota de hace 100 días se vinculó a una de hoy en SQL real. | No implementa una ventana de ±5 días; ingesta fuera de orden puede ocultar hechos distintos. Agregar cota superior y probar ambos órdenes. El radio/título aceptado en DEC-021 es otra decisión; no se cambió. | A09 |
| H13 | SMTP ausente usa fallback de consola y devuelve sin excepción; registro devuelve `mail_enviado:true`. Reproducción: 201 y true con ningún envío. | Usuario bloqueado esperando un correo inexistente; códigos además terminan en logs. Separar modo de desarrollo explícito y fallo real; no afirmar envío. Evitar que el frontend ignore `mail_enviado:false` cuando sí hay error SMTP. | F11/A15 |
| H14 | Tres fallos actuales de suite: registro sin `nombre_usuario` espera 404 y obtiene 422; reset usa alta inválida sin nombre y no genera código; conteo inseguridad espera 1135, carga 1121. | La suite integral **no está verde**. Dos fixtures quedaron incompatibles con el contrato nuevo y una expectativa con los datos nuevos. Arreglar preparación/aserciones, conservar pruebas del flujo. CI ejecuta esta suite con PostGIS: no hay evidencia de verde para este árbol local. | T01/T05/A22 |
| H15 | Migración 006 copia email (hasta 255) a nombre (50) y agrega unicidad. Email sintético de más de 50 dio `StringDataRightTruncation`. | Upgrade desde cuentas válidas de 005 puede fallar y bloquear arranque. Backfill determinista con longitud/unicidad, sin identidad personal hardcodeada; probar datos previos reales anonimizados. | A14/F11 |
| H16 | `/health` responde 200 con DB caída; watchdog y healthcheck de Compose sólo comprueban éxito HTTP. Reproducción: 200 + `estado:degradado`. | Falso positivo de disponibilidad. Separar liveness/readiness y comprobar esquema/capas requeridas; no reiniciar ciegamente ante una falla externa. | T04/T06 |
| H17 | Clima cacheado vencido se devuelve sin fecha ni estado de fallback; inseguridad/corredores sólo se actualizan al montar o reintentar. | Las capas dependen de hora/prensa, pero una pestaña abierta mantiene ajustes viejos mientras hotspots sí renueva cada cinco minutos. Exponer timestamp/estado y política de refresco consistente; probar cambio de franja y pérdida de proveedor. Clima simulado sin red devolvió únicamente humedad/lluvia/temperatura. | A10/A11/A15/F09 |
| H18 | Política de privacidad afirma que no hay cuentas/email y describe expiración/consenso como borrado, aunque las filas persisten. REPASO_FINAL documenta credencial de prueba y hash anterior y afirma ausencia de publicación, en conflicto con infraestructura Funnel posterior. | Actualizar inventario de datos/retención para F11 y corregir “ocultar” vs “borrar”. Retirar material de credenciales de documentación antes de publicar. No se afirma que la credencial anterior siga vigente: F11 ya no usa ese login. No se copió ese material al assessment ni se incluyó en su commit. | G01/F11/T04 |

## Otras observaciones que requieren validación, no fallas graves demostradas

- “Rápida” y “Equilibrada” comparan `r.min` (sin tráfico), aunque hay `etaTrafico.con_trafico_min`. Puede diferir de la opción más rápida ahora. Aclarar contrato o usar ETA vigente; no se alteró la decisión de ranking.
- El botón “Menor exposición” sigue visible cuando ninguna ruta supera cobertura; el fallback selecciona la rápida. El aviso por tarjeta ayuda, pero el nombre del botón no refleja ese estado.
- `calcularRuta` no cancela ni identifica respuestas obsoletas como sí hace el buscador. Revisar respuestas fuera de orden al editar destino/recalcular y pérdida de sesión durante navegación. No se reprodujo visualmente en esta sesión.
- `auth._conn()` abre conexiones fuera del pool de `main`; sus contextos transaccionales no son cierre explícito. No se demostró fuga sostenida, pero faltan timeout/pool/acotamiento en el nuevo flujo.
- El limitador IP necesita prueba detrás de Vite/Nginx/Funnel: Vite no configura explícitamente generación de X-Forwarded-For y Uvicorn confía sólo en loopback. No se demostró qué IP llega desde todos los caminos públicos; evitar asumir límites por usuario real.
- El script de vigilancia puede terminar cualquier Python cuyo comando incluya `multiprocessing.spawn`, sin restringirlo al proyecto. Riesgo operativo para otros trabajos Python de la PC; no se ejecutó el watchdog ni se mataron procesos ajenos.
- `.dockerignore` excluye `venv*/` pero no `.venv_test/`; `COPY .` puede incorporar ese entorno local al construir. El directorio está sin seguimiento. Excluir entornos y evidencias privadas del contexto; inspeccionar imagen final antes de publicarla.
- Falta nueva auditoría visual/accesible de F11, autorización/privacidad multiusuario y tests de concurrencia de consumo OTP. Los 108 tests no prueban todo ese flujo.
- La calibración de probabilidades, estabilidad temporal, pesos de scoring y cobertura GBA tienen limitaciones ya registradas. DEC-022 mantiene sexo por decisión de Rodo; DEC-023 mantiene radio 600 m; DEC-026 no autoriza rediseñar el score por magnitud. Esta auditoría no revierte esas decisiones.

## Qué se conserva y qué no puede darse por cerrado

Se comprobaron el build, lint, gran parte de la suite, carga real de 740 hotspots + 243 corredores + 1121 hotspots de inseguridad en base nueva (el fallo es la expectativa de 1135), modelo con 53 columnas y huella vigente. Existen defensas valiosas: token de borrado no publicado, SQL parametrizado en los caminos revisados, cookies con flags de protección, escape/textContent para noticias, locks de migraciones y separación de base de pruebas.

No se encontró evidencia aquí de pérdida de la base, extracción de secretos por un atacante ni fallo total de la aplicación. **Tampoco corresponde mantener “validado sin pendientes” para A05/A07/A18 o afirmar CI verde sobre estos cambios**, dados H01/H02/H06/H08/H14. El estado operativo se actualiza en el BACKLOG único, no en una segunda lista.

## Secuencia recomendada de remediación (propuesta, no ejecutada)

1. **Antes de exposición externa:** H04–H07, H11 y revisión de secretos de H18. Endurecer cuentas, identidad de votos, cuotas y superficie de DB.
2. **Integridad del producto:** H01–H03 y H12. Medir efecto sobre rutas/noticias reales antes de aprobar cambios que alteren recomendaciones; conservar evidencia previa.
3. **Entrega reproducible:** H08/H09/H13–H16. Corregir proveedor, correo, migración, datos de despliegue y pruebas; repetir desde clon limpio y base vacía.
4. **Defensa y operación:** H10/H17/H18; actualizar tesis y gestión según implementación comprobada, validar refrescos y E2E móvil.

Rodo decide las políticas que cambien comportamiento (identidad/anónimo, fechas inciertas para ajustes, contrato de cobertura y evaluación final). No hace falta rehacer todo el proyecto; sí resolver estos caminos concretos y probar que no reaparecen.

## Reproducibilidad

Los scripts adjuntos no se usan para iniciar la aplicación ni deben apuntarse a una base productiva. `probe_backend.py` fuerza un servidor aislado en **127.0.0.1:55439**, crea una base con nombre aleatorio y la borra al finalizar. Sus credenciales son deliberadamente ficticias para ese contenedor. El correo está sustituido, excepto el camino SMTP ausente (cuyo logger también se intercepta). Los proveedores se simulan cuando corresponde. Las respuestas de API y SQL son reales dentro de ese montaje.

Comandos ejecutados desde la raíz, salvo los de frontend/backend que se ejecutaron en sus carpetas:

```powershell
node docs/assessment_2026-10-22/probe_cobertura.mjs
.\backend\venv312\Scripts\python.exe docs/assessment_2026-10-22/probe_backend.py
# En frontend/: vitest run, eslint ., vite build --outDir dist_assessment
# En backend/: pytest tests -q con MOTOSAFE_TEST_DATABASE_URL del servidor desechable
```

No se guardaron correos reales, cookies, códigos de usuarios ni secretos en las salidas. La prueba de cobertura adapta únicamente la resolución de imports y el entorno Vite para poder ejecutarse en Node; usa las funciones y constantes de cálculo reales, sin reimplementarlas.
