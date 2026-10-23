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
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit

import psycopg2
import pytest
from fastapi.testclient import TestClient

import auth
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
    rol_app = os.getenv('MOTOSAFE_TEST_ROL_SIN_DUENO')
    if rol_app:
        # T01 (SES-149): además del dueño (admin, usado para crear/migrar la
        # base), se prueba que el ROL que de verdad usaría el backend en
        # producción -- sin privilegios de dueño/superusuario -- alcance con
        # las concesiones de abajo. Si falta algo puntual, un test de este
        # archivo lo va a mostrar como un error de permisos real.
        grants = os.getenv('MOTOSAFE_TEST_GRANTS_SQL', '')
        if grants:
            admin = psycopg2.connect(url_base)
            admin.autocommit = True
            cur = admin.cursor()
            for sentencia in grants.split(';'):
                sentencia = sentencia.strip()
                if sentencia:
                    cur.execute(sentencia.format(rol=rol_app, db=urlsplit(url_base).path.lstrip('/')))
            admin.close()
    return url_base


@pytest.fixture
def pool_real(migrada, monkeypatch):
    """Pool nuevo de main apuntando a la base de prueba, sin mocks."""
    url_pool = migrada
    rol_app = os.getenv('MOTOSAFE_TEST_ROL_SIN_DUENO')
    if rol_app:
        partes = urlsplit(migrada)
        clave = os.getenv('MOTOSAFE_TEST_ROL_SIN_DUENO_PW', '')
        netloc = f'{rol_app}:{clave}@{partes.hostname}:{partes.port}'
        url_pool = urlunsplit(partes._replace(netloc=netloc))
    monkeypatch.setattr(main, 'DATABASE_URL', url_pool)
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


def test_ciclo_de_reportes_con_base_real(pool_real, migrada):
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


def test_mis_reportes_distingue_vigente_vencido_y_desmentido_con_base_real(pool_real, migrada):
    """F08: historial de reportes propios por (id, delete_token) -- la misma
    credencial privada que autoriza borrar. GET /reportes no sirve para esto
    porque excluye a propósito lo vencido y lo desmentido."""
    cliente = TestClient(main.app)
    autor = str(uuid.uuid4())

    vigente = cliente.post('/reportes', json={'lat': -34.6, 'lng': -58.4, 'categoria': 'robo', 'autor_id': autor})
    vencido = cliente.post('/reportes', json={'lat': -34.6, 'lng': -58.4, 'categoria': 'corte', 'autor_id': autor})
    desmentido = cliente.post('/reportes', json={'lat': -34.6, 'lng': -58.4, 'categoria': 'pavimento', 'autor_id': autor})
    id_vigente, token_vigente = vigente.json()['id'], vigente.json()['delete_token']
    id_vencido, token_vencido = vencido.json()['id'], vencido.json()['delete_token']
    id_desmentido, token_desmentido = desmentido.json()['id'], desmentido.json()['delete_token']

    # 'corte' vence a las 12h (VIGENCIA_HORAS_POR_CATEGORIA): lo hacemos pasar
    # como creado hace 13h para que quede vencido sin esperar de verdad.
    with psycopg2.connect(migrada) as conn, conn.cursor() as cur:
        cur.execute(
            "UPDATE reportes_colaborativos SET creado_en = now() - interval '13 hours' WHERE id = %s",
            (id_vencido,),
        )

    # Dos votantes distintos desmienten el tercero -- supera MIN_DESMENTIDAS_PARA_OCULTAR
    # y la diferencia contra confirmaciones (0) también.
    for _ in range(2):
        votante = str(uuid.uuid4())
        assert cliente.post(
            f'/reportes/{id_desmentido}/confirmar', json={'autor_id': votante, 'tipo': 'desmiente'}
        ).status_code == 201

    consulta = {'reportes': [
        {'id': id_vigente, 'delete_token': token_vigente},
        {'id': id_vencido, 'delete_token': token_vencido},
        {'id': id_desmentido, 'delete_token': token_desmentido},
        {'id': id_vigente, 'delete_token': 'x' * 40},  # token equivocado: no debe aparecer
        {'id': 999999, 'delete_token': 'y' * 40},  # id inexistente: no debe aparecer
    ]}
    r = cliente.post('/reportes/mios', json=consulta)
    assert r.status_code == 200
    por_id = {fila['id']: fila for fila in r.json()}
    assert len(por_id) == 3  # ni el token equivocado ni el id inexistente aparecen
    assert por_id[id_vigente]['estado'] == 'vigente'
    assert por_id[id_vencido]['estado'] == 'vencido'
    assert por_id[id_desmentido]['estado'] == 'desmentido'
    assert por_id[id_desmentido]['desmentidas'] == 2


