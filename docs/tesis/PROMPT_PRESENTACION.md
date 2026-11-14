# ACTUALIZACIÓN: versión dinámica con animaciones y demo de la app

No uses Gamma (el profesor ya lo tiene muy visto). Para algo dinámico, con animaciones reales
y que muestre la app funcionando, lo mejor es pedirle a **Claude.ai (chat nuevo)** una
presentación en **HTML** (tipo reveal.js), no un .pptx estático. Claude puede meter
transiciones entre slides, elementos que aparecen animados al avanzar, y **las capturas reales
de la app ya guardadas en el repo** (`docs/tesis/capturas_prod/`: mapa con capas,
panel de prensa, comparador de rutas, vista móvil, login).

### Qué hacer en el chat nuevo de Claude.ai
1. Empezá el chat.
2. Subí las 5 imágenes de `docs/tesis/capturas_prod/`.
3. Pegá el prompt de más abajo, agregando al final este párrafo:

> Quiero que sea una presentación HTML interactiva (no PowerPoint), con transiciones animadas
> entre secciones (fade/slide al navegar), números que cuentan hacia arriba cuando aparecen
> (ej. "740 hotspots", "168 pruebas"), y que uses las capturas reales de la app que te adjunté
> para mostrar el mapa, el comparador de rutas y la vista móvil funcionando — no inventes
> mockups, usá esas imágenes tal cual. Navegable con flechas de teclado o clics, para mostrarla
> en pantalla completa durante la defensa.

Eso te da algo que se ve vivo, con la app real adentro, y nada parecido a Gamma.

---

# Dónde ponerlo

**Recomendado: Gamma.app** (gamma.app, gratis, hace decks visuales buenos solo con un prompt de texto, exportable a PPTX/PDF). Pegás el prompt de abajo tal cual en "Generate" → "Paste in text".

Alternativa: Claude.ai (claude.ai, chat nuevo) pidiéndole "generá una presentación .pptx" con este mismo prompt — hace el archivo pero el diseño es más simple que Gamma.

Si usás cualquiera de las dos, **adjuntá también** `docs/tesis/MotoSafe_GBA_Capitulos_1_a_8_FINAL.docx` (la tesis completa) como fuente adicional, así puede citar datos exactos si el prompt se queda corto en algo.

---

# Prompt (pegar tal cual)

Necesito una presentación completa y profesional para la defensa de mi Proyecto Final de Ingeniería en Informática (Universidad del Salvador). El proyecto es **MotoSafe GBA**: una plataforma web que ayuda a motociclistas del Área Metropolitana de Buenos Aires a evaluar el riesgo vial antes de salir, cruzando siniestros históricos, inseguridad, prensa y reportes comunitarios en un mapa interactivo.

Quiero ~18-22 slides, tono académico pero claro (no vendedor), con números reales (no inventes ninguno que no te dé acá). Estructura:

