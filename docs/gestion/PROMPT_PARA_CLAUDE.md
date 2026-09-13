# Prompt para retomar con Claude

Copiar y pegar este texto al iniciar una nueva conversación con Claude:

> Continuá el proyecto final de Ingeniería **MotoSafe GBA** desde este repositorio. Antes de editar, ejecutá `git status` y leé, en este orden: `docs/README.md`, `docs/gestion/CONTINUIDAD.md`, `docs/gestion/BACKLOG.md`, `docs/gestion/BITACORA.md`, `docs/gestion/DECISIONES.md` y `docs/gestion/VALIDACION.md`. 
>
> ChatGPT/Codex trabajó sobre la auditoría integral iniciada en el commit `c24b8a7` y centralizó todo el contexto, decisiones, cambios y pendientes. Los cambios posteriores están publicados en `main`; usá `git log --oneline` y el estado por ID del BACKLOG, no resúmenes viejos, para saber el punto exacto de partida. 
>
> Forma de trabajo acordada con Rodo: avanzar de manera autónoma por bloques. Para cada bloque: implementar, ejecutar pruebas pertinentes, actualizar BACKLOG, BITACORA y CONTINUIDAD; actualizar DECISIONES ante una decisión nueva; crear commit y hacer `git push origin main` antes de abrir el siguiente bloque. No crear backlogs o bitácoras paralelos, no reescribir el assessment histórico y no inventar métricas, aprobaciones o pruebas.
>
> Prioridad actual: (1) validez del modelo y cobertura de rutas A01–A06; (2) validación PostgreSQL/migraciones A12/A14/T01; (3) errores, procedencia y reintentos A09–A11/A15; (4) GPS, rendimiento y E2E A16–A18/T02–T03; (5) accesibilidad, visual y documentación. El modelo clasifica gravedad condicionada a un siniestro, no probabilidad de ocurrencia por viaje; 2025 no es una evaluación temporal independiente porque intervino en selección de configuraciones. 
>
> Cambios ya realizados incluyen seguridad de reportes con token privado, sanitización de prensa, validación de entradas, pool acotado, migraciones iniciales, recuperación de capas con caché, accesibilidad de foco/zoom/movimiento reducido y documentación centralizada. Verificá lo que sigue pendiente contra el código y el BACKLOG antes de declararlo cerrado. Si un servicio local no está disponible, documentá el límite y continuá con los bloques que sí puedan validarse.