def test_mis_reportes_vacio_no_pega_a_la_base(pool_real, migrada):
    assert TestClient(main.app).post('/reportes/mios', json={'reportes': []}).json() == []


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


def test_prensa_excluye_google_y_usa_fecha_de_ingesta_si_la_publicada_no_sirve(pool_real, migrada):
    """SES-080 (DEC-011): Google Noticias no se devuelve, y una fecha de
    publicación implausible (anterior a la ventana o posterior a la ingesta)
    cae a la de ingesta. Las filas no se borran."""
    cliente = TestClient(main.app)
    assert cliente.get('/reportes-prensa').status_code == 200
    casos = [
        ('Google Noticias GBA - seguridad', 'https://g.test/1', 'now()', 'now()'),                       # excluida por fuente
        ('Infobae', 'https://i.test/ayer', "now() - interval '2 days'", 'now()'),                       # fecha publicada válida
        ('Infobae', 'https://i.test/2013', "'2013-05-01'", "now() - interval '3 days'"),               # fecha imposible -> ingesta
        ('Infobae', 'https://i.test/sin-fecha', 'NULL', "now() - interval '1 day'"),                    # sin fecha -> ingesta
        ('Infobae', 'https://i.test/vieja', "now() - interval '2 days'", "now() - interval '40 days'"),  # ingesta vencida
    ]
    with psycopg2.connect(migrada) as conn, conn.cursor() as cur:
        for fuente, url, publicado, creado in casos:
            cur.execute(f"""
                INSERT INTO reportes_prensa (lat, lng, nivel_precision, radio_metros, titular, url_fuente, fuente, publicado_en, creado_en)
                VALUES (-34.6, -58.4, 'barrio', 800, 'Robo de moto', %s, %s, {publicado}, {creado})
            """, (url, fuente))

    filas = {f['url_fuente']: f for f in cliente.get('/reportes-prensa').json()}
    assert set(filas) == {'https://i.test/ayer', 'https://i.test/2013', 'https://i.test/sin-fecha'}
    # La fecha 2013 no se muestra: se reemplaza por la de ingesta (hace 3 días).
    fecha_2013 = datetime.fromisoformat(filas['https://i.test/2013']['publicado_en'])
    assert fecha_2013.year >= datetime.now(timezone.utc).year


# --- F11 (SES-165): sistema de usuarios real (registro, verificación, login, reseteo) ---
# auth.py hace sus propias conexiones (auth._conn(), no pasa por main._pool_conexiones),
# así que acá apuntamos auth.DATABASE_URL a la misma base de prueba desechable que ya
# arma `migrada`, en vez de reusar el fixture `pool_real` (que es específico de main).

@pytest.fixture
def auth_db(migrada, monkeypatch):
    monkeypatch.setattr(auth, 'DATABASE_URL', migrada)
    yield migrada


@pytest.fixture(autouse=True)
def _limite_de_intentos_limpio(monkeypatch):
    """H07 (assessment 2026-10-22, SES-168) sumó rate limiting a /auth/registro
    -- sin esto, los ~10 tests de este archivo que llaman a registro (todos
    desde el mismo "IP" del TestClient) se pisan entre sí y algunos empiezan a
    dar 429 según el orden en que corran, en vez del código que cada test
    quiere probar."""
    monkeypatch.setattr(auth, '_intentos_fallidos', {})


@pytest.fixture
def sin_mail_real(monkeypatch):
    """Los tests automáticos no mandan mail real -- eso se verificó aparte, a
    mano, con una casilla real (ver docs/evidencias de F11). Acá solo se
    registra qué se habría mandado, para poder leer el código real del test.
    Devuelve True (igual que un envío real por SMTP) para que mail_enviado
    en las respuestas siga comportándose como en producción."""
    enviados = []

    def _fake_enviar(destinatario, tipo, codigo):
        enviados.append({'destinatario': destinatario, 'tipo': tipo, 'codigo': codigo})
        return True

    monkeypatch.setattr(auth.email_service, 'enviar_codigo', _fake_enviar)
    return enviados


