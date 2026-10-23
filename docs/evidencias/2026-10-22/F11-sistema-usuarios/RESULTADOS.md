# F11 — sistema de usuarios real: registro, verificación y reseteo por código de mail (2026-10-22, SES-165)

Pedido explícito de Rodo: reemplazar el usuario único fijo (`AUTH_USERNAME`/`AUTH_PASSWORD_HASH` en
`backend/.env`) por un sistema real -- cualquiera se registra con su propio email, recibe un código de 6
dígitos por correo real para verificar la cuenta, y puede pedir otro código para resetear la contraseña.
Nada más (sin favoritos, sin preferencias). Las 4 fases se hicieron en una sola sesión, sin pausas, con
permiso explícito para decidir con criterio propio.

## Fase 1 — backend: tabla de usuarios, registro y login multiusuario

### Qué había antes (leído `backend/auth.py` completo antes de tocar nada)

Un único usuario fijo por variables de entorno: cookie firmada (itsdangerous, HttpOnly+Secure+SameSite=Lax,
sin estado de sesión en el servidor), payload `{"usuario": AUTH_USERNAME}`, y un limitador de intentos por
IP (5 en 60s) ya implementado para `/auth/login`. Sin tabla de usuarios, sin registro.

### Migración `backend/migrations/005_usuarios.sql`

Mismo estilo que las 4 migraciones ya existentes. Dos tablas:
- `usuarios`: id, email (único), password_hash (bcrypt), email_verificado (bool, default false), creado_en.
- `codigos_auth`: id, usuario_id (FK), codigo (6 dígitos), tipo ('verificacion'|'reset_password'),
  expira_en (15 min desde la creación), usado_en (nullable), intentos_fallidos (default 0).

### Decisión 1: ¿el login bloquea si el email no está verificado?

**Sí, bloquea.** Con un mensaje claro ("Confirmá tu cuenta con el código que te mandamos a tu correo"), no
un 401 genérico -- el frontend usa ese mensaje para ofrecer reenviar el código en el mismo lugar, sin que la
persona tenga que volver a registrarse. Además, una credencial correcta mal usada así (email+password
válidos pero sin verificar) **no cuenta como intento fallido** para el limitador de fuerza bruta -- esa
distinción es real: la credencial era correcta, lo que falta es otra cosa.

### Decisión 2: ¿qué hacer con el usuario único viejo del `.env`?

**No se migró.** `AUTH_USERNAME` es "rodo", un nombre de usuario, no un email real -- no hay ninguna
casilla de correo legítima con la que migrarlo con integridad a la tabla nueva. Inventar una
(`rodo@local`, por ejemplo) crearía una cuenta fantasma con un reseteo de contraseña que nunca podría
completarse de verdad (no hay bandeja real detrás). Lo más limpio: Rodo se registra de cero con su email
real por el flujo nuevo, con una cuenta genuinamente verificada desde el día uno.
`AUTH_USERNAME`/`AUTH_PASSWORD_HASH` quedan en el `.env` sin usar por `/auth/login` -- no se borraron ni se
rompió `generar_password.py`, no hacía falta para este cambio.

### Verificación real (no solo tests)

Aplicada la migración contra la base real (`python migrar.py`, aplicó `005_usuarios.sql`). Registrado de
verdad (`POST /auth/registro` real contra el backend real), confirmada la fila real en la base
(`usuarios.email_verificado = false`) y el código real generado en `codigos_auth`. Logueado de verdad una
vez verificado (ver Fase 2 más abajo, donde se hace el ciclo completo).

## Fase 2 — mail real, verificación y reseteo

`backend/email_service.py` nuevo: SMTP de Gmail (`smtp.gmail.com:587`, STARTTLS), texto plano, dos
plantillas (código de verificación, código de reseteo). Si `SMTP_USER`/`SMTP_PASSWORD` faltan, no rompe el
arranque del backend -- cae a loguear el código por consola (fallback de desarrollo) en vez de fallar en
silencio. **No fue necesario usar ese fallback**: las credenciales ya estaban puestas en `.env`
(`motosafe.noreply@gmail.com`, cuenta dedicada armada por Rodo específicamente para esto, confirmado que no
es su Gmail personal).

Endpoints nuevos: `POST /auth/verificar-codigo`, `POST /auth/reenviar-codigo`, `POST /auth/olvide-password`
(siempre responde igual exista o no la cuenta) y `POST /auth/resetear-password`. Un código con 5 intentos
fallidos queda invalidado (columna `intentos_fallidos`), sin esperar a que venza.

