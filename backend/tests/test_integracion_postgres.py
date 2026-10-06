"""Integración contra un PostgreSQL/PostGIS real (A12, T01).

Se saltean salvo que MOTOSAFE_TEST_DATABASE_URL apunte a un servidor
desechable (por ejemplo un contenedor postgis/postgis:16-3.4). Cada corrida
crea una base nueva con nombre aleatorio y la borra al final: nunca usa la base
personal ni la de DATABASE_URL.

    MOTOSAFE_TEST_DATABASE_URL=postgresql://usuario:clave@127.0.0.1:55433/postgres pytest tests/test_integracion_postgres.py
"""
import os
import threading
import uuid
from urllib.parse import urlsplit, urlunsplit

import psycopg2
import pytest
from fastapi.testclient import TestClient

import main
import migrar

URL_SERVIDOR = os.getenv('MOTOSAFE_TEST_DATABASE_URL')
pytestmark = pytest.mark.skipif(not URL_SERVIDOR, reason='MOTOSAFE_TEST_DATABASE_URL no definida')


def _url_con_base(url, base):
    partes = urlsplit(url)
    return urlunsplit(partes._replace(path=f'/{base}'))


@pytest.fixture(scope='module')
def url_base():
    nombre = f'motosafe_test_{uuid.uuid4().hex[:10]}'
    admin = psycopg2.connect(URL_SERVIDOR)
    admin.autocommit = True
    admin.cursor().execute(f'CREATE DATABASE {nombre}')
    try:
        yield _url_con_base(URL_SERVIDOR, nombre)
    finally:
        cur = admin.cursor()
        cur.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s', (nombre,))
        cur.execute(f'DROP DATABASE IF EXISTS {nombre}')
        admin.close()


@pytest.fixture(scope='module')
def migrada(url_base):
    migrar.aplicar_migraciones(url_base)
    return url_base


@pytest.fixture
def pool_real(migrada, monkeypatch):
    """Pool nuevo de main apuntando a la base de prueba, sin mocks."""
    monkeypatch.setattr(main, 'DATABASE_URL', migrada)
    pool = main._PoolConexiones(maxsize=2, timeout=1)
    monkeypatch.setattr(main, '_pool_conexiones', pool)
    yield pool
    while not pool._libres.empty():
        pool._libres.get_nowait().close()


def _contar(url, sql, *params):
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()[0]


