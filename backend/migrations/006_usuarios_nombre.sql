-- F11 (SES-166): se suma nombre de usuario, ademas del email -- Rodo lo
-- pidio despues de probar el registro real ("que tenga nombre de usuario no
-- solo mail"). Nullable primero para poder backfillear la cuenta real que ya
-- existia antes de este cambio (creada en SES-165, sin esta columna todavia);
-- NOT NULL recien despues del backfill, para no romper esa fila real.
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS nombre_usuario VARCHAR(50);

UPDATE usuarios SET nombre_usuario = 'Rodo'
    WHERE email = 'barrionuevors0204@gmail.com' AND nombre_usuario IS NULL;

-- Cualquier otra fila real sin nombre (no deberia haber ninguna salvo la de
-- arriba, pero por si el backfill de arriba no alcanzo a todas) usa el email
-- como nombre de respaldo, para que la columna pueda quedar NOT NULL sin
-- inventar un valor sin sentido.
-- H15 (assessment 2026-10-22, SES-168): la version original copiaba el email
-- entero -- con uno de mas de 50 caracteres (el limite de la columna), rompia
-- la migracion entera con StringDataRightTruncation. `left(email, 41)` deja
-- lugar de sobra para el separador y el id (hasta 8 digitos), que ademas
-- garantiza que dos emails truncados al mismo prefijo no choquen contra el
-- UNIQUE de mas abajo.
UPDATE usuarios SET nombre_usuario = left(email, 41) || '_' || id::text WHERE nombre_usuario IS NULL;

ALTER TABLE usuarios ALTER COLUMN nombre_usuario SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_nombre_usuario_unico
    ON usuarios (nombre_usuario);
