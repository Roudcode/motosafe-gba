# Fichas de fuentes de datos y servicios externos (D01)

Actualizado: 2026-10-06 (SES-078). Licencias y políticas verificadas ese día en las páginas oficiales enlazadas; pueden cambiar. Las cifras de período y registros salen de `backend/metadatos_capas.json` (`notebooks/generar_metadatos_capas.py`). El modelo tiene su ficha en [MODELO_VIGENTE_2026-09-07.md](../modelo/MODELO_VIGENTE_2026-09-07.md) y [CONTRATO_Y_EVALUACION.md](../modelo/CONTRATO_Y_EVALUACION.md); el detalle de los siniestros con moto, en [FICHA_SINIESTROS_MOTO.md](FICHA_SINIESTROS_MOTO.md).

## Datasets

### Siniestros viales (GCBA)

| Campo | Valor |
|---|---|
| Publicador | Secretaría de Transporte, Subsecretaría de Planificación de la Movilidad, Observatorio de Movilidad y Seguridad Vial (GCBA) |
| Página | https://data.buenosaires.gob.ar/dataset/victimas-siniestros-viales |
| Licencia | Creative Commons Attribution (según la página del dataset). Requiere citar la fuente. |
| Recursos usados | `siniestros_viales_hechos.csv`, `siniestros_viales_victimas.csv` |
| Actualización | Anual. Última del publicador: 2026-07-14. |
| Período usado | 2019-01-01 a 2025-12-31; 23.343 siniestros con moto tras la limpieza (`motos_limpio.csv`) |
| Unidad | Siniestro con al menos una víctima en moto |
| Filtros | Limpieza del notebook histórico (paso 0 del pipeline): moto como modo de desplazamiento, coordenadas y hora válidas |
| Alimenta | Modelo de gravedad, hotspots, corredores, umbrales |
| Versionado | Crudos no versionados (`data/` ignorado); derivados de capas versionados (SES-076) |
| Límites | Solo CABA. Faltantes de edad y sexo no aleatorios (A03). La limpieza no tiene script canónico (A19, ya resuelto por `limpiar_siniestros_motos.py`, SES-112). **Agregado 2026-10-21**: se buscó un diccionario de datos oficial del publicador (descripción campo por campo de los CSV) en la página del dataset y no existe -- la página solo describe el recurso en una frase ("fecha y ubicación del hecho y tipo de transporte"), sin detalle de columnas. Lo más cercano es un PDF de metodología ("Metodología y fuentes de información para las estadísticas de siniestros viales") que puede tener definiciones, pero no se pudo confirmar su contenido desde acá. Para dudas puntuales sobre un campo, el publicador deja un contacto: observatoriovial@buenosaires.gob.ar. Se documenta la ausencia del diccionario como límite real de la fuente, no como un pendiente nuestro de código. |

### Delitos (GCBA)

| Campo | Valor |
|---|---|
| Publicador | Dirección General Estadística Criminal y Mapa del Delito, Ministerio de Seguridad (GCBA) |
| Página | https://data.buenosaires.gob.ar/dataset/delitos |
| Licencia | Creative Commons Attribution (según la página del dataset) |
| Recursos usados | CSV anuales 2016–2025, unidos en `delitos_caba.csv` por `notebooks/fetch_delitos_caba.py` |
| Actualización | Anual. Última del publicador: 2026-06-22. |
| Período usado | Ventana de los últimos 3 años del dataset: 2023-01-01 a 2025-12-31 (447.938 delitos; 15.792 con uso de moto) |
| Unidad | Delito registrado con coordenadas |
| Filtros | Ventana de 3 años; general excluye infracciones de tránsito; moto = `uso_moto == 'SI'` |
| Alimenta | Hotspots de inseguridad (general y moto), índice de inseguridad por comuna (feature del modelo) |
| Límites | Coordenadas ausentes o cero sin limpieza uniforme entre pipelines (A20). Delito registrado no equivale a riesgo vial. |

### Clima histórico y en vivo (Open-Meteo)