@pytest.fixture
def cliente_auth(auth_db, sin_mail_real):
    return TestClient(main.app, base_url='https://testserver'), sin_mail_real


def _codigo_real(url, email, tipo):
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute(
            """SELECT c.codigo FROM codigos_auth c JOIN usuarios u ON u.id = c.usuario_id
               WHERE u.email = %s AND c.tipo = %s ORDER BY c.creado_en DESC LIMIT 1""",
            (email, tipo),
        )
        fila = cur.fetchone()
        return fila[0] if fila else None


def test_registro_crea_fila_real_y_manda_codigo_de_verificacion(cliente_auth, auth_db):
    cliente, enviados = cliente_auth
    respuesta = cliente.post('/auth/registro', json={'email': 'Prueba@Ejemplo.com', 'nombre_usuario': 'Prueba', 'password': 'una-clave-larga-1'})
    assert respuesta.status_code == 201
    assert respuesta.json() == {'ok': True, 'mail_enviado': True}

    # Email normalizado a minúsculas en la fila real.
    assert _contar(auth_db, "SELECT count(*) FROM usuarios WHERE email = 'prueba@ejemplo.com'") == 1
    assert _contar(auth_db, "SELECT count(*) FROM usuarios WHERE email_verificado = false AND email = 'prueba@ejemplo.com'") == 1
    assert len(enviados) == 1 and enviados[0]['tipo'] == 'verificacion'
    assert len(enviados[0]['codigo']) == 6 and enviados[0]['codigo'].isdigit()


def test_registro_rechaza_email_duplicado(cliente_auth):
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'dup@ejemplo.com', 'nombre_usuario': 'Dup1', 'password': 'una-clave-larga-1'})
    respuesta = cliente.post('/auth/registro', json={'email': 'dup@ejemplo.com', 'nombre_usuario': 'Dup2', 'password': 'otra-clave-larga-2'})
    assert respuesta.status_code == 409


def test_registro_rechaza_nombre_usuario_duplicado(cliente_auth):
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'nombre1@ejemplo.com', 'nombre_usuario': 'MismoNombre', 'password': 'una-clave-larga-1'})
    respuesta = cliente.post('/auth/registro', json={'email': 'nombre2@ejemplo.com', 'nombre_usuario': 'MismoNombre', 'password': 'otra-clave-larga-2'})
    assert respuesta.status_code == 409
    assert 'nombre de usuario' in respuesta.json()['detail'].lower()


def test_registro_rechaza_contrasena_corta(cliente_auth):
    cliente, _ = cliente_auth
    respuesta = cliente.post('/auth/registro', json={'email': 'corta@ejemplo.com', 'nombre_usuario': 'Corta', 'password': 'corta1'})
    assert respuesta.status_code == 400


def test_registro_rechaza_nombre_usuario_vacio(cliente_auth):
    cliente, _ = cliente_auth
    respuesta = cliente.post('/auth/registro', json={'email': 'sinnombre@ejemplo.com', 'nombre_usuario': '  ', 'password': 'una-clave-larga-1'})
    assert respuesta.status_code == 400


def test_login_falla_sin_verificar_el_mail(cliente_auth):
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'sinverificar@ejemplo.com', 'nombre_usuario': 'SinVerificar', 'password': 'una-clave-larga-1'})
    respuesta = cliente.post('/auth/login', json={'email': 'sinverificar@ejemplo.com', 'password': 'una-clave-larga-1'})
    assert respuesta.status_code == 403
    assert 'código' in respuesta.json()['detail'].lower()


