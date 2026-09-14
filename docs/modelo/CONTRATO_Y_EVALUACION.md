# Contrato académico y evaluación del modelo de gravedad

**Estado:** protocolo temporal implementado; evaluación interna del artefacto vigente reproducida. La evaluación temporal independiente sigue pendiente.
**Ítems:** A01, A02, A03, A04, D01, D02.
**Actualizado:** 2026-09-13.

## Referencia vigente del artefacto

La ficha [MODELO_VIGENTE_2026-09-07.md](MODELO_VIGENTE_2026-09-07.md) es la única referencia para hiperparámetros y métricas del pickle que carga el backend. Registra 55 columnas, 300 árboles, profundidad 12, hojas mínimas de 5, `balanced_subsample` y la reproducción del split interno. Los resultados de Fase 4 pertenecen a un modelo anterior de 66 columnas y no deben mezclarse con esta versión.

## Qué estima y qué no estima

MotoSafe GBA usa un clasificador multiclase para estimar la distribución de
`gravedad_siniestro` **condicionada a que ocurrió un siniestro** y a las
variables de contexto disponibles en el registro. Su salida es:

`P(gravedad = c | siniestro observado, contexto registrado)`

No estima la probabilidad de que una persona tenga un siniestro por viaje,
kilómetro, tramo o ventana temporal. Por ello, el resultado no prueba que una
ruta sea segura ni cuantifica el riesgo individual. La interfaz debe hablar de
gravedad estimada y cobertura histórica; la exposición de rutas se deriva de
capas espaciales separadas y tiene sus propios límites.

## Protocolo temporal independiente

El script `notebooks/evaluar_modelo_academico.py` separa tres momentos:

1. entrenamiento: años anteriores al de selección;
2. selección: un año completo posterior, para comparar configuraciones
   predefinidas sin tocar la evaluación final;
3. evaluación: un año todavía posterior, usado una vez para informar el
   desempeño temporal.

La imputación de edad, las categorías one-hot y el conjunto de columnas se
ajustan exclusivamente con entrenamiento. El índice de inseguridad agregado
queda fuera de esta evaluación hasta contar con una versión fechada y
reconstruible por corte temporal. Así se evita atribuir al pasado una capa
construida con datos posteriores.

El protocolo no sobrescribe `modelo_final.pkl`, `columnas_modelo.pkl`, datos
ni artefactos del backend. Escribir resultados requiere `--output` explícito.

## Faltantes, sesgo y unidad de inferencia

La edad y el sexo provienen de víctimas registradas. La ausencia de edad se
conserva como `edad_desconocida`; no se interpreta como una característica de
la persona. El reporte compara el modelo base con ablaciones que retiran edad,
indicador de ausencia y variables demográficas. Informa distribución de
faltantes y métricas por estrato, pero no permite conclusiones causales ni de
equidad individual.

Los perfiles agregados de hotspots no representan víctimas reales ni deben
presentarse como perfil del conductor de una ruta. Su uso debe revisarse por
separado antes de cualquier cambio de producto.

## Score, calibración y costos

El score es una probabilidad de clase estimada por el modelo para el universo
condicionado anterior. Se evalúa con Brier por clase y ECE multicategoría,
además de precisión, recall y F1. Una probabilidad no se comunica como certeza.

No existe todavía una política aprobada de costos para alertas falsas frente a
omisiones de gravedad. El script deja trazabilidad de la matriz de confusión;
la elección de umbrales o acciones debe compararse bajo escenarios documentados
y aprobarse antes de afectar alertas o recomendaciones.

## Ejecución cuando el entorno esté disponible

Desde la raíz del repositorio:

```powershell
python notebooks/evaluar_modelo_academico.py --selection-year 2023 --test-year 2024 --output docs/evidencias/2026-09-13/A01-A04
```

Usar años que existan completos en el dataset. Conservar el JSON y CSV
producidos como evidencia, revisar soporte por clase y registrar los resultados
reales en `docs/gestion/VALIDACION.md` y `BITACORA.md`.
