-- La plataforma debe contar con extensión espacial antes de incorporar
-- consultas/geometrías PostGIS. Es repetible y funciona tanto en la imagen
-- postgis oficial como en proveedores que habilitan la extensión al usuario.
CREATE EXTENSION IF NOT EXISTS postgis;