### Verificación real de entrega, no solo "el log dice que se mandó"

Se registró con el email real `motosafe.noreply@gmail.com` (la propia cuenta dedicada, usada también como
destinatario de prueba -- permite verificar la entrega real por IMAP con las mismas credenciales ya
provistas, sin necesitar una casilla de un tercero). Confirmado leyendo el inbox real por IMAP
(`imap.gmail.com`, mismas credenciales que SMTP) que el mail **llegó de verdad**, con el código real
coincidiendo exacto con el de la base:

```
Código real en la base: 712671
Mail real recibido -- De: motosafe.noreply@gmail.com
  Asunto: Tu código de verificación de MotoSafe GBA
  Cuerpo: "Tu código de verificación de MotoSafe GBA es: 712671..."
```

Ciclo completo real, por API directa (`curl`), confirmado paso a paso:
1. `POST /auth/registro` → `{"ok": true, "mail_enviado": true}`.
2. Código real `712671` confirmado en la base Y en el inbox real (arriba).
3. `POST /auth/verificar-codigo` con el código real → `{"ok": true}`.
4. `POST /auth/login` con la contraseña real → `200`, cookie de sesión real seteada.
5. `GET /auth/me` con esa cookie → `{"usuario": "motosafe.noreply@gmail.com", "auth_habilitado": true}`.
6. `POST /auth/olvide-password` → código real `778341` confirmado en el inbox real (mail de reseteo,
   asunto distinto, cuerpo distinto).
7. `POST /auth/resetear-password` con ese código real → `{"ok": true}`.
8. Login con la contraseña vieja → `401` (falla, como debe ser).
9. Login con la contraseña nueva → `200` (funciona).

Usuario de prueba borrado de la base real al terminar (no queda ninguna cuenta de prueba en la base
personal).

## Fase 3 — frontend

### Qué había antes (revisado `LoginGate.jsx` real antes de tocarlo)

Un único formulario (usuario fijo + contraseña), sin ninguna otra pantalla.

### Qué se agregó

`LoginGate.jsx` reescrito como un flujo de 5 pantallas dentro del mismo componente (`FlujoAcceso`), todas
reusando las clases visuales ya existentes (`.login-fondo`, `.login-tarjeta`, `.login-campo`,
`.login-input`, `.login-boton`, `.login-error`) y 3 clases nuevas chicas (`.login-aviso`,
`.login-enlaces`/`.login-enlace`, `.login-input-codigo`) -- sin librería ni componente nuevo:

1. **Login**: email + contraseña (antes era usuario + contraseña), con "¿Olvidaste tu contraseña?" y "Crear
   cuenta" como enlaces.
2. **Crear cuenta**: email + contraseña + confirmar, validación real (longitud mínima, coincidencia) antes
   de pegarle al backend.
3. **Verificar código**: campo numérico de 6 dígitos, botón "Reenviar código", vuelve sola al login al
   verificar bien.
4. **¿Olvidaste tu contraseña?**: pide el email, siempre avanza a la pantalla siguiente (coherente con que
   el backend nunca revela si la cuenta existe).
5. **Código + contraseña nueva**: mismo patrón de validación que crear cuenta.

### Verificación real en el navegador (no solo API)

Con el stack real levantado (frontend + backend reiniciado con el código nuevo), se repitió el ciclo
completo **clickeando la UI real**, con el mismo email real: Crear cuenta → código real leído del inbox
real por IMAP → tipeado en el campo → Verificar → vuelta al login → login real → `/auth/me` confirmó
`"motosafe.noreply@gmail.com"` en el menú de herramientas ("Sesión de motosafe.noreply@gmail.com") → Cerrar
sesión → ¿Olvidaste tu contraseña? → código real de reset leído del inbox real → tipeado → contraseña nueva
→ login real con la contraseña nueva confirmado por API. Capturas reales en esta misma carpeta
(`login_exitoso.jpg`, pantalla de la app ya logueada con el onboarding real de V12 encima).

## Fase 4 — endurecimiento, tests, documentación

### Suite de tests

**Reorganización necesaria**: el login ahora necesita la tabla `usuarios` para devolver un 401 limpio (antes
era comparación directa contra una variable, sin tocar la base) -- el job de CI "backend-sintaxis" corre
`pytest -q` **sin ninguna base de datos levantada**. Se sacó la verificación de `DATABASE_URL` al importar
`auth.py` (si no, rompía ese job entero) y se movieron todos los tests que necesitan un login/registro real
a `test_integracion_postgres.py` (gateado por `MOTOSAFE_TEST_DATABASE_URL`, con una base desechable migrada
-- nunca la base personal), siguiendo el mismo patrón ya establecido ahí (A12/T01). `test_auth.py` quedó
acotado a lo que de verdad no necesita base: login deshabilitado y el middleware de sesión.

