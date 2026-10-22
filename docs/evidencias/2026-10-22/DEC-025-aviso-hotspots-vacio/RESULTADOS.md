# DEC-025 — extender el aviso de "capa vacía" a /hotspots (2026-10-22, SES-157)

Ejecución directa de una decisión ya tomada por Rodo (DEC-025 en `docs/gestion/DECISIONES.md`, confirmada
en el chat el 2026-10-22: "Sí, agregarlo"). No hay criterio nuevo que aplicar acá -- es implementar lo ya
decidido con el mismo patrón que ya tienen `corredores` e `inseguridadGeneral`/`inseguridadMoto` (V10,
SES-153).

## Qué se tocó

- **`frontend/src/App.jsx`**: agregado `hotspots: ZONAS_RIESGO.length === 0` al objeto `capasVacias` que se
  pasa a `CapaErrorBanners` (mismo patrón que las otras tres capas). `ZONAS_RIESGO` es el estado real que
  llena `cargarHotspots()` desde `/hotspots`.
- **`frontend/src/components/CapaErrorBanners.jsx`**: agregada la entrada `hotspots: 'hotspots de siniestros'`
  a `NOMBRE_CAPA` (el texto que se muestra en el aviso). Corregido el comentario del componente, que
  explicaba por qué `/hotspots` quedaba **a propósito** afuera de esta lista -- esa explicación ya no es
  cierta después de DEC-025, así que se actualizó para reflejar la decisión real.
- **`frontend/src/components/CapaErrorBanners.test.jsx`**: un test nuevo (`DEC-025: muestra el aviso de
  vacía para hotspots, igual que corredores/inseguridad`) que confirma que `capasVacias.hotspots = true`
  dispara el mismo aviso informativo, sin ícono de alerta ni botón de reintento, con el texto "hotspots de
  siniestros".

## Por qué no se verificó en pantalla con el backend real

Mismo motivo que ya documenta DEC-025 en `DECISIONES.md`: hoy `/hotspots` siempre devuelve las 740 filas
reales (no es un caso que ocurra en producción), así que no había forma de reproducir el escenario real
sin forzar artificialmente una respuesta vacía del backend -- y eso ya está cubierto por el test de
componente, que prueba exactamente la rama de código nueva sin necesitar simular nada contra un backend
real. Mismo criterio que ya se usó para cualquier rama defensiva que hoy no se dispara en producción.

## Verificación

- `node node_modules/vitest/vitest.mjs run` (desde `frontend/`): **108/108** tests en verde (102 antes +
  6 nuevos de `brechaCoberturaEnRecomendada`/DEC-026 + 1 de este punto -- ver evidencia de DEC-026 para el
  resto).
- Lint (`eslint src/`): limpio, sin errores ni warnings.
- Build (`vite build`): compila sin errores.

## Qué no se tocó

El backend (`backend/main.py`, línea 623) ya tenía el `if not resultado: return []` y el comentario que
anticipa este estado como válido -- no hizo falta ningún cambio ahí. Ninguna otra capa ni comportamiento de
la app.