1. **Portada**: MotoSafe GBA, subtítulo "Plataforma web de riesgo vial para motociclistas del AMBA", autor Rodolfo Barrionuevo, Universidad del Salvador.
2. **El problema**: en Argentina los motociclistas son el 46% de las víctimas fatales de tránsito (ANSV, 2025). La información para decidir una ruta está fragmentada (siniestros, inseguridad, prensa, clima, cada uno con su propia fuente y vigencia).
3. **Hipótesis**: la utilidad no está en predecir con precisión un siniestro individual, sino en la trazabilidad de las fuentes — una interfaz que declare qué sabe, desde cuándo y con qué cobertura es más defendible que un único indicador de riesgo.
4. **Qué es MotoSafe GBA (resumen funcional)**: mapa con 4 capas de riesgo activables (siniestros, hotspots viales, inseguridad general, prensa), comparador de hasta 3 rutas con cobertura por fuente, reportes comunitarios, panel de noticias filtrable.
5. **Arquitectura técnica**: React + Vite + MapLibre (frontend), FastAPI + Python (backend), PostgreSQL con PostGIS (base de datos), Random Forest con scikit-learn (modelo de gravedad). Desplegado 100% en la nube, sin costo, sin tarjeta de crédito: Render (frontend y API), Supabase (base de datos), GitHub Actions (scraper de prensa automático).
6. **El modelo de Machine Learning**: Random Forest de 300 árboles, entrenado sobre 23.338 siniestros reales de motociclistas en CABA (2019-2025). Estima gravedad (leve/grave/mortal) condicionada a que un siniestro ya ocurrió — NO predice la probabilidad de que ocurra un accidente.
7. **Validación honesta del modelo**: evaluación con split aleatorio da F1 macro 0,368; evaluación temporal (entrenar con años pasados, medir contra un año nunca visto, como pasaría en uso real) da F1 macro 0,3032 — una diferencia de ~6,5 puntos que demuestra que el protocolo de evaluación cambia la conclusión. El modelo prioriza bien entre zonas, pero no es una probabilidad exacta.
8. **Clustering de zonas de riesgo**: migración de DBSCAN a HDBSCAN resolvió un problema real de cobertura (pasó de 49,9% a 75,6% de los siniestros de moto asignados a alguna zona), dando 740 hotspots viales y 243 corredores de riesgo.
9. **Validación con usuarios reales**: 12 motociclistas probaron la app. El mapa se usa sin dificultad (10 de 12 completaron tareas sin ayuda), pero comprender qué mide el score es más difícil (solo 4 de 12 explicaron bien la cobertura; 2 de 12 confundieron el modelo con una predicción de accidente). Esto llevó a simplificar la interfaz por defecto.
10. **Ingesta de prensa**: scraper automático corriendo cada 3 horas en GitHub Actions, solo fuentes directas (RSS/sitemaps), respetando robots.txt — se retiró Google Noticias como fuente al confirmar que no lo permitía.
11. **Seguridad y cuentas reales**: sistema de autenticación real (registro, verificación por email, login, reseteo de contraseña), cookies con revocación de sesión, límites de frecuencia contra abuso.
12. **Suite de pruebas**: 168 pruebas de backend + 108 de frontend, corriendo automático en cada cambio vía GitHub Actions (CI), incluida la integración contra una base PostgreSQL real.
13. **Despliegue 100% gratuito verificado**: los tres componentes (frontend, API, scraper) corren en producción hoy sin costo, sin tarjeta de crédito en ningún proveedor.
14. **Justificación económica (si escalara a operación comercial)**: bajo supuestos declarados y no validados con el mercado, VAN ≈ +USD 2.061, TIR ≈ 25,3% a 5 años, con tres fuentes de ingreso proyectadas (licencia de datos a municipios/aseguradoras, suscripción Premium con viaje compartido en vivo, publicidad en el plan gratuito). Aclarar que es un ejercicio numérico, no una validación de mercado real.
15. **Limitaciones declaradas honestamente**: validación del modelo limitada a CABA (no todo el GBA), demografía de víctimas no mejora la predicción entre años, cobertura de inseguridad general menor que la de siniestros (delitos más dispersos geográficamente).
16. **Conclusión central**: MotoSafe GBA funciona mejor como herramienta de ordenamiento y contexto declarado que como herramienta de predicción exacta — y esa distinción, medida y declarada en vez de ocultada, es el resultado de fondo del proyecto.
17. **Trabajo futuro / recomendaciones**: validar diferencial de mercado con más usuarios, repetir la validación de UX tras los cambios aplicados, decidir sobre variables demográficas del modelo.
18. **Cierre / preguntas**.

Para el diseño: paleta seria (azules oscuros, un acento amarillo/ámbar para alertas), tipografía clara, un screenshot-placeholder o ícono de mapa en las slides de producto (4, 8, 10), gráficos simples de barras para los números del modelo (slide 7) y la economía (slide 14). Nada de clip art genérico ni íconos de moto caricaturescos — el tono es de ingeniería seria, no de app de consumo.