14 tests nuevos en `test_integracion_postgres.py`: alta real + duplicado + contraseña corta, login bloqueado
sin verificar, flujo completo registro→verificar→login, código de verificación invalidado tras 5 intentos
fallidos, reenviar-código y olvidé-password **no filtran si el email existe** (mismas respuestas exista o
no la cuenta, confirmado comparando las dos respuestas byte a byte), flujo completo de reseteo (incluida la
contraseña vieja fallando después), login con email inexistente, bloqueo por intentos fallidos de login.

### Corrida real

```
MOTOSAFE_TEST_DATABASE_URL=postgresql://motosafe:motosafe_dev@localhost:5432/postgres
python -m pytest -q tests/test_integracion_postgres.py
→ 22 passed, 1 failed (ver nota abajo, no relacionado)
```

Suite rápida (sin base, igual que corre CI): `135 passed, 23 skipped` (los 23 son los de integración,
correctamente saltados sin `MOTOSAFE_TEST_DATABASE_URL`). Frontend: `108/108` tests, lint limpio, build sin
errores.

**Hallazgo real, no relacionado con F11, documentado sin corregir** (fuera de alcance -- es territorio
A/D, el pedido fue explícito en que eso no entra esta sesión): `test_carga_inicial_solo_llena_tablas_vacias`
falla con un conteo esperado desactualizado (`1135`) contra el real de hoy (`1121` = 619 generales + 502
con moto) -- refleja la limpieza geográfica de DEC-024, aplicada en una sesión anterior, que nunca actualizó
este test. Confirmado con `git log` que esa línea del test no cambió hoy; el fallo es preexistente, solo se
hizo visible al correr la suite completa de integración.

### Ningún endpoint filtra si un email existe

Confirmado con test real (`test_reenviar_codigo_no_filtra_si_el_email_existe`,
`test_olvide_password_no_filtra_si_el_email_existe`): las respuestas de `/auth/reenviar-codigo` y
`/auth/olvide-password` son **idénticas** exista o no la cuenta. La única excepción consciente es
`/auth/registro`, que sí dice "ese email ya está registrado" con un 409 -- es el comportamiento esperado y
estándar para un alta (no es la misma garantía que pide "no filtrar" para reseteo/reenvío, que son los
puntos de ataque reales para enumerar cuentas ajenas).

## Qué falta: sección nueva en la tesis

El Capítulo 4 (`docs/tesis/MotoSafe_GBA_Capitulos_1_a_6.docx`) va a necesitar una sección nueva describiendo
este sistema una vez cerrado -- **no se implementó en esta sesión**, señalado tal como pidió Rodo
explícitamente ("sin implementarlo").

## Qué no se tocó (en la sesión original, SES-165)

Catálogo V/A/D/T (salvo el hallazgo no relacionado documentado arriba, sin corregir). Ningún favorito,
preferencia ni función más allá de registro/verificación/login/reseteo.

---

## Follow-up 1 — nombre de usuario propio + ojo de contraseña (SES-166)

Rodo confirmó que todo lo de arriba le funcionó perfecto de punta a punta (registro real, cambio de
contraseña real, todo OK) y pidió tres cosas puntuales: un nombre de usuario además del email, fijar
`nombre_usuario='Rodo'` en su cuenta real, impedir nombre de usuario duplicado igual que el email, y un
ícono de ojo para ver lo que se escribe en los campos de contraseña.

- Migración `006_usuarios_nombre.sql`: columna `nombre_usuario VARCHAR(50)` nullable primero, backfill
  especial a `'Rodo'` para `barrionuevors0204@gmail.com`, backfill genérico para cualquier otra fila sin
  nombre, `NOT NULL` + índice único recién después.
- `auth.py`: `RegistroBody.nombre_usuario` obligatorio, `registro()` valida duplicado (409, mismo criterio
  que el email), `/auth/me` devuelve `nombre_usuario` además de `usuario`.
- `LoginGate.jsx`: componente `CampoPassword` (ícono Eye/EyeOff de `lucide-react`, alterna
  `type="password"`/`"text"`) usado en los 5 campos de contraseña del flujo; campo "Nombre de usuario"
  nuevo en el formulario de registro. `HerramientasMenu.jsx` muestra el nombre en vez del email.

