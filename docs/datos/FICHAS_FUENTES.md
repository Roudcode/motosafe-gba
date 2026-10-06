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
| Límites | Solo CABA. Faltantes de edad y sexo no aleatorios (A03). La limpieza no tiene script canónico (A19). |

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
| Límites | Un MVP comercial requiere el plan pago. La atribución se muestra en el control de atribución del mapa desde SES-078. |

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
| **Nominatim** (OSM) | Geocodificación del scraper (backend) y del buscador del frontend | Datos ODbL con atribución. Máximo 1 pedido por segundo, User-Agent o Referer identificable, caché recomendada. **Prohíbe el autocompletado**, consultas sistemáticas y reventa. https://operations.osmfoundation.org/policies/nominatim/ | Scraper: 1,1 s entre pedidos y User-Agent propio. Frontend: sin autocompletado desde SES-079 (`useBusquedaDireccion`); un pedido por búsqueda confirmada (Enter o botón). Resuelto A18. |
| **OSRM** (servidor demo) | Geometría de corredores, una vez, offline (`fetch_corredores_geometria.py`) | Máximo 1 pedido por segundo, uso razonable no comercial, sin garantías. https://github.com/Project-OSRM/osrm-backend/wiki/Demo-server | La pausa era de 0,3 s (unos 3 por segundo); se corrigió a 1,1 s en SES-078. El ruteo en vivo ya no lo usa (TomTom). |
| **TomTom** | Ruteo (`/rutas`) y teselas de tráfico | Plan gratuito: 20.000 pedidos de ruteo y 200.000 de teselas de tráfico por mes. La página de precios no aclara el uso comercial en el plan gratuito. https://docs.tomtom.com/pricing | Clave fuera del repo. Falta revisar los términos de servicio antes de un uso comercial. |
| **OpenFreeMap** | Teselas del mapa base | Uso comercial permitido, sin límites declarados. Atribución obligatoria «OpenFreeMap © OpenMapTiles Data from OpenStreetMap». https://openfreemap.org | MapLibre muestra la atribución (`attributionControl`). |

## Pendientes derivados

1. Cuota de Nominatim para uso de producción (las búsquedas del frontend ya son una por confirmación; A18 quedó resuelto en SES-079).
2. Términos de servicio de Open-Meteo y TomTom antes de cualquier uso comercial del MVP.
