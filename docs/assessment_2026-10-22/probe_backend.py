"""Reproducciones de auditoría. Solo PostgreSQL desechable en 127.0.0.1:55439.
No envía correos, no usa .env y no toca la base de la aplicación.
Ejecutar desde la raíz con backend/venv312/Scripts/python.exe.
"""
import os
import sys
import json
import uuid
from pathlib import Path
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
URL = 'postgresql://audit:audit-local-disposable@127.0.0.1:55439/'
os.environ.update(DATABASE_URL=URL+'postgres', SESSION_SECRET='only-disposable-audit-secret',
                  AUTH_HABILITADO='true', SMTP_USER='', SMTP_PASSWORD='', TOMTOM_API_KEY='')
import psycopg2
import migrar
import auth
import main
from fastapi.testclient import TestClient

admin = psycopg2.connect(URL+'postgres')
admin.autocommit = True
db = 'audit_probe_' + uuid.uuid4().hex[:10]
admin.cursor().execute('CREATE DATABASE ' + db)
out = {}
try:
    url = URL+db
    migrar.aplicar_migraciones(url)
    auth.DATABASE_URL = main.DATABASE_URL = url
    main._pool_conexiones = main._PoolConexiones()
    client = TestClient(main.app, base_url='https://audit.test')
    with patch.object(auth.email_service, 'enviar_codigo'):
        response = client.post('/auth/registro', json={'email':'audit@example.invalid', 'nombre_usuario':'Audit', 'password':'original-only-test'})
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute('UPDATE usuarios SET email_verificado=true RETURNING id')
        uid = cur.fetchone()[0]
        for seconds, code in ((2,'111111'), (1,'222222')):
            cur.execute("INSERT INTO codigos_auth(usuario_id,codigo,tipo,expira_en,creado_en) VALUES(%s,%s,'reset_password',%s,%s)",
                        (uid, code, datetime.now(timezone.utc)+timedelta(minutes=15),datetime.now(timezone.utc)-timedelta(seconds=seconds)))
    client.post('/auth/login', json={'email':'audit@example.invalid','password':'original-only-test'})
    old_cookie = client.cookies.get(auth.SESSION_COOKIE_NAME)
    result_new = client.post('/auth/resetear-password',json={'email':'audit@example.invalid','codigo':'222222','password_nueva':'new-only-test'})
    result_old = client.post('/auth/resetear-password',json={'email':'audit@example.invalid','codigo':'111111','password_nueva':'old-code-reused-test'})
    out['older_reset_code_after_newer_consumed'] = [result_new.status_code, result_old.status_code]
    attacker = TestClient(main.app, base_url='https://audit.test')
    attacker.cookies.set(auth.SESSION_COOKIE_NAME,old_cookie)
    out['session_after_password_reset'] = attacker.get('/auth/me').status_code
    client.post('/auth/logout')
    out['copied_session_after_logout'] = attacker.get('/auth/me').status_code
    with patch.object(auth.email_service, '_fallback_consola') as fallback:
        r = client.post('/auth/registro',json={'email':'no-smtp@example.invalid','nombre_usuario':'NoSMTP','password':'only-test-password'})
        out['no_smtp_registration'] = {'status':r.status_code,'body':r.json(),'console_fallback_called':fallback.called}
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO reportes_prensa(lat,lng,nivel_precision,radio_metros,titular,url_fuente,fuente,tipo_incidente,publicado_en) VALUES(-34.6,-58.4,'calle',100,'Noticia antigua de prueba','https://example.invalid/old','Medio directo','choque',now()-interval '2 years')")
    out['two_year_old_article_in_recent_list'] = len(attacker.get('/reportes-prensa').json())
    main._cache_reportes_recientes.clear()
    out['two_year_old_article_adjusts_risk'] = len(main._obtener_reportes_recientes_por_tipo('choque'))
    # Ventana de deduplicación real: la nota vieja recibe una candidata nueva.
    import scrapear_noticias_robos as scraper
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute("INSERT INTO reportes_prensa(lat,lng,nivel_precision,radio_metros,titular,url_fuente,fuente,tipo_incidente,publicado_en) VALUES(-34.7,-58.5,'calle',100,'Choque nuevo en una esquina','https://example.invalid/new','Medio directo','choque',now()) RETURNING id")
        new_id = cur.fetchone()[0]
        dup = scraper._detectar_duplicado_semantico(cur,'Choque antiguo distinto','choque',-34.7,-58.5,100,datetime.now(timezone.utc)-timedelta(days=100))
        out['dedup_100_days_apart'] = {'matched':dup==new_id,'days':100}
    # Semántica de disponibilidad, sin cortar ningún servicio real.
    with patch.object(main._pool_conexiones,'getconn',side_effect=RuntimeError('simulated unavailable')):
        r = client.get('/health')
        out['health_without_db']={'status':r.status_code,'state':r.json()['estado']}
    out['model_runtime'] = {'type':type(main.modelo_final).__name__, 'trees':main.modelo_final.n_estimators,
        'max_depth':main.modelo_final.max_depth,'min_samples_leaf':main.modelo_final.min_samples_leaf,
        'class_weight':main.modelo_final.class_weight,'features':main.modelo_final.n_features_in_,
        'columns':len(main.columnas_modelo),'classes':main.modelo_final.classes_.tolist(),
        'threshold_fingerprint_matches':main.UMBRALES_RIESGO_ACTUALIZADOS,
        'sklearn_version_matches':main.SKLEARN_VERSION_ENTRENAMIENTO == main.sklearn.__version__}
    with patch.object(main.httpx,'get',side_effect=RuntimeError('offline')):
        main._cache_clima.update(datos={'lluvia':'SI','temperatura':20.0,'humedad':90.0},timestamp=0)
        out['weather_stale_response_keys']=sorted(main.obtener_clima_actual().keys())
    from unittest.mock import Mock
    upstream = Mock(content=b'fake-only-audit')
    with patch.object(main,'TOMTOM_API_KEY','fake-audit-key'), patch.object(main.httpx,'get',return_value=upstream) as get:
        out['invalid_traffic_tile_status']=attacker.get('/trafico/tiles/99/-1/-1.png').status_code
        out['invalid_traffic_tile_reaches_upstream']=get.called
    # Límite público de registro: se prueba el control, sin bcrypt ni correo real.
    with patch.object(auth,'_hashear_password',return_value='test-only'), patch.object(auth.email_service,'enviar_codigo'):
        out['registrations_same_ip']=[client.post('/auth/registro',json={'email':f'limit{i}@example.invalid','nombre_usuario':f'Limit{i}','password':'test-only-password'}).status_code for i in range(8)]
    # Votación desde la MISMA sesión cambiando el identificador proporcionado.
    r = attacker.post('/reportes',json={'lat':-34.6,'lng':-58.4,'categoria':'pavimento','autor_id':str(uuid.uuid4())})
    report_id=r.json()['id']
    out['same_session_multiple_votes']=[attacker.post(f'/reportes/{report_id}/confirmar',json={'autor_id':str(uuid.uuid4()),'tipo':'desmiente'}).status_code for _ in range(3)]
    out['own_report_visible_after_self_votes']=any(r['id']==report_id for r in attacker.get('/reportes').json())
    # La migración 006 falla con una cuenta preexistente cuyo email supera 50 caracteres.
    with psycopg2.connect(url) as conn, conn.cursor() as cur:
        cur.execute('ALTER TABLE usuarios DROP COLUMN nombre_usuario CASCADE')
        cur.execute("INSERT INTO usuarios(email,password_hash) VALUES(%s,'test')", ('a'*51+'@example.invalid',))
    try:
        with psycopg2.connect(url) as conn, conn.cursor() as cur:
            cur.execute((ROOT/'backend/migrations/006_usuarios_nombre.sql').read_text(encoding='utf-8'))
        out['migration_long_email']='ok'
    except Exception as exc:
        out['migration_long_email']=type(exc).__name__
    print(json.dumps(out,indent=2,ensure_ascii=False))
finally:
    with admin.cursor() as cur:
        cur.execute('SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=%s',(db,))
        cur.execute('DROP DATABASE '+db)
    admin.close()
