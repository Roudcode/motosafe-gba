# Política de privacidad — datos de ubicación de los reportes colaborativos

Este documento cierra el pendiente señalado en 6.5 del Capítulo 6 (barrera legal/ética acotada) y en el Capítulo 8 (8.4): formalizar un criterio de privacidad para la ubicación de los reportes comunitarios, que hasta esta entrega vivía solo en comentarios de código (`backend/main.py`) y en decisiones puntuales de la bitácora (DEC-007 en adelante). Describe lo que el sistema recolecta hoy, verificado contra el código real a 20/10/2026, no un diseño aspiracional.

## 1. Qué datos recolecta un reporte colaborativo

Al crear un reporte (`POST /reportes`), el sistema guarda cuatro campos en `reportes_colaborativos`: latitud y longitud (precisión completa, sin redondear ni desplazar — ver limitación en la sección 4), categoría del reporte (robo, inseguridad, choque, etc.) y `autor_id`. `autor_id` es un UUID que el frontend genera una vez por dispositivo y guarda en `localStorage`; no es una identidad real, no está atado a un nombre, email ni número de teléfono, y nada en el sistema puede usarlo para identificar a una persona fuera del propio dispositivo que lo generó.

Al confirmar o desmentir un reporte ajeno (`POST /reportes/{id}/confirmar`), se guarda el mismo `autor_id` del dispositivo que vota, la referencia al reporte y el tipo de voto, con una restricción `UNIQUE(reporte_id, autor_id)` que impide que el mismo dispositivo vote dos veces sobre el mismo reporte.

## 2. Qué NO recolecta

MotoSafe GBA no pide ni guarda nombre, email, teléfono ni ningún dato que identifique a la persona detrás de un reporte. No hay cuentas de usuario para quien consulta el mapa: el único login del sistema (`/auth/login`) es administrativo, de un solo usuario (el autor del proyecto), no de los motociclistas que usan la app. No se vende ni se comparte ningún dato con terceros; no hay integración de analítica de terceros (Google Analytics u otro) que trackee a la persona entre sesiones.

La dirección IP de quien crea o borra un reporte se usa de forma transitoria para dos cosas — el límite de frecuencia general (`slowapi`, 20 pedidos/minuto) y el bloqueo de intentos fallidos de login administrativo (5 intentos por minuto) — y en ningún caso queda guardada en una tabla ni en un archivo: el conteo vive en memoria del proceso y se pierde al reiniciar el backend.

## 3. Retención y borrado

Cada reporte tiene una vigencia por categoría (`VIGENCIA_HORAS_POR_CATEGORIA`, por defecto 7 días si la categoría no tiene un valor propio); pasado ese plazo deja de aparecer como vigente en `GET /reportes`, aunque la fila sigue existiendo en la base hasta que se borra. Puede borrarse antes de tres formas: por quien lo creó, con el token privado de un solo uso que recibió al crearlo (`DELETE /reportes/{id}`); automáticamente, cuando otros usuarios lo desmienten por consenso (doble umbral de votos); o por vencimiento natural, descripto arriba.

Reportes creados antes del 14 de septiembre de 2026 (cuando se introdujo el token de borrado privado) no tienen ese token y no pueden borrarse por esa vía; queda pendiente, como ya señala el Capítulo 6 (R-03), decidir qué hacer con ese conjunto residual.

## 4. Limitación declarada: la ubicación se guarda a precisión completa

A diferencia de otras capas del sistema (por ejemplo, las claves de caché de geocodificación usan un redondeo a ~1 km, ver `backend/main.py`), los reportes colaborativos guardan latitud y longitud exactas, sin redondear ni desplazar aleatoriamente. Esto es una decisión de diseño, no un descuido: la precisión exacta es la que le da utilidad al reporte para otro motociclista que decide una ruta. El costado de privacidad de esa decisión es real y se declara acá de forma explícita: un reporte creado reiteradamente desde el mismo punto (por ejemplo, la puerta de un domicilio) podría, en principio, dejar un patrón geográfico reconocible si alguien correlacionara varios reportes del mismo `autor_id`. El sistema no hace esa correlación ni la expone en ningún endpoint público, pero la posibilidad técnica existe a nivel de los datos crudos en la base, y queda documentada en vez de asumida como inexistente.

## 5. Datos que no son de reportes colaborativos

Los siniestros históricos, los delitos del GCBA, la prensa y el clima son datos públicos oficiales o de acceso público, agregados y sin ningún dato personal identificable de terceros (no incluyen nombres de víctimas ni de denunciantes). Su tratamiento de privacidad es el de la fuente original; MotoSafe GBA no agrega ningún dato personal nuevo a esas capas.

## 6. Alcance de este documento

Este criterio aplica al estado actual del proyecto como entrega académica de un MVP de un solo desarrollador, sin despliegue comercial. Si el proyecto avanza a un uso productivo con una base de usuarios real, este documento es el punto de partida para una política de privacidad formal más completa (con, por ejemplo, un mecanismo de solicitud de borrado total de los reportes de un dispositivo, hoy cubierto solo reporte por reporte), no el documento final.
