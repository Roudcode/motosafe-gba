# QA de accesibilidad y visual

**Ítems:** A23, V01–V14. **Estado:** protocolo listo; ejecución en dispositivos pendiente.

| Escenario | Comprobar | Resultado esperado |
|---|---|---|
| Teclado | Tab, Shift+Tab, Enter y Escape | Foco visible; ningún control queda inaccesible. |
| Zoom | Navegador a 200% | Buscar, capas, ruta y reportar siguen utilizables. |
| Tema | Claro y oscuro | Texto, ruta, alertas y controles se distinguen sobre el mapa. |
| Móvil | 360 y 390 px, vertical/horizontal | CTA de ruta, mapa y cierre de panel permanecen alcanzables. |
| Movimiento reducido | Preferencia del sistema activada | No hay animación decorativa persistente. |
| Red | Sin backend y con caché | Se explica fallo, fuente y acción de reintento. |

Registrar dispositivo, navegador, tamaño, resultado y captura sólo si no revela
ubicaciones personales. Una revisión CSS o tests unitarios no reemplazan esta
prueba visual real.