def test_flujo_completo_registro_verificar_login(cliente_auth, auth_db):
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'completo@ejemplo.com', 'nombre_usuario': 'Completo', 'password': 'una-clave-larga-1'})
    codigo = _codigo_real(auth_db, 'completo@ejemplo.com', 'verificacion')
    assert codigo is not None

    mal = cliente.post('/auth/verificar-codigo', json={'email': 'completo@ejemplo.com', 'codigo': '000000'})
    assert mal.status_code == 400

    bien = cliente.post('/auth/verificar-codigo', json={'email': 'completo@ejemplo.com', 'codigo': codigo})
    assert bien.status_code == 200
    assert _contar(auth_db, "SELECT count(*) FROM usuarios WHERE email = 'completo@ejemplo.com' AND email_verificado = true") == 1

    login = cliente.post('/auth/login', json={'email': 'completo@ejemplo.com', 'password': 'una-clave-larga-1'})
    assert login.status_code == 200
    assert 'motosafe_session' in login.cookies


def test_login_con_nombre_de_usuario_funciona_igual_que_con_email(cliente_auth, auth_db):
    """SES-169: el mismo campo de login acepta email o nombre de usuario."""
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'conusuario@ejemplo.com', 'nombre_usuario': 'ConUsuario', 'password': 'una-clave-larga-1'})
    codigo = _codigo_real(auth_db, 'conusuario@ejemplo.com', 'verificacion')
    cliente.post('/auth/verificar-codigo', json={'email': 'conusuario@ejemplo.com', 'codigo': codigo})

    con_email = cliente.post('/auth/login', json={'email': 'conusuario@ejemplo.com', 'password': 'una-clave-larga-1'})
    assert con_email.status_code == 200
    cliente.post('/auth/logout')

    con_nombre = cliente.post('/auth/login', json={'email': 'ConUsuario', 'password': 'una-clave-larga-1'})
    assert con_nombre.status_code == 200
    assert 'motosafe_session' in con_nombre.cookies

    me = cliente.get('/auth/me')
    assert me.json()['usuario'] == 'conusuario@ejemplo.com'


def test_login_con_nombre_de_usuario_distinto_mayusculas_falla(cliente_auth, auth_db):
    """El nombre de usuario es case-sensitive, igual que al registrarse."""
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'caseusuario@ejemplo.com', 'nombre_usuario': 'CaseUsuario', 'password': 'una-clave-larga-1'})
    codigo = _codigo_real(auth_db, 'caseusuario@ejemplo.com', 'verificacion')
    cliente.post('/auth/verificar-codigo', json={'email': 'caseusuario@ejemplo.com', 'codigo': codigo})

    respuesta = cliente.post('/auth/login', json={'email': 'caseusuario', 'password': 'una-clave-larga-1'})
    assert respuesta.status_code == 401


def test_login_sin_verificar_con_nombre_de_usuario_devuelve_el_email_real(cliente_auth):
    """SES-169: si se loguea con nombre de usuario y falta verificar, el
    frontend necesita el email real (no el nombre de usuario) para reenviar
    o verificar el código -- lo manda el header X-Email."""
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'sinverificarconusuario@ejemplo.com', 'nombre_usuario': 'SinVerificarConUsuario', 'password': 'una-clave-larga-1'})
    respuesta = cliente.post('/auth/login', json={'email': 'SinVerificarConUsuario', 'password': 'una-clave-larga-1'})
    assert respuesta.status_code == 403
    assert respuesta.headers['X-Email'] == 'sinverificarconusuario@ejemplo.com'


def test_codigo_de_verificacion_se_invalida_tras_varios_intentos_fallidos(cliente_auth):
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'fuerza-bruta@ejemplo.com', 'nombre_usuario': 'FuerzaBruta', 'password': 'una-clave-larga-1'})
    for _ in range(5):
        r = cliente.post('/auth/verificar-codigo', json={'email': 'fuerza-bruta@ejemplo.com', 'codigo': '111111'})
        assert r.status_code == 400
    # El sexto intento, aunque el código real esté bien ingresado a mano, ya está bloqueado.
    bloqueado = cliente.post('/auth/verificar-codigo', json={'email': 'fuerza-bruta@ejemplo.com', 'codigo': '111111'})
    assert 'intentos' in bloqueado.json()['detail'].lower()


def test_reenviar_codigo_no_filtra_si_el_email_existe(cliente_auth):
    cliente, enviados = cliente_auth
    existe = cliente.post('/auth/reenviar-codigo', json={'email': 'no-existe-nunca@ejemplo.com'})
    no_existe_resp = cliente.post('/auth/reenviar-codigo', json={'email': 'tampoco-existe@ejemplo.com'})
    assert existe.status_code == 200 and no_existe_resp.status_code == 200
    assert existe.json() == no_existe_resp.json()
    assert enviados == []  # ninguno de los dos emails está registrado, no se manda nada