def test_migraciones_concurrentes_se_aplican_una_sola_vez(url_base):
    # Mismo escenario que api + scraper arrancando juntos en Compose (SES-067).
    resultados, errores = [], []

    def correr():
        try:
            resultados.append(migrar.aplicar_migraciones(url_base))
        except Exception as err:  # noqa: BLE001 -- se informa abajo
            errores.append(err)

    hilos = [threading.Thread(target=correr) for _ in range(4)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    assert not errores, errores
    disponibles = [a.name for a in migrar.migraciones_disponibles()]
    assert sorted(sum(resultados, [])) == sorted(disponibles), 'cada migración la aplica un solo proceso'
    assert _contar(url_base, 'SELECT count(*) FROM schema_migrations') == len(disponibles)
    assert migrar.aplicar_migraciones(url_base) == []


def test_postgis_habilitado_por_migracion(migrada):
    assert _contar(migrada, "SELECT count(*) FROM pg_extension WHERE extname = 'postgis'") == 1


def test_pool_no_supera_el_maximo_con_conexiones_reales(pool_real):
    a, b = pool_real.getconn(), pool_real.getconn()
    with pytest.raises(RuntimeError, match='agotado'):
        pool_real.getconn()
    pool_real.putconn(a)
    assert pool_real.getconn() is a, 'reutiliza la conexión devuelta'
    pool_real.putconn(a)
    pool_real.putconn(b)


def test_error_sql_no_deja_la_conexion_en_transaccion_abortada(pool_real):
    conn = pool_real.getconn()
    with pytest.raises(psycopg2.errors.UndefinedTable):
        conn.cursor().execute('SELECT * FROM tabla_que_no_existe')
    pool_real.putconn(conn)  # hace rollback
    reutilizada = pool_real.getconn()
    assert reutilizada is conn
    cur = reutilizada.cursor()
    cur.execute('SELECT 1')
    assert cur.fetchone()[0] == 1
    pool_real.putconn(reutilizada)


def test_conexion_cortada_por_el_servidor_se_descarta(pool_real, migrada):
    conn = pool_real.getconn()
    pid = conn.get_backend_pid()
    pool_real.putconn(conn)
    with psycopg2.connect(migrada) as admin, admin.cursor() as cur:
        cur.execute('SELECT pg_terminate_backend(%s)', (pid,))
    # La conexión del pool está muerta pero psycopg2 todavía no lo sabe.
    muerta = pool_real.getconn()
    with pytest.raises(psycopg2.OperationalError):
        muerta.cursor().execute('SELECT 1')
    pool_real.putconn(muerta)  # rollback falla: se cierra y se olvida
    nueva = pool_real.getconn()
    assert nueva is not muerta and nueva.get_backend_pid() != pid
    cur = nueva.cursor()
    cur.execute('SELECT 1')
    assert cur.fetchone()[0] == 1
    pool_real.putconn(nueva)


def test_ciclo_de_reportes_con_base_real(pool_real, migrada, monkeypatch):
    monkeypatch.setattr(main, '_esquema_reportes_listo', False)
    cliente = TestClient(main.app)
    autor, votante = str(uuid.uuid4()), str(uuid.uuid4())
    r = cliente.post('/reportes', json={'lat': -34.6037, 'lng': -58.3816, 'categoria': 'robo', 'autor_id': autor})
    assert r.status_code == 201, r.text
    rid, token = r.json()['id'], r.json()['delete_token']
    # El token se guarda como hash, nunca en claro.
    assert _contar(migrada, 'SELECT count(*) FROM reportes_colaborativos WHERE delete_token_hash = %s', token) == 0

    assert cliente.post(f'/reportes/{rid}/confirmar', json={'autor_id': votante, 'tipo': 'confirma'}).status_code == 201
    assert cliente.post(f'/reportes/{rid}/confirmar', json={'autor_id': votante, 'tipo': 'desmiente'}).status_code == 201
    assert _contar(migrada, 'SELECT count(*) FROM reportes_confirmaciones WHERE reporte_id = %s', rid) == 1

    assert cliente.delete(f'/reportes/{rid}', headers={'X-Report-Delete-Token': 'x' * 40}).status_code == 404
    assert cliente.delete(f'/reportes/{rid}', headers={'X-Report-Delete-Token': token}).status_code == 200
    # ON DELETE CASCADE de la migración 001.
    assert _contar(migrada, 'SELECT count(*) FROM reportes_confirmaciones WHERE reporte_id = %s', rid) == 0


def test_health_informa_base_ok_con_postgres_real(pool_real):
    r = TestClient(main.app).get('/health')
    assert r.status_code == 200
    assert r.json()['base_datos'] == 'ok'


def test_carga_inicial_solo_llena_tablas_vacias(url_base, tmp_path):
    import shutil

    import cargar_datos_iniciales as carga

    nombre = f'motosafe_test_carga_{uuid.uuid4().hex[:8]}'
    admin = psycopg2.connect(URL_SERVIDOR)
    admin.autocommit = True
    admin.cursor().execute(f'CREATE DATABASE {nombre}')
    url = _url_con_base(URL_SERVIDOR, nombre)
    try:
        migrar.aplicar_migraciones(url)
        # Sin CSV: no falla, avisa.
        assert set(carga.cargar_si_vacias(url, tmp_path).values()) == {'sin CSV'}

        datos = carga.cargar_hotspots.DIR_DATOS_POR_DEFECTO
        # data/ no está versionado (.gitignore): en un clon limpio, como el CI,
        # no hay CSV y solo se puede probar el camino de arriba.
        if not all((datos / a).is_file() for _, _, archivos in carga.CAPAS for a in archivos):
            pytest.skip('faltan los CSV de data/ (no versionados); se probó solo «sin CSV»')
        primera = carga.cargar_si_vacias(url, datos)
        assert primera == {'hotspots_riesgo': 'cargada 740', 'corredores_riesgo': 'cargada 243',
                           'hotspots_inseguridad': 'cargada 1135'}

        # Idempotente: con datos no recarga (aunque una fila se haya editado).
        with psycopg2.connect(url) as conn, conn.cursor() as cur:
            cur.execute("UPDATE corredores_riesgo SET calle = 'EDITADA' WHERE id = (SELECT min(id) FROM corredores_riesgo)")
        segunda = carga.cargar_si_vacias(url, datos)
        assert segunda == {'hotspots_riesgo': 'ya tenía 740', 'corredores_riesgo': 'ya tenía 243',
                           'hotspots_inseguridad': 'ya tenía 1135'}
        assert _contar(url, "SELECT count(*) FROM corredores_riesgo WHERE calle = 'EDITADA'") == 1

        # Solo la capa vacía se vuelve a cargar.
        with psycopg2.connect(url) as conn, conn.cursor() as cur:
            cur.execute('DELETE FROM hotspots_inseguridad')
        tercera = carga.cargar_si_vacias(url, datos)
        assert tercera['hotspots_inseguridad'] == 'cargada 1135'
        assert tercera['corredores_riesgo'] == 'ya tenía 243'
    finally:
        cur = admin.cursor()
        cur.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = %s', (nombre,))
        cur.execute(f'DROP DATABASE IF EXISTS {nombre}')
        admin.close()
