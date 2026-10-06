# T02 — E2E real en la máquina de Rodo (SES-068)

Fecha: 2026-10-05/06. Sesión: SES-068 (Claude Code nativo).

## Montaje aislado

Tailscale Funnel estaba activo y publica `127.0.0.1:5173` (Vite de Rodo, que apunta al backend `:8000`). El E2E no tocó esos puertos ni la base personal:

| Pieza | Dónde |
|---|---|
| PostGIS efímero `postgis/postgis:16-3.4` | `127.0.0.1:55432`, contenedor borrado al terminar |
| Datos | `migrar.py` y los tres `cargar_*.py` del repo sobre la base vacía: 740 hotspots, 243 corredores, 633 + 502 zonas de inseguridad |
| Backend | `uvicorn main:app` en `127.0.0.1:8100`, venv instalado desde `backend/requirements.lock`, login activado con credenciales de prueba generadas en la sesión (no las de Rodo, no guardadas en el repo) |
| Frontend | `vite build` servido con `vite preview` en `127.0.0.1:4173`, proxy `/api` a `:8100` (`MOTOSAFE_API_TARGET`, `MOTOSAFE_SIN_HTTPS=1`) |

## Resultado

- **Base nueva desde el repo:** fallaba. `cargar_hotspots.py` hacía `DELETE FROM hotspots_riesgo` sobre una tabla que nada creaba. Se agregó `CREATE TABLE IF NOT EXISTS` con el esquema de la base de desarrollo; después cargó las 740 zonas.
- **Navegador, build de producción:** el login rechazó la contraseña incorrecta y aceptó la de prueba; aparecieron la app, la bienvenida y el botón "Salir". **El mapa quedaba en blanco**: MapLibre 6.8 pedía `/assets/maplibre-gl-worker.mjs`, que `vite build` no emitía; el servidor devolvía `index.html` («Failed to load module script… text/html»). Se corrigió en `MapaMotoSafe.jsx` con `?worker&url` y `setWorkerUrl`, solo en el build. Después del arreglo, el mapa dibujó teselas y 38 marcadores agrupados.
- **`npm run dev`:** en el navegador integrado no dibujó el mapa ni con el código original. Más tarde se comprobó que el panel había dejado de pintar (`requestAnimationFrame` detenido, ventana sin foco), así que no se pudo verificar el modo dev. Por eso el arreglo se limitó a `import.meta.env.PROD` y el modo dev queda como estaba.
- **E2E HTTP** (`e2e_http.py`, misma cadena proxy → API → PostGIS, sin mocks): 23 de 23 verificaciones. Resultado en `resultado_e2e_http.txt`. Incluye:
  - sesión: 401 sin sesión, cookie HttpOnly/Secure/SameSite=Lax y 401 al salir;
  - las cuatro capas con sus cantidades;
  - `/predecir`;
  - ciclo completo de reportes: crear, el autor no puede votar, otro dispositivo vota, cambiar el voto lo reemplaza, token inválido da 404, borrar y desaparecer;
  - prensa;
  - rutas reales con TomTom (Obelisco → Plaza Italia: 3 alternativas);
  - tesela PNG de tráfico.

## No verificado

- Flujos visuales posteriores al arreglo (clic en zona, búsqueda, trazar ruta en el mapa, reportar desde la interfaz, navegación GPS): el panel dejó de pintar cuando la ventana de Claude quedó sin foco.
- El modo dev con el navegador pintando.
- Móvil, teclado y temas.
- El scraper contra esta base: sí corrió dentro del compose de producción (SES-067).

## Reproducir

Levantar las cuatro piezas como en la tabla y correr:

```
E2E_BASE=http://localhost:4173 E2E_USER=<usuario de prueba> E2E_PASS=<contraseña de prueba> python e2e_http.py
```
