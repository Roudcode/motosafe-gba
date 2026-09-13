# Cobertura, procedencia y límites de las capas de riesgo

**Ítems:** A05, A06, A09, A10, A11, D03, D04.  
**Estado:** implementación inicial de cobertura por fuente; validación externa pendiente.

## Qué muestra el comparador

Para cada alternativa se muestrean hasta 120 vértices de su trazado. Se informa
por separado la proporción cercana a registros de **siniestros** y de
**inseguridad**. Una fuente ausente se muestra como `sin datos`, que es
distinto de `0%`: el primero no permite concluir nada y el segundo indica que
la fuente disponible no tuvo registros próximos bajo el radio configurado.

La recomendación «menor exposición» exige al menos 60% de cobertura del eje
histórico de siniestros. Registros de inseguridad no reemplazan esa cobertura:
ambas capas tienen procedencia, unidad y significado distintos. El resultado
compara alternativas del mismo pedido; no estima siniestralidad por viaje.

## Procedencia y actualización

| Capa | Procedencia | Unidad | Actualización / TTL | Límite visible |
|---|---|---|---|---|
| Hotspots | Siniestros históricos procesados en CABA | Punto/cluster | Backend consulta cada 5 min desde el cliente | No cubre ni predice automáticamente GBA. |
| Corredores | Corredores offline derivados de siniestros | Geometría de calle | Carga al iniciar; cache local de última respuesta | Falta fecha de generación publicada por fuente. |
| Inseguridad | Delitos GCBA procesados, general o con moto | Punto/cluster | Carga al iniciar; cache local de última respuesta | No equivale a gravedad vial. |
| Prensa | Noticias filtradas y geocodificadas | Hecho puntual aproximado | Cliente consulta cada 10 min; vigencia de 30 días | Puede ser ambiguo, incompleto o tener ubicación aproximada. |
| Reportes comunitarios | Personas usuarias | Hecho puntual | Consulta cada 30 s; vigencia por categoría | No son verificados automáticamente. |

La aplicación conserva la última respuesta local cuando una actualización
falla. Esa persistencia no debe presentarse como fecha de origen del dato. Para
cerrar A10/A11 falta devolver desde backend la fecha de generación de cada
artefacto y mostrarla en la interfaz.

## Validación pendiente y reproducible

`docs/evidencias/2026-09-13/A09/prensa_etiquetada.csv` es la plantilla para un
conjunto revisado por persona. Ejecutar:

```powershell
python backend/evaluar_extractor_prensa.py docs/evidencias/2026-09-13/A09/prensa_etiquetada.csv
```

El script entrega precisión, recall, abstenciones y error geográfico sólo si
se completan etiquetas reales. No usar pruebas sintéticas como métrica de
calidad de prensa.

Las rutas de referencia se registran en
`docs/evidencias/2026-09-13/D03/rutas_referencia.csv`. Deben contener casos
con cobertura parcial, empate, desvío y fuentes discordantes antes de ajustar
el radio de 60% o los pesos de ranking.
