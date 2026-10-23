-- H05 (assessment 2026-10-22, SES-168): cambiar la contrasena no revocaba
-- una cookie de sesion ya emitida -- quien la haya copiado antes del reset
-- seguia entrando con la vieja. La cookie pasa a llevar la version vigente
-- al momento de loguearse; resetear_password incrementa esta columna, asi
-- que cualquier cookie firmada con una version anterior deja de validar la
-- proxima vez que se revise (sin esperar a que venza el Max-Age de 12hs).
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS sesion_version INTEGER NOT NULL DEFAULT 1;
