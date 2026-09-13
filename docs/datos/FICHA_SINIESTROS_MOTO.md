# Ficha de datos — siniestros con motos

**Estado:** ficha inicial basada en archivos locales; no sustituye licencia ni
metadatos del publicador. **Ítems:** D01, A02, A03.

| Campo | Descripción |
|---|---|
| Unidad | Siniestro vial con registro de una víctima en moto, tras los filtros del pipeline. |
| Fuente local | `data/motos_limpio.csv`, complementado por `data/siniestros_viales_victimas.csv` y `data/clima_historico.csv`. |
| Cobertura conocida | Hechos históricos de CABA; no constituye muestra representativa ni cobertura predictiva de GBA. |
| Resultado | `gravedad_siniestro`, categoría del siniestro registrado. |
| Variables | Hora, día, comuna, tipo de vía, contraparte, clima y campos demográficos de víctima cuando existen. |
| Transformaciones | Normalización de texto, descarte de hora/clima ausente, cruce por fecha-hora, tratamiento de edad fuera de 14–95 y bandera `edad_desconocida`. |
| Faltantes relevantes | Edad y sexo pueden faltar por calidad/completitud del registro. No se asumen aleatorios. |
| Limitaciones | El cruce climático puede reducir filas; variables agregadas por comuna requieren fecha de disponibilidad para evaluación temporal. |
| Privacidad | Los artefactos de evaluación deben contener sólo métricas agregadas, nunca filas ni coordenadas personales. |

La procedencia, licencia, fecha de descarga y diccionario original deben
completarse con las fuentes primarias antes de una publicación académica.