| Campo | Valor |
|---|---|
| Servicio | https://open-meteo.com — términos: https://open-meteo.com/en/terms |
| Licencia | CC BY 4.0, con atribución a Open-Meteo. Uso gratuito solo **no comercial**: menos de 10.000 pedidos por día, 5.000 por hora y 600 por minuto. |
| Uso | `fetch_clima_historico.py` (clima por hora para entrenar) y la API en vivo (`obtener_clima_actual`, con caché de 10 minutos) |
| Límites | Un MVP comercial requiere el plan pago. La atribución se muestra en el control de atribución del mapa desde SES-078. **Agregado 2026-10-21**: los términos (https://open-meteo.com/en/terms) definen "no comercial" por remisión a Creative Commons -- califican sitios/apps privados o sin fines de lucro, sin suscripción ni publicidad, domótica personal, investigación pública e investigación educativa. Se considera comercial cualquier sitio/app con suscripción o publicidad, producto o actividad promocional comercial, o investigación no publicada dentro de una empresa comercial. MotoSafe GBA, como proyecto académico sin publicidad ni suscripción, encaja en la categoría no comercial mientras se mantenga así; pasaría a necesitar el plan pago si alguna vez se monetiza o lleva publicidad. |

### Prensa (medios digitales)

| Campo | Valor |
|---|---|
| Fuentes | Medios del GBA vía RSS, sitemaps y secciones listadas en `backend/scrapear_noticias_robos.py`. Google Noticias se retiró por su `robots.txt` (DEC-011). |
| Qué se guarda | Titular, URL, fuente, fechas, tipo de hecho y ubicación geocodificada. No se guarda el texto de la nota. |
| Derechos | Los textos son de cada medio. La app muestra el titular con enlace a la nota. |
| Identificación | User-Agent `MotoSafeGBA-tesis-USAL/1.0`, pausas entre pedidos y respeto de `robots.txt` |
| Vigencia | 30 días por fecha de publicación (o de ingesta si falta) |
| Límites | Precisión temática 0,84 y recall 0,923 medidos (A09); geocodificación validada por zona (SES-069) |

## Servicios externos

| Servicio | Uso en MotoSafe | Licencia / política (verificada) | Estado de cumplimiento |
|---|---|---|---|
| **Nominatim** (OSM) | Geocodificación del scraper (backend), geocodificación de prensa, y respaldo de `/lugares` cuando TomTom no encuentra nada relevante (SES-108) | Datos ODbL con atribución. Máximo 1 pedido por segundo (4/min para scripts periódicos), User-Agent o Referer identificable, caché recomendada. **Prohíbe el autocompletado**, consultas sistemáticas y reventa. https://operations.osmfoundation.org/policies/nominatim/ | Scraper: 15 s entre pedidos (cumple el límite de 4/min para scripts periódicos, SES-102), User-Agent propio, caché por corrida. `/lugares`: NO es autocompletado -- TomTom sigue siendo quien responde mientras se escribe; Nominatim se consulta como mucho una vez por búsqueda confirmada, solo cuando TomTom no encontró nada con relación real a lo buscado (`_algun_resultado_relevante`), y el resultado se cachea igual que el de TomTom. Resuelto A18 (autocompletado) y ampliado en SES-108 (respaldo). |
| **OSRM** (servidor demo) | Geometría de corredores, una vez, offline (`fetch_corredores_geometria.py`) | Máximo 1 pedido por segundo, uso razonable no comercial, sin garantías. https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server | La pausa era de 0,3 s (unos 3 por segundo); se corrigió a 1,1 s en SES-078. El ruteo en vivo ya no lo usa (TomTom). |
| **TomTom** | Ruteo (`/rutas`) y teselas de tráfico | Plan gratuito: 20.000 pedidos de ruteo y 200.000 de teselas de tráfico por mes. La página de precios no aclara explícitamente si el plan gratuito permite producción, solo lo describe como "free evaluation" ("Sign up for a free evaluation and start testing TomTom APIs right away"). https://docs.tomtom.com/pricing, https://docs.tomtom.com/legal/terms-and-conditions | Clave fuera del repo. **Revisado 2026-10-21**: el marco de "evaluación" sugiere que el uso previsto del plan gratuito es desarrollo/pruebas, no necesariamente producción sostenida -- no se encontró una frase explícita que lo prohíba, pero tampoco una que lo autorice sin reservas. Sigue pendiente, antes de cualquier uso más allá de un MVP académico/de evaluación, confirmar con TomTom (soporte/ventas) si el volumen y el carácter del proyecto encajan en el plan gratuito o requieren uno pago. |
| **OpenFreeMap** | Teselas del mapa base | Uso comercial permitido, sin límites declarados. Atribución obligatoria «OpenFreeMap © OpenMapTiles Data from OpenStreetMap». https://openfreemap.org | MapLibre muestra la atribución (`attributionControl`). |

## Pendientes derivados

1. Cuota de Nominatim para uso de producción (las búsquedas del frontend ya son una por confirmación; A18 quedó resuelto en SES-079).
2. **Actualizado 2026-10-21**: los términos de Open-Meteo ya están revisados y resumidos arriba -- MotoSafe GBA encaja hoy en "no comercial" (sin publicidad ni suscripción). Los de TomTom quedan sin resolver del todo: la página de precios enmarca el plan gratuito como "evaluación", no como autorización explícita de producción; confirmar con TomTom antes de cualquier uso más allá de un MVP académico.
