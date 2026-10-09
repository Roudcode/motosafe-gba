-- Tabla de prensa externa (scraper de noticias) y las dos columnas que se
-- agregaron despues del primer CREATE TABLE en produccion (tipo_incidente,
-- relacionado_moto) mas el ensanche de url_fuente a TEXT para agregadores
-- con enlaces largos. Mismo esquema final que creaban en tiempo de ejecucion
-- backend/main.py (_crear_o_actualizar_tabla_prensa) y
-- backend/scrapear_noticias_robos.py (_asegurar_tabla) -- ver A14 en BACKLOG.md.
CREATE TABLE IF NOT EXISTS reportes_prensa (
    id SERIAL PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    nivel_precision VARCHAR(20) NOT NULL,
    radio_metros INTEGER NOT NULL,
    titular TEXT NOT NULL,
    url_fuente TEXT NOT NULL UNIQUE,
    fuente VARCHAR(50) NOT NULL,
    tipo_incidente VARCHAR(20) NOT NULL DEFAULT 'robo',
    relacionado_moto BOOLEAN NOT NULL DEFAULT FALSE,
    publicado_en TIMESTAMPTZ,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE reportes_prensa ADD COLUMN IF NOT EXISTS tipo_incidente VARCHAR(20) NOT NULL DEFAULT 'robo';
ALTER TABLE reportes_prensa ADD COLUMN IF NOT EXISTS relacionado_moto BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE reportes_prensa ALTER COLUMN url_fuente TYPE TEXT;