def test_olvide_password_no_filtra_si_el_email_existe(cliente_auth, auth_db):
    cliente, enviados = cliente_auth
    cliente.post('/auth/registro', json={'email': 'existente@ejemplo.com', 'nombre_usuario': 'Existente', 'password': 'una-clave-larga-1'})
    enviados.clear()

    con_cuenta = cliente.post('/auth/olvide-password', json={'email': 'existente@ejemplo.com'})
    sin_cuenta = cliente.post('/auth/olvide-password', json={'email': 'inventado-total@ejemplo.com'})
    assert con_cuenta.status_code == 200 and sin_cuenta.status_code == 200
    assert con_cuenta.json() == sin_cuenta.json(), 'la respuesta tiene que ser idéntica exista o no la cuenta'
    assert len(enviados) == 1 and enviados[0]['tipo'] == 'reset_password'


def test_flujo_completo_reset_password(cliente_auth, auth_db):
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'reset@ejemplo.com', 'nombre_usuario': 'Reset', 'password': 'clave-original-1'})
    codigo_verif = _codigo_real(auth_db, 'reset@ejemplo.com', 'verificacion')
    cliente.post('/auth/verificar-codigo', json={'email': 'reset@ejemplo.com', 'codigo': codigo_verif})

    cliente.post('/auth/olvide-password', json={'email': 'reset@ejemplo.com'})
    codigo_reset = _codigo_real(auth_db, 'reset@ejemplo.com', 'reset_password')
    assert codigo_reset is not None

    reset = cliente.post('/auth/resetear-password', json={
        'email': 'reset@ejemplo.com', 'codigo': codigo_reset, 'password_nueva': 'clave-nueva-2',
    })
    assert reset.status_code == 200

    falla_con_vieja = cliente.post('/auth/login', json={'email': 'reset@ejemplo.com', 'password': 'clave-original-1'})
    assert falla_con_vieja.status_code == 401

    funciona_con_nueva = cliente.post('/auth/login', json={'email': 'reset@ejemplo.com', 'password': 'clave-nueva-2'})
    assert funciona_con_nueva.status_code == 200


def test_auth_me_sin_sesion_da_401(cliente_auth):
    cliente, _ = cliente_auth
    assert cliente.get('/auth/me').status_code == 401


def test_login_con_email_inexistente_falla(cliente_auth):
    cliente, _ = cliente_auth
    respuesta = cliente.post('/auth/login', json={'email': 'no-existe@ejemplo.com', 'password': 'cualquiera'})
    assert respuesta.status_code == 401


def test_bloqueo_tras_varios_intentos_fallidos_de_login(cliente_auth, monkeypatch):
    import auth as auth_module
    monkeypatch.setattr(auth_module, '_intentos_fallidos', {})
    cliente, _ = cliente_auth
    email = 'bloqueo@ejemplo.com'
    for _ in range(5):
        cliente.post('/auth/login', json={'email': email, 'password': 'mal'})
    respuesta = cliente.post('/auth/login', json={'email': email, 'password': 'sigue-mal'})
    assert respuesta.status_code == 429


# --- H04/H05/H07/H13 (assessment 2026-10-22, corregidos SES-168) -----------

def test_codigo_anterior_se_invalida_al_pedir_uno_nuevo(cliente_auth, auth_db):
    """H04: antes, pedir un código nuevo (reenviar-codigo) no invalidaba el
    anterior -- quien tuviera el primer mail podía seguir usándolo."""
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'codigoviejo@ejemplo.com', 'nombre_usuario': 'CodigoViejo', 'password': 'una-clave-larga-1'})
    codigo_viejo = _codigo_real(auth_db, 'codigoviejo@ejemplo.com', 'verificacion')
    assert codigo_viejo is not None

    cliente.post('/auth/reenviar-codigo', json={'email': 'codigoviejo@ejemplo.com'})
    codigo_nuevo = _codigo_real(auth_db, 'codigoviejo@ejemplo.com', 'verificacion')
    assert codigo_nuevo is not None and codigo_nuevo != codigo_viejo

    con_el_viejo = cliente.post('/auth/verificar-codigo', json={'email': 'codigoviejo@ejemplo.com', 'codigo': codigo_viejo})
    assert con_el_viejo.status_code == 400

    con_el_nuevo = cliente.post('/auth/verificar-codigo', json={'email': 'codigoviejo@ejemplo.com', 'codigo': codigo_nuevo})
    assert con_el_nuevo.status_code == 200


