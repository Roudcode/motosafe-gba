CREATE TABLE IF NOT EXISTS reportes_colaborativos (
    id SERIAL PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    categoria VARCHAR(30) NOT NULL,
    autor_id VARCHAR(50) NOT NULL,
    delete_token_hash VARCHAR(64),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE reportes_colaborativos
    ADD COLUMN IF NOT EXISTS delete_token_hash VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_reportes_colaborativos_creado_en
    ON reportes_colaborativos (creado_en DESC);

CREATE TABLE IF NOT EXISTS reportes_confirmaciones (
    id SERIAL PRIMARY KEY,
    reporte_id INTEGER NOT NULL REFERENCES reportes_colaborativos(id) ON DELETE CASCADE,
    autor_id VARCHAR(50) NOT NULL,
    tipo VARCHAR(10) NOT NULL,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (reporte_id, autor_id)
);

CREATE INDEX IF NOT EXISTS idx_reportes_confirmaciones_reporte_id
    ON reportes_confirmaciones (reporte_id);
