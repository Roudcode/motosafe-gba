# Evidencia de la auditoría del 23/10/2026

Ejecutar desde la raíz del repositorio, con el entorno Python del backend y las dependencias instaladas:

```powershell
& .\backend\venv312\Scripts\python.exe -X utf8 docs/tesis/auditoria_2026-10-23/verificar_modelo_y_costos.py
node docs/tesis/auditoria_2026-10-23/probe_rutas.mjs
```

El primer script lee el modelo, las columnas y los datos locales; no reentrena ni promueve artefactos. Escribe `verificaciones.json` junto al script: guardar una copia aparte si se quiere preservar el resultado fechado. Los valores dependen de conservar los insumos auditados. El segundo probe importa la lógica de rutas real y sustituye solamente sus imports por constantes ordinales de la versión auditada para probarla sin iniciar la interfaz.

`VERIFICACIONES.json` es la salida cuantitativa guardada de esta auditoría. `sensibilidad_reproducida.txt` contiene la repetición del análisis de sensibilidad. Estos archivos no incluyen los resultados de pytest/vitest: sus recuentos se registraron a partir de las ejecuciones en la sesión y se distinguen de la evidencia adjunta.

La evaluación temporal se repitió mediante `docs/evidencias/2026-10-18/A04-decision-costo-por-clase/matriz_confusion_sin_edad.py`; no reemplazó al pickle. Se probó también la variante con el índice que consume backend. Ninguna recuperó exactamente la matriz temporal del Word. Esto requiere rastrear la versión original antes de homologar cifras.

Se hizo lectura pública de web y `/health`; no se hizo auditoría autenticada de producción. Las 33 pruebas PostgreSQL usaron una base efímera PostGIS independiente, eliminada al finalizar. No reutilizar una base personal/productiva para repetirlas.

La extracción completa del Word, el snapshot y el PDF temporal permanecieron fuera del commit para no duplicar el documento del autor. Los localizadores de párrafo del informe corresponden al SHA del Word que figura en su encabezado.
