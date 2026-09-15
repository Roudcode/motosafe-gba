# Pruebas técnicas del estado actual

Fecha: 2026-09-15. Evaluador: Codex (IA). Base Git: `08bc55610c07595b1f50648880e3d822b131270d`. IDs: G02, T02; observaciones relacionadas con A01, A11, A22, V08 y V12.

## Resultado comprobado

| Comprobación ejecutada | Resultado | Límite |
|---|---|---|
| `npm.cmd test`, desde frontend | Falló: `vitest` no reconocido | Problema de lanzador local; no fue un fallo de aserciones. |
| `node node_modules/vitest/vitest.mjs run`, desde frontend | 80 pruebas aprobadas, 4 archivos; 2,11 s informados por Vitest | Utilidades de geometría, riesgo de ruta, tiempo y almacenamiento; no renderiza los flujos completos. |
| `node node_modules/eslint/bin/eslint.js .`, desde frontend | Salida 0, sin errores | Análisis estático. |
| `node node_modules/vite/bin/vite.js build`, desde frontend | Salida 0; 1.835 módulos; compilación 4,88 s | Advertencia por JS de 1.292,98 kB (357,29 kB gzip); no es medición de rendimiento móvil. |
| `.\venv\Scripts\python.exe -m pytest -q -p no:cacheprovider`, desde backend | 65 pruebas aprobadas en 78,53 s | 1.200 advertencias de deprecación de NumPy al cargar con joblib. DB simulada; `/predecir` usa artefacto real. |
| `node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort` | Servidor Vite inició en HTTPS local | No se ejecutó el lanzador general ni la ingesta de noticias. |
| Apertura de `https://localhost:5173/` mediante navegador integrado | Bloqueada: `net::ERR_CERT_AUTHORITY_INVALID` | No se aceptó automáticamente el certificado ni se omitió su validación. La respuesta «acepto» del usuario en el chat no demostró aceptación dentro del navegador. |

Resultados transcritos de las salidas de herramientas de esta sesión; no se adjuntan logs completos. El intérprete del backend sí funciona en esta sesión, aunque documentación histórica indicaba lo contrario.

## Tareas del instrumento: evidencia real

| Ítem | Alcance verificado | Estado de la ejecución visual |
|---|---|---|
| 4: buscar y activar capa | Código contiene entrada «Buscar zona o avenida» y panel de capas. | No ejecutada: acceso bloqueado antes de cargar la aplicación. |
| 5: comparar dos rutas y explicar cobertura | Utilidades probadas; tarjetas, cobertura por fuente y aviso revisados en código. | No ejecutada con proveedor de rutas real. |
| 6: Motos y abrir noticia | Código contiene activación de Prensa, filtro Motos, detalle con fuente y antigüedad. | No ejecutada; disponibilidad de noticias y apertura real no comprobadas. |
| 7–10: percepción y comprensión | Se revisaron textos del código. | Sin evaluación humana ni verificación visual de legibilidad. |

El impedimento técnico no es un fracaso atribuible a un motociclista. No registrar estas tareas como «no completadas» por participantes reales: no hubo participantes.

## Observaciones trazables del código

1. **Cobertura y ayuda (A11):** `frontend/src/App.jsx:1716` explica en un atributo `title` que se mide proximidad de puntos del trazado a registros. La tarjeta muestra siniestros e inseguridad por separado y el aviso de alcance está en la línea 1733. Conviene ensayar su comprensión en pantalla táctil; no se verificó cómo presenta esa ayuda el navegador.
2. **Entrada a Motos (V08):** `frontend/src/components/CapasPanel.jsx` solo muestra los filtros después de activar Prensa. «Seguridad» corresponde internamente al filtro `inseguridad`. Es una ambigüedad posible para preguntar, no una confusión humana medida.
3. **Bienvenida (A01/V12):** `frontend/src/components/Onboarding.jsx` menciona historial, recálculo y Machine Learning, pero no explica allí la gravedad condicionada. El detalle de zona sí advierte que no estima la probabilidad de sufrir un siniestro durante el viaje (`App.jsx:1827`). Evaluar si el usuario llega a leerlo.
4. **Significado de cobertura (A11):** `frontend/src/utils/riesgoRuta.js` calcula proporción de vértices muestreados próximos a zonas; no mide exactamente porcentaje de kilómetros ni completitud del registro de siniestros. Si no hay zonas de una fuente devuelve `null`; eso por sí solo no distingue una fuente vacía de una que falló.
5. **Fecha y precisión de prensa (A10/A11):** `MapaMotoSafe.jsx:96` y `:101` construyen texto con fuente, antigüedad y precisión. `App.jsx:490` usa publicación o, si falta, creación. No se comprobó el contenido vigente de la base.
6. **Ejecución local (A22/T02):** el lanzador npm no encontró Vitest, aunque la invocación directa del módulo sí pasó. El certificado impidió el recorrido de interfaz. Ambos límites deben resolverse antes de una sesión real.

## Pendientes y alcance

G02 y T02 permanecen en curso. Falta completar la prueba de interfaz tras resolver el certificado, confirmar backend/PostgreSQL y servicios externos, probar las tres tareas en móvil/escritorio y aplicar el instrumento con consentimiento a personas reales. No se ensayaron GPS de campo, carga concurrente, despliegue, backup, ingesta ni una nueva evaluación del modelo. No se modificaron código funcional, modelo, datasets ni el Word de tesis. Cambios documentales sin commit ni push en esta sesión.