def test_codigo_usa_secrets_no_random():
    """H04: _generar_codigo tiene que usar secrets (CSPRNG), no random."""
    import inspect

    lineas_de_codigo = [
        linea for linea in inspect.getsource(auth._generar_codigo).splitlines()
        if not linea.strip().startswith('#')
    ]
    assert any('secrets.randbelow' in linea for linea in lineas_de_codigo)
    assert not any('random.randint' in linea for linea in lineas_de_codigo)


def test_cookie_emitida_antes_del_reset_deja_de_validar_despues(cliente_auth, auth_db):
    """H05: antes, una cookie de sesión ya firmada seguía funcionando incluso
    después de restablecer la contraseña -- la sesión era puramente un token
    firmado sin ninguna verificación contra la base."""
    cliente, _ = cliente_auth
    cliente.post('/auth/registro', json={'email': 'revocar@ejemplo.com', 'nombre_usuario': 'Revocar', 'password': 'clave-original-1'})
    codigo_verif = _codigo_real(auth_db, 'revocar@ejemplo.com', 'verificacion')
    cliente.post('/auth/verificar-codigo', json={'email': 'revocar@ejemplo.com', 'codigo': codigo_verif})

    login = cliente.post('/auth/login', json={'email': 'revocar@ejemplo.com', 'password': 'clave-original-1'})
    assert login.status_code == 200
    assert cliente.get('/auth/me').status_code == 200, 'la cookie recién emitida sigue siendo válida'

    cliente.post('/auth/olvide-password', json={'email': 'revocar@ejemplo.com'})
    codigo_reset = _codigo_real(auth_db, 'revocar@ejemplo.com', 'reset_password')
    reset = cliente.post('/auth/resetear-password', json={
        'email': 'revocar@ejemplo.com', 'codigo': codigo_reset, 'password_nueva': 'clave-nueva-2',
    })
    assert reset.status_code == 200

    # La misma cookie (el cliente la sigue mandando) ya no debería validar.
    sesion_vieja = cliente.get('/auth/me')
    assert sesion_vieja.status_code == 401

    nuevo_login = cliente.post('/auth/login', json={'email': 'revocar@ejemplo.com', 'password': 'clave-nueva-2'})
    assert nuevo_login.status_code == 200
    assert cliente.get('/auth/me').status_code == 200, 'la cookie nueva, emitida después del reset, sí vale'


def test_registro_se_bloquea_tras_varios_intentos_desde_la_misma_ip(cliente_auth):
    """H07: /auth/registro no tenía ningún límite de intentos por IP."""
    cliente, _ = cliente_auth
    for i in range(5):
        cliente.post('/auth/registro', json={
            'email': f'rl{i}@ejemplo.com', 'nombre_usuario': f'RL{i}', 'password': 'una-clave-larga-1',
        })
    respuesta = cliente.post('/auth/registro', json={
        'email': 'rl-de-mas@ejemplo.com', 'nombre_usuario': 'RLDeMas', 'password': 'una-clave-larga-1',
    })
    assert respuesta.status_code == 429


def test_registro_informa_mail_enviado_false_si_no_hay_smtp_configurado(auth_db, monkeypatch):
    """H13: antes, si SMTP no estaba configurado, enviar_codigo caía al
    fallback de consola pero el endpoint igual respondía mail_enviado: true."""
    monkeypatch.setattr(auth.email_service, 'enviar_codigo', lambda destinatario, tipo, codigo: False)
    cliente = TestClient(main.app, base_url='https://testserver')
    respuesta = cliente.post('/auth/registro', json={
        'email': 'sinsmtp@ejemplo.com', 'nombre_usuario': 'SinSmtp', 'password': 'una-clave-larga-1',
    })
    assert respuesta.status_code == 201
    assert respuesta.json() == {'ok': True, 'mail_enviado': False}
