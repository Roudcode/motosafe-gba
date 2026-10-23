CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(100) NOT NULL,
    email_verificado BOOLEAN NOT NULL DEFAULT false,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS codigos_auth (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    codigo VARCHAR(6) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    expira_en TIMESTAMPTZ NOT NULL,
    usado_en TIMESTAMPTZ,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_codigos_auth_usuario_id ON codigos_auth (usuario_id);
-- Buscar el codigo vigente mas reciente de un tipo es la consulta real que
-- hacen verificar/reenviar/resetear -- este indice la cubre directo.
CREATE INDEX IF NOT EXISTS idx_codigos_auth_usuario_tipo_creado
    ON codigos_auth (usuario_id, tipo, creado_en DESC);
