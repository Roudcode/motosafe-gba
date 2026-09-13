# Matriz académica y demo reproducible

**Ítems:** G01, G02, G03, G04. **Estado:** guion y matriz preparados; ejecución con usuarios pendiente.

| Objetivo | Evidencia actual | Límite que debe declararse |
|---|---|---|
| Mapear contexto vial | Hotspots, corredores y cobertura por fuente | Datos históricos de CABA; no cobertura validada de todo GBA. |
| Estimar gravedad | Contrato y evaluador temporal reproducible | Falta ejecución temporal real por entorno Python. |
| Comparar rutas | Trazado TomTom, cruces y cobertura separada | No predice ocurrencia ni garantiza seguridad. |
| Informar datos recientes | Prensa y reportes comunitarios | Scraper sin medición humana aún; reportes no son verificación oficial. |
| Usabilidad | Foco, zoom, movimiento reducido y matriz QA | Falta prueba con personas y dispositivos reales. |

## Guion de demo

1. Abrir el mapa y explicar cobertura/fuentes antes de seleccionar una ruta.
2. Buscar origen y destino, mostrar alternativas, tiempo, exposición y cobertura por fuente.
3. Activar una capa de inseguridad y aclarar que no reemplaza siniestros.
4. Simular fallo de capa y mostrar caché + reintento localizado.
5. Activar modo viaje y mostrar progreso continuo, ETA y salida.
6. Cerrar con límites: gravedad condicionada, datos históricos CABA y fuentes recientes imperfectas.

No usar la demo como prueba de reducción de accidentes. Registrar versión, commit,
datos cargados, servicios disponibles y fallos simulados antes de presentarla.