**Verificación real**: ciclo completo clickeando la UI (registro con nombre de usuario, ojo
mostrando/ocultando la contraseña en vivo, capturas `login_exitoso.jpg` y
`nombre_usuario_y_ojo_contrasena.jpg` en esta misma carpeta) y confirmado por SQL contra la base real que la
cuenta de Rodo quedó con `nombre_usuario='Rodo'`.

## Follow-up 2 — corrección de H04/H05/H07/H13/H15 del assessment de SES-167 (SES-168)

Una sesión concurrente hizo una auditoría de seguridad completa (`docs/assessment_2026-10-22/ASSESSMENT.md`)
y encontró 5 bugs reales dentro del propio código de F11 (más otros fuera de este alcance, catálogo V/A/D/T).
Rodo autorizó explícitamente corregir los de F11 ("dale corrige").

| Hallazgo | Problema real | Corrección |
|---|---|---|
| H04 | `random.randint` (no criptográfico); un código viejo sin usar seguía válido después de pedir uno nuevo; sin lock, dos pedidos concurrentes con el mismo código podían pasar los dos | `secrets.randbelow`; `_crear_codigo` invalida (marca usado) cualquier código sin usar del mismo tipo antes de insertar el nuevo; `_codigo_vigente` usa `SELECT ... FOR UPDATE` |
| H05 | Cambiar la contraseña no revocaba una cookie de sesión ya emitida (token firmado puro, sin verificación contra la base) | Migración `007_usuarios_sesion_version.sql` (`sesion_version`); la cookie lleva la versión vigente al loguearse, se valida contra la base en cada pedido protegido, `resetear_password` la incrementa |
| H07 | `/auth/registro` sin rate limiting por IP | Mismo límite que login/reenviar/olvide/resetear (5/60s) |
| H13 | `mail_enviado: true` aunque SMTP no estuviera configurado (fallback de consola silencioso) | `email_service.enviar_codigo` devuelve `bool` real; `registro`/`reenviar_codigo`/`olvide_password` lo usan |
| H15 | Backfill de la migración 006 podía romper con `StringDataRightTruncation` en un email >50 caracteres | `left(email, 41) || '_' || id` en vez de copiar el email entero |

### Verificación real

Migración 007 aplicada a la base real local (`python migrar.py`) -- confirmado por SQL que
`usuarios.sesion_version` existe y la cuenta de Rodo quedó en `1` (sin resets de por medio). 9 tests nuevos
en `test_integracion_postgres.py`, contra PostgreSQL real desechable (no mockeado), reproduciendo los
escenarios exactos del assessment pero esperando ahora el comportamiento corregido:

- código viejo deja de funcionar después de pedir uno nuevo (`reenviar-codigo`);
- `_generar_codigo` usa `secrets.randbelow`, no `random.randint`;
- una cookie emitida antes de un reset de contraseña deja de validar `/auth/me` después del reset, y una
  cookie nueva (post-reset) sigue funcionando;
- `/auth/registro` responde 429 después de 5 intentos desde la misma IP;
- `mail_enviado: false` real cuando `enviar_codigo` no manda por SMTP de verdad.

```
MOTOSAFE_TEST_DATABASE_URL=postgresql://motosafe:motosafe_dev@localhost:5432/postgres
python -m pytest -q tests/test_integracion_postgres.py
→ 29 passed, 1 failed (el mismo 1135/1121 preexistente de siempre, no relacionado)
```

Suite rápida (sin base, igual que CI): `135 passed, 30 skipped`, sin regresiones.

**Decisión sobre el alcance de la revocación (H05)**: se corrigió específicamente la revocación por reset de
contraseña, que es lo que pedía el hallazgo. No se agregó un "cerrar sesión en todos los dispositivos" aparte
(no estaba pedido ni dentro del alcance autorizado).

**No se repitió la verificación con mail real por SMTP para esta tanda**: los 9 tests nuevos ya reproducen
los pasos exactos del assessment contra una base real (no mockeada), que es el mismo estándar de evidencia
usado en SES-165 para estos endpoints -- solo el envío del mail sigue simulado en los tests automáticos
(igual que en F11 original), nunca se mandó un mail real nuevo para este follow-up.

## Qué no se tocó (en ningún follow-up)

Catálogo V/A/D/T completo (H01, H02, H03, H06, H08 a H12, H16, H17, y la parte de H14 ajena a F11) -- fuera
del alcance autorizado hoy. Ningún favorito, preferencia ni función más allá de
registro/verificación/login/reseteo/nombre de usuario.
